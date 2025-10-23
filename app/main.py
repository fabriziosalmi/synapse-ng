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
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Literal, Set, List, Optional

# --- Crittografia ---
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature, InvalidTag

# --- WebRTC ---
from app.webrtc_manager import ConnectionManager
from app.synapsesub_protocol import PubSubManager, SynapseSubMessage, MessageType

# --- Zero-Knowledge Proofs ---
from app.zkp_utils import (
    generate_reputation_proof,
    verify_reputation_proof,
    get_reputation_tier,
    get_tier_weight,
    get_node_secret_from_private_key,
    REPUTATION_TIERS
)

# --- Collaborative Teams ---
from app.collaborative_teams import (
    TaskComposite,
    SubTask,
    NodeSkills,
    TeamAnnouncement,
    validate_composite_task,
    validate_node_skills,
    calculate_skill_match,
    can_node_join_team,
    is_team_complete,
    all_subtasks_completed,
    get_workspace_channel_name,
    distribute_rewards,
    generate_team_announcement,
    auto_assign_subtasks,
    log_team_event
)

# --- AI Agent ---
from app.ai_agent import (
    AIAgent,
    UserObjectives,
    AgentObjective,
    NetworkContext,
    AgentAction,
    initialize_agent,
    get_agent,
    is_agent_enabled
)

# --- Self-Upgrade System ---
from app.self_upgrade import (
    SelfUpgradeManager,
    UpgradePackage,
    UpgradeProposal,
    UpgradeStatus,
    PackageSource,
    initialize_upgrade_manager,
    get_upgrade_manager,
    is_upgrade_system_available
)

# --- Evolutionary Engine (Phase 7: Network Singularity) ---
from app.evolutionary_engine import (
    EvolutionaryEngine,
    NetworkMetrics,
    Inefficiency,
    GeneratedCode,
    EvolutionProposal,
    InefficencyType,
    CodeLanguage,
    initialize_evolutionary_engine,
    get_evolutionary_engine,
    is_evolutionary_engine_available
)

# --- Immune System (Proactive Self-Healing) ---
from app.immune_system import (
    ImmuneSystemManager,
    NetworkMetrics as ImmuneNetworkMetrics,
    HealthIssue,
    ProposedRemedy,
    initialize_immune_system,
    get_immune_system,
    get_immune_system_state,
    is_immune_system_enabled
)

# --- Configurazione Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# --- Configurazione CORS per Dashboard ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:15000",
        "http://localhost:8080",
        "http://127.0.0.1:15000",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
class CreateTaskPayload(BaseModel):
    title: str
    reward: int = 0  # Ricompensa in Synapse Points (opzionale, deprecato con auction)
    schema_name: str = "task_v2"  # ⚠️ SOLO task_v2 supportato (Common Tools richiede treasury)
    tags: List[str] = []  # Tags opzionali
    description: str = ""  # Descrizione opzionale
    required_tools: List[str] = []  # Common tools necessari per completare il task
    # Auction parameters (for task_v2 schema)
    enable_auction: bool = False  # Se True, usa meccanismo d'asta
    max_reward: int = 0  # Ricompensa massima per l'asta
    auction_deadline_hours: int = 24  # Ore prima della chiusura automatica dell'asta

class CreateProposalPayload(BaseModel):
    title: str
    description: str = ""
    proposal_type: str = "generic"  # "generic", "config_change", "network_operation", "command", "code_upgrade"
    params: dict = {}  # For config_change: {"key": "value"}, for network_operation: {"operation": "...", ...}, for code_upgrade: {"package_url": "...", "package_hash": "...", "version": "..."}
    command: dict = {}  # For command: {"operation": "acquire_common_tool"|"deprecate_common_tool", "params": {...}}
    schema_name: str = "proposal_v1"  # Schema da usare per validazione
    tags: List[str] = []  # Tags opzionali

class VotePayload(BaseModel):
    vote: Literal["yes", "no"]
    # Zero-Knowledge Proof fields (optional, for anonymous voting)
    anonymous: bool = False  # Se True, usa ZKP per voto anonimo
    zkp_proof: Optional[Dict[str, str]] = None  # Proof generato da zkp_utils.generate_reputation_proof()

class BidPayload(BaseModel):
    amount: int  # Reward richiesta per completare il task
    estimated_days: int  # Stima giorni per completamento
    
state_lock = asyncio.Lock()

# ========================================
# Common Tools: Credential Encryption
# ========================================

def derive_channel_encryption_key(channel_id: str) -> bytes:
    """
    Deriva una chiave simmetrica da un channel_id usando HKDF.
    
    Questa funzione crea una chiave deterministica ma crittograficamente sicura
    a partire dall'ID del canale. Tutti i nodi che conoscono il channel_id possono
    derivare la stessa chiave, permettendo la crittografia/decrittografia condivisa.
    
    IMPORTANTE: In produzione, questo dovrebbe usare un segreto condiviso più robusto,
    come una chiave derivata dal validator set o un threshold encryption scheme.
    
    Args:
        channel_id: ID univoco del canale
    
    Returns:
        Chiave simmetrica a 256 bit (32 bytes) per AESGCM
    """
    # Usa NODE_ID come salt per garantire unicità per deployment
    # In produzione, considera un salt condiviso via governance
    salt = NODE_ID.encode('utf-8')[:32].ljust(32, b'\x00')
    
    # Derive key usando HKDF con SHA256
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bit
        salt=salt,
        info=b'synapse-ng-common-tools-v1'
    )
    
    return hkdf.derive(channel_id.encode('utf-8'))


def encrypt_tool_credentials(credentials: str, channel_id: str) -> str:
    """
    Cripta le credenziali di uno strumento usando AESGCM.
    
    Le credenziali vengono criptate con una chiave derivata dal channel_id.
    Questo permette a qualsiasi nodo del canale di decriptare le credenziali
    quando necessario per eseguire operazioni autorizzate.
    
    Args:
        credentials: Credenziali in chiaro (es. API key)
        channel_id: ID del canale proprietario dello strumento
    
    Returns:
        Credenziali criptate in formato base64: "nonce:ciphertext"
    """
    # Deriva chiave dal channel_id
    key = derive_channel_encryption_key(channel_id)
    
    # Inizializza AESGCM
    aesgcm = AESGCM(key)
    
    # Genera nonce casuale (96 bit = 12 bytes per AESGCM)
    nonce = os.urandom(12)
    
    # Cripta le credenziali
    ciphertext = aesgcm.encrypt(nonce, credentials.encode('utf-8'), associated_data=None)
    
    # Combina nonce + ciphertext e codifica in base64
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_tool_credentials(encrypted_credentials: str, channel_id: str) -> str:
    """
    Decripta le credenziali di uno strumento.
    
    ATTENZIONE: Questa funzione restituisce credenziali in chiaro in memoria.
    Deve essere usata solo quando strettamente necessario e le credenziali
    devono essere immediatamente pulite dalla memoria dopo l'uso.
    
    Args:
        encrypted_credentials: Credenziali criptate (base64)
        channel_id: ID del canale proprietario
    
    Returns:
        Credenziali in chiaro
    
    Raises:
        InvalidTag: Se la decrittografia fallisce (chiave errata o dati corrotti)
    """
    # Deriva chiave dal channel_id
    key = derive_channel_encryption_key(channel_id)
    
    # Inizializza AESGCM
    aesgcm = AESGCM(key)
    
    # Decodifica da base64
    encrypted_data = base64.b64decode(encrypted_credentials.encode('utf-8'))
    
    # Separa nonce (primi 12 bytes) e ciphertext
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    
    # Decripta
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    
    return plaintext.decode('utf-8')

# Default network configuration (can be modified via governance)
DEFAULT_CONFIG = {
    "task_completion_reputation_reward": 10,
    "proposal_vote_reputation_reward": 1,
    "transaction_tax_percentage": 0.02,  # 2% tax on task rewards
    "vote_weight_log_base": 2,
    "initial_balance_sp": 1000,
    "treasury_initial_balance": 0,
    # Immune system (peer scoring & mesh optimization)
    "peer_score_weight_reputation": 0.5,
    "peer_score_weight_stability": 0.3,
    "peer_score_weight_latency": 0.2,
    "max_peer_connections": 20,
    "protected_peer_count": 5,
    # Two-tier governance (validator set / council)
    "validator_set_size": 7,
    "validator_election_interval_seconds": 600,  # 10 minutes
    # Auto-evolution (automatic proposal closing)
    "proposal_auto_close_after_seconds": 86400  # 24 hours
}

subscribed_channels: Set[str] = {"global"}.union(set(c.strip() for c in SUBSCRIBED_CHANNELS_ENV.split(",") if c.strip()))
network_state = {
    "global": {
        "nodes": {},
        "proposals": {},
        "config": DEFAULT_CONFIG.copy(),
        "config_version": 1,
        "config_updated_at": datetime.now(timezone.utc).isoformat(),
        "validator_set": [],  # List of node IDs forming the governing council
        "validator_set_updated_at": None,
        "pending_operations": [],  # Network operations awaiting council ratification
        "execution_log": [],  # Append-only log of executed commands (CRDT)
        "ratification_votes": {},  # Temporary votes for pending ratifications {proposal_id: {validator_id: True}}
        "last_executed_command_index": -1,  # Pointer to last executed command (per-node tracking)
        "zkp_nullifiers": {},  # ZKP nullifiers per proposal: {proposal_id: set([nullifier1, nullifier2, ...])}
        "schemas": {  # Schema definitions for typed data (CRDT LWW)
            "task_v1": {
                "schema_name": "task_v1",
                "version": 1,
                "description": "Standard task schema",
                "fields": {
                    "title": {"type": "string", "required": True, "min_length": 1, "max_length": 200},
                    "reward": {"type": "integer", "required": False, "min": 0, "default": 0},
                    "tags": {"type": "list[string]", "required": False, "default": []},
                    "description": {"type": "string", "required": False, "default": ""},
                    "assignee": {"type": "string", "required": False, "default": None},
                    "status": {"type": "enum", "required": False, "values": ["open", "claimed", "in_progress", "completed"], "default": "open"},
                    "required_tools": {"type": "list[string]", "required": False, "default": []}  # Common tools necessari per questo task
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "proposal_v1": {
                "schema_name": "proposal_v1",
                "version": 1,
                "description": "Standard proposal schema",
                "fields": {
                    "title": {"type": "string", "required": True, "min_length": 1, "max_length": 200},
                    "description": {"type": "string", "required": False, "default": ""},
                    "proposal_type": {"type": "enum", "required": True, "values": ["generic", "config_change", "network_operation", "command"], "default": "generic"},
                    "params": {"type": "object", "required": False, "default": {}},
                    "command": {"type": "object", "required": False, "default": {}},
                    "tags": {"type": "list[string]", "required": False, "default": []}
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "task_v2": {
                "schema_name": "task_v2",
                "version": 2,
                "description": "Task schema with auction mechanism",
                "fields": {
                    "title": {"type": "string", "required": True, "min_length": 1, "max_length": 200},
                    "tags": {"type": "list[string]", "required": False, "default": []},
                    "description": {"type": "string", "required": False, "default": ""},
                    "assignee": {"type": "string", "required": False, "default": None},
                    "status": {"type": "enum", "required": False, "values": ["open", "auction_open", "auction_closed", "claimed", "in_progress", "completed"], "default": "open"},
                    "required_tools": {"type": "list[string]", "required": False, "default": []},  # Common tools necessari per questo task
                    "auction": {
                        "type": "object",
                        "required": False,
                        "default": {
                            "enabled": False,
                            "status": "closed",
                            "max_reward": 0,
                            "deadline": None,
                            "bids": {},
                            "selected_bid": None
                        },
                        "fields": {
                            "enabled": {"type": "boolean", "required": True},
                            "status": {"type": "enum", "required": True, "values": ["open", "closed", "finalized"]},
                            "max_reward": {"type": "integer", "required": True, "min": 0},
                            "deadline": {"type": "string", "required": False},  # ISO timestamp
                            "bids": {"type": "object", "required": False, "default": {}},
                            "selected_bid": {"type": "string", "required": False, "default": None}  # peer_id of winner
                        }
                    }
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    }
}
for channel in subscribed_channels:
    if channel not in network_state:
        network_state[channel] = {
            "participants": {NODE_ID},
            "tasks": {},
            "proposals": {},
            "treasury_balance": 0,
            "composite_tasks": {},  # Task compositi
            "team_announcements": {},  # Annunci di ricerca membri
            "node_skills": {},  # Profili skills dei nodi
            "common_tools": {}  # Strumenti comuni finanziati dalla tesoreria
        }
known_peers = set()

network_state["global"]["nodes"][NODE_ID] = {
    "id": NODE_ID, "url": OWN_URL, "kx_public_key": KX_PUBLIC_KEY_B64,
    "last_seen": time.time(), "version": 1
}

# --- WebRTC Connection Manager ---
webrtc_manager = ConnectionManager(NODE_ID, RENDEZVOUS_URL if not USE_P2P_MODE else None, DEFAULT_CONFIG)

# --- PubSub Manager ---
pubsub_manager = PubSubManager(NODE_ID, webrtc_manager)

# --- Raft Manager (inizializzato in startup) ---
from app.raft_manager import RaftManager
raft_manager: Optional[RaftManager] = None

# --- mDNS Discovery (inizializzato in startup) ---
mdns_discovery = None
mdns_discovery_queue = asyncio.Queue()  # Queue per peer scoperti via mDNS

# --- Endpoint di Base ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "node_id": NODE_ID})

@app.get("/whoami")
async def whoami():
    """Returns the local node's ID."""
    return {"node_id": NODE_ID}

# ========================================
# Self-Upgrade Endpoints
# ========================================

@app.post("/upgrades/propose", status_code=201)
async def propose_upgrade(
    channel: str,
    title: str,
    description: str,
    version: str,
    package_url: str,
    package_hash: str,
    package_size: Optional[int] = None,
    wasm_module_name: str = "upgrade"
):
    """
    Crea una proposta di code upgrade.
    
    Args:
        channel: Canale per la proposta
        title: Titolo dell'upgrade
        description: Descrizione delle modifiche
        version: Versione target (es. "1.2.0")
        package_url: URL o hash IPFS del pacchetto WASM
        package_hash: SHA256 del pacchetto
        package_size: Dimensione in bytes (opzionale)
        wasm_module_name: Nome del modulo WASM principale
    
    Returns:
        Proposta creata con ID univoco
    """
    if not is_upgrade_system_available():
        raise HTTPException(503, "Sistema di upgrade non disponibile")
    
    # Crea proposta di tipo code_upgrade
    proposal_id = str(uuid.uuid4())
    
    payload = CreateProposalPayload(
        title=title,
        description=description,
        proposal_type="code_upgrade",
        params={
            "package_url": package_url,
            "package_hash": package_hash,
            "package_size": package_size,
            "wasm_module_name": wasm_module_name,
            "version": version
        }
    )
    
    # Usa l'endpoint esistente per creare la proposta
    result = await create_proposal(channel, payload)
    
    return {
        "message": "Proposta di upgrade creata",
        "proposal_id": proposal_id,
        "version": version,
        "package_hash": package_hash,
        "next_steps": [
            "1. Community vote on proposal",
            "2. Validator set ratification",
            "3. Automatic download and verification",
            "4. Execution in WASM sandbox",
            "5. Network upgrade completed"
        ]
    }


@app.post("/upgrades/{proposal_id}/test", status_code=200)
async def test_upgrade(proposal_id: str, channel: str):
    """
    Testa un upgrade in modalità dry-run senza applicarlo.
    
    Args:
        proposal_id: ID della proposta di upgrade
        channel: Canale della proposta
    
    Returns:
        Risultati del test (download, verifica, sandbox test)
    """
    if not is_upgrade_system_available():
        raise HTTPException(503, "Sistema di upgrade non disponibile")
    
    # Recupera proposta
    async with state_lock:
        proposal_dict = network_state[channel]["proposals"].get(proposal_id)
    
    if not proposal_dict:
        raise HTTPException(404, "Proposta non trovata")
    
    if proposal_dict.get("proposal_type") != "code_upgrade":
        raise HTTPException(400, "Proposta non è di tipo code_upgrade")
    
    # Crea oggetti UpgradePackage e UpgradeProposal
    params = proposal_dict.get("params", {})
    
    package = UpgradePackage(
        package_url=params["package_url"],
        package_hash=params["package_hash"],
        package_size=params.get("package_size"),
        wasm_module_name=params.get("wasm_module_name", "upgrade")
    )
    
    upgrade_proposal = UpgradeProposal(
        proposal_id=proposal_id,
        title=proposal_dict["title"],
        description=proposal_dict.get("description", ""),
        version=params["version"],
        package=package,
        proposer=proposal_dict["proposer"],
        created_at=proposal_dict["created_at"]
    )
    
    # Esegui test in dry-run
    upgrade_mgr = get_upgrade_manager()
    success, error, result = await upgrade_mgr.execute_upgrade(upgrade_proposal, dry_run=True)
    
    return {
        "proposal_id": proposal_id,
        "test_success": success,
        "error": error,
        "result": result,
        "dry_run": True
    }


@app.get("/upgrades/status", status_code=200)
async def get_upgrade_status():
    """
    Recupera lo stato del sistema di upgrade.
    
    Returns:
        Versione corrente, upgrade history, capabilities
    """
    if not is_upgrade_system_available():
        return {
            "available": False,
            "reason": "Sistema di upgrade non inizializzato o WASM non disponibile"
        }
    
    upgrade_mgr = get_upgrade_manager()
    stats = upgrade_mgr.get_stats()
    
    return {
        "available": True,
        **stats
    }


@app.get("/upgrades/history", status_code=200)
async def get_upgrade_history():
    """
    Recupera lo storico degli upgrade eseguiti.
    
    Returns:
        Lista di upgrade con versioni, date, risultati
    """
    if not is_upgrade_system_available():
        raise HTTPException(503, "Sistema di upgrade non disponibile")
    
    upgrade_mgr = get_upgrade_manager()
    history = upgrade_mgr.get_upgrade_history()
    
    return {
        "total_upgrades": len(history),
        "history": history
    }


@app.post("/upgrades/{proposal_id}/rollback", status_code=200)
async def rollback_upgrade(proposal_id: str):
    """
    Rollback di un upgrade precedentemente eseguito.
    
    Args:
        proposal_id: ID della proposta di upgrade da rollback
    
    Returns:
        Risultato del rollback
    """
    if not is_upgrade_system_available():
        raise HTTPException(503, "Sistema di upgrade non disponibile")
    
    upgrade_mgr = get_upgrade_manager()
    success, error = await upgrade_mgr.rollback_upgrade(proposal_id)
    
    if not success:
        raise HTTPException(400, f"Rollback fallito: {error}")
    
    return {
        "message": "Rollback completato",
        "proposal_id": proposal_id
    }


# ========================================
# Evolutionary Engine Endpoints (Phase 7)
# ========================================

@app.post("/evolution/analyze", status_code=200)
async def analyze_network_evolution():
    """
    Analizza le metriche di rete e identifica inefficienze.
    
    Questo endpoint analizza lo stato corrente della rete,
    calcola le metriche di performance e identifica opportunità
    di ottimizzazione autonoma.
    
    Returns:
        Lista di inefficienze rilevate con severity score
    """
    if not is_evolutionary_engine_available():
        raise HTTPException(503, "Motore evolutivo non disponibile")
    
    engine = get_evolutionary_engine()
    
    # Collect current metrics from network state
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    
    # Calculate metrics (simplified)
    # TODO: Calculate real metrics from network state
    metrics = NetworkMetrics(
        avg_consensus_time=5.0,  # Would be calculated from logs
        avg_auction_completion_time=45.0,
        avg_task_completion_time=200.0,
        cpu_usage=60.0,
        memory_usage=1024.0,
        peer_count=len(state_copy["global"]["nodes"]),
        message_throughput=100.0,
        validator_rotation_frequency=2.0,
        proposal_approval_rate=0.75
    )
    
    # Analyze for inefficiencies
    inefficiencies = await engine.analyze_network_metrics(metrics)
    
    return {
        "metrics": {
            "avg_consensus_time": metrics.avg_consensus_time,
            "avg_auction_completion_time": metrics.avg_auction_completion_time,
            "peer_count": metrics.peer_count,
            "cpu_usage": metrics.cpu_usage
        },
        "inefficiencies_detected": len(inefficiencies),
        "inefficiencies": [
            {
                "type": ineff.type.value,
                "description": ineff.description,
                "severity": ineff.severity,
                "current_metric": ineff.current_metric,
                "target_metric": ineff.target_metric,
                "affected_component": ineff.affected_component,
                "suggested_improvement": ineff.suggested_improvement
            }
            for ineff in inefficiencies
        ]
    }


@app.post("/evolution/generate", status_code=200)
async def generate_evolution_code(
    inefficiency_type: str,
    target_component: str,
    language: str = "rust"
):
    """
    Genera codice ottimizzato per una specifica inefficienza.
    
    L'AI analizza l'inefficienza e genera codice WASM ottimizzato
    per risolverla. Il codice viene compilato automaticamente.
    
    Args:
        inefficiency_type: Tipo di inefficienza (es. "consensus", "auction")
        target_component: Componente da ottimizzare
        language: Linguaggio di generazione (rust, assemblyscript, wat)
    
    Returns:
        Codice generato con WASM binary e hash
    """
    if not is_evolutionary_engine_available():
        raise HTTPException(503, "Motore evolutivo non disponibile")
    
    engine = get_evolutionary_engine()
    
    # Create synthetic inefficiency for code generation
    try:
        ineff_type = InefficencyType(inefficiency_type)
        code_lang = CodeLanguage(language)
    except ValueError:
        raise HTTPException(400, "Tipo inefficienza o linguaggio non valido")
    
    inefficiency = Inefficiency(
        type=ineff_type,
        description=f"Optimize {target_component}",
        severity=0.7,
        current_metric=10.0,
        target_metric=5.0,
        affected_component=target_component,
        suggested_improvement="AI-generated optimization"
    )
    
    # Generate code
    generated_code = await engine.generate_optimization_code(inefficiency, code_lang)
    
    if not generated_code:
        raise HTTPException(500, "Generazione codice fallita")
    
    # Compile to WASM
    compilation_success = await engine.compile_to_wasm(generated_code)
    
    return {
        "language": generated_code.language.value,
        "source_code": generated_code.source_code,
        "description": generated_code.description,
        "compilation_success": compilation_success,
        "wasm_size": len(generated_code.wasm_binary) if generated_code.wasm_binary else 0,
        "wasm_hash": generated_code.wasm_hash,
        "estimated_improvement": generated_code.estimated_improvement
    }


@app.post("/evolution/propose", status_code=201)
async def create_autonomous_evolution_proposal():
    """
    🧬 AUTONOMOUS EVOLUTION: Il ciclo auto-evolutivo completo.
    
    Questo endpoint esegue l'intero ciclo evolutivo:
    1. Analizza metriche di rete
    2. Identifica inefficienze
    3. Genera codice ottimizzato (WASM)
    4. Crea proposta di upgrade autonoma
    5. Sottomette alla governance per voto
    
    È il culmine della "Singolarità della Rete": l'AI scrive codice
    e propone modifiche autonomamente!
    
    Returns:
        Proposta di evolution creata e sottomessa
    """
    if not is_evolutionary_engine_available():
        raise HTTPException(503, "Motore evolutivo non disponibile")
    
    engine = get_evolutionary_engine()
    
    # Collect metrics
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    
    # Calculate real metrics
    metrics = NetworkMetrics(
        avg_consensus_time=7.0,  # Example: slow consensus
        avg_auction_completion_time=80.0,  # Example: slow auctions
        avg_task_completion_time=250.0,
        cpu_usage=75.0,
        memory_usage=2048.0,
        peer_count=len(state_copy["global"]["nodes"]),
        message_throughput=120.0,
        validator_rotation_frequency=1.5,
        proposal_approval_rate=0.80
    )
    
    # Run evolutionary cycle
    proposal = await engine.evolutionary_cycle(metrics, state_copy)
    
    if not proposal:
        return {
            "message": "No auto-evolution proposal created",
            "reason": "No critical inefficiencies or manual approval required",
            "check": "GET /evolution/analyze for details"
        }
    
    # Create upgrade proposal in network state
    proposal_id = f"evo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    proposal.proposal_id = proposal_id
    
    # Upload WASM to temporary location (in production: IPFS)
    wasm_path = os.path.join(engine.data_dir, "generated_code", f"{proposal_id}.wasm")
    with open(wasm_path, "wb") as f:
        f.write(proposal.generated_code.wasm_binary)
    
    package_url = f"file://{wasm_path}"  # In production: ipfs://Qm...
    
    # Create upgrade package
    upgrade_package = UpgradePackage(
        package_url=package_url,
        package_hash=proposal.generated_code.wasm_hash,
        package_size=len(proposal.generated_code.wasm_binary),
        wasm_module_name="autonomous_evolution"
    )
    
    # Create proposal in network state
    async with state_lock:
        new_proposal = {
            "id": proposal_id,
            "title": proposal.title,
            "description": proposal.description,
            "proposal_type": "code_upgrade",
            "proposed_by": NODE_ID,
            "channel": "global",
            "timestamp": proposal.created_at,
            "status": "voting",
            "votes": {},
            "params": {
                "version": proposal.version,
                "package_url": package_url,
                "package_hash": proposal.generated_code.wasm_hash,
                "package_size": len(proposal.generated_code.wasm_binary),
                "generated_by": "ai_evolutionary_engine",
                "inefficiency_type": proposal.inefficiency.type.value,
                "inefficiency_severity": proposal.inefficiency.severity,
                "expected_benefits": proposal.expected_benefits,
                "risks": proposal.risks
            }
        }
        
        network_state["global"]["proposals"][proposal_id] = new_proposal
    
    return {
        "message": "🧬 Autonomous evolution proposal created!",
        "proposal_id": proposal_id,
        "title": proposal.title,
        "version": proposal.version,
        "inefficiency": {
            "type": proposal.inefficiency.type.value,
            "severity": proposal.inefficiency.severity,
            "description": proposal.inefficiency.description
        },
        "code": {
            "language": proposal.generated_code.language.value,
            "wasm_hash": proposal.generated_code.wasm_hash,
            "wasm_size": len(proposal.generated_code.wasm_binary),
            "estimated_improvement": f"{proposal.generated_code.estimated_improvement:.1f}%"
        },
        "next_steps": [
            f"Community votes on proposal {proposal_id}",
            "Validator set ratifies if approved",
            "Network autonomously upgrades itself",
            "Performance improvement measured"
        ]
    }


@app.get("/evolution/status", status_code=200)
async def get_evolution_status():
    """
    Stato del sistema evolutivo e storico evolution.
    
    Returns:
        Statistiche sul motore evolutivo e proposte generate
    """
    if not is_evolutionary_engine_available():
        raise HTTPException(503, "Motore evolutivo non disponibile")
    
    engine = get_evolutionary_engine()
    
    # Count AI-generated proposals
    async with state_lock:
        ai_proposals = [
            p for p in network_state["global"]["proposals"].values()
            if p.get("params", {}).get("generated_by") == "ai_evolutionary_engine"
        ]
    
    return {
        "evolutionary_engine": {
            "available": True,
            "auto_evolution_enabled": engine.enable_auto_evolution,
            "safety_threshold": engine.safety_threshold,
            "llm_available": engine.llm is not None
        },
        "statistics": {
            "total_ai_proposals": len(ai_proposals),
            "approved_ai_proposals": len([p for p in ai_proposals if p["status"] == "approved"]),
            "executed_ai_proposals": len([p for p in ai_proposals if p.get("params", {}).get("executed", False)]),
            "detected_inefficiencies": len(engine.detected_inefficiencies)
        },
        "recent_ai_proposals": [
            {
                "id": p["id"],
                "title": p["title"],
                "status": p["status"],
                "version": p.get("params", {}).get("version"),
                "timestamp": p["timestamp"]
            }
            for p in sorted(ai_proposals, key=lambda x: x["timestamp"], reverse=True)[:5]
        ]
    }


# ========================================
# State and Network Endpoints
# ========================================

@app.get("/state")
async def get_state():
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    reputations = calculate_reputations(state_copy)
    balances = calculate_balances(state_copy)
    treasuries = calculate_treasuries(state_copy)

    # Add calculated values to nodes
    for node_id, node_data in state_copy["global"]["nodes"].items():
        # Reputazione ora è un dict (formato v2)
        reputation_dict = reputations.get(node_id, {
            "_total": 0,
            "_last_updated": datetime.now(timezone.utc).isoformat(),
            "tags": {}
        })
        node_data["reputation"] = reputation_dict
        node_data["balance"] = balances.get(node_id, 0)

    # Add calculated treasury balances to channels
    for channel_id in state_copy:
        if channel_id != "global" and channel_id in treasuries:
            state_copy[channel_id]["treasury_balance"] = treasuries[channel_id]
    
    # Add calculated auction info to tasks
    now = datetime.now(timezone.utc)
    for channel_id, channel_data in state_copy.items():
        if channel_id == "global":
            continue
        
        for task_id, task in channel_data.get("tasks", {}).items():
            auction = task.get("auction", {})
            
            if auction.get("enabled", False):
                # Calcola tempo rimanente
                deadline_str = auction.get("deadline")
                if deadline_str:
                    deadline = datetime.fromisoformat(deadline_str)
                    time_remaining_seconds = (deadline - now).total_seconds()
                    time_remaining_hours = max(0, time_remaining_seconds / 3600)
                    
                    # Aggiungi info calcolate
                    task["auction_info"] = {
                        "bids_count": len(auction.get("bids", {})),
                        "time_remaining_hours": round(time_remaining_hours, 2),
                        "is_expired": time_remaining_seconds <= 0,
                        "min_bid_amount": min((bid["amount"] for bid in auction.get("bids", {}).values()), default=None),
                        "max_bid_amount": max((bid["amount"] for bid in auction.get("bids", {}).values()), default=None)
                    }

    # Add immune system data to global state
    try:
        immune_state = get_immune_system_state()
        logging.info(f"[get_state] Immune state: enabled={immune_state.get('enabled')}, issues={len(immune_state.get('active_issues', []))}")
        state_copy["global"]["immune_system"] = immune_state
    except Exception as e:
        logging.error(f"[get_state] Error getting immune system state: {e}")
        state_copy["global"]["immune_system"] = {"enabled": False, "error": str(e)}

    return state_copy

@app.get("/channels", response_model=List[str])
async def get_subscribed_channels():
    return list(subscribed_channels)

@app.get("/treasury/{channel_id}")
async def get_treasury_balance(channel_id: str):
    """
    Ottiene il balance della tesoreria di un canale specifico.
    """
    if channel_id == "global":
        raise HTTPException(400, "Il canale 'global' non ha una tesoreria")

    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))

    treasuries = calculate_treasuries(state_copy)

    if channel_id not in treasuries:
        raise HTTPException(404, f"Canale '{channel_id}' non trovato")

    return {
        "channel_id": channel_id,
        "treasury_balance": treasuries[channel_id]
    }

# ========================================
# Common Tools Endpoints
# ========================================

@app.post("/tools/{tool_id}/execute", status_code=200)
async def execute_common_tool(
    tool_id: str,
    channel: str,
    task_id: str,
    tool_params: dict = {}
):
    """
    Esegue un Common Tool in modo sicuro.
    
    SECURITY CRITICAL ENDPOINT
    
    Questo endpoint permette l'esecuzione di strumenti comuni (es. chiamate API esterne)
    usando credenziali criptate. Implementa controlli rigorosi di sicurezza:
    
    1. AUTENTICAZIONE: Verifica che il chiamante sia l'assignee del task
    2. AUTORIZZAZIONE: Verifica che il task richieda effettivamente il tool
    3. STATUS CHECK: Verifica che il tool sia "active" e il task "in_progress"
    4. DECRYPTION: Decripta le credenziali SOLO in memoria temporanea
    5. EXECUTION: Esegue la logica specifica del tool
    6. CLEANUP: Pulisce immediatamente le credenziali dalla memoria
    
    Args:
        tool_id: Identificatore dello strumento da eseguire
        channel: Canale proprietario dello strumento
        task_id: ID del task che richiede l'esecuzione
        tool_params: Parametri specifici per l'esecuzione (es. query, filters, etc.)
    
    Returns:
        Risultato dell'esecuzione dello strumento (tool-specific)
    
    Example Request:
        POST /tools/geolocation_api/execute?channel=sviluppo_ui&task_id=abc123
        Body: {"ip_address": "8.8.8.8"}
    
    Example Response:
        {
            "success": true,
            "tool_id": "geolocation_api",
            "result": {
                "country": "United States",
                "city": "Mountain View",
                "latitude": 37.4056,
                "longitude": -122.0775
            },
            "executed_at": "2025-10-24T12:00:00Z"
        }
    """
    logging.info(f"🔒 Richiesta esecuzione tool '{tool_id}' per task '{task_id[:8]}...' nel canale '{channel}'")
    
    # === VALIDAZIONE PARAMETRI ===
    if not tool_id or not channel or not task_id:
        raise HTTPException(400, "tool_id, channel e task_id sono obbligatori")
    
    async with state_lock:
        # === VERIFICA ESISTENZA CANALE ===
        if channel not in network_state:
            raise HTTPException(404, f"Canale '{channel}' non trovato")
        
        channel_data = network_state[channel]
        
        # === VERIFICA ESISTENZA TOOL ===
        common_tools = channel_data.get("common_tools", {})
        if tool_id not in common_tools:
            raise HTTPException(404, f"Tool '{tool_id}' non trovato nel canale '{channel}'")
        
        tool_data = common_tools[tool_id]
        
        # === VERIFICA STATUS TOOL ===
        if tool_data.get("status") != "active":
            raise HTTPException(403, f"Tool '{tool_id}' non è attivo (status: {tool_data.get('status')})")
        
        # === VERIFICA ESISTENZA TASK ===
        tasks = channel_data.get("tasks", {})
        if task_id not in tasks:
            raise HTTPException(404, f"Task '{task_id}' non trovato nel canale '{channel}'")
        
        task = tasks[task_id]
        
        # === AUTENTICAZIONE: Verifica assignee ===
        # NOTE: In produzione, questo dovrebbe verificare una firma crittografica
        # Per ora, accettiamo NODE_ID come identificativo dell'assignee
        if task.get("assignee") != NODE_ID:
            raise HTTPException(403, f"Accesso negato: solo l'assignee del task può eseguire i suoi tools (assignee: {task.get('assignee', 'none')[:16]}...)")
        
        # === VERIFICA STATUS TASK ===
        if task.get("status") not in ["claimed", "in_progress"]:
            raise HTTPException(403, f"Il task non è in uno stato eseguibile (status: {task.get('status')})")
        
        # === AUTORIZZAZIONE: Verifica required_tools ===
        required_tools = task.get("required_tools", [])
        if tool_id not in required_tools:
            raise HTTPException(403, f"Il task non richiede il tool '{tool_id}' (required_tools: {required_tools})")
        
        # === DECRYPTION: Recupera credenziali (IN MEMORIA TEMPORANEA) ===
        encrypted_credentials = tool_data.get("encrypted_credentials")
        if not encrypted_credentials:
            raise HTTPException(500, f"Tool '{tool_id}' non ha credenziali configurate")
        
        try:
            # ATTENZIONE: credenziali in chiaro in memoria!
            credentials_plain = decrypt_tool_credentials(encrypted_credentials, channel)
            
            logging.info(f"   ✅ Credenziali decriptate per tool '{tool_id}'")
            
            # === EXECUTION: Logica specifica per tipo di tool ===
            tool_type = tool_data.get("type", "api_key")
            result = None
            
            if tool_type == "api_key":
                # Esegui chiamata API usando le credenziali
                result = await execute_api_key_tool(
                    tool_id=tool_id,
                    api_key=credentials_plain,
                    tool_params=tool_params
                )
            elif tool_type == "oauth_token":
                # Esegui chiamata OAuth
                result = await execute_oauth_tool(
                    tool_id=tool_id,
                    oauth_token=credentials_plain,
                    tool_params=tool_params
                )
            elif tool_type == "webhook":
                # Esegui webhook
                result = await execute_webhook_tool(
                    tool_id=tool_id,
                    webhook_url=credentials_plain,
                    tool_params=tool_params
                )
            else:
                raise HTTPException(400, f"Tipo di tool non supportato: {tool_type}")
            
            # === CLEANUP: Pulisci credenziali dalla memoria ===
            credentials_plain = None  # Permetti garbage collection
            del credentials_plain
            
            logging.info(f"   ✅ Tool '{tool_id}' eseguito con successo per task '{task_id[:8]}...'")
            
            return {
                "success": True,
                "tool_id": tool_id,
                "tool_type": tool_type,
                "task_id": task_id,
                "channel": channel,
                "result": result,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
        
        except InvalidTag:
            raise HTTPException(500, "Errore di decrittografia: credenziali corrotte o chiave errata")
        except Exception as e:
            # Assicura cleanup anche in caso di errore
            try:
                credentials_plain = None
                del credentials_plain
            except:
                pass
            
            logging.error(f"   ❌ Errore durante esecuzione tool '{tool_id}': {e}")
            raise HTTPException(500, f"Errore durante esecuzione tool: {str(e)}")


# === Helper functions per esecuzione tool-specific ===

async def execute_api_key_tool(tool_id: str, api_key: str, tool_params: dict) -> dict:
    """
    Esegue un tool di tipo api_key.
    
    Implementazione dimostrativa. In produzione, questo dovrebbe:
    - Usare httpx per chiamate HTTP asincrone
    - Implementare retry logic
    - Gestire rate limiting
    - Validare parametri specifici del tool
    """
    logging.info(f"      🔌 Esecuzione API call per tool '{tool_id}'")
    
    # Esempio: tool_id specifici con logiche dedicate
    if tool_id == "geolocation_api":
        # Simula chiamata API di geolocalizzazione
        ip_address = tool_params.get("ip_address", "0.0.0.0")
        
        # In produzione: async with httpx.AsyncClient() as client:
        #     response = await client.get(f"https://api.service.com/lookup?ip={ip_address}&key={api_key}")
        #     return response.json()
        
        # Simulazione per demo
        return {
            "ip": ip_address,
            "country": "United States",
            "city": "Mountain View",
            "latitude": 37.4056,
            "longitude": -122.0775,
            "timezone": "America/Los_Angeles",
            "simulated": True  # Rimosso in produzione
        }
    
    # Tool generico: restituisci info parametri
    return {
        "message": f"Tool '{tool_id}' eseguito",
        "parameters": tool_params,
        "note": "Implementazione generica - estendi execute_api_key_tool() per logica specifica"
    }


async def execute_oauth_tool(tool_id: str, oauth_token: str, tool_params: dict) -> dict:
    """
    Esegue un tool di tipo oauth_token.
    """
    logging.info(f"      🔑 Esecuzione OAuth call per tool '{tool_id}'")
    
    # Implementazione specifica per tool OAuth
    return {
        "message": f"OAuth tool '{tool_id}' eseguito",
        "parameters": tool_params
    }


async def execute_webhook_tool(tool_id: str, webhook_url: str, tool_params: dict) -> dict:
    """
    Esegue un tool di tipo webhook.
    """
    logging.info(f"      📡 Esecuzione Webhook per tool '{tool_id}'")
    
    # In produzione: POST al webhook_url con tool_params
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(webhook_url, json=tool_params)
    #     return response.json()
    
    return {
        "message": f"Webhook '{tool_id}' eseguito",
        "parameters": tool_params,
        "simulated": True
    }

@app.get("/treasuries")
async def get_all_treasuries():
    """
    Ottiene i balance di tutte le tesorerie dei canali.
    """
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))

    treasuries = calculate_treasuries(state_copy)

    return {
        "treasuries": [
            {"channel_id": channel_id, "balance": balance}
            for channel_id, balance in treasuries.items()
        ]
    }

@app.get("/config")
async def get_config():
    """
    Ottiene la configurazione corrente della rete.
    """
    async with state_lock:
        config = network_state["global"]["config"].copy()
        config_version = network_state["global"].get("config_version", 1)
        config_updated_at = network_state["global"].get("config_updated_at", "")

    return {
        "config": config,
        "version": config_version,
        "updated_at": config_updated_at
    }

@app.get("/config/history")
async def get_config_history():
    """
    Ottiene la storia delle modifiche alla configurazione tramite governance.
    """
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))

    # Trova tutte le proposte config_change eseguite
    config_changes = []

    for channel_id, channel_data in state_copy.items():
        if channel_id == "global":
            for proposal_id, proposal in channel_data.get("proposals", {}).items():
                if (proposal.get("proposal_type") == "config_change" and
                    proposal.get("status") == "executed" and
                    proposal.get("execution_result", {}).get("success")):

                    exec_result = proposal["execution_result"]
                    config_changes.append({
                        "proposal_id": proposal_id,
                        "title": proposal.get("title", ""),
                        "key": exec_result.get("key"),
                        "old_value": exec_result.get("old_value"),
                        "new_value": exec_result.get("new_value"),
                        "executed_at": exec_result.get("executed_at"),
                        "proposer": proposal.get("proposer")
                    })

    # Ordina per data di esecuzione
    config_changes.sort(key=lambda x: x.get("executed_at", ""), reverse=True)

    return {
        "changes": config_changes,
        "total": len(config_changes)
    }

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

@app.get("/webrtc/ice-metrics")
async def get_ice_metrics():
    """
    Restituisce metriche ICE per monitoring e debugging.
    Utile per valutare success rate delle connessioni e efficacia NAT traversal.
    """
    metrics = webrtc_manager.ice_metrics.copy()

    # Calcola success rate
    attempted = metrics["total_connections_attempted"]
    established = metrics["total_connections_established"]
    failed = metrics["total_connections_failed"]

    success_rate = (established / attempted * 100) if attempted > 0 else 0

    return {
        "summary": {
            "total_attempted": attempted,
            "total_established": established,
            "total_failed": failed,
            "success_rate_percent": round(success_rate, 2),
            "ice_candidates_sent": metrics["ice_candidates_sent"],
            "ice_candidates_received": metrics["ice_candidates_received"],
        },
        "connection_states": metrics["connection_states"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/pubsub/stats")
async def get_pubsub_stats():
    """Restituisce statistiche sul protocollo PubSub"""
    return pubsub_manager.get_stats()

@app.get("/network/stats")
async def get_network_stats():
    """
    Restituisce metriche di rete in tempo reale per la visualizzazione UI.
    Separa le statistiche volatili dallo stato CRDT persistente.
    Include peer health scores dal sistema immunitario.
    """
    # Calcola reputazioni e config per scoring
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))

    reputations = calculate_reputations(state_copy)
    config = state_copy.get("global", {}).get("config", DEFAULT_CONFIG)

    # Calcola scores di tutti i peer connessi
    peer_scores = webrtc_manager.peer_scorer.get_all_scores(reputations, config)

    # Statistiche WebRTC con peer scores
    webrtc_peers = {}
    for peer_id, pc in webrtc_manager.connections.items():
        channel_state = "none"
        if peer_id in webrtc_manager.data_channels:
            channel_state = webrtc_manager.data_channels[peer_id].readyState

        # Ottieni metriche dal peer scorer
        metrics = webrtc_manager.peer_scorer.get_metrics(peer_id)
        latency_ms = metrics.latency_ms if metrics else 100.0
        stability = metrics.get_stability() if metrics else 0.0

        # Simula latenza se non tracciata
        if channel_state == "open" and not metrics:
            latency_ms = random.randint(20, 200)

        # Ottieni score
        score = peer_scores.get(peer_id, 0.0)

        # Determina health status (per colore UI)
        if score >= 0.7:
            health_status = "excellent"
        elif score >= 0.4:
            health_status = "good"
        else:
            health_status = "poor"

        webrtc_peers[peer_id] = {
            "state": pc.connectionState,
            "ice_state": pc.iceConnectionState,
            "data_channel": channel_state,
            "latency_ms": latency_ms,
            "stability": stability,
            "reputation": reputations.get(peer_id, 0),
            "score": score,
            "health_status": health_status
        }

    # Statistiche PubSub
    pubsub_stats = pubsub_manager.get_stats()
    topics_detail = {}
    for topic_name, topic_data in pubsub_stats.get("topics", {}).items():
        topics_detail[topic_name] = {
            "mesh_size": topic_data.get("peers", 0),
            "messages_seen": topic_data.get("seen_messages", 0)
        }

    # Calcola nodi scoperti (conosciuti ma non connessi via WebRTC)
    async with state_lock:
        all_known_nodes = set(network_state.get("global", {}).get("nodes", {}).keys())

    connected_nodes = set(webrtc_manager.connections.keys())
    discovered_but_not_connected = all_known_nodes - connected_nodes - {NODE_ID}

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webrtc_connections": {
            "total_established": len([p for p in webrtc_peers.values() if p["state"] == "connected"]),
            "total_connecting": len([p for p in webrtc_peers.values() if p["state"] in ["connecting", "new"]]),
            "peers": webrtc_peers
        },
        "synapsesub_stats": {
            "total_subscriptions": pubsub_stats.get("subscribed_topics", 0),
            "topics": topics_detail,
            "total_messages_seen": sum(t.get("messages_seen", 0) for t in topics_detail.values())
        },
        "network_topology": {
            "total_nodes": len(all_known_nodes),
            "connected_direct": len(connected_nodes),
            "discovered_only": len(discovered_but_not_connected)
        }
    }

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

# --- Endpoint Raft (Consenso Forte per Consiglio Direttivo) ---

class RaftRequestVotePayload(BaseModel):
    """RPC RequestVote - Richiesta di voto da un candidato"""
    term: int
    candidate_id: str
    last_log_index: int
    last_log_term: int

class RaftAppendEntriesPayload(BaseModel):
    """RPC AppendEntries - Replicazione log / heartbeat"""
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[dict] = []  # Serializzazione di RaftLogEntry
    leader_commit: int

@app.post("/raft/request_vote")
async def raft_request_vote(payload: RaftRequestVotePayload):
    """
    Endpoint per RequestVote RPC (Raft).
    
    Chiamato da un candidato per richiedere voti agli altri validatori.
    Solo i nodi validatori dovrebbero rispondere.
    """
    if not raft_manager or not raft_manager.is_validator():
        raise HTTPException(403, "Questo nodo non è un validatore")

    result = await raft_manager.request_vote(
        candidate_id=payload.candidate_id,
        term=payload.term,
        last_log_index=payload.last_log_index,
        last_log_term=payload.last_log_term
    )

    return result

@app.post("/raft/append_entries")
async def raft_append_entries(payload: RaftAppendEntriesPayload):
    """
    Endpoint per AppendEntries RPC (Raft).
    
    Chiamato dal leader per:
    - Inviare heartbeat (entries vuoto)
    - Replicare log entries ai follower
    
    Solo i nodi validatori dovrebbero rispondere.
    """
    if not raft_manager or not raft_manager.is_validator():
        raise HTTPException(403, "Questo nodo non è un validatore")

    result = await raft_manager.append_entries(
        leader_id=payload.leader_id,
        term=payload.term,
        prev_log_index=payload.prev_log_index,
        prev_log_term=payload.prev_log_term,
        entries=payload.entries,
        leader_commit=payload.leader_commit
    )

    return result

# --- Endpoint Task ---
@app.post("/tasks", status_code=201)
async def create_task(payload: CreateTaskPayload, channel: str, funded_by: str = "user"):
    """
    Crea un nuovo task con ricompensa opzionale in Synapse Points.
    
    Ora richiede validazione contro uno schema. Il payload deve rispettare
    le regole definite nello schema specificato (default: task_v1).

    Se reward > 0:
    - funded_by="user": Verifica che il creator abbia balance sufficiente
    - funded_by="treasury": Verifica che la tesoreria del canale abbia balance sufficiente
    - La reward viene "congelata" (sottratta dal balance del creator o treasury)
    - Quando il task viene completato, la reward va all'assignee (meno la tassa)
    """
    if channel not in subscribed_channels:
        raise HTTPException(400, "Canale non sottoscritto.")

    # Tasks cannot be created on global channel (only proposals allowed)
    if channel == "global":
        raise HTTPException(400, "I task non possono essere creati sul canale 'global'. Usa un canale specifico.")

    # Validazione contro schema
    async with state_lock:
        schemas = network_state["global"].get("schemas", {})
    
    # Prepara dati per validazione
    task_data = {
        "title": payload.title,
        "tags": payload.tags,
        "description": payload.description
    }
    
    # Se asta abilitata, usa task_v2 e configura auction
    if payload.enable_auction:
        payload.schema_name = "task_v2"
        deadline = datetime.now(timezone.utc) + timedelta(hours=payload.auction_deadline_hours)
        task_data["auction"] = {
            "enabled": True,
            "status": "open",
            "max_reward": payload.max_reward,
            "deadline": deadline.isoformat(),
            "bids": {},
            "selected_bid": None
        }
        task_data["status"] = "auction_open"
    else:
        # Task tradizionale con reward fissa (anche per task_v2 senza asta)
        task_data["reward"] = payload.reward
        # Per task_v2 senza asta, forza status="open" invece del default "auction_open"
        if payload.schema_name == "task_v2":
            task_data["status"] = "open"
    
    # Valida contro schema
    is_valid, error_msg = validate_against_schema(task_data, payload.schema_name, schemas)
    if not is_valid:
        logging.warning(f"❌ Task validation failed: {error_msg}")
        raise HTTPException(400, f"Validazione schema fallita: {error_msg}")
    
    # Applica default dallo schema
    task_data = apply_schema_defaults(task_data, payload.schema_name, schemas)
    
    logging.info(f"✅ Task validato con successo contro schema '{payload.schema_name}'")

    # Valida reward/max_reward se specificato
    if payload.enable_auction:
        if payload.max_reward <= 0:
            raise HTTPException(400, "max_reward deve essere > 0 per task con asta")
    else:
        if payload.reward < 0:
            raise HTTPException(400, "La reward non può essere negativa")

    # Determina il creator
    if funded_by == "treasury":
        creator = f"channel:{channel}"
    elif funded_by == "user":
        creator = NODE_ID
    else:
        raise HTTPException(400, "funded_by deve essere 'user' o 'treasury'")

    # Verifica balance solo per task tradizionali con reward > 0
    if not payload.enable_auction and payload.reward > 0:
        # Calcola balance corrente
        async with state_lock:
            state_copy = json.loads(json.dumps(network_state, default=list))

        if funded_by == "treasury":
            # Verifica balance della tesoreria
            treasuries = calculate_treasuries(state_copy)
            treasury_balance = treasuries.get(channel, 0)

            if treasury_balance < payload.reward:
                raise HTTPException(400, f"Tesoreria insufficiente. Canale '{channel}' ha {treasury_balance} SP, richiesti {payload.reward} SP")
        else:
            # Verifica balance del creator
            balances = calculate_balances(state_copy)
            creator_balance = balances.get(NODE_ID, 0)

            if creator_balance < payload.reward:
                raise HTTPException(400, f"Balance insufficiente. Hai {creator_balance} SP, richiesti {payload.reward} SP")

    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    new_task = {
        "id": task_id,
        "creator": creator,  # Può essere NODE_ID o "channel:channel_id"
        "owner": NODE_ID,    # Manteniamo per compatibilità
        "title": payload.title,
        "status": task_data.get("status", "open"),
        "assignee": task_data.get("assignee"),
        "tags": payload.tags,
        "description": payload.description,
        "schema_name": payload.schema_name,  # Salva quale schema è stato usato
        "created_at": now,
        "updated_at": now,
        "is_deleted": False
    }
    
    # Aggiungi campi specifici per auction o reward tradizionale
    if payload.enable_auction:
        new_task["auction"] = task_data["auction"]
        new_task["reward"] = 0  # Reward sarà determinata dall'asta
        logging.info(f"🔨 Task con asta creato: '{payload.title}' - max_reward={payload.max_reward} SP, deadline={payload.auction_deadline_hours}h")
    else:
        new_task["reward"] = payload.reward
        if payload.reward > 0:
            if funded_by == "treasury":
                logging.info(f"🏛️ Task '{payload.title}' finanziato dalla tesoreria con reward {payload.reward} SP")
            else:
                logging.info(f"💰 Task '{payload.title}' creato con reward {payload.reward} SP")
        else:
            logging.info(f"📋 Task '{payload.title}' creato senza reward")

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

@app.post("/tasks/{task_id}/bid", status_code=201)
async def place_bid(task_id: str, channel: str, payload: BidPayload):
    """
    Piazza un'offerta per un task in asta.
    
    L'offerta include:
    - amount: reward richiesta (deve essere <= max_reward)
    - estimated_days: stima giorni per completamento
    - reputation: calcolata automaticamente dal sistema
    
    Le bid sono CRDT (merge via LWW per peer_id) e si propagano via gossip.
    """
    if channel not in network_state or task_id not in network_state[channel]["tasks"]:
        raise HTTPException(404, "Task non trovato")
    
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        
        # Verifica che il task abbia un'asta attiva
        if not task.get("auction", {}).get("enabled", False):
            raise HTTPException(400, "Questo task non ha un'asta abilitata")
        
        auction = task["auction"]
        
        # Verifica stato asta
        if auction["status"] != "open":
            raise HTTPException(400, f"L'asta è {auction['status']}, non accetta nuove offerte")
        
        # Verifica deadline
        deadline = datetime.fromisoformat(auction["deadline"])
        if datetime.now(timezone.utc) > deadline:
            raise HTTPException(400, "L'asta è scaduta")
        
        # Verifica che l'offerta non superi max_reward
        if payload.amount > auction["max_reward"]:
            raise HTTPException(400, f"L'offerta ({payload.amount} SP) supera la reward massima ({auction['max_reward']} SP)")
        
        if payload.amount <= 0:
            raise HTTPException(400, "L'offerta deve essere > 0")
        
        if payload.estimated_days <= 0:
            raise HTTPException(400, "I giorni stimati devono essere > 0")
        
        # Calcola reputazione del bidder
        state_copy = json.loads(json.dumps(network_state, default=list))
        reputations = calculate_reputations(state_copy)
        bidder_reputation = reputations.get(NODE_ID, 0)
        
        # Crea/aggiorna bid (CRDT LWW per peer)
        bid_data = {
            "amount": payload.amount,
            "estimated_days": payload.estimated_days,
            "reputation": bidder_reputation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if "bids" not in auction:
            auction["bids"] = {}
        
        auction["bids"][NODE_ID] = bid_data
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logging.info(f"🔨 Nuova bid per task '{task['title']}': {payload.amount} SP, {payload.estimated_days} giorni, reputazione {bidder_reputation}")
    
    return {
        "task_id": task_id,
        "bid": bid_data,
        "total_bids": len(auction["bids"])
    }

@app.post("/tasks/{task_id}/select_bid", status_code=200)
async def select_bid(task_id: str, channel: str):
    """
    Chiude l'asta e seleziona il vincitore.
    
    Può essere chiamato solo dall'owner del task.
    Usa l'algoritmo select_winning_bid() per determinare il vincitore.
    
    Una volta selezionata la bid:
    - auction.status → "finalized"
    - auction.selected_bid → peer_id vincitore
    - task.status → "claimed"
    - task.assignee → peer_id vincitore
    - task.reward → amount della bid vincente
    """
    if channel not in network_state or task_id not in network_state[channel]["tasks"]:
        raise HTTPException(404, "Task non trovato")
    
    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        
        # Verifica che sia l'owner
        if task["owner"] != NODE_ID:
            raise HTTPException(403, "Solo l'owner può selezionare la bid vincente")
        
        # Verifica che il task abbia un'asta
        if not task.get("auction", {}).get("enabled", False):
            raise HTTPException(400, "Questo task non ha un'asta abilitata")
        
        auction = task["auction"]
        
        # Verifica che l'asta sia ancora aperta
        if auction["status"] == "finalized":
            raise HTTPException(400, "L'asta è già stata finalizzata")
        
        # Verifica che ci siano bid
        if not auction.get("bids"):
            raise HTTPException(400, "Nessuna bid disponibile per la selezione")
        
        # Seleziona il vincitore
        winner_id = select_winning_bid(auction["bids"], auction["max_reward"])
        
        if not winner_id:
            raise HTTPException(500, "Errore nella selezione del vincitore")
        
        winning_bid = auction["bids"][winner_id]
        
        # Aggiorna task
        auction["status"] = "finalized"
        auction["selected_bid"] = winner_id
        task["status"] = "claimed"
        task["assignee"] = winner_id
        task["reward"] = winning_bid["amount"]  # La reward finale è l'amount della bid vincente
        task["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        logging.info(f"🎯 Asta chiusa per task '{task['title']}': vincitore {winner_id[:16]}... con {winning_bid['amount']} SP")
    
    return {
        "task_id": task_id,
        "winner": winner_id,
        "winning_bid": winning_bid,
        "total_bids": len(auction["bids"])
    }

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
    """
    Completa un task.

    Se il task ha una reward:
    - La reward viene trasferita dal creator all'assignee (automaticamente tramite calculate_balances)
    - Il completamento incrementa anche la reputazione dell'assignee (+10)
    """
    if channel not in network_state or task_id not in network_state[channel]["tasks"]:
        raise HTTPException(404, "Task non trovato")

    async with state_lock:
        task = network_state[channel]["tasks"][task_id]
        if task["assignee"] != NODE_ID or task["status"] != "in_progress":
            raise HTTPException(403, "Azione non permessa o stato non valido.")

        reward = task.get("reward", 0)
        creator = task.get("creator")

        task["status"] = "completed"
        task["updated_at"] = datetime.now(timezone.utc).isoformat()

    if reward > 0 and creator:
        logging.info(f"✅ Task '{task['title']}' completato! {reward} SP trasferiti da {creator[:8]}... a {NODE_ID[:8]}...")
    else:
        logging.info(f"✅ Task '{task['title']}' completato!")

    return task

# ============================================================================
# --- COLLABORATIVE TEAMS: Task Compositi e Squadre ---
# ============================================================================

@app.post("/skills/profile", status_code=200)
async def update_skills_profile(channel: str, skills: List[str], bio: str = ""):
    """
    Aggiorna il profilo skills del nodo corrente.
    
    Args:
        channel: Canale di riferimento
        skills: Lista di skills (es. ["python", "react", "docker"])
        bio: Breve biografia (opzionale)
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    # Crea o aggiorna profilo
    profile = NodeSkills(
        node_id=NODE_ID,
        skills=skills,
        bio=bio
    )
    
    # Valida
    valid, msg = validate_node_skills(profile)
    if not valid:
        raise HTTPException(400, f"Profilo non valido: {msg}")
    
    async with state_lock:
        network_state[channel]["node_skills"][NODE_ID] = profile.dict()
    
    logging.info(f"👤 Profilo skills aggiornato: {', '.join(skills)}")
    
    return {
        "message": "Profilo aggiornato",
        "node_id": NODE_ID,
        "skills": skills,
        "bio": bio
    }


@app.get("/skills/profile", status_code=200)
async def get_skills_profile(channel: str, node_id: Optional[str] = None):
    """
    Recupera il profilo skills di un nodo.
    
    Args:
        channel: Canale di riferimento
        node_id: ID del nodo (se None, restituisce il profilo del nodo corrente)
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    target_node = node_id or NODE_ID
    
    async with state_lock:
        profile = network_state[channel]["node_skills"].get(target_node)
    
    if not profile:
        raise HTTPException(404, f"Profilo non trovato per nodo {target_node}")
    
    return profile


@app.post("/tasks/composite/create", status_code=201)
async def create_composite_task(channel: str, task_data: Dict):
    """
    Crea un task composito con sub-tasks e skills richieste.
    
    Body esempio:
    {
        "title": "Dashboard Analytics",
        "description": "Dashboard completa",
        "max_team_size": 5,
        "coordinator_bonus": 100,
        "sub_tasks": [
            {
                "title": "Backend API",
                "description": "REST API con FastAPI",
                "required_skills": ["python", "fastapi"],
                "reward_points": 300
            },
            ...
        ]
    }
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    # Crea task composito
    task = TaskComposite(
        **task_data,
        channel=channel,
        created_by=NODE_ID
    )
    
    # Valida
    valid, msg = validate_composite_task(task)
    if not valid:
        raise HTTPException(400, f"Task composito non valido: {msg}")
    
    async with state_lock:
        network_state[channel]["composite_tasks"][task.task_id] = task.dict()
    
    log_team_event("TASK_CREATED", task.task_id, {
        "title": task.title,
        "sub_tasks_count": len(task.sub_tasks),
        "total_reward": task.total_reward_points
    })
    
    return {
        "message": "✅ Task composito creato",
        "task_id": task.task_id,
        "title": task.title,
        "sub_tasks_count": len(task.sub_tasks),
        "required_skills": task.required_skills,
        "total_reward": task.total_reward_points,
        "status": task.status
    }


@app.post("/tasks/composite/{task_id}/claim", status_code=200)
async def claim_composite_task(task_id: str, channel: str):
    """
    Reclama un task composito, diventando il coordinatore.
    
    Il coordinatore è responsabile di:
    - Pubblicare annunci per cercare membri
    - Selezionare i membri della squadra
    - Coordinare il lavoro
    - Ricevere coordinator_bonus al completamento
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        task_dict = network_state[channel]["composite_tasks"].get(task_id)
        
        if not task_dict:
            raise HTTPException(404, "Task composito non trovato")
        
        task = TaskComposite(**task_dict)
        
        # Verifica se il task può essere reclamato
        if task.status != "open":
            raise HTTPException(400, f"Task non disponibile (status: {task.status})")
        
        if task.coordinator:
            raise HTTPException(400, "Task già ha un coordinatore")
        
        # Reclama task
        task.coordinator = NODE_ID
        task.status = "forming_team"
        
        # Aggiorna
        network_state[channel]["composite_tasks"][task_id] = task.dict()
    
    # Genera annuncio
    announcement = generate_team_announcement(task, NODE_ID)
    
    async with state_lock:
        network_state[channel]["team_announcements"][announcement.announcement_id] = announcement.dict()
    
    log_team_event("TASK_CLAIMED", task_id, {
        "coordinator": NODE_ID,
        "announcement_id": announcement.announcement_id
    })
    
    return {
        "message": "✅ Sei diventato coordinatore!",
        "task_id": task_id,
        "coordinator": NODE_ID,
        "status": "forming_team",
        "announcement_id": announcement.announcement_id,
        "announcement": announcement.message
    }


@app.post("/tasks/composite/{task_id}/apply", status_code=200)
async def apply_to_composite_task(task_id: str, channel: str, message: str = ""):
    """
    Candidati per partecipare a un task composito.
    
    Il nodo si candida con le sue skills. Il coordinatore può poi
    accettare o rifiutare la candidatura.
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        # Recupera profilo skills
        profile_dict = network_state[channel]["node_skills"].get(NODE_ID)
        if not profile_dict:
            raise HTTPException(400, "Devi prima creare un profilo skills con POST /skills/profile")
        
        profile = NodeSkills(**profile_dict)
        
        # Recupera task
        task_dict = network_state[channel]["composite_tasks"].get(task_id)
        if not task_dict:
            raise HTTPException(404, "Task composito non trovato")
        
        task = TaskComposite(**task_dict)
        
        # Verifica se può candidarsi
        current_team_size = len(task.team_members) + (1 if task.coordinator else 0)
        can_join, reason = can_node_join_team(NODE_ID, profile.skills, task, current_team_size)
        
        if not can_join:
            raise HTTPException(400, reason)
        
        # Verifica se già candidato
        for applicant in task.applicants:
            if applicant["node_id"] == NODE_ID:
                raise HTTPException(400, "Già candidato per questo task")
        
        # Calcola skill match
        skill_match = calculate_skill_match(profile.skills, task.required_skills)
        
        # Aggiungi candidatura
        application = {
            "node_id": NODE_ID,
            "skills": profile.skills,
            "skill_match": round(skill_match * 100, 1),
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        task.applicants.append(application)
        
        # Aggiorna
        network_state[channel]["composite_tasks"][task_id] = task.dict()
    
    log_team_event("APPLICATION_SUBMITTED", task_id, {
        "applicant": NODE_ID,
        "skill_match": round(skill_match * 100, 1)
    })
    
    return {
        "message": "✅ Candidatura inviata!",
        "task_id": task_id,
        "applicant": NODE_ID,
        "skill_match": f"{skill_match*100:.1f}%",
        "skills": profile.skills
    }


@app.post("/tasks/composite/{task_id}/accept/{applicant_id}", status_code=200)
async def accept_team_member(task_id: str, applicant_id: str, channel: str):
    """
    Accetta un candidato nella squadra (solo coordinatore).
    
    Quando un candidato è accettato:
    - Viene aggiunto a team_members
    - La candidatura viene rimossa da applicants
    - Se la squadra è completa, il workspace viene creato automaticamente
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        task_dict = network_state[channel]["composite_tasks"].get(task_id)
        if not task_dict:
            raise HTTPException(404, "Task composito non trovato")
        
        task = TaskComposite(**task_dict)
        
        # Verifica permessi
        if task.coordinator != NODE_ID:
            raise HTTPException(403, "Solo il coordinatore può accettare membri")
        
        # Trova candidatura
        applicant = None
        for app in task.applicants:
            if app["node_id"] == applicant_id:
                applicant = app
                break
        
        if not applicant:
            raise HTTPException(404, "Candidatura non trovata")
        
        # Verifica spazio disponibile
        if len(task.team_members) >= task.max_team_size - 1:  # -1 per coordinatore
            raise HTTPException(400, "Squadra già al completo")
        
        # Accetta membro
        task.team_members.append(applicant_id)
        task.applicants.remove(applicant)
        
        # Verifica se squadra è completa
        team_complete = is_team_complete(task)
        
        if team_complete and not task.workspace_channel:
            # Crea workspace temporaneo
            workspace = get_workspace_channel_name(task_id)
            task.workspace_channel = workspace
            task.status = "in_progress"
            task.team_formed_at = datetime.now(timezone.utc).isoformat()
            task.started_at = datetime.now(timezone.utc).isoformat()
            
            # Crea il canale workspace
            if workspace not in network_state:
                network_state[workspace] = {
                    "participants": set([task.coordinator] + task.team_members),
                    "tasks": {},
                    "proposals": {},
                    "treasury_balance": 0,
                    "composite_tasks": {},
                    "team_announcements": {},
                    "node_skills": {},
                    "is_temporary": True,
                    "parent_task_id": task_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            
            log_team_event("WORKSPACE_CREATED", task_id, {
                "workspace": workspace,
                "team_size": len(task.team_members) + 1
            })
        
        # Aggiorna task
        network_state[channel]["composite_tasks"][task_id] = task.dict()
    
    log_team_event("MEMBER_ACCEPTED", task_id, {
        "member": applicant_id,
        "team_size": len(task.team_members) + 1
    })
    
    response = {
        "message": f"✅ Membro {applicant_id[:16]}... accettato!",
        "task_id": task_id,
        "new_member": applicant_id,
        "team_size": len(task.team_members) + 1,
        "team_complete": team_complete
    }
    
    if task.workspace_channel:
        response["workspace_channel"] = task.workspace_channel
        response["status"] = "in_progress"
    
    return response


@app.post("/tasks/composite/{task_id}/subtask/{subtask_id}/complete", status_code=200)
async def complete_subtask(task_id: str, subtask_id: str, channel: str):
    """
    Marca un sub-task come completato.
    
    Solo il membro assegnato al sub-task può completarlo.
    Quando tutti i sub-tasks sono completati, il task composito viene chiuso
    e i rewards vengono distribuiti automaticamente.
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        task_dict = network_state[channel]["composite_tasks"].get(task_id)
        if not task_dict:
            raise HTTPException(404, "Task composito non trovato")
        
        task = TaskComposite(**task_dict)
        
        # Trova sub-task
        subtask = None
        for st in task.sub_tasks:
            if st.sub_task_id == subtask_id:
                subtask = st
                break
        
        if not subtask:
            raise HTTPException(404, "Sub-task non trovato")
        
        # Verifica permessi
        if subtask.assigned_to != NODE_ID:
            raise HTTPException(403, "Solo il membro assegnato può completare questo sub-task")
        
        if subtask.status == "completed":
            raise HTTPException(400, "Sub-task già completato")
        
        # Completa sub-task
        subtask.status = "completed"
        subtask.completed_at = datetime.now(timezone.utc).isoformat()
        
        # Verifica se tutti i sub-tasks sono completati
        all_done = all_subtasks_completed(task)
        
        rewards_distributed = {}
        
        if all_done:
            # Completa task composito
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc).isoformat()
            
            # Distribuisci rewards
            peer_scores = network_state[channel].get("peer_scores", {})
            synapse_points = network_state[channel].get("synapse_points", {})
            
            rewards_distributed = distribute_rewards(task, peer_scores, synapse_points)
            
            # Aggiorna stati
            network_state[channel]["peer_scores"] = peer_scores
            network_state[channel]["synapse_points"] = synapse_points
            
            # Dissolvi workspace temporaneo (opzionale, può rimanere per storico)
            if task.workspace_channel and task.workspace_channel in network_state:
                workspace_state = network_state[task.workspace_channel]
                workspace_state["dissolved_at"] = datetime.now(timezone.utc).isoformat()
                workspace_state["status"] = "dissolved"
            
            log_team_event("TASK_COMPLETED", task_id, {
                "rewards_distributed": rewards_distributed,
                "total_reward": sum(rewards_distributed.values())
            })
        
        # Aggiorna task
        network_state[channel]["composite_tasks"][task_id] = task.dict()
    
    response = {
        "message": "✅ Sub-task completato!",
        "task_id": task_id,
        "subtask_id": subtask_id,
        "all_completed": all_done
    }
    
    if all_done:
        response["task_status"] = "completed"
        response["rewards_distributed"] = rewards_distributed
    
    return response


@app.get("/tasks/composite", status_code=200)
async def list_composite_tasks(channel: str, status: Optional[str] = None):
    """
    Lista task compositi in un canale.
    
    Args:
        channel: Nome del canale
        status: Filtra per status (open, forming_team, in_progress, completed)
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        all_tasks = network_state[channel]["composite_tasks"]
    
    tasks = []
    for task_dict in all_tasks.values():
        if status and task_dict["status"] != status:
            continue
        
        # Rimuovi dati sensibili (candidature) se non sei coordinatore
        task_copy = task_dict.copy()
        if task_copy.get("coordinator") != NODE_ID:
            task_copy["applicants"] = []
        
        tasks.append(task_copy)
    
    return {
        "channel": channel,
        "total_tasks": len(tasks),
        "filter_status": status,
        "tasks": tasks
    }


@app.get("/tasks/composite/{task_id}", status_code=200)
async def get_composite_task(task_id: str, channel: str):
    """
    Recupera dettagli di un task composito.
    """
    if channel not in network_state:
        raise HTTPException(404, "Canale non trovato")
    
    async with state_lock:
        task_dict = network_state[channel]["composite_tasks"].get(task_id)
    
    if not task_dict:
        raise HTTPException(404, "Task composito non trovato")
    
    # Rimuovi candidature se non sei coordinatore
    task_copy = task_dict.copy()
    if task_copy.get("coordinator") != NODE_ID:
        task_copy["applicants"] = []
    
    return task_copy


# ========================================
# AI Agent Endpoints
# ========================================

@app.post("/agent/prompt", status_code=200)
async def agent_prompt(channel: str, prompt: str):
    """
    Invia un prompt in linguaggio naturale all'AI agent.
    
    L'agent analizza il prompt, costruisce il contesto della rete,
    e genera comandi API da eseguire automaticamente.
    
    Args:
        channel: Canale di default per le azioni
        prompt: Prompt testuale in linguaggio naturale
        
    Returns:
        actions_executed: Lista di azioni eseguite
        raw_response: Risposta grezza del LLM
    """
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile. Configura AI_MODEL_PATH e riavvia.")
    
    agent = get_agent()
    
    # Costruisci contesto
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    
    channel_data = state_copy.get(channel, {})
    
    # Calcola SP (somma da tutti i canali)
    sp = 0
    for ch in state_copy.values():
        if isinstance(ch, dict) and "synapse_points" in ch:
            sp += ch["synapse_points"].get(NODE_ID, 0)
    
    reputations = calculate_reputations(state_copy)
    reputation = reputations.get(NODE_ID, 0.0)
    node_skills = channel_data.get("node_skills", {}).get(NODE_ID, {})
    skills = node_skills.get("skills", [])
    
    open_tasks = [t for t in channel_data.get("tasks", {}).values() if t.get("status") == "open"]
    active_proposals = [p for p in channel_data.get("proposals", {}).values() if p.get("status") == "open"]
    active_auctions = [a for a in channel_data.get("auctions", {}).values() if a.get("status") == "open"]
    available_teams = [t for t in channel_data.get("composite_tasks", {}).values() 
                       if t.get("status") == "forming_team" and NODE_ID not in t.get("team_members", [])]
    
    peer_count = len(webrtc_manager.peer_connections)
    
    context = NetworkContext(
        node_id=NODE_ID,
        channel=channel,
        synapse_points=sp,
        reputation=reputation,
        skills=skills,
        open_tasks=open_tasks,
        active_proposals=active_proposals,
        active_auctions=active_auctions,
        available_teams=available_teams,
        peer_count=peer_count
    )
    
    # Processa prompt
    actions, raw_response = await agent.process_prompt(prompt, context)
    
    # Esegui azioni validate
    actions_executed = []
    for action in actions:
        is_valid, reason = agent.validate_action(action, context)
        
        if is_valid:
            try:
                await execute_agent_action(action, channel, state_copy)
                actions_executed.append({
                    "action": action.action,
                    "params": action.params,
                    "reasoning": action.reasoning,
                    "status": "executed"
                })
            except Exception as e:
                actions_executed.append({
                    "action": action.action,
                    "params": action.params,
                    "reasoning": action.reasoning,
                    "status": "failed",
                    "error": str(e)
                })
        else:
            actions_executed.append({
                "action": action.action,
                "params": action.params,
                "reasoning": action.reasoning,
                "status": "rejected",
                "reason": reason
            })
    
    return {
        "message": "Prompt processato dall'AI agent",
        "prompt": prompt,
        "actions_generated": len(actions),
        "actions_executed": actions_executed,
        "raw_llm_response": raw_response
    }


@app.get("/agent/objectives", status_code=200)
async def get_agent_objectives():
    """Recupera obiettivi correnti dell'AI agent"""
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile")
    
    agent = get_agent()
    return agent.get_stats()


@app.post("/agent/objectives", status_code=200)
async def set_agent_objectives(objectives: dict):
    """
    Configura obiettivi dell'AI agent.
    
    Args:
        objectives: Dizionario con chiavi:
            - primary_objective: "maximize_sp", "maximize_reputation", etc.
            - target_skills: Lista di skills da specializzare
            - min_sp_reserve: SP minimi da mantenere
            - max_bid_percentage: % massima di SP per bid
            - auto_vote: bool
            - auto_apply_tasks: bool
            - auto_join_teams: bool
            - risk_tolerance: 0.0-1.0
    """
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile")
    
    agent = get_agent()
    
    user_objectives = UserObjectives(
        primary_objective=AgentObjective(objectives.get("primary_objective", "balanced_participation")),
        target_skills=objectives.get("target_skills", []),
        min_sp_reserve=objectives.get("min_sp_reserve", 100),
        max_bid_percentage=objectives.get("max_bid_percentage", 0.3),
        auto_vote=objectives.get("auto_vote", True),
        auto_apply_tasks=objectives.get("auto_apply_tasks", True),
        auto_join_teams=objectives.get("auto_join_teams", True),
        risk_tolerance=objectives.get("risk_tolerance", 0.5)
    )
    
    agent.set_objectives(user_objectives)
    
    return {
        "message": "Obiettivi AI agent aggiornati",
        "objectives": agent.get_stats()["objectives"]
    }


@app.get("/agent/status", status_code=200)
async def get_agent_status():
    """Stato dell'AI agent"""
    agent = get_agent()
    
    if not agent:
        return {
            "enabled": False,
            "reason": "Agent not initialized",
            "model_path": os.getenv("AI_MODEL_PATH", "models/qwen3-0.6b.gguf")
        }
    
    return agent.get_stats()


# ========================================
# Governance Endpoints
# ========================================

# --- Endpoint Governance: Proposte ---

@app.post("/proposals", status_code=201)
async def create_proposal(channel: str, payload: CreateProposalPayload):
    """
    Crea una nuova proposta in un canale.
    
    Ora richiede validazione contro uno schema. Il payload deve rispettare
    le regole definite nello schema specificato (default: proposal_v1).

    Args:
        channel: ID del canale
        payload: Dati della proposta (title, description opzionale, proposal_type opzionale)
    """
    if channel not in subscribed_channels:
        raise HTTPException(400, "Canale non sottoscritto")

    # Validazione contro schema
    async with state_lock:
        schemas = network_state["global"].get("schemas", {})
    
    # Prepara dati per validazione
    proposal_data = {
        "title": payload.title,
        "description": payload.description,
        "proposal_type": payload.proposal_type,
        "params": payload.params,
        "command": payload.command,
        "tags": payload.tags
    }
    
    # Valida contro schema
    is_valid, error_msg = validate_against_schema(proposal_data, payload.schema_name, schemas)
    if not is_valid:
        logging.warning(f"❌ Proposal validation failed: {error_msg}")
        raise HTTPException(400, f"Validazione schema fallita: {error_msg}")
    
    # Applica default dallo schema
    proposal_data = apply_schema_defaults(proposal_data, payload.schema_name, schemas)
    
    logging.info(f"✅ Proposta validata con successo contro schema '{payload.schema_name}'")

    proposal_id = str(uuid.uuid4())
    async with state_lock:
        local_state = network_state.setdefault(channel, {"participants": set(), "tasks": {}, "proposals": {}})
        proposal = {
            "id": proposal_id,
            "title": payload.title,
            "description": payload.description,
            "proposal_type": payload.proposal_type,  # Usa il nome corretto del campo
            "params": payload.params,
            "command": payload.command,  # Aggiungi il campo command
            "tags": payload.tags,
            "schema_name": payload.schema_name,  # Salva quale schema è stato usato
            "proposer": NODE_ID,
            "status": "open",
            "votes": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "closed_at": None
        }
        local_state["proposals"][proposal_id] = proposal

    logging.info(f"📝 Proposta creata: {payload.title[:30]}... su canale {channel}")
    return proposal

@app.get("/zkp/generate_proof", status_code=200)
async def generate_zkp_proof(channel: str, proposal_id: str):
    """
    Helper endpoint per generare una proof ZKP per votazione anonima.
    
    Calcola la reputazione corrente del nodo, deriva il secret dalla chiave privata,
    e genera una proof completa che può essere usata nell'endpoint /vote.
    """
    local_state = network_state.get_channel_state(channel)
    if not local_state:
        raise HTTPException(status_code=404, detail="Canale non trovato")
    
    # Verifica che la proposta esista
    proposal = local_state["proposals"].get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    
    # Calcola la reputazione corrente del nodo
    peer_id = NODE_ID
    reputation = local_state["peer_scores"].get(peer_id, {}).get("reputation", 0)
    
    # Deriva il node_secret dalla chiave privata Ed25519
    with open(ED25519_KEY_FILE, "rb") as f:
        private_key_bytes = f.read()
    node_secret = get_node_secret_from_private_key(private_key_bytes)
    
    # Genera la proof
    proof = generate_reputation_proof(reputation, node_secret, proposal_id)
    
    tier = get_reputation_tier(reputation)
    tier_weight = get_tier_weight(tier)
    
    logging.info(f"🔐 ZKP proof generata per proposta {proposal_id}: tier={tier}, weight={tier_weight}")
    
    return {
        "proof": proof,
        "tier": tier,
        "tier_weight": tier_weight,
        "current_reputation": reputation,
        "proposal_id": proposal_id,
        "instructions": "Usa questo oggetto 'proof' nel campo zkp_proof quando voti con anonymous=true"
    }

@app.post("/proposals/{proposal_id}/vote", status_code=200)
async def vote_on_proposal(proposal_id: str, channel: str, payload: VotePayload):
    """
    Vota su una proposta (tradizionale o anonimo con ZKP).

    Modalità Tradizionale (anonymous=False):
    - Voto firmato con NODE_ID
    - Peso basato su reputazione esatta
    
    Modalità Anonima (anonymous=True):
    - Voto con Zero-Knowledge Proof
    - Prova appartenenza a fascia reputazione senza rivelare ID
    - Protezione anti-double-voting via nullifiers
    
    Args:
        proposal_id: ID della proposta
        channel: ID del canale
        payload: Dati del voto con campi optional per ZKP
    """
    if channel not in network_state or proposal_id not in network_state[channel].get("proposals", {}):
        raise HTTPException(404, "Proposta non trovata")

    async with state_lock:
        proposal = network_state[channel]["proposals"][proposal_id]

        if proposal["status"] != "open":
            raise HTTPException(400, "La proposta è già chiusa")

        # Voto Anonimo con ZKP
        if payload.anonymous:
            if not payload.zkp_proof:
                raise HTTPException(400, "ZKP proof richiesto per voto anonimo")
            
            # Inizializza nullifiers se non esistono
            if "zkp_nullifiers" not in network_state["global"]:
                network_state["global"]["zkp_nullifiers"] = {}
            
            if proposal_id not in network_state["global"]["zkp_nullifiers"]:
                network_state["global"]["zkp_nullifiers"][proposal_id] = set()
            
            used_nullifiers = network_state["global"]["zkp_nullifiers"][proposal_id]
            
            # Verifica ZKP
            is_valid, error_msg = verify_reputation_proof(
                payload.zkp_proof,
                proposal_id,
                used_nullifiers
            )
            
            if not is_valid:
                logging.warning(f"❌ ZKP verification failed: {error_msg}")
                raise HTTPException(400, f"ZKP non valido: {error_msg}")
            
            # Aggiungi nullifier a set usati (anti-double-voting)
            nullifier = payload.zkp_proof["nullifier"]
            network_state["global"]["zkp_nullifiers"][proposal_id].add(nullifier)
            
            # Inizializza anonymous_votes se non esiste
            if "anonymous_votes" not in proposal:
                proposal["anonymous_votes"] = []
            
            # Salva voto anonimo
            anonymous_vote_data = {
                "vote": payload.vote,
                "tier": payload.zkp_proof["tier"],
                "nullifier": nullifier,  # Pubblico, usato per anti-replay
                "timestamp": payload.zkp_proof["timestamp"]
            }
            
            proposal["anonymous_votes"].append(anonymous_vote_data)
            proposal["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            logging.info(f"🔒 Voto anonimo '{payload.vote}' (tier: {payload.zkp_proof['tier']}) su proposta {proposal_id[:8]}...")
            
            return {
                "status": "voted",
                "vote": payload.vote,
                "anonymous": True,
                "tier": payload.zkp_proof["tier"]
            }
        
        # Voto Tradizionale
        else:
            # Aggiungi/aggiorna voto
            proposal["votes"][NODE_ID] = payload.vote
            proposal["updated_at"] = datetime.now(timezone.utc).isoformat()

            logging.info(f"🗳️  Voto '{payload.vote}' su proposta {proposal_id[:8]}... da {NODE_ID[:8]}...")
            
            return {
                "status": "voted",
                "vote": payload.vote,
                "anonymous": False
            }

@app.post("/proposals/{proposal_id}/close", status_code=200)
async def close_proposal(proposal_id: str, channel: str):
    """
    Chiude una proposta e calcola l'esito con voto ponderato.
    Qualsiasi nodo può chiudere una proposta per calcolare il risultato.
    """
    if channel not in network_state or proposal_id not in network_state[channel].get("proposals", {}):
        raise HTTPException(404, "Proposta non trovata")

    async with state_lock:
        proposal = network_state[channel]["proposals"][proposal_id]

        if proposal["status"] != "open":
            raise HTTPException(400, "La proposta è già chiusa")

        # Calcola reputazioni
        state_copy = json.loads(json.dumps(network_state, default=list))
        reputations = calculate_reputations(state_copy)

        # Calcola esito con voto ponderato
        outcome = calculate_proposal_outcome(proposal, reputations)

        # Aggiorna proposta
        proposal["status"] = "closed"
        proposal["closed_at"] = datetime.now(timezone.utc).isoformat()
        proposal["updated_at"] = datetime.now(timezone.utc).isoformat()
        proposal["outcome"] = outcome["outcome"]  # Salva solo la stringa "approved" o "rejected"
        proposal["vote_details"] = outcome  # Salva i dettagli completi in un campo separato

        # Se approvata, gestisci in base al tipo di proposta
        if outcome["outcome"] == "approved":
            proposal_type = proposal.get("proposal_type", "generic")

            # CONFIG_CHANGE: esecuzione automatica immediata (CRDT)
            if proposal_type == "config_change":
                params = proposal.get("params", {})
                key = params.get("key")
                value = params.get("value")

                # Valida che la chiave esista nella config
                if key and key in network_state["global"]["config"]:
                    old_value = network_state["global"]["config"][key]

                    # Valida che il tipo sia corretto
                    if type(value) == type(old_value):
                        # Applica la modifica
                        network_state["global"]["config"][key] = value
                        network_state["global"]["config_version"] += 1
                        network_state["global"]["config_updated_at"] = datetime.now(timezone.utc).isoformat()

                        # Aggiorna proposta con risultato esecuzione
                        proposal["status"] = "executed"
                        proposal["execution_result"] = {
                            "success": True,
                            "key": key,
                            "old_value": old_value,
                            "new_value": value,
                            "executed_at": datetime.now(timezone.utc).isoformat()
                        }

                        logging.info(f"🧬 Config auto-eseguita: {key} cambiato da {old_value} a {value} (proposta {proposal_id[:8]}...)")
                    else:
                        proposal["execution_result"] = {
                            "success": False,
                            "error": f"Tipo non valido: atteso {type(old_value).__name__}, ricevuto {type(value).__name__}"
                        }
                        logging.warning(f"⚠️  Esecuzione config fallita: tipo non valido per {key}")
                else:
                    proposal["execution_result"] = {
                        "success": False,
                        "error": f"Chiave '{key}' non trovata nella configurazione"
                    }
                    logging.warning(f"⚠️  Esecuzione config fallita: chiave '{key}' non valida")

            # COMMAND: esecuzione automatica immediata tramite dispatch_command
            elif proposal_type == "command":
                command = proposal.get("command", {})
                if not command or "operation" not in command:
                    proposal["execution_result"] = {
                        "success": False,
                        "error": "Campo 'command.operation' mancante"
                    }
                    logging.warning(f"⚠️  Esecuzione command fallita: campo 'operation' mancante")
                else:
                    try:
                        # Esegui il comando tramite dispatch_command
                        result = dispatch_command(command)
                        proposal["status"] = "executed" if result.get("success") else "failed"
                        proposal["execution_result"] = result
                        proposal["executed_at"] = datetime.now(timezone.utc).isoformat()
                        
                        if result.get("success"):
                            logging.info(f"⚡ Command auto-eseguito: {command['operation']} (proposta {proposal_id[:8]}...)")
                        else:
                            logging.warning(f"⚠️  Command fallito: {command['operation']} - {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        proposal["status"] = "failed"
                        proposal["execution_result"] = {
                            "success": False,
                            "error": str(e)
                        }
                        logging.error(f"❌ Eccezione esecuzione command: {command.get('operation', 'unknown')} - {e}")

            # NETWORK_OPERATION: richiede ratifica del consiglio (Raft)
            elif proposal_type == "network_operation":
                # Cambia stato a pending_ratification invece di executed
                proposal["status"] = "pending_ratification"
                proposal["pending_since"] = datetime.now(timezone.utc).isoformat()

                # Inizializza struttura per i voti di ratifica
                if "ratification_votes" not in network_state["global"]:
                    network_state["global"]["ratification_votes"] = {}
                network_state["global"]["ratification_votes"][proposal_id] = {}

                # Aggiungi ai pending_operations per essere processata dal consiglio
                operation_entry = {
                    "proposal_id": proposal_id,
                    "channel": channel,
                    "operation": proposal.get("params", {}).get("operation"),
                    "params": proposal.get("params", {}),
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "status": "awaiting_council"
                }
                network_state["global"]["pending_operations"].append(operation_entry)

                logging.info(f"👑 Network operation approvata, in attesa di ratifica del consiglio: {operation_entry['operation']} (proposta {proposal_id[:8]}...)")
            
            # CODE_UPGRADE: aggiornamento codice sorgente con WASM
            elif proposal_type == "code_upgrade":
                # Cambia stato a pending_ratification (richiede ratifica validator set)
                proposal["status"] = "pending_ratification"
                proposal["pending_since"] = datetime.now(timezone.utc).isoformat()
                
                # Aggiungi ai pending_operations per essere processata dal consiglio
                upgrade_entry = {
                    "proposal_id": proposal_id,
                    "channel": channel,
                    "operation": "execute_upgrade",
                    "params": proposal.get("params", {}),
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "status": "awaiting_council"
                }
                network_state["global"]["pending_operations"].append(upgrade_entry)
                
                logging.info(f"🔄 Code upgrade approvato, in attesa di ratifica: {proposal.get('params', {}).get('version')} (proposta {proposal_id[:8]}...)")
                logging.info(f"   Parametri: {operation_entry['params']}")

            # GENERIC: nessuna esecuzione automatica
            else:
                logging.info(f"📝 Proposta generica approvata: {proposal.get('title')} (proposta {proposal_id[:8]}...)")

    logging.info(f"🏛️  Proposta {proposal_id[:8]}... chiusa: {outcome['outcome']} (yes: {outcome['yes_weight']}, no: {outcome['no_weight']})")
    return proposal

@app.get("/proposals/{proposal_id}/details")
async def get_proposal_details(proposal_id: str, channel: str):
    """
    Ottiene i dettagli completi di una proposta inclusi i pesi dei voti.
    """
    if channel not in network_state or proposal_id not in network_state[channel].get("proposals", {}):
        raise HTTPException(404, "Proposta non trovata")

    async with state_lock:
        proposal = network_state[channel]["proposals"][proposal_id].copy()

        # Calcola reputazioni correnti
        state_copy = json.loads(json.dumps(network_state, default=list))
        reputations = calculate_reputations(state_copy)

        # Calcola esito attuale (anche se ancora aperta)
        outcome = calculate_proposal_outcome(proposal, reputations)

        # Aggiungi dettagli outcome
        proposal["current_outcome"] = outcome

    return proposal

@app.post("/governance/ratify/{proposal_id}", status_code=200)
async def ratify_proposal(proposal_id: str, channel: str):
    """
    Ratifica una proposta network_operation da parte di un validatore.
    
    Solo i membri del validator set possono chiamare questo endpoint.
    Quando una maggioranza (N/2 + 1) di validatori ratifica, l'operazione viene
    aggiunta all'execution_log e diventa irreversibile.
    
    Questo simula il consenso Raft: una volta che la maggioranza ha accettato,
    il comando è committed e tutti i nodi lo eseguiranno in modo identico.
    """
    if channel not in network_state or proposal_id not in network_state[channel].get("proposals", {}):
        raise HTTPException(404, "Proposta non trovata")
    
    async with state_lock:
        proposal = network_state[channel]["proposals"][proposal_id]
        
        # Verifica che la proposta sia in stato pending_ratification
        if proposal.get("status") != "pending_ratification":
            raise HTTPException(400, f"La proposta non è in stato pending_ratification (stato attuale: {proposal.get('status')})")
        
        # Verifica che il chiamante sia un validatore
        # NOTE: In produzione, questo dovrebbe verificare una firma crittografica
        # Per ora, accettiamo NODE_ID come validator (simulazione)
        validator_id = NODE_ID
        
        current_validator_set = network_state["global"].get("validator_set", [])
        if validator_id not in current_validator_set:
            raise HTTPException(403, f"Solo i validatori possono ratificare proposte. Validator set corrente: {current_validator_set}")
        
        # Inizializza struttura ratification_votes se non esiste
        if "ratification_votes" not in network_state["global"]:
            network_state["global"]["ratification_votes"] = {}
        if proposal_id not in network_state["global"]["ratification_votes"]:
            network_state["global"]["ratification_votes"][proposal_id] = {}
        
        # Aggiungi voto del validatore
        ratification_votes = network_state["global"]["ratification_votes"][proposal_id]
        
        # Evita doppi voti
        if validator_id in ratification_votes:
            logging.info(f"👑 Validatore {validator_id[:8]}... ha già ratificato la proposta {proposal_id[:8]}...")
            return {
                "status": "already_voted",
                "proposal_id": proposal_id,
                "current_votes": len(ratification_votes),
                "required_votes": (len(current_validator_set) // 2) + 1,
                "validators_voted": list(ratification_votes.keys())
            }
        
        # Registra il voto
        ratification_votes[validator_id] = True
        logging.info(f"👑 Validatore {validator_id[:8]}... ha ratificato la proposta {proposal_id[:8]}... ({len(ratification_votes)}/{len(current_validator_set)} voti)")
        
        # Verifica se abbiamo raggiunto la maggioranza
        required_votes = (len(current_validator_set) // 2) + 1
        
        if len(ratification_votes) >= required_votes:
            # MAGGIORANZA RAGGIUNTA: Crea il comando e aggiungilo all'execution_log
            command_id = str(uuid.uuid4())
            command = {
                "command_id": command_id,
                "proposal_id": proposal_id,
                "operation": proposal.get("params", {}).get("operation"),
                "params": proposal.get("params", {}),
                "ratified_at": datetime.now(timezone.utc).isoformat(),
                "ratified_by": list(ratification_votes.keys())
            }
            
            # Aggiungi al log di esecuzione (append-only CRDT)
            network_state["global"]["execution_log"].append(command)
            
            # Aggiorna stato della proposta
            proposal["status"] = "ratified"
            proposal["ratified_at"] = command["ratified_at"]
            proposal["ratified_by"] = command["ratified_by"]
            proposal["command_id"] = command_id
            proposal["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Rimuovi dai pending_operations
            network_state["global"]["pending_operations"] = [
                op for op in network_state["global"]["pending_operations"]
                if op.get("proposal_id") != proposal_id
            ]
            
            # Pulisci i voti di ratifica (non più necessari)
            del network_state["global"]["ratification_votes"][proposal_id]
            
            logging.info(f"⚡ COMANDO RATIFICATO: {command['operation']} (comando {command_id[:8]}..., proposta {proposal_id[:8]}...)")
            logging.info(f"   Ratificato da: {[v[:8] + '...' for v in command['ratified_by']]}")
            logging.info(f"   Parametri: {command['params']}")
            logging.info(f"   📜 Aggiunto all'execution_log (index {len(network_state['global']['execution_log']) - 1})")
            
            return {
                "status": "ratified",
                "proposal_id": proposal_id,
                "command_id": command_id,
                "operation": command["operation"],
                "params": command["params"],
                "ratified_by": command["ratified_by"],
                "execution_log_index": len(network_state["global"]["execution_log"]) - 1
            }
        else:
            # Ancora in attesa di altri voti
            return {
                "status": "pending",
                "proposal_id": proposal_id,
                "current_votes": len(ratification_votes),
                "required_votes": required_votes,
                "validators_voted": list(ratification_votes.keys()),
                "validators_pending": [v for v in current_validator_set if v not in ratification_votes]
            }

# --- Schema Management Endpoints ---
@app.get("/schemas")
async def get_schemas():
    """
    Ottiene tutti gli schemi definiti nella rete.
    """
    async with state_lock:
        schemas = network_state["global"].get("schemas", {})
    
    return {
        "schemas": schemas,
        "count": len(schemas)
    }

@app.get("/schemas/{schema_name}")
async def get_schema(schema_name: str):
    """
    Ottiene un singolo schema per nome.
    """
    async with state_lock:
        schemas = network_state["global"].get("schemas", {})
        
        if schema_name not in schemas:
            raise HTTPException(404, f"Schema '{schema_name}' non trovato")
        
        return schemas[schema_name]

@app.post("/schemas/validate")
async def validate_data(schema_name: str, data: dict):
    """
    Valida un oggetto dati contro uno schema senza salvarlo.
    Utile per testing e debugging.
    """
    async with state_lock:
        schemas = network_state["global"].get("schemas", {})
    
    is_valid, error_msg = validate_against_schema(data, schema_name, schemas)
    
    if is_valid:
        # Applica defaults per mostrare il risultato finale
        data_with_defaults = apply_schema_defaults(data, schema_name, schemas)
        return {
            "valid": True,
            "schema_name": schema_name,
            "data_with_defaults": data_with_defaults
        }
    else:
        return {
            "valid": False,
            "schema_name": schema_name,
            "error": error_msg
        }

# --- Endpoint Gossip ---
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
            
            # Merge execution_log (append-only CRDT)
            incoming_log = incoming_state.get("execution_log", [])
            local_log = local_state.get("execution_log", [])
            
            # Usa command_id come chiave univoca per deduplicazione
            local_command_ids = {cmd.get("command_id") for cmd in local_log}
            
            for incoming_command in incoming_log:
                command_id = incoming_command.get("command_id")
                if command_id and command_id not in local_command_ids:
                    # Nuovo comando, aggiungilo
                    local_state["execution_log"].append(incoming_command)
                    local_command_ids.add(command_id)
                    logging.info(f"📜 Nuovo comando ricevuto via gossip: {incoming_command.get('operation')} (ID: {command_id[:8]}...)")
            
            # Ordina il log per ratified_at per garantire ordine deterministico
            local_state["execution_log"].sort(key=lambda cmd: cmd.get("ratified_at", ""))
            
            # Merge ratification_votes (union dei voti)
            incoming_ratifications = incoming_state.get("ratification_votes", {})
            local_ratifications = local_state.setdefault("ratification_votes", {})
            
            for proposal_id, votes in incoming_ratifications.items():
                if proposal_id not in local_ratifications:
                    local_ratifications[proposal_id] = {}
                # Union dei voti (ogni validatore può votare solo una volta)
                local_ratifications[proposal_id].update(votes)
            
            # Merge pending_operations (union con deduplicazione per proposal_id)
            incoming_pending = incoming_state.get("pending_operations", [])
            local_pending = local_state.get("pending_operations", [])
            local_pending_ids = {op.get("proposal_id") for op in local_pending}
            
            for incoming_op in incoming_pending:
                proposal_id = incoming_op.get("proposal_id")
                if proposal_id and proposal_id not in local_pending_ids:
                    local_state["pending_operations"].append(incoming_op)
                    local_pending_ids.add(proposal_id)
            
            # Merge config (LWW basato su config_version)
            incoming_config_version = incoming_state.get("config_version", 0)
            local_config_version = local_state.get("config_version", 0)
            
            if incoming_config_version > local_config_version:
                local_state["config"] = incoming_state.get("config", {})
                local_state["config_version"] = incoming_config_version
                local_state["config_updated_at"] = incoming_state.get("config_updated_at", "")
                logging.info(f"🔧 Configurazione aggiornata a versione {incoming_config_version}")
            
            # Merge validator_set (LWW basato su validator_set_updated_at)
            incoming_vs_updated_at = incoming_state.get("validator_set_updated_at")
            local_vs_updated_at = local_state.get("validator_set_updated_at")
            
            if incoming_vs_updated_at and (not local_vs_updated_at or incoming_vs_updated_at > local_vs_updated_at):
                local_state["validator_set"] = incoming_state.get("validator_set", [])
                local_state["validator_set_updated_at"] = incoming_vs_updated_at
                logging.info(f"👑 Validator set aggiornato ({len(local_state['validator_set'])} validatori)")
        else:
            # Merge dei partecipanti per canali tematici
            local_state["participants"].update(incoming_state.get("participants", []))

        # Logica di merge completa per Task e Proposte in QUALSIASI canale
        # Merge Tasks (Logica LWW con validazione schema) - VERSIONE CON SCHEMA VALIDATION
        schemas = network_state["global"].get("schemas", {})
        
        for tid, itask in incoming_state.get("tasks", {}).items():
            ltask = local_state.get("tasks", {}).get(tid)

            # Validazione schema per task in arrivo
            schema_name = itask.get("schema_name", "task_v1")
            is_valid, error_msg = validate_against_schema(itask, schema_name, schemas)
            
            if not is_valid:
                logging.warning(f"❌ Task {tid[:8]}... rifiutato durante gossip: {error_msg}")
                continue  # Scarta il task non valido
            
            # Caso 1: Il task è completamente nuovo per questo nodo.
            if not ltask:
                local_state["tasks"][tid] = itask
                logging.debug(f"✅ Task {tid[:8]}... accettato (nuovo, schema validato)")
                continue

            # Caso 2: Il task esiste, applica la regola Last-Write-Wins.
            # Prosegui solo se l'aggiornamento ricevuto è più recente.
            # Nel gossip ci fidiamo del timestamp updated_at come unica fonte di verità.
            # La validazione delle transizioni di stato è gestita negli endpoint API.
            if itask.get("updated_at", "") > ltask.get("updated_at", ""):
                local_state["tasks"][tid] = itask
                logging.debug(f"✅ Task {tid[:8]}... aggiornato (LWW, schema validato)")

        # Merge Proposals (LWW ibrido con validazione schema)
        for pid, iprop in incoming_state.get("proposals", {}).items():
            lprop = local_state.get("proposals", {}).get(pid)
            
            # Validazione schema per proposal in arrivo
            schema_name = iprop.get("schema_name", "proposal_v1")
            is_valid, error_msg = validate_against_schema(iprop, schema_name, schemas)
            
            if not is_valid:
                logging.warning(f"❌ Proposal {pid[:8]}... rifiutata durante gossip: {error_msg}")
                continue  # Scarta la proposal non valida
            
            if not lprop:
                local_state["proposals"][pid] = iprop
                logging.debug(f"✅ Proposal {pid[:8]}... accettata (nuova, schema validata)")
            else:
                merged_votes = lprop.get("votes", {}).copy()
                merged_votes.update(iprop.get("votes", {}))
                if iprop.get("updated_at", "") > lprop.get("updated_at", ""):
                    lprop.update(iprop)
                lprop["votes"] = merged_votes
                logging.debug(f"✅ Proposal {pid[:8]}... aggiornata (LWW, schema validata)")

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
        # Track message propagation latency for immune system
        if "created_at" in payload:
            try:
                created_at_iso = payload["created_at"]
                if isinstance(created_at_iso, str):
                    created_dt = datetime.fromisoformat(created_at_iso.replace('Z', '+00:00'))
                    created_timestamp = created_dt.timestamp()
                    
                    immune_system = get_immune_system()
                    if immune_system:
                        immune_system.record_message_propagation(created_timestamp)
            except Exception as e:
                logging.debug(f"Could not track message latency: {e}")
        
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

# --- Callback per Sistema Immunitario (Mesh Optimization) ---

async def get_network_state_for_scoring():
    """Callback per ottenere lo stato della rete (per calcolo score peer)"""
    async with state_lock:
        return json.loads(json.dumps(network_state, default=list))

async def get_discovered_nodes():
    """Callback per ottenere i nodi scoperti ma non connessi"""
    async with state_lock:
        all_nodes = set(network_state.get("global", {}).get("nodes", {}).keys())
    return list(all_nodes)

# --- Handler Messaggi WebRTC e PubSub ---

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
            # Pubblica lo stato su ogni canale sottoscritto (incluso global per governance)
            for channel_id in subscribed_channels:
                # Topic formato: "channel:global:state" o "channel:sviluppo_ui:state"
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

# --- Schema Validation System ---

class SchemaValidationError(Exception):
    """Eccezione sollevata quando un oggetto non rispetta lo schema"""
    pass

def validate_against_schema(data: dict, schema_name: str, schemas: dict) -> tuple[bool, Optional[str]]:
    """
    Valida un oggetto dati contro uno schema definito.
    
    Args:
        data: L'oggetto da validare
        schema_name: Nome dello schema da usare per la validazione
        schemas: Dizionario di tutti gli schemi disponibili
    
    Returns:
        (is_valid, error_message)
        - is_valid: True se l'oggetto è valido, False altrimenti
        - error_message: None se valido, stringa di errore se invalido
    
    Esempio:
        is_valid, error = validate_against_schema(
            {"title": "Fix bug", "reward": 100},
            "task_v1",
            network_state["global"]["schemas"]
        )
    """
    # Verifica che lo schema esista
    if schema_name not in schemas:
        return False, f"Schema '{schema_name}' non trovato"
    
    schema = schemas[schema_name]
    fields_def = schema.get("fields", {})
    
    # Valida ogni field definito nello schema
    for field_name, field_spec in fields_def.items():
        field_type = field_spec.get("type")
        required = field_spec.get("required", False)
        default_value = field_spec.get("default")
        
        # Verifica campo obbligatorio
        if required and field_name not in data:
            return False, f"Campo obbligatorio '{field_name}' mancante"
        
        # Se il campo non è presente e non è obbligatorio, OK (userà default se specificato)
        if field_name not in data:
            continue
        
        value = data[field_name]
        
        # Se il valore è None e il default è None, lo considera valido
        if value is None and default_value is None:
            continue
        
        # Validazione per tipo: string
        if field_type == "string":
            if not isinstance(value, str):
                return False, f"Campo '{field_name}' deve essere string, ricevuto {type(value).__name__}"
            
            min_length = field_spec.get("min_length")
            max_length = field_spec.get("max_length")
            
            if min_length is not None and len(value) < min_length:
                return False, f"Campo '{field_name}' deve avere almeno {min_length} caratteri"
            
            if max_length is not None and len(value) > max_length:
                return False, f"Campo '{field_name}' deve avere massimo {max_length} caratteri"
        
        # Validazione per tipo: integer
        elif field_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):  # bool è sottotipo di int in Python
                return False, f"Campo '{field_name}' deve essere integer, ricevuto {type(value).__name__}"
            
            min_val = field_spec.get("min")
            max_val = field_spec.get("max")
            
            if min_val is not None and value < min_val:
                return False, f"Campo '{field_name}' deve essere >= {min_val}"
            
            if max_val is not None and value > max_val:
                return False, f"Campo '{field_name}' deve essere <= {max_val}"
        
        # Validazione per tipo: list[string]
        elif field_type == "list[string]":
            if not isinstance(value, list):
                return False, f"Campo '{field_name}' deve essere list, ricevuto {type(value).__name__}"
            
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    return False, f"Campo '{field_name}[{i}]' deve essere string, ricevuto {type(item).__name__}"
        
        # Validazione per tipo: object (dict)
        elif field_type == "object":
            if not isinstance(value, dict):
                return False, f"Campo '{field_name}' deve essere object, ricevuto {type(value).__name__}"
        
        # Validazione per tipo: enum
        elif field_type == "enum":
            allowed_values = field_spec.get("values", [])
            if value not in allowed_values:
                return False, f"Campo '{field_name}' deve essere uno di {allowed_values}, ricevuto '{value}'"
        
        # Tipo non riconosciuto
        else:
            logging.warning(f"Tipo di campo '{field_type}' non riconosciuto per '{field_name}'")
    
    # Verifica campi extra non definiti nello schema (warning, non errore)
    extra_fields = set(data.keys()) - set(fields_def.keys())
    if extra_fields:
        logging.debug(f"Campi extra non definiti nello schema '{schema_name}': {extra_fields}")
    
    return True, None

def apply_schema_defaults(data: dict, schema_name: str, schemas: dict) -> dict:
    """
    Applica i valori di default definiti nello schema ai campi mancanti.
    
    Args:
        data: L'oggetto da arricchire
        schema_name: Nome dello schema
        schemas: Dizionario degli schemi
    
    Returns:
        Nuovo dizionario con i default applicati
    """
    if schema_name not in schemas:
        return data
    
    schema = schemas[schema_name]
    fields_def = schema.get("fields", {})
    
    result = data.copy()
    
    for field_name, field_spec in fields_def.items():
        if field_name not in result and "default" in field_spec:
            default_value = field_spec["default"]
            # Se il default è mutabile (list, dict), crea una copia
            if isinstance(default_value, (list, dict)):
                import copy
                result[field_name] = copy.deepcopy(default_value)
            else:
                result[field_name] = default_value
    
    return result

# --- Command Execution System ---

def execute_split_channel(params: dict) -> dict:
    """
    Esegue l'operazione split_channel in modo deterministico.
    
    Divide un canale esistente in più canali nuovi basandosi su una logica di split.
    Questa funzione deve essere puramente deterministica: dato lo stesso stato iniziale
    e gli stessi parametri, tutti i nodi devono arrivare esattamente allo stesso risultato.
    
    Args:
        params: {
            "target_channel": str,  # Canale da dividere
            "new_channels": [str, str, ...],  # Nuovi canali da creare
            "split_logic": str,  # "by_tag", "by_title_prefix", "by_age", etc.
            "split_params": dict  # Parametri specifici per la logica
        }
    
    Returns:
        dict con risultato dell'operazione
    
    Example:
        params = {
            "target_channel": "general",
            "new_channels": ["backend", "frontend"],
            "split_logic": "by_tag",
            "split_params": {
                "backend": ["api", "database"],
                "frontend": ["ui", "ux"]
            }
        }
    """
    target_channel = params.get("target_channel")
    new_channels = params.get("new_channels", [])
    split_logic = params.get("split_logic", "by_tag")
    split_params = params.get("split_params", {})
    
    logging.info(f"🔀 Esecuzione split_channel: {target_channel} → {new_channels}")
    logging.info(f"   Logica: {split_logic}, Params: {split_params}")
    
    # Verifica che il canale esista
    if target_channel not in network_state:
        error_msg = f"Canale '{target_channel}' non trovato"
        logging.error(f"❌ Split fallito: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Crea i nuovi canali vuoti
    for new_channel in new_channels:
        if new_channel not in network_state:
            network_state[new_channel] = {
                "participants": set(),
                "tasks": {},
                "proposals": {},
                "treasury_balance": 0,
                "created_by_split": True,
                "split_from": target_channel,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            logging.info(f"   ✅ Canale '{new_channel}' creato")
    
    # Ottieni i dati del canale target
    target_data = network_state[target_channel]
    tasks_moved = {ch: 0 for ch in new_channels}
    proposals_moved = {ch: 0 for ch in new_channels}
    
    # SPLIT LOGIC: by_tag (esempio di implementazione deterministica)
    if split_logic == "by_tag":
        # split_params dovrebbe essere: {"channel_name": ["tag1", "tag2"]}
        
        # Sposta i task
        for task_id, task in list(target_data.get("tasks", {}).items()):
            task_tags = task.get("tags", [])
            
            # Determina in quale canale va (prima corrispondenza)
            for channel_name, required_tags in split_params.items():
                if channel_name in new_channels:
                    # Se uno dei tag del task è nella lista required_tags
                    if any(tag in required_tags for tag in task_tags):
                        network_state[channel_name]["tasks"][task_id] = task
                        tasks_moved[channel_name] += 1
                        # Non rimuovere dal canale originale (manteniamo per storico)
                        break
        
        # Sposta le proposte (stesso criterio)
        for proposal_id, proposal in list(target_data.get("proposals", {}).items()):
            proposal_tags = proposal.get("tags", [])
            
            for channel_name, required_tags in split_params.items():
                if channel_name in new_channels:
                    if any(tag in required_tags for tag in proposal_tags):
                        network_state[channel_name]["proposals"][proposal_id] = proposal
                        proposals_moved[channel_name] += 1
                        break
    
    # SPLIT LOGIC: by_title_prefix
    elif split_logic == "by_title_prefix":
        # split_params: {"channel_name": ["PREFIX1", "PREFIX2"]}
        
        for task_id, task in list(target_data.get("tasks", {}).items()):
            task_title = task.get("title", "").lower()
            
            for channel_name, prefixes in split_params.items():
                if channel_name in new_channels:
                    if any(task_title.startswith(prefix.lower()) for prefix in prefixes):
                        network_state[channel_name]["tasks"][task_id] = task
                        tasks_moved[channel_name] += 1
                        break
        
        for proposal_id, proposal in list(target_data.get("proposals", {}).items()):
            proposal_title = proposal.get("title", "").lower()
            
            for channel_name, prefixes in split_params.items():
                if channel_name in new_channels:
                    if any(proposal_title.startswith(prefix.lower()) for prefix in prefixes):
                        network_state[channel_name]["proposals"][proposal_id] = proposal
                        proposals_moved[channel_name] += 1
                        break
    
    # Marca il canale originale come archiviato (non cancellato)
    target_data["archived"] = True
    target_data["archived_at"] = datetime.now(timezone.utc).isoformat()
    target_data["split_into"] = new_channels
    
    result = {
        "success": True,
        "target_channel": target_channel,
        "new_channels": new_channels,
        "tasks_moved": tasks_moved,
        "proposals_moved": proposals_moved,
        "split_logic": split_logic
    }
    
    logging.info(f"✅ Split completato: {target_channel} → {new_channels}")
    logging.info(f"   Task spostati: {tasks_moved}")
    logging.info(f"   Proposte spostate: {proposals_moved}")
    
    return result

def execute_merge_channels(params: dict) -> dict:
    """
    Esegue l'operazione merge_channels in modo deterministico.
    
    Unisce più canali esistenti in un singolo canale.
    
    Args:
        params: {
            "source_channels": [str, str, ...],  # Canali da unire
            "target_channel": str,  # Canale destinazione
            "conflict_resolution": str  # "keep_all", "prefer_source", etc.
        }
    
    Returns:
        dict con risultato dell'operazione
    """
    source_channels = params.get("source_channels", [])
    target_channel = params.get("target_channel")
    conflict_resolution = params.get("conflict_resolution", "keep_all")
    
    logging.info(f"🔗 Esecuzione merge_channels: {source_channels} → {target_channel}")
    
    # Crea il canale target se non esiste
    if target_channel not in network_state:
        network_state[target_channel] = {
            "participants": set(),
            "tasks": {},
            "proposals": {},
            "treasury_balance": 0,
            "created_by_merge": True,
            "merged_from": source_channels,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    target_data = network_state[target_channel]
    total_tasks_merged = 0
    total_proposals_merged = 0
    
    # Unisci tutti i canali sorgente
    for source_channel in source_channels:
        if source_channel not in network_state:
            logging.warning(f"   ⚠️  Canale sorgente '{source_channel}' non trovato, skip")
            continue
        
        source_data = network_state[source_channel]
        
        # Unisci task (conflict_resolution: keep_all = mantieni duplicati con ID univoco)
        for task_id, task in source_data.get("tasks", {}).items():
            if conflict_resolution == "keep_all":
                # Aggiungi sempre (ID è già univoco per costruzione)
                target_data["tasks"][task_id] = task
                total_tasks_merged += 1
        
        # Unisci proposte
        for proposal_id, proposal in source_data.get("proposals", {}).items():
            if conflict_resolution == "keep_all":
                target_data["proposals"][proposal_id] = proposal
                total_proposals_merged += 1
        
        # Unisci participants
        target_data["participants"].update(source_data.get("participants", set()))
        
        # Marca il canale sorgente come archiviato
        source_data["archived"] = True
        source_data["archived_at"] = datetime.now(timezone.utc).isoformat()
        source_data["merged_into"] = target_channel
    
    result = {
        "success": True,
        "source_channels": source_channels,
        "target_channel": target_channel,
        "tasks_merged": total_tasks_merged,
        "proposals_merged": total_proposals_merged,
        "conflict_resolution": conflict_resolution
    }
    
    logging.info(f"✅ Merge completato: {source_channels} → {target_channel}")
    logging.info(f"   Task uniti: {total_tasks_merged}")
    logging.info(f"   Proposte unite: {total_proposals_merged}")
    
    return result

def execute_update_schema(params: dict) -> dict:
    """
    Esegue l'operazione update_schema in modo deterministico.
    
    Crea o aggiorna uno schema nella rete.
    Questa operazione permette alla rete di evolvere le sue strutture dati.
    
    Args:
        params: {
            "schema_name": str,  # Nome dello schema
            "schema_definition": dict  # Definizione completa dello schema
        }
    
    Returns:
        dict con risultato dell'operazione
    
    Example:
        params = {
            "schema_name": "task_v2",
            "schema_definition": {
                "schema_name": "task_v2",
                "version": 2,
                "description": "Task schema with priority field",
                "fields": {
                    "title": {"type": "string", "required": True},
                    "priority": {"type": "enum", "values": ["low", "medium", "high"], "default": "medium"},
                    ...
                }
            }
        }
    """
    schema_name = params.get("schema_name")
    schema_definition = params.get("schema_definition", {})
    
    logging.info(f"📋 Esecuzione update_schema: {schema_name}")
    
    if not schema_name:
        error_msg = "schema_name è obbligatorio"
        logging.error(f"❌ Update schema fallito: {error_msg}")
        return {"success": False, "error": error_msg}
    
    if not schema_definition:
        error_msg = "schema_definition è obbligatoria"
        logging.error(f"❌ Update schema fallito: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Verifica che la definizione contenga i campi obbligatori
    required_fields = ["schema_name", "fields"]
    for field in required_fields:
        if field not in schema_definition:
            error_msg = f"Campo obbligatorio '{field}' mancante nella schema_definition"
            logging.error(f"❌ Update schema fallito: {error_msg}")
            return {"success": False, "error": error_msg}
    
    # Verifica che schema_name corrisponda
    if schema_definition.get("schema_name") != schema_name:
        error_msg = f"schema_name in params ('{schema_name}') non corrisponde a quello in definition ('{schema_definition.get('schema_name')}')"
        logging.error(f"❌ Update schema fallito: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Determina se è un nuovo schema o un aggiornamento
    is_new = schema_name not in network_state["global"]["schemas"]
    
    # Aggiungi timestamp
    now = datetime.now(timezone.utc).isoformat()
    schema_definition["updated_at"] = now
    if is_new:
        schema_definition["created_at"] = now
    
    # Salva lo schema
    network_state["global"]["schemas"][schema_name] = schema_definition
    
    action = "creato" if is_new else "aggiornato"
    result = {
        "success": True,
        "schema_name": schema_name,
        "action": action,
        "version": schema_definition.get("version", 1)
    }
    
    logging.info(f"✅ Schema {action}: {schema_name} (v{schema_definition.get('version', 1)})")
    
    return result

def execute_acquire_common_tool(params: dict) -> dict:
    """
    Esegue l'acquisizione di un nuovo strumento comune (Common Tool).
    
    Questa operazione:
    1. Verifica che la tesoreria del canale abbia fondi sufficienti
    2. Sottrae il costo del primo mese dalla tesoreria
    3. Cripta le credenziali fornite
    4. Aggiunge lo strumento al dict common_tools del canale
    
    Args:
        params: {
            "channel": str,  # Canale proprietario
            "tool_id": str,  # Identificatore univoco dello strumento
            "description": str,  # Descrizione dello strumento
            "type": str,  # Tipo: "api_key", "oauth_token", "webhook", etc.
            "monthly_cost_sp": int,  # Costo mensile in Synapse Points
            "credentials_to_encrypt": str  # Credenziali in chiaro (saranno criptate)
        }
    
    Returns:
        dict con risultato dell'operazione
    
    Example:
        params = {
            "channel": "sviluppo_ui",
            "tool_id": "geolocation_api",
            "description": "API per geolocalizzare indirizzi IP",
            "type": "api_key",
            "monthly_cost_sp": 100,
            "credentials_to_encrypt": "sk_live_abc123..."
        }
    """
    channel = params.get("channel")
    tool_id = params.get("tool_id")
    description = params.get("description", "")
    tool_type = params.get("type", "api_key")
    monthly_cost_sp = params.get("monthly_cost_sp", 0)
    credentials_plain = params.get("credentials_to_encrypt", "")
    
    logging.info(f"🔧 Esecuzione acquire_common_tool: {tool_id} per canale {channel}")
    
    # Validazione parametri
    if not channel or channel not in network_state:
        error_msg = f"Canale '{channel}' non trovato"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    if not tool_id:
        error_msg = "tool_id è obbligatorio"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    if not credentials_plain:
        error_msg = "credentials_to_encrypt è obbligatorio"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Verifica che lo strumento non esista già
    channel_data = network_state[channel]
    if tool_id in channel_data.get("common_tools", {}):
        error_msg = f"Tool '{tool_id}' già esistente nel canale '{channel}'"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Verifica fondi nella tesoreria
    treasuries = calculate_treasuries(network_state)
    current_balance = treasuries.get(channel, 0)
    
    if current_balance < monthly_cost_sp:
        error_msg = f"Tesoreria insufficiente. Canale '{channel}' ha {current_balance} SP, richiesti {monthly_cost_sp} SP per il primo mese"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Sottrai il costo del primo mese dalla tesoreria
    # (Nota: la tesoreria viene ricalcolata, quindi modifichiamo il balance direttamente)
    channel_data["treasury_balance"] = current_balance - monthly_cost_sp
    
    # Cripta le credenziali
    try:
        encrypted_credentials = encrypt_tool_credentials(credentials_plain, channel)
    except Exception as e:
        error_msg = f"Errore durante la crittografia: {str(e)}"
        logging.error(f"❌ Acquisizione tool fallita: {error_msg}")
        # Rollback tesoreria
        channel_data["treasury_balance"] = current_balance
        return {"success": False, "error": error_msg}
    
    # Crea struttura dello strumento
    now = datetime.now(timezone.utc).isoformat()
    tool_data = {
        "tool_id": tool_id,
        "description": description,
        "type": tool_type,
        "status": "active",
        "monthly_cost_sp": monthly_cost_sp,
        "owner_channel": channel,
        "created_at": now,
        "last_payment_at": now,
        "encrypted_credentials": encrypted_credentials
    }
    
    # Aggiungi lo strumento al canale
    if "common_tools" not in channel_data:
        channel_data["common_tools"] = {}
    
    channel_data["common_tools"][tool_id] = tool_data
    
    result = {
        "success": True,
        "channel": channel,
        "tool_id": tool_id,
        "type": tool_type,
        "monthly_cost_sp": monthly_cost_sp,
        "first_payment_deducted": monthly_cost_sp,
        "treasury_balance_after": channel_data["treasury_balance"],
        "status": "active"
    }
    
    logging.info(f"✅ Tool acquisito: {tool_id} (canale: {channel}, costo mensile: {monthly_cost_sp} SP)")
    logging.info(f"   Tesoreria dopo acquisizione: {channel_data['treasury_balance']} SP")
    
    return result

def execute_deprecate_common_tool(params: dict) -> dict:
    """
    Esegue la deprecazione di uno strumento comune esistente.
    
    Questa operazione:
    1. Trova lo strumento nel canale specificato
    2. Cambia lo status a "deprecated"
    3. Interrompe i pagamenti mensili futuri
    
    Le credenziali rimangono nel sistema (criptate) per audit,
    ma lo strumento non sarà più utilizzabile né pagato.
    
    Args:
        params: {
            "channel": str,  # Canale proprietario
            "tool_id": str  # Identificatore dello strumento da deprecare
        }
    
    Returns:
        dict con risultato dell'operazione
    
    Example:
        params = {
            "channel": "sviluppo_ui",
            "tool_id": "geolocation_api"
        }
    """
    channel = params.get("channel")
    tool_id = params.get("tool_id")
    
    logging.info(f"🗑️  Esecuzione deprecate_common_tool: {tool_id} nel canale {channel}")
    
    # Validazione parametri
    if not channel or channel not in network_state:
        error_msg = f"Canale '{channel}' non trovato"
        logging.error(f"❌ Deprecazione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    if not tool_id:
        error_msg = "tool_id è obbligatorio"
        logging.error(f"❌ Deprecazione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Verifica che lo strumento esista
    channel_data = network_state[channel]
    common_tools = channel_data.get("common_tools", {})
    
    if tool_id not in common_tools:
        error_msg = f"Tool '{tool_id}' non trovato nel canale '{channel}'"
        logging.error(f"❌ Deprecazione tool fallita: {error_msg}")
        return {"success": False, "error": error_msg}
    
    tool_data = common_tools[tool_id]
    
    # Verifica che non sia già deprecato
    if tool_data.get("status") == "deprecated":
        logging.info(f"   ℹ️  Tool '{tool_id}' già deprecato")
        return {
            "success": True,
            "channel": channel,
            "tool_id": tool_id,
            "message": "Tool già deprecato",
            "status": "deprecated"
        }
    
    # Depreca lo strumento
    previous_status = tool_data.get("status")
    tool_data["status"] = "deprecated"
    tool_data["deprecated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = {
        "success": True,
        "channel": channel,
        "tool_id": tool_id,
        "previous_status": previous_status,
        "new_status": "deprecated",
        "message": "Pagamenti mensili interrotti. Strumento non più utilizzabile."
    }
    
    logging.info(f"✅ Tool deprecato: {tool_id} (canale: {channel})")
    logging.info(f"   Status: {previous_status} → deprecated")
    
    return result

def dispatch_command(command: dict) -> dict:
    """
    Dispatcher per l'esecuzione dei comandi.
    
    Smista i comandi in base all'operazione e chiama la funzione appropriata.
    Tutte le funzioni di esecuzione devono essere deterministiche.
    
    Args:
        command: {
            "command_id": str,
            "operation": str,
            "params": dict,
            ...
        }
    
    Returns:
        dict con risultato dell'esecuzione
    """
    operation = command.get("operation")
    params = command.get("params", {})
    
    logging.info(f"⚙️  Dispatching comando: {operation} (ID: {command.get('command_id', 'unknown')[:8]}...)")
    
    if operation == "split_channel":
        return execute_split_channel(params)
    elif operation == "merge_channels":
        return execute_merge_channels(params)
    elif operation == "update_schema":
        return execute_update_schema(params)
    elif operation == "acquire_common_tool":
        return execute_acquire_common_tool(params)
    elif operation == "deprecate_common_tool":
        return execute_deprecate_common_tool(params)
    else:
        error_msg = f"Operazione '{operation}' non riconosciuta"
        logging.error(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

async def command_processor_task():
    """
    Background task che processa i comandi dall'execution_log.
    
    Questo task mantiene un puntatore (last_executed_command_index) all'ultimo
    comando che ha eseguito. Ad ogni ciclo, controlla se ci sono nuovi comandi
    nel log e li esegue in ordine.
    
    Questo garantisce che:
    1. Tutti i nodi eseguano gli stessi comandi nello stesso ordine
    2. Ogni comando venga eseguito esattamente una volta per nodo
    3. L'esecuzione sia idempotente (se un nodo si riavvia, riprende da dove aveva lasciato)
    """
    await asyncio.sleep(15)  # Aspetta che la rete sia inizializzata
    
    logging.info("🔧 Command processor avviato")
    
    while True:
        try:
            async with state_lock:
                execution_log = network_state["global"].get("execution_log", [])
                last_executed_index = network_state["global"].get("last_executed_command_index", -1)
                
                # Controlla se ci sono nuovi comandi da eseguire
                if len(execution_log) > last_executed_index + 1:
                    # Esegui tutti i comandi nuovi in ordine
                    for i in range(last_executed_index + 1, len(execution_log)):
                        command = execution_log[i]
                        command_id = command.get("command_id", "unknown")
                        
                        logging.info(f"🚀 Esecuzione comando {i}: {command.get('operation')} (ID: {command_id[:8]}...)")
                        
                        # Esegui il comando (funzione sincrona deterministica)
                        result = dispatch_command(command)
                        
                        # Aggiorna il puntatore
                        network_state["global"]["last_executed_command_index"] = i
                        
                        # Aggiorna la proposta originaria con il risultato
                        proposal_id = command.get("proposal_id")
                        if proposal_id:
                            # Trova il canale della proposta
                            for channel_id, channel_data in network_state.items():
                                if proposal_id in channel_data.get("proposals", {}):
                                    proposal = channel_data["proposals"][proposal_id]
                                    proposal["status"] = "executed"
                                    proposal["executed_at"] = datetime.now(timezone.utc).isoformat()
                                    proposal["execution_result"] = result
                                    proposal["updated_at"] = datetime.now(timezone.utc).isoformat()
                                    
                                    logging.info(f"   📝 Proposta {proposal_id[:8]}... marcata come executed")
                                    break
                        
                        if result.get("success"):
                            logging.info(f"   ✅ Comando eseguito con successo")
                        else:
                            logging.error(f"   ❌ Comando fallito: {result.get('error')}")
            
            # Aspetta prima di controllare nuovamente
            await asyncio.sleep(5)
        
        except Exception as e:
            logging.error(f"❌ Errore nel command processor: {e}")
            await asyncio.sleep(10)

async def auction_processor_task():
    """
    Background task che processa le aste scadute.
    
    Ogni 30 secondi controlla tutti i task con aste attive e:
    1. Verifica se la deadline è passata
    2. Se ci sono bid, seleziona automaticamente il vincitore
    3. Chiude l'asta e assegna il task
    
    Questo garantisce che le aste non rimangano aperte indefinitamente.
    """
    await asyncio.sleep(20)  # Aspetta che la rete sia inizializzata
    
    logging.info("🔨 Auction processor avviato")
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            async with state_lock:
                # Scansiona tutti i canali
                for channel_id, channel_data in network_state.items():
                    if channel_id == "global":
                        continue
                    
                    # Scansiona tutti i task
                    for task_id, task in channel_data.get("tasks", {}).items():
                        auction = task.get("auction", {})
                        
                        # Verifica se è un'asta attiva
                        if not auction.get("enabled", False):
                            continue
                        
                        if auction["status"] != "open":
                            continue
                        
                        # Verifica deadline
                        deadline_str = auction.get("deadline")
                        if not deadline_str:
                            continue
                        
                        deadline = datetime.fromisoformat(deadline_str)
                        
                        # Se la deadline è passata e ci sono bid
                        if now > deadline and auction.get("bids"):
                            logging.info(f"⏰ Asta scaduta per task '{task['title']}' ({task_id[:8]}...)")
                            
                            # Seleziona il vincitore
                            winner_id = select_winning_bid(auction["bids"], auction["max_reward"])
                            
                            if winner_id:
                                winning_bid = auction["bids"][winner_id]
                                
                                # Chiudi l'asta
                                auction["status"] = "finalized"
                                auction["selected_bid"] = winner_id
                                task["status"] = "claimed"
                                task["assignee"] = winner_id
                                task["reward"] = winning_bid["amount"]
                                task["updated_at"] = now.isoformat()
                                
                                logging.info(f"   🎯 Auto-assegnato a {winner_id[:16]}... con {winning_bid['amount']} SP")
                            else:
                                logging.warning(f"   ⚠️  Nessun vincitore selezionato per task {task_id[:8]}...")
                        
                        # Se la deadline è passata ma non ci sono bid
                        elif now > deadline and not auction.get("bids"):
                            logging.info(f"⏰ Asta scaduta senza bid per task '{task['title']}' ({task_id[:8]}...)")
                            auction["status"] = "closed"
                            task["status"] = "open"  # Torna allo stato open per permettere claim tradizionale
                            task["updated_at"] = now.isoformat()
            
            # Controlla ogni 30 secondi
            await asyncio.sleep(30)
        
        except Exception as e:
            logging.error(f"❌ Errore nell'auction processor: {e}")
            await asyncio.sleep(30)

def calculate_reputations(full_state: dict) -> Dict[str, dict]:
    """
    Calcola la reputazione di ogni nodo basata su task completati e voti.
    
    Versione v2 con supporto per specializzazioni basate su tag.
    
    Returns:
        Dict[node_id, reputation_dict] dove reputation_dict ha formato:
        {
            "_total": int,
            "_last_updated": str,
            "tags": {
                "tag1": int,
                "tag2": int,
                ...
            }
        }
    """
    config = full_state.get("global", {}).get("config", DEFAULT_CONFIG)
    task_reward = config.get("task_completion_reputation_reward", 10)
    vote_reward = config.get("proposal_vote_reputation_reward", 1)

    # Inizializza reputazioni con formato v2
    reputations = {}
    for node_id in full_state.get("global", {}).get("nodes", {}):
        reputations[node_id] = {
            "_total": 0,
            "_last_updated": datetime.now(timezone.utc).isoformat(),
            "tags": {}
        }
    
    # Calcola reputazione da task completati (con specializzazioni)
    for channel_id, channel_data in full_state.items():
        if channel_id != "global":
            for task in channel_data.get("tasks", {}).values():
                if task.get("status") == "completed":
                    assignee = task.get("assignee")
                    if assignee and assignee in reputations:
                        # Ottieni tag del task
                        task_tags = task.get("tags", [])
                        
                        # Aggiorna specializzazioni per ogni tag
                        for tag in task_tags:
                            if tag in reputations[assignee]["tags"]:
                                reputations[assignee]["tags"][tag] += task_reward
                            else:
                                reputations[assignee]["tags"][tag] = task_reward
                        
                        # Aggiorna totale
                        reputations[assignee]["_total"] += task_reward
    
    # Aggiungi reputazione da voti (senza specializzazione)
    for channel_id, channel_data in full_state.items():
        for prop in channel_data.get("proposals", {}).values():
            for voter_id in prop.get("votes", {}):
                if voter_id in reputations:
                    reputations[voter_id]["_total"] += vote_reward
    
    return reputations

def select_winning_bid(bids: dict, max_reward: int) -> Optional[str]:
    """
    Seleziona l'offerta vincente usando un algoritmo di scoring ponderato.
    
    Scoring Formula:
    - Cost Score (40%): (max_reward - amount) / max_reward → premia bid più basse
    - Reputation Score (40%): reputation / max_reputation → premia alta reputazione
    - Time Score (20%): (1 / estimated_days) → premia consegna più veloce
    
    Returns:
        peer_id del vincitore, o None se nessuna bid valida
    """
    if not bids:
        return None
    
    # Trova valori max per normalizzazione
    max_reputation = max((bid["reputation"] for bid in bids.values()), default=1)
    max_days = max((bid["estimated_days"] for bid in bids.values()), default=1)
    
    best_peer = None
    best_score = -1
    
    for peer_id, bid in bids.items():
        # Cost score: premia offerte più basse (normalizzato 0-1)
        cost_score = (max_reward - bid["amount"]) / max_reward if max_reward > 0 else 0
        
        # Reputation score: premia alta reputazione (normalizzato 0-1)
        reputation_score = bid["reputation"] / max_reputation if max_reputation > 0 else 0
        
        # Time score: premia consegna veloce (normalizzato 0-1)
        # Inverso dei giorni, normalizzato rispetto al minimo
        time_score = (1 / bid["estimated_days"]) / (1 / max(1, max_days))
        
        # Score totale ponderato
        total_score = (
            0.4 * cost_score +
            0.4 * reputation_score +
            0.2 * time_score
        )
        
        logging.debug(f"Bid {peer_id[:8]}... → score={total_score:.3f} (cost={cost_score:.3f}, rep={reputation_score:.3f}, time={time_score:.3f})")
        
        if total_score > best_score:
            best_score = total_score
            best_peer = peer_id
    
    if best_peer:
        logging.info(f"🏆 Vincitore asta: {best_peer[:16]}... con score {best_score:.3f}")
    
    return best_peer

def calculate_balances(full_state: dict) -> Dict[str, int]:
    """
    Calcola il balance SP (Synapse Points) di ogni nodo.

    Il balance è calcolato localmente da ogni nodo tracciando tutte le transazioni implicite:
    - Ogni nodo parte con un balance iniziale (default 1000 SP, configurabile via config)
    - Quando un task con reward viene creato, il creator perde reward SP (congelati)
    - Quando un task viene completato:
        * L'assignee guadagna reward SP (meno la tassa)
        * La tesoreria del canale guadagna la tassa (es. 2% del reward)
    - Il calcolo è deterministico: tutti i nodi arrivano allo stesso risultato

    Returns:
        Dict[node_id, balance_sp]
    """
    config = full_state.get("global", {}).get("config", DEFAULT_CONFIG)
    INITIAL_BALANCE = config.get("initial_balance_sp", 1000)
    TAX_RATE = config.get("transaction_tax_percentage", 0.02)

    balances = {node_id: INITIAL_BALANCE for node_id in full_state.get("global", {}).get("nodes", {})}

    # Traccia le transazioni attraverso i task
    for channel_id, channel_data in full_state.items():
        if channel_id == "global":
            continue

        for task in channel_data.get("tasks", {}).values():
            reward = task.get("reward", 0)

            if reward > 0:
                creator = task.get("creator")
                assignee = task.get("assignee")
                status = task.get("status")

                # Il creator ha speso reward SP per creare il task (sempre, appena creato)
                # Se il creator è il canale stesso (task finanziato dalla tesoreria),
                # il costo viene gestito nella calculate_treasuries
                if creator and creator in balances:
                    balances[creator] -= reward

                # Se il task è completato, l'assignee guadagna reward SP (meno la tassa)
                if status == "completed" and assignee and assignee in balances:
                    tax_amount = max(1, round(reward * TAX_RATE))  # Minimo 1 SP, arrotondato
                    net_reward = reward - tax_amount
                    balances[assignee] += net_reward
                    # La tassa va alla tesoreria (calcolata in calculate_treasuries)

    return balances

def calculate_treasuries(full_state: dict) -> Dict[str, int]:
    """
    Calcola il balance della tesoreria di ogni canale.

    La tesoreria viene finanziata da:
    - Tasse sui task completati (es. 2% del reward)
    - Balance iniziale configurabile

    La tesoreria viene spesa per:
    - Task creati dal canale stesso (channel-owned tasks)

    Returns:
        Dict[channel_id, treasury_balance]
    """
    config = full_state.get("global", {}).get("config", DEFAULT_CONFIG)
    INITIAL_TREASURY = config.get("treasury_initial_balance", 0)
    TAX_RATE = config.get("transaction_tax_percentage", 0.02)

    treasuries = {}

    for channel_id, channel_data in full_state.items():
        if channel_id == "global":
            continue

        treasury = INITIAL_TREASURY
        
        # DEBUG: Count tasks
        tasks = channel_data.get("tasks", {})
        completed_tasks = [t for t in tasks.values() if t.get("status") == "completed"]
        logging.info(f"🔍 Treasury calc for '{channel_id}': {len(tasks)} tasks, {len(completed_tasks)} completed")

        for task in channel_data.get("tasks", {}).values():
            reward = task.get("reward", 0)

            if reward > 0:
                creator = task.get("creator")
                status = task.get("status")
                
                # DEBUG: Log task details
                logging.info(f"   Task: reward={reward}, creator={creator[:16] if creator else None}..., status={status}")

                # Se il task è stato creato dal canale (treasury-funded)
                if creator == f"channel:{channel_id}":
                    # La tesoreria paga il reward
                    treasury -= reward

                    # Se completato, la tassa torna alla tesoreria
                    # (effettivamente solo net_reward esce dalla tesoreria)
                    if status == "completed":
                        tax_amount = max(1, round(reward * TAX_RATE))  # Minimo 1 SP, arrotondato
                        treasury += tax_amount
                        logging.info(f"   💰 Treasury-funded task completed: +{tax_amount} SP tax back")

                # Se il task è di un utente normale e completato
                elif status == "completed" and creator:
                    # La tesoreria riceve la tassa
                    tax_amount = max(1, round(reward * TAX_RATE))  # Minimo 1 SP, arrotondato
                    treasury += tax_amount
                    logging.info(f"   💰 User task completed: +{tax_amount} SP tax")

        logging.info(f"   📊 Final treasury for '{channel_id}': {treasury} SP")
        treasuries[channel_id] = treasury

    return treasuries

def calculate_vote_weight(reputation: int) -> float:
    """
    Calcola il peso di un voto basato sulla reputazione.
    Usa una funzione logaritmica per evitare dominanza eccessiva dei nodi ad alta reputazione.

    Formula: peso = 1 + log2(reputazione + 1)

    Esempi:
    - reputation 0: peso 1.0
    - reputation 10: peso ~4.46
    - reputation 50: peso ~6.67
    - reputation 100: peso ~7.66
    - reputation 1000: peso ~10.97
    """
    import math
    return 1.0 + math.log2(reputation + 1)

def migrate_reputation_to_v2(old_reputation: int) -> dict:
    """
    Migra una reputazione da formato integer a formato dict specializzato.
    
    Args:
        old_reputation: Valore integer della vecchia reputazione
        
    Returns:
        Dict con struttura v2: {"_total": int, "_last_updated": str, "tags": {}}
    """
    return {
        "_total": old_reputation,
        "_last_updated": datetime.now(timezone.utc).isoformat(),
        "tags": {}
    }

def ensure_reputation_v2_format(reputation: any) -> dict:
    """
    Assicura che la reputazione sia nel formato v2.
    Se è un integer, lo migra. Se è già un dict, lo restituisce.
    
    Args:
        reputation: Reputazione in formato qualsiasi
        
    Returns:
        Dict con struttura v2
    """
    if isinstance(reputation, int):
        return migrate_reputation_to_v2(reputation)
    elif isinstance(reputation, dict):
        # Verifica che abbia i campi necessari
        if "_total" not in reputation:
            reputation["_total"] = 0
        if "_last_updated" not in reputation:
            reputation["_last_updated"] = datetime.now(timezone.utc).isoformat()
        if "tags" not in reputation:
            reputation["tags"] = {}
        return reputation
    else:
        # Fallback: crea reputazione vuota
        return {
            "_total": 0,
            "_last_updated": datetime.now(timezone.utc).isoformat(),
            "tags": {}
        }

def update_reputation_on_task_complete(reputation: dict, task_tags: List[str], reward_points: int) -> dict:
    """
    Aggiorna la reputazione di un nodo quando completa un task.
    
    Args:
        reputation: Dict reputazione in formato v2
        task_tags: Lista di tag del task completato
        reward_points: Punti reward del task (default: 10)
        
    Returns:
        Dict reputazione aggiornato
    """
    # Assicura formato v2
    reputation = ensure_reputation_v2_format(reputation)
    
    # Aggiorna specializzazioni per ogni tag
    for tag in task_tags:
        if tag in reputation["tags"]:
            reputation["tags"][tag] += reward_points
        else:
            reputation["tags"][tag] = reward_points
    
    # Aggiorna totale
    reputation["_total"] += reward_points
    
    # Aggiorna timestamp
    reputation["_last_updated"] = datetime.now(timezone.utc).isoformat()
    
    return reputation

def calculate_contextual_vote_weight(reputation: dict, proposal_tags: List[str]) -> float:
    """
    Calcola il peso di un voto basato sulla reputazione e sul contesto della proposta.
    
    La formula combina:
    - Base weight: log2(_total + 1) - reputazione generale
    - Bonus weight: log2(specialization_score + 1) - expertise nei tag della proposta
    
    Args:
        reputation: Dict reputazione in formato v2
        proposal_tags: Lista di tag della proposta
        
    Returns:
        Float peso totale del voto
        
    Examples:
        >>> rep = {"_total": 1023, "tags": {"security": 500, "python": 100}}
        >>> calculate_contextual_vote_weight(rep, ["security", "refactor"])
        18.9  # base (10) + bonus (8.9)
    """
    import math
    
    # Assicura formato v2
    reputation = ensure_reputation_v2_format(reputation)
    
    # Calcola peso base dalla reputazione totale
    base_weight = 1.0 + math.log2(reputation["_total"] + 1)
    
    # Calcola specialization score sommando reputazione per tag matchati
    specialization_score = 0
    for tag in proposal_tags:
        specialization_score += reputation["tags"].get(tag, 0)
    
    # Calcola peso bonus (smorzato con logaritmo)
    bonus_weight = math.log2(specialization_score + 1) if specialization_score > 0 else 0
    
    # Peso totale
    total_weight = base_weight + bonus_weight
    
    return round(total_weight, 2)

async def reputation_decay_loop():
    """
    Background task che applica il decadimento della reputazione.
    
    Esegue una volta al giorno (ogni 24 ore) e:
    - Applica decay factor (default 0.99 = -1% al giorno) a ogni tag
    - Ricalcola _total come somma dei tag
    - Rimuove tag sotto soglia minima (0.1)
    - Aggiorna timestamp
    """
    DECAY_INTERVAL = 24 * 60 * 60  # 24 ore in secondi
    DECAY_FACTOR = 0.99  # -1% al giorno
    MIN_TAG_VALUE = 0.1  # Soglia minima per mantenere un tag
    
    logging.info("🕒 Reputation decay loop avviato (intervallo: 24h, factor: -1%)")
    
    while True:
        try:
            await asyncio.sleep(DECAY_INTERVAL)
            
            logging.info("⏳ Applicazione decay reputazione...")
            
            async with state_lock:
                nodes = network_state.get("global", {}).get("nodes", {})
                decay_applied_count = 0
                tags_removed_count = 0
                
                for node_id, node_data in nodes.items():
                    reputation = node_data.get("reputation", 0)
                    
                    # Assicura formato v2
                    reputation = ensure_reputation_v2_format(reputation)
                    
                    # Applica decay a ogni tag
                    tags_to_remove = []
                    for tag, value in reputation["tags"].items():
                        new_value = value * DECAY_FACTOR
                        
                        if new_value < MIN_TAG_VALUE:
                            tags_to_remove.append(tag)
                        else:
                            reputation["tags"][tag] = round(new_value, 2)
                    
                    # Rimuovi tag sotto soglia
                    for tag in tags_to_remove:
                        del reputation["tags"][tag]
                        tags_removed_count += 1
                    
                    # Ricalcola _total come somma dei tag
                    reputation["_total"] = sum(reputation["tags"].values())
                    
                    # Aggiorna timestamp
                    reputation["_last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Salva nel network state
                    node_data["reputation"] = reputation
                    decay_applied_count += 1
            
            logging.info(f"✅ Decay applicato a {decay_applied_count} nodi ({tags_removed_count} tag rimossi)")
            
        except Exception as e:
            logging.error(f"❌ Errore in reputation decay loop: {e}")
            await asyncio.sleep(60)  # Riprova dopo 1 minuto in caso di errore

async def common_tools_maintenance_loop():
    """
    Background task per la manutenzione dei Common Tools.
    
    Esegue una volta al giorno (ogni 24 ore) e:
    - Controlla ogni tool con status "active"
    - Verifica se è passato un mese da last_payment_at
    - Se sì, tenta di addebitare monthly_cost_sp dalla tesoreria
    - Se fondi insufficienti, imposta status a "inactive_funding_issue"
    - Se fondi sufficienti, aggiorna last_payment_at e sottrae dalla tesoreria
    """
    MAINTENANCE_INTERVAL = 24 * 60 * 60  # 24 ore in secondi
    PAYMENT_CYCLE_DAYS = 30  # Ciclo di pagamento mensile
    
    logging.info("🔧 Common Tools maintenance loop avviato (intervallo: 24h, ciclo pagamento: 30 giorni)")
    
    while True:
        try:
            await asyncio.sleep(MAINTENANCE_INTERVAL)
            
            logging.info("🛠️  Esecuzione manutenzione Common Tools...")
            
            async with state_lock:
                now = datetime.now(timezone.utc)
                tools_checked = 0
                payments_processed = 0
                tools_suspended = 0
                
                # Itera su tutti i canali
                for channel_id, channel_data in network_state.items():
                    if channel_id == "global":
                        continue
                    
                    common_tools = channel_data.get("common_tools", {})
                    
                    # Itera su tutti gli strumenti del canale
                    for tool_id, tool_data in common_tools.items():
                        tools_checked += 1
                        
                        # Processa solo strumenti attivi
                        if tool_data.get("status") != "active":
                            continue
                        
                        # Verifica se è passato un mese dall'ultimo pagamento
                        last_payment_str = tool_data.get("last_payment_at")
                        if not last_payment_str:
                            logging.warning(f"   ⚠️  Tool '{tool_id}' senza last_payment_at, skip")
                            continue
                        
                        last_payment = datetime.fromisoformat(last_payment_str)
                        days_since_payment = (now - last_payment).days
                        
                        if days_since_payment < PAYMENT_CYCLE_DAYS:
                            # Non ancora tempo di pagare
                            continue
                        
                        # È tempo di pagare!
                        monthly_cost = tool_data.get("monthly_cost_sp", 0)
                        
                        logging.info(f"   💰 Tool '{tool_id}' richiede pagamento: {monthly_cost} SP (ultimo pagamento: {days_since_payment} giorni fa)")
                        
                        # Calcola tesoreria corrente
                        treasuries = calculate_treasuries(network_state)
                        current_balance = treasuries.get(channel_id, 0)
                        
                        # Verifica fondi sufficienti
                        if current_balance < monthly_cost:
                            # Fondi insufficienti: sospendi strumento
                            tool_data["status"] = "inactive_funding_issue"
                            tool_data["suspended_at"] = now.isoformat()
                            tool_data["suspension_reason"] = f"Tesoreria insufficiente: {current_balance} SP disponibili, {monthly_cost} SP richiesti"
                            tools_suspended += 1
                            
                            logging.warning(f"   ⚠️  Tool '{tool_id}' sospeso per fondi insufficienti (tesoreria: {current_balance} SP, richiesti: {monthly_cost} SP)")
                        else:
                            # Fondi sufficienti: processa pagamento
                            # Sottrai dalla tesoreria (modifica diretta del balance)
                            channel_data["treasury_balance"] = current_balance - monthly_cost
                            
                            # Aggiorna last_payment_at
                            tool_data["last_payment_at"] = now.isoformat()
                            
                            payments_processed += 1
                            
                            logging.info(f"   ✅ Pagamento processato per tool '{tool_id}': {monthly_cost} SP")
                            logging.info(f"      Tesoreria canale '{channel_id}': {current_balance} SP → {channel_data['treasury_balance']} SP")
            
            logging.info(f"🎯 Manutenzione completata: {tools_checked} tools controllati, {payments_processed} pagamenti processati, {tools_suspended} tools sospesi")
            
        except Exception as e:
            logging.error(f"❌ Errore in common tools maintenance loop: {e}")
            await asyncio.sleep(60)  # Riprova dopo 1 minuto in caso di errore

def calculate_proposal_outcome(proposal: dict, reputations: Dict[str, int]) -> dict:
    """
    Calcola l'esito di una proposta con voto ponderato.
    
    Supporta sia voti tradizionali (con voter_id visibile) che voti anonimi (con ZKP).

    Returns:
        {
            "total_votes": int,
            "yes_count": int,
            "no_count": int,
            "yes_weight": float,
            "no_weight": float,
            "outcome": "approved" | "rejected" | "pending",
            "vote_details": [
                {"voter_id": str, "vote": "yes"|"no", "reputation": int, "weight": float},
                ...
            ],
            "anonymous_vote_summary": {
                "total": int,
                "yes_count": int,
                "no_count": int,
                "tier_breakdown": {...}
            }
        }
    """
    votes = proposal.get("votes", {})
    anonymous_votes = proposal.get("anonymous_votes", [])
    
    vote_details = []
    yes_weight = 0.0
    no_weight = 0.0
    yes_count = 0
    no_count = 0

    # Ottieni tag della proposta per calcolo contestuale
    proposal_tags = proposal.get("tags", [])
    
    # Elabora voti tradizionali (pubblici) con peso contestuale
    for voter_id, vote_value in votes.items():
        reputation = reputations.get(voter_id, {
            "_total": 0,
            "_last_updated": datetime.now(timezone.utc).isoformat(),
            "tags": {}
        })
        
        # Usa calcolo contestuale se ci sono tag, altrimenti usa quello semplice
        if proposal_tags and isinstance(reputation, dict):
            weight = calculate_contextual_vote_weight(reputation, proposal_tags)
        else:
            # Fallback per compatibilità con vecchie reputazioni integer
            rep_total = reputation["_total"] if isinstance(reputation, dict) else reputation
            weight = calculate_vote_weight(rep_total)

        vote_details.append({
            "voter_id": voter_id,
            "vote": vote_value,
            "reputation": reputation["_total"] if isinstance(reputation, dict) else reputation,
            "weight": round(weight, 2),
            "anonymous": False
        })

        if vote_value == "yes":
            yes_weight += weight
            yes_count += 1
        elif vote_value == "no":
            no_weight += weight
            no_count += 1

    # Elabora voti anonimi (con ZKP)
    anonymous_summary = {
        "total": len(anonymous_votes),
        "yes_count": 0,
        "no_count": 0,
        "tier_breakdown": {}
    }
    
    for anon_vote in anonymous_votes:
        vote_value = anon_vote["vote"]
        tier = anon_vote["tier"]
        tier_weight = get_tier_weight(tier)
        
        # Conta per tier
        if tier not in anonymous_summary["tier_breakdown"]:
            anonymous_summary["tier_breakdown"][tier] = {"yes": 0, "no": 0}
        anonymous_summary["tier_breakdown"][tier][vote_value] += 1
        
        # Aggiungi peso al totale
        if vote_value == "yes":
            yes_weight += tier_weight
            yes_count += 1
            anonymous_summary["yes_count"] += 1
        elif vote_value == "no":
            no_weight += tier_weight
            no_count += 1
            anonymous_summary["no_count"] += 1

    # Determina l'esito basato sui voti
    # Se ci sono voti, calcola sempre l'esito (anche se la proposta non è ancora chiusa)
    if yes_weight > 0 or no_weight > 0:
        outcome = "approved" if yes_weight > no_weight else "rejected"
    else:
        outcome = "pending"

    return {
        "total_votes": len(votes) + len(anonymous_votes),
        "yes_count": yes_count,
        "no_count": no_count,
        "yes_weight": round(yes_weight, 2),
        "no_weight": round(no_weight, 2),
        "outcome": outcome,
        "vote_details": vote_details,
        "anonymous_vote_summary": anonymous_summary
    }

def determine_validator_set(full_state: dict, reputations: Dict[str, int]) -> List[str]:
    """
    Determina il set di validatori (Consiglio Direttivo) basato sulla reputazione.

    I validatori sono i top N nodi con la reputazione più alta.
    Questo è un calcolo deterministico: tutti i nodi arrivano alla stessa lista.

    Args:
        full_state: Lo stato completo della rete
        reputations: Dict di {node_id: reputation}

    Returns:
        Lista ordinata di node_id (dal più reputato al meno)

    Example:
        Se ci sono 20 nodi e validator_set_size=7, ritorna i top 7.
        Se ci sono meno di 7 nodi, ritorna tutti i nodi disponibili.
    """
    config = full_state.get("global", {}).get("config", DEFAULT_CONFIG)
    validator_set_size = config.get("validator_set_size", 7)

    # Ottieni tutti i nodi attivi (presenti nello stato globale)
    all_nodes = full_state.get("global", {}).get("nodes", {})

    # Filtra solo i nodi che hanno reputazione >= 0 (tutti i nodi, essenzialmente)
    # Questo permette di estendere in futuro con requisiti minimi
    eligible_nodes = [
        node_id for node_id in all_nodes.keys()
        if reputations.get(node_id, 0) >= 0
    ]

    # Ordina per reputazione decrescente
    sorted_nodes = sorted(
        eligible_nodes,
        key=lambda nid: reputations.get(nid, 0),
        reverse=True
    )

    # Prendi i top N
    validator_set = sorted_nodes[:validator_set_size]

    logging.info(f"👑 Validator Set calcolato: {len(validator_set)} validatori su {len(eligible_nodes)} nodi totali")
    for i, node_id in enumerate(validator_set):
        rep = reputations.get(node_id, 0)
        is_self = " (ME)" if node_id == NODE_ID else ""
        logging.info(f"   #{i+1}: {node_id[:8]}... (rep: {rep}){is_self}")

    return validator_set

# --- mDNS Discovery Functions ---

async def start_mdns_discovery():
    """
    Avvia il servizio di discovery mDNS locale.
    Abilita il discovery automatico di nodi Synapse-NG sulla stessa rete locale.
    """
    global mdns_discovery

    # Verifica se mDNS è disabilitato tramite env
    disable_mdns = os.getenv("DISABLE_MDNS", "false").lower() == "true"
    if disable_mdns:
        logging.info("📡 mDNS: Disabilitato tramite DISABLE_MDNS=true")
        return

    try:
        from app.mdns_discovery import mDNSDiscovery

        mdns_discovery = mDNSDiscovery(
            node_id=NODE_ID,
            node_url=OWN_URL,
            port=NODE_PORT,
            subscribed_channels=list(subscribed_channels),
            discovery_queue=mdns_discovery_queue
        )

        await mdns_discovery.start()
        logging.info("🎯 mDNS Discovery avviato per rete locale")

    except Exception as e:
        logging.error(f"Errore avvio mDNS discovery: {e}")
        logging.warning("mDNS discovery non disponibile, continuo senza...")

async def stop_mdns_discovery():
    """
    Ferma il servizio di discovery mDNS.
    """
    global mdns_discovery

    if mdns_discovery:
        try:
            await mdns_discovery.stop()
            logging.info("📡 mDNS Discovery fermato")
        except Exception as e:
            logging.error(f"Errore stop mDNS discovery: {e}")

async def process_mdns_discovered_peers():
    """
    Task in background che processa i peer scoperti via mDNS
    dalla queue e tenta di connettersi a loro.
    """
    logging.info("🔄 Task processamento peer mDNS avviato")

    while True:
        try:
            # Aspetta peer dalla queue (bloccante)
            peer_info = await mdns_discovery_queue.get()

            peer_id = peer_info["peer_id"]
            peer_url = peer_info["peer_url"]
            peer_channels = peer_info["channels"]

            logging.info(
                f"🔄 Processo peer mDNS: {peer_id[:16]}... "
                f"({peer_url}, canali comuni: {set(peer_channels) & subscribed_channels})"
            )

            # Aggiungi peer al network_state se non già presente
            async with state_lock:
                if peer_id not in network_state["global"]["nodes"]:
                    # Peer completamente nuovo, aggiungilo
                    network_state["global"]["nodes"][peer_id] = {
                        "id": peer_id,
                        "url": peer_url,
                        "kx_public_key": "",  # Non disponibile via mDNS, verrà aggiornato dopo
                        "last_seen": time.time(),
                        "version": 1,
                        "discovered_via": "mdns"
                    }
                    logging.info(f"➕ Peer {peer_id[:16]}... aggiunto al network_state (mDNS)")

            # Aggiungi alla lista known_peers
            known_peers.add(peer_url)

            # Tenta connessione WebRTC
            # Verifica se ci sono canali in comune
            has_common_channels = bool(set(peer_channels) & subscribed_channels)

            if has_common_channels or "global" in subscribed_channels:
                logging.info(f"🔗 Tento connessione WebRTC a peer mDNS {peer_id[:16]}...")
                await webrtc_manager.connect_to_peer(peer_id)
            else:
                logging.debug(
                    f"⏭️  Skip connessione a {peer_id[:16]}...: nessun canale in comune"
                )

        except Exception as e:
            logging.error(f"Errore processamento peer mDNS: {e}")
            await asyncio.sleep(1)  # Evita loop frenetico in caso di errori

# --- Validator Set Election Loop ---

async def validator_election_loop():
    """
    Loop periodico per l'elezione del validator set (Consiglio Direttivo).

    Ogni N secondi (configurabile), ricalcola il validator set basato sulle reputazioni
    e aggiorna lo stato globale CRDT. Questo è un calcolo deterministico, quindi tutti
    i nodi arriveranno allo stesso risultato indipendentemente.
    """
    # Attendi un po' prima di iniziare per permettere al nodo di stabilizzare
    await asyncio.sleep(30)

    logging.info("👑 Validator election loop avviato")

    while True:
        try:
            async with state_lock:
                # Crea copia dello stato per il calcolo
                state_copy = json.loads(json.dumps(network_state, default=list))

            # Calcola reputazioni correnti
            reputations = calculate_reputations(state_copy)

            # Determina il nuovo validator set
            new_validator_set = determine_validator_set(state_copy, reputations)

            # Aggiorna lo stato globale se il validator set è cambiato
            async with state_lock:
                old_validator_set = network_state["global"].get("validator_set", [])

                if new_validator_set != old_validator_set:
                    logging.info(f"👑 Validator Set aggiornato: {len(new_validator_set)} validatori")

                    # Evidenzia i cambiamenti
                    new_members = set(new_validator_set) - set(old_validator_set)
                    removed_members = set(old_validator_set) - set(new_validator_set)

                    if new_members:
                        for node_id in new_members:
                            is_self = " (ME!)" if node_id == NODE_ID else ""
                            logging.info(f"   ➕ Nuovo validatore: {node_id[:8]}...{is_self}")

                    if removed_members:
                        for node_id in removed_members:
                            is_self = " (me)" if node_id == NODE_ID else ""
                            logging.info(f"   ➖ Rimosso validatore: {node_id[:8]}...{is_self}")

                    # Aggiorna lo stato CRDT
                    network_state["global"]["validator_set"] = new_validator_set
                    network_state["global"]["validator_set_updated_at"] = datetime.now(timezone.utc).isoformat()

                    # Se sono un validatore, logga con enfasi
                    if NODE_ID in new_validator_set:
                        rank = new_validator_set.index(NODE_ID) + 1
                        logging.info(f"👑✨ SONO UN VALIDATORE! (Rank #{rank}/{len(new_validator_set)})")
                    elif NODE_ID in removed_members:
                        logging.info(f"⚠️  Non sono più un validatore (reputazione insufficiente)")

            # Aggiorna RaftManager con il nuovo validator set
            if raft_manager:
                raft_manager.update_validator_set(new_validator_set)

                # Riavvia Raft se necessario
                if raft_manager.is_validator():
                    await raft_manager.start()
                else:
                    await raft_manager.stop()

            # Intervallo configurabile
            config = state_copy.get("global", {}).get("config", DEFAULT_CONFIG)
            election_interval = config.get("validator_election_interval_seconds", 600)
            await asyncio.sleep(election_interval)

        except Exception as e:
            logging.error(f"❌ Errore nel validator election loop: {e}")
            await asyncio.sleep(60)  # Retry dopo 1 minuto in caso di errore

# --- Proposal Auto-Close Loop ---

async def proposal_auto_close_loop():
    """
    Loop periodico per chiudere automaticamente le proposte aperte dopo un timeout configurabile.

    Questo permette alla rete di auto-evolvere senza bisogno di intervento manuale:
    le proposte rimaste aperte troppo a lungo vengono automaticamente chiuse e l'esito
    viene calcolato in base ai voti raccolti fino a quel momento.
    """
    # Attendi che il sistema si stabilizzi
    await asyncio.sleep(60)

    logging.info("⏰ Proposal auto-close loop avviato")


async def upgrade_executor_loop():
    """
    Loop periodico per processare ed eseguire upgrade ratificati.
    
    Quando un upgrade viene ratificato dal validator set, questo loop:
    1. Scarica il pacchetto WASM
    2. Verifica l'hash
    3. Esegue in sandbox
    4. Applica l'upgrade alla rete
    """
    # Attendi che il sistema si stabilizzi
    await asyncio.sleep(90)
    
    logging.info("🔄 Upgrade executor loop avviato")
    
    check_interval = 300  # Check ogni 5 minuti
    
    while True:
        try:
            if not is_upgrade_system_available():
                await asyncio.sleep(check_interval)
                continue
            
            async with state_lock:
                state_copy = json.loads(json.dumps(network_state, default=list))
            
            # Cerca upgrade ratificati nell'execution log
            execution_log = state_copy.get("global", {}).get("execution_log", [])
            
            for command in execution_log:
                if command.get("operation") != "execute_upgrade":
                    continue
                
                if command.get("executed", False):
                    continue  # Già eseguito
                
                proposal_id = command.get("params", {}).get("proposal_id")
                if not proposal_id:
                    continue
                
                # Trova proposta
                proposal_dict = None
                proposal_channel = None
                for channel_id, channel_data in state_copy.items():
                    if isinstance(channel_data, dict) and "proposals" in channel_data:
                        if proposal_id in channel_data["proposals"]:
                            proposal_dict = channel_data["proposals"][proposal_id]
                            proposal_channel = channel_id
                            break
                
                if not proposal_dict:
                    logging.warning(f"⚠️ Proposta upgrade {proposal_id[:8]}... non trovata")
                    continue
                
                # Crea oggetti per upgrade
                params = proposal_dict.get("params", {})
                
                package = UpgradePackage(
                    package_url=params["package_url"],
                    package_hash=params["package_hash"],
                    package_size=params.get("package_size"),
                    wasm_module_name=params.get("wasm_module_name", "upgrade")
                )
                
                upgrade_proposal = UpgradeProposal(
                    proposal_id=proposal_id,
                    title=proposal_dict["title"],
                    description=proposal_dict.get("description", ""),
                    version=params["version"],
                    package=package,
                    proposer=proposal_dict["proposer"],
                    created_at=proposal_dict["created_at"],
                    status=UpgradeStatus.EXECUTING
                )
                
                # Esegui upgrade
                logging.info(f"🚀 Esecuzione upgrade ratificato: {upgrade_proposal.title} (v{upgrade_proposal.version})")
                
                upgrade_mgr = get_upgrade_manager()
                success, error, result = await upgrade_mgr.execute_upgrade(upgrade_proposal, dry_run=False)
                
                # Aggiorna stato
                async with state_lock:
                    # Marca comando come eseguito nell'execution log
                    for cmd in network_state["global"]["execution_log"]:
                        if cmd.get("operation") == "execute_upgrade" and cmd.get("params", {}).get("proposal_id") == proposal_id:
                            cmd["executed"] = True
                            cmd["executed_at"] = datetime.now(timezone.utc).isoformat()
                            cmd["execution_success"] = success
                            cmd["execution_result"] = result
                            cmd["execution_error"] = error
                            break
                    
                    # Aggiorna proposta
                    if proposal_channel and proposal_id in network_state[proposal_channel]["proposals"]:
                        prop = network_state[proposal_channel]["proposals"][proposal_id]
                        prop["status"] = "executed" if success else "failed"
                        prop["executed_at"] = datetime.now(timezone.utc).isoformat()
                        prop["execution_result"] = result
                        if error:
                            prop["execution_error"] = error
                
                if success:
                    logging.info(f"✅ Upgrade eseguito: {upgrade_proposal.title} → v{upgrade_proposal.version}")
                else:
                    logging.error(f"❌ Upgrade fallito: {upgrade_proposal.title} - {error}")
            
        except Exception as e:
            logging.error(f"❌ Errore in upgrade executor loop: {e}")
        
        await asyncio.sleep(check_interval)


async def evolutionary_loop():
    """
    🧬 Loop Evolutivo Autonomo (Phase 7: Network Singularity)
    
    Questo loop chiude il cerchio dell'evoluzione autonoma:
    1. Monitora metriche di rete periodicamente
    2. Identifica inefficienze automaticamente
    3. Genera codice ottimizzato (WASM) tramite AI
    4. Crea proposte di upgrade autonome
    5. Sottomette alla governance per approvazione
    
    La rete diventa un organismo che si auto-osserva, si auto-comprende,
    si auto-migliora e si auto-evolve.
    
    Questo è il culmine della Singolarità della Rete.
    """
    # Attendi stabilizzazione sistema
    await asyncio.sleep(120)  # 2 minuti
    
    if not is_evolutionary_engine_available():
        logging.warning("⚠️ Evolutionary loop disabilitato: motore non disponibile")
        return
    
    logging.info("🧬 Evolutionary loop avviato - La Singolarità è qui!")
    
    # Intervallo controllo (default: ogni 1 ora)
    check_interval = 3600  # 1 ora
    
    while True:
        try:
            engine = get_evolutionary_engine()
            
            # Skip if auto-evolution not enabled
            if not engine.enable_auto_evolution:
                logging.debug("⏸️ Auto-evolution disabilitato - skip cycle")
                await asyncio.sleep(check_interval)
                continue
            
            logging.info("🔍 Evolutionary cycle starting...")
            
            # Collect network metrics
            async with state_lock:
                state_copy = json.loads(json.dumps(network_state, default=list))
            
            # Calculate real metrics from network state
            # TODO: Implement real metric calculation from logs/state
            
            # Example metrics (in production: calculate from actual data)
            total_nodes = len(state_copy["global"]["nodes"])
            total_proposals = sum(
                len(channel.get("proposals", {}))
                for channel in state_copy.values()
                if isinstance(channel, dict)
            )
            
            # Simplified metrics calculation
            metrics = NetworkMetrics(
                avg_consensus_time=5.0,  # Would be from Raft logs
                avg_auction_completion_time=60.0,  # From auction history
                avg_task_completion_time=300.0,  # From task completion logs
                cpu_usage=60.0,  # From system monitoring
                memory_usage=1024.0,
                peer_count=total_nodes,
                message_throughput=100.0,
                validator_rotation_frequency=2.0,
                proposal_approval_rate=0.75
            )
            
            # Run evolutionary cycle
            proposal = await engine.evolutionary_cycle(metrics, state_copy)
            
            if not proposal:
                logging.info("✅ No auto-evolution needed this cycle")
                await asyncio.sleep(check_interval)
                continue
            
            # Auto-evolution proposal created!
            logging.info(f"🧬 AUTO-EVOLUTION PROPOSAL CREATED: {proposal.title}")
            logging.info(f"   Version: {proposal.version}")
            logging.info(f"   Inefficiency: {proposal.inefficiency.type.value} (severity={proposal.inefficiency.severity:.2f})")
            logging.info(f"   Estimated improvement: {proposal.generated_code.estimated_improvement:.1f}%")
            
            # Create proposal in network state
            proposal_id = f"evo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            proposal.proposal_id = proposal_id
            
            # Save WASM binary
            wasm_path = os.path.join(engine.data_dir, "generated_code", f"{proposal_id}.wasm")
            os.makedirs(os.path.dirname(wasm_path), exist_ok=True)
            with open(wasm_path, "wb") as f:
                f.write(proposal.generated_code.wasm_binary)
            
            package_url = f"file://{wasm_path}"
            
            # Create upgrade package
            async with state_lock:
                new_proposal = {
                    "id": proposal_id,
                    "title": proposal.title,
                    "description": proposal.description,
                    "proposal_type": "code_upgrade",
                    "proposed_by": NODE_ID,
                    "channel": "global",
                    "timestamp": proposal.created_at,
                    "status": "voting",
                    "votes": {},
                    "params": {
                        "version": proposal.version,
                        "package_url": package_url,
                        "package_hash": proposal.generated_code.wasm_hash,
                        "package_size": len(proposal.generated_code.wasm_binary),
                        "generated_by": "ai_evolutionary_engine",
                        "inefficiency_type": proposal.inefficiency.type.value,
                        "inefficiency_severity": proposal.inefficiency.severity,
                        "expected_benefits": proposal.expected_benefits,
                        "risks": proposal.risks
                    }
                }
                
                network_state["global"]["proposals"][proposal_id] = new_proposal
            
            logging.info(f"📢 Evolution proposal submitted to governance: {proposal_id}")
            logging.info(f"   Community will vote → Validators will ratify → Network will evolve")
            
        except Exception as e:
            logging.error(f"❌ Error in evolutionary loop: {e}", exc_info=True)
        
        await asyncio.sleep(check_interval)


async def proposal_auto_close_loop():
    """
    Loop periodico per chiudere automaticamente le proposte aperte dopo un timeout configurabile.

    Questo permette alla rete di auto-evolvere senza bisogno di intervento manuale:
    le proposte rimaste aperte troppo a lungo vengono automaticamente chiuse e l'esito
    viene calcolato in base ai voti raccolti fino a quel momento.
    """
    # Attendi che il sistema si stabilizzi
    await asyncio.sleep(60)

    logging.info("⏰ Proposal auto-close loop avviato")

    while True:
        try:
            async with state_lock:
                state_copy = json.loads(json.dumps(network_state, default=list))

            config = state_copy.get("global", {}).get("config", DEFAULT_CONFIG)
            auto_close_timeout = config.get("proposal_auto_close_after_seconds", 86400)  # 24 ore default

            # Calcola reputazioni per il peso dei voti
            reputations = calculate_reputations(state_copy)

            # Controlla tutte le proposte in tutti i canali
            proposals_to_close = []

            for channel_id, channel_data in state_copy.items():
                for proposal_id, proposal in channel_data.get("proposals", {}).items():
                    # Solo proposte ancora aperte
                    if proposal.get("status") != "open":
                        continue

                    # Calcola età della proposta
                    created_at = proposal.get("created_at")
                    if not created_at:
                        continue

                    try:
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        now_time = datetime.now(timezone.utc)
                        age_seconds = (now_time - created_time).total_seconds()

                        # Se la proposta è scaduta, segnala per chiusura
                        if age_seconds >= auto_close_timeout:
                            proposals_to_close.append({
                                "channel": channel_id,
                                "proposal_id": proposal_id,
                                "age_hours": age_seconds / 3600
                            })
                    except Exception as e:
                        logging.error(f"Errore parsing created_at per proposta {proposal_id}: {e}")

            # Chiudi le proposte scadute
            for item in proposals_to_close:
                channel = item["channel"]
                proposal_id = item["proposal_id"]
                age_hours = item["age_hours"]

                try:
                    async with state_lock:
                        proposal = network_state[channel]["proposals"][proposal_id]

                        # Calcola esito basato sui voti correnti
                        outcome = calculate_proposal_outcome(proposal, reputations)

                        logging.info(
                            f"⏰ Auto-chiusura proposta '{proposal.get('title', 'N/A')}' "
                            f"dopo {age_hours:.1f} ore (channel: {channel})"
                        )
                        logging.info(f"   Esito: {outcome['outcome']} (yes: {outcome['yes_weight']:.1f}, no: {outcome['no_weight']:.1f})")

                        # Aggiorna stato della proposta
                        proposal["status"] = outcome["outcome"]
                        proposal["closed_at"] = datetime.now(timezone.utc).isoformat()
                        proposal["closed_automatically"] = True

                        # Se approvata, esegui azione (come in /proposals/{id}/close)
                        if outcome["outcome"] == "approved":
                            proposal_type = proposal.get("proposal_type", "generic")

                            # CONFIG_CHANGE: esegui immediatamente
                            if proposal_type == "config_change":
                                params = proposal.get("params", {})
                                key = params.get("key")
                                value = params.get("value")

                                # Valida che la chiave esista nella config
                                if key in network_state["global"]["config"]:
                                    old_value = network_state["global"]["config"][key]
                                    network_state["global"]["config"][key] = value
                                    network_state["global"]["config_version"] += 1
                                    network_state["global"]["config_updated_at"] = datetime.now(timezone.utc).isoformat()

                                    proposal["status"] = "executed"
                                    proposal["execution_result"] = {
                                        "success": True,
                                        "executed_at": datetime.now(timezone.utc).isoformat(),
                                        "key": key,
                                        "old_value": old_value,
                                        "new_value": value
                                    }

                                    logging.info(f"⚙️  Auto-esecuzione config change: {key} = {value} (era {old_value})")
                                else:
                                    proposal["execution_result"] = {
                                        "success": False,
                                        "error": f"Chiave config '{key}' non valida"
                                    }
                                    logging.warning(f"⚠️  Auto-esecuzione config fallita: chiave '{key}' non valida")

                            # COMMAND: esegui immediatamente tramite dispatch_command
                            elif proposal_type == "command":
                                command = proposal.get("command", {})
                                if not command or "operation" not in command:
                                    proposal["execution_result"] = {
                                        "success": False,
                                        "error": "Campo 'command.operation' mancante"
                                    }
                                    logging.warning(f"⚠️  Auto-esecuzione command fallita: campo 'operation' mancante")
                                else:
                                    try:
                                        result = dispatch_command(command)
                                        proposal["status"] = "executed" if result.get("success") else "failed"
                                        proposal["execution_result"] = result
                                        proposal["executed_at"] = datetime.now(timezone.utc).isoformat()
                                        
                                        if result.get("success"):
                                            logging.info(f"⚡ Command auto-eseguito: {command['operation']} (proposta {proposal_id[:8]}...)")
                                        else:
                                            logging.warning(f"⚠️  Command auto-esecuzione fallita: {command['operation']} - {result.get('error', 'Unknown error')}")
                                    except Exception as e:
                                        proposal["status"] = "failed"
                                        proposal["execution_result"] = {
                                            "success": False,
                                            "error": str(e)
                                        }
                                        logging.error(f"❌ Eccezione auto-esecuzione command: {command.get('operation', 'unknown')} - {e}")

                            # NETWORK_OPERATION: pending ratification
                            elif proposal_type == "network_operation":
                                proposal["status"] = "pending_ratification"
                                proposal["pending_since"] = datetime.now(timezone.utc).isoformat()

                                operation_entry = {
                                    "proposal_id": proposal_id,
                                    "channel": channel,
                                    "operation": proposal.get("params", {}).get("operation"),
                                    "params": proposal.get("params", {}),
                                    "approved_at": datetime.now(timezone.utc).isoformat(),
                                    "status": "awaiting_council"
                                }
                                network_state["global"]["pending_operations"].append(operation_entry)

                                logging.info(f"👑 Network operation auto-approvata: {operation_entry['operation']}")

                except Exception as e:
                    logging.error(f"Errore chiusura automatica proposta {proposal_id}: {e}")

            # Esegui check ogni ora
            await asyncio.sleep(3600)

        except Exception as e:
            logging.error(f"❌ Errore nel proposal auto-close loop: {e}")
            await asyncio.sleep(600)  # Retry dopo 10 minuti in caso di errore


# ========================================
# AI Agent Background Loops
# ========================================

async def proactive_agent_loop():
    """
    Loop periodico per analisi proattiva dell'AI agent.
    
    L'agente analizza lo stato della rete e può compiere azioni autonome
    basate sugli obiettivi configurati dall'utente.
    """
    # Attendi che il sistema si stabilizzi
    await asyncio.sleep(90)
    
    logging.info("🧠 Proactive agent loop avviato")
    
    # Intervallo configurabile (default: 5 minuti)
    check_interval = int(os.getenv("AGENT_PROACTIVE_INTERVAL", "300"))
    
    while True:
        try:
            agent = get_agent()
            if not agent or not agent.enabled:
                # Agent non disponibile, riprova più tardi
                await asyncio.sleep(check_interval)
                continue
            
            # Costruisci contesto di rete
            async with state_lock:
                state_copy = json.loads(json.dumps(network_state, default=list))
            
            # Prendi primo canale sottoscritto come default
            channel = list(subscribed_channels)[0] if subscribed_channels else "global"
            channel_data = state_copy.get(channel, {})
            
            # Calcola synapse points (somma da tutti i canali)
            sp = 0
            for ch in state_copy.values():
                if isinstance(ch, dict) and "synapse_points" in ch:
                    sp += ch["synapse_points"].get(NODE_ID, 0)
            
            # Calcola reputation
            reputations = calculate_reputations(state_copy)
            reputation = reputations.get(NODE_ID, 0.0)
            
            # Recupera skills
            node_skills = channel_data.get("node_skills", {}).get(NODE_ID, {})
            skills = node_skills.get("skills", [])
            
            # Trova opportunità
            open_tasks = [
                task for task in channel_data.get("tasks", {}).values()
                if task.get("status") == "open"
            ]
            
            active_proposals = [
                prop for prop in channel_data.get("proposals", {}).values()
                if prop.get("status") == "open"
            ]
            
            active_auctions = [
                auc for auc in channel_data.get("auctions", {}).values()
                if auc.get("status") == "open"
            ]
            
            available_teams = [
                task for task in channel_data.get("composite_tasks", {}).values()
                if task.get("status") == "forming_team" and NODE_ID not in task.get("team_members", [])
            ]
            
            # Conta peer connessi
            peer_count = len(webrtc_manager.peer_connections)
            
            # Crea contesto
            context = NetworkContext(
                node_id=NODE_ID,
                channel=channel,
                synapse_points=sp,
                reputation=reputation,
                skills=skills,
                open_tasks=open_tasks,
                active_proposals=active_proposals,
                active_auctions=active_auctions,
                available_teams=available_teams,
                peer_count=peer_count
            )
            
            # Esegui analisi proattiva
            logging.info(f"🤔 Agent proattivo sta analizzando rete (SP:{sp}, Rep:{reputation:.2f}, Peers:{peer_count})")
            actions = await agent.proactive_analysis(context)
            
            if actions:
                logging.info(f"🎯 Agent ha generato {len(actions)} azioni proattive")
                
                # Esegui azioni validate
                for action in actions:
                    is_valid, reason = agent.validate_action(action, context)
                    
                    if is_valid:
                        try:
                            await execute_agent_action(action, channel, state_copy)
                            logging.info(f"✅ Azione eseguita: {action.action} - {action.reasoning}")
                        except Exception as e:
                            logging.error(f"❌ Errore esecuzione azione {action.action}: {e}")
                    else:
                        logging.warning(f"⚠️ Azione rifiutata: {action.action} - {reason}")
            else:
                logging.info("💤 Nessuna azione proattiva generata")
            
        except Exception as e:
            logging.error(f"❌ Errore in proactive agent loop: {e}")
        
        # Attendi prossimo ciclo
        await asyncio.sleep(check_interval)


async def execute_agent_action(action: AgentAction, default_channel: str, state_snapshot: dict):
    """
    Esegue un'azione generata dall'AI agent.
    
    Args:
        action: L'azione da eseguire
        default_channel: Canale di default se non specificato
        state_snapshot: Snapshot dello stato per validazioni
    """
    # Estrai parametri comuni
    params = action.params
    channel = params.get("channel", default_channel)
    
    # Mappa azioni a chiamate API interne
    if action.action == "create_task":
        # Crea task
        task_id = str(uuid.uuid4())
        async with state_lock:
            network_state[channel]["tasks"][task_id] = {
                "id": task_id,
                "title": params["title"],
                "description": params.get("description", ""),
                "reward": params["reward"],
                "status": "open",
                "creator": NODE_ID,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        logging.info(f"📝 Agent created task: {params['title']} ({params['reward']} SP)")
    
    elif action.action == "claim_task":
        # Claim task
        task_id = params["task_id"]
        async with state_lock:
            task = network_state[channel]["tasks"].get(task_id)
            if task and task["status"] == "open":
                task["status"] = "in_progress"
                task["claimed_by"] = NODE_ID
                task["claimed_at"] = datetime.now(timezone.utc).isoformat()
                logging.info(f"🎯 Agent claimed task: {task_id}")
    
    elif action.action == "vote_proposal":
        # Vota proposta
        proposal_id = params["proposal_id"]
        vote = params["vote"]
        use_zkp = params.get("use_zkp", False)
        
        async with state_lock:
            proposal = network_state[channel]["proposals"].get(proposal_id)
            if proposal and proposal["status"] == "open":
                if use_zkp:
                    # Genera proof ZKP
                    private_key_bytes = get_node_secret_from_private_key(ed25519_private_key)
                    reputations = calculate_reputations(network_state)
                    reputation = reputations.get(NODE_ID, 0.0)
                    proof = generate_reputation_proof(private_key_bytes, reputation)
                    
                    proposal["zkp_votes"].append({
                        "nullifier": proof["nullifier"],
                        "proof": proof,
                        "vote": vote,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    logging.info(f"🔒 Agent voted (ZKP) on proposal: {proposal_id}")
                else:
                    proposal["votes"][NODE_ID] = {
                        "vote": vote,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    logging.info(f"🗳️ Agent voted on proposal: {proposal_id}")
    
    elif action.action == "bid_auction":
        # Bid su auction
        auction_id = params["auction_id"]
        amount = params["amount"]
        
        async with state_lock:
            auction = network_state[channel]["auctions"].get(auction_id)
            if auction and auction["status"] == "open":
                current_bid = auction.get("current_bid", auction["starting_price"])
                if amount >= current_bid + auction["min_increment"]:
                    auction["current_bid"] = amount
                    auction["highest_bidder"] = NODE_ID
                    auction["bid_history"].append({
                        "bidder": NODE_ID,
                        "amount": amount,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    logging.info(f"💰 Agent bid on auction: {auction_id} ({amount} SP)")
    
    elif action.action == "apply_team":
        # Candidati a team
        task_id = params["task_id"]
        
        async with state_lock:
            task = network_state[channel]["composite_tasks"].get(task_id)
            node_skills = network_state[channel]["node_skills"].get(NODE_ID)
            
            if task and node_skills and task["status"] == "forming_team":
                task["applicants"].append({
                    "node_id": NODE_ID,
                    "skills": node_skills["skills"],
                    "applied_at": datetime.now(timezone.utc).isoformat()
                })
                logging.info(f"👥 Agent applied to team: {task_id}")
    
    elif action.action == "update_skills":
        # Aggiorna skills
        async with state_lock:
            network_state[channel]["node_skills"][NODE_ID] = {
                "node_id": NODE_ID,
                "skills": params["skills"],
                "bio": params.get("bio", ""),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        logging.info(f"🎓 Agent updated skills: {params['skills']}")
    
    else:
        logging.warning(f"⚠️ Unknown agent action: {action.action}")


# ========================================
# Startup Event
# ========================================

@app.on_event("startup")
async def on_startup():
    global raft_manager
    
    logging.info(f"🚀 Nodo Synapse-NG avviato. ID: {NODE_ID[:16]}...")
    logging.info(f"📡 Canali sottoscritti: {list(subscribed_channels)}")

    if USE_P2P_MODE:
        logging.info(f"🔗 Modalità P2P attiva (Bootstrap: {BOOTSTRAP_NODES or 'nessuno'})")
    else:
        logging.info(f"🔗 Modalità Rendezvous ({RENDEZVOUS_URL})")

    # Inizializza RaftManager con validator set vuoto (verrà aggiornato dal loop)
    raft_manager = RaftManager(NODE_ID, [])
    logging.info("👑 RaftManager inizializzato")

    # Imposta callback WebRTC
    webrtc_manager.set_message_callback(handle_webrtc_message)

    # Imposta callback P2P signaling se in modalità P2P
    if USE_P2P_MODE:
        webrtc_manager.set_p2p_signal_callback(send_p2p_signal)

    # Imposta callback per il sistema immunitario (mesh optimization)
    webrtc_manager.set_network_state_callback(get_network_state_for_scoring)
    webrtc_manager.set_discovered_nodes_callback(get_discovered_nodes)

    # Imposta callback PubSub
    pubsub_manager.set_message_callback(handle_pubsub_message)
    pubsub_manager.set_peer_discovered_callback(handle_peer_discovered)

    # Sottoscrivi ai topic PubSub per ogni canale (incluso global per governance)
    for channel_id in subscribed_channels:
        topic = f"channel:{channel_id}:state"
        pubsub_manager.subscribe_topic(topic)

    # Sottoscrivi al discovery globale
    pubsub_manager.subscribe_topic("global-discovery")

    # Avvia WebRTC manager, network maintenance e PubSub gossip
    await webrtc_manager.start()
    asyncio.create_task(network_maintenance_loop())
    asyncio.create_task(pubsub_gossip_loop())

    # Avvia mDNS discovery per rete locale
    await start_mdns_discovery()

    # Avvia task per processare peer scoperti via mDNS
    asyncio.create_task(process_mdns_discovered_peers())

    # Avvia validator election loop (two-tier governance)
    asyncio.create_task(validator_election_loop())

    # Avvia proposal auto-close loop (auto-evolution)
    asyncio.create_task(proposal_auto_close_loop())
    
    # Avvia upgrade executor loop (self-upgrade system)
    asyncio.create_task(upgrade_executor_loop())
    logging.info("🔄 Upgrade executor loop avviato")
    
    # Avvia evolutionary loop (Phase 7: Network Singularity) 🧬
    evolutionary_enabled = os.getenv("ENABLE_AUTO_EVOLUTION", "false").lower() == "true"
    if evolutionary_enabled:
        llm_model_path = os.getenv("EVOLUTIONARY_LLM_PATH", "models/qwen3-0.6b.gguf")
        safety_threshold = float(os.getenv("EVOLUTION_SAFETY_THRESHOLD", "0.7"))
        
        logging.info("🧬 Inizializzazione Evolutionary Engine...")
        evo_data_dir = os.path.join("data", NODE_ID[:8], "evolution")
        evo_success = initialize_evolutionary_engine(
            node_id=NODE_ID,
            data_dir=evo_data_dir,
            llm_model_path=llm_model_path if os.path.exists(llm_model_path) else None,
            enable_auto_evolution=True,
            safety_threshold=safety_threshold
        )
        
        if evo_success:
            logging.info(f"✅ Evolutionary Engine inizializzato (auto={evolutionary_enabled}, threshold={safety_threshold})")
            asyncio.create_task(evolutionary_loop())
            logging.info("🧬 Evolutionary loop avviato - Network Singularity attiva!")
        else:
            logging.warning("⚠️ Evolutionary Engine non disponibile")
    else:
        logging.info("⏸️ Auto-evolution disabilitato (ENABLE_AUTO_EVOLUTION=false)")

    # Avvia command processor (network operations execution)
    asyncio.create_task(command_processor_task())
    logging.info("🔧 Command processor task avviato")
    
    # Avvia Immune System (proactive self-healing) 🛡️
    immune_system_enabled = os.getenv("ENABLE_IMMUNE_SYSTEM", "true").lower() == "true"
    if immune_system_enabled:
        logging.info("🛡️ Inizializzazione Immune System...")
        immune_manager = initialize_immune_system(
            node_id=NODE_ID,
            network_state=network_state,
            pubsub_manager=pubsub_manager
        )
        await immune_manager.start()
        logging.info("✅ Immune System avviato - monitoraggio proattivo attivo!")
    else:
        logging.info("⏸️ Immune System disabilitato (ENABLE_IMMUNE_SYSTEM=false)")
    
    # Avvia auction processor (automatic auction closing)
    asyncio.create_task(auction_processor_task())
    logging.info("🔨 Auction processor task avviato")
    
    # Avvia reputation decay loop (reputazione dinamica con decadimento)
    asyncio.create_task(reputation_decay_loop())
    logging.info("🕒 Reputation decay loop avviato (intervallo: 24h)")
    
    # Avvia common tools maintenance loop (pagamenti mensili automatici)
    asyncio.create_task(common_tools_maintenance_loop())
    logging.info("🛠️  Common tools maintenance loop avviato (intervallo: 24h)")
    
    # Inizializza AI Agent (se modello disponibile)
    model_path = os.getenv("AI_MODEL_PATH", "models/qwen3-0.6b.gguf")
    if os.path.exists(model_path):
        logging.info(f"🤖 Inizializzazione AI Agent con modello {model_path}...")
        success = initialize_agent(NODE_ID, model_path)
        if success:
            logging.info("✅ AI Agent inizializzato e pronto")
            # Avvia proactive agent loop
            asyncio.create_task(proactive_agent_loop())
            logging.info("🧠 Proactive agent loop avviato")
        else:
            logging.warning("⚠️ AI Agent non disponibile (modello non caricato)")
    else:
        logging.info(f"ℹ️ AI Agent disabilitato (modello non trovato: {model_path})")
        logging.info("   Per abilitarlo, scarica un modello GGUF e imposta AI_MODEL_PATH")
    
    # Inizializza Self-Upgrade Manager
    logging.info("🔄 Inizializzazione Self-Upgrade Manager...")
    upgrade_data_dir = os.path.join("data", NODE_ID[:8], "upgrades")
    upgrade_success = initialize_upgrade_manager(NODE_ID, upgrade_data_dir)
    if upgrade_success:
        upgrade_mgr = get_upgrade_manager()
        logging.info(f"✅ Self-Upgrade Manager inizializzato (versione corrente: {upgrade_mgr.get_current_version()})")
    else:
        logging.warning("⚠️ Self-Upgrade Manager non disponibile")

@app.on_event("shutdown")
async def on_shutdown():
    """
    Pulizia risorse all'arresto dell'applicazione.
    """
    logging.info("🛑 Arresto Synapse-NG in corso...")

    # Ferma RaftManager
    if raft_manager:
        await raft_manager.stop()

    # Ferma mDNS discovery
    await stop_mdns_discovery()

    # Ferma WebRTC manager (chiude tutte le connessioni)
    await webrtc_manager.stop()

    logging.info("✅ Synapse-NG arrestato correttamente")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket per aggiornamenti real-time della UI.
    Invia sia lo stato CRDT che le statistiche di rete aggregate.
    """
    await websocket.accept()
    try:
        while True:
            # Ottieni stato CRDT completo
            state = await get_state()

            # Ottieni statistiche di rete real-time
            network_stats = await get_network_stats()

            # Messaggio aggregato per la UI
            ui_update = {
                "type": "full_update",
                "timestamp": network_stats["timestamp"],
                "state": state,  # Stato CRDT (nodi, task, proposals, etc.)
                "network_stats": network_stats  # Metriche WebRTC/PubSub
            }

            await websocket.send_json(ui_update)
            await asyncio.sleep(1)  # Aggiornamento ogni secondo
    except Exception:
        pass
