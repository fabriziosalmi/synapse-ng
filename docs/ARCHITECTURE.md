# Architecture

Synapse-NG is built on a three-layer architecture that separates the concerns of network transport, message propagation, and application logic. This modular design allows for flexibility and scalability.

## Three-Layer Communication Stack

```
┌─────────────────────────────────────────────────┐
│            APPLICATION LAYER                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Channels │  │  Tasks   │  │Governance│     │
│  │ Treasury │  │ Auctions │  │ Rep. v2  │     │
│  │ Common   │  │  Teams   │  │ Commands │     │
│  │  Tools   │  │          │  │          │     │
│  └──────────┘  └──────────┘  └──────────┘     │
├─────────────────────────────────────────────────┤
│          SYNAPSESUB PROTOCOL                    │
│  ┌──────────────────────────────────────┐      │
│  │  Topic-Based PubSub + Routing        │      │
│  │  ANNOUNCE | MESSAGE | I_HAVE | ...   │      │
│  └──────────────────────────────────────┘      │
├─────────────────────────────────────────────────┤
│         WEBRTC TRANSPORT LAYER                  │
│  ┌──────────────────────────────────────┐      │
│  │   P2P Connections + Data Channels     │      │
│  │   Encrypted (DTLS/SRTP)               │      │
│  └──────────────────────────────────────┘      │
└─────────────────────────────────────────────────┘
```

*   **Application Layer:** This is where the core logic of Synapse-NG resides. It includes modules for managing channels, tasks, governance, and the economy.
*   **SynapseSub Protocol:** This is a custom topic-based pub/sub protocol that handles message routing and propagation throughout the network.
*   **WebRTC Transport Layer:** This layer is responsible for establishing and maintaining P2P connections between nodes. It uses WebRTC data channels for secure and efficient communication.

## Peer-to-Peer Networking

Synapse-NG uses a peer-to-peer networking model, which means that there is no central server. Nodes communicate directly with each other to form a resilient and decentralized network. The network supports two modes of operation:

*   **Rendezvous Mode:** In this mode, a central rendezvous server is used for peer discovery and signaling. This is the simplest way to set up a network, but it introduces a single point of failure.
*   **Pure P2P Mode:** In this mode, nodes bootstrap from a list of existing peers. This is a fully decentralized and resilient mode of operation.

## CRDT State Synchronization

Synapse-NG uses Conflict-free Replicated Data Types (CRDTs) to ensure that all nodes in the network have a consistent view of the system's state. Specifically, it uses a Last-Write-Wins (LWW) CRDT, where the entry with the most recent timestamp is considered the correct one. This allows for eventual consistency without the need for a central authority.