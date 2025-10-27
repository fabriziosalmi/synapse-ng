# API Reference

This document provides a comprehensive reference for all Synapse-NG API endpoints. The API enables interaction with the autonomous decentralized network, including task management, governance, evolution, and more.

## Table of Contents

- [Authentication](#authentication)
- [Base Information](#base-information)
- [Network State & Monitoring](#network-state--monitoring)
- [Task Management](#task-management)
  - [Basic Tasks](#basic-tasks)
  - [Composite Tasks (Teams)](#composite-tasks-teams)
  - [Task Auctions](#task-auctions)
- [Skills & Profiles](#skills--profiles)
- [Governance & Proposals](#governance--proposals)
- [Zero-Knowledge Proofs (ZKP)](#zero-knowledge-proofs-zkp)
- [AI Agent](#ai-agent)
- [Self-Upgrade System](#self-upgrade-system)
- [Evolutionary Engine](#evolutionary-engine)
- [Common Tools](#common-tools)
- [Treasury Management](#treasury-management)
- [Configuration Management](#configuration-management)
- [Schema Management](#schema-management)
- [WebRTC & P2P](#webrtc--p2p)
- [RAFT Consensus](#raft-consensus)
- [WebSocket](#websocket)

## Authentication

Currently, most endpoints use the `NODE_ID` from the environment to identify the requesting node. Some operations (like voting, task claiming) verify node permissions based on network state and reputation.

**Common Query Parameters:**
- `channel`: Channel ID where the operation takes place (required for most endpoints)
- `task_id`: Task identifier (for task-related operations)
- `proposal_id`: Proposal identifier (for governance operations)

## Base Information

### `GET /`

Returns the web dashboard interface.

**Response:** HTML page

---

### `GET /whoami`

Returns the current node's identity.

**Response:**
```json
{
  "node_id": "node-123",
  "public_key": "base64_encoded_public_key"
}
```

---

## Network State & Monitoring

### `GET /state`

Returns the complete network state including nodes, tasks, proposals, reputations, balances, and immune system status.

**Response:**
```json
{
  "global": {
    "nodes": {
      "node-123": {
        "id": "node-123",
        "public_key": "...",
        "reputation": {
          "_total": 150,
          "_last_updated": "2024-01-01T12:00:00Z",
          "tags": {
            "python": 50,
            "security": 100
          }
        },
        "balance": 1000
      }
    },
    "immune_system": {
      "enabled": true,
      "active_issues": [],
      "last_scan": "2024-01-01T12:00:00Z"
    }
  },
  "channel-1": {
    "participants": ["node-123", "node-456"],
    "tasks": {},
    "proposals": {},
    "treasury_balance": 5000
  }
}
```

---

### `GET /channels`

Returns the list of channels subscribed by this node.

**Response:**
```json
["global", "channel-1", "channel-2"]
```

---

### `GET /network/stats`

Returns network statistics including peer count, message counts, and performance metrics.

**Response:**
```json
{
  "total_peers": 5,
  "messages_sent": 1234,
  "messages_received": 5678,
  "uptime_seconds": 86400
}
```

---

### `GET /webrtc/connections`

Returns the status of WebRTC peer connections.

**Response:**
```json
{
  "connections": [
    {
      "peer_id": "node-456",
      "state": "connected",
      "ice_connection_state": "connected",
      "data_channel_state": "open"
    }
  ]
}
```

---

### `GET /webrtc/ice-metrics`

Returns ICE (Interactive Connectivity Establishment) metrics for WebRTC connections.

**Response:**
```json
{
  "metrics": [
    {
      "peer_id": "node-456",
      "candidate_pairs": 3,
      "selected_pair": "udp/host/relay"
    }
  ]
}
```

---

### `GET /pubsub/stats`

Returns PubSub protocol statistics.

**Response:**
```json
{
  "total_messages": 1000,
  "subscribed_channels": 3,
  "message_rate": 10.5
}
```

---

## Task Management

### Basic Tasks

### `POST /tasks`

Creates a new task with optional reward in Synapse Points.

**Query Parameters:**
- `channel` (required): Channel ID
- `funded_by` (optional): "user" (default) or "treasury"

**Request Body:**
```json
{
  "title": "Implement feature X",
  "description": "Detailed description of the task",
  "tags": ["python", "security"],
  "reward": 100,
  "schema_name": "task_v2",
  "required_tools": ["geolocation_api"],
  "enable_auction": false,
  "max_reward": 200,
  "auction_deadline_hours": 24
}
```

**Response:**
```json
{
  "id": "task-uuid",
  "title": "Implement feature X",
  "status": "open",
  "creator": "node-123",
  "reward": 100,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**
- `201`: Task created successfully
- `400`: Channel not subscribed or validation failed
- `403`: Insufficient balance

---

### `POST /tasks/{task_id}/claim`

Claims an open task.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Task claimed successfully",
  "task_id": "task-uuid",
  "assignee": "node-123"
}
```

**Status Codes:**
- `200`: Task claimed successfully
- `400`: Task already claimed or not found
- `403`: Node not eligible to claim

---

### `POST /tasks/{task_id}/progress`

Updates task progress (assignee only).

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "progress_note": "Completed initial implementation"
}
```

**Response:**
```json
{
  "message": "Progress updated",
  "task_id": "task-uuid"
}
```

---

### `POST /tasks/{task_id}/complete`

Marks a task as complete and transfers the reward to the assignee.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Task completed",
  "task_id": "task-uuid",
  "reward_transferred": 95,
  "tax_collected": 5
}
```

**Status Codes:**
- `200`: Task completed successfully
- `400`: Task not claimed or already completed
- `403`: Only assignee can complete

---

### `DELETE /tasks/{task_id}`

Deletes a task (creator only, only if not claimed).

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Task deleted successfully",
  "task_id": "task-uuid"
}
```

**Status Codes:**
- `200`: Task deleted
- `403`: Not authorized or task already claimed

---

### Composite Tasks (Teams)

### `POST /tasks/composite/create`

Creates a composite task requiring a team of nodes with specific skills.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "title": "Build Full-Stack Application",
  "description": "Complex project requiring multiple skills",
  "total_reward": 1000,
  "required_team_size": 3,
  "subtasks": [
    {
      "title": "Backend API",
      "required_skills": ["python", "api"],
      "reward_percentage": 40
    },
    {
      "title": "Frontend UI",
      "required_skills": ["react", "css"],
      "reward_percentage": 40
    },
    {
      "title": "DevOps",
      "required_skills": ["docker", "ci/cd"],
      "reward_percentage": 20
    }
  ]
}
```

**Response:**
```json
{
  "task_id": "composite-task-uuid",
  "status": "forming_team",
  "workspace_channel": "workspace_composite-task-uuid",
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### `POST /tasks/composite/{task_id}/apply`

Apply to join a composite task team.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "message": "I have 5 years experience with Python and FastAPI"
}
```

**Response:**
```json
{
  "message": "Application submitted",
  "task_id": "composite-task-uuid",
  "applicant_id": "node-123"
}
```

---

### `POST /tasks/composite/{task_id}/accept/{applicant_id}`

Accept a team member application (creator only).

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Team member accepted",
  "team_size": 2,
  "required_size": 3
}
```

---

### `POST /tasks/composite/{task_id}/claim`

Claim the composite task (for backward compatibility, prefer /apply).

**Query Parameters:**
- `channel` (required): Channel ID

---

### `POST /tasks/composite/{task_id}/subtask/{subtask_id}/complete`

Mark a subtask as complete.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Subtask completed",
  "subtask_id": "subtask-1",
  "all_subtasks_complete": false
}
```

---

### `GET /tasks/composite`

List all composite tasks.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "composite_tasks": [
    {
      "id": "composite-task-uuid",
      "title": "Build Full-Stack Application",
      "status": "forming_team",
      "team_size": 2,
      "required_team_size": 3
    }
  ]
}
```

---

### `GET /tasks/composite/{task_id}`

Get details of a specific composite task.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "id": "composite-task-uuid",
  "title": "Build Full-Stack Application",
  "status": "in_progress",
  "team_members": ["node-123", "node-456"],
  "subtasks": [...],
  "workspace_channel": "workspace_composite-task-uuid"
}
```

---

### Task Auctions

### `POST /tasks/{task_id}/bid`

Place a bid on a task with auction enabled.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "amount": 80,
  "estimated_days": 5
}
```

**Response:**
```json
{
  "message": "Bid placed successfully",
  "task_id": "task-uuid",
  "bidder": "node-123",
  "amount": 80
}
```

**Status Codes:**
- `201`: Bid placed successfully
- `400`: Auction closed or invalid bid
- `403`: Cannot bid on own task

---

### `POST /tasks/{task_id}/select_bid`

Select a winning bid (task creator only).

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "bidder_id": "node-456"
}
```

**Response:**
```json
{
  "message": "Bid selected",
  "winner": "node-456",
  "amount": 80,
  "task_status": "claimed"
}
```

---

## Skills & Profiles

### `POST /skills/profile`

Update the current node's skills profile.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "skills": ["python", "react", "docker"],
  "bio": "Full-stack developer with 5 years experience"
}
```

**Response:**
```json
{
  "message": "Profile updated",
  "node_id": "node-123",
  "skills": ["python", "react", "docker"],
  "bio": "Full-stack developer with 5 years experience"
}
```

---

### `GET /skills/profile`

Get skills profile of a node.

**Query Parameters:**
- `channel` (required): Channel ID
- `node_id` (optional): Node ID (defaults to current node)

**Response:**
```json
{
  "node_id": "node-123",
  "skills": ["python", "react", "docker"],
  "bio": "Full-stack developer with 5 years experience"
}
```

---

## Governance & Proposals

### `POST /proposals`

Create a new governance proposal.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "title": "Upgrade security protocol",
  "description": "Proposal to implement new encryption standard",
  "proposal_type": "network_operation",
  "params": {
    "operation": "upgrade_protocol",
    "version": "2.0"
  },
  "tags": ["security", "protocol"],
  "schema_name": "proposal_v1"
}
```

**Proposal Types:**
- `generic`: General proposals
- `config_change`: Change network configuration
- `network_operation`: Operational changes
- `command`: Execute specific commands (e.g., acquire tools)
- `code_upgrade`: Self-upgrade proposals

**Response:**
```json
{
  "id": "proposal-uuid",
  "title": "Upgrade security protocol",
  "proposer": "node-123",
  "status": "open",
  "votes": {},
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### `POST /proposals/{proposal_id}/vote`

Vote on a proposal.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "vote": "yes",
  "anonymous": false,
  "zkp_proof": null
}
```

For anonymous voting with Zero-Knowledge Proofs:
```json
{
  "vote": "yes",
  "anonymous": true,
  "zkp_proof": {
    "commitment": "...",
    "challenge": "...",
    "response": "...",
    "tier": "gold",
    "tier_weight": 3
  }
}
```

**Response:**
```json
{
  "message": "Vote recorded",
  "proposal_id": "proposal-uuid",
  "voter": "node-123",
  "vote": "yes"
}
```

---

### `POST /proposals/{proposal_id}/close`

Close a proposal and tally votes.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Proposal closed",
  "proposal_id": "proposal-uuid",
  "result": "approved",
  "yes_votes": 15,
  "no_votes": 5
}
```

---

### `GET /proposals/{proposal_id}/details`

Get detailed information about a proposal.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "id": "proposal-uuid",
  "title": "Upgrade security protocol",
  "description": "...",
  "proposer": "node-123",
  "status": "open",
  "votes": {
    "node-123": "yes",
    "node-456": "no"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "closed_at": null
}
```

---

### `POST /governance/ratify/{proposal_id}`

Ratify a proposal (validators only).

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Proposal ratified",
  "proposal_id": "proposal-uuid",
  "executed": true
}
```

**Status Codes:**
- `200`: Proposal ratified successfully
- `403`: Not a validator or proposal not approved

---

## Zero-Knowledge Proofs (ZKP)

### `GET /zkp/generate_proof`

Generate a Zero-Knowledge Proof for anonymous voting.

**Query Parameters:**
- `channel` (required): Channel ID
- `proposal_id` (required): Proposal ID

**Response:**
```json
{
  "proof": {
    "commitment": "base64_encoded_commitment",
    "challenge": "base64_encoded_challenge",
    "response": "base64_encoded_response",
    "tier": "gold",
    "tier_weight": 3
  },
  "current_reputation": 150,
  "message": "Proof generated successfully"
}
```

---

## AI Agent

The AI Agent allows natural language interaction with the network.

### `POST /agent/prompt`

Send a natural language prompt to the AI agent.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "prompt": "Create a task to implement a new API endpoint with 100 SP reward"
}
```

**Response:**
```json
{
  "message": "Prompt processed by AI agent",
  "prompt": "Create a task...",
  "actions_generated": 1,
  "actions_executed": [
    {
      "action": "create_task",
      "params": {
        "title": "Implement new API endpoint",
        "reward": 100
      },
      "reasoning": "User requested task creation with specified reward",
      "status": "executed"
    }
  ],
  "raw_llm_response": "..."
}
```

**Status Codes:**
- `200`: Prompt processed successfully
- `503`: AI Agent not available

---

### `GET /agent/objectives`

Get current AI agent objectives and statistics.

**Response:**
```json
{
  "objectives": {
    "maximize_sp": true,
    "build_reputation": true,
    "contribute_to_network": true
  },
  "stats": {
    "actions_executed": 50,
    "tasks_created": 10,
    "proposals_voted": 20
  }
}
```

---

### `POST /agent/objectives`

Set or update AI agent objectives.

**Request Body:**
```json
{
  "maximize_sp": true,
  "build_reputation": true,
  "contribute_to_network": true,
  "focus_areas": ["development", "governance"]
}
```

**Response:**
```json
{
  "message": "Objectives updated",
  "objectives": {...}
}
```

---

### `GET /agent/status`

Get AI agent status and health.

**Response:**
```json
{
  "enabled": true,
  "model_loaded": true,
  "last_action": "2024-01-01T12:00:00Z",
  "pending_actions": 0
}
```

---

## Self-Upgrade System

### `POST /upgrades/propose`

Propose a code upgrade to the network.

**Query Parameters:**
- `channel` (required): Channel ID
- `title` (required): Upgrade title
- `description` (required): Description of changes
- `version` (required): Target version (e.g., "1.2.0")
- `package_url` (required): URL or IPFS hash of WASM package
- `package_hash` (required): SHA256 hash of package
- `package_size` (optional): Package size in bytes
- `wasm_module_name` (optional): WASM module name (default: "upgrade")

**Response:**
```json
{
  "message": "Upgrade proposal created",
  "proposal_id": "proposal-uuid",
  "version": "1.2.0",
  "package_hash": "sha256...",
  "next_steps": [
    "1. Community vote on proposal",
    "2. Validator set ratification",
    "3. Automatic download and verification",
    "4. Execution in WASM sandbox",
    "5. Network upgrade completed"
  ]
}
```

---

### `POST /upgrades/{proposal_id}/test`

Test an upgrade in sandbox mode.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Upgrade tested successfully",
  "test_results": {
    "syntax_valid": true,
    "security_checks": "passed",
    "performance_impact": "low"
  }
}
```

---

### `GET /upgrades/status`

Get status of all upgrades.

**Response:**
```json
{
  "active_upgrades": [
    {
      "proposal_id": "proposal-uuid",
      "version": "1.2.0",
      "status": "testing",
      "progress": 50
    }
  ]
}
```

---

### `GET /upgrades/history`

Get upgrade history.

**Response:**
```json
{
  "upgrades": [
    {
      "version": "1.1.0",
      "applied_at": "2024-01-01T00:00:00Z",
      "status": "success"
    }
  ]
}
```

---

### `POST /upgrades/{proposal_id}/rollback`

Rollback a failed upgrade.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Upgrade rolled back successfully",
  "restored_version": "1.1.0"
}
```

---

## Evolutionary Engine

The Evolutionary Engine enables the network to analyze itself and propose autonomous improvements.

### `POST /evolution/analyze`

Analyze the network for inefficiencies.

**Query Parameters:**
- `channel` (required): Channel ID

**Response:**
```json
{
  "message": "Network analyzed",
  "inefficiencies_found": 3,
  "inefficiencies": [
    {
      "type": "performance",
      "severity": "high",
      "description": "Task assignment algorithm is O(n²)",
      "affected_component": "task_matching"
    }
  ]
}
```

---

### `POST /evolution/generate`

Generate code to fix identified inefficiencies.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "inefficiency_id": "ineff-uuid",
  "language": "python",
  "target_component": "task_matching"
}
```

**Response:**
```json
{
  "message": "Code generated",
  "code": "def improved_task_matching(...):\n    ...",
  "language": "python",
  "estimated_improvement": "60% faster"
}
```

---

### `POST /evolution/propose`

Create a proposal for autonomous evolution.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "title": "Optimize task matching algorithm",
  "generated_code_id": "code-uuid",
  "rationale": "Current algorithm is too slow for large networks"
}
```

**Response:**
```json
{
  "message": "Evolution proposal created",
  "proposal_id": "proposal-uuid",
  "requires_community_vote": true
}
```

---

### `GET /evolution/status`

Get status of evolutionary engine.

**Response:**
```json
{
  "enabled": true,
  "last_analysis": "2024-01-01T12:00:00Z",
  "pending_evolutions": 2,
  "applied_evolutions": 5
}
```

---

## Common Tools

Common tools are shared API credentials or services that the network can acquire and use collectively.

### `POST /proposals` (for tool acquisition)

Propose acquisition of a common tool.

**Query Parameters:**
- `channel` (required): Channel ID

**Request Body:**
```json
{
  "title": "Acquire Geolocation API Tool",
  "description": "Proposal to acquire geolocation service",
  "proposal_type": "command",
  "command": {
    "operation": "acquire_common_tool",
    "params": {
      "channel": "channel-1",
      "tool_id": "geolocation_api",
      "monthly_cost_sp": 100,
      "credentials_to_encrypt": "API_KEY_HERE",
      "description": "Geolocation API for analytics tasks",
      "type": "api_key"
    }
  }
}
```

---

### `POST /tools/{tool_id}/execute`

Execute a common tool (authorized task assignees only).

**Query Parameters:**
- `channel` (required): Channel ID
- `task_id` (required): Task ID

**Request Body:**
```json
{
  "ip_address": "8.8.8.8"
}
```

**Response:**
```json
{
  "result": {
    "country": "United States",
    "city": "Mountain View",
    "latitude": 37.386,
    "longitude": -122.084
  },
  "tool_id": "geolocation_api",
  "execution_cost_sp": 1
}
```

**Status Codes:**
- `200`: Tool executed successfully
- `403`: Not authorized (must be task assignee)
- `402`: Insufficient task budget

---

## Treasury Management

### `GET /treasury/{channel_id}`

Get treasury balance for a specific channel.

**Response:**
```json
{
  "channel_id": "channel-1",
  "balance": 5000,
  "reserved": 1000,
  "available": 4000
}
```

---

### `GET /treasuries`

Get treasury balances for all channels.

**Response:**
```json
{
  "treasuries": {
    "channel-1": 5000,
    "channel-2": 3000
  }
}
```

---

## Configuration Management

### `GET /config`

Get current network configuration.

**Response:**
```json
{
  "task_completion_tax": 0.05,
  "proposal_voting_period": 86400,
  "validator_set": ["node-123", "node-456"],
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

### `GET /config/history`

Get configuration change history.

**Response:**
```json
{
  "changes": [
    {
      "key": "task_completion_tax",
      "old_value": 0.1,
      "new_value": 0.05,
      "changed_at": "2024-01-01T00:00:00Z",
      "changed_by": "proposal-uuid"
    }
  ]
}
```

---

## Schema Management

### `GET /schemas`

Get all available schemas.

**Response:**
```json
{
  "schemas": {
    "task_v1": {...},
    "task_v2": {...},
    "proposal_v1": {...}
  }
}
```

---

### `GET /schemas/{schema_name}`

Get a specific schema definition.

**Response:**
```json
{
  "name": "task_v2",
  "version": "2.0",
  "fields": {
    "title": {"type": "string", "required": true},
    "reward": {"type": "integer", "min": 0}
  }
}
```

---

### `POST /schemas/validate`

Validate data against a schema.

**Request Body:**
```json
{
  "schema_name": "task_v2",
  "data": {
    "title": "Test task",
    "reward": 100
  }
}
```

**Response:**
```json
{
  "valid": true,
  "errors": []
}
```

---

## WebRTC & P2P

### `POST /bootstrap/handshake`

Perform initial handshake with bootstrap node.

**Request Body:**
```json
{
  "node_id": "node-123",
  "public_key": "base64_encoded_key"
}
```

**Response:**
```json
{
  "message": "Handshake successful",
  "peers": ["node-456", "node-789"]
}
```

---

### `POST /p2p/signal/relay`

Relay WebRTC signaling message to another peer.

**Request Body:**
```json
{
  "target_peer_id": "node-456",
  "signal_data": {...}
}
```

---

### `POST /p2p/signal/receive`

Receive WebRTC signaling message.

**Request Body:**
```json
{
  "from_peer_id": "node-123",
  "signal_data": {...}
}
```

---

## RAFT Consensus

### `POST /raft/request_vote`

Request vote from a node (RAFT consensus algorithm).

**Request Body:**
```json
{
  "term": 5,
  "candidate_id": "node-123",
  "last_log_index": 100,
  "last_log_term": 4
}
```

**Response:**
```json
{
  "term": 5,
  "vote_granted": true
}
```

---

### `POST /raft/append_entries`

Append entries to log (RAFT consensus algorithm).

**Request Body:**
```json
{
  "term": 5,
  "leader_id": "node-123",
  "prev_log_index": 99,
  "prev_log_term": 4,
  "entries": [...],
  "leader_commit": 100
}
```

**Response:**
```json
{
  "term": 5,
  "success": true
}
```

---

## WebSocket

### `WebSocket /ws`

WebSocket endpoint for real-time bidirectional communication.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

**Incoming Messages:**
```json
{
  "type": "task_created",
  "data": {
    "task_id": "task-uuid",
    "title": "New task"
  }
}
```

**Outgoing Messages:**
```json
{
  "type": "subscribe",
  "channel": "channel-1"
}
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
  "detail": "Validation error message"
}
```

**403 Forbidden:**
```json
{
  "detail": "Not authorized to perform this action"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## Rate Limiting

Currently, there are no rate limits enforced at the API level. However, resource-intensive operations (like AI agent prompts or evolution analysis) may have internal throttling based on network load and node reputation.
