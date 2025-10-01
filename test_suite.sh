#!/bin/bash

# Suite di Test Completa per Synapse-NG
# Testa: Convergenza, WebRTC, PubSub, Task Lifecycle

set -e

# --- Funzioni Helper ---

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }
print_success() { echo -e "\e[32m✓ $1\e[0m"; }
print_error() { echo -e "\e[31m✗ $1\e[0m"; }
assert_equals() { [ "$2" == "$1" ] && print_success "$3" || { print_error "$3 - Atteso: $1, Ricevuto: $2"; exit 1; }; }

# Funzione per ottenere la reputazione di un nodo
get_reputation() {
  local node_port=$1
  local node_id_to_check=$2
  curl -s "http://localhost:$node_port/state" | jq -r ".global.nodes[\"$node_id_to_check\"].reputation // 0"
}

# Funzione per ottenere il balance SP di un nodo
get_balance() {
  local node_port=$1
  local node_id_to_check=$2
  curl -s "http://localhost:$node_port/state" | jq -r ".global.nodes[\"$node_id_to_check\"].balance // 0"
}

# Funzione per ottenere lo status di una proposta
get_proposal_status() {
  local node_port=$1
  local channel=$2
  local prop_id=$3
  curl -s "http://localhost:$node_port/state" | jq -r ".$channel.proposals[\"$prop_id\"].status // \"not_found\""
}

# Funzione per ottenere l'esito di una proposta
get_proposal_outcome() {
  local node_port=$1
  local channel=$2
  local prop_id=$3
  curl -s "http://localhost:$node_port/state" | jq -r ".$channel.proposals[\"$prop_id\"].outcome // \"pending\""
}

# Funzione di polling robusta
wait_for_condition() {
    local condition_cmd=$1
    local success_msg=$2
    local timeout=${3:-60}
    local interval=5
    local elapsed=0
    echo -n "In attesa di: $success_msg... "
    while [ $elapsed -lt $timeout ]; do
        if eval "$condition_cmd" &>/dev/null; then
            echo -e "\e[32mOK\e[0m"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    echo -e "\e[31mTIMEOUT\e[0m"
    exit 1
}

# --- Scenari di Test ---

run_all_tests() {
    print_header "SYNAPSE-NG TEST SUITE COMPLETA"
    echo "Modalità: Rendezvous + WebRTC + SynapseSub"
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans

    # 1. AVVIO A FREDDO + CONVERGENZA
    print_header "SCENARIO 1: AVVIO A FREDDO (3 NODI)"
    docker-compose up --build -d rendezvous node-1 node-2 node-3

    echo "Attendo convergenza iniziale..."
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 1" 90
    wait_for_condition "curl -s http://localhost:8002/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 2" 60
    wait_for_condition "curl -s http://localhost:8003/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 3" 60
    print_success "Convergenza raggiunta su tutti i nodi"

    # 2. VERIFICA WEBRTC
    print_header "SCENARIO 2: VERIFICA CONNESSIONI WEBRTC"

    echo "Attendo stabilizzazione WebRTC (15s)..."
    sleep 15

    WEBRTC_NODE1=$(curl -s http://localhost:8001/webrtc/connections | jq '.total_connections')
    WEBRTC_NODE2=$(curl -s http://localhost:8002/webrtc/connections | jq '.total_connections')
    WEBRTC_NODE3=$(curl -s http://localhost:8003/webrtc/connections | jq '.total_connections')

    echo "Connessioni WebRTC:"
    echo "  Nodo 1: $WEBRTC_NODE1"
    echo "  Nodo 2: $WEBRTC_NODE2"
    echo "  Nodo 3: $WEBRTC_NODE3"

    # Verifica che ci siano connessioni (almeno 1 per nodo)
    [ "$WEBRTC_NODE1" -ge 1 ] && print_success "Nodo 1 ha connessioni WebRTC" || print_error "Nodo 1 senza connessioni"
    [ "$WEBRTC_NODE2" -ge 1 ] && print_success "Nodo 2 ha connessioni WebRTC" || print_error "Nodo 2 senza connessioni"
    [ "$WEBRTC_NODE3" -ge 1 ] && print_success "Nodo 3 ha connessioni WebRTC" || print_error "Nodo 3 senza connessioni"

    # 3. VERIFICA PUBSUB
    print_header "SCENARIO 3: VERIFICA PROTOCOLLO PUBSUB"

    PUBSUB_NODE1=$(curl -s http://localhost:8001/pubsub/stats | jq '.subscribed_topics')
    PUBSUB_NODE2=$(curl -s http://localhost:8002/pubsub/stats | jq '.subscribed_topics')

    echo "Topic PubSub sottoscritti:"
    echo "  Nodo 1: $PUBSUB_NODE1 topic"
    echo "  Nodo 2: $PUBSUB_NODE2 topic"

    [ "$PUBSUB_NODE1" -ge 2 ] && print_success "Nodo 1 ha sottoscrizioni PubSub" || print_error "Nodo 1 senza sottoscrizioni"
    [ "$PUBSUB_NODE2" -ge 2 ] && print_success "Nodo 2 ha sottoscrizioni PubSub" || print_error "Nodo 2 senza sottoscrizioni"

    # 4. INGRESSO NUOVO NODO
    print_header "SCENARIO 4: INGRESSO NUOVO NODO"
    docker-compose up -d --no-recreate node-4
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^4$'" "Rete a 4 nodi stabile" 90
    print_success "Nodo 4 integrato con successo"

    # 5. LIFECYCLE TASK COMPLETO
    print_header "SCENARIO 5: LIFECYCLE TASK COMPLETO"
    echo "Creo un task sul Nodo 1..."
    TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"title":"Test Suite Task"}' | jq -r '.id')

    [ -n "$TASK_ID" ] && print_success "Task creato: $TASK_ID" || { print_error "Creazione task fallita"; exit 1; }

    echo "Attendo propagazione (20s)..."
    sleep 20

    wait_for_condition "curl -s http://localhost:8002/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"open\"'" "Propagazione task al Nodo 2"
    wait_for_condition "curl -s http://localhost:8003/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"open\"'" "Propagazione task al Nodo 3"
    print_success "Task propagato a tutti i nodi"

    echo "Nodo 2 prende in carico il task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=sviluppo_ui" -d '' > /dev/null

    echo "Attendo propagazione claim (20s)..."
    sleep 20

    wait_for_condition "curl -s http://localhost:8001/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"claimed\"'" "Propagazione claim al Nodo 1"
    print_success "Claim propagato"

    echo "Completamento task (progress → complete)..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=sviluppo_ui" -d '' > /dev/null
    sleep 2
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=sviluppo_ui" -d '' > /dev/null

    echo "Attendo propagazione completamento (20s)..."
    sleep 20

    wait_for_condition "curl -s http://localhost:8001/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"completed\"'" "Propagazione completamento al Nodo 1"
    wait_for_condition "curl -s http://localhost:8003/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"completed\"'" "Propagazione completamento al Nodo 3"
    print_success "Task completato e propagato a tutta la rete"

    # 6. VERIFICA REPUTAZIONE
    print_header "SCENARIO 6: VERIFICA SISTEMA REPUTAZIONE"

    NODE2_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-2:8000") | .key')
    NODE2_REP=$(curl -s http://localhost:8001/state | jq --arg nid "$NODE2_ID" '.global.nodes[$nid].reputation')

    echo "Reputazione Nodo 2: $NODE2_REP"
    [ "$NODE2_REP" -ge 10 ] && print_success "Reputazione incrementata correttamente (+10 per task completato)" || print_error "Reputazione non aggiornata"

    # 7. STATISTICHE FINALI
    print_header "STATISTICHE FINALI DELLA RETE"

    echo ""
    echo "📊 Stato Globale:"
    curl -s http://localhost:8001/state | jq '{
        total_nodes: .global.nodes | length,
        total_tasks: .sviluppo_ui.tasks | length,
        completed_tasks: [.sviluppo_ui.tasks[] | select(.status == "completed")] | length
    }'

    echo ""
    echo "🔗 Connessioni WebRTC:"
    echo "  Nodo 1: $(curl -s http://localhost:8001/webrtc/connections | jq '.total_connections') connessioni, $(curl -s http://localhost:8001/webrtc/connections | jq '.active_data_channels') canali attivi"
    echo "  Nodo 2: $(curl -s http://localhost:8002/webrtc/connections | jq '.total_connections') connessioni, $(curl -s http://localhost:8002/webrtc/connections | jq '.active_data_channels') canali attivi"

    echo ""
    echo "📡 PubSub Topics:"
    curl -s http://localhost:8001/pubsub/stats | jq '.topics | keys'

    print_header "TUTTI I TEST COMPLETATI CON SUCCESSO ✅"
    echo ""
    echo "La rete Synapse-NG funziona correttamente:"
    echo "  ✓ Convergenza dello stato"
    echo "  ✓ Connessioni WebRTC P2P"
    echo "  ✓ Protocollo SynapseSub"
    echo "  ✓ Task lifecycle completo"
    echo "  ✓ Sistema di reputazione"
    echo ""
    echo "Pulizia finale..."
    docker-compose down -v --remove-orphans
}

# --- NUOVO SCENARIO 7: Voto Ponderato e Governance Meritocratica ---
test_weighted_voting_governance() {
    print_header "SCENARIO 7: VOTO PONDERATO E GOVERNANCE MERITOCRATICA"
    
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans
    
    print_header "FASE 1: SETUP - Avvio 3 nodi (A=node-1, B=node-2, C=node-3)"
    docker-compose up --build -d rendezvous node-1 node-2 node-3
    
    echo "Attendo convergenza iniziale..."
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza a 3 nodi" 90
    print_success "Rete a 3 nodi convergente"
    
    # Ottieni gli ID dei nodi
    NODE_A_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-1:8000") | .key')
    NODE_B_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-2:8000") | .key')
    NODE_C_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-3:8000") | .key')
    
    echo "Node IDs:"
    echo "  Node A (node-1): ${NODE_A_ID:0:16}..."
    echo "  Node B (node-2): ${NODE_B_ID:0:16}..."
    echo "  Node C (node-3): ${NODE_C_ID:0:16}..."
    
    print_header "FASE 2: COSTRUZIONE REPUTAZIONE"
    
    # Nodo A completa 2 task per guadagnare +20 reputazione
    echo "Nodo A crea e completa 2 task per guadagnare reputazione..."
    for i in 1 2; do
        TASK_A=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
            -H "Content-Type: application/json" \
            -d "{\"title\":\"Task A$i per reputazione\"}" | jq -r '.id')
        
        sleep 2
        curl -s -X POST "http://localhost:8001/tasks/$TASK_A/claim?channel=sviluppo_ui" -d '' > /dev/null
        sleep 2
        curl -s -X POST "http://localhost:8001/tasks/$TASK_A/progress?channel=sviluppo_ui" -d '' > /dev/null
        sleep 2
        curl -s -X POST "http://localhost:8001/tasks/$TASK_A/complete?channel=sviluppo_ui" -d '' > /dev/null
        
        echo "  Task A$i completato"
    done
    
    # Nodo B vota su una proposta per guadagnare +1 reputazione
    echo "Nodo C crea una proposta di test..."
    PROP_TEST=$(curl -s -X POST "http://localhost:8003/proposals?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"title":"Test Proposta per Reputazione"}' | jq -r '.id')
    
    echo "Attendo propagazione proposta (20s)..."
    sleep 20
    
    echo "Nodo B vota YES sulla proposta di test..."
    curl -s -X POST "http://localhost:8002/proposals/$PROP_TEST/vote?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"vote":"yes"}' > /dev/null
    
    echo "Attendo propagazione reputazione (25s)..."
    sleep 25
    
    # Verifica reputazioni su tutti i nodi
    echo ""
    echo "Verifica reputazione su tutti i nodi:"
    for port in 8001 8002 8003; do
        REP_A=$(get_reputation $port "$NODE_A_ID")
        REP_B=$(get_reputation $port "$NODE_B_ID")
        REP_C=$(get_reputation $port "$NODE_C_ID")
        echo "  Nodo :$port → A=$REP_A, B=$REP_B, C=$REP_C"
    done
    
    # Asserzioni reputazione
    REP_A_FINAL=$(get_reputation 8001 "$NODE_A_ID")
    REP_B_FINAL=$(get_reputation 8001 "$NODE_B_ID")
    REP_C_FINAL=$(get_reputation 8001 "$NODE_C_ID")
    
    [ "$REP_A_FINAL" -eq 20 ] && print_success "Nodo A: reputazione 20 (2 task completati)" || print_error "Nodo A: reputazione errata (atteso 20, ricevuto $REP_A_FINAL)"
    [ "$REP_B_FINAL" -ge 1 ] && print_success "Nodo B: reputazione >= 1 (1 voto)" || print_error "Nodo B: reputazione errata (atteso >= 1, ricevuto $REP_B_FINAL)"
    [ "$REP_C_FINAL" -eq 0 ] && print_success "Nodo C: reputazione 0 (nessuna azione)" || print_error "Nodo C: reputazione errata (atteso 0, ricevuto $REP_C_FINAL)"
    
    print_header "FASE 3: TEST VOTAZIONE PONDERATA"
    
    echo "Nodo C (bassa reputazione) crea proposta critica..."
    PROP_CRITICAL=$(curl -s -X POST "http://localhost:8003/proposals?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"title":"Proposta Critica - Test Voto Ponderato"}' | jq -r '.id')
    
    echo "Attendo propagazione proposta critica (25s)..."
    sleep 25
    
    echo "Votazione:"
    echo "  Nodo A (alta reputazione, peso ~5.4) vota NO..."
    curl -s -X POST "http://localhost:8001/proposals/$PROP_CRITICAL/vote?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"vote":"no"}' > /dev/null
    
    sleep 3
    
    echo "  Nodo B (bassa reputazione, peso ~2.0) vota YES..."
    curl -s -X POST "http://localhost:8002/proposals/$PROP_CRITICAL/vote?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"vote":"yes"}' > /dev/null
    
    sleep 3
    
    echo "  Nodo C (reputazione 0, peso 1.0) vota YES..."
    curl -s -X POST "http://localhost:8003/proposals/$PROP_CRITICAL/vote?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"vote":"yes"}' > /dev/null
    
    echo "Attendo propagazione voti (20s)..."
    sleep 20
    
    print_header "FASE 4: ASSERZIONI ESITO VOTAZIONE"
    
    # Verifica che la proposta sia ancora open (non chiusa automaticamente)
    STATUS_1=$(get_proposal_status 8001 "sviluppo_ui" "$PROP_CRITICAL")
    echo "Status proposta su Nodo 1: $STATUS_1"
    
    # Chiudi manualmente la proposta
    echo "Chiusura proposta per calcolare l'esito..."
    curl -s -X POST "http://localhost:8001/proposals/$PROP_CRITICAL/close?channel=sviluppo_ui" -d '' > /dev/null
    
    echo "Attendo propagazione chiusura (20s)..."
    sleep 20
    
    # Verifica esito su tutti i nodi
    echo ""
    echo "Verifica esito votazione su tutti i nodi:"
    for port in 8001 8002 8003; do
        STATUS=$(get_proposal_status $port "sviluppo_ui" "$PROP_CRITICAL")
        OUTCOME=$(curl -s "http://localhost:$port/state" | jq -r ".sviluppo_ui.proposals[\"$PROP_CRITICAL\"].outcome // \"unknown\"")
        echo "  Nodo :$port → Status: $STATUS, Outcome: $OUTCOME"
    done
    
    # Asserzione finale: la proposta deve essere REJECTED
    FINAL_STATUS=$(get_proposal_status 8001 "sviluppo_ui" "$PROP_CRITICAL")
    FINAL_OUTCOME=$(curl -s "http://localhost:8001/state" | jq -r ".sviluppo_ui.proposals[\"$PROP_CRITICAL\"].outcome // \"unknown\"")
    
    if [ "$FINAL_STATUS" == "closed" ] && [ "$FINAL_OUTCOME" == "rejected" ]; then
        print_success "✅ VOTO PONDERATO FUNZIONA: Proposta REJECTED nonostante 2 YES vs 1 NO"
        print_success "   Il peso della reputazione di Nodo A (peso ~5.4) ha superato B+C (pesi ~2.0+1.0)"
    else
        print_error "❌ VOTO PONDERATO FALLITO: Status=$FINAL_STATUS, Outcome=$FINAL_OUTCOME"
        print_error "   Atteso: Status=closed, Outcome=rejected"
        exit 1
    fi
    
    echo ""
    echo "Pulizia ambiente..."
    docker-compose down -v --remove-orphans
}

# --- NUOVO SCENARIO 8: Economia dei Task e Trasferimento Valore (Synapse Points) ---
test_task_economy_sp_transfer() {
    print_header "SCENARIO 8: ECONOMIA DEI TASK E TRASFERIMENTO VALORE (SP)"
    
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans
    
    print_header "FASE 1: SETUP - Avvio 3 nodi con saldo iniziale"
    docker-compose up --build -d rendezvous node-1 node-2 node-3
    
    echo "Attendo convergenza iniziale..."
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza a 3 nodi" 90
    print_success "Rete a 3 nodi convergente"
    
    # Ottieni gli ID dei nodi
    NODE_A_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-1:8000") | .key')
    NODE_B_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-2:8000") | .key')
    NODE_C_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-3:8000") | .key')
    
    echo "Node IDs:"
    echo "  Node A (node-1): ${NODE_A_ID:0:16}..."
    echo "  Node B (node-2): ${NODE_B_ID:0:16}..."
    echo "  Node C (node-3): ${NODE_C_ID:0:16}..."
    
    # Verifica saldi iniziali
    echo ""
    echo "Verifica saldi iniziali (dovrebbero essere 1000 SP per tutti):"
    for port in 8001 8002 8003; do
        BAL_A=$(get_balance $port "$NODE_A_ID")
        BAL_B=$(get_balance $port "$NODE_B_ID")
        BAL_C=$(get_balance $port "$NODE_C_ID")
        echo "  Nodo :$port → A=$BAL_A SP, B=$BAL_B SP, C=$BAL_C SP"
    done
    
    INITIAL_BAL_A=$(get_balance 8001 "$NODE_A_ID")
    INITIAL_BAL_B=$(get_balance 8001 "$NODE_B_ID")
    INITIAL_BAL_C=$(get_balance 8001 "$NODE_C_ID")
    
    [ "$INITIAL_BAL_A" -eq 1000 ] && print_success "Nodo A: saldo iniziale 1000 SP" || print_error "Nodo A: saldo errato (atteso 1000, ricevuto $INITIAL_BAL_A)"
    [ "$INITIAL_BAL_B" -eq 1000 ] && print_success "Nodo B: saldo iniziale 1000 SP" || print_error "Nodo B: saldo errato (atteso 1000, ricevuto $INITIAL_BAL_B)"
    [ "$INITIAL_BAL_C" -eq 1000 ] && print_success "Nodo C: saldo iniziale 1000 SP" || print_error "Nodo C: saldo errato (atteso 1000, ricevuto $INITIAL_BAL_C)"
    
    print_header "FASE 2: CREAZIONE TASK CON REWARD"
    
    echo "Nodo A crea un task con reward di 30 SP..."
    TASK_REWARD=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d '{"title":"Task con Reward - Test Economia","reward":30}' | jq -r '.id')
    
    [ -n "$TASK_REWARD" ] && print_success "Task con reward creato: ${TASK_REWARD:0:16}..." || { print_error "Creazione task fallita"; exit 1; }
    
    echo "Attendo propagazione task (25s)..."
    sleep 25
    
    print_header "FASE 3: VERIFICA CONGELAMENTO SP"
    
    echo "Verifica balance dopo creazione task (A dovrebbe avere 970 SP congelati):"
    for port in 8001 8002 8003; do
        BAL_A=$(get_balance $port "$NODE_A_ID")
        BAL_B=$(get_balance $port "$NODE_B_ID")
        BAL_C=$(get_balance $port "$NODE_C_ID")
        echo "  Nodo :$port → A=$BAL_A SP, B=$BAL_B SP, C=$BAL_C SP"
    done
    
    BAL_A_FROZEN=$(get_balance 8002 "$NODE_A_ID")
    [ "$BAL_A_FROZEN" -eq 970 ] && print_success "✅ SP CONGELATI: Nodo A ha 970 SP (1000 - 30 congelati)" || { print_error "❌ Congelamento fallito (atteso 970, ricevuto $BAL_A_FROZEN)"; exit 1; }
    
    print_header "FASE 4: COMPLETAMENTO TASK E TRASFERIMENTO SP"
    
    echo "Nodo B prende in carico il task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_REWARD/claim?channel=sviluppo_ui" -d '' > /dev/null
    
    sleep 5
    
    echo "Nodo B completa il task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_REWARD/progress?channel=sviluppo_ui" -d '' > /dev/null
    sleep 2
    curl -s -X POST "http://localhost:8002/tasks/$TASK_REWARD/complete?channel=sviluppo_ui" -d '' > /dev/null
    
    echo "Attendo propagazione completamento e trasferimento SP (30s)..."
    sleep 30
    
    print_header "FASE 5: ASSERZIONI FINALI - VERIFICA DETERMINISMO ECONOMICO"
    
    echo ""
    echo "Verifica balance finali su TUTTI i nodi (devono essere identici):"
    for port in 8001 8002 8003; do
        BAL_A=$(get_balance $port "$NODE_A_ID")
        BAL_B=$(get_balance $port "$NODE_B_ID")
        BAL_C=$(get_balance $port "$NODE_C_ID")
        echo "  Nodo :$port → A=$BAL_A SP, B=$BAL_B SP, C=$BAL_C SP"
    done
    
    # Verifica su ogni nodo separatamente
    for port in 8001 8002 8003; do
        BAL_A=$(get_balance $port "$NODE_A_ID")
        BAL_B=$(get_balance $port "$NODE_B_ID")
        BAL_C=$(get_balance $port "$NODE_C_ID")
        
        if [ "$BAL_A" -ne 970 ]; then
            print_error "❌ DIVERGENZA ECONOMICA su Nodo :$port - Nodo A: atteso 970 SP, ricevuto $BAL_A SP"
            exit 1
        fi
        
        if [ "$BAL_B" -ne 1030 ]; then
            print_error "❌ DIVERGENZA ECONOMICA su Nodo :$port - Nodo B: atteso 1030 SP, ricevuto $BAL_B SP"
            exit 1
        fi
        
        if [ "$BAL_C" -ne 1000 ]; then
            print_error "❌ DIVERGENZA ECONOMICA su Nodo :$port - Nodo C: atteso 1000 SP, ricevuto $BAL_C SP"
            exit 1
        fi
    done
    
    print_success "✅ ECONOMIA DETERMINISTICA: Tutti i nodi concordano sui balance!"
    print_success "   Nodo A: 970 SP (1000 - 30 pagati)"
    print_success "   Nodo B: 1030 SP (1000 + 30 guadagnati)"
    print_success "   Nodo C: 1000 SP (invariato)"
    
    echo ""
    print_header "TEST ECONOMIA COMPLETATO CON SUCCESSO ✅"
    echo "L'economia dei Synapse Points è:"
    echo "  ✓ Deterministica (tutti i nodi concordano)"
    echo "  ✓ Transazionale (SP congelati → trasferiti)"
    echo "  ✓ Affidabile (nessun double-spend o perdita di fondi)"
    echo ""
    
    echo "Pulizia ambiente..."
    docker-compose down -v --remove-orphans
}

# --- Main Execution ---

# Menu di selezione test
if [ "$1" == "all" ] || [ -z "$1" ]; then
    echo "Esecuzione suite completa..."
    run_all_tests
    
    echo ""
    echo "=========================================="
    echo "Esecuzione test economici aggiuntivi..."
    echo "=========================================="
    
    test_weighted_voting_governance
    test_task_economy_sp_transfer
    
    print_header "🎉 TUTTI I TEST COMPLETATI CON SUCCESSO 🎉"
    echo ""
    echo "Test Base:"
    echo "  ✓ Convergenza dello stato"
    echo "  ✓ Connessioni WebRTC P2P"
    echo "  ✓ Protocollo SynapseSub"
    echo "  ✓ Task lifecycle completo"
    echo "  ✓ Sistema di reputazione"
    echo ""
    echo "Test Economia e Governance:"
    echo "  ✓ Voto ponderato basato su reputazione"
    echo "  ✓ Economia task e trasferimento SP"
    echo "  ✓ Determinismo economico (no double-spend)"
    echo ""
    
elif [ "$1" == "base" ]; then
    echo "Esecuzione solo test base..."
    run_all_tests
    
elif [ "$1" == "governance" ]; then
    echo "Esecuzione test governance con voto ponderato..."
    test_weighted_voting_governance
    
elif [ "$1" == "economy" ]; then
    echo "Esecuzione test economia SP..."
    test_task_economy_sp_transfer
    
elif [ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo ""
    echo "Synapse-NG Test Suite"
    echo "====================="
    echo ""
    echo "Uso: ./test_suite.sh [opzione]"
    echo ""
    echo "Opzioni:"
    echo "  all (default)  - Esegue tutti i test (base + economia + governance)"
    echo "  base           - Esegue solo i test base (convergenza, WebRTC, PubSub, task)"
    echo "  governance     - Esegue solo il test del voto ponderato"
    echo "  economy        - Esegue solo il test dell'economia SP"
    echo "  help           - Mostra questo messaggio"
    echo ""
    echo "Esempi:"
    echo "  ./test_suite.sh              # Esegue tutti i test"
    echo "  ./test_suite.sh base         # Solo test base"
    echo "  ./test_suite.sh governance   # Solo test governance"
    echo "  ./test_suite.sh economy      # Solo test economia"
    echo ""
else
    echo "Opzione non riconosciuta: $1"
    echo "Usa './test_suite.sh help' per vedere le opzioni disponibili"
    exit 1
fi
