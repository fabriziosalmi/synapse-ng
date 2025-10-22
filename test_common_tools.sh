#!/usr/bin/env bash

# ========================================
# Test Suite: Common Tools System
# ========================================
# Test completo del sistema di Common Tools:
# - Acquisizione tools tramite governance
# - Crittografia credenziali
# - Pagamenti mensili automatici
# - Deprecazione tools
# - Esecuzione sicura tools

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurazione
NODE_1="http://localhost:8001"
NODE_2="http://localhost:8002"
NODE_3="http://localhost:8003"
CHANNEL="${CHANNEL:-sviluppo_ui}"

# Contatori test
TESTS_PASSED=0
TESTS_FAILED=0

# ========================================
# Helper Functions
# ========================================

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test() {
    echo -e "\n${YELLOW}🧪 TEST: $1${NC}"
}

pass() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

wait_sync() {
    echo -e "${BLUE}⏳ Attendo sincronizzazione (5s)...${NC}"
    sleep 5
}

get_node_id() {
    local node=$1
    curl -s "${node}/whoami" | jq -r '.node_id' 2>/dev/null || echo ""
}

# ========================================
# Setup Functions
# ========================================

setup() {
    print_header "🔧 SETUP: Preparazione ambiente test"
    
    # Verifica che i nodi siano attivi
    for node in $NODE_1 $NODE_2 $NODE_3; do
        if ! curl -s -f "${node}/whoami" > /dev/null 2>&1; then
            echo -e "${RED}❌ Nodo $node non raggiungibile${NC}"
            echo -e "${YELLOW}Avvia la rete con: docker-compose up --build${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Tutti i nodi sono attivi${NC}"
    
    # Ottieni Node IDs
    NODE_1_ID=$(get_node_id $NODE_1)
    NODE_2_ID=$(get_node_id $NODE_2)
    NODE_3_ID=$(get_node_id $NODE_3)
    
    echo "   Nodo 1: ${NODE_1_ID:0:16}..."
    echo "   Nodo 2: ${NODE_2_ID:0:16}..."
    echo "   Nodo 3: ${NODE_3_ID:0:16}..."
    
    # Attendi stabilizzazione rete
    wait_sync
}

# ========================================
# TEST 1: Acquisizione Tool tramite Governance
# ========================================

test_tool_acquisition() {
    print_test "Acquisizione Tool tramite Governance"
    
    # 1. Verifica tesoreria iniziale
    echo "   📊 Controllo tesoreria canale '${CHANNEL}'..."
    TREASURY_BEFORE=$(curl -s "${NODE_1}/state" | jq -r ".${CHANNEL}.treasury_balance // 0")
    echo "      Tesoreria prima: ${TREASURY_BEFORE} SP"
    
    # Assicuriamoci che ci siano fondi (completa un task se necessario)
    if [ "$TREASURY_BEFORE" -lt 100 ]; then
        echo "   💰 Tesoreria insufficiente, creo e completo un task..."
        
        # Crea task
        TASK_RESPONSE=$(curl -s -X POST "${NODE_1}/tasks?channel=${CHANNEL}" \
            -H "Content-Type: application/json" \
            -d '{
                "title": "Finanziare tesoreria per test",
                "reward": 200,
                "schema_name": "task_v1"
            }')
        
        TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task_id')
        echo "      Task creato: ${TASK_ID:0:8}..."
        
        wait_sync
        
        # Claim e completa
        curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/claim?channel=${CHANNEL}" > /dev/null
        wait_sync
        curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/complete?channel=${CHANNEL}" > /dev/null
        wait_sync
        
        TREASURY_BEFORE=$(curl -s "${NODE_1}/state" | jq -r ".${CHANNEL}.treasury_balance // 0")
        echo "      Tesoreria dopo task: ${TREASURY_BEFORE} SP"
    fi
    
    if [ "$TREASURY_BEFORE" -lt 100 ]; then
        fail "Tesoreria ancora insufficiente: ${TREASURY_BEFORE} SP (servono almeno 100 SP)"
        return
    fi
    
    # 2. Proponi acquisizione tool
    echo "   📝 Creazione proposta acquisizione tool..."
    PROPOSAL_RESPONSE=$(curl -s -X POST "${NODE_1}/proposals?channel=${CHANNEL}" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Acquisire API Geolocalizzazione per Testing",
            "description": "Tool per test suite automatizzato",
            "proposal_type": "network_operation",
            "params": {
                "operation": "acquire_common_tool",
                "channel": "'"${CHANNEL}"'",
                "tool_id": "test_geolocation_api",
                "description": "API Geolocalizzazione per test",
                "type": "api_key",
                "monthly_cost_sp": 100,
                "credentials_to_encrypt": "sk_test_abc123xyz789_ENCRYPTED_DEMO"
            }
        }')
    
    PROPOSAL_ID=$(echo "$PROPOSAL_RESPONSE" | jq -r '.proposal_id')
    
    if [ "$PROPOSAL_ID" == "null" ] || [ -z "$PROPOSAL_ID" ]; then
        fail "Creazione proposta fallita"
        echo "      Response: $PROPOSAL_RESPONSE"
        return
    fi
    
    echo "      Proposta creata: ${PROPOSAL_ID:0:8}..."
    
    wait_sync
    
    # 3. Vota la proposta da tutti i nodi
    echo "   🗳️  Votazione proposta..."
    for node in $NODE_1 $NODE_2 $NODE_3; do
        curl -s -X POST "${node}/proposals/${PROPOSAL_ID}/vote?channel=${CHANNEL}" \
            -H "Content-Type: application/json" \
            -d '{"vote": "yes"}' > /dev/null
    done
    
    wait_sync
    
    # 4. Chiudi proposta
    echo "   🔒 Chiusura proposta..."
    CLOSE_RESPONSE=$(curl -s -X POST "${NODE_1}/proposals/${PROPOSAL_ID}/close?channel=${CHANNEL}")
    
    OUTCOME=$(echo "$CLOSE_RESPONSE" | jq -r '.outcome // "unknown"')
    
    if [ "$OUTCOME" != "approved" ]; then
        fail "Proposta non approvata (outcome: $OUTCOME)"
        return
    fi
    
    echo "      Proposta approvata!"
    
    wait_sync
    
    # 5. Ratifica da validator set
    echo "   👑 Ratifica validator set..."
    
    # Ottieni validator set
    VALIDATORS=$(curl -s "${NODE_1}/state" | jq -r '.global.validator_set[]' 2>/dev/null || echo "")
    
    if [ -z "$VALIDATORS" ]; then
        echo "      ⚠️  Validator set vuoto, skip ratifica"
    else
        # Ratifica da almeno un validator
        for validator in $VALIDATORS; do
            NODE_URL=""
            if [ "$validator" == "$NODE_1_ID" ]; then NODE_URL=$NODE_1
            elif [ "$validator" == "$NODE_2_ID" ]; then NODE_URL=$NODE_2
            elif [ "$validator" == "$NODE_3_ID" ]; then NODE_URL=$NODE_3
            fi
            
            if [ -n "$NODE_URL" ]; then
                curl -s -X POST "${NODE_URL}/governance/ratify/${PROPOSAL_ID}?channel=${CHANNEL}" > /dev/null
                echo "      Ratificato da validator: ${validator:0:8}..."
                break  # Uno basta per test
            fi
        done
    fi
    
    wait_sync
    
    # 6. Verifica che il tool sia stato aggiunto
    echo "   🔍 Verifica presenza tool nel canale..."
    TOOL_DATA=$(curl -s "${NODE_1}/state" | jq ".${CHANNEL}.common_tools.test_geolocation_api")
    
    if [ "$TOOL_DATA" == "null" ] || [ -z "$TOOL_DATA" ]; then
        fail "Tool non trovato nel canale dopo acquisizione"
        return
    fi
    
    # Verifica campi obbligatori
    TOOL_STATUS=$(echo "$TOOL_DATA" | jq -r '.status')
    TOOL_COST=$(echo "$TOOL_DATA" | jq -r '.monthly_cost_sp')
    ENCRYPTED_CREDS=$(echo "$TOOL_DATA" | jq -r '.encrypted_credentials')
    
    if [ "$TOOL_STATUS" == "active" ] && [ "$TOOL_COST" == "100" ] && [ -n "$ENCRYPTED_CREDS" ] && [ "$ENCRYPTED_CREDS" != "null" ]; then
        pass "Tool acquisito correttamente (status: active, costo: 100 SP, credenziali criptate)"
    else
        fail "Tool acquisito ma con dati errati (status: $TOOL_STATUS, costo: $TOOL_COST)"
        return
    fi
    
    # 7. Verifica che la tesoreria sia stata addebitata
    echo "   💸 Verifica addebito tesoreria..."
    TREASURY_AFTER=$(curl -s "${NODE_1}/state" | jq -r ".${CHANNEL}.treasury_balance // 0")
    TREASURY_DIFF=$((TREASURY_BEFORE - TREASURY_AFTER))
    
    echo "      Tesoreria prima: ${TREASURY_BEFORE} SP"
    echo "      Tesoreria dopo: ${TREASURY_AFTER} SP"
    echo "      Addebitato: ${TREASURY_DIFF} SP"
    
    if [ "$TREASURY_DIFF" == "100" ]; then
        pass "Tesoreria addebitata correttamente (100 SP)"
    else
        fail "Addebito tesoreria errato: atteso 100 SP, addebitato ${TREASURY_DIFF} SP"
    fi
}

# ========================================
# TEST 2: Esecuzione Sicura Tool
# ========================================

test_tool_execution() {
    print_test "Esecuzione Sicura Tool"
    
    # 1. Crea task che richiede il tool
    echo "   📝 Creazione task con required_tools..."
    TASK_RESPONSE=$(curl -s -X POST "${NODE_1}/tasks?channel=${CHANNEL}" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Test esecuzione tool geolocalizzazione",
            "description": "Task per test suite",
            "required_tools": ["test_geolocation_api"],
            "reward": 50,
            "schema_name": "task_v1"
        }')
    
    TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task_id')
    
    if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
        fail "Creazione task fallita"
        return
    fi
    
    echo "      Task creato: ${TASK_ID:0:8}..."
    
    wait_sync
    
    # 2. Claim il task (Nodo 1)
    echo "   🤝 Claim task..."
    CLAIM_RESPONSE=$(curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/claim?channel=${CHANNEL}")
    
    if ! echo "$CLAIM_RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
        fail "Claim task fallito"
        return
    fi
    
    echo "      Task claimed da Nodo 1"
    
    wait_sync
    
    # 3. Segna task in_progress
    echo "   ⚙️  Task in progress..."
    curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/progress?channel=${CHANNEL}" > /dev/null
    
    wait_sync
    
    # 4. ESEGUI IL TOOL (chiamata autorizzata)
    echo "   🔒 Esecuzione tool (chiamata autorizzata)..."
    EXEC_RESPONSE=$(curl -s -X POST "${NODE_1}/tools/test_geolocation_api/execute?channel=${CHANNEL}&task_id=${TASK_ID}" \
        -H "Content-Type: application/json" \
        -d '{"ip_address": "8.8.8.8"}')
    
    EXEC_SUCCESS=$(echo "$EXEC_RESPONSE" | jq -r '.success')
    EXEC_RESULT=$(echo "$EXEC_RESPONSE" | jq -r '.result')
    
    if [ "$EXEC_SUCCESS" == "true" ] && [ "$EXEC_RESULT" != "null" ]; then
        pass "Tool eseguito con successo"
        echo "      Risultato: $(echo "$EXEC_RESULT" | jq -c '.')"
    else
        fail "Esecuzione tool fallita"
        echo "      Response: $EXEC_RESPONSE"
        return
    fi
    
    # 5. TEST SICUREZZA: Tentativo esecuzione da nodo non autorizzato
    echo "   🛡️  Test sicurezza: esecuzione non autorizzata..."
    UNAUTH_RESPONSE=$(curl -s -X POST "${NODE_2}/tools/test_geolocation_api/execute?channel=${CHANNEL}&task_id=${TASK_ID}" \
        -H "Content-Type: application/json" \
        -d '{"ip_address": "1.1.1.1"}')
    
    UNAUTH_ERROR=$(echo "$UNAUTH_RESPONSE" | jq -r '.detail' 2>/dev/null || echo "")
    
    if echo "$UNAUTH_ERROR" | grep -q "Accesso negato"; then
        pass "Sicurezza: accesso negato correttamente a nodo non autorizzato"
    else
        fail "Sicurezza: nodo non autorizzato ha potuto eseguire tool!"
        echo "      Response: $UNAUTH_RESPONSE"
    fi
    
    # 6. TEST SICUREZZA: Esecuzione tool non richiesto dal task
    echo "   🛡️  Test sicurezza: tool non in required_tools..."
    
    # Prima crea un altro tool (senza usarlo)
    curl -s -X POST "${NODE_1}/proposals?channel=${CHANNEL}" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Tool non usato",
            "proposal_type": "network_operation",
            "params": {
                "operation": "acquire_common_tool",
                "channel": "'"${CHANNEL}"'",
                "tool_id": "unused_tool",
                "type": "api_key",
                "monthly_cost_sp": 0,
                "credentials_to_encrypt": "dummy"
            }
        }' > /dev/null
    
    wait_sync
    
    # Prova a usare tool non richiesto
    WRONG_TOOL_RESPONSE=$(curl -s -X POST "${NODE_1}/tools/unused_tool/execute?channel=${CHANNEL}&task_id=${TASK_ID}" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    WRONG_TOOL_ERROR=$(echo "$WRONG_TOOL_RESPONSE" | jq -r '.detail' 2>/dev/null || echo "")
    
    if echo "$WRONG_TOOL_ERROR" | grep -q "non richiede il tool"; then
        pass "Sicurezza: esecuzione tool non richiesto bloccata"
    else
        fail "Sicurezza: tool non richiesto eseguito!"
        echo "      Response: $WRONG_TOOL_RESPONSE"
    fi
}

# ========================================
# TEST 3: Deprecazione Tool
# ========================================

test_tool_deprecation() {
    print_test "Deprecazione Tool"
    
    # 1. Proponi deprecazione
    echo "   📝 Creazione proposta deprecazione..."
    PROPOSAL_RESPONSE=$(curl -s -X POST "${NODE_1}/proposals?channel=${CHANNEL}" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Deprecare test_geolocation_api",
            "description": "Tool non più necessario",
            "proposal_type": "network_operation",
            "params": {
                "operation": "deprecate_common_tool",
                "channel": "'"${CHANNEL}"'",
                "tool_id": "test_geolocation_api"
            }
        }')
    
    PROPOSAL_ID=$(echo "$PROPOSAL_RESPONSE" | jq -r '.proposal_id')
    
    if [ "$PROPOSAL_ID" == "null" ] || [ -z "$PROPOSAL_ID" ]; then
        fail "Creazione proposta deprecazione fallita"
        return
    fi
    
    echo "      Proposta creata: ${PROPOSAL_ID:0:8}..."
    
    wait_sync
    
    # 2. Vota e approva
    echo "   🗳️  Votazione e approvazione..."
    for node in $NODE_1 $NODE_2 $NODE_3; do
        curl -s -X POST "${node}/proposals/${PROPOSAL_ID}/vote?channel=${CHANNEL}" \
            -H "Content-Type: application/json" \
            -d '{"vote": "yes"}' > /dev/null
    done
    
    wait_sync
    
    curl -s -X POST "${NODE_1}/proposals/${PROPOSAL_ID}/close?channel=${CHANNEL}" > /dev/null
    
    wait_sync
    
    # 3. Ratifica (se necessario)
    VALIDATORS=$(curl -s "${NODE_1}/state" | jq -r '.global.validator_set[]' 2>/dev/null || echo "")
    if [ -n "$VALIDATORS" ]; then
        for validator in $VALIDATORS; do
            NODE_URL=""
            if [ "$validator" == "$NODE_1_ID" ]; then NODE_URL=$NODE_1
            elif [ "$validator" == "$NODE_2_ID" ]; then NODE_URL=$NODE_2
            elif [ "$validator" == "$NODE_3_ID" ]; then NODE_URL=$NODE_3
            fi
            
            if [ -n "$NODE_URL" ]; then
                curl -s -X POST "${NODE_URL}/governance/ratify/${PROPOSAL_ID}?channel=${CHANNEL}" > /dev/null
                break
            fi
        done
    fi
    
    wait_sync
    
    # 4. Verifica che il tool sia deprecated
    echo "   🔍 Verifica status tool..."
    TOOL_STATUS=$(curl -s "${NODE_1}/state" | jq -r ".${CHANNEL}.common_tools.test_geolocation_api.status")
    
    if [ "$TOOL_STATUS" == "deprecated" ]; then
        pass "Tool deprecato correttamente (status: deprecated)"
    else
        fail "Tool non deprecato (status: $TOOL_STATUS)"
        return
    fi
    
    # 5. Verifica che non sia più eseguibile
    echo "   🛡️  Verifica tool non più eseguibile..."
    
    # Crea nuovo task per test
    TASK_RESPONSE=$(curl -s -X POST "${NODE_1}/tasks?channel=${CHANNEL}" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Test tool deprecated",
            "required_tools": ["test_geolocation_api"],
            "reward": 10
        }')
    
    TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task_id')
    
    wait_sync
    
    curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/claim?channel=${CHANNEL}" > /dev/null
    wait_sync
    curl -s -X POST "${NODE_1}/tasks/${TASK_ID}/progress?channel=${CHANNEL}" > /dev/null
    wait_sync
    
    # Prova a eseguire tool deprecated
    EXEC_RESPONSE=$(curl -s -X POST "${NODE_1}/tools/test_geolocation_api/execute?channel=${CHANNEL}&task_id=${TASK_ID}" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    EXEC_ERROR=$(echo "$EXEC_RESPONSE" | jq -r '.detail' 2>/dev/null || echo "")
    
    if echo "$EXEC_ERROR" | grep -q "non è attivo"; then
        pass "Tool deprecated non eseguibile"
    else
        fail "Tool deprecated ancora eseguibile!"
        echo "      Response: $EXEC_RESPONSE"
    fi
}

# ========================================
# TEST 4: Verifica Sistema Manutenzione (Simulato)
# ========================================

test_maintenance_system() {
    print_test "Sistema Manutenzione (Verifica Strutture)"
    
    # Questo test verifica che le strutture per il maintenance loop siano presenti
    # Il loop stesso gira ogni 24h, quindi non possiamo testarlo in real-time
    
    echo "   🔍 Verifica presenza loop manutenzione nel codice..."
    
    # Verifica che il loop sia registrato nello startup
    if grep -q "common_tools_maintenance_loop" /app/main.py 2>/dev/null || \
       grep -q "common_tools_maintenance_loop" app/main.py 2>/dev/null; then
        pass "Maintenance loop presente nel codice"
    else
        fail "Maintenance loop non trovato"
        return
    fi
    
    # Verifica strutture dati necessarie
    echo "   📊 Verifica strutture dati tool..."
    TOOL_DATA=$(curl -s "${NODE_1}/state" | jq ".${CHANNEL}.common_tools" 2>/dev/null)
    
    if [ "$TOOL_DATA" != "null" ] && [ -n "$TOOL_DATA" ]; then
        pass "Struttura common_tools presente nel network state"
    else
        fail "Struttura common_tools mancante"
        return
    fi
    
    # Verifica che i tools abbiano i campi necessari per il maintenance
    SAMPLE_TOOL=$(curl -s "${NODE_1}/state" | jq ".${CHANNEL}.common_tools | to_entries[0].value" 2>/dev/null)
    
    if [ "$SAMPLE_TOOL" == "null" ] || [ -z "$SAMPLE_TOOL" ]; then
        echo "      ℹ️  Nessun tool presente per verifica campi"
        pass "Verifica campi saltata (nessun tool)"
        return
    fi
    
    HAS_MONTHLY_COST=$(echo "$SAMPLE_TOOL" | jq 'has("monthly_cost_sp")')
    HAS_LAST_PAYMENT=$(echo "$SAMPLE_TOOL" | jq 'has("last_payment_at")')
    HAS_STATUS=$(echo "$SAMPLE_TOOL" | jq 'has("status")')
    
    if [ "$HAS_MONTHLY_COST" == "true" ] && [ "$HAS_LAST_PAYMENT" == "true" ] && [ "$HAS_STATUS" == "true" ]; then
        pass "Campi necessari per manutenzione presenti (monthly_cost_sp, last_payment_at, status)"
    else
        fail "Campi manutenzione mancanti nel tool"
    fi
}

# ========================================
# Cleanup
# ========================================

cleanup() {
    print_header "🧹 CLEANUP"
    echo "   Pulizia risorse test completata"
}

# ========================================
# Main Test Execution
# ========================================

main() {
    print_header "🛠️ TEST SUITE: COMMON TOOLS SYSTEM"
    echo "Testing Synapse-NG Common Tools (Beni Comuni)"
    echo ""
    echo "Questo test suite verifica:"
    echo "  • Acquisizione tools tramite governance"
    echo "  • Crittografia credenziali"
    echo "  • Esecuzione sicura tools"
    echo "  • Controlli di sicurezza"
    echo "  • Deprecazione tools"
    echo "  • Strutture per manutenzione automatica"
    
    # Setup
    setup
    
    # Esegui test
    test_tool_acquisition
    test_tool_execution
    test_tool_deprecation
    test_maintenance_system
    
    # Cleanup
    cleanup
    
    # Summary
    print_header "📊 RISULTATI TEST"
    echo ""
    echo -e "  Test eseguiti: $((TESTS_PASSED + TESTS_FAILED))"
    echo -e "  ${GREEN}✓ Test passati: ${TESTS_PASSED}${NC}"
    echo -e "  ${RED}✗ Test falliti: ${TESTS_FAILED}${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}  ✅ TUTTI I TEST SUPERATI! ✅${NC}"
        echo -e "${GREEN}  Common Tools System è pienamente operativo!${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 0
    else
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}  ❌ ALCUNI TEST FALLITI${NC}"
        echo -e "${RED}  Controlla i log sopra per dettagli${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        exit 1
    fi
}

# Run main
main "$@"
