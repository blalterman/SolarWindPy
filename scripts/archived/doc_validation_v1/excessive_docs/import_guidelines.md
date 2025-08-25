# SolarWindPy Import Guidelines & Circular Import Prevention

This document provides guidelines for maintaining healthy import structure in SolarWindPy and preventing circular import issues.

## Current Status

✅ **No circular imports detected** (as of 2025-08-09)  
✅ **Comprehensive audit completed**  
✅ **Automated tools available for ongoing monitoring**

## Import Best Practices

### ✅ Recommended Patterns

1. **Use Relative Imports Within Packages**
   ```python
   # ✅ Good
   from . import base
   from . import vector
   from .plotting import histograms
   ```

2. **Use Absolute Imports for External Dependencies**
   ```python
   # ✅ Good
   import numpy as np
   import pandas as pd
   import matplotlib.pyplot as plt
   ```

3. **Explicit Public API in __init__.py**
   ```python
   # ✅ Good
   from .core import Base, Core, Plasma
   from .plotting import histograms, scatter
   
   __all__ = [
       "Base", "Core", "Plasma",
       "histograms", "scatter"
   ]
   ```

4. **Lazy Imports for Optional Dependencies**
   ```python
   # ✅ Good for heavy optional imports
   def plot_advanced():
       import seaborn as sns  # Only import when needed
       # ... plotting code
   ```

### ❌ Patterns to Avoid

1. **Wildcard Imports**
   ```python
   # ❌ Bad - can mask circular imports
   from module import *
   ```

2. **Cross-Package Circular Dependencies**
   ```python
   # ❌ Bad example
   # In core/plasma.py:
   from solarwindpy.plotting import histograms
   
   # In plotting/histograms.py:
   from solarwindpy.core import Plasma  # Creates cycle
   ```

3. **Import Statements Inside Classes**
   ```python
   # ❌ Bad - can create subtle circular imports
   class MyClass:
       from . import some_module  # Don't do this
   ```

## Monitoring & Prevention Tools

### Automated Testing

Run these commands to check for circular imports:

```bash
# Quick static analysis
python scripts/analyze_imports_fixed.py

# Comprehensive dynamic testing
python scripts/test_dynamic_imports.py

# Full test suite
pytest solarwindpy/tests/test_circular_imports.py -v
```

### CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Check for circular imports
  run: |
    pytest solarwindpy/tests/test_circular_imports.py
    python scripts/analyze_imports_fixed.py
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: circular-import-check
      name: Check for circular imports
      entry: python scripts/analyze_imports_fixed.py
      language: system
      pass_filenames: false
```

## Module Organization Guidelines

### Package Structure

Maintain clear hierarchical organization:

```
solarwindpy/
├── __init__.py          # Main package API
├── core/                # Core functionality
│   ├── base.py         # Base classes
│   ├── plasma.py       # Main Plasma class
│   └── ...
├── plotting/            # Visualization tools  
│   ├── histograms.py   # Plotting classes
│   └── ...
├── fitfunctions/        # Mathematical fitting
└── solar_activity/      # Solar data tools
```

### Dependency Flow Rules

Follow these dependency flow patterns:

1. **Core → Utilities**: Core modules can import utility modules
2. **Plotting → Core**: Plotting can import core classes for visualization
3. **Applications → Core + Plotting**: High-level modules can import both
4. **Avoid**: Core importing from plotting or applications

### Import Layers

Organize imports in modules by layer:

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Local relative imports (within same package)
from . import base
from . import vector

# Local absolute imports (cross-package)
from solarwindpy.core import Plasma
```

## Troubleshooting Circular Imports

### Detection

If you suspect a circular import:

1. **Run static analysis**:
   ```bash
   python scripts/analyze_imports_fixed.py
   ```

2. **Check specific modules**:
   ```bash
   python -c "import solarwindpy.module_name"
   ```

3. **Run comprehensive tests**:
   ```bash
   pytest solarwindpy/tests/test_circular_imports.py::TestCircularImports::test_individual_module_imports -v
   ```

### Common Solutions

1. **Move imports to function level** (lazy loading):
   ```python
   def function_that_needs_module():
       from . import problematic_module
       # Use module here
   ```

2. **Extract shared dependencies**:
   ```python
   # Create a new shared module for common functionality
   # Both modules can import from shared module
   ```

3. **Use dependency injection**:
   ```python
   # Pass objects as parameters instead of importing
   def process_data(plasma_obj):  # Instead of importing Plasma
       # Process the plasma object
   ```

4. **Refactor module organization**:
   ```python
   # Move tightly coupled classes to the same module
   # Or reorganize the package structure
   ```

## Warning Signs

Watch for these patterns that often lead to circular imports:

- Two modules importing each other
- Long import chains (A → B → C → D → A)
- Import statements inside class definitions
- Wildcard imports masking dependencies
- Cross-package imports in both directions

## Code Review Checklist

When reviewing import changes:

- [ ] No wildcard imports added
- [ ] Import statements at module top level
- [ ] Consistent with existing patterns
- [ ] No obvious circular dependencies
- [ ] Public API changes properly reflected in `__all__`
- [ ] Tests pass including circular import tests

## Useful Commands

```bash
# Quick import health check
python -c "import solarwindpy; print('✅ Main package imports successfully')"

# Find all import statements in a file
grep -n "^import\|^from.*import" solarwindpy/core/plasma.py

# Run specific circular import test
pytest solarwindpy/tests/test_circular_imports.py::TestCircularImports::test_static_dependency_analysis -v

# Generate dependency report
python scripts/analyze_imports_fixed.py > import_health_report.txt
```

---

*This document was generated as part of the circular import audit completed on 2025-08-09. Update as needed when significant structural changes are made to the package.*