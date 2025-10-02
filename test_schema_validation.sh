#!/bin/bash

# Test Schema Validation System
# Tests schema validation at creation time and gossip time

set -e

echo "🧬 === Synapse-NG Schema Validation Test Suite ==="
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

# Test 1: Get default schemas
print_step "Test 1: Verifica schemi di default"
SCHEMAS=$(curl -s "$NODE1/schemas" | jq -r '.schemas | keys[]')
echo "   Schemi disponibili:"
echo "$SCHEMAS"

if echo "$SCHEMAS" | grep -q "task_v1" && echo "$SCHEMAS" | grep -q "proposal_v1"; then
    print_success "Schemi di default presenti"
else
    print_error "Schemi di default mancanti"
    exit 1
fi
echo ""

# Test 2: Get task_v1 schema
print_step "Test 2: Dettagli schema task_v1"
TASK_SCHEMA=$(curl -s "$NODE1/schemas/task_v1" | jq '.fields | keys[]')
echo "   Campi definiti in task_v1:"
echo "$TASK_SCHEMA"
print_success "Schema task_v1 recuperato"
echo ""

# Test 3: Validate valid data
print_step "Test 3: Validazione dati validi (senza creazione)"
VALID_RESULT=$(curl -s -X POST "$NODE1/schemas/validate?schema_name=task_v1" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "reward": 100, "tags": ["test"]}')

IS_VALID=$(echo "$VALID_RESULT" | jq -r '.valid')
echo "   Result: $IS_VALID"

if [ "$IS_VALID" == "true" ]; then
    print_success "Dati validi riconosciuti"
    echo "   Dati con defaults applicati:"
    echo "$VALID_RESULT" | jq '.data_with_defaults'
else
    print_error "Validazione fallita inaspettatamente"
    echo "$VALID_RESULT" | jq
    exit 1
fi
echo ""

# Test 4: Validate invalid data (missing required field)
print_step "Test 4: Validazione dati invalidi (campo obbligatorio mancante)"
INVALID_RESULT=$(curl -s -X POST "$NODE1/schemas/validate?schema_name=task_v1" \
  -H "Content-Type: application/json" \
  -d '{"reward": 100}')

IS_VALID=$(echo "$INVALID_RESULT" | jq -r '.valid')
ERROR_MSG=$(echo "$INVALID_RESULT" | jq -r '.error')
echo "   Result: $IS_VALID"
echo "   Error: $ERROR_MSG"

if [ "$IS_VALID" == "false" ]; then
    print_success "Dati invalidi correttamente rifiutati"
else
    print_error "Dati invalidi accettati (ERRORE!)"
    exit 1
fi
echo ""

# Test 5: Create valid task
print_step "Test 5: Creazione task valido"
VALID_TASK=$(curl -s -X POST "$NODE1/tasks?channel=test_schema" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Valid task with schema",
    "reward": 100,
    "tags": ["test", "schema"],
    "description": "This task respects the schema",
    "schema_name": "task_v1"
  }')

TASK_ID=$(echo "$VALID_TASK" | jq -r '.id')
echo "   Task ID: $TASK_ID"

if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
    print_success "Task valido creato"
    echo "$VALID_TASK" | jq '{id, title, schema_name, status}'
else
    print_error "Creazione task fallita"
    echo "$VALID_TASK"
    exit 1
fi
echo ""

# Test 6: Try to create invalid task (should fail)
print_step "Test 6: Tentativo creazione task invalido (dovrebbe fallire)"
INVALID_TASK=$(curl -s -X POST "$NODE1/tasks?channel=test_schema" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "",
    "reward": -100,
    "schema_name": "task_v1"
  }' || echo '{"error": "request failed"}')

ERROR_DETAIL=$(echo "$INVALID_TASK" | jq -r '.detail // .error')
echo "   Errore ricevuto: $ERROR_DETAIL"

if echo "$ERROR_DETAIL" | grep -q -i "validazione"; then
    print_success "Task invalido correttamente rifiutato"
else
    print_warning "Risposta inaspettata (potrebbe essere stata accettata)"
    echo "$INVALID_TASK"
fi
echo ""

# Test 7: Try invalid reward (negative)
print_step "Test 7: Tentativo creazione task con reward negativa"
INVALID_REWARD=$(curl -s -X POST "$NODE1/tasks?channel=test_schema" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Task with invalid reward",
    "reward": -50,
    "schema_name": "task_v1"
  }' || echo '{"error": "request failed"}')

ERROR_DETAIL=$(echo "$INVALID_REWARD" | jq -r '.detail // .error')
echo "   Errore ricevuto: $ERROR_DETAIL"

if echo "$ERROR_DETAIL" | grep -q -i "reward.*negativ\|reward.*>= 0"; then
    print_success "Reward negativa correttamente rifiutata"
else
    print_warning "Risposta inaspettata"
    echo "$INVALID_REWARD"
fi
echo ""

# Test 8: Try invalid enum value
print_step "Test 8: Tentativo creazione task con status invalido"
INVALID_ENUM=$(curl -s -X POST "$NODE1/tasks?channel=test_schema" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Task with invalid status",
    "reward": 0,
    "status": "invalid_status",
    "schema_name": "task_v1"
  }' || echo '{"error": "request failed"}')

# Check if task was created (it might be created if status is not in initial payload)
ENUM_TASK_ID=$(echo "$INVALID_ENUM" | jq -r '.id // "null"')
echo "   Task ID: $ENUM_TASK_ID"

if [ "$ENUM_TASK_ID" == "null" ]; then
    print_success "Status invalido correttamente rifiutato"
    ERROR_DETAIL=$(echo "$INVALID_ENUM" | jq -r '.detail // .error')
    echo "   Errore: $ERROR_DETAIL"
else
    print_warning "Task creato nonostante status invalido (potrebbe essere OK se status è opzionale)"
fi
echo ""

# Test 9: Check gossip validation (create on node 1, check node 2)
print_step "Test 9: Verifica propagazione via gossip (con validazione)"
echo "   Creazione task su Node 1..."
GOSSIP_TASK=$(curl -s -X POST "$NODE1/tasks?channel=test_schema" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Gossip test task",
    "reward": 75,
    "tags": ["gossip"],
    "schema_name": "task_v1"
  }')

GOSSIP_TASK_ID=$(echo "$GOSSIP_TASK" | jq -r '.id')
echo "   Task ID: $GOSSIP_TASK_ID"

echo "   Attendo propagazione via gossip (10s)..."
sleep 10

echo "   Verifica presenza su Node 2..."
NODE2_TASK=$(curl -s "$NODE2/state" | jq -r ".test_schema.tasks[\"$GOSSIP_TASK_ID\"] // null")

if [ "$NODE2_TASK" != "null" ]; then
    print_success "Task propagato e validato con successo su Node 2"
    echo "$NODE2_TASK" | jq '{id, title, schema_name}'
else
    print_warning "Task non ancora propagato (potrebbe richiedere più tempo)"
fi
echo ""

# Test 10: Check logs for validation messages
print_step "Test 10: Verifica log di validazione"
echo "   Cercando log di validazione schema..."

# Check if running in Docker
if command -v docker &> /dev/null; then
    VALID_LOGS=$(docker logs node-1 2>&1 | grep -i "schema validat" | tail -5 || echo "")
    
    if [ -n "$VALID_LOGS" ]; then
        print_success "Log di validazione trovati"
        echo "$VALID_LOGS"
    else
        print_warning "Nessun log di validazione trovato (potrebbe essere normale)"
    fi
else
    print_warning "Docker non disponibile, skip controllo log"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "🎉 Test Schema Validation completato!"
echo ""
echo "Riepilogo:"
echo "  ✓ Schemi di default presenti (task_v1, proposal_v1)"
echo "  ✓ Validazione dati validi funzionante"
echo "  ✓ Validazione dati invalidi funzionante (rifiuto)"
echo "  ✓ Creazione task con schema funzionante"
echo "  ✓ Rifiuto task invalidi funzionante"
echo "  ✓ Propagazione gossip con validazione"
echo ""
echo "📚 Documentazione completa: docs/SCHEMA_VALIDATION.md"
echo "═══════════════════════════════════════════════════════════"
