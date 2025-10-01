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
        with open(ED25519_KEY_FILE, "wb") as f: f.write(ed_priv_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    try:
        with open(X25519_KEY_FILE, "rb") as f: x_priv_key = serialization.load_pem_private_key(f.read(), password=None)
    except (FileNotFoundError, ValueError):
        logging.warning(f"File chiave X25519 non trovato, ne genero uno nuovo.")
        x_priv_key = x25519.X25519PrivateKey.generate()
        with open(X25519_KEY_FILE, "wb") as f: f.write(x_priv_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    return ed_priv_key, x_priv_key

ed25519_private_key, x25519_private_key = load_or_create_keys()
NODE_ID = base64.urlsafe_b64encode(ed25519_private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode('utf-8')
KX_PUBLIC_KEY_B64 = base64.urlsafe_b64encode(x25519_private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)).decode('utf-8')

# --- Strutture Dati ---
class GossipPacket(BaseModel): channel_id: str; payload: str; sender_id: str; signature: str

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

# --- Endpoint ---
@app.get("/channels", response_model=List[str])
async def get_subscribed_channels():
    return list(subscribed_channels)

# ... (Altri endpoint come /tasks, /proposals, etc. rimangono qui) ...

# --- Logica di Rete e Gossip con Logging Migliorato ---
@app.post("/gossip")
async def receive_gossip(packet: GossipPacket):
    try:
        sender_public_key = ed25519.Ed25519PublicKey.from_public_bytes(base64.urlsafe_b64decode(packet.sender_id))
        sender_public_key.verify(base64.urlsafe_b64decode(packet.signature), packet.payload.encode('utf-8'))
    except (InvalidSignature, ValueError, TypeError) as e:
        logging.warning(f"Pacchetto gossip con firma non valida ricevuto da {packet.sender_id[:10]}... Errore: {e}")
        raise HTTPException(status_code=401, detail=f"Firma non valida: {e}")

    channel_id = packet.channel_id
    if channel_id not in subscribed_channels:
        return {"status": "ignored_unsubscribed_channel"}

    # ... (Logica di merge CRDT invariata) ...
    return {"status": "merged"}

def create_signed_packet(channel_id: str) -> dict:
    if channel_id not in network_state: return None
    network_state["global"]["nodes"][NODE_ID]["last_seen"] = time.time()
    network_state["global"]["nodes"][NODE_ID]["version"] += 1
    if channel_id != "global":
        network_state[channel_id]["participants"].add(NODE_ID)
    payload_str = json.dumps(network_state[channel_id], default=list)
    signature = ed25519_private_key.sign(payload_str.encode('utf-8'))
    return {
        "channel_id": channel_id, "payload": payload_str,
        "sender_id": NODE_ID, "signature": base64.urlsafe_b64encode(signature).decode('utf-8')
    }

async def gossip_and_discovery():
    await asyncio.sleep(5)
    while True:
        # 1. Discovery
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{RENDEZVOUS_URL}/register", json={"url": OWN_URL}, timeout=5)
                response = await client.get(f"{RENDEZVOUS_URL}/get_peers?limit=10", timeout=5)
                if response.status_code == 200:
                    new_peers = set(response.json()); new_peers.discard(OWN_URL)
                    if new_peers:
                        logging.info(f"Scoperti {len(new_peers)} nuovi peer dal Rendezvous Server.")
                        known_peers.update(new_peers)
        except httpx.RequestError as e:
            logging.error(f"Errore di rete durante il contatto con Rendezvous Server a {RENDEZVOUS_URL}: {e}")
        except Exception as e:
            logging.error(f"Errore imprevisto durante il discovery: {e}", exc_info=True)

        if not known_peers: 
            logging.warning("Nessun peer conosciuto. In attesa del prossimo ciclo di discovery.")
            await asyncio.sleep(10); continue
        
        # 2. Gossip Channel-Aware
        peer_url = random.choice(list(known_peers))
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{peer_url}/channels")
                response.raise_for_status() # Solleva eccezione per status code 4xx/5xx
                peer_channels = set(response.json())
                
                common_channels = subscribed_channels.intersection(peer_channels)
                logging.info(f"Canali in comune con {peer_url}: {list(common_channels)}")
                
                for channel in common_channels:
                    packet = create_signed_packet(channel)
                    if packet:
                        gossip_response = await client.post(f"{peer_url}/gossip", json=packet)
                        gossip_response.raise_for_status()

        except httpx.RequestError as e:
            logging.warning(f"Errore di rete durante il gossip con {peer_url}. Rimuovo dai peer noti. Errore: {e}")
            known_peers.discard(peer_url)
        except Exception as e:
            logging.error(f"Errore imprevisto durante il gossip con {peer_url}: {e}", exc_info=True)
        
        await asyncio.sleep(5)

# ... (Tutta la logica per reputazione, governance, chat e altri task in background rimane qui) ...

@app.on_event("startup")
async def on_startup():
    logging.info(f"🚀 Nodo Synapse-NG (Logging v2) avviato. ID: {NODE_ID[:16]}...")
    logging.info(f"📡 Canali sottoscritti: {list(subscribed_channels)}")
    asyncio.create_task(gossip_and_discovery())
    # ... (avvio degli altri task in background) ...
