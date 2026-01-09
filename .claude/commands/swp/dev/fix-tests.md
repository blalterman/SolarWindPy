---
description: Diagnose and fix failing tests with guided recovery
---

## Fix Tests Workflow: $ARGUMENTS

### Phase 1: Test Execution & Analysis

Run the failing test(s):
```bash
pytest <test_path> -v --tb=short
```

Parse pytest output to extract:
- **Test name**: Function that failed
- **Status**: FAILED, ERROR, SKIPPED
- **Assertion**: What was expected vs actual
- **Traceback**: File, line number, context

### Phase 2: Failure Categorization

**Category A: Assertion Failures (Logic Errors)**
- Pattern: `AssertionError: <message>`
- Cause: Code doesn't match test specification
- Action: Review implementation against test assertion

**Category B: Physics Constraint Violations**
- Pattern: "convention violated", "conservation", "must be positive"
- Cause: Implementation breaks physics rules
- Action: Check SI units, formula correctness, edge cases
- Reference: `.claude/templates/test-patterns.py` for correct formulas

**Category C: DataFrame/Data Structure Errors**
- Pattern: `KeyError`, `IndexError`, `ValueError: incompatible shapes`
- Cause: MultiIndex structure mismatch or incorrect level access
- Action: Review MultiIndex level names (M/C/S), use `.xs()` instead of `.copy()`

**Category D: Coverage Gaps**
- Pattern: Tests pass but coverage below 95%
- Cause: Edge cases or branches not exercised
- Action: Add tests for boundary conditions, NaN handling, empty inputs

**Category E: Type/Import Errors**
- Pattern: `ImportError`, `AttributeError: has no attribute`
- Cause: Interface mismatch or incomplete implementation
- Action: Verify function exists, check import paths

**Category F: Timeout/Performance**
- Pattern: `timeout after XXs`, tests stalled
- Cause: Inefficient algorithm or infinite loop
- Action: Profile, optimize NumPy operations, add `@pytest.mark.slow`

### Phase 3: Targeted Fixes

**For Logic Errors:**
1. Extract expected vs actual values
2. Locate implementation (grep for function name)
3. Review line-by-line against test
4. Fix discrepancy

**For Physics Violations:**
1. Identify violated law (thermal speed, Alfvén, conservation)
2. Look up correct formula in:
   - `.claude/docs/DEVELOPMENT.md` (physics rules)
   - `.claude/templates/test-patterns.py` (reference formulas)
3. Verify SI units throughout
4. Fix formula using correct physics

**For DataFrame Errors:**
1. Check MultiIndex structure: `df.columns.names` should be `['M', 'C', 'S']`
2. Replace `.copy()` with `.xs()` for level selection
3. Use `.xs(key, level='Level')` instead of positional indexing
4. Verify level values match expected (n, v, w, b for M; x, y, z, par, per for C)

**For Coverage Gaps:**
1. Get missing line numbers from coverage report
2. Identify untested code path
3. Create test case for that path:
   - `test_<function>_empty_input`
   - `test_<function>_nan_handling`
   - `test_<function>_boundary`

### Phase 4: Re-Test Loop

After fixes:
```bash
pytest <specific_test> -v  # Verify fix
.claude/hooks/test-runner.sh --changed  # Run affected tests
```

Repeat Phases 2-4 until all tests pass.

### Phase 5: Completion

**Success Criteria:**
- [ ] All target tests passing
- [ ] No regressions (previously passing tests still pass)
- [ ] Coverage maintained (≥95% for changed modules)
- [ ] Physics validation complete (if applicable)

**Output Summary:**
```
Tests Fixed: X/X now passing
Regression Check: ✅ No broken tests
Coverage: XX.X% (maintained)

Changes Made:
  • <file>: <fix description>
  • <file>: <fix description>

Physics Validation:
  ✅ Thermal speed convention
  ✅ Unit consistency
  ✅ Missing data handling
```

---

**Quick Reference - Common Fixes:**

| Error Pattern | Likely Cause | Fix |
|--------------|--------------|-----|
| `KeyError: 'p1'` | Wrong MultiIndex level | Use `.xs('p1', level='S')` |
| `ValueError: shapes` | DataFrame alignment | Check `.reorder_levels().sort_index()` |
| `AssertionError: thermal` | Wrong formula | Use `sqrt(2 * k_B * T / m)` |
| Coverage < 95% | Missing edge cases | Add NaN, empty, boundary tests |
