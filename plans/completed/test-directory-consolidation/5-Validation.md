# Phase 5: Validation

## Phase Tasks
- [ ] **Run full test suite** (Est: 10 min) - Execute pytest -q to verify all tests pass
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Verify pytest discovery** (Est: 5 min) - Confirm pytest finds all tests correctly
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Check CI/CD pipeline** (Est: 10 min) - Validate GitHub Actions continue working
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Validate import resolution** (Est: 5 min) - Ensure all import statements resolve properly
  - Commit: `<checksum>`
  - Status: Pending

## Comprehensive Validation Protocol

### Step 1: Local Test Suite Execution
```bash
# Full test suite - must pass 100%
pytest -q

# Verbose output for debugging if needed
pytest -v

# Test with coverage to ensure all code paths tested
pytest --cov=solarwindpy --cov-report=term-missing
```

**Success Criteria:**
- [ ] All tests pass (0 failures, 0 errors)
- [ ] No import errors or warnings
- [ ] Test discovery finds all expected tests
- [ ] Coverage metrics maintained or improved

### Step 2: Test Discovery Verification
```bash
# Verify pytest discovers all tests
pytest --collect-only

# Check specific subdirectories
pytest tests/core --collect-only
pytest tests/plotting --collect-only  
pytest tests/fitfunctions --collect-only
```

**Expected Results:**
- Total test count: ~170+ tests (existing + migrated)
- All subdirectories properly discovered
- No collection warnings or errors
- Fixture resolution successful

### Step 3: Import Resolution Testing
```bash
# Test imports independently
python -c "import tests.conftest; print('Root conftest imported successfully')"

# Verify test modules import correctly  
python -c "from tests.core import test_plasma; print('Core tests import successfully')"
python -c "from tests.plotting.labels import test_base; print('Plotting tests import successfully')"
```

**Validation Checks:**
- [ ] No circular import errors
- [ ] All external package imports resolve
- [ ] Test data paths accessible
- [ ] Fixture dependencies satisfied

### Step 4: CI/CD Pipeline Validation
```bash
# Simulate GitHub Actions locally
pytest -q --tb=short

# Check formatting requirements
black --check tests/
flake8 tests/
```

**CI/CD Compatibility:**
- [ ] Standard pytest discovery works (no custom configuration needed)
- [ ] Code formatting standards maintained
- [ ] No additional dependencies required
- [ ] Existing workflow commands continue working

### Step 5: Specific Test Category Validation

#### Core Module Tests
```bash
pytest tests/core/ -v
```
Expected: ~11 core tests pass with proper fixture access

#### Plotting Tests  
```bash
pytest tests/plotting/ -v
```
Expected: ~5 plotting tests pass with label functionality

#### Fitfunction Tests
```bash
pytest tests/fitfunctions/ -v
```
Expected: ~170 fitfunction tests pass (already working)

#### Utility Tests
```bash
pytest tests/test_circular_imports.py -v
pytest tests/test_issue_titles.py -v
pytest tests/test_planning_agents_architecture.py -v
```
Expected: Utility tests pass with updated imports

## Performance Validation

### Test Execution Time
- Monitor test execution time (should remain comparable)
- Identify any significant performance regressions
- Ensure parallel test execution still works

### Memory Usage
- Verify test memory usage patterns
- Check for fixture memory leaks
- Validate test isolation maintained

## Rollback Criteria

If validation fails:
1. **Immediate Issues**: Import errors, test failures
2. **Performance Issues**: >50% slower execution
3. **CI/CD Issues**: GitHub Actions failures
4. **Coverage Issues**: Significant coverage reduction

**Rollback Process:**
```bash
git reset --hard [checkpoint-commit]
git clean -fd
```

## Success Validation Checklist
- [ ] 100% test pass rate maintained
- [ ] All tests discoverable by pytest
- [ ] No import resolution errors
- [ ] CI/CD pipeline functions normally
- [ ] Test execution performance acceptable
- [ ] Coverage metrics maintained
- [ ] No regression in functionality

## Navigation
- **Previous Phase**: [4-Configuration-Consolidation.md](./4-Configuration-Consolidation.md)
- **Next Phase**: [6-Cleanup.md](./6-Cleanup.md)
- **Overview**: [0-Overview.md](./0-Overview.md)