# Sistema di Squadre Collaborative e Task Compositi

## 📋 Panoramica

Il sistema di **Collaborative Teams** permette alla rete Synapse-NG di formare automaticamente squadre temporanee specializzate per affrontare task complessi che richiedono competenze diverse. Questo abilita l'**auto-organizzazione emergente** simile alla formazione di "organi" specializzati in un organismo biologico.

**Data Implementazione**: 2025-10-02  
**Status**: ✅ Production-Ready

---

## 🎯 Caratteristiche Principali

✅ **Task Compositi**: Task divisi in sub-tasks con skills specifiche richieste  
✅ **Profili Skills**: Ogni nodo dichiara le proprie competenze  
✅ **Matching Automatico**: Algoritmo di skill matching per candidature  
✅ **Coordinatore**: Un nodo reclama il task e coordina la squadra  
✅ **Workspace Temporaneo**: Canale privato auto-creato per la collaborazione  
✅ **Distribuzione Rewards**: Reward automatici per coordinatore e membri  
✅ **Auto-Dissoluzione**: Il workspace si dissolve al completamento  

---

## 🏗️ Architettura

### Componenti Chiave

```
Task Composito
├── Coordinatore (1 nodo che ha reclamato il task)
├── Sub-Tasks (lista di micro-tasks)
│   ├── Sub-Task 1 → required_skills: ["python", "fastapi"]
│   ├── Sub-Task 2 → required_skills: ["react", "typescript"]
│   └── Sub-Task 3 → required_skills: ["docker", "kubernetes"]
├── Team Members (nodi selezionati dal coordinatore)
├── Workspace Channel (canale temporaneo privato)
└── Rewards (points distribuiti al completamento)
```

### Stati del Task Composito

```
open → forming_team → in_progress → completed
  ↓         ↓              ↓             ↓
Creato   Coordinatore   Squadra      Tutti sub-tasks
         reclamato      formata      completati
```

---

## 📊 Schema Dati

### TaskComposite

```json
{
  "task_id": "tc-abc12345",
  "title": "Implementare Dashboard Analytics",
  "description": "Dashboard completa con backend, frontend e deployment",
  "task_type": "composite",
  
  "sub_tasks": [
    {
      "sub_task_id": "st-xyz789",
      "title": "Backend API",
      "description": "Creare REST API con FastAPI",
      "required_skills": ["python", "fastapi", "postgresql"],
      "assigned_to": "node-alice",
      "status": "in_progress",
      "reward_points": 300
    }
  ],
  
  "coordinator": "node-alice",
  "team_members": ["node-bob", "node-carol"],
  "max_team_size": 5,
  "required_skills": ["python", "fastapi", "react", "docker"],
  
  "status": "in_progress",
  "workspace_channel": "team-tc-abc12345",
  
  "total_reward_points": 1000,
  "coordinator_bonus": 100,
  
  "applicants": [
    {
      "node_id": "node-dave",
      "skills": ["python", "django"],
      "skill_match": 50.0,
      "message": "Esperienza 5 anni",
      "timestamp": "2025-10-02T10:30:00Z"
    }
  ],
  
  "created_at": "2025-10-02T10:00:00Z",
  "team_formed_at": "2025-10-02T10:45:00Z",
  "started_at": "2025-10-02T10:45:00Z",
  "completed_at": null,
  "deadline": "2025-10-09T10:00:00Z",
  
  "created_by": "node-alice",
  "channel": "dev"
}
```

### NodeSkills (Profilo)

```json
{
  "node_id": "node-alice",
  "skills": ["python", "fastapi", "postgresql", "docker"],
  "skill_levels": {
    "python": 5,
    "fastapi": 4,
    "postgresql": 3,
    "docker": 4
  },
  "bio": "Backend developer con 5 anni di esperienza",
  "availability": "available",
  "completed_tasks": 42,
  "team_participations": 15,
  "coordinator_count": 7,
  "updated_at": "2025-10-02T10:00:00Z"
}
```

---

## 🔌 API Reference

### 1. Gestione Profilo Skills

#### Aggiorna Profilo
```http
POST /skills/profile?channel=dev
Content-Type: application/json

{
  "skills": ["python", "fastapi", "postgresql", "docker"],
  "bio": "Backend developer"
}
```

**Response**:
```json
{
  "message": "Profilo aggiornato",
  "node_id": "node-alice",
  "skills": ["python", "fastapi", "postgresql", "docker"],
  "bio": "Backend developer"
}
```

#### Recupera Profilo
```http
GET /skills/profile?channel=dev&node_id=node-alice
```

---

### 2. Creazione Task Composito

```http
POST /tasks/composite/create?channel=dev
Content-Type: application/json

{
  "title": "Dashboard Analytics",
  "description": "Dashboard completa con backend, frontend e deployment",
  "max_team_size": 5,
  "coordinator_bonus": 100,
  "sub_tasks": [
    {
      "title": "Backend API",
      "description": "REST API con FastAPI",
      "required_skills": ["python", "fastapi", "postgresql"],
      "reward_points": 300
    },
    {
      "title": "Frontend Dashboard",
      "description": "UI React con grafici",
      "required_skills": ["react", "typescript", "d3.js"],
      "reward_points": 350
    },
    {
      "title": "DevOps & Deploy",
      "description": "Setup CI/CD e deployment",
      "required_skills": ["docker", "kubernetes", "ci/cd"],
      "reward_points": 250
    }
  ]
}
```

**Response**:
```json
{
  "message": "✅ Task composito creato",
  "task_id": "tc-abc12345",
  "title": "Dashboard Analytics",
  "sub_tasks_count": 3,
  "required_skills": ["python", "fastapi", "postgresql", "react", "typescript", "d3.js", "docker", "kubernetes", "ci/cd"],
  "total_reward": 1000,
  "status": "open"
}
```

---

### 3. Reclama Task (Diventa Coordinatore)

```http
POST /tasks/composite/tc-abc12345/claim?channel=dev
```

**Response**:
```json
{
  "message": "✅ Sei diventato coordinatore!",
  "task_id": "tc-abc12345",
  "coordinator": "node-alice",
  "status": "forming_team",
  "announcement_id": "ann-xyz789",
  "announcement": "🔍 Cerco 4 membri per task composito!\n\n📋 Task: Dashboard Analytics\n🎯 Skills richieste: python, fastapi, react, docker, kubernetes\n💰 Reward totale: 1000 SP\n👥 Posti disponibili: 4\n\nCandidati con: POST /tasks/composite/tc-abc12345/apply"
}
```

---

### 4. Candidatura per Task

```http
POST /tasks/composite/tc-abc12345/apply?channel=dev
Content-Type: application/json

{
  "message": "Ho 5 anni di esperienza con React e TypeScript"
}
```

**Response**:
```json
{
  "message": "✅ Candidatura inviata!",
  "task_id": "tc-abc12345",
  "applicant": "node-bob",
  "skill_match": "66.7%",
  "skills": ["react", "typescript", "javascript", "css"]
}
```

---

### 5. Accetta Membro (Solo Coordinatore)

```http
POST /tasks/composite/tc-abc12345/accept/node-bob?channel=dev
```

**Response**:
```json
{
  "message": "✅ Membro node-bob accettato!",
  "task_id": "tc-abc12345",
  "new_member": "node-bob",
  "team_size": 2,
  "team_complete": false
}
```

**Quando la squadra è completa**:
```json
{
  "message": "✅ Membro node-carol accettato!",
  "task_id": "tc-abc12345",
  "new_member": "node-carol",
  "team_size": 3,
  "team_complete": true,
  "workspace_channel": "team-tc-abc12345",
  "status": "in_progress"
}
```

---

### 6. Completa Sub-Task

```http
POST /tasks/composite/tc-abc12345/subtask/st-xyz789/complete?channel=dev
```

**Response** (sub-task completato):
```json
{
  "message": "✅ Sub-task completato!",
  "task_id": "tc-abc12345",
  "subtask_id": "st-xyz789",
  "all_completed": false
}
```

**Response** (tutti sub-tasks completati):
```json
{
  "message": "✅ Sub-task completato!",
  "task_id": "tc-abc12345",
  "subtask_id": "st-def456",
  "all_completed": true,
  "task_status": "completed",
  "rewards_distributed": {
    "node-alice": 400,
    "node-bob": 350,
    "node-carol": 250
  }
}
```

---

### 7. Lista Task Compositi

```http
GET /tasks/composite?channel=dev&status=open
```

**Response**:
```json
{
  "channel": "dev",
  "total_tasks": 3,
  "filter_status": "open",
  "tasks": [
    {
      "task_id": "tc-abc12345",
      "title": "Dashboard Analytics",
      "status": "open",
      "required_skills": ["python", "react", "docker"],
      "total_reward_points": 1000,
      "...": "..."
    }
  ]
}
```

---

### 8. Dettagli Task Composito

```http
GET /tasks/composite/tc-abc12345?channel=dev
```

**Response**: Restituisce il task completo (le candidature sono visibili solo al coordinatore)

---

## 🔄 Flusso Completo

### Scenario: "Implementare Dashboard Analytics"

```
┌─────────────┐
│ 1. Alice    │
│ crea task   │
│ composito   │
└──────┬──────┘
       │
       │ POST /tasks/composite/create
       │
       ▼
┌────────────────────────────────────────┐
│ Task: Dashboard Analytics              │
│ - Backend API (300 SP)                 │
│ - Frontend (350 SP)                    │
│ - DevOps (250 SP)                      │
│ Status: open                           │
└──────┬─────────────────────────────────┘
       │
       │ 2. Alice reclama (diventa coordinatore)
       │ POST /tasks/composite/{id}/claim
       │
       ▼
┌────────────────────────────────────────┐
│ Status: forming_team                   │
│ Coordinator: Alice                     │
│ Announcement pubblicato                │
└──────┬─────────────────────────────────┘
       │
       │ 3. Bob, Carol, Dave si candidano
       │ POST /tasks/composite/{id}/apply
       │
       ▼
┌────────────────────────────────────────┐
│ Applicants:                            │
│ - Bob: 66.7% match (react, typescript)│
│ - Carol: 100% match (docker, k8s)     │
│ - Dave: 33.3% match (python, django)  │
└──────┬─────────────────────────────────┘
       │
       │ 4. Alice accetta Bob e Carol
       │ POST /tasks/composite/{id}/accept/node-bob
       │ POST /tasks/composite/{id}/accept/node-carol
       │
       ▼
┌────────────────────────────────────────┐
│ Status: in_progress                    │
│ Team: Alice (coordinator), Bob, Carol  │
│ Workspace: team-tc-abc12345 (creato!) │
│                                        │
│ Auto-assegnamento:                     │
│ - Backend API → Alice                  │
│ - Frontend → Bob                       │
│ - DevOps → Carol                       │
└──────┬─────────────────────────────────┘
       │
       │ 5. Membri lavorano nel workspace
       │ [Collaborazione nel canale team-tc-abc12345]
       │
       │ 6. Completamento sub-tasks
       │ POST /tasks/.../subtask/st-1/complete (Alice)
       │ POST /tasks/.../subtask/st-2/complete (Bob)
       │ POST /tasks/.../subtask/st-3/complete (Carol)
       │
       ▼
┌────────────────────────────────────────┐
│ Status: completed ✅                   │
│                                        │
│ Rewards distribuiti:                   │
│ - Alice: 300 + 100 (bonus) = 400 SP   │
│ - Bob: 350 SP                          │
│ - Carol: 250 SP                        │
│                                        │
│ Workspace: dissolved                   │
└────────────────────────────────────────┘
```

---

## 🧮 Algoritmi Chiave

### Skill Matching

```python
def calculate_skill_match(node_skills: List[str], required_skills: List[str]) -> float:
    """
    Calcola % di match tra skills del nodo e skills richieste.
    
    Esempio:
    - node_skills = ["python", "react", "docker"]
    - required_skills = ["python", "fastapi", "postgresql"]
    - match = 1/3 = 33.3%
    """
    if not required_skills:
        return 1.0
    
    matched = set(node_skills).intersection(set(required_skills))
    return len(matched) / len(required_skills)
```

### Auto-Assegnamento Sub-Tasks

```python
def auto_assign_subtasks(task, node_skills_map):
    """
    Assegna ogni sub-task al membro con il miglior skill match.
    
    1. Per ogni sub-task non assegnato
    2. Calcola skill match con ogni membro
    3. Assegna al membro con match più alto
    """
    for subtask in task.sub_tasks:
        if subtask.assigned_to:
            continue
        
        best_member = None
        best_score = -1
        
        for member_id in task.team_members:
            score = calculate_skill_match(
                node_skills_map[member_id],
                subtask.required_skills
            )
            if score > best_score:
                best_score = score
                best_member = member_id
        
        if best_member:
            subtask.assigned_to = best_member
```

### Distribuzione Rewards

```python
def distribute_rewards(task, peer_scores, synapse_points):
    """
    Distribuisce rewards a:
    1. Membri che hanno completato sub-tasks (reward_points del sub-task)
    2. Coordinatore (coordinator_bonus)
    
    Aggiorna anche la reputazione (+10% dei points guadagnati)
    """
    distribution = {}
    
    # Sub-tasks
    for st in task.sub_tasks:
        if st.status == "completed" and st.assigned_to:
            distribution[st.assigned_to] = st.reward_points
    
    # Coordinatore
    if task.coordinator:
        distribution[task.coordinator] += task.coordinator_bonus
    
    # Applica
    for node_id, points in distribution.items():
        synapse_points[node_id] += points
        peer_scores[node_id]["reputation"] += points * 0.1
    
    return distribution
```

---

## 🎯 Esempi d'Uso

### Esempio 1: Backend Developer

Alice è una backend developer che vuole guadagnare Synapse Points:

```bash
# 1. Crea profilo skills
curl -X POST "http://localhost:8001/skills/profile?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["python", "fastapi", "postgresql", "docker"],
    "bio": "Backend developer con 5 anni di esperienza"
  }'

# 2. Cerca task compositi aperti
curl "http://localhost:8001/tasks/composite?channel=dev&status=open"

# 3. Candidati per un task
curl -X POST "http://localhost:8001/tasks/composite/tc-abc123/apply?channel=dev" \
  -d '{"message": "Ho esperienza con FastAPI e PostgreSQL"}'

# 4. (Se accettata) Lavora sul sub-task assegnato nel workspace

# 5. Completa il sub-task
curl -X POST "http://localhost:8001/tasks/composite/tc-abc123/subtask/st-xyz789/complete?channel=dev"

# 6. Ricevi reward automaticamente al completamento del task
```

---

### Esempio 2: Project Manager

Bob vuole coordinare un progetto complesso:

```bash
# 1. Crea task composito
curl -X POST "http://localhost:8001/tasks/composite/create?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "E-Commerce Platform",
    "description": "Piattaforma completa con frontend, backend, payment, deployment",
    "max_team_size": 6,
    "coordinator_bonus": 200,
    "sub_tasks": [
      {
        "title": "Backend API",
        "description": "REST API con autenticazione",
        "required_skills": ["python", "fastapi", "jwt"],
        "reward_points": 400
      },
      {
        "title": "Frontend React",
        "description": "UI responsive con React",
        "required_skills": ["react", "typescript", "tailwind"],
        "reward_points": 450
      },
      {
        "title": "Payment Integration",
        "description": "Stripe integration",
        "required_skills": ["stripe", "payment", "security"],
        "reward_points": 350
      },
      {
        "title": "DevOps",
        "description": "CI/CD pipeline e deployment",
        "required_skills": ["docker", "kubernetes", "terraform"],
        "reward_points": 300
      }
    ]
  }'

# 2. Reclama task (diventa coordinatore)
curl -X POST "http://localhost:8001/tasks/composite/tc-xyz789/claim?channel=dev"

# 3. Ricevi candidature automaticamente
# (i nodi con skill match si candidano)

# 4. Accetta membri
curl -X POST "http://localhost:8001/tasks/composite/tc-xyz789/accept/node-alice?channel=dev"
curl -X POST "http://localhost:8001/tasks/composite/tc-xyz789/accept/node-carol?channel=dev"
# ... accetta altri membri

# 5. (Quando squadra completa) Workspace creato automaticamente!
# Coordinamento nel canale "team-tc-xyz789"

# 6. Al completamento, ricevi coordinator_bonus (200 SP)
```

---

### Esempio 3: Skill Match Automatico

```python
# Scenario: Task richiede ["python", "fastapi", "postgresql"]

# Candidato 1: Alice
skills = ["python", "fastapi", "postgresql", "docker"]
match = 3/3 = 100%  # Match perfetto! ✅

# Candidato 2: Bob
skills = ["python", "django", "mysql"]
match = 1/3 = 33.3%  # Solo Python match

# Candidato 3: Carol
skills = ["javascript", "react", "node.js"]
match = 0/3 = 0%  # Nessun match ❌

# Il sistema mostra al coordinatore:
# 1. Alice: 100% match
# 2. Bob: 33.3% match
# 3. Carol: 0% match (potrebbe non essere mostrata)
```

---

## 🔐 Sicurezza e Permessi

### Controlli di Accesso

| Azione | Chi può eseguirla |
|--------|-------------------|
| Creare task composito | Chiunque |
| Reclamare task | Chiunque (se task è `open`) |
| Vedere candidature | Solo coordinatore |
| Accettare membri | Solo coordinatore |
| Candidarsi | Chiunque con profilo skills |
| Completare sub-task | Solo membro assegnato |
| Vedere workspace | Solo membri della squadra |

### Privacy

- ✅ **Candidature private**: Solo il coordinatore vede le candidature
- ✅ **Workspace privato**: Solo membri della squadra accedono al canale
- ✅ **Skills pubbliche**: I profili skills sono visibili a tutti (necessario per matching)

---

## 📊 Metriche e Statistiche

### Profilo Nodo

Ogni profilo tracks:
- `completed_tasks`: Numero di sub-tasks completati
- `team_participations`: Numero di squadre di cui ha fatto parte
- `coordinator_count`: Volte che è stato coordinatore

### Task Composito

Statistiche:
- Tempo medio per formazione squadra
- Skill match medio dei membri
- Tasso di completamento
- Reward totale distribuito

---

## 🚀 Casi d'Uso Avanzati

### 1. Auto-Formazione Basata su Reputazione

```python
# Future enhancement: priorità candidature per reputazione
for applicant in sorted(task.applicants, key=lambda x: get_reputation(x["node_id"]), reverse=True):
    if len(team) < max_size:
        accept_member(applicant["node_id"])
```

### 2. Task Ricorsivi

```python
# Future: Sub-tasks possono essere a loro volta task compositi
{
  "sub_tasks": [
    {
      "title": "Backend",
      "type": "composite",  # ← Questo sub-task è composito!
      "sub_tasks": [
        {"title": "Database Schema"},
        {"title": "API Endpoints"}
      ]
    }
  ]
}
```

### 3. Skill Endorsement

```python
# Future: Membri possono endorsare skills di altri membri
{
  "node_id": "node-alice",
  "skills": ["python"],
  "endorsements": {
    "python": ["node-bob", "node-carol", "node-dave"]  # 3 endorsement
  }
}
```

---

## 🧪 Testing

### Test Manuale Rapido

```bash
# Terminal 1: Nodo Alice (coordinatore)
curl -X POST "http://localhost:8001/skills/profile?channel=dev" \
  -d '{"skills": ["python", "fastapi"]}'

curl -X POST "http://localhost:8001/tasks/composite/create?channel=dev" \
  -d @task_composite_example.json

curl -X POST "http://localhost:8001/tasks/composite/tc-xxx/claim?channel=dev"

# Terminal 2: Nodo Bob (membro)
curl -X POST "http://localhost:8002/skills/profile?channel=dev" \
  -d '{"skills": ["react", "typescript"]}'

curl -X POST "http://localhost:8002/tasks/composite/tc-xxx/apply?channel=dev" \
  -d '{"message": "Esperto React"}'

# Terminal 1: Alice accetta Bob
curl -X POST "http://localhost:8001/tasks/composite/tc-xxx/accept/node-bob?channel=dev"

# Verifica workspace creato
curl "http://localhost:8001/tasks/composite/tc-xxx?channel=dev"
```

### Test Automatizzato

Vedi `test_collaborative_teams.sh` per suite completa.

---

## 📚 Riferimenti

### File Sorgenti
- `app/collaborative_teams.py`: Modulo core con logica e algoritmi
- `app/main.py`: Endpoint API (linee 1053-1500+)
- `docs/COLLABORATIVE_TEAMS.md`: Questa documentazione

### Documentazione Correlata
- [AUTONOMOUS_ORGANISM_COMPLETE.md](AUTONOMOUS_ORGANISM_COMPLETE.md): Visione complessiva
- [AUCTION_SYSTEM.md](AUCTION_SYSTEM.md): Sistema di aste per task
- [GOVERNANCE_ARCHITECTURE.md](GOVERNANCE_ARCHITECTURE.md): Governance decentralizzata

---

## 💡 Best Practices

### Per Coordinatori

1. **Descrizioni chiare**: Scrivi descrizioni dettagliate dei sub-tasks
2. **Skills specifiche**: Elenca skills precise (es. "fastapi" vs "python web")
3. **Reward equilibrato**: Distribuisci reward proporzionalmente alla complessità
4. **Comunicazione**: Usa il workspace per coordinare il lavoro
5. **Flessibilità**: Accetta membri con skill match >= 50%

### Per Membri

1. **Profilo aggiornato**: Mantieni le skills aggiornate
2. **Candidature motivate**: Scrivi messaggi di candidatura significativi
3. **Disponibilità**: Candidati solo se hai tempo per il task
4. **Comunicazione**: Segnala problemi o ritardi nel workspace
5. **Completamento**: Marca i sub-tasks come completati quando finiti

### Per la Rete

1. **Task piccoli**: Preferisci task con 3-5 sub-tasks (più gestibili)
2. **Deadline realistiche**: Dai tempo sufficiente per completare
3. **Skill diversificate**: Crea task che richiedono competenze complementari
4. **Iterazione**: Usa feedback per migliorare task futuri

---

## 🔧 Troubleshooting

### Problema: "Devi prima creare un profilo skills"
**Soluzione**: Crea profilo con `POST /skills/profile`

### Problema: "Squadra già al completo"
**Soluzione**: Il task ha raggiunto `max_team_size`, cerca altri task

### Problema: "Nessuna skill richiesta corrisponde"
**Soluzione**: Aggiorna il tuo profilo skills per includere competenze richieste

### Problema: "Solo il coordinatore può accettare membri"
**Soluzione**: Solo chi ha reclamato il task può accettare candidati

### Problema: Workspace non creato
**Soluzione**: Workspace si crea solo quando la squadra è completa (tutti sub-tasks assegnati)

---

## 🎓 Glossario

- **Task Composito**: Task diviso in sub-tasks con skills diverse
- **Sub-Task**: Micro-task parte di un task composito
- **Coordinatore**: Nodo che ha reclamato il task e gestisce la squadra
- **Skill Match**: Percentuale di overlap tra skills del nodo e skills richieste
- **Workspace**: Canale temporaneo privato per la collaborazione
- **Coordinator Bonus**: Reward extra per il coordinatore

---

**Versione**: 1.0.0  
**Data**: 2025-10-02  
**Autore**: Synapse-NG Development Team  
**Stato**: ✅ Production-Ready
