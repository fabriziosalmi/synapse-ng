# Governance

Synapse-NG features a sophisticated governance system that allows the network to make decisions, manage resources, and evolve over time. The system is designed to be democratic, meritocratic, and secure.

## Two-Tier Governance

The governance system has two tiers:

1.  **Community CRDT Voting:** This is the primary voting mechanism, where any node can propose changes and vote on them. The voting power of each node is weighted by its reputation.
2.  **Validator Raft Ratification:** For critical network operations, a smaller set of validator nodes must ratify the proposal using the Raft consensus algorithm. This provides an additional layer of security and stability.

## Reputation v2

Reputation in Synapse-NG is not just a single score. The Reputation v2 system is a dynamic and specialized system that tracks expertise in different domains.

*   **Tag-Based Expertise:** Reputation is associated with specific tags (e.g., `{"python": 50, "security": 70}`).
*   **Contextual Voting:** A node's voting power on a proposal is amplified by its expertise in the proposal's tags.
*   **Time Decay:** Reputation scores slowly decay over time, which encourages continuous contribution to the network.

## Zero-Knowledge Voting

For sensitive decisions, Synapse-NG supports zero-knowledge proof (ZKP) anonymous voting. This allows nodes to vote on proposals without revealing their identity, while still ensuring the integrity of the vote.

## Executable Proposals

Proposals in Synapse-NG can be executable. This means that if a proposal is approved, the network will automatically execute a command to modify its state. This is a powerful feature that allows for autonomous network evolution.