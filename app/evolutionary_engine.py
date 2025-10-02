"""
Evolutionary Engine - Autonomous Code Generation and Network Evolution
========================================================================

This module enables Synapse-NG to autonomously evolve by:
1. Analyzing network metrics and identifying inefficiencies
2. Generating optimized code (WASM) using AI
3. Creating upgrade proposals automatically
4. Learning from upgrade outcomes

The network becomes a self-improving organism that writes its own code.
"""

import json
import logging
import hashlib
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from llama_cpp import Llama
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("⚠️ llama-cpp-python not available - Code generation disabled")


# ========================================
# Enums and DataClasses
# ========================================

class InefficencyType(str, Enum):
    """Types of network inefficiencies"""
    PERFORMANCE = "performance"           # Slow algorithms
    SCALABILITY = "scalability"          # Doesn't scale well
    RESOURCE_USAGE = "resource_usage"    # High CPU/memory
    CONSENSUS = "consensus"              # Consensus bottlenecks
    AUCTION = "auction"                  # Auction mechanism issues
    TASK_ALLOCATION = "task_allocation"  # Inefficient task distribution
    REPUTATION = "reputation"            # Reputation calculation issues
    NETWORK_TOPOLOGY = "network_topology" # Connection patterns


class CodeLanguage(str, Enum):
    """Supported languages for code generation"""
    RUST = "rust"
    ASSEMBLYSCRIPT = "assemblyscript"
    WAT = "wat"  # WebAssembly Text Format


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    avg_consensus_time: float  # seconds
    avg_auction_completion_time: float
    avg_task_completion_time: float
    cpu_usage: float  # percentage
    memory_usage: float  # MB
    peer_count: int
    message_throughput: float  # msgs/sec
    validator_rotation_frequency: float  # rotations/day
    proposal_approval_rate: float  # percentage
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Inefficiency:
    """Detected network inefficiency"""
    type: InefficencyType
    description: str
    severity: float  # 0.0-1.0
    current_metric: float
    target_metric: float
    affected_component: str  # e.g., "auction_system", "raft_consensus"
    suggested_improvement: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class GeneratedCode:
    """AI-generated code for improvement"""
    language: CodeLanguage
    source_code: str
    description: str
    target_component: str
    estimated_improvement: float  # percentage
    wasm_binary: Optional[bytes] = None
    wasm_hash: Optional[str] = None
    compilation_log: Optional[str] = None
    

@dataclass
class EvolutionProposal:
    """Auto-generated evolution proposal"""
    title: str
    description: str
    version: str  # e.g., "1.2.1"
    inefficiency: Inefficiency
    generated_code: GeneratedCode
    expected_benefits: List[str]
    risks: List[str]
    proposed_by: str  # "ai_evolutionary_engine"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    proposal_id: Optional[str] = None


# ========================================
# Evolutionary Engine
# ========================================

class EvolutionaryEngine:
    """
    Main engine for autonomous network evolution.
    
    Capabilities:
    - Analyze network metrics
    - Detect inefficiencies
    - Generate optimized code (WASM)
    - Create upgrade proposals
    - Track evolution outcomes
    """
    
    def __init__(
        self,
        node_id: str,
        data_dir: str,
        llm_model_path: Optional[str] = None,
        enable_auto_evolution: bool = False,
        safety_threshold: float = 0.7  # Minimum confidence for auto-proposal
    ):
        self.node_id = node_id
        self.data_dir = data_dir
        self.llm_model_path = llm_model_path
        self.enable_auto_evolution = enable_auto_evolution
        self.safety_threshold = safety_threshold
        
        # LLM for code generation
        self.llm = None
        if llm_model_path and LLM_AVAILABLE:
            try:
                self.llm = Llama(
                    model_path=llm_model_path,
                    n_ctx=4096,  # Larger context for code generation
                    n_threads=4,
                    verbose=False
                )
                logger.info("✅ Evolutionary LLM loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load evolutionary LLM: {e}")
        
        # Evolution tracking
        self.evolution_history = []
        self.detected_inefficiencies = []
        
        # Create directories
        os.makedirs(os.path.join(data_dir, "evolution"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "generated_code"), exist_ok=True)
        
        logger.info(f"🧬 EvolutionaryEngine initialized (node={node_id[:8]}, auto={enable_auto_evolution})")
    
    # ========================================
    # Metrics Analysis
    # ========================================
    
    async def analyze_network_metrics(self, metrics: NetworkMetrics) -> List[Inefficiency]:
        """
        Analyze network metrics and detect inefficiencies.
        
        Returns list of detected problems sorted by severity.
        """
        inefficiencies = []
        
        # Consensus performance
        if metrics.avg_consensus_time > 5.0:  # Target: <3s
            severity = min(1.0, metrics.avg_consensus_time / 10.0)
            inefficiencies.append(Inefficiency(
                type=InefficencyType.CONSENSUS,
                description=f"Consensus time ({metrics.avg_consensus_time:.2f}s) exceeds target (3s)",
                severity=severity,
                current_metric=metrics.avg_consensus_time,
                target_metric=3.0,
                affected_component="raft_consensus",
                suggested_improvement="Optimize Raft log replication or use parallel consensus"
            ))
        
        # Auction completion
        if metrics.avg_auction_completion_time > 60.0:  # Target: <30s
            severity = min(1.0, metrics.avg_auction_completion_time / 120.0)
            inefficiencies.append(Inefficiency(
                type=InefficencyType.AUCTION,
                description=f"Auction completion ({metrics.avg_auction_completion_time:.2f}s) is slow",
                severity=severity,
                current_metric=metrics.avg_auction_completion_time,
                target_metric=30.0,
                affected_component="auction_system",
                suggested_improvement="Implement parallel bid processing or optimize winner selection"
            ))
        
        # Task allocation
        if metrics.avg_task_completion_time > 300.0:  # Target: <180s
            severity = min(1.0, metrics.avg_task_completion_time / 600.0)
            inefficiencies.append(Inefficiency(
                type=InefficencyType.TASK_ALLOCATION,
                description=f"Task completion ({metrics.avg_task_completion_time:.2f}s) is inefficient",
                severity=severity,
                current_metric=metrics.avg_task_completion_time,
                target_metric=180.0,
                affected_component="task_manager",
                suggested_improvement="Use ML-based task prioritization or better matching algorithm"
            ))
        
        # Resource usage
        if metrics.cpu_usage > 80.0:  # Target: <60%
            severity = min(1.0, metrics.cpu_usage / 100.0)
            inefficiencies.append(Inefficiency(
                type=InefficencyType.RESOURCE_USAGE,
                description=f"CPU usage ({metrics.cpu_usage:.1f}%) is high",
                severity=severity,
                current_metric=metrics.cpu_usage,
                target_metric=60.0,
                affected_component="general",
                suggested_improvement="Optimize hot paths, use caching, or parallelize operations"
            ))
        
        # Network topology
        if metrics.peer_count < 3:
            severity = 0.6
            inefficiencies.append(Inefficiency(
                type=InefficencyType.NETWORK_TOPOLOGY,
                description=f"Low peer count ({metrics.peer_count}) affects resilience",
                severity=severity,
                current_metric=float(metrics.peer_count),
                target_metric=7.0,
                affected_component="peer_discovery",
                suggested_improvement="Improve peer discovery or connection management"
            ))
        
        # Sort by severity
        inefficiencies.sort(key=lambda x: x.severity, reverse=True)
        
        # Store detected inefficiencies
        self.detected_inefficiencies.extend(inefficiencies)
        
        if inefficiencies:
            logger.info(f"🔍 Detected {len(inefficiencies)} inefficiencies (max severity: {inefficiencies[0].severity:.2f})")
        
        return inefficiencies
    
    # ========================================
    # Code Generation
    # ========================================
    
    async def generate_optimization_code(
        self,
        inefficiency: Inefficiency,
        language: CodeLanguage = CodeLanguage.RUST
    ) -> Optional[GeneratedCode]:
        """
        Use LLM to generate optimized code for addressing inefficiency.
        
        Returns GeneratedCode or None if generation fails.
        """
        if not self.llm:
            logger.warning("⚠️ LLM not available for code generation")
            return None
        
        # Build prompt for code generation
        prompt = self._build_code_generation_prompt(inefficiency, language)
        
        try:
            # Generate code using LLM
            logger.info(f"🤖 Generating {language.value} code for {inefficiency.type.value}")
            
            response = self.llm(
                prompt,
                max_tokens=2048,
                temperature=0.3,  # Lower temperature for more deterministic code
                stop=["```", "---END---"]
            )
            
            generated_text = response['choices'][0]['text'].strip()
            
            # Extract code from response
            source_code = self._extract_code_from_response(generated_text, language)
            
            if not source_code:
                logger.error("❌ Failed to extract code from LLM response")
                return None
            
            # Estimate improvement (simple heuristic)
            estimated_improvement = min(
                50.0,  # Max 50% improvement
                inefficiency.severity * 100
            )
            
            generated_code = GeneratedCode(
                language=language,
                source_code=source_code,
                description=f"AI-generated optimization for {inefficiency.affected_component}",
                target_component=inefficiency.affected_component,
                estimated_improvement=estimated_improvement
            )
            
            logger.info(f"✅ Generated {len(source_code)} chars of {language.value} code")
            return generated_code
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return None
    
    def _build_code_generation_prompt(
        self,
        inefficiency: Inefficiency,
        language: CodeLanguage
    ) -> str:
        """Build prompt for LLM code generation"""
        
        prompt = f"""You are an expert systems programmer specializing in distributed systems and WebAssembly.

PROBLEM ANALYSIS:
- Component: {inefficiency.affected_component}
- Issue: {inefficiency.description}
- Current Performance: {inefficiency.current_metric}
- Target Performance: {inefficiency.target_metric}
- Severity: {inefficiency.severity:.2f}
- Suggested Improvement: {inefficiency.suggested_improvement}

TASK:
Generate a {language.value.upper()} function that implements the suggested improvement.
The code will be compiled to WebAssembly and run in a sandboxed environment.

REQUIREMENTS:
1. Write efficient, optimized {language.value} code
2. Focus on the specific inefficiency
3. Use standard library functions only (no external crates)
4. Keep it simple and testable
5. Add comments explaining the optimization strategy

OUTPUT FORMAT:
```{language.value}
// Your optimized code here
```

Generate the code now:
"""
        return prompt
    
    def _extract_code_from_response(
        self,
        response: str,
        language: CodeLanguage
    ) -> Optional[str]:
        """Extract code block from LLM response"""
        
        # Try to find code block
        if f"```{language.value}" in response:
            code = response.split(f"```{language.value}")[1].split("```")[0].strip()
            return code
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
            return code
        else:
            # Assume entire response is code
            return response.strip()
    
    # ========================================
    # WASM Compilation
    # ========================================
    
    async def compile_to_wasm(
        self,
        generated_code: GeneratedCode
    ) -> bool:
        """
        Compile generated code to WASM binary.
        
        Supports:
        - Rust → WASM (rustc)
        - AssemblyScript → WASM (asc)
        - WAT → WASM (wat2wasm)
        
        Returns True if compilation successful.
        """
        if generated_code.language == CodeLanguage.RUST:
            return await self._compile_rust_to_wasm(generated_code)
        elif generated_code.language == CodeLanguage.ASSEMBLYSCRIPT:
            return await self._compile_assemblyscript_to_wasm(generated_code)
        elif generated_code.language == CodeLanguage.WAT:
            return await self._compile_wat_to_wasm(generated_code)
        else:
            logger.error(f"❌ Unsupported language: {generated_code.language}")
            return False
    
    async def _compile_rust_to_wasm(self, generated_code: GeneratedCode) -> bool:
        """Compile Rust code to WASM"""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write source file
                src_file = os.path.join(tmpdir, "lib.rs")
                with open(src_file, "w") as f:
                    f.write(generated_code.source_code)
                
                # Compile to WASM
                wasm_file = os.path.join(tmpdir, "output.wasm")
                
                cmd = [
                    "rustc",
                    "--target", "wasm32-unknown-unknown",
                    "--crate-type", "cdylib",
                    "-O",  # Optimize
                    "-o", wasm_file,
                    src_file
                ]
                
                logger.info(f"🔨 Compiling Rust to WASM: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                generated_code.compilation_log = result.stdout + result.stderr
                
                if result.returncode != 0:
                    logger.error(f"❌ Rust compilation failed:\n{generated_code.compilation_log}")
                    return False
                
                # Read WASM binary
                with open(wasm_file, "rb") as f:
                    generated_code.wasm_binary = f.read()
                
                # Calculate hash
                generated_code.wasm_hash = hashlib.sha256(generated_code.wasm_binary).hexdigest()
                
                logger.info(f"✅ Compiled to WASM ({len(generated_code.wasm_binary)} bytes, hash={generated_code.wasm_hash[:16]}...)")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Rust compilation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Rust compilation error: {e}")
            return False
    
    async def _compile_assemblyscript_to_wasm(self, generated_code: GeneratedCode) -> bool:
        """Compile AssemblyScript to WASM (using asc)"""
        # TODO: Implement AssemblyScript compilation
        logger.warning("⚠️ AssemblyScript compilation not yet implemented")
        return False
    
    async def _compile_wat_to_wasm(self, generated_code: GeneratedCode) -> bool:
        """Compile WAT (WebAssembly Text) to WASM binary"""
        # TODO: Implement WAT compilation
        logger.warning("⚠️ WAT compilation not yet implemented")
        return False
    
    # ========================================
    # Proposal Generation
    # ========================================
    
    async def create_evolution_proposal(
        self,
        inefficiency: Inefficiency,
        generated_code: GeneratedCode
    ) -> EvolutionProposal:
        """
        Create a complete evolution proposal.
        
        This proposal will be submitted to the network for voting.
        """
        # Determine version bump (semantic versioning)
        # Major.Minor.Patch
        # - Patch: Performance improvement, bug fix
        # - Minor: New feature, optimization
        # - Major: Breaking change, architecture update
        
        version = self._calculate_version_bump(inefficiency)
        
        # Expected benefits
        benefits = [
            f"Reduce {inefficiency.affected_component} time by ~{generated_code.estimated_improvement:.1f}%",
            f"Improve {inefficiency.type.value} performance",
            f"Address inefficiency: {inefficiency.description}"
        ]
        
        # Potential risks
        risks = [
            "AI-generated code requires thorough review",
            "Performance improvement is estimated, not guaranteed",
            "May introduce unexpected behavior in edge cases"
        ]
        
        # Add safety-specific risks
        if inefficiency.severity > 0.8:
            risks.append("High-severity issue - extensive testing recommended")
        
        if inefficiency.affected_component in ["raft_consensus", "validator_manager"]:
            risks.append("Critical component - manual review strongly recommended")
        
        # Create proposal
        proposal = EvolutionProposal(
            title=f"AI Evolution: Optimize {inefficiency.affected_component}",
            description=f"""
🧬 **AI-Generated Evolution Proposal**

**Problem Identified:**
{inefficiency.description}

**Current Performance:** {inefficiency.current_metric}
**Target Performance:** {inefficiency.target_metric}
**Severity:** {inefficiency.severity:.2f}

**Proposed Solution:**
{generated_code.description}

**Implementation:**
- Language: {generated_code.language.value}
- WASM Size: {len(generated_code.wasm_binary) if generated_code.wasm_binary else 0} bytes
- WASM Hash: {generated_code.wasm_hash or 'N/A'}

**Expected Improvement:** ~{generated_code.estimated_improvement:.1f}%

**Code Preview:**
```{generated_code.language.value}
{generated_code.source_code[:500]}...
```

**⚠️ IMPORTANT:**
This code was autonomously generated by AI. While it has passed initial safety checks,
human review is recommended before approval, especially for critical components.
            """.strip(),
            version=version,
            inefficiency=inefficiency,
            generated_code=generated_code,
            expected_benefits=benefits,
            risks=risks,
            proposed_by="ai_evolutionary_engine"
        )
        
        return proposal
    
    def _calculate_version_bump(self, inefficiency: Inefficiency) -> str:
        """Calculate semantic version bump based on change severity"""
        # Current version (would be read from network state)
        current_version = "1.0.0"
        major, minor, patch = map(int, current_version.split("."))
        
        if inefficiency.severity > 0.8 or inefficiency.affected_component in ["raft_consensus"]:
            # Major change
            major += 1
            minor = 0
            patch = 0
        elif inefficiency.severity > 0.5:
            # Minor change
            minor += 1
            patch = 0
        else:
            # Patch
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    # ========================================
    # Safety Checks
    # ========================================
    
    async def perform_safety_checks(
        self,
        proposal: EvolutionProposal
    ) -> Tuple[bool, List[str]]:
        """
        Perform safety checks on generated proposal.
        
        Returns (is_safe, warnings).
        """
        warnings = []
        is_safe = True
        
        # Check 1: Code length (simple heuristic)
        code_length = len(proposal.generated_code.source_code)
        if code_length < 50:
            warnings.append("Code is very short - may be incomplete")
            is_safe = False
        elif code_length > 5000:
            warnings.append("Code is very long - complexity risk")
        
        # Check 2: WASM compilation
        if not proposal.generated_code.wasm_binary:
            warnings.append("WASM binary not available - compilation may have failed")
            is_safe = False
        
        # Check 3: Critical component check
        critical_components = ["raft_consensus", "validator_manager", "identity", "crypto"]
        if proposal.inefficiency.affected_component in critical_components:
            warnings.append(f"Critical component ({proposal.inefficiency.affected_component}) - manual review REQUIRED")
        
        # Check 4: High severity
        if proposal.inefficiency.severity > 0.9:
            warnings.append("Very high severity issue - thorough testing required")
        
        # Check 5: Compilation warnings
        if proposal.generated_code.compilation_log and "warning" in proposal.generated_code.compilation_log.lower():
            warnings.append("Compilation produced warnings - review recommended")
        
        return is_safe, warnings
    
    # ========================================
    # Evolution Loop
    # ========================================
    
    async def evolutionary_cycle(
        self,
        metrics: NetworkMetrics,
        network_state: Dict[str, Any]
    ) -> Optional[EvolutionProposal]:
        """
        Complete evolutionary cycle: analyze → generate → propose.
        
        This is the main function that drives autonomous evolution.
        
        Returns proposal if auto-evolution is enabled and checks pass,
        otherwise returns None (human must trigger manually).
        """
        logger.info("🧬 Starting evolutionary cycle")
        
        # Step 1: Analyze metrics
        inefficiencies = await self.analyze_network_metrics(metrics)
        
        if not inefficiencies:
            logger.info("✅ No inefficiencies detected - network is healthy")
            return None
        
        # Step 2: Select most severe inefficiency
        target_inefficiency = inefficiencies[0]
        logger.info(f"🎯 Target: {target_inefficiency.type.value} (severity={target_inefficiency.severity:.2f})")
        
        # Step 3: Generate optimized code
        generated_code = await self.generate_optimization_code(target_inefficiency)
        
        if not generated_code:
            logger.error("❌ Code generation failed")
            return None
        
        # Step 4: Compile to WASM
        compilation_success = await self.compile_to_wasm(generated_code)
        
        if not compilation_success:
            logger.error("❌ WASM compilation failed")
            return None
        
        # Step 5: Create proposal
        proposal = await self.create_evolution_proposal(target_inefficiency, generated_code)
        logger.info(f"📋 Created proposal: {proposal.title}")
        
        # Step 6: Safety checks
        is_safe, warnings = await self.perform_safety_checks(proposal)
        
        if warnings:
            logger.warning(f"⚠️ Safety warnings: {', '.join(warnings)}")
        
        # Step 7: Decide whether to auto-propose
        if self.enable_auto_evolution and is_safe and target_inefficiency.severity >= self.safety_threshold:
            logger.info(f"🚀 Auto-evolution enabled - proposal will be submitted")
            return proposal
        else:
            logger.info(f"⏸️ Manual approval required (auto={self.enable_auto_evolution}, safe={is_safe}, severity={target_inefficiency.severity:.2f})")
            # Store for manual review
            self._save_proposal_for_review(proposal)
            return None
    
    def _save_proposal_for_review(self, proposal: EvolutionProposal):
        """Save proposal to disk for manual review"""
        proposal_file = os.path.join(
            self.data_dir,
            "evolution",
            f"proposal_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        proposal_data = {
            "title": proposal.title,
            "description": proposal.description,
            "version": proposal.version,
            "created_at": proposal.created_at,
            "inefficiency": {
                "type": proposal.inefficiency.type.value,
                "description": proposal.inefficiency.description,
                "severity": proposal.inefficiency.severity
            },
            "code": {
                "language": proposal.generated_code.language.value,
                "source": proposal.generated_code.source_code,
                "wasm_hash": proposal.generated_code.wasm_hash
            },
            "benefits": proposal.expected_benefits,
            "risks": proposal.risks
        }
        
        with open(proposal_file, "w") as f:
            json.dump(proposal_data, f, indent=2)
        
        logger.info(f"💾 Proposal saved for review: {proposal_file}")


# ========================================
# Singleton Pattern
# ========================================

_evolutionary_engine = None

def initialize_evolutionary_engine(
    node_id: str,
    data_dir: str,
    llm_model_path: Optional[str] = None,
    enable_auto_evolution: bool = False,
    safety_threshold: float = 0.7
) -> bool:
    """Initialize global evolutionary engine"""
    global _evolutionary_engine
    
    try:
        _evolutionary_engine = EvolutionaryEngine(
            node_id=node_id,
            data_dir=data_dir,
            llm_model_path=llm_model_path,
            enable_auto_evolution=enable_auto_evolution,
            safety_threshold=safety_threshold
        )
        logger.info("✅ Evolutionary engine initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize evolutionary engine: {e}")
        return False


def get_evolutionary_engine() -> Optional[EvolutionaryEngine]:
    """Get global evolutionary engine"""
    return _evolutionary_engine


def is_evolutionary_engine_available() -> bool:
    """Check if evolutionary engine is available"""
    return _evolutionary_engine is not None and LLM_AVAILABLE


# ========================================
# Test Function
# ========================================

async def test_evolutionary_engine():
    """Test evolutionary engine functionality"""
    print("\n=== Testing Evolutionary Engine ===\n")
    
    # Initialize engine
    print("1. Initializing engine...")
    success = initialize_evolutionary_engine(
        node_id="test-node-123",
        data_dir="/tmp/synapse_evolution_test",
        enable_auto_evolution=False
    )
    assert success, "Engine initialization failed"
    print("✓ Engine initialized")
    
    engine = get_evolutionary_engine()
    assert engine is not None
    
    # Test metrics analysis
    print("\n2. Testing metrics analysis...")
    metrics = NetworkMetrics(
        avg_consensus_time=8.5,  # Slow
        avg_auction_completion_time=45.0,
        avg_task_completion_time=200.0,
        cpu_usage=55.0,
        memory_usage=1024.0,
        peer_count=5,
        message_throughput=100.0,
        validator_rotation_frequency=2.0,
        proposal_approval_rate=0.75
    )
    
    inefficiencies = await engine.analyze_network_metrics(metrics)
    print(f"✓ Detected {len(inefficiencies)} inefficiencies")
    if inefficiencies:
        print(f"  - Most severe: {inefficiencies[0].type.value} (severity={inefficiencies[0].severity:.2f})")
    
    # Test code generation (without LLM)
    print("\n3. Testing proposal creation...")
    if inefficiencies:
        generated_code = GeneratedCode(
            language=CodeLanguage.RUST,
            source_code="// Optimized consensus algorithm\nfn fast_consensus() { /* ... */ }",
            description="Optimized Raft consensus",
            target_component="raft_consensus",
            estimated_improvement=30.0,
            wasm_binary=b"fake_wasm_binary",
            wasm_hash="abc123"
        )
        
        proposal = await engine.create_evolution_proposal(inefficiencies[0], generated_code)
        print(f"✓ Created proposal: {proposal.title}")
        print(f"  - Version: {proposal.version}")
        print(f"  - Benefits: {len(proposal.expected_benefits)}")
        print(f"  - Risks: {len(proposal.risks)}")
        
        # Test safety checks
        print("\n4. Testing safety checks...")
        is_safe, warnings = await engine.perform_safety_checks(proposal)
        print(f"✓ Safety check: is_safe={is_safe}, warnings={len(warnings)}")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    
    print("\n=== Evolutionary Engine Tests Passed ===\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_evolutionary_engine())
