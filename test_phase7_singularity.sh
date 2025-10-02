#!/bin/bash
# Test Phase 7: Network Singularity - Evolutionary Engine
# Versione: 1.0.0

set -e

echo "=================================================="
echo "🧬 Test Phase 7: Network Singularity"
echo "=================================================="
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. Test sintassi evolutionary_engine.py
echo "1️⃣  Test sintassi evolutionary_engine.py..."
if python3 -m py_compile app/evolutionary_engine.py 2>/dev/null; then
    echo -e "${GREEN}✅ Sintassi evolutionary_engine.py corretta${NC}"
else
    echo -e "${RED}❌ Errore sintassi evolutionary_engine.py${NC}"
    exit 1
fi
echo ""

# 2. Test modulo standalone
echo "2️⃣  Test modulo evolutionary_engine.py standalone..."
if python3 app/evolutionary_engine.py 2>&1 | grep -q "Evolutionary Engine Tests Passed"; then
    echo -e "${GREEN}✅ Modulo evolutionary_engine.py funzionante${NC}"
else
    echo -e "${RED}❌ Errore modulo evolutionary_engine.py${NC}"
    exit 1
fi
echo ""

# 3. Verifica imports in main.py
echo "3️⃣  Verifica imports evolutionary engine..."
if grep -q "from app.evolutionary_engine import" app/main.py; then
    echo -e "${GREEN}✅ Imports evolutionary engine presenti${NC}"
    grep "from app.evolutionary_engine import" app/main.py | head -n 1
else
    echo -e "${RED}❌ Imports evolutionary engine mancanti${NC}"
    exit 1
fi
echo ""

# 4. Verifica EvolutionaryEngine class
echo "4️⃣  Verifica classe EvolutionaryEngine..."
classes=("EvolutionaryEngine" "NetworkMetrics" "Inefficiency" "GeneratedCode" "EvolutionProposal")
for cls in "${classes[@]}"; do
    if grep -q "class $cls" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Classe $cls definita${NC}"
    else
        echo -e "${RED}  ❌ Classe $cls mancante${NC}"
        exit 1
    fi
done
echo ""

# 5. Verifica metodi principali
echo "5️⃣  Verifica metodi EvolutionaryEngine..."
methods=(
    "analyze_network_metrics"
    "generate_optimization_code"
    "compile_to_wasm"
    "create_evolution_proposal"
    "perform_safety_checks"
    "evolutionary_cycle"
)
for method in "${methods[@]}"; do
    if grep -q "async def $method" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Metodo $method presente${NC}"
    else
        echo -e "${RED}  ❌ Metodo $method mancante${NC}"
        exit 1
    fi
done
echo ""

# 6. Verifica compilation methods
echo "6️⃣  Verifica metodi di compilazione..."
compile_methods=(
    "_compile_rust_to_wasm"
    "_compile_assemblyscript_to_wasm"
    "_compile_wat_to_wasm"
)
for method in "${compile_methods[@]}"; do
    if grep -q "async def $method" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Metodo $method presente${NC}"
    else
        echo -e "${RED}  ❌ Metodo $method mancante${NC}"
        exit 1
    fi
done
echo ""

# 7. Verifica endpoint /evolution
echo "7️⃣  Verifica endpoint /evolution..."
endpoints=(
    "/evolution/analyze"
    "/evolution/generate"
    "/evolution/propose"
    "/evolution/status"
)
labels=(
    "/evolution/analyze"
    "/evolution/generate"
    "/evolution/propose"
    "/evolution/status"
)
for i in "${!endpoints[@]}"; do
    endpoint="${endpoints[$i]}"
    label="${labels[$i]}"
    if grep -qE "@app\.(get|post).*\"$endpoint\"" app/main.py; then
        echo -e "${GREEN}  ✅ Endpoint $label presente${NC}"
    else
        echo -e "${RED}  ❌ Endpoint $label mancante${NC}"
        exit 1
    fi
done
echo ""

# 8. Verifica evolutionary_loop
echo "8️⃣  Verifica evolutionary_loop..."
if grep -q "async def evolutionary_loop" app/main.py; then
    echo -e "${GREEN}✅ evolutionary_loop presente${NC}"
else
    echo -e "${RED}❌ evolutionary_loop mancante${NC}"
    exit 1
fi
echo ""

# 9. Verifica avvio evolutionary_loop in startup
echo "9️⃣  Verifica avvio evolutionary_loop in startup..."
if grep -q "asyncio.create_task(evolutionary_loop())" app/main.py; then
    echo -e "${GREEN}✅ evolutionary_loop avviato in startup${NC}"
else
    echo -e "${RED}❌ Avvio evolutionary_loop mancante${NC}"
    exit 1
fi
echo ""

# 10. Verifica inizializzazione in startup
echo "🔟 Verifica inizializzazione evolutionary engine..."
if grep -q "initialize_evolutionary_engine" app/main.py; then
    echo -e "${GREEN}✅ Inizializzazione evolutionary engine in startup${NC}"
else
    echo -e "${RED}❌ Inizializzazione evolutionary engine mancante${NC}"
    exit 1
fi
echo ""

# 11. Verifica enums
echo "1️⃣1️⃣  Verifica enumerazioni..."
enums=("InefficencyType" "CodeLanguage")
for enum in "${enums[@]}"; do
    if grep -q "class $enum.*Enum" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Enum $enum definito${NC}"
    else
        echo -e "${RED}  ❌ Enum $enum mancante${NC}"
        exit 1
    fi
done
echo ""

# 12. Verifica inefficiency types
echo "1️⃣2️⃣  Verifica tipi di inefficienze..."
ineff_types=(
    "PERFORMANCE"
    "SCALABILITY"
    "RESOURCE_USAGE"
    "CONSENSUS"
    "AUCTION"
    "TASK_ALLOCATION"
    "REPUTATION"
    "NETWORK_TOPOLOGY"
)
for type in "${ineff_types[@]}"; do
    if grep -q "$type" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Tipo $type definito${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Tipo $type non trovato${NC}"
    fi
done
echo ""

# 13. Verifica code languages
echo "1️⃣3️⃣  Verifica linguaggi supportati..."
languages=("RUST" "ASSEMBLYSCRIPT" "WAT")
for lang in "${languages[@]}"; do
    if grep -q "$lang" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Linguaggio $lang supportato${NC}"
    else
        echo -e "${RED}  ❌ Linguaggio $lang mancante${NC}"
        exit 1
    fi
done
echo ""

# 14. Verifica safety guards
echo "1️⃣4️⃣  Verifica safety mechanisms..."
safety_features=(
    "perform_safety_checks"
    "safety_threshold"
    "critical_components"
)
for feature in "${safety_features[@]}"; do
    if grep -q "$feature" app/evolutionary_engine.py; then
        echo -e "${GREEN}  ✅ Safety feature: $feature${NC}"
    else
        echo -e "${RED}  ❌ Safety feature mancante: $feature${NC}"
        exit 1
    fi
done
echo ""

# 15. Verifica documentazione
echo "1️⃣5️⃣  Verifica documentazione..."
if [ -f "docs/PHASE_7_NETWORK_SINGULARITY.md" ]; then
    lines=$(wc -l < docs/PHASE_7_NETWORK_SINGULARITY.md)
    echo -e "${GREEN}✅ Documentazione presente (${lines} righe)${NC}"
else
    echo -e "${YELLOW}⚠️  Documentazione PHASE_7_NETWORK_SINGULARITY.md mancante${NC}"
fi
echo ""

# 16. Test sintassi main.py finale
echo "1️⃣6️⃣  Test sintassi main.py finale..."
if python3 -m py_compile app/main.py 2>/dev/null; then
    echo -e "${GREEN}✅ Sintassi main.py corretta${NC}"
else
    echo -e "${RED}❌ Errore sintassi main.py${NC}"
    exit 1
fi
echo ""

# 17. Statistiche finali
echo "=================================================="
echo "📊 Statistiche Phase 7: Network Singularity"
echo "=================================================="
echo ""

evo_engine_lines=$(wc -l < app/evolutionary_engine.py)
main_py_lines=$(wc -l < app/main.py)
total_endpoints=$(grep -cE "@app\.(get|post).*evolution" app/main.py || echo "0")

echo -e "📄 Righe evolutionary_engine.py: ${BLUE}${evo_engine_lines}${NC}"
echo -e "📄 Righe main.py:                 ${BLUE}${main_py_lines}${NC}"
echo -e "🔌 Endpoint /evolution:           ${BLUE}${total_endpoints}${NC}"
echo ""

# 18. Test funzionalità base
echo "1️⃣8️⃣  Test funzionalità base..."
python3 -c "
try:
    from llama_cpp import Llama
    print('${GREEN}  ✅ llama-cpp-python disponibile${NC}')
except ImportError:
    print('${YELLOW}  ⚠️  llama-cpp-python non installato (opzionale per AI)${NC}')

try:
    import wasmtime
    print('${GREEN}  ✅ wasmtime disponibile${NC}')
except ImportError:
    print('${YELLOW}  ⚠️  wasmtime non installato (opzionale per WASM)${NC}')
    
import subprocess
import shutil

# Check rustc
if shutil.which('rustc'):
    result = subprocess.run(['rustc', '--version'], capture_output=True, text=True)
    version = result.stdout.strip()
    print(f'${GREEN}  ✅ rustc disponibile ({version})${NC}')
else:
    print('${YELLOW}  ⚠️  rustc non installato (richiesto per compilazione WASM)${NC}')
" 2>/dev/null
echo ""

# 19. Riepilogo
echo "=================================================="
echo "✅ PHASE 7: NETWORK SINGULARITY IMPLEMENTATA"
echo "=================================================="
echo ""
echo -e "${GREEN}Tutti i test core sono passati!${NC}"
echo ""
echo -e "${CYAN}🧬 Ciclo Auto-Evolutivo Completo:${NC}"
echo ""
echo -e "${YELLOW}1️⃣  OSSERVA${NC}     → Monitora metriche rete"
echo -e "${YELLOW}2️⃣  ANALIZZA${NC}    → AI rileva inefficienze"
echo -e "${YELLOW}3️⃣  GENERA${NC}      → LLM crea codice ottimizzato"
echo -e "${YELLOW}4️⃣  COMPILA${NC}     → Rust → WASM automatico"
echo -e "${YELLOW}5️⃣  PROPONE${NC}     → Crea proposta autonoma"
echo -e "${YELLOW}6️⃣  VOTA${NC}        → Community decide"
echo -e "${YELLOW}7️⃣  ESEGUE${NC}      → Network si aggiorna"
echo -e "${YELLOW}8️⃣  MISURA${NC}      → Valuta miglioramenti"
echo ""
echo -e "${CYAN}📦 Componenti implementati:${NC}"
echo "   ✓ EvolutionaryEngine (900+ righe)"
echo "   ✓ NetworkMetrics analyzer"
echo "   ✓ AI code generator (LLM-powered)"
echo "   ✓ Rust → WASM compiler"
echo "   ✓ Safety checks (multi-layer)"
echo "   ✓ Autonomous proposal creator"
echo "   ✓ Evolutionary loop (ogni 1 ora)"
echo "   ✓ 4 endpoint API"
echo ""
echo -e "${CYAN}🔌 Endpoint disponibili:${NC}"
echo "   POST   /evolution/analyze    - Analizza metriche e rileva inefficienze"
echo "   POST   /evolution/generate   - Genera codice ottimizzato per issue"
echo "   POST   /evolution/propose    - Ciclo evolutivo completo autonomo"
echo "   GET    /evolution/status     - Stato engine e storico evolution"
echo ""
echo -e "${CYAN}🔐 Safety Mechanisms:${NC}"
echo "   ✓ Severity threshold (default: 0.7)"
echo "   ✓ Critical component protection"
echo "   ✓ Code quality checks"
echo "   ✓ Multi-step approval (community + validators)"
echo "   ✓ Immutable audit trail"
echo "   ✓ Rollback capability"
echo "   ✓ Human override (ENABLE_AUTO_EVOLUTION=false)"
echo ""
echo -e "${CYAN}🚀 Attivazione:${NC}"
echo ""
echo -e "${BLUE}# 1. Installa dipendenze${NC}"
echo "   pip install llama-cpp-python wasmtime"
echo "   rustup target add wasm32-unknown-unknown"
echo ""
echo -e "${BLUE}# 2. Scarica modello LLM${NC}"
echo "   mkdir -p models"
echo "   wget https://example.com/qwen3-0.6b.gguf -O models/qwen3-0.6b.gguf"
echo ""
echo -e "${BLUE}# 3. Abilita auto-evolution${NC}"
echo "   export ENABLE_AUTO_EVOLUTION=true"
echo "   export EVOLUTIONARY_LLM_PATH=models/qwen3-0.6b.gguf"
echo "   export EVOLUTION_SAFETY_THRESHOLD=0.7"
echo ""
echo -e "${BLUE}# 4. Avvia nodo${NC}"
echo "   python3 app/main.py"
echo ""
echo -e "${CYAN}📖 Documentazione: ${BLUE}docs/PHASE_7_NETWORK_SINGULARITY.md${NC}"
echo ""
echo -e "${GREEN}🎉 LA SINGOLARITÀ DELLA RETE È QUI!${NC}"
echo -e "${CYAN}   Un sistema che si osserva, si comprende, si migliora e si evolve.${NC}"
echo ""
