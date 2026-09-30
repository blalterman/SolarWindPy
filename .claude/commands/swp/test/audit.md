---
description: Audit test quality patterns using validated SolarWindPy conventions from spiral plot work
---

## Test Patterns Audit: $ARGUMENTS

### Overview

Proactive test quality audit using patterns validated during the spiral plot contours test audit.
Detects anti-patterns BEFORE they cause test failures.

**Reference Documentation:** `.claude/docs/TEST_PATTERNS.md`. Where this audit and
TEST_PATTERNS.md disagree, TEST_PATTERNS.md governs.
**ast-grep Rules:** `tools/dev/ast_grep/test-patterns.yml`

**Default Scope:** `tests/`
**Custom Scope:** Pass path as argument (e.g., `tests/plotting/`)

### Anti-Patterns to Detect

| ID | Pattern | Severity | Count (baseline) |
|----|---------|----------|------------------|
| swp-test-003 | Assert without error message | info | - |
| swp-test-004 | `plt.subplots()` (verify cleanup) | info | 59 |
| swp-test-009 | `isinstance(X, object)` (disguised trivial) | warning | 0 |

### Good Patterns to Track (Adoption Metrics)

| ID | Pattern | Goal | Count (baseline) |
|----|---------|------|------------------|
| swp-test-008 | `pytest.raises` with `match=` | Increase | - |

### Detection Methods

**PRIMARY: ast-grep MCP Tools (No Installation Required)**

Use these MCP tools for structural pattern matching:

```python
# 1. plt.subplots calls to verify cleanup (swp-test-004)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="plt.subplots()",
    language="python",
    max_results=30
)

# 2. Disguised trivial assertion (swp-test-009)
# isinstance(X, object) is equivalent to X is not None
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="isinstance($OBJ, object)",
    language="python",
    max_results=50
)
```

**FALLBACK: CLI ast-grep (requires local `sg` installation)**

```bash
# Run all rules
sg scan --rule tools/dev/ast_grep/test-patterns.yml tests/

# Run specific rule (--filter has no effect with --rule, so filter the output)
sg scan --rule tools/dev/ast_grep/test-patterns.yml --report-style short tests/ | grep swp-test-009

# Quick pattern search
sg run -p "isinstance(\$OBJ, object)" -l python tests/
```

**FALLBACK: grep (always available)**

```bash
# plt.subplots
grep -rn "plt.subplots()" tests/
```

### Audit Execution Steps

**Step 1: Run anti-pattern detection**
Execute MCP tools for each anti-pattern category.

**Step 2: Count good patterns**
Track adoption of recommended patterns (pytest.raises with match).

**Step 3: Generate report**
Compile findings into actionable table format.

**Step 4: Reference fixes**
Point to TEST_PATTERNS.md sections for remediation guidance.

### Output Report Format

```markdown
## Test Patterns Audit Report

**Scope:** <path>
**Date:** <date>

### Anti-Pattern Summary
| Rule | Description | Count | Trend |
|------|-------------|-------|-------|
| swp-test-009 | Disguised trivial assertion | X | ↑/↓/= |

### Good Pattern Adoption
| Rule | Description | Count | Target |
|------|-------------|-------|--------|
| swp-test-008 | pytest.raises with match | X | Increase |

### Top Issues by File
| File | Issues | Primary Problem |
|------|--------|-----------------|
| tests/xxx.py | N | swp-test-XXX |

### Remediation
See `.claude/docs/TEST_PATTERNS.md` for fix patterns:
- What a test asserts: expected values with a named source; errors; plots
- Fakes: which boundaries may be faked; showing a parameter takes effect
- Inputs and fixtures: distinctive non-default inputs
- Checklist for writing or reviewing a test: common mistakes to avoid
```

### Scope

This skill is for **routine audits** - quick pattern detection before/during test writing.

For **complex test quality work** (strategy design, coverage planning, physics-aware testing), work through it directly rather than running this audit.

---

**Quick Reference - Fix Patterns:**

| Anti-Pattern | Fix | TEST_PATTERNS.md Section |
|--------------|-----|-------------------------|
| `assert X is not None` | Assert the expected value, its source on the line | What a test asserts |
| `isinstance(X, object)` | Assert the expected value, its source on the line | What a test asserts |
| `patch.object(i, m)` | Run SolarWindPy for real; fake only network, clock, filesystem | Fakes |
| Missing `plt.close()` | `plt.close("all")` | What a test asserts |
| Default parameter values | Use distinctive non-default values | Inputs and fixtures |
