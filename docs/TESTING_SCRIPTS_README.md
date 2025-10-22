# 🧪 Experiment Testing Scripts

**Strumenti per eseguire e analizzare il First Task Experiment**

---

## 📋 File Disponibili

### 1. `test_first_task_experiment.sh`
**Script standard per il test automatizzato**

```bash
./test_first_task_experiment.sh
```

**Features:**
- ✅ Esecuzione end-to-end completa
- ✅ Verifica 3 checkpoint
- ✅ Output colorato leggibile
- ✅ Exit code (0 = success, 1 = fail)

**Use case:** Quick test per verificare che il sistema funzioni

---

### 2. `test_first_task_experiment_enhanced.sh` ⭐
**Script avanzato con metriche dettagliate**

```bash
./test_first_task_experiment_enhanced.sh
```

**Features:**
- ✅ Timing preciso al millisecondo
- ✅ Log strutturato (`experiment_*.log`)
- ✅ Metriche JSON (`metrics_*.json`)
- ✅ Tabelle formattate con analisi
- ✅ Salvataggio automatico risultati

**Output files:**
- `experiment_20251022_143022.log` - Log completo
- `metrics_20251022_143022.json` - Metriche strutturate

**Use case:** Esperimenti da documentare e analizzare

---

### 3. `analyze_experiment.py` 🔬
**Script di analisi post-esperimento**

```bash
./analyze_experiment.py metrics_20251022_143022.json [output_report.md]
```

**Features:**
- ✅ Analisi timing dettagliata
- ✅ Valutazione performance
- ✅ Analisi economica con ROI
- ✅ Verifica consenso
- ✅ Raccomandazioni automatiche
- ✅ Report markdown generato

**Output:**
- Terminal: Report colorato interattivo
- File: `analysis_report.md` (o nome custom)

**Use case:** Analisi scientifica dei risultati

---

### 4. `contributor_helper.sh`
**Helper CLI per contributori**

```bash
./contributor_helper.sh <command>
```

**Commands:**
- `setup` - Setup iniziale (clone + docker)
- `status` - Verifica stato nodi
- `my-balance` - Mostra il tuo balance
- `my-reputation` - Mostra la tua reputation
- `list-tasks` - Lista task disponibili
- `claim <task_id>` - Reclama task
- `progress <task_id>` - Marca in progress
- `complete <task_id>` - Completa task
- `create-task` - Crea nuovo task (interattivo)

**Use case:** Semplificare comandi per nuovi contributori

---

## 🚀 Workflow Consigliato

### Esperimento Scientifico (Con Analisi)

```bash
# 1. Avvia network
docker-compose up -d
sleep 15

# 2. Esegui test enhanced
./test_first_task_experiment_enhanced.sh

# 3. Analizza risultati
./analyze_experiment.py metrics_*.json

# 4. Review report
cat analysis_report.md
```

**Output:**
- `experiment_*.log` - Log completo
- `metrics_*.json` - Metriche raw
- `analysis_report.md` - Report formattato

---

### Test Rapido (Quick Check)

```bash
# Avvia e testa in un comando
docker-compose up -d && sleep 15 && ./test_first_task_experiment.sh
```

**Output:**
- Terminal output con checkpoints
- Exit code (0/1)

---

### Contributor Workflow (Utente Finale)

```bash
# Setup iniziale (solo prima volta)
./contributor_helper.sh setup

# Check status
./contributor_helper.sh status

# Vedi il tuo balance
./contributor_helper.sh my-balance

# Lista task disponibili
./contributor_helper.sh list-tasks dev_ui

# Claim un task
./contributor_helper.sh claim abc123...

# Completa il task
./contributor_helper.sh complete abc123...

# Verifica reward
./contributor_helper.sh my-balance
./contributor_helper.sh my-reputation
```

---

## 📊 Interpretare i Risultati

### Script Enhanced Output

**Sezione Timing:**
```
📊 Task Creation Time                    245 ms
📊 Task Propagation Time                8532 ms
📊 Claim Operation Time                  187 ms
📊 Claim Propagation Time               7891 ms
📊 Complete Operation Time               203 ms
📊 Complete Propagation Time            9124 ms
📊 Total Experiment Duration           45782 ms
```

**Interpretazione:**
- Operation times < 500ms: ✅ Ottimo
- Propagation times < 10s: ✅ Accettabile
- Propagation times > 15s: ⚠️ Investigare

**Sezione Economic:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Creator Initial Balance                              1000 SP    │
│ Creator Final Balance                                 990 SP    │
│ Creator Delta                                         -10 SP    │
│ Contributor Initial Balance                          1000 SP    │
│ Contributor Final Balance                            1010 SP    │
│ Contributor Delta                                     +10 SP    │
│ Tax Collected (Treasury)                                0 SP    │
└─────────────────────────────────────────────────────────────────┘
```

**Interpretazione:**
- Creator delta = -10: ✅ Corretto (pagato reward)
- Contributor delta = +10: ✅ Corretto (ricevuto reward meno tassa)
- Tax collected = 0-1 SP: ✅ Normale (2% di 10 = 0.2 ≈ 0)

**Sezione Consensus:**
```
┌─────────────────────────────────────────────────────────────────┐
│ Balance Consensus                                       ✓ YES   │
│ Status Consensus                                        ✓ YES   │
│ Checkpoint 1 (Balance Frozen)                           PASS    │
│ Checkpoint 2 (Task Claimed)                             PASS    │
│ Checkpoint 3 (Reward Transfer)                          PASS    │
└─────────────────────────────────────────────────────────────────┘
```

**Interpretazione:**
- Tutti ✓ YES + PASS: ✅ Esperimento riuscito
- Qualsiasi ✗ NO o FAIL: ❌ Investigare logs

---

## 🔬 Analisi Avanzata

### Comando Base
```bash
./analyze_experiment.py metrics_20251022_143022.json
```

### Con Output Custom
```bash
./analyze_experiment.py metrics_20251022_143022.json my_analysis.md
```

### Metriche nel JSON

Il file `metrics_*.json` contiene:

```json
{
  "experiment_date": "2025-10-22 14:30:22",
  "result": "SUCCESS",
  "timing": {
    "task_creation_ms": 245,
    "task_propagation_ms": 8532,
    ...
  },
  "economic": {
    "creator_initial_sp": 1000,
    "creator_final_sp": 990,
    "creator_delta_sp": -10,
    "contributor_delta_sp": 10,
    "tax_collected_sp": 0,
    "contributor_reputation_gain": 10
  },
  "consensus": {
    "balance_consensus": true,
    "status_consensus": true,
    "checkpoint1": "PASS",
    "checkpoint2": "PASS",
    "checkpoint3": "PASS"
  },
  "node_ids": {
    "node1": "abc123...",
    "node2": "def456...",
    "node3": "ghi789..."
  },
  "task_id": "xyz789..."
}
```

Puoi usare `jq` per query specifiche:

```bash
# Tempo totale esperimento
jq '.timing.total_duration_ms' metrics_*.json

# Delta contributor
jq '.economic.contributor_delta_sp' metrics_*.json

# Tutti i checkpoint
jq '.consensus | {checkpoint1, checkpoint2, checkpoint3}' metrics_*.json
```

---

## 🐛 Troubleshooting

### Script non eseguibile
```bash
chmod +x test_first_task_experiment.sh
chmod +x test_first_task_experiment_enhanced.sh
chmod +x analyze_experiment.py
chmod +x contributor_helper.sh
```

### Nodi non online
```bash
# Verifica Docker
docker ps

# Riavvia
docker-compose down
docker-compose up -d

# Attendi stabilizzazione
sleep 15
```

### jq non installato
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

### Python non installato
```bash
# Lo script usa Python 3.9+
python3 --version

# Se manca, installa da python.org
```

---

## 📝 Best Practices

### Per Esperimenti Scientifici
1. **Sempre usa lo script enhanced**
2. **Salva tutti gli artifact** (logs, metrics, reports)
3. **Esegui multipli run** (3-5) per media statistica
4. **Documenta anomalie** nei logs
5. **Analizza con Python script** per report formali

### Per Quick Tests
1. **Usa script standard** per verifica veloce
2. **Check exit code** per CI/CD integration
3. **Review terminal output** per debug veloce

### Per Contributori
1. **Usa contributor_helper.sh** per comandi semplificati
2. **Documenta ogni step** se trovi problemi
3. **Salva screenshot** per dimostrare reward ricevuto

---

## 🎯 Obiettivo

Questi script non sono solo "test".

Sono la **dimostrazione empirica** che un organismo digitale può:
- Auto-organizzarsi
- Auto-incentivare comportamenti utili
- Raggiungere consenso deterministico
- Operare senza autorità centrale

**Se i test passano, il principio è dimostrato.**

Tutto il resto è scala. 🧬

---

**Creato**: 22 Ottobre 2025  
**Versione**: 2.0 Enhanced  
**Maintainer**: Synapse-NG Core Team
