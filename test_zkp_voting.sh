#!/bin/bash

# test_zkp_voting.sh
# Script di test per il sistema di voto anonimo con Zero-Knowledge Proofs
#
# Questo script testa:
# 1. Generazione di proof ZKP valide
# 2. Voto anonimo con successo
# 3. Prevenzione doppi voti (nullifier system)
# 4. Conteggio corretto con mix di voti pubblici/anonimi
# 5. Verifica outcome ponderato per tier

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurazione
PORT1=8001
PORT2=8002
PORT3=8003
BASE_URL="http://localhost:$PORT1"
CHANNEL="test-zkp-governance"

# Contatori
TESTS_PASSED=0
TESTS_FAILED=0

# Funzioni di utilità
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funzione per chiamare API e verificare
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    fi
    
    # Separa body e status code
    body=$(echo "$response" | sed '$d')
    status=$(echo "$response" | tail -n1)
    
    if [ "$status" = "$expected_status" ]; then
        echo "$body"
        return 0
    else
        echo "ERROR: Expected status $expected_status, got $status"
        echo "Response: $body"
        return 1
    fi
}

# Verifica che i nodi siano in esecuzione
check_nodes() {
    print_header "Verifica Nodi in Esecuzione"
    
    for port in $PORT1 $PORT2 $PORT3; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "Nodo su porta $port è raggiungibile"
        else
            print_error "Nodo su porta $port NON raggiungibile"
            echo "Assicurati che i nodi siano in esecuzione (docker-compose up -d)"
            exit 1
        fi
    done
}

# Test 1: Creazione canale e proposta
test_create_proposal() {
    print_header "Test 1: Creazione Canale e Proposta"
    
    print_test "Creazione canale '$CHANNEL'..."
    result=$(api_call "POST" "/channels/create" "{\"channel_name\": \"$CHANNEL\"}" "200")
    if echo "$result" | grep -q "channel_name"; then
        print_success "Canale creato con successo"
    else
        print_error "Fallita creazione canale"
    fi
    
    sleep 1
    
    print_test "Creazione proposta di test..."
    proposal_data='{
        "title": "Test ZKP Voting System",
        "description": "Proposta per testare il sistema di voto anonimo con ZKP",
        "proposal_type": "parameter_change",
        "auto_close_hours": 24
    }'
    
    result=$(api_call "POST" "/proposals/create?channel=$CHANNEL" "$proposal_data" "200")
    PROPOSAL_ID=$(echo "$result" | jq -r '.proposal_id')
    
    if [ -n "$PROPOSAL_ID" ] && [ "$PROPOSAL_ID" != "null" ]; then
        print_success "Proposta creata: $PROPOSAL_ID"
    else
        print_error "Fallita creazione proposta"
        exit 1
    fi
}

# Test 2: Generazione proof ZKP
test_generate_proof() {
    print_header "Test 2: Generazione Proof ZKP"
    
    print_test "Richiesta generazione proof per proposta $PROPOSAL_ID..."
    result=$(api_call "GET" "/zkp/generate_proof?channel=$CHANNEL&proposal_id=$PROPOSAL_ID" "" "200")
    
    # Verifica presenza di tutti i campi richiesti
    tier=$(echo "$result" | jq -r '.tier')
    tier_weight=$(echo "$result" | jq -r '.tier_weight')
    proof=$(echo "$result" | jq -r '.proof')
    
    if [ -n "$tier" ] && [ "$tier" != "null" ]; then
        print_success "Tier rilevato: $tier (weight: $tier_weight)"
    else
        print_error "Tier non trovato nella risposta"
    fi
    
    # Salva la proof per test successivi
    echo "$result" | jq -c '.proof' > /tmp/zkp_proof.json
    
    # Verifica componenti della proof
    nullifier=$(echo "$proof" | jq -r '.nullifier')
    commitment=$(echo "$proof" | jq -r '.commitment')
    challenge=$(echo "$proof" | jq -r '.challenge')
    response=$(echo "$proof" | jq -r '.response')
    
    if [ -n "$nullifier" ] && [ "$nullifier" != "null" ]; then
        print_success "Proof generata con nullifier: ${nullifier:0:16}..."
    else
        print_error "Proof non contiene nullifier valido"
    fi
    
    if [ -n "$commitment" ] && [ -n "$challenge" ] && [ -n "$response" ]; then
        print_success "Proof contiene tutti i componenti crittografici"
    else
        print_error "Proof incompleta"
    fi
}

# Test 3: Voto anonimo con successo
test_anonymous_vote() {
    print_header "Test 3: Voto Anonimo con Successo"
    
    print_test "Invio voto anonimo YES con proof ZKP..."
    proof=$(cat /tmp/zkp_proof.json)
    vote_data=$(jq -n \
        --arg vote "yes" \
        --argjson proof "$proof" \
        '{vote: $vote, anonymous: true, zkp_proof: $proof}')
    
    result=$(api_call "POST" "/proposals/$PROPOSAL_ID/vote?channel=$CHANNEL" "$vote_data" "200")
    
    if echo "$result" | grep -q "Voto anonimo registrato"; then
        print_success "Voto anonimo registrato con successo"
        
        # Verifica dettagli della risposta
        tier=$(echo "$result" | jq -r '.tier')
        tier_weight=$(echo "$result" | jq -r '.tier_weight')
        print_info "Tier: $tier, Weight: $tier_weight"
    else
        print_error "Fallita registrazione voto anonimo"
    fi
}

# Test 4: Prevenzione doppio voto (nullifier)
test_double_vote_prevention() {
    print_header "Test 4: Prevenzione Doppio Voto (Nullifier)"
    
    print_test "Tentativo di votare di nuovo con la stessa proof..."
    
    # Rigenera la stessa proof (stesso nodo, stessa proposta → stesso nullifier)
    result=$(api_call "GET" "/zkp/generate_proof?channel=$CHANNEL&proposal_id=$PROPOSAL_ID" "" "200")
    proof=$(echo "$result" | jq -c '.proof')
    
    vote_data=$(jq -n \
        --arg vote "no" \
        --argjson proof "$proof" \
        '{vote: $vote, anonymous: true, zkp_proof: $proof}')
    
    # Questo dovrebbe FALLIRE (status 400)
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$vote_data" \
        "$BASE_URL/proposals/$PROPOSAL_ID/vote?channel=$CHANNEL")
    
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status" = "400" ] && echo "$body" | grep -q "Nullifier già usato"; then
        print_success "Doppio voto correttamente rifiutato (nullifier già usato)"
    else
        print_error "Il sistema non ha rifiutato il doppio voto! Status: $status"
        echo "Response: $body"
    fi
}

# Test 5: Voto tradizionale (non anonimo)
test_traditional_vote() {
    print_header "Test 5: Voto Tradizionale (Non Anonimo)"
    
    print_test "Creazione nuova proposta per voto tradizionale..."
    proposal_data='{
        "title": "Test Traditional Voting",
        "description": "Proposta per testare voto tradizionale",
        "proposal_type": "spending",
        "auto_close_hours": 24
    }'
    
    result=$(api_call "POST" "/proposals/create?channel=$CHANNEL" "$proposal_data" "200")
    PROPOSAL_ID_2=$(echo "$result" | jq -r '.proposal_id')
    
    print_test "Voto tradizionale (pubblico) su proposta $PROPOSAL_ID_2..."
    vote_data='{"vote": "yes", "anonymous": false}'
    
    result=$(api_call "POST" "/proposals/$PROPOSAL_ID_2/vote?channel=$CHANNEL" "$vote_data" "200")
    
    if echo "$result" | grep -q "Voto registrato"; then
        voter_id=$(echo "$result" | jq -r '.voter_id')
        print_success "Voto tradizionale registrato (voter_id visibile: ${voter_id:0:16}...)"
    else
        print_error "Fallita registrazione voto tradizionale"
    fi
}

# Test 6: Mix di voti pubblici e anonimi
test_mixed_voting() {
    print_header "Test 6: Mix di Voti Pubblici e Anonimi"
    
    print_test "Creazione proposta per test mix voti..."
    proposal_data='{
        "title": "Test Mixed Voting",
        "description": "Proposta per testare mix di voti pubblici e anonimi",
        "proposal_type": "governance",
        "auto_close_hours": 24
    }'
    
    result=$(api_call "POST" "/proposals/create?channel=$CHANNEL" "$proposal_data" "200")
    PROPOSAL_ID_3=$(echo "$result" | jq -r '.proposal_id')
    
    # Voto tradizionale YES
    print_test "Voto tradizionale YES..."
    vote_data='{"vote": "yes", "anonymous": false}'
    api_call "POST" "/proposals/$PROPOSAL_ID_3/vote?channel=$CHANNEL" "$vote_data" "200" > /dev/null
    
    # Voto anonimo YES (dal nodo 1, ma questo è già votato tradizionalmente)
    # Creiamo una nuova proposta per evitare conflitti
    print_test "Creazione proposta finale per test completo..."
    result=$(api_call "POST" "/proposals/create?channel=$CHANNEL" "$proposal_data" "200")
    PROPOSAL_ID_FINAL=$(echo "$result" | jq -r '.proposal_id')
    
    # Voto anonimo YES
    print_test "Voto anonimo YES su proposta finale..."
    result=$(api_call "GET" "/zkp/generate_proof?channel=$CHANNEL&proposal_id=$PROPOSAL_ID_FINAL" "" "200")
    proof=$(echo "$result" | jq -c '.proof')
    vote_data=$(jq -n \
        --arg vote "yes" \
        --argjson proof "$proof" \
        '{vote: $vote, anonymous: true, zkp_proof: $proof}')
    api_call "POST" "/proposals/$PROPOSAL_ID_FINAL/vote?channel=$CHANNEL" "$vote_data" "200" > /dev/null
    
    # Recupera la proposta e verifica il conteggio
    print_test "Verifica conteggio voti..."
    sleep 2  # Attendi replicazione
    
    result=$(api_call "GET" "/proposals/$PROPOSAL_ID_FINAL?channel=$CHANNEL" "" "200")
    
    # Verifica presenza di anonymous_votes
    anon_votes=$(echo "$result" | jq '.anonymous_votes // []')
    anon_count=$(echo "$anon_votes" | jq 'length')
    
    if [ "$anon_count" -gt 0 ]; then
        print_success "Proposta contiene $anon_count voto/i anonimo/i"
        
        # Mostra dettagli
        echo "$anon_votes" | jq -r '.[] | "  - Voto: \(.vote), Tier: \(.tier), Nullifier: \(.nullifier[:16])..."'
    else
        print_error "Nessun voto anonimo trovato nella proposta"
    fi
}

# Test 7: Verifica outcome ponderato
test_weighted_outcome() {
    print_header "Test 7: Verifica Outcome Ponderato"
    
    print_test "Creazione proposta per test outcome ponderato..."
    proposal_data='{
        "title": "Test Weighted Outcome",
        "description": "Proposta per testare il calcolo dell'\''outcome ponderato",
        "proposal_type": "parameter_change",
        "auto_close_hours": 0.001
    }'
    
    result=$(api_call "POST" "/proposals/create?channel=$CHANNEL" "$proposal_data" "200")
    PROPOSAL_ID_WEIGHTED=$(echo "$result" | jq -r '.proposal_id')
    
    # Vota con proof ZKP
    print_test "Voto anonimo YES con proof ZKP..."
    result=$(api_call "GET" "/zkp/generate_proof?channel=$CHANNEL&proposal_id=$PROPOSAL_ID_WEIGHTED" "" "200")
    proof=$(echo "$result" | jq -c '.proof')
    tier=$(echo "$result" | jq -r '.tier')
    tier_weight=$(echo "$result" | jq -r '.tier_weight')
    
    print_info "Tier del nodo corrente: $tier (weight: $tier_weight)"
    
    vote_data=$(jq -n \
        --arg vote "yes" \
        --argjson proof "$proof" \
        '{vote: $vote, anonymous: true, zkp_proof: $proof}')
    api_call "POST" "/proposals/$PROPOSAL_ID_WEIGHTED/vote?channel=$CHANNEL" "$vote_data" "200" > /dev/null
    
    # Attendi chiusura automatica
    print_test "Attendo chiusura automatica della proposta..."
    sleep 10
    
    # Recupera outcome
    result=$(api_call "GET" "/proposals/$PROPOSAL_ID_WEIGHTED?channel=$CHANNEL" "" "200")
    
    outcome=$(echo "$result" | jq -r '.outcome // "pending"')
    yes_weight=$(echo "$result" | jq -r '.yes_weight // 0')
    no_weight=$(echo "$result" | jq -r '.no_weight // 0')
    
    print_info "Outcome: $outcome (YES weight: $yes_weight, NO weight: $no_weight)"
    
    if [ "$outcome" = "approved" ] && [ "$yes_weight" != "0" ]; then
        print_success "Outcome ponderato calcolato correttamente"
    elif [ "$outcome" = "pending" ]; then
        print_error "Proposta ancora pending (forse non si è chiusa automaticamente)"
    else
        print_error "Outcome non corretto: $outcome"
    fi
}

# Test 8: Verifica anonymous_vote_summary
test_anonymous_summary() {
    print_header "Test 8: Verifica Anonymous Vote Summary"
    
    print_test "Recupero proposta con voto anonimo..."
    result=$(api_call "GET" "/proposals/$PROPOSAL_ID_FINAL?channel=$CHANNEL" "" "200")
    
    # Controlla se esiste anonymous_vote_summary
    summary=$(echo "$result" | jq '.anonymous_vote_summary // null')
    
    if [ "$summary" != "null" ]; then
        total=$(echo "$summary" | jq -r '.total')
        yes_count=$(echo "$summary" | jq -r '.yes_count')
        tier_breakdown=$(echo "$summary" | jq -r '.tier_breakdown')
        
        print_success "Anonymous vote summary presente"
        print_info "Total: $total, YES: $yes_count"
        echo "$tier_breakdown" | jq '.'
    else
        print_error "Anonymous vote summary non trovato"
    fi
}

# Test 9: Verifica struttura proposal completa
test_proposal_structure() {
    print_header "Test 9: Verifica Struttura Proposta Completa"
    
    print_test "Analisi struttura proposta con voti anonimi..."
    result=$(api_call "GET" "/proposals/$PROPOSAL_ID?channel=$CHANNEL" "" "200")
    
    # Verifica campi principali
    has_votes=$(echo "$result" | jq 'has("votes")')
    has_anonymous_votes=$(echo "$result" | jq 'has("anonymous_votes")')
    has_outcome=$(echo "$result" | jq 'has("outcome")')
    
    if [ "$has_votes" = "true" ]; then
        print_success "Campo 'votes' presente"
    else
        print_error "Campo 'votes' mancante"
    fi
    
    if [ "$has_anonymous_votes" = "true" ]; then
        print_success "Campo 'anonymous_votes' presente"
    else
        print_error "Campo 'anonymous_votes' mancante"
    fi
    
    if [ "$has_outcome" = "true" ]; then
        print_success "Campo 'outcome' presente"
    else
        print_error "Campo 'outcome' mancante"
    fi
}

# Cleanup
cleanup() {
    print_header "Cleanup"
    print_info "Rimuovendo file temporanei..."
    rm -f /tmp/zkp_proof.json
    print_success "Cleanup completato"
}

# Report finale
print_report() {
    print_header "REPORT FINALE"
    
    total_tests=$((TESTS_PASSED + TESTS_FAILED))
    
    echo -e "${GREEN}Test Passati: $TESTS_PASSED${NC}"
    echo -e "${RED}Test Falliti: $TESTS_FAILED${NC}"
    echo -e "Totale Test: $total_tests"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ TUTTI I TEST SONO PASSATI!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ ALCUNI TEST SONO FALLITI${NC}\n"
        exit 1
    fi
}

# Main execution
main() {
    print_header "Test Suite ZKP Voting System"
    echo "Data: $(date)"
    echo "Base URL: $BASE_URL"
    echo "Canale: $CHANNEL"
    
    check_nodes
    test_create_proposal
    test_generate_proof
    test_anonymous_vote
    test_double_vote_prevention
    test_traditional_vote
    test_mixed_voting
    test_weighted_outcome
    test_anonymous_summary
    test_proposal_structure
    
    cleanup
    print_report
}

# Trap per cleanup in caso di interruzione
trap cleanup EXIT

# Esegui test
main
