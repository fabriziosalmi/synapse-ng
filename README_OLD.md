# 🧬 Synapse-NG: The Autonomous Digital Organism

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**A self-governing, self-funding, self-evolving decentralized network.**

Synapse-NG is not just a peer-to-peer network—it's a **living digital organism** that can think, decide, evolve, and own resources. There is no central authority, no mandatory server, no traditional leader. Each node is an autonomous agent that collaborates to form a collective intelligence capable of making decisions, completing tasks, acquiring shared resources, and continuously improving itself.

---

## 🎯 Vision

**Synapse-NG represents a new paradigm: a decentralized organism that can:**

- � **Think** - Optional AI agents analyze network state and propose optimizations
- 🗳️ **Decide** - Democratic governance with specialized reputation and contextual voting
- 💰 **Own** - Collective treasury funds common resources (API keys, services, credentials)
- 🔄 **Evolve** - Self-upgrade system enables autonomous code evolution
- 🤝 **Collaborate** - Temporary teams form organically for complex multi-skill tasks
- 🛡️ **Protect** - Zero-knowledge voting, encrypted credentials, sandboxed execution

**No central server. No single authority. No developer "pushing" updates. Pure collective intelligence.**

---

## ⚡ Quick Start

**New to Synapse-NG? Start here:**

- **[📚 Getting Started Guide](docs/GETTING_STARTED.md)** - Setup your first node in 10 minutes
- **[🧪 Testing Guide](docs/TESTING_GUIDE.md)** - Run comprehensive test suite
- **[⚡ Quick Start](QUICKSTART.md)** - 5-minute contribution walkthrough (if available)

---

## 📖 Core Concepts

## 📖 Core Concepts

Synapse-NG's knowledge base is organized into thematic guides. Each document is comprehensive, updated, and reflects the current state of the implemented system.

### 🏗️ Architecture and P2P Network
**[Architecture Guide](docs/ARCHITECTURE.md)** - The complete blueprint of the digital organism
- Three-layer communication stack (WebRTC → SynapseSub → Application)
- P2P connectivity, topic-based routing, CRDT state synchronization
- Cryptographic identity, peer discovery, and mesh topology

### 🗳️ Governance and Decision-Making
**[Governance Guide](docs/GOVERNANCE.md)** - The nervous system that coordinates collective decisions
- Two-tier governance (Community CRDT voting + Validator Raft ratification)
- **Reputation v2**: Dynamic, specialized reputation with tag-based expertise tracking
- **Contextual voting**: Your influence scales with your expertise in proposal topics
- Zero-knowledge proof anonymous voting for sensitive decisions
- Executable proposals (`command` type) that modify network state deterministically

### 💰 Economic System and Incentives
**[Economy Guide](docs/ECONOMY.md)** - The metabolic system that sustains the organism
- **Synapse Points (SP)**: Internal currency for rewarding contributions
- **Auction System**: Market-based task allocation with bid competition
- **Reputation v2**: Tag-specialized expertise with time decay (incentivizes continuous activity)
- **Common Tools (Beni Comuni)**: 🆕 Network-owned resources financed by treasury
  - Collective ownership of API keys, services, and credentials
  - Encrypted storage with secure execution endpoints
  - Automatic monthly maintenance from channel treasury
  - Democratic acquisition through governance proposals

### 🧠 Intelligence and Autonomous Evolution
**[Intelligence Guide](docs/INTELLIGENCE.md)** - The brain that learns and adapts
- **AI Agents** (optional): Local LLM integration for autonomous decision-making
- **Self-Upgrade System**: WASM-sandboxed code evolution through governance
- **Network Singularity** (optional): AI-powered autonomous code generation
- Collaborative teams for complex multi-skill tasks

### 🔐 Security and Privacy
**[Security Guide](docs/SECURITY.md)** - The immune system that protects the organism
- Cryptographic identity (Ed25519), signature verification
- WebRTC encrypted channels (DTLS/SRTP)
- Common Tools credential encryption (AESGCM + HKDF key derivation)
- WASM sandbox isolation for self-upgrade execution
- Reputation-based sybil resistance
- Threat model analysis and mitigation strategies

### 🧪 Testing and Quality Assurance
**[Testing Guide](docs/TESTING_GUIDE.md)** - Validation and quality control
- Comprehensive test suite (network, governance, economy, reputation v2, common tools)
- Automated test scenarios with deterministic outcomes
- Performance benchmarks and quality metrics

### 🚀 Getting Started
**[Getting Started Guide](docs/GETTING_STARTED.md)** - Your first steps with Synapse-NG
- Installation and setup (Docker + Python)
- Running your first node
- Multi-node network deployment
- Configuration and environment variables

---

## 🤖 A Project Co-Created with AI

**Synapse-NG is built through human-AI collaboration.**

This project demonstrates a unique development workflow where an **AI Orchestrator** (human expert) guides multiple AI agents through complex, multi-phase implementation work. The result is a system of extraordinary depth and coherence.

📖 **[Read: Our AI Orchestration Workflow](docs/AI_ORCHESTRATION_WORKFLOW.md)**

Learn how we use structured prompts, iterative refinement, and AI as a thought partner to build systems that would take months with traditional development.

---

## 🏗️ System Status

**Current Version**: 2.0 (Evolved)  
**Status**: ✅ Production-Ready

### Implemented Features

✅ **Core P2P Network** - WebRTC, SynapseSub protocol, CRDT state  
✅ **Two-Tier Governance** - Community voting + Validator ratification  
✅ **Reputation System v2** - Tag-specialized, time-decay, contextual voting  
✅ **Economic System** - SP, auctions, treasuries, automatic taxes  
✅ **Common Tools System** - Network-owned encrypted resources  
✅ **Self-Upgrade** - WASM-sandboxed autonomous code evolution  
✅ **Collaborative Teams** - Multi-skill task coordination  
✅ **AI Integration** (optional) - Local LLM agents, autonomous analysis  
✅ **Network Singularity** (optional) - AI-generated code proposals  
✅ **Security** - Encrypted credentials, ZKP voting, sandbox isolation

### Recent Evolutions

🧬 **Reputation v2** (October 2025)
- Migrated from simple integer to dynamic specialized system
- Tag-based expertise tracking (`{"python": 50, "security": 70}`)
- Contextual vote weighting (expertise amplifies influence)
- Time decay mechanism (-1% daily, encourages continuous contribution)

🛠️ **Common Tools** (October 2025)  
- Network can now own and manage shared resources
- Treasury-funded API keys, services, credentials
- AESGCM encryption with HKDF key derivation
- Three-layer authorization (status, task assignment, tool requirement)
- Automatic monthly maintenance with funding checks
- Governance-based acquisition/deprecation

---

## ⚙️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│            APPLICATION LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Channels │  │  Tasks   │  │Governance│     │
│  │ Treasury │  │ Auctions │  │ Rep. v2  │     │
│  │ Common   │  │  Teams   │  │ Commands │     │
│  │  Tools   │  │          │  │          │     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│          SYNAPSESUB PROTOCOL                    │
│  ┌──────────────────────────────────────┐      │
│  │  Topic-Based PubSub + Routing        │      │
│  │  ANNOUNCE | MESSAGE | I_HAVE | ...   │      │
│  └──────────────────────────────────────┘      │
├─────────────────────────────────────────────────┤
│         WEBRTC TRANSPORT LAYER                  │
│  ┌──────────────────────────────────────┐      │
│  │   P2P Connections + Data Channels     │      │
│  │   Encrypted (DTLS/SRTP)               │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Installation & Quick Start

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

# Ratify network_operation proposal (validators only)
POST /governance/ratify/{proposal_id}?channel=CHANNEL_ID
```

### **Network Operations (Self-Evolution)**

```bash
# Create network operation proposal (split channel)
POST /proposals?channel=global
Content-Type: application/json
{
  "title": "Split general channel",
  "proposal_type": "network_operation",
  "params": {
    "operation": "split_channel",
    "target_channel": "general",
    "new_channels": ["backend", "frontend"],
    "split_logic": "by_tag",
    "split_params": {
      "backend": ["api", "database"],
      "frontend": ["ui", "ux"]
    }
  }
}

# Create network operation proposal (merge channels)
POST /proposals?channel=global
Content-Type: application/json
{
  "title": "Merge channels",
  "proposal_type": "network_operation",
  "params": {
    "operation": "merge_channels",
    "source_channels": ["backend", "frontend"],
    "target_channel": "development"
  }
}

# Check execution log
GET /state
# Look at: .global.execution_log
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

Tests convergence, WebRTC, PubSub, task lifecycle, reputation, economy, governance, and network operations.

```bash
# All tests (base + economy + governance + operations)
./test_suite.sh

# Base tests only
./test_suite.sh base

# Governance tests only (weighted voting)
./test_suite.sh governance

# Economy tests only (Synapse Points)
./test_suite.sh economy

# Network operations test (self-evolution)
./test_network_operations.sh

# Schema validation test (type safety)
./test_schema_validation.sh

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

**Network Operations Tests (Scenario 9):**
9. ✅ **Self-Evolution**: Complete flow of network_operation proposal → vote → ratify → execute (split/merge channels)

**Schema Validation Tests (Scenario 10):**
10. ✅ **Type Safety**: Schema validation at creation time and gossip time, rejection of invalid data ✨ **NEW**

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
├── test_network_operations.sh     # Network self-evolution tests
├── test_schema_validation.sh      # Schema validation tests
├── test_auction.sh                # Auction system tests 🔨 **NEW**
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

## 📖 Additional Documentation

For detailed documentation on specific topics, see:

- **[Security Considerations](docs/SECURITY.md)** - Threat model, security measures, and mitigation strategies
- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute to Synapse-NG
## 🔮 Future Roadmap

- [x] **Two-Tier Governance**: Validator set + Raft consensus
- [x] **Reputation System**: Merit-based network participation
- [x] **Economic System**: Synapse Points with treasury
- [x] **Network Operations**: Self-evolution via split/merge channels
- [x] **Executive System**: Deterministic command execution across all nodes
- [x] **Schema Validation**: Type-safe data structures with automatic validation
- [x] **Auction System**: Market-based task allocation with competitive bidding
- [x] **Self-Upgrade System**: Autonomous code evolution with WASM sandboxing
- [x] **AI-Powered Evolution**: Network generates and proposes code upgrades
- [ ] **Dynamic Sharding**: Automatic channel balancing via network operations
- [ ] **Complete Raft Implementation**: Full leader election and log replication
- [ ] **Operation Rollback**: Automatic rollback on execution failure
- [ ] **E2E Encryption**: Payload encryption beyond WebRTC
- [ ] **DHT**: Distributed Hash Table for peer lookup
- [ ] **Mobile Nodes**: Support for mobile/intermittent nodes

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
