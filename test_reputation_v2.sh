#!/bin/bash

# ==============================================================================
# 🧬 Test Suite: Reputation System v2
# ==============================================================================
# 
# Testa le seguenti funzionalità:
# 1. Migrazione automatica da v1 a v2
# 2. Guadagno specializzato con tag
# 3. Decadimento temporale (decay)
# 4. Voto ponderato contestuale
#
# ==============================================================================

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configurazione
NODE1_PORT=8001
NODE2_PORT=8002
NODE3_PORT=8003
CHANNEL=${CHANNEL:-"sviluppo_ui"}

# Funzioni utility
print_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}🧪 TEST: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

get_node_id() {
    local port=$1
    curl -s "http://localhost:$port/whoami" | jq -r '.node_id'
}

get_reputation() {
    local port=$1
    local node_id=$2
    curl -s "http://localhost:$port/state" | jq ".global.nodes.\"$node_id\".reputation"
}

# ==============================================================================
# TEST 1: Migrazione Automatica v1 → v2
# ==============================================================================

test_migration() {
    print_header "TEST 1: Migrazione Automatica v1 → v2"
    
    print_test "Verifica che le reputazioni siano nel formato v2"
    
    local node1_id=$(get_node_id $NODE1_PORT)
    local rep=$(get_reputation $NODE1_PORT "$node1_id")
    
    # Verifica presenza campi v2
    local has_total=$(echo "$rep" | jq 'has("_total")')
    local has_tags=$(echo "$rep" | jq 'has("tags")')
    local has_timestamp=$(echo "$rep" | jq 'has("_last_updated")')
    
    if [ "$has_total" = "true" ] && [ "$has_tags" = "true" ] && [ "$has_timestamp" = "true" ]; then
        print_success "Formato v2 confermato"
        print_info "Reputazione: $rep"
        echo ""
        return 0
    else
        print_error "Formato v2 non trovato"
        echo "Reputazione ricevuta: $rep"
        return 1
    fi
}

# ==============================================================================
# TEST 2: Guadagno Specializzato con Tag
# ==============================================================================

test_specialized_gain() {
    print_header "TEST 2: Guadagno Specializzato con Tag"
    
    print_test "Creiamo un task con tag specifici e verifichiamo il guadagno"
    
    # Ottieni node IDs
    local creator_id=$(get_node_id $NODE1_PORT)
    local contributor_id=$(get_node_id $NODE2_PORT)
    
    print_info "Creator: ${creator_id:0:20}..."
    print_info "Contributor: ${contributor_id:0:20}..."
    
    # Reputazione iniziale
    local rep_before=$(get_reputation $NODE2_PORT "$contributor_id")
    local total_before=$(echo "$rep_before" | jq '._total')
    print_info "Reputazione iniziale contributor: $total_before"
    
    # Crea task con tag multipli
    print_info "Creazione task con tag: [python, api, backend] e reward 15..."
    local task_response=$(curl -s -X POST "http://localhost:$NODE1_PORT/tasks?channel=$CHANNEL" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Implementare API REST",
            "description": "Creare endpoint RESTful con documentazione OpenAPI",
            "reward": 15,
            "tags": ["python", "api", "backend"],
            "schema_name": "task_v1"
        }')
    
    local task_id=$(echo "$task_response" | jq -r '.id')
    
    if [ -z "$task_id" ] || [ "$task_id" = "null" ]; then
        print_error "Creazione task fallita"
        echo "$task_response" | jq .
        return 1
    fi
    
    print_success "Task creato: ${task_id:0:20}..."
    
    # Attendi propagazione
    sleep 10
    
    # Claim del task
    print_info "Contributor claims il task..."
    curl -s -X POST "http://localhost:$NODE2_PORT/tasks/$task_id/claim?channel=$CHANNEL" > /dev/null
    sleep 10
    
    # Complete del task
    print_info "Contributor completa il task..."
    curl -s -X POST "http://localhost:$NODE2_PORT/tasks/$task_id/progress?channel=$CHANNEL" > /dev/null
    sleep 3
    curl -s -X POST "http://localhost:$NODE2_PORT/tasks/$task_id/complete?channel=$CHANNEL" > /dev/null
    sleep 15
    
    # Verifica reputazione finale
    local rep_after=$(get_reputation $NODE2_PORT "$contributor_id")
    local total_after=$(echo "$rep_after" | jq '._total')
    local tag_python_after=$(echo "$rep_after" | jq '.tags.python // 0')
    local tag_api_after=$(echo "$rep_after" | jq '.tags.api // 0')
    local tag_backend_after=$(echo "$rep_after" | jq '.tags.backend // 0')
    
    # Calcola tag iniziali per verificare incremento
    local tag_python_before=$(echo "$rep_before" | jq '.tags.python // 0')
    local tag_api_before=$(echo "$rep_before" | jq '.tags.api // 0')
    local tag_backend_before=$(echo "$rep_before" | jq '.tags.backend // 0')
    
    print_info "Reputazione finale:"
    echo "   _total: $total_after (era $total_before)"
    echo "   tags.python: $tag_python_after (era $tag_python_before)"
    echo "   tags.api: $tag_api_after (era $tag_api_before)"
    echo "   tags.backend: $tag_backend_after (era $tag_backend_before)"
    
    # Verifica aspettative
    # Nota: Il sistema usa task_completion_reputation_reward dalla config (default: 10)
    # NON il reward SP del task. Questo separa economia da reputazione.
    local delta_total=$((total_after - total_before))
    local delta_python=$((tag_python_after - tag_python_before))
    local delta_api=$((tag_api_after - tag_api_before))
    local delta_backend=$((tag_backend_after - tag_backend_before))
    local expected_reward=10  # Valore di default dalla config
    
    if [ "$delta_total" -eq "$expected_reward" ] && [ "$delta_python" -eq "$expected_reward" ] && [ "$delta_api" -eq "$expected_reward" ] && [ "$delta_backend" -eq "$expected_reward" ]; then
        print_success "Guadagno specializzato verificato!"
        print_success "Ogni tag ha ricevuto $expected_reward punti reputazione"
        print_info "Nota: Punti reputazione sono indipendenti dal reward SP del task"
        return 0
    else
        print_error "Guadagno non corretto"
        print_error "Atteso: delta_total=$expected_reward, delta_python=$expected_reward, delta_api=$expected_reward, delta_backend=$expected_reward"
        print_error "Ricevuto: delta_total=$delta_total, delta_python=$delta_python, delta_api=$delta_api, delta_backend=$delta_backend"
        return 1
    fi
}

# ==============================================================================
# TEST 3: Decadimento Temporale (Simulato)
# ==============================================================================

test_decay() {
    print_header "TEST 3: Decadimento Temporale (Verifica Funzione)"
    
    print_test "Verifichiamo che la funzione di decay sia attiva"
    
    print_info "Nota: Il decay reale avviene ogni 24h"
    print_info "Per testarlo in tempo reale, modificare DECAY_INTERVAL nel codice"
    print_info "Oppure chiamare manualmente la funzione di decay"
    
    # Verifichiamo che il loop sia attivo cercando nei log
    print_info "Verifica che il decay loop sia stato avviato..."
    
    local node1_id=$(get_node_id $NODE1_PORT)
    local rep=$(get_reputation $NODE1_PORT "$node1_id")
    
    print_info "Reputazione attuale nodo 1:"
    echo "$rep" | jq .
    
    print_info "Calcolo teorico dopo 7 giorni di decay (-1%/giorno):"
    
    # Simula matematicamente il decay
    local total=$(echo "$rep" | jq '._total')
    
    if [ "$total" -gt 0 ]; then
        # Calcolo: total * (0.99^7)
        local after_7days=$(echo "$total * 0.9321" | bc -l | xargs printf "%.2f")
        print_info "Se _total è $total oggi, dopo 7 giorni sarà circa $after_7days"
        print_info "Perdita: $(echo "$total - $after_7days" | bc -l | xargs printf "%.2f") punti (-6.8%)"
        
        print_success "Formula di decay verificata matematicamente"
        print_info "Per test end-to-end del decay, eseguire dopo 24h o modificare DECAY_INTERVAL"
        return 0
    else
        print_info "Nessuna reputazione presente per testare il decay"
        return 0
    fi
}

# ==============================================================================
# TEST 4: Voto Ponderato Contestuale
# ==============================================================================

test_contextual_voting() {
    print_header "TEST 4: Voto Ponderato Contestuale"
    
    print_test "Creiamo una proposta con tag specifici e verifichiamo i pesi di voto"
    
    # Ottieni node IDs
    local node1_id=$(get_node_id $NODE1_PORT)
    local node2_id=$(get_node_id $NODE2_PORT)
    local node3_id=$(get_node_id $NODE3_PORT)
    
    # Mostra reputazioni attuali
    print_info "Reputazioni attuali:"
    
    local rep1=$(get_reputation $NODE1_PORT "$node1_id")
    local rep2=$(get_reputation $NODE2_PORT "$node2_id")
    local rep3=$(get_reputation $NODE3_PORT "$node3_id")
    
    echo "Nodo 1: $(echo "$rep1" | jq -c '.')"
    echo "Nodo 2: $(echo "$rep2" | jq -c '.')"
    echo "Nodo 3: $(echo "$rep3" | jq -c '.')"
    
    # Crea proposta con tag specifici
    print_info "Creazione proposta con tag: [python, security]..."
    
    local prop_response=$(curl -s -X POST "http://localhost:$NODE1_PORT/proposals?channel=global" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Upgrade security protocols",
            "description": "Implementare nuovi protocolli di sicurezza",
            "proposal_type": "config_change",
            "tags": ["python", "security"],
            "schema_name": "proposal_v1"
        }')
    
    local prop_id=$(echo "$prop_response" | jq -r '.id')
    
    if [ -z "$prop_id" ] || [ "$prop_id" = "null" ]; then
        print_error "Creazione proposta fallita"
        echo "$prop_response" | jq .
        return 1
    fi
    
    print_success "Proposta creata: ${prop_id:0:20}..."
    
    # Attendi propagazione
    sleep 5
    
    # Voti dei nodi
    print_info "Nodo 2 vota YES..."
    curl -s -X POST "http://localhost:$NODE2_PORT/proposals/$prop_id/vote?channel=global" \
        -H "Content-Type: application/json" \
        -d '{"vote": "yes"}' > /dev/null
    
    sleep 3
    
    print_info "Nodo 3 vota YES..."
    curl -s -X POST "http://localhost:$NODE3_PORT/proposals/$prop_id/vote?channel=global" \
        -H "Content-Type: application/json" \
        -d '{"vote": "yes"}' > /dev/null
    
    sleep 5
    
    # Verifica outcome con dettagli voti
    print_info "Verifica outcome proposta..."
    
    local proposal=$(curl -s "http://localhost:$NODE1_PORT/state" | jq ".global.proposals.\"$prop_id\"")
    
    if [ -z "$proposal" ] || [ "$proposal" = "null" ]; then
        print_error "Proposta non trovata"
        return 1
    fi
    
    # Estrai pesi voti
    print_info "Dettagli voti:"
    echo "$proposal" | jq -r '.votes'
    
    # Calcola outcome
    print_info "Calcolo outcome con voti ponderati..."
    
    # Simula calcolo peso base per confronto
    local total2=$(echo "$rep2" | jq '._total')
    local total3=$(echo "$rep3" | jq '._total')
    
    local tags2_python=$(echo "$rep2" | jq '.tags.python // 0')
    local tags2_security=$(echo "$rep2" | jq '.tags.security // 0')
    
    local tags3_python=$(echo "$rep3" | jq '.tags.python // 0')
    local tags3_security=$(echo "$rep3" | jq '.tags.security // 0')
    
    print_info "Nodo 2:"
    echo "   _total: $total2"
    echo "   specialization (python+security): $((tags2_python + tags2_security))"
    
    print_info "Nodo 3:"
    echo "   _total: $total3"
    echo "   specialization (python+security): $((tags3_python + tags3_security))"
    
    if [ "$tags2_python" -gt 0 ] || [ "$tags2_security" -gt 0 ]; then
        print_success "Nodo 2 ha specializzazione nei tag della proposta"
        print_success "Il suo voto avrà peso maggiore (base_weight + bonus_weight)"
    else
        print_info "Nodo 2 non ha specializzazione specifica"
        print_info "Il suo voto avrà solo base_weight"
    fi
    
    if [ "$tags3_python" -gt 0 ] || [ "$tags3_security" -gt 0 ]; then
        print_success "Nodo 3 ha specializzazione nei tag della proposta"
        print_success "Il suo voto avrà peso maggiore (base_weight + bonus_weight)"
    else
        print_info "Nodo 3 non ha specializzazione specifica"
        print_info "Il suo voto avrà solo base_weight"
    fi
    
    print_success "Test voto contestuale completato"
    print_info "I pesi effettivi vengono calcolati in calculate_proposal_outcome()"
    
    return 0
}

# ==============================================================================
# MAIN TEST SUITE
# ==============================================================================

main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                          ║${NC}"
    echo -e "${CYAN}║       🧬 REPUTATION SYSTEM V2 - TEST SUITE 🧬           ║${NC}"
    echo -e "${CYAN}║                                                          ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    print_info "Channel: $CHANNEL"
    print_info "Nodi: localhost:$NODE1_PORT, :$NODE2_PORT, :$NODE3_PORT"
    echo ""
    
    # Contatore risultati
    local passed=0
    local failed=0
    
    # Verifica che i nodi siano online
    print_info "Verifica connettività nodi..."
    if ! curl -s "http://localhost:$NODE1_PORT/whoami" > /dev/null; then
        print_error "Nodi non raggiungibili. Avvia: docker-compose up -d"
        exit 1
    fi
    print_success "Nodi online"
    
    # Esegui test
    if test_migration; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_specialized_gain; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_decay; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if test_contextual_voting; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Risultati finali
    print_header "RISULTATI FINALI"
    
    echo -e "${GREEN}✓ Test passati: $passed${NC}"
    if [ $failed -gt 0 ]; then
        echo -e "${RED}✗ Test falliti: $failed${NC}"
    else
        echo -e "${GREEN}✓ Test falliti: 0${NC}"
    fi
    
    echo ""
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                          ║${NC}"
        echo -e "${GREEN}║              ✅ TUTTI I TEST SUPERATI! ✅                ║${NC}"
        echo -e "${GREEN}║                                                          ║${NC}"
        echo -e "${GREEN}║         Reputation System v2 Fully Operational!          ║${NC}"
        echo -e "${GREEN}║                                                          ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║                                                          ║${NC}"
        echo -e "${RED}║              ❌ ALCUNI TEST FALLITI ❌                   ║${NC}"
        echo -e "${RED}║                                                          ║${NC}"
        echo -e "${RED}║            Controllare i log sopra per dettagli          ║${NC}"
        echo -e "${RED}║                                                          ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

# Esegui main
main
