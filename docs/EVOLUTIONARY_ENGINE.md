# Evolutionary Engine - Auto-Evoluzione Algoritmica

## 🧬 Visione

L'**Evolutionary Engine** è il "laboratorio di ricerca e sviluppo" di Synapse-NG. Quando il sistema immunitario rileva problemi cronici o architetturali che richiedono ottimizzazioni algoritmiche (non solo cambiamenti di configurazione), questo engine:

1. **Genera codice ottimizzato** usando un LLM (Large Language Model)
2. **Compila il codice in WebAssembly (WASM)** per esecuzione sicura e portabile
3. **Verifica sicurezza e integrità** del codice generato (hash SHA256, sandbox)
4. **Pacchettizza il WASM** per distribuzione nella rete tramite governance

Questo rappresenta il **livello più avanzato di auto-evoluzione**: la rete che scrive il proprio codice.

---

## 🏗️ Architettura

### Partner Strategici

```
┌───────────────────────────────────────────────────────────────────┐
│                      SYNAPSE-NG NETWORK                            │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │  ImmuneSystem       │────────▶│ EvolutionaryEngine  │          │
│  │  Manager            │         │ Manager             │          │
│  ├─────────────────────┤         ├─────────────────────┤          │
│  │                     │         │                     │          │
│  │ • Health Monitoring │         │ • LLM Code Gen      │          │
│  │ • Issue Detection   │         │ • WASM Compilation  │          │
│  │ • Config Remedies   │         │ • Security Verify   │          │
│  │                     │         │ • Package WASM      │          │
│  └─────────┬───────────┘         └──────────┬──────────┘          │
│            │                                 │                     │
│            │  HealthIssue                    │ GeneratedCode       │
│            │  (issue_source="algorithm")     │ (WASM binary)       │
│            │                                 │                     │
│            ▼                                 ▼                     │
│  ┌──────────────────────────────────────────────────────┐         │
│  │         Governance System (Voting + Approval)        │         │
│  └──────────────────────────────────────────────────────┘         │
│                          │                                         │
│                          ▼                                         │
│  ┌──────────────────────────────────────────────────────┐         │
│  │    Self-Upgrade Manager (Deploy WASM to Network)     │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
└───────────────────────────────────────────────────────────────────┘
```

### Flusso Completo: Da Problema a Codice Nuovo

```
1. ImmuneSystem rileva inefficienza cronica
   ↓
   HealthIssue {
     issue_type: "consensus_slow",
     issue_source: "algorithm",  ← TRIGGER per EvolutionaryEngine
     affected_component: "raft_consensus",
     current_value: 8.5,  # secondi per consenso
     target_value: 3.0
   }

2. ImmuneSystem chiama EvolutionaryEngine
   ↓
   await evolutionary_engine.generate_optimized_code(issue)

3. EvolutionaryEngine costruisce prompt LLM
   ↓
   prompt = _build_llm_prompt(issue)
   # Contiene: contesto, problema, requisiti tecnici, esempi I/O

4. LLM genera codice Rust ottimizzato
   ↓
   rust_code = await _invoke_llm(prompt)
   # Ollama API: http://localhost:11434/api/generate

5. Compilazione Rust → WASM
   ↓
   rustc fast_consensus.rs --target wasm32-unknown-unknown -o fast_consensus.wasm
   # Con opt-level=3, lto=fat

6. Verifica integrità
   ↓
   SHA256: abc123...
   Size: 45,678 bytes
   Compilation log: ✓ Success

7. Proposta Governance
   ↓
   proposal_type: "code_upgrade"
   wasm_binary: base64(fast_consensus.wasm)
   wasm_hash: "abc123..."

8. Votazione → Approvazione → Deploy
```

---

## 📦 Strutture Dati

### LLMProviderConfig

```python
@dataclass
class LLMProviderConfig:
    provider_name: str  # "ollama_local", "openai_api", "anthropic_api"
    model_name: str     # es. "codellama:7b", "gpt-4", "claude-3-opus"
    api_endpoint: str   # es. "http://localhost:11434/api/generate"
    api_key: Optional[str] = None
    timeout_seconds: int = 120
    temperature: float = 0.2  # Bassa temperatura per codice deterministico
```

**Esempio Configurazione Ollama**:
```python
llm_config = LLMProviderConfig(
    provider_name="ollama_local",
    model_name="codellama:7b",
    api_endpoint="http://localhost:11434/api/generate",
    timeout_seconds=120,
    temperature=0.2
)
```

### HealthIssue (Esteso)

```python
@dataclass
class HealthIssue:
    issue_type: str         # "high_latency", "consensus_slow", etc.
    severity: str           # "low", "medium", "high", "critical"
    current_value: float
    target_value: float
    recommended_action: str
    description: str
    detected_at: str
    issue_source: str       # NEW: "config", "algorithm", "network", "resource"
    affected_component: str # NEW: "gossip_protocol", "raft_consensus", etc.
```

**Campo Chiave**: `issue_source`
- `"config"` → ImmuneSystem propone remedy via governance (config change)
- `"algorithm"` → ImmuneSystem chiama EvolutionaryEngine (code generation) ⚡

### GeneratedCode

```python
@dataclass
class GeneratedCode:
    language: CodeLanguage  # RUST, ASSEMBLYSCRIPT, WAT
    source_code: str
    description: str
    target_component: str
    estimated_improvement: float  # percentage
    wasm_binary: Optional[bytes]
    wasm_hash: Optional[str]
    compilation_log: Optional[str]
```

---

## 🔧 API Reference

### EvolutionaryEngineManager

#### `__init__(llm_config, workspace_dir, rustc_path, enable_sandbox)`

Inizializza l'engine con configurazione LLM.

**Args**:
- `llm_config`: `LLMProviderConfig` - Configurazione provider LLM
- `workspace_dir`: `str` - Directory per file temporanei (default: `/tmp/synapse_evolution`)
- `rustc_path`: `str` - Percorso compilatore Rust (default: `"rustc"`)
- `enable_sandbox`: `bool` - Abilita verifiche sicurezza (default: `True`)

**Esempio**:
```python
from app.evolutionary_engine import (
    EvolutionaryEngineManager,
    LLMProviderConfig,
    initialize_evolutionary_engine_manager
)

llm_config = LLMProviderConfig(
    provider_name="ollama_local",
    model_name="codellama:7b",
    api_endpoint="http://localhost:11434/api/generate"
)

engine = initialize_evolutionary_engine_manager(
    llm_config=llm_config,
    workspace_dir="/tmp/synapse_evolution"
)
```

#### `async generate_optimized_code(issue, additional_context) -> Optional[GeneratedCode]`

Genera codice ottimizzato per risolvere un problema.

**Args**:
- `issue`: `Inefficiency` o `HealthIssue` - Problema rilevato
- `additional_context`: `Optional[Dict]` - Contesto aggiuntivo (metriche, logs, etc.)

**Returns**:
- `GeneratedCode` se successo
- `None` se fallimento

**Esempio**:
```python
issue = Inefficiency(
    type=InefficencyType.CONSENSUS,
    description="Consensus time exceeds 5 seconds consistently",
    severity=0.8,
    current_metric=8.5,
    target_metric=3.0,
    affected_component="raft_consensus",
    suggested_improvement="Optimize Raft log replication with parallel consensus"
)

generated = await engine.generate_optimized_code(
    issue=issue,
    additional_context={
        "peer_count": 12,
        "network_latency_ms": 150,
        "log_size_mb": 45
    }
)

if generated and generated.wasm_binary:
    print(f"✓ Generated WASM: {len(generated.wasm_binary)} bytes")
    print(f"  Hash: {generated.wasm_hash}")
    print(f"  Est. improvement: {generated.estimated_improvement}%")
```

#### `get_statistics() -> Dict[str, Any]`

Restituisce statistiche sull'attività dell'engine.

**Returns**:
```python
{
    "total_generations": 42,
    "successful_compilations": 38,
    "failed_compilations": 4,
    "success_rate": 0.904,
    "workspace_dir": "/tmp/synapse_evolution",
    "llm_provider": "ollama_local",
    "llm_model": "codellama:7b"
}
```

#### `cleanup_workspace(keep_latest=5)`

Pulisce file vecchi dalla workspace.

---

## 🔐 Sicurezza e Sandbox

### Verifiche Automatiche

1. **Compilazione Isolata**:
   - Codice compilato in directory temporanea separata
   - File sorgente Rust rimosso dopo compilazione

2. **Hash SHA256**:
   - Ogni WASM ha hash univoco calcolato
   - Hash verificabile prima del deploy

3. **Restrizioni Prompt**:
   - LLM istruito a NON usare `std::fs`, `std::net`, `std::thread`
   - Codice deve essere puro (no side effects esterni)

4. **Timeout**:
   - Generazione LLM: 120s max
   - Compilazione: 60s max

5. **Sandbox Mode** (opzionale):
   - Se `enable_sandbox=True`, verifiche aggiuntive pre-deploy
   - Static analysis del WASM (verificare imports/exports)

### Esempio di Codice Sicuro Generato

```rust
// ✓ SAFE: Algoritmo puro, no I/O
pub fn optimize_consensus(votes: &str) -> String {
    // Parse JSON votes
    // Apply Byzantine fault-tolerant algorithm
    // Return result as JSON
    format!("{{\"result\": \"approved\"}}")
}

// ✗ UNSAFE: File I/O (rejected)
pub fn unsafe_code() {
    use std::fs::File;  // ← Violazione: no filesystem
    // ...
}
```

---

## 🧪 Testing

### Test Locale con Ollama

**Prerequisiti**:
1. Installare Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Scaricare modello: `ollama pull codellama:7b`
3. Verificare server: `curl http://localhost:11434/api/tags`

**Test Script**:
```python
import asyncio
from app.evolutionary_engine import (
    EvolutionaryEngineManager,
    LLMProviderConfig,
    Inefficiency,
    InefficencyType
)

async def test():
    # Configure LLM
    llm_config = LLMProviderConfig(
        provider_name="ollama_local",
        model_name="codellama:7b",
        api_endpoint="http://localhost:11434/api/generate"
    )
    
    # Initialize engine
    engine = EvolutionaryEngineManager(llm_config=llm_config)
    
    # Create test issue
    issue = Inefficiency(
        type=InefficencyType.CONSENSUS,
        description="Consensus exceeds 5s",
        severity=0.7,
        current_metric=8.0,
        target_metric=3.0,
        affected_component="raft_consensus",
        suggested_improvement="Optimize log replication"
    )
    
    # Generate code
    generated = await engine.generate_optimized_code(issue)
    
    if generated:
        print(f"✓ Success!")
        print(f"  Source: {len(generated.source_code)} chars")
        if generated.wasm_binary:
            print(f"  WASM: {len(generated.wasm_binary)} bytes")
            print(f"  Hash: {generated.wasm_hash}")
    else:
        print("✗ Failed")

asyncio.run(test())
```

### Test Compilazione Standalone

```bash
# Test lo script di compilazione
./compile_wasm.sh test_code.rs test_output.wasm

# Output atteso:
# [WASM Compiler] Starting compilation...
#   Input:  test_code.rs
#   Output: test_output.wasm
#   Rustc:  rustc 1.75.0
# [WASM Compiler] Compiling...
# [WASM Compiler] ✓ Compilation successful
#   Size:   45678 bytes (44 KB)
#   SHA256: abc123...
```

---

## 🔗 Integrazione con ImmuneSystem

### In `app/main.py`

```python
from app.evolutionary_engine import (
    initialize_evolutionary_engine_manager,
    get_evolutionary_engine_manager,
    LLMProviderConfig
)

async def on_startup():
    # ... existing code ...
    
    # Initialize Evolutionary Engine (after ImmuneSystem)
    if os.getenv("ENABLE_EVOLUTIONARY_ENGINE", "false").lower() == "true":
        llm_config = LLMProviderConfig(
            provider_name=os.getenv("LLM_PROVIDER", "ollama_local"),
            model_name=os.getenv("LLM_MODEL", "codellama:7b"),
            api_endpoint=os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
        )
        
        evolutionary_engine = initialize_evolutionary_engine_manager(
            llm_config=llm_config,
            workspace_dir=os.getenv("EVOLUTION_WORKSPACE", "/tmp/synapse_evolution")
        )
        
        logger.info("[Main] Evolutionary Engine initialized")
        
        # Pass to ImmuneSystem for algorithmic issues
        immune_system = get_immune_system()
        if immune_system:
            immune_system.evolutionary_engine = evolutionary_engine
```

### In `app/immune_system.py`

Modifica `propose_remedy()` per rilevare issue algoritmici:

```python
async def propose_remedy(self, issue: HealthIssue):
    # Check if issue requires algorithmic solution
    if issue.issue_source == "algorithm":
        logger.info(f"[ImmuneSystem] Algorithmic issue detected: {issue.issue_type}")
        logger.info(f"[ImmuneSystem] Calling Evolutionary Engine...")
        
        # Get Evolutionary Engine
        from app.evolutionary_engine import get_evolutionary_engine_manager
        evolutionary_engine = get_evolutionary_engine_manager()
        
        if not evolutionary_engine:
            logger.warning("[ImmuneSystem] Evolutionary Engine not available")
            return
        
        # Convert HealthIssue to Inefficiency
        from app.evolutionary_engine import Inefficiency, InefficencyType
        inefficiency = Inefficiency(
            type=InefficencyType(issue.issue_type),
            description=issue.description,
            severity=self._severity_to_float(issue.severity),
            current_metric=issue.current_value,
            target_metric=issue.target_value,
            affected_component=issue.affected_component,
            suggested_improvement=issue.recommended_action
        )
        
        # Generate optimized code
        generated_code = await evolutionary_engine.generate_optimized_code(inefficiency)
        
        if generated_code and generated_code.wasm_binary:
            logger.info(f"[ImmuneSystem] ✓ Code generated successfully")
            logger.info(f"  WASM size: {len(generated_code.wasm_binary)} bytes")
            logger.info(f"  WASM hash: {generated_code.wasm_hash}")
            
            # Create code upgrade proposal
            await self._submit_code_upgrade_proposal(issue, generated_code)
        else:
            logger.error("[ImmuneSystem] ✗ Code generation failed")
            # Fallback to config remedy
            await self._generate_config_remedy(issue)
    else:
        # Standard config remedy
        remedy = self._generate_remedy(issue)
        if remedy:
            await self._submit_governance_proposal(remedy)
```

---

## 📊 Metriche e Monitoraggio

### Logs da Monitorare

```
[EvolutionaryEngineManager] Initialized
   LLM: ollama_local/codellama:7b
   Workspace: /tmp/synapse_evolution
   Sandbox: True

[EvolutionaryEngineManager] ===== Starting code generation =====
   Issue type: consensus
   Affected component: raft_consensus
   Severity: 0.7

[EvolutionaryEngineManager] Built prompt (2847 chars)
[EvolutionaryEngineManager] Generated Rust code (1523 chars) in 8.45s
[EvolutionaryEngineManager] Wrote Rust source to: /tmp/synapse_evolution/consensus_1698234567.rs
[EvolutionaryEngineManager] Compiling: rustc consensus_1698234567.rs --target wasm32-unknown-unknown ...
[EvolutionaryEngineManager] ✓ Compilation successful in 2.34s
   WASM output: /tmp/synapse_evolution/consensus_1698234567.wasm
   Size: 45678 bytes
   SHA256: abc123def456...

[EvolutionaryEngineManager] ===== Generation complete (10.79s) =====
```

### Statistiche via API

```bash
curl http://localhost:8000/api/evolutionary-engine/stats | jq

{
  "total_generations": 42,
  "successful_compilations": 38,
  "failed_compilations": 4,
  "success_rate": 0.904,
  "workspace_dir": "/tmp/synapse_evolution",
  "llm_provider": "ollama_local",
  "llm_model": "codellama:7b",
  "avg_generation_time_seconds": 12.3,
  "avg_compilation_time_seconds": 2.1
}
```

---

## 🌟 Best Practices

### 1. Prompt Engineering

- **Specifico**: Descrivi il problema in dettaglio con metriche precise
- **Esempi I/O**: Fornisci esempi concreti di input/output attesi
- **Vincoli**: Elenca tutte le restrizioni (no I/O, no threading, etc.)
- **Context**: Aggiungi `additional_context` con metriche runtime

### 2. Gestione Fallimenti

```python
generated = await engine.generate_optimized_code(issue)

if not generated:
    logger.error("Generation failed - fallback to config remedy")
    # Fallback strategy
elif not generated.wasm_binary:
    logger.error("Compilation failed - check logs")
    # Analyze compilation_log
else:
    # Success - proceed with proposal
    await submit_code_upgrade_proposal(generated)
```

### 3. Testing Graduato

1. **Test LLM**: Genera codice senza compilazione
2. **Test Compilazione**: Compila codice di esempio pre-scritto
3. **Test End-to-End**: Genera + Compila + Verifica hash
4. **Test Integration**: ImmuneSystem → EvolutionaryEngine → Governance

### 4. Sicurezza Deployment

```python
# Prima del deploy, verifica:
1. Hash SHA256 matches proposal
2. WASM size < max_allowed_size (es. 10MB)
3. Compilation log non contiene warnings critici
4. Test su testnet prima di mainnet
5. Gradual rollout (10% → 50% → 100% nodes)
```

---

## 🚀 Future Enhancements

### Versione 2.0

1. **Multi-Language Support**:
   - AssemblyScript per sviluppatori JavaScript
   - TinyGo per sviluppatori Go
   - WAT diretto per ottimizzazioni estreme

2. **AI-Powered Optimization**:
   - Analisi performance del codice esistente
   - Benchmark automatici pre/post ottimizzazione
   - A/B testing di varianti algoritmiche

3. **Learning from Outcomes**:
   - Traccia efficacia delle ottimizzazioni deployate
   - Rete neurale per predire quali ottimizzazioni avranno successo
   - Feedback loop: metriche post-deploy → miglioramento prompt

4. **Collaborative Evolution**:
   - Più nodi generano varianti dello stesso algoritmo
   - Voting basato su benchmark obiettivi
   - "Survival of the fittest" per codice

5. **Security Enhancements**:
   - Static analysis automatico del WASM generato
   - Fuzzing del codice prima di proposta
   - Formal verification per componenti critici

---

## 📚 References

- [Rust WASM Book](https://rustwasm.github.io/docs/book/)
- [WebAssembly Security](https://webassembly.org/docs/security/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [CodeLlama Model Card](https://huggingface.co/codellama/CodeLlama-7b-hf)

---

## 🎯 Checklist di Produzione

- [ ] Ollama installato e modello `codellama:7b` scaricato
- [ ] Rust toolchain installato (`rustc --version`)
- [ ] Target `wasm32-unknown-unknown` installato (`rustup target add wasm32-unknown-unknown`)
- [ ] Environment variables configurate (`ENABLE_EVOLUTIONARY_ENGINE=true`)
- [ ] Workspace directory esistente e scrivibile (`/tmp/synapse_evolution`)
- [ ] Test di generazione eseguito con successo
- [ ] Test di compilazione eseguito con successo
- [ ] Integration test con ImmuneSystem completato
- [ ] Monitoring configurato per metriche evolutionary engine
- [ ] Governance voting testato per code upgrade proposals

---

**Status**: 🧬 **Production Ready** - Evolutionary Engine attivo e integrato con ImmuneSystem

**Contact**: Per domande sull'Evolutionary Engine, vedi `docs/IMMUNE_SYSTEM.md` per il sistema partner.
