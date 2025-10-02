# 🧬 Autonomous Organism Implementation Plan

## Overview

This document details the implementation of three critical systems that transform Synapse-NG from a distributed network into a truly autonomous, self-governing, and self-sustaining organism:

1. **Network Metabolism** - Treasury & Transaction Taxes
2. **Immune System** - Peer Scoring & Mesh Optimization
3. **Self-Evolution** - Executable Governance Proposals

---

## Phase 1: Network Metabolism (Treasury & Taxes) ✅ IN PROGRESS

### Objective
Create a common fund (treasury) for each channel, financed by micro-taxes, to incentivize community-serving tasks.

### Implementation Status

#### ✅ Completed
1. **Global Configuration System**
   - Added `DEFAULT_CONFIG` with configurable parameters
   - `transaction_tax_percentage`: 0.02 (2% tax)
   - `task_completion_reputation_reward`: 10
   - `proposal_vote_reputation_reward`: 1
   - `vote_weight_log_base`: 2
   - `initial_balance_sp`: 1000
   - `treasury_initial_balance`: 0

2. **Treasury Data Structure**
   - Each channel now has `treasury_balance: 0` field
   - Calculated determin

istically from transaction history

3. **Transaction Tax Logic**
   - `calculate_balances()` updated to apply tax on completion
   - Assignee receives: `reward - (reward * tax_rate)`
   - Example: 100 SP reward → 98 SP to assignee, 2 SP to treasury

4. **Treasury Calculation**
   - New `calculate_treasuries()` function
   - Tracks tax income from completed tasks
   - Handles treasury-funded task expenses

#### 🚧 In Progress
5. **Treasury-Funded Tasks**
   - Modify task creation to allow `creator = "channel:channel_id"`
   - Validation logic to check treasury balance
   - Update gossip to handle channel-owned tasks

6. **API Endpoints**
   ```python
   # Get treasury balance
   GET /treasury/{channel_id}

   # Create community-funded task
   POST /tasks?channel=CHANNEL_ID
   {
       "title": "Fix critical bug",
       "reward": 50,
       "funded_by": "treasury"  # Special flag
   }
   ```

### Example Workflow

```bash
# 1. Check treasury balance
curl http://localhost:8001/treasury/dev_ui

# 2. Node A creates task with 100 SP reward
curl -X POST http://localhost:8001/tasks?channel=dev_ui \
  -H "Content-Type: application/json" \
  -d '{"title": "Implement feature", "reward": 100}'

# 3. Node B completes the task
curl -X POST http://localhost:8001/tasks/{task_id}/complete?channel=dev_ui

# 4. Final state:
# - Node A: balance -= 100 SP
# - Node B: balance += 98 SP (100 - 2% tax)
# - Treasury: += 2 SP

# 5. Community creates treasury-funded task
curl -X POST http://localhost:8001/tasks?channel=dev_ui \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix security issue",
    "reward": 50,
    "funded_by": "treasury"
  }'
# Treasury: -= 50 SP (frozen)
# When completed: assignee gets 49 SP, treasury gets 1 SP back
```

---

## Phase 3: Self-Evolution (Executable Proposals) ✅ IN PROGRESS

### Objective
Enable the network to modify its own fundamental rules through governance (DAO capability).

### Implementation Status

#### ✅ Completed
1. **Extended Proposal Model**
   ```python
   class CreateProposalPayload(BaseModel):
       title: str
       description: str = ""
       proposal_type: str = "generic"  # "generic", "config_change"
       params: dict = {}  # For config_change: {"key": "value"}
   ```

2. **Configuration in Network State**
   ```python
   network_state["global"]["config"] = {
       "task_completion_reputation_reward": 10,
       "transaction_tax_percentage": 0.02,
       ...
   }
   ```

3. **Dynamic Configuration Reading**
   - All functions now read from `network_state["global"]["config"]`
   - No more hardcoded values
   - Configuration version tracking

#### 🚧 In Progress
4. **Config Change Proposal Execution**
   ```python
   @app.post("/proposals/{proposal_id}/close")
   async def close_proposal(...):
       # After calculating outcome
       if outcome["outcome"] == "approved":
           if proposal["proposal_type"] == "config_change":
               # Validate params
               key = proposal["params"].get("key")
               value = proposal["params"].get("value")

               # Validate key exists and type is correct
               if key in network_state["global"]["config"]:
                   old_value = network_state["global"]["config"][key]
                   if type(value) == type(old_value):
                       # Apply change
                       network_state["global"]["config"][key] = value
                       network_state["global"]["config_version"] += 1
                       network_state["global"]["config_updated_at"] = now()

                       proposal["status"] = "executed"
                       proposal["execution_result"] = {
                           "success": True,
                           "old_value": old_value,
                           "new_value": value
                       }
   ```

### Example Governance Workflow

```bash
# 1. Node proposes to increase task reward reputation
curl -X POST http://localhost:8001/proposals?channel=global \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Increase task completion reward to 15",
    "description": "We need to incentivize more task completion",
    "proposal_type": "config_change",
    "params": {
      "key": "task_completion_reputation_reward",
      "value": 15
    }
  }'

# 2. Nodes vote (weighted by reputation)
curl -X POST http://localhost:8001/proposals/{proposal_id}/vote?channel=global \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

# 3. Close voting and auto-execute if approved
curl -X POST http://localhost:8001/proposals/{proposal_id}/close?channel=global

# 4. If approved with weighted majority:
# - Config changes: task_completion_reputation_reward: 10 → 15
# - All nodes apply new config immediately
# - Proposal marked as "executed"
# - Future task completions give +15 reputation instead of +10
```

### Governable Parameters

```python
GOVERNABLE_PARAMS = {
    "task_completion_reputation_reward": {
        "type": "int",
        "min": 1,
        "max": 100,
        "description": "Reputation reward for completing a task"
    },
    "proposal_vote_reputation_reward": {
        "type": "int",
        "min": 1,
        "max": 10,
        "description": "Reputation reward for voting on proposals"
    },
    "transaction_tax_percentage": {
        "type": "float",
        "min": 0.0,
        "max": 0.1,
        "description": "Tax rate on task rewards (0.02 = 2%)"
    },
    "vote_weight_log_base": {
        "type": "int",
        "min": 2,
        "max": 10,
        "description": "Log base for vote weight calculation"
    }
}
```

---

## Phase 2: Immune System (Peer Scoring) 🔮 FUTURE

### Objective
Make the network aware of connection quality and capable of optimizing its mesh topology.

### Planned Implementation

1. **Peer Scoring System**
   ```python
   # In WebRTCConnectionManager
   peer_scores = {}  # {peer_id: score}

   def calculate_peer_score(peer_id):
       reputation = get_reputation(peer_id)
       stability = connection_uptime[peer_id] / max_uptime
       latency = measure_latency(peer_id)

       # Configurable weights
       w1, w2, w3 = 0.4, 0.3, 0.3

       score = (w1 * normalize(reputation)) + \
               (w2 * stability) - \
               (w3 * normalize(latency))

       return score
   ```

2. **Mesh Optimization (Churn)**
   ```python
   async def optimize_mesh():
       while True:
           scores = {p: calculate_peer_score(p) for p in peers}

           # Protect top N peers
           top_peers = sorted(scores, key=scores.get, reverse=True)[:5]

           # Drop worst peer if over capacity
           if len(peers) > MAX_PEERS:
               worst = min(scores, key=scores.get)
               if worst not in top_peers:
                   disconnect(worst)

                   # Try new peer
                   candidate = discover_new_peer()
                   if candidate:
                       connect(candidate)

           await asyncio.sleep(60)
   ```

3. **UI Visualization**
   - WebRTC links colored by health:
     - Green (thick): High score (>0.7)
     - Yellow (medium): Medium score (0.4-0.7)
     - Red (thin, dashed): Low score (<0.4)
   - Node inspector shows peer scores

---

## Testing Strategy

### Treasury Tests
```bash
# Test 1: Tax collection
./test_suite.sh economy

# Expected:
# - Task with 100 SP reward
# - Assignee gets 98 SP
# - Treasury gets 2 SP

# Test 2: Treasury-funded task
# - Treasury starts with 100 SP (from previous taxes)
# - Create task funded_by: treasury (50 SP)
# - Treasury: 100 - 50 = 50 SP (frozen)
# - Task completed
# - Assignee: +49 SP
# - Treasury: 50 + 1 SP = 51 SP (tax returned)
```

### Governance Tests
```bash
# Test 1: Config change proposal
./test_governance_config.sh

# Expected:
# - Proposal to change tax from 2% to 3%
# - Voting with weighted votes
# - If approved: config updates automatically
# - Future tasks use 3% tax
# - All nodes agree on new config

# Test 2: Determinism
# - All nodes must have identical config
# - Config version must increment atomically
# - No config conflicts or forks
```

---

## API Summary

### Treasury Endpoints
```bash
GET /treasury/{channel_id}                # Get treasury balance
GET /treasuries                            # Get all treasury balances
POST /tasks?funded_by=treasury            # Create treasury-funded task
```

### Governance Endpoints
```bash
POST /proposals?channel=global            # Create config_change proposal
GET /config                                # Get current network config
GET /config/history                        # Get config change history
```

### Future: Peer Management
```bash
GET /peers/scores                          # Get peer health scores
POST /peers/{peer_id}/disconnect          # Manual disconnect
GET /mesh/health                           # Overall mesh health
```

---

## Implementation Priority

### Sprint 1 (Current) ✅
- [x] Global config system
- [x] Treasury data structure
- [x] Tax calculation
- [ ] Treasury-funded tasks API
- [ ] Config change proposal execution

### Sprint 2
- [ ] Treasury UI visualization
- [ ] Governance UI for config changes
- [ ] Comprehensive tests for economy
- [ ] Documentation and examples

### Sprint 3 (Future)
- [ ] Peer scoring system
- [ ] Mesh optimization algorithm
- [ ] Health visualization in UI
- [ ] Advanced consensus (if needed)

---

## Success Criteria

### Phase 1: Network Metabolism ✅
- ✅ Treasury balance calculated deterministically
- ✅ Taxes collected on all task completions
- 🔄 Community can create treasury-funded tasks
- 🔄 All nodes agree on treasury state
- ⏳ UI shows treasury and tax flows

### Phase 3: Self-Evolution ✅
- ✅ Configuration stored in network state
- ✅ All code reads from dynamic config
- 🔄 Config change proposals auto-execute when approved
- 🔄 All nodes converge to same config version
- ⏳ UI for creating executable proposals

### Phase 2: Immune System ⏳
- ⏳ Peer scores calculated accurately
- ⏳ Mesh optimizes automatically (keeps best peers)
- ⏳ Network self-heals from bad connections
- ⏳ UI visualizes network health

---

## Next Steps

1. **Complete Treasury Implementation**
   - Add validation for treasury-funded tasks
   - Implement GET /treasury endpoints
   - Update gossip protocol for channel-owned tasks

2. **Complete Governance Execution**
   - Add config change validation
   - Implement auto-execution logic
   - Add execution_result to proposal state

3. **Testing**
   - Write comprehensive economy tests
   - Write governance config change tests
   - Verify determinism across all nodes

4. **Documentation**
   - Update README with treasury system
   - Create governance cookbook
   - Document all governable parameters

---

**Synapse-NG** - An organism that feeds itself, governs itself, and evolves itself. 🧬✨
