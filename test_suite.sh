#!/bin/bash

# Suite di test automatici potenziata per Synapse-NG

# Ferma l'esecuzione in caso di errore
set -e

# --- Funzioni Helper ---

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }
assert_equals() { [ "$2" == "$1" ] && echo -e "\e[32m✓ SUCCESS\e[0m: $3" || { echo -e "\e[31m✗ FAILURE\e[0m: $3 - Atteso: $1, Ricevuto: $2"; exit 1; }; }

# Helper per chiamate API
api_get() { curl -s "http://localhost:$1$2"; }
api_post() { curl -s -X POST "http://localhost:$1$2" -H "Content-Type: application/json" -d "$3"; }

# Funzioni di Polling (più robuste di sleep)
wait_for_condition() {
    local condition_cmd=$1
    local success_msg=$2
    local timeout=${3:-60} # Timeout di default 60s
    local interval=5
    local elapsed=0
    echo -n "In attesa di: $success_msg... "
    while [ $elapsed -lt $timeout ]; do
        if eval "$condition_cmd"; then
            echo -e "\e[32mOK\e[0m"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    echo -e "\e[31mTIMEOUT\e[0m"
    exit 1
}

# --- Funzioni di Test Specifiche (rese più robuste) ---

get_node_id() { local result=$(api_get $1 "/state" 2>/dev/null | jq -r --arg url \"http://node-$2:8000\" '.global.nodes[] | select(.url == $url) | .id' 2>/dev/null); echo "${result:-null}"; }
get_node_count() { local result=$(api_get $1 "/state" 2>/dev/null | jq '.global.nodes | length' 2>/dev/null); echo "${result:-0}"; }
get_task_status() { local result=$(api_get $1 "/state" 2>/dev/null | jq -r --arg ch "$2" --arg tid "$3" '.[$ch].tasks[$tid].status' 2>/dev/null); echo "${result:-null}"; }
get_reputation() { local result=$(api_get $1 "/state" 2>/dev/null | jq --arg nid "$2" '.global.nodes[$nid].reputation' 2>/dev/null); echo "${result:-0}"; }

# --- Scenari di Test ---

run_all_tests() {
    print_header "AVVIO SUITE DI TEST"
    echo "Pulizia ambiente Docker..."
    docker-compose down -v --remove-orphans

    # 1. AVVIO A FREDDO
    print_header "SCENARIO 1: AVVIO A FREDDO (3 NODI)"
    docker-compose up --build -d rendezvous node-1 node-2 node-3
    wait_for_condition "[ $(get_node_count 8001) -eq 3 ]" "Nodo 1 vede 3 nodi"
    assert_equals 3 "$(get_node_count 8002)" "Nodo 2 vede 3 nodi"
    assert_equals 3 "$(get_node_count 8003)" "Nodo 3 vede 3 nodi"

    # 2. INGRESSO NUOVO NODO
    print_header "SCENARIO 2: INGRESSO NUOVO NODO"
    docker-compose up -d --no-recreate node-4
    wait_for_condition "[ $(get_node_count 8001) -eq 4 ]" "Nodo 1 vede 4 nodi"
    assert_equals 4 "$(get_node_count 8004)" "Il nuovo nodo 4 vede 4 nodi"

    # 3. LIFECYCLE TASK E REPUTAZIONE
    print_header "SCENARIO 3: LIFECYCLE TASK E REPUTAZIONE"
    NODE2_ID=$(get_node_id 8001 2)
    local rep_initial=$(get_reputation 8001 "$NODE2_ID")
    assert_equals "0" "$rep_initial" "La reputazione iniziale del Nodo 2 è 0"

    local TASK_ID=$(api_post 8001 "/tasks?channel=sviluppo_ui&title=TestReputazione" | jq -r '.id')
    wait_for_condition "[ \"$(get_task_status 8002 sviluppo_ui $TASK_ID)\" == \"open\" ]" "Nodo 2 vede il nuovo task"
    
    api_post 8002 "/tasks/$TASK_ID/claim?channel=sviluppo_ui"
    wait_for_condition "[ \"$(get_task_status 8001 sviluppo_ui $TASK_ID)\" == \"claimed\" ]" "Nodo 1 vede il task come 'claimed'"

    api_post 8002 "/tasks/$TASK_ID/progress?channel=sviluppo_ui" && sleep 1
    api_post 8002 "/tasks/$TASK_ID/complete?channel=sviluppo_ui"
    wait_for_condition "[ \"$(get_task_status 8001 sviluppo_ui $TASK_ID)\" == \"completed\" ]" "Nodo 1 vede il task come 'completed'"

    local rep_after_task=$(get_reputation 8001 "$NODE2_ID")
    assert_equals "10" "$rep_after_task" "Reputazione del Nodo 2 è 10 dopo aver completato un task"

    # 4. GOVERNANCE E REPUTAZIONE
    print_header "SCENARIO 4: GOVERNANCE E REPUTAZIONE"
    local PROP_ID=$(api_post 8001 "/proposals?channel=global" '{"title":"Test Voto","description":"Votare incrementa la reputazione?"}' | jq -r '.id')
    wait_for_condition "[ $(api_get 8002 /state | jq --arg pid $PROP_ID '.global.proposals | has($pid)') == true ]" "Nodo 2 vede la nuova proposta"

    api_post 8002 "/proposals/$PROP_ID/vote?channel=global" '{"choice":"yes"}'
    wait_for_condition "[ $(api_get 8001 /state | jq --arg pid $PROP_ID '.global.proposals[$pid].votes | length') -eq 1 ]" "Nodo 1 vede il voto del Nodo 2"

    local rep_final=$(get_reputation 8001 "$NODE2_ID")
    assert_equals "11" "$rep_final" "Reputazione del Nodo 2 è 11 dopo aver votato"

    # 5. CHAT E2E CIFRATA
    print_header "SCENARIO 5: CHAT E2E CIFRATA"
    NODE1_ID=$(get_node_id 8002 1)
    api_post 8002 "/chat/initiate" "{\"recipient_id\":\"$NODE1_ID\"}"
    sleep 2
    api_post 8002 "/chat/send/$NODE1_ID" '{"message":"messaggio_segreto_123"}'
    sleep 5
    docker logs synapse-ng-node-1-1 2>&1 | grep "messaggio_segreto_123"
    echo -e "\e[32m✓ SUCCESS\e[0m: Trovato log del messaggio decifrato sul Nodo 1"

    print_header "TUTTI I TEST COMPLETATI CON SUCCESSO"
    echo "Pulizia finale..."
    docker-compose down -v --remove-orphans
}

# Esegui la suite
run_all_tests
