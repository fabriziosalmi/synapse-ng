# 🧬 Synapse-NG: The Autonomous Digital Organism

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

**A self-governing, self-funding, self-evolving decentralized network.**

Synapse-NG is not just a peer-to-peer network—it's a **living digital organism** that can think, decide, evolve, and own resources. There is no central authority, no mandatory server, no traditional leader. Each node is an autonomous agent that collaborates to form a collective intelligence capable of making decisions, completing tasks, acquiring shared resources, and continuously improving itself.

---

## 🎯 Vision

**Synapse-NG represents a new paradigm: a decentralized organism that can:**

- 🧠 **Think** - Optional AI agents analyze network state and propose optimizations
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

---

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

## 🚀 Installation

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **Python 3.10+** (for local development)
- **`jq`** (for test scripts)

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/synapse-ng.git
cd synapse-ng

# Start 3-node network
docker-compose up --build -d

# Check network status
curl http://localhost:8001/state | jq '.global.nodes | length'
# Expected output: 3

# Run test suite
./test_suite.sh
```

### Manual Setup (Local Development)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Generate node identity
python3 -c "
from app.identity import generate_identity
import os
os.makedirs('data/node-1', exist_ok=True)
generate_identity('data/node-1')
print('✅ Identity generated')
"

# Start node
export NODE_ID="node-1"
export HTTP_PORT=8000
python3 app/main.py
```

---

## 🧪 Testing

### Run Complete Test Suite

```bash
./test_suite.sh
```

**Tests Coverage:**
- ✅ Network convergence (CRDT state synchronization)
- ✅ WebRTC P2P connections
- ✅ SynapseSub message propagation
- ✅ Task lifecycle (create → claim → complete)
- ✅ Reputation v2 (tag-based, decay)
- ✅ Weighted voting (contextual)
- ✅ Synapse Points economy
- ✅ Auction system
- ✅ Common Tools execution
- ✅ Network operations (governance commands)

### Targeted Testing

```bash
# Base network tests only
./test_suite.sh base

# Governance tests only
./test_suite.sh governance

# Economy tests only
./test_suite.sh economy

# Common Tools tests
./test_common_tools_experiment.sh
```

---

## 📡 Key API Endpoints

### Status & Monitoring

```bash
# Network state
GET /state

# Connected peers
GET /peers

# Channel list
GET /channels
```

### Tasks

```bash
# Create task
POST /tasks?channel={CHANNEL_ID}
{
  "title": "Implement feature X",
  "tags": ["python", "security"],
  "reward": 100
}

# Claim task
POST /tasks/{task_id}/claim?channel={CHANNEL_ID}

# Complete task
POST /tasks/{task_id}/complete?channel={CHANNEL_ID}
```

### Governance

```bash
# Create proposal
POST /proposals?channel={CHANNEL_ID}
{
  "title": "Upgrade security protocol",
  "tags": ["security", "protocol"],
  "proposal_type": "network_operation",
  "params": {...}
}

# Vote on proposal
POST /proposals/{proposal_id}/vote?channel={CHANNEL_ID}
{
  "vote": "yes"
}

# Close and tally votes
POST /proposals/{proposal_id}/close?channel={CHANNEL_ID}

# Validator ratification
POST /governance/ratify/{proposal_id}?channel={CHANNEL_ID}
```

### Common Tools

```bash
# Propose acquisition
POST /proposals?channel={CHANNEL_ID}
{
  "title": "Acquire Geolocation API Tool",
  "description": "Proposal to acquire a tool for geolocation services.",
  "proposal_type": "command",
  "command": {
    "operation": "acquire_common_tool",
    "params": {
      "tool_id": "geolocation_api",
      "monthly_cost_sp": 100,
      "credentials_to_encrypt": "API_KEY_HERE",
      "description": "Geolocation API for analytics tasks",
      "type": "api_key",
      "channel": "{CHANNEL_ID}"
    }
  }
}

# Execute tool (authorized task assignees only)
POST /tools/{tool_id}/execute?channel={CHANNEL_ID}&task_id={TASK_ID}
{
  "ip_address": "8.8.8.8"
}
```

---

## 📚 Documentation

For comprehensive guides on each subsystem, see the `/docs` directory:

| Guide | Description |
|-------|-------------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Complete system architecture |
| **[GOVERNANCE.md](docs/GOVERNANCE.md)** | Governance, reputation v2, contextual voting |
| **[ECONOMY.md](docs/ECONOMY.md)** | SP, auctions, treasury, common tools |
| **[INTELLIGENCE.md](docs/INTELLIGENCE.md)** | AI agents, self-upgrade, network singularity |
| **[SECURITY.md](docs/SECURITY.md)** | Security model, encryption, threat analysis |
| **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** | Comprehensive testing documentation |
| **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** | Installation and setup guide |
| **[AI_ORCHESTRATION_WORKFLOW.md](docs/AI_ORCHESTRATION_WORKFLOW.md)** | How this project was built with AI |

---

## 🔮 Roadmap

- [x] Core P2P network (WebRTC + SynapseSub)
- [x] Two-tier governance (CRDT + Raft)
- [x] Reputation system v2 (tag-specialized + decay)
- [x] Economic system (SP + auctions + treasury)
- [x] Common Tools (network-owned resources)
- [x] Self-upgrade (WASM sandbox)
- [x] AI integration (optional local LLM)
- [x] Network Singularity (AI code generation)
- [ ] Complete Raft implementation (full leader election)
- [ ] Dynamic sharding (automatic load balancing)
- [ ] E2E encryption (beyond WebRTC)
- [ ] Mobile node support (intermittent connectivity)
- [ ] DHT integration (distributed peer lookup)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. **Read** [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
2. **Open an issue** first for major changes
3. **Follow** commit message conventions in [docs/COMMIT_MESSAGE.md](docs/COMMIT_MESSAGE.md)

---

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

This project demonstrates what's possible when human expertise guides AI capabilities. Synapse-NG was architected and implemented through structured AI collaboration, proving that the future of software development is **human-AI partnership**.

**Built with:**
- Python, FastAPI, uvicorn
- aiortc (WebRTC)
- Docker
- Love for decentralized systems ❤️

---

**Status**: ✅ Production-Ready | **Version**: 2.0 | **Last Updated**: October 2025
