# Phase 4: Configuration Consolidation

## Phase Tasks
- [ ] **Analyze existing conftest.py files** (Est: 20 min) - Inventory fixtures from both locations
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Merge conftest.py configurations** (Est: 30 min) - Create consolidated root conftest.py
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Eliminate redundant configurations** (Est: 10 min) - Remove duplicated or conflicting settings
  - Commit: `<checksum>`
  - Status: Pending

## Configuration Analysis

### Current Configuration Files

#### Root `/tests/conftest.py` (Fitfunctions)
- Fitfunction-specific fixtures
- Simple linear data generators
- Gaussian data fixtures
- Edge case data for error testing
- Standard pytest configuration

#### Package `/solarwindpy/tests/conftest.py` (Core)
- Core module fixtures
- Plasma data fixtures
- Ion species test data
- Spacecraft trajectory fixtures  
- Development-specific setup

### Consolidation Strategy

#### Root Level `/tests/conftest.py`
Create comprehensive fixture collection:
- **Data Fixtures**: Plasma, ion, spacecraft test data
- **Fitfunction Fixtures**: Mathematical function test data
- **Utility Fixtures**: Common test utilities and helpers
- **Configuration**: Global pytest settings

#### Subdirectory Specific Fixtures
Keep specialized fixtures in subdirectories:
- `/tests/fitfunctions/conftest.py`: Fitfunction-specific fixtures only
- Remove redundant fixtures that are now in root conftest.py

## Fixture Consolidation Plan

### Step 1: Fixture Inventory
**From Root conftest.py:**
- `simple_linear_data()`
- `gaussian_data()`
- `edge_case_data()`
- Fitfunction-specific utilities

**From Package conftest.py:**
- `sample_plasma_data()`
- `test_ions_data()`
- `spacecraft_trajectory()`
- Core module utilities

### Step 2: Merged Root Configuration
```python
# /tests/conftest.py - Consolidated Configuration
import pytest
import pandas as pd
import numpy as np

# Core data fixtures
@pytest.fixture
def sample_plasma_data():
    """Plasma test data for core module tests"""
    # Implementation from package conftest

@pytest.fixture  
def test_ions_data():
    """Ion species test data"""
    # Implementation from package conftest

# Fitfunction data fixtures
@pytest.fixture
def simple_linear_data():
    """Simple linear data for fitfunction tests"""
    # Implementation from root conftest

@pytest.fixture
def gaussian_data():
    """Gaussian data for fitfunction tests"""
    # Implementation from root conftest

# Global pytest configuration
pytest_plugins = ['pytest_cov']
```

### Step 3: Specialized Subdirectory Fixtures
```python
# /tests/fitfunctions/conftest.py - Specialized Only
import pytest

@pytest.fixture
def fitfunction_specific_fixture():
    """Fixtures unique to fitfunctions only"""
    # Keep only fitfunction-specific fixtures here
```

## Configuration Migration Process

### Phase 4a: Backup Current Configurations
```bash
cp tests/conftest.py tests/conftest.py.backup
cp solarwindpy/tests/conftest.py solarwindpy/tests/conftest.py.backup
```

### Phase 4b: Create Consolidated Root Configuration
1. Merge fixture definitions from both sources
2. Eliminate duplicate or redundant fixtures
3. Standardize fixture naming and documentation
4. Add global pytest settings

### Phase 4c: Update Subdirectory Configurations
1. Remove fixtures now available at root level
2. Keep only specialized, subdirectory-specific fixtures
3. Update fixture references to use root-level fixtures

### Phase 4d: Remove Package Configurations
```bash
rm solarwindpy/tests/conftest.py
rmdir solarwindpy/tests  # If empty after migration
```

## Validation Steps
- [ ] All fixtures available to appropriate tests
- [ ] No duplicate fixture definitions
- [ ] Pytest discovery works correctly
- [ ] All test dependencies satisfied
- [ ] Configuration settings preserved

## Navigation
- **Previous Phase**: [3-Import-Transformation.md](./3-Import-Transformation.md)
- **Next Phase**: [5-Validation.md](./5-Validation.md)
- **Overview**: [0-Overview.md](./0-Overview.md)