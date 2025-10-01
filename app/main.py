import asyncio
import base64
import httpx
import json
import os
import random
import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Literal, Set, List

# --- Crittografia ---
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature, InvalidTag

# --- Configurazione Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# --- Configurazione Identità e Rete ---
DATA_DIR = "data"
ED25519_KEY_FILE = os.path.join(DATA_DIR, "ed25519_private_key.pem")
X25519_KEY_FILE = os.path.join(DATA_DIR, "x25519_private_key.pem")

NODE_PORT = int(os.getenv("NODE_PORT", "8000"))
RENDEZVOUS_URL = os.getenv("RENDEZVOUS_URL")
OWN_URL = os.getenv("OWN_URL")
SUBSCRIBED_CHANNELS_ENV = os.getenv("SUBSCRIBED_CHANNELS", "")

if not RENDEZVOUS_URL or not OWN_URL:
    raise ValueError("Le variabili d'ambiente RENDEZVOUS_URL e OWN_URL sono obbligatorie.")

# --- Gestione Chiavi Crittografiche ---
def load_or_create_keys():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(ED25519_KEY_FILE, "rb") as f: ed_priv_key = serialization.load_pem_private_key(f.read(), password=None)
    except (FileNotFoundError, ValueError):
        logging.warning(f"File chiave Ed25519 non trovato, ne genero uno nuovo.")
        ed_priv_key = ed25519.Ed25519PrivateKey.generate()
        with open(ED25519_KEY_FILE, "wb") as f: f.write(ed_priv_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    try:
        with open(X25519_KEY_FILE, "rb") as f: x_priv_key = serialization.load_pem_private_key(f.read(), password=None)
    except (FileNotFoundError, ValueError):
        logging.warning(f"File chiave X25519 non trovato, ne genero uno nuovo.")
        x_priv_key = x25519.X25519PrivateKey.generate()
        with open(X25519_KEY_FILE, "wb") as f: f.write(x_priv_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    return ed_priv_key, x_priv_key

ed25519_private_key, x25519_private_key = load_or_create_keys()
NODE_ID = base64.urlsafe_b64encode(ed25519_private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode('utf-8')
KX_PUBLIC_KEY_B64 = base64.urlsafe_b64encode(x25519_private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode('utf-8')

# --- Strutture Dati e Lock per la Concorrenza ---
class GossipPacket(BaseModel): channel_id: str; payload: str; sender_id: str; signature: str
class CreateTaskPayload(BaseModel): title: str

state_lock = asyncio.Lock()

subscribed_channels: Set[str] = {"global"}.union(set(c.strip() for c in SUBSCRIBED_CHANNELS_ENV.split(",") if c.strip()))
network_state = {"global": {"nodes": {}, "proposals": {}}}
for channel in subscribed_channels:
    if channel not in network_state:
        network_state[channel] = {"participants": {NODE_ID}, "tasks": {}, "proposals": {}}
known_peers = set()

network_state["global"]["nodes"][NODE_ID] = {
    "id": NODE_ID, "url": OWN_URL, "kx_public_key": KX_PUBLIC_KEY_B64,
    "last_seen": time.time(), "version": 1
}

# --- Endpoint di Base ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "node_id": NODE_ID})

@app.get("/state")
async def get_state():
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    reputations = calculate_reputations(state_copy)
    for node_id, node_data in state_copy["global"]["nodes"].items():
        node_data["reputation"] = reputations.get(node_id, 0)
    return state_copy

@app.get("/channels", response_model=List[str])
async def get_subscribed_channels():
    return list(subscribed_channels)

# --- Endpoint Task ---
@app.post("/tasks", status_code=201)
async def create_task(payload: CreateTaskPayload, channel: str):
    if channel == "global" or channel not in subscribed_channels: raise HTTPException(400, "Canale non valido o non sottoscritto.")
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    new_task = {
        "id": task_id, "owner": NODE_ID, "title": payload.title, "status": "open",
        "assignee": None, "created_at": now, "updated_at": now, "is_deleted": False
    }
    async with state_lock:
        network_state[channel]["tasks"][task_id] = new_task
    return new_task

@app.delete("/tasks/{task_id}", status_code=200)
async def delete_task(task_id: str, channel: str):
    if channel not in network_state or task_id not in network_state[channel]["tasks"]: raise HTTPException(404, "Task non trovato nel canale specificato")
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        if task["owner"] != NODE_ID: raise HTTPException(403, "Non sei il proprietario del task.")
        task["is_deleted"] = True
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return task

@app.post("/tasks/{task_id}/claim", status_code=200)
async def claim_task(task_id: str, channel: str):
    if channel not in network_state or task_id not in network_state[channel]["tasks"]: raise HTTPException(404, "Task non trovato")
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        if task["status"] != "open": raise HTTPException(400, f"Impossibile prendere in carico il task: stato attuale '{task['status']}'")
        task["status"] = "claimed"
        task["assignee"] = NODE_ID
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return task

@app.post("/tasks/{task_id}/progress", status_code=200)
async def progress_task(task_id: str, channel: str):
    if channel not in network_state or task_id not in network_state[channel]["tasks"]: raise HTTPException(404, "Task non trovato")
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        if task["assignee"] != NODE_ID or task["status"] != "claimed": raise HTTPException(403, "Azione non permessa o stato non valido.")
        task["status"] = "in_progress"
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return task

@app.post("/tasks/{task_id}/complete", status_code=200)
async def complete_task(task_id: str, channel: str):
    if channel not in network_state or task_id not in network_state[channel]["tasks"]: raise HTTPException(404, "Task non trovato")
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        if task["assignee"] != NODE_ID or task["status"] != "in_progress": raise HTTPException(403, "Azione non permessa o stato non valido.")
        task["status"] = "completed"
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
    return task

# --- Endpoint Governance ---
@app.post("/gossip")
async def receive_gossip(packet: GossipPacket):
    try:
        sender_public_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(packet.sender_id))
        sender_public_key.verify(base64.urlsafe_b64decode(packet.signature), packet.payload.encode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Firma non valida: {e}")

    channel_id = packet.channel_id
    if channel_id not in subscribed_channels: return {"status": "ignored_unsubscribed_channel"}

    async with state_lock:
        incoming_state = json.loads(packet.payload)
        local_state = network_state.setdefault(channel_id, {"participants": set(), "tasks": {}, "proposals": {}})
        
        if channel_id == "global":
            # Merge dei nodi globali
            for nid, ndata in incoming_state.get("nodes", {}).items():
                if nid != NODE_ID and (nid not in local_state.get("nodes", {}) or ndata.get("last_seen", 0) > local_state["nodes"][nid].get("last_seen", 0)):
                    local_state["nodes"][nid] = ndata
        else:
            # Merge dei partecipanti per canali tematici
            local_state["participants"].update(incoming_state.get("participants", []))

        # Logica di merge completa per Task e Proposte in QUALSIASI canale
        # Merge Tasks (Logica LWW con validazione) - VERSIONE CORRETTA
        for tid, itask in incoming_state.get("tasks", {}).items():
            ltask = local_state.get("tasks", {}).get(tid)

            # Caso 1: Il task è completamente nuovo per questo nodo.
            if not ltask:
                local_state["tasks"][tid] = itask
                continue

            # Caso 2: Il task esiste, applica la regola Last-Write-Wins.
            # Prosegui solo se l'aggiornamento ricevuto è più recente.
            # Nel gossip ci fidiamo del timestamp updated_at come unica fonte di verità.
            # La validazione delle transizioni di stato è gestita negli endpoint API.
            if itask.get("updated_at", "") > ltask.get("updated_at", ""):
                local_state["tasks"][tid] = itask

        # Merge Proposals (LWW ibrido)
        for pid, iprop in incoming_state.get("proposals", {}).items():
            lprop = local_state.get("proposals", {}).get(pid)
            if not lprop:
                local_state["proposals"][pid] = iprop
            else:
                merged_votes = lprop.get("votes", {}).copy()
                merged_votes.update(iprop.get("votes", {}))
                if iprop.get("updated_at", "") > lprop.get("updated_at", ""):
                    lprop.update(iprop)
                lprop["votes"] = merged_votes

    return await create_signed_packet(channel_id)

async def create_signed_packet(channel_id: str) -> dict:
    async with state_lock:
        if channel_id not in network_state: return None
        network_state["global"]["nodes"][NODE_ID]["last_seen"] = time.time()
        network_state["global"]["nodes"][NODE_ID]["version"] += 1
        if channel_id != "global":
            network_state[channel_id]["participants"].add(NODE_ID)
        payload_copy = json.loads(json.dumps(network_state[channel_id], default=list))
    payload_str = json.dumps(payload_copy, separators=(",", ":"))
    signature = ed25519_private_key.sign(payload_str.encode('utf-8'))
    return {
        "channel_id": channel_id, "payload": payload_str,
        "sender_id": NODE_ID, "signature": base64.urlsafe_b64encode(signature).decode('utf-8')
    }

async def network_maintenance_loop():
    await asyncio.sleep(5)
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{RENDEZVOUS_URL}/register", json={"url": OWN_URL}, timeout=5)
                response = await client.get(f"{RENDEZVOUS_URL}/get_peers?limit=10", timeout=5)
                if response.status_code == 200:
                    new_peers = set(response.json())
                    new_peers.discard(OWN_URL)
                    if new_peers - known_peers:
                        known_peers.update(new_peers)
        except httpx.RequestError as e:
            logging.warning(f"Impossibile contattare Rendezvous Server: {e}")
        except Exception: pass
        if known_peers:
            peer_url = random.choice(list(known_peers))
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(f"{peer_url}/channels")
                    response.raise_for_status()
                    peer_channels = set(response.json())
                    common_channels = subscribed_channels.intersection(peer_channels)
                    for channel in common_channels:
                        packet = await create_signed_packet(channel)
                        if packet:
                            gossip_response = await client.post(f"{peer_url}/gossip", json=packet)
                            gossip_response.raise_for_status()
                            response_packet = GossipPacket(**gossip_response.json())
                            await receive_gossip(response_packet)
            except httpx.RequestError as e:
                logging.warning(f"Gossip con {peer_url} fallito. Errore: {e}")
                known_peers.discard(peer_url)
            except Exception: pass
        await asyncio.sleep(random.uniform(5, 10))

def calculate_reputations(full_state: dict) -> Dict[str, int]:
    reputations = {node_id: 0 for node_id in full_state.get("global", {}).get("nodes", {})}
    for channel_id, channel_data in full_state.items():
        if channel_id != "global":
            for task in channel_data.get("tasks", {}).values():
                if task.get("status") == "completed" and task.get("assignee") in reputations:
                    reputations[task["assignee"]] += 10
        for prop in channel_data.get("proposals", {}).values():
            for voter_id in prop.get("votes", {}):
                if voter_id in reputations:
                    reputations[voter_id] += 1
    return reputations

@app.on_event("startup")
async def on_startup():
    logging.info(f"🚀 Nodo Synapse-NG avviato. ID: {NODE_ID[:16]}...")
    logging.info(f"📡 Canali sottoscritti: {list(subscribed_channels)}")
    asyncio.create_task(network_maintenance_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            state = await get_state()
            await websocket.send_json(state)
            await asyncio.sleep(1)
    except Exception:
        pass
