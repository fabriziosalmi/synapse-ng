#!/bin/zsh

echo "💰 Finanziamento tesoreria 'sviluppo_ui'..."

for i in {1..3}; do
  echo "\n📝 Task #$i..."
  TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
    -H "Content-Type: application/json" \
    -d "{\"title\": \"Financing Task #$i\", \"reward\": 50}" | jq -r '.id')
  
  echo "   ID: $TASK_ID"
  
  curl -s -X POST "http://localhost:8001/tasks/$TASK_ID/claim?channel=sviluppo_ui" > /dev/null
  sleep 1
  curl -s -X POST "http://localhost:8001/tasks/$TASK_ID/progress?channel=sviluppo_ui" > /dev/null
  sleep 1
  curl -s -X POST "http://localhost:8001/tasks/$TASK_ID/complete?channel=sviluppo_ui" > /dev/null
  
  sleep 2
done

echo "\n💰 Tesoreria finale:"
curl -s http://localhost:8001/state | jq '.sviluppo_ui.treasury_balance'
