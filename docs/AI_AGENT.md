# AI Agent - Local Assistant for Synapse-NG Nodes

> ⚠️ **Note**: AI features are completely **optional**. See [AI_SETUP.md](AI_SETUP.md) for installation instructions.

## 📋 Overview

Each Synapse-NG node can be equipped with a local AI agent based on LLM that enables:
- 🗣️ **Natural language interaction** - Voice/text commands instead of API calls
- 🧠 **Automatic strategic analysis** - Agent "thinks" autonomously and suggests actions
- 🤖 **Intelligent automation** - Executes actions based on user-defined goals
- 🎯 **Goal-oriented behavior** - Maximizes SP, reputation, participation

**Model**: Qwen2.5-0.5B-Instruct (GGUF format)  
**Engine**: llama-cpp-python  
**Memory**: ~1GB RAM for model  
**Latency**: ~100-500ms per generation

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────┐
│ User                                                       │
│ "Create a task to fix the UI bug with 50SP reward"        │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ POST /agent/prompt                                         │
│  - Receives text prompt                                    │
│  - Builds context (network state, available APIs)          │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Local LLM (Qwen2.5-0.5B)                                   │
│  - Analyzes prompt + context                               │
│  - Generates API command sequence in JSON                  │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Executor                                                   │
│  - Validates generated commands (SP reserve, permissions)  │
│  - Executes internal API actions                           │
│  - Returns results to user                                 │
└────────────────────────────────────────────────────────────┘
```

### Proactive Agent (Background Loop)

The agent can run autonomously in background:

```python
while True:
    context = build_network_context()
    
    # Analyze opportunities
    if profitable_task_available():
        claim_task()
    
    if good_proposal_to_vote():
        vote_on_proposal()
    
    if low_on_synapse_points():
        complete_tasks()
    
    await asyncio.sleep(300)  # Every 5 minutes
```

---

## 🚀 Quick Start

### 1. Installation

See [AI_SETUP.md](AI_SETUP.md) for complete instructions:

```bash
# 1. Uncomment llama-cpp-python in requirements.txt
# 2. Download model (Qwen2.5-0.5B-Instruct recommended)
wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf \
  -O models/qwen3-0.6b.gguf

# 3. Rebuild containers
docker-compose build
```

### 2. Configuration

```bash
# config.env
AI_MODEL_PATH=models/qwen3-0.6b.gguf
AI_AUTONOMOUS_MODE=false  # true to enable background agent
AI_STRATEGY=balanced  # aggressive | balanced | conservative
```

### 3. Verify

```bash
curl http://localhost:8001/agent/status
```

---

## 📖 API Reference

### 1. Send Prompt to AI

```http
POST /agent/prompt?channel=dev
Content-Type: application/json

{
  "prompt": "Create a high-priority task to fix the UI bug with 50 SP reward"
}
```

**Response**:
```json
{
  "actions_executed": [
    {
      "action": "POST /tasks/create",
      "params": {
        "title": "Fix UI bug",
        "priority": "high",
        "reward": 50
      },
      "result": "Task created: task-abc123"
    }
  ],
  "raw_response": "I created a high-priority task with ID task-abc123..."
}
```

---

### 2. Get/Set Agent Objectives

```http
GET /agent/objectives?channel=dev
```

**Response**:
```json
{
  "objectives": [
    {
      "name": "maximize_synapse_points",
      "priority": 10,
      "parameters": {"target_sp": 10000}
    },
    {
      "name": "build_reputation",
      "priority": 8
    }
  ]
}
```

```http
POST /agent/objectives?channel=dev
Content-Type: application/json

{
  "objectives": [
    {
      "name": "maximize_synapse_points",
      "priority": 10,
      "parameters": {"target_sp": 10000}
    }
  ]
}
```

---

### 3. Agent Status

```http
GET /agent/status
```

**Response**:
```json
{
  "ai_available": true,
  "model_path": "models/qwen3-0.6b.gguf",
  "model_loaded": true,
  "autonomous_mode": false,
  "strategy": "balanced",
  "last_action": "2025-10-02T10:30:00Z"
}
```

---

## 🎯 Available Objectives

The agent can be configured with different objectives:

| Objective | Description | Priority |
|-----------|-------------|----------|
| `maximize_synapse_points` | Earn as many SP as possible | 10 |
| `build_reputation` | Increase reputation score | 8 |
| `complete_tasks` | Focus on task completion rate | 7 |
| `participate_governance` | Active in voting and proposals | 6 |
| `optimize_network` | Improve network health | 5 |

### Strategy Modes

- **Aggressive**: High risk, high reward. Claims expensive tasks, makes bold proposals
- **Balanced**: Default. Balanced risk/reward, selective task claiming
- **Conservative**: Low risk. Only claims easy tasks, votes on safe proposals

---

## 💡 Usage Examples

### Example 1: Natural Language Task Creation

```bash
curl -X POST "http://localhost:8001/agent/prompt?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a task for implementing dark mode in the UI with 100 SP reward and high priority"
  }'
```

Agent generates:
1. Parses intent: create task
2. Extracts parameters: title="dark mode", reward=100, priority="high"
3. Calls `POST /tasks/create` internally
4. Returns human-readable result

---

### Example 2: Strategic Decision Making

```bash
curl -X POST "http://localhost:8001/agent/prompt?channel=dev" \
  -d '{
    "prompt": "Should I vote yes on proposal prop-123?"
  }'
```

Agent analyzes:
1. Reads proposal details
2. Evaluates impact on network
3. Considers current SP and reputation
4. Recommends vote with reasoning

---

### Example 3: Autonomous Mode

```yaml
# docker-compose.yml
services:
  node-1:
    environment:
      - AI_AUTONOMOUS_MODE=true
      - AI_STRATEGY=balanced
```

Agent will automatically:
- Claim profitable tasks (if SP reserve sufficient)
- Vote on proposals (aligned with network health)
- Complete tasks to maintain reputation
- Participate in auctions (bid strategically)

---

## 🧠 Proactive Analysis

### Opportunity Detection

The agent monitors:

```python
# Task opportunities
open_tasks = get_open_tasks()
for task in open_tasks:
    if task.reward > 50 and estimate_completion_time(task) < 2h:
        claim_task(task.id)

# Governance opportunities
proposals = get_active_proposals()
for proposal in proposals:
    if proposal.type == "network_upgrade" and proposal.votes_needed < 10:
        vote(proposal.id, "yes")

# Auction opportunities
auctions = get_active_auctions()
for auction in auctions:
    if auction.current_bid < estimated_value(auction) * 0.8:
        place_bid(auction.id, calculate_optimal_bid())
```

### Strategic Planning

The agent builds plans:
1. **Short-term** (next hour): Which task to claim?
2. **Medium-term** (next day): How to reach SP target?
3. **Long-term** (next week): Which skills to develop?

---

## 🔒 Security and Validation

### Input Validation

- ✅ Prompt sanitization (no code injection)
- ✅ Action whitelisting (only allowed APIs)
- ✅ Parameter validation (check types and ranges)

### Output Validation

```python
def validate_action(action):
    # Check SP reserve
    if action.type == "create_task":
        if action.params.reward > current_sp * 0.1:
            return False, "Reward too high (>10% of SP)"
    
    # Check permissions
    if action.type == "accept_member":
        if not is_coordinator(task_id):
            return False, "Not coordinator"
    
    # Check rate limits
    if count_actions_last_hour() > 100:
        return False, "Rate limit exceeded"
    
    return True, "OK"
```

### Autonomous Mode Safeguards

- **SP Reserve**: Never spend more than X% of total SP
- **Risk Limits**: Conservative strategy by default
- **Manual Override**: User can disable autonomous mode anytime
- **Audit Log**: All actions logged for review

---

## 📊 Monitoring and Logging

### Action Log

```json
{
  "timestamp": "2025-10-02T10:30:00Z",
  "action": "claim_task",
  "task_id": "task-abc123",
  "reasoning": "High reward (80 SP) and good skill match (90%)",
  "result": "success",
  "sp_delta": -10,
  "reputation_delta": +8
}
```

### Performance Metrics

- Actions per hour
- Success rate
- SP earned vs spent
- Reputation change
- Task completion rate

---

## 🧪 Testing

### Test AI Without Model

```python
# For testing without actual LLM
os.environ["AI_MOCK_MODE"] = "true"

# Agent will use rule-based responses instead of LLM
response = agent.prompt("Create a task")
# Returns: {"action": "POST /tasks/create", ...}
```

### Test Autonomous Agent

```bash
# Enable autonomous mode
curl -X POST "http://localhost:8001/agent/objectives?channel=dev" \
  -d '{
    "objectives": [{"name": "maximize_synapse_points", "priority": 10}]
  }'

# Start autonomous loop (runs in background)
curl -X POST "http://localhost:8001/agent/start"

# Monitor actions
docker logs synapse-ng-node-1-1 | grep "AI_AGENT"
```

---

## 🚀 Best Practices

### For Users

1. **Start simple**: Test with simple prompts first
2. **Review actions**: Check what agent plans to do before confirming
3. **Set limits**: Configure SP reserve and risk tolerance
4. **Monitor logs**: Review agent decisions regularly
5. **Iterate**: Refine objectives based on results

### For Developers

1. **Graceful degradation**: Handle missing AI model gracefully
2. **Validation**: Always validate agent-generated actions
3. **Logging**: Log all agent decisions for debugging
4. **Rate limiting**: Prevent agent from spamming network
5. **Testing**: Test both with and without AI model

---

## 🔍 Troubleshooting

### Issue: "AI Agent not available"
**Cause**: Model not loaded or llama-cpp-python not installed  
**Solution**: See [AI_SETUP.md](AI_SETUP.md) for installation

### Issue: Agent makes bad decisions
**Cause**: Wrong strategy or objectives  
**Solution**: Adjust strategy to "conservative" and review objectives

### Issue: Slow response times
**Cause**: Model too large for available CPU  
**Solution**: Use smaller model (Qwen2.5-0.5B instead of larger models)

### Issue: High memory usage
**Cause**: Model loaded in RAM  
**Solution**: 
- Use quantized model (Q4_K_M)
- Increase container memory limit
- Disable AI if not needed

---

## 📚 References

### Source Files
- `app/ai_agent.py`: AI agent implementation
- `app/main.py`: API endpoints for AI agent
- `docs/AI_AGENT.md`: This documentation
- `docs/AI_SETUP.md`: Installation and setup guide

### Related Documentation
- [AUTONOMOUS_ORGANISM.md](AUTONOMOUS_ORGANISM.md): Network self-organization
- [PHASE_7_NETWORK_SINGULARITY.md](PHASE_7_NETWORK_SINGULARITY.md): Self-evolution with AI

---

## 🎓 FAQ

**Q: Do I need AI to use Synapse-NG?**  
A: No! AI is completely optional. All core features work without AI.

**Q: Which model should I use?**  
A: Qwen2.5-0.5B-Instruct is recommended (good balance of speed/quality).

**Q: Can the agent spend all my SP?**  
A: No. Agent has built-in safeguards (SP reserve, risk limits).

**Q: Is the agent always running?**  
A: Only if `AI_AUTONOMOUS_MODE=true`. Otherwise on-demand only.

**Q: Can I use GPT-4/Claude instead?**  
A: Not currently. Only local models supported for privacy/decentralization.

**Q: How do I disable AI?**  
A: Comment out `llama-cpp-python` in requirements.txt and rebuild.

---

**Version**: 1.0.0  
**Date**: 2025-10-03  
**Author**: Synapse-NG Development Team  
**Status**: ⚠️ Optional Feature
