#!/bin/bash

# Helper Script per Contributori
# Semplifica i comandi comuni per partecipare a Synapse-NG

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

show_help() {
    cat << EOF
🧬 Synapse-NG Contributor Helper

Usage: ./contributor_helper.sh <command>

Commands:
  setup           - Setup inicial: clona repo e avvia nodi
  status          - Mostra stato dei nodi
  my-balance      - Mostra il tuo balance SP
  my-reputation   - Mostra la tua reputation
  list-tasks      - Lista task disponibili nel channel
  claim <task_id> - Reclama un task
  progress <id>   - Marca task come in progress
  complete <id>   - Completa task
  create-task     - Crea un nuovo task (interattivo)
  help            - Mostra questo help

Examples:
  ./contributor_helper.sh setup
  ./contributor_helper.sh my-balance
  ./contributor_helper.sh list-tasks dev_ui
  ./contributor_helper.sh claim abc123
  ./contributor_helper.sh complete abc123

Note: 
  - Default node: http://localhost:8002 (Node 2)
  - Default channel: dev_ui
  - Change with env vars: NODE_PORT=8001 CHANNEL=test ./contributor_helper.sh <cmd>
EOF
}

# Configuration
NODE_PORT=${NODE_PORT:-8002}
NODE_URL="http://localhost:$NODE_PORT"
CHANNEL=${CHANNEL:-dev_ui}

case "$1" in
    setup)
        print_header "Setup Synapse-NG"
        
        if [ ! -d ".git" ]; then
            print_info "Cloning repository..."
            git clone https://github.com/fabriziosalmi/synapse-ng.git
            cd synapse-ng
        fi
        
        print_info "Starting Docker containers..."
        docker-compose up -d
        
        print_info "Waiting 15s for network stabilization..."
        sleep 15
        
        print_success "Setup complete!"
        print_info "Run: ./contributor_helper.sh status"
        ;;
    
    status)
        print_header "Network Status"
        
        for port in 8001 8002 8003; do
            if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
                print_success "Node $port is online"
            else
                echo "✗ Node $port is offline"
            fi
        done
        ;;
    
    my-balance)
        print_header "Your Balance"
        
        MY_NODE_ID=$(curl -s "$NODE_URL/state" | jq -r '.global.nodes | keys[0]')
        BALANCE=$(curl -s "$NODE_URL/state" | jq ".global.nodes.\"$MY_NODE_ID\".balance // 1000")
        
        echo "Node ID: ${MY_NODE_ID:0:16}..."
        echo "Balance: $BALANCE SP"
        ;;
    
    my-reputation)
        print_header "Your Reputation"
        
        MY_NODE_ID=$(curl -s "$NODE_URL/state" | jq -r '.global.nodes | keys[0]')
        REP=$(curl -s "$NODE_URL/reputations" | jq ".\"$MY_NODE_ID\" // 0")
        
        echo "Node ID: ${MY_NODE_ID:0:16}..."
        echo "Reputation: $REP"
        ;;
    
    list-tasks)
        CHANNEL_ARG=${2:-$CHANNEL}
        print_header "Tasks in channel: $CHANNEL_ARG"
        
        curl -s "$NODE_URL/state" | jq ".${CHANNEL_ARG}.tasks // {} | to_entries | map({id: .key[0:16], title: .value.title, status: .value.status, reward: .value.reward})"
        ;;
    
    claim)
        if [ -z "$2" ]; then
            echo "Error: Task ID required"
            echo "Usage: ./contributor_helper.sh claim <task_id>"
            exit 1
        fi
        
        TASK_ID=$2
        print_header "Claiming Task: ${TASK_ID:0:16}..."
        
        curl -X POST "$NODE_URL/tasks/$TASK_ID/claim?channel=$CHANNEL"
        
        print_success "Task claimed!"
        print_info "Run: ./contributor_helper.sh progress $TASK_ID"
        ;;
    
    progress)
        if [ -z "$2" ]; then
            echo "Error: Task ID required"
            echo "Usage: ./contributor_helper.sh progress <task_id>"
            exit 1
        fi
        
        TASK_ID=$2
        print_header "Marking Task as In Progress: ${TASK_ID:0:16}..."
        
        curl -X POST "$NODE_URL/tasks/$TASK_ID/progress?channel=$CHANNEL"
        
        print_success "Task in progress!"
        print_info "When done, run: ./contributor_helper.sh complete $TASK_ID"
        ;;
    
    complete)
        if [ -z "$2" ]; then
            echo "Error: Task ID required"
            echo "Usage: ./contributor_helper.sh complete <task_id>"
            exit 1
        fi
        
        TASK_ID=$2
        print_header "Completing Task: ${TASK_ID:0:16}..."
        
        curl -X POST "$NODE_URL/tasks/$TASK_ID/complete?channel=$CHANNEL"
        
        print_success "Task completed!"
        print_info "Waiting 15s for reward propagation..."
        sleep 15
        
        print_header "Your New Balance & Reputation"
        $0 my-balance
        $0 my-reputation
        ;;
    
    create-task)
        print_header "Create New Task"
        
        read -p "Task title: " TITLE
        read -p "Task description: " DESC
        read -p "Reward (SP): " REWARD
        read -p "Channel [dev_ui]: " CHANNEL_INPUT
        CHANNEL_INPUT=${CHANNEL_INPUT:-dev_ui}
        
        curl -X POST "$NODE_URL/tasks?channel=$CHANNEL_INPUT" \
            -H "Content-Type: application/json" \
            -d "{\"title\": \"$TITLE\", \"description\": \"$DESC\", \"reward\": $REWARD}"
        
        print_success "Task created!"
        ;;
    
    help|--help|-h|"")
        show_help
        ;;
    
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
