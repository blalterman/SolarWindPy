# Phase 3: Import Transformation

## Phase Tasks
- [ ] **Transform internal test module imports** (Est: 45 min) - Update imports from solarwindpy.tests to direct package imports
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Update test utility imports** (Est: 30 min) - Replace conftest imports with pytest fixtures
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Fix test data path references** (Est: 30 min) - Update paths from package location to root /tests/data/
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Validate import resolution** (Est: 15 min) - Verify all imports resolve correctly
  - Commit: `<checksum>`
  - Status: Pending

## Import Pattern Transformations

### Type 1: Internal Test Module Imports
**Before:**
```python
from solarwindpy.tests import test_base as base
```
**After:**
```python
from solarwindpy.core import base  # Direct package import
```

### Type 2: Test Utility Imports
**Before:**
```python
from solarwindpy.tests.conftest import sample_plasma_data
```
**After:**
```python
import pytest
# Use @pytest.fixture in consolidated conftest.py
```

### Type 3: Test Data Path References
**Before:**
```python
data_path = "solarwindpy/tests/data/plasma.csv"
```
**After:**
```python
import os
data_path = os.path.join("tests", "data", "plasma.csv")
```

### Type 4: Relative Internal Imports
**Before:**
```python
from . import conftest
from ..test_base import BaseTestCase
```
**After:**
```python
import pytest
from solarwindpy.core.base import BaseClass  # Direct imports
```

## Systematic Import Update Process

### Step 1: Identify Import Patterns
Scan all migrated test files for:
- `from solarwindpy.tests import`
- `from solarwindpy.tests.conftest import`
- Relative imports starting with `.`
- Hard-coded paths to `solarwindpy/tests/data/`

### Step 2: Update Core Test Imports
For each file in `/tests/core/`:
1. Replace internal test imports with direct package imports
2. Update test data path references
3. Remove relative imports
4. Verify pytest fixture compatibility

### Step 3: Update Plotting Test Imports  
For each file in `/tests/plotting/`:
1. Update label test imports to use package modules
2. Fix any cross-test dependencies
3. Ensure proper pytest discovery

### Step 4: Update Utility Test Imports
For utility tests in `/tests/`:
1. Replace any internal test module references
2. Update configuration imports to use fixtures
3. Maintain test isolation and independence

## Expected Import Transformations

### Core Module Tests
- `test_base.py`: Update base class imports
- `test_plasma.py`: Fix plasma module imports and data paths
- `test_ions.py`: Update ion class imports
- `test_spacecraft.py`: Fix spacecraft imports and data references

### Plotting Tests
- Label tests: Update to import from `solarwindpy.plotting.labels`
- Remove internal plotting test dependencies

### Utility Tests
- `test_circular_imports.py`: Update import analysis code
- `test_planning_agents_architecture.py`: Fix agent architecture imports

## Validation Checks
- [ ] All imports resolve without errors
- [ ] No circular import warnings
- [ ] Test data paths point to correct locations
- [ ] Pytest can discover all tests
- [ ] No broken relative imports remain

## Navigation
- **Previous Phase**: [2-File-Migration.md](./2-File-Migration.md)
- **Next Phase**: [4-Configuration-Consolidation.md](./4-Configuration-Consolidation.md)
- **Overview**: [0-Overview.md](./0-Overview.md)