# Network Operations - Executive System Documentation

## Overview

Synapse-NG implements a complete **executive operations system** that allows the network to evolve itself through two-tier governance. This document describes the complete flow from proposal creation to network modification.

## Architecture

### Three-Layer Governance

1. **Community Layer (CRDT Voting)**
   - All nodes can create and vote on proposals
   - Weighted voting based on reputation
   - Proposals are approved by community consensus

2. **Council Layer (Validator Set)**
   - Top N nodes by reputation form the validator set
   - Validators must ratify network_operation proposals
   - Requires majority consensus ((N/2) + 1 votes)

3. **Execution Layer (Command Processor)**
   - Ratified commands are added to an append-only execution_log
   - All nodes execute commands deterministically
   - Idempotent execution (nodes can restart and resume)

### Data Structures

```json
{
  "global": {
    "execution_log": [
      {
        "command_id": "uuid",
        "proposal_id": "original_proposal_id",
        "operation": "split_channel",
        "params": {...},
        "ratified_at": "2025-10-02T10:30:00Z",
        "ratified_by": ["validator_1", "validator_2", ...]
      }
    ],
    "ratification_votes": {
      "proposal_id": {
        "validator_1": true,
        "validator_2": true
      }
    },
    "pending_operations": [
      {
        "proposal_id": "...",
        "operation": "split_channel",
        "params": {...},
        "status": "awaiting_council"
      }
    ],
    "validator_set": ["node_id_1", "node_id_2", ...],
    "last_executed_command_index": 5
  }
}
```

## Complete Flow

### Phase 1: Community Proposal

A node creates a `network_operation` proposal to modify the network structure.

```bash
# Create a network_operation proposal
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Split general channel into backend and frontend",
    "description": "Our general channel has grown too large. We need to split it based on tags.",
    "proposal_type": "network_operation",
    "params": {
      "operation": "split_channel",
      "target_channel": "general",
      "new_channels": ["backend", "frontend"],
      "split_logic": "by_tag",
      "split_params": {
        "backend": ["api", "database", "server"],
        "frontend": ["ui", "ux", "design"]
      }
    }
  }'
```

**Response:**
```json
{
  "id": "prop_abc123",
  "title": "Split general channel into backend and frontend",
  "proposal_type": "network_operation",
  "status": "open",
  "proposer": "node_xyz",
  "created_at": "2025-10-02T10:00:00Z",
  "votes": {}
}
```

### Phase 2: Community Voting

Nodes vote on the proposal (weighted by reputation).

```bash
# Node 1 votes YES
curl -X POST "http://localhost:8001/proposals/prop_abc123/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

# Node 2 votes YES
curl -X POST "http://localhost:8002/proposals/prop_abc123/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

# Node 3 votes NO
curl -X POST "http://localhost:8003/proposals/prop_abc123/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "no"}'
```

### Phase 3: Close Voting

Any node can close the proposal to calculate the outcome.

```bash
# Close the proposal (calculate outcome)
curl -X POST "http://localhost:8001/proposals/prop_abc123/close?channel=global"
```

**Response (if approved):**
```json
{
  "id": "prop_abc123",
  "status": "pending_ratification",
  "outcome": "approved",
  "vote_details": {
    "yes_weight": 15.4,
    "no_weight": 7.2,
    "outcome": "approved"
  },
  "pending_since": "2025-10-02T10:15:00Z"
}
```

**Key Point:** The proposal is now in `pending_ratification` status and **will NOT be executed** until the validator set ratifies it.

### Phase 4: Council Ratification

Validators (top N nodes by reputation) must ratify the proposal.

```bash
# Validator 1 ratifies
curl -X POST "http://localhost:8001/governance/ratify/prop_abc123?channel=global"

# Validator 2 ratifies
curl -X POST "http://localhost:8002/governance/ratify/prop_abc123?channel=global"

# Validator 3 ratifies
curl -X POST "http://localhost:8003/governance/ratify/prop_abc123?channel=global"

# Validator 4 ratifies (assuming validator_set_size=7, needs 4 votes for majority)
curl -X POST "http://localhost:8004/governance/ratify/prop_abc123?channel=global"
```

**Response (before majority):**
```json
{
  "status": "pending",
  "proposal_id": "prop_abc123",
  "current_votes": 3,
  "required_votes": 4,
  "validators_voted": ["node_1", "node_2", "node_3"],
  "validators_pending": ["node_4", "node_5", "node_6", "node_7"]
}
```

**Response (after majority reached):**
```json
{
  "status": "ratified",
  "proposal_id": "prop_abc123",
  "command_id": "cmd_xyz789",
  "operation": "split_channel",
  "params": {
    "target_channel": "general",
    "new_channels": ["backend", "frontend"],
    "split_logic": "by_tag",
    "split_params": {...}
  },
  "ratified_by": ["node_1", "node_2", "node_3", "node_4"],
  "execution_log_index": 5
}
```

**Key Point:** The command is now in the `execution_log` and will be executed by all nodes.

### Phase 5: Automatic Execution

The `command_processor_task` (running on every node) automatically detects the new command and executes it.

```
🚀 Esecuzione comando 5: split_channel (ID: cmd_xyz789...)
🔀 Esecuzione split_channel: general → [backend, frontend]
   Logica: by_tag, Params: {...}
   ✅ Canale 'backend' creato
   ✅ Canale 'frontend' creato
✅ Split completato: general → [backend, frontend]
   Task spostati: {'backend': 12, 'frontend': 8}
   Proposte spostate: {'backend': 3, 'frontend': 2}
   📝 Proposta prop_abc123... marcata come executed
   ✅ Comando eseguito con successo
```

### Phase 6: Verification

Check that the operation was executed successfully.

```bash
# Check the execution log
curl http://localhost:8001/state | jq '.global.execution_log'

# Check the proposal status
curl "http://localhost:8001/proposals/prop_abc123/details?channel=global" | jq '.status, .execution_result'

# Check that new channels exist
curl http://localhost:8001/state | jq 'keys'

# Verify tasks were moved
curl http://localhost:8001/state | jq '.backend.tasks | length'
curl http://localhost:8001/state | jq '.frontend.tasks | length'
```

**Expected Output:**
```json
// Execution log
[
  {
    "command_id": "cmd_xyz789",
    "proposal_id": "prop_abc123",
    "operation": "split_channel",
    "params": {...},
    "ratified_at": "2025-10-02T10:20:00Z",
    "ratified_by": ["node_1", "node_2", "node_3", "node_4"]
  }
]

// Proposal status
"executed"
{
  "success": true,
  "target_channel": "general",
  "new_channels": ["backend", "frontend"],
  "tasks_moved": {"backend": 12, "frontend": 8},
  "proposals_moved": {"backend": 3, "frontend": 2}
}

// Channels
["global", "general", "backend", "frontend"]

// Task counts
12  // backend tasks
8   // frontend tasks
```

## Supported Operations

### 1. split_channel

Divides a channel into multiple new channels based on a splitting logic.

**Parameters:**
```json
{
  "operation": "split_channel",
  "target_channel": "general",
  "new_channels": ["backend", "frontend"],
  "split_logic": "by_tag",  // or "by_title_prefix"
  "split_params": {
    "backend": ["api", "database"],
    "frontend": ["ui", "ux"]
  }
}
```

**Splitting Logic:**

- **by_tag**: Moves tasks/proposals based on their tags
  ```json
  "split_params": {
    "backend": ["api", "database", "server"],
    "frontend": ["ui", "ux", "design"]
  }
  ```
  Tasks with tags `["api", "bugfix"]` → moved to `backend`
  Tasks with tags `["ui", "feature"]` → moved to `frontend`

- **by_title_prefix**: Moves tasks/proposals based on title prefix
  ```json
  "split_params": {
    "backend": ["API:", "DB:", "Server:"],
    "frontend": ["UI:", "UX:", "Design:"]
  }
  ```
  Tasks titled "API: Fix authentication" → moved to `backend`
  Tasks titled "UI: Update dashboard" → moved to `frontend`

**Result:**
- New channels are created
- Tasks/proposals are moved to appropriate channels
- Original channel is marked as `archived`
- Original channel retains metadata: `split_into`, `archived_at`

### 2. merge_channels

Combines multiple channels into a single channel.

**Parameters:**
```json
{
  "operation": "merge_channels",
  "source_channels": ["backend", "frontend"],
  "target_channel": "development",
  "conflict_resolution": "keep_all"
}
```

**Conflict Resolution:**
- **keep_all**: Keeps all tasks/proposals (IDs are unique)

**Result:**
- All tasks/proposals from source channels are moved to target
- Source channels are marked as `archived`
- Source channels retain metadata: `merged_into`, `archived_at`

## Security and Consensus

### Validator Authentication

Currently, the system uses `NODE_ID` for validator identification. In production, this should be enhanced with:

1. **Cryptographic Signatures**: Validators sign their ratification votes
2. **Timestamp Verification**: Prevent replay attacks
3. **Rate Limiting**: Prevent spam ratifications

### Deterministic Execution

All execution functions are **deterministic**:
- Same input state + same command → same output state on ALL nodes
- No randomness, no external API calls, no non-deterministic operations
- Guaranteed convergence across the network

### CRDT Properties

The execution_log is an **append-only CRDT**:
- Commands are never deleted or modified
- Commands are deduplicated by `command_id`
- Commands are sorted by `ratified_at` for deterministic ordering
- Gossip propagates the log to all nodes

### Idempotent Execution

The command processor is **idempotent**:
- Each node tracks `last_executed_command_index`
- Commands are executed exactly once per node
- Nodes can restart and resume from where they left off
- No side effects from re-execution

## Monitoring and Debugging

### Check Validator Set

```bash
curl http://localhost:8001/state | jq '.global.validator_set'
```

### Check Pending Operations

```bash
curl http://localhost:8001/state | jq '.global.pending_operations'
```

### Check Execution Log

```bash
curl http://localhost:8001/state | jq '.global.execution_log'
```

### Check Ratification Status

```bash
curl http://localhost:8001/state | jq '.global.ratification_votes'
```

### Check Proposal Details

```bash
curl "http://localhost:8001/proposals/PROPOSAL_ID/details?channel=global" | jq
```

## Error Handling

### Proposal Rejected by Community

If `no_weight > yes_weight`, the proposal is marked as `rejected` and **will not** proceed to ratification.

```json
{
  "status": "closed",
  "outcome": "rejected",
  "vote_details": {
    "yes_weight": 7.2,
    "no_weight": 15.4,
    "outcome": "rejected"
  }
}
```

### Insufficient Validator Votes

If validators don't ratify (or not enough validators are online), the proposal stays in `pending_ratification` indefinitely.

**Solution:** Implement a timeout mechanism or allow proposal cancellation.

### Execution Failure

If command execution fails (e.g., target channel doesn't exist), the error is logged in the proposal's `execution_result`:

```json
{
  "status": "executed",
  "execution_result": {
    "success": false,
    "error": "Canale 'non_existent' non trovato"
  }
}
```

The execution_log still contains the command, but the network state is **not modified**.

## Best Practices

### 1. Test on Small Channels First

Before splitting/merging large channels, test the logic on small test channels.

### 2. Clearly Define Split Logic

Use descriptive tags or prefixes to avoid ambiguity:
- ✅ Good: `["backend:api", "backend:db", "frontend:ui"]`
- ❌ Bad: `["bug", "feature"]` (too vague)

### 3. Communicate with Community

Before creating a network_operation proposal, discuss with the community to ensure alignment.

### 4. Monitor Validator Health

Ensure validators are online and responsive. If validators are offline, ratification will stall.

### 5. Backup Before Operations

While operations are deterministic, it's good practice to backup the state before major operations.

## Future Enhancements

### 1. Automatic Rollback

If execution fails, automatically rollback to the previous state.

### 2. Operation Preview

Allow nodes to simulate an operation before voting.

### 3. Multi-Step Operations

Chain multiple operations together (e.g., split then merge).

### 4. Dynamic Validator Set

Allow validators to be elected/removed dynamically based on reputation.

### 5. Operation Cancellation

Allow proposers to cancel operations before execution.

## Conclusion

Synapse-NG is now a **self-modifying autonomous organism**. The network can:

1. **Propose changes** (any node)
2. **Vote democratically** (weighted by reputation)
3. **Ratify critically** (validator consensus)
4. **Execute deterministically** (all nodes in sync)

This is true **digital organism auto-evolution**. 🧬✨

---

**Versione:** 1.0  
**Data:** 2 Ottobre 2025  
**Autore:** Synapse-NG Development Team
