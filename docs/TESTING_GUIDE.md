# Testing Guide - Comprehensive Test Suite

**End-to-End Testing for Synapse-NG Systems**

Version: 1.0  
Last Updated: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Scenarios](#test-scenarios)
4. [Helper Functions](#helper-functions)
5. [Manual Testing](#manual-testing)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Synapse-NG includes a comprehensive test suite that verifies:

- **Network Convergence** - CRDT state synchronization
- **P2P Connectivity** - WebRTC peer connections
- **PubSub Protocol** - SynapseSub message propagation
- **Task Lifecycle** - Complete task workflow
- **Reputation System** - Merit accumulation
- **Weighted Voting** - Governance with reputation weights
- **Economy System** - Synapse Points (SP) transfers

### Test Philosophy

All tests are **deterministic end-to-end** tests that verify:
1. ✅ **Correctness** - System behaves as specified
2. ✅ **Determinism** - All nodes reach same state
3. ✅ **Atomicity** - State changes are atomic
4. ✅ **Consistency** - No divergence across nodes

---

## Quick Start

### Run All Tests

```bash
./test_suite.sh
# or
./test_suite.sh all
```

**Runs:**
1. Base tests (Scenarios 1-6)
2. Governance test (Scenario 7)
3. Economy test (Scenario 8)

**Duration:** ~5-8 minutes

### Run Selective Tests

```bash
# Only base tests (convergence, WebRTC, PubSub, task lifecycle, reputation)
./test_suite.sh base

# Only governance test (weighted voting)
./test_suite.sh governance

# Only economy test (SP transfers)
./test_suite.sh economy

# Show help
./test_suite.sh help
```

---

## Test Scenarios

### Scenario 1: State Convergence

**Objective**: Verify CRDT state synchronization across all nodes

**Process**:
1. Start 3 nodes (node-1, node-2, node-3)
2. Wait 20 seconds for gossip propagation
3. Check each node discovers the other two

**Verification**:
```bash
curl http://localhost:8001/state | jq '.global.nodes | length'
# Expected: 3 (self + 2 peers)
```

**Success Criteria**:
- ✅ All 3 nodes have 3 entries in `global.nodes`
- ✅ Each node's ID appears in all other nodes' state

---

### Scenario 2: P2P WebRTC Connections

**Objective**: Verify direct peer-to-peer connections

**Process**:
1. Start 3 nodes
2. Wait for WebRTC handshakes (mDNS discovery + STUN)
3. Query `/peers` endpoint

**Verification**:
```bash
curl http://localhost:8001/peers | jq '. | length'
# Expected: 2 (connected to 2 other nodes)
```

**Success Criteria**:
- ✅ Each node has 2 active WebRTC connections
- ✅ Data channels open and functional

---

### Scenario 3: SynapseSub Protocol

**Objective**: Verify topic-based message propagation

**Process**:
1. Node-1 creates task in channel "dev_ui"
2. Wait for gossip propagation
3. Check task appears on Node-2 and Node-3

**Verification**:
```bash
curl http://localhost:8002/tasks?channel=dev_ui | jq '. | length'
# Expected: 1 (task propagated)
```

**Success Criteria**:
- ✅ Task created on Node-1 appears on all nodes
- ✅ Propagation time < 15 seconds

---

### Scenario 4: Task Lifecycle

**Objective**: Verify complete task workflow: create → claim → progress → complete

**Process**:
1. Node-1 creates task
2. Node-2 claims task → status: "claimed"
3. Node-2 marks progress → status: "in_progress"
4. Node-2 completes task → status: "completed"

**Verification**:
```bash
curl http://localhost:8003/tasks?channel=dev_ui | jq '.[0].status'
# Expected: "completed"
```

**Success Criteria**:
- ✅ Status transitions work correctly
- ✅ State propagates to all nodes
- ✅ Only assignee can progress task

---

### Scenario 5: Reputation System

**Objective**: Verify reputation accumulation

**Process**:
1. Node-1 completes 2 tasks → +10 reputation each = +20 total
2. Query Node-2 for Node-1's reputation

**Verification**:
```bash
curl http://localhost:8002/state | jq --arg nid "$NODE_1_ID" \
  '.global.nodes[$nid].reputation'
# Expected: 20
```

**Success Criteria**:
- ✅ Task completion grants +10 reputation
- ✅ Reputation visible to all nodes
- ✅ Voting grants +1 reputation

---

### Scenario 6: Channel Isolation

**Objective**: Verify tasks don't leak across channels

**Process**:
1. Create task in "dev_ui" channel
2. Query "backend_api" channel

**Verification**:
```bash
curl http://localhost:8001/tasks?channel=backend_api | jq '. | length'
# Expected: 0 (no tasks in different channel)
```

**Success Criteria**:
- ✅ Channels are isolated
- ✅ Tasks only appear in their designated channel

---

### Scenario 7: Weighted Voting Governance ⭐

**Objective**: Verify reputation-weighted voting works correctly

**Formula**: `vote_weight = 1.0 + log₂(reputation + 1)`

**Process**:

1. **Build Reputation**:
   - Node A: Complete 2 tasks → reputation 20 (weight ~5.4)
   - Node B: Vote on 1 proposal → reputation 1 (weight ~2.0)
   - Node C: No actions → reputation 0 (weight 1.0)

2. **Create Proposal** (Node C):
   ```bash
   curl -X POST http://localhost:8003/proposals?channel=dev_ui \
     -H "Content-Type: application/json" \
     -d '{"title": "Critical Change", "description": "Test weighted voting"}'
   ```

3. **Vote**:
   - Node A: NO (weight 5.4)
   - Node B: YES (weight 2.0)
   - Node C: YES (weight 1.0)
   - **Total**: NO = 5.4, YES = 3.0

4. **Close Proposal**:
   ```bash
   curl -X POST http://localhost:8001/proposals/{id}/close?channel=dev_ui
   ```

**Verification**:
```bash
curl http://localhost:8002/proposals?channel=dev_ui | jq '.[0].outcome'
# Expected: "rejected" (despite 2 YES vs 1 NO, weight favors NO)
```

**Success Criteria**:
- ✅ Proposal outcome = "rejected"
- ✅ All nodes agree on outcome
- ✅ Weighted algorithm works correctly

**What This Proves**:
- ✅ Meritocratic governance (quality over quantity)
- ✅ Logarithmic weighting prevents dominance
- ✅ Deterministic calculation across nodes

---

### Scenario 8: Economy System (Synapse Points) ⭐

**Objective**: Verify deterministic SP transfers

**Process**:

1. **Initial State**:
   - Node A: 1000 SP
   - Node B: 1000 SP
   - Node C: 1000 SP

2. **Create Task with Reward** (Node A):
   ```bash
   curl -X POST http://localhost:8001/tasks?channel=dev_ui \
     -d '{"title": "Test Task", "reward": 30}'
   ```

3. **Verify Frozen SP** (check on Node B):
   ```bash
   curl http://localhost:8002/state | jq --arg nid "$NODE_A_ID" \
     '.global.nodes[$nid].balance'
   # Expected: 970 (1000 - 30 frozen)
   ```

4. **Complete Task** (Node B):
   ```bash
   curl -X POST http://localhost:8002/tasks/{id}/claim?channel=dev_ui
   curl -X POST http://localhost:8002/tasks/{id}/progress?channel=dev_ui
   curl -X POST http://localhost:8002/tasks/{id}/complete?channel=dev_ui
   ```

5. **Verify Final Balances** (on ALL nodes):
   ```bash
   for port in 8001 8002 8003; do
     echo "=== Node :$port ==="
     curl http://localhost:$port/state | jq \
       --arg na "$NODE_A_ID" --arg nb "$NODE_B_ID" --arg nc "$NODE_C_ID" \
       '{
         node_a: .global.nodes[$na].balance,
         node_b: .global.nodes[$nb].balance,
         node_c: .global.nodes[$nc].balance
       }'
   done
   ```

**Expected Output (IDENTICAL on all nodes)**:
```json
{
  "node_a": 970,
  "node_b": 1030,
  "node_c": 1000
}
```

**Success Criteria**:
- ✅ Node A: 970 SP (paid 30 SP)
- ✅ Node B: 1030 SP (earned 30 SP)
- ✅ Node C: 1000 SP (unchanged)
- ✅ **All nodes agree** (no divergence)
- ✅ Total SP conserved (3000 SP)

**What This Proves**:
- ✅ Deterministic economy
- ✅ No double-spend possible
- ✅ No value creation/destruction
- ✅ Atomic transfers

---

## Helper Functions

The test suite includes bash helper functions:

### `get_reputation(node_port, node_id)`

Get reputation of a specific node.

```bash
REP=$(get_reputation 8001 "$NODE_A_ID")
echo "Node A reputation: $REP"
```

### `get_balance(node_port, node_id)`

Get Synapse Points balance.

```bash
BAL=$(get_balance 8002 "$NODE_B_ID")
echo "Node B balance: $BAL SP"
```

### `get_proposal_status(node_port, channel, proposal_id)`

Get proposal status (open, closed).

```bash
STATUS=$(get_proposal_status 8003 "dev_ui" "$PROP_ID")
echo "Proposal status: $STATUS"
```

### `get_proposal_outcome(node_port, channel, proposal_id)`

Get calculated outcome (approved, rejected, pending).

```bash
OUTCOME=$(get_proposal_outcome 8001 "dev_ui" "$PROP_ID")
echo "Proposal outcome: $OUTCOME"
```

---

## Manual Testing

### Economy Test (Manual Steps)

```bash
# 1. Start network
docker-compose up --build -d rendezvous node-1 node-2 node-3
sleep 20

# 2. Get node IDs
NODE_1_ID=$(curl -s http://localhost:8001/state | jq -r '.local.id')
NODE_2_ID=$(curl -s http://localhost:8002/state | jq -r '.local.id')

# 3. Check initial balances
curl http://localhost:8001/state | jq '.global.nodes[] | {id: .id[:16], balance}'

# 4. Create task with reward (Node 1)
TASK_ID=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Reward","reward":50}' | jq -r '.id')

# 5. Wait and check frozen SP
sleep 20
curl http://localhost:8002/state | jq --arg nid "$NODE_1_ID" \
  '.global.nodes[$nid] | {id: .id[:16], balance: .balance}'
# Expected: balance = 950

# 6. Complete task (Node 2)
curl -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui"
sleep 5
curl -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui"
sleep 5
curl -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui"
sleep 25

# 7. Verify final balances (must be identical on all nodes!)
for port in 8001 8002 8003; do
  echo "=== Node :$port ==="
  curl -s http://localhost:$port/state | jq \
    --arg n1 "$NODE_1_ID" --arg n2 "$NODE_2_ID" \
    '.global.nodes | {node1: .[$n1].balance, node2: .[$n2].balance}'
done
```

### Governance Test (Manual Steps)

```bash
# 1. Build reputation (Node 1 completes 2 tasks)
for i in 1 2; do
  TASK=$(curl -s -X POST "http://localhost:8001/tasks?channel=dev_ui" \
    -d "{\"title\":\"Rep Task $i\"}" | jq -r '.id')
  sleep 3
  curl -X POST "http://localhost:8001/tasks/$TASK/claim?channel=dev_ui"
  sleep 3
  curl -X POST "http://localhost:8001/tasks/$TASK/progress?channel=dev_ui"
  sleep 3
  curl -X POST "http://localhost:8001/tasks/$TASK/complete?channel=dev_ui"
  echo "Task $i completed"
done

sleep 25

# 2. Check reputation
curl http://localhost:8002/state | jq --arg nid "$NODE_1_ID" \
  '.global.nodes[$nid] | {id: .id[:16], reputation: .reputation}'
# Expected: reputation = 20

# 3. Create proposal (Node 3)
PROP_ID=$(curl -s -X POST "http://localhost:8003/proposals?channel=dev_ui" \
  -d '{"title":"Test Weighted Vote","description":"Testing"}' | jq -r '.id')

sleep 10

# 4. Vote
curl -X POST "http://localhost:8001/proposals/$PROP_ID/vote?channel=dev_ui" -d '{"vote":"rejection"}'
curl -X POST "http://localhost:8002/proposals/$PROP_ID/vote?channel=dev_ui" -d '{"vote":"approval"}'
curl -X POST "http://localhost:8003/proposals/$PROP_ID/vote?channel=dev_ui" -d '{"vote":"approval"}'

sleep 15

# 5. Close and check outcome
curl -X POST "http://localhost:8001/proposals/$PROP_ID/close?channel=dev_ui"
sleep 15

curl http://localhost:8002/proposals?channel=dev_ui | jq '.[0] | {outcome, votes}'
# Expected: outcome = "rejected" (despite 2 YES vs 1 NO)
```

---

## Troubleshooting

### Test Fails: State Not Converged

**Problem**: Nodes don't see each other after 20 seconds  
**Solutions**:
- Increase wait time (slow network)
- Check Docker networking: `docker network inspect synapse-ng_synapse-net`
- Check mDNS discovery: `docker logs node-1 | grep mDNS`

### Test Fails: Weighted Vote Incorrect

**Problem**: Proposal outcome doesn't match expected  
**Debug**:
```bash
# Check votes and weights
curl http://localhost:8001/proposals?channel=dev_ui | jq '.[0].votes'

# Manually calculate:
# weight = 1.0 + log2(reputation + 1)
```

**Common Issues**:
- Reputation not propagated (wait longer)
- Vote timestamps out of order (clock sync)

### Test Fails: Balance Divergence

**Problem**: Different nodes show different balances  
**This is CRITICAL** - indicates economic bug

**Debug**:
```bash
# Check transaction history
curl http://localhost:8001/state | jq '.channels["dev_ui"].transactions'

# Compare on all nodes
for port in 8001 8002 8003; do
  echo "=== Node :$port ==="
  curl http://localhost:$port/state | jq '.global.nodes | 
    to_entries | map({id: .value.id[:16], balance: .value.balance})'
done
```

**Root Causes**:
- CRDT merge conflict (check logs)
- Task status race condition
- Network partition during transaction

### Test Suite Hangs

**Problem**: Test gets stuck waiting  
**Solutions**:
```bash
# Check if all containers running
docker-compose ps

# Check logs for errors
docker-compose logs node-1

# Kill and restart
docker-compose down
./test_suite.sh
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Synapse-NG Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Run base tests
        run: ./test_suite.sh base
      
      - name: Run governance tests
        run: ./test_suite.sh governance
      
      - name: Run economy tests
        run: ./test_suite.sh economy
      
      - name: Cleanup
        if: always()
        run: docker-compose down -v
```

---

## Related Documentation

- [Governance System](GOVERNANCE_SYSTEM.md) - Weighted voting details
- [Autonomous Organism](AUTONOMOUS_ORGANISM.md) - Economy system
- [Getting Started](GETTING_STARTED.md) - Setup guide

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Status**: ✅ Production Ready
