# 🧬 Organism Consciousness Dashboard - Complete Guide

**Version:** 2.0  
**Last Updated:** 23 October 2025  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Dashboard Components](#dashboard-components)
   - 4.1 [Panel 1: Homeostatic System](#panel-1-homeostatic-system)
   - 4.2 [Panel 2: Nervous System](#panel-2-nervous-system)
   - 4.3 [Panel 3: Evolutionary Genome](#panel-3-evolutionary-genome)
5. [Data Structure Reference](#data-structure-reference)
6. [API Integration](#api-integration)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Development Guide](#development-guide)
10. [Performance Optimization](#performance-optimization)
11. [Security Considerations](#security-considerations)
12. [Changelog](#changelog)

---

## 1. Overview

### What is the Organism Consciousness Dashboard?

The **Organism Consciousness Dashboard** is a real-time monitoring interface that visualizes Synapse-NG as a living digital organism with three integrated consciousness systems:

- **🫀 Homeostatic System**: Physical health monitoring (like a body's vital signs)
- **🧠 Nervous System**: Governance and decision-making (like a brain's neural network)
- **🧬 Evolutionary Genome**: Self-improvement and code evolution (like DNA and adaptation)

### Key Features

- ✅ **Real-time monitoring** - 10-second polling interval
- ✅ **Traffic light indicators** - Instant visual health status
- ✅ **CORS-enabled** - Secure cross-origin requests
- ✅ **Zero dependencies** - Pure vanilla JavaScript
- ✅ **Responsive design** - Works on desktop and mobile
- ✅ **Biotech aesthetic** - Animated EEG-style background

### Live Demo

```bash
# Start dashboard
cd /Users/fab/GitHub/synapse-ng
./launch_dashboard.sh

# Access at
http://localhost:15000
```

---

## 2. Architecture

### Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│                 Browser (Chrome/Firefox)                │
├─────────────────────────────────────────────────────────┤
│  HTML5 + CSS3 + Vanilla JavaScript (No Frameworks!)    │
├─────────────────────────────────────────────────────────┤
│            HTTP Server (Python 3 http.server)           │
├─────────────────────────────────────────────────────────┤
│                  CORS Middleware (FastAPI)              │
├─────────────────────────────────────────────────────────┤
│              Synapse-NG Node (Docker Container)         │
└─────────────────────────────────────────────────────────┘
```

### File Structure

```
dashboard_ui/
├── index.html              # Main HTML (269 lines)
├── styles/
│   ├── main.css           # Core styles + animations (343 lines)
│   ├── panels.css         # Panel-specific styles (468 lines)
│   └── components.css     # Modals, badges, tooltips (467 lines)
├── scripts/
│   ├── api-client.js      # API communication (362 lines)
│   ├── health-monitor.js  # Panel 1 logic (295 lines)
│   ├── governance-monitor.js # Panel 2 logic (110 lines)
│   ├── evolution-monitor.js  # Panel 3 logic (165 lines)
│   ├── vote-simulator.js  # Vote weight calculator (243 lines)
│   └── main.js            # App orchestrator (292 lines)
├── README.md              # Quick start guide
├── MOCKUP.md             # Visual mockups
└── DELIVERY.md           # Delivery documentation
```

**Total Lines of Code:** 3,314 lines across 13 files

---

## 3. Installation & Setup

### Prerequisites

- ✅ Python 3.6+ (for HTTP server)
- ✅ Docker & Docker Compose (for Synapse-NG node)
- ✅ Modern browser (Chrome 90+, Firefox 88+, Safari 14+)

### Quick Start (5 minutes)

```bash
# 1. Clone repository
cd /Users/fab/GitHub/synapse-ng

# 2. Start Synapse-NG stack
docker-compose up -d

# 3. Wait for nodes to initialize (30 seconds)
sleep 30

# 4. Launch dashboard
./launch_dashboard.sh

# 5. Open browser
# Dashboard auto-opens at http://localhost:15000
```

### Manual Setup

```bash
# Start HTTP server manually
cd dashboard_ui
python3 -m http.server 15000

# Or use Node.js
npx http-server -p 15000

# Or use Python 2 (legacy)
python -m SimpleHTTPServer 15000
```

### Connection Configuration

1. **Open Dashboard**: http://localhost:15000
2. **Enter Node Endpoint**: `http://localhost:8001` (node-1)
3. **Click "Connect"**
4. **Verify**: Green status indicator + Node ID displayed

**Alternative Endpoints:**
- Node 2: `http://localhost:8002`
- Node 3: `http://localhost:8003`
- Node 4: `http://localhost:8004`

---

## 4. Dashboard Components

---

## 4.1 Panel 1: Homeostatic System

**Purpose:** Monitor the physical health and vital signs of the organism

### 4.1.1 Vital Signs (4 Cards)

#### ⚡ Propagation Latency
- **What it measures**: Average time for messages to propagate across the network
- **Current value**: Extracted from `state.global.immune_system.health.avg_propagation_latency_ms.current`
- **Target value**: `state.global.immune_system.health.avg_propagation_latency_ms.target` (default: 10000 ms)
- **Traffic Light Logic**:
  - 🟢 **Green (Healthy)**: `current <= target`
  - 🟡 **Yellow (Warning)**: `current <= target * 1.5`
  - 🔴 **Red (Critical)**: `current > target * 1.5`

**API Path:**
```javascript
const latency = state.global.immune_system.health.avg_propagation_latency_ms;
console.log(`Current: ${latency.current} ms, Target: ${latency.target} ms`);
```

#### 👥 Active Peers
- **What it measures**: Number of connected nodes in the network
- **Current value**: `state.global.immune_system.health.active_peers.current`
- **Target value**: `state.global.immune_system.health.active_peers.target` (default: 3)
- **Traffic Light Logic**:
  - 🟢 **Green (Healthy)**: `current >= target`
  - 🟡 **Yellow (Warning)**: `current >= target * 0.67`
  - 🔴 **Red (Critical)**: `current < target * 0.67`

**API Path:**
```javascript
const peers = state.global.immune_system.health.active_peers;
console.log(`Current: ${peers.current}, Target: ${peers.target}`);
```

#### 🎯 Consensus Ratio
- **What it measures**: Percentage of nodes in consensus agreement
- **Current value**: `state.global.immune_system.health.consensus_ratio.current` (0.0 to 1.0)
- **Target value**: `state.global.immune_system.health.consensus_ratio.target` (default: 0.67 = 67%)
- **Display**: Converted to percentage (1.0 = 100%)
- **Traffic Light Logic**:
  - 🟢 **Green (Healthy)**: `current >= target`
  - 🟡 **Yellow (Warning)**: `current >= target * 0.8`
  - 🔴 **Red (Critical)**: `current < target * 0.8`

**API Path:**
```javascript
const consensus = state.global.immune_system.health.consensus_ratio;
console.log(`Consensus: ${(consensus.current * 100).toFixed(1)}%`);
```

#### 📨 Messages Propagated
- **What it measures**: Total count of successfully propagated messages
- **Current value**: `state.global.immune_system.health.messages_propagated.current`
- **Target value**: `state.global.immune_system.health.messages_propagated.target` (informational, typically 0)
- **Display**: Raw count (not a percentage)

**API Path:**
```javascript
const messages = state.global.immune_system.health.messages_propagated;
console.log(`Messages: ${messages.current}`);
```

---

### 4.1.2 Active Diagnoses

**Purpose:** Display health issues detected by the Immune System

**Data Source:** `state.global.immune_system.active_issues[]`

**Structure:**
```javascript
{
  "issue_type": "high_latency",
  "severity": "medium",          // low, medium, high, critical
  "current_value": 15000,
  "target_value": 10000,
  "diagnosis": "Network propagation latency exceeds target by 50%",
  "recommended_action": "Consider adding more peers or optimizing network topology",
  "detected_at": "2025-10-23T21:00:00Z",
  "issue_source": "config"       // config, algorithm, network, resource
}
```

**Display Logic:**
- Empty state: "No health issues detected - Organism is healthy" ✓
- Issues present: Show cards with severity badges and recommended actions

**Severity Badge Colors:**
- 🟦 **Low**: Blue
- 🟡 **Medium**: Yellow
- 🟠 **High**: Orange
- 🔴 **Critical**: Red

---

### 4.1.3 Autonomous Remedies

**Purpose:** Display remedy proposals automatically generated by the Immune System

**Data Source:** Filter proposals where `title` contains "Immune System", "Health", or "Remedy"

**API Query:**
```javascript
const immuneProposals = state.global.proposals
  .filter(p => 
    p.title.includes('Immune System') || 
    p.title.includes('Health') ||
    p.title.includes('Remedy')
  );
```

**Display:**
- Empty state: "No autonomous remedies proposed"
- Proposals present: Show cards with status and description

---

## 4.2 Panel 2: Nervous System

**Purpose:** Visualize governance, decision-making, and treasury management

### 4.2.1 Governance Kanban

**Purpose:** Display governance proposals in a 4-column kanban board

**Data Source:** `state.global.proposals[]`

**Columns:**

#### 📋 OPEN (status: "open")
- New proposals awaiting votes
- Anyone can submit a vote

#### 🗳️ VOTING (status: "voting")
- Proposals actively being voted on
- Shows vote progress bars

#### 🎖️ RATIFYING (status: "ratifying")
- Proposals passed voting, awaiting validator ratification
- Requires validator signatures

#### ✅ CLOSED (status: "executed" or "rejected")
- **Executed**: Proposal passed and applied
- **Rejected**: Proposal failed to reach consensus

**Proposal Card Structure:**
```javascript
{
  "id": "a6fb3684-5b51-4f33-8da6-eb73a865172d",
  "title": "Optimize Consensus Timeout",
  "description": "Reduce timeout from 30s to 20s",
  "proposal_type": "config_change",  // generic, config_change, network_operation, command
  "status": "open",
  "votes_for": 3,
  "votes_against": 1,
  "created_at": "2025-10-23T21:00:00Z",
  "updated_at": "2025-10-23T21:05:00Z",
  "tags": ["performance", "consensus"]
}
```

**API Query:**
```javascript
// Get proposals by status
const openProposals = state.global.proposals.filter(p => p.status === "open");
const votingProposals = state.global.proposals.filter(p => p.status === "voting");
const ratifyingProposals = state.global.proposals.filter(p => p.status === "ratifying");
const closedProposals = state.global.proposals.filter(p => 
  p.status === "executed" || p.status === "rejected"
);
```

---

### 4.2.2 Network Treasury

**Purpose:** Display Synapse Points (SP) balance for each channel

**Data Source:** `state[channel_id].treasury_balance`

**Channels:**
- `global`: Main treasury
- `sviluppo_ui`: UI development treasury
- Custom channels: As created

**API Query:**
```javascript
// Get all channel treasuries
const treasuries = {};
Object.keys(state).forEach(channelId => {
  if (channelId !== 'global' && state[channelId].treasury_balance !== undefined) {
    treasuries[channelId] = state[channelId].treasury_balance;
  }
});
```

**Display:**
```
💰 Network Treasury
├─ sviluppo_ui: 1,250 SP
├─ global: 5,000 SP
└─ Total: 6,250 SP
```

---

### 4.2.3 Vote Simulator (Modal)

**Purpose:** Calculate contextual vote weight for a specific node on a proposal

**Trigger:** Click on proposal card "Simulate Vote" button

**Formula:**
```javascript
total_weight = base_weight + bonus_weight

// Base weight = 1.0 for all nodes

// Bonus weight calculation:
bonus_weight = 0
for each tag in proposal.tags:
  if node has specialization matching tag:
    bonus_weight += 0.1

// Example:
// Proposal tags: ["performance", "consensus"]
// Node specializations: ["performance", "security", "consensus"]
// Matching: ["performance", "consensus"] = 2 matches
// bonus_weight = 0.2
// total_weight = 1.0 + 0.2 = 1.2
```

**Data Source:**
- Node reputation: `state.global.nodes[node_id].reputation`
- Node specializations: `state.global.nodes[node_id].specializations`
- Proposal tags: `state.global.proposals[proposal_id].tags`

---

## 4.3 Panel 3: Evolutionary Genome

**Purpose:** Visualize code evolution, self-improvement, and autonomous solutions

### 4.3.1 Evolutionary Timeline

**Purpose:** Display chronological history of code upgrade proposals

**Data Source:** Filter proposals where `proposal_type === "code_upgrade"`

**API Query:**
```javascript
const codeUpgrades = state.global.proposals
  .filter(p => p.proposal_type === "code_upgrade")
  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
```

**Timeline Card Structure:**
```javascript
{
  "id": "upgrade-123",
  "title": "API Rate Limiting",
  "description": "Add Redis-based rate limiter",
  "status": "executed",  // pending, approved, rejected, executed
  "impact": "32% performance improvement",
  "created_at": "2025-10-20T10:00:00Z",
  "executed_at": "2025-10-22T15:30:00Z"
}
```

**Display:**
```
🧬 Evolutionary Timeline
├─ 2025-10-22 ✅ API Rate Limiting (executed)
│  └─ ↑ 32% performance improvement
├─ 2025-10-20 ⏳ WebSocket Optimization (pending)
│  └─ Expected: 25% latency reduction
└─ 2025-10-18 ❌ Memory Pool Rewrite (rejected)
   └─ Insufficient testing coverage
```

---

### 4.3.2 Evolution Statistics

**Purpose:** Display aggregated metrics about code evolution

**Metrics:**

#### Total Code Generations
```javascript
const totalGenerations = state.global.proposals
  .filter(p => p.proposal_type === "code_upgrade")
  .length;
```

#### Successful Compilations
```javascript
const successfulCompilations = state.global.proposals
  .filter(p => p.proposal_type === "code_upgrade" && 
              (p.status === "executed" || p.status === "approved"))
  .length;
```

#### Success Rate
```javascript
const successRate = totalGenerations > 0 
  ? (successfulCompilations / totalGenerations * 100).toFixed(0)
  : 0;
```

#### Code Upgrades Applied
```javascript
const appliedUpgrades = state.global.proposals
  .filter(p => p.proposal_type === "code_upgrade" && p.status === "executed")
  .length;
```

---

### 4.3.3 Proposed Cures

**Purpose:** Display evolutionary solutions pending review

**Data Source:** Filter code_upgrade proposals with status "pending" or "open"

**API Query:**
```javascript
const pendingSolutions = state.global.proposals
  .filter(p => 
    p.proposal_type === "code_upgrade" && 
    (p.status === "pending" || p.status === "open")
  );
```

---

## 5. Data Structure Reference

### 5.1 Complete State Object

```json
{
  "global": {
    "immune_system": {
      "enabled": true,
      "health": {
        "avg_propagation_latency_ms": {
          "current": 0.0,
          "target": 10000,
          "status": "healthy"
        },
        "active_peers": {
          "current": 4,
          "target": 3,
          "status": "healthy"
        },
        "consensus_ratio": {
          "current": 1.0,
          "target": 0.67,
          "status": "healthy"
        },
        "messages_propagated": {
          "current": 0,
          "target": 0,
          "status": "healthy"
        }
      },
      "active_issues": [],
      "health_targets": {
        "max_avg_propagation_latency_ms": 10000,
        "min_active_peers": 3,
        "min_consensus_ratio": 0.67
      },
      "last_check": "2025-10-23T21:00:00Z",
      "pending_proposals": 0
    },
    "nodes": {
      "JkN-5D2q...": {
        "reputation": {
          "_total": 0,
          "_last_updated": "2025-10-23T21:00:00Z",
          "tags": {}
        },
        "balance": 0,
        "specializations": ["consensus", "networking"]
      }
    },
    "proposals": [
      {
        "id": "a6fb3684-5b51-4f33-8da6-eb73a865172d",
        "title": "Optimize Consensus Timeout",
        "description": "Reduce timeout from 30s to 20s",
        "proposal_type": "config_change",
        "status": "open",
        "votes_for": 0,
        "votes_against": 0,
        "created_at": "2025-10-23T21:00:00Z",
        "updated_at": "2025-10-23T21:00:00Z",
        "tags": ["performance", "consensus"],
        "params": {"timeout": 20}
      }
    ]
  },
  "sviluppo_ui": {
    "tasks": {
      "b3239440-d719-42d3-b713-e7ffd0984c31": {
        "id": "b3239440-d719-42d3-b713-e7ffd0984c31",
        "title": "Add Dark Mode Toggle",
        "description": "Implement dark/light theme toggle",
        "status": "open",
        "reward": 100,
        "tags": ["ui", "frontend"],
        "created_at": "2025-10-23T21:00:00Z"
      }
    },
    "treasury_balance": 0
  }
}
```

---

## 6. API Integration

### 6.1 Endpoint Reference

#### GET /state
**Description:** Returns complete network state including immune system, nodes, proposals, tasks

**URL:** `http://localhost:8001/state`

**Response:** JSON object (see section 5.1)

**Polling Rate:** 10 seconds (10,000ms)

**CORS Headers:**
```
Access-Control-Allow-Origin: http://localhost:15000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Credentials: true
Access-Control-Allow-Headers: *
```

---

### 6.2 API Client Implementation

**File:** `dashboard_ui/scripts/api-client.js`

**Key Methods:**

```javascript
class SynapseAPI {
  // Connect to node
  async setEndpoint(endpoint)
  
  // Fetch state
  async fetchState()
  
  // Get health metrics
  getHealthMetrics() // Returns {latency, peers, consensus, messageSuccess, targets}
  
  // Get diagnoses
  getDiagnoses() // Returns active_issues[]
  
  // Get proposals
  getProposals() // Returns global.proposals[]
  
  // Get proposals by status
  getProposalsByStatus(status) // filter by "open", "voting", etc.
  
  // Calculate vote weight
  calculateVoteWeight(nodeId, proposal)
  
  // Event emitter
  on(event, callback) // 'connected', 'disconnected', 'state-updated'
}
```

---

## 7. Configuration

### 7.1 Dashboard Configuration

**File:** `dashboard_ui/scripts/api-client.js`

```javascript
// Polling rate (milliseconds)
this.pollingRate = 10000; // 10 seconds

// Connection timeout
this.connectionTimeout = 5000; // 5 seconds
```

### 7.2 Node Configuration

**File:** `app/main.py`

```python
# CORS allowed origins
allow_origins=[
    "http://localhost:15000",
    "http://localhost:8080",
    "http://127.0.0.1:15000",
    "http://127.0.0.1:8080"
]
```

### 7.3 Immune System Targets

**File:** `app/immune_system.py`

```python
DEFAULT_HEALTH_TARGETS = {
    "max_avg_propagation_latency_ms": 10000,
    "min_active_peers": 3,
    "min_consensus_ratio": 0.67
}
```

---

## 8. Troubleshooting

### Issue 1: "CORS Error" in Browser Console

**Symptoms:**
```
Bloccata richiesta multiorigine (cross-origin): 
header CORS 'Access-Control-Allow-Origin' mancante
```

**Solution:**
```bash
# Rebuild node with CORS enabled
docker-compose down
docker-compose build --no-cache node-1
docker-compose up -d

# Verify CORS headers
curl -v -H "Origin: http://localhost:15000" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS http://localhost:8001/state 2>&1 | grep -i "access-control"
```

---

### Issue 2: "Active Peers = 0" (Incorrect Data)

**Symptoms:** Dashboard shows 0 peers but node is running

**Cause:** Browser cache or incorrect API path

**Solution:**
```bash
# Hard refresh browser
# Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
# Firefox: Ctrl+F5
# Safari: Cmd+Option+R

# Or clear cache + reload
# DevTools → Network → Disable cache → Reload
```

---

### Issue 3: "Node: unknown" (No Node ID)

**Cause:** API client using old data structure

**Solution:** Already fixed in v2.0 - ensure cache is cleared

---

### Issue 4: Dashboard Shows Old Data

**Cause:** Browser serving cached JavaScript

**Solution:** Files now use version parameter `?v=2`

```html
<script src="scripts/api-client.js?v=2"></script>
```

---

## 9. Development Guide

### 9.1 Adding a New Panel

1. **Add HTML section** in `index.html`:
```html
<section class="panel new-panel">
  <div class="panel-header">
    <h2>🔬 New System</h2>
  </div>
  <div class="panel-content">
    <!-- Content here -->
  </div>
</section>
```

2. **Add CSS** in `styles/panels.css`:
```css
.new-panel {
  /* Styles */
}
```

3. **Create monitor class** in `scripts/new-monitor.js`:
```javascript
class NewMonitor {
  constructor(api) {
    this.api = api;
  }
  
  init() {
    this.api.on('state-updated', () => this.update());
  }
  
  update() {
    // Update logic
  }
}
```

4. **Register in main.js**:
```javascript
const newMonitor = new NewMonitor(api);
newMonitor.init();
```

---

### 9.2 Modifying Data Extraction

**File:** `dashboard_ui/scripts/api-client.js`

**Example:** Add new health metric

```javascript
getHealthMetrics() {
  const health = this.lastState?.global?.immune_system?.health || {};
  
  return {
    latency: health.avg_propagation_latency_ms?.current || 0,
    peers: health.active_peers?.current || 0,
    consensus: health.consensus_ratio?.current || 0,
    messageSuccess: health.messages_propagated?.current || 0,
    
    // Add new metric
    memoryUsage: health.memory_usage_mb?.current || 0,
    
    targets: {
      max_latency_ms: health.avg_propagation_latency_ms?.target || 10000,
      min_peers: health.active_peers?.target || 3,
      
      // Add target
      max_memory_mb: health.memory_usage_mb?.target || 1024
    }
  };
}
```

---

## 10. Performance Optimization

### 10.1 Polling Optimization

**Current:** 10-second polling interval

**Optimization Options:**

```javascript
// Adaptive polling based on activity
if (hasActiveProposals) {
  this.pollingRate = 5000; // 5 seconds when active
} else {
  this.pollingRate = 30000; // 30 seconds when idle
}
```

### 10.2 DOM Updates

**Current:** Full re-render on each update

**Optimization:** Only update changed elements

```javascript
// Before (full re-render)
updateVitalSigns() {
  // Re-render all 4 cards
}

// After (differential update)
updateVitalSigns() {
  const newMetrics = this.api.getHealthMetrics();
  if (this.lastMetrics.latency !== newMetrics.latency) {
    // Only update latency card
  }
  this.lastMetrics = newMetrics;
}
```

---

## 11. Security Considerations

### 11.1 CORS Configuration

**Current:** Allows specific origins

```python
allow_origins=[
    "http://localhost:15000",
    "http://localhost:8080",
]
```

**Production:** Use environment variable

```python
ALLOWED_ORIGINS = os.getenv("DASHBOARD_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS
)
```

### 11.2 Authentication (Future)

**TODO:** Add JWT or API key authentication

```javascript
// Future implementation
class SynapseAPI {
  constructor() {
    this.apiKey = localStorage.getItem('synapse_api_key');
  }
  
  async fetchState() {
    const response = await fetch(`${this.endpoint}/state`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`
      }
    });
  }
}
```

---

## 12. Changelog

### Version 2.0 (23 October 2025)

#### ✅ Added
- Immune System integration in `/state` endpoint
- CORS middleware for dashboard access
- Real-time health metrics with traffic lights
- Node ID extraction from `global.nodes`
- Cache busting with `?v=2` parameter

#### 🔧 Fixed
- Active Peers showing 0 (was using wrong API path)
- Node ID showing "unknown" (was looking in wrong location)
- Consensus Time renamed to Consensus Ratio (correct semantics)
- Message Success Rate renamed to Messages Propagated (correct semantics)

#### 📝 Changed
- Updated `getHealthMetrics()` to use new data structure
- Updated `getNodeId()` to extract from `global.nodes`
- Modified traffic light thresholds for better sensitivity

### Version 1.0 (22 October 2025)

#### ✅ Initial Release
- Three-panel consciousness dashboard
- Biotech aesthetic with animated grid
- Vote simulator with contextual weights
- Evolutionary timeline visualization
- Real-time polling (10s interval)

---

## 📚 Additional Resources

- **Main README**: `/Users/fab/GitHub/synapse-ng/dashboard_ui/README.md`
- **Visual Mockup**: `/Users/fab/GitHub/synapse-ng/dashboard_ui/MOCKUP.md`
- **Delivery Doc**: `/Users/fab/GitHub/synapse-ng/dashboard_ui/DELIVERY.md`
- **System Summary**: `/Users/fab/GitHub/synapse-ng/docs/COMPLETE_SYSTEM_SUMMARY.md`

---

## 🤝 Contributing

To contribute improvements to the dashboard:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/dashboard-improvement`
3. Make changes and test locally
4. Submit pull request with detailed description
5. Update this documentation accordingly

---

## 📝 License

Same as Synapse-NG project

---

**Last Updated:** 23 October 2025  
**Maintainer:** Synapse-NG Development Team  
**Status:** ✅ Production Ready
