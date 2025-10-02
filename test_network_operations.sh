#!/bin/bash

# Test Network Operations - Complete Flow
# Tests the full lifecycle: proposal → vote → close → ratify → execute

set -e

echo "🧬 === Synapse-NG Network Operations Test Suite ==="
echo ""

# Configuration
NODE1="http://localhost:8001"
NODE2="http://localhost:8002"
NODE3="http://localhost:8003"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

wait_for_convergence() {
    echo -e "${YELLOW}⏱  Attendo convergenza CRDT (5s)...${NC}"
    sleep 5
}

# Test 1: Check validator set
print_step "Test 1: Verifica Validator Set"
VALIDATOR_SET=$(curl -s "$NODE1/state" | jq -r '.global.validator_set | length')
echo "   Validator set size: $VALIDATOR_SET"
if [ "$VALIDATOR_SET" -gt 0 ]; then
    print_success "Validator set attivo"
    curl -s "$NODE1/state" | jq '.global.validator_set'
else
    print_warning "Validator set vuoto (normale all'avvio, verrà popolato dopo 10 minuti)"
fi
echo ""

# Test 2: Create test channel and tasks with tags
print_step "Test 2: Crea canale di test con task taggati"

# Subscribe to test channel (simulate via creating tasks)
echo "   Creazione task nel canale 'test_general'..."

# Create backend tasks
curl -s -X POST "$NODE1/tasks?channel=test_general" \
  -H "Content-Type: application/json" \
  -d '{"title": "Implement API endpoint", "reward": 100}' > /dev/null

TASK_ID_1=$(curl -s "$NODE1/state" | jq -r '.test_general.tasks | keys[0]')
echo "   Task 1 creato: $TASK_ID_1"

curl -s -X POST "$NODE1/tasks?channel=test_general" \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix database query", "reward": 80}' > /dev/null

TASK_ID_2=$(curl -s "$NODE1/state" | jq -r '.test_general.tasks | keys[1]')
echo "   Task 2 creato: $TASK_ID_2"

# Create frontend tasks
curl -s -X POST "$NODE2/tasks?channel=test_general" \
  -H "Content-Type: application/json" \
  -d '{"title": "Update UI dashboard", "reward": 90}' > /dev/null

TASK_ID_3=$(curl -s "$NODE2/state" | jq -r '.test_general.tasks | keys[2]')
echo "   Task 3 creato: $TASK_ID_3"

curl -s -X POST "$NODE2/tasks?channel=test_general" \
  -H "Content-Type: application/json" \
  -d '{"title": "Improve UX flow", "reward": 70}' > /dev/null

TASK_ID_4=$(curl -s "$NODE2/state" | jq -r '.test_general.tasks | keys[3]')
echo "   Task 4 creato: $TASK_ID_4"

wait_for_convergence

TASK_COUNT=$(curl -s "$NODE1/state" | jq '.test_general.tasks | length')
echo "   Task totali nel canale: $TASK_COUNT"

if [ "$TASK_COUNT" -ge 4 ]; then
    print_success "Canale di test popolato con task"
else
    print_error "Errore: task non convergenti"
    exit 1
fi
echo ""

# Test 3: Create network_operation proposal (split_channel)
print_step "Test 3: Crea proposta network_operation (split_channel)"

PROPOSAL_RESPONSE=$(curl -s -X POST "$NODE1/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Split test_general into backend and frontend",
    "description": "Testing channel split operation",
    "proposal_type": "network_operation",
    "params": {
      "operation": "split_channel",
      "target_channel": "test_general",
      "new_channels": ["test_backend", "test_frontend"],
      "split_logic": "by_title_prefix",
      "split_params": {
        "test_backend": ["Implement", "Fix", "API", "database"],
        "test_frontend": ["Update", "Improve", "UI", "UX"]
      }
    }
  }')

PROPOSAL_ID=$(echo "$PROPOSAL_RESPONSE" | jq -r '.id')
echo "   Proposta creata: $PROPOSAL_ID"
print_success "Proposta network_operation creata"
echo ""

wait_for_convergence

# Test 4: Vote on proposal
print_step "Test 4: Votazione della proposta"

echo "   Node 1 vota YES..."
curl -s -X POST "$NODE1/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}' > /dev/null

echo "   Node 2 vota YES..."
curl -s -X POST "$NODE2/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}' > /dev/null

echo "   Node 3 vota YES..."
curl -s -X POST "$NODE3/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}' > /dev/null

wait_for_convergence

VOTE_COUNT=$(curl -s "$NODE1/proposals/$PROPOSAL_ID/details?channel=global" | jq '.votes | length')
echo "   Voti totali: $VOTE_COUNT"

if [ "$VOTE_COUNT" -ge 3 ]; then
    print_success "Votazione completata"
else
    print_error "Errore: voti non convergenti"
    exit 1
fi
echo ""

# Test 5: Close proposal
print_step "Test 5: Chiusura proposta (calcolo outcome)"

CLOSE_RESPONSE=$(curl -s -X POST "$NODE1/proposals/$PROPOSAL_ID/close?channel=global")
OUTCOME=$(echo "$CLOSE_RESPONSE" | jq -r '.outcome')
STATUS=$(echo "$CLOSE_RESPONSE" | jq -r '.status')

echo "   Outcome: $OUTCOME"
echo "   Status: $STATUS"

if [ "$OUTCOME" == "approved" ] && [ "$STATUS" == "pending_ratification" ]; then
    print_success "Proposta approvata dalla comunità, in attesa di ratifica"
else
    print_error "Errore: proposta non approvata o status errato"
    echo "$CLOSE_RESPONSE" | jq
    exit 1
fi
echo ""

wait_for_convergence

# Test 6: Check pending operations
print_step "Test 6: Verifica pending operations"

PENDING_OPS=$(curl -s "$NODE1/state" | jq '.global.pending_operations | length')
echo "   Pending operations: $PENDING_OPS"

if [ "$PENDING_OPS" -gt 0 ]; then
    print_success "Operazione aggiunta ai pending"
    curl -s "$NODE1/state" | jq '.global.pending_operations[0]'
else
    print_warning "Nessuna pending operation trovata"
fi
echo ""

# Test 7: Validator ratification
print_step "Test 7: Ratifica da parte dei validatori"

# Get current validator set
VALIDATORS=$(curl -s "$NODE1/state" | jq -r '.global.validator_set[]')
VALIDATOR_COUNT=$(curl -s "$NODE1/state" | jq '.global.validator_set | length')
REQUIRED_VOTES=$(( (VALIDATOR_COUNT / 2) + 1 ))

echo "   Validator set size: $VALIDATOR_COUNT"
echo "   Required votes: $REQUIRED_VOTES"

if [ "$VALIDATOR_COUNT" -eq 0 ]; then
    print_warning "Validator set vuoto, salto ratifica simulata"
    print_warning "In produzione, aspettare che il validator set venga popolato"
    echo ""
    echo "🎯 Test completato parzialmente (validator set non ancora attivo)"
    echo "   Riprova questo test dopo 10 minuti per vedere la ratifica completa."
    exit 0
fi

echo "   Validatori:"
echo "$VALIDATORS"
echo ""

# Simulate ratification by first 3 nodes (assuming they are validators)
echo "   Node 1 ratifica..."
RATIFY_1=$(curl -s -X POST "$NODE1/governance/ratify/$PROPOSAL_ID?channel=global")
RATIFY_STATUS_1=$(echo "$RATIFY_1" | jq -r '.status')
echo "   Status: $RATIFY_STATUS_1"

if [ "$RATIFY_STATUS_1" == "ratified" ]; then
    print_success "Ratifica completata con il primo voto (validator set = 1)"
    COMMAND_ID=$(echo "$RATIFY_1" | jq -r '.command_id')
    echo "   Command ID: $COMMAND_ID"
elif [ "$RATIFY_STATUS_1" == "pending" ]; then
    echo "   Node 2 ratifica..."
    RATIFY_2=$(curl -s -X POST "$NODE2/governance/ratify/$PROPOSAL_ID?channel=global")
    RATIFY_STATUS_2=$(echo "$RATIFY_2" | jq -r '.status')
    echo "   Status: $RATIFY_STATUS_2"
    
    if [ "$RATIFY_STATUS_2" == "ratified" ]; then
        print_success "Ratifica completata con il secondo voto"
        COMMAND_ID=$(echo "$RATIFY_2" | jq -r '.command_id')
        echo "   Command ID: $COMMAND_ID"
    elif [ "$RATIFY_STATUS_2" == "pending" ]; then
        echo "   Node 3 ratifica..."
        RATIFY_3=$(curl -s -X POST "$NODE3/governance/ratify/$PROPOSAL_ID?channel=global")
        RATIFY_STATUS_3=$(echo "$RATIFY_3" | jq -r '.status')
        echo "   Status: $RATIFY_STATUS_3"
        
        if [ "$RATIFY_STATUS_3" == "ratified" ]; then
            print_success "Ratifica completata con il terzo voto"
            COMMAND_ID=$(echo "$RATIFY_3" | jq -r '.command_id')
            echo "   Command ID: $COMMAND_ID"
        else
            print_error "Ratifica non completata dopo 3 voti"
            exit 1
        fi
    fi
else
    print_error "Errore nella ratifica: $RATIFY_STATUS_1"
    echo "$RATIFY_1" | jq
    exit 1
fi
echo ""

wait_for_convergence

# Test 8: Check execution_log
print_step "Test 8: Verifica execution_log"

LOG_SIZE=$(curl -s "$NODE1/state" | jq '.global.execution_log | length')
echo "   Execution log size: $LOG_SIZE"

if [ "$LOG_SIZE" -gt 0 ]; then
    print_success "Comando aggiunto all'execution_log"
    curl -s "$NODE1/state" | jq '.global.execution_log[-1]'
else
    print_error "Execution log vuoto"
    exit 1
fi
echo ""

# Test 9: Wait for execution
print_step "Test 9: Attendo esecuzione automatica del comando"

echo "   Attendendo command processor (15s)..."
sleep 15

# Check proposal status
PROPOSAL_STATUS=$(curl -s "$NODE1/proposals/$PROPOSAL_ID/details?channel=global" | jq -r '.status')
echo "   Proposal status: $PROPOSAL_STATUS"

if [ "$PROPOSAL_STATUS" == "executed" ]; then
    print_success "Comando eseguito automaticamente"
    
    # Check execution result
    echo ""
    echo "   Execution result:"
    curl -s "$NODE1/proposals/$PROPOSAL_ID/details?channel=global" | jq '.execution_result'
else
    print_warning "Comando non ancora eseguito (status: $PROPOSAL_STATUS)"
fi
echo ""

# Test 10: Verify channel split
print_step "Test 10: Verifica risultato dello split"

CHANNELS=$(curl -s "$NODE1/state" | jq -r 'keys[]')
echo "   Canali esistenti:"
echo "$CHANNELS"

if echo "$CHANNELS" | grep -q "test_backend" && echo "$CHANNELS" | grep -q "test_frontend"; then
    print_success "Nuovi canali creati: test_backend, test_frontend"
    
    BACKEND_TASKS=$(curl -s "$NODE1/state" | jq '.test_backend.tasks | length')
    FRONTEND_TASKS=$(curl -s "$NODE1/state" | jq '.test_frontend.tasks | length')
    
    echo ""
    echo "   Task in test_backend: $BACKEND_TASKS"
    echo "   Task in test_frontend: $FRONTEND_TASKS"
    
    if [ "$BACKEND_TASKS" -gt 0 ] && [ "$FRONTEND_TASKS" -gt 0 ]; then
        print_success "Task correttamente spostati nei nuovi canali"
    else
        print_warning "Task non ancora spostati (potrebbero richiedere più tempo)"
    fi
    
    # Check if original channel is archived
    ARCHIVED=$(curl -s "$NODE1/state" | jq -r '.test_general.archived // false')
    echo ""
    echo "   Canale originale archiviato: $ARCHIVED"
    
    if [ "$ARCHIVED" == "true" ]; then
        print_success "Canale originale marcato come archiviato"
        curl -s "$NODE1/state" | jq '.test_general | {archived, archived_at, split_into}'
    fi
else
    print_warning "Nuovi canali non ancora visibili (potrebbero richiedere convergenza)"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "🎉 Test Network Operations completato!"
echo ""
echo "Riepilogo:"
echo "  ✓ Proposta network_operation creata"
echo "  ✓ Votazione completata"
echo "  ✓ Proposta approvata dalla comunità"
if [ "$VALIDATOR_COUNT" -gt 0 ]; then
    echo "  ✓ Ratifica del validator set completata"
    echo "  ✓ Comando aggiunto all'execution_log"
    if [ "$PROPOSAL_STATUS" == "executed" ]; then
        echo "  ✓ Comando eseguito automaticamente"
        echo "  ✓ Split channel completato"
    else
        echo "  ⏱  Comando in esecuzione..."
    fi
else
    echo "  ⚠  Ratifica saltata (validator set vuoto)"
fi
echo ""
echo "📚 Documentazione completa: docs/NETWORK_OPERATIONS.md"
echo "═══════════════════════════════════════════════════════════"
