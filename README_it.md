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
- ✅ **Canali tematici**: Partizionamento logico dei task (richiede sottoscrizione)
- ✅ **Lifecycle completo**: open → claimed → in_progress → completed
- ✅ **Propagazione CRDT**: Convergenza garantita via PubSub topic-based
- ✅ **Validazione transizioni**: Solo agli endpoint API
- ⚠️ **Sottoscrizione richiesta**: I nodi devono essere sottoscritti ai canali per ricevere aggiornamenti

### **Governance**
- ✅ **Sistema di proposte**: Ogni nodo può proporre cambiamenti
- ✅ **Voto ponderato**: Peso basato su reputazione (weight = 1 + log₂(reputation + 1))
- ✅ **Voting distribuito**: Voti propagati via PubSub
- ✅ **Reputazione dinamica**: Basata su contributi (+10 task, +1 voto)
- ✅ **Meritocrazia**: Nodi con alta reputazione hanno più influenza nelle decisioni

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

**⚠️ IMPORTANTE: Sottoscrizioni Canali**

Per ricevere task e messaggi su un canale, **tutti i nodi devono essere sottoscritti** al topic corrispondente tramite `SUBSCRIBED_CHANNELS`. Se un nodo non è sottoscritto a un canale, **non riceverà** gli aggiornamenti di quel canale tramite PubSub.

Esempio:
- `SUBSCRIBED_CHANNELS=sviluppo_ui` → riceve solo task del canale `sviluppo_ui`
- `SUBSCRIBED_CHANNELS=sviluppo_ui,marketing` → riceve task di entrambi i canali

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

### **Governance**

```bash
# Crea proposta
POST /proposals?channel=CHANNEL_ID
Content-Type: application/json
{"title": "Proposal Title", "description": "Details", "proposal_type": "generic"}

# Vota su proposta
POST /proposals/{proposal_id}/vote?channel=CHANNEL_ID
Content-Type: application/json
{"vote": "yes"}  # o "no"

# Chiudi proposta e calcola esito
POST /proposals/{proposal_id}/close?channel=CHANNEL_ID

# Dettagli proposta (include pesi voti)
GET /proposals/{proposal_id}/details?channel=CHANNEL_ID
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

Testa convergenza, WebRTC, PubSub, task lifecycle, reputazione, economia e governance.

```bash
# Tutti i test (base + economia + governance)
./test_suite.sh

# Solo test base
./test_suite.sh base

# Solo test governance (voto ponderato)
./test_suite.sh governance

# Solo test economia (Synapse Points)
./test_suite.sh economy

# Mostra opzioni
./test_suite.sh help
```

**Scenari testati:**

**Test Base (Scenari 1-6):**
1. ✅ Avvio a freddo (3 nodi)
2. ✅ Connessioni WebRTC (verifica peer connections e data channels)
3. ✅ Sottoscrizioni PubSub (verifica topic subscriptions)
4. ✅ Ingresso nuovo nodo (scalabilità dinamica)
5. ✅ Task lifecycle completo (create → claim → progress → complete)
6. ✅ Sistema reputazione (+10 per task completati)

**Test Economia e Governance (Scenari 7-8):**
7. ✅ **Voto Ponderato**: Verifica che nodi con alta reputazione abbiano più influenza (peso = 1 + log₂(rep + 1))
8. ✅ **Economia SP**: Verifica trasferimento deterministico di Synapse Points (creazione task con reward, congelamento SP, trasferimento al completamento)

**📚 Documentazione Test:**
- `TEST_ECONOMIA_GOVERNANCE.md` - Documentazione completa
- `QUICK_START_TESTS.md` - Guida rapida
- `ESEMPI_API_TEST.md` - Esempi API per test manuali

**⚠️ Note sui Test:**
- Tutti i nodi devono essere sottoscritti agli stessi canali per i test cross-node
- I timeout sono calibrati per WebRTC + PubSub (più lenti del gossip HTTP diretto)
- La test suite viene eseguita automaticamente nel pre-push git hook
- I test economia/governance verificano il determinismo: tutti i nodi devono concordare su balance e voti

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
     │   (sottoscrizione al canale)   │
     │                                │
     │ 5. MESSAGE (Gossip)            │
     │<══SynapseSub══════════════════>│
     │    Topic: channel:dev:state    │
     │    (solo se entrambi           │
     │     sottoscritti al topic!)    │
     │                                │
     │ 6. Forward ad altri peer       │
     │         nella mesh             │
     └────────────────────────────────┘
```

**Note sul Flusso:**
- Passo 4: I nodi annunciano i topic a cui sono interessati (`SUBSCRIBED_CHANNELS`)
- Passo 5: I messaggi vengono inoltrati **solo ai peer sottoscritti** al topic
- Se un nodo non è sottoscritto, non riceverà messaggi su quel topic

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

### Sistema di Reputazione e Voto Ponderato

**Calcolo Reputazione:**
```python
# Azioni che incrementano reputazione
- Completamento task: +10
- Voto su proposta: +1

# Calcolo (app/main.py:846-858)
for task in channel.tasks:
    if task.status == "completed":
        reputation[task.assignee] += 10

for proposal in channel.proposals:
    for voter_id in proposal.votes:
        reputation[voter_id] += 1
```

**Voto Ponderato:**
```python
# Peso del voto basato su reputazione (app/main.py:914-915)
def calculate_vote_weight(reputation: int) -> float:
    return 1.0 + math.log2(reputation + 1)

# Esempi:
# Reputazione 0 → Peso 1.0
# Reputazione 1 → Peso 2.0
# Reputazione 20 → Peso 5.4
# Reputazione 100 → Peso 7.7

# Esito proposta (app/main.py:966-969)
if yes_weight > no_weight:
    outcome = "approved"
else:
    outcome = "rejected"
```

**Esempio pratico:**
```
Scenario: Proposta con 3 nodi
- Node A: reputazione 20 (2 task completati) → peso voto ~5.4
- Node B: reputazione 1 (1 voto) → peso voto ~2.0
- Node C: reputazione 0 → peso voto 1.0

Votazione:
- Node A vota NO → peso 5.4
- Node B vota YES → peso 2.0
- Node C vota YES → peso 1.0

Risultato:
- YES totale: 3.0
- NO totale: 5.4
- Esito: REJECTED ✅

La meritocrazia prevale: il nodo più esperto ha più influenza!
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
