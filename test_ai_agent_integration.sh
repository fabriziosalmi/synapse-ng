#!/bin/bash
# Test script per verificare l'integrazione AI Agent in Synapse-NG
# Versione: 1.0.0

set -e

echo "=================================================="
echo "🧪 Test Integrazione AI Agent"
echo "=================================================="
echo ""

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Test sintassi Python
echo "1️⃣  Test sintassi main.py..."
if python3 -m py_compile app/main.py 2>/dev/null; then
    echo -e "${GREEN}✅ Sintassi main.py corretta${NC}"
else
    echo -e "${RED}❌ Errore sintassi main.py${NC}"
    exit 1
fi
echo ""

# 2. Test modulo ai_agent.py standalone
echo "2️⃣  Test modulo ai_agent.py..."
if python3 app/ai_agent.py 2>&1 | grep -q "All AI Agent Tests Passed"; then
    echo -e "${GREEN}✅ Modulo ai_agent.py funzionante${NC}"
else
    echo -e "${RED}❌ Errore modulo ai_agent.py${NC}"
    exit 1
fi
echo ""

# 3. Verifica imports AI agent in main.py
echo "3️⃣  Verifica imports AI agent..."
if grep -q "from app.ai_agent import" app/main.py; then
    echo -e "${GREEN}✅ Imports AI agent presenti${NC}"
    grep "from app.ai_agent import" app/main.py | head -n 1
else
    echo -e "${RED}❌ Imports AI agent mancanti${NC}"
    exit 1
fi
echo ""

# 4. Verifica funzioni AI agent
echo "4️⃣  Verifica funzioni AI agent..."
functions=("proactive_agent_loop" "execute_agent_action")
for func in "${functions[@]}"; do
    if grep -q "async def $func" app/main.py; then
        echo -e "${GREEN}  ✅ Funzione $func presente${NC}"
    else
        echo -e "${RED}  ❌ Funzione $func mancante${NC}"
        exit 1
    fi
done
echo ""

# 5. Verifica endpoints AI agent
echo "5️⃣  Verifica endpoints AI agent..."
endpoints=("/agent/prompt" "/agent/objectives" "/agent/status")
for endpoint in "${endpoints[@]}"; do
    if grep -q "$endpoint" app/main.py; then
        echo -e "${GREEN}  ✅ Endpoint $endpoint presente${NC}"
    else
        echo -e "${RED}  ❌ Endpoint $endpoint mancante${NC}"
        exit 1
    fi
done
echo ""

# 6. Verifica inizializzazione agent in startup
echo "6️⃣  Verifica inizializzazione agent..."
if grep -q "initialize_agent(NODE_ID, model_path)" app/main.py; then
    echo -e "${GREEN}✅ Inizializzazione agent in startup${NC}"
else
    echo -e "${RED}❌ Inizializzazione agent mancante${NC}"
    exit 1
fi
echo ""

# 7. Verifica documentazione
echo "7️⃣  Verifica documentazione..."
if [ -f "docs/AI_AGENT.md" ]; then
    lines=$(wc -l < docs/AI_AGENT.md)
    echo -e "${GREEN}✅ Documentazione presente (${lines} righe)${NC}"
else
    echo -e "${YELLOW}⚠️  Documentazione AI_AGENT.md mancante${NC}"
fi
echo ""

# 8. Verifica dipendenza llama-cpp-python
echo "8️⃣  Verifica dipendenza llama-cpp-python..."
if grep -q "llama-cpp-python" requirements.txt; then
    echo -e "${GREEN}✅ Dipendenza llama-cpp-python in requirements.txt${NC}"
else
    echo -e "${RED}❌ Dipendenza llama-cpp-python mancante${NC}"
    exit 1
fi
echo ""

# 9. Verifica variabile ambiente AI_MODEL_PATH
echo "9️⃣  Verifica configurazione modello..."
if grep -q "AI_MODEL_PATH" app/main.py; then
    echo -e "${GREEN}✅ Configurazione AI_MODEL_PATH presente${NC}"
    model_path=$(grep "AI_MODEL_PATH" app/main.py | head -n 1 | cut -d'"' -f2)
    echo -e "   Path di default: ${BLUE}${model_path}${NC}"
else
    echo -e "${YELLOW}⚠️  Configurazione AI_MODEL_PATH non trovata${NC}"
fi
echo ""

# 10. Statistiche finali
echo "=================================================="
echo "📊 Statistiche Integrazione"
echo "=================================================="
echo ""

main_py_lines=$(wc -l < app/main.py)
ai_agent_lines=$(wc -l < app/ai_agent.py)
total_agent_endpoints=$(grep -c "@app\.\(get\|post\).*agent" app/main.py || echo "0")

echo -e "📄 Righe main.py:             ${BLUE}${main_py_lines}${NC}"
echo -e "📄 Righe ai_agent.py:         ${BLUE}${ai_agent_lines}${NC}"
echo -e "🔌 Endpoint AI agent:         ${BLUE}${total_agent_endpoints}${NC}"
echo ""

# 11. Riepilogo
echo "=================================================="
echo "✅ INTEGRAZIONE AI AGENT COMPLETATA"
echo "=================================================="
echo ""
echo -e "${GREEN}Tutti i test sono passati!${NC}"
echo ""
echo -e "${YELLOW}📝 Prossimi passi:${NC}"
echo "   1. Scarica modello GGUF (es. qwen3-0.6b.gguf)"
echo "   2. Imposta AI_MODEL_PATH=models/qwen3-0.6b.gguf"
echo "   3. Avvia nodo: python3 app/main.py"
echo "   4. Testa endpoint: curl -X POST 'http://localhost:8001/agent/prompt?channel=test' -d '{\"prompt\":\"crea task test\"}'"
echo ""
echo -e "${BLUE}📖 Documentazione: docs/AI_AGENT.md${NC}"
echo ""
