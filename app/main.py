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

# --- WebRTC ---
from app.webrtc_manager import ConnectionManager
from app.synapsesub_protocol import PubSubManager, SynapseSubMessage, MessageType

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
RENDEZVOUS_URL = os.getenv("RENDEZVOUS_URL")  # Opzionale per P2P mode
BOOTSTRAP_NODES = os.getenv("BOOTSTRAP_NODES", "")  # Lista di nodi bootstrap separati da virgola
OWN_URL = os.getenv("OWN_URL")
SUBSCRIBED_CHANNELS_ENV = os.getenv("SUBSCRIBED_CHANNELS", "")

# Verifica configurazione
if not OWN_URL:
    raise ValueError("La variabile d'ambiente OWN_URL è obbligatoria.")

# Determina modalità operativa
USE_P2P_MODE = (RENDEZVOUS_URL is None or RENDEZVOUS_URL == "")
if USE_P2P_MODE and not BOOTSTRAP_NODES:
    logging.warning("⚠️  Modalità P2P attiva ma nessun BOOTSTRAP_NODES configurato. Il nodo sarà isolato.")

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

# --- WebRTC Connection Manager ---
webrtc_manager = ConnectionManager(NODE_ID, RENDEZVOUS_URL if not USE_P2P_MODE else None)

# --- PubSub Manager ---
pubsub_manager = PubSubManager(NODE_ID, webrtc_manager)

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

@app.get("/webrtc/connections")
async def get_webrtc_connections():
    """Restituisce lo stato delle connessioni WebRTC"""
    connections_status = {}
    for peer_id, pc in webrtc_manager.connections.items():
        channel_state = "none"
        if peer_id in webrtc_manager.data_channels:
            channel_state = webrtc_manager.data_channels[peer_id].readyState

        connections_status[peer_id] = {
            "connection_state": pc.connectionState,
            "ice_connection_state": pc.iceConnectionState,
            "data_channel_state": channel_state
        }

    return {
        "total_connections": len(webrtc_manager.connections),
        "active_data_channels": len([
            dc for dc in webrtc_manager.data_channels.values()
            if dc.readyState == "open"
        ]),
        "connections": connections_status
    }

@app.get("/pubsub/stats")
async def get_pubsub_stats():
    """Restituisce statistiche sul protocollo PubSub"""
    return pubsub_manager.get_stats()

# --- Endpoint Bootstrap P2P ---

@app.post("/bootstrap/handshake")
async def bootstrap_handshake(peer_info: dict):
    """
    Endpoint per bootstrap P2P.
    Un nuovo nodo si connette qui per ottenere le informazioni
    necessarie per stabilire una connessione WebRTC.
    """
    peer_id = peer_info.get("peer_id")
    peer_url = peer_info.get("peer_url")

    if not peer_id or not peer_url:
        raise HTTPException(400, "peer_id e peer_url sono obbligatori")

    logging.info(f"🤝 Bootstrap handshake da {peer_id[:16]}...")

    # Aggiungi il peer ai known_peers
    known_peers.add(peer_url)

    # Restituisci informazioni su questo nodo e altri peer conosciuti
    return {
        "node_id": NODE_ID,
        "node_url": OWN_URL,
        "channels": list(subscribed_channels),
        "known_peers": list(known_peers)[:10]  # Max 10 peer
    }

@app.post("/p2p/signal/relay")
async def relay_signaling_message(msg: dict):
    """
    Relay di messaggi di signaling P2P.
    Quando un nodo A vuole connettersi a un nodo C ma non può contattarlo direttamente,
    invia il messaggio di signaling a un nodo B che conosce entrambi, chiedendo di inoltrarlo.
    """
    to_peer_id = msg.get("to_peer")
    from_peer_id = msg.get("from_peer")
    signal_type = msg.get("type")
    payload = msg.get("payload")

    if not all([to_peer_id, from_peer_id, signal_type, payload]):
        raise HTTPException(400, "Parametri incompleti")

    logging.info(f"📡 Relay signaling {signal_type} da {from_peer_id[:16]}... a {to_peer_id[:16]}...")

    # Prova a inviare via WebRTC se il destinatario è connesso
    if to_peer_id in webrtc_manager.data_channels:
        relay_msg = {
            "type": "SIGNAL_RELAY",
            "from_peer": from_peer_id,
            "signal_type": signal_type,
            "payload": payload
        }
        await webrtc_manager.send_message(to_peer_id, json.dumps(relay_msg))
        return {"status": "relayed"}

    # Altrimenti, prova a trovare il nodo via HTTP (fallback)
    for nid, ndata in network_state.get("global", {}).get("nodes", {}).items():
        if nid == to_peer_id:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.post(
                        f"{ndata['url']}/p2p/signal/receive",
                        json={
                            "from_peer": from_peer_id,
                            "type": signal_type,
                            "payload": payload
                        }
                    )
                    if response.status_code == 200:
                        return {"status": "relayed_http"}
            except Exception as e:
                logging.warning(f"Errore relay HTTP: {e}")

    raise HTTPException(404, "Destinatario non raggiungibile")

@app.post("/p2p/signal/receive")
async def receive_p2p_signaling(msg: dict):
    """
    Riceve un messaggio di signaling inoltrato da un altro peer.
    """
    from_peer = msg.get("from_peer")
    signal_type = msg.get("type")
    payload = msg.get("payload")

    logging.info(f"📥 Signaling P2P ricevuto da {from_peer[:16]}... (tipo: {signal_type})")

    # Gestisci il messaggio di signaling
    await webrtc_manager._handle_signaling_message(from_peer, signal_type, payload)

    return {"status": "processed"}

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

async def handle_pubsub_message(topic: str, payload: dict, sender_id: str):
    """Callback per messaggi SynapseSub ricevuti"""
    try:
        # Ricostruisci il pacchetto gossip dal payload
        if topic.startswith("channel:") and topic.endswith(":state"):
            # Estrai il channel_id dal topic (formato: "channel:sviluppo_ui:state")
            channel_id = topic.split(":")[1]

            # Il payload contiene lo stato del canale
            packet = GossipPacket(
                channel_id=channel_id,
                payload=json.dumps(payload),
                sender_id=sender_id,
                signature=""  # La firma è già stata verificata in WebRTC
            )

            await receive_gossip(packet)
            logging.info(f"📨 Stato '{channel_id}' ricevuto via PubSub da {sender_id[:16]}...")
    except Exception as e:
        logging.error(f"Errore gestione messaggio PubSub: {e}")

async def handle_peer_discovered(peer_id: str, channels: List[str]):
    """Callback quando un peer viene scoperto via PubSub"""
    logging.info(f"🔍 Peer scoperto via PubSub: {peer_id[:16]}... (canali: {channels})")

async def send_p2p_signal(to_peer_id: str, signal_type: str, payload: dict):
    """
    Callback per inviare messaggi di signaling in modalità P2P.
    Cerca un peer connesso che possa fare da relay.
    """
    # Cerca un peer connesso via WebRTC che possa fare da relay
    for relay_peer_id in webrtc_manager.data_channels.keys():
        if relay_peer_id != to_peer_id:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    # Trova l'URL del relay peer
                    relay_url = None
                    for nid, ndata in network_state.get("global", {}).get("nodes", {}).items():
                        if nid == relay_peer_id:
                            relay_url = ndata.get("url")
                            break

                    if relay_url:
                        response = await client.post(
                            f"{relay_url}/p2p/signal/relay",
                            json={
                                "from_peer": NODE_ID,
                                "to_peer": to_peer_id,
                                "type": signal_type,
                                "payload": payload
                            }
                        )
                        if response.status_code == 200:
                            logging.info(f"📡 Signaling inviato via relay {relay_peer_id[:16]}...")
                            return
            except Exception as e:
                logging.debug(f"Errore relay via {relay_peer_id[:16]}...: {e}")

    # Fallback: prova a contattare direttamente il peer via HTTP
    for nid, ndata in network_state.get("global", {}).get("nodes", {}).items():
        if nid == to_peer_id:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    await client.post(
                        f"{ndata['url']}/p2p/signal/receive",
                        json={
                            "from_peer": NODE_ID,
                            "type": signal_type,
                            "payload": payload
                        }
                    )
                    logging.info(f"📡 Signaling inviato direttamente a {to_peer_id[:16]}...")
                    return
            except Exception as e:
                logging.warning(f"Errore signaling diretto a {to_peer_id[:16]}...: {e}")

    logging.warning(f"Impossibile inviare signaling a {to_peer_id[:16]}... (nessun relay disponibile)")

async def handle_webrtc_message(peer_id: str, message: str):
    """Callback per messaggi ricevuti via WebRTC DataChannel"""
    try:
        data = json.loads(message)
        msg_type = data.get("type")

        # Controlla se è un messaggio SynapseSub
        if msg_type in [t.value for t in MessageType]:
            # Messaggio SynapseSub
            synapse_msg = SynapseSubMessage.from_json(message)
            pubsub_manager.handle_message(peer_id, synapse_msg)

        elif msg_type == "gossip":
            # Legacy: pacchetto gossip diretto via WebRTC
            packet = GossipPacket(**data["packet"])
            await receive_gossip(packet)
            logging.info(f"📨 Gossip ricevuto via WebRTC da {peer_id[:16]}...")
        else:
            logging.debug(f"Messaggio WebRTC sconosciuto: {msg_type}")
    except Exception as e:
        logging.error(f"Errore gestione messaggio WebRTC: {e}")

async def pubsub_gossip_loop():
    """Loop per pubblicare lo stato sui topic PubSub"""
    await asyncio.sleep(10)  # Aspetta che le connessioni WebRTC siano stabilite

    while True:
        try:
            # Pubblica lo stato su ogni canale sottoscritto
            for channel_id in subscribed_channels:
                if channel_id == "global":
                    continue  # Il global viene gestito diversamente

                # Topic formato: "channel:sviluppo_ui:state"
                topic = f"channel:{channel_id}:state"

                # Ottieni lo stato del canale
                async with state_lock:
                    if channel_id in network_state:
                        channel_state = json.loads(json.dumps(network_state[channel_id], default=list))

                        # Pubblica via PubSub
                        pubsub_manager.publish(topic, channel_state)

        except Exception as e:
            logging.error(f"Errore nel gossip PubSub: {e}")

        await asyncio.sleep(random.uniform(8, 12))

async def bootstrap_from_nodes():
    """Bootstrap iniziale da BOOTSTRAP_NODES"""
    if not BOOTSTRAP_NODES:
        return

    bootstrap_urls = [url.strip() for url in BOOTSTRAP_NODES.split(",") if url.strip()]

    for bootstrap_url in bootstrap_urls:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{bootstrap_url}/bootstrap/handshake",
                    json={
                        "peer_id": NODE_ID,
                        "peer_url": OWN_URL
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    bootstrap_node_id = data.get("node_id")
                    bootstrap_node_url = data.get("node_url")
                    discovered_peers = data.get("known_peers", [])

                    logging.info(f"🚀 Bootstrap con {bootstrap_node_id[:16]}... riuscito")

                    # Aggiungi bootstrap node ai known peers
                    known_peers.add(bootstrap_node_url)

                    # Aggiungi altri peer scoperti
                    for peer_url in discovered_peers:
                        if peer_url != OWN_URL:
                            known_peers.add(peer_url)

                    # Tenta connessione WebRTC con il bootstrap node
                    if bootstrap_node_id not in webrtc_manager.connections:
                        await webrtc_manager.connect_to_peer(bootstrap_node_id)

        except Exception as e:
            logging.warning(f"Bootstrap fallito con {bootstrap_url}: {e}")

async def network_maintenance_loop():
    await asyncio.sleep(5)

    # Bootstrap iniziale se in modalità P2P
    if USE_P2P_MODE:
        await bootstrap_from_nodes()

    while True:
        # Discovery via Rendezvous (se disponibile)
        if not USE_P2P_MODE:
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

        # Tenta connessioni WebRTC con i peer conosciuti
        if known_peers:
            peer_url = random.choice(list(known_peers))
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    # Ottieni l'ID del peer
                    state_response = await client.get(f"{peer_url}/state")
                    if state_response.status_code == 200:
                        peer_state = state_response.json()
                        # Trova il peer_id dal suo URL
                        for nid, ndata in peer_state.get("global", {}).get("nodes", {}).items():
                            if ndata.get("url") == peer_url:
                                peer_id = nid
                                # Stabilisci connessione WebRTC se non esiste
                                if peer_id not in webrtc_manager.connections:
                                    await webrtc_manager.connect_to_peer(peer_id)
                                    logging.info(f"🔗 Tentativo connessione WebRTC a {peer_id[:16]}...")
                                break

                    # Fallback HTTP gossip solo se WebRTC non disponibile
                    response = await client.get(f"{peer_url}/channels")
                    response.raise_for_status()
                    peer_channels = set(response.json())
                    common_channels = subscribed_channels.intersection(peer_channels)

                    for channel in common_channels:
                        packet = await create_signed_packet(channel)
                        if packet:
                            # Fallback a HTTP solo se necessario
                            gossip_response = await client.post(f"{peer_url}/gossip", json=packet)
                            gossip_response.raise_for_status()
                            response_packet = GossipPacket(**gossip_response.json())
                            await receive_gossip(response_packet)
            except httpx.RequestError as e:
                logging.warning(f"Gossip con {peer_url} fallito. Errore: {e}")
                known_peers.discard(peer_url)
            except Exception: pass

        # Cleanup messaggi vecchi in PubSub
        pubsub_manager.cleanup_old_messages()

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

    if USE_P2P_MODE:
        logging.info(f"🔗 Modalità P2P attiva (Bootstrap: {BOOTSTRAP_NODES or 'nessuno'})")
    else:
        logging.info(f"🔗 Modalità Rendezvous ({RENDEZVOUS_URL})")

    # Imposta callback WebRTC
    webrtc_manager.set_message_callback(handle_webrtc_message)

    # Imposta callback P2P signaling se in modalità P2P
    if USE_P2P_MODE:
        webrtc_manager.set_p2p_signal_callback(send_p2p_signal)

    # Imposta callback PubSub
    pubsub_manager.set_message_callback(handle_pubsub_message)
    pubsub_manager.set_peer_discovered_callback(handle_peer_discovered)

    # Sottoscrivi ai topic PubSub per ogni canale
    for channel_id in subscribed_channels:
        if channel_id != "global":
            topic = f"channel:{channel_id}:state"
            pubsub_manager.subscribe_topic(topic)

    # Sottoscrivi al discovery globale
    pubsub_manager.subscribe_topic("global-discovery")

    # Avvia WebRTC manager, network maintenance e PubSub gossip
    await webrtc_manager.start()
    asyncio.create_task(network_maintenance_loop())
    asyncio.create_task(pubsub_gossip_loop())

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
