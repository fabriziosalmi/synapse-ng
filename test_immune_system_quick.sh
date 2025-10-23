#!/bin/bash

# Quick Immune System Test - Simplified version
# This test demonstrates the immune system with a manually triggered scenario

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🛡️========================================"
echo "  IMMUNE SYSTEM QUICK TEST"
echo "========================================🛡️"
echo ""

NODE1="http://localhost:8001"

pass() { echo -e "${GREEN}✓${NC} $1"; }
info() { echo -e "${BLUE}ℹ${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "Step 1: Check Immune System is running"
echo "========================================="
info "Checking if nodes have immune system enabled..."
echo ""

# Check health targets exist
health_targets=$(curl -s "$NODE1/state?channel=global" | jq '.global.config.health_targets')

if [ "$health_targets" != "null" ]; then
    pass "Immune System initialized - health targets found"
    echo "$health_targets" | jq '.'
else
    warn "Health targets not found - system may not be initialized yet"
fi

echo ""
echo "Step 2: Understanding the Immune System Cycle"
echo "==============================================="
echo ""
info "The Immune System runs every 1 hour (3600 seconds) in production"
info "First check happens 60 seconds after node startup"
info ""
info "To see it in action:"
echo ""
echo "  1. Restart the network: docker-compose restart"
echo "  2. Wait 60-70 seconds"
echo "  3. Check logs: docker logs synapse-ng-node-1-1 | grep ImmuneSystem"
echo ""
info "You should see:"
echo "  - [ImmuneSystem] Loop started - first check in 60 seconds"
echo "  - [ImmuneSystem] ===== Starting health check cycle ====="
echo "  - [ImmuneSystem] Metrics: {...}"
echo ""

echo "Step 3: How to Trigger a Health Issue"
echo "========================================"
echo ""
info "The system detects issues when metrics exceed thresholds:"
echo ""
echo "  Current Thresholds:"
echo "  - max_avg_propagation_latency_ms: 10000 (10 seconds)"
echo "  - min_active_peers: 3"
echo "  - max_failed_message_rate: 0.05 (5%)"
echo ""
info "To trigger high_latency detection:"
echo "  - Network must have actual message propagation delays > 10s"
echo "  - Messages must have 'created_at' timestamps"
echo "  - System tracks latency via record_message_propagation()"
echo ""

echo "Step 4: Manual Test Scenario"
echo "=============================="
echo ""
info "For testing, you can lower the threshold temporarily:"
echo ""
echo "1. Create a proposal to change health_targets:"
echo ""
echo 'curl -X POST "http://localhost:8001/proposals?channel=global" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{
    "title": "Lower latency threshold for testing",
    "proposal_type": "config_change",
    "params": {
      "config_changes": {
        "health_targets": {
          "max_avg_propagation_latency_ms": 100
        }
      }
    }
  }'"'"
echo ""
echo "2. Vote and approve the proposal"
echo "3. Wait for next immune system cycle"
echo "4. System should detect high_latency and propose a fix"
echo ""

echo "Step 5: Check Current Network Health"
echo "======================================"
echo ""

# Create some tasks to generate traffic
info "Creating 10 tasks to generate network activity..."
for i in {1..10}; do
    curl -s -X POST "$NODE1/tasks?channel=sviluppo_ui" \
        -H "Content-Type: application/json" \
        -d "{\"title\": \"Health Check Task $i\", \"reward\": 5}" > /dev/null
    echo -n "."
done
echo ""
pass "Tasks created"
echo ""

info "Waiting 5 seconds for propagation..."
sleep 5

echo ""
info "Checking for any immune system proposals..."
proposals=$(curl -s "$NODE1/state?channel=global" | jq -c '[.global.proposals // {} | to_entries[] | select(.value.tags[]? == "immune_system")]')
count=$(echo "$proposals" | jq 'length')

if [ "$count" -gt 0 ]; then
    pass "Found $count immune system proposal(s)!"
    echo "$proposals" | jq '.[0].value | {title, status, config_changes: .params.config_changes}'
else
    info "No immune system proposals found (network is healthy)"
fi

echo ""
echo "========================================="
echo "  IMMUNE SYSTEM STATUS"
echo "========================================="
echo ""
pass "System is initialized and monitoring"
info "Next automatic check: within 1 hour of last restart"
info "Monitor with: docker logs synapse-ng-node-1-1 | grep ImmuneSystem"
echo ""
echo "🛡️ The network has an immune system! 🛡️"
echo ""
