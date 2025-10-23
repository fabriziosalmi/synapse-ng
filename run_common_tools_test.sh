#!/usr/bin/env bash

# ========================================
# Test Runner Helper: Common Tools
# ========================================
# Script per eseguire scenari specifici durante lo sviluppo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT="$SCRIPT_DIR/test_common_tools_experiment.sh"

# Colori
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_usage() {
    cat << EOF
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${BLUE}  Test Runner Helper: Common Tools${NC}
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${GREEN}Usage:${NC}
  $0 [command] [options]

${GREEN}Commands:${NC}
  all                 Esegue tutti gli scenari (default)
  quick               Esegue solo scenari critici (S1-S4, S6)
  security            Esegue solo test di sicurezza (S3)
  economic            Esegui solo test economici (S1, S2)
  s1                  Esegui solo Scenario 1 (Insufficient Funds)
  s2                  Esegui solo Scenario 2 (Successful Acquisition)
  s3                  Esegui solo Scenario 3 (Unauthorized Usage)
  s4                  Esegui solo Scenario 4 (Authorized Usage)
  s5                  Esegui solo Scenario 5 (Monthly Payments)
  s6                  Esegui solo Scenario 6 (Tool Deprecation)
  list                Lista tutti gli scenari disponibili
  help                Mostra questo help

${GREEN}Options:${NC}
  CHANNEL=<name>      Usa canale specifico (default: sviluppo_ui)
  DEBUG=1             Abilita debug mode (set -x)

${GREEN}Examples:${NC}
  $0 quick
  $0 s3
  $0 security
  CHANNEL=ricerca_ia $0 all
  DEBUG=1 $0 s2

EOF
}

list_scenarios() {
    cat << EOF
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
${BLUE}  Scenari Disponibili${NC}
${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

${GREEN}S1: Insufficient Funds${NC} (🔴 Critical)
    Verifica rifiuto acquisizione con fondi insufficienti
    
${GREEN}S2: Successful Acquisition${NC} (🔴 Critical)
    Ciclo completo acquisizione tool con governance
    
${GREEN}S3: Unauthorized Usage${NC} (🔴 Critical)
    Test sicurezza: accesso non autorizzato a tools
    - Tool non richiesto dal task
    - Chiamante non è assignee
    - Task completato
    
${GREEN}S4: Authorized Usage${NC} (🟡 High)
    Happy path: esecuzione tool con tutte le autorizzazioni
    
${GREEN}S5: Monthly Payments${NC} (🟢 Medium, ⚠️ Optional)
    Verifica pagamenti mensili automatici (35+ secondi)
    
${GREEN}S6: Tool Deprecation${NC} (🟡 High)
    Deprecazione tool attraverso governance

EOF
}

# Estrae e modifica il test script per eseguire solo scenari specifici
run_scenarios() {
    local scenarios="$1"
    
    # Crea script temporaneo
    TEMP_SCRIPT=$(mktemp /tmp/common_tools_test_XXXXXX.sh)
    
    # Copia header e setup
    sed -n '1,/^main() {/p' "$TEST_SCRIPT" > "$TEMP_SCRIPT"
    
    # Aggiungi main personalizzato
    cat >> "$TEMP_SCRIPT" << EOF
    setup
    
    $scenarios
    
    print_report
}

# Esegui main
main "\$@"
EOF
    
    # Esegui script temporaneo
    chmod +x "$TEMP_SCRIPT"
    
    if [[ -n "${DEBUG}" ]]; then
        set -x
    fi
    
    "$TEMP_SCRIPT"
    EXIT_CODE=$?
    
    # Cleanup
    rm "$TEMP_SCRIPT"
    
    exit $EXIT_CODE
}

# Parse command
COMMAND="${1:-all}"

case "$COMMAND" in
    help|-h|--help)
        print_usage
        exit 0
        ;;
    
    list)
        list_scenarios
        exit 0
        ;;
    
    all)
        echo -e "${GREEN}Esecuzione TUTTI gli scenari${NC}"
        bash "$TEST_SCRIPT"
        ;;
    
    quick)
        echo -e "${GREEN}Esecuzione scenari critici (S1-S4, S6)${NC}"
        run_scenarios "
            test_acquisition_insufficient_funds
            test_acquisition_success
            test_unauthorized_tool_usage
            test_authorized_tool_usage
            test_tool_deprecation
        "
        ;;
    
    security)
        echo -e "${GREEN}Esecuzione test di sicurezza (S3)${NC}"
        echo -e "${YELLOW}NOTA: Richiede tool acquisito. Eseguo anche S2...${NC}"
        run_scenarios "
            test_acquisition_success
            test_unauthorized_tool_usage
        "
        ;;
    
    economic)
        echo -e "${GREEN}Esecuzione test economici (S1, S2)${NC}"
        run_scenarios "
            test_acquisition_insufficient_funds
            test_acquisition_success
        "
        ;;
    
    s1)
        echo -e "${GREEN}Esecuzione Scenario 1: Insufficient Funds${NC}"
        run_scenarios "test_acquisition_insufficient_funds"
        ;;
    
    s2)
        echo -e "${GREEN}Esecuzione Scenario 2: Successful Acquisition${NC}"
        run_scenarios "test_acquisition_success"
        ;;
    
    s3)
        echo -e "${GREEN}Esecuzione Scenario 3: Unauthorized Usage${NC}"
        echo -e "${YELLOW}NOTA: Richiede tool acquisito. Eseguo anche S2...${NC}"
        run_scenarios "
            test_acquisition_success
            test_unauthorized_tool_usage
        "
        ;;
    
    s4)
        echo -e "${GREEN}Esecuzione Scenario 4: Authorized Usage${NC}"
        echo -e "${YELLOW}NOTA: Richiede tool e task. Eseguo anche S2 e S3...${NC}"
        run_scenarios "
            test_acquisition_success
            test_unauthorized_tool_usage
            test_authorized_tool_usage
        "
        ;;
    
    s5)
        echo -e "${GREEN}Esecuzione Scenario 5: Monthly Payments${NC}"
        echo -e "${YELLOW}⚠️  ATTENZIONE: Richiede 35+ secondi di attesa${NC}"
        echo -e "${YELLOW}NOTA: Richiede tool acquisito. Eseguo anche S2...${NC}"
        
        # Crea script con S5 abilitato
        TEMP_SCRIPT=$(mktemp /tmp/common_tools_test_XXXXXX.sh)
        
        # Copia tutto tranne main
        sed -n '1,/^main() {/p' "$TEST_SCRIPT" > "$TEMP_SCRIPT"
        
        # Main con S5
        cat >> "$TEMP_SCRIPT" << 'EOF'
    setup
    test_acquisition_success
    test_monthly_payments
    print_report
}

main "$@"
EOF
        
        chmod +x "$TEMP_SCRIPT"
        "$TEMP_SCRIPT"
        EXIT_CODE=$?
        rm "$TEMP_SCRIPT"
        exit $EXIT_CODE
        ;;
    
    s6)
        echo -e "${GREEN}Esecuzione Scenario 6: Tool Deprecation${NC}"
        echo -e "${YELLOW}NOTA: Richiede tool acquisito. Eseguo anche S2...${NC}"
        run_scenarios "
            test_acquisition_success
            test_tool_deprecation
        "
        ;;
    
    *)
        echo -e "${YELLOW}Comando non riconosciuto: $COMMAND${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac
