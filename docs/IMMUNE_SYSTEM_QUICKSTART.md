# 🛡️ Immune System - Quick Start Guide

## ✅ System Status

The Immune System is **IMPLEMENTED** and **RUNNING** in Synapse-NG.

## 🚀 Quick Verification

```bash
# Run quick test
./test_immune_system_quick.sh
```

**Expected Output:**
```
✓ Immune System initialized - health targets found
✓ System is initialized and monitoring
🛡️ The network has an immune system! 🛡️
```

---

## 📊 Current Configuration

Default health targets (auto-initialized):

```json
{
  "max_avg_propagation_latency_ms": 10000,  // 10 seconds
  "min_active_peers": 3,
  "max_failed_message_rate": 0.05  // 5%
}
```

---

## 🔄 How It Works

### Monitoring Cycle

```
Every 1 hour:
  1. Collect network metrics (latency, connectivity, message loss)
  2. Compare against health targets
  3. If threshold exceeded → diagnose issue
  4. Generate governance proposal automatically
  5. Community votes on proposed remedy
  6. If approved → apply config change
  7. Next cycle verifies improvement
```

### First Cycle

- **Timing**: 60 seconds after node startup (then every hour)
- **Check logs**: `docker logs synapse-ng-node-1-1 | grep ImmuneSystem`

---

## 🧪 Testing Scenarios

### Scenario 1: Check System is Running

```bash
# View logs
docker logs synapse-ng-node-1-1 | grep "ImmuneSystem"

# Expected output:
# [ImmuneSystem] Initialized for node ...
# [ImmuneSystem] Started - monitoring every hour
# [ImmuneSystem] Loop started - first check in 60 seconds
```

### Scenario 2: Trigger a Health Check

```bash
# Restart network to trigger immediate check (after 60s)
docker-compose restart

# Wait 70 seconds
sleep 70

# Check results
docker logs synapse-ng-node-1-1 | grep "health check cycle"
```

### Scenario 3: Lower Threshold for Testing

To see the immune system propose a remedy, temporarily lower the health threshold:

```bash
# 1. Create proposal to lower latency threshold
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lower latency threshold for immune system testing",
    "proposal_type": "config_change",
    "params": {
      "config_changes": {
        "health_targets": {
          "max_avg_propagation_latency_ms": 100
        }
      }
    }
  }'

# 2. Get proposal ID from response
# 3. Vote on it from multiple nodes
# 4. Close and approve
# 5. Wait for next immune system cycle (up to 1 hour)
# 6. System should detect "high_latency" and propose increasing gossip peers
```

---

## 📋 Monitoring Commands

### Check Health Targets

```bash
curl -s "http://localhost:8001/state?channel=global" | \
  jq '.global.config.health_targets'
```

### Check for Immune System Proposals

```bash
curl -s "http://localhost:8001/state?channel=global" | \
  jq '[.global.proposals // {} | to_entries[] | select(.value.tags[]? == "immune_system")]'
```

### View Execution Log

```bash
curl -s "http://localhost:8001/state?channel=global" | \
  jq '.global.execution_log | map(select(.operation == "config_change"))'
```

---

## 🎯 What to Expect

### Healthy Network

```
[ImmuneSystem] ===== Starting health check cycle =====
[ImmuneSystem] Metrics: {
  "avg_propagation_latency_ms": 450.5,
  "total_messages_propagated": 120,
  "active_peers": 4,
  "failed_messages": 0
}
[ImmuneSystem] Network health is optimal ✓
```

### Unhealthy Network (Issue Detected)

```
[ImmuneSystem] ⚠️ Detected 1 health issue(s)
  - high_latency: Average message propagation latency (15200ms) exceeds target (10000ms)
[ImmuneSystem] Proposal uuid-generated submitted successfully
```

Then check proposals:

```json
{
  "id": "uuid-generated",
  "title": "[IMMUNE SYSTEM] Corrective Action: High Latency",
  "proposal_type": "config_change",
  "params": {
    "config_changes": {
      "max_gossip_peers": 7  // increased from 5
    }
  },
  "tags": ["immune_system", "automated", "high_latency"],
  "status": "open"
}
```

---

## 🔧 Configuration

### Enable/Disable

```yaml
# docker-compose.yml
environment:
  - ENABLE_IMMUNE_SYSTEM=true  # default
```

### Adjust Check Frequency (for testing)

```python
# app/immune_system.py line 146
await asyncio.sleep(3600)  # 1 hour (change to 300 for 5 min testing)
```

---

## 📚 Full Documentation

- **[IMMUNE_SYSTEM.md](IMMUNE_SYSTEM.md)** - Complete guide (architecture, API, examples)
- **[IMMUNE_SYSTEM_IMPLEMENTATION_SUMMARY.md](IMMUNE_SYSTEM_IMPLEMENTATION_SUMMARY.md)** - Technical summary

---

## ✅ Implementation Checklist

- [x] Core module (`app/immune_system.py`) - 620 lines
- [x] Integration in `app/main.py` - Auto-starts at node startup
- [x] Health targets configuration - Auto-initialized
- [x] Message latency tracking - Real-time in PubSub handler
- [x] Test suite (`test_immune_system_quick.sh`) - Quick verification
- [x] Docker configuration - `ENABLE_IMMUNE_SYSTEM=true`
- [x] Documentation - Complete guides

---

## 🎓 Key Points

1. **System is Active**: Immune system runs automatically on all nodes
2. **First Check**: 60 seconds after startup, then every hour
3. **Automatic Proposals**: System generates governance proposals autonomously
4. **Democratic**: Community votes on proposed remedies
5. **Self-Healing**: Approved changes applied automatically

---

**Status**: ✅ Production-Ready  
**The network can heal itself!** 🛡️
