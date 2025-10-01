#!/bin/bash

# Suite di Test Definitiva e Robusta per Synapse-NG

# Ferma l'esecuzione in caso di errore
set -e

# --- Funzioni Helper ---

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }
assert_equals() { [ "$2" == "$1" ] && echo -e "\e[32m✓ SUCCESS\e[0m: $3" || { echo -e "\e[31m✗ FAILURE\e[0m: $3 - Atteso: $1, Ricevuto: $2"; exit 1; }; }

# Funzione di polling robusta
wait_for_condition() {
    local condition_cmd=$1
    local success_msg=$2
    local timeout=${3:-60}
    local interval=5
    local elapsed=0
    echo -n "In attesa di: $success_msg... "
    while [ $elapsed -lt $timeout ]; do
        # Esegui il comando e controlla se ha successo (exit code 0)
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
    print_header "AVVIO SUITE DI TEST DEFINITIVA"
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans

    # 1. AVVIO A FREDDO
    print_header "SCENARIO 1: AVVIO A FREDDO (3 NODI)"
    docker-compose up --build -d rendezvous node-1 node-2 node-3
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 1"
    wait_for_condition "curl -s http://localhost:8002/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 2"
    wait_for_condition "curl -s http://localhost:8003/state | jq '.global.nodes | length' | grep -q '^3$'" "Convergenza Nodo 3"
    echo "Tutti i nodi hanno raggiunto la convergenza."

    # 2. INGRESSO NUOVO NODO
    print_header "SCENARIO 2: INGRESSO NUOVO NODO"
    docker-compose up -d --no-recreate node-4
    wait_for_condition "curl -s http://localhost:8001/state | jq '.global.nodes | length' | grep -q '^4$'" "Rete a 4 nodi stabile"

    # 3. LIFECYCLE TASK
    print_header "SCENARIO 3: LIFECYCLE TASK"
    echo "Creo un task..."
    TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" -H "Content-Type: application/json" -d '{"title":"Fix a bug"}' | jq -r '.id')
    assert_equals "string" "$( [ -n "$TASK_ID" ] && echo "string")" "Task creato con successo con un ID."
    
    echo "Attendo la propagazione del task (20s)..."
    sleep 20

    wait_for_condition "curl -s http://localhost:8002/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"open\"'" "Propagazione task al Nodo 2"

    echo "Eseguo il claim del task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=sviluppo_ui" -d '' > /dev/null
    
    echo "Attendo la propagazione del claim (20s)..."
    sleep 20

    wait_for_condition "curl -s http://localhost:8001/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"claimed\"'" "Propagazione claim al Nodo 1"

    echo "Completo il task..."
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=sviluppo_ui" -d '' > /dev/null
    sleep 1 # Piccola pausa tra stati
    curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=sviluppo_ui" -d '' > /dev/null

    wait_for_condition "curl -s http://localhost:8001/state | jq -e --arg tid \"$TASK_ID\" '.sviluppo_ui.tasks[$tid] | .status == \"completed\"'" "Propagazione completamento al Nodo 1"

    print_header "TUTTI I TEST COMPLETATI CON SUCCESSO"
    echo "Pulizia finale..."
    docker-compose down -v --remove-orphans
}

# Esegui la suite
run_all_tests