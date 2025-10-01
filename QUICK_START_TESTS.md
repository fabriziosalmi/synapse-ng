# 🧪 Quick Start: Test Economia e Governance

## 🚀 Esecuzione Rapida

```bash
# Tutti i test (base + economia + governance)
./test_suite.sh

# Solo test economici
./test_suite.sh economy

# Solo test governance
./test_suite.sh governance

# Aiuto
./test_suite.sh help
```

---

## 📊 Cosa Viene Testato

### Test 7: Voto Ponderato
**Verifica**: Nodi con alta reputazione hanno più influenza nelle votazioni

**Setup**:
- Nodo A: 2 task completati → reputazione 20 → peso voto ~5.4
- Nodo B: 1 voto espresso → reputazione 1 → peso voto ~2.0  
- Nodo C: nessuna azione → reputazione 0 → peso voto 1.0

**Test**:
- Nodo A vota NO (peso 5.4)
- Nodi B e C votano YES (peso totale 3.0)

**Asserzione**: Proposta REJECTED (peso NO > peso YES)

---

### Test 8: Economia SP
**Verifica**: Trasferimento deterministico di Synapse Points (SP)

**Setup**:
- Tutti i nodi: 1000 SP iniziali

**Test**:
- Nodo A crea task con reward 30 SP → balance A = 970 SP (congelati)
- Nodo B completa task → balance B = 1030 SP

**Asserzioni su TUTTI i nodi**:
- Balance A = 970 SP ✅
- Balance B = 1030 SP ✅
- Balance C = 1000 SP ✅
- Totale rete = 3000 SP (conservato) ✅

---

## 🔧 Funzioni Helper Aggiunte

```bash
# Ottieni reputazione
get_reputation 8001 "$NODE_ID"

# Ottieni balance SP
get_balance 8001 "$NODE_ID"

# Ottieni status proposta
get_proposal_status 8001 "sviluppo_ui" "$PROP_ID"

# Ottieni esito proposta
get_proposal_outcome 8001 "sviluppo_ui" "$PROP_ID"
```

---

## ⚙️ Configurazione

### docker-compose.yml
```yaml
environment:
  - INITIAL_BALANCE=1000  # Saldo iniziale SP (configurabile)
```

### app/main.py
```python
# Legge INITIAL_BALANCE da env (default 1000)
INITIAL_BALANCE = int(os.getenv("INITIAL_BALANCE", "1000"))
```

---

## ✅ Risultato Atteso

```
✅ VOTO PONDERATO FUNZIONA
✅ ECONOMIA DETERMINISTICA: Tutti i nodi concordano sui balance!

🎉 TUTTI I TEST COMPLETATI CON SUCCESSO 🎉

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

---

## 🐛 Debugging

```bash
# Stato completo nodo
curl -s http://localhost:8001/state | jq '.'

# Solo reputazioni
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id, reputation}'

# Solo balance
curl -s http://localhost:8001/state | jq '.global.nodes[] | {id, balance}'

# Log container
docker-compose logs -f node-1
```

---

## 📚 Documentazione Completa

Vedi `TEST_ECONOMIA_GOVERNANCE.md` per:
- Descrizione dettagliata di ogni fase
- Spiegazione della logica di test
- Troubleshooting avanzato
- Riferimenti al codice
- Checklist pre-produzione

---

## 🎯 Perché Sono Critici

1. **Determinismo**: Ogni nodo deve calcolare gli stessi risultati
2. **No Double-Spend**: Gli SP non possono essere duplicati
3. **Governance Affidabile**: Il voto ponderato deve funzionare correttamente
4. **Fiducia**: Base per economia decentralizzata e DAO future

---

**Files Modificati**:
- ✅ `test_suite.sh` - Nuove funzioni helper + 2 scenari test
- ✅ `docker-compose.yml` - Variabile INITIAL_BALANCE
- ✅ `app/main.py` - Supporto INITIAL_BALANCE configurabile
- ✅ `TEST_ECONOMIA_GOVERNANCE.md` - Documentazione completa
- ✅ `QUICK_START_TESTS.md` - Questa guida rapida
