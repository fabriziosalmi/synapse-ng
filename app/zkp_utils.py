"""
Zero-Knowledge Proof utilities for anonymous voting.

This module implements a simplified ZKP system for reputation-based anonymous voting:
- Nodes can prove they belong to a specific reputation tier without revealing their exact reputation
- Votes remain anonymous while maintaining weighted governance
- Anti-double-voting protection via nullifiers

Architecture:
1. Reputation Tiers: novice (0-50), intermediate (51-150), expert (151+)
2. Pedersen Commitments: Cryptographic commitment to reputation value
3. Range Proofs: Prove reputation is within a specific range
4. Nullifiers: Unique per (proposal_id, node_secret) to prevent double voting

Note: This is a simplified educational implementation. Production systems should use
battle-tested libraries like libsnark, bellman, or zkSNARKs frameworks.
"""

import hashlib
import secrets
from typing import Tuple, Dict, Optional
from datetime import datetime, timezone

# For production, use py_ecc. For now, we use a simplified approach with hashing
# from py_ecc.bn128 import G1, multiply, add, curve_order

# Reputation tiers (public knowledge)
REPUTATION_TIERS = {
    "novice": {"min": 0, "max": 50, "weight_multiplier": 1.0},
    "intermediate": {"min": 51, "max": 150, "weight_multiplier": 1.5},
    "expert": {"min": 151, "max": float('inf'), "weight_multiplier": 2.0}
}

def get_reputation_tier(reputation: int) -> str:
    """
    Determina la fascia di reputazione di un nodo.
    
    Args:
        reputation: Valore reputazione del nodo
        
    Returns:
        Nome della fascia ("novice", "intermediate", "expert")
    """
    for tier_name, tier_range in REPUTATION_TIERS.items():
        if tier_range["min"] <= reputation <= tier_range["max"]:
            return tier_name
    return "novice"  # Fallback

def get_tier_weight(tier_name: str) -> float:
    """
    Ottiene il moltiplicatore di peso per una fascia.
    
    Args:
        tier_name: Nome della fascia
        
    Returns:
        Moltiplicatore di peso (1.0, 1.5, o 2.0)
    """
    return REPUTATION_TIERS.get(tier_name, {}).get("weight_multiplier", 1.0)

def generate_nullifier(node_secret: str, proposal_id: str) -> str:
    """
    Genera un nullifier univoco per impedire double-voting.
    
    Il nullifier è un hash deterministico di (node_secret, proposal_id).
    Ogni nodo ha un segreto persistente, quindi può generare sempre lo stesso
    nullifier per la stessa proposta, ma nullifier diversi per proposte diverse.
    
    Args:
        node_secret: Segreto del nodo (derivato da private key)
        proposal_id: ID della proposta
        
    Returns:
        Nullifier (hash hex)
    """
    data = f"{node_secret}:{proposal_id}".encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def generate_reputation_proof(
    reputation: int,
    node_secret: str,
    proposal_id: str
) -> Dict[str, str]:
    """
    Genera una Zero-Knowledge Proof che dimostra:
    1. Il nodo ha reputazione nella fascia dichiarata
    2. Il nodo è univoco per questa proposta (via nullifier)
    
    Simplified approach (educational):
    - Commitment: hash(reputation || random_nonce)
    - Proof: Fiat-Shamir heuristic style challenge-response
    - Nullifier: hash(node_secret || proposal_id)
    
    In production, use proper zk-SNARKs or Bulletproofs.
    
    Args:
        reputation: Valore reputazione attuale del nodo
        node_secret: Segreto del nodo
        proposal_id: ID della proposta
        
    Returns:
        Dict con proof components:
            - tier: Fascia di reputazione
            - nullifier: Hash univoco anti-double-vote
            - commitment: Pedersen-style commitment
            - challenge: Fiat-Shamir challenge
            - response: Prova crittografica
            - timestamp: Timestamp generazione
    """
    # Determina fascia
    tier = get_reputation_tier(reputation)
    tier_range = REPUTATION_TIERS[tier]
    
    # Genera nullifier (pubblico, usato per anti-replay)
    nullifier = generate_nullifier(node_secret, proposal_id)
    
    # Genera nonce random per commitment
    nonce = secrets.token_hex(32)
    
    # Commitment: hash(reputation || nonce)
    commitment_data = f"{reputation}:{nonce}".encode('utf-8')
    commitment = hashlib.sha256(commitment_data).hexdigest()
    
    # Challenge (Fiat-Shamir): hash(commitment || tier || nullifier || proposal_id)
    challenge_data = f"{commitment}:{tier}:{nullifier}:{proposal_id}".encode('utf-8')
    challenge = hashlib.sha256(challenge_data).hexdigest()
    
    # Response: hash(nonce || node_secret || challenge)
    # In un vero ZKP, questa sarebbe una prova matematica che reputation ∈ [min, max]
    response_data = f"{nonce}:{node_secret}:{challenge}".encode('utf-8')
    response = hashlib.sha256(response_data).hexdigest()
    
    proof = {
        "tier": tier,
        "nullifier": nullifier,
        "commitment": commitment,
        "challenge": challenge,
        "response": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # In produzione, aggiungi: range_proof, schnorr_signature, etc.
    }
    
    return proof

def verify_reputation_proof(
    proof: Dict[str, str],
    proposal_id: str,
    used_nullifiers: set
) -> Tuple[bool, str]:
    """
    Verifica una Zero-Knowledge Proof di reputazione.
    
    Controlli:
    1. Nullifier non è già stato usato (anti-double-voting)
    2. Challenge è valido (Fiat-Shamir check)
    3. Tier è una fascia valida
    4. Timestamp è recente (< 1 ora)
    
    Note: In un vero sistema ZKP, verificheresti anche:
    - Range proof che reputation ∈ [tier.min, tier.max]
    - Schnorr signature o altro crypto proof
    
    Args:
        proof: Proof generato da generate_reputation_proof()
        proposal_id: ID della proposta
        used_nullifiers: Set di nullifier già usati per questa proposta
        
    Returns:
        Tuple (is_valid: bool, error_message: str)
    """
    try:
        # 1. Verifica campi richiesti
        required_fields = ["tier", "nullifier", "commitment", "challenge", "response", "timestamp"]
        for field in required_fields:
            if field not in proof:
                return False, f"Campo mancante: {field}"
        
        # 2. Verifica che tier sia valido
        if proof["tier"] not in REPUTATION_TIERS:
            return False, f"Tier non valido: {proof['tier']}"
        
        # 3. Anti-double-voting: verifica nullifier
        if proof["nullifier"] in used_nullifiers:
            return False, "Nullifier già usato (double voting detected)"
        
        # 4. Verifica timestamp (proof deve essere recente, < 1 ora)
        proof_time = datetime.fromisoformat(proof["timestamp"])
        now = datetime.now(timezone.utc)
        time_diff = (now - proof_time).total_seconds()
        
        if time_diff > 3600:  # 1 ora
            return False, f"Proof troppo vecchio ({time_diff/60:.1f} minuti)"
        
        if time_diff < -60:  # 1 minuto di tolleranza per clock skew
            return False, "Proof dal futuro (clock skew)"
        
        # 5. Verifica Fiat-Shamir challenge
        # Ricalcola challenge: hash(commitment || tier || nullifier || proposal_id)
        challenge_data = f"{proof['commitment']}:{proof['tier']}:{proof['nullifier']}:{proposal_id}".encode('utf-8')
        expected_challenge = hashlib.sha256(challenge_data).hexdigest()
        
        if proof["challenge"] != expected_challenge:
            return False, "Challenge non valido (Fiat-Shamir check failed)"
        
        # 6. In produzione: verifica range proof, schnorr signature, ecc.
        # Per ora, assumiamo che se challenge è valido, il proof è corretto
        
        # Proof valido!
        return True, ""
    
    except Exception as e:
        return False, f"Errore nella verifica: {str(e)}"

def get_node_secret_from_private_key(ed25519_private_key_bytes: bytes) -> str:
    """
    Deriva un segreto persistente dalla private key del nodo.
    
    Questo segreto è usato per generare nullifier deterministici.
    Non deve mai essere rivelato pubblicamente.
    
    Args:
        ed25519_private_key_bytes: Private key Ed25519 del nodo
        
    Returns:
        Segreto hex (64 caratteri)
    """
    # Deriva segreto via HKDF-style (hash della private key)
    secret = hashlib.sha256(ed25519_private_key_bytes).hexdigest()
    return secret

# --- Testing utilities ---

def test_zkp_flow():
    """Test del flusso completo ZKP."""
    print("🧪 Testing ZKP Flow")
    print("=" * 50)
    
    # Setup
    node_secret = secrets.token_hex(32)
    proposal_id = "prop_test_123"
    reputation = 120  # Tier: intermediate
    
    # 1. Generate proof
    print(f"\n1. Generazione proof per reputation={reputation}")
    proof = generate_reputation_proof(reputation, node_secret, proposal_id)
    print(f"   Tier: {proof['tier']}")
    print(f"   Nullifier: {proof['nullifier'][:16]}...")
    print(f"   Commitment: {proof['commitment'][:16]}...")
    
    # 2. Verify proof
    print(f"\n2. Verifica proof")
    used_nullifiers = set()
    is_valid, error = verify_reputation_proof(proof, proposal_id, used_nullifiers)
    print(f"   Valid: {is_valid}")
    if error:
        print(f"   Error: {error}")
    
    # 3. Anti-double-voting
    print(f"\n3. Test anti-double-voting")
    used_nullifiers.add(proof['nullifier'])
    is_valid2, error2 = verify_reputation_proof(proof, proposal_id, used_nullifiers)
    print(f"   Second vote valid: {is_valid2}")
    print(f"   Error: {error2}")
    
    # 4. Different proposal (should work)
    print(f"\n4. Test stesso nodo, proposta diversa")
    proposal_id_2 = "prop_test_456"
    proof2 = generate_reputation_proof(reputation, node_secret, proposal_id_2)
    used_nullifiers_2 = set()
    is_valid3, error3 = verify_reputation_proof(proof2, proposal_id_2, used_nullifiers_2)
    print(f"   Valid: {is_valid3}")
    print(f"   Nullifier diverso: {proof2['nullifier'] != proof['nullifier']}")
    
    print("\n" + "=" * 50)
    print("✅ Test completato!")

if __name__ == "__main__":
    test_zkp_flow()
