# Security Considerations

This document outlines security considerations, threat models, and mitigation strategies for Synapse-NG.

## 🔒 Current Security Measures

### 1. Cryptographic Identity (Ed25519)

Each node has a unique cryptographic identity:

```python
# app/identity.py
- Private key: 32 bytes, never shared
- Public key: Used as node_id, shared with all peers
- Signing: All proposals and votes are signed
```

**Guarantees:**
- Unforgeable identity
- Message authenticity (signature verification)
- Non-repudiation (signed actions)

**Limitations:**
- No encryption at application layer (only WebRTC channel encryption)
- Public keys are visible to all nodes

### 2. WebRTC Transport Security

WebRTC provides encrypted channels by default:

- **DTLS**: Encryption for DataChannel
- **SRTP**: Encryption for media streams
- **ICE**: NAT traversal with STUN/TURN

**Guarantees:**
- Encrypted peer-to-peer communication
- Protection against eavesdropping on the network layer

**Limitations:**
- Encryption is point-to-point (each hop in gossip)
- No end-to-end encryption for multi-hop gossip
- Relay servers (TURN) can see metadata (not payload)

### 3. Schema Validation

All messages are validated against predefined schemas (see `app/schemas.py`):

```python
# Example: Task creation
TaskCreate = {
    "title": {"type": "string", "minlength": 1, "maxlength": 200, "required": True},
    "description": {"type": "string", "maxlength": 2000, "nullable": True},
    # ...
}
```

**Guarantees:**
- Protection against malformed data
- Type safety (string, integer, enum validation)
- Bounds checking (min/max length)

**Limitations:**
- Does not prevent semantic attacks (e.g., spam with valid tasks)
- No rate limiting at schema level

## ⚠️ Known Limitations and Threat Model

### 1. Sybil Attacks

**Threat:** A malicious actor creates many fake nodes to:
- Accumulate reputation artificially
- Gain disproportionate voting power
- Spam the network with tasks/proposals

**Current Mitigation:**
- **Reputation-based voting**: Weight = 1 + log₂(reputation + 1)
  - New nodes have minimal influence (weight ≈ 1.0)
  - High-reputation nodes have more influence
  - Logarithmic scaling limits the benefit of creating many low-reputation nodes

**Example:**
```
Creating 100 nodes with reputation 0:
- Total weight: 100 × 1.0 = 100

vs. 1 node with reputation 1023 (100 completed tasks):
- Weight: 1 + log₂(1024) = 11.0

Sybil attack is NOT profitable in reputation-weighted voting!
```

**Limitations:**
- Still vulnerable if attacker completes many tasks on fake nodes
- No Proof-of-Work or stake requirement for joining

**Future Enhancements:**
- **Proof-of-Work for joining**: Require computational work to create a node
- **Stake requirement**: Require locking Synapse Points to join
- **Social graph analysis**: Detect clusters of fake nodes based on interaction patterns

### 2. Eclipse Attacks

**Threat:** An attacker surrounds a victim node with malicious nodes, isolating it from the honest network.

**Current Mitigation:**
- **Multiple bootstrap nodes**: Nodes can specify multiple `BOOTSTRAP_NODES`
- **Peer diversity**: WebRTC mesh topology connects to multiple peers
- **Gossip redundancy**: Messages are forwarded to all subscribed peers

**Limitations:**
- No explicit peer diversity enforcement
- No detection of eclipse attacks
- No reputation-based peer selection

**Future Enhancements:**
- **Peer scoring**: Prefer high-reputation peers for connections
- **Connection diversity**: Enforce connections to peers from different network segments
- **Heartbeat monitoring**: Detect when a node stops receiving messages from the broader network

### 3. CRDT Conflict Exploitation (Last-Write-Wins)

**Threat:** An attacker with a synchronized clock can always "win" conflicts by setting a future timestamp.

**Current Behavior:**
```python
# app/main.py:196-201
if incoming_task["updated_at"] > local_task["updated_at"]:
    local_state["tasks"][task_id] = incoming_task
```

**Attack Scenario:**
1. Node A creates task X at `t=1000`
2. Node B modifies task X at `t=2000`
3. Malicious node C modifies task X with timestamp `t=99999` (far future)
4. All nodes accept C's version (highest timestamp)

**Limitations:**
- No timestamp validation
- No bounds on "reasonable" timestamps
- No vector clocks or causal ordering

**Future Enhancements:**
- **Timestamp bounds**: Reject updates with timestamps > `now + threshold` (e.g., 1 hour)
- **Lamport clocks**: Use logical clocks instead of wall-clock timestamps
- **Vector clocks**: Track causality instead of relying on timestamps
- **Hybrid Logical Clocks (HLC)**: Combine wall-clock and logical clocks

### 4. Spam and Denial of Service

**Threat:** A node floods the network with valid but useless tasks/proposals/messages.

**Current Mitigation:**
- **Channel subscriptions**: Nodes only receive messages for subscribed channels
- **Message deduplication**: SynapseSub caches seen messages (`msg_id`)

**Limitations:**
- No rate limiting per node
- No cost for creating tasks/proposals (future: Synapse Points economy)
- No blacklisting or banning mechanism

**Future Enhancements:**
- **SP cost for actions**: Require Synapse Points to create tasks/proposals
- **Reputation penalties**: Reduce reputation for rejected proposals or abandoned tasks
- **Rate limiting**: Limit messages per node per time window
- **Blacklist mechanism**: Allow nodes to ignore malicious peers

### 5. Code Injection (Self-Upgrade System)

**Threat:** A malicious proposal introduces backdoored code via the self-upgrade system.

**Current Mitigation (Phase 6: Self-Upgrade):**
- **WASM sandboxing**: Code runs in isolated WebAssembly environment
- **Proposal voting**: Code changes require governance approval
- **Validator ratification**: High-reputation validators must approve

**Limitations:**
- WASM sandbox can be escaped (see CVEs)
- No formal verification of proposed code
- No rollback mechanism if malicious code is executed

**Future Enhancements:**
- **Code review by AI**: Automated analysis for suspicious patterns
- **Gradual rollout**: Deploy to subset of nodes first
- **Kill switch**: Emergency mechanism to revert malicious upgrades
- **Formal verification**: Prove properties of critical code paths

### 6. Privacy and Metadata Leakage

**Threat:** All state is public, allowing passive observers to analyze:
- Who creates tasks
- Who votes on proposals
- Reputation levels
- Network topology

**Current Behavior:**
- All tasks, proposals, and votes are public
- Node IDs (public keys) are visible
- No anonymous voting (except ZKP voting, roadmap item)

**Limitations:**
- No privacy for node actions
- Reputation and voting patterns are public
- Network graph is discoverable

**Future Enhancements:**
- **Zero-Knowledge Proofs (ZKP)**: Anonymous voting without revealing voter identity
- **Homomorphic encryption**: Compute on encrypted data (e.g., vote tallying)
- **Mixnets**: Anonymize message routing
- **Differential privacy**: Add noise to reputation/statistics

## 🛡️ Recommended Security Practices

### For Node Operators

1. **Keep private keys secure**
   - Store in encrypted storage
   - Never commit to version control
   - Use hardware security modules (HSM) if possible

2. **Use multiple bootstrap nodes**
   - Reduces risk of eclipse attacks
   - Improves network resilience

3. **Monitor reputation**
   - Watch for unexpected reputation changes
   - Report suspicious nodes to the community

4. **Update regularly**
   - Stay current with security patches
   - Participate in governance for security proposals

### For Developers

1. **Validate all inputs**
   - Use schema validation for all data
   - Reject invalid data at API boundaries
   - Sanitize user-provided strings

2. **Assume adversarial network**
   - Never trust incoming messages
   - Verify signatures on critical actions
   - Implement rate limiting

3. **Test security scenarios**
   - Add tests for Sybil resistance
   - Test with malicious nodes
   - Fuzz test message parsing

4. **Document threat models**
   - Update this document when adding features
   - Consider attack vectors for new code
   - Perform security reviews for major changes

## 🔮 Roadmap: Security Enhancements

### Short-term (v0.2)
- [ ] **Timestamp validation**: Reject future timestamps in CRDT
- [ ] **Rate limiting**: Limit messages per node per minute
- [ ] **SP cost for tasks/proposals**: Economic deterrent for spam

### Medium-term (v0.5)
- [ ] **End-to-End Encryption (E2E)**: Encrypt payloads beyond WebRTC
- [ ] **Peer scoring**: Reputation-based peer selection
- [ ] **Blacklist mechanism**: Ignore malicious nodes

### Long-term (v1.0)
- [ ] **Zero-Knowledge Proofs (ZKP)**: Anonymous voting
- [ ] **Proof-of-Work for joining**: Sybil resistance
- [ ] **Formal verification**: Critical code paths
- [ ] **Security audit**: External third-party audit

## 📞 Reporting Security Vulnerabilities

**Please do not open public GitHub issues for security vulnerabilities.**

Instead:
1. Email security details to: [YOUR_EMAIL] (or create a private security advisory)
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## 🙏 Acknowledgments

Security is a continuous process. We welcome:
- Security audits
- Responsible disclosure of vulnerabilities
- Contributions to improve security
- Threat model analysis

Thank you for helping keep Synapse-NG secure! 🔒✨
