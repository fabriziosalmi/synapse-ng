#!/bin/bash

# Script di test avanzato per Synapse-NG
# Simula topologia complessa: Docker bridge + Docker host + nodi standalone

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   ███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗║
║   ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝║
║   ███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗║
║   ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║║
║   ███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝║
║                    Next Generation                    ║
║              Advanced Network Testing                 ║
╚═══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Funzione per cleanup completo
cleanup() {
    echo -e "\n${YELLOW}🧹 Pulizia ambiente...${NC}"
    docker-compose -f docker-compose.yml down 2>/dev/null || true
    docker-compose -f docker-compose.wan.yml down 2>/dev/null || true
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    rm -rf /tmp/synapse-test-* 2>/dev/null || true
    echo -e "${GREEN}✓ Ambiente pulito${NC}"
}

trap cleanup EXIT

# Verifica prerequisiti
check_requirements() {
    echo -e "${BLUE}🔍 Verifica prerequisiti...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker non trovato${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ docker-compose non trovato${NC}"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠ jq non trovato. Installa con: brew install jq${NC}"
        echo -e "${YELLOW}  Alcuni check saranno limitati${NC}"
    fi

    echo -e "${GREEN}✓ Prerequisiti OK${NC}\n"
}

# Scenario 1: Classic Docker Bridge Network
scenario_docker_bridge() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}SCENARIO 1: Docker Bridge Network (LAN simulata)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}📦 Caratteristiche:${NC}"
    echo -e "  • 3 nodi in rete privata Docker"
    echo -e "  • DNS interno: node-1, node-2, node-3"
    echo -e "  • PEERS statico configurato"
    echo -e "  • mDNS disabilitato (non funziona cross-container)\n"

    echo -e "${YELLOW}🚀 Avvio nodi...${NC}"
    docker-compose up --build -d

    echo -e "${YELLOW}⏳ Attendo convergenza (15s)...${NC}"
    for i in {15..1}; do
        echo -ne "${YELLOW}\r  ⏱  $i secondi...${NC}"
        sleep 1
    done
    echo -e "\n"

    echo -e "${GREEN}📊 Stato della rete:${NC}"
    for port in 8001 8002 8003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state | jq '. | length' 2>/dev/null || echo "?")
            echo -e "  🔵 Node :$port → ${GREEN}$count nodi${NC} visibili"
        else
            echo -e "  🔵 Node :$port → http://localhost:$port/state"
        fi
    done

    echo -e "\n${GREEN}✓ Bridge network attivo${NC}"
    echo -e "${CYAN}🌐 Apri browser:${NC}"
    echo -e "   • http://localhost:8001"
    echo -e "   • http://localhost:8002"
    echo -e "   • http://localhost:8003"
}

# Scenario 2: Docker Host Network (WAN simulata)
scenario_docker_host() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}SCENARIO 2: Docker Host Network (WAN simulata)${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}📦 Caratteristiche:${NC}"
    echo -e "  • 3 nodi con network_mode: host"
    echo -e "  • Simulano macchine separate su Internet"
    echo -e "  • mDNS abilitato (funziona su host network!)"
    echo -e "  • Peer bootstrap: localhost:7001\n"

    echo -e "${YELLOW}🚀 Avvio nodi WAN...${NC}"
    docker-compose -f docker-compose.wan.yml up --build -d

    echo -e "${YELLOW}⏳ Attendo discovery mDNS (15s)...${NC}"
    for i in {15..1}; do
        echo -ne "${YELLOW}\r  ⏱  $i secondi...${NC}"
        sleep 1
    done
    echo -e "\n"

    echo -e "${GREEN}📊 Stato della rete WAN:${NC}"
    for port in 7001 7002 7003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "?")
            echo -e "  🌍 WAN Node :$port → ${GREEN}$count nodi${NC} visibili"
        else
            echo -e "  🌍 WAN Node :$port → http://localhost:$port/state"
        fi
    done

    echo -e "\n${YELLOW}🔍 Verifica mDNS discovery nei log:${NC}"
    sleep 2
    if docker logs synapse-wan-2 2>&1 | grep -q "Nodo scoperto via mDNS"; then
        echo -e "  ${GREEN}✓ mDNS discovery funzionante!${NC}"
    else
        echo -e "  ${YELLOW}⚠ mDNS discovery non rilevato (potrebbe richiedere più tempo)${NC}"
    fi

    echo -e "\n${GREEN}✓ Host network attivo${NC}"
    echo -e "${CYAN}🌐 Apri browser:${NC}"
    echo -e "   • http://localhost:7001"
    echo -e "   • http://localhost:7002"
    echo -e "   • http://localhost:7003"
}

# Scenario 3: Topologia ibrida completa
scenario_hybrid() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}SCENARIO 3: Topologia Ibrida Multi-Layer${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}📦 Architettura:${NC}"
    echo -e "  ${BLUE}Layer 1${NC}: Docker Bridge (3 nodi privati)"
    echo -e "  ${MAGENTA}Layer 2${NC}: Docker Host (3 nodi 'WAN')"
    echo -e "  ${GREEN}Bridge${NC}: Nodo che connette entrambi i layer\n"

    # Avvia entrambe le reti
    echo -e "${YELLOW}🚀 Avvio Layer 1 (Bridge)...${NC}"
    docker-compose up --build -d
    sleep 8

    echo -e "${YELLOW}🚀 Avvio Layer 2 (Host/WAN)...${NC}"
    docker-compose -f docker-compose.wan.yml up --build -d
    sleep 8

    # Avvia bridge node
    echo -e "${YELLOW}🌉 Avvio Bridge Node (porta 6000)...${NC}"
    NODE_PORT=6000 \
        PEERS="http://localhost:8001,http://localhost:7001" \
        ENABLE_MDNS=true \
        uvicorn app.main:app --host 0.0.0.0 --port 6000 \
        > /tmp/synapse-bridge-node.log 2>&1 &
    BRIDGE_PID=$!

    echo -e "${YELLOW}⏳ Attendo convergenza completa (20s)...${NC}"
    for i in {20..1}; do
        echo -ne "${YELLOW}\r  ⏱  $i secondi...${NC}"
        sleep 1
    done
    echo -e "\n"

    echo -e "${GREEN}📊 Mappa della rete unificata:${NC}\n"

    echo -e "${BLUE}  Layer 1 - Bridge Network:${NC}"
    for port in 8001 8002 8003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "?")
            echo -e "    🔵 :$port → ${count} nodi"
        fi
    done

    echo -e "\n${MAGENTA}  Layer 2 - Host Network (WAN):${NC}"
    for port in 7001 7002 7003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "?")
            echo -e "    🌍 :$port → ${count} nodi"
        fi
    done

    if command -v jq &> /dev/null; then
        bridge_count=$(curl -s http://localhost:6000/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
        echo -e "\n${GREEN}  🌉 Bridge Node :6000 → ${bridge_count} nodi totali${NC}"

        if [[ "$bridge_count" =~ ^[0-9]+$ ]] && [ "$bridge_count" -gt 5 ]; then
            echo -e "\n${GREEN}✨ SUCCESS! Tutti i layer comunicano!${NC}"
            echo -e "${GREEN}   L'organismo è vivo e completamente connesso.${NC}"
        else
            echo -e "\n${YELLOW}⚠ Convergenza parziale (attendi o verifica connessioni)${NC}"
        fi
    fi

    echo -e "\n${CYAN}🌐 Visualizza tutti i nodi:${NC}"
    echo -e "   Bridge: http://localhost:6000 ${GREEN}← Vedi tutto qui!${NC}"
    echo -e "   Layer1: http://localhost:8001-8003"
    echo -e "   Layer2: http://localhost:7001-7003"

    echo -e "\n${CYAN}📜 Log del bridge node:${NC}"
    echo -e "   tail -f /tmp/synapse-bridge-node.log"
}

# Scenario 4: Resilience test
scenario_resilience() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}SCENARIO 4: Test di Resilienza${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}🔥 Simulazione fallimenti di rete...${NC}\n"

    # Assumiamo che scenario 1 sia già attivo
    echo -e "${RED}💥 Killing node-2...${NC}"
    docker-compose stop node-2

    echo -e "${YELLOW}⏳ Attendo 35 secondi (timeout nodi morti = 30s)...${NC}"
    sleep 35

    echo -e "\n${GREEN}📊 Stato dopo fallimento:${NC}"
    for port in 8001 8003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "?")
            echo -e "  Node :$port → ${count} nodi (dovrebbe essere 2)"
        fi
    done

    echo -e "\n${GREEN}🔄 Riavvio node-2...${NC}"
    docker-compose start node-2

    echo -e "${YELLOW}⏳ Attendo re-join (10s)...${NC}"
    sleep 10

    echo -e "\n${GREEN}📊 Stato dopo recovery:${NC}"
    for port in 8001 8002 8003; do
        if command -v jq &> /dev/null; then
            count=$(curl -s http://localhost:$port/state 2>/dev/null | jq '. | length' 2>/dev/null || echo "?")
            echo -e "  Node :$port → ${count} nodi (dovrebbe essere 3)"
        fi
    done

    echo -e "\n${GREEN}✓ Test resilienza completato${NC}"
}

# Menu principale
show_menu() {
    echo -e "\n${YELLOW}╔════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  Scegli scenario di test:             ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════╝${NC}"
    echo -e "  ${BLUE}1)${NC} Docker Bridge (classico, 3 nodi)"
    echo -e "  ${MAGENTA}2)${NC} Docker Host Network (WAN simulata)"
    echo -e "  ${GREEN}3)${NC} Hybrid Multi-Layer (Bridge + WAN + Gateway)"
    echo -e "  ${RED}4)${NC} Resilience Test (fallimenti e recovery)"
    echo -e "  ${CYAN}5)${NC} Run All (sequenziale)"
    echo -e "  ${YELLOW}q)${NC} Quit"
    echo -e -n "\n${BLUE}➜ Scelta: ${NC}"
}

# Main
check_requirements

if [ "$1" == "1" ] || [ "$1" == "bridge" ]; then
    scenario_docker_bridge
    echo -e "\n${GREEN}✓ Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
elif [ "$1" == "2" ] || [ "$1" == "wan" ]; then
    scenario_docker_host
    echo -e "\n${GREEN}✓ Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
elif [ "$1" == "3" ] || [ "$1" == "hybrid" ]; then
    scenario_hybrid
    echo -e "\n${GREEN}✓ Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
elif [ "$1" == "4" ] || [ "$1" == "resilience" ]; then
    scenario_docker_bridge
    sleep 5
    scenario_resilience
    echo -e "\n${GREEN}✓ Test completato${NC}"
elif [ "$1" == "all" ]; then
    scenario_docker_bridge
    read -p $'\n\033[0;33mPremi INVIO per scenario WAN...\033[0m'
    cleanup
    scenario_docker_host
    read -p $'\n\033[0;33mPremi INVIO per scenario Hybrid...\033[0m'
    cleanup
    scenario_hybrid
    echo -e "\n${GREEN}✓ Tutti gli scenari completati. Premi Ctrl+C per uscire${NC}"
    tail -f /dev/null
else
    # Menu interattivo
    while true; do
        show_menu
        read choice
        case $choice in
            1)
                cleanup
                scenario_docker_bridge
                ;;
            2)
                cleanup
                scenario_docker_host
                ;;
            3)
                cleanup
                scenario_hybrid
                ;;
            4)
                scenario_resilience
                ;;
            5)
                scenario_docker_bridge
                read -p $'\n\033[0;33mContinua con WAN? [Y/n]\033[0m ' ans
                if [[ $ans != "n" ]]; then
                    cleanup
                    scenario_docker_host
                    read -p $'\n\033[0;33mContinua con Hybrid? [Y/n]\033[0m ' ans
                    if [[ $ans != "n" ]]; then
                        cleanup
                        scenario_hybrid
                    fi
                fi
                echo -e "\n${GREEN}✓ Test completati. Premi Ctrl+C per uscire${NC}"
                tail -f /dev/null
                ;;
            q|Q)
                echo -e "${GREEN}Arrivederci! 👋${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Scelta non valida${NC}"
                ;;
        esac
    done
fi
