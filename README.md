# Synapse-NG (Next Generation)

**Un organismo digitale decentralizzato, scalabile e intelligente.**

Synapse-NG è una rete peer-to-peer completamente decentralizzata che si auto-organizza come un organismo vivente. Non esiste autorità centrale, nessun server obbligatorio, nessun leader. Ogni nodo è un agente autonomo che collabora per formare una coscienza collettiva, prendere decisioni e portare a termine compiti.

## 🧬 Filosofia

Ogni nodo è un "neurone" sovrano. La rete "vive" attraverso principi fondamentali:

- **Identità Sovrana**: Ogni nodo possiede la propria identità crittografica (Ed25519), immutabile e non falsificabile.
- **Comunicazione P2P**: Connessioni WebRTC dirette tra peer, senza intermediari.
- **Gossip Intelligente**: Protocollo SynapseSub topic-based per sincronizzare solo ciò che serve.
- **Consenso senza Conflitti (CRDT)**: Lo stato condiviso converge matematicamente allo stesso risultato su tutti i nodi.
- **Bootstrap Decentralizzato**: Nessun server centrale obbligatorio, bootstrap da peer esistenti.
- **Intelligenza Collettiva**: Sistema di proposte, voti e reputazione distribuito.

## ✨ Architettura SynapseComms v2.0

Synapse-NG implementa un'architettura di comunicazione a tre livelli:

### **Livello 1: WebRTC Transport Layer**
- Connessioni P2P dirette tra nodi
- `RTCDataChannel` per comunicazione bidirezionale
- Supporto signaling sia centralizzato che P2P

### **Livello 2: SynapseSub Protocol**
- PubSub topic-based su WebRTC
- Mesh di peer per ogni topic
- Deduplica automatica messaggi
- Forward intelligente basato su interesse

### **Livello 3: Application Layer**
- Canali tematici (sharding)
- Task management distribuito
- Governance e voting
- Sistema di reputazione

```
┌─────────────────────────────────────────────────┐
│            APPLICATION LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Channels │  │  Tasks   │  │Governance│     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│          SYNAPSESUB PROTOCOL                    │
│  ┌──────────────────────────────────────┐      │
│  │  PubSub Topics + Message Routing     │      │
│  │  ANNOUNCE | MESSAGE | I_HAVE | ...   │      │
│  └──────────────────────────────────────┘      │
├─────────────────────────────────────────────────┤
│         WEBRTC TRANSPORT LAYER                  │
│  ┌──────────────────────────────────────┐      │
│  │   RTCPeerConnection + DataChannel     │      │
│  │   P2P Signaling (tunneling)           │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

## 🚀 Features

### **Comunicazione**
- ✅ **WebRTC P2P**: Connessioni dirette tra nodi, bassa latenza
- ✅ **SynapseSub**: Protocollo PubSub ottimizzato per mesh network
- ✅ **Topic-based routing**: Solo i dati rilevanti vengono trasmessi
- ✅ **Deduplica automatica**: Cache di messaggi visti

### **Decentralizzazione**
- ✅ **Bootstrap P2P**: Handshake con peer esistenti
- ✅ **P2P Signaling**: Tunneling attraverso peer connessi
- ✅ **Rendezvous opzionale**: Server centrale solo per facilità
- ✅ **Nessun SPOF**: Nessun single point of failure

### **Task Management**
- ✅ **Canali tematici**: Partizionamento logico dei task
- ✅ **Lifecycle completo**: open → claimed → in_progress → completed
- ✅ **Propagazione CRDT**: Convergenza garantita
- ✅ **Validazione transizioni**: Solo agli endpoint API

### **Governance**
- ✅ **Sistema di proposte**: Ogni nodo può proporre cambiamenti
- ✅ **Voting distribuito**: Voti propagati via gossip
- ✅ **Reputazione dinamica**: Basata su contributi (+10 task, +1 voto)

## 📦 Installazione

### Requisiti
- Docker & Docker Compose
- Python 3.9+ (per sviluppo locale)
- `jq` (per test scripts)

### Quick Start (Modalità Rendezvous)

```bash
# Clone
git clone https://github.com/your-org/synapse-ng.git
cd synapse-ng

# Avvia rete con Rendezvous Server
docker-compose up --build -d

# Verifica stato
curl http://localhost:8001/state | jq '.global.nodes | length'

# Run test suite
./test_suite.sh
```

### Quick Start (Modalità P2P Pura)

```bash
# Avvia rete completamente decentralizzata
docker-compose -f docker-compose.p2p.yml up --build -d

# Verifica connessioni P2P
curl http://localhost:8001/webrtc/connections | jq

# Run test P2P
./test_p2p.sh
```

## ⚙️ Configurazione

### Variabili d'Ambiente

| Variabile | Descrizione | Richiesto | Default |
|-----------|-------------|-----------|---------|
| `OWN_URL` | URL di questo nodo | ✅ Sì | - |
| `RENDEZVOUS_URL` | URL del Rendezvous Server | ⚠️ Solo per modalità Rendezvous | - |
| `BOOTSTRAP_NODES` | Lista di peer bootstrap (CSV) | ⚠️ Solo per modalità P2P | - |
| `SUBSCRIBED_CHANNELS` | Canali da sottoscrivere (CSV) | No | "" |
| `NODE_PORT` | Porta del nodo | No | 8000 |

### Modalità Operative

#### **Modalità 1: Rendezvous (Più semplice)**

Usa un server centrale per discovery e signaling.

```yaml
environment:
  - OWN_URL=http://node-1:8000
  - RENDEZVOUS_URL=http://rendezvous:8080
  - SUBSCRIBED_CHANNELS=sviluppo_ui
```

**Pro**: Setup semplice, discovery automatico
**Contro**: Punto centrale di fallimento

#### **Modalità 2: P2P Puro (Decentralizzato)**

Nessun server centrale, bootstrap da peer esistenti.

```yaml
environment:
  - OWN_URL=http://node-2:8000
  - BOOTSTRAP_NODES=http://node-1:8000,http://node-3:8000
  - SUBSCRIBED_CHANNELS=sviluppo_ui
```

**Pro**: Completamente decentralizzato, resiliente
**Contro**: Richiede almeno un bootstrap node

## 📡 API Endpoints

### **Stato e Monitoring**

```bash
# Stato globale della rete
GET /state

# Canali sottoscritti
GET /channels

# Connessioni WebRTC
GET /webrtc/connections

# Statistiche PubSub
GET /pubsub/stats
```

### **Task Management**

```bash
# Crea task
POST /tasks?channel=CHANNEL_ID
Content-Type: application/json
{"title": "Fix bug"}

# Prendi in carico
POST /tasks/{task_id}/claim?channel=CHANNEL_ID

# Segna in progresso
POST /tasks/{task_id}/progress?channel=CHANNEL_ID

# Completa
POST /tasks/{task_id}/complete?channel=CHANNEL_ID

# Elimina
DELETE /tasks/{task_id}?channel=CHANNEL_ID
```

### **Bootstrap P2P**

```bash
# Handshake iniziale
POST /bootstrap/handshake
{"peer_id": "NODE_ID", "peer_url": "http://node:8000"}

# Relay signaling P2P
POST /p2p/signal/relay
{"from_peer": "ID_A", "to_peer": "ID_C", "type": "offer", "payload": {...}}

# Ricevi signaling P2P
POST /p2p/signal/receive
{"from_peer": "ID_A", "type": "answer", "payload": {...}}
```

## 🧪 Testing

### Test Suite Completa

Testa convergenza, WebRTC, PubSub, task lifecycle, reputazione.

```bash
./test_suite.sh
```

**Scenari testati:**
1. ✅ Avvio a freddo (3 nodi)
2. ✅ Connessioni WebRTC
3. ✅ Sottoscrizioni PubSub
4. ✅ Ingresso nuovo nodo
5. ✅ Task lifecycle completo
6. ✅ Sistema reputazione

### Test WebRTC + SynapseSub

```bash
./test_webrtc.sh
```

**Verifica:**
- Connessioni WebRTC dirette
- Statistiche PubSub
- Gossip via DataChannel
- Logs di debugging

### Test P2P Decentralizzato

```bash
./test_p2p.sh
```

**Verifica:**
- Bootstrap da peer
- P2P signaling tunneling
- Gossip senza Rendezvous
- Rete completamente autonoma

## 🏗️ Architettura Dettagliata

### Struttura File

```
synapse-ng/
├── app/
│   ├── main.py                    # Application server
│   ├── webrtc_manager.py          # WebRTC connection manager
│   ├── synapsesub_protocol.py     # PubSub protocol
│   ├── identity.py                # Identità crittografica
│   └── templates/                 # UI templates
├── rendezvous/
│   └── main.py                    # Rendezvous server (opzionale)
├── docker-compose.yml             # Config Rendezvous mode
├── docker-compose.p2p.yml         # Config P2P mode
├── test_suite.sh                  # Test completo
├── test_webrtc.sh                 # Test WebRTC/PubSub
├── test_p2p.sh                    # Test P2P puro
└── README.md                      # Questo file
```

### Flusso di Comunicazione

```
┌─────────┐                      ┌─────────┐
│ Node A  │                      │ Node B  │
└────┬────┘                      └────┬────┘
     │                                │
     │ 1. Bootstrap/Discovery         │
     │───────────────────────────────>│
     │                                │
     │ 2. WebRTC Signaling            │
     │<──────────────────────────────>│
     │   (Rendezvous o P2P Tunnel)    │
     │                                │
     │ 3. RTCDataChannel Aperto       │
     │<═══════════════════════════════>│
     │                                │
     │ 4. ANNOUNCE Topic              │
     │───SynapseSub──────────────────>│
     │                                │
     │ 5. MESSAGE (Gossip)            │
     │<══SynapseSub══════════════════>│
     │    Topic: channel:dev:state    │
     │                                │
     │ 6. Forward ad altri peer       │
     │         nella mesh             │
     └────────────────────────────────┘
```

### CRDT e Convergenza

Lo stato distribuito usa **Last-Write-Wins (LWW)** basato su timestamp:

```python
# Merge logic (app/main.py:196-201)
if incoming_task["updated_at"] > local_task["updated_at"]:
    local_state["tasks"][task_id] = incoming_task
```

- **Validazione transizioni**: Solo negli endpoint API
- **Nel gossip**: Timestamp è fonte di verità
- **Convergenza**: Garantita matematicamente (CRDT)

### Sistema di Reputazione

```
Azioni che incrementano reputazione:
- Completamento task: +10
- Voto su proposta: +1

Calcolo (app/main.py:606-613):
for task in channel.tasks:
    if task.status == "completed":
        reputation[task.assignee] += 10

for proposal in channel.proposals:
    for voter_id in proposal.votes:
        reputation[voter_id] += 1
```

## 🔮 Roadmap Futura

- [ ] **mDNS Discovery**: Discovery locale senza bootstrap
- [ ] **DHT**: Distributed Hash Table per lookup peer
- [ ] **Encryption E2E**: Cifratura payload oltre a WebRTC
- [ ] **NAT Traversal**: STUN/TURN integrati
- [ ] **Mobile Nodes**: Supporto nodi mobili/intermittenti
- [ ] **Sharding Dinamico**: Bilanciamento automatico canali
- [ ] **Consensus avanzato**: Raft/PBFT per decisioni critiche

## 🤝 Contributing

Contributi benvenuti! Per feature importanti, apri prima una issue per discutere.

```bash
# Setup sviluppo
pip install -r requirements.txt

# Run local node
python -m uvicorn app.main:app --reload --port 8000
```

## 📄 License

MIT License - vedi [LICENSE](LICENSE) per dettagli.

## 🙏 Acknowledgments

Ispirato da:
- **libp2p**: Modular P2P networking stack
- **GossipSub**: PubSub protocol per mesh networks
- **WebRTC**: Standard P2P per il web
- **IPFS**: InterPlanetary File System
- **Holochain**: Agent-centric distributed computing

---

**Synapse-NG** - Dove ogni nodo è un neurone, e insieme formano un organismo vivente. 🧠✨
