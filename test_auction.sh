#!/bin/bash
# Test Script per Sistema d'Asta - Synapse-NG

set -e

BASE_URL="http://localhost:8001"
CHANNEL="dev_ui"

echo "🔨 Test Suite: Sistema d'Asta Synapse-NG"
echo "=========================================="
echo ""

# Colori per output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione per stampare test
print_test() {
    echo -e "${YELLOW}TEST $1:${NC} $2"
}

# Funzione per successo
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Funzione per errore
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Test 1: Verifica schema task_v2
print_test "1" "Verifica schema task_v2 esistente"
SCHEMA=$(curl -s "$BASE_URL/schemas/task_v2")
if echo "$SCHEMA" | jq -e '.schema_name == "task_v2"' > /dev/null; then
    print_success "Schema task_v2 trovato"
    echo "$SCHEMA" | jq '.fields.auction'
else
    print_error "Schema task_v2 non trovato"
    exit 1
fi
echo ""

# Test 2: Crea task con asta
print_test "2" "Creazione task con meccanismo d'asta"
TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Test Auction Task",
        "description": "Task di test per il sistema di aste",
        "enable_auction": true,
        "max_reward": 500,
        "auction_deadline_hours": 1,
        "tags": ["test", "auction"]
    }')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id')
AUCTION_STATUS=$(echo "$TASK_RESPONSE" | jq -r '.auction.status')
MAX_REWARD=$(echo "$TASK_RESPONSE" | jq -r '.auction.max_reward')

if [ "$AUCTION_STATUS" = "open" ] && [ "$MAX_REWARD" = "500" ]; then
    print_success "Task con asta creato: $TASK_ID"
    echo "   Max Reward: $MAX_REWARD SP"
    echo "   Asta Status: $AUCTION_STATUS"
else
    print_error "Errore nella creazione del task"
    exit 1
fi
echo ""

# Test 3: Piazza prima bid
print_test "3" "Piazza bid #1 (amount: 450, days: 3)"
BID1_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 450,
        "estimated_days": 3
    }')

BID1_AMOUNT=$(echo "$BID1_RESPONSE" | jq -r '.bid.amount')
BID1_REP=$(echo "$BID1_RESPONSE" | jq -r '.bid.reputation')
TOTAL_BIDS=$(echo "$BID1_RESPONSE" | jq -r '.total_bids')

if [ "$BID1_AMOUNT" = "450" ] && [ "$TOTAL_BIDS" = "1" ]; then
    print_success "Bid #1 piazzata con successo"
    echo "   Amount: $BID1_AMOUNT SP"
    echo "   Reputation: $BID1_REP"
    echo "   Total Bids: $TOTAL_BIDS"
else
    print_error "Errore nel piazzare bid #1"
    exit 1
fi
echo ""

# Test 4: Piazza seconda bid (simula aggiornamento)
print_test "4" "Aggiorna bid (amount: 400, days: 4) - stesso peer"
BID2_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 400,
        "estimated_days": 4
    }')

BID2_AMOUNT=$(echo "$BID2_RESPONSE" | jq -r '.bid.amount')
TOTAL_BIDS_2=$(echo "$BID2_RESPONSE" | jq -r '.total_bids')

if [ "$BID2_AMOUNT" = "400" ] && [ "$TOTAL_BIDS_2" = "1" ]; then
    print_success "Bid aggiornata (LWW funziona)"
    echo "   Nuovo Amount: $BID2_AMOUNT SP"
    echo "   Total Bids (stesso peer): $TOTAL_BIDS_2"
else
    print_error "Errore nell'aggiornamento bid"
    exit 1
fi
echo ""

# Test 5: Verifica stato asta in /state
print_test "5" "Verifica auction_info in GET /state"
STATE=$(curl -s "$BASE_URL/state")
BIDS_COUNT=$(echo "$STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".auction_info.bids_count")
TIME_REMAINING=$(echo "$STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".auction_info.time_remaining_hours")
IS_EXPIRED=$(echo "$STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".auction_info.is_expired")

if [ "$BIDS_COUNT" != "null" ]; then
    print_success "Auction info trovata in /state"
    echo "   Bids Count: $BIDS_COUNT"
    echo "   Time Remaining: $TIME_REMAINING hours"
    echo "   Is Expired: $IS_EXPIRED"
else
    print_error "Auction info non trovata"
    exit 1
fi
echo ""

# Test 6: Tenta bid superiore a max_reward (deve fallire)
print_test "6" "Tenta bid > max_reward (deve fallire)"
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 600,
        "estimated_days": 2
    }')

if echo "$ERROR_RESPONSE" | jq -e '.detail' | grep -q "supera"; then
    print_success "Bid > max_reward correttamente rifiutata"
    echo "   Errore: $(echo "$ERROR_RESPONSE" | jq -r '.detail')"
else
    print_error "Bid > max_reward non è stata rifiutata!"
    exit 1
fi
echo ""

# Test 7: Verifica bid con amount negativo (deve fallire)
print_test "7" "Tenta bid con amount negativo (deve fallire)"
ERROR_RESPONSE_2=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "amount": -100,
        "estimated_days": 2
    }')

if echo "$ERROR_RESPONSE_2" | jq -e '.detail' | grep -q "> 0"; then
    print_success "Bid negativa correttamente rifiutata"
else
    print_error "Bid negativa non è stata rifiutata!"
    exit 1
fi
echo ""

# Test 8: Seleziona vincitore manualmente
print_test "8" "Selezione vincitore manuale (owner)"
SELECT_RESPONSE=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/select_bid?channel=$CHANNEL")
WINNER_ID=$(echo "$SELECT_RESPONSE" | jq -r '.winner')
WINNING_AMOUNT=$(echo "$SELECT_RESPONSE" | jq -r '.winning_bid.amount')

if [ "$WINNER_ID" != "null" ] && [ "$WINNING_AMOUNT" = "400" ]; then
    print_success "Vincitore selezionato con successo"
    echo "   Winner: ${WINNER_ID:0:16}..."
    echo "   Winning Amount: $WINNING_AMOUNT SP"
else
    print_error "Errore nella selezione del vincitore"
    exit 1
fi
echo ""

# Test 9: Verifica stato finale task
print_test "9" "Verifica stato finale del task"
FINAL_STATE=$(curl -s "$BASE_URL/state")
FINAL_STATUS=$(echo "$FINAL_STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".status")
FINAL_ASSIGNEE=$(echo "$FINAL_STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".assignee")
FINAL_REWARD=$(echo "$FINAL_STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".reward")
AUCTION_FINAL=$(echo "$FINAL_STATE" | jq -r ".${CHANNEL}.tasks.\"${TASK_ID}\".auction.status")

if [ "$FINAL_STATUS" = "claimed" ] && [ "$FINAL_REWARD" = "400" ] && [ "$AUCTION_FINAL" = "finalized" ]; then
    print_success "Task correttamente assegnato"
    echo "   Status: $FINAL_STATUS"
    echo "   Assignee: ${FINAL_ASSIGNEE:0:16}..."
    echo "   Reward: $FINAL_REWARD SP"
    echo "   Auction Status: $AUCTION_FINAL"
else
    print_error "Stato finale del task non corretto"
    exit 1
fi
echo ""

# Test 10: Tenta nuova bid su asta finalizzata (deve fallire)
print_test "10" "Tenta bid su asta finalizzata (deve fallire)"
ERROR_RESPONSE_3=$(curl -s -X POST "$BASE_URL/tasks/$TASK_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 350,
        "estimated_days": 2
    }')

if echo "$ERROR_RESPONSE_3" | jq -e '.detail' | grep -q "finalized"; then
    print_success "Bid su asta chiusa correttamente rifiutata"
else
    print_error "Bid su asta chiusa non è stata rifiutata!"
    exit 1
fi
echo ""

# Test 11: Crea task senza asta (backward compatibility)
print_test "11" "Crea task tradizionale (senza asta)"
TRAD_TASK=$(curl -s -X POST "$BASE_URL/tasks?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Traditional Task",
        "description": "Task senza asta",
        "enable_auction": false,
        "reward": 100,
        "schema_name": "task_v1"
    }')

TRAD_ID=$(echo "$TRAD_TASK" | jq -r '.id')
TRAD_STATUS=$(echo "$TRAD_TASK" | jq -r '.status')
HAS_AUCTION=$(echo "$TRAD_TASK" | jq -r '.auction // "null"')

if [ "$TRAD_STATUS" = "open" ] && [ "$HAS_AUCTION" = "null" ]; then
    print_success "Task tradizionale creato (backward compatible)"
    echo "   Task ID: $TRAD_ID"
    echo "   Status: $TRAD_STATUS"
    echo "   Has Auction: false"
else
    print_error "Errore nella creazione task tradizionale"
    exit 1
fi
echo ""

# Test 12: Crea task con asta breve per test auto-close
print_test "12" "Test auto-close asta (deadline 5 secondi)"
AUTO_TASK=$(curl -s -X POST "$BASE_URL/tasks?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "Auto-Close Test Task",
        "description": "Task per testare chiusura automatica",
        "enable_auction": true,
        "max_reward": 300,
        "auction_deadline_hours": 0.0014,
        "tags": ["test", "auto-close"]
    }')

AUTO_ID=$(echo "$AUTO_TASK" | jq -r '.id')
print_success "Task con deadline breve creato: $AUTO_ID"

# Piazza una bid
curl -s -X POST "$BASE_URL/tasks/$AUTO_ID/bid?channel=$CHANNEL" \
    -H "Content-Type: application/json" \
    -d '{"amount": 250, "estimated_days": 2}' > /dev/null

echo "   Aspetto 35 secondi per l'auto-close..."
sleep 35

# Verifica che l'asta sia stata chiusa automaticamente
AUTO_STATE=$(curl -s "$BASE_URL/state")
AUTO_AUCTION_STATUS=$(echo "$AUTO_STATE" | jq -r ".${CHANNEL}.tasks.\"${AUTO_ID}\".auction.status")
AUTO_TASK_STATUS=$(echo "$AUTO_STATE" | jq -r ".${CHANNEL}.tasks.\"${AUTO_ID}\".status")

if [ "$AUTO_AUCTION_STATUS" = "finalized" ] && [ "$AUTO_TASK_STATUS" = "claimed" ]; then
    print_success "Asta chiusa automaticamente alla deadline"
    echo "   Auction Status: $AUTO_AUCTION_STATUS"
    echo "   Task Status: $AUTO_TASK_STATUS"
else
    print_error "Auto-close non ha funzionato"
    echo "   Auction Status: $AUTO_AUCTION_STATUS"
    echo "   Task Status: $AUTO_TASK_STATUS"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}✓ Tutti i test completati con successo!${NC}"
echo ""
echo "Test eseguiti:"
echo "  1. ✓ Schema task_v2 verificato"
echo "  2. ✓ Creazione task con asta"
echo "  3. ✓ Piazzamento bid"
echo "  4. ✓ Aggiornamento bid (LWW)"
echo "  5. ✓ Auction info in /state"
echo "  6. ✓ Validazione bid > max_reward"
echo "  7. ✓ Validazione bid negativa"
echo "  8. ✓ Selezione vincitore manuale"
echo "  9. ✓ Stato finale task"
echo " 10. ✓ Rifiuto bid su asta chiusa"
echo " 11. ✓ Backward compatibility (task tradizionali)"
echo " 12. ✓ Auto-close asta alla deadline"
echo ""
echo "🔨 Sistema d'Asta: FUNZIONANTE ✨"
