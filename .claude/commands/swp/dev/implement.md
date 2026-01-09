---
description: Implement a feature or fix from description through passing tests
---

## Implementation Workflow: $ARGUMENTS

### Phase 1: Analysis & Planning

Analyze the implementation request:
- **What**: Identify the specific modification needed
- **Where**: Locate target module(s) and file(s) in solarwindpy/
- **Why**: Understand purpose and validate physics alignment (if core/instabilities)

**Target Module Mapping:**
- Physics calculations → `solarwindpy/core/` or `solarwindpy/instabilities/`
- Curve fitting → `solarwindpy/fitfunctions/`
- Visualization → `solarwindpy/plotting/`
- Utilities → `solarwindpy/tools/`

Search for existing patterns and implementations:
1. Grep for similar functionality
2. Review module structure
3. Identify integration points

Create execution plan:
- Files to create/modify
- Test strategy (unit, integration, physics validation)
- Coverage targets (≥95% for core/instabilities)

### Phase 2: Implementation

Follow SolarWindPy conventions:
- **Docstrings**: NumPy style with parameters, returns, examples
- **Units**: SI internally (see physics rules below)
- **Code style**: Black (88 chars), Flake8 compliant
- **Missing data**: Use NaN (never 0 or -999)

**Physics Rules (for core/ and instabilities/):**
- Thermal speed convention: mw² = 2kT
- SI units: m/s, kg, K, Pa, T, m³
- Conservation laws: Validate mass, energy, momentum
- Alfvén speed: V_A = B/√(μ₀ρ) with proper composition

Create test file mirroring source structure:
- Source: `solarwindpy/core/ions.py` → Test: `tests/core/test_ions.py`

### Phase 3: Hook Validation Loop

After each edit, hooks automatically run:
```
PostToolUse → test-runner.sh --changed → pytest for modified files
```

Monitor test results. If tests fail:
1. Parse pytest output for failure type
2. Categorize: Logic error | Physics violation | DataFrame issue | Coverage gap
3. Fix targeted issue
4. Re-test automatically on next edit

**Recovery Guide:**
- **AssertionError**: Check implementation against test expectation
- **Physics constraint violation**: Verify SI units and formula correctness
- **ValueError/KeyError**: Check MultiIndex structure (M/C/S levels), use .xs()
- **Coverage below 95%**: Add edge case tests (empty input, NaN handling, boundaries)

### Phase 4: Completion

Success criteria:
- [ ] All tests pass
- [ ] Coverage ≥95% (core/instabilities) or ≥85% (plotting)
- [ ] Physics validation passed (if applicable)
- [ ] Conventional commit message ready

**Output Summary:**
```
Files Modified: [list]
Test Results: X/X passed
Coverage: XX.X%
Physics Validation: ✅/❌

Suggested Commit:
  git add <files>
  git commit -m "feat(<module>): <description>

  🤖 Generated with Claude Code
  Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

**Execution Notes:**
- Hooks are the "Definition of Done" - no separate validation needed
- Use `test-runner.sh --physics` for core/instabilities modules
- Reference `.claude/templates/test-patterns.py` for test examples
- Check `.claude/docs/DEVELOPMENT.md` for detailed conventions
