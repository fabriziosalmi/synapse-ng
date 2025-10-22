# 📋 First Task Experiment - Creator Checklist

**Usa questa checklist quando inviti qualcuno al primo esperimento.**

---

## 🎬 Pre-Experiment Setup

### ☑️ Step 1: Network Running
- [ ] `docker-compose up -d` eseguito
- [ ] 3 nodi online (verifica con `curl http://localhost:800{1,2,3}/health`)
- [ ] Atteso 15s per stabilizzazione rete

### ☑️ Step 2: Verifica Balance Iniziali
```bash
# Cattura node IDs
NODE1_ID=$(curl -s http://localhost:8001/state | jq -r '.global.nodes | keys[0]')
NODE2_ID=$(curl -s http://localhost:8002/state | jq -r '.global.nodes | keys[1]')

# Verifica balance
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance"
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance"
```
- [ ] Nodo 1: 1000 SP ✓
- [ ] Nodo 2: 1000 SP ✓

---

## 🎯 Durante l'Esperimento

### ☑️ Step 3: Crea il Task
```bash
curl -X POST "http://localhost:8001/tasks?channel=dev_ui" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trovare il primo bug in Synapse-NG",
    "description": "Esplora il sistema e documenta il primo comportamento inatteso. Crea un issue su GitHub come prova del completamento.",
    "reward": 10,
    "tags": ["testing", "bug-hunting", "first-contribution"]
  }'
```
- [ ] Task creato con successo
- [ ] Salvato task_id: `_________________`

### ☑️ Step 4: Condividi con il Contributore

**Invia questo messaggio:**

```
🧪 Primo Esperimento Synapse-NG

Ho creato un task per te:
- Titolo: "Trovare il primo bug in Synapse-NG"
- Reward: 10 Synapse Points + 10 Reputation
- Task ID: <inserisci_task_id>

Cosa fare:
1. Clona il repo: git clone https://github.com/fabriziosalmi/synapse-ng.git
2. Esplora il sistema (leggi doc, prova comandi)
3. Trova qualsiasi cosa migliorabile (bug, typo, ecc.)
4. Crea un'issue su GitHub: https://github.com/fabriziosalmi/synapse-ng/issues/new/choose
5. Fammi sapere quando hai il link dell'issue

Poi ti mostro come fare claim e complete del task per ricevere i tuoi SP!

Quick Start: cat QUICKSTART.md
```

- [ ] Messaggio inviato al contributore

### ☑️ Step 5: Guida il Contributore

**Quando ha creato l'issue:**

```bash
# Dai il comando di claim
curl -X POST "http://localhost:8002/tasks/<task_id>/claim?channel=dev_ui"

# Attendi 10s
sleep 10

# Verifica claim
curl -s http://localhost:8001/state | jq '.dev_ui.tasks."<task_id>".status'
# Should be: "claimed"

# Progress
curl -X POST "http://localhost:8002/tasks/<task_id>/progress?channel=dev_ui"

# Complete
curl -X POST "http://localhost:8002/tasks/<task_id>/complete?channel=dev_ui"

# Attendi 15s per propagazione
sleep 15
```

- [ ] Contributore ha fatto claim
- [ ] Contributore ha fatto complete

---

## 📊 Post-Experiment Verification

### ☑️ Step 6: Verifica Transfer

```bash
# Balance finali
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE1_ID\".balance"
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance"

# Reputazione
curl -s http://localhost:8001/reputations | jq "."
```

**Valori attesi:**
- [ ] Creator (Nodo 1): 990 SP (pagato 10 SP)
- [ ] Contributore (Nodo 2): ~1010 SP (ricevuto 10 SP meno tassa)
- [ ] Contributore: +10 reputation

### ☑️ Step 7: Verifica Consenso

```bash
# Balance contributore visto da tutti i nodi
curl -s http://localhost:8001/state | jq ".global.nodes.\"$NODE2_ID\".balance"
curl -s http://localhost:8002/state | jq ".global.nodes.\"$NODE2_ID\".balance"
curl -s http://localhost:8003/state | jq ".global.nodes.\"$NODE2_ID\".balance"
```

- [ ] Tutti i nodi concordano sul balance
- [ ] Tutti i nodi concordano sulla reputation

---

## 🎉 Esperimento Riuscito!

### ☑️ Step 8: Debrief con il Contributore

**Fai queste domande:**

1. **"È chiaro che hai ricevuto valore per il tuo contributo?"**
   - [ ] Risposta chiara e positiva

2. **"Ti fidi che il sistema ha eseguito correttamente il contratto?"**
   - [ ] Sì, ha visto i suoi SP aumentare
   - [ ] Sì, ha visto la sua reputation aumentare

3. **"Faresti un altro task?"**
   - [ ] Sì, il valore è chiaro
   - [ ] No, non vede il valore (se no, chiedi perché)

4. **"Cosa miglioreresti dell'esperienza?"**
   - Feedback: ___________________________________

### ☑️ Step 9: Documenta i Risultati

Crea un post-mortem:
```markdown
# Primo Esperimento - Post-Mortem

**Data**: <data>
**Contributore**: <nome/handle>
**Esito**: ✅ Successo / ❌ Fallito

## Metriche
- Tempo totale: ___ minuti
- Tempo propagazione task: ___ secondi
- Tempo propagazione complete: ___ secondi
- SP trasferiti: 10
- Reputation guadagnata: 10

## Feedback Contributore
- Esperienza: ___/10
- Chiarezza processo: ___/10
- Fiducia nel sistema: ___/10

## Cosa ha funzionato
- 

## Cosa migliorare
- 

## Prossimi passi
- 
```

- [ ] Post-mortem scritto
- [ ] Condiviso con la community (GitHub Discussions, Discord, ecc.)

---

## 🚀 Next Iteration

**Se l'esperimento è riuscito:**

- [ ] Invita più persone (obiettivo: 10 contributori)
- [ ] Crea task più complessi (reward più alte)
- [ ] Prova il sistema d'asta
- [ ] Prova task compositi con squadre

**Se l'esperimento è fallito:**

- [ ] Identifica il punto di rottura
- [ ] Crea un'issue per il bug trovato
- [ ] Fixa il bug
- [ ] Retry l'esperimento

---

## 📝 Note

Usa questo spazio per appunti personali:

```
[Scrivi qui]
```

---

**Remember**: Non stiamo testando software. Stiamo dimostrando un principio.

Se questo funziona, abbiamo la prova che un organismo digitale può auto-organizzarsi senza autorità centrale.

Tutto il resto è scala. 🧬
