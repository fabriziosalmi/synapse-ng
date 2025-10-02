# API Testing Examples - Manual Verification

**Practical API Examples for Manual Testing**

Version: 1.0  
Last Updated: October 2025

---

## Table of Contents

1. [Setup](#setup)
2. [Economy Tests](#economy-tests)
3. [Governance Tests](#governance-tests)
4. [Auction Tests](#auction-tests)
5. [Query Reference](#query-reference)

---

## Setup

### 1. Start Network

```bash
docker-compose up --build -d rendezvous node-1 node-2 node-3
```

### 2. Wait for Convergence

```bash
sleep 20
```

### 3. Get Node IDs

```bash
# Node 1
NODE_1_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-1:8000") | .key')
echo "Node 1 ID: $NODE_1_ID"

# Node 2
NODE_2_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-2:8000") | .key')
echo "Node 2 ID: $NODE_2_ID"

# Node 3
NODE_3_ID=$(curl -s http://localhost:8003/state | jq -r '.global.nodes | to_entries[] | select(.value.url == "http://node-3:8000") | .key')
echo "Node 3 ID: $NODE_3_ID"
```

---

## Economy Tests

### Test: Synapse Points Transfer

#### 1. Check Initial Balances

```bash
# View all node balances (should be 1000 SP each)
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id: .id[:16], balance: .balance}'
```

**Expected Output:**
```json
{
  "id": "abc123...",
  "balance": 1000
}
```

#### 2. Create Task with Reward (Node 1)

```bash
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Task with Reward","reward":50}' | jq -r '.id')

echo "Task ID: $TASK_ID"
```

#### 3. Verify SP Freeze

```bash
# Wait for propagation
sleep 20

# Check balance on Node 2 (should see Node 1 with 950 SP)
curl -s http://localhost:8002/state | jq --arg nid "$NODE_1_ID" \
  '.global.nodes[$nid] | {id: .id[:16], balance: .balance}'
```

**Expected Output:**
```json
{
  "id": "abc123...",
  "balance": 950
}
```

#### 4. Complete Task (Node 2)

```bash
# Claim
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui" -d ''
sleep 5

# Progress
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui" -d ''
sleep 5

# Complete
curl -s -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui" -d ''
```

#### 5. Verify SP Transfer

```bash
# Wait for propagation
sleep 25

# Check balances on all nodes (must be identical!)
for port in 8001 8002 8003; do
  echo "=== Node :$port ==="
  curl -s http://localhost:$port/state | jq \
    --arg n1 "$NODE_1_ID" --arg n2 "$NODE_2_ID" \
    '.global.nodes | {node1_balance: .[$n1].balance, node2_balance: .[$n2].balance}'
done
```

**Expected Output (IDENTICAL on all nodes):**
```json
{
  "node1_balance": 950,
  "node2_balance": 1050
}
```

#### ✅ Success Criteria

All nodes must show identical balances. If they differ, there is **economic divergence** (critical bug).

---

## Governance Tests

### Test: Weighted Voting

#### 1. Build Reputation (Node 1 completes tasks)

```bash
# Complete 2 tasks to gain +20 reputation
for i in 1 2; do
  TASK_REP=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"Reputation Task $i\"}" | jq -r '.id')
  
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/claim?channel=dev_ui" -d ''
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/progress?channel=dev_ui" -d ''
  sleep 3
  curl -s -X POST "http://localhost:8001/tasks/$TASK_REP/complete?channel=dev_ui" -d ''
  
  echo "Task $i completed"
done

sleep 25
```

#### 2. Verify Reputation

```bash
# Check reputation on Node 2
curl -s http://localhost:8002/state | jq --arg nid "$NODE_1_ID" \
  '.global.nodes[$nid] | {id: .id[:16], reputation: .reputation}'
```

**Expected Output:**
```json
{
  "id": "abc123...",
  "reputation": 20
}
```

#### 3. Create Proposal (Node 3)

```bash
PROP_ID=$(curl -s -X POST "http://localhost:8003/proposals?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Weighted Vote","description":"Testing weighted voting mechanism"}' \
  | jq -r '.id')

echo "Proposal ID: $PROP_ID"

sleep 10
```

#### 4. Cast Votes

```bash
# Node 1 (high reputation ~20, weight ~5.4): votes NO
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/vote?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"rejection"}'

# Node 2 (low reputation ~0-1, weight ~1-2): votes YES
curl -s -X POST "http://localhost:8002/proposals/$PROP_ID/vote?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"approval"}'

# Node 3 (no reputation, weight 1.0): votes YES
curl -s -X POST "http://localhost:8003/proposals/$PROP_ID/vote?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"vote":"approval"}'

sleep 15
```

#### 5. Close Proposal and Check Outcome

```bash
# Close proposal
curl -s -X POST "http://localhost:8001/proposals/$PROP_ID/close?channel=dev_ui" -d ''

sleep 15

# Check outcome (should be "rejected" despite 2 YES vs 1 NO)
curl -s http://localhost:8002/proposals?channel=dev_ui | jq '.[0] | {outcome: .outcome, votes: .votes}'
```

**Expected Output:**
```json
{
  "outcome": "rejected",
  "votes": {
    "node1_id": "rejection",
    "node2_id": "approval",
    "node3_id": "approval"
  }
}
```

#### ✅ Success Criteria

- Outcome: **"rejected"**
- Despite 2 YES vs 1 NO, Node 1's high reputation weight (5.4) > Node 2+3 weights (3.0)
- Proves weighted voting works correctly

---

## Auction Tests

### Test: Bid Competition

#### 1. Create Auction Task

```bash
AUCTION_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Implement Dashboard",
    "description":"Build analytics dashboard",
    "enable_auction":true,
    "max_reward":500,
    "auction_deadline_hours":48,
    "tags":["ui","analytics"]
  }' | jq -r '.id')

echo "Auction Task ID: $AUCTION_ID"

sleep 10
```

#### 2. Place Bids

```bash
# Node 2 bids (high reputation)
curl -s -X POST "http://localhost:8002/tasks/$AUCTION_ID/bid?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"amount":450,"estimated_days":3}'

sleep 5

# Node 3 bids (low reputation, lower price)
curl -s -X POST "http://localhost:8003/tasks/$AUCTION_ID/bid?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"amount":400,"estimated_days":4}'

sleep 15
```

#### 3. Check Bids

```bash
curl -s http://localhost:8001/tasks?channel=dev_ui | jq \
  --arg tid "$AUCTION_ID" \
  '.[] | select(.id == $tid) | .auction.bids'
```

**Expected Output:**
```json
{
  "node2_id": {
    "amount": 450,
    "reputation": 20,
    "estimated_days": 3,
    "timestamp": "2025-10-03T10:00:00Z"
  },
  "node3_id": {
    "amount": 400,
    "reputation": 0,
    "estimated_days": 4,
    "timestamp": "2025-10-03T10:05:00Z"
  }
}
```

#### 4. Wait for Deadline (or manually close for testing)

```bash
# For testing, manually trigger deadline processing
# In production, background loop processes automatically

# Check winner after deadline
sleep 60

curl -s http://localhost:8002/tasks?channel=dev_ui | jq \
  --arg tid "$AUCTION_ID" \
  '.[] | select(.id == $tid) | {status: .status, assignee: .assignee, selected_bid: .auction.selected_bid}'
```

**Expected Output:**
```json
{
  "status": "claimed",
  "assignee": "node2_id",
  "selected_bid": "node2_id"
}
```

**Winner Explanation**: Node 2 wins despite higher price due to reputation weight (40%)

---

## Query Reference

### Get All Tasks

```bash
curl -s http://localhost:8001/tasks?channel=CHANNEL_ID | jq '.'
```

### Get Specific Task

```bash
curl -s http://localhost:8001/tasks/TASK_ID?channel=CHANNEL_ID | jq '.'
```

### Get All Proposals

```bash
curl -s http://localhost:8001/proposals?channel=CHANNEL_ID | jq '.'
```

### Get Node State

```bash
curl -s http://localhost:8001/state | jq '.'
```

### Get Specific Node Info

```bash
curl -s http://localhost:8001/state | jq --arg nid "NODE_ID" '.global.nodes[$nid]'
```

### Get Node Balance

```bash
curl -s http://localhost:8001/state | jq --arg nid "NODE_ID" '.global.nodes[$nid].balance'
```

### Get Node Reputation

```bash
curl -s http://localhost:8001/state | jq --arg nid "NODE_ID" '.global.nodes[$nid].reputation'
```

### Get Channel Treasury

```bash
curl -s http://localhost:8001/treasury/CHANNEL_ID | jq '.'
```

### Get Transactions History

```bash
curl -s http://localhost:8001/state | jq '.channels["CHANNEL_ID"].transactions'
```

### Get Proposal Votes

```bash
curl -s http://localhost:8001/proposals?channel=CHANNEL_ID | jq '.[0].votes'
```

### Get Active Auctions

```bash
curl -s http://localhost:8001/tasks?channel=CHANNEL_ID | jq '.[] | select(.status == "auction_open")'
```

---

## Debugging Queries

### Check Network Convergence

```bash
# Get node count from each node (should all be 3)
for port in 8001 8002 8003; do
  echo "Node :$port"
  curl -s http://localhost:$port/state | jq '.global.nodes | length'
done
```

### Check Clock Sync

```bash
# Compare local times on all nodes
for port in 8001 8002 8003; do
  echo "Node :$port"
  curl -s http://localhost:$port/state | jq '.local.timestamp'
done
```

### Check Gossip Propagation

```bash
# Create task on Node 1
TASK=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -d '{"title":"Propagation Test"}' | jq -r '.id')

# Wait and check on Node 3
sleep 10
curl -s http://localhost:8003/tasks?channel=dev_ui | jq --arg tid "$TASK" '.[] | select(.id == $tid)'
```

### Verify Balance Consistency

```bash
# All nodes must report identical balances
for port in 8001 8002 8003; do
  echo "=== Node :$port ==="
  curl -s http://localhost:$port/state | jq '.global.nodes | to_entries | map({id: .value.id[:16], balance: .value.balance})'
done
```

---

## Manual Testing Checklist

### Economy System ✅

- [ ] Initial balances correct (1000 SP each)
- [ ] SP freeze on task creation
- [ ] SP transfer on task completion
- [ ] Balance consistency across all nodes
- [ ] Total SP conserved (no creation/destruction)

### Governance System ✅

- [ ] Reputation accumulates correctly (+10 per task, +1 per vote)
- [ ] Vote weight calculation works (1.0 + log₂(rep + 1))
- [ ] Proposal outcome deterministic across nodes
- [ ] Meritocratic voting (quality over quantity)

### Auction System ✅

- [ ] Auction task creation works
- [ ] Bids accept correct data
- [ ] Deadline processing automatic
- [ ] Winner selection algorithm correct
- [ ] Fallback to traditional if no bids

### Network Basics ✅

- [ ] State convergence (all nodes discover each other)
- [ ] WebRTC P2P connections established
- [ ] SynapseSub message propagation works
- [ ] Task lifecycle complete (create → claim → progress → complete)
- [ ] Channel isolation maintained

---

## Related Documentation

- [Testing Guide](TESTING_GUIDE.md) - Automated test suite
- [Governance System](GOVERNANCE_SYSTEM.md) - Voting mechanisms
- [Auction System](AUCTION_SYSTEM.md) - Bidding details
- [Autonomous Organism](AUTONOMOUS_ORGANISM.md) - Economy design

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Status**: ✅ Production Ready
