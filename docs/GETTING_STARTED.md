# 🚀 Getting Started with Synapse-NG

**Welcome to Synapse-NG - The Autonomous Decentralized Network**

This guide will get you up and running in less than 10 minutes.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL2)
- **Python**: 3.10 or higher
- **RAM**: Minimum 2GB, recommended 4GB+
- **Disk**: 1GB free space

### Required Software
```bash
# Check Python version
python3 --version  # Should be >= 3.10

# Check pip
pip3 --version
```

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/fabriziosalmi/synapse-ng.git
cd synapse-ng
```

### 2. Install Dependencies
```bash
pip3 install -r requirements.txt
```

**Core dependencies**:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `aiortc` - WebRTC implementation
- `cryptography` - Cryptographic operations
- `httpx` - HTTP client

**Optional dependencies** (for advanced features):
```bash
# AI Agent (local LLM)
pip3 install llama-cpp-python

# Self-Upgrade System (WASM execution)
pip3 install wasmtime ipfshttpclient

# ZKP Voting (zero-knowledge proofs)
pip3 install py_arkworks_bls12381

# WASM Compilation
rustup target add wasm32-unknown-unknown
```

### 3. Generate Node Identity
Each node needs cryptographic keys:
```bash
python3 -c "
from app.identity import generate_identity
import os

node_name = 'node-1'
data_dir = f'data/{node_name}'
os.makedirs(data_dir, exist_ok=True)

ed25519_priv, ed25519_pub, x25519_priv, x25519_pub = generate_identity(data_dir)
print(f'✅ Identity generated for {node_name}')
print(f'   Ed25519 Public Key: {ed25519_pub.hex()[:32]}...')
print(f'   Keys saved to {data_dir}/')
"
```

---

## 🎬 Quick Start

### Launch Your First Node

**Simple setup** (single node):
```bash
export NODE_ID="node-$(uuidgen | cut -d'-' -f1)"
export HTTP_PORT=8000
export DATA_DIR="data/${NODE_ID:0:8}"

python3 app/main.py
```

You should see:
```
🚀 Synapse-NG Node Starting...
✅ Identity loaded: node-abc12345
🌐 HTTP API listening on 0.0.0.0:8000
🔄 Background loops started
```

### Test the API

Open another terminal:
```bash
# Check node status
curl http://localhost:8000/state | jq

# Get network info
curl http://localhost:8000/peers | jq

# Create a channel
curl -X POST http://localhost:8000/channels \
  -H "Content-Type: application/json" \
  -d '{"name": "general", "description": "General discussion"}'
```

---

## 🧪 Run Quick Tests

### Test Script
```bash
chmod +x test_network.sh
./test_network.sh
```

This will test:
- ✅ Node startup
- ✅ API endpoints
- ✅ Channel creation
- ✅ Task system
- ✅ Governance proposals

### Expected Output
```
==================================================
🧪 Test Synapse-NG Network
==================================================

1️⃣  Starting node...
✅ Node started on port 8000

2️⃣  Testing API endpoints...
✅ /state endpoint working
✅ /peers endpoint working

3️⃣  Testing channels...
✅ Channel created: general

... (more tests)

==================================================
✅ ALL TESTS PASSED
==================================================
```

---

## 🌐 Multi-Node Network

### Setup 3-Node Network

**Terminal 1** (Node 1):
```bash
export NODE_ID="node-1"
export HTTP_PORT=8001
python3 app/main.py
```

**Terminal 2** (Node 2):
```bash
export NODE_ID="node-2"
export HTTP_PORT=8002
export BOOTSTRAP_PEER="http://localhost:8001"
python3 app/main.py
```

**Terminal 3** (Node 3):
```bash
export NODE_ID="node-3"
export HTTP_PORT=8003
export BOOTSTRAP_PEER="http://localhost:8001"
python3 app/main.py
```

### Docker Compose (Recommended)
```bash
docker-compose up -d
```

This starts:
- 3 Synapse-NG nodes (ports 8001-8003)
- 1 Rendezvous server (optional, port 8080)
- 1 TURN server (optional, for NAT traversal)

Check status:
```bash
docker-compose ps
docker-compose logs -f node-1
```

---

## 🎯 Basic Concepts

### 1. **Channels**
Channels are topical spaces for communication and collaboration.

```bash
# Create channel
curl -X POST http://localhost:8000/channels \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dev-team",
    "description": "Development discussions"
  }'

# List channels
curl http://localhost:8000/channels
```

### 2. **Tasks**
Distributed task system with SP rewards.

```bash
# Create task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement feature X",
    "description": "Add new consensus algorithm",
    "channel": "dev-team",
    "reward": 100,
    "required_skills": ["rust", "distributed-systems"]
  }'

# Claim task
curl -X POST http://localhost:8000/tasks/task-123/claim

# Submit task
curl -X POST http://localhost:8000/tasks/task-123/submit \
  -H "Content-Type: application/json" \
  -d '{"result": "Implemented successfully"}'
```

### 3. **Governance**
Democratic decision-making with proposals and voting.

```bash
# Create proposal
curl -X POST http://localhost:8000/proposals \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Increase task rewards",
    "description": "Raise minimum task reward from 50 to 100 SP",
    "proposal_type": "config_change",
    "channel": "global"
  }'

# Vote on proposal
curl -X POST http://localhost:8000/proposals/prop-123/vote \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve"}'
```

### 4. **Reputation**
Earn reputation through contributions.

```bash
# Check your reputation
curl http://localhost:8000/state | jq '.global.nodes["node-123"].reputation'

# View reputation leaderboard
curl http://localhost:8000/reputation
```

---

## 🔧 Configuration

### Environment Variables

**Basic**:
```bash
export NODE_ID="node-unique-id"          # Unique node identifier
export HTTP_PORT=8000                     # API port
export DATA_DIR="data/node-unique-id"    # Data directory
```

**Network**:
```bash
export BOOTSTRAP_PEER="http://peer:8000" # Initial peer to connect
export RENDEZVOUS_URL="http://rdv:8080"  # Optional rendezvous server
export ENABLE_MDNS="true"                 # Local network discovery
```

**Features**:
```bash
# AI Agent (requires LLM model)
export AI_MODEL_PATH="models/qwen3-0.6b.gguf"

# Evolutionary Engine (Phase 7)
export ENABLE_AUTO_EVOLUTION="false"      # Enable AI code generation
export EVOLUTIONARY_LLM_PATH="models/qwen3-0.6b.gguf"
export EVOLUTION_SAFETY_THRESHOLD="0.7"   # Auto-propose threshold

# Self-Upgrade System
export ENABLE_AUTO_UPGRADE="false"        # Enable auto-upgrades
```

### Configuration File
Create `config.env`:
```bash
# Copy example
cp config.env.example config.env

# Edit configuration
nano config.env

# Load configuration
source config.env
python3 app/main.py
```

---

## 📚 Next Steps

**Now that you have a node running:**

1. **Learn the Architecture** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Explore Governance** → See [GOVERNANCE.md](GOVERNANCE.md)
3. **Try Advanced Features**:
   - [AI Agent](AI_AGENT.md) - Local LLM integration
   - [Self-Upgrade](SELF_UPGRADE.md) - Autonomous code updates
   - [Network Singularity](PHASE_7_NETWORK_SINGULARITY.md) - AI writes code
4. **Deploy to Production** → Follow [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
5. **Contribute** → Check [DEVELOPMENT.md](DEVELOPMENT.md)

---

## 🆘 Troubleshooting

### Node Won't Start

**Issue**: `ImportError: No module named 'app'`
```bash
# Make sure you're in the project root
cd /path/to/synapse-ng
python3 app/main.py
```

**Issue**: `Address already in use`
```bash
# Change port
export HTTP_PORT=8001
python3 app/main.py
```

### Can't Connect to Peers

**Issue**: No peers found
```bash
# Check if bootstrap peer is reachable
curl http://bootstrap-peer:8000/state

# Enable mDNS for local discovery
export ENABLE_MDNS="true"
```

**Issue**: WebRTC connection fails
```bash
# Use TURN server for NAT traversal
docker-compose -f docker-compose.turn.yml up -d
```

### Performance Issues

**Issue**: High CPU usage
```bash
# Reduce background loop frequency in config
# Or disable unused features
export ENABLE_AUTO_EVOLUTION="false"
```

### Get Help

- **Documentation**: Check [docs/](../docs/)
- **Tests**: Run `./test_network.sh` to diagnose issues
- **Logs**: Check terminal output for error messages
- **GitHub Issues**: Report bugs at [github.com/fabriziosalmi/synapse-ng/issues](https://github.com/fabriziosalmi/synapse-ng/issues)

---

## 🎓 Learning Path

**For Beginners**:
1. ✅ This guide (you are here!)
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
3. [API_REFERENCE.md](API_REFERENCE.md) - Learn the API
4. [TESTING.md](TESTING.md) - Run tests

**For Advanced Users**:
1. [GOVERNANCE.md](GOVERNANCE.md) - Deep dive into governance
2. [ECONOMY.md](ECONOMY.md) - Economic mechanisms
3. [AI_AGENT.md](AI_AGENT.md) - AI integration
4. [PHASE_7_NETWORK_SINGULARITY.md](PHASE_7_NETWORK_SINGULARITY.md) - Autonomous evolution

**For Developers**:
1. [DEVELOPMENT.md](DEVELOPMENT.md) - Contributing guide
2. [SCHEMA_VALIDATION.md](SCHEMA_VALIDATION.md) - Data validation
3. [ZKP_GUIDE.md](ZKP_GUIDE.md) - Privacy features

---

**🎉 Congratulations! You're now part of the autonomous network.**

Ready to dive deeper? Continue to [ARCHITECTURE.md](ARCHITECTURE.md) →
