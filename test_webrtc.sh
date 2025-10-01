#!/bin/bash

# Test per verificare WebRTC e SynapseSub

set -e

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }

print_header "TEST WEBRTC + SYNAPSESUB - FASE 2"

echo "Pulizia ambiente..."
docker-compose down -v --remove-orphans

echo "Avvio nodi..."
docker-compose up --build -d rendezvous node-1 node-2 node-3

echo "Attendo 20s per stabilire connessioni WebRTC..."
sleep 20

print_header "VERIFICA CONNESSIONI WEBRTC"

echo "Stato WebRTC Nodo 1:"
curl -s http://localhost:8001/webrtc/connections | jq '.'

echo -e "\nStato WebRTC Nodo 2:"
curl -s http://localhost:8002/webrtc/connections | jq '.'

echo -e "\nStato WebRTC Nodo 3:"
curl -s http://localhost:8003/webrtc/connections | jq '.'

print_header "VERIFICA PUBSUB"

echo "Statistiche PubSub Nodo 1:"
curl -s http://localhost:8001/pubsub/stats | jq '.'

echo -e "\nStatistiche PubSub Nodo 2:"
curl -s http://localhost:8002/pubsub/stats | jq '.'

echo -e "\nStatistiche PubSub Nodo 3:"
curl -s http://localhost:8003/pubsub/stats | jq '.'

print_header "TEST GOSSIP VIA PUBSUB"

echo "Creo un task sul Nodo 1..."
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test PubSub"}' | jq -r '.id')

echo "Task ID: $TASK_ID"

echo "Attendo propagazione via PubSub (15s)..."
sleep 15

echo -e "\nVerifica task sul Nodo 2:"
curl -s http://localhost:8002/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid]'

echo -e "\nVerifica task sul Nodo 3:"
curl -s http://localhost:8003/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid]'

print_header "VERIFICA LOGS SYNAPSESUB"

echo "Logs SynapseSub Nodo 1 (ultimi 30):"
docker logs synapse-ng-node-1-1 2>&1 | grep -i "pubsub\|announce\|message\|topic\|mesh" | tail -30

echo -e "\nLogs SynapseSub Nodo 2 (ultimi 30):"
docker logs synapse-ng-node-2-1 2>&1 | grep -i "pubsub\|announce\|message\|topic\|mesh" | tail -30

print_header "TEST COMPLETATO"
echo "Usa 'docker-compose down -v' per pulire l'ambiente"
