"""
Integration Code for app/main.py

Add this code to the on_startup() function in app/main.py
to link ImmuneSystem with EvolutionaryEngine.

This enables the complete autonomous evolution cycle:
Config remedies → Persistent issues → Code generation → WASM deployment
"""

# ============================================================================
# ADD TO app/main.py → on_startup() function
# ============================================================================

async def on_startup():
    """Application startup - Initialize all systems"""
    
    # ... existing initialization code ...
    
    # ========================================================================
    # IMMUNE SYSTEM INITIALIZATION
    # ========================================================================
    
    immune_system_enabled = os.getenv("ENABLE_IMMUNE_SYSTEM", "true").lower() == "true"
    
    if immune_system_enabled:
        from app.immune_system import (
            initialize_immune_system,
            get_immune_system
        )
        
        immune_manager = initialize_immune_system(
            node_id=NODE_ID,
            network_state=network_state,
            pubsub_manager=pubsub_manager
        )
        await immune_manager.start()
        logger.info("[Main] ✓ ImmuneSystem initialized and started")
    else:
        logger.warning("[Main] ImmuneSystem disabled")
        return
    
    # ========================================================================
    # EVOLUTIONARY ENGINE INITIALIZATION
    # ========================================================================
    
    evolutionary_enabled = os.getenv("ENABLE_EVOLUTIONARY_ENGINE", "false").lower() == "true"
    
    if evolutionary_enabled:
        from app.evolutionary_engine import (
            initialize_evolutionary_engine_manager,
            get_evolutionary_engine_manager,
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
        
        logger.info(f"[Main] Initializing EvolutionaryEngine...")
        logger.info(f"  LLM Provider: {llm_config.provider_name}")
        logger.info(f"  LLM Model: {llm_config.model_name}")
        logger.info(f"  LLM Endpoint: {llm_config.api_endpoint}")
        
        evolutionary_engine = initialize_evolutionary_engine_manager(
            llm_config=llm_config,
            workspace_dir=os.getenv("EVOLUTION_WORKSPACE", "/tmp/synapse_evolution"),
            rustc_path=os.getenv("RUSTC_PATH", "rustc")
        )
        
        logger.info("[Main] ✓ EvolutionaryEngine initialized")
        
        # ====================================================================
        # 🔗 LINK IMMUNE SYSTEM ↔ EVOLUTIONARY ENGINE
        # ====================================================================
        # This is the critical connection that enables algorithmic evolution
        
        immune_manager = get_immune_system()
        if immune_manager:
            immune_manager.evolutionary_engine = evolutionary_engine
            logger.info("[Main] 🧬 ✓ ImmuneSystem ↔ EvolutionaryEngine LINKED")
            logger.info("[Main]    Network can now self-evolve at code level!")
        else:
            logger.error("[Main] ✗ Could not link EvolutionaryEngine - ImmuneSystem not found")
    else:
        logger.info("[Main] EvolutionaryEngine disabled (config-only remedies)")
    
    logger.info("[Main] === Autonomous Evolution System Ready ===")


# ============================================================================
# ADD TO docker-compose.yml
# ============================================================================

DOCKER_COMPOSE_ADDITIONS = """
services:
  node-1:
    environment:
      # Immune System
      - ENABLE_IMMUNE_SYSTEM=true
      
      # Evolutionary Engine
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
# TESTING THE INTEGRATION
# ============================================================================

async def test_integration_manually():
    """
    Manual test to verify ImmuneSystem → EvolutionaryEngine integration.
    
    Run this from the FastAPI /api/test-evolution endpoint or similar.
    """
    from app.immune_system import get_immune_system, HealthIssue
    from datetime import datetime, timezone
    
    immune_system = get_immune_system()
    
    if not immune_system:
        return {"error": "ImmuneSystem not initialized"}
    
    if not immune_system.evolutionary_engine:
        return {"error": "EvolutionaryEngine not linked to ImmuneSystem"}
    
    # Create a test algorithmic issue
    test_issue = HealthIssue(
        issue_type="high_latency",
        severity="high",
        current_value=12000.0,  # 12 seconds
        target_value=3000.0,    # Target: 3 seconds
        recommended_action="generate_optimized_code",  # ← This triggers code gen
        description="Message propagation latency consistently exceeds 10 seconds despite config changes",
        detected_at=datetime.now(timezone.utc).isoformat(),
        issue_source="algorithm",  # ← Critical: marks as algorithmic
        affected_component="gossip_protocol"
    )
    
    # Trigger remedy proposal (will invoke EvolutionaryEngine)
    await immune_system.propose_remedy(test_issue)
    
    return {
        "status": "test_issue_submitted",
        "issue_type": test_issue.issue_type,
        "check": "Watch logs for '[EvolutionaryEngine] ✓ Compilation successful'"
    }


# ============================================================================
# EXAMPLE API ENDPOINT (add to app/main.py)
# ============================================================================

@app.get("/api/evolution/test")
async def test_evolution_integration():
    """
    Test endpoint to trigger evolutionary code generation.
    
    Usage:
        curl http://localhost:8000/api/evolution/test
    """
    try:
        result = await test_integration_manually()
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/evolution/stats")
async def get_evolution_stats():
    """
    Get statistics from EvolutionaryEngine.
    
    Usage:
        curl http://localhost:8000/api/evolution/stats | jq
    """
    from app.evolutionary_engine import get_evolutionary_engine_manager
    
    engine = get_evolutionary_engine_manager()
    
    if not engine:
        return {"error": "EvolutionaryEngine not initialized"}
    
    return engine.get_statistics()


@app.get("/api/evolution/proposals")
async def get_code_upgrade_proposals():
    """
    List all code upgrade proposals in governance.
    
    Usage:
        curl http://localhost:8000/api/evolution/proposals | jq
    """
    proposals = network_state.get("global", {}).get("proposals", {})
    
    code_upgrades = [
        {
            "id": p["id"],
            "title": p["title"],
            "status": p["status"],
            "component": p["params"]["target_component"],
            "wasm_hash": p["params"]["wasm_hash"][:16] + "...",
            "wasm_size_bytes": p["params"]["wasm_size_bytes"],
            "estimated_improvement": p["params"]["estimated_improvement"],
            "votes": p["vote_count"],
            "created_at": p["created_at"]
        }
        for p in proposals.values()
        if p.get("proposal_type") == "code_upgrade"
    ]
    
    return {
        "total_proposals": len(proposals),
        "code_upgrade_proposals": len(code_upgrades),
        "proposals": code_upgrades
    }


# ============================================================================
# VERIFICATION CHECKLIST
# ============================================================================

VERIFICATION_CHECKLIST = """
✅ Integration Checklist:

1. Environment Variables:
   [ ] ENABLE_IMMUNE_SYSTEM=true
   [ ] ENABLE_EVOLUTIONARY_ENGINE=true
   [ ] LLM_PROVIDER=ollama_local
   [ ] LLM_MODEL=codellama:7b
   [ ] LLM_ENDPOINT configured

2. Prerequisites:
   [ ] Ollama running (check: curl http://localhost:11434/api/tags)
   [ ] codellama:7b model downloaded (ollama pull codellama:7b)
   [ ] Rust installed (rustc --version)
   [ ] wasm32-unknown-unknown target installed

3. Initialization Logs:
   [ ] "[Main] ✓ ImmuneSystem initialized and started"
   [ ] "[Main] ✓ EvolutionaryEngine initialized"
   [ ] "[Main] 🧬 ✓ ImmuneSystem ↔ EvolutionaryEngine LINKED"

4. Test Evolution:
   [ ] curl http://localhost:8000/api/evolution/test
   [ ] Check logs for "[EvolutionaryEngine] Generated Rust code"
   [ ] Check logs for "[EvolutionaryEngine] ✓ Compilation successful"
   [ ] Check logs for "[ImmuneSystem] 🧬 Code upgrade proposal submitted"

5. Verify Proposals:
   [ ] curl http://localhost:8000/api/evolution/proposals | jq
   [ ] Proposal type should be "code_upgrade"
   [ ] WASM hash should be present
   [ ] Source code should be visible in proposal description

6. Vote and Deploy:
   [ ] Vote on code upgrade proposal via governance
   [ ] After approval, check self-upgrade manager deploys WASM
   [ ] Monitor performance metrics for improvement

=== SUCCESS CRITERIA ===

✓ ImmuneSystem detects persistent algorithmic issue (3+ cycles)
✓ Issue escalates to Evolutionary Engine
✓ LLM generates optimized Rust code
✓ Code compiles to WASM successfully
✓ Governance proposal created with type="code_upgrade"
✓ Community can vote on proposal
✓ Approved WASM deployed to network
✓ Performance metrics improve post-deployment

Status: 🧬 INTEGRATION READY
"""

if __name__ == "__main__":
    print(VERIFICATION_CHECKLIST)
