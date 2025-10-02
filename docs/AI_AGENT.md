# AI Agent - Assistente Locale per Nodi Synapse-NG

## 📋 Panoramica

Ogni nodo Synapse-NG può essere dotato di un **agente AI locale** basato su LLM che permette:
- 🗣️ **Interazione in linguaggio naturale** - Comandi vocali/testuali invece di chiamate API
- 🧠 **Analisi strategica automatica** - L'agente "pensa" autonomamente e suggerisce azioni
- 🤖 **Automazione intelligente** - Esegue azioni basate su obiettivi definiti dall'utente
- 🎯 **Comportamento orientato agli obiettivi** - Massimizza SP, reputazione, partecipazione

**Modello**: Qwen3 0.6B (GGUF format)  
**Engine**: llama-cpp-python  
**Memoria**: ~1GB RAM per il modello  
**Latenza**: ~100-500ms per generazione comandi

---

## 🏗️ Architettura

```
┌────────────────────────────────────────────────────────────┐
│ Utente                                                     │
│ "Crea un task per fixare il bug della UI con reward 50SP" │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ POST /agent/prompt                                         │
│  - Riceve prompt testuale                                  │
│  - Costruisce contesto (stato rete, API disponibili)       │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ LLM Locale (Qwen3 0.6B)                                    │
│  - Analizza prompt + contesto                              │
│  - Genera sequenza di comandi API in JSON                  │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│ Executor                                                   │
│  - Valida comandi generati (SP reserve, permissions)       │
│  - Esegue azioni API interne                               │
│  - Ritorna risultati all'utente                            │
└────────────────────────────────────────────────────────────┘
```

### Agente Proattivo (Background Loop)

```
┌─────────────────────────────────────────────────────────────┐
│ Proactive Agent Loop (ogni 5 minuti)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Legge stato rete (tasks, proposals, auctions, teams)    │
│ 2. Calcola synapse points e reputation                     │
│ 3. Costruisce NetworkContext                               │
│ 4. Chiede all'LLM: "Suggerisci azioni strategiche"        │
│ 5. Riceve lista di azioni (es. bid su auction, vota)      │
│ 6. Valida azioni (rispetta obiettivi utente)              │
│ 7. Esegue azioni validate                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installazione e Setup

### 1. Installa Dipendenze

```bash
cd /Users/fab/GitHub/synapse-ng
pip install llama-cpp-python
```

**Nota**: `llama-cpp-python` richiede compilazione. Per macOS:
```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

Per GPU (CUDA):
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### 2. Scarica Modello GGUF

Scarica **Qwen3 0.6B** in formato GGUF:

```bash
mkdir -p models
cd models

# Opzione 1: Download diretto (esempio)
wget https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q8_0.gguf \
  -O qwen3-0.6b.gguf

# Opzione 2: Usa huggingface-cli
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct-GGUF \
  qwen2.5-0.5b-instruct-q8_0.gguf \
  --local-dir .
```

**Modelli alternativi compatibili**:
- TinyLlama 1.1B GGUF (~600MB)
- Phi-2 2.7B GGUF (~1.5GB)
- Mistral 7B GGUF Q4 (~4GB)

### 3. Configura Path Modello

Imposta variabile d'ambiente:

```bash
export AI_MODEL_PATH="$(pwd)/models/qwen3-0.6b.gguf"

# Opzionale: intervallo analisi proattiva (default: 300 secondi)
export AGENT_PROACTIVE_INTERVAL="600"
```

Aggiungi a `.env` o `config.env`:
```bash
AI_MODEL_PATH=models/qwen3-0.6b.gguf
AGENT_PROACTIVE_INTERVAL=300
```

### 4. Verifica Modulo

```bash
python3 app/ai_agent.py
```

**Output atteso**:
```
=== Testing AI Agent ===

1. Creating AI Agent for node test-node-123
   ✓ Agent created (model loading skipped for test)

2. Setting objectives
   ✓ Objectives set: AgentObjective.MAXIMIZE_SP

...

=== All AI Agent Tests Passed ===
```

---

## 🔧 Integrazione in `main.py`

**NOTA**: Per questioni di dimensione del file `main.py` (4000+ righe), l'integrazione completa è rimandata. Ecco le modifiche necessarie:

### 1. Import AI Agent

Aggiungi dopo gli import di collaborative teams (~line 56):

```python
# --- AI Agent ---
from app.ai_agent import (
    AIAgent,
    UserObjectives,
    AgentObjective,
    NetworkContext,
    AgentAction,
    initialize_agent,
    get_agent,
    is_agent_enabled
)
```

### 2. Inizializzazione all'Avvio

Aggiungi in `on_startup()` (~line 3795):

```python
# Inizializza AI Agent (se modello disponibile)
model_path = os.getenv("AI_MODEL_PATH", "models/qwen3-0.6b.gguf")
if os.path.exists(model_path):
    logging.info(f"🤖 Inizializzazione AI Agent con modello {model_path}...")
    success = initialize_agent(NODE_ID, model_path)
    if success:
        logging.info("✅ AI Agent inizializzato e pronto")
        # Avvia proactive agent loop
        asyncio.create_task(proactive_agent_loop())
        logging.info("🧠 Proactive agent loop avviato")
    else:
        logging.warning("⚠️ AI Agent non disponibile (modello non caricato)")
else:
    logging.info(f"ℹ️ AI Agent disabilitato (modello non trovato: {model_path})")
    logging.info("   Per abilitarlo, scarica un modello GGUF e imposta AI_MODEL_PATH")
```

### 3. Funzioni Helper

Aggiungi prima degli endpoint (~line 3700):

```python
async def proactive_agent_loop():
    """Loop periodico per analisi proattiva dell'AI agent"""
    await asyncio.sleep(90)
    logging.info("🧠 Proactive agent loop avviato")
    
    check_interval = int(os.getenv("AGENT_PROACTIVE_INTERVAL", "300"))
    
    while True:
        try:
            agent = get_agent()
            if not agent or not agent.enabled:
                await asyncio.sleep(check_interval)
                continue
            
            # Costruisci contesto di rete
            async with state_lock:
                state_copy = json.loads(json.dumps(network_state, default=list))
            
            channel = list(subscribed_channels)[0] if subscribed_channels else "global"
            channel_data = state_copy.get(channel, {})
            
            # Calcola synapse points
            sp = channel_data.get("synapse_points", {}).get(NODE_ID, 0)
            
            # Calcola reputation
            reputations = calculate_reputations(state_copy)
            reputation = reputations.get(NODE_ID, 0.0)
            
            # Recupera skills
            node_skills = channel_data.get("node_skills", {}).get(NODE_ID, {})
            skills = node_skills.get("skills", [])
            
            # Trova opportunità
            open_tasks = [
                task for task in channel_data.get("tasks", {}).values()
                if task.get("status") == "open"
            ]
            
            active_proposals = [
                prop for prop in channel_data.get("proposals", {}).values()
                if prop.get("status") == "open"
            ]
            
            active_auctions = [
                auc for auc in channel_data.get("auctions", {}).values()
                if auc.get("status") == "open"
            ]
            
            available_teams = [
                task for task in channel_data.get("composite_tasks", {}).values()
                if task.get("status") == "forming_team" and NODE_ID not in task.get("team_members", [])
            ]
            
            peer_count = len(webrtc_manager.peer_connections)
            
            # Crea contesto
            context = NetworkContext(
                node_id=NODE_ID,
                channel=channel,
                synapse_points=sp,
                reputation=reputation,
                skills=skills,
                open_tasks=open_tasks,
                active_proposals=active_proposals,
                active_auctions=active_auctions,
                available_teams=available_teams,
                peer_count=peer_count
            )
            
            # Esegui analisi proattiva
            logging.info(f"🤔 Agent proattivo sta analizzando rete (SP:{sp}, Rep:{reputation:.2f}, Peers:{peer_count})")
            actions = await agent.proactive_analysis(context)
            
            if actions:
                logging.info(f"🎯 Agent ha generato {len(actions)} azioni proattive")
                
                # Esegui azioni validate
                for action in actions:
                    is_valid, reason = agent.validate_action(action, context)
                    
                    if is_valid:
                        try:
                            await execute_agent_action(action, channel, state_copy)
                            logging.info(f"✅ Azione eseguita: {action.action} - {action.reasoning}")
                        except Exception as e:
                            logging.error(f"❌ Errore esecuzione azione {action.action}: {e}")
                    else:
                        logging.warning(f"⚠️ Azione rifiutata: {action.action} - {reason}")
            else:
                logging.info("💤 Nessuna azione proattiva generata")
            
        except Exception as e:
            logging.error(f"❌ Errore in proactive agent loop: {e}")
        
        await asyncio.sleep(check_interval)


async def execute_agent_action(action: AgentAction, default_channel: str, state_snapshot: dict):
    """Esegue un'azione generata dall'AI agent"""
    params = action.params
    channel = params.get("channel", default_channel)
    
    if action.action == "create_task":
        task_id = str(uuid.uuid4())
        async with state_lock:
            network_state[channel]["tasks"][task_id] = {
                "id": task_id,
                "title": params["title"],
                "description": params.get("description", ""),
                "reward": params["reward"],
                "status": "open",
                "creator": NODE_ID,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        logging.info(f"📝 Agent created task: {params['title']} ({params['reward']} SP)")
    
    elif action.action == "claim_task":
        task_id = params["task_id"]
        async with state_lock:
            task = network_state[channel]["tasks"].get(task_id)
            if task and task["status"] == "open":
                task["status"] = "in_progress"
                task["claimed_by"] = NODE_ID
                task["claimed_at"] = datetime.now(timezone.utc).isoformat()
                logging.info(f"🎯 Agent claimed task: {task_id}")
    
    elif action.action == "vote_proposal":
        proposal_id = params["proposal_id"]
        vote = params["vote"]
        use_zkp = params.get("use_zkp", False)
        
        async with state_lock:
            proposal = network_state[channel]["proposals"].get(proposal_id)
            if proposal and proposal["status"] == "open":
                if use_zkp:
                    # Genera proof ZKP
                    private_key_bytes = get_node_secret_from_private_key(ed25519_private_key)
                    reputations = calculate_reputations(network_state)
                    reputation = reputations.get(NODE_ID, 0.0)
                    proof = generate_reputation_proof(private_key_bytes, reputation)
                    
                    proposal.setdefault("anonymous_votes", []).append({
                        "vote": vote,
                        "tier": proof["tier"],
                        "nullifier": proof["nullifier"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    logging.info(f"🔒 Agent voted (ZKP) on proposal: {proposal_id}")
                else:
                    proposal.setdefault("votes", {})[NODE_ID] = {
                        "vote": vote,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    logging.info(f"🗳️ Agent voted on proposal: {proposal_id}")
    
    elif action.action == "bid_auction":
        auction_id = params["auction_id"]
        amount = params["amount"]
        
        async with state_lock:
            auction = network_state[channel]["auctions"].get(auction_id)
            if auction and auction["status"] == "open":
                current_bid = auction.get("current_bid", auction["starting_price"])
                if amount >= current_bid + auction["min_increment"]:
                    auction["current_bid"] = amount
                    auction["highest_bidder"] = NODE_ID
                    auction.setdefault("bid_history", []).append({
                        "bidder": NODE_ID,
                        "amount": amount,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    logging.info(f"💰 Agent bid on auction: {auction_id} ({amount} SP)")
    
    elif action.action == "apply_team":
        task_id = params["task_id"]
        
        async with state_lock:
            task = network_state[channel]["composite_tasks"].get(task_id)
            node_skills = network_state[channel]["node_skills"].get(NODE_ID)
            
            if task and node_skills and task["status"] == "forming_team":
                task.setdefault("applicants", []).append({
                    "node_id": NODE_ID,
                    "skills": node_skills["skills"],
                    "applied_at": datetime.now(timezone.utc).isoformat()
                })
                logging.info(f"👥 Agent applied to team: {task_id}")
    
    elif action.action == "update_skills":
        async with state_lock:
            network_state[channel]["node_skills"][NODE_ID] = {
                "node_id": NODE_ID,
                "skills": params["skills"],
                "bio": params.get("bio", ""),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        logging.info(f"🎓 Agent updated skills: {params['skills']}")
    
    else:
        logging.warning(f"⚠️ Unknown agent action: {action.action}")
```

### 4. Endpoint `/agent/prompt`

Aggiungi prima della sezione governance (~line 1550):

```python
# ========================================
# AI Agent Endpoints
# ========================================

@app.post("/agent/prompt", status_code=200)
async def agent_prompt(channel: str, prompt: str):
    """
    Invia un prompt in linguaggio naturale all'AI agent.
    
    L'agent analizza il prompt, costruisce il contesto della rete,
    e genera comandi API da eseguire automaticamente.
    
    Args:
        channel: Canale di default per le azioni
        prompt: Prompt testuale in linguaggio naturale
        
    Returns:
        actions_executed: Lista di azioni eseguite
        raw_response: Risposta grezza del LLM
    """
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile. Configura AI_MODEL_PATH e riavvia.")
    
    agent = get_agent()
    
    # Costruisci contesto
    async with state_lock:
        state_copy = json.loads(json.dumps(network_state, default=list))
    
    channel_data = state_copy.get(channel, {})
    
    sp = channel_data.get("synapse_points", {}).get(NODE_ID, 0)
    reputations = calculate_reputations(state_copy)
    reputation = reputations.get(NODE_ID, 0.0)
    node_skills = channel_data.get("node_skills", {}).get(NODE_ID, {})
    skills = node_skills.get("skills", [])
    
    open_tasks = [t for t in channel_data.get("tasks", {}).values() if t.get("status") == "open"]
    active_proposals = [p for p in channel_data.get("proposals", {}).values() if p.get("status") == "open"]
    active_auctions = [a for a in channel_data.get("auctions", {}).values() if a.get("status") == "open"]
    available_teams = [t for t in channel_data.get("composite_tasks", {}).values() 
                       if t.get("status") == "forming_team" and NODE_ID not in t.get("team_members", [])]
    
    peer_count = len(webrtc_manager.peer_connections)
    
    context = NetworkContext(
        node_id=NODE_ID,
        channel=channel,
        synapse_points=sp,
        reputation=reputation,
        skills=skills,
        open_tasks=open_tasks,
        active_proposals=active_proposals,
        active_auctions=active_auctions,
        available_teams=available_teams,
        peer_count=peer_count
    )
    
    # Processa prompt
    actions, raw_response = await agent.process_prompt(prompt, context)
    
    # Esegui azioni validate
    actions_executed = []
    for action in actions:
        is_valid, reason = agent.validate_action(action, context)
        
        if is_valid:
            try:
                await execute_agent_action(action, channel, state_copy)
                actions_executed.append({
                    "action": action.action,
                    "params": action.params,
                    "reasoning": action.reasoning,
                    "status": "executed"
                })
            except Exception as e:
                actions_executed.append({
                    "action": action.action,
                    "params": action.params,
                    "reasoning": action.reasoning,
                    "status": "failed",
                    "error": str(e)
                })
        else:
            actions_executed.append({
                "action": action.action,
                "params": action.params,
                "reasoning": action.reasoning,
                "status": "rejected",
                "reason": reason
            })
    
    return {
        "message": "Prompt processato dall'AI agent",
        "prompt": prompt,
        "actions_generated": len(actions),
        "actions_executed": actions_executed,
        "raw_llm_response": raw_response
    }


@app.get("/agent/objectives", status_code=200)
async def get_agent_objectives():
    """Recupera obiettivi correnti dell'AI agent"""
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile")
    
    agent = get_agent()
    return agent.get_stats()


@app.post("/agent/objectives", status_code=200)
async def set_agent_objectives(objectives: dict):
    """
    Configura obiettivi dell'AI agent.
    
    Args:
        objectives: Dizionario con chiavi:
            - primary_objective: "maximize_sp", "maximize_reputation", etc.
            - target_skills: Lista di skills da specializzare
            - min_sp_reserve: SP minimi da mantenere
            - max_bid_percentage: % massima di SP per bid
            - auto_vote: bool
            - auto_apply_tasks: bool
            - auto_join_teams: bool
            - risk_tolerance: 0.0-1.0
    """
    if not is_agent_enabled():
        raise HTTPException(503, "AI Agent non disponibile")
    
    agent = get_agent()
    
    user_objectives = UserObjectives(
        primary_objective=AgentObjective(objectives.get("primary_objective", "balanced_participation")),
        target_skills=objectives.get("target_skills", []),
        min_sp_reserve=objectives.get("min_sp_reserve", 100),
        max_bid_percentage=objectives.get("max_bid_percentage", 0.3),
        auto_vote=objectives.get("auto_vote", True),
        auto_apply_tasks=objectives.get("auto_apply_tasks", True),
        auto_join_teams=objectives.get("auto_join_teams", True),
        risk_tolerance=objectives.get("risk_tolerance", 0.5)
    )
    
    agent.set_objectives(user_objectives)
    
    return {
        "message": "Obiettivi AI agent aggiornati",
        "objectives": agent.get_stats()["objectives"]
    }


@app.get("/agent/status", status_code=200)
async def get_agent_status():
    """Stato dell'AI agent"""
    agent = get_agent()
    
    if not agent:
        return {
            "enabled": False,
            "reason": "Agent not initialized",
            "model_path": os.getenv("AI_MODEL_PATH", "models/qwen3-0.6b.gguf")
        }
    
    return agent.get_stats()
```

---

## 📖 API Reference

### 1. POST /agent/prompt

Invia un prompt in linguaggio naturale all'AI agent.

**Request**:
```bash
curl -X POST "http://localhost:8001/agent/prompt?channel=dev" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Crea un task per fixare il bug della UI con reward 50 SP"}'
```

**Response**:
```json
{
  "message": "Prompt processato dall'AI agent",
  "prompt": "Crea un task per fixare il bug della UI con reward 50 SP",
  "actions_generated": 1,
  "actions_executed": [
    {
      "action": "create_task",
      "params": {
        "channel": "dev",
        "title": "Fix UI bug",
        "description": "Risolvere il bug dell'interfaccia utente",
        "reward": 50
      },
      "reasoning": "Utente ha richiesto creazione task con reward 50 SP",
      "status": "executed"
    }
  ],
  "raw_llm_response": "{\"action\": \"create_task\", ...}"
}
```

### 2. GET /agent/objectives

Recupera obiettivi correnti dell'AI agent.

**Request**:
```bash
curl "http://localhost:8001/agent/objectives"
```

**Response**:
```json
{
  "enabled": true,
  "node_id": "node-abc123",
  "model_path": "models/qwen3-0.6b.gguf",
  "objectives": {
    "primary": "maximize_synapse_points",
    "target_skills": ["python", "backend"],
    "min_sp_reserve": 100,
    "max_bid_percentage": 0.3,
    "auto_vote": true,
    "auto_apply_tasks": true,
    "auto_join_teams": true,
    "risk_tolerance": 0.5
  },
  "total_actions_executed": 5,
  "recent_actions": [...]
}
```

### 3. POST /agent/objectives

Configura obiettivi dell'AI agent.

**Request**:
```bash
curl -X POST "http://localhost:8001/agent/objectives" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_objective": "maximize_reputation",
    "target_skills": ["backend", "python", "fastapi"],
    "min_sp_reserve": 200,
    "max_bid_percentage": 0.2,
    "auto_vote": true,
    "auto_apply_tasks": false,
    "auto_join_teams": true,
    "risk_tolerance": 0.3
  }'
```

### 4. GET /agent/status

Verifica stato dell'AI agent.

**Request**:
```bash
curl "http://localhost:8001/agent/status"
```

---

## 🎯 Obiettivi Disponibili

L'AI agent può essere configurato con vari obiettivi primari:

| Obiettivo | Descrizione | Comportamento |
|-----------|-------------|---------------|
| `maximize_synapse_points` | Massimizza SP | Completa task, vince aste a basso costo |
| `maximize_reputation` | Massimizza reputazione | Vota su proposte, partecipa attivamente |
| `specialize_in_skills` | Specializza skills | Applica solo a task che matchano target_skills |
| `participate_in_governance` | Partecipa governance | Vota tutte le proposte, crea proposte |
| `join_collaborative_teams` | Unisciti a team | Candidati a team compositi |
| `win_valuable_auctions` | Vinci aste di valore | Bidda aggressivamente su aste profittevoli |
| `maintain_privacy_zkp` | Mantieni privacy | Vota sempre con ZKP |
| `balanced_participation` | Bilanciato | Mix di tutte le attività |

### Esempio Configurazione

```json
{
  "primary_objective": "maximize_synapse_points",
  "target_skills": ["python", "backend", "fastapi"],
  "min_sp_reserve": 100,
  "max_bid_percentage": 0.3,
  "auto_vote": true,
  "auto_apply_tasks": true,
  "auto_join_teams": true,
  "risk_tolerance": 0.5
}
```

**Parametri**:
- `min_sp_reserve`: SP minimi da non toccare mai (riserva di sicurezza)
- `max_bid_percentage`: % massima di SP da usare per bid (es. 0.3 = 30%)
- `auto_vote`: Se `true`, l'agent vota automaticamente su proposte aperte
- `auto_apply_tasks`: Se `true`, l'agent si candida automaticamente a task
- `auto_join_teams`: Se `true`, l'agent si candida a team compositi
- `risk_tolerance`: 0.0 = conservativo, 1.0 = aggressivo

---

## 💡 Esempi d'Uso

### Esempio 1: Creazione Task

**Prompt**:
> "Crea un task per implementare l'autenticazione JWT con reward 150 SP"

**Azione Generata**:
```json
{
  "action": "create_task",
  "params": {
    "channel": "dev",
    "title": "Implement JWT Authentication",
    "description": "Add JWT authentication to API endpoints",
    "reward": 150
  },
  "reasoning": "User requested task creation for JWT auth with 150 SP reward"
}
```

**Esecuzione**: Task creato automaticamente nel canale

---

### Esempio 2: Voto su Proposta

**Prompt**:
> "Vota YES sulla proposta per aumentare il timeout delle proposte, usa privacy"

**Azione Generata**:
```json
{
  "action": "vote_proposal",
  "params": {
    "channel": "governance",
    "proposal_id": "prop-123",
    "vote": "yes",
    "use_zkp": true
  },
  "reasoning": "User requested anonymous vote YES on timeout proposal"
}
```

**Esecuzione**: Voto anonimo con ZKP registrato

---

### Esempio 3: Bid su Asta

**Prompt**:
> "Bidda 200 SP sull'asta per il task di frontend"

**Azione Generata**:
```json
{
  "action": "bid_auction",
  "params": {
    "channel": "dev",
    "auction_id": "auc-456",
    "amount": 200
  },
  "reasoning": "User wants to bid 200 SP on frontend task auction"
}
```

**Validazione**: 
- ✓ Controlla che 200 SP non superi `max_bid_percentage` (es. 30% di 1000 SP = 300 SP)
- ✓ Controlla che dopo la bid rimangano almeno `min_sp_reserve` SP

**Esecuzione**: Bid registrata

---

### Esempio 4: Candidatura a Team

**Prompt**:
> "Candidati al team per il dashboard analytics project"

**Azione Generata**:
```json
{
  "action": "apply_team",
  "params": {
    "channel": "dev",
    "task_id": "tc-789"
  },
  "reasoning": "User wants to join the dashboard analytics team"
}
```

**Esecuzione**: Candidatura inviata al coordinatore

---

### Esempio 5: Aggiornamento Skills

**Prompt**:
> "Aggiungi React e TypeScript alle mie competenze"

**Azione Generata**:
```json
{
  "action": "update_skills",
  "params": {
    "skills": ["python", "fastapi", "docker", "react", "typescript"],
    "bio": "Full-stack developer with backend and frontend expertise"
  },
  "reasoning": "User wants to add React and TypeScript to their skill profile"
}
```

**Esecuzione**: Profilo skills aggiornato

---

## 🧠 Analisi Proattiva

L'agent esegue analisi proattiva ogni **5 minuti** (configurabile con `AGENT_PROACTIVE_INTERVAL`).

### Cosa Analizza

1. **Stato Rete**:
   - Synapse Points disponibili
   - Reputazione corrente
   - Peer connessi

2. **Opportunità**:
   - Task aperti
   - Proposte da votare
   - Aste attive
   - Team che reclutano

3. **Obiettivi**:
   - Primary objective (es. maximize_sp)
   - Target skills
   - Constraint (SP reserve, bid %)

### Azioni Autonome

Se l'agent rileva opportunità allineate con gli obiettivi:

**Esempio 1: Auto-Claim Task**
```
Opportunità: Task "Fix bug" (100 SP) aperto
Skill Match: 80% (python, backend)
Obiettivo: maximize_synapse_points
Decisione: Claim task automaticamente
```

**Esempio 2: Auto-Vote**
```
Opportunità: Proposta "Increase rewards" aperta
Beneficio: Aumenta SP per tutti
Obiettivo: maximize_synapse_points
Decisione: Vota YES (anonimo se enabled)
```

**Esempio 3: Auto-Bid**
```
Opportunità: Asta task (max 500 SP, current bid 200 SP)
Valutazione: Task vale più di 200 SP
Budget: 30% di 1000 SP = 300 SP disponibili
Decisione: Bid 250 SP
```

---

## 🔒 Sicurezza e Validazione

### Validazione Azioni

Prima di eseguire qualsiasi azione, l'agent valida:

1. **SP Constraints**:
   ```python
   if synapse_points - amount < min_sp_reserve:
       return False, "Azione ridurrebbe SP sotto la riserva"
   ```

2. **Bid Constraints**:
   ```python
   max_bid = synapse_points * max_bid_percentage
   if amount > max_bid:
       return False, f"Bid eccede il massimo consentito ({max_bid} SP)"
   ```

3. **Permission Constraints**:
   ```python
   if action.action == "vote_proposal" and not objectives.auto_vote:
       return False, "Auto-voting disabilitato negli obiettivi"
   ```

### Rate Limiting

- **Proactive Loop**: 1 analisi ogni 5 minuti (default)
- **Prompt API**: Nessun rate limit (ma limitato da costi LLM)

### Privacy

- L'agent gira **localmente** sul nodo
- Il modello GGUF è **offline**, nessun dato inviato a server esterni
- Le azioni sono **trasparenti** (logged)

---

## 📊 Monitoring e Logging

### Log Events

L'agent logga tutte le azioni:

```
[INFO] 🤖 Inizializzazione AI Agent con modello models/qwen3-0.6b.gguf...
[INFO] ✅ AI Agent inizializzato e pronto
[INFO] 🧠 Proactive agent loop avviato
[INFO] 🤔 Agent proattivo sta analizzando rete (SP:500, Rep:0.75, Peers:3)
[INFO] 🎯 Agent ha generato 2 azioni proattive
[INFO] ✅ Azione eseguita: claim_task - High reward task matches skills
[INFO] ✅ Azione eseguita: vote_proposal - Increase rewards benefits all
[WARNING] ⚠️ Azione rifiutata: bid_auction - Bid 200 eccede max allowed 150
```

### Statistiche

Recupera stats dell'agent:

```bash
curl "http://localhost:8001/agent/status" | jq '.recent_actions'
```

**Output**:
```json
[
  {
    "action": "claim_task",
    "params": {"channel": "dev", "task_id": "task-123"},
    "reasoning": "Task matches target skills and offers good reward"
  },
  {
    "action": "vote_proposal",
    "params": {"channel": "governance", "proposal_id": "prop-456", "vote": "yes"},
    "reasoning": "Proposal aligns with maximize_reputation objective"
  }
]
```

---

## 🧪 Testing

### Test Manuale

1. **Avvia nodo con AI agent**:
   ```bash
   AI_MODEL_PATH=models/qwen3-0.6b.gguf python3 app/main.py
   ```

2. **Invia prompt**:
   ```bash
   curl -X POST "http://localhost:8001/agent/prompt?channel=test" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Crea un task di test con reward 10 SP"}'
   ```

3. **Verifica stato**:
   ```bash
   curl "http://localhost:8001/state" | jq '.test.tasks'
   ```

### Test Script (TODO)

Creare `test_ai_agent.sh`:
```bash
#!/bin/bash
# Test AI Agent functionality

# 1. Verifica agent attivo
# 2. Configura obiettivi
# 3. Invia prompt di test
# 4. Verifica azioni eseguite
# 5. Testa analisi proattiva
```

---

## 🚀 Best Practices

### 1. Modello Giusto

- **Qwen3 0.6B**: Ottimo per dispositivi con 2-4GB RAM, veloce
- **Phi-2 2.7B**: Migliore qualità, richiede 4-6GB RAM
- **Mistral 7B Q4**: Massima qualità, richiede 8-12GB RAM

### 2. Obiettivi Bilanciati

```json
{
  "primary_objective": "balanced_participation",
  "min_sp_reserve": 100,
  "max_bid_percentage": 0.25,
  "auto_vote": true,
  "auto_apply_tasks": false,
  "risk_tolerance": 0.4
}
```

Evita:
- `max_bid_percentage` > 0.5 (rischio eccessivo)
- `min_sp_reserve` < 50 (riserva troppo bassa)
- `risk_tolerance` > 0.8 (comportamento troppo aggressivo)

### 3. Monitoring

Controlla regolarmente:
```bash
# Stats agent
curl http://localhost:8001/agent/status | jq

# Azioni recenti
curl http://localhost:8001/agent/status | jq '.recent_actions'

# SP correnti
curl http://localhost:8001/state | jq '.CHANNEL.synapse_points[NODE_ID]'
```

### 4. Privacy

Per massima privacy, abilita sempre ZKP:
```json
{
  "primary_objective": "maintain_privacy_zkp",
  "auto_vote": true
}
```

---

## 🔍 Troubleshooting

### Agent Non Si Avvia

**Problema**: `⚠️ AI Agent non disponibile (modello non caricato)`

**Soluzione**:
1. Verifica path modello:
   ```bash
   echo $AI_MODEL_PATH
   ls -lh models/
   ```
2. Reinstalla llama-cpp-python:
   ```bash
   pip uninstall llama-cpp-python
   pip install llama-cpp-python --no-cache-dir
   ```

### Prompt Non Generano Azioni

**Problema**: `actions_generated: 0`

**Soluzione**:
- Riformula prompt in modo più esplicito
- Esempio: "Vota sulla proposta 123" → "Vota YES sulla proposta con ID prop-123 nel canale governance"

### Azioni Sempre Rifiutate

**Problema**: `status: "rejected", reason: "..."`

**Soluzione**:
- Controlla obiettivi:
  ```bash
  curl http://localhost:8001/agent/objectives
  ```
- Aumenta `max_bid_percentage` se necessario
- Riduci `min_sp_reserve` se troppo alto

### LLM Lento

**Problema**: Generazione richiede > 5 secondi

**Soluzione**:
- Usa modello più piccolo (Qwen3 0.6B instead of Mistral 7B)
- Compila llama-cpp-python con accelerazione:
  ```bash
  CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python  # macOS
  CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python # NVIDIA GPU
  ```

---

## 📚 Riferimenti

- **llama-cpp-python**: https://github.com/abetlen/llama-cpp-python
- **Qwen Models**: https://huggingface.co/Qwen
- **GGUF Format**: https://github.com/ggerganov/llama.cpp
- **AI Agent Source**: `app/ai_agent.py`

---

## 🎓 FAQ

**Q: L'agent può fare azioni dannose?**  
A: No. Tutte le azioni sono validate contro gli obiettivi dell'utente e i constraint di SP. Puoi disabilitare azioni specifiche (es. `auto_vote: false`).

**Q: Quanto costa in termini di risorse?**  
A: Modello Qwen3 0.6B: ~1GB RAM, CPU ~10-20% durante generazione, idle altrimenti.

**Q: Posso usare GPT-4 o Gemini?**  
A: Il sistema è progettato per modelli locali (privacy, offline). Per API esterne, dovresti modificare `LLMEngine`.

**Q: L'agent può imparare dai miei comportamenti?**  
A: Attualmente no. Puoi configurare manualmente gli obiettivi. Future versioni potrebbero includere RL (Reinforcement Learning).

**Q: Come disabilito l'agent?**  
A: Non impostare `AI_MODEL_PATH` o rimuovi il modello GGUF. L'agent non si avvierà.

---

**Versione**: 1.0.0  
**Data**: 2025-10-02  
**Autore**: Synapse-NG Development Team  
**Status**: ✅ Modulo Completo (Integrazione Manuale Richiesta)
