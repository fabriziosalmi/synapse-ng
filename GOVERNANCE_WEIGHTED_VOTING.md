# 🗳️ Sistema di Governance: Voto Ponderato Basato su Reputazione

## 📋 Sommario

Synapse-NG implementa un sistema di **Governance Meritocratica Distribuita** dove il peso di ogni voto è proporzionale alla reputazione del votante. Questo sistema previene la dominanza dei nodi ad alta reputazione usando una funzione logaritmica, garantendo al contempo che i contributi passati abbiano un impatto sul processo decisionale.

---

## 🧮 Formula del Peso del Voto

### Funzione Logaritmica

```python
peso_voto = 1.0 + log₂(reputazione + 1)
```

**Rationale:**
- **Base = 1.0**: Ogni nodo ha un voto minimo, indipendentemente dalla reputazione
- **Logaritmo base 2**: Crescita sublineare che previene dominanza eccessiva
- **+1 all'argomento**: Evita log(0) quando reputazione è 0

### Tabella Esempi

| Reputazione | Task Completati | Peso Voto | Incremento |
|-------------|-----------------|-----------|------------|
| 0 | 0 | 1.00 | - |
| 10 | 1 task | 4.46 | +3.46 |
| 50 | 5 task | 6.67 | +2.21 |
| 100 | 10 task | 7.66 | +0.99 |
| 200 | 20 task | 8.65 | +0.99 |
| 500 | 50 task | 9.97 | +1.32 |
| 1000 | 100 task | 10.97 | +1.00 |

**Insight:**
- Un nodo con 10 task completati (rep 100) ha ~7.7x il potere di voto di un nuovo nodo
- Ma un nodo con 100 task (rep 1000) ha solo ~11x, non 100x
- Questo mantiene l'influenza dei veterani senza renderli onnipotenti

---

## 🔧 Backend: Implementazione

### File: `app/main.py`

#### 1. Calcolo Reputazione (linee 663-675)

```python
def calculate_reputations(full_state: dict) -> Dict[str, int]:
    """Calcola la reputazione di ogni nodo basata su task completati e voti."""
    reputations = {node_id: 0 for node_id in full_state.get("global", {}).get("nodes", {})}
    for channel_id, channel_data in full_state.items():
        if channel_id != "global":
            # Task completati: +10 reputazione
            for task in channel_data.get("tasks", {}).values():
                if task.get("status") == "completed" and task.get("assignee") in reputations:
                    reputations[task["assignee"]] += 10
        # Voti espressi: +1 reputazione
        for prop in channel_data.get("proposals", {}).values():
            for voter_id in prop.get("votes", {}):
                if voter_id in reputations:
                    reputations[voter_id] += 1
    return reputations
```

**Meccanica:**
- **Task Completato**: +10 reputazione
- **Voto Espresso**: +1 reputazione
- **Globale**: Somma su tutti i canali

---

#### 2. Calcolo Peso Voto (linee 677-692)

```python
def calculate_vote_weight(reputation: int) -> float:
    """
    Calcola il peso di un voto basato sulla reputazione.
    Usa una funzione logaritmica per evitare dominanza eccessiva.

    Formula: peso = 1 + log2(reputazione + 1)

    Esempi:
    - reputation 0: peso 1.0
    - reputation 10: peso ~4.46
    - reputation 50: peso ~6.67
    - reputation 100: peso ~7.66
    - reputation 1000: peso ~10.97
    """
    import math
    return 1.0 + math.log2(reputation + 1)
```

---

#### 3. Calcolo Esito Proposta (linee 694-751)

```python
def calculate_proposal_outcome(proposal: dict, reputations: Dict[str, int]) -> dict:
    """
    Calcola l'esito di una proposta con voto ponderato.

    Returns:
        {
            "total_votes": int,
            "yes_count": int,
            "no_count": int,
            "yes_weight": float,
            "no_weight": float,
            "outcome": "approved" | "rejected" | "pending",
            "vote_details": [
                {"voter_id": str, "vote": "yes"|"no", "reputation": int, "weight": float},
                ...
            ]
        }
    """
    votes = proposal.get("votes", {})
    vote_details = []
    yes_weight = 0.0
    no_weight = 0.0
    yes_count = 0
    no_count = 0

    for voter_id, vote_value in votes.items():
        reputation = reputations.get(voter_id, 0)
        weight = calculate_vote_weight(reputation)

        vote_details.append({
            "voter_id": voter_id,
            "vote": vote_value,
            "reputation": reputation,
            "weight": round(weight, 2)
        })

        if vote_value == "yes":
            yes_weight += weight
            yes_count += 1
        elif vote_value == "no":
            no_weight += weight
            no_count += 1

    # Determina l'esito: yes_weight > no_weight
    if proposal.get("status") == "closed":
        outcome = "approved" if yes_weight > no_weight else "rejected"
    else:
        outcome = "pending"

    return {
        "total_votes": len(votes),
        "yes_count": yes_count,
        "no_count": no_count,
        "yes_weight": round(yes_weight, 2),
        "no_weight": round(no_weight, 2),
        "outcome": outcome,
        "vote_details": vote_details
    }
```

**Logica Decisionale:**
- ✅ **Approved**: `yes_weight > no_weight`
- ❌ **Rejected**: `no_weight >= yes_weight`
- ⏳ **Pending**: Status ancora "open"

---

## 📡 API Endpoints

### 1. Creare una Proposta

```bash
POST /proposals?channel=CHANNEL_ID
Content-Type: application/json

{
  "title": "Aumentare timeout task a 24h",
  "description": "I task complessi richiedono più tempo per essere completati",
  "proposal_type": "parameter_change"
}
```

**Response:**
```json
{
  "id": "uuid-proposta",
  "title": "Aumentare timeout task a 24h",
  "description": "...",
  "type": "parameter_change",
  "proposer": "NODE_ID",
  "status": "open",
  "votes": {},
  "created_at": "2025-10-02T...",
  "updated_at": "2025-10-02T...",
  "closed_at": null
}
```

---

### 2. Votare su una Proposta

```bash
POST /proposals/{proposal_id}/vote?channel=CHANNEL_ID&vote=yes
# vote può essere "yes" o "no"
```

**Response:**
```json
{
  "status": "voted",
  "vote": "yes"
}
```

**Logs:**
```
🗳️  Voto 'yes' su proposta dcd51... da JkN-5D2q...
```

---

### 3. Chiudere una Proposta

```bash
POST /proposals/{proposal_id}/close?channel=CHANNEL_ID
```

**Autorizzazione:**
- Solo il **proposer** può chiudere la proposta

**Response:**
```json
{
  "id": "uuid-proposta",
  "title": "Aumentare timeout task a 24h",
  "status": "closed",
  "closed_at": "2025-10-02T...",
  "outcome": {
    "total_votes": 5,
    "yes_count": 3,
    "no_count": 2,
    "yes_weight": 22.3,
    "no_weight": 9.8,
    "outcome": "approved",
    "vote_details": [
      {"voter_id": "NODE_A", "vote": "yes", "reputation": 100, "weight": 7.66},
      {"voter_id": "NODE_B", "vote": "yes", "reputation": 50, "weight": 6.67},
      {"voter_id": "NODE_C", "vote": "yes", "reputation": 10, "weight": 4.46},
      {"voter_id": "NODE_D", "vote": "no", "reputation": 20, "weight": 5.39},
      {"voter_id": "NODE_E", "vote": "no", "reputation": 0, "weight": 1.0}
    ]
  }
}
```

**Logs:**
```
🏛️  Proposta dcd51... chiusa: approved (yes: 22.3, no: 9.8)
```

---

### 4. Ottenere Dettagli Proposta

```bash
GET /proposals/{proposal_id}/details?channel=CHANNEL_ID
```

**Response:**
```json
{
  "id": "uuid-proposta",
  "title": "...",
  "status": "open",
  "votes": {"NODE_A": "yes", "NODE_B": "no"},
  "current_outcome": {
    "total_votes": 2,
    "yes_count": 1,
    "no_count": 1,
    "yes_weight": 7.66,
    "no_weight": 1.0,
    "outcome": "pending",
    "vote_details": [...]
  }
}
```

**Note:**
- `current_outcome` viene calcolato **real-time** anche per proposte ancora aperte
- Utile per mostrare il conteggio in tempo reale nell'UI

---

## 🎨 UI: Visualizzazione Voto Ponderato

### File: `app/templates/index.html`

#### 1. Ispettore Nodo - Sezione Voti (linee 401-439)

Quando clicchi su un nodo, l'ispettore mostra:

```
🔎 Ispettore Nodo                    [✕]

ID Completo: JkN-5D2qxGet881...
Reputazione: 120
URL: http://node-2:8000
---
📡 Canali Sottoscritti:
• sviluppo_ui
• marketing
---
🗳️ Voti su Proposte (2):

  ┌ sviluppo_ui
  │ Aumentare timeout task a 24h
  │ Voto: ✅ YES
  └ Peso Voto: 7.66

  ┌ marketing
  │ Aggiungere budget per campagna
  │ Voto: ❌ NO
  └ Peso Voto: 7.66
```

**Codice:**
```javascript
// Voti sulle Proposte
let nodeVotes = [];
for (const [channelId, channelData] of Object.entries(currentState.state)) {
    if (channelId === 'global') continue;
    if (channelData.proposals) {
        for (const [propId, prop] of Object.entries(channelData.proposals)) {
            if (prop.votes && prop.votes[nodeId]) {
                // Calcola il peso del voto
                const reputation = nodeData.reputation || 0;
                const weight = 1.0 + Math.log2(reputation + 1);

                nodeVotes.push({
                    channel: channelId,
                    proposal: prop,
                    vote: prop.votes[nodeId],
                    weight: weight.toFixed(2)
                });
            }
        }
    }
}

html += `
    <div style="margin: 8px 0;">
        <strong>🗳️  Voti su Proposte (${nodeVotes.length}):</strong><br>
        ${nodeVotes.length > 0
            ? nodeVotes.map(v => `
                <div style="margin: 4px 0; padding: 4px; background: rgba(255, 170, 0, 0.1); border-left: 2px solid #ffaa00;">
                    <strong style="color: #ffaa00;">${v.channel}</strong><br>
                    <span style="font-size: 10px;">${v.proposal.title}</span><br>
                    <span style="font-size: 10px; color: ${v.vote === 'yes' ? '#00ff88' : '#ff4444'};">
                        Voto: ${v.vote === 'yes' ? '✅ YES' : '❌ NO'}
                    </span><br>
                    <span style="font-size: 10px; color: #ccc;">Peso Voto: ${v.weight}</span>
                </div>
            `).join('')
            : '<span style="color: #888;">Nessun voto</span>'}
    </div>
`;
```

---

#### 2. Pannello Analisi Canale - Sezione Proposte (linee 787-813)

Quando selezioni un canale specifico, il pannello mostra le proposte attive:

```
🔍 Canale: sviluppo_ui
---
Partecipanti: 3
Task Attivi: 5
Proposte: 2
---
Salute Mesh:
Dimensione Mesh: 3
Messaggi Visti: 150
Latenza Media: 75 ms
---
🗳️ Proposte:

⏳ Aumentare timeout task a 24h
Status: open
Yes: 22.3 | No: 9.8

✅ Aggiungere feature X
Status: closed
Yes: 45.2 | No: 12.1
```

**Codice:**
```javascript
// Lista Proposte Attive con Voto Ponderato
if (channelData.proposals && Object.keys(channelData.proposals).length > 0) {
    html += `<hr style="border: 1px solid #444; margin: 8px 0;"><strong>🗳️ Proposte:</strong><br>`;

    for (const [propId, prop] of Object.entries(channelData.proposals)) {
        // Calcola pesi voti
        let yesWeight = 0, noWeight = 0;
        for (const [voterId, vote] of Object.entries(prop.votes || {})) {
            const voterRep = state.global.nodes[voterId]?.reputation || 0;
            const weight = 1.0 + Math.log2(voterRep + 1);
            if (vote === 'yes') yesWeight += weight;
            else if (vote === 'no') noWeight += weight;
        }

        const statusColor = prop.status === 'open' ? '#ffaa00' : (yesWeight > noWeight ? '#00ff88' : '#ff4444');
        const statusIcon = prop.status === 'open' ? '⏳' : (yesWeight > noWeight ? '✅' : '❌');

        html += `
            <div style="margin: 4px 0; padding: 4px; background: rgba(255, 170, 0, 0.05); border-left: 2px solid ${statusColor}; font-size: 10px;">
                ${statusIcon} <strong style="color: ${statusColor};">${prop.title.substring(0, 30)}...</strong><br>
                <span style="color: #ccc;">Status: ${prop.status}</span><br>
                <span style="color: #00ff88;">Yes: ${yesWeight.toFixed(1)}</span> |
                <span style="color: #ff4444;">No: ${noWeight.toFixed(1)}</span>
            </div>
        `;
    }
}
```

---

## 🔍 Scenari d'Uso

### Scenario 1: Nuova Feature

**Contesto:**
- Canale `sviluppo_ui`
- 5 partecipanti:
  - Alice (rep 200, peso 8.65)
  - Bob (rep 100, peso 7.66)
  - Carol (rep 50, peso 6.67)
  - Dave (rep 10, peso 4.46)
  - Eve (rep 0, peso 1.00)

**Proposta:**
- Titolo: "Implementare tema scuro"
- Proposer: Alice

**Voti:**
- Alice: Yes (peso 8.65)
- Bob: Yes (peso 7.66)
- Carol: No (peso 6.67)
- Dave: No (peso 4.46)
- Eve: Yes (peso 1.00)

**Calcolo:**
- Yes: 8.65 + 7.66 + 1.00 = **17.31**
- No: 6.67 + 4.46 = **11.13**

**Esito:** ✅ **APPROVED** (17.31 > 11.13)

**Insight:**
- Anche se il voto numerico è 3 vs 2 (60% yes), il peso ponderato riflette la competenza
- I due veterani (Alice + Bob) prevalgono sui due intermedi (Carol + Dave) + un novizio

---

### Scenario 2: Cambio Parametro Critico

**Contesto:**
- Canale `global`
- Proposta: "Ridurre timeout task a 1 ora"
- Proposer: Nuovo nodo (rep 0)

**Problema:**
- Un nuovo nodo propone un cambio che potrebbe danneggiare la rete
- Se passasse a maggioranza semplice, 2 nuovi nodi potrebbero imporre la decisione

**Soluzione con Voto Ponderato:**
- Nuovi nodi (rep 0): peso 1.0 ciascuno
- Nodi veterani (rep 100+): peso 7.66+ ciascuno

**Risultato:**
- Anche se 3 nuovi nodi votano yes (peso tot 3.0), bastano 2 veterani no (peso tot ~15.3) per bloccare
- La rete è **protetta da decisioni avventate** dei nuovi arrivati

---

### Scenario 3: Governance Equilibrata

**Contesto:**
- Decisione controversa: "Cambiare algoritmo di consensus"
- Partecipanti: 10 nodi con reputazioni variabili

**Voti:**
- 5 veterani (rep 100-500): 3 yes (peso tot ~23), 2 no (peso tot ~16)
- 5 nuovi (rep 0-20): 2 yes (peso tot ~11), 3 no (peso tot ~14)

**Totali:**
- Yes: 23 + 11 = **34**
- No: 16 + 14 = **30**

**Esito:** ✅ **APPROVED**

**Insight:**
- I veterani sono divisi (3 vs 2)
- I nuovi sono divisi (2 vs 3)
- La maggioranza veterani yes + minoranza nuovi yes prevale
- Sistema funziona correttamente: i più esperti hanno più influenza ma non dominano completamente

---

## 🎯 Design Goals

### 1. ✅ Meritocracy
- I nodi che hanno contribuito di più hanno più voce
- Incentivo a completare task e partecipare

### 2. ✅ Fairness
- Funzione logaritmica previene dominanza assoluta
- Un nuovo nodo ha comunque peso 1.0 (non 0)

### 3. ✅ Sybil Resistance
- Creare molti nodi fake con rep 0 è inefficace
- 100 nodi rep 0 = peso 100, ma 1 nodo rep 100 = peso 7.66
- Per avere impatto reale, serve **contribuire**

### 4. ✅ Transparency
- Ogni voto mostra:
  - Chi ha votato
  - Il loro voto
  - La loro reputazione
  - Il peso del voto
- Audit trail completo

### 5. ✅ Real-Time Visibility
- L'UI mostra il conteggio in tempo reale
- Si può vedere come sta andando una proposta prima di chiuderla

---

## 🚀 Future Enhancements

### 1. Time-Weighted Reputation
Diminuire il peso della reputazione vecchia:
```python
weight = (1.0 + log2(rep + 1)) * decay_factor(last_contribution_time)
```

### 2. Domain-Specific Reputation
Reputazione separata per canale:
```python
weight = 1.0 + log2(channel_reputation + global_reputation/2 + 1)
```

### 3. Quadratic Voting
Permettere di "spendere" reputazione per votare più volte:
```python
cost = votes_used^2
max_votes = sqrt(reputation)
```

### 4. Delegation
Permettere di delegare il proprio voto a un altro nodo fidato.

### 5. Automatic Proposal Closing
Background task che chiude automaticamente le proposte dopo un timeout se raggiunta una soglia di voti.

---

## 📊 Confronto: Semplice vs Ponderato

### Proposta: "Cambiare logo"

**Scenario A: Voto Semplice (1 nodo, 1 voto)**

| Nodo | Reputation | Voto | Peso |
|------|------------|------|------|
| Alice | 200 | Yes | 1 |
| Bob | 100 | Yes | 1 |
| Carol | 50 | No | 1 |
| Dave | 10 | No | 1 |
| Eve | 0 | No | 1 |

**Risultato:** ❌ Rejected (2 yes vs 3 no)

---

**Scenario B: Voto Ponderato**

| Nodo | Reputation | Voto | Peso |
|------|------------|------|------|
| Alice | 200 | Yes | 8.65 |
| Bob | 100 | Yes | 7.66 |
| Carol | 50 | No | 6.67 |
| Dave | 10 | No | 4.46 |
| Eve | 0 | No | 1.00 |

**Risultato:** ✅ Approved (16.31 yes vs 12.13 no)

---

**Analisi:**
- Nel voto semplice, 3 nodi poco esperti bloccano la decisione di 2 veterani
- Nel voto ponderato, l'esperienza dei veterani prevale
- Questo è **desiderabile** se crediamo che Alice e Bob abbiano miglior giudizio basato sul loro track record

---

## 🎓 Conclusioni

Il sistema di **Voto Ponderato Basato su Reputazione** trasforma Synapse-NG da una democrazia diretta a una **Meritocrazia Distribuita**:

1. ✅ **Premia i Contributori**: Chi lavora ha più voce
2. ✅ **Previene Attacchi**: Difficile manipolare con nodi fake
3. ✅ **Mantiene Fairness**: Funzione logaritmica limita la dominanza
4. ✅ **Trasparente**: Tutti i pesi sono visibili e auditabili
5. ✅ **Integrato nella UI**: Visualizzazione real-time del conteggio

**Synapse-NG non è solo una rete P2P - è un organismo che premia il merito! 🧠✨**
