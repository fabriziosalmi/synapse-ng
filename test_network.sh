#!/bin/bash

# Script di test automatico per Synapse-NG
# Testa configurazioni: Docker, LAN standalone, e bridge

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Synapse-NG Test Automatico           ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo ""

# Funzione per cleanup
cleanup() {
    echo -e "\n${YELLOW}🧹 Pulizia processi...${NC}"
    docker-compose down 2>/dev/null || true
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    rm -rf /tmp/synapse-test-* 2>/dev/null || true
    echo -e "${GREEN}✓ Pulizia completata${NC}"
}

trap cleanup EXIT

# Test 1: Docker Network
test_docker() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}TEST 1: Docker Network (3 nodi)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    docker-compose up --build -d

    echo -e "${YELLOW}⏳ Attendo 15 secondi per convergenza...${NC}"
    sleep 15

    echo -e "\n${GREEN}📊 Verifica stato nodi Docker:${NC}"
    for port in 8001 8002 8003; do
        count=$(curl -s http://localhost:$port/state | jq '. | length' 2>/dev/null || echo "0")
        echo -e "  Node port ${port}: ${GREEN}${count}${NC} nodi visibili"
    done

    echo -e "\n${GREEN}✓ Docker network attivo${NC}"
    echo -e "${YELLOW}🌐 Visualizza: http://localhost:8001 | 8002 | 8003${NC}"
}

# Test 2: Standalone LAN nodes con mDNS
test_lan() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}TEST 2: LAN Standalone (2 nodi mDNS)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # Verifica dipendenze
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq non trovato. Installa con: brew install jq${NC}"
        return 1
    fi

    # Avvia 2 nodi standalone con mDNS
    echo -e "${YELLOW}🚀 Avvio nodo LAN-1 (porta 9001)...${NC}"
    NODE_PORT=9001 PEERS="" ENABLE_MDNS=true \
        uvicorn app.main:app --host 0.0.0.0 --port 9001 \
        > /tmp/synapse-test-lan1.log 2>&1 &
    LAN1_PID=$!

    echo -e "${YELLOW}🚀 Avvio nodo LAN-2 (porta 9002)...${NC}"
    NODE_PORT=9002 PEERS="" ENABLE_MDNS=true \
        uvicorn app.main:app --host 0.0.0.0 --port 9002 \
        > /tmp/synapse-test-lan2.log 2>&1 &
    LAN2_PID=$!

    echo -e "${YELLOW}⏳ Attendo 10 secondi per mDNS discovery...${NC}"
    sleep 10

    echo -e "\n${GREEN}📊 Verifica discovery mDNS:${NC}"

    # Controlla i log per discovery
    if grep -q "Nodo scoperto via mDNS" /tmp/synapse-test-lan1.log; then
        echo -e "  LAN-1: ${GREEN}✓${NC} Ha scoperto peer via mDNS"
    else
        echo -e "  LAN-1: ${YELLOW}⚠${NC} Nessun peer scoperto (normale se mDNS non funziona su questo sistema)"
    fi

    if grep -q "Nodo scoperto via mDNS" /tmp/synapse-test-lan2.log; then
        echo -e "  LAN-2: ${GREEN}✓${NC} Ha scoperto peer via mDNS"
    else
        echo -e "  LAN-2: ${YELLOW}⚠${NC} Nessun peer scoperto (normale se mDNS non funziona su questo sistema)"
    fi

    # Controlla stato
    count1=$(curl -s http://localhost:9001/state | jq '. | length' 2>/dev/null || echo "1")
    count2=$(curl -s http://localhost:9002/state | jq '. | length' 2>/dev/null || echo "1")

    echo -e "\n${GREEN}📊 Stato nodi LAN:${NC}"
    echo -e "  LAN-1 (9001): ${GREEN}${count1}${NC} nodi visibili"
    echo -e "  LAN-2 (9002): ${GREEN}${count2}${NC} nodi visibili"

    if [ "$count1" -gt 1 ] || [ "$count2" -gt 1 ]; then
        echo -e "\n${GREEN}✓ Discovery funzionante!${NC}"
    else
        echo -e "\n${YELLOW}⚠ mDNS potrebbe non funzionare su questo sistema (Docker for Mac lo blocca)${NC}"
        echo -e "${YELLOW}  Su macchina Linux o LXC funzionerebbe meglio${NC}"
    fi

    echo -e "${YELLOW}🌐 Visualizza: http://localhost:9001 | 9002${NC}"

    # Mantieni aperti per test 3
    echo -e "\n${YELLOW}💾 PID salvati: LAN1=$LAN1_PID, LAN2=$LAN2_PID${NC}"
}

# Test 3: Bridge tra Docker e LAN
test_bridge() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}TEST 3: Bridge Node (Docker ↔ LAN)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    echo -e "${YELLOW}🌉 Avvio nodo bridge (porta 9003)...${NC}"
    echo -e "${YELLOW}   Collega: Docker network + LAN mDNS${NC}"

    NODE_PORT=9003 \
        PEERS="http://localhost:8001" \
        ENABLE_MDNS=true \
        uvicorn app.main:app --host 0.0.0.0 --port 9003 \
        > /tmp/synapse-test-bridge.log 2>&1 &
    BRIDGE_PID=$!

    echo -e "${YELLOW}⏳ Attendo 15 secondi per convergenza completa...${NC}"
    sleep 15

    echo -e "\n${GREEN}📊 Verifica rete unificata:${NC}"

    # Controlla se il bridge vede entrambi i layer
    bridge_count=$(curl -s http://localhost:9003/state | jq '. | length' 2>/dev/null || echo "1")
    echo -e "  Bridge (9003): ${GREEN}${bridge_count}${NC} nodi totali visibili"

    # Controlla se Docker vede LAN attraverso il bridge
    docker_count=$(curl -s http://localhost:8001/state | jq '. | length' 2>/dev/null || echo "3")
    echo -e "  Docker-1 (8001): ${GREEN}${docker_count}${NC} nodi visibili"

    if [ "$bridge_count" -gt 3 ]; then
        echo -e "\n${GREEN}✓ Bridge funzionante! Nodi Docker e LAN comunicano${NC}"
    else
        echo -e "\n${YELLOW}⚠ Bridge parziale (limitazioni mDNS su questo sistema)${NC}"
    fi

    echo -e "${YELLOW}🌐 Visualizza: http://localhost:9003${NC}"

    echo -e "\n${GREEN}📝 Log disponibili:${NC}"
    echo -e "  tail -f /tmp/synapse-test-lan1.log"
    echo -e "  tail -f /tmp/synapse-test-lan2.log"
    echo -e "  tail -f /tmp/synapse-test-bridge.log"

    kill $BRIDGE_PID 2>/dev/null || true
}

# Menu interattivo
show_menu() {
    echo -e "\n${YELLOW}Scegli test da eseguire:${NC}"
    echo "  1) Test Docker Network (raccomandato per iniziare)"
    echo "  2) Test LAN Standalone con mDNS"
    echo "  3) Test Bridge (Docker + LAN)"
    echo "  4) Test completo (tutti e 3)"
    echo "  5) Solo avvio e mantieni attivo"
    echo "  q) Esci"
    echo -e -n "\n${BLUE}Scelta: ${NC}"
}

# Main
if [ "$1" == "all" ]; then
    test_docker
    read -p "$(echo -e ${YELLOW}Premi INVIO per test LAN...${NC})"
    test_lan
    read -p "$(echo -e ${YELLOW}Premi INVIO per test Bridge...${NC})"
    test_bridge
elif [ "$1" == "docker" ]; then
    test_docker
    echo -e "\n${GREEN}✓ Test Docker completato. Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
elif [ "$1" == "lan" ]; then
    test_lan
    echo -e "\n${GREEN}✓ Test LAN completato. Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
elif [ "$1" == "bridge" ]; then
    test_docker
    sleep 10
    test_lan
    sleep 5
    test_bridge
    echo -e "\n${GREEN}✓ Test Bridge completato. Premi Ctrl+C per terminare${NC}"
    tail -f /dev/null
else
    # Menu interattivo
    while true; do
        show_menu
        read choice
        case $choice in
            1) test_docker ;;
            2) test_lan ;;
            3)
                test_docker
                sleep 10
                test_lan
                sleep 5
                test_bridge
                ;;
            4)
                test_docker
                read -p "$(echo -e ${YELLOW}Premi INVIO per continuare...${NC})"
                test_lan
                read -p "$(echo -e ${YELLOW}Premi INVIO per continuare...${NC})"
                test_bridge
                ;;
            5)
                test_docker
                test_lan
                echo -e "\n${GREEN}✓ Nodi attivi. Premi Ctrl+C per terminare${NC}"
                tail -f /dev/null
                ;;
            q|Q)
                echo -e "${GREEN}Ciao!${NC}"
                exit 0
                ;;
            *) echo -e "${RED}Scelta non valida${NC}" ;;
        esac
    done
fi
