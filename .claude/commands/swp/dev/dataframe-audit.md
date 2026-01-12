---
description: Audit DataFrame usage patterns across the SolarWindPy codebase
---

## DataFrame Patterns Audit: $ARGUMENTS

### Overview

Audit SolarWindPy code for compliance with DataFrame conventions:
- MultiIndex structure (M/C/S columns)
- Memory-efficient access patterns (.xs())
- Level operation patterns

**Default Scope:** `solarwindpy/`
**Custom Scope:** Pass path as argument (e.g., `solarwindpy/core/`)

### Pattern Catalog

**1. Level Selection with .xs()**
```python
# Preferred: Returns view, memory-efficient
df.xs('p1', axis=1, level='S')
df.xs(('n', '', 'p1'), axis=1)

# Avoid: Creates copy, wastes memory
df[df.columns.get_level_values('S') == 'p1']
```

**2. Level Reordering Chain**
```python
# Required pattern after concat/manipulation
df.reorder_levels(['M', 'C', 'S'], axis=1).sort_index(axis=1)
```

**3. Level-Specific Operations**
```python
# Preferred: Broadcasts correctly across levels
df.multiply(series, axis=1, level='C')
df.pow(exp, axis=1, level='C')
df.drop(['p1'], axis=1, level='S')
```

**4. Groupby Transpose Pattern (pandas 2.0+)**
```python
# Deprecated (pandas < 2.0)
df.sum(axis=1, level='S')

# Required (pandas >= 2.0)
df.T.groupby(level='S').sum().T
```

**5. Column Duplication Prevention**
```python
# Check before concat
if new.columns.isin(existing.columns).any():
    raise ValueError("Duplicate columns")

# Remove duplicates after operations
df.loc[:, ~df.columns.duplicated()]
```

**6. Empty String Conventions**
```python
# Scalars: empty component
('n', '', 'p1')   # density for p1

# Magnetic field: empty species
('b', 'x', '')    # Bx component

# Spacecraft: empty species
('pos', 'x', '')  # position x
```

### Audit Execution

**PRIMARY: ast-grep MCP Tools (No Installation Required)**

Use these MCP tools for structural pattern matching:

```python
# 1. Boolean indexing anti-pattern (swp-df-001)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="get_level_values($LEVEL)",
    language="python",
    max_results=50
)

# 2. reorder_levels usage - check for missing sort_index (swp-df-002)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="reorder_levels($LEVELS)",
    language="python",
    max_results=30
)

# 3. Deprecated level= aggregation (swp-df-003) - pandas 2.0+
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="$METHOD(axis=1, level=$L)",
    language="python",
    max_results=30
)

# 4. Good .xs() usage - track adoption
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="$DF.xs($KEY, axis=1, level=$L)",
    language="python"
)

# 5. pd.concat without duplicate check (swp-df-005)
mcp__ast-grep__find_code(
    project_folder="/path/to/SolarWindPy",
    pattern="pd.concat($ARGS)",
    language="python",
    max_results=50
)
```

**FALLBACK: CLI ast-grep (requires local `sg` installation)**

```bash
# Quick pattern search (if sg installed)
sg run -p "get_level_values" -l python solarwindpy/
sg run -p "reorder_levels" -l python solarwindpy/
```

**FALLBACK: grep (always available)**

```bash
# .xs() usage (informational)
grep -rn "\.xs(" solarwindpy/

# reorder_levels usage (check for missing sort_index)
grep -rn "reorder_levels" solarwindpy/

# Deprecated level= aggregation (pandas 2.0+)
grep -rn "axis=1, level=" solarwindpy/

# Boolean indexing anti-pattern
grep -rn "get_level_values" solarwindpy/
```

**Step 2: Check for violations**
- `swp-df-001`: Boolean indexing instead of .xs()
- `swp-df-002`: reorder_levels without sort_index
- `swp-df-003`: axis=1, level= aggregation (deprecated)
- `swp-df-004`: MultiIndex without standard names
- `swp-df-005`: Missing column duplicate checks
- `swp-df-006`: multiply without level= parameter

**Step 3: Report findings**

| File | Line | Rule ID | Issue | Severity |
|------|------|---------|-------|----------|
| ... | ... | swp-df-XXX | ... | warn/info |

### Contract Tests Reference

The following contracts validate DataFrame structure:

1. **MultiIndex names**: `columns.names == ['M', 'C', 'S']`
2. **DatetimeIndex row**: `isinstance(df.index, pd.DatetimeIndex)`
3. **xs returns view**: `not result._is_copy`
4. **No duplicate columns**: `not df.columns.duplicated().any()`
5. **Sorted after reorder**: `df.columns.is_monotonic_increasing`

### Output Format

```markdown
## DataFrame Patterns Audit Report

**Scope:** <path>
**Date:** <date>

### Summary
| Pattern | Files | Issues |
|---------|-------|--------|
| xs-usage | X | Y |
| reorder-levels | X | Y |
| groupby-transpose | X | Y |

### Issues Found

#### xs-usage (N issues)
1. **file.py:line**
   - Issue: Boolean indexing instead of .xs()
   - Current: `df[df.columns.get_level_values('S') == 'p1']`
   - Suggested: `df.xs('p1', axis=1, level='S')`

[...]
```

---

**Reference Documentation:**
- `tmp/copilot-plan/dataframe-patterns.md` - Full specification
- `tests/test_contracts_dataframe.py` - Contract test suite
- `tools/dev/ast_grep/dataframe-patterns.yml` - ast-grep rules
