#!/bin/bash

# Test First Task Experiment
# Dimostra il principio fondamentale: Contributo → Valore

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

wait_for_condition() {
    local condition=$1
    local description=$2
    local max_wait=${3:-30}
    local elapsed=0
    
    while ! eval "$condition" > /dev/null 2>&1; do
        if [ $elapsed -ge $max_wait ]; then
            print_error "$description - Timeout dopo ${max_wait}s"
            return 1
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    print_success "$description"
    return 0
}

print_header "🧪 FIRST TASK EXPERIMENT - Contributo → Valore"

echo "Questo esperimento dimostra che:"
echo "  1. Un task viene creato con reward"
echo "  2. Qualcuno lo completa (fornisce valore)"
echo "  3. Riceve automaticamente SP + reputazione"
echo "  4. Tutti i nodi concordano sul nuovo stato"
echo "  5. Nessun manager ha approvato nulla"
echo ""
echo "Principio: Il sistema si auto-esegue."

# Check if nodes are running
print_header "STEP 0: Verifica Nodi Attivi"

for port in 8001 8002 8003; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        print_success "Nodo su porta $port è online"
    else
        print_error "Nodo su porta $port non risponde"
        echo "Esegui: docker-compose up -d"
        exit 1
    fi
done

# Wait for network stabilization
echo ""
print_info "Attendo 15 secondi per stabilizzazione rete..."
sleep 15

print_header "STEP 1: Capture Node IDs"

NODE1_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | keys[0]')
NODE2_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | keys[0]')
NODE3_ID=$(curl -s http://localhost:8003/state | jq -r '.global.nodes | keys[0]')

if [ -z "$NODE1_ID" ] || [ "$NODE1_ID" = "null" ]; then
    print_error "Non riesco a ottenere NODE1_ID"
    exit 1
fi

print_success "Nodo 1: ${NODE1_ID:0:16}..."
print_success "Nodo 2: ${NODE2_ID:0:16}..."
print_success "Nodo 3: ${NODE3_ID:0:16}..."

print_header "STEP 2: Verifica Balance Iniziali"

BALANCE1_INIT=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")
BALANCE2_INIT=$(curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo "Creator (Nodo 1): $BALANCE1_INIT SP"
echo "Contributore (Nodo 2): $BALANCE2_INIT SP"

if [ "$BALANCE1_INIT" -lt 10 ]; then
    print_error "Balance insufficiente per creare task con reward 10 SP"
    exit 1
fi

print_header "STEP 3: Crea Task con Reward (Nodo 1 = Creator)"

TASK_RESPONSE=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trovare il primo bug in Synapse-NG",
    "description": "Esplora il sistema e documenta il primo comportamento inatteso. Crea un issue su GitHub come prova del completamento.",
    "reward": 10,
    "tags": ["testing", "bug-hunting", "first-contribution"]
  }')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id')

if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
    print_error "Creazione task fallita"
    echo "$TASK_RESPONSE" | jq .
    exit 1
fi

print_success "Task creato: ${TASK_ID:0:16}..."
echo "   Titolo: Trovare il primo bug in Synapse-NG"
echo "   Reward: 10 SP"
echo "   Channel: dev_ui"

print_header "STEP 4: Verifica Balance Frozen (Creator)"

echo "Attendo 10s per propagazione..."
sleep 10

BALANCE1_FROZEN=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")

echo "Balance Creator dopo creazione task:"
echo "   Nodo 1: $BALANCE1_FROZEN SP (era $BALANCE1_INIT SP)"
echo "   Differenza: $((BALANCE1_INIT - BALANCE1_FROZEN)) SP"

EXPECTED_FROZEN=$((BALANCE1_INIT - 10))

if [ "$BALANCE1_FROZEN" -ne "$EXPECTED_FROZEN" ]; then
    print_error "Balance frozen non corretto. Expected: $EXPECTED_FROZEN, Got: $BALANCE1_FROZEN"
else
    print_success "10 SP correttamente congelati"
fi

# Verifica consenso su tutti i nodi
BALANCE1_ON_NODE2=$(curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")
BALANCE1_ON_NODE3=$(curl -s http://localhost:8003/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")

echo ""
echo "Verifica consenso balance Creator:"
echo "   Nodo 1: $BALANCE1_FROZEN SP"
echo "   Nodo 2: $BALANCE1_ON_NODE2 SP"
echo "   Nodo 3: $BALANCE1_ON_NODE3 SP"

if [ "$BALANCE1_FROZEN" -eq "$BALANCE1_ON_NODE2" ] && [ "$BALANCE1_FROZEN" -eq "$BALANCE1_ON_NODE3" ]; then
    print_success "✅ CHECKPOINT 1: Tutti i nodi concordano sul balance frozen"
else
    print_error "❌ CHECKPOINT 1 FALLITO: Consenso mancante"
    exit 1
fi

print_header "STEP 5: Claim Task (Nodo 2 = Contributore)"

wait_for_condition "curl -s http://localhost:8002/state | jq -e '.dev_ui.tasks.\"$TASK_ID\"'" "Task visibile su Nodo 2" 30

CLAIM_RESPONSE=$(curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui")

echo "$CLAIM_RESPONSE" | jq .

print_success "Task claimed dal Nodo 2"

echo ""
print_info "Attendo 10s per propagazione claim..."
sleep 10

# Verifica che tutti i nodi vedono il claim
STATUS_NODE1=$(curl -s http://localhost:8001/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")
STATUS_NODE2=$(curl -s http://localhost:8002/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")
STATUS_NODE3=$(curl -s http://localhost:8003/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")

echo "Status task dopo claim:"
echo "   Nodo 1: $STATUS_NODE1"
echo "   Nodo 2: $STATUS_NODE2"
echo "   Nodo 3: $STATUS_NODE3"

if [ "$STATUS_NODE1" = "claimed" ] && [ "$STATUS_NODE2" = "claimed" ] && [ "$STATUS_NODE3" = "claimed" ]; then
    print_success "✅ CHECKPOINT 2: Tutti i nodi concordano su status=claimed"
else
    print_error "❌ CHECKPOINT 2 FALLITO: Status inconsistente"
    exit 1
fi

print_header "STEP 6: Progress e Complete Task (Nodo 2)"

echo "Simulo completamento del bug report..."
echo ""
echo "📝 In uno scenario reale, il contributore avrebbe:"
echo "   1. Trovato un bug (es. typo nella doc, comando non funzionante)"
echo "   2. Creato un'issue su GitHub"
echo "   3. Inserito il link dell'issue come proof"
echo ""
echo "Per questo test, simuliamo il completamento diretto."

# Progress
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui" > /dev/null
print_success "Task in progress"

sleep 5

# Complete
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui" > /dev/null
print_success "Task completato"

echo ""
print_info "Attendo 15s per propagazione complete e calcolo balance..."
sleep 15

print_header "STEP 7: Verifica Transfer SP e Reputazione"

# Balance finali
BALANCE1_FINAL=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")
BALANCE2_FINAL=$(curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo "Balance finali:"
echo "   Creator (Nodo 1): $BALANCE1_FINAL SP (era $BALANCE1_INIT SP)"
echo "   Contributore (Nodo 2): $BALANCE2_FINAL SP (era $BALANCE2_INIT SP)"
echo ""

CREATOR_DELTA=$((BALANCE1_FINAL - BALANCE1_INIT))
CONTRIBUTOR_DELTA=$((BALANCE2_FINAL - BALANCE2_INIT))

echo "Delta:"
echo "   Creator: $CREATOR_DELTA SP"
echo "   Contributore: +$CONTRIBUTOR_DELTA SP"

# Calcola reputazioni
echo ""
echo "Calcolo reputazioni..."

REP_FULL=$(curl -s http://localhost:8001/reputations)
REP1=$(echo "$REP_FULL" | jq ".\"$NODE1_ID\" // 0")
REP2=$(echo "$REP_FULL" | jq ".\"$NODE2_ID\" // 0")

echo "Reputazioni:"
echo "   Creator (Nodo 1): $REP1"
echo "   Contributore (Nodo 2): $REP2"

# Verifica consenso finale
BALANCE2_ON_NODE1=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")
BALANCE2_ON_NODE3=$(curl -s http://localhost:8003/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo ""
echo "Verifica consenso balance Contributore:"
echo "   Nodo 1: $BALANCE2_ON_NODE1 SP"
echo "   Nodo 2: $BALANCE2_FINAL SP"
echo "   Nodo 3: $BALANCE2_ON_NODE3 SP"

print_header "📊 RISULTATI FINALI"

SUCCESS=true

# Check 1: Creator ha pagato
if [ "$CREATOR_DELTA" -eq -10 ]; then
    print_success "Creator ha pagato 10 SP"
else
    print_error "Creator delta non corretto: $CREATOR_DELTA (expected: -10)"
    SUCCESS=false
fi

# Check 2: Contributore ha ricevuto (meno tassa)
# Con tassa 2%, reward netto = 10 * 0.98 = 9.8 ≈ 10 (arrotondato)
if [ "$CONTRIBUTOR_DELTA" -ge 9 ] && [ "$CONTRIBUTOR_DELTA" -le 10 ]; then
    print_success "Contributore ha ricevuto ~10 SP (meno tassa)"
else
    print_error "Contributore delta non corretto: $CONTRIBUTOR_DELTA (expected: 9-10)"
    SUCCESS=false
fi

# Check 3: Reputazione aumentata
if [ "$REP2" -ge 10 ]; then
    print_success "Contributore ha guadagnato reputazione (+$REP2)"
else
    print_error "Reputazione non aumentata: $REP2 (expected: ≥10)"
    SUCCESS=false
fi

# Check 4: Consenso
if [ "$BALANCE2_FINAL" -eq "$BALANCE2_ON_NODE1" ] && [ "$BALANCE2_FINAL" -eq "$BALANCE2_ON_NODE3" ]; then
    print_success "Consenso raggiunto su tutti i nodi"
else
    print_error "Consenso mancante"
    SUCCESS=false
fi

echo ""
if [ "$SUCCESS" = true ]; then
    print_header "🎉 ESPERIMENTO RIUSCITO!"
    echo ""
    echo "✅ Il sistema ha dimostrato che:"
    echo "   1. Un task con reward è stato creato"
    echo "   2. Un contributore lo ha completato"
    echo "   3. Ha ricevuto automaticamente SP + reputazione"
    echo "   4. Tutti i nodi concordano sul nuovo stato"
    echo "   5. Nessun manager ha approvato nulla"
    echo ""
    echo "Principio dimostrato: Contributo → Valore"
    echo "Il sistema si auto-esegue. 🧬"
    echo ""
    print_success "✅ CHECKPOINT 3: Transfer e reputazione verificati"
    exit 0
else
    print_header "❌ ESPERIMENTO FALLITO"
    echo ""
    echo "Uno o più checkpoint non sono stati superati."
    echo "Controlla i log sopra per dettagli."
    echo ""
    print_error "Il sistema richiede debug"
    exit 1
fi
