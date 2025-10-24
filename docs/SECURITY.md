# Security

Synapse-NG is designed with security in mind. The project incorporates a variety of security features to protect the network from attacks and ensure the privacy of its users.

## Cryptographic Identity

Each node in the network has a unique cryptographic identity, which is based on an Ed25519 key pair. All messages are signed and verified to ensure their authenticity and integrity.

## Encrypted Communication

All communication between nodes is encrypted using the DTLS/SRTP protocols, which are part of the WebRTC standard. This ensures that all data transmitted over the network is confidential and secure.

## Common Tools Credential Encryption

Credentials for common tools are encrypted using AES-GCM with an HKDF-derived key. This ensures that sensitive information, such as API keys, is stored securely.

## WASM Sandbox

The self-upgrade system uses a WASM sandbox to safely execute new code. This prevents malicious or buggy code from affecting the stability of the network.

## Sybil Resistance

The reputation system provides a degree of resistance to Sybil attacks. Since reputation is earned through contributions to the network, it is difficult for an attacker to create a large number of fake identities with high reputation.

## Threat Model

A detailed threat model and mitigation strategies are available in the full security guide, which will be available soon.