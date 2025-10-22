#!/bin/zsh

echo "💰 Finanziamento tesoreria 'sviluppo_ui' con multi-nodo..."

# Array di nodi
NODES=(8001 8002 8003 8004)
CHANNEL="sviluppo_ui"

echo "\n📊 Tesoreria iniziale:"
curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance"

# Creiamo 5 task da 30 SP ciascuno = 150 SP totali
for i in {1..5}; do
  echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📝 Task #$i (reward: 30 SP)..."
  
  # Crea task sul nodo 1
  TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=${CHANNEL}" \
    -H "Content-Type: application/json" \
    -d "{\"title\": \"Financing Task #$i\", \"description\": \"Accumula fondi per Common Tools\", \"reward\": 30}" | jq -r '.id')
  
  if [ "$TASK_ID" = "null" ]; then
    echo "❌ Errore creazione task"
    continue
  fi
  
  echo "   ✅ Task creato: $TASK_ID"
  sleep 2
  
  # Scegli un nodo random per claim
  NODE_PORT=${NODES[$((RANDOM % ${#NODES[@]} + 1))]}
  echo "   👤 Claim da nodo :$NODE_PORT..."
  
  CLAIM_RESP=$(curl -s -X POST "http://localhost:${NODE_PORT}/tasks/${TASK_ID}/claim?channel=${CHANNEL}")
  sleep 2
  
  echo "   🚀 Mark in progress..."
  curl -s -X POST "http://localhost:${NODE_PORT}/tasks/${TASK_ID}/progress?channel=${CHANNEL}" > /dev/null
  sleep 2
  
  echo "   ✅ Complete task..."
  COMPLETE_RESP=$(curl -s -X POST "http://localhost:${NODE_PORT}/tasks/${TASK_ID}/complete?channel=${CHANNEL}")
  sleep 3
  
  # Verifica tesoreria corrente
  CURRENT=$(curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance")
  echo "   💰 Tesoreria corrente: ${CURRENT} SP"
done

echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Tesoreria finale:"
curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance"

echo "\n✅ Finanziamento completato!"
