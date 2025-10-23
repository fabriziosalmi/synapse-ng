# Common Tools Test Matrix

## Test Coverage Overview

| ID | Scenario | Priority | Status | Last Run | Notes |
|----|----------|----------|--------|----------|-------|
| S1 | Insufficient Funds | 🔴 Critical | ✅ Pass | 2025-10-23 | Economic protection |
| S2 | Successful Acquisition | 🔴 Critical | ✅ Pass | 2025-10-23 | End-to-end flow |
| S3 | Unauthorized Usage | 🔴 Critical | ✅ Pass | 2025-10-23 | Security checks |
| S4 | Authorized Usage | 🟡 High | ✅ Pass | 2025-10-23 | Happy path |
| S5 | Monthly Payments | 🟢 Medium | ⚠️ Optional | - | Time-consuming |
| S6 | Tool Deprecation | 🟡 High | ✅ Pass | 2025-10-23 | Lifecycle management |
| S7 | Multiple Tools | 🟢 Medium | 📝 Planned | - | Future |
| S8 | Free Tools | 🟢 Medium | 📝 Planned | - | Future |
| S9 | Concurrent Execution | 🟡 High | 📝 Planned | - | Future |
| S10 | Credential Rotation | 🟢 Medium | 📝 Planned | - | Future |

## Security Tests Matrix

### Authorization Layer 1: Required Tools Check

| Test Case | Input | Expected Output | Status |
|-----------|-------|-----------------|--------|
| Tool not in required_tools | task.required_tools = [] | HTTP 403 | ✅ S3.1 |
| Tool in required_tools | task.required_tools = [tool_id] | Pass to Layer 2 | ✅ S3 |

### Authorization Layer 2: Assignee Verification

| Test Case | Input | Expected Output | Status |
|-----------|-------|-----------------|--------|
| Caller ≠ assignee | NODE_3 calls tool for NODE_2 task | HTTP 403 | ✅ S3.2 |
| Caller = assignee | NODE_2 calls tool for NODE_2 task | Pass to Layer 3 | ✅ S4 |

### Authorization Layer 3: Task State Validation

| Test Case | Task Status | Expected Output | Status |
|-----------|-------------|-----------------|--------|
| open | open | HTTP 403 | ⚠️ Not tested |
| claimed | claimed | HTTP 200* | ✅ S4 |
| in_progress | in_progress | HTTP 200* | ✅ S4 |
| completed | completed | HTTP 403 | ✅ S3.3 |
| cancelled | cancelled | HTTP 403 | ⚠️ Not tested |

*Assuming Layers 1-2 passed

### Data Protection

| Test Case | Input | Expected Output | Status |
|-----------|-------|-----------------|--------|
| Credentials stored | Plain text: "sk_abc123" | Encrypted blob (base64) | ✅ S2 |
| Credentials NOT in clear | Check encrypted_credentials field | ≠ plain text | ✅ S2 |
| Credentials decryption | Valid channel key | Correct plain text | ✅ S4 |
| Invalid channel key | Wrong key | InvalidTag exception | ⚠️ Not tested |

## Economic Tests Matrix

### Treasury Management

| Test Case | Treasury Balance | Tool Cost | Expected Result | Status |
|-----------|------------------|-----------|-----------------|--------|
| Insufficient funds | 50 SP | 100 SP | Execution fails | ✅ S1 |
| Exact funds | 100 SP | 100 SP | Success, balance = 0 | ⚠️ Not tested |
| Surplus funds | 150 SP | 100 SP | Success, balance = 50 | ✅ S2 |
| Zero balance | 0 SP | 50 SP | Execution fails | ⚠️ Not tested |

### Monthly Payments

| Test Case | Tool Status | Expected Behavior | Status |
|-----------|-------------|-------------------|--------|
| Active tool | active | Deduct monthly_cost_sp | ⚠️ S5 (optional) |
| Deprecated tool | deprecated | No deduction | ⚠️ Not tested |
| Insufficient treasury | treasury < cost | Auto-deprecate? | ⚠️ Not tested |

## Governance Tests Matrix

### Proposal Flow

| Test Case | Proposal Type | Votes | Expected Result | Status |
|-----------|---------------|-------|-----------------|--------|
| Acquire tool | command | 4/4 YES | Ratified + Executed | ✅ S2 |
| Acquire tool (fail) | command | 4/4 YES | Ratified + Exec Fail | ✅ S1 |
| Deprecate tool | command | 4/4 YES | Ratified + Executed | ✅ S6 |
| Acquire tool | command | 2/4 YES | Not ratified | ⚠️ Not tested |
| Acquire tool | command | 4/4 NO | Rejected | ⚠️ Not tested |

## Integration Tests Matrix

### End-to-End Workflows

| Workflow | Steps | Expected Result | Status |
|----------|-------|-----------------|--------|
| Full acquisition | Propose → Vote → Ratify → Execute | Tool active, treasury updated | ✅ S2 |
| Full deprecation | Propose → Vote → Ratify → Execute | Tool deprecated | ✅ S6 |
| Tool usage | Acquire → Create task → Claim → Execute | Result returned | ✅ S2+S4 |
| Multiple tools | Acquire A → Acquire B → Use A → Use B | Both work independently | ⚠️ Not tested |

## Edge Cases Matrix

| Edge Case | Expected Behavior | Status |
|-----------|-------------------|--------|
| Tool already exists | Acquisition fails | ⚠️ Not tested |
| Tool not found | Execute fails (HTTP 404) | ⚠️ Not tested |
| Deprecate non-existent tool | Fails with error | ⚠️ Not tested |
| Deprecate already deprecated | Success, idempotent | ⚠️ Not tested |
| Empty credentials | Acquisition fails | ⚠️ Not tested |
| Invalid tool type | Acquisition fails | ⚠️ Not tested |
| Monthly cost = 0 | Acquisition success, no payments | ⚠️ Not tested |
| Negative monthly cost | Validation error | ⚠️ Not tested |

## Performance Tests Matrix

| Test Case | Metric | Target | Status |
|-----------|--------|--------|--------|
| Tool acquisition time | Time from ratify to available | <2s | ⚠️ Not measured |
| Tool execution latency | Time from API call to response | <1s | ⚠️ Not measured |
| Credential decryption time | Time to decrypt credentials | <100ms | ⚠️ Not measured |
| Concurrent executions | 10+ tools executed simultaneously | No failures | ⚠️ Not tested |

## Reliability Tests Matrix

| Test Case | Scenario | Expected Behavior | Status |
|-----------|----------|-------------------|--------|
| Node restart during acquisition | Node goes down mid-acquisition | CRDT convergence, tool eventually available | ⚠️ Not tested |
| Network partition | Nodes 1-2 vs 3-4 | No tool creation until heal | ⚠️ Not tested |
| Corrupted credentials | encrypted_credentials tampered | Decryption fails, HTTP 500 | ⚠️ Not tested |
| Missing channel key | Channel key not available | Decryption fails | ⚠️ Not tested |

## Legend

### Status Icons
- ✅ **Pass**: Test implemented and passing
- ❌ **Fail**: Test implemented but failing
- ⚠️ **Not tested**: Scenario identified but not yet tested
- 📝 **Planned**: Scenario documented for future implementation
- 🚧 **In progress**: Test being developed

### Priority Levels
- 🔴 **Critical**: Must pass for production readiness
- 🟡 **High**: Important for robust system
- 🟢 **Medium**: Nice to have, improves quality
- 🔵 **Low**: Optional, edge case

## Coverage Statistics

### Overall Coverage
- **Total Scenarios Planned**: 10
- **Scenarios Implemented**: 6
- **Scenarios Passing**: 5
- **Optional Scenarios**: 1
- **Coverage**: 50% (5/10)

### Security Coverage
- **Authorization Tests**: 3/5 (60%)
- **Data Protection Tests**: 2/4 (50%)
- **Overall Security**: 55%

### Economic Coverage
- **Treasury Management**: 2/4 (50%)
- **Monthly Payments**: 1/3 (33%)
- **Overall Economic**: 42%

### Governance Coverage
- **Proposal Flow**: 3/5 (60%)

### Integration Coverage
- **End-to-End Workflows**: 3/4 (75%)

### Edge Cases Coverage
- **Edge Cases**: 1/11 (9%)

### Critical Tests Status
- **Critical Tests Total**: 3
- **Critical Tests Passing**: 3
- **Critical Coverage**: 100% ✅

## Recommendations

### Immediate Priority (Next Sprint)
1. ✅ Implement S1-S6 (completed)
2. 🔴 Add test for "Tool already exists" (prevents duplicates)
3. 🔴 Add test for "Invalid channel key" (security)
4. 🔴 Add test for "Corrupted credentials" (reliability)

### Short Term (2-4 weeks)
1. 🟡 Implement S7: Multiple Tools per Channel
2. 🟡 Implement S9: Concurrent Tool Execution
3. 🟡 Add governance rejection tests (2/4 votes, all NO)
4. 🟡 Add task state validation for 'open' and 'cancelled'

### Medium Term (1-2 months)
1. 🟢 Implement S8: Free Tools (monthly_cost = 0)
2. 🟢 Implement S10: Credential Rotation
3. 🟢 Add performance measurement suite
4. 🟢 Add reliability tests (network partition, node restart)

### Long Term (3+ months)
1. 🔵 Chaos engineering: Random node failures during operations
2. 🔵 Load testing: 100+ tools per channel
3. 🔵 Security audit: Penetration testing
4. 🔵 Compliance testing: GDPR, audit trails

## Test Automation

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
name: Common Tools Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start network
        run: docker-compose up -d
      - name: Fund treasury
        run: ./fund_treasury_v2.sh
      - name: Run tests
        run: ./test_common_tools_experiment.sh
      - name: Collect logs
        if: failure()
        run: docker-compose logs > test_logs.txt
      - name: Upload artifacts
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: test-logs
          path: test_logs.txt
```

### Scheduled Testing
```bash
# Cron job for nightly tests
0 2 * * * cd /path/to/synapse-ng && ./test_common_tools_experiment.sh >> /var/log/synapse_tests.log 2>&1
```

## Changelog

### 2025-10-23
- ✅ Initial test suite implementation (S1-S6)
- ✅ Created test matrix documentation
- 📝 Planned future scenarios (S7-S10)
- 📝 Documented security, economic, and governance coverage

---

Last Updated: 2025-10-23
Maintained by: Synapse-NG Team
