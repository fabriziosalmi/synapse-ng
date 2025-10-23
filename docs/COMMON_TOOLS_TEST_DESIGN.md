# Test Suite: Common Tools System (Experimental)

## Panoramica

La suite di test `test_common_tools_experiment.sh` è progettata per validare il sistema di **Common Tools** (Beni Comuni Digitali) in scenari complessi e situazioni edge case, con particolare focus su **sicurezza**, **governance** e **gestione economica**.

## Filosofia del Test

> "Test-Driven Security: I test di sicurezza non dovrebbero solo verificare che il sistema funzioni, ma anche che NON funzioni quando non dovrebbe."

Questa suite implementa il principio **"Fail-Safe by Design"**: ogni scenario verifica non solo il successo delle operazioni legittime, ma anche il **corretto fallimento** delle operazioni non autorizzate.

## Scenari Testati

### ✅ Scenario 1: Acquisizione Fallita (Fondi Insufficienti)

**Obiettivo**: Verificare che il sistema rifiuti acquisizioni impossibili dal punto di vista economico.

**Flusso**:
1. Calcola costo impossibile: `treasury_balance + 1000 SP`
2. Crea proposta governance con `acquire_common_tool`
3. Ottiene ratifica (4 voti YES)
4. **Verifica**: Esecuzione fallisce con errore specifico
5. **Verifica**: Tool non presente nel sistema
6. **Verifica**: Tesoreria invariata

**Test Critici**:
- ✓ Proposta ratificata (governance funziona)
- ✓ Esecuzione fallita (protezione economica)
- ✓ Tool non creato (rollback implicito)
- ✓ Tesoreria non modificata (integrità economica)

**Output Atteso**:
```
✓ PASS: Proposta ratificata correttamente
✓ PASS: Esecuzione fallita come previsto
✓ PASS: Tool non presente nel sistema (corretto)
✓ PASS: Tesoreria invariata: 150 SP
```

---

### ✅ Scenario 2: Acquisizione Riuscita (Ciclo Completo)

**Obiettivo**: Validare l'intero ciclo di acquisizione di un Common Tool.

**Flusso**:
1. Verifica fondi disponibili (≥50 SP richiesti)
2. Crea proposta con tool valido (Geolocation API)
3. Ratifica tramite governance
4. **Verifica**: Tool aggiunto a `common_tools`
5. **Verifica**: Status `active`
6. **Verifica**: Credenziali criptate (non in chiaro)
7. **Verifica**: Tesoreria decrementata correttamente

**Dettagli Tool**:
```json
{
  "tool_id": "test_geolocation_api_<timestamp>",
  "type": "api_key",
  "monthly_cost_sp": 50,
  "credentials_to_encrypt": "sk_test_geoloc_abc123xyz789",
  "status": "active"
}
```

**Test Critici**:
- ✓ Proposta ratificata
- ✓ Comando eseguito con successo
- ✓ Tool presente in `common_tools`
- ✓ Tool status = `active`
- ✓ **SECURITY**: Credenziali criptate
- ✓ **SECURITY**: Credenziali NON in chiaro
- ✓ Tesoreria: `treasury_before - 50 = treasury_after`

**Output Atteso**:
```
✓ PASS: Proposta ratificata
✓ PASS: Comando eseguito con successo
✓ PASS: Tool presente in common_tools
✓ PASS: Tool status: active
✓ PASS: Credenziali criptate presenti
✓ PASS: Credenziali correttamente criptate (non in chiaro)
✓ PASS: Tesoreria aggiornata: 150 - 50 = 100 SP
```

**Artefatti Generati**:
- `ACQUIRED_TOOL_ID`: Salvato per test successivi

---

### 🔒 Scenario 3: Utilizzo non Autorizzato (Security Test)

**Obiettivo**: Verificare tutti i controlli di sicurezza dell'endpoint `/tools/{tool_id}/execute`.

**Flusso**:

#### Test 3.1: Tool non Richiesto dal Task
1. Crea task SENZA `required_tools`
2. Assegna a Nodo 2
3. **Tentativo**: Nodo 2 prova a eseguire tool
4. **Verifica**: HTTP 403 (tool non richiesto)

#### Test 3.2: Chiamante non è Assignee
1. Crea task CON `required_tools: [tool_id]`
2. Assegna a Nodo 2
3. **Tentativo**: Nodo 3 (diverso) prova a eseguire tool
4. **Verifica**: HTTP 403 (non sei l'assignee)

#### Test 3.3: Task Completato
1. Usa task valido assegnato a Nodo 2
2. Completa il task
3. **Tentativo**: Nodo 2 prova a eseguire tool dopo completamento
4. **Verifica**: HTTP 403 (task non in_progress)

**Test Critici**:
- ✓ Accesso negato se tool non richiesto dal task
- ✓ Accesso negato se chiamante ≠ assignee
- ✓ Accesso negato se task.status ≠ `in_progress`

**Output Atteso**:
```
✓ PASS: Accesso negato (403) - tool non richiesto dal task
✓ PASS: Accesso negato (403) - chiamante non è assignee
✓ PASS: Accesso negato (403) - task completato
```

**Principi di Sicurezza Verificati**:
- **Authorization Layer 1**: Required Tools Check
- **Authorization Layer 2**: Assignee Verification
- **Authorization Layer 3**: Task State Validation

---

### ✅ Scenario 4: Utilizzo Autorizzato (Happy Path)

**Obiettivo**: Verificare esecuzione corretta con tutte le autorizzazioni presenti.

**Prerequisiti**:
- Task status: `in_progress`
- Task `required_tools`: contiene `tool_id`
- Chiamante = Assignee del task

**Flusso**:
1. Usa task preparato nello Scenario 3
2. Verifica status `in_progress`
3. **Esecuzione**: Nodo 2 (assignee) esegue tool
4. **Verifica**: HTTP 200
5. **Verifica**: Response structure corretta
6. **Verifica**: Result contiene dati geolocalizzazione

**Response Attesa**:
```json
{
  "success": true,
  "tool_id": "test_geolocation_api_...",
  "tool_type": "api_key",
  "task_id": "abc123...",
  "channel": "sviluppo_ui",
  "result": {
    "ip": "8.8.8.8",
    "country": "United States",
    "city": "Mountain View",
    "latitude": 37.4056,
    "longitude": -122.0775,
    "timezone": "America/Los_Angeles"
  },
  "executed_at": "2025-10-23T12:34:56Z"
}
```

**Test Critici**:
- ✓ Esecuzione riuscita (HTTP 200)
- ✓ Response.success = true
- ✓ Tool ID corretto
- ✓ Result presente e valido
- ✓ Dati geolocalizzazione presenti

**Output Atteso**:
```
✓ PASS: Esecuzione riuscita (HTTP 200)
✓ PASS: Response success: true
✓ PASS: Tool ID corretto nel response
✓ PASS: Result presente nel response
✓ PASS: Dati geolocalizzazione presenti (country: United States, city: Mountain View)
```

---

### ⏱️ Scenario 5: Pagamenti Mensili (Opzionale)

**Obiettivo**: Verificare deduzione automatica dei costi mensili.

**⚠️ WARNING**: Questo test richiede **35+ secondi** di attesa.

**Flusso**:
1. Registra `treasury_before`
2. Ottieni `monthly_cost_sp` del tool
3. **Attesa**: 35 secondi (trigger pagamento mensile)
4. Registra `treasury_after`
5. **Verifica**: `diff = treasury_before - treasury_after`
6. **Verifica**: `0 ≤ diff ≤ (monthly_cost_sp × 2)`

**Note**:
- Il pagamento mensile è asincrono (loop di 30s)
- La verifica è "soft" (range accettabile)
- Test può essere skippato con Ctrl+C nei primi 5s

**Test Critici**:
- ✓ Tesoreria variata sensatamente
- ✓ Differenza entro range atteso

---

### 🗑️ Scenario 6: Deprecazione Tool

**Obiettivo**: Verificare deprecazione corretta di un tool attivo.

**Flusso**:
1. Verifica tool status = `active`
2. Crea proposta `deprecate_common_tool`
3. Ratifica tramite governance
4. **Verifica**: Esecuzione riuscita
5. **Verifica**: Status cambiato a `deprecated`
6. **Verifica**: Tool ancora presente (audit trail)

**Test Critici**:
- ✓ Deprecazione eseguita
- ✓ Status: `active` → `deprecated`
- ✓ Tool ancora presente nel sistema (audit)

**Output Atteso**:
```
✓ PASS: Deprecazione eseguita
✓ PASS: Tool status: deprecated
✓ PASS: Tool ancora presente nel sistema
```

**Principio**: I tool deprecati rimangono nel sistema per **audit trail** e **analisi storica**, ma non sono più utilizzabili né pagati.

---

## Esecuzione

### Prerequisiti

1. **Rete attiva**:
   ```bash
   docker-compose up --build -d
   ```

2. **Tesoreria finanziata** (≥150 SP consigliati):
   ```bash
   ./fund_treasury_v2.sh
   ```

3. **4 nodi operativi**:
   - node-1 (porta 8001)
   - node-2 (porta 8002)
   - node-3 (porta 8003)
   - node-4 (porta 8004)

### Esecuzione Standard

```bash
./test_common_tools_experiment.sh
```

**Durata**: 2-5 minuti (senza Scenario 5)

### Esecuzione con Pagamenti Mensili

```bash
# Decommentare nel codice:
# test_monthly_payments

./test_common_tools_experiment.sh
```

**Durata**: 5-8 minuti (con Scenario 5)

### Variabili d'Ambiente

```bash
# Usa canale diverso
CHANNEL=ricerca_ia ./test_common_tools_experiment.sh

# Debug verbose
set -x
./test_common_tools_experiment.sh
```

---

## Output

### Report Finale

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 REPORT FINALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Test Superati:  24
✗ Test Falliti:   0
⊘ Test Skippati:  0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Totale:         24

🎉 TUTTI I TEST SUPERATI!
```

### Exit Codes

- `0`: Tutti i test superati
- `1`: Almeno un test fallito

---

## Architettura dei Test

### Pattern: Triple-A (Arrange-Act-Assert)

Ogni scenario segue il pattern:

```bash
# ARRANGE: Prepara stato
create_proposal()
vote_proposal()
wait_sync()

# ACT: Esegui azione
execute_tool()

# ASSERT: Verifica risultato
if [[ $result == expected ]]; then
  pass "Test description"
else
  fail "Test description"
fi
```

### Gestione Stato

I test sono **sequenziali** e **stateful**:

1. Scenario 1: Testa fallimento
2. Scenario 2: Crea tool → `ACQUIRED_TOOL_ID`
3. Scenario 3: Usa `ACQUIRED_TOOL_ID` per test security → `VALID_TASK_ID`
4. Scenario 4: Usa `VALID_TASK_ID` per test esecuzione
5. Scenario 6: Depreca `ACQUIRED_TOOL_ID`

**Beneficio**: Riduce setup time e testa real-world workflow.

**Svantaggio**: Fallimento in Scenario 2 causa skip degli scenari successivi.

### Sincronizzazione

```bash
SYNC_WAIT=5          # Sync base tra nodi
GOVERNANCE_WAIT=10   # Attesa ratifica proposta
PAYMENT_WAIT=35      # Trigger pagamento mensile
```

Valori calibrati per:
- Convergenza CRDT
- Gossip protocol
- Processing governance
- Background tasks

---

## Test Coverage

### Funzionalità Testate

| Funzionalità | Scenario | Status |
|--------------|----------|--------|
| Governance Flow | 1, 2, 6 | ✅ |
| Economic Validation | 1, 2 | ✅ |
| Tool Acquisition | 2 | ✅ |
| Credentials Encryption | 2 | ✅ |
| Authorization Checks | 3 | ✅ |
| Tool Execution | 4 | ✅ |
| Monthly Payments | 5 | ⚠️ (opzionale) |
| Tool Deprecation | 6 | ✅ |

### Security Coverage

| Controllo | Scenario | Tipo |
|-----------|----------|------|
| Insufficient Funds | 1 | Economic |
| Required Tools Check | 3.1 | Authorization |
| Assignee Verification | 3.2 | Authentication |
| Task State Validation | 3.3 | Authorization |
| Credentials Encryption | 2 | Data Protection |
| Credentials Not in Clear | 2 | Data Protection |

### Edge Cases

- ✅ Tool cost > treasury balance
- ✅ Tool già esistente
- ✅ Task senza required_tools
- ✅ Chiamante ≠ assignee
- ✅ Task completato
- ✅ Tool già deprecato
- ⚠️ Multiple tools per canale (pianificato)
- ⚠️ Tool con monthly_cost = 0 (pianificato)

---

## Troubleshooting

### Test Falliscono: "Nodi non raggiungibili"

**Causa**: Rete non avviata o in errore.

**Soluzione**:
```bash
docker-compose down
docker-compose up --build -d
sleep 10
./test_common_tools_experiment.sh
```

---

### Test Falliscono: "Tesoreria insufficiente"

**Causa**: Tesoreria del canale < 150 SP.

**Soluzione**:
```bash
./fund_treasury_v2.sh
# Oppure crea/completa alcuni task
```

---

### Test Skippati: "Nessun tool disponibile"

**Causa**: Scenario 2 fallito, tool non acquisito.

**Soluzione**:
1. Controlla logs Scenario 2
2. Verifica tesoreria disponibile
3. Verifica governance attiva (quorum)

---

### HTTP 500 invece di 403

**Causa**: Bug nel codice di validazione.

**Debug**:
```bash
# Check logs nodo
docker logs synapse-ng-node-2-1 | grep "ERROR"

# Verifica stato task
curl -s localhost:8001/state | jq '.sviluppo_ui.tasks' | less
```

---

## Sviluppi Futuri

### Test da Aggiungere

1. **Scenario 7: Multiple Tools per Canale**
   - Acquista 3+ tools diversi
   - Verifica isolation credenziali
   - Verifica pagamenti separati

2. **Scenario 8: Tool Free (monthly_cost = 0)**
   - Tool senza costi mensili
   - Verifica nessuna deduzione tesoreria

3. **Scenario 9: Concurrent Tool Execution**
   - Più nodi eseguono tools in parallelo
   - Verifica no race conditions

4. **Scenario 10: Tool Credential Rotation**
   - Aggiorna credenziali tool esistente
   - Verifica vecchie credenziali invalidate

5. **Scenario 11: Channel Bankruptcy**
   - Tesoreria va a 0 durante pagamento mensile
   - Verifica auto-deprecation tools

### Metriche da Raccogliere

- [ ] Tempo medio acquisizione tool
- [ ] Tempo medio esecuzione tool
- [ ] Memoria occupata da credenziali criptate
- [ ] Latenza decrypt credenziali

---

## Contribuire

Per aggiungere nuovi scenari:

1. **Segui il pattern esistente**:
   ```bash
   test_my_scenario() {
       print_section "SCENARIO X: Descrizione"
       print_test "Cosa testo"
       
       # Arrange
       print_step "Setup..."
       
       # Act
       print_step "Esecuzione..."
       
       # Assert
       if [[ $result == expected ]]; then
           pass "Descrizione test"
       else
           fail "Descrizione test"
       fi
   }
   ```

2. **Aggiungi al main**:
   ```bash
   main() {
       # ...
       test_my_scenario
       # ...
   }
   ```

3. **Documenta in README**: Aggiungi sezione scenario.

---

## Licenza

Questo test è parte del progetto Synapse-NG.
Vedi LICENSE per dettagli.

---

## Contatti

Per domande o bug report:
- Issues: https://github.com/fabriziosalmi/synapse-ng/issues
- Docs: https://github.com/fabriziosalmi/synapse-ng/docs
