"""
Collaborative Teams System for Synapse-NG

Questo modulo implementa il sistema di squadre/gilde temporanee per task complessi:
- Task compositi con sub-tasks e skills richieste
- Protocollo di formazione squadra (coordinatore + membri)
- Workspace temporanei (canali privati auto-dissolvibili)
- Sistema di candidature e selezione membri
- Gestione skills/profili nodi
- Completamento collaborativo con reward distribution

Autore: Synapse-NG Development Team
Data: 2025-10-02
"""

from typing import Dict, List, Optional, Set
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import logging
import uuid

# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

class SubTask(BaseModel):
    """
    Un sub-task all'interno di un task composito.
    """
    sub_task_id: str = Field(default_factory=lambda: f"st-{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None  # NODE_ID del membro assegnato
    status: str = "pending"  # pending, in_progress, completed, failed
    reward_points: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)


class TaskComposite(BaseModel):
    """
    Schema per task compositi (task_composite_v1).
    
    Un task composito è composto da più sub-tasks che richiedono
    diverse competenze. Viene assegnato a una squadra coordinata.
    """
    task_id: str = Field(default_factory=lambda: f"tc-{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    task_type: str = "composite"
    
    # Sub-tasks
    sub_tasks: List[SubTask] = Field(default_factory=list)
    
    # Coordinamento
    coordinator: Optional[str] = None  # NODE_ID del coordinatore
    team_members: List[str] = Field(default_factory=list)  # Lista di NODE_IDs
    max_team_size: int = 10
    
    # Skills richieste (aggregato dai sub-tasks)
    required_skills: List[str] = Field(default_factory=list)
    
    # Stato
    status: str = "open"  # open, forming_team, in_progress, completed, failed, cancelled
    
    # Workspace
    workspace_channel: Optional[str] = None  # Nome del canale temporaneo
    
    # Rewards
    total_reward_points: int = 0
    coordinator_bonus: int = 0  # Bonus extra per il coordinatore
    
    # Candidature
    applicants: List[Dict] = Field(default_factory=list)  # [{node_id, skills, message, timestamp}]
    
    # Timeline
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    team_formed_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deadline: Optional[str] = None
    
    # Metadata
    created_by: Optional[str] = None
    channel: str = "general"
    metadata: Dict = Field(default_factory=dict)


class NodeSkills(BaseModel):
    """
    Profilo di skills di un nodo.
    """
    node_id: str
    skills: List[str] = Field(default_factory=list)  # Es. ["python", "frontend", "devops"]
    skill_levels: Dict[str, int] = Field(default_factory=dict)  # {"python": 3, "frontend": 2}
    bio: str = ""
    availability: str = "available"  # available, busy, unavailable
    completed_tasks: int = 0
    team_participations: int = 0
    coordinator_count: int = 0
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TeamAnnouncement(BaseModel):
    """
    Annuncio di ricerca membri per task composito.
    """
    announcement_id: str = Field(default_factory=lambda: f"ann-{uuid.uuid4().hex[:8]}")
    task_id: str
    coordinator: str  # NODE_ID
    required_skills: List[str]
    team_size_needed: int
    message: str
    channel: str
    expires_at: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_skill_match(node_skills: List[str], required_skills: List[str]) -> float:
    """
    Calcola il matching percentuale tra skills del nodo e skills richieste.
    
    Returns:
        float: Percentuale di match (0.0 - 1.0)
    """
    if not required_skills:
        return 1.0
    
    node_set = set(s.lower() for s in node_skills)
    required_set = set(s.lower() for s in required_skills)
    
    matched = node_set.intersection(required_set)
    return len(matched) / len(required_set)


def get_unique_skills_from_subtasks(sub_tasks: List[SubTask]) -> List[str]:
    """
    Estrae lista unica di skills richieste da tutti i sub-tasks.
    """
    skills = set()
    for st in sub_tasks:
        skills.update(st.required_skills)
    return sorted(list(skills))


def calculate_total_reward(sub_tasks: List[SubTask], coordinator_bonus: int = 0) -> int:
    """
    Calcola il reward totale del task composito.
    """
    subtask_rewards = sum(st.reward_points for st in sub_tasks)
    return subtask_rewards + coordinator_bonus


def can_node_join_team(
    node_id: str,
    node_skills: List[str],
    task: TaskComposite,
    current_team_size: int
) -> tuple[bool, str]:
    """
    Verifica se un nodo può unirsi a una squadra.
    
    Returns:
        (bool, str): (can_join, reason)
    """
    # Verifica se il task è nello stato corretto
    if task.status not in ["open", "forming_team"]:
        return False, f"Task non accetta nuovi membri (status: {task.status})"
    
    # Verifica se c'è spazio
    if current_team_size >= task.max_team_size:
        return False, "Squadra già al completo"
    
    # Verifica se il nodo è già membro
    if node_id in task.team_members:
        return False, "Nodo già membro della squadra"
    
    # Verifica se il nodo è il coordinatore
    if node_id == task.coordinator:
        return False, "Nodo è già il coordinatore"
    
    # Verifica skills (almeno una skill match richiesto)
    skill_match = calculate_skill_match(node_skills, task.required_skills)
    if skill_match == 0 and len(task.required_skills) > 0:
        return False, "Nessuna skill richiesta corrisponde al profilo del nodo"
    
    return True, "OK"


def is_team_complete(task: TaskComposite) -> bool:
    """
    Verifica se tutti i sub-tasks hanno un membro assegnato.
    """
    for st in task.sub_tasks:
        if st.assigned_to is None:
            return False
    return True


def all_subtasks_completed(task: TaskComposite) -> bool:
    """
    Verifica se tutti i sub-tasks sono completati.
    """
    for st in task.sub_tasks:
        if st.status != "completed":
            return False
    return True


def get_workspace_channel_name(task_id: str) -> str:
    """
    Genera nome del canale workspace per un task composito.
    
    Returns:
        str: Nome canale (es. "team-tc-abc123")
    """
    return f"team-{task_id}"


def distribute_rewards(
    task: TaskComposite,
    peer_scores: Dict[str, Dict],
    synapse_points: Dict[str, int]
) -> Dict[str, int]:
    """
    Distribuisce i rewards ai membri della squadra.
    
    Args:
        task: Task composito completato
        peer_scores: Dict di peer scores
        synapse_points: Dict di synapse points
    
    Returns:
        Dict[node_id, points_earned]: Mapping dei punti guadagnati
    """
    distribution = {}
    
    # Reward per sub-tasks completati
    for st in task.sub_tasks:
        if st.status == "completed" and st.assigned_to:
            node_id = st.assigned_to
            distribution[node_id] = distribution.get(node_id, 0) + st.reward_points
    
    # Bonus coordinatore
    if task.coordinator and task.coordinator_bonus > 0:
        distribution[task.coordinator] = distribution.get(task.coordinator, 0) + task.coordinator_bonus
    
    # Applica i rewards
    for node_id, points in distribution.items():
        if node_id in synapse_points:
            synapse_points[node_id] += points
        else:
            synapse_points[node_id] = points
        
        # Aggiorna reputazione (bonus per collaborazione)
        if node_id in peer_scores:
            peer_scores[node_id]["reputation"] = peer_scores[node_id].get("reputation", 0) + points * 0.1
    
    return distribution


def generate_team_announcement(task: TaskComposite, coordinator: str) -> TeamAnnouncement:
    """
    Genera un annuncio di ricerca membri per un task composito.
    """
    # Calcola quanti membri servono ancora
    current_size = len(task.team_members) + 1  # +1 per coordinatore
    team_size_needed = task.max_team_size - current_size
    
    # Messaggio automatico
    skills_str = ", ".join(task.required_skills[:5])
    if len(task.required_skills) > 5:
        skills_str += f" (+{len(task.required_skills) - 5} altre)"
    
    message = f"""
🔍 Cerco {team_size_needed} membri per task composito!

📋 Task: {task.title}
🎯 Skills richieste: {skills_str}
💰 Reward totale: {task.total_reward_points} SP
👥 Posti disponibili: {team_size_needed}

Candidati con: POST /tasks/composite/{task.task_id}/apply
""".strip()
    
    # Scadenza annuncio: 24 ore
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    
    return TeamAnnouncement(
        task_id=task.task_id,
        coordinator=coordinator,
        required_skills=task.required_skills,
        team_size_needed=team_size_needed,
        message=message,
        channel=task.channel,
        expires_at=expires_at
    )


def auto_assign_subtasks(task: TaskComposite, node_skills_map: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Assegna automaticamente sub-tasks ai membri della squadra basandosi sulle skills.
    
    Returns:
        Dict[sub_task_id, node_id]: Mapping assegnamenti
    """
    assignments = {}
    
    # Crea mapping node -> skills match score per ogni sub-task
    for st in task.sub_tasks:
        if st.assigned_to:
            continue  # Già assegnato
        
        best_match = None
        best_score = -1
        
        for node_id in task.team_members:
            node_skills = node_skills_map.get(node_id, [])
            score = calculate_skill_match(node_skills, st.required_skills)
            
            if score > best_score:
                best_score = score
                best_match = node_id
        
        if best_match:
            st.assigned_to = best_match
            assignments[st.sub_task_id] = best_match
    
    return assignments


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_composite_task(task: TaskComposite) -> tuple[bool, str]:
    """
    Valida un task composito.
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    if not task.title or len(task.title.strip()) == 0:
        return False, "Titolo vuoto"
    
    if not task.sub_tasks or len(task.sub_tasks) == 0:
        return False, "Nessun sub-task definito"
    
    if task.max_team_size < len(task.sub_tasks):
        return False, "max_team_size deve essere >= numero di sub-tasks"
    
    # Verifica sub-tasks
    for i, st in enumerate(task.sub_tasks):
        if not st.title or len(st.title.strip()) == 0:
            return False, f"Sub-task {i+1} ha titolo vuoto"
        
        if st.reward_points < 0:
            return False, f"Sub-task {i+1} ha reward negativo"
    
    # Calcola total reward
    task.total_reward_points = calculate_total_reward(task.sub_tasks, task.coordinator_bonus)
    
    # Estrai skills uniche
    task.required_skills = get_unique_skills_from_subtasks(task.sub_tasks)
    
    return True, "OK"


def validate_node_skills(skills: NodeSkills) -> tuple[bool, str]:
    """
    Valida il profilo skills di un nodo.
    """
    if not skills.node_id:
        return False, "node_id mancante"
    
    # Verifica che skill_levels contenga solo skills presenti in skills
    for skill in skills.skill_levels.keys():
        if skill not in skills.skills:
            return False, f"skill_levels contiene '{skill}' non presente in skills"
    
    return True, "OK"


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def log_team_event(event_type: str, task_id: str, details: Dict):
    """
    Log eventi relativi alla formazione/gestione squadre.
    """
    logging.info(f"👥 TEAM EVENT [{event_type}] Task={task_id} | {details}")


# ============================================================================
# TEST FUNCTION
# ============================================================================

def test_collaborative_teams():
    """
    Test del sistema di squadre collaborative.
    """
    print("🧪 Testing Collaborative Teams System")
    print("=" * 60)
    
    # 1. Crea task composito
    print("\n1. Creazione task composito")
    task = TaskComposite(
        title="Implementare Dashboard Analytics",
        description="Dashboard completa con backend, frontend e deployment",
        channel="dev",
        created_by="node-alice",
        max_team_size=5,
        coordinator_bonus=100,
        sub_tasks=[
            SubTask(
                title="Backend API",
                description="Creare REST API con FastAPI",
                required_skills=["python", "fastapi", "postgresql"],
                reward_points=300
            ),
            SubTask(
                title="Frontend Dashboard",
                description="UI React con grafici",
                required_skills=["react", "typescript", "d3.js"],
                reward_points=350
            ),
            SubTask(
                title="DevOps & Deploy",
                description="Setup CI/CD e deployment",
                required_skills=["docker", "kubernetes", "ci/cd"],
                reward_points=250
            )
        ]
    )
    
    valid, msg = validate_composite_task(task)
    print(f"   Valid: {valid}")
    print(f"   Total reward: {task.total_reward_points} SP")
    print(f"   Required skills: {', '.join(task.required_skills)}")
    
    # 2. Crea profili nodi
    print("\n2. Creazione profili nodi")
    alice = NodeSkills(
        node_id="node-alice",
        skills=["python", "fastapi", "postgresql", "docker"],
        skill_levels={"python": 5, "fastapi": 4, "postgresql": 3}
    )
    
    bob = NodeSkills(
        node_id="node-bob",
        skills=["react", "typescript", "javascript", "css"],
        skill_levels={"react": 5, "typescript": 4}
    )
    
    carol = NodeSkills(
        node_id="node-carol",
        skills=["docker", "kubernetes", "terraform", "ci/cd"],
        skill_levels={"docker": 5, "kubernetes": 4, "ci/cd": 5}
    )
    
    print(f"   Alice: {', '.join(alice.skills)}")
    print(f"   Bob: {', '.join(bob.skills)}")
    print(f"   Carol: {', '.join(carol.skills)}")
    
    # 3. Test skill matching
    print("\n3. Test skill matching")
    for node in [alice, bob, carol]:
        match = calculate_skill_match(node.skills, task.required_skills)
        print(f"   {node.node_id}: {match*100:.1f}% match")
    
    # 4. Simula formazione squadra
    print("\n4. Formazione squadra")
    task.coordinator = "node-alice"
    task.team_members = ["node-bob", "node-carol"]
    task.status = "forming_team"
    print(f"   Coordinatore: {task.coordinator}")
    print(f"   Membri: {', '.join(task.team_members)}")
    
    # 5. Auto-assegnamento sub-tasks
    print("\n5. Auto-assegnamento sub-tasks")
    node_skills_map = {
        "node-alice": alice.skills,
        "node-bob": bob.skills,
        "node-carol": carol.skills
    }
    
    assignments = auto_assign_subtasks(task, node_skills_map)
    for st in task.sub_tasks:
        print(f"   {st.title} → {st.assigned_to}")
    
    # 6. Genera workspace channel
    print("\n6. Workspace temporaneo")
    workspace = get_workspace_channel_name(task.task_id)
    task.workspace_channel = workspace
    print(f"   Canale: {workspace}")
    
    # 7. Simula completamento
    print("\n7. Completamento task")
    for st in task.sub_tasks:
        st.status = "completed"
        st.completed_at = datetime.now(timezone.utc).isoformat()
    
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc).isoformat()
    
    all_done = all_subtasks_completed(task)
    print(f"   Tutti sub-tasks completati: {all_done}")
    
    # 8. Distribuzione rewards
    print("\n8. Distribuzione rewards")
    peer_scores = {
        "node-alice": {"reputation": 100},
        "node-bob": {"reputation": 80},
        "node-carol": {"reputation": 90}
    }
    synapse_points = {
        "node-alice": 1000,
        "node-bob": 800,
        "node-carol": 900
    }
    
    distribution = distribute_rewards(task, peer_scores, synapse_points)
    for node_id, points in distribution.items():
        print(f"   {node_id}: +{points} SP")
    
    # 9. Test annuncio
    print("\n9. Generazione annuncio")
    announcement = generate_team_announcement(task, task.coordinator)
    print(f"   Announcement ID: {announcement.announcement_id}")
    print(f"   Membri cercati: {announcement.team_size_needed}")
    
    print("\n" + "=" * 60)
    print("✅ Test completato!")


if __name__ == "__main__":
    test_collaborative_teams()
