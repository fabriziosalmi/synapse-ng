"""
Integration Example: ImmuneSystem + EvolutionaryEngine

Questo file mostra come integrare il sistema immunitario con
l'evolutionary engine in app/main.py
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# STEP 1: Inizializzazione in app/main.py → on_startup()
# ============================================================================

async def initialize_autonomous_evolution(
    node_id: str,
    network_state: dict,
    pubsub_manager
):
    """
    Inizializza il sistema completo di auto-evoluzione:
    1. ImmuneSystem (monitoring + config remedies)
    2. EvolutionaryEngine (code generation + WASM compilation)
    3. Integrazione tra i due
    
    Questa funzione dovrebbe essere chiamata in app/main.py → on_startup()
    """
    
    # Initialize ImmuneSystem
    from app.immune_system import (
        initialize_immune_system,
        get_immune_system
    )
    
    immune_system_enabled = os.getenv("ENABLE_IMMUNE_SYSTEM", "true").lower() == "true"
    
    if immune_system_enabled:
        immune_manager = initialize_immune_system(
            node_id=node_id,
            network_state=network_state,
            pubsub_manager=pubsub_manager
        )
        await immune_manager.start()
        logger.info("[AutonomousEvolution] ImmuneSystem initialized")
    else:
        logger.warning("[AutonomousEvolution] ImmuneSystem disabled")
        return
    
    # Initialize EvolutionaryEngine (optional)
    evolutionary_enabled = os.getenv("ENABLE_EVOLUTIONARY_ENGINE", "false").lower() == "true"
    
    if evolutionary_enabled:
        from app.evolutionary_engine import (
            initialize_evolutionary_engine_manager,
            LLMProviderConfig
        )
        
        # Configure LLM provider
        llm_config = LLMProviderConfig(
            provider_name=os.getenv("LLM_PROVIDER", "ollama_local"),
            model_name=os.getenv("LLM_MODEL", "codellama:7b"),
            api_endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate"),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT", "120")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.2"))
        )
        
        evolutionary_engine = initialize_evolutionary_engine_manager(
            llm_config=llm_config,
            workspace_dir=os.getenv("EVOLUTION_WORKSPACE", "/tmp/synapse_evolution"),
            rustc_path=os.getenv("RUSTC_PATH", "rustc")
        )
        
        logger.info("[AutonomousEvolution] EvolutionaryEngine initialized")
        logger.info(f"  LLM: {llm_config.provider_name}/{llm_config.model_name}")
        
        # Link EvolutionaryEngine to ImmuneSystem
        immune_manager.evolutionary_engine = evolutionary_engine
        logger.info("[AutonomousEvolution] ✓ ImmuneSystem ↔ EvolutionaryEngine linked")
    else:
        logger.info("[AutonomousEvolution] EvolutionaryEngine disabled (config-only remedies)")
    
    logger.info("[AutonomousEvolution] === Autonomous Evolution System Ready ===")


# ============================================================================
# STEP 2: Modifica in app/immune_system.py → ImmuneSystemManager
# ============================================================================

class ImmuneSystemManagerExtended:
    """
    Estensione della classe ImmuneSystemManager per supportare
    la generazione di codice algoritmico tramite EvolutionaryEngine.
    
    Questa logica dovrebbe essere integrata in app/immune_system.py
    """
    
    def __init__(self, node_id: str, network_state: dict, pubsub_manager):
        # ... existing init code ...
        self.evolutionary_engine: Optional[object] = None  # Set by main.py
    
    
    async def propose_remedy(self, issue):
        """
        Propone un rimedio per un problema di salute.
        
        LOGICA DECISIONALE:
        - Se issue_source == "config" → Config remedy (governance config_change)
        - Se issue_source == "algorithm" → Code generation (EvolutionaryEngine)
        """
        
        # Check if issue requires algorithmic solution
        if getattr(issue, 'issue_source', 'config') == "algorithm":
            logger.info(f"[ImmuneSystem] Algorithmic issue detected: {issue.issue_type}")
            
            if self.evolutionary_engine is None:
                logger.warning("[ImmuneSystem] Evolutionary Engine not available - fallback to config remedy")
                # Fallback to config remedy
                await self._propose_config_remedy(issue)
                return
            
            # Call EvolutionaryEngine
            logger.info(f"[ImmuneSystem] Calling Evolutionary Engine for code generation...")
            generated_code = await self._generate_code_solution(issue)
            
            if generated_code and generated_code.wasm_binary:
                logger.info(f"[ImmuneSystem] ✓ Code generated successfully")
                logger.info(f"  Component: {generated_code.target_component}")
                logger.info(f"  WASM size: {len(generated_code.wasm_binary)} bytes")
                logger.info(f"  WASM hash: {generated_code.wasm_hash}")
                
                # Create code upgrade proposal
                await self._submit_code_upgrade_proposal(issue, generated_code)
            else:
                logger.error("[ImmuneSystem] ✗ Code generation failed - fallback to config remedy")
                await self._propose_config_remedy(issue)
        else:
            # Standard config remedy
            logger.info(f"[ImmuneSystem] Config issue detected: {issue.issue_type}")
            await self._propose_config_remedy(issue)
    
    
    async def _generate_code_solution(self, issue):
        """
        Chiama l'EvolutionaryEngine per generare codice ottimizzato.
        
        Converte HealthIssue → Inefficiency e invoca generate_optimized_code()
        """
        from app.evolutionary_engine import Inefficiency, InefficencyType
        
        # Map issue_type to InefficencyType
        inefficiency_type_map = {
            "high_latency": InefficencyType.PERFORMANCE,
            "low_connectivity": InefficencyType.NETWORK_TOPOLOGY,
            "consensus_slow": InefficencyType.CONSENSUS,
            "auction_slow": InefficencyType.AUCTION,
            "memory_pressure": InefficencyType.RESOURCE_USAGE,
        }
        
        inefficiency_type = inefficiency_type_map.get(
            issue.issue_type,
            InefficencyType.PERFORMANCE
        )
        
        # Convert HealthIssue to Inefficiency
        inefficiency = Inefficiency(
            type=inefficiency_type,
            description=issue.description,
            severity=self._severity_to_float(issue.severity),
            current_metric=issue.current_value,
            target_metric=issue.target_value,
            affected_component=issue.affected_component,
            suggested_improvement=issue.recommended_action,
            timestamp=issue.detected_at
        )
        
        # Generate optimized code
        try:
            generated_code = await self.evolutionary_engine.generate_optimized_code(
                issue=inefficiency,
                additional_context={
                    "node_id": self.node_id,
                    "active_peers": len(self.network_state.get("global", {}).get("nodes", {})),
                    "network_health": "degraded" if issue.severity in ["high", "critical"] else "stable"
                }
            )
            
            return generated_code
            
        except Exception as e:
            logger.error(f"[ImmuneSystem] Error generating code: {e}", exc_info=True)
            return None
    
    
    async def _propose_config_remedy(self, issue):
        """
        Standard config remedy (existing logic).
        Questo è il metodo esistente _generate_remedy() + _submit_governance_proposal()
        """
        remedy = self._generate_remedy(issue)
        if remedy:
            await self._submit_governance_proposal(remedy)
    
    
    async def _submit_code_upgrade_proposal(self, issue, generated_code):
        """
        Sottomette una proposta di governance per deploy di nuovo codice WASM.
        
        Tipo: "code_upgrade"
        Contiene: source code, WASM binary (base64), hash, compilation log
        """
        import uuid
        import base64
        from datetime import datetime, timezone, timedelta
        
        proposal_id = str(uuid.uuid4())
        
        # Encode WASM binary as base64
        wasm_base64 = base64.b64encode(generated_code.wasm_binary).decode('utf-8')
        
        # Construct proposal
        proposal = {
            "id": proposal_id,
            "title": f"[EVOLUTIONARY] Code Upgrade: {issue.affected_component}",
            "description": f"""**Automated Code Generation**

The Evolutionary Engine has generated optimized code to resolve a chronic algorithmic issue.

**Issue Type**: {issue.issue_type}
**Severity**: {issue.severity}
**Affected Component**: {issue.affected_component}
**Current Performance**: {issue.current_value:.2f}
**Target Performance**: {issue.target_value:.2f}

**Problem Description**:
{issue.description}

**Generated Solution**:
- Language: {generated_code.language.value}
- Target Component: {generated_code.target_component}
- Estimated Improvement: {generated_code.estimated_improvement:.1f}%

**WASM Binary Details**:
- Size: {len(generated_code.wasm_binary)} bytes
- SHA256: {generated_code.wasm_hash}
- Compilation: {"✓ Success" if generated_code.wasm_binary else "✗ Failed"}

**Source Code** (Rust):
```rust
{generated_code.source_code}
```

**Compilation Log**:
```
{generated_code.compilation_log}
```

**Security Notes**:
- Code generated by LLM with safety constraints
- Compiled for wasm32-unknown-unknown (sandboxed)
- No filesystem, network, or threading operations
- Hash verification required before deployment

**Detected At**: {issue.detected_at}
**Proposed By**: Node {self.node_id} (Evolutionary Engine)
""",
            "proposal_type": "code_upgrade",
            "params": {
                "target_component": generated_code.target_component,
                "wasm_binary_base64": wasm_base64,
                "wasm_hash": generated_code.wasm_hash,
                "source_code_rust": generated_code.source_code,
                "estimated_improvement": generated_code.estimated_improvement,
                "language": generated_code.language.value
            },
            "tags": ["evolutionary_engine", "code_upgrade", "automated", issue.issue_type],
            "author": self.node_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "votes": {},
            "status": "open",
            "closes_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
            "vote_count": {"yes": 0, "no": 0, "abstain": 0},
            "result": None
        }
        
        # Add to network state
        if "global" not in self.network_state:
            self.network_state["global"] = {}
        if "proposals" not in self.network_state["global"]:
            self.network_state["global"]["proposals"] = {}
        
        self.network_state["global"]["proposals"][proposal_id] = proposal
        
        # Broadcast proposal
        if self.pubsub_manager:
            message_payload = {
                "action": "code_upgrade_proposal_created",
                "proposal": proposal
            }
            await self.pubsub_manager.publish("global", message_payload)
        
        logger.info(f"[ImmuneSystem] Code upgrade proposal {proposal_id} submitted")
        return proposal_id
    
    
    def _severity_to_float(self, severity: str) -> float:
        """Converte severità string → float (0.0-1.0)"""
        severity_map = {
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "critical": 1.0
        }
        return severity_map.get(severity.lower(), 0.5)


# ============================================================================
# STEP 3: Environment Variables (docker-compose.yml)
# ============================================================================

DOCKER_COMPOSE_EXAMPLE = """
services:
  node-1:
    environment:
      # ImmuneSystem
      - ENABLE_IMMUNE_SYSTEM=true
      
      # EvolutionaryEngine
      - ENABLE_EVOLUTIONARY_ENGINE=true
      - LLM_PROVIDER=ollama_local
      - LLM_MODEL=codellama:7b
      - LLM_ENDPOINT=http://host.docker.internal:11434/api/generate
      - LLM_TIMEOUT=120
      - LLM_TEMPERATURE=0.2
      - EVOLUTION_WORKSPACE=/app/data/evolution
      - RUSTC_PATH=rustc
"""


# ============================================================================
# STEP 4: Example Usage - Trigger Algorithmic Issue
# ============================================================================

async def example_trigger_algorithmic_issue():
    """
    Esempio di come il sistema immunitario può rilevare un issue
    algoritmico e triggerare l'EvolutionaryEngine.
    
    Questo sarebbe chiamato internamente da ImmuneSystemManager
    quando rileva performance degradate che non possono essere risolte
    con semplici config changes.
    """
    from app.immune_system import get_immune_system
    from app.immune_system import HealthIssue
    from datetime import datetime, timezone
    
    immune_system = get_immune_system()
    
    if not immune_system:
        print("ImmuneSystem not initialized")
        return
    
    # Create an algorithmic issue
    algorithmic_issue = HealthIssue(
        issue_type="consensus_slow",
        severity="high",
        current_value=8.5,  # 8.5 seconds per consensus round
        target_value=3.0,   # Target: <3 seconds
        recommended_action="optimize_raft_algorithm",
        description="Raft consensus consistently exceeds 5 seconds per round, causing network delays",
        detected_at=datetime.now(timezone.utc).isoformat(),
        issue_source="algorithm",  # ← KEY: Triggers EvolutionaryEngine
        affected_component="raft_consensus"
    )
    
    # Propose remedy (will trigger code generation)
    await immune_system.propose_remedy(algorithmic_issue)
    
    print("✓ Algorithmic issue submitted to ImmuneSystem")
    print("  → EvolutionaryEngine will generate optimized Raft code")
    print("  → Compiled WASM will be proposed via governance")


# ============================================================================
# STEP 5: Monitor Generated Proposals
# ============================================================================

def check_code_upgrade_proposals(network_state: dict):
    """
    Cerca proposte di code upgrade nel network state.
    """
    proposals = network_state.get("global", {}).get("proposals", {})
    
    code_upgrades = [
        p for p in proposals.values()
        if p.get("proposal_type") == "code_upgrade"
    ]
    
    print(f"\n=== Code Upgrade Proposals ({len(code_upgrades)}) ===")
    
    for proposal in code_upgrades:
        print(f"\nProposal: {proposal['title']}")
        print(f"  ID: {proposal['id']}")
        print(f"  Status: {proposal['status']}")
        print(f"  Component: {proposal['params']['target_component']}")
        print(f"  WASM Hash: {proposal['params']['wasm_hash'][:16]}...")
        print(f"  Est. Improvement: {proposal['params']['estimated_improvement']}%")
        print(f"  Votes: {proposal['vote_count']}")


# ============================================================================
# MAIN INTEGRATION SUMMARY
# ============================================================================

INTEGRATION_SUMMARY = """
=== Integration Summary: ImmuneSystem + EvolutionaryEngine ===

1. Initialization (app/main.py):
   - Call initialize_autonomous_evolution() in on_startup()
   - Sets up both ImmuneSystem and EvolutionaryEngine
   - Links them together (immune_system.evolutionary_engine = engine)

2. Decision Logic (app/immune_system.py):
   - HealthIssue.issue_source == "config" → Config remedy
   - HealthIssue.issue_source == "algorithm" → Code generation
   
3. Code Generation Flow:
   a) ImmuneSystem detects chronic algorithmic issue
   b) Calls EvolutionaryEngine.generate_optimized_code()
   c) LLM generates Rust code
   d) Rust compiled to WASM
   e) WASM proposal submitted to governance
   
4. Governance Flow:
   a) Community votes on code upgrade proposal
   b) If approved → Self-upgrade manager deploys WASM
   c) New code executes in sandboxed WASM runtime
   
5. Monitoring:
   - Check logs for "[EvolutionaryEngine] ✓ Compilation successful"
   - Query /api/evolutionary-engine/stats for metrics
   - Review proposals with type="code_upgrade"

=== Environment Variables ===

Required:
- ENABLE_IMMUNE_SYSTEM=true
- ENABLE_EVOLUTIONARY_ENGINE=true

LLM Configuration:
- LLM_PROVIDER=ollama_local
- LLM_MODEL=codellama:7b
- LLM_ENDPOINT=http://localhost:11434/api/generate

Optional:
- LLM_TIMEOUT=120
- LLM_TEMPERATURE=0.2
- EVOLUTION_WORKSPACE=/tmp/synapse_evolution
- RUSTC_PATH=rustc

=== Testing Checklist ===

[ ] Ollama running and codellama:7b model downloaded
[ ] Rust toolchain installed (rustc --version)
[ ] wasm32-unknown-unknown target installed
[ ] ImmuneSystem initializes successfully
[ ] EvolutionaryEngine initializes successfully
[ ] Link between systems established
[ ] Test issue with issue_source="algorithm" triggers code gen
[ ] LLM generates valid Rust code
[ ] Rust code compiles to WASM
[ ] Proposal created with type="code_upgrade"
[ ] Voting and approval workflow tested

=== Success Criteria ===

✓ ImmuneSystem detects algorithmic inefficiency
✓ EvolutionaryEngine generates optimized code
✓ Code compiles to WASM successfully
✓ WASM hash calculated and verified
✓ Governance proposal created and broadcasted
✓ Community can vote on code upgrade
✓ Approved code deployed to network
✓ Performance metrics improve post-deployment

Status: INTEGRATION READY 🚀
"""

if __name__ == "__main__":
    print(INTEGRATION_SUMMARY)
