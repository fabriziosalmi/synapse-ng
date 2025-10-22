#!/bin/bash

# Test First Task Experiment - Enhanced Version
# Dimostra il principio fondamentale: Contributo → Valore
# Con analisi automatizzata dei risultati e metriche dettagliate

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Timestamp functions
get_timestamp_ms() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        python3 -c 'import time; print(int(time.time() * 1000))'
    else
        # Linux
        date +%s%3N
    fi
}

# Logging
LOG_FILE="experiment_$(date +%Y%m%d_%H%M%S).log"
METRICS_FILE="metrics_$(date +%Y%m%d_%H%M%S).json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    log "=== $1 ==="
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    log "SUCCESS: $1"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    log "ERROR: $1"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
    log "INFO: $1"
}

print_metric() {
    echo -e "${CYAN}📊 $1${NC}"
    log "METRIC: $1"
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

# Initialize metrics
declare -A METRICS
METRICS[experiment_start]=$(get_timestamp_ms)

print_header "🧪 FIRST TASK EXPERIMENT - Enhanced Version"

echo "Questo esperimento dimostra che:"
echo "  1. Un task viene creato con reward"
echo "  2. Qualcuno lo completa (fornisce valore)"
echo "  3. Riceve automaticamente SP + reputazione"
echo "  4. Tutti i nodi concordano sul nuovo stato"
echo "  5. Nessun manager ha approvato nulla"
echo ""
echo "Principio: Il sistema si auto-esegue."
echo ""
echo "📝 Log file: $LOG_FILE"
echo "📊 Metrics file: $METRICS_FILE"

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

print_success "Nodo 1 (Creator): ${NODE1_ID:0:16}..."
print_success "Nodo 2 (Contributor): ${NODE2_ID:0:16}..."
print_success "Nodo 3 (Observer): ${NODE3_ID:0:16}..."

METRICS[node1_id]=$NODE1_ID
METRICS[node2_id]=$NODE2_ID
METRICS[node3_id]=$NODE3_ID

print_header "STEP 2: Verifica Balance Iniziali"

BALANCE1_INIT=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")
BALANCE2_INIT=$(curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo "Creator (Nodo 1): $BALANCE1_INIT SP"
echo "Contributor (Nodo 2): $BALANCE2_INIT SP"

METRICS[balance1_init]=$BALANCE1_INIT
METRICS[balance2_init]=$BALANCE2_INIT

if [ "$BALANCE1_INIT" -lt 10 ]; then
    print_error "Balance insufficiente per creare task con reward 10 SP"
    exit 1
fi

print_header "STEP 3: Crea Task con Reward (Nodo 1 = Creator)"

# 🔹 OTTIMIZZAZIONE: Estrazione automatica task_id
METRICS[task_creation_start]=$(get_timestamp_ms)

TASK_RESPONSE=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trovare il primo bug in Synapse-NG",
    "description": "Esplora il sistema e documenta il primo comportamento inatteso. Crea un issue su GitHub come prova del completamento.",
    "reward": 10,
    "tags": ["testing", "bug-hunting", "first-contribution"]
  }')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id')

METRICS[task_creation_end]=$(get_timestamp_ms)
METRICS[task_id]=$TASK_ID

if [ -z "$TASK_ID" ] || [ "$TASK_ID" = "null" ]; then
    print_error "Creazione task fallita"
    echo "$TASK_RESPONSE" | jq .
    exit 1
fi

print_success "Task creato: ${TASK_ID:0:16}..."
echo "   Titolo: Trovare il primo bug in Synapse-NG"
echo "   Reward: 10 SP"
echo "   Channel: dev_ui"

CREATION_TIME=$((METRICS[task_creation_end] - METRICS[task_creation_start]))
print_metric "Tempo creazione task: ${CREATION_TIME}ms"

print_header "STEP 4: Verifica Balance Frozen (Creator)"

echo "Attendo 10s per propagazione..."
sleep 10

METRICS[balance_check_start]=$(get_timestamp_ms)

BALANCE1_FROZEN=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")

echo "Balance Creator dopo creazione task:"
echo "   Nodo 1: $BALANCE1_FROZEN SP (era $BALANCE1_INIT SP)"
echo "   Differenza: $((BALANCE1_INIT - BALANCE1_FROZEN)) SP"

METRICS[balance1_frozen]=$BALANCE1_FROZEN

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

METRICS[balance1_on_node2]=$BALANCE1_ON_NODE2
METRICS[balance1_on_node3]=$BALANCE1_ON_NODE3

if [ "$BALANCE1_FROZEN" -eq "$BALANCE1_ON_NODE2" ] && [ "$BALANCE1_FROZEN" -eq "$BALANCE1_ON_NODE3" ]; then
    print_success "✅ CHECKPOINT 1: Tutti i nodi concordano sul balance frozen"
    METRICS[checkpoint1]="PASS"
else
    print_error "❌ CHECKPOINT 1 FALLITO: Consenso mancante"
    METRICS[checkpoint1]="FAIL"
    exit 1
fi

# Misura tempo di propagazione
METRICS[task_propagation_check]=$(get_timestamp_ms)
PROPAGATION_TIME=$((METRICS[task_propagation_check] - METRICS[task_creation_end]))
print_metric "Tempo propagazione task creation: ${PROPAGATION_TIME}ms"

print_header "STEP 5: Claim Task (Nodo 2 = Contributor)"

wait_for_condition "curl -s http://localhost:8002/state | jq -e '.dev_ui.tasks.\"$TASK_ID\"'" "Task visibile su Nodo 2" 30

METRICS[claim_start]=$(get_timestamp_ms)

CLAIM_RESPONSE=$(curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui")

METRICS[claim_end]=$(get_timestamp_ms)

echo "$CLAIM_RESPONSE" | jq .

print_success "Task claimed dal Nodo 2"

CLAIM_TIME=$((METRICS[claim_end] - METRICS[claim_start]))
print_metric "Tempo operazione claim: ${CLAIM_TIME}ms"

echo ""
print_info "Attendo 10s per propagazione claim..."
sleep 10

METRICS[claim_propagation_check]=$(get_timestamp_ms)

# Verifica che tutti i nodi vedono il claim
STATUS_NODE1=$(curl -s http://localhost:8001/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")
STATUS_NODE2=$(curl -s http://localhost:8002/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")
STATUS_NODE3=$(curl -s http://localhost:8003/state | jq -r ".dev_ui.tasks.\"$TASK_ID\".status")

echo "Status task dopo claim:"
echo "   Nodo 1: $STATUS_NODE1"
echo "   Nodo 2: $STATUS_NODE2"
echo "   Nodo 3: $STATUS_NODE3"

METRICS[status_node1]=$STATUS_NODE1
METRICS[status_node2]=$STATUS_NODE2
METRICS[status_node3]=$STATUS_NODE3

if [ "$STATUS_NODE1" = "claimed" ] && [ "$STATUS_NODE2" = "claimed" ] && [ "$STATUS_NODE3" = "claimed" ]; then
    print_success "✅ CHECKPOINT 2: Tutti i nodi concordano su status=claimed"
    METRICS[checkpoint2]="PASS"
else
    print_error "❌ CHECKPOINT 2 FALLITO: Status inconsistente"
    METRICS[checkpoint2]="FAIL"
    exit 1
fi

CLAIM_PROPAGATION_TIME=$((METRICS[claim_propagation_check] - METRICS[claim_end]))
print_metric "Tempo propagazione claim: ${CLAIM_PROPAGATION_TIME}ms"

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
METRICS[progress_start]=$(get_timestamp_ms)
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui" > /dev/null
METRICS[progress_end]=$(get_timestamp_ms)
print_success "Task in progress"

sleep 5

# Complete
METRICS[complete_start]=$(get_timestamp_ms)
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui" > /dev/null
METRICS[complete_end]=$(get_timestamp_ms)
print_success "Task completato"

COMPLETE_TIME=$((METRICS[complete_end] - METRICS[complete_start]))
print_metric "Tempo operazione complete: ${COMPLETE_TIME}ms"

echo ""
print_info "Attendo 15s per propagazione complete e calcolo balance..."
sleep 15

METRICS[complete_propagation_check]=$(get_timestamp_ms)

print_header "STEP 7: Verifica Transfer SP e Reputazione"

# Balance finali
BALANCE1_FINAL=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance // 1000")
BALANCE2_FINAL=$(curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo "Balance finali:"
echo "   Creator (Nodo 1): $BALANCE1_FINAL SP (era $BALANCE1_INIT SP)"
echo "   Contributor (Nodo 2): $BALANCE2_FINAL SP (era $BALANCE2_INIT SP)"
echo ""

METRICS[balance1_final]=$BALANCE1_FINAL
METRICS[balance2_final]=$BALANCE2_FINAL

CREATOR_DELTA=$((BALANCE1_FINAL - BALANCE1_INIT))
CONTRIBUTOR_DELTA=$((BALANCE2_FINAL - BALANCE2_INIT))

METRICS[creator_delta]=$CREATOR_DELTA
METRICS[contributor_delta]=$CONTRIBUTOR_DELTA

echo "Delta:"
echo "   Creator: $CREATOR_DELTA SP"
echo "   Contributor: +$CONTRIBUTOR_DELTA SP"

# Calcola reputazioni
echo ""
echo "Calcolo reputazioni..."

REP_FULL=$(curl -s http://localhost:8001/reputations)
REP1=$(echo "$REP_FULL" | jq ".\"$NODE1_ID\" // 0")
REP2=$(echo "$REP_FULL" | jq ".\"$NODE2_ID\" // 0")

echo "Reputazioni:"
echo "   Creator (Nodo 1): $REP1"
echo "   Contributor (Nodo 2): $REP2"

METRICS[reputation1]=$REP1
METRICS[reputation2]=$REP2

# Verifica consenso finale
BALANCE2_ON_NODE1=$(curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")
BALANCE2_ON_NODE3=$(curl -s http://localhost:8003/state | jq ".global.nodes.\"$NODE2_ID\".balance // 1000")

echo ""
echo "Verifica consenso balance Contributor:"
echo "   Nodo 1: $BALANCE2_ON_NODE1 SP"
echo "   Nodo 2: $BALANCE2_FINAL SP"
echo "   Nodo 3: $BALANCE2_ON_NODE3 SP"

METRICS[balance2_on_node1]=$BALANCE2_ON_NODE1
METRICS[balance2_on_node3]=$BALANCE2_ON_NODE3

COMPLETE_PROPAGATION_TIME=$((METRICS[complete_propagation_check] - METRICS[complete_end]))
print_metric "Tempo propagazione complete: ${COMPLETE_PROPAGATION_TIME}ms"

print_header "📊 RISULTATI FINALI"

SUCCESS=true

# Check 1: Creator ha pagato
if [ "$CREATOR_DELTA" -eq -10 ]; then
    print_success "Creator ha pagato 10 SP"
else
    print_error "Creator delta non corretto: $CREATOR_DELTA (expected: -10)"
    SUCCESS=false
fi

# Check 2: Contributor ha ricevuto (meno tassa)
if [ "$CONTRIBUTOR_DELTA" -ge 9 ] && [ "$CONTRIBUTOR_DELTA" -le 10 ]; then
    print_success "Contributor ha ricevuto ~10 SP (meno tassa)"
else
    print_error "Contributor delta non corretto: $CONTRIBUTOR_DELTA (expected: 9-10)"
    SUCCESS=false
fi

# Check 3: Reputazione aumentata
if [ "$REP2" -ge 10 ]; then
    print_success "Contributor ha guadagnato reputazione (+$REP2)"
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

METRICS[experiment_end]=$(get_timestamp_ms)
TOTAL_TIME=$((METRICS[experiment_end] - METRICS[experiment_start]))

echo ""
if [ "$SUCCESS" = true ]; then
    print_header "🎉 ESPERIMENTO RIUSCITO!"
    METRICS[result]="SUCCESS"
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
    METRICS[checkpoint3]="PASS"
else
    print_header "❌ ESPERIMENTO FALLITO"
    METRICS[result]="FAIL"
    echo ""
    echo "Uno o più checkpoint non sono stati superati."
    echo "Controlla i log sopra per dettagli."
    echo ""
    print_error "Il sistema richiede debug"
    METRICS[checkpoint3]="FAIL"
fi

# Generate metrics summary
print_header "📈 ANALISI METRICHE"

echo ""
echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│                     TIMING METRICS                              │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Task Creation Time" "$CREATION_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Task Propagation Time" "$PROPAGATION_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Claim Operation Time" "$CLAIM_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Claim Propagation Time" "$CLAIM_PROPAGATION_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Complete Operation Time" "$COMPLETE_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Complete Propagation Time" "$COMPLETE_PROPAGATION_TIME"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s ms${NC} ${CYAN}│${NC}\n" "Total Experiment Duration" "$TOTAL_TIME"
echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"

echo ""
echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│                   ECONOMIC METRICS                              │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Creator Initial Balance" "$BALANCE1_INIT"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Creator Final Balance" "$BALANCE1_FINAL"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Creator Delta" "$CREATOR_DELTA"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Contributor Initial Balance" "$BALANCE2_INIT"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Contributor Final Balance" "$BALANCE2_FINAL"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Contributor Delta" "$CONTRIBUTOR_DELTA"
TAX=$((10 - CONTRIBUTOR_DELTA))
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s SP${NC} ${CYAN}│${NC}\n" "Tax Collected (Treasury)" "$TAX"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s${NC} ${CYAN}│${NC}\n" "Contributor Reputation Gain" "$REP2"
echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"

echo ""
echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│                   CONSENSUS METRICS                             │${NC}"
echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"

BALANCE_DISCREPANCY=0
if [ "$BALANCE2_FINAL" -ne "$BALANCE2_ON_NODE1" ] || [ "$BALANCE2_FINAL" -ne "$BALANCE2_ON_NODE3" ]; then
    BALANCE_DISCREPANCY=1
fi

if [ "$BALANCE_DISCREPANCY" -eq 0 ]; then
    printf "${CYAN}│${NC} %-45s ${GREEN}%10s${NC} ${CYAN}│${NC}\n" "Balance Consensus" "✓ YES"
else
    printf "${CYAN}│${NC} %-45s ${RED}%10s${NC} ${CYAN}│${NC}\n" "Balance Consensus" "✗ NO"
fi

if [ "$STATUS_NODE1" = "$STATUS_NODE2" ] && [ "$STATUS_NODE2" = "$STATUS_NODE3" ]; then
    printf "${CYAN}│${NC} %-45s ${GREEN}%10s${NC} ${CYAN}│${NC}\n" "Status Consensus" "✓ YES"
else
    printf "${CYAN}│${NC} %-45s ${RED}%10s${NC} ${CYAN}│${NC}\n" "Status Consensus" "✗ NO"
fi

printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s${NC} ${CYAN}│${NC}\n" "Checkpoint 1 (Balance Frozen)" "${METRICS[checkpoint1]}"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s${NC} ${CYAN}│${NC}\n" "Checkpoint 2 (Task Claimed)" "${METRICS[checkpoint2]}"
printf "${CYAN}│${NC} %-45s ${MAGENTA}%10s${NC} ${CYAN}│${NC}\n" "Checkpoint 3 (Reward Transfer)" "${METRICS[checkpoint3]}"
echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"

# Save metrics to JSON
cat > "$METRICS_FILE" <<EOF
{
  "experiment_date": "$(date '+%Y-%m-%d %H:%M:%S')",
  "result": "${METRICS[result]}",
  "timing": {
    "task_creation_ms": $CREATION_TIME,
    "task_propagation_ms": $PROPAGATION_TIME,
    "claim_operation_ms": $CLAIM_TIME,
    "claim_propagation_ms": $CLAIM_PROPAGATION_TIME,
    "complete_operation_ms": $COMPLETE_TIME,
    "complete_propagation_ms": $COMPLETE_PROPAGATION_TIME,
    "total_duration_ms": $TOTAL_TIME
  },
  "economic": {
    "creator_initial_sp": $BALANCE1_INIT,
    "creator_final_sp": $BALANCE1_FINAL,
    "creator_delta_sp": $CREATOR_DELTA,
    "contributor_initial_sp": $BALANCE2_INIT,
    "contributor_final_sp": $BALANCE2_FINAL,
    "contributor_delta_sp": $CONTRIBUTOR_DELTA,
    "tax_collected_sp": $TAX,
    "contributor_reputation_gain": $REP2
  },
  "consensus": {
    "balance_consensus": $([ "$BALANCE_DISCREPANCY" -eq 0 ] && echo "true" || echo "false"),
    "status_consensus": $([ "$STATUS_NODE1" = "$STATUS_NODE2" ] && [ "$STATUS_NODE2" = "$STATUS_NODE3" ] && echo "true" || echo "false"),
    "checkpoint1": "${METRICS[checkpoint1]}",
    "checkpoint2": "${METRICS[checkpoint2]}",
    "checkpoint3": "${METRICS[checkpoint3]}"
  },
  "node_ids": {
    "node1": "$NODE1_ID",
    "node2": "$NODE2_ID",
    "node3": "$NODE3_ID"
  },
  "task_id": "$TASK_ID"
}
EOF

echo ""
print_success "📊 Metriche salvate in: $METRICS_FILE"
print_success "📝 Log salvato in: $LOG_FILE"

echo ""
if [ "$SUCCESS" = true ]; then
    exit 0
else
    exit 1
fi
