# 🏗️ Synapse-NG Architecture: The Digital Organism

**Complete System Architecture**

Version: 2.0 (Evolved)  
Last Updated: October 2025  
Status: ✅ Production-Ready

---

## 📋 Table of Contents

1. [Vision](#vision)
2. [Three-Layer Architecture](#three-layer-architecture)
3. [Core Components](#core-components)
4. [Network Topology](#network-topology)
5. [Data Flow](#data-flow)
6. [State Management](#state-management)
7. [Implementation Details](#implementation-details)

---

## 🎯 Vision

Synapse-NG is architected as a **living digital organism** - a decentralized network that exhibits properties of biological systems:

| Biological System | Network Equivalent | Implementation |
|-------------------|-------------------|----------------|
| **Neurons** | Nodes | Autonomous agents with cryptographic identity |
| **Nervous System** | Governance | Two-tier democratic decision-making |
| **Metabolism** | Economy | Treasury, SP currency, automatic taxes |
| **Immune System** | Security | Reputation-based sybil resistance, encryption |
| **DNA/Evolution** | Self-Upgrade | WASM-sandboxed code evolution |
| **Collective Intelligence** | AI Integration | Optional LLM agents (completely optional) |

**Core Principle**: No central authority. No single point of failure. Pure emergent behavior.

---

## 🏗️ Three-Layer Architecture

Synapse-NG implements a clean separation of concerns across three distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Channels │  │  Tasks   │  │Governance│  │ Common   │   │
│  │ Treasury │  │ Auctions │  │ Rep. v2  │  │  Tools   │   │
│  │          │  │  Teams   │  │ Commands │  │ (Encrypt)│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
├─────────────────────────────────────────────────────────────┤
│                 SYNAPSESUB PROTOCOL                          │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Topic-Based PubSub over WebRTC                   │      │
│  │  • ANNOUNCE | MESSAGE | I_HAVE | WANT_PIECE       │      │
│  │  • Intelligent message routing                    │      │
│  │  • Automatic deduplication (seen_msg_cache)       │      │
│  │  • Peer mesh per topic                            │      │
│  └───────────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                WEBRTC TRANSPORT LAYER                        │
│  ┌───────────────────────────────────────────────────┐      │
│  │  • RTCPeerConnection (STUN/TURN/ICE)              │      │
│  │  • RTCDataChannel (bidirectional, encrypted)      │      │
│  │  • P2P Signaling (rendezvous or peer tunneling)   │      │
│  │  • DTLS encryption (automatic)                    │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: WebRTC Transport

**Purpose**: Establish encrypted P2P connections between nodes

**Key Technologies**:
- `aiortc` library for Python WebRTC
- ICE (Interactive Connectivity Establishment) for NAT traversal
- STUN/TURN servers for firewall traversal
- DTLS encryption (automatic, built-in)

**Connection Flow**:
```
Node A                               Node B
  |                                    |
  | 1. Generate ICE candidates        |
  |    (local, server-reflexive, relay)|
  |                                    |
  | 2. SDP Offer (via signaling)      |
  |─────────────────────────────────>|
  |                                    |
  |       3. SDP Answer               |
  |<─────────────────────────────────|
  |                                    |
  | 4. ICE checks (STUN binding)     |
  |<────────────────────────────────>|
  |                                    |
  | 5. DTLS handshake                |
  |<════════════════════════════════>|
  |                                    |
  | 6. RTCDataChannel OPEN ✅         |
  |<════════════════════════════════>|
```

**Signaling Modes**:

1. **Rendezvous Mode** (centralized signaling):
   - Central server coordinates SDP exchange
   - Simpler setup, single point of failure
   - Ideal for: development, small networks

2. **P2P Mode** (decentralized signaling):
   - Signaling tunneled through existing connections
   - No central server required
   - Ideal for: production, censorship resistance

---

### Layer 2: SynapseSub Protocol

**Purpose**: Topic-based publish-subscribe over WebRTC data channels

**Inspired by**: libp2p GossipSub, but optimized for WebRTC mesh networks

**Message Types**:

```python
ANNOUNCE     # "I'm interested in topic X"
MESSAGE      # "Here's data for topic X"
I_HAVE       # "I have these message IDs"
WANT_PIECE   # "Send me message ID xyz"
PRUNE        # "I'm no longer interested in topic X"
GRAFT        # "Add me to your topic mesh for X"
```

**Topic Structure**:
```
channel:{channel_id}:state      # Channel state gossip
channel:{channel_id}:tasks      # Task updates
channel:{channel_id}:proposals  # Governance proposals
global:state                    # Network-wide state
```

**Deduplication**:
```python
seen_messages = {}  # msg_id -> timestamp
TTL = 300 seconds   # Cache duration

def should_forward(msg_id):
    if msg_id in seen_messages:
        return False
    seen_messages[msg_id] = time.now()
    return True
```

**Routing Intelligence**:
- Messages only forwarded to peers subscribed to the topic
- Reduces bandwidth consumption
- Enables horizontal scaling (millions of channels)

---

### Layer 3: Application

**Purpose**: Business logic for decentralized task management, governance, economy

**Core Subsystems**:

1. **Channels** - Logical workspaces with isolated state
2. **Tasks** - Lifecycle: `open → claimed → in_progress → completed`
3. **Governance** - Proposals, voting, validator ratification
4. **Economy** - Synapse Points, auctions, treasury
5. **Common Tools** - Encrypted shared resources
6. **Reputation v2** - Tag-specialized expertise tracking
7. **Self-Upgrade** (optional) - WASM code evolution
8. **AI Agents** (optional) - Local LLM integration

---

## 🧩 Core Components

### 1. Cryptographic Identity

**Each node has a sovereign identity:**

```python
# Ed25519 key pair (signing)
ed25519_private_key: 32 bytes   # Never shared
ed25519_public_key:  32 bytes   # Node ID (globally unique)

# X25519 key pair (encryption, future use)
x25519_private_key: 32 bytes
x25519_public_key:  32 bytes
```

**Properties**:
- ✅ **Unforgeable** - Private key never leaves the node
- ✅ **Verifiable** - All messages signed, signature verified
- ✅ **Persistent** - Identity survives restarts (stored in `data/{node_id}/`)

**Signature Flow**:
```python
# Signing a proposal
signature = ed25519_sign(private_key, proposal_data)

# Verification by other nodes
is_valid = ed25519_verify(public_key, proposal_data, signature)
```

---

### 2. CRDT State Synchronization

**Last-Write-Wins (LWW) CRDT**:

```python
# Merge rule
def merge_task(local_task, incoming_task):
    if incoming_task["updated_at"] > local_task["updated_at"]:
        return incoming_task
    else:
        return local_task
```

**Properties**:
- ✅ **Convergence** - All nodes eventually reach same state
- ✅ **No coordination** - Updates independent of network topology
- ✅ **Partition tolerance** - Network splits heal automatically

**Limitations**:
- ⚠️ Requires synchronized clocks (NTP recommended)
- ⚠️ No causal ordering (see Security docs for improvements)

---

### 3. Channels (Logical Sharding)

**Channels isolate state:**

```json
{
  "dev_ui": {
    "tasks": {...},
    "proposals": {...},
    "treasury_balance": 500,
    "common_tools": {...}
  },
  "backend": {
    "tasks": {...},
    "proposals": {...},
    "treasury_balance": 1200,
    "common_tools": {...}
  }
}
```

**Subscription Model**:
- Nodes explicitly subscribe: `SUBSCRIBED_CHANNELS=dev_ui,backend`
- Only receive gossip for subscribed channels
- Enables horizontal scaling

---

### 4. Two-Tier Governance

**Tier 1: Community Voting (CRDT)**

All nodes vote, outcomes calculated locally:

```python
for node_id, vote in proposal.votes.items():
    reputation = get_reputation_v2(node_id)
    weight = calculate_contextual_vote_weight(reputation, proposal.tags)
    
    if vote == "yes":
        yes_weight += weight
    else:
        no_weight += weight

outcome = "approved" if yes_weight > no_weight else "rejected"
```

**Tier 2: Validator Ratification (Raft)**

For `network_operation` proposals:

```python
validator_set = top_N_nodes_by_reputation(N=7)

def ratify(proposal_id):
    if caller not in validator_set:
        return 403  # Forbidden
    
    ratification_votes[proposal_id][caller] = True
    
    if len(ratification_votes[proposal_id]) >= (N // 2) + 1:
        # Majority reached
        append_to_execution_log(proposal_id)
        execute_command(proposal)
```

---

### 5. Reputation System v2

**From integer to specialized:**

```python
# Old (v1)
reputation: int = 100

# New (v2)
reputation: {
  "_total": 100,
  "_last_updated": "2025-10-23T10:00:00Z",
  "tags": {
    "python": 50,
    "security": 30,
    "testing": 20
  }
}
```

**Contextual Vote Weighting**:

```python
def calculate_contextual_vote_weight(reputation, proposal_tags):
    # Base weight from total reputation
    base_weight = 1.0 + log2(reputation["_total"] + 1)
    
    # Bonus from tag specialization
    specialization_score = sum(
        reputation["tags"].get(tag, 0)
        for tag in proposal_tags
    )
    bonus_weight = log2(specialization_score + 1)
    
    return base_weight + bonus_weight
```

**Time Decay**:
```python
# Background task runs every 24h
async def reputation_decay_loop():
    while True:
        await asyncio.sleep(86400)  # 24 hours
        
        for node in all_nodes:
            for tag, value in node.reputation["tags"].items():
                new_value = value * 0.99  # -1% daily
                
                if new_value < 0.1:
                    del node.reputation["tags"][tag]
                else:
                    node.reputation["tags"][tag] = new_value
            
            node.reputation["_total"] = sum(node.reputation["tags"].values())
```

---

### 6. Common Tools (Network-Owned Resources)

**Encrypted credential storage:**

```python
# Encryption (AESGCM + HKDF)
def encrypt_credentials(channel_id, credentials):
    key = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=NODE_ID.encode()[:32],
        info=b'synapse-ng-common-tools-v1'
    ).derive(channel_id.encode())
    
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, credentials.encode(), None)
    
    return base64.b64encode(nonce + ciphertext)

# Decryption (in-memory only)
def decrypt_credentials(channel_id, encrypted_credentials):
    key = derive_key_from_channel_id(channel_id)
    data = base64.b64decode(encrypted_credentials)
    
    nonce = data[:12]
    ciphertext = data[12:]
    
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    return plaintext.decode()  # Immediately use, then discard
```

**Three-Layer Authorization**:

1. **Status check**: Tool must be `"active"`
2. **Task assignment**: Caller must be task assignee
3. **Tool requirement**: Task must declare tool in `required_tools`

---

## 🌐 Network Topology

### Bootstrap Process

**Initial Network Formation**:

```
┌──────────────────────────────────────────────────────┐
│ BOOTSTRAP SEQUENCE                                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 1. Node A starts (first node in network)            │
│    └─> No peers, waits for connections              │
│                                                      │
│ 2. Node B starts with bootstrap: Node A             │
│    ├─> HTTP POST /bootstrap/handshake to Node A    │
│    ├─> Exchange peer info (ID, URL, channels)       │
│    ├─> Initiate WebRTC signaling                    │
│    └─> Establish RTCDataChannel                     │
│                                                      │
│ 3. Node C starts with bootstrap: Node A             │
│    ├─> Handshake with Node A                        │
│    ├─> Node A introduces Node C to Node B           │
│    ├─> Node C connects to both A and B              │
│    └─> Full mesh formed (N=3, connections=3)        │
│                                                      │
│ 4. Gossip synchronization                           │
│    ├─> All nodes exchange full state                │
│    ├─> CRDT merge resolves conflicts                │
│    └─> Convergence achieved (~30 seconds)           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Peer Discovery

**Methods**:

1. **mDNS** (local network): Automatic discovery via multicast DNS
2. **Rendezvous Server**: Central directory of active nodes
3. **Bootstrap Peers**: Manual configuration of known nodes
4. **Peer Gossip**: Nodes share their peer list with each other

---

## 📊 State Management

### Network State Structure

```python
network_state = {
    "global": {
        "nodes": {
            "node_id_1": {
                "id": "...",
                "url": "http://...",
                "last_seen": "2025-10-23T10:00:00Z",
                "reputation": {
                    "_total": 150,
                    "tags": {"python": 70, "security": 50, ...}
                },
                "balance_sp": 1000,
                "subscribed_channels": ["dev", "qa"]
            }
        },
        "config": {
            "transaction_tax_percentage": 0.02,
            "task_completion_reputation_reward": 10,
            ...
        },
        "execution_log": [
            {
                "command_id": "...",
                "operation": "acquire_common_tool",
                "params": {...},
                "ratified_at": "..."
            }
        ],
        "validator_set": ["node_id_1", "node_id_2", ...]
    },
    
    "dev": {
        "tasks": {
            "task_id_1": {
                "title": "...",
                "status": "completed",
                "tags": ["python", "testing"],
                "assignee": "node_id_2",
                ...
            }
        },
        "proposals": {...},
        "treasury_balance": 500,
        "common_tools": {
            "geolocation_api": {
                "status": "active",
                "monthly_cost_sp": 100,
                "encrypted_credentials": "..."
            }
        }
    }
}
```

### State Persistence

**Storage Location**: `data/{node_id}/state.json`

**Save Triggers**:
- State change via API endpoint
- Incoming gossip message (after CRDT merge)
- Periodic backup (every 60 seconds)

**Load on Startup**:
```python
async def load_state():
    if os.path.exists(f'data/{NODE_ID}/state.json'):
        with open(...) as f:
            network_state = json.load(f)
    else:
        network_state = initialize_default_state()
```

---

## 🔄 Data Flow

### Task Creation Flow

```
User                  Node A                  Node B                  Node C
 |                     |                       |                       |
 | POST /tasks         |                       |                       |
 |-------------------->|                       |                       |
 |                     |                       |                       |
 |                     | 1. Validate request   |                       |
 |                     | 2. Create task object |                       |
 |                     | 3. Update local state |                       |
 |                     |                       |                       |
 |                     | 4. Gossip MESSAGE     |                       |
 |                     |---------------------->|                       |
 |                     |---------------------- |--------------------->|
 |                     |                       |                       |
 |                     |                       | 5. CRDT merge         |
 |                     |                       | 6. Save state         |
 |                     |                       |                       |
 |                     |                       |                       | 5. CRDT merge
 |                     |                       |                       | 6. Save state
 |                     |                       |                       |
 | 200 OK             |                       |                       |
 |<--------------------|                       |                       |
 |                     |                       |                       |
```

### Proposal Voting Flow

```
1. CREATE PROPOSAL
   Node A: POST /proposals → gossip to all nodes

2. VOTE
   Node B: POST /proposals/{id}/vote → vote added to CRDT
   Node C: POST /proposals/{id}/vote → vote added to CRDT
   
   (All nodes have local copy of all votes via gossip)

3. CLOSE & TALLY
   Any node: POST /proposals/{id}/close
   
   Each node calculates outcome independently:
   - Sum yes_weight = Σ(vote_weight for "yes" votes)
   - Sum no_weight = Σ(vote_weight for "no" votes)
   - outcome = "approved" if yes_weight > no_weight

4. IF network_operation PROPOSAL:
   Validators ratify via POST /governance/ratify/{id}
   
   When majority reached:
   - Command added to execution_log (CRDT)
   - All nodes execute command identically
```

---

## 🛠️ Implementation Details

### File Structure

```
app/
├── main.py                      # FastAPI server, all endpoints
├── webrtc_manager.py            # WebRTC connection lifecycle
├── synapsesub_protocol.py       # PubSub implementation
├── identity.py                  # Cryptographic identity management
├── ai_agent.py                  # Optional AI integration
├── self_upgrade.py              # Optional WASM self-upgrade
├── evolutionary_engine.py       # Optional AI code generation
└── schemas.py                   # Data validation schemas
```

### Key Background Tasks

```python
# In main.py
async def startup_event():
    asyncio.create_task(gossip_task())
    asyncio.create_task(webrtc_keep_alive())
    asyncio.create_task(reputation_decay_loop())
    asyncio.create_task(common_tools_maintenance_loop())
    asyncio.create_task(auction_processor_task())
    
    # Optional
    if AI_ENABLED:
        asyncio.create_task(ai_agent_loop())
```

### Deterministic Calculations

**Critical for consensus:**

```python
def calculate_balances():
    """Must produce identical results on all nodes"""
    balances = {node_id: INITIAL_BALANCE for node_id in nodes}
    
    for channel in channels:
        for task in sorted_by_timestamp(channel.tasks):
            if task.status == "completed":
                balances[task.created_by] -= task.reward
                
                tax = max(1, round(task.reward * TAX_RATE))
                balances[task.assignee] += (task.reward - tax)
    
    return balances
```

**Why deterministic**:
- Same input → same output on all nodes
- No reliance on local timestamps
- Sorted iteration ensures order

---

## 🎓 Design Principles

1. **Decentralization First** - No required central services
2. **Determinism** - All nodes reach same conclusion independently
3. **Eventual Consistency** - CRDT guarantees convergence
4. **Defense in Depth** - Multiple security layers
5. **Graceful Degradation** - System works even if features disabled
6. **Modularity** - Clean separation of concerns (3 layers)
7. **Extensibility** - Easy to add new features (see Common Tools)

---

## 📚 Related Documentation

- **[GOVERNANCE.md](GOVERNANCE.md)** - Governance, reputation v2, voting
- **[ECONOMY.md](ECONOMY.md)** - SP, auctions, treasury, common tools
- **[SECURITY.md](SECURITY.md)** - Threat model and mitigations
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup guide

---

**Version**: 2.0 | **Status**: ✅ Production-Ready | **Last Updated**: October 2025
