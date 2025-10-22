# 🧬 Sistema di Reputazione v2: Dinamico e Specializzato

## 📋 Panoramica

Il sistema di reputazione di Synapse-NG è stato evoluto da un semplice contatore integer a un sistema dinamico, specializzato e contestuale che traccia:

1. **Reputazione totale** (`_total`) - somma di tutte le specializzazioni
2. **Specializzazioni per tag** (`tags`) - expertise in aree specifiche
3. **Timestamp ultimo aggiornamento** (`_last_updated`) - per il decadimento
4. **Decadimento automatico** - incentiva attività continua
5. **Voto ponderato contestuale** - expertise influenza le decisioni

---

## 🏗️ Struttura Dati

### Formato v2 della Reputazione

```json
{
  "_total": 150,
  "_last_updated": "2025-10-23T10:00:00Z",
  "tags": {
    "python": 50,
    "security": 70,
    "testing": 20,
    "bug-hunting": 10
  }
}
```

### Campi

- **`_total`**: Reputazione totale, somma di tutti i valori nei tag
- **`_last_updated`**: Timestamp ISO 8601 dell'ultimo aggiornamento
- **`tags`**: Dict {tag_name: reputation_points} che traccia specializzazioni

---

## 🔄 Migrazione Automatica

Il sistema migra automaticamente le vecchie reputazioni integer al nuovo formato:

```python
# Vecchio formato
"reputation": 100

# Nuovo formato (dopo migrazione)
"reputation": {
  "_total": 100,
  "_last_updated": "2025-10-23T10:00:00Z",
  "tags": {}
}
```

### Funzioni di Migrazione

- `migrate_reputation_to_v2(old_reputation: int) -> dict`
- `ensure_reputation_v2_format(reputation: any) -> dict`

---

## 📈 Guadagno di Reputazione

Quando un nodo completa un task, la reputazione viene aggiornata:

### Esempio

**Task completato:**
```json
{
  "title": "Implementare autenticazione",
  "tags": ["python", "security"],
  "reward": 10
}
```

**Nodo prima:**
```json
{
  "_total": 100,
  "tags": {
    "python": 30
  }
}
```

**Nodo dopo:**
```json
{
  "_total": 120,
  "tags": {
    "python": 40,    // +10
    "security": 10    // nuovo tag
  }
}
```

### Logica

```python
def update_reputation_on_task_complete(reputation, task_tags, reward_points):
    for tag in task_tags:
        reputation["tags"][tag] += reward_points  # crea se non esiste
    reputation["_total"] += reward_points
    reputation["_last_updated"] = now()
    return reputation
```

---

## ⏳ Decadimento della Reputazione

Il sistema applica un decadimento giornaliero per incentivare l'attività continua.

### Parametri

- **Frequenza**: Ogni 24 ore
- **Decay Factor**: 0.99 (-1% al giorno)
- **Soglia Minima**: 0.1 (tag sotto questa soglia vengono rimossi)

### Algoritmo

```python
async def reputation_decay_loop():
    while True:
        await asyncio.sleep(24 * 60 * 60)  # 24 ore
        
        for node in all_nodes:
            for tag, value in node.reputation["tags"]:
                new_value = value * 0.99  # -1%
                
                if new_value < 0.1:
                    remove tag
                else:
                    node.reputation["tags"][tag] = new_value
            
            # Ricalcola _total come somma dei tag
            node.reputation["_total"] = sum(tag_values)
```

### Esempio di Evoluzione

| Giorno | Python | Security | Testing | Total |
|--------|--------|----------|---------|-------|
| 0 | 100.0 | 50.0 | 10.0 | 160.0 |
| 1 | 99.0 | 49.5 | 9.9 | 158.4 |
| 7 | 93.2 | 46.6 | 9.3 | 149.1 |
| 30 | 73.9 | 36.9 | 7.4 | 118.2 |
| 90 | 40.5 | 20.3 | 4.1 | 64.9 |

**Insight**: Un nodo inattivo perde circa 26% della reputazione in un mese, ~60% in 3 mesi.

---

## 🎯 Voto Ponderato Contestuale

Il peso di un voto dipende sia dalla reputazione totale che dall'expertise nei tag della proposta.

### Formula

```
total_weight = base_weight + bonus_weight

dove:
  base_weight = 1 + log2(_total + 1)
  bonus_weight = log2(specialization_score + 1)
  specialization_score = sum(reputation["tags"][tag] for tag in proposal.tags)
```

### Esempio Reale

**Votante:**
```json
{
  "_total": 1023,
  "tags": {
    "security": 500,
    "python": 100,
    "testing": 50
  }
}
```

**Proposta A** - `["security", "refactor"]`:
```
base_weight = log2(1023 + 1) = 10.0
specialization_score = 500 (security) + 0 (refactor) = 500
bonus_weight = log2(500 + 1) ≈ 8.9
total_weight = 10.0 + 8.9 = 18.9
```

**Proposta B** - `["frontend", "ui"]`:
```
base_weight = 10.0
specialization_score = 0 + 0 = 0
bonus_weight = log2(0 + 1) = 0
total_weight = 10.0 + 0 = 10.0
```

**Insight**: Il votante ha quasi **doppia influenza** su proposte di security rispetto a proposte generiche!

---

## 🔧 API e Funzioni

### Funzioni Core

```python
# Migrazione
ensure_reputation_v2_format(reputation) -> dict

# Aggiornamento
update_reputation_on_task_complete(
    reputation: dict,
    task_tags: List[str],
    reward_points: int
) -> dict

# Calcolo peso voto
calculate_contextual_vote_weight(
    reputation: dict,
    proposal_tags: List[str]
) -> float

# Background task
reputation_decay_loop()
```

### Endpoint Modificati

- **GET `/state`**: Ora restituisce reputazioni in formato v2
- **POST `/proposals/{id}/vote`**: Usa peso contestuale automaticamente
- **GET `/whoami`**: Include breakdown delle specializzazioni

---

## 🎨 Esempi d'Uso

### 1. Creare Task con Tag Appropriati

```bash
curl -X POST "http://localhost:8001/tasks?channel=sviluppo_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implementare login OAuth",
    "tags": ["python", "security", "authentication"],
    "reward": 15
  }'
```

### 2. Verificare Reputazione di un Nodo

```bash
curl -s http://localhost:8001/state | jq '.global.nodes["NODE_ID"].reputation'
```

Output:
```json
{
  "_total": 150,
  "_last_updated": "2025-10-23T15:30:00Z",
  "tags": {
    "python": 60,
    "security": 50,
    "testing": 30,
    "bug-hunting": 10
  }
}
```

### 3. Creare Proposta con Tag per Voto Specializzato

```bash
curl -X POST "http://localhost:8001/proposals?channel=global" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Upgrade security protocols",
    "tags": ["security", "cryptography"],
    "proposal_type": "protocol_upgrade"
  }'
```

---

## 📊 Metriche e Monitoraggio

### Metriche Chiave da Tracciare

1. **Distribuzione Specializzazioni**
   - Quanti nodi hanno expertise in ciascun tag?
   - Quali tag sono più richiesti?

2. **Efficacia Decadimento**
   - Tasso di retention dei nodi attivi
   - Impatto sulla distribuzione del voto

3. **Impatto Voto Contestuale**
   - Differenza media tra peso base e peso totale
   - Correlazione tra expertise e outcome votazioni

### Query Esempio

```python
# Top nodi per security expertise
nodes_by_security = sorted(
    nodes,
    key=lambda n: n.reputation["tags"].get("security", 0),
    reverse=True
)[:10]

# Tag più popolari
tag_popularity = {}
for node in nodes:
    for tag in node.reputation["tags"]:
        tag_popularity[tag] = tag_popularity.get(tag, 0) + 1
```

---

## 🚀 Vantaggi del Sistema v2

### 1. **Meritocracy Specializzata**
- Nodi esperti hanno più influenza in aree di competenza
- Riduce rischio di voti "ignoranti"

### 2. **Incentivo Attività Continua**
- Decadimento premia chi contribuisce regolarmente
- Previene accumulazione passiva di potere

### 3. **Trasparenza Skills**
- La reputazione mostra chiaramente le expertise
- Facilita team matching per task complessi

### 4. **Flessibilità**
- Sistema adattivo: nuovi tag emergono organicamente
- Nessuna categorizzazione rigida predefinita

### 5. **Governance Migliore**
- Decisioni tecniche prese da esperti del dominio
- Maggiore legittimità degli outcome

---

## 🔮 Evoluzioni Future

### Phase 2: Cross-Tag Synergies
```json
"synergies": {
  "python+security": 1.2,  // bonus 20% quando combinati
  "testing+bug-hunting": 1.15
}
```

### Phase 3: Reputation Staking
- Nodi possono "stakare" reputazione su proposte
- Reward/penalty basati su outcome

### Phase 4: Peer Reviews
- Nodi possono validare l'expertise altrui
- Sistema di endorsement

### Phase 5: ML-Based Decay
- Decadimento adattivo basato su pattern storici
- Predizione churn e early warnings

---

## 📝 Migration Checklist

- [x] Struttura dati v2 implementata
- [x] Funzioni di migrazione automatica
- [x] `calculate_reputations()` aggiornata con tag support
- [x] `reputation_decay_loop()` implementato
- [x] `calculate_contextual_vote_weight()` implementato
- [x] Endpoint `/state` aggiornato
- [x] Sistema di voto aggiornato
- [x] Decay loop aggiunto a startup
- [ ] Test automatici per reputazione v2
- [ ] Dashboard visualizzazione specializzazioni
- [ ] Documentazione API aggiornata
- [ ] Migration guide per nodi esistenti

---

## 🎓 Best Practices

### Per Task Creators

1. **Usa tag specifici e descrittivi**
   - ✅ `["python", "async", "websocket"]`
   - ❌ `["code", "backend"]`

2. **Bilancia reward con complessità**
   - Task multi-tag dovrebbero avere reward maggiori
   - Considera expertise richiesta

3. **Aggiorna tag se necessario**
   - Aggiungi nuovi tag emergenti
   - Mantieni nomenclatura consistente

### Per Contributors

1. **Specializzati strategicamente**
   - Costruisci expertise in 2-3 aree chiave
   - Diversifica per evitare decay totale

2. **Contribuisci regolarmente**
   - Decadimento punisce inattività
   - Mantieni momentum su tag importanti

3. **Vota su proposte rilevanti**
   - Massimizza impatto votando su tag di expertise
   - Astieniti su aree fuori competenza

---

## 📚 Riferimenti

- [Algoritmi di Decadimento Temporale](https://en.wikipedia.org/wiki/Time_decay)
- [Weighted Voting Systems](https://en.wikipedia.org/wiki/Weighted_voting)
- [Reputation Systems Design](https://www.sciencedirect.com/topics/computer-science/reputation-system)
- [Stack Overflow Reputation System](https://stackoverflow.com/help/whats-reputation)

---

**Versione**: 2.0.0  
**Data**: 23 Ottobre 2025  
**Autore**: Synapse-NG Core Team  
**Status**: ✅ Implementato e Attivo
