---
description: Audit test quality patterns using validated SolarWindPy conventions from spiral plot work
---

## Test Patterns Audit: $ARGUMENTS

### Overview

Proactive test quality audit using patterns validated during the spiral plot contours test audit.
Detects anti-patterns BEFORE they cause test failures.

**Reference Documentation:** `.claude/docs/TEST_PATTERNS.md`
**ast-grep Rules:** `tools/dev/ast_grep/test-patterns.yml`

**Default Scope:** `tests/`
**Custom Scope:** Pass path as argument (e.g., `tests/plotting/`)

### Anti-Patterns to Detect

| ID | Pattern | Severity | Count (baseline) |
|----|---------|----------|------------------|
| swp-test-001 | `assert X is not None` (trivial) | warning | 74 |
| swp-test-002 | `patch.object` without `wraps=` | warning | 76 |
| swp-test-003 | Assert without error message | info | - |
| swp-test-004 | `plt.subplots()` (verify cleanup) | info | 59 |
| swp-test-006 | `len(x) > 0` without type check | info | - |
| swp-test-009 | `isinstance(X, object)` (disguised trivial) | warning | 0 |

### Good Patterns to Track (Adoption Metrics)

| ID | Pattern | Goal | Count (baseline) |
|----|---------|------|------------------|
| swp-test-005 | `patch.object` WITH `wraps=` | Increase | 4 |
| swp-test-007 | `isinstance` assertions | Increase | - |
| swp-test-008 | `pytest.raises` with `match=` | Increase | - |

### Detection Methods

**PRIMARY: ast-grep MCP Tools (No Installation Required)**

Use these MCP tools for structural pattern matching:

```python
# 1. Trivial assertions (swp-test-001)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="assert $X is not None",
    language="python",
    max_results=50
)

# 2. Weak mocks without wraps (swp-test-002)
mcp__ast-grep__find_code_by_rule(
    project_folder="/path/to/SolarWindPy",
    yaml="""
id: mock-without-wraps
language: python
rule:
  pattern: patch.object($INSTANCE, $METHOD)
  not:
    has:
      pattern: wraps=$_
""",
    max_results=50
)

# 3. Good mock pattern - track adoption (swp-test-005)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="patch.object($I, $M, wraps=$W)",
    language="python"
)

# 4. plt.subplots calls to verify cleanup (swp-test-004)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="plt.subplots()",
    language="python",
    max_results=30
)

# 5. Disguised trivial assertion (swp-test-009)
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
sg scan --config tools/dev/ast_grep/test-patterns.yml tests/

# Run specific rule
sg scan --config tools/dev/ast_grep/test-patterns.yml --rule swp-test-002 tests/

# Quick pattern search
sg run -p "assert \$X is not None" -l python tests/
```

**FALLBACK: grep (always available)**

```bash
# Trivial assertions
grep -rn "assert .* is not None" tests/

# Mock without wraps (approximate)
grep -rn "patch.object" tests/ | grep -v "wraps="

# plt.subplots
grep -rn "plt.subplots()" tests/
```

### Audit Execution Steps

**Step 1: Run anti-pattern detection**
Execute MCP tools for each anti-pattern category.

**Step 2: Count good patterns**
Track adoption of recommended patterns (wraps=, isinstance, pytest.raises with match).

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
| swp-test-001 | Trivial None assertions | X | ↑/↓/= |
| swp-test-002 | Mock without wraps | X | ↑/↓/= |

### Good Pattern Adoption
| Rule | Description | Count | Target |
|------|-------------|-------|--------|
| swp-test-005 | Mock with wraps | X | Increase |

### Top Issues by File
| File | Issues | Primary Problem |
|------|--------|-----------------|
| tests/xxx.py | N | swp-test-XXX |

### Remediation
See `.claude/docs/TEST_PATTERNS.md` for fix patterns:
- Section 1: Mock-with-Wraps Pattern
- Section 2: Parameter Passthrough Verification
- Anti-Patterns section: Common mistakes to avoid
```

### Integration with TestEngineer Agent

For **complex test quality work** (strategy design, coverage planning, physics-aware testing), use the full TestEngineer agent instead of this skill.

This skill is for **routine audits** - quick pattern detection before/during test writing.

---

**Quick Reference - Fix Patterns:**

| Anti-Pattern | Fix | TEST_PATTERNS.md Section |
|--------------|-----|-------------------------|
| `assert X is not None` | `assert isinstance(X, Type)` | #6 Return Type Verification |
| `isinstance(X, object)` | `isinstance(X, SpecificType)` | #6 Return Type Verification |
| `patch.object(i, m)` | `patch.object(i, m, wraps=i.m)` | #1 Mock-with-Wraps |
| Missing `plt.close()` | Add at test end | #15 Resource Cleanup |
| Default parameter values | Use distinctive values (77, 2.5) | #2 Parameter Passthrough |
