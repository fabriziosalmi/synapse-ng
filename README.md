# Synapse-NG (Next Generation)

**Un organismo digitale decentralizzato, ora scalabile e intelligente.**

Synapse-NG è una rete peer-to-peer che si auto-organizza come un organismo vivente. Non esiste autorità centrale, nessun server, nessun leader. Ogni nodo è un agente autonomo che collabora per formare una coscienza collettiva, prendere decisioni e portare a termine compiti.

Grazie a un'architettura a **canali (sharding)**, la rete è in grado di scalare gestendo contesti multipli e isolati, garantendo efficienza e flessibilità.

## 🧬 Filosofia

Ogni nodo è un "neurone" sovrano. La rete "vive" attraverso principi fondamentali:

- **Identità Sovrana**: Ogni nodo possiede la propria identità crittografica (Ed25519), immutabile e non falsificabile.
- **Gossip Intelligente**: I nodi "chiacchierano" per sincronizzare lo stato, ma solo per i canali di interesse comune, riducendo drasticamente il carico di rete.
- **Consenso senza Conflitti (CRDT)**: Lo stato condiviso (task, voti) converge matematicamente allo stesso risultato su tutti i nodi, anche in presenza di latenza di rete e aggiornamenti concorrenti.
- **Intelligenza Collettiva**: La rete può prendere decisioni tramite un sistema di proposte e voti, e misura il merito dei suoi membri attraverso un punteggio di reputazione dinamico.
- **Comunicazione Sicura**: I nodi possono stabilire canali di chat privati e cifrati end-to-end.

## ✨ Features

Synapse-NG è evoluto da una semplice rete di discovery a una piattaforma per l'organizzazione decentralizzata.

- **Architettura a Canali (Sharding)**: Lo stato globale è partizionato in "canali" tematici. I nodi sottoscrivono solo i canali di loro interesse, garantendo la scalabilità.
- **Identità Criptografica Forte**: L'ID di ogni nodo è la sua chiave pubblica Ed25519. Ogni comunicazione è firmata digitalmente e verificata.
- **Discovery Dinamico**: Un semplice **Rendezvous Server** permette ai nodi di trovarsi a vicenda senza configurazioni statiche, facilitando il bootstrap della rete.
- **Gestione Task Decentralizzata**: Un sistema completo per creare, assegnare e completare task. La sincronizzazione è gestita da CRDT (Last-Write-Wins & Observed-Remove Sets) per garantire coerenza.
- **Governance On-Chain**: La rete può auto-governarsi tramite un sistema di proposte e votazioni. Le decisioni vengono ratificate in modo decentralizzato.
- **Reputazione Dinamica**: Ogni nodo calcola localmente un punteggio di reputazione per tutti gli altri, basato su contributi verificabili come il completamento di task e la partecipazione alla governance.
- **Chat Privata E2E Cifrata**: I nodi possono stabilire canali di comunicazione privati utilizzando un protocollo di crittografia ibrida (X25519 + AES-GCM).

## 🚀 Quick Start

### Requisiti
- Docker & Docker Compose
- `curl` e `jq` (per interagire e visualizzare l'output JSON)

### Avvia la Rete

Il `docker-compose.yml` avvia un ecosistema completo: un Rendezvous Server e tre nodi Synapse-NG.

```bash
# Avvia tutti i servizi in background
docker-compose up --build -d
```

Apri i pannelli di controllo dei singoli nodi nel browser:
- **Nodo 1**: http://localhost:8001
- **Nodo 2**: http://localhost:8002
- **Nodo 3**: http://localhost:8003

Per fermare la rete:
```bash
docker-compose down -v # L'opzione -v rimuove anche i volumi con le chiavi
```

## 🔬 Esempi di Interazione con cURL

Dopo aver avviato la rete, apri un terminale e usa questi comandi per interagire con i nodi.

### 1. Controllare lo Stato di un Nodo
```bash
# Interroga lo stato completo visto dal nodo 1
curl -s http://localhost:8001/state | jq
```

### 2. Gestire i Canali
```bash
# Fai in modo che il nodo 1 si unisca al canale "marketing"
curl -s -X POST http://localhost:8001/channels/join -H "Content-Type: application/json" -d '{"channel_id": "marketing"}' | jq

# Verifica che il nodo 1 sia ora iscritto a 3 canali (global, sviluppo_ui, marketing)
curl -s http://localhost:8001/channels | jq
```

### 3. Creare e Gestire un Task
```bash
# Nodo 2 crea un nuovo task nel canale "sviluppo_ui"
TASK_ID=$(curl -s -X POST "http://localhost:8002/tasks?channel=sviluppo_ui&title=Refactor+del+motore+3D" | jq -r '.id')
echo "Task creato con ID: $TASK_ID"

# Attendi qualche secondo per il gossip, poi verifica che il nodo 1 veda il task
sleep 8
curl -s http://localhost:8001/state | jq '.sviluppo_ui.tasks["'$TASK_ID'"]

# Nodo 1 prende in carico il task
curl -s -X POST "http://localhost:8001/tasks/$TASK_ID/claim?channel=sviluppo_ui" | jq
```

### 4. Partecipare alla Governance
```bash
# Nodo 3 crea una proposta di governance nel canale globale
PROP_ID=$(curl -s -X POST "http://localhost:8003/proposals?channel=global" -H "Content-Type: application/json" -d '{"title": "Aumentare il budget per il marketing", "description": "Propongo di raddoppiare il budget."}' | jq -r '.id')
echo "Proposta creata con ID: $PROP_ID"

sleep 8

# Nodo 1 e 2 votano sulla proposta
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/vote?channel=global" -H "Content-Type: application/json" -d '{"choice": "yes"}' > /dev/null
curl -s -X POST "http://localhost:8002/proposals/$PROP_ID/vote?channel=global" -H "Content-Type: application/json" -d '{"choice": "no"}' > /dev/null

# Verifica lo stato dei voti sul nodo 3
curl -s http://localhost:8003/state | jq '.global.proposals["'$PROP_ID'"].votes'
```

## 🔧 Configurazione Nodo

La configurazione di un nodo avviene tramite variabili d'ambiente nel file `docker-compose.yml`.

```yaml
# Esempio di configurazione per un nodo
environment:
  - NODE_PORT=8000
  # L'URL del server di discovery
  - RENDEZVOUS_URL=http://rendezvous:8080
  # L'URL pubblico che questo nodo userà per registrarsi
  - OWN_URL=http://node-1:8000
  # Lista di canali tematici a cui iscriversi all'avvio (separati da virgola)
  - SUBSCRIBED_CHANNELS=sviluppo_ui,marketing
```

## 🏗️ Architettura

### Stack Tecnologico
- **Backend**: FastAPI (Python 3.9+)
- **Crittografia**: `cryptography` (Ed25519 per le firme, X25519 per lo scambio chiavi, AES-GCM per la cifratura simmetrica)
- **Frontend**: La UI 3D (in `index.html`) è un visualizzatore che interpreta lo stato ricevuto via WebSocket.

### Struttura Progetto
```
synapse-ng/
├── app/                  # Codice del nodo Synapse-NG
│   ├── main.py           # Server FastAPI con tutta la logica
│   └── templates/
│       └── index.html    # Visualizzazione 3D
├── rendezvous/           # Codice del server di discovery
│   ├── main.py
│   └── Dockerfile
├── docker-compose.yml    # Orchestra l'intera rete
└── README.md             # Questo file
```

### Protocollo di Gossip Channel-Aware

Il vecchio approccio "inonda tutti" è stato sostituito da un protocollo più efficiente:

1.  **Handshake**: Nodo A contatta un peer B e chiede `GET /channels`.
2.  **Intersezione**: Nodo A calcola i canali in comune con B.
3.  **Gossip Mirato**: Nodo A invia un pacchetto di gossip firmato per ogni canale in comune, usando `POST /gossip`. Il pacchetto contiene `channel_id` per specificare il contesto.

Questo riduce drasticamente la ridondanza e permette alla rete di scalare a un gran numero di canali e nodi.

### Stato della Rete (Multi-Canale)

Lo stato non è più monolitico. È un dizionario di canali. Il canale `global` è speciale e contiene la "verità" sui nodi e la governance di sistema.

```json
{
  "global": {
    "nodes": {
      "NODE_ID_1": { "id": "...", "url": "...", "kx_public_key": "...", "reputation": 50 }
    },
    "proposals": { /* Proposte a livello di rete */ }
  },
  "sviluppo_ui": {
    "participants": ["NODE_ID_1", "NODE_ID_2"],
    "tasks": { /* Task relativi alla UI */ },
    "proposals": { /* Proposte relative alla UI */ }
  }
}
```

## 📊 API Endpoints Principali

La maggior parte degli endpoint richiede un parametro di query `?channel=...` per specificare il contesto.

- `GET /state`: Stato completo (con reputazione calcolata) visibile dal nodo.
- `GET /channels`: Restituisce i canali sottoscritti (usato per l'handshake).
- `POST /channels/join` & `/leave`: Per iscriversi o lasciare un canale.

- `POST /gossip`: Endpoint principale per la sincronizzazione (riceve pacchetti per canale).

- `POST /tasks?channel=...`: Crea un task in un canale specifico.
- `POST /tasks/{id}/claim?channel=...`: Prende in carico un task.

- `POST /proposals?channel=...`: Crea una proposta in un canale.
- `POST /proposals/{id}/vote?channel=...`: Vota una proposta.

- `POST /chat/initiate`: Stabilisce una sessione di chat E2E cifrata.
- `POST /chat/send/{recipient_id}`: Invia un messaggio cifrato.

## 🔮 Visione Futura

Con questa architettura scalabile, le possibilità sono immense:

- **Inter-Channel Communication**: Nodi "bridge" che inoltrano selettivamente informazioni tra canali.
- **Reputazione Ponderata**: Il voto di un nodo con alta reputazione potrebbe valere di più.
- **Storage Decentralizzato**: Integrare IPFS per associare file a task o proposte.
- **Plugin e Smart Contract**: Un sistema per eseguire codice custom in modo sicuro all'interno della rete.

---

**"La rete non ha centro. La rete È il centro."**