# Synapse-NG (Next Generation)

**A decentralized, scalable, and intelligent digital organism.**

Synapse-NG is a fully decentralized peer-to-peer network that self-organizes like a living organism. There is no central authority, no mandatory server, no leader. Each node is an autonomous agent that collaborates to form a collective consciousness, make decisions, and accomplish tasks.

## 🧬 Philosophy

Each node is a sovereign "neuron". The network "lives" through fundamental principles:

- **Sovereign Identity**: Each node possesses its own cryptographic identity (Ed25519), immutable and unforgeable.
- **P2P Communication**: Direct WebRTC connections between peers, without intermediaries.
- **Intelligent Gossip**: Topic-based SynapseSub protocol to synchronize only what's needed.
- **Conflict-Free Consensus (CRDT)**: Shared state mathematically converges to the same result on all nodes.
- **Decentralized Bootstrap**: No mandatory central server, bootstrap from existing peers.
- **Collective Intelligence**: Distributed proposal, voting, and reputation system.

## ✨ SynapseComms v2.0 Architecture

Synapse-NG implements a three-layer communication architecture:

### **Layer 1: WebRTC Transport Layer**
- Direct P2P connections between nodes
- `RTCDataChannel` for bidirectional communication
- Support for both centralized and P2P signaling

### **Layer 2: SynapseSub Protocol**
- Topic-based PubSub over WebRTC
- Peer mesh for each topic
- Automatic message deduplication
- Intelligent forwarding based on interest

### **Layer 3: Application Layer**
- Thematic channels (sharding)
- Distributed task management
- Governance and voting
- Reputation system

```
┌─────────────────────────────────────────────────┐
│            APPLICATION LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Channels │  │  Tasks   │  │Governance│     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│          SYNAPSESUB PROTOCOL                    │
│  ┌──────────────────────────────────────┐      │
│  │  PubSub Topics + Message Routing     │      │
│  │  ANNOUNCE | MESSAGE | I_HAVE | ...   │      │
│  └──────────────────────────────────────┘      │
├─────────────────────────────────────────────────┤
│         WEBRTC TRANSPORT LAYER                  │
│  ┌──────────────────────────────────────┐      │
│  │   RTCPeerConnection + DataChannel     │      │
│  │   P2P Signaling (tunneling)           │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

## 🚀 Features

### **Communication**
- ✅ **WebRTC P2P**: Direct connections between nodes, low latency
- ✅ **SynapseSub**: PubSub protocol optimized for mesh networks
- ✅ **Topic-based routing**: Only relevant data is transmitted
- ✅ **Automatic deduplication**: Cache of seen messages

### **Decentralization**
- ✅ **P2P Bootstrap**: Handshake with existing peers
- ✅ **P2P Signaling**: Tunneling through connected peers
- ✅ **Optional Rendezvous**: Central server only for convenience
- ✅ **No SPOF**: No single point of failure

### **Task Management**
- ✅ **Thematic channels**: Logical partitioning of tasks (requires subscription)
- ✅ **Complete lifecycle**: open → claimed → in_progress → completed
- ✅ **CRDT propagation**: Guaranteed convergence via topic-based PubSub
- ✅ **Transition validation**: Only at API endpoints
- ⚠️ **Subscription required**: Nodes must subscribe to channels to receive updates

### **Governance**
- ✅ **Proposal system**: Any node can propose changes
- ✅ **Weighted voting**: Weight based on reputation (weight = 1 + log₂(reputation + 1))
- ✅ **Distributed voting**: Votes propagated via PubSub
- ✅ **Dynamic reputation**: Based on contributions (+10 tasks, +1 vote)
- ✅ **Meritocracy**: High-reputation nodes have more influence in decisions

## 📦 Installation

### Requirements
- Docker & Docker Compose
- Python 3.9+ (for local development)
- `jq` (for test scripts)

### Quick Start (Rendezvous Mode)

```bash
# Clone
git clone https://github.com/your-org/synapse-ng.git
cd synapse-ng

# Start network with Rendezvous Server
docker-compose up --build -d

# Check status
curl http://localhost:8001/state | jq '.global.nodes | length'

# Run test suite
./test_suite.sh
```

### Quick Start (Pure P2P Mode)

```bash
# Start fully decentralized network
docker-compose -f docker-compose.p2p.yml up --build -d

# Check P2P connections
curl http://localhost:8001/webrtc/connections | jq

# Run P2P tests
./test_p2p.sh
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OWN_URL` | This node's URL | ✅ Yes | - |
| `RENDEZVOUS_URL` | Rendezvous Server URL | ⚠️ Rendezvous mode only | - |
| `BOOTSTRAP_NODES` | Bootstrap peer list (CSV) | ⚠️ P2P mode only | - |
| `SUBSCRIBED_CHANNELS` | Channels to subscribe (CSV) | No | "" |
| `NODE_PORT` | Node port | No | 8000 |

**⚠️ IMPORTANT: Channel Subscriptions**

To receive tasks and messages on a channel, **all nodes must subscribe** to the corresponding topic via `SUBSCRIBED_CHANNELS`. If a node is not subscribed to a channel, it **will not receive** updates for that channel via PubSub.

Example:
- `SUBSCRIBED_CHANNELS=dev_ui` → receives only tasks from `dev_ui` channel
- `SUBSCRIBED_CHANNELS=dev_ui,marketing` → receives tasks from both channels

### Operating Modes

#### **Mode 1: Rendezvous (Simpler)**

Uses a central server for discovery and signaling.

```yaml
environment:
  - OWN_URL=http://node-1:8000
  - RENDEZVOUS_URL=http://rendezvous:8080
  - SUBSCRIBED_CHANNELS=dev_ui
```

**Pros**: Simple setup, automatic discovery
**Cons**: Central point of failure

#### **Mode 2: Pure P2P (Decentralized)**

No central server, bootstrap from existing peers.

```yaml
environment:
  - OWN_URL=http://node-2:8000
  - BOOTSTRAP_NODES=http://node-1:8000,http://node-3:8000
  - SUBSCRIBED_CHANNELS=dev_ui
```

**Pros**: Fully decentralized, resilient
**Cons**: Requires at least one bootstrap node

## 📡 API Endpoints

### **Status and Monitoring**

```bash
# Global network state
GET /state

# Subscribed channels
GET /channels

# WebRTC connections
GET /webrtc/connections

# PubSub statistics
GET /pubsub/stats
```

### **Task Management**

```bash
# Create task
POST /tasks?channel=CHANNEL_ID
Content-Type: application/json
{"title": "Fix bug"}

# Claim task
POST /tasks/{task_id}/claim?channel=CHANNEL_ID

# Mark in progress
POST /tasks/{task_id}/progress?channel=CHANNEL_ID

# Complete task
POST /tasks/{task_id}/complete?channel=CHANNEL_ID

# Delete task
DELETE /tasks/{task_id}?channel=CHANNEL_ID
```

### **Governance**

```bash
# Create proposal
POST /proposals?channel=CHANNEL_ID
Content-Type: application/json
{"title": "Proposal Title", "description": "Details", "proposal_type": "generic"}

# Vote on proposal
POST /proposals/{proposal_id}/vote?channel=CHANNEL_ID
Content-Type: application/json
{"vote": "yes"}  # or "no"

# Close proposal and calculate outcome
POST /proposals/{proposal_id}/close?channel=CHANNEL_ID

# Get proposal details (includes vote weights)
GET /proposals/{proposal_id}/details?channel=CHANNEL_ID
```

### **P2P Bootstrap**

```bash
# Initial handshake
POST /bootstrap/handshake
{"peer_id": "NODE_ID", "peer_url": "http://node:8000"}

# Relay P2P signaling
POST /p2p/signal/relay
{"from_peer": "ID_A", "to_peer": "ID_C", "type": "offer", "payload": {...}}

# Receive P2P signaling
POST /p2p/signal/receive
{"from_peer": "ID_A", "type": "answer", "payload": {...}}
```

## 🧪 Testing

### Complete Test Suite

Tests convergence, WebRTC, PubSub, task lifecycle, reputation, economy, and governance.

```bash
# All tests (base + economy + governance)
./test_suite.sh

# Base tests only
./test_suite.sh base

# Governance tests only (weighted voting)
./test_suite.sh governance

# Economy tests only (Synapse Points)
./test_suite.sh economy

# Show options
./test_suite.sh help
```

**Tested Scenarios:**

**Base Tests (Scenarios 1-6):**
1. ✅ Cold start (3 nodes)
2. ✅ WebRTC connections (verify peer connections and data channels)
3. ✅ PubSub subscriptions (verify topic subscriptions)
4. ✅ New node joining (dynamic scalability)
5. ✅ Complete task lifecycle (create → claim → progress → complete)
6. ✅ Reputation system (+10 for completed tasks)

**Economy and Governance Tests (Scenarios 7-8):**
7. ✅ **Weighted Voting**: Verifies that high-reputation nodes have more influence (weight = 1 + log₂(rep + 1))
8. ✅ **SP Economy**: Verifies deterministic transfer of Synapse Points (task creation with reward, SP freezing, transfer on completion)

**📚 Test Documentation:**
- `TEST_ECONOMIA_GOVERNANCE.md` - Complete documentation
- `QUICK_START_TESTS.md` - Quick guide
- `ESEMPI_API_TEST.md` - API examples for manual tests

**⚠️ Test Notes:**
- All nodes must subscribe to the same channels for cross-node tests
- Timeouts are calibrated for WebRTC + PubSub (slower than direct HTTP gossip)
- Test suite runs automatically in pre-push git hook
- Economy/governance tests verify determinism: all nodes must agree on balances and votes

### WebRTC + SynapseSub Tests

```bash
./test_webrtc.sh
```

**Verifies:**
- Direct WebRTC connections
- PubSub statistics
- Gossip via DataChannel
- Debug logs

### Decentralized P2P Tests

```bash
./test_p2p.sh
```

**Verifies:**
- Bootstrap from peers
- P2P signaling tunneling
- Gossip without Rendezvous
- Fully autonomous network

## 🏗️ Detailed Architecture

### File Structure

```
synapse-ng/
├── app/
│   ├── main.py                    # Application server
│   ├── webrtc_manager.py          # WebRTC connection manager
│   ├── synapsesub_protocol.py     # PubSub protocol
│   ├── identity.py                # Cryptographic identity
│   └── templates/                 # UI templates
├── rendezvous/
│   └── main.py                    # Rendezvous server (optional)
├── docker-compose.yml             # Rendezvous mode config
├── docker-compose.p2p.yml         # P2P mode config
├── test_suite.sh                  # Complete test suite
├── test_webrtc.sh                 # WebRTC/PubSub tests
├── test_p2p.sh                    # Pure P2P tests
└── README.md                      # This file
```

### Communication Flow

```
┌─────────┐                      ┌─────────┐
│ Node A  │                      │ Node B  │
└────┬────┘                      └────┬────┘
     │                                │
     │ 1. Bootstrap/Discovery         │
     │───────────────────────────────>│
     │                                │
     │ 2. WebRTC Signaling            │
     │<──────────────────────────────>│
     │   (Rendezvous or P2P Tunnel)   │
     │                                │
     │ 3. RTCDataChannel Open         │
     │<═══════════════════════════════>│
     │                                │
     │ 4. ANNOUNCE Topic              │
     │───SynapseSub──────────────────>│
     │   (channel subscription)       │
     │                                │
     │ 5. MESSAGE (Gossip)            │
     │<══SynapseSub══════════════════>│
     │    Topic: channel:dev:state    │
     │    (only if both               │
     │     subscribed to topic!)      │
     │                                │
     │ 6. Forward to other peers      │
     │         in the mesh            │
     └────────────────────────────────┘
```

**Flow Notes:**
- Step 4: Nodes announce topics they're interested in (`SUBSCRIBED_CHANNELS`)
- Step 5: Messages are forwarded **only to peers subscribed** to the topic
- If a node is not subscribed, it won't receive messages on that topic

### CRDT and Convergence

Distributed state uses **Last-Write-Wins (LWW)** based on timestamps:

```python
# Merge logic (app/main.py:196-201)
if incoming_task["updated_at"] > local_task["updated_at"]:
    local_state["tasks"][task_id] = incoming_task
```

- **Transition validation**: Only at API endpoints
- **In gossip**: Timestamp is source of truth
- **Convergence**: Mathematically guaranteed (CRDT)

### Reputation and Weighted Voting System

**Reputation Calculation:**
```python
# Actions that increase reputation
- Task completion: +10
- Proposal vote: +1

# Calculation (app/main.py:846-858)
for task in channel.tasks:
    if task.status == "completed":
        reputation[task.assignee] += 10

for proposal in channel.proposals:
    for voter_id in proposal.votes:
        reputation[voter_id] += 1
```

**Weighted Voting:**
```python
# Vote weight based on reputation (app/main.py:914-915)
def calculate_vote_weight(reputation: int) -> float:
    return 1.0 + math.log2(reputation + 1)

# Examples:
# Reputation 0 → Weight 1.0
# Reputation 1 → Weight 2.0
# Reputation 20 → Weight 5.4
# Reputation 100 → Weight 7.7

# Proposal outcome (app/main.py:966-969)
if yes_weight > no_weight:
    outcome = "approved"
else:
    outcome = "rejected"
```

**Practical Example:**
```
Scenario: Proposal with 3 nodes
- Node A: reputation 20 (2 completed tasks) → vote weight ~5.4
- Node B: reputation 1 (1 vote) → vote weight ~2.0
- Node C: reputation 0 → vote weight 1.0

Voting:
- Node A votes NO → weight 5.4
- Node B votes YES → weight 2.0
- Node C votes YES → weight 1.0

Result:
- YES total: 3.0
- NO total: 5.4
- Outcome: REJECTED ✅

Meritocracy prevails: the most experienced node has more influence!
```

## 🔮 Future Roadmap

- [ ] **mDNS Discovery**: Local discovery without bootstrap
- [ ] **DHT**: Distributed Hash Table for peer lookup
- [ ] **E2E Encryption**: Payload encryption beyond WebRTC
- [ ] **NAT Traversal**: Integrated STUN/TURN
- [ ] **Mobile Nodes**: Support for mobile/intermittent nodes
- [ ] **Dynamic Sharding**: Automatic channel balancing
- [ ] **Advanced Consensus**: Raft/PBFT for critical decisions

## 🤝 Contributing

Contributions welcome! For important features, please open an issue first to discuss.

```bash
# Development setup
pip install -r requirements.txt

# Run local node
python -m uvicorn app.main:app --reload --port 8000
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Inspired by:
- **libp2p**: Modular P2P networking stack
- **GossipSub**: PubSub protocol for mesh networks
- **WebRTC**: P2P standard for the web
- **IPFS**: InterPlanetary File System
- **Holochain**: Agent-centric distributed computing

---

**Synapse-NG** - Where each node is a neuron, and together they form a living organism. 🧠✨
