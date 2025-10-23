#!/bin/bash
# test_evolutionary_engine.sh - Test per EvolutionaryEngine
#
# Questo script testa il sistema di auto-evoluzione:
# 1. Verifica prerequisiti (Rust, Ollama)
# 2. Test compilazione WASM standalone
# 3. Test integrazione EvolutionaryEngine
# 4. Verifica generazione codice end-to-end

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Synapse-NG Evolutionary Engine Test Suite               ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# ============================================================================
# TEST 0: Prerequisites Check
# ============================================================================

echo -e "${GREEN}[TEST 0]${NC} Checking prerequisites..."

# Check Rust
if ! command -v rustc &> /dev/null; then
    echo -e "${RED}✗ FAIL: rustc not found${NC}"
    echo "Install Rust from: https://rustup.rs/"
    exit 1
fi

RUSTC_VERSION=$(rustc --version)
echo -e "${GREEN}✓${NC} Rust compiler found: $RUSTC_VERSION"

# Check wasm32 target
if ! rustc --print target-list | grep -q "wasm32-unknown-unknown"; then
    echo -e "${YELLOW}⚠${NC} wasm32-unknown-unknown target not installed"
    echo "Installing..."
    rustup target add wasm32-unknown-unknown
fi

echo -e "${GREEN}✓${NC} wasm32-unknown-unknown target available"

# Check Ollama (optional)
if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>&1 || echo "unknown")
    echo -e "${GREEN}✓${NC} Ollama found: $OLLAMA_VERSION"
    
    # Check if Ollama server is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama server is running"
        
        # Check for codellama model
        if ollama list | grep -q "codellama"; then
            echo -e "${GREEN}✓${NC} codellama model available"
        else
            echo -e "${YELLOW}⚠${NC} codellama model not found (optional for full test)"
            echo "  Download with: ollama pull codellama:7b"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Ollama server not running (optional for full test)"
        echo "  Start with: ollama serve"
    fi
else
    echo -e "${YELLOW}⚠${NC} Ollama not installed (optional for full test)"
    echo "  Install from: https://ollama.com"
fi

echo ""

# ============================================================================
# TEST 1: Compile WASM Helper Script
# ============================================================================

echo -e "${GREEN}[TEST 1]${NC} Testing compile_wasm.sh script..."

# Create test Rust code
TEST_RS_FILE="/tmp/test_evolutionary_$(date +%s).rs"
TEST_WASM_FILE="/tmp/test_evolutionary_$(date +%s).wasm"

cat > "$TEST_RS_FILE" << 'EOF'
#![no_std]

#[no_mangle]
pub extern "C" fn execute() -> i32 {
    // Simple test function that returns 42
    42
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
EOF

echo "Created test Rust file: $TEST_RS_FILE"

# Test compilation script
if [ -f "./compile_wasm.sh" ]; then
    echo "Running: ./compile_wasm.sh $TEST_RS_FILE $TEST_WASM_FILE"
    
    if ./compile_wasm.sh "$TEST_RS_FILE" "$TEST_WASM_FILE"; then
        echo -e "${GREEN}✓${NC} Compilation script successful"
        
        if [ -f "$TEST_WASM_FILE" ]; then
            WASM_SIZE=$(stat -f%z "$TEST_WASM_FILE" 2>/dev/null || stat -c%s "$TEST_WASM_FILE" 2>/dev/null)
            echo -e "${GREEN}✓${NC} WASM file created: $TEST_WASM_FILE ($WASM_SIZE bytes)"
            
            # Cleanup
            rm -f "$TEST_WASM_FILE"
        else
            echo -e "${RED}✗ FAIL: WASM file not created${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ FAIL: Compilation script failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} compile_wasm.sh not found, skipping script test"
fi

# Cleanup
rm -f "$TEST_RS_FILE"

echo ""

# ============================================================================
# TEST 2: Python Module Import
# ============================================================================

echo -e "${GREEN}[TEST 2]${NC} Testing Python module imports..."

python3 << 'EOF'
import sys

try:
    from app.evolutionary_engine import (
        EvolutionaryEngineManager,
        LLMProviderConfig,
        Inefficiency,
        InefficencyType,
        GeneratedCode,
        CodeLanguage
    )
    print("✓ All imports successful")
    print(f"  - EvolutionaryEngineManager: {EvolutionaryEngineManager.__name__}")
    print(f"  - LLMProviderConfig: {LLMProviderConfig.__name__}")
    print(f"  - Inefficiency: {Inefficiency.__name__}")
    
except ImportError as e:
    print(f"✗ FAIL: Import error: {e}")
    sys.exit(1)

# Check for HealthIssue extension
try:
    from app.immune_system import HealthIssue
    
    # Create test instance
    test_issue = HealthIssue(
        issue_type="test",
        severity="low",
        current_value=1.0,
        target_value=0.5,
        recommended_action="test",
        description="test",
        detected_at="2025-01-01T00:00:00Z",
        issue_source="algorithm",
        affected_component="test_component"
    )
    
    print("✓ HealthIssue extended with issue_source and affected_component")
    
except Exception as e:
    print(f"⚠ WARNING: HealthIssue extension check failed: {e}")
EOF

echo ""

# ============================================================================
# TEST 3: EvolutionaryEngineManager Initialization
# ============================================================================

echo -e "${GREEN}[TEST 3]${NC} Testing EvolutionaryEngineManager initialization..."

python3 << 'EOF'
import sys
import os

try:
    from app.evolutionary_engine import (
        EvolutionaryEngineManager,
        LLMProviderConfig
    )
    
    # Create LLM config
    llm_config = LLMProviderConfig(
        provider_name="ollama_local",
        model_name="codellama:7b",
        api_endpoint="http://localhost:11434/api/generate",
        timeout_seconds=120,
        temperature=0.2
    )
    
    print(f"✓ LLM config created: {llm_config.provider_name}/{llm_config.model_name}")
    
    # Initialize engine
    engine = EvolutionaryEngineManager(
        llm_config=llm_config,
        workspace_dir="/tmp/synapse_evolution_test",
        rustc_path="rustc",
        enable_sandbox=True
    )
    
    print("✓ EvolutionaryEngineManager initialized")
    print(f"  Workspace: {engine.workspace_dir}")
    print(f"  Sandbox: {engine.enable_sandbox}")
    
    # Get statistics
    stats = engine.get_statistics()
    print("✓ Statistics retrieved:")
    print(f"  Total generations: {stats['total_generations']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""

# ============================================================================
# TEST 4: Prompt Building
# ============================================================================

echo -e "${GREEN}[TEST 4]${NC} Testing prompt building..."

python3 << 'EOF'
import sys

try:
    from app.evolutionary_engine import (
        EvolutionaryEngineManager,
        LLMProviderConfig,
        Inefficiency,
        InefficencyType
    )
    
    llm_config = LLMProviderConfig(
        provider_name="ollama_local",
        model_name="codellama:7b",
        api_endpoint="http://localhost:11434/api/generate"
    )
    
    engine = EvolutionaryEngineManager(llm_config=llm_config)
    
    # Create test issue
    test_issue = Inefficiency(
        type=InefficencyType.CONSENSUS,
        description="Consensus time exceeds 5 seconds",
        severity=0.7,
        current_metric=8.0,
        target_metric=3.0,
        affected_component="raft_consensus",
        suggested_improvement="Optimize Raft log replication",
        timestamp="2025-01-01T00:00:00Z"
    )
    
    # Build prompt
    prompt = engine._build_llm_prompt(test_issue, None)
    
    print("✓ Prompt built successfully")
    print(f"  Length: {len(prompt)} characters")
    
    # Check prompt contains key sections
    required_sections = [
        "CONTESTO",
        "PROBLEMA RILEVATO",
        "OBIETTIVO",
        "REQUISITI TECNICI",
        "FORMATO OUTPUT"
    ]
    
    for section in required_sections:
        if section in prompt:
            print(f"  ✓ Contains '{section}' section")
        else:
            print(f"  ✗ Missing '{section}' section")
            sys.exit(1)
    
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""

# ============================================================================
# TEST 5: Direct Rust Compilation
# ============================================================================

echo -e "${GREEN}[TEST 5]${NC} Testing direct Rust→WASM compilation..."

python3 << 'EOF'
import sys

try:
    from app.evolutionary_engine import (
        EvolutionaryEngineManager,
        LLMProviderConfig
    )
    
    llm_config = LLMProviderConfig(
        provider_name="ollama_local",
        model_name="codellama:7b",
        api_endpoint="http://localhost:11434/api/generate"
    )
    
    engine = EvolutionaryEngineManager(
        llm_config=llm_config,
        workspace_dir="/tmp/synapse_evolution_test"
    )
    
    # Test Rust code
    test_rust_code = '''
#![no_std]

#[no_mangle]
pub extern "C" fn optimize_consensus() -> i32 {
    // Optimized consensus algorithm placeholder
    42
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    loop {}
}
'''
    
    print("Testing Rust compilation...")
    success, log, wasm_path, wasm_hash, wasm_size = engine._compile_rust_to_wasm(
        test_rust_code,
        "test_consensus"
    )
    
    if success:
        print("✓ Compilation successful")
        print(f"  WASM path: {wasm_path}")
        print(f"  WASM size: {wasm_size} bytes")
        print(f"  WASM hash: {wasm_hash[:32]}...")
    else:
        print("✗ FAIL: Compilation failed")
        print(f"Log:\n{log}")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""

# ============================================================================
# TEST 6: Code Extraction
# ============================================================================

echo -e "${GREEN}[TEST 6]${NC} Testing Rust code extraction from LLM response..."

python3 << 'EOF'
import sys

try:
    from app.evolutionary_engine import (
        EvolutionaryEngineManager,
        LLMProviderConfig
    )
    
    llm_config = LLMProviderConfig(
        provider_name="ollama_local",
        model_name="codellama:7b",
        api_endpoint="http://localhost:11434/api/generate"
    )
    
    engine = EvolutionaryEngineManager(llm_config=llm_config)
    
    # Mock LLM response
    mock_response = '''
Here is the optimized Rust code:

```rust
pub fn optimize_gossip(peers: &[u8]) -> Vec<u8> {
    // Optimized gossip algorithm
    vec![1, 2, 3]
}
```

This algorithm improves efficiency by 30%.
'''
    
    extracted_code = engine._extract_rust_code(mock_response)
    
    if extracted_code:
        print("✓ Code extraction successful")
        print(f"  Extracted: {len(extracted_code)} characters")
        
        if "pub fn optimize_gossip" in extracted_code:
            print("  ✓ Contains expected function")
        else:
            print("  ✗ Missing expected function")
            sys.exit(1)
    else:
        print("✗ FAIL: Could not extract code")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""

# ============================================================================
# TEST 7: Full Integration (with Ollama - optional)
# ============================================================================

echo -e "${GREEN}[TEST 7]${NC} Full integration test (requires Ollama)..."

if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "Ollama server detected - running full test..."
    
    python3 << 'EOF'
import asyncio
import sys

async def test_full_integration():
    try:
        from app.evolutionary_engine import (
            EvolutionaryEngineManager,
            LLMProviderConfig,
            Inefficiency,
            InefficencyType
        )
        
        llm_config = LLMProviderConfig(
            provider_name="ollama_local",
            model_name="codellama:7b",
            api_endpoint="http://localhost:11434/api/generate",
            timeout_seconds=60,  # Shorter for testing
            temperature=0.2
        )
        
        engine = EvolutionaryEngineManager(
            llm_config=llm_config,
            workspace_dir="/tmp/synapse_evolution_test"
        )
        
        # Create test issue
        issue = Inefficiency(
            type=InefficencyType.PERFORMANCE,
            description="Simple test for code generation",
            severity=0.5,
            current_metric=10.0,
            target_metric=5.0,
            affected_component="test_module",
            suggested_improvement="Write a simple Rust function",
            timestamp="2025-01-01T00:00:00Z"
        )
        
        print("Calling generate_optimized_code() (may take 30-60 seconds)...")
        
        generated = await engine.generate_optimized_code(issue)
        
        if generated:
            print("✓ Code generation successful")
            print(f"  Source code: {len(generated.source_code)} chars")
            print(f"  Compilation: {'Success' if generated.wasm_binary else 'Failed'}")
            
            if generated.wasm_binary:
                print(f"  WASM size: {len(generated.wasm_binary)} bytes")
                print(f"  WASM hash: {generated.wasm_hash[:32]}...")
            
            stats = engine.get_statistics()
            print(f"✓ Statistics: {stats['successful_compilations']}/{stats['total_generations']} success")
        else:
            print("⚠ Code generation returned None (may be timeout or LLM issue)")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return 1

sys.exit(asyncio.run(test_full_integration()))
EOF
    
else
    echo -e "${YELLOW}⚠${NC} Ollama server not running - skipping full integration test"
    echo "  To run full test: ollama serve & ollama pull codellama:7b"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Suite Complete                                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✓${NC} All core tests passed"
echo ""
echo "Next steps:"
echo "  1. Integrate with ImmuneSystem (see docs/EVOLUTIONARY_ENGINE_INTEGRATION.py)"
echo "  2. Configure environment variables in docker-compose.yml"
echo "  3. Test with real algorithmic issues from ImmuneSystem"
echo "  4. Monitor governance proposals with type='code_upgrade'"
echo ""
echo "Documentation:"
echo "  - Architecture: docs/EVOLUTIONARY_ENGINE.md"
echo "  - Integration: docs/EVOLUTIONARY_ENGINE_INTEGRATION.py"
echo "  - Immune System: docs/IMMUNE_SYSTEM.md"
echo ""

exit 0
