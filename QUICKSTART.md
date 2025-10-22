# 🚀 Quick Start - Your First Contribution

**In 5 minuti scopri come Synapse-NG ti ricompensa direttamente per i tuoi contributi.**

---

## 🎯 What You'll Do

1. Find a bug (or typo, or anything improvable)
2. Create a GitHub issue
3. Claim a task
4. Complete it
5. **Receive Synapse Points + Reputation automatically**

No approvals. No waiting. The system self-executes.

---

## ⚡ Setup (30 seconds)

### Prerequisites
- Docker & Docker Compose installed
- Git installed

### Start the Network

```bash
# Clone the repo
git clone https://github.com/fabriziosalmi/synapse-ng.git
cd synapse-ng

# Start 3 nodes
docker-compose up -d

# Wait 15 seconds for network stabilization
sleep 15

# Verify nodes are online
curl http://localhost:8001/health  # Node 1
curl http://localhost:8002/health  # Node 2
curl http://localhost:8003/health  # Node 3
```

---

## 🧪 Run the First Experiment

This automated test demonstrates the core principle:

```bash
./test_first_task_experiment.sh
```

**What happens:**
1. Node 1 creates a task: "Find the first bug" (reward: 10 SP)
2. Node 2 claims and completes it
3. Node 2 receives 10 SP + reputation
4. All nodes agree on the new state
5. **No manager approved anything**

Expected output:
```
✓ Creator paid 10 SP
✓ Contributor received ~10 SP
✓ Contributor gained reputation
✓ Consensus reached on all nodes

🎉 EXPERIMENT SUCCESSFUL!
```

---

## 🐛 Your Turn: Find a Real Bug

### Step 1: Explore the System

```bash
# Read the docs
cat README.md
cat docs/GETTING_STARTED.md

# Try commands
curl http://localhost:8001/state | jq .

# Create a test task
curl -X POST "http://localhost:8001/tasks?channel=test" \
  -H "Content-Type: application/json" \
  -d '{"title": "My test task", "reward": 5}'

# Look for anything weird
```

### Step 2: Document What You Found

Create a GitHub issue:
```
Title: [Bug] <Brief description>

Found in: <File/command/endpoint>

Expected: <What should happen>
Actual: <What actually happens>

Steps to reproduce:
1. ...
2. ...

Labels: bug, first-contribution
```

### Step 3: Claim the Real Task

Once the "First Bug" task is created on the network:

```bash
# Get task ID (ask in Discord/Telegram)
TASK_ID="<task_id_from_creator>"

# Claim it (from Node 2)
curl -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui"

# Progress
curl -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui"

# Complete (paste your GitHub issue URL)
curl -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui"
```

### Step 4: Check Your Rewards

```bash
# Get your node ID
MY_NODE_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | keys[0]')

# Check balance
curl -s http://localhost:8002/state | jq ".global.nodes.\"$MY_NODE_ID\".balance"

# Check reputation
curl -s http://localhost:8002/reputations | jq ".\"$MY_NODE_ID\""
```

---

## 🎁 What You Get

### Synapse Points (SP)
- Internal currency of the network
- Used to create tasks, vote on proposals
- Tradeable value within the ecosystem

### Reputation
- Earned by completing tasks (+10 per task)
- Increases your voting power
- Makes you eligible for validator set
- Gives you competitive advantage in auctions

### Recognition
- Your contribution is permanently recorded in the network state
- All nodes agree on your contribution
- No central authority can revoke it

---

## 📚 Next Steps

### Learn More
- [Complete Architecture](docs/SYNAPSE_COMPLETE_ARCHITECTURE.md)
- [Auction System](docs/AUCTION_SYSTEM.md) - Competitive task bidding
- [Governance](docs/GOVERNANCE_SYSTEM.md) - Weighted voting
- [AI Agents](docs/AI_AGENT.md) - Autonomous task execution

### Join the Community
- GitHub: [Issues](https://github.com/fabriziosalmi/synapse-ng/issues)
- Telegram: [Join here]
- Discord: [Join here]

### Create Your Own Tasks
```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Improve documentation",
    "description": "Fix typos in README.md",
    "reward": 15,
    "tags": ["docs", "easy"]
  }'
```

### Try Auctions
```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build new feature",
    "enable_auction": true,
    "max_reward": 100,
    "auction_deadline_hours": 24
  }'
```

---

## 🧬 The Core Principle

> **Contribution → Value**

You provide value (bug report, feature, doc improvement).  
You receive value (SP + reputation).  
No middleman. No approval. Just execution.

This is not a test. This is the future of work.

Welcome to the organism. 🌟

---

**Ready?** Run `./test_first_task_experiment.sh` and see it for yourself.
