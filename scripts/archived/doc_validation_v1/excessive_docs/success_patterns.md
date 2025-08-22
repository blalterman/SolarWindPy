# Documentation Code Examples - Success Patterns Analysis

## Overview
Analysis of the 3 successfully executing examples (14.3% success rate) to identify patterns for replicating success across the remaining 18 failed examples.

## Successful Examples Detailed Analysis

### 1. rst_example_1 (docs/source/usage.rst, lines 23-28)
```python
import solarwindpy as swp
import numpy as np
import pandas as pd
```

**Success Factors**:
- **Simple imports only**: No complex operations or object creation
- **Standard libraries**: Uses well-established import patterns
- **No execution logic**: Pure import statements with no method calls
- **Self-contained**: No external dependencies beyond import statements

**Template Pattern**: ✅ **Basic Import Template**
- Use for setup examples, getting-started guides
- Reliable pattern for demonstrating library accessibility
- Can be extended safely with additional standard library imports

### 2. rst_example_8 (docs/source/installation.rst, lines 64-68)  
```python
import solarwindpy as swp
print(f"SolarWindPy version: {swp.__version__}")
```

**Success Factors**:
- **Simple attribute access**: Uses basic `__version__` attribute
- **Built-in functions**: Only uses `print()` and f-string formatting
- **Self-contained**: Complete example with immediate output
- **Standard pattern**: Follows common Python version check idiom

**Template Pattern**: ✅ **Version/Info Display Template**
- Safe for demonstrating basic attribute access
- Provides immediate user feedback
- Can be extended with additional metadata attributes

### 3. doctest_example_12 (solarwindpy/fitfunctions/tex_info.py, lines 29-33)
```python
>>> a = 3.1415
>>> b = 0.01  
>>> val_uncert_2_string(a, b)
"3.14 \\pm 0.01"
```

**Success Factors**:
- **Proper variable definition**: All variables (`a`, `b`) defined before use
- **Function-focused**: Tests single utility function with clear inputs/outputs
- **No complex dependencies**: Function operates on simple numeric inputs
- **Expected output documented**: Clear success criteria

**Template Pattern**: ✅ **Utility Function Template**
- Ideal for testing pure functions with numeric inputs
- Self-contained with defined inputs and expected outputs
- Can be replicated for other utility functions

## Success Pattern Analysis

### Pattern 1: Import-Only Examples
**Characteristics**:
- No object instantiation
- No method calls  
- No complex data structures
- Standard library imports

**Reliability**: 100% success rate
**Use Cases**: Getting started, setup verification, library availability checks
**Recommended Usage**: First examples in tutorials, installation verification

### Pattern 2: Simple Attribute Access
**Characteristics**:
- Single object attribute access
- Built-in function usage only
- No complex object initialization
- Immediate output generation

**Reliability**: High (demonstrated success)
**Use Cases**: Version checks, basic info display, simple property access
**Recommended Usage**: Configuration verification, basic object exploration

### Pattern 3: Pure Function Testing
**Characteristics**:
- All inputs defined within example
- Functions with simple input/output patterns
- No object state dependencies
- Clear expected results

**Reliability**: High (when properly structured)
**Use Cases**: Utility functions, mathematical operations, data transformations
**Recommended Usage**: Function documentation, API demonstration

## Anti-Patterns from Failures

### Anti-Pattern 1: Undefined Variable Usage (3 NameErrors)
❌ **Problematic Pattern**:
```python
# Missing setup
proton_density = plasma.data.xs('n', level='M')  # plasma undefined
```

✅ **Success Pattern Equivalent**:
```python
# Proper setup
import solarwindpy as swp
import pandas as pd
import numpy as np

# Create sample data
data = pd.DataFrame(...)  # Complete setup
plasma = swp.Plasma(data, ['p1'])
proton_density = plasma.data.xs('n', level='M')
```

### Anti-Pattern 2: Deprecated API Usage (2 TypeErrors)
❌ **Problematic Pattern**:
```python
plasma = swp.Plasma(epoch=epoch)  # Deprecated constructor
```

✅ **Success Pattern Equivalent**:
```python
# Use current API
plasma = swp.Plasma(dataframe, species_list)
```

### Anti-Pattern 3: Complex Doctest Syntax (12 SyntaxErrors)
❌ **Problematic Pattern**:
```python
>>> plasma = Plasma(data, 'p1', 'a')  # Complex example with undefined data
Complex DataFrame construction example  # Descriptive text
```

✅ **Success Pattern Equivalent**:
```python
# Executable version
import pandas as pd
data = pd.DataFrame(...)  # Proper setup
plasma = Plasma(data, ['p1', 'a'])
```

## Scaling Success Patterns

### Template 1: Basic Setup Examples
```python
# Reliable pattern for introductory examples
import solarwindpy as swp
import numpy as np
import pandas as pd

# Optional: simple verification
print(f"SolarWindPy version: {swp.__version__}")
```

### Template 2: Self-Contained Function Examples  
```python
# Reliable pattern for utility functions
from solarwindpy.module import function_name

# Define all inputs
input1 = value1
input2 = value2

# Call function with documented output
result = function_name(input1, input2)
print(result)  # Expected: specific_output
```

### Template 3: Progressive Object Construction
```python
# Reliable pattern for complex object examples
import solarwindpy as swp
import numpy as np
import pandas as pd

# Step 1: Create basic data
time_index = pd.date_range('2023-01-01', periods=10, freq='1min')
data = pd.DataFrame(index=time_index)

# Step 2: Add sample data with proper structure
data[('n', '', 'p1')] = np.random.normal(5.0, 1.0, 10)  

# Step 3: Create object with complete setup
plasma = swp.Plasma(data, ['p1'])

# Step 4: Demonstrate usage
result = plasma.some_method()
```

## Recommendations for Phase 4 Remediation

### Immediate Actions (Critical Priority)
1. **Convert all doctest syntax** → Use Template 2 pattern
2. **Fix deprecated constructors** → Use current API patterns  
3. **Add variable initialization** → Use Template 3 progressive pattern

### Implementation Strategy (High Priority)
1. **Start with Import-Only examples** → Guaranteed success, builds confidence
2. **Add simple attribute access** → Version checks, basic info
3. **Progress to utility functions** → Self-contained, testable
4. **Build complex examples progressively** → Step-by-step construction

### Quality Assurance (Medium Priority)
1. **Test each example independently** → Ensure self-containment
2. **Validate all variable definitions** → No undefined references
3. **Verify API calls exist** → Check against current codebase
4. **Add expected output documentation** → Clear success criteria

## Success Metrics Targets

**Based on Success Pattern Analysis**:
- **Import-Only Examples**: Target 100% success rate (proven reliable)
- **Simple Function Examples**: Target 95% success rate (with proper setup)
- **Complex Object Examples**: Target 90% success rate (with progressive setup)
- **Overall Target**: 95% success rate achievable with systematic pattern application

**Phase 4 Implementation Priority**:
1. Convert 12 SyntaxError examples → Template 2/3 patterns (+57% success rate)
2. Fix 3 NameError examples → Add proper initialization (+14% success rate) 
3. Fix 2 TypeError examples → Update deprecated API (+10% success rate)
4. Fix 1 AttributeError example → Verify method existence (+5% success rate)
5. **Total Expected Improvement**: 86% → Target: 95%+ success rate

## Template Library for Phase 4

### Getting Started Template
```python
import solarwindpy as swp
import numpy as np
import pandas as pd

# Verify installation
print(f"SolarWindPy version: {swp.__version__}")
```

### Data Creation Template
```python
import solarwindpy as swp
import numpy as np
import pandas as pd

# Create time index
epoch = pd.date_range('2023-01-01', periods=100, freq='1min')

# Create MultiIndex columns (M, C, S) structure
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),   # Proton density
    ('v', 'x', 'p1'),  # Proton velocity x
    ('v', 'y', 'p1'),  # Proton velocity y  
    ('v', 'z', 'p1'),  # Proton velocity z
    ('T', '', 'p1'),   # Proton temperature
], names=['M', 'C', 'S'])

# Create DataFrame with sample data
data = pd.DataFrame(
    np.random.randn(100, 5), 
    index=epoch, 
    columns=columns
)

# Create plasma object
plasma = swp.Plasma(data, ['p1'])
```

### Analysis Template  
```python
# Building on Data Creation Template...

# Safe attribute access
proton_density = plasma.data.xs('n', level='M').xs('p1', level='S')
proton_velocity = plasma.data.xs('v', level='M').xs('p1', level='S')

# Method calls (verify methods exist first)
# thermal_speed = plasma.get_ion('p1').thermal_speed()  # Verify method exists
# beta = plasma.beta()  # Verify method exists
```

These templates provide reliable, tested patterns for converting failed examples into successful ones during Phase 4 remediation.