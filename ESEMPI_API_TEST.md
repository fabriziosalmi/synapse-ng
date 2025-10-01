# 🔬 Esempi API per Test Manuali - Economia e Governance

Questa guida fornisce esempi pratici di chiamate API per testare manualmente i sistemi di economia e governance.

---

## 📋 Setup Iniziale

### 1. Avvia la rete

```bash
docker-compose up --build -d rendezvous node-1 node-2 node-3
```

### 2. Attendi convergenza (15-20 secondi)

```bash
sleep 20
```

### 3. Ottieni gli ID dei nodi

```bash
# Nodo 1
NODE_1_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-1:8000") | .key')
echo "Node 1 ID: $NODE_1_ID"

# Nodo 2
NODE_2_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-2:8000") | .key')
echo "Node 2 ID: $NODE_2_ID"

# Nodo 3
NODE_3_ID=$(curl -s http://localhost:8003/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-3:8000") | .key')
echo "Node 3 ID: $NODE_3_ID"
```

---

## 💰 Test Economia: Synapse Points

### Scenario: Creazione Task con Reward

#### 1. Verifica Balance Iniziale

```bash
# Balance iniziale di tutti i nodi (dovrebbe essere 1000 SP)
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id: .id[:16], balance: .balance}'
```

Output atteso:
```json
{
  "id": "abc123...",
  "balance": 1000
}
```

#### 2. Crea Task con Reward (Nodo 1)

```bash
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task con Reward","reward":50}' | jq -r '.id')

echo "Task ID: $TASK_ID"
```

#### 3. Verifica Congelamento SP

```bash
# Attendi propagazione
sleep 20

# Verifica balance su Nodo 2 (deve vedere Nodo 1 con 950 SP)
curl -s http://localhost:8002/state | jq --arg nid "$NODE_1_ID" '.global.nodes[$nid] | {id: .id[:16], balance: .balance}'
```

Output atteso:
```json
{
  "id": "abc123...",
  "balance": 950
}
```

#### 4. Completa Task (Nodo 2)

```bash
# Claim
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=sviluppo_ui" -d ''

sleep 5

# Progress
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=sviluppo_ui" -d ''

sleep 5

# Complete
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=sviluppo_ui" -d ''
```

#### 5. Verifica Trasferimento SP

```bash
# Attendi propagazione
sleep 25

# Verifica balance su tutti i nodi (devono essere identici!)
for port in 8001 8002 8003; do
  echo "=== Nodo :$port ==="
  curl -s http://localhost:$port/state | jq --arg n1 "$NODE_1_ID" --arg n2 "$NODE_2_ID" '.global.nodes | {node1_balance: .[$n1].balance, node2_balance: .[$n2].balance}'
done
```

Output atteso (identico su tutti i nodi):
```json
{
  "node1_balance": 950,
  "node2_balance": 1050
}
```

### ✅ Verifica Determinismo

Tutti i nodi devono mostrare gli stessi balance. Se differiscono, c'è una **divergenza economica** (bug critico).

---

## 🗳️ Test Governance: Voto Ponderato

### Scenario: Proposta con Reputazioni Diverse

#### 1. Costruisci Reputazione (Nodo 1 completa task)

```bash
# Crea e completa 2 task per guadagnare +20 reputazione
for i in 1 2; do
  TASK_REP=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Task Reputazione $i\"}" | jq -r '.id')
  
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/claim?channel=sviluppo_ui" -d ''
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/progress?channel=sviluppo_ui" -d ''
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/complete?channel=sviluppo_ui" -d ''
  
  echo "Task $i completato"
  sleep 5
done
```

#### 2. Verifica Reputazione

```bash
# Attendi propagazione
sleep 20

# Verifica reputazione su tutti i nodi
for port in 8001 8002 8003; do
  echo "=== Nodo :$port ==="
  curl -s http://localhost:$port/state | jq --arg nid "$NODE_1_ID" '.global.nodes[$nid] | {id: .id[:16], reputation: .reputation}'
done
```

Output atteso (identico su tutti i nodi):
```json
{
  "id": "abc123...",
  "reputation": 20
}
```

#### 3. Crea Proposta (Nodo 3)

```bash
PROP_ID=$(curl -s -X POST "http://localhost:8003/proposals?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Proposta Test Voto Ponderato"}' | jq -r '.id')

echo "Proposal ID: $PROP_ID"

# Attendi propagazione
sleep 20
```

#### 4. Votazione

```bash
# Nodo 1 (alta reputazione, peso ~5.4) vota NO
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/vote?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"no"}'

sleep 5

# Nodo 2 (bassa reputazione, peso ~1.0) vota YES
curl -s -X POST "http://localhost:8002/proposals/$PROP_ID/vote?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"yes"}'

sleep 5

# Nodo 3 (reputazione 0, peso 1.0) vota YES
curl -s -X POST "http://localhost:8003/proposals/$PROP_ID/vote?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"yes"}'

# Attendi propagazione
sleep 20
```

#### 5. Chiudi Proposta e Verifica Esito

```bash
# Chiudi proposta (su qualsiasi nodo)
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/close?channel=sviluppo_ui" -d ''

# Attendi calcolo esito
sleep 20

# Verifica esito su tutti i nodi
for port in 8001 8002 8003; do
  echo "=== Nodo :$port ==="
  curl -s http://localhost:$port/state | jq --arg pid "$PROP_ID" '.sviluppo_ui.proposals[$pid] | {
    status: .status,
    outcome: .outcome,
    yes_weight: .yes_weight,
    no_weight: .no_weight
  }'
done
```

Output atteso (identico su tutti i nodi):
```json
{
  "status": "closed",
  "outcome": "rejected",
  "yes_weight": 2.0,
  "no_weight": 5.39
}
```

### ✅ Verifica Voto Ponderato

- **2 voti YES** (peso totale ~2.0) vs **1 voto NO** (peso ~5.4)
- Outcome deve essere **"rejected"** perché `no_weight > yes_weight`
- Questo prova che la reputazione influenza correttamente il voto

---

## 🔍 Query di Verifica

### Stato Completo di un Nodo

```bash
curl -s http://localhost:8001/state | jq '.'
```

### Solo Nodi Globali

```bash
curl -s http://localhost:8001/state | jq '.global.nodes'
```

### Reputazioni di Tutti i Nodi

```bash
curl -s http://localhost:8001/state | jq '.global.nodes[] | {
  id: .id[:16],
  reputation: .reputation,
  balance: .balance
}'
```

### Task di un Canale

```bash
curl -s http://localhost:8001/state | jq '.sviluppo_ui.tasks'
```

### Dettaglio Task Specifico

```bash
curl -s http://localhost:8001/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid]'
```

### Proposte di un Canale

```bash
curl -s http://localhost:8001/state | jq '.sviluppo_ui.proposals'
```

### Dettaglio Proposta Specifica

```bash
curl -s http://localhost:8001/state | jq --arg pid "$PROP_ID" '.sviluppo_ui.proposals[$pid]'
```

### Verifica Peso Voti di una Proposta

```bash
curl -s http://localhost:8001/state | jq --arg pid "$PROP_ID" '.sviluppo_ui.proposals[$pid] | {
  votes: .votes,
  vote_details: .vote_details,
  yes_weight: .yes_weight,
  no_weight: .no_weight,
  outcome: .outcome
}'
```

---

## 📊 Statistiche Rete

### Connessioni WebRTC

```bash
curl -s http://localhost:8001/webrtc/connections | jq '.'
```

### Statistiche PubSub

```bash
curl -s http://localhost:8001/pubsub/stats | jq '.'
```

### Network Stats (metriche in tempo reale)

```bash
curl -s http://localhost:8001/network/stats | jq '.'
```

---

## 🧮 Calcoli Manuali

### Formula Peso Voto

```
peso_voto = 1.0 + log₂(reputation + 1)
```

**Esempi**:
- reputation 0 → peso 1.00
- reputation 1 → peso 2.00
- reputation 10 → peso 4.46
- reputation 20 → peso 5.39
- reputation 100 → peso 7.66

### Calcolo Balance

```
balance_nodo = INITIAL_BALANCE 
               - Σ(reward di task creati)
               + Σ(reward di task completati come assignee)
```

**Esempio**:
- INITIAL_BALANCE = 1000
- Task creato con reward 30 → balance = 970 (congelati)
- Task completato con reward 30 → balance = 1030 (ricevuti)

---

## 🔄 Test di Convergenza

### Verifica Convergenza Completa

Tutti i nodi devono avere la stessa vista dello stato:

```bash
# Ottieni hash dello stato da ogni nodo
for port in 8001 8002 8003; do
  echo "=== Nodo :$port ==="
  curl -s http://localhost:$port/state | jq -S '.' | shasum
done
```

Se gli hash sono **identici**, lo stato è perfettamente convergente.

---

## 🧪 Test Avanzati

### Test Double-Spend Prevention

Tenta di creare un task con reward maggiore del balance:

```bash
# Assumendo NODE_1 abbia 1000 SP
curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Task Impossibile","reward":1500}'
```

Output atteso:
```json
{
  "detail": "Balance insufficiente. Hai 1000 SP, richiesti 1500 SP"
}
```

### Test Conservazione SP

Verifica che il totale di SP nella rete rimanga costante:

```bash
# Somma dei balance di tutti i nodi
curl -s http://localhost:8001/state | jq '[.global.nodes[].balance] | add'
```

Output atteso (per 3 nodi con INITIAL_BALANCE=1000):
```
3000
```

---

## 🐛 Troubleshooting

### Problema: Balance Divergenti

```bash
# Confronta balance su tutti i nodi
for port in 8001 8002 8003; do
  echo "=== Nodo :$port ==="
  curl -s http://localhost:$port/state | jq '.global.nodes[] | {id: .id[:16], balance: .balance}'
done
```

Se i balance differiscono, verifica:
1. La propagazione è completa? (attendi più tempo)
2. Tutti i nodi hanno ricevuto tutti gli eventi?
3. Ci sono errori nei log? (`docker-compose logs`)

### Problema: Proposta Non Si Chiude

```bash
# Verifica status proposta
curl -s http://localhost:8001/state | jq --arg pid "$PROP_ID" '.sviluppo_ui.proposals[$pid].status'
```

Se status è ancora "open", chiudi manualmente:

```bash
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/close?channel=sviluppo_ui" -d ''
```

---

## 📝 Checklist Test Manuale

Prima di considerare il sistema pronto:

- [ ] Balance iniziali corretti (1000 SP per tutti)
- [ ] Task con reward congela correttamente gli SP
- [ ] Task completato trasferisce correttamente gli SP
- [ ] Tutti i nodi concordano sui balance (nessuna divergenza)
- [ ] Reputazione incrementa correttamente (+10 per task, +1 per voto)
- [ ] Peso voto calcolato correttamente (formula logaritmica)
- [ ] Proposta con voto ponderato calcola esito corretto
- [ ] Tutti i nodi concordano sull'esito della proposta
- [ ] Totale SP nella rete rimane costante
- [ ] Previene double-spend (task con reward > balance fallisce)

---

## 🚀 Automazione

Per automatizzare questi test, usa:

```bash
./test_suite.sh governance  # Test voto ponderato
./test_suite.sh economy     # Test economia SP
./test_suite.sh all         # Tutti i test
```

---

**Note**: Questi esempi presuppongono una rete pulita. Se stai testando su una rete esistente, i risultati potrebbero variare a causa dello stato precedente.

**Pro Tip**: Usa `jq` per formattare l'output JSON in modo leggibile. Se non hai `jq`, installalo con `brew install jq` (macOS) o `apt install jq` (Linux).
