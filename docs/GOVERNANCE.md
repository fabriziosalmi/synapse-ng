# 🗳️ Governance System: The Democratic Nervous System

**Complete Governance Guide - Reputation v2, Contextual Voting, and Executable Commands**

Version: 2.0 (Evolved)  
Last Updated: October 2025  
Status: ✅ Production-Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Two-Tier Architecture](#two-tier-architecture)
3. [Reputation System v2](#reputation-system-v2)
4. [Contextual Voting](#contextual-voting)
5. [Proposal Types](#proposal-types)
6. [Executable Commands](#executable-commands)
7. [Zero-Knowledge Voting](#zero-knowledge-voting)
8. [Complete Workflows](#complete-workflows)
9. [API Reference](#api-reference)

---

## 🎯 Overview

Synapse-NG implements a **sophisticated democratic governance system** that combines:

1. **Community Voting** (Tier 1) - All nodes participate with weighted votes
2. **Validator Ratification** (Tier 2) - Top nodes ensure network stability
3. **Specialized Reputation** - Tag-based expertise tracking
4. **Contextual Vote Weighting** - Experts have more influence in their domains
5. **Executable Proposals** - Network can modify itself autonomously

**Core Innovation**: Your voting power depends not just on how much you've contributed, but on **what** you've contributed. A Python expert's vote on a security proposal carries less weight than a security expert's vote—this is **meritocratic specialization**.

---

## 🏗️ Two-Tier Architecture

### Tier 1: Community Voting (CRDT-Based)

**All nodes can:**
- Create proposals
- Vote on any proposal
- Have vote weight determined by reputation

**Mechanism**:
```python
# Each node calculates outcome independently
yes_weight = sum(vote_weight(node) for node in voters if vote == "yes")
no_weight = sum(vote_weight(node) for node in voters if vote == "no")

outcome = "approved" if yes_weight > no_weight else "rejected"
```

**CRDT Properties**:
- Last-Write-Wins on vote changes
- Automatic conflict resolution (newest vote wins)
- Guaranteed eventual consistency

**Threshold**: Configurable (default 60% yes_weight required)

---

### Tier 2: Validator Ratification (Raft-Based)

**For Critical Proposals** (`network_operation` type):

```python
validator_set = top_N_nodes_by_total_reputation(N=7)

def ratify_proposal(proposal_id):
    # Only validators can ratify
    if caller not in validator_set:
        return 403
    
    # Record vote
    ratification_votes[proposal_id][caller] = True
    
    # Check majority
    required_votes = (len(validator_set) // 2) + 1
    if len(ratification_votes[proposal_id]) >= required_votes:
        # Majority reached - execute!
        append_to_execution_log(proposal)
        execute_command_on_all_nodes(proposal)
```

**Validator Selection**:
- Dynamic, recalculated periodically
- Based on `_total` reputation (sum of all tag specializations)
- Ensures experienced nodes have final say on critical operations

---

## 🧬 Reputation System v2

### Evolution from v1 to v2

**v1 (Simple)**:
```python
reputation: int = 100
```

**v2 (Specialized)**:
```json
{
  "_total": 150,
  "_last_updated": "2025-10-23T10:00:00Z",
  "tags": {
    "python": 60,
    "security": 50,
    "testing": 30,
    "devops": 10
  }
}
```

### How Reputation is Earned

**Task Completion**:
```python
# When a task with tags=["python", "security"] is completed with reward=10
reputation["tags"]["python"] += 10
reputation["tags"]["security"] += 10
reputation["_total"] += 20  # Sum of all tags
reputation["_last_updated"] = now()
```

**Voting Participation**:
```python
# When you vote on a proposal
reputation["_total"] += 1
reputation["_last_updated"] = now()
```

### Time Decay Mechanism

**Purpose**: Incentivize continuous activity, prevent stagnation

**Algorithm**:
```python
# Runs every 24 hours
async def reputation_decay_loop():
    while True:
        await asyncio.sleep(86400)  # 24h
        
        for node in all_nodes:
            for tag, value in node.reputation["tags"].items():
                new_value = value * 0.99  # -1% daily
                
                if new_value < 0.1:
                    # Remove insignificant tags
                    del node.reputation["tags"][tag]
                else:
                    node.reputation["tags"][tag] = new_value
            
            # Recalculate total
            node.reputation["_total"] = sum(node.reputation["tags"].values())
```

**Impact Over Time**:

| Days Inactive | Reputation Remaining |
|--------------|---------------------|
| 0 | 100% |
| 7 | ~93% |
| 30 | ~74% |
| 90 | ~41% |
| 180 | ~16% |

**Message**: Stay active or lose influence!

---

## 🎯 Contextual Voting

### The Core Innovation

**Traditional weighted voting**:
```
vote_weight = 1 + log2(total_reputation + 1)
```

**Contextual weighted voting** (v2):
```python
def calculate_contextual_vote_weight(reputation, proposal_tags):
    # Base weight from total contributions
    base_weight = 1.0 + math.log2(reputation["_total"] + 1)
    
    # Bonus from expertise in proposal's domain
    specialization_score = sum(
        reputation["tags"].get(tag, 0)
        for tag in proposal_tags
    )
    bonus_weight = math.log2(specialization_score + 1)
    
    return base_weight + bonus_weight
```

### Example Scenario

**Voter Profile**:
```json
{
  "_total": 1023,
  "tags": {
    "security": 500,
    "python": 300,
    "testing": 200,
    "devops": 23
  }
}
```

**Proposal A** - Security Upgrade (`tags: ["security", "cryptography"]`):
```
base_weight = 1 + log2(1024) = 11.0
specialization = 500 (security) + 0 (cryptography) = 500
bonus_weight = log2(501) ≈ 8.97
total_weight = 11.0 + 8.97 = 19.97 ✨ EXPERT INFLUENCE
```

**Proposal B** - UI Redesign (`tags: ["frontend", "design"]`):
```
base_weight = 11.0
specialization = 0 + 0 = 0
bonus_weight = log2(1) = 0
total_weight = 11.0 + 0 = 11.0 ⚖️ STANDARD INFLUENCE
```

**Result**: Voter has **81% more influence** on security proposals than UI proposals!

### Benefits

✅ **Meritocratic Specialization** - Experts decide in their domains  
✅ **Reduced Bad Decisions** - Non-experts can't override domain experts  
✅ **Incentive to Specialize** - Building expertise increases influence  
✅ **Protection from Generalists** - Can't game system with shallow knowledge  

---

## 📜 Proposal Types

### 1. `generic`

**Purpose**: General proposals without automatic execution

**Fields**:
```json
{
  "title": "Should we adopt coding standard X?",
  "description": "Detailed rationale...",
  "proposal_type": "generic",
  "tags": ["coding-standards", "governance"]
}
```

**Execution**: None (advisory only)

---

### 2. `config_change`

**Purpose**: Modify network configuration parameters

**Fields**:
```json
{
  "title": "Increase task completion reward to 15 SP",
  "proposal_type": "config_change",
  "tags": ["economy", "rewards"],
  "params": {
    "key": "task_completion_reputation_reward",
    "value": 15
  }
}
```

**Execution**: Automatic upon approval
```python
network_state["global"]["config"][key] = value
```

**Configurable Parameters**:
- `task_completion_reputation_reward`
- `transaction_tax_percentage`
- `vote_weight_log_base`
- `initial_balance_sp`
- `validator_set_size`

---

### 3. `network_operation`

**Purpose**: Execute structural changes to the network

**Requires**: Validator ratification (Tier 2)

**Supported Operations**:

#### a) `split_channel`

```json
{
  "title": "Split general into backend/frontend",
  "proposal_type": "network_operation",
  "tags": ["channels", "organization"],
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
}
```

#### b) `merge_channels`

```json
{
  "params": {
    "operation": "merge_channels",
    "source_channels": ["backend", "frontend"],
    "target_channel": "development"
  }
}
```

#### c) `acquire_common_tool` 🆕

```json
{
  "params": {
    "operation": "acquire_common_tool",
    "channel": "dev",
    "tool_id": "geolocation_api",
    "description": "MaxMind GeoIP2 for user analytics",
    "type": "api_key",
    "monthly_cost_sp": 150,
    "credentials_to_encrypt": "YOUR_API_KEY_HERE"
  }
}
```

**Execution**: Automatic upon ratification
- Validates treasury has sufficient funds
- Encrypts credentials (AESGCM)
- Adds tool to channel
- Deducts first month payment

#### d) `deprecate_common_tool`

```json
{
  "params": {
    "operation": "deprecate_common_tool",
    "channel": "dev",
    "tool_id": "old_api"
  }
}
```

---

### 4. `code_upgrade` (Self-Upgrade)

**Purpose**: Autonomous code evolution via WASM

**Fields**:
```json
{
  "title": "Optimize consensus algorithm",
  "proposal_type": "code_upgrade",
  "tags": ["performance", "consensus"],
  "params": {
    "package_url": "ipfs://Qm...",
    "package_hash": "sha256:abc123...",
    "version": "1.2.0",
    "description": "Optimized Raft implementation",
    "breaking": false
  }
}
```

**Execution**: After validator ratification
1. Download WASM package
2. Verify SHA256 hash
3. Test in sandbox
4. Execute upgrade
5. Rollback on failure

---

## ⚙️ Executable Commands

### Command Execution Flow

```
1. PROPOSAL APPROVED (Tier 1)
   └─> Status: "approved"

2. IF network_operation:
   └─> Status: "pending_ratification"
   
3. VALIDATORS RATIFY
   └─> Votes: {validator_1: true, validator_2: true, ...}
   
4. MAJORITY REACHED
   ├─> Status: "ratified"
   ├─> Command added to execution_log (CRDT)
   └─> Trigger: command_processor_task()

5. EXECUTE ON ALL NODES
   ├─> Read next command from execution_log
   ├─> Dispatch to handler (split/merge/acquire/etc.)
   ├─> Execute deterministically
   ├─> Update last_executed_command_index
   └─> Save state

6. PROPAGATE STATE
   └─> Gossip updated state to all nodes
```

### Execution Log Structure

```json
{
  "global": {
    "execution_log": [
      {
        "command_id": "cmd_abc123",
        "proposal_id": "prop_xyz789",
        "operation": "acquire_common_tool",
        "params": {
          "channel": "dev",
          "tool_id": "sendgrid_api",
          ...
        },
        "ratified_at": "2025-10-23T15:30:00Z",
        "ratified_by": ["node_1", "node_2", "node_3", "node_4"],
        "executed_at": "2025-10-23T15:30:05Z",
        "execution_result": {
          "success": true,
          "message": "Tool acquired successfully"
        }
      }
    ],
    "last_executed_command_index": 0
  }
}
```

### Deterministic Execution

**Critical**: All nodes must execute identically

```python
def execute_command(command):
    operation = command["params"]["operation"]
    
    if operation == "split_channel":
        split_channel_deterministic(command["params"])
    elif operation == "merge_channels":
        merge_channels_deterministic(command["params"])
    elif operation == "acquire_common_tool":
        acquire_tool_deterministic(command["params"])
    elif operation == "deprecate_common_tool":
        deprecate_tool_deterministic(command["params"])
    
    # All nodes reach identical state
```

---

## 🔐 Zero-Knowledge Proof Voting

**Purpose**: Anonymous voting for sensitive proposals

### ZKP Voting Flow

```
1. VOTER GENERATES PROOF
   ├─> Input: vote (yes/no), private_key
   ├─> ZKP circuit: "I have valid voting rights"
   └─> Output: proof (vote content hidden)

2. SUBMIT ENCRYPTED VOTE
   ├─> Encrypted ballot: E(vote, nonce)
   ├─> Commitment: hash(vote || nonce)
   └─> ZKP proof of validity

3. NETWORK VALIDATES
   ├─> Verify ZKP (eligibility, no double-voting)
   ├─> Accept encrypted ballot
   └─> Store commitment

4. VOTING CLOSES
   ├─> Voters reveal nonces
   ├─> Homomorphic tally OR threshold decryption
   └─> Result computed without revealing individual votes

5. VERIFIABLE OUTCOME
   └─> Anyone can verify tally matches commitments
```

### When to Use ZKP Voting

✅ **Sensitive decisions**: Funding, personnel, controversial changes  
✅ **Protection from coercion**: Voters can't be pressured  
✅ **Honest voting**: No social pressure to conform  
❌ **Not needed**: Technical proposals, routine operations  

---

## 🔄 Complete Workflows

### Workflow 1: Simple Proposal (generic)

```bash
# 1. Create proposal
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Adopt Python Black formatter",
    "tags": ["coding-standards", "python"],
    "proposal_type": "generic"
  }'

# 2. Nodes vote
curl -X POST "http://localhost:8001/proposals/{id}/vote?channel=global" \
  -d '{"vote": "yes"}'

# 3. Close and calculate outcome
curl -X POST "http://localhost:8001/proposals/{id}/close?channel=global"

# Response:
{
  "outcome": "approved",
  "yes_weight": 45.6,
  "no_weight": 12.3
}
```

---

### Workflow 2: Config Change

```bash
# 1. Propose config change
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -d '{
    "title": "Increase task reward to 15 SP",
    "proposal_type": "config_change",
    "tags": ["economy"],
    "params": {
      "key": "task_completion_reputation_reward",
      "value": 15
    }
  }'

# 2. Vote + Close
# (same as workflow 1)

# 3. Automatic execution on approval
# network_state["global"]["config"]["task_completion_reputation_reward"] = 15
```

---

### Workflow 3: Network Operation (Acquire Common Tool)

```bash
# 1. Propose tool acquisition
curl -X POST "http://localhost:8001/proposals?channel=dev" \
  -d '{
    "title": "Acquire SendGrid API for notifications",
    "proposal_type": "network_operation",
    "tags": ["tools", "notifications"],
    "params": {
      "operation": "acquire_common_tool",
      "channel": "dev",
      "tool_id": "sendgrid_api",
      "monthly_cost_sp": 100,
      "credentials_to_encrypt": "SG.xxxxxxxxxxxx"
    }
  }'

# 2. Community votes
# (all nodes participate)

# 3. Close proposal
curl -X POST "http://localhost:8001/proposals/{id}/close?channel=dev"
# Status: "pending_ratification"

# 4. Validators ratify
curl -X POST "http://localhost:8001/governance/ratify/{id}?channel=dev"
curl -X POST "http://localhost:8002/governance/ratify/{id}?channel=dev"
curl -X POST "http://localhost:8003/governance/ratify/{id}?channel=dev"
curl -X POST "http://localhost:8004/governance/ratify/{id}?channel=dev"

# 5. Majority reached → command executes automatically
# - Validates treasury >= 100 SP
# - Encrypts credentials
# - Adds tool to channel
# - Deducts 100 SP from treasury
```

---

## 📊 API Reference

### Create Proposal

```http
POST /proposals?channel={CHANNEL_ID}
Content-Type: application/json

{
  "title": string,
  "description": string (optional),
  "proposal_type": "generic" | "config_change" | "network_operation" | "code_upgrade",
  "tags": [string],
  "params": object (for config_change and network_operation)
}
```

### Vote on Proposal

```http
POST /proposals/{proposal_id}/vote?channel={CHANNEL_ID}
Content-Type: application/json

{
  "vote": "yes" | "no"
}
```

### Close Proposal

```http
POST /proposals/{proposal_id}/close?channel={CHANNEL_ID}
```

Response:
```json
{
  "outcome": "approved" | "rejected",
  "yes_weight": 45.6,
  "no_weight": 23.1,
  "status": "closed" | "pending_ratification"
}
```

### Ratify Proposal (Validators Only)

```http
POST /governance/ratify/{proposal_id}?channel={CHANNEL_ID}
```

Response:
```json
{
  "status": "pending" | "ratified",
  "current_votes": 3,
  "required_votes": 4,
  "command_id": "cmd_xyz" (if ratified)
}
```

### Get Proposal Details

```http
GET /proposals/{proposal_id}/details?channel={CHANNEL_ID}
```

Response includes:
- Vote breakdown by node
- Individual vote weights
- Contextual weighting calculations
- Tag specialization scores

---

## 🎓 Best Practices

### For Proposers

✅ **Tag appropriately** - Tags determine who has expertise  
✅ **Provide context** - Clear description increases approval rate  
✅ **Estimate impact** - Explain benefits and risks  
✅ **Check treasury** - For `acquire_common_tool`, verify funds  

### For Voters

✅ **Vote on expertise** - High impact in your specialized domains  
✅ **Abstain when appropriate** - Don't vote outside expertise  
✅ **Review carefully** - Reputation at stake with bad decisions  

### For Validators

✅ **Ratify responsibly** - Final checkpoint for critical operations  
✅ **Verify execution safety** - Ensure commands won't break network  
✅ **Respond quickly** - Don't block network evolution  

---

## 📚 Related Documentation

- **[ECONOMY.md](ECONOMY.md)** - SP, treasury, common tools details
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[SECURITY.md](SECURITY.md)** - Security considerations
- **[REPUTATION_V2_SYSTEM.md](REPUTATION_V2_SYSTEM.md)** - Deep dive on reputation

---

**Version**: 2.0 | **Status**: ✅ Production-Ready | **Last Updated**: October 2025
