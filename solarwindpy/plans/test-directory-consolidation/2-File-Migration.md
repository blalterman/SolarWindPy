# Phase 2: File Migration

## Phase Tasks
- [ ] **Move core tests** (Est: 45 min) - Migrate 11 core module tests to /tests/core/
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Relocate plotting tests** (Est: 30 min) - Move 5 plotting tests to /tests/plotting/labels/
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Transfer utility tests** (Est: 15 min) - Move 3 utility tests to /tests/ root
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Relocate test data files** (Est: 15 min) - Move CSV data files from /solarwindpy/tests/data/ to /tests/data/
  - Commit: `<checksum>`
  - Status: Pending

## File Migration Operations

### Core Module Tests (11 files)
**Source**: `/solarwindpy/tests/`  
**Destination**: `/tests/core/`

Files to migrate:
- `test_alfvenic_turbulence.py`
- `test_base.py`
- `test_base_head_tail.py`
- `test_base_mi_tuples.py`
- `test_core_verify_datetimeindex.py`
- `test_ions.py`
- `test_plasma.py`
- `test_plasma_io.py`
- `test_quantities.py`
- `test_spacecraft.py`
- `test_units_constants.py`

### Plotting Tests (5 files)
**Source**: `/solarwindpy/tests/plotting/labels/`  
**Destination**: `/tests/plotting/labels/`

Files to migrate:
- `test_base.py`
- `test_chemistry.py`
- `test_composition.py`
- `test_datetime.py`
- `test_init.py`

### Utility Tests (3 files)
**Source**: `/solarwindpy/tests/`  
**Destination**: `/tests/`

Files to migrate:
- `test_circular_imports.py`
- `test_issue_titles.py`
- `test_planning_agents_architecture.py`

### Test Data Files (3 files)
**Source**: `/solarwindpy/tests/data/`  
**Destination**: `/tests/data/`

Files to migrate:
- `epoch.csv`
- `plasma.csv`
- `spacecraft.csv`

## Migration Commands

### Create Directory Structure
```bash
mkdir -p /tests/core
mkdir -p /tests/plotting/labels
mkdir -p /tests/data
```

### Move Files with Git History Preservation
```bash
# Core tests
git mv solarwindpy/tests/test_*.py tests/core/

# Plotting tests
git mv solarwindpy/tests/plotting/labels/test_*.py tests/plotting/labels/

# Utility tests (individually)
git mv solarwindpy/tests/test_circular_imports.py tests/
git mv solarwindpy/tests/test_issue_titles.py tests/
git mv solarwindpy/tests/test_planning_agents_architecture.py tests/

# Test data
git mv solarwindpy/tests/data/*.csv tests/data/
```

## Post-Migration Verification
- [ ] Verify all 22 test files successfully moved
- [ ] Confirm git history preserved for all files
- [ ] Check directory structure matches expected layout
- [ ] Validate test data file integrity

## Navigation
- **Previous Phase**: [1-Structure-Preparation.md](./1-Structure-Preparation.md)
- **Next Phase**: [3-Import-Transformation.md](./3-Import-Transformation.md)
- **Overview**: [0-Overview.md](./0-Overview.md)