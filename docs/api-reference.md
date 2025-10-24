# API Reference

This document provides a detailed reference for the Synapse-NG API endpoints.

## Status & Monitoring

### `GET /state`

Returns the current state of the network.

### `GET /peers`

Returns a list of connected peers.

### `GET /channels`

Returns a list of subscribed channels.

## Tasks

### `POST /tasks?channel={CHANNEL_ID}`

Creates a new task.

**Request Body:**

```json
{
  "title": "Implement feature X",
  "tags": ["python", "security"],
  "reward": 100
}
```

### `POST /tasks/{task_id}/claim?channel={CHANNEL_ID}`

Claims a task.

### `POST /tasks/{task_id}/complete?channel={CHANNEL_ID}`

Marks a task as complete.

## Governance

### `POST /proposals?channel={CHANNEL_ID}`

Creates a new proposal.

**Request Body:**

```json
{
  "title": "Upgrade security protocol",
  "tags": ["security", "protocol"],
  "proposal_type": "network_operation",
  "params": {}
}
```

### `POST /proposals/{proposal_id}/vote?channel={CHANNEL_ID}`

Votes on a proposal.

**Request Body:**

```json
{
  "vote": "yes"
}
```

### `POST /proposals/{proposal_id}/close?channel={CHANNEL_ID}`

Closes a proposal and tallies the votes.

### `POST /governance/ratify/{proposal_id}?channel={CHANNEL_ID}`

Ratifies a proposal (validators only).

## Common Tools

### `POST /proposals?channel={CHANNEL_ID}`

Proposes the acquisition of a common tool.

**Request Body:**

```json
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
```

### `POST /tools/{tool_id}/execute?channel={CHANNEL_ID}&task_id={TASK_ID}`

Executes a common tool (authorized task assignees only).

**Request Body:**

```json
{
  "ip_address": "8.8.8.8"
}
```
