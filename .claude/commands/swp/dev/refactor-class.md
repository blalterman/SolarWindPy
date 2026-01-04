---
description: Analyze and refactor SolarWindPy class patterns
---

## Class Refactoring Workflow: $ARGUMENTS

### Class Hierarchy Overview

```
Core (abstract base)
├── Base (abstract, data container)
│   ├── Plasma (multi-species plasma container)
│   ├── Ion (single species container)
│   ├── Spacecraft (spacecraft trajectory)
│   ├── Vector (3D vector, x/y/z components)
│   └── Tensor (tensor quantities, par/per/scalar)
```

### Phase 1: Analysis

**Identify target class:**
- Parse class name from input
- Locate in `solarwindpy/core/`

**Analyze class structure:**
```bash
# Find class definition
grep -n "class <ClassName>" solarwindpy/core/

# Find usage
grep -rn "<ClassName>" solarwindpy/ tests/
```

**Review patterns:**
1. Constructor signature and validation
2. Data structure requirements (MultiIndex levels)
3. Public properties and methods
4. Cross-section patterns (`.xs()`, `.loc[]`)

### Phase 2: Pattern Validation

**Constructor Patterns by Class:**

| Class | Constructor | Data Requirement |
|-------|-------------|------------------|
| Plasma | `(data, *species, spacecraft=None, auxiliary_data=None)` | 3-level M/C/S |
| Ion | `(data, species)` | 2-level M/C (extracts from 3-level) |
| Spacecraft | `(data, name, frame)` | 2 or 3-level with pos/vel |
| Vector | `(data)` | Must have x, y, z columns |
| Tensor | `(data)` | Must have par, per, scalar columns |

**Validation Rules:**
1. Constructor calls `super().__init__()`
2. Logger, units, constants initialized via `Core.__init__()`
3. `set_data()` validates MultiIndex structure
4. Required columns checked with informative errors

**Species Handling:**
- Plasma allows compound species: `"p1+a"`, `"p1,a"`
- Ion forbids "+" (single species only)
- Spacecraft: only PSP, WIND for name; HCI, GSE for frame

### Phase 3: Refactoring Checklist

**Constructor:**
- [ ] Calls `super().__init__()` correctly
- [ ] Validates input types
- [ ] Provides actionable error messages

**Data Validation:**
- [ ] Checks MultiIndex level names (M/C/S or M/C)
- [ ] Validates required columns present
- [ ] Handles empty/NaN data gracefully

**Properties:**
- [ ] Return correct types (Vector, Tensor, Series, DataFrame)
- [ ] Use `.xs()` for level selection (not `.copy()`)
- [ ] Cache expensive computations where appropriate

**Cross-Section Usage:**
```python
# Correct: explicit axis and level
data.xs('p1', axis=1, level='S')
data.xs(('n', '', 'p1'), axis=1)

# Avoid: ambiguous
data['p1']  # May not work with MultiIndex
```

**Species Extraction (Plasma → Ion):**
```python
# Pattern from Plasma._set_ions()
ions = pd.Series({s: ions.Ion(self.data, s) for s in species})
```

### Phase 4: Contract Tests

Verify these contracts for each class:

**Core Contracts:**
- `__init__` creates _logger, _units, _constants
- Equality based on data content, not identity

**Plasma Contracts:**
- Species tuple validation
- Ion objects created via `._set_ions()`
- `__getattr__` enables `plasma.p1` shortcut

**Ion Contracts:**
- Species format validation (no "+")
- Data extraction from 3-level to 2-level
- Required columns: n, v.x, v.y, v.z, w.par, w.per

**Spacecraft Contracts:**
- Frame/name uppercase normalization
- Valid frame enum (HCI, GSE)
- Valid name enum (PSP, WIND)

**Vector Contracts:**
- Requires x, y, z columns
- `.mag` = sqrt(x² + y² + z²)

**Tensor Contracts:**
- Requires par, per, scalar columns
- `__call__('par')` returns par component

### Output Format

```markdown
## Refactoring Analysis: [ClassName]

### Class Signature
- File: solarwindpy/core/<module>.py
- Constructor: [signature]
- Parent: [parent_class]

### Constructor Validation
[Current validation logic summary]

### Properties & Methods
[Public interface listing]

### Usage Statistics
- Direct instantiations: N
- Test coverage: X%
- Cross-section patterns: Y

### Recommendations
1. [Specific improvement]
2. [Specific improvement]
...

### Contract Test Results
[PASS/FAIL for each test]
```

---

**Reference Documentation:**
- `tmp/copilot-plan/class-usage.md` - Full specification
- `tests/test_contracts_class.py` - Contract test suite
- `tools/dev/ast_grep/class-patterns.yml` - ast-grep rules
