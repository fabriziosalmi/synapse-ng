# Governance System - Complete Guide

**Synapse-NG Decentralized Governance**

Version: 2.0  
Last Updated: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Two-Tier Architecture](#two-tier-architecture)
3. [Weighted Voting System](#weighted-voting-system)
4. [ZKP Anonymous Voting](#zkp-anonymous-voting)
5. [Proposal Types](#proposal-types)
6. [Implementation Details](#implementation-details)
7. [API Reference](#api-reference)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)

---

## Overview

Synapse-NG implements a **two-tier democratic governance system** combining:

1. **Community Voting (Tier 1)** - CRDT-based decentralized voting
2. **Validator Ratification (Tier 2)** - Raft consensus for final approval

This architecture ensures both **democratic participation** and **network stability**.

### Key Features

- ✅ **Reputation-weighted voting** - Influence based on contribution
- ✅ **Zero-knowledge proof privacy** - Anonymous voting option
- ✅ **Automatic execution** - Approved proposals auto-execute
- ✅ **Multiple proposal types** - Generic, config, operations, code upgrades
- ✅ **Immutable audit trail** - All decisions permanently logged

---

## Two-Tier Architecture

### Tier 1: Community Voting (CRDT)

**Purpose**: Democratic decision-making with reputation weighting

**Mechanism**:
- Any node can create proposals
- All nodes vote (approval/rejection)
- Votes weighted by reputation score
- CRDT (Last-Write-Wins) ensures convergence
- Configurable approval threshold (default: 60%)

**CRDT Properties**:
```python
# Automatic conflict resolution
vote_state = {
    "node_1": {"vote": "approval", "timestamp": "2025-10-03T10:00:00Z"},
    "node_2": {"vote": "rejection", "timestamp": "2025-10-03T10:01:00Z"}
}
# Last write wins (LWW) - node_2's vote is newer
```

### Tier 2: Validator Ratification (Raft)

**Purpose**: Ensure network-critical decisions have validator consensus

**Mechanism**:
- Validator set = top 7 nodes by reputation
- Raft consensus algorithm (leader election, log replication)
- Requires >50% validator approval
- Ratified proposals added to execution log
- Automatic execution by command processor

**Raft Benefits**:
- Strong consistency guarantee
- Leader-based coordination
- Fault tolerance (can survive minority failures)
- Linearizable operations

### Decision Flow

```
1. CREATE PROPOSAL
   └─> Any node proposes change

2. COMMUNITY VOTE (Tier 1)
   ├─> All nodes vote
   ├─> Reputation-weighted tallying
   └─> Threshold check (default: 60%)

3. IF APPROVED:
   └─> VALIDATOR RATIFICATION (Tier 2)
       ├─> Top 7 validators vote
       ├─> Raft consensus
       └─> >50% required

4. IF RATIFIED:
   └─> EXECUTION LOG
       ├─> Append-only CRDT log
       └─> Command processor executes

5. STATE UPDATE
   └─> Network state updated globally
```

---

## Weighted Voting System

### Reputation Score Calculation

Reputation is earned through **positive contributions** and **network participation**:

```python
reputation_score = (
    task_completions * 10 +
    proposals_approved * 5 +
    auction_wins * 3 +
    uptime_days * 1 -
    malicious_actions * 50
)
```

### Vote Weight Formula

```python
vote_weight = sqrt(reputation_score) / total_sqrt_reputation
```

**Example**:
- Node A: reputation = 100 → weight = sqrt(100) = 10
- Node B: reputation = 400 → weight = sqrt(400) = 20
- Node C: reputation = 900 → weight = sqrt(900) = 30
- Total: 10 + 20 + 30 = 60

Node A influence: 10/60 = 16.7%  
Node B influence: 20/60 = 33.3%  
Node C influence: 30/60 = 50.0%

### Benefits of Square Root Weighting

- **Diminishing returns**: Prevents whales from dominating
- **New node opportunity**: Easier for newcomers to gain influence
- **Plutocracy resistance**: No single node can control outcome
- **Sybil attack mitigation**: Multiple fake identities less effective

### Reputation Decay

To prevent stagnation:
```python
# Weekly decay
reputation_new = reputation_old * 0.95  # 5% decay

# After 1 month without activity:
# reputation = initial * (0.95^4) ≈ initial * 0.81 (19% loss)
```

---

## ZKP Anonymous Voting

### Why Zero-Knowledge Proofs?

In some scenarios, voters want **privacy** while maintaining **verifiability**:

- Sensitive proposals (funding, personnel changes)
- Protection from coercion or retaliation
- Encourage honest voting without social pressure

### ZKP Voting Flow

```
1. VOTER GENERATES PROOF
   ├─> Input: vote (approval/rejection), secret key
   ├─> ZKP circuit proves: "I have valid voting rights"
   └─> Output: proof (no vote content revealed)

2. VOTER SUBMITS ENCRYPTED VOTE
   ├─> Encrypted ballot: E(vote, nonce)
   ├─> ZKP proof of validity
   └─> Commitment: hash(vote, nonce)

3. NETWORK VALIDATES PROOF
   ├─> Verify ZKP (voter eligibility, no double-voting)
   ├─> Accept encrypted ballot
   └─> Store commitment

4. AFTER VOTING CLOSES
   ├─> Voters reveal nonces (or use threshold decryption)
   ├─> Votes decrypted homomorphically
   └─> Tally computed without revealing individual votes

5. VERIFIABLE RESULT
   └─> Anyone can verify tally matches commitments
```

### ZKP Implementation (Simplified)

**Libraries Used**:
- `py_ecc` - Elliptic curve cryptography
- `zksnark` - ZK-SNARK proof generation/verification

**Proof Statement**:
```
"I know a secret key sk such that:
  1. pk = G * sk (public key derivation)
  2. pk is in ValidVoterSet
  3. I have not voted before (nullifier check)"
```

### ZKP API Endpoints

```bash
# Enable ZKP for proposal
POST /proposals/{proposal_id}/enable_zkp
{
  "zkp_enabled": true,
  "reveal_after": "2025-10-10T00:00:00Z"
}

# Submit ZKP vote
POST /proposals/{proposal_id}/vote_zkp
{
  "encrypted_vote": "base64_encrypted_ballot",
  "proof": "base64_zkp_proof",
  "commitment": "hash_of_vote_and_nonce",
  "nullifier": "unique_voting_token"
}

# Reveal after voting closes
POST /proposals/{proposal_id}/reveal_zkp
{
  "nonce": "random_nonce_used_in_encryption"
}
```

### Privacy Guarantees

- ✅ **Vote secrecy**: No one knows your individual vote
- ✅ **Eligibility verifiable**: Proof you can vote, but not who you are
- ✅ **No double-voting**: Nullifier prevents multiple votes
- ✅ **Verifiable tally**: Final result mathematically provable

### When to Use ZKP vs Normal Voting

| Scenario | Voting Type | Reason |
|----------|-------------|--------|
| Routine config changes | Normal | Transparency preferred |
| Budget allocation | ZKP | Prevent collusion |
| Validator removal | ZKP | Protect from retaliation |
| Code upgrades | Normal | Technical review needed |
| Emergency actions | Normal | Speed and clarity required |

---

## Proposal Types

Synapse-NG supports **4 proposal types**:

### 1. Generic Proposal

**Purpose**: General discussions, non-binding decisions

**Example**:
```bash
POST /proposals
{
  "title": "Community Discussion: Feature Priorities",
  "description": "What should we build next?",
  "proposal_type": "generic",
  "channel": "global"
}
```

**Outcome**: No automatic execution, consensus signaling only

---

### 2. Config Change Proposal

**Purpose**: Modify network configuration parameters

**Parameters**:
```python
config_params = {
    "consensus_timeout": 5000,  # ms
    "max_validators": 7,
    "min_reputation_for_validator": 100,
    "proposal_approval_threshold": 0.6,  # 60%
    "auction_duration": 3600,  # seconds
    "zkp_enabled_by_default": false
}
```

**Example**:
```bash
POST /proposals
{
  "title": "Increase Validator Count",
  "description": "Expand validator set to 9 nodes",
  "proposal_type": "config_change",
  "params": {
    "key": "max_validators",
    "value": 9
  }
}
```

**Execution**: If approved → config auto-updated

---

### 3. Network Operation Proposal

**Purpose**: Structural network changes (split/merge channels, etc.)

**Operations**:
- `split_channel`: Divide channel into sub-channels
- `merge_channels`: Combine multiple channels
- `create_validator_council`: Form specialized group
- `update_reputation_formula`: Modify reputation calculation

**Example**:
```bash
POST /proposals
{
  "title": "Split #development Channel",
  "description": "Create #backend and #frontend sub-channels",
  "proposal_type": "network_operation",
  "params": {
    "operation": "split_channel",
    "source_channel": "development",
    "new_channels": ["backend", "frontend"]
  }
}
```

**Execution**: Operation queued for validator ratification

---

### 4. Code Upgrade Proposal

**Purpose**: Autonomous network evolution (see [Phase 7](PHASE_7_NETWORK_SINGULARITY.md))

**Example**:
```bash
POST /upgrades/propose
{
  "title": "Optimize Consensus Algorithm",
  "version": "1.2.0",
  "package_url": "ipfs://Qm...",
  "package_hash": "sha256:abc123...",
  "package_size": 1024000
}
```

**Execution**: Download WASM → Verify hash → Execute in sandbox → Network upgrades

---

## Implementation Details

### Validator Selection Algorithm

```python
def select_validators(network_state, max_validators=7):
    """
    Select top N nodes by reputation as validators.
    
    Re-runs every 24 hours or when significant reputation changes occur.
    """
    reputations = calculate_reputations(network_state)
    
    # Sort nodes by reputation (descending)
    sorted_nodes = sorted(
        reputations.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Select top N
    validators = [node_id for node_id, rep in sorted_nodes[:max_validators]]
    
    return validators
```

### Proposal Status Lifecycle

```
proposed → voting → approved/rejected

If approved:
  ├─> pending_ratification (waiting for validators)
  └─> ratified/denied

If ratified:
  ├─> queued_for_execution
  ├─> executing
  └─> executed/failed
```

### Execution Log (CRDT)

**Structure**:
```python
execution_log = [
    {
        "command_id": "cmd_001",
        "operation": "config_change",
        "params": {"key": "max_validators", "value": 9},
        "proposal_id": "prop_123",
        "timestamp": "2025-10-03T12:00:00Z",
        "executed": false,
        "result": null
    },
    # Append-only, never modified
]
```

**Properties**:
- Append-only (monotonic growth)
- CRDT convergence (all nodes eventually have same log)
- Idempotent execution (re-running same command = same result)

---

## API Reference

### Create Proposal

```http
POST /proposals
Content-Type: application/json

{
  "title": "Proposal Title",
  "description": "Detailed description",
  "proposal_type": "generic|config_change|network_operation|code_upgrade",
  "channel": "global",
  "params": {
    // Type-specific parameters
  }
}
```

**Response**:
```json
{
  "proposal_id": "prop_20251003_120000",
  "status": "voting",
  "created_at": "2025-10-03T12:00:00Z"
}
```

---

### Vote on Proposal

```http
POST /proposals/{proposal_id}/vote
Content-Type: application/json

{
  "vote": "approval|rejection",
  "reasoning": "Optional explanation"
}
```

**Response**:
```json
{
  "vote_registered": true,
  "vote_weight": 0.15,
  "current_tally": {
    "approval": 0.65,
    "rejection": 0.35
  }
}
```

---

### Get Proposal Status

```http
GET /proposals/{proposal_id}
```

**Response**:
```json
{
  "id": "prop_20251003_120000",
  "title": "Increase Validator Count",
  "status": "ratified",
  "votes": {
    "node_1": {"vote": "approval", "weight": 0.15},
    "node_2": {"vote": "approval", "weight": 0.25}
  },
  "tally": {
    "approval": 0.70,
    "rejection": 0.30
  },
  "execution_status": "pending"
}
```

---

### List Active Proposals

```http
GET /proposals?status=voting&channel=global
```

**Response**:
```json
{
  "proposals": [
    {
      "id": "prop_001",
      "title": "...",
      "status": "voting",
      "created_at": "..."
    }
  ],
  "total": 5
}
```

---

## Usage Examples

### Example 1: Simple Configuration Change

```bash
# 1. Create proposal
curl -X POST http://localhost:8000/proposals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Increase Consensus Timeout",
    "description": "Network latency requires longer timeout",
    "proposal_type": "config_change",
    "params": {
      "key": "consensus_timeout",
      "value": 7000
    }
  }'
# Response: {"proposal_id": "prop_001"}

# 2. Vote on proposal
curl -X POST http://localhost:8000/proposals/prop_001/vote \
  -H "Content-Type: application/json" \
  -d '{
    "vote": "approval",
    "reasoning": "Agree, we need more time for Raft"
  }'

# 3. Check status
curl http://localhost:8000/proposals/prop_001

# 4. Wait for approval + ratification
# 5. Config automatically updated!
```

---

### Example 2: ZKP Anonymous Vote

```bash
# 1. Create proposal with ZKP enabled
curl -X POST http://localhost:8000/proposals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Remove Validator Node XYZ",
    "proposal_type": "network_operation",
    "zkp_enabled": true
  }'

# 2. Submit ZKP vote (vote content hidden)
curl -X POST http://localhost:8000/proposals/prop_002/vote_zkp \
  -H "Content-Type: application/json" \
  -d '{
    "encrypted_vote": "base64_encrypted_data",
    "proof": "zkp_proof_base64",
    "commitment": "hash123",
    "nullifier": "unique_token"
  }'

# 3. After voting closes, reveal nonce
curl -X POST http://localhost:8000/proposals/prop_002/reveal_zkp \
  -d '{"nonce": "random_nonce"}'

# 4. Tally computed, votes remain anonymous
```

---

### Example 3: Channel Split Operation

```bash
# Propose splitting large channel
curl -X POST http://localhost:8000/proposals \
  -d '{
    "title": "Split #engineering Channel",
    "proposal_type": "network_operation",
    "params": {
      "operation": "split_channel",
      "source_channel": "engineering",
      "new_channels": ["backend", "frontend", "devops"]
    }
  }'

# If approved + ratified:
# - Old #engineering archived
# - New channels created
# - Messages/tasks migrated
```

---

## Best Practices

### For Proposal Creators

1. **Clear Title**: Describe the change in <10 words
2. **Detailed Description**: Explain why, benefits, risks
3. **Right Type**: Use correct proposal type for auto-execution
4. **Test Impact**: Understand consequences before proposing
5. **Community Discussion**: Discuss in channel before formal proposal

### For Voters

1. **Research**: Read full description and discussion
2. **Vote Weight**: Remember your vote is reputation-weighted
3. **Timeliness**: Vote before timeout (default: 24 hours)
4. **Reasoning**: Add reasoning to help others understand
5. **ZKP When Needed**: Use anonymous voting for sensitive issues

### For Validators

1. **Responsibility**: Ratification is final approval
2. **Technical Review**: Especially for code upgrades
3. **Network Health**: Consider impact on all nodes
4. **Availability**: Stay online to participate in Raft consensus
5. **Honest Voting**: Your reputation depends on good decisions

### Security Considerations

1. **Sybil Resistance**: Reputation weighting mitigates fake identities
2. **51% Attack**: Two-tier system prevents majority takeover
3. **Configuration Bounds**: Some params have min/max limits
4. **Code Review**: Critical upgrades should have manual review period
5. **Rollback Plan**: All changes should be reversible

---

## Troubleshooting

### Proposal Stuck in "Voting"

**Problem**: Proposal not closing after timeout  
**Solution**: Check `proposal_auto_close_loop` is running:
```bash
# Check logs
grep "proposal_auto_close_loop" logs/node.log

# Manual close (if needed)
curl -X POST /proposals/{proposal_id}/close
```

### Votes Not Counted

**Problem**: Vote submitted but not reflected in tally  
**Solution**:
1. Check node reputation > 0
2. Verify vote format (approval/rejection exactly)
3. Check CRDT sync (may take few seconds)

### Validator Ratification Timeout

**Problem**: Approved proposal stuck in "pending_ratification"  
**Solution**:
1. Check validator count: `GET /validators`
2. Ensure >50% validators online
3. Check Raft leader: `GET /raft/status`
4. If leader failed, election will auto-trigger

---

## Related Documentation

- [Phase 7: Network Singularity](PHASE_7_NETWORK_SINGULARITY.md) - AI-powered code evolution
- [Self-Upgrade System](SELF_UPGRADE_SYSTEM.md) - Autonomous network upgrades
- [Network Operations](NETWORK_OPERATIONS.md) - Channel management
- [API Examples](API_EXAMPLES.md) - More API usage examples

---

**Version**: 2.0  
**Last Updated**: October 2025  
**Status**: ✅ Production Ready
