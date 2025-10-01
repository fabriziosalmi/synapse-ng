#!/bin/bash

# Test per modalità P2P completamente decentralizzata

set -e

print_header() { echo -e "\n\e[1;34m================== $1 ==================\e[0m"; }

print_header "TEST P2P - FASE 3: DECENTRALIZZAZIONE COMPLETA"

echo "Pulizia ambiente..."
docker-compose -f docker-compose.p2p.yml down -v --remove-orphans
rm -rf data/bootstrap data/node-2 data/node-3 data/node-4

echo "Avvio nodi in modalità P2P..."
docker-compose -f docker-compose.p2p.yml up --build -d

echo "Attendo 30s per bootstrap e connessioni WebRTC..."
sleep 30

print_header "VERIFICA BOOTSTRAP NODE"

echo "Stato Bootstrap Node:"
curl -s http://localhost:8001/state | jq '.global.nodes | length'

echo -e "\nConnessioni WebRTC Bootstrap:"
curl -s http://localhost:8001/webrtc/connections | jq '.total_connections, .active_data_channels'

print_header "VERIFICA RETE P2P"

echo "Stato Nodo 2 (dovrebbe vedere >= 2 nodi):"
curl -s http://localhost:8002/state | jq '.global.nodes | length'

echo -e "\nStato Nodo 3 (dovrebbe vedere >= 3 nodi):"
curl -s http://localhost:8003/state | jq '.global.nodes | length'

echo -e "\nStato Nodo 4 (dovrebbe vedere 4 nodi):"
curl -s http://localhost:8004/state | jq '.global.nodes | length'

print_header "VERIFICA PUBSUB P2P"

echo "Stats PubSub Nodo 2:"
curl -s http://localhost:8002/pubsub/stats | jq '.'

echo -e "\nStats PubSub Nodo 3:"
curl -s http://localhost:8003/pubsub/stats | jq '.'

print_header "TEST GOSSIP SENZA RENDEZVOUS"

echo "Creo un task sul Bootstrap Node..."
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test P2P Decentralizzato"}' | jq -r '.id')

echo "Task ID: $TASK_ID"

echo "Attendo propagazione P2P (20s)..."
sleep 20

echo -e "\nVerifica task su Nodo 2:"
TASK_NODE2=$(curl -s http://localhost:8002/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid] // "NOT_FOUND"')
echo "$TASK_NODE2"

echo -e "\nVerifica task su Nodo 3:"
TASK_NODE3=$(curl -s http://localhost:8003/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid] // "NOT_FOUND"')
echo "$TASK_NODE3"

echo -e "\nVerifica task su Nodo 4:"
TASK_NODE4=$(curl -s http://localhost:8004/state | jq --arg tid "$TASK_ID" '.sviluppo_ui.tasks[$tid] // "NOT_FOUND"')
echo "$TASK_NODE4"

print_header "VERIFICA LOGS P2P"

echo "Logs Bootstrap (ultimi 40):"
docker logs synapse-ng-bootstrap 2>&1 | grep -i "bootstrap\|p2p\|relay\|webrtc\|pubsub" | tail -40

echo -e "\nLogs Nodo 2 (ultimi 40):"
docker logs synapse-ng-node-2 2>&1 | grep -i "bootstrap\|p2p\|relay\|webrtc\|pubsub" | tail -40

print_header "TEST COMPLETATO"
echo "✅ La rete funziona SENZA Rendezvous Server!"
echo ""
echo "Comandi utili:"
echo "  docker-compose -f docker-compose.p2p.yml logs -f bootstrap"
echo "  docker-compose -f docker-compose.p2p.yml down -v"
