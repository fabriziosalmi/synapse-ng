# Auction System - Competitive Task Market

**Decentralized Task Allocation via Competitive Bidding**

Version: 2.0  
Last Updated: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Complete Workflow](#complete-workflow)
4. [API Reference](#api-reference)
5. [Bid Selection Algorithm](#bid-selection-algorithm)
6. [Economic Model](#economic-model)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## Overview

The **Auction System** replaces the traditional "first-come-first-served" task allocation with a **competitive decentralized marketplace** where tasks are assigned based on an algorithm that weighs:

- **Cost** (40%): Rewards lower bids
- **Reputation** (40%): Rewards reliable nodes with positive track record
- **Time** (20%): Rewards faster delivery

This creates a **dynamic internal economy** that rewards efficiency, reliability, and quality—not just speed in claiming a task.

### Why Auctions?

**Traditional System Problems**:
- Fast clickers win regardless of skill
- No quality consideration
- No market-driven pricing
- Inefficient resource allocation

**Auction System Benefits**:
- ✅ Quality-driven allocation
- ✅ Market-based pricing discovery
- ✅ Reputation incentives
- ✅ Optimal resource matching
- ✅ Community benefit maximization

---

## Architettura

### Schema Task v2

Il nuovo schema `task_v2` introduce l'oggetto `auction`:

```json
{
  "title": "Implementa feature X",
  "description": "Dettagli del task...",
  "status": "auction_open",
  "auction": {
    "enabled": true,
    "status": "open",
    "max_reward": 500,
    "deadline": "2025-10-03T12:00:00Z",
    "bids": {
      "peer_id_1": {
        "amount": 400,
        "reputation": 120,
        "estimated_days": 3,
        "timestamp": "2025-10-02T10:00:00Z"
      },
      "peer_id_2": {
        "amount": 450,
        "reputation": 80,
        "estimated_days": 2,
        "timestamp": "2025-10-02T11:00:00Z"
      }
    },
    "selected_bid": null
  }
}
```

### Campi Auction

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `enabled` | boolean | Se true, il task usa il meccanismo d'asta |
| `status` | enum | `open`, `closed`, `finalized` |
| `max_reward` | integer | Ricompensa massima offerta dal creator |
| `deadline` | string (ISO) | Timestamp di scadenza dell'asta |
| `bids` | object | Dizionario di offerte: `{peer_id: bid_data}` |
| `selected_bid` | string | ID del peer vincitore (dopo selezione) |

### Stati del Task con Asta

```
auction_open → auction_closed → claimed → in_progress → completed
```

- **auction_open**: Asta attiva, accetta bid
- **auction_closed**: Deadline passata, nessuna bid ricevuta (torna a `open` per claim tradizionale)
- **claimed**: Vincitore selezionato, task assegnato
- **in_progress**: Il vincitore sta lavorando al task
- **completed**: Task completato, reward trasferita

---

## Flusso Completo

### 1. Creazione Task con Asta

**Endpoint:** `POST /tasks?channel=dev_ui`

**Payload:**
```json
{
  "title": "Implementa dashboard analytics",
  "description": "Crea dashboard con grafici real-time",
  "enable_auction": true,
  "max_reward": 500,
  "auction_deadline_hours": 48,
  "tags": ["ui", "analytics"]
}
```

**Cosa succede:**
- Schema automaticamente impostato a `task_v2`
- `auction.status` → `"open"`
- `auction.deadline` → 48 ore da ora
- `task.status` → `"auction_open"`
- Task propagato via gossip a tutta la rete

### 2. Piazzare un'Offerta

**Endpoint:** `POST /tasks/{task_id}/bid?channel=dev_ui`

**Payload:**
```json
{
  "amount": 450,
  "estimated_days": 3
}
```

**Validazioni:**
- ✅ Task esiste e ha asta abilitata
- ✅ Asta è ancora `open`
- ✅ Deadline non è passata
- ✅ `amount` <= `max_reward`
- ✅ `amount` > 0 e `estimated_days` > 0

**Cosa succede:**
- Calcola automaticamente `reputation` del bidder dal sistema
- Crea/aggiorna bid in `auction.bids[NODE_ID]` (CRDT LWW)
- Bid propagata via gossip a tutti i nodi
- Tutti i nodi vedono tutte le bid in tempo reale

**Response:**
```json
{
  "task_id": "abc123...",
  "bid": {
    "amount": 450,
    "estimated_days": 3,
    "reputation": 120,
    "timestamp": "2025-10-02T15:30:00Z"
  },
  "total_bids": 3
}
```

### 3. Selezione Vincitore

#### Manuale (da owner)

**Endpoint:** `POST /tasks/{task_id}/select_bid?channel=dev_ui`

**Requisiti:**
- Solo l'owner del task può chiamare questo endpoint
- Asta deve avere almeno una bid

**Cosa succede:**
- Esegue `select_winning_bid()` algorithm
- Chiude l'asta: `auction.status` → `"finalized"`
- Assegna task: `task.assignee` → `winner_id`
- Imposta reward: `task.reward` → `winning_bid.amount`
- Cambia stato: `task.status` → `"claimed"`

#### Automatica (alla deadline)

Il **Auction Processor** (background task) controlla ogni 30 secondi:

```python
async def auction_processor_task():
    # Ogni 30s, per ogni task:
    if now > auction.deadline and auction.bids:
        winner_id = select_winning_bid(auction.bids, max_reward)
        # Chiude asta e assegna automaticamente
```

**Comportamento:**
- ✅ **Con bid**: Seleziona automaticamente il vincitore e assegna
- ⚠️ **Senza bid**: Chiude l'asta (`status: closed`) e torna task a `"open"` per claim tradizionale

### 4. Completamento Task

Una volta assegnato, il workflow è identico ai task tradizionali:

```bash
# Il vincitore inizia il lavoro
POST /tasks/{task_id}/progress?channel=dev_ui

# Il vincitore completa il task
POST /tasks/{task_id}/complete?channel=dev_ui
```

**Reward:**
- Viene trasferita dal creator al vincitore
- Applicata la tassa configurabile (default 2%)
- Reputazione del vincitore aumenta (+10 default)

---

## Algoritmo di Selezione

### Formula di Scoring

```python
def select_winning_bid(bids: dict, max_reward: int) -> str:
    for peer_id, bid in bids.items():
        # Normalizza tutti i valori 0-1
        cost_score = (max_reward - bid["amount"]) / max_reward
        reputation_score = bid["reputation"] / max_reputation
        time_score = (1 / bid["estimated_days"]) / (1 / min_days)
        
        # Ponderazione
        total_score = (
            0.4 * cost_score +
            0.4 * reputation_score +
            0.2 * time_score
        )
    
    return peer_with_highest_score
```

### Esempio Pratico

**Task:** `max_reward = 500 SP`

**Bid ricevute:**

| Peer | Amount | Reputation | Est. Days | Cost Score | Rep Score | Time Score | **Total** |
|------|--------|------------|-----------|------------|-----------|------------|-----------|
| A | 400 | 150 | 3 | 0.20 | 1.00 | 0.60 | **0.68** ✅ |
| B | 350 | 100 | 5 | 0.30 | 0.67 | 0.36 | **0.60** |
| C | 480 | 80 | 2 | 0.04 | 0.53 | 0.90 | **0.49** |

**Vincitore: Peer A** (miglior balance tra costo, reputazione e tempo)

---

## API Reference

### POST /tasks (con asta)

**Crea un task con meccanismo d'asta.**

**Query Params:**
- `channel` (required): Canale dove creare il task

**Body:**
```json
{
  "title": "Task title",
  "description": "Task description",
  "enable_auction": true,
  "max_reward": 500,
  "auction_deadline_hours": 24,
  "tags": ["tag1", "tag2"]
}
```

**Response:** Task object con `auction` configurato

---

### POST /tasks/{task_id}/bid

**Piazza un'offerta per un task in asta.**

**Query Params:**
- `channel` (required): Canale del task

**Body:**
```json
{
  "amount": 450,
  "estimated_days": 3
}
```

**Response:**
```json
{
  "task_id": "...",
  "bid": {
    "amount": 450,
    "estimated_days": 3,
    "reputation": 120,
    "timestamp": "..."
  },
  "total_bids": 5
}
```

**Errori:**
- `400`: Task non ha asta abilitata
- `400`: Asta già chiusa/finalizzata
- `400`: Deadline passata
- `400`: Amount supera max_reward
- `404`: Task non trovato

---

### POST /tasks/{task_id}/select_bid

**Chiude l'asta e seleziona il vincitore (solo owner).**

**Query Params:**
- `channel` (required): Canale del task

**Response:**
```json
{
  "task_id": "...",
  "winner": "peer_id",
  "winning_bid": {
    "amount": 450,
    "estimated_days": 3,
    "reputation": 120,
    "timestamp": "..."
  },
  "total_bids": 5
}
```

**Errori:**
- `403`: Non sei l'owner del task
- `400`: Task non ha asta
- `400`: Asta già finalizzata
- `400`: Nessuna bid disponibile
- `404`: Task non trovato

---

### GET /state

**Include informazioni calcolate sulle aste.**

Per ogni task con asta abilitata, aggiunge `auction_info`:

```json
{
  "auction_info": {
    "bids_count": 5,
    "time_remaining_hours": 12.5,
    "is_expired": false,
    "min_bid_amount": 350,
    "max_bid_amount": 480
  }
}
```

---

## Propagazione CRDT

### Merge delle Bid

Le bid sono **CRDT Last-Write-Wins** per `peer_id`:

```python
# Nodo A riceve gossip da Nodo B
incoming_bids = incoming_task["auction"]["bids"]
local_bids = local_task["auction"]["bids"]

for peer_id, incoming_bid in incoming_bids.items():
    if peer_id not in local_bids:
        # Nuova bid
        local_bids[peer_id] = incoming_bid
    else:
        # Merge LWW: prendi la più recente
        local_ts = datetime.fromisoformat(local_bids[peer_id]["timestamp"])
        incoming_ts = datetime.fromisoformat(incoming_bid["timestamp"])
        
        if incoming_ts > local_ts:
            local_bids[peer_id] = incoming_bid
```

**Proprietà CRDT:**
- ✅ **Commutatività**: Ordine dei merge irrilevante
- ✅ **Associatività**: Merge in batch = merge sequenziali
- ✅ **Idempotenza**: Merge ripetuto = merge singolo
- ✅ **Convergenza**: Tutti i nodi convergono allo stesso stato

### Stato Asta

Il cambio di stato dell'asta (`open` → `finalized`) avviene tramite:
- Endpoint manuale `/select_bid` (owner)
- Auction processor automatico (alla deadline)

Una volta `finalized`, nessuna nuova bid può essere aggiunta.

---

## Vantaggi del Sistema

### 1. Efficienza Economica

**Prima (FCFS):**
```
Task reward: 500 SP
→ Primo che clicca "claim" vince
→ Nessun incentivo a essere efficiente
→ Possibile sovrapprezzo
```

**Dopo (Asta):**
```
Task max_reward: 500 SP
→ Bid competono: 450, 400, 350 SP
→ Vincitore: migliore qualità/prezzo
→ Creator risparmia, vincitore efficiente
```

### 2. Meritocrazia

Alta reputazione = vantaggio competitivo:
- Nodi con track record positivo hanno score più alto
- Incentivo a completare bene i task per aumentare reputazione
- Nuovi nodi devono competere su prezzo/tempo

### 3. Trasparenza

Tutte le bid sono pubbliche:
- Visibilità completa del mercato
- Nessuna negoziazione privata
- Algoritmo deterministico e verificabile

### 4. Flessibilità

Supporta entrambi i meccanismi:
- `enable_auction: false` → claim tradizionale (FCFS)
- `enable_auction: true` → asta competitiva
- Creator sceglie in base al task

---

## Scenari d'Uso

### Scenario 1: Task Urgente

**Parametri:**
- `max_reward`: 1000 SP (alto)
- `auction_deadline_hours`: 2 (breve)

**Risultato:**
- Molte bid competitive
- Vincitore probabilmente ottimizza su `estimated_days`
- Trade-off: reward più alta per consegna veloce

### Scenario 2: Task Budget-Constrained

**Parametri:**
- `max_reward`: 200 SP (basso)
- `auction_deadline_hours`: 72 (lungo)

**Risultato:**
- Poche bid (reward bassa)
- Vincitore ottimizza su `amount` (bid più bassa)
- Trade-off: tempo più lungo per risparmio

### Scenario 3: Task Mission-Critical

**Parametri:**
- `max_reward`: 800 SP (medio-alto)
- `auction_deadline_hours`: 24 (medio)
- Vincitore selezionato manualmente dall'owner

**Risultato:**
- Owner può valutare reputation prima di selezionare
- Scelta del nodo più affidabile, non solo più economico
- Garanzia di qualità

---

## Monitoraggio

### Log Patterns

```
🔨 Nuova bid per task 'Feature X': 450 SP, 3 giorni, reputazione 120
⏰ Asta scaduta per task 'Feature X' (abc123...)
   🎯 Auto-assegnato a peer_abc... con 450 SP
```

### Metriche da Tracciare

1. **Numero medio di bid per task**
   - Indicatore di competitività del mercato
   - Target: 3-5 bid per task

2. **Delta tra max_reward e winning_bid**
   - Risparmio medio per creator
   - Target: 10-20% di risparmio

3. **Distribuzione reputation dei vincitori**
   - Verifica che non vinca sempre lo stesso nodo
   - Target: distribuzione equilibrata

4. **Tempo medio di chiusura asta**
   - Quanti task chiudono prima/dopo deadline
   - Target: 80% chiuso entro deadline

---

## Configurazione Avanzata

### Pesi dell'Algoritmo

Attualmente hardcoded:
```python
total_score = (
    0.4 * cost_score +      # 40% peso costo
    0.4 * reputation_score + # 40% peso reputazione
    0.2 * time_score         # 20% peso tempo
)
```

**Future enhancement:** Rendere configurabili via governance:
```json
{
  "auction_cost_weight": 0.4,
  "auction_reputation_weight": 0.4,
  "auction_time_weight": 0.2
}
```

### Deadline di Default

Attualmente: `auction_deadline_hours` nel payload

**Future enhancement:** Default configurabile:
```json
{
  "default_auction_deadline_hours": 24
}
```

---

## Sicurezza

### Protezioni Implementate

1. **Solo owner può selezionare vincitore**
   ```python
   if task["owner"] != NODE_ID:
       raise HTTPException(403)
   ```

2. **Bid non può superare max_reward**
   ```python
   if payload.amount > auction["max_reward"]:
       raise HTTPException(400)
   ```

3. **Nessuna bid dopo deadline**
   ```python
   if datetime.now(timezone.utc) > deadline:
       raise HTTPException(400)
   ```

4. **Selezione deterministica**
   - Algoritmo pubblico e verificabile
   - Tutti i nodi possono verificare la selezione

### Attacchi Possibili

#### 1. Bid Spam
**Attacco:** Nodo invia centinaia di bid diverse

**Mitigazione:** LWW per peer_id → solo l'ultima bid conta

#### 2. Last-Second Bidding
**Attacco:** Aspetta ultimo secondo per bid competitiva

**Mitigazione:** 
- Deadline automatica rigorosa
- Nessuna estensione automatica

#### 3. Reputation Gaming
**Attacco:** Completa molti task facili per aumentare reputation

**Mitigazione:**
- Reputation pesa solo 40% (costo conta ugualmente)
- Future: reputazione ponderata per difficoltà task

---

## Roadmap

### Fase 1 (Corrente) ✅
- [x] Schema task_v2 con auction
- [x] Endpoint bid/select_bid
- [x] Algoritmo di selezione
- [x] Auto-close alla deadline
- [x] Propagazione CRDT

### Fase 2 (Prossima)
- [ ] Pesi algoritmo configurabili via governance
- [ ] Auction analytics dashboard
- [ ] Bid history e statistiche
- [ ] Notifiche per nuove bid

### Fase 3 (Futuro)
- [ ] Auction multi-round (estensioni automatiche)
- [ ] Reputation ponderata per difficoltà
- [ ] Bid privata (sealed-bid auction)
- [ ] Escrow automatico della reward

---

## Esempio End-to-End

### Setup

```bash
# Avvia 3 nodi
docker-compose up -d

# Node 1: 8001 (creator)
# Node 2: 8002 (bidder A, alta reputation)
# Node 3: 8003 (bidder B, bassa reputation)
```

### 1. Creator (Node 1) crea task con asta

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement payment system",
    "description": "Integrate Stripe API",
    "enable_auction": true,
    "max_reward": 1000,
    "auction_deadline_hours": 24,
    "tags": ["backend", "payment"]
  }'
```

**Response:**
```json
{
  "id": "task_abc123",
  "title": "Implement payment system",
  "status": "auction_open",
  "auction": {
    "enabled": true,
    "status": "open",
    "max_reward": 1000,
    "deadline": "2025-10-03T15:00:00Z",
    "bids": {},
    "selected_bid": null
  }
}
```

### 2. Bidder A (Node 2) piazza offerta

```bash
curl -X POST "http://localhost:8002/tasks/task_abc123/bid?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 800,
    "estimated_days": 5
  }'
```

**Response:**
```json
{
  "task_id": "task_abc123",
  "bid": {
    "amount": 800,
    "estimated_days": 5,
    "reputation": 150,
    "timestamp": "2025-10-02T16:00:00Z"
  },
  "total_bids": 1
}
```

### 3. Bidder B (Node 3) piazza offerta più bassa

```bash
curl -X POST "http://localhost:8003/tasks/task_abc123/bid?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 750,
    "estimated_days": 7
  }'
```

### 4. Controllo stato

```bash
curl "http://localhost:8001/state" | jq '.dev_ui.tasks.task_abc123.auction_info'
```

**Response:**
```json
{
  "bids_count": 2,
  "time_remaining_hours": 22.5,
  "is_expired": false,
  "min_bid_amount": 750,
  "max_bid_amount": 800
}
```

### 5. Owner seleziona vincitore

```bash
curl -X POST "http://localhost:8001/tasks/task_abc123/select_bid?channel=dev_ui"
```

**Log (tutti i nodi):**
```
Bid peer_node2... → score=0.723 (cost=0.200, rep=1.000, time=0.600)
Bid peer_node3... → score=0.617 (cost=0.250, rep=0.600, time=0.514)
🏆 Vincitore asta: peer_node2... con score 0.723
🎯 Asta chiusa per task 'Implement payment system': vincitore peer_node2... con 800 SP
```

**Response:**
```json
{
  "task_id": "task_abc123",
  "winner": "peer_node2...",
  "winning_bid": {
    "amount": 800,
    "estimated_days": 5,
    "reputation": 150,
    "timestamp": "2025-10-02T16:00:00Z"
  },
  "total_bids": 2
}
```

### 6. Vincitore completa task

```bash
# Progress
curl -X POST "http://localhost:8002/tasks/task_abc123/progress?channel=dev_ui"

# Complete
curl -X POST "http://localhost:8002/tasks/task_abc123/complete?channel=dev_ui"
```

**Risultato:**
- Node 2 riceve 800 SP (meno 2% tassa = 784 SP)
- Node 1 risparmia 200 SP rispetto al max_reward
- Node 2 aumenta reputation (+10)
- Treasury riceve 16 SP di tassa

---

## Conclusione

Il **Sistema d'Asta** trasforma Synapse-NG in un **mercato autonomo efficiente** dove:

✅ **Efficienza economica**: I task vanno a chi offre il miglior rapporto qualità/prezzo  
✅ **Meritocrazia**: La reputazione diventa un asset competitivo  
✅ **Trasparenza**: Tutte le bid sono pubbliche e verificabili  
✅ **Flessibilità**: Supporta sia asta che claim tradizionale  
✅ **Decentralizzazione**: Nessuna autorità centrale decide i prezzi  

L'organismo digitale ora ha un **sistema nervoso economico** che auto-regola i prezzi attraverso il consenso distribuito, premiando efficienza e affidabilità. 🔨💰✨
