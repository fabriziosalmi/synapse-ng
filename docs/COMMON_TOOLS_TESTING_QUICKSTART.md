# Common Tools Testing - Quick Start

## 🚀 Quick Start (60 secondi)

```bash
# 1. Avvia la rete
docker-compose up -d

# 2. Finanzia la tesoreria (opzionale ma consigliato)
./fund_treasury_v2.sh

# 3. Esegui i test
./test_common_tools_experiment.sh
```

**Output atteso**: 24 test passed in ~3 minuti

---

## 📋 Test Scenario Overview

| Scenario | Durata | Priorità | Cosa Testa |
|----------|--------|----------|------------|
| **S1** | 15s | 🔴 Critical | Rifiuto acquisizione con fondi insufficienti |
| **S2** | 20s | 🔴 Critical | Acquisizione completa tool con governance |
| **S3** | 30s | 🔴 Critical | Security checks (3 test di autorizzazione) |
| **S4** | 10s | 🟡 High | Esecuzione tool autorizzata |
| **S5** | 35s | 🟢 Optional | Pagamenti mensili automatici |
| **S6** | 15s | 🟡 High | Deprecazione tool |

**Totale**: ~2-3 minuti (senza S5), ~4-5 minuti (con S5)

---

## 🎯 Test Specifici

### Esegui solo scenari critici (2 minuti)
```bash
./run_common_tools_test.sh quick
```
Esegue: S1, S2, S3, S4, S6 (esclude S5 che richiede 35s di attesa)

### Esegui solo test di sicurezza
```bash
./run_common_tools_test.sh security
```
Esegue: S2 (setup) + S3 (security tests)

### Esegui solo test economici
```bash
./run_common_tools_test.sh economic
```
Esegue: S1 (insufficient funds) + S2 (successful acquisition)

### Esegui singolo scenario
```bash
./run_common_tools_test.sh s1  # Solo Scenario 1
./run_common_tools_test.sh s2  # Solo Scenario 2
# etc.
```

---

## 🔍 Interpretare i Risultati

### ✅ Tutti i Test Superati
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 REPORT FINALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Test Superati:  24
✗ Test Falliti:   0
⊘ Test Skippati:  0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Totale:         24

🎉 TUTTI I TEST SUPERATI!
```

**Azione**: Nessuna. Sistema funziona correttamente.

---

### ❌ Test Falliti - Economic

```
✗ FAIL: Tesoreria non corretta: atteso 100, trovato 150
```

**Causa Probabile**: 
- Tesoreria non decrementata
- Costo tool non applicato
- Bug in `execute_acquire_common_tool`

**Debug**:
```bash
# Verifica tesoreria
curl -s localhost:8001/treasury/sviluppo_ui | jq .

# Verifica tool acquisito
curl -s localhost:8001/state | jq '.sviluppo_ui.common_tools'

# Check logs
docker logs synapse-ng-node-1-1 | grep "acquire_common_tool"
```

---

### ❌ Test Falliti - Security

```
✗ FAIL: Doveva restituire 403, restituito: 200
```

**Causa Probabile**:
- Controllo autorizzazione mancante/bypassato
- Bug in `/tools/{tool_id}/execute`
- Validazione assignee non funzionante

**Debug**:
```bash
# Testa manualmente
curl -s -w "\n%{http_code}\n" -X POST \
  "localhost:8002/tools/test_tool/execute?channel=sviluppo_ui&task_id=invalid" \
  -H "Content-Type: application/json" \
  -d '{}'

# Check logs
docker logs synapse-ng-node-2-1 | grep "execute_common_tool"
```

---

### ⚠️ Test Skippati

```
⊘ SKIP: Tesoreria insufficiente per test (richiesti ≥50 SP)
```

**Causa**: Tesoreria del canale < 50 SP

**Soluzione**:
```bash
# Opzione 1: Finanzia tesoreria
./fund_treasury_v2.sh

# Opzione 2: Crea/completa alcuni task
curl -X POST localhost:8001/tasks?channel=sviluppo_ui \
  -d '{"title": "Test", "reward": 100, "schema_name": "task_v2"}'
# ... claim, progress, complete
```

---

## 🐛 Troubleshooting

### Problema: "Nodi non raggiungibili"

```bash
# Rebuild completo
docker-compose down
docker-compose up --build -d

# Attendi stabilizzazione (10s)
sleep 10

# Ri-esegui test
./test_common_tools_experiment.sh
```

---

### Problema: "Proposta non ratificata"

**Causa**: Quorum non raggiunto (serve 4 nodi)

**Verifica**:
```bash
# Check nodi attivi
curl -s localhost:8001/whoami | jq .
curl -s localhost:8002/whoami | jq .
curl -s localhost:8003/whoami | jq .
curl -s localhost:8004/whoami | jq .

# Verifica proposal status
curl -s localhost:8001/state | jq '.sviluppo_ui.proposals | to_entries | last'
```

---

### Problema: HTTP 500 durante esecuzione tool

**Causa Probabile**: Credenziali corrotte o chiave mancante

**Debug**:
```bash
# Check tool data
curl -s localhost:8001/state | \
  jq '.sviluppo_ui.common_tools.test_geolocation_api'

# Check encrypted_credentials presente
curl -s localhost:8001/state | \
  jq '.sviluppo_ui.common_tools.test_geolocation_api.encrypted_credentials' | \
  head -c 100

# Check logs per InvalidTag exception
docker logs synapse-ng-node-2-1 2>&1 | grep -A 5 "InvalidTag"
```

---

## 📊 Coverage Report

### Dopo esecuzione, verifica coverage:

```bash
# Test coverage summary
./run_common_tools_test.sh list

# Full coverage matrix
cat docs/COMMON_TOOLS_TEST_MATRIX.md
```

### Coverage attuale:

- **Overall**: 50% (5/10 scenari)
- **Critical Tests**: 100% (3/3 passing)
- **Security**: 55%
- **Economic**: 42%

---

## 🔧 Sviluppo Test

### Aggiungere nuovo scenario

1. **Modifica** `test_common_tools_experiment.sh`:
```bash
test_my_new_scenario() {
    print_section "SCENARIO 7: Descrizione"
    print_test "Cosa sto testando"
    
    # Setup
    print_step "Preparazione..."
    
    # Execute
    print_step "Esecuzione..."
    
    # Assert
    if [[ $result == expected ]]; then
        pass "Test description"
    else
        fail "Test description"
    fi
    
    echo -e "${GREEN}✅ Scenario 7 completato${NC}"
}
```

2. **Aggiungi al main**:
```bash
main() {
    # ...
    test_my_new_scenario
    # ...
}
```

3. **Documenta** in `docs/COMMON_TOOLS_TEST_DESIGN.md`

4. **Aggiorna matrix** in `docs/COMMON_TOOLS_TEST_MATRIX.md`

---

## 📚 Documentazione Completa

- **Design completo**: [`docs/COMMON_TOOLS_TEST_DESIGN.md`](./COMMON_TOOLS_TEST_DESIGN.md)
- **Test matrix**: [`docs/COMMON_TOOLS_TEST_MATRIX.md`](./COMMON_TOOLS_TEST_MATRIX.md)
- **Sistema Common Tools**: [`docs/COMMON_TOOLS_SYSTEM.md`](./COMMON_TOOLS_SYSTEM.md)

---

## 💡 Tips

### Durante sviluppo

```bash
# Test solo lo scenario che stai modificando
DEBUG=1 ./run_common_tools_test.sh s3

# Watch mode (re-run on change)
while true; do
  ./run_common_tools_test.sh quick
  sleep 5
done
```

### Prima di commit

```bash
# Full test suite
./test_common_tools_experiment.sh

# Verifica no regressioni
git diff main -- app/main.py | grep -E "(acquire_common_tool|execute_common_tool)"
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Common Tools Tests
  run: |
    docker-compose up -d
    sleep 10
    ./fund_treasury_v2.sh
    ./test_common_tools_experiment.sh
```

---

## 🎓 Best Practices

1. **Sempre esegui setup**: I test assumono rete attiva e tesoreria finanziata
2. **Test sono stateful**: S2 crea tool usato da S3-S6
3. **Attendi sync**: CRDT convergence richiede 5-10s
4. **Check logs sempre**: In caso di fallimento, usa `docker logs`
5. **Test idempotenti**: Puoi ri-eseguire test senza cleanup

---

## 🤝 Contribuire

1. Fork del repository
2. Crea branch: `git checkout -b feature/new-test-scenario`
3. Implementa test seguendo pattern esistente
4. Documenta in README e matrix
5. Esegui full test suite: `./test_common_tools_experiment.sh`
6. Pull request con descrizione dettagliata

---

## 📞 Supporto

- **Issues**: https://github.com/fabriziosalmi/synapse-ng/issues
- **Docs**: https://github.com/fabriziosalmi/synapse-ng/tree/main/docs
- **Tests**: https://github.com/fabriziosalmi/synapse-ng/tree/main/test_*.sh

---

**Last Updated**: 2025-10-23  
**Version**: 1.0.0  
**Maintainer**: Synapse-NG Team
