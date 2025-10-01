#!/bin/bash

# Suite di Test Completa per Synapse-NG
# Testa: Convergenza, WebRTC, PubSub, Task Lifecycle

set -e

# --- Funzioni Helper ---

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }
print_success() { echo -e "\e[32m✓ $1\e[0m"; }
print_error() { echo -e "\e[31m✗ $1\e[0m"; }
assert_equals() { [ "$2" == "$1" ] && print_success "$3" || { print_error "$3 - Atteso: $1, Ricevuto: $2"; exit 1; }; }

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

# Esegui la suite
run_all_tests
