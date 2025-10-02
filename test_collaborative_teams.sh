#!/bin/bash

# test_collaborative_teams.sh
# Script di test per il sistema di squadre collaborative e task compositi
#
# Questo script testa:
# 1. Creazione profili skills
# 2. Creazione task composito
# 3. Reclamo task (coordinatore)
# 4. Candidature membri
# 5. Accettazione membri
# 6. Formazione squadra e workspace
# 7. Completamento sub-tasks
# 8. Distribuzione rewards

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configurazione
PORT1=8001
PORT2=8002
PORT3=8003
BASE_URL_1="http://localhost:$PORT1"
BASE_URL_2="http://localhost:$PORT2"
BASE_URL_3="http://localhost:$PORT3"
CHANNEL="dev-teams"

# Contatori
TESTS_PASSED=0
TESTS_FAILED=0

# Funzioni di utilità
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${MAGENTA}[INFO]${NC} $1"
}

# Funzione per chiamare API
api_call() {
    local method=$1
    local url=$2
    local data=$3
    local expected_status=$4
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url")
    elif [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    fi
    
    body=$(echo "$response" | sed '$d')
    status=$(echo "$response" | tail -n1)
    
    if [ "$status" = "$expected_status" ]; then
        echo "$body"
        return 0
    else
        echo "ERROR: Expected status $expected_status, got $status"
        echo "Response: $body"
        return 1
    fi
}

# Verifica nodi
check_nodes() {
    print_header "Verifica Nodi in Esecuzione"
    
    for port in $PORT1 $PORT2 $PORT3; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "Nodo su porta $port raggiungibile"
        else
            print_error "Nodo su porta $port NON raggiungibile"
            echo "Esegui: docker-compose up -d"
            exit 1
        fi
    done
}

# Test 1: Creazione canale
test_create_channel() {
    print_header "Test 1: Creazione Canale"
    
    print_test "Creazione canale '$CHANNEL' su nodo 1..."
    result=$(api_call "POST" "$BASE_URL_1/channels/create" "{\"channel_name\": \"$CHANNEL\"}" "200")
    if echo "$result" | grep -q "channel_name"; then
        print_success "Canale creato su nodo 1"
    else
        print_error "Fallita creazione canale"
    fi
    
    sleep 2
    
    # Altri nodi si uniscono
    for port in $PORT2 $PORT3; do
        print_test "Nodo su porta $port si unisce al canale..."
        result=$(api_call "POST" "http://localhost:$port/channels/create" "{\"channel_name\": \"$CHANNEL\"}" "200")
        if echo "$result" | grep -q "channel_name"; then
            print_success "Nodo $port unito al canale"
        fi
    done
    
    sleep 2
}

# Test 2: Creazione profili skills
test_create_skills_profiles() {
    print_header "Test 2: Creazione Profili Skills"
    
    # Nodo 1: Alice (Backend)
    print_test "Creazione profilo Alice (Backend)..."
    result=$(api_call "POST" "$BASE_URL_1/skills/profile?channel=$CHANNEL" \
        '{"skills": ["python", "fastapi", "postgresql", "docker"], "bio": "Backend developer"}' \
        "200")
    if echo "$result" | grep -q "Profilo aggiornato"; then
        print_success "Profilo Alice creato"
    else
        print_error "Fallita creazione profilo Alice"
    fi
    
    # Nodo 2: Bob (Frontend)
    print_test "Creazione profilo Bob (Frontend)..."
    result=$(api_call "POST" "$BASE_URL_2/skills/profile?channel=$CHANNEL" \
        '{"skills": ["react", "typescript", "javascript", "css"], "bio": "Frontend developer"}' \
        "200")
    if echo "$result" | grep -q "Profilo aggiornato"; then
        print_success "Profilo Bob creato"
    else
        print_error "Fallita creazione profilo Bob"
    fi
    
    # Nodo 3: Carol (DevOps)
    print_test "Creazione profilo Carol (DevOps)..."
    result=$(api_call "POST" "$BASE_URL_3/skills/profile?channel=$CHANNEL" \
        '{"skills": ["docker", "kubernetes", "terraform", "ci/cd"], "bio": "DevOps engineer"}' \
        "200")
    if echo "$result" | grep -q "Profilo aggiornato"; then
        print_success "Profilo Carol creata"
    else
        print_error "Fallita creazione profilo Carol"
    fi
    
    sleep 1
}

# Test 3: Creazione task composito
test_create_composite_task() {
    print_header "Test 3: Creazione Task Composito"
    
    print_test "Creazione task 'Dashboard Analytics'..."
    
    task_data='{
        "title": "Dashboard Analytics Completa",
        "description": "Dashboard con backend, frontend e deployment",
        "max_team_size": 5,
        "coordinator_bonus": 100,
        "sub_tasks": [
            {
                "title": "Backend API",
                "description": "REST API con FastAPI e PostgreSQL",
                "required_skills": ["python", "fastapi", "postgresql"],
                "reward_points": 300
            },
            {
                "title": "Frontend Dashboard",
                "description": "UI React con grafici D3.js",
                "required_skills": ["react", "typescript", "d3.js"],
                "reward_points": 350
            },
            {
                "title": "DevOps & Deploy",
                "description": "CI/CD pipeline e deployment K8s",
                "required_skills": ["docker", "kubernetes", "ci/cd"],
                "reward_points": 250
            }
        ]
    }'
    
    result=$(api_call "POST" "$BASE_URL_1/tasks/composite/create?channel=$CHANNEL" "$task_data" "201")
    TASK_ID=$(echo "$result" | jq -r '.task_id')
    
    if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        print_success "Task composito creato: $TASK_ID"
        total_reward=$(echo "$result" | jq -r '.total_reward')
        print_info "Total reward: $total_reward SP"
    else
        print_error "Fallita creazione task composito"
        exit 1
    fi
    
    sleep 1
}

# Test 4: Reclamo task (coordinatore)
test_claim_task() {
    print_header "Test 4: Reclamo Task (Coordinatore)"
    
    print_test "Alice reclama task $TASK_ID..."
    result=$(api_call "POST" "$BASE_URL_1/tasks/composite/$TASK_ID/claim?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "coordinatore"; then
        print_success "Alice è diventata coordinatore"
        
        announcement_id=$(echo "$result" | jq -r '.announcement_id')
        print_info "Announcement ID: $announcement_id"
        
        # Mostra annuncio
        announcement=$(echo "$result" | jq -r '.announcement')
        echo "$announcement" | while read line; do
            print_info "$line"
        done
    else
        print_error "Fallito reclamo task"
    fi
    
    sleep 1
}

# Test 5: Candidature
test_apply_to_task() {
    print_header "Test 5: Candidature al Task"
    
    # Bob si candida
    print_test "Bob si candida per il task..."
    result=$(api_call "POST" "$BASE_URL_2/tasks/composite/$TASK_ID/apply?channel=$CHANNEL" \
        '{"message": "Esperto React con 5 anni di esperienza"}' \
        "200")
    
    if echo "$result" | grep -q "Candidatura inviata"; then
        skill_match=$(echo "$result" | jq -r '.skill_match')
        print_success "Bob candidato (skill match: $skill_match)"
    else
        print_error "Fallita candidatura Bob"
    fi
    
    sleep 1
    
    # Carol si candida
    print_test "Carol si candida per il task..."
    result=$(api_call "POST" "$BASE_URL_3/tasks/composite/$TASK_ID/apply?channel=$CHANNEL" \
        '{"message": "DevOps specialist con certificazioni K8s"}' \
        "200")
    
    if echo "$result" | grep -q "Candidatura inviata"; then
        skill_match=$(echo "$result" | jq -r '.skill_match')
        print_success "Carol candidata (skill match: $skill_match)"
    else
        print_error "Fallita candidatura Carol"
    fi
    
    sleep 1
}

# Test 6: Recupero dettagli task
test_get_task_details() {
    print_header "Test 6: Dettagli Task Composito"
    
    print_test "Recupero dettagli task $TASK_ID..."
    result=$(api_call "GET" "$BASE_URL_1/tasks/composite/$TASK_ID?channel=$CHANNEL" "" "200")
    
    status=$(echo "$result" | jq -r '.status')
    applicants_count=$(echo "$result" | jq '.applicants | length')
    
    print_info "Status: $status"
    print_info "Candidature ricevute: $applicants_count"
    
    if [ "$applicants_count" -eq 2 ]; then
        print_success "Candidature registrate correttamente"
    else
        print_error "Numero candidature errato: expected 2, got $applicants_count"
    fi
}

# Test 7: Accettazione membri
test_accept_members() {
    print_header "Test 7: Accettazione Membri"
    
    # Recupera NODE_IDs
    BOB_ID=$(curl -s "$BASE_URL_2/info" | jq -r '.node_id')
    CAROL_ID=$(curl -s "$BASE_URL_3/info" | jq -r '.node_id')
    
    # Alice accetta Bob
    print_test "Alice accetta Bob ($BOB_ID)..."
    result=$(api_call "POST" "$BASE_URL_1/tasks/composite/$TASK_ID/accept/$BOB_ID?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "accettato"; then
        team_size=$(echo "$result" | jq -r '.team_size')
        print_success "Bob accettato (team size: $team_size)"
    else
        print_error "Fallita accettazione Bob"
    fi
    
    sleep 1
    
    # Alice accetta Carol
    print_test "Alice accetta Carol ($CAROL_ID)..."
    result=$(api_call "POST" "$BASE_URL_1/tasks/composite/$TASK_ID/accept/$CAROL_ID?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "accettato"; then
        team_size=$(echo "$result" | jq -r '.team_size')
        team_complete=$(echo "$result" | jq -r '.team_complete')
        
        print_success "Carol accettata (team size: $team_size)"
        
        if [ "$team_complete" = "true" ]; then
            workspace=$(echo "$result" | jq -r '.workspace_channel')
            print_success "Squadra completa! Workspace: $workspace"
            WORKSPACE_CHANNEL=$workspace
        fi
    else
        print_error "Fallita accettazione Carol"
    fi
    
    sleep 2
}

# Test 8: Verifica workspace creato
test_workspace_created() {
    print_header "Test 8: Verifica Workspace Creato"
    
    print_test "Verifica esistenza workspace $WORKSPACE_CHANNEL..."
    result=$(api_call "GET" "$BASE_URL_1/state?channel=$WORKSPACE_CHANNEL" "" "200")
    
    if echo "$result" | grep -q "is_temporary"; then
        print_success "Workspace temporaneo creato correttamente"
        
        participants=$(echo "$result" | jq -r '.participants | length')
        print_info "Partecipanti: $participants"
    else
        print_error "Workspace non trovato"
    fi
}

# Test 9: Completamento sub-tasks
test_complete_subtasks() {
    print_header "Test 9: Completamento Sub-Tasks"
    
    # Recupera task per ottenere sub-task IDs
    result=$(api_call "GET" "$BASE_URL_1/tasks/composite/$TASK_ID?channel=$CHANNEL" "" "200")
    
    # Estrai sub-task IDs
    SUBTASK_1=$(echo "$result" | jq -r '.sub_tasks[0].sub_task_id')
    SUBTASK_2=$(echo "$result" | jq -r '.sub_tasks[1].sub_task_id')
    SUBTASK_3=$(echo "$result" | jq -r '.sub_tasks[2].sub_task_id')
    
    print_info "Sub-task 1 (Backend): $SUBTASK_1"
    print_info "Sub-task 2 (Frontend): $SUBTASK_2"
    print_info "Sub-task 3 (DevOps): $SUBTASK_3"
    
    # Alice completa sub-task 1
    print_test "Alice completa Backend API..."
    result=$(api_call "POST" "$BASE_URL_1/tasks/composite/$TASK_ID/subtask/$SUBTASK_1/complete?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "completato"; then
        print_success "Sub-task 1 completato"
    else
        print_error "Fallito completamento sub-task 1"
    fi
    
    sleep 1
    
    # Bob completa sub-task 2
    print_test "Bob completa Frontend Dashboard..."
    result=$(api_call "POST" "$BASE_URL_2/tasks/composite/$TASK_ID/subtask/$SUBTASK_2/complete?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "completato"; then
        print_success "Sub-task 2 completato"
    else
        print_error "Fallito completamento sub-task 2"
    fi
    
    sleep 1
    
    # Carol completa sub-task 3 (ultimo)
    print_test "Carol completa DevOps & Deploy (ultimo sub-task)..."
    result=$(api_call "POST" "$BASE_URL_3/tasks/composite/$TASK_ID/subtask/$SUBTASK_3/complete?channel=$CHANNEL" "" "200")
    
    if echo "$result" | grep -q "completato"; then
        all_completed=$(echo "$result" | jq -r '.all_completed')
        
        if [ "$all_completed" = "true" ]; then
            print_success "Tutti sub-tasks completati!"
            
            # Verifica rewards distribuiti
            if echo "$result" | jq -e '.rewards_distributed' > /dev/null; then
                print_success "Rewards distribuiti automaticamente"
                
                # Mostra rewards
                echo "$result" | jq -r '.rewards_distributed | to_entries[] | "  \(.key): +\(.value) SP"' | while read line; do
                    print_info "$line"
                done
            fi
        else
            print_error "Task non marcato come completato"
        fi
    else
        print_error "Fallito completamento sub-task 3"
    fi
    
    sleep 2
}

# Test 10: Verifica stato finale
test_final_state() {
    print_header "Test 10: Verifica Stato Finale"
    
    print_test "Recupero stato finale task $TASK_ID..."
    result=$(api_call "GET" "$BASE_URL_1/tasks/composite/$TASK_ID?channel=$CHANNEL" "" "200")
    
    status=$(echo "$result" | jq -r '.status')
    completed_at=$(echo "$result" | jq -r '.completed_at')
    
    print_info "Status: $status"
    print_info "Completato: $completed_at"
    
    if [ "$status" = "completed" ]; then
        print_success "Task completato correttamente"
    else
        print_error "Status finale errato: $status"
    fi
    
    # Verifica sub-tasks
    all_completed=true
    for i in 0 1 2; do
        st_status=$(echo "$result" | jq -r ".sub_tasks[$i].status")
        if [ "$st_status" != "completed" ]; then
            all_completed=false
        fi
    done
    
    if [ "$all_completed" = "true" ]; then
        print_success "Tutti sub-tasks marcati come completati"
    else
        print_error "Alcuni sub-tasks non completati"
    fi
}

# Test 11: Lista task compositi
test_list_composite_tasks() {
    print_header "Test 11: Lista Task Compositi"
    
    print_test "Lista tutti task compositi..."
    result=$(api_call "GET" "$BASE_URL_1/tasks/composite?channel=$CHANNEL" "" "200")
    
    total_tasks=$(echo "$result" | jq -r '.total_tasks')
    print_info "Total tasks: $total_tasks"
    
    if [ "$total_tasks" -ge 1 ]; then
        print_success "Lista task recuperata"
    else
        print_error "Nessun task trovato"
    fi
    
    # Filtra per status
    print_test "Filtra task completati..."
    result=$(api_call "GET" "$BASE_URL_1/tasks/composite?channel=$CHANNEL&status=completed" "" "200")
    
    completed_count=$(echo "$result" | jq -r '.total_tasks')
    if [ "$completed_count" -ge 1 ]; then
        print_success "Task completati: $completed_count"
    fi
}

# Cleanup
cleanup() {
    print_header "Cleanup"
    print_info "Test completato, nessun cleanup necessario"
}

# Report finale
print_report() {
    print_header "REPORT FINALE"
    
    total_tests=$((TESTS_PASSED + TESTS_FAILED))
    
    echo -e "${GREEN}Test Passati: $TESTS_PASSED${NC}"
    echo -e "${RED}Test Falliti: $TESTS_FAILED${NC}"
    echo -e "Totale Test: $total_tests"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}✓ TUTTI I TEST SONO PASSATI!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}✗ ALCUNI TEST SONO FALLITI${NC}\n"
        exit 1
    fi
}

# Main execution
main() {
    print_header "Test Suite: Collaborative Teams System"
    echo "Data: $(date)"
    echo "Canale: $CHANNEL"
    
    check_nodes
    test_create_channel
    test_create_skills_profiles
    test_create_composite_task
    test_claim_task
    test_apply_to_task
    test_get_task_details
    test_accept_members
    test_workspace_created
    test_complete_subtasks
    test_final_state
    test_list_composite_tasks
    
    cleanup
    print_report
}

# Trap per cleanup
trap cleanup EXIT

# Esegui test
main
