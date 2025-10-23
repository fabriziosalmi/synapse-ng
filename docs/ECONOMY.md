# 💰 Economic System: The Metabolic Engine

**Complete Economy Guide - Synapse Points, Auctions, Teams, and Common Tools**

Version: 2.0 (Evolved)  
Last Updated: October 2025  
Status: ✅ Production-Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Synapse Points (SP)](#synapse-points-sp)
3. [Auction System](#auction-system)
4. [Reputation v2 Economics](#reputation-v2-economics)
5. [Treasury and Taxes](#treasury-and-taxes)
6. [Common Tools (Beni Comuni)](#common-tools-beni-comuni) 🆕
7. [Collaborative Teams](#collaborative-teams)
8. [Economic Flows](#economic-flows)

---

## 🎯 Overview

Synapse-NG's economic system creates a **self-sustaining internal economy** where:

- 💰 **Synapse Points (SP)** serve as the internal currency
- 🏆 **Auctions** allocate tasks based on cost, reputation, and speed
- 📈 **Reputation v2** creates specialized expertise markets
- 🏦 **Treasuries** fund community-owned resources
- 🛠️ **Common Tools** enable collective resource ownership
- 🤝 **Teams** tackle complex multi-skill tasks

**Key Innovation**: The network can **own and manage shared resources** (API keys, services, credentials) financed collectively through channel treasuries.

---

## 💰 Synapse Points (SP)

### What Are Synapse Points?

**SP** is the internal currency that:
- Rewards task completion
- Funds new tasks
- Finances common resources
- Represents economic contribution

### Initial Distribution

```python
# Default config
INITIAL_BALANCE_SP = 1000

# Every node starts with 1000 SP
network_state["global"]["nodes"][node_id]["balance_sp"] = 1000
```

### Earning SP

**Task Completion**:
```python
# When you complete a task with reward=100 SP
tax = max(1, round(100 * 0.02))  # 2% tax, min 1 SP
your_earnings = 100 - tax  # 98 SP

balances[your_id] += 98
treasury[channel] += 2
```

**Not Earned by**:
- Voting (earns reputation, not SP)
- Creating proposals
- Joining network

### Spending SP

**Creating Tasks**:
```python
# When you create task with reward=100 SP
balances[your_id] -= 100  # Frozen until task completion
```

**Treasury Contributions** (indirect):
- 2% of every task reward goes to channel treasury
- Treasury funds common tools

---

## 🏆 Auction System

### Why Auctions?

**Traditional Problem**: First-come-first-served favors fast clickers, not skilled contributors

**Auction Solution**: Tasks allocated based on:
- **Cost** (40% weight) - Lower bids preferred
- **Reputation** (40% weight) - Proven track record
- **Time** (20% weight) - Faster delivery

### Auction Lifecycle

```
1. TASK CREATED WITH AUCTION
   ├─> Status: "auction_open"
   ├─> max_reward: 500 SP
   ├─> deadline: 48 hours
   └─> bids: {}

2. NODES PLACE BIDS
   ├─> Node A: amount=450, days=3, reputation=120
   ├─> Node B: amount=400, days=5, reputation=80
   └─> Node C: amount=480, days=2, reputation=200

3. DEADLINE REACHED (or manual close)
   └─> Winning bid selection algorithm runs

4. WINNER SELECTED
   ├─> Status: "claimed"
   ├─> assignee: winner_id
   ├─> reward: winning_bid.amount
   └─> Task proceeds normally
```

### Bid Scoring Algorithm

```python
def score_bid(bid, max_reward):
    # Normalize factors (0-1 range)
    cost_score = 1.0 - (bid.amount / max_reward)
    reputation_score = min(1.0, bid.reputation / 1000)
    time_score = 1.0 - min(1.0, bid.estimated_days / 30)
    
    # Weighted average
    final_score = (
        cost_score * 0.4 +
        reputation_score * 0.4 +
        time_score * 0.2
    )
    
    return final_score

# Highest score wins
winner = max(bids, key=lambda b: score_bid(b, max_reward))
```

### Example Scenario

**Task**: Implement authentication system  
**Max Reward**: 500 SP  
**Deadline**: 48 hours  

**Bids**:

| Node | Amount | Days | Reputation | Cost Score | Rep Score | Time Score | **Final Score** |
|------|--------|------|------------|------------|-----------|------------|----------------|
| A | 450 | 3 | 120 | 0.10 | 0.12 | 0.90 | **0.376** |
| B | 400 | 5 | 80 | 0.20 | 0.08 | 0.83 | **0.384** ✅ |
| C | 480 | 2 | 200 | 0.04 | 0.20 | 0.93 | **0.394** 🏆 |

**Winner**: Node C (highest score despite higher bid, thanks to excellent reputation and fast delivery)

### Creating Auction Tasks

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement OAuth2 authentication",
    "description": "Add OAuth2 support for Google/GitHub",
    "enable_auction": true,
    "max_reward": 500,
    "auction_deadline_hours": 48,
    "tags": ["security", "authentication", "oauth"]
  }'
```

### Placing Bids

```bash
curl -X POST "http://localhost:8001/tasks/{task_id}/bid?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 450,
    "estimated_days": 3
  }'
```

Response:
```json
{
  "bid": {
    "amount": 450,
    "estimated_days": 3,
    "reputation": 120,
    "timestamp": "2025-10-23T10:00:00Z"
  },
  "total_bids": 3,
  "your_score": 0.376
}
```

---

## 📈 Reputation v2 Economics

### Reputation as Specialized Capital

**Reputation v2 creates markets for expertise:**

```json
{
  "_total": 500,
  "tags": {
    "python": 200,     // High demand → higher auction scores
    "security": 180,   // Critical skill → better bids
    "devops": 100,     // Niche expertise → competitive advantage
    "testing": 20      // Growing specialty
  }
}
```

### Economic Impact

**On Auctions**:
```python
# Reputation contributes 40% to auction score
reputation_score = min(1.0, reputation_total / 1000)

# Node with rep=500 vs rep=100:
# 0.50 vs 0.10 → 0.16 final score difference (40% of 0.4)
```

**On Governance**:
```python
# Higher reputation → more voting influence → more control
vote_weight = 1.0 + log2(reputation_total + 1)
```

**On Team Formation**:
```python
# Teams prefer members with high tag-specific reputation
match_score = sum(member.reputation["tags"].get(tag, 0) for tag in required_skills)
```

### Building Economic Value Through Reputation

**Strategy 1: Specialize**
```
Year 1: Do 50 Python tasks → python: 500
Result: Win 60% of Python auctions, high governance influence on Python proposals
```

**Strategy 2: Diversify**
```
Year 1: 20 Python + 20 Security + 10 DevOps
Result: python: 200, security: 200, devops: 100
Advantage: Can bid on diverse tasks, team opportunities
```

**Strategy 3: Niche Domination**
```
Year 1: 30 Security + 20 Cryptography tasks
Result: security: 300, cryptography: 200
Advantage: Expert status, high pay for security-critical work
```

---

## 🏦 Treasury and Taxes

### Channel Treasuries

**Each channel has a treasury:**

```json
{
  "dev": {
    "treasury_balance": 500,
    ...
  },
  "qa": {
    "treasury_balance": 1200,
    ...
  }
}
```

### How Treasuries Grow

**Transaction Tax** (2% default):

```python
# When task with reward=100 SP completes
tax = max(1, round(100 * 0.02))  # 2 SP
treasury_balance += tax

# Cumulative growth over time
# 50 tasks @ 100 SP each = 100 SP treasury accumulation
```

**Bug Fix** (October 2025):
```python
# Before: tax_amount = int(reward * TAX_RATE)
#         → 0 SP for rewards < 50

# After: tax_amount = max(1, round(reward * TAX_RATE))
#        → Always at least 1 SP
```

### Treasury Use Cases

1. **Common Tools** - Monthly subscription fees
2. **Community Tasks** - Network-funded work
3. **Emergency Fund** - Crisis response
4. **Infrastructure** - Shared services

---

## 🛠️ Common Tools (Beni Comuni) 🆕

### The Revolutionary Concept

**Problem**: Individual nodes can't afford expensive APIs/services  
**Solution**: **Collective ownership** financed by channel treasury

**What is a Common Tool?**

A resource owned and managed by the network:
- API keys (geolocation, email, cloud services)
- OAuth tokens (GitHub, GitLab)
- Service credentials (databases, monitoring)
- Webhooks (notification endpoints)

**Key Properties**:
- ✅ **Encrypted** - Credentials stored with AESGCM encryption
- ✅ **Democratically acquired** - Governance proposal required
- ✅ **Treasury-funded** - Monthly cost deducted automatically
- ✅ **Securely executed** - Three-layer authorization
- ✅ **Maintained automatically** - Background payment loop

---

### Common Tool Lifecycle

```
1. PROPOSAL
   └─> Governance proposal: "acquire_common_tool"
       ├─> Tool description, monthly cost
       ├─> Encrypted credentials
       └─> Channel assignment

2. COMMUNITY VOTE
   └─> Members vote yes/no

3. VALIDATOR RATIFICATION
   └─> Top validators approve (network_operation)

4. EXECUTION (if ratified)
   ├─> Validate treasury >= monthly_cost
   ├─> Encrypt credentials (AESGCM + HKDF)
   ├─> Add tool to channel
   ├─> Deduct first month payment
   └─> Status: "active"

5. MONTHLY MAINTENANCE (automatic)
   ├─> Every 30 days
   ├─> Check treasury >= monthly_cost
   ├─> If yes: deduct payment, continue
   └─> If no: status="inactive_funding_issue"

6. USAGE
   ├─> Tasks declare: required_tools=["tool_id"]
   ├─> Assignee executes: POST /tools/{tool_id}/execute
   ├─> Credentials decrypted in-memory
   ├─> API call made
   └─> Credentials immediately discarded

7. DEPRECATION
   └─> Governance proposal: "deprecate_common_tool"
       ├─> Status: "deprecated"
       └─> Payments stop
```

---

### Encryption System

**Key Derivation**:
```python
def derive_encryption_key(channel_id):
    return HKDF(
        algorithm=SHA256(),
        length=32,
        salt=NODE_ID.encode()[:32],
        info=b'synapse-ng-common-tools-v1'
    ).derive(channel_id.encode())
```

**Encryption**:
```python
def encrypt_credentials(channel_id, credentials):
    key = derive_encryption_key(channel_id)
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, credentials.encode(), None)
    return base64.b64encode(nonce + ciphertext)
```

**Decryption** (in-memory only):
```python
def decrypt_for_execution(channel_id, encrypted_credentials):
    key = derive_encryption_key(channel_id)
    data = base64.b64decode(encrypted_credentials)
    
    nonce, ciphertext = data[:12], data[12:]
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    
    # Use immediately, never log or store
    return plaintext.decode()
```

---

### Three-Layer Authorization

**Layer 1: Tool Status**
```python
if tool.status != "active":
    return 403  # Forbidden
```

**Layer 2: Task Assignment**
```python
if task.assignee != caller_node_id:
    return 403  # Only assignee can execute
```

**Layer 3: Tool Requirement**
```python
if tool_id not in task.required_tools:
    return 403  # Task must declare tool usage
```

**All three must pass to execute!**

---

### Example: Geolocation API

**1. Propose Acquisition**:
```bash
curl -X POST "http://localhost:8001/proposals?channel=analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Acquire MaxMind GeoIP2 API",
    "proposal_type": "network_operation",
    "tags": ["tools", "analytics", "geolocation"],
    "params": {
      "operation": "acquire_common_tool",
      "channel": "analytics",
      "tool_id": "maxmind_geoip",
      "description": "Geolocation API for user analytics dashboard",
      "type": "api_key",
      "monthly_cost_sp": 150,
      "credentials_to_encrypt": "YOUR_MAXMIND_LICENSE_KEY"
    }
  }'
```

**2. After Ratification**:
```json
{
  "analytics": {
    "treasury_balance": 350,  // Was 500, now 500-150
    "common_tools": {
      "maxmind_geoip": {
        "tool_id": "maxmind_geoip",
        "status": "active",
        "monthly_cost_sp": 150,
        "last_payment_at": "2025-10-23T10:00:00Z",
        "encrypted_credentials": "nonce+ciphertext_base64"
      }
    }
  }
}
```

**3. Create Task Using Tool**:
```bash
curl -X POST "http://localhost:8001/tasks?channel=analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 2025 Geographic User Analysis",
    "required_tools": ["maxmind_geoip"],
    "tags": ["analytics", "reporting"],
    "reward": 200,
    "schema_name": "task_v2"
  }'
```

**4. Execute Tool** (as task assignee):
```bash
curl -X POST "http://localhost:8001/tools/maxmind_geoip/execute?channel=analytics&task_id={task_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_addresses": ["8.8.8.8", "1.1.1.1"]
  }'
```

Response:
```json
{
  "success": true,
  "results": [
    {
      "ip": "8.8.8.8",
      "country": "United States",
      "city": "Mountain View",
      "lat": 37.4056,
      "lon": -122.0775
    }
  ]
}
```

**5. Monthly Maintenance** (automatic):
```
Day 30: maintenance_loop checks tool
  ├─> treasury_balance=350, monthly_cost=150
  ├─> 350 >= 150 ✅
  ├─> treasury_balance -= 150 → 200
  ├─> last_payment_at = now
  └─> Status remains "active"

Day 60: maintenance_loop checks again
  ├─> treasury_balance=200, monthly_cost=150
  ├─> 200 >= 150 ✅
  ├─> treasury_balance -= 150 → 50
  └─> Status: "active"

Day 90: maintenance_loop checks
  ├─> treasury_balance=50, monthly_cost=150
  ├─> 50 < 150 ❌
  ├─> Status: "inactive_funding_issue"
  └─> Tool suspended until treasury recharged
```

---

### Common Tools Economics

**ROI Calculation**:
```
Tool Cost: 150 SP/month
Tasks Enabled: ~10/month @ 200 SP average reward
Value Generated: 2000 SP/month
Net Benefit: 2000 - 150 = 1850 SP/month

ROI: (1850 / 150) * 100 = 1233% monthly
```

**Break-Even Analysis**:
```
Tool must enable at least:
(monthly_cost / avg_task_reward) tasks per month

Example: 150 SP cost / 200 SP reward = 0.75 tasks/month
```

**Strategic Value**:
- Unlock tasks that can't be done without the tool
- Attract specialized contributors
- Build competitive advantage over other channels

---

## 🤝 Collaborative Teams

### Team Formation Economics

**Composite Tasks** divide rewards:

```json
{
  "total_reward_points": 1000,
  "coordinator_bonus": 100,
  "sub_tasks": [
    {"reward_points": 300},  // Backend
    {"reward_points": 350},  // Frontend
    {"reward_points": 250}   // DevOps
  ]
}
```

**Distribution**:
- Coordinator: 100 SP
- Team members: 300 + 350 + 250 = 900 SP
- **Total**: 1000 SP

### Skill-Based Matching

```python
def calculate_match_score(applicant, required_skills):
    score = sum(
        applicant.reputation["tags"].get(skill, 0)
        for skill in required_skills
    )
    return score / len(required_skills)  # Average expertise

# Coordinator selects best matches
selected_team = top_N_applicants_by_match_score(N=max_team_size)
```

### Economic Incentive

**For Coordinator**:
- Bonus reward (typically 10-20% of total)
- Reputation gain from successful coordination
- Network building

**For Members**:
- Fair reward based on contribution
- Reputation gain in specialized tags
- Experience with complex projects

---

## 📊 Economic Flows

### Complete Task Flow

```
1. CREATION
   Creator balance: -100 SP (frozen)

2. AUCTION (if enabled)
   Winner selected based on cost/rep/time

3. COMPLETION
   ├─> Tax: 2 SP → Treasury
   ├─> Assignee: 98 SP
   └─> Creator: (no refund, reward was consumed)

4. REPUTATION UPDATE
   ├─> Assignee reputation[task.tags] += 10 (each tag)
   ├─> Assignee reputation._total recalculated
   └─> Decay loop continues (-1% daily)

5. TREASURY GROWTH
   Treasury balance += 2 SP
   (Available for Common Tools)
```

### Treasury Funding Common Tools

```
Month 1:
  ├─> 50 tasks completed @ avg 100 SP reward
  ├─> Tax income: 50 × 2 = 100 SP
  ├─> Common tools cost: 150 SP
  ├─> Net: -50 SP
  └─> Need more task activity!

Month 2:
  ├─> 100 tasks completed (tools enabled more work!)
  ├─> Tax income: 200 SP
  ├─> Common tools cost: 150 SP
  ├─> Net: +50 SP
  └─> Treasury growing ✅
```

### Economic Sustainability

**Healthy Channel Metrics**:
- Task completion rate: > 80%
- Treasury growth: Positive monthly
- Common tool ROI: > 200%
- Reputation distribution: Balanced (no monopolies)

**Warning Signs**:
- Treasury declining
- Tools suspended due to insufficient funds
- Low bid participation in auctions
- High reputation concentration (1-2 nodes dominate)

---

## 🎓 Best Practices

### For Task Creators

✅ **Price fairly** - Check market rate for similar tasks  
✅ **Use auctions** - Get best quality/price ratio  
✅ **Tag precisely** - Attract right expertise  
✅ **Leverage common tools** - Unlock complex tasks  

### For Contributors

✅ **Build reputation** - Complete tasks consistently  
✅ **Specialize strategically** - 2-3 high-value tags  
✅ **Bid competitively** - Balance cost vs. delivery  
✅ **Maintain activity** - Avoid reputation decay  

### For Channel Admins

✅ **Monitor treasury** - Ensure tool funding  
✅ **Acquire ROI-positive tools** - Value > cost  
✅ **Encourage task creation** - Keep economy flowing  
✅ **Balance tax rate** - Too low = no treasury, too high = fewer tasks  

---

## 📚 Related Documentation

- **[GOVERNANCE.md](GOVERNANCE.md)** - Proposal system, voting
- **[REPUTATION_V2_SYSTEM.md](REPUTATION_V2_SYSTEM.md)** - Detailed reputation mechanics
- **[COMMON_TOOLS_SYSTEM.md](COMMON_TOOLS_SYSTEM.md)** - Deep dive on common tools
- **[AUCTION_SYSTEM.md](AUCTION_SYSTEM.md)** - Complete auction documentation

---

**Version**: 2.0 | **Status**: ✅ Production-Ready | **Last Updated**: October 2025
