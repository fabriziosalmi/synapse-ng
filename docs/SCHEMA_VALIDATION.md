# Schema Validation System - Type-Safe Data Evolution

**Ensuring Structural Integrity Through Distributed Schemas**

Version: 1.0  
Last Updated: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Philosophy](#philosophy)
3. [Architecture](#architecture)
4. [Schema Structure](#schema-structure)
5. [Built-in Schemas](#built-in-schemas)
6. [API Usage](#api-usage)
7. [Schema Evolution](#schema-evolution)
8. [Security](#security)
9. [Best Practices](#best-practices)

---

## Overview

Synapse-NG implements a **schema validation system** that ensures all data flowing through the network is structured, valid, and error-proof. This system allows the network to evolve its data structures in a controlled and safe manner.

### Key Features

- ✅ **Type-safe data** - All entities validated against schemas
- ✅ **CRDT schemas** - Distributed schema definitions sync automatically
- ✅ **Creation-time validation** - Invalid data rejected immediately
- ✅ **Gossip-time validation** - Network self-heals from corrupt data
- ✅ **Schema evolution** - Upgrade schemas via governance proposals
- ✅ **Default values** - Missing fields auto-filled with defaults
- ✅ **Custom schemas** - Create domain-specific data types

## Philosophy

Just like biological organisms have DNA that defines their structure, Synapse-NG has **schemas** that define the structure of its data. This creates a **type-safe digital organism** where:

1. **Every piece of data has a defined structure** (schema)
2. **Invalid data is rejected** at creation time and during gossip
3. **Data structures can evolve** through governance
4. **All nodes agree on what "valid" means** (CRDT schemas)

### Why Schema Validation?

**Problem**: Without schemas:
- Invalid data corrupts network state
- No agreement on data structure
- Evolution breaks backward compatibility
- Debugging is nightmare (unexpected types)

**Solution**: With schemas:
- ✅ Data integrity guaranteed
- ✅ Self-documenting API
- ✅ Controlled evolution
- ✅ Type safety across entire network

## Architecture

### Three-Layer Validation

```
┌─────────────────────────────────────────────┐
│         APPLICATION LAYER                   │
│  ┌──────────────────────────────────┐      │
│  │  POST /tasks (validate)          │      │
│  │  POST /proposals (validate)      │      │
│  └──────────────────────────────────┘      │
├─────────────────────────────────────────────┤
│         GOSSIP LAYER                        │
│  ┌──────────────────────────────────┐      │
│  │  Receive task (validate schema)  │      │
│  │  → Valid: merge                  │      │
│  │  → Invalid: discard + log        │      │
│  └──────────────────────────────────┘      │
├─────────────────────────────────────────────┤
│         SCHEMA LAYER (CRDT)                 │
│  ┌──────────────────────────────────┐      │
│  │  global.schemas (LWW)            │      │
│  │  - task_v1                       │      │
│  │  - proposal_v1                   │      │
│  │  - custom schemas...             │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

## Schema Structure

### Schema Definition

```json
{
  "schema_name": "task_v1",
  "version": 1,
  "description": "Standard task schema",
  "fields": {
    "title": {
      "type": "string",
      "required": true,
      "min_length": 1,
      "max_length": 200
    },
    "reward": {
      "type": "integer",
      "required": false,
      "min": 0,
      "default": 0
    },
    "tags": {
      "type": "list[string]",
      "required": false,
      "default": []
    },
    "status": {
      "type": "enum",
      "required": false,
      "values": ["open", "claimed", "in_progress", "completed"],
      "default": "open"
    }
  },
  "created_at": "2025-10-02T10:00:00Z",
  "updated_at": "2025-10-02T10:00:00Z"
}
```

### Supported Types

| Type | Description | Validations | Example |
|------|-------------|-------------|---------|
| `string` | Text value | `min_length`, `max_length` | `"Fix bug"` |
| `integer` | Whole number | `min`, `max` | `100` |
| `list[string]` | Array of strings | Item type validation | `["ui", "bug"]` |
| `object` | JSON object | Type check only | `{"key": "value"}` |
| `enum` | One of predefined values | `values` array | `"open"` (from `["open", "closed"]`) |

### Field Properties

| Property | Required | Description | Example |
|----------|----------|-------------|---------|
| `type` | ✅ Yes | Data type | `"string"` |
| `required` | No | If field is mandatory | `true` |
| `default` | No | Default value if missing | `0` |
| `min_length` | No | Minimum string length | `1` |
| `max_length` | No | Maximum string length | `200` |
| `min` | No | Minimum integer value | `0` |
| `max` | No | Maximum integer value | `1000` |
| `values` | No (required for enum) | Allowed enum values | `["yes", "no"]` |

## Built-in Schemas

### task_v1

Standard schema for tasks.

**Fields:**
- `title` (string, required, 1-200 chars)
- `reward` (integer, optional, min 0, default 0)
- `tags` (list[string], optional, default [])
- `description` (string, optional, default "")
- `assignee` (string, optional, default null)
- `status` (enum, optional, values: ["open", "claimed", "in_progress", "completed"], default "open")

### proposal_v1

Standard schema for proposals.

**Fields:**
- `title` (string, required, 1-200 chars)
- `description` (string, optional, default "")
- `proposal_type` (enum, required, values: ["generic", "config_change", "network_operation"], default "generic")
- `params` (object, optional, default {})
- `tags` (list[string], optional, default [])

## API Usage

### 1. Create Task (with validation)

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement feature",
    "reward": 100,
    "tags": ["ui", "feature"],
    "description": "Add new dashboard widget",
    "schema_name": "task_v1"
  }'
```

**Success Response:**
```json
{
  "id": "task_abc123",
  "title": "Implement feature",
  "reward": 100,
  "tags": ["ui", "feature"],
  "description": "Add new dashboard widget",
  "status": "open",
  "assignee": null,
  "schema_name": "task_v1",
  "created_at": "2025-10-02T10:00:00Z"
}
```

**Validation Error Response:**
```json
{
  "detail": "Validazione schema fallita: Campo 'title' deve avere almeno 1 caratteri"
}
```

### 2. Validation Errors

```bash
# Missing required field
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "reward": 100,
    "schema_name": "task_v1"
  }'
# Error: Campo obbligatorio 'title' mancante

# Invalid type
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "reward": "invalid",
    "schema_name": "task_v1"
  }'
# Error: Campo 'reward' deve essere integer, ricevuto str

# Invalid enum value
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "status": "invalid_status",
    "schema_name": "task_v1"
  }'
# Error: Campo 'status' deve essere uno di ['open', 'claimed', 'in_progress', 'completed'], ricevuto 'invalid_status'
```

### 3. Get All Schemas

```bash
curl http://localhost:8001/schemas
```

**Response:**
```json
{
  "schemas": {
    "task_v1": {
      "schema_name": "task_v1",
      "version": 1,
      "fields": {...}
    },
    "proposal_v1": {
      "schema_name": "proposal_v1",
      "version": 1,
      "fields": {...}
    }
  },
  "count": 2
}
```

### 4. Get Single Schema

```bash
curl http://localhost:8001/schemas/task_v1
```

### 5. Validate Data (without saving)

```bash
curl -X POST "http://localhost:8001/schemas/validate?schema_name=task_v1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "reward": 50
  }'
```

**Response:**
```json
{
  "valid": true,
  "schema_name": "task_v1",
  "data_with_defaults": {
    "title": "Test task",
    "reward": 50,
    "tags": [],
    "description": "",
    "assignee": null,
    "status": "open"
  }
}
```

## Schema Evolution via Governance

### Create New Schema Version

To evolve data structures, create a `network_operation` proposal:

```bash
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add priority field to tasks",
    "description": "Create task_v2 schema with priority support",
    "proposal_type": "network_operation",
    "params": {
      "operation": "update_schema",
      "schema_name": "task_v2",
      "schema_definition": {
        "schema_name": "task_v2",
        "version": 2,
        "description": "Task schema with priority field",
        "fields": {
          "title": {"type": "string", "required": true, "min_length": 1, "max_length": 200},
          "reward": {"type": "integer", "required": false, "min": 0, "default": 0},
          "tags": {"type": "list[string]", "required": false, "default": []},
          "description": {"type": "string", "required": false, "default": ""},
          "priority": {
            "type": "enum",
            "required": false,
            "values": ["low", "medium", "high"],
            "default": "medium"
          },
          "assignee": {"type": "string", "required": false, "default": null},
          "status": {
            "type": "enum",
            "required": false,
            "values": ["open", "claimed", "in_progress", "completed"],
            "default": "open"
          }
        }
      }
    }
  }'
```

### Complete Flow

1. **Propose schema update** (any node)
2. **Community votes** (weighted voting)
3. **Close proposal** (calculate outcome)
4. **Validator ratification** (majority consensus)
5. **Automatic execution** (schema added to `global.schemas`)
6. **Use new schema** (`schema_name: "task_v2"`)

### Example: Using New Schema

After the schema is ratified and executed:

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Critical bug fix",
    "reward": 200,
    "priority": "high",
    "schema_name": "task_v2"
  }'
```

## Gossip-Time Validation

### How It Works

When a node receives a task or proposal via gossip:

1. **Extract schema_name** from the object
2. **Validate against schema** using `validate_against_schema()`
3. **If valid**: Merge into local state (LWW)
4. **If invalid**: Discard + log warning

### Logs

**Valid object:**
```
✅ Task abc123... accettato (nuovo, schema validato)
```

**Invalid object:**
```
❌ Task xyz789... rifiutato durante gossip: Campo 'title' deve avere almeno 1 caratteri
```

### Benefits

- **Network resilience**: Malformed data never enters the state
- **Prevents corruption**: Invalid data can't spread via gossip
- **Self-healing**: If a node has corrupt data, other nodes won't accept it
- **Debugging**: Clear logs of validation failures

## Security Considerations

### Attack Vectors

1. **Malformed Data Injection**
   - ❌ **Before**: Malicious node could inject invalid data
   - ✅ **After**: Validation rejects all invalid data

2. **Schema Bypassing**
   - ❌ **Before**: Nodes could ignore schemas
   - ✅ **After**: Gossip validation enforces schemas network-wide

3. **Type Confusion**
   - ❌ **Before**: String where integer expected → runtime errors
   - ✅ **After**: Type validation prevents confusion

### Best Practices

1. **Always specify schema_name** when creating tasks/proposals
2. **Use strict validation** (required fields, min/max lengths)
3. **Test schemas** with `/schemas/validate` before proposing
4. **Version schemas** (task_v1, task_v2) for backward compatibility
5. **Monitor logs** for validation failures (possible attacks)

## Migration Strategies

### Strategy 1: Parallel Schemas

Run old and new schemas in parallel:

```
task_v1 (old) → still valid
task_v2 (new) → new features

Nodes can create tasks with either schema.
Eventually, deprecate task_v1 via governance.
```

### Strategy 2: Graceful Upgrade

1. Propose `task_v2` with new fields (all optional with defaults)
2. Once ratified, start using `task_v2` for new tasks
3. Old `task_v1` tasks remain valid (backward compatible)
4. Gradually migrate old tasks or leave them as-is

### Strategy 3: Breaking Change

1. Propose `task_v2` with incompatible changes
2. Before execution, manually migrate existing tasks
3. After execution, only `task_v2` is valid
4. Old `task_v1` tasks fail validation (must be updated)

**Note:** Strategy 3 requires careful coordination and should be used sparingly.

## Example: Complete Schema Evolution Flow

### Step 1: Current State

```bash
# Check current schemas
curl http://localhost:8001/schemas | jq '.schemas | keys'
# Output: ["task_v1", "proposal_v1"]
```

### Step 2: Propose New Schema

```bash
PROPOSAL_ID=$(curl -s -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Add estimated_hours field to tasks",
    "proposal_type": "network_operation",
    "params": {
      "operation": "update_schema",
      "schema_name": "task_v2",
      "schema_definition": {
        "schema_name": "task_v2",
        "version": 2,
        "fields": {
          "title": {"type": "string", "required": true, "min_length": 1},
          "estimated_hours": {"type": "integer", "min": 1, "max": 100, "default": 1},
          "reward": {"type": "integer", "min": 0, "default": 0}
        }
      }
    }
  }' | jq -r '.id')

echo "Proposal ID: $PROPOSAL_ID"
```

### Step 3: Vote and Ratify

```bash
# Vote (3 nodes)
curl -X POST "http://localhost:8001/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

curl -X POST "http://localhost:8002/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

curl -X POST "http://localhost:8003/proposals/$PROPOSAL_ID/vote?channel=global" \
  -H "Content-Type: application/json" \
  -d '{"vote": "yes"}'

# Close
curl -X POST "http://localhost:8001/proposals/$PROPOSAL_ID/close?channel=global"

# Ratify (validators)
curl -X POST "http://localhost:8001/governance/ratify/$PROPOSAL_ID?channel=global"
curl -X POST "http://localhost:8002/governance/ratify/$PROPOSAL_ID?channel=global"
```

### Step 4: Wait for Execution

```bash
# Wait for command processor (10-15 seconds)
sleep 15

# Check if schema exists
curl http://localhost:8001/schemas/task_v2
```

### Step 5: Use New Schema

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Refactor authentication module",
    "estimated_hours": 8,
    "reward": 500,
    "schema_name": "task_v2"
  }'
```

## Monitoring and Debugging

### Check Validation Logs

```bash
docker logs node-1 2>&1 | grep -i "schema"
```

**Expected output:**
```
✅ Task validato con successo contro schema 'task_v1'
✅ Proposal validata con successo contro schema 'proposal_v1'
✅ Task abc123... accettato (nuovo, schema validato)
```

**Error indicators:**
```
❌ Task validation failed: Campo 'title' deve avere almeno 1 caratteri
❌ Task xyz789... rifiutato durante gossip: Campo obbligatorio 'reward' mancante
```

### Test Schema Locally

```bash
# Test valid data
curl -X POST "http://localhost:8001/schemas/validate?schema_name=task_v1" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "reward": 100}'

# Test invalid data
curl -X POST "http://localhost:8001/schemas/validate?schema_name=task_v1" \
  -H "Content-Type: application/json" \
  -d '{"title": "", "reward": -50}'
```

## Conclusion

The Schema Validation System transforms Synapse-NG from a **loosely-typed gossip network** into a **strongly-typed digital organism** with:

✅ **Type safety**: All data conforms to defined schemas  
✅ **Evolution capability**: Schemas can be upgraded via governance  
✅ **Network resilience**: Invalid data is rejected at every layer  
✅ **Self-documentation**: Schemas serve as living documentation  
✅ **Backward compatibility**: Multiple schema versions can coexist  

This is the **genetic code** of the digital organism. Just as DNA mutations must pass natural selection, schema changes must pass governance. 🧬✨

---

**Versione:** 1.0  
**Data:** 2 Ottobre 2025  
**Autore:** Synapse-NG Development Team
