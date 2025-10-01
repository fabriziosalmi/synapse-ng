#!/bin/bash

# Suite di Test Definitiva per Synapse-NG
# Questo script è stato riscritto per essere più robusto e diretto.

# Ferma l'esecuzione in caso di errore
set -e

# --- Funzioni Helper ---

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }
assert_equals() { [ "$2" == "$1" ] && echo -e "\e[32m✓ SUCCESS\e[0m: $3" || { echo -e "\e[31m✗ FAILURE\e[0m: $3 - Atteso: $1, Ricevuto: $2"; exit 1; }; }

# Funzione di polling robusta
wait_for_node_count() {
    local port=$1
    local expected_count=$2
    local timeout=60
    local interval=5
    local elapsed=0
    echo -n "In attesa che il nodo su porta $port veda $expected_count nodi... "
    while [ $elapsed -lt $timeout ]; do
        # Assegna 0 se il comando curl/jq fallisce o restituisce null
        local count=$(curl -s "http://localhost:$port/state" | jq '.global.nodes | length')
        count=${count:-0}

        if [ "$count" -eq "$expected_count" ]; then
            echo -e "\e[32mOK\e[0m"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    echo -e "\e[31mTIMEOUT\e[0m"
    echo "DEBUG: Ultimo conteggio nodi ricevuto: ${count:-'nessuno'}"
    echo "DEBUG: Ultimo stato ricevuto da $port:"
    curl -s "http://localhost:$port/state" | jq .
    exit 1
}

# --- Scenari di Test ---

run_all_tests() {
    print_header "AVVIO SUITE DI TEST DEFINITIVA"
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans

    # 1. AVVIO A FREDDO
    print_header "SCENARIO 1: AVVIO A FREDDO (3 NODI)"
    docker-compose up --build -d rendezvous node-1 node-2 node-3
    wait_for_node_count 8001 3
    assert_equals 3 "$(curl -s http://localhost:8002/state | jq '.global.nodes | length')" "Nodo 2 vede 3 nodi"
    assert_equals 3 "$(curl -s http://localhost:8003/state | jq '.global.nodes | length')" "Nodo 3 vede 3 nodi"

    # 2. INGRESSO NUOVO NODO
    print_header "SCENARIO 2: INGRESSO NUOVO NODO"
    docker-compose up -d --no-recreate node-4
    wait_for_node_count 8001 4
    assert_equals 4 "$(curl -s http://localhost:8004/state | jq '.global.nodes | length')" "Il nuovo nodo 4 vede 4 nodi"

    # 3. LIFECYCLE TASK
    print_header "SCENARIO 3: LIFECYCLE TASK"
    echo "Creo un task..."
    TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" -H "Content-Type: application/json" -d '{"title":"Fix a bug"}' | jq -r '.id')
    assert_equals "string" "$( [ -n "$TASK_ID" ] && echo "string")" "Task creato con successo con un ID."
    
    echo "Attendo la propagazione del task..."
    sleep 10

    TASK_STATUS_ON_2=$(curl -s http://localhost:8002/state | jq -r --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid].status')
    assert_equals "open" "$TASK_STATUS_ON_2" "Nodo 2 vede il nuovo task come 'open'"

    echo "Eseguo il claim del task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=sviluppo_ui" -d '' > /dev/null
    sleep 10

    TASK_STATUS_ON_1=$(curl -s http://localhost:8001/state | jq -r --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid].status')
    assert_equals "claimed" "$TASK_STATUS_ON_1" "Nodo 1 vede il task come 'claimed'"

    print_header "TUTTI I TEST COMPLETATI CON SUCCESSO"
    echo "Pulizia finale..."
    docker-compose down -v --remove-orphans
}

# Esegui la suite
run_all_tests
