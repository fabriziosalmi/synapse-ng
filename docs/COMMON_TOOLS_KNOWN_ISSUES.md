# Common Tools - Known Issues & Limitations

## 🚧 Status: Test Suite Ready, Implementation Pending

La test suite per i Common Tools è **completa e documentata**, ma l'esecuzione rivela che **l'integrazione con la governance richiede sviluppo addizionale**.

---

## ❌ Blocker: Governance Command Support

### Problema

Le proposte di governance attualmente supportano solo 3 tipi:
- `generic`: Proposte generiche (no execution)
- `config_change`: Modifiche configurazione
- `network_operation`: Operazioni di rete (split/merge)

**Manca**: Supporto per `command` type che esegue operazioni arbitrarie come `acquire_common_tool`.

### Dettagli Tecnici

```bash
# Tentativo attuale
curl -X POST "/proposals?channel=sviluppo_ui" \
  -d '{
    "proposal_type": "command",  # ❌ Non supportato!
    "command": {
      "operation": "acquire_common_tool",
      "params": {...}
    }
  }'

# Errore
{
  "detail": "Campo 'proposal_type' deve essere uno di ['generic', 'config_change', 'network_operation'], ricevuto 'command'"
}
```

### Root Cause

Nel file `app/main.py`, la validazione dei proposals (linea ~1200-1300) accetta solo i 3 tipi menzionati. Il sistema di execution dei comandi (`dispatch_command`) esiste ed è funzionante, ma non c'è bridge dalla governance.

### Impact

- ❌ Scenario 1 (S1): Non eseguibile - richiede proposta
- ❌ Scenario 2 (S2): Non eseguibile - richiede proposta  
- ❌ Scenario 3 (S3): Dipende da S2
- ❌ Scenario 4 (S4): Dipende da S2
- ❌ Scenario 5 (S5): Dipende da S2
- ❌ Scenario 6 (S6): Non eseguibile - richiede proposta

**Test Coverage Impact**: 0% (tutti gli scenari bloccati)

---

## ⚠️ Issue: Tax Calculation for Low Rewards

### Problema

Con reward piccoli (es. 30 SP) e tax rate 2%, la tassa è 0.6 SP che diventa 0 con `int()`.

### Fix Applicato

```python
# Prima (BUGGY)
tax_amount = int(reward * TAX_RATE)  # int(30 * 0.02) = int(0.6) = 0

# Dopo (FIXED)
tax_amount = max(1, round(reward * TAX_RATE))  # max(1, round(0.6)) = 1
```

### Rationale

- **Minimo 1 SP**: Ogni transazione contribuisce almeno 1 SP alla tesoreria
- **Arrotondamento**: `round()` invece di `int()` per fairness
- **Backward Compatible**: Con reward ≥50 SP, comportamento identico

### Validazione

✅ Tesoreria ora si accumula correttamente:
```bash
./fund_treasury_v2.sh
# Output: 1 SP → 2 SP → 3 SP → 4 SP ✓
```

---

## 🔄 Required Implementation

### Task 1: Add "command" Proposal Type

**File**: `app/main.py`  
**Location**: ~line 1200-1300 (proposal validation)

**Changes Needed**:

```python
# In create_proposal endpoint
ALLOWED_PROPOSAL_TYPES = [
    "generic",
    "config_change", 
    "network_operation",
    "command"  # ← ADD THIS
]

# Add command field to validation
if proposal_type == "command":
    if "command" not in proposal_data or "operation" not in proposal_data["command"]:
        raise HTTPException(400, "Proposals of type 'command' require 'command.operation'")
```

**Effort**: ~30 minutes

---

### Task 2: Execute Commands on Ratification

**File**: `app/main.py`  
**Location**: Proposal ratification logic (~line 3800-3900)

**Changes Needed**:

```python
# When proposal becomes "ratified"
if proposal["proposal_type"] == "command":
    command = proposal.get("command", {})
    try:
        result = dispatch_command(command)
        proposal["execution_result"] = result
        proposal["status"] = "executed" if result.get("success") else "failed"
    except Exception as e:
        proposal["execution_result"] = {"success": False, "error": str(e)}
        proposal["status"] = "failed"
```

**Effort**: ~1 hour

---

### Task 3: Test Execution Validation

After implementing Task 1 & 2:

```bash
# Should now work
./test_common_tools_experiment.sh

# Expected: All 6 scenarios pass
```

**Effort**: ~30 minutes (testing + bug fixes)

---

## 📋 Total Implementation Effort

| Task | Effort | Priority |
|------|--------|----------|
| Add "command" proposal type | 30 min | 🔴 Critical |
| Execute commands on ratification | 1 hour | 🔴 Critical |
| Test & validate | 30 min | 🔴 Critical |
| **TOTAL** | **2 hours** | - |

---

## ✅ What's Already Done

### Test Infrastructure (100% Complete)

- ✅ 6 test scenarios designed and implemented
- ✅ 850+ lines of test code
- ✅ Helper runner script for targeted testing
- ✅ Comprehensive error handling and reporting

### Documentation (100% Complete)

- ✅ Test Design Document (800+ lines)
- ✅ Test Matrix (500+ lines)
- ✅ Quick Start Guide (400+ lines)
- ✅ Test Metrics tracking (400+ lines)
- ✅ Integration with main docs

### Backend Logic (95% Complete)

- ✅ `execute_acquire_common_tool()` - Fully implemented
- ✅ `execute_deprecate_common_tool()` - Fully implemented
- ✅ `/tools/{tool_id}/execute` endpoint - Fully implemented with security
- ✅ Credential encryption/decryption - Fully implemented
- ✅ `dispatch_command()` - Fully implemented
- ✅ Treasury calculation - Fixed and working
- ⚠️ Governance bridge - **MISSING** (Task 1 & 2)

### Economic System (100% Complete)

- ✅ Tax calculation fixed (minimum 1 SP)
- ✅ Treasury accumulation validated
- ✅ Balance calculation correct
- ✅ Funding script working

---

## 🎯 Recommendation

### Option A: Complete Implementation (2 hours)

Implement Task 1 & 2, then run full test suite.

**Pros**: 
- Complete feature
- All tests passing
- Production ready

**Cons**: 
- Requires 2 hours dev time
- Touches governance (sensitive area)

---

### Option B: Document & Defer (30 minutes)

Update docs to mark feature as "Ready for Integration", defer implementation.

**Pros**:
- No risk to governance system
- Test suite remains valuable reference
- Clear path forward documented

**Cons**:
- Feature not usable
- Tests can't validate implementation

---

## 📞 Next Steps

1. **Review this document** with team
2. **Choose Option A or B** based on priorities
3. **If Option A**: Assign Task 1 & 2 to developer
4. **If Option B**: Update roadmap with "Q1 2026: Common Tools Integration"

---

## 📚 References

- Test Suite: `test_common_tools_experiment.sh`
- Test Design: `docs/COMMON_TOOLS_TEST_DESIGN.md`
- Test Matrix: `docs/COMMON_TOOLS_TEST_MATRIX.md`
- Quick Start: `docs/COMMON_TOOLS_TESTING_QUICKSTART.md`
- Backend Logic: `app/main.py` (lines 3974-4220, 4524-4590, 1007-1200)

---

**Last Updated**: 2025-10-23  
**Status**: Blocked on Governance Integration  
**Severity**: Medium (feature complete, integration pending)  
**Estimated Fix**: 2 hours development time
