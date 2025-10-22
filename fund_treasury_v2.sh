#!/bin/zsh

echo "💰 Finanziamento tesoreria 'sviluppo_ui' con task_v2..."

CHANNEL="sviluppo_ui"

echo "\n📊 Tesoreria iniziale:"
curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance"

# Creiamo 4 task da 30 SP ciascuno con schema task_v2 = 120 SP totali
for i in {1..4}; do
  echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📝 Task V2 #$i (reward: 30 SP)..."
  
  # Crea task V2 sul nodo 1
  # Common Tools richiede SOLO task_v2 (treasury support)
  # enable_auction=false per permettere claim diretto
  TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=${CHANNEL}" \
    -H "Content-Type: application/json" \
    -d "{
      \"title\": \"Financing Task V2 #$i\", 
      \"description\": \"Accumula fondi per Common Tools\", 
      \"reward\": 30,
      \"schema_name\": \"task_v2\",
      \"enable_auction\": false
    }" | jq -r '.id')
  
  if [ "$TASK_ID" = "null" ] || [ -z "$TASK_ID" ]; then
    echo "❌ Errore creazione task"
    continue
  fi
  
  echo "   ✅ Task V2 creato: $TASK_ID"
  sleep 2
  
  echo "   👤 Claim task..."
  curl -s -X POST "http://localhost:8001/tasks/${TASK_ID}/claim?channel=${CHANNEL}" > /dev/null
  sleep 2
  
  echo "   🚀 Mark in progress..."
  curl -s -X POST "http://localhost:8001/tasks/${TASK_ID}/progress?channel=${CHANNEL}" > /dev/null
  sleep 2
  
  echo "   ✅ Complete task..."
  curl -s -X POST "http://localhost:8001/tasks/${TASK_ID}/complete?channel=${CHANNEL}" > /dev/null
  sleep 3
  
  # Verifica tesoreria corrente
  CURRENT=$(curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance")
  echo "   💰 Tesoreria corrente: ${CURRENT} SP"
done

echo "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Riepilogo finale:"
FINAL=$(curl -s http://localhost:8001/state | jq ".${CHANNEL}.treasury_balance")
echo "   Tesoreria: ${FINAL} SP"
echo "\n✅ Finanziamento completato!"
