# Phase 5: TestPyPI Validation

## Overview
Perform comprehensive validation of the v0.1.0-rc5 package deployed to TestPyPI to ensure functionality, dependencies, and metadata correctness before proceeding to production release.

## Objectives
- Validate package installation from TestPyPI
- Test core functionality and imports
- Verify dependency resolution
- Confirm metadata accuracy
- Validate version detection
- Document any issues requiring resolution

## Tasks

### Task 5.1: Clean Environment Installation Test (15 minutes)
**Purpose**: Verify package installs correctly in fresh environment

**Implementation Steps:**
```bash
# Create completely clean test environment
conda create -n solarwindpy-test python=3.12 -y
conda activate solarwindpy-test

# Install from TestPyPI with PyPI fallback for dependencies
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            solarwindpy==0.1.0rc5

# Verify installation succeeded
echo "Installation completed. Testing import..."
```

**Success Criteria:**
- No installation errors
- All dependencies resolve correctly
- Package installs to expected location

### Task 5.2: Core Functionality Validation (10 minutes)
**Purpose**: Confirm essential package functionality works correctly

**Implementation Steps:**
```python
# Test basic imports and version detection
python -c "
import solarwindpy as swp
print(f'SolarWindPy version: {swp.__version__}')
print('Basic import successful')

# Test core classes
from solarwindpy.core import Plasma, Ion
print('Core classes imported successfully')

# Test key modules
import solarwindpy.plotting as pp
import solarwindpy.tools as tools
print('Key modules imported successfully')

# Test package structure
print('Available modules:', [attr for attr in dir(swp) if not attr.startswith('_')])
"
```

**Expected Output:**
```
SolarWindPy version: 0.1.0rc5
Basic import successful
Core classes imported successfully
Key modules imported successfully
Available modules: [list of available modules]
```

### Task 5.3: Dependency Chain Validation (5 minutes)
**Purpose**: Ensure all required dependencies are properly resolved

**Implementation Steps:**
```bash
# List installed packages and versions
pip list | grep -E "(numpy|pandas|matplotlib|scipy|astropy)"

# Test scientific computing stack
python -c "
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from astropy import units as u
print('All core dependencies available')
print(f'NumPy: {np.__version__}')
print(f'Pandas: {pd.__version__}')
print(f'Matplotlib: {plt.matplotlib.__version__}')
"
```

**Expected Behavior:**
- All core scientific dependencies present
- Version compatibility maintained
- No import errors or warnings

## Comprehensive Test Suite

### Test 5.4: Metadata Verification (5 minutes)
**Check Package Information:**
```bash
# Display package metadata
pip show solarwindpy
```

**Verify Expected Metadata:**
- **Name**: solarwindpy
- **Version**: 0.1.0rc5
- **Summary**: Solar wind plasma analysis toolkit
- **Author**: [Expected author information]
- **License**: [Expected license]
- **Dependencies**: Correct requirement versions

### Test 5.5: Basic Data Processing Test (5 minutes)
**Purpose**: Validate core data processing functionality

**Implementation Steps:**
```python
python -c "
import solarwindpy as swp
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Create sample time series data
start_time = datetime(2023, 1, 1)
times = pd.date_range(start_time, periods=100, freq='1min')

# Test basic data structures work
print('Testing basic data operations...')
data = pd.DataFrame({'test': np.random.randn(100)}, index=times)
print(f'Created DataFrame with {len(data)} points')
print('Basic data processing test passed')
"
```

## Installation Variants Testing

### Test 5.6: Different Python Versions (Optional - 10 minutes)
**Purpose**: Validate compatibility across Python versions

**Test Matrix:**
```bash
# Test with Python 3.9 (if time permits)
conda create -n test-py39 python=3.9 -y
conda activate test-py39
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            solarwindpy==0.1.0rc5
python -c "import solarwindpy; print(solarwindpy.__version__)"
conda deactivate

# Test with Python 3.11 (if time permits)
conda create -n test-py311 python=3.11 -y
conda activate test-py311
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            solarwindpy==0.1.0rc5
python -c "import solarwindpy; print(solarwindpy.__version__)"
conda deactivate
```

## Acceptance Criteria

### Installation Requirements ✅
- [ ] Package installs without errors in clean environment
- [ ] All dependencies resolve correctly from PyPI
- [ ] No conflicts with existing packages
- [ ] Installation completes in reasonable time

### Functionality Requirements ✅
- [ ] Core imports work without errors
- [ ] Version detection returns "0.1.0rc5"
- [ ] Key classes (Plasma, Ion) importable
- [ ] Module structure accessible
- [ ] Basic operations execute successfully

### Metadata Requirements ✅
- [ ] Package metadata complete and accurate
- [ ] Dependencies listed correctly
- [ ] Version number formatted properly
- [ ] License and author information present

### Quality Requirements ✅
- [ ] No deprecation warnings on import
- [ ] No missing dependency errors
- [ ] Scientific computing stack functional
- [ ] Basic data processing operations work

## Issue Documentation

### If Installation Fails
**Document:**
- Exact error messages
- Python version and platform
- Dependency conflicts
- Network/proxy issues

**Resolution Steps:**
- Check TestPyPI package integrity
- Verify dependency versions
- Test with different Python versions
- Review package configuration

### If Functionality Issues
**Document:**
- Specific failing imports or operations
- Error messages and tracebacks
- Expected vs actual behavior
- Workaround attempts

**Resolution Steps:**
- Review package build process
- Check missing files or modules
- Validate entry points
- Test local development install

## Environment Cleanup
```bash
# Remove test environments after validation
conda env remove -n solarwindpy-test
conda env remove -n test-py39
conda env remove -n test-py311

# Return to development environment
conda activate solarwindpy-20250403
```

## Progress Tracking
- [ ] Task 5.1: Clean installation test completed
- [ ] Task 5.2: Core functionality validated
- [ ] Task 5.3: Dependency chain verified
- [ ] Task 5.4: Metadata confirmed correct
- [ ] Task 5.5: Basic data processing tested
- [ ] Task 5.6: Multiple Python versions tested (optional)
- [ ] All acceptance criteria met
- [ ] Issues documented and resolved
- [ ] Ready for Phase 6: Production Release

## Time Estimate
**Total: 30 minutes**
- Task 5.1: 15 minutes
- Task 5.2: 10 minutes
- Task 5.3: 5 minutes
- Task 5.4: 5 minutes
- Task 5.5: 5 minutes
- Task 5.6: 10 minutes (optional)

## Risk Mitigation
- **Clean Environments**: Prevent contamination from development setup
- **Multiple Tests**: Validate different aspects of functionality
- **Documentation**: Record issues for systematic resolution
- **Fallback Plan**: Manual PyPI upload available if automation fails
- **Version Control**: TestPyPI provides safe testing ground

## Notes
- TestPyPI validation is critical before production PyPI deployment
- This phase confirms the entire packaging and distribution pipeline
- Success here provides confidence for v0.1.0 production release
- Any issues discovered must be resolved before proceeding
- Clean test environments ensure realistic user experience simulation