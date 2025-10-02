# Self-Upgrade System - Autonomous Code Evolution

**Decentralized Network Self-Modification**

Version: 1.0  
Last Updated: October 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Creating WASM Packages](#creating-wasm-packages)
4. [Upgrade Workflow](#upgrade-workflow)
5. [API Reference](#api-reference)
6. [Security Model](#security-model)
7. [Monitoring & Rollback](#monitoring--rollback)
8. [Best Practices](#best-practices)

---

## Overview

Synapse-NG includes a **decentralized self-upgrade system** that allows the network to update its own source code securely and autonomously, without centralized developer intervention.

### Key Features

- 🔄 **Code upgrade proposals** - Special proposals for code updates
- 📦 **WASM packages** - Code distributed as WebAssembly modules
- 🔒 **Cryptographic verification** - SHA256 hash validation before execution
- 🧪 **Secure sandbox** - Isolated execution with wasmtime
- 👥 **Democratic approval** - Community vote + validator ratification
- ⏮️ **Automatic rollback** - Revert to previous version if upgrade fails
- 📊 **Version tracking** - Complete version history and audit trail

### Why Self-Upgrade?

**Problem**: Traditional networks require:
- Centralized developers to push updates
- All nodes manually upgrade
- Downtime during deployment
- Trust in update source

**Solution**: Synapse-NG self-upgrades through:
- Democratic community approval
- Automatic cryptographic verification
- Sandboxed safe execution
- Zero downtime deployment
- Immutable audit trail

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│ SelfUpgradeManager                                          │
├─────────────────────────────────────────────────────────────┤
│ • Download packages (IPFS/HTTP/HTTPS)                      │
│ • Verify SHA256 hash                                        │
│ • Test in WASM sandbox                                      │
│ • Execute upgrade                                           │
│ • Version management                                        │
│ • Rollback capability                                       │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐         ┌──────────────────┐
│ IPFS/HTTP Client │         │ wasmtime Engine  │
│ Package download │         │ Sandbox execution│
└──────────────────┘         └──────────────────┘
```

### Approval Flow

```
┌──────────────────┐
│ 1. Proposal      │  NODE_A creates code_upgrade proposal
│    Creation      │  with package_url, hash, version
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Community     │  Nodes vote (approval/rejection)
│    Voting        │  Weight based on reputation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 3. Approval      │  If majority → status="approved"
│    Check         │  
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 4. Validator     │  Validator set votes via Raft
│    Ratification  │  Distributed consensus
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. Execution     │  EXECUTE_UPGRADE in execution_log
│    Log           │  Append-only CRDT
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 6. Upgrade       │  upgrade_executor_loop processes
│    Execution     │  command and executes upgrade
└──────────────────┘
```

### Package Sources

| Source | URL Format | Use Case |
|--------|------------|----------|
| **IPFS** | `ipfs://Qm...` | Decentralized storage, permanent |
| **HTTP** | `http://example.com/pkg.wasm` | Private servers, testing |
| **HTTPS** | `https://example.com/pkg.wasm` | Secure external hosting |

---

## Creating WASM Packages

### Step 1: Write Rust Code

```rust
// upgrade_v1_2_0/src/lib.rs
use wasm_bindgen::prelude::*;
use serde_json::{Value, json};

#[wasm_bindgen]
pub fn upgrade(network_state_json: &str) -> String {
    // Parse network state
    let mut state: Value = serde_json::from_str(network_state_json)
        .expect("Invalid JSON");
    
    // Apply upgrade logic
    // Example: Add new field to all nodes
    if let Some(nodes) = state["global"]["nodes"].as_object_mut() {
        for (node_id, node_data) in nodes.iter_mut() {
            if let Some(obj) = node_data.as_object_mut() {
                obj.insert("new_feature_enabled".to_string(), json!(true));
            }
        }
    }
    
    // Update version
    state["global"]["version"] = json!("1.2.0");
    
    // Return modified state
    serde_json::to_string(&state).unwrap()
}

#[wasm_bindgen]
pub fn get_upgrade_info() -> String {
    json!({
        "version": "1.2.0",
        "description": "Add new_feature_enabled flag",
        "breaking": false
    }).to_string()
}
```

**Cargo.toml**:
```toml
[package]
name = "synapse_upgrade_v1_2_0"
version = "1.2.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

### Step 2: Compile to WASM

```bash
# Install Rust WASM target
rustup target add wasm32-unknown-unknown

# Compile with optimizations
cargo build --target wasm32-unknown-unknown --release

# Output: target/wasm32-unknown-unknown/release/synapse_upgrade_v1_2_0.wasm
```

### Step 3: Optimize WASM (Optional)

```bash
# Install wasm-opt
npm install -g wasm-opt

# Optimize binary size
wasm-opt -Oz \
  target/wasm32-unknown-unknown/release/synapse_upgrade_v1_2_0.wasm \
  -o upgrade_v1_2_0_optimized.wasm

# Result: ~50-70% size reduction
```

### Step 4: Calculate Hash

```bash
# SHA256 hash for verification
sha256sum upgrade_v1_2_0_optimized.wasm

# Output: abc123def456... upgrade_v1_2_0_optimized.wasm
```

### Step 5: Upload to IPFS

```bash
# Add to IPFS
ipfs add upgrade_v1_2_0_optimized.wasm

# Output: added Qm... upgrade_v1_2_0_optimized.wasm

# Or upload to HTTP server
scp upgrade_v1_2_0_optimized.wasm user@server:/var/www/upgrades/
```

---

## Upgrade Workflow

### 1. Create Proposal

```bash
curl -X POST http://localhost:8000/upgrades/propose \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Upgrade to v1.2.0: Add Feature Flag",
    "description": "This upgrade adds new_feature_enabled to all nodes",
    "version": "1.2.0",
    "package_url": "ipfs://Qm...",
    "package_hash": "abc123def456...",
    "package_size": 1048576
  }'
```

**Response**:
```json
{
  "proposal_id": "upgrade_20251003_120000",
  "status": "voting",
  "next_steps": [
    "Community votes on proposal",
    "If approved, validators ratify",
    "Upgrade executes automatically"
  ]
}
```

### 2. Community Votes

```bash
# Vote approval
curl -X POST http://localhost:8000/proposals/upgrade_20251003_120000/vote \
  -d '{"vote": "approval"}'

# Check voting progress
curl http://localhost:8000/proposals/upgrade_20251003_120000
```

### 3. Validator Ratification

**Automatic**: Once community approves, validators vote via Raft consensus.

### 4. Automatic Execution

**upgrade_executor_loop** (runs every 5 minutes):

```python
async def upgrade_executor_loop():
    while True:
        # Read execution log
        for command in execution_log:
            if command["operation"] == "execute_upgrade" and not command["executed"]:
                # Find proposal
                proposal = find_proposal(command["proposal_id"])
                
                # Create upgrade package
                package = UpgradePackage(
                    package_url=proposal["params"]["package_url"],
                    package_hash=proposal["params"]["package_hash"],
                    ...
                )
                
                # Execute upgrade
                success, error, result = await upgrade_manager.execute_upgrade(proposal)
                
                # Update logs
                command["executed"] = True
                command["success"] = success
                proposal["status"] = "executed" if success else "failed"
        
        await asyncio.sleep(300)  # 5 minutes
```

### 5. Execution Pipeline

```
┌────────────────┐
│ 1. Download    │ → Fetch WASM from IPFS/HTTP
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 2. Verify Hash │ → SHA256 must match proposal
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 3. Test Sandbox│ → Load in wasmtime, call test function
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 4. Backup      │ → Save current version
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 5. Execute     │ → Call upgrade() with network state
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 6. Update      │ → Save new version, log success
└────────────────┘
```

---

## API Reference

### Propose Upgrade

```http
POST /upgrades/propose
Content-Type: application/json

{
  "title": "Upgrade Title",
  "description": "Detailed description",
  "version": "1.2.0",
  "package_url": "ipfs://Qm... or https://...",
  "package_hash": "sha256:abc123...",
  "package_size": 1048576
}
```

### Test Upgrade (Dry Run)

```http
POST /upgrades/{proposal_id}/test
```

**Purpose**: Test upgrade without applying changes

**Process**:
1. Download package
2. Verify hash
3. Load in sandbox
4. Call `upgrade()` with copy of network state
5. Return result (no state modification)

### Get Upgrade Status

```http
GET /upgrades/status
```

**Response**:
```json
{
  "system_available": true,
  "current_version": "1.1.0",
  "total_upgrades": 3,
  "wasm_available": true,
  "ipfs_available": true
}
```

### Get Upgrade History

```http
GET /upgrades/history
```

**Response**:
```json
{
  "history": [
    {
      "version": "1.1.0",
      "executed_at": "2025-09-15T10:30:00Z",
      "proposal_id": "upgrade_001",
      "success": true,
      "result": "Migration completed successfully"
    }
  ]
}
```

### Rollback Upgrade

```http
POST /upgrades/{proposal_id}/rollback
```

**Purpose**: Revert to previous version

**Process**:
1. Load backup from `versions/` directory
2. Restore previous network state
3. Update current_version.txt
4. Log rollback event

---

## Security Model

### Multi-Layer Security

```
┌─────────────────────────────────────────────┐
│ Layer 1: Democratic Approval                │
│ • Community vote (reputation-weighted)      │
│ • Validator ratification (Raft consensus)   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Layer 2: Cryptographic Verification         │
│ • SHA256 hash mandatory                     │
│ • Package integrity check                   │
│ • Fails if hash mismatch                    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Layer 3: Sandbox Isolation                  │
│ • wasmtime runtime                          │
│ • No filesystem access                      │
│ • No network access                         │
│ • Memory limits enforced                    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Layer 4: Audit Trail                        │
│ • All upgrades logged                       │
│ • Immutable execution_log (CRDT)            │
│ • Version history preserved                 │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Layer 5: Rollback Safety                    │
│ • Automatic backup before upgrade           │
│ • One-command rollback                      │
│ • Previous version tested & stable          │
└─────────────────────────────────────────────┘
```

### Attack Vectors & Mitigations

| Attack | Mitigation |
|--------|------------|
| **Malicious WASM** | SHA256 verification + sandbox isolation |
| **Compromised package URL** | Hash verification fails → rejected |
| **Sybil voting** | Reputation weighting limits fake nodes |
| **Validator collusion** | Requires >50% malicious validators |
| **Code bugs** | Sandbox prevents system damage, rollback available |

---

## Monitoring & Rollback

### Monitoring Upgrade Status

```bash
# Check current version
curl http://localhost:8000/upgrades/status

# Monitor logs
tail -f logs/node.log | grep "upgrade"

# Expected output:
# [INFO] 🔄 Upgrade executor loop started
# [INFO] ✅ Upgrade executed: Add Feature Flag → v1.2.0
```

### Rollback Procedure

**Automatic Rollback** (if upgrade fails):
```python
if not success:
    logging.error("Upgrade failed, rolling back...")
    await upgrade_manager.rollback_upgrade(proposal_id)
```

**Manual Rollback**:
```bash
# Rollback specific upgrade
curl -X POST http://localhost:8000/upgrades/upgrade_20251003_120000/rollback

# Response
{
  "message": "Rollback completed",
  "restored_version": "1.1.0",
  "previous_version": "1.2.0"
}
```

### Version Directory Structure

```
data/node-abc123/upgrades/
├── current_version.txt          # Current version (e.g., "1.2.0")
├── upgrade_history.json         # All upgrades log
├── cache/                       # Downloaded WASM packages
│   ├── upgrade_001.wasm
│   └── upgrade_002.wasm
└── versions/                    # Version backups
    ├── 1.0.0/
    │   └── network_state.json
    ├── 1.1.0/
    │   └── network_state.json
    └── 1.2.0/
        └── network_state.json
```

---

## Best Practices

### For Upgrade Proposers

1. **Test Thoroughly**: Test upgrade on local dev network first
2. **Clear Description**: Explain what changes and why
3. **Small Increments**: Prefer small upgrades over massive rewrites
4. **Breaking Changes**: Clearly indicate if upgrade breaks compatibility
5. **Documentation**: Update docs alongside code upgrade

### For Voters

1. **Review Code**: Check WASM source if provided
2. **Assess Risk**: Consider impact on network stability
3. **Test Vote**: Use dry-run test endpoint before voting
4. **Communicate**: Discuss concerns in community channel
5. **Vote Timely**: Don't delay important security patches

### For Validators

1. **Stay Online**: Ensure availability for Raft consensus
2. **Technical Review**: Code upgrades require deeper analysis
3. **Performance Check**: Monitor system after ratification
4. **Rollback Readiness**: Be prepared to approve rollback if issues arise

### Development Guidelines

**WASM Module Best Practices**:
```rust
// ✅ Good: Pure function, no side effects
#[wasm_bindgen]
pub fn upgrade(state: &str) -> String {
    // Transform state and return
}

// ❌ Bad: Side effects, filesystem access
#[wasm_bindgen]
pub fn upgrade(state: &str) -> String {
    std::fs::write("file.txt", "data");  // Won't work in sandbox!
    state.to_string()
}
```

**Version Semantics**:
- **Major (1.0.0 → 2.0.0)**: Breaking changes, incompatible
- **Minor (1.1.0 → 1.2.0)**: New features, backward compatible
- **Patch (1.1.1 → 1.1.2)**: Bug fixes only

---

## Troubleshooting

### Upgrade Stuck in "Downloading"

**Problem**: Package download hanging  
**Solution**:
```bash
# Check network connectivity
curl -I ipfs://Qm...  # or https://...

# Check IPFS daemon
ipfs swarm peers

# Retry manually
curl -X POST /upgrades/{proposal_id}/test
```

### Hash Verification Failed

**Problem**: Downloaded package hash ≠ expected hash  
**Solution**:
- Package corrupted during upload
- Attacker modified package
- **DO NOT PROCEED** - Reject proposal

### WASM Execution Failed

**Problem**: Sandbox execution error  
**Solution**:
```bash
# Check wasmtime installation
wasmtime --version

# Test WASM locally
wasmtime upgrade.wasm --invoke upgrade '{"test": true}'

# Check WASM module exports
wasm-objdump -x upgrade.wasm
```

### Rollback Not Working

**Problem**: Previous version backup missing  
**Solution**:
- Check `versions/` directory exists
- Verify backup was created before upgrade
- If missing, manual state restoration required

---

## Related Documentation

- [Phase 7: Network Singularity](PHASE_7_NETWORK_SINGULARITY.md) - AI-generated upgrades
- [Governance System](GOVERNANCE_SYSTEM.md) - Proposal approval process
- [Production Deployment](PRODUCTION_DEPLOYMENT.md) - Setup guide

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Status**: ✅ Production Ready
