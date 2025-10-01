# 🧪 Test Economia e Governance - Synapse-NG

## 📋 Panoramica

Questa documentazione descrive i nuovi test end-to-end per verificare la correttezza e il determinismo dei sistemi economici e di governance in Synapse-NG:

1. **Voto Ponderato Basato su Reputazione** - Verifica che i nodi con maggiore reputazione abbiano più influenza nelle decisioni
2. **Economia dei Task e Synapse Points** - Verifica il corretto trasferimento di valore (SP) e l'assenza di divergenze economiche

Questi test sono **critici** perché garantiscono che ogni nodo, in modo indipendente, arrivi esattamente allo stesso risultato economico e di governance.

---

## 🚀 Esecuzione dei Test

### Test Completo (Base + Economia + Governance)

```bash
./test_suite.sh
# oppure
./test_suite.sh all
```

### Test Selettivi

```bash
# Solo test base (convergenza, WebRTC, PubSub, task lifecycle)
./test_suite.sh base

# Solo test voto ponderato e governance
./test_suite.sh governance

# Solo test economia Synapse Points
./test_suite.sh economy

# Mostra opzioni disponibili
./test_suite.sh help
```

---

## 🔧 Funzioni Helper Bash

Sono state aggiunte nuove funzioni helper in `test_suite.sh` per facilitare l'interrogazione dello stato economico e di governance:

### `get_reputation(node_port, node_id)`

Ottiene la reputazione di un nodo specifico da un altro nodo.

**Esempio:**
```bash
REP=$(get_reputation 8001 "$NODE_A_ID")
echo "Reputazione Nodo A: $REP"
```

### `get_balance(node_port, node_id)`

Ottiene il balance in Synapse Points (SP) di un nodo specifico.

**Esempio:**
```bash
BAL=$(get_balance 8002 "$NODE_B_ID")
echo "Balance Nodo B: $BAL SP"
```

### `get_proposal_status(node_port, channel, proposal_id)`

Ottiene lo status di una proposta (open, closed, ecc.).

**Esempio:**
```bash
STATUS=$(get_proposal_status 8003 "sviluppo_ui" "$PROP_ID")
echo "Status proposta: $STATUS"
```

### `get_proposal_outcome(node_port, channel, proposal_id)`

Ottiene l'esito calcolato di una proposta (approved, rejected, pending).

**Esempio:**
```bash
OUTCOME=$(get_proposal_outcome 8001 "sviluppo_ui" "$PROP_ID")
echo "Esito proposta: $OUTCOME"
```

---

## 🗳️ Scenario Test 7: Voto Ponderato e Governance Meritocratica

### Obiettivo

Verificare che i nodi con più alta reputazione abbiano effettivamente più influenza nelle votazioni, grazie alla funzione logaritmica di peso del voto:

```
peso_voto = 1.0 + log₂(reputazione + 1)
```

### Fasi del Test

#### FASE 1: Setup
- Avvio 3 nodi (A, B, C)
- Attesa convergenza rete

#### FASE 2: Costruzione Reputazione
- **Nodo A**: Completa 2 task → **+20 reputazione** (peso voto ~5.4)
- **Nodo B**: Vota su 1 proposta → **+1 reputazione** (peso voto ~2.0)
- **Nodo C**: Nessuna azione → **0 reputazione** (peso voto 1.0)
- Verifica che tutti i nodi concordino sulla reputazione

#### FASE 3: Test Votazione Ponderata
- **Nodo C** crea una proposta critica
- **Votazione:**
  - Nodo A (alta reputazione): vota **NO** (peso ~5.4)
  - Nodo B (bassa reputazione): vota **YES** (peso ~2.0)
  - Nodo C (reputazione 0): vota **YES** (peso 1.0)

#### FASE 4: Asserzioni
- La proposta viene chiusa
- **Verifica Critica**: La proposta deve essere **REJECTED** su tutti i nodi
- Nonostante 2 voti YES contro 1 NO, il peso della reputazione di A (5.4) supera B+C (3.0)

### Cosa Verifica Questo Test

✅ **Governance Meritocratica**: I nodi con più contributi hanno più influenza  
✅ **Funzione Logaritmica**: Previene dominanza eccessiva ma riconosce il merito  
✅ **Determinismo**: Tutti i nodi calcolano lo stesso esito indipendentemente  
✅ **Integrità del Voto**: I pesi sono calcolati correttamente da ogni nodo  

### Risultato Atteso

```
✅ VOTO PONDERATO FUNZIONA: Proposta REJECTED nonostante 2 YES vs 1 NO
   Il peso della reputazione di Nodo A (peso ~5.4) ha superato B+C (pesi ~2.0+1.0)
```

---

## 💰 Scenario Test 8: Economia dei Task e Trasferimento Valore (SP)

### Obiettivo

Verificare che:
1. I Synapse Points (SP) vengano correttamente "congelati" quando un task con reward viene creato
2. Gli SP vengano trasferiti correttamente quando il task viene completato
3. **Tutti i nodi concordino sui balance finali** (nessun double-spend o perdita di fondi)

### Fasi del Test

#### FASE 1: Setup
- Avvio 3 nodi (A, B, C)
- Attesa convergenza rete
- Verifica saldi iniziali: **1000 SP per tutti** (configurabile via `INITIAL_BALANCE`)

#### FASE 2: Creazione Task con Reward
- **Nodo A** crea un task con reward di **30 SP**
- Attesa propagazione

#### FASE 3: Verifica Congelamento SP
- **Verifica su Nodo B e C**: Balance di Nodo A deve essere **970 SP** (1000 - 30 congelati)
- Questo prova che gli SP sono immediatamente sottratti dal balance del creator

#### FASE 4: Completamento Task
- **Nodo B** prende in carico il task (claim)
- **Nodo B** completa il task (progress → complete)
- Attesa propagazione

#### FASE 5: Asserzioni Finali - Determinismo Economico
- **Verifica CRITICA su TUTTI i nodi (8001, 8002, 8003):**
  - Balance Nodo A: **970 SP** (1000 - 30 pagati)
  - Balance Nodo B: **1030 SP** (1000 + 30 guadagnati)
  - Balance Nodo C: **1000 SP** (invariato)

### Cosa Verifica Questo Test

✅ **Determinismo Economico**: Tutti i nodi calcolano lo stesso balance  
✅ **Transazionalità**: SP congelati → trasferiti atomicamente  
✅ **Conservazione del Valore**: SP totali prima = SP totali dopo (3000 SP)  
✅ **Assenza di Double-Spend**: Nessun nodo può spendere più di quanto possiede  
✅ **Assenza di Perdita di Fondi**: Nessun SP viene creato o distrutto  

### Risultato Atteso

```
✅ ECONOMIA DETERMINISTICA: Tutti i nodi concordano sui balance!
   Nodo A: 970 SP (1000 - 30 pagati)
   Nodo B: 1030 SP (1000 + 30 guadagnati)
   Nodo C: 1000 SP (invariato)
```

### Se il Test Fallisce

Se anche **un solo nodo** riporta un balance diverso, il test fallisce con:

```
❌ DIVERGENZA ECONOMICA su Nodo :8002 - Nodo A: atteso 970 SP, ricevuto 950 SP
```

Questo indicherebbe un bug critico nel calcolo deterministico dei balance.

---

## ⚙️ Configurazione: INITIAL_BALANCE

### Variabile d'Ambiente

È stata aggiunta la variabile `INITIAL_BALANCE` per facilitare i test economici:

**File: `docker-compose.yml`**
```yaml
node-1:
  environment:
    - INITIAL_BALANCE=1000  # Saldo iniziale SP per modalità test
```

**Default:** 1000 SP per nodo

### Codice Python

**File: `app/main.py` - Funzione `calculate_balances()`**
```python
def calculate_balances(full_state: dict) -> Dict[str, int]:
    # Leggi INITIAL_BALANCE da variabile d'ambiente (default 1000)
    INITIAL_BALANCE = int(os.getenv("INITIAL_BALANCE", "1000"))
    
    balances = {node_id: INITIAL_BALANCE for node_id in full_state.get("global", {}).get("nodes", {})}
    # ... resto della logica
```

### Personalizzazione per Test Diversi

Puoi modificare il saldo iniziale per test specifici:

```yaml
environment:
  - INITIAL_BALANCE=500   # Test con budget limitato
  - INITIAL_BALANCE=10000 # Test con alto capitale
```

---

## 🔍 Debugging dei Test

### Visualizzare gli Stati Intermedi

Durante i test, puoi interrogare manualmente lo stato di un nodo:

```bash
# Stato completo
curl -s http://localhost:8001/state | jq '.'

# Solo reputazioni
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id, reputation}'

# Solo balance
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id, balance}'

# Proposte di un canale
curl -s http://localhost:8001/state | jq '.sviluppo_ui.proposals'

# Task di un canale
curl -s http://localhost:8001/state | jq '.sviluppo_ui.tasks'
```

### Log dei Container Docker

```bash
# Tutti i nodi
docker-compose logs -f

# Singolo nodo
docker-compose logs -f node-1
```

### Timeout e Timing

I test utilizzano sleep strategici per garantire la propagazione:
- **Convergenza iniziale**: 90s (primo avvio cold)
- **Propagazione task/proposta**: 20-25s
- **Propagazione voti**: 20s
- **Propagazione completamento**: 30s

Se i test falliscono per timeout, potrebbero esserci problemi di rete WebRTC o PubSub.

---

## 📊 Output dei Test

### Test Riuscito

```
================== SCENARIO 7: VOTO PONDERATO E GOVERNANCE MERITOCRATICA ==================

...

✅ VOTO PONDERATO FUNZIONA: Proposta REJECTED nonostante 2 YES vs 1 NO
   Il peso della reputazione di Nodo A (peso ~5.4) ha superato B+C (pesi ~2.0+1.0)

================== SCENARIO 8: ECONOMIA DEI TASK E TRASFERIMENTO VALORE (SP) ==================

...

✅ ECONOMIA DETERMINISTICA: Tutti i nodi concordano sui balance!
   Nodo A: 970 SP (1000 - 30 pagati)
   Nodo B: 1030 SP (1000 + 30 guadagnati)
   Nodo C: 1000 SP (invariato)

================== 🎉 TUTTI I TEST COMPLETATI CON SUCCESSO 🎉 ==================

Test Base:
  ✓ Convergenza dello stato
  ✓ Connessioni WebRTC P2P
  ✓ Protocollo SynapseSub
  ✓ Task lifecycle completo
  ✓ Sistema di reputazione

Test Economia e Governance:
  ✓ Voto ponderato basato su reputazione
  ✓ Economia task e trasferimento SP
  ✓ Determinismo economico (no double-spend)
```

### Test Fallito

```
❌ VOTO PONDERATO FALLITO: Status=open, Outcome=pending
   Atteso: Status=closed, Outcome=rejected
```

Oppure:

```
❌ DIVERGENZA ECONOMICA su Nodo :8003 - Nodo B: atteso 1030 SP, ricevuto 1020 SP
```

---

## 🎯 Perché Questi Test Sono Critici

### 1. Fiducia nel Sistema

Se anche un solo nodo calcola un balance o un esito di voto diverso dagli altri, la fiducia nella rete crolla. Questi test garantiscono che **ogni nodo sia una calcolatrice indipendente che arriva sempre allo stesso risultato**.

### 2. Prevenzione Double-Spend

Nel mondo delle criptovalute, il "double-spend" è il problema più grave. Questi test verificano che:
- Un nodo non possa spendere più SP di quanti ne possiede
- Gli SP non vengano duplicati o persi durante i trasferimenti
- Il totale di SP nella rete rimanga costante

### 3. Governance Affidabile

Il voto ponderato deve essere:
- **Giusto**: Chi contribuisce di più ha più voce
- **Non Tirannico**: La funzione logaritmica previene dittature
- **Deterministico**: Tutti concordano sull'esito

### 4. Base per Espansione Futura

Questi test formano la base per:
- Implementazione di contratti intelligenti
- Mercati decentralizzati di task
- Token economy più complesse
- DAO (Decentralized Autonomous Organization)

---

## 🔗 Riferimenti

- **Governance**: `GOVERNANCE_WEIGHTED_VOTING.md` - Documentazione completa del sistema di voto ponderato
- **Codice**: `app/main.py` - Funzioni `calculate_reputations()`, `calculate_balances()`, `calculate_proposal_outcome()`
- **Test Base**: `test_suite.sh` - Scenari 1-6
- **Docker**: `docker-compose.yml` - Configurazione ambiente test

---

## 📝 Note Implementative

### Calcolo Reputazione

```python
# Task completato: +10 reputazione
reputations[task["assignee"]] += 10

# Voto espresso: +1 reputazione
reputations[voter_id] += 1
```

### Calcolo Balance

```python
# Creazione task: il creator perde reward SP
balances[creator] -= reward

# Completamento task: l'assignee guadagna reward SP
if status == "completed":
    balances[assignee] += reward
```

### Peso Voto

```python
peso_voto = 1.0 + math.log2(reputation + 1)

# Esempi:
# reputation 0   → peso 1.00
# reputation 20  → peso 5.39
# reputation 100 → peso 7.66
```

---

## ✅ Checklist Pre-Produzione

Prima di mettere in produzione queste feature, verifica:

- [ ] Tutti i test passano con successo su macchine diverse
- [ ] I test passano con INITIAL_BALANCE diversi (100, 1000, 10000)
- [ ] I test passano con 4+ nodi (testato solo con 3 nodi)
- [ ] I test passano con latenze di rete simulate
- [ ] I test passano con fallimenti di nodi durante le operazioni
- [ ] La documentazione è completa e aggiornata
- [ ] Gli utenti possono eseguire i test facilmente (`./test_suite.sh`)
- [ ] I log sono chiari e debuggabili

---

## 🚀 Prossimi Passi

Dopo che questi test passano stabilmente:

1. **Stress Test**: Testare con centinaia di task e proposte
2. **Test di Resilienza**: Testare con nodi che vanno offline durante transazioni
3. **Test di Latenza**: Testare con ritardi di rete significativi
4. **Test di Sicurezza**: Tentare attacchi double-spend e vote manipulation
5. **Performance Test**: Misurare il throughput delle transazioni SP
6. **Integration Test**: Testare l'integrazione con UI 3D per visualizzare flussi economici

---

**Autore**: Synapse-NG Development Team  
**Versione**: 1.0  
**Data**: Ottobre 2025  
**Status**: ✅ Pronto per Testing
