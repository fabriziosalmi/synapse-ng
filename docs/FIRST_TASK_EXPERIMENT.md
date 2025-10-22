# 🧪 First Task Experiment - "Find the First Bug"

**Il primo micro-esperimento per dimostrare il principio fondamentale di Synapse-NG**

> **Principio**: Contributo → Valore. Niente gerarchie, niente approvazioni. Solo contratti digitali auto-eseguibili.

---

## 🎯 Obiettivo

Dimostrare che Synapse-NG funziona come un organismo economico autonomo dove:

1. ✅ Un task viene creato con una reward specifica
2. ✅ Qualcuno lo completa (fornisce valore)
3. ✅ Riceve automaticamente il valore promesso (Synapse Points)
4. ✅ La sua reputazione aumenta
5. ✅ Tutti i nodi della rete concordano su questo nuovo stato
6. ✅ Nessun manager ha approvato nulla. Il sistema si auto-esegue.

---

## 📋 Il Task

### Titolo
**"Trovare il primo bug in Synapse-NG"**

### Descrizione
```
Esplora il sistema Synapse-NG e documenta il primo comportamento inatteso, 
errore, o problema che trovi.

Per completare questo task:
1. Interagisci con il sistema (crea task, vota, fai claim, ecc.)
2. Documenta il bug trovato creando un'issue su GitHub
3. Fai claim di questo task
4. Fai complete del task inserendo il link all'issue nel campo "proof"

Reward: 10 SP (simbolico ma reale)
```

### Reward
- **10 Synapse Points** (SP)
- **+10 Reputation** (guadagnato al completamento)

### Valore Simbolico
Non stiamo salvando il mondo. Stiamo testando il **core loop** del sistema:
- Il contributore fornisce valore reale (trova un bug)
- Il sistema fornisce valore reale (SP + reputazione)
- Nessuna intermediazione umana necessaria

---

## 🚀 Come Eseguire l'Esperimento

### Opzione A: Script Automatizzato (Consigliato)

**Script Standard:**
```bash
# Avvia la rete
docker-compose up -d
sleep 15

# Esegui il test
./test_first_task_experiment.sh
```

**Script Enhanced (con metriche dettagliate):**
```bash
# Avvia la rete
docker-compose up -d
sleep 15

# Esegui il test con analisi avanzata
./test_first_task_experiment_enhanced.sh

# Analizza i risultati
./analyze_experiment.py metrics_*.json
```

**Output dello script enhanced:**
- Log dettagliato: `experiment_*.log`
- Metriche JSON: `metrics_*.json`
- Timing preciso al millisecondo
- Tabelle formattate con analisi economica
- Report markdown generato automaticamente

### Opzione B: Esecuzione Manuale (Passo-passo)

### Step 1: Avvia la Rete (3 nodi)

```bash
# In terminal 1
docker-compose up

# Verifica che tutti e 3 i nodi siano online
curl http://localhost:8001/health  # Nodo 1
curl http://localhost:8002/health  # Nodo 2
curl http://localhost:8003/health  # Nodo 3
```

### Step 2: Crea il Task (Tu, il Creator)

```bash
# Cattura NODE_ID del Nodo 1 (il creator)
NODE1_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | keys[0]')

# Verifica balance iniziale
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance"
# Expected: 1000 SP

# Crea il task
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trovare il primo bug in Synapse-NG",
    "description": "Esplora il sistema e documenta il primo comportamento inatteso. Crea un issue su GitHub come prova del completamento.",
    "reward": 10,
    "tags": ["testing", "bug-hunting", "first-contribution"]
  }'

# Salva task_id dalla response
```

**Cosa succede:**
- Il Nodo 1 perde 10 SP (congelati)
- Task propagato via gossip a Nodo 2 e Nodo 3
- Status = `open`

### Step 3: Verifica Balance Frozen (Observer)

```bash
# Attendi 10 secondi per propagazione
sleep 10

# Controlla balance su tutti i nodi
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance"
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE1_ID\".balance"
curl -s http://localhost:8003/state | jq ".global.nodes.\"$NODE1_ID\".balance"

# Expected: 990 SP (1000 - 10 congelati)
```

✅ **Checkpoint 1**: Tutti i nodi concordano che il Creator ha 990 SP

### Step 4: Trova un Bug (Il Contributore)

**Istruzioni per il tuo amico:**

1. Vai su GitHub e clona il repo:
   ```bash
   git clone https://github.com/fabriziosalmi/synapse-ng.git
   cd synapse-ng
   ```

2. Esplora il sistema:
   ```bash
   # Leggi la documentazione
   cat README.md
   cat docs/GETTING_STARTED.md
   
   # Prova a creare task, fare claim, votare proposte
   # Cerca comportamenti strani, errori, inconsistenze
   ```

3. Trova un bug (qualsiasi cosa: typo nella doc, comando che non funziona, errore logico, ecc.)

4. Crea un'issue su GitHub:
   ```
   Titolo: [First Task] <Descrizione del bug>
   
   Body:
   - Cosa hai trovato
   - Come riprodurlo
   - Output atteso vs output reale
   
   Label: bug, first-task-experiment
   ```

5. Salva il link dell'issue (es. `https://github.com/fabriziosalmi/synapse-ng/issues/123`)

### Step 5: Claim del Task (Il Contributore)

```bash
# Cattura NODE_ID del Nodo 2 (il contributore)
NODE2_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | keys[1]')

# Verifica balance iniziale
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance"
# Expected: 1000 SP

# Claim task (usando task_id salvato prima)
curl -X POST "http://localhost:8002/tasks/$TASK_ID/claim?channel=dev_ui"

# Attendi propagazione
sleep 10

# Verifica che tutti i nodi vedono il claim
curl -s http://localhost:8001/state | jq ".dev_ui.tasks.\"$TASK_ID\".status"
curl -s http://localhost:8002/state | jq ".dev_ui.tasks.\"$TASK_ID\".status"
curl -s http://localhost:8003/state | jq ".dev_ui.tasks.\"$TASK_ID\".status"

# Expected: "claimed"
```

✅ **Checkpoint 2**: Tutti i nodi concordano che il task è `claimed` dal Nodo 2

### Step 6: Progress e Complete (Il Contributore)

```bash
# Progress
curl -X POST "http://localhost:8002/tasks/$TASK_ID/progress?channel=dev_ui"

sleep 5

# Complete
curl -X POST "http://localhost:8002/tasks/$TASK_ID/complete?channel=dev_ui"

sleep 10
```

### Step 7: Verifica Transfer e Reputazione (Tutti gli Osservatori)

```bash
# Controlla balance finale su tutti i nodi

# Nodo 1 (creator)
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance"
# Expected: 990 SP (pagato 10 SP al contributore)

# Nodo 2 (contributore)
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance"
# Expected: 1010 SP (guadagnato 10 SP, meno 0.2 SP di tassa = +9.8 SP netti)
# Nota: con tassa 2%, reward netto = 10 * 0.98 = 9.8 SP

# Controlla reputazione su tutti i nodi
curl -s http://localhost:8001/state | jq '.global | .nodes | to_entries | map({node_id: .key[0:16], reputation: .value.reputation})'
curl -s http://localhost:8002/state | jq '.global | .nodes | to_entries | map({node_id: .key[0:16], reputation: .value.reputation})'
curl -s http://localhost:8003/state | jq '.global | .nodes | to_entries | map({node_id: .key[0:16], reputation: .value.reputation})'

# Il Nodo 2 dovrebbe avere reputation = 10 (reward per completamento task)
```

✅ **Checkpoint 3**: Tutti i nodi concordano su:
- Creator: 990 SP
- Contributore: ~1010 SP (considerando la tassa)
- Contributore: +10 reputation

---

## 🎯 Criteri di Successo

### ✅ Il sistema è un successo se:

1. **Trasferimento SP**: Il balance del creator è diminuito e quello del contributore è aumentato
2. **Consenso**: Tutti e 3 i nodi concordano sui valori finali
3. **Reputazione**: Il contributore ha guadagnato +10 reputation
4. **Nessun Manager**: Nessuno ha "approvato" il task. Il sistema si è auto-eseguito
5. **Valore Reale**: L'output del task (un bug report) ha valore concreto per il progetto

### ❌ Il sistema ha fallito se:

1. I nodi hanno valori diversi (mancanza di consenso)
2. I balance non si sono aggiornati
3. La reputazione non è aumentata
4. Il task è rimasto in uno stato inconsistente

---

## 💡 Cosa Dimostra Questo Esperimento

### Per il Contributore
- **"Ho fornito valore, ho ricevuto valore"**: Il bug report migliora il progetto, il contributore riceve SP e reputazione
- **"Nessuno mi ha giudicato"**: Il sistema ha auto-eseguito il contratto, nessun human-in-the-loop
- **"La mia reputazione è cresciuta"**: I futuri task potranno pesare questa contribuzione

### Per il Creator
- **"Ho incentivato comportamento utile"**: Ha pagato 10 SP per ricevere un bug report
- **"Il sistema ha eseguito il contratto"**: Non ha dovuto "approvare" manualmente il completamento

### Per la Rete
- **"Il consenso funziona"**: Tutti i nodi hanno la stessa view dello stato
- **"L'economia è reale"**: SP ha valore perché permette di incentivare comportamenti
- **"Il sistema è auto-sufficiente"**: Nessun intervento centrale necessario

---

## 🔬 Varianti dell'Esperimento

### Variante 1: Test con Auction
Invece di reward fissa, usa il sistema d'asta:

```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trovare il primo bug in Synapse-NG",
    "enable_auction": true,
    "max_reward": 20,
    "auction_deadline_hours": 1
  }'

# Nodo 2 fa bid di 10 SP
curl -X POST "http://localhost:8002/tasks/$TASK_ID/bid?channel=dev_ui" \
  -d '{"amount": 10, "estimated_days": 1}'

# Nodo 3 fa bid di 8 SP (più basso = più competitivo)
curl -X POST "http://localhost:8003/tasks/$TASK_ID/bid?channel=dev_ui" \
  -d '{"amount": 8, "estimated_days": 1}'

# Creator seleziona vincitore
curl -X POST "http://localhost:8001/tasks/$TASK_ID/select_bid?channel=dev_ui"
```

### Variante 2: Test con Team Compositi
Crea un task composito con sub-tasks per testare il sistema di squadre collaborative.

### Variante 3: Test con ZKP Voting
Il contributore vota anonimamente su una proposta usando zero-knowledge proof.

---

## 📊 Metriche da Raccogliere

### Automatizzate (Script Enhanced)

Lo script `test_first_task_experiment_enhanced.sh` raccoglie automaticamente:

**Timing Metrics:**
- Task creation time (ms)
- Task propagation time (ms)
- Claim operation time (ms)
- Claim propagation time (ms)
- Complete operation time (ms)
- Complete propagation time (ms)
- Total experiment duration (ms)

**Economic Metrics:**
- Creator initial/final balance
- Contributor initial/final balance
- SP deltas (creator and contributor)
- Tax collected by treasury
- Contributor reputation gain
- SP transfer efficiency (%)

**Consensus Metrics:**
- Balance consensus (boolean)
- Status consensus (boolean)
- Checkpoint results (PASS/FAIL)
- Node-by-node comparison

### Analisi Post-Esperimento

Usa lo script `analyze_experiment.py` per generare:

```bash
./analyze_experiment.py metrics_20251022_143022.json
```

**Output:**
1. **Terminal**: Report colorato con tabelle formattate
2. **Markdown**: Report completo in `analysis_report.md`
3. **Raccomandazioni**: Suggerimenti basati sui risultati

**Esempio di analisi generata:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     TIMING METRICS                              │
├─────────────────────────────────────────────────────────────────┤
│ Task Creation Time                                    245 ms    │
│ Task Propagation Time                                8532 ms    │
│ Claim Operation Time                                  187 ms    │
│ Claim Propagation Time                               7891 ms    │
│ Complete Operation Time                               203 ms    │
│ Complete Propagation Time                            9124 ms    │
│ Total Experiment Duration                           45782 ms    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   ECONOMIC METRICS                              │
├─────────────────────────────────────────────────────────────────┤
│ Creator Initial Balance                              1000 SP    │
│ Creator Final Balance                                 990 SP    │
│ Creator Delta                                         -10 SP    │
│ Contributor Initial Balance                          1000 SP    │
│ Contributor Final Balance                            1010 SP    │
│ Contributor Delta                                     +10 SP    │
│ Tax Collected (Treasury)                                0 SP    │
│ Contributor Reputation Gain                             10      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   CONSENSUS METRICS                             │
├─────────────────────────────────────────────────────────────────┤
│ Balance Consensus                                       ✓ YES   │
│ Status Consensus                                        ✓ YES   │
│ Checkpoint 1 (Balance Frozen)                           PASS    │
│ Checkpoint 2 (Task Claimed)                             PASS    │
│ Checkpoint 3 (Reward Transfer)                          PASS    │
└─────────────────────────────────────────────────────────────────┘
```

### Manuali (Opzionale)

Se esegui manualmente, raccogli:

**Performance:**
- Tempo di propagazione del task (creation → visibilità su tutti i nodi)
- Tempo di propagazione del claim
- Tempo di propagazione del complete
- Tempo totale dell'esperimento

**Consenso:**
- Differenza di balance tra nodi (dovrebbe essere 0)
- Differenza di reputation tra nodi (dovrebbe essere 0)
- Numero di inconsistenze rilevate

**Economiche:**
- SP iniziali vs finali (creator)
- SP iniziali vs finali (contributore)
- Tassa raccolta dalla treasury
- ROI per il creator (valore del bug report vs 10 SP)

---

## 🎬 Prossimi Passi

### Se l'esperimento ha successo:

1. **Documenta**: Scrivi un post-mortem con screenshot e output reali
2. **Itera**: Aumenta la complessità (più nodi, task concorrenti, ecc.)
3. **Invita**: Allarga il cerchio, invita più contributori
4. **Scala**: Passa da 3 a 10+ nodi, da 1 a 100+ task

### Se l'esperimento fallisce:

1. **Debug**: Usa i log per capire dove il consenso si è rotto
2. **Fix**: Correggi il bug trovato
3. **Retry**: Esegui di nuovo l'esperimento
4. **Learn**: Documenta cosa hai imparato

---

## 📚 Riferimenti

- [Getting Started Guide](GETTING_STARTED.md)
- [Task Lifecycle](README.md#task-management)
- [Synapse Points Economy](SYNAPSE_COMPLETE_ARCHITECTURE.md#economic-system)
- [Reputation System](README.md#reputation-and-weighted-voting)
- [Auction System](AUCTION_SYSTEM.md)

---

## 🧬 Filosofia

Questo non è "solo un test".

È la **dimostrazione empirica** che:

> Un organismo digitale autonomo può auto-organizzarsi, auto-incentivare comportamenti utili, e raggiungere consenso deterministico senza autorità centrale.

Se questo micro-esperimento funziona, abbiamo la prova che il principio è valido.

Tutto il resto è scala.

---

**Creato**: 22 Ottobre 2025  
**Versione**: 1.0  
**Status**: Ready to Execute ✨
