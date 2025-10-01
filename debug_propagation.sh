#!/bin/bash

# Script di debug minimale per isolare problemi di propagazione dei dati di canale.

set -e

print_header() { echo -e "\n\e[1;33m--- $1 ---\e[0m"; }

# --- INIZIO SCRIPT ---

print_header "PULIZIA AMBIENTE"
docker-compose down -v --remove-orphans

print_header "AVVIO DI 2 NODI E RENDEZVOUS"
docker-compose up --build -d rendezvous node-1 node-2

echo "Attendo 20 secondi per la convergenza iniziale..."
sleep 20

print_header "VERIFICA CONVERGENZA INIZIALE"
NODE1_COUNT=$(curl -s http://localhost:8001/state | jq '.global.nodes | length')
NODE2_COUNT=$(curl -s http://localhost:8002/state | jq '.global.nodes | length')

if [ "$NODE1_COUNT" -ne 2 ] || [ "$NODE2_COUNT" -ne 2 ]; then
    echo -e "\e[31m✗ FALLIMENTO: I nodi non si vedono a vicenda prima della creazione del task.\e[0m"
    echo "Stato Nodo 1:"
    curl -s http://localhost:8001/state | jq .
    echo "Stato Nodo 2:"
    curl -s http://localhost:8002/state | jq .
    exit 1
fi
echo -e "\e[32m✓ SUCCESS: I nodi si vedono correttamente (Conteggio: $NODE1_COUNT).\e[0m"

print_header "NODO 1 CREA UN TASK NEL CANALE 'sviluppo_ui'"
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" -H "Content-Type: application/json" -d '{"title":"DEBUG TASK"}' | jq -r '.id')

if [ -z "$TASK_ID" ] || [ "$TASK_ID" == "null" ]; then
    echo -e "\e[31m✗ FALLIMENTO: La creazione del task non ha restituito un ID valido.\e[0m"
    exit 1
fi
echo "Task creato con ID: $TASK_ID"

print_header "ATTENDO 15 SECONDI PER IL GOSSIP"
sleep 15

print_header "ANALISI DELLO STATO DEL NODO 2 (NODO RICEVENTE)"

echo "Interrogo lo stato completo del Nodo 2..."
STATE_NODE_2=$(curl -s http://localhost:8002/state)

if [ -z "$STATE_NODE_2" ]; then
    echo -e "\e[31m✗ FALLIMENTO: Lo stato del Nodo 2 è vuoto.\e[0m"
    exit 1
fi

echo "--- STATO COMPLETO NODO 2 ---"
echo $STATE_NODE_2 | jq .
echo "-----------------------------"

print_header "VERIFICA FINALE"
TASK_STATUS=$(echo $STATE_NODE_2 | jq -r --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid].status')

if [ "$TASK_STATUS" == "open" ]; then
    echo -e "\e[32m✓✓✓ SUCCESS: Il task è stato propagato e trovato nel Nodo 2!\e[0m"
else
    echo -e "\e[31m✗✗✗ FAILURE: Il task NON è stato trovato nel Nodo 2 (stato ricevuto: $TASK_STATUS).\e[0m"
fi

print_header "PULIZIA FINALE"
docker-compose down -v
