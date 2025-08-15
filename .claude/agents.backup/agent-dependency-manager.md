---
name: DependencyManager
description: Manages package dependencies, versions, and conda/pip compatibility
priority: low
tags:
  - dependencies
  - conda
  - pip
  - packaging
applies_to:
  - requirements*.txt
  - pyproject.toml
  - setup.cfg
  - recipe/meta.yaml
  - "*.yml"
---

# DependencyManager Agent

## Purpose
Maintains consistent, reproducible dependency management across pip, conda, and development environments.

## Key Responsibilities

### Dependency Specification
```toml
# pyproject.toml
[project]
dependencies = [
    "numpy>=1.20,<2.0",
    "scipy>=1.7",
    "pandas>=1.3",
    "matplotlib>=3.3",
    "astropy>=4.2",
    "numba>=0.53",
    "h5py>=3.0",
    "pyyaml>=5.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "pytest-cov>=2.10",
    "black>=21.0",
    "flake8>=3.9",
    "sphinx>=4.0",
    "line-profiler>=3.0",
    "memory-profiler>=0.58",
]

docs = [
    "sphinx>=4.0",
    "sphinx-rtd-theme>=0.5",
    "nbsphinx>=0.8",
]
```

### Requirements Files
```python
# requirements.txt - Core dependencies only
numpy>=1.20,<2.0
scipy>=1.7
pandas>=1.3
matplotlib>=3.3
astropy>=4.2
numba>=0.53
h5py>=3.0
pyyaml>=5.4
bottleneck>=1.3
numexpr>=2.7
tabulate>=0.8

# requirements-dev.txt - Include dev tools
-r requirements.txt
pytest>=6.0
pytest-cov>=2.10
black>=21.0
flake8>=3.9
pytables>=3.6
```

## Conda Recipe Management

### Meta.yaml Generation
```python
#!/usr/bin/env python
"""Update conda recipe from requirements."""

import yaml
import re

def update_conda_recipe():
    """Sync recipe/meta.yaml with requirements."""
    
    # Read requirements
    with open('requirements.txt') as f:
        requirements = parse_requirements(f.read())
    
    # Load existing meta.yaml
    with open('recipe/meta.yaml') as f:
        meta = yaml.safe_load(f)
    
    # Update dependencies
    meta['requirements']['run'] = format_conda_deps(requirements)
    
    # Update version
    meta['package']['version'] = get_package_version()
    
    # Write updated recipe
    with open('recipe/meta.yaml', 'w') as f:
        yaml.dump(meta, f, default_flow_style=False)

def parse_requirements(content):
    """Parse requirements file."""
    deps = {}
    for line in content.strip().split('\n'):
        if line and not line.startswith('#'):
            match = re.match(r'([a-zA-Z0-9-_]+)([><=!]+.*)?', line)
            if match:
                name, version = match.groups()
                deps[name] = version or ''
    return deps

def format_conda_deps(requirements):
    """Convert pip to conda format."""
    conda_deps = []
    
    # Map pip names to conda names
    name_map = {
        'pytables': 'tables',
        'scikit-learn': 'scikit-learn',
    }
    
    for name, version in requirements.items():
        conda_name = name_map.get(name, name)
        if version:
            # Convert pip version to conda format
            version = version.replace('>=', ' >=')
            version = version.replace('==', ' ==')
            conda_deps.append(f"{conda_name}{version}")
        else:
            conda_deps.append(conda_name)
    
    return conda_deps
```

### Environment YAML
```yaml
# solarwindpy-dev.yml
name: solarwindpy-dev
channels:
  - conda-forge
  - defaults
dependencies:
  # Core scientific stack
  - python=3.11
  - numpy=1.24
  - scipy=1.10
  - pandas=2.0
  - matplotlib=3.7
  - astropy=5.2
  - numba=0.57
  - h5py=3.8
  
  # Development tools
  - pytest=7.3
  - black=23.3
  - flake8=6.0
  - ipython=8.12
  - jupyter=1.0
  
  # Performance tools
  - line_profiler=4.0
  - memory_profiler=0.61
  
  # Pip-only packages
  - pip
  - pip:
    - pytest-cov
    - sphinx-rtd-theme
```

## Version Compatibility

### Compatibility Matrix
```python
COMPATIBILITY_MATRIX = {
    'numpy': {
        '1.20': {'python': '>=3.7', 'scipy': '>=1.5'},
        '1.21': {'python': '>=3.7', 'scipy': '>=1.7'},
        '1.24': {'python': '>=3.8', 'scipy': '>=1.8'},
    },
    'pandas': {
        '1.3': {'python': '>=3.7', 'numpy': '>=1.17.3'},
        '2.0': {'python': '>=3.8', 'numpy': '>=1.20.3'},
    },
    'numba': {
        '0.53': {'python': '>=3.6', 'numpy': '>=1.15'},
        '0.57': {'python': '>=3.8', 'numpy': '>=1.21'},
    }
}

def check_compatibility(deps):
    """Verify dependency compatibility."""
    issues = []
    
    for pkg, version in deps.items():
        if pkg in COMPATIBILITY_MATRIX:
            constraints = COMPATIBILITY_MATRIX[pkg].get(version, {})
            for dep, required in constraints.items():
                if dep in deps:
                    if not version_satisfies(deps[dep], required):
                        issues.append(
                            f"{pkg}=={version} requires {dep}{required}, "
                            f"but found {dep}=={deps[dep]}"
                        )
    
    return issues
```

### Minimum Version Testing
```python
# tox.ini
[tox]
envlist = py{38,39,310,311}-{min,latest}

[testenv]
deps =
    min: numpy==1.20.0
    min: scipy==1.7.0
    min: pandas==1.3.0
    latest: numpy
    latest: scipy
    latest: pandas
    pytest
commands = pytest {posargs}

[testenv:py38-min]
# Test with minimum supported versions
deps = 
    -r requirements-min.txt
    pytest
```

## Dependency Updates

### Update Workflow
```python
def update_dependencies(conservative=True):
    """Update dependencies safely."""
    
    # Check for updates
    updates = check_for_updates()
    
    if conservative:
        # Only update patch versions
        updates = filter_patch_updates(updates)
    
    # Test with updates
    for pkg, new_version in updates.items():
        if test_with_update(pkg, new_version):
            apply_update(pkg, new_version)
        else:
            print(f"Update {pkg} to {new_version} failed tests")

def check_for_updates():
    """Check for available updates."""
    import subprocess
    import json
    
    result = subprocess.run(
        ['pip', 'list', '--outdated', '--format=json'],
        capture_output=True,
        text=True
    )
    
    outdated = json.loads(result.stdout)
    return {pkg['name']: pkg['latest_version'] for pkg in outdated}
```

### Security Monitoring
```python
def check_security_vulnerabilities():
    """Check for known security issues."""
    import subprocess
    
    # Use safety to check for vulnerabilities
    result = subprocess.run(
        ['safety', 'check', '--json'],
        capture_output=True,
        text=True
    )
    
    vulnerabilities = json.loads(result.stdout)
    
    if vulnerabilities:
        for vuln in vulnerabilities:
            print(f"SECURITY: {vuln['package']} {vuln['installed_version']} "
                  f"has known vulnerability: {vuln['vulnerability']}")
            print(f"Recommendation: Update to {vuln['safe_version']}")
```

## Platform-Specific Dependencies

```python
# setup.py
import sys
import platform

install_requires = [
    'numpy>=1.20',
    'scipy>=1.7',
    'pandas>=1.3',
]

# Platform-specific dependencies
if sys.platform == 'win32':
    install_requires.append('pywin32')
elif sys.platform == 'darwin':
    install_requires.append('pyobjc-framework-Cocoa')

# Python version-specific
if sys.version_info < (3, 8):
    install_requires.append('importlib-metadata')
```

## Dependency Resolution

### Conflict Resolution
```python
def resolve_conflicts(requirements):
    """Resolve dependency conflicts."""
    from pip._internal.resolution.resolvelib import Resolver
    
    resolver = Resolver()
    
    try:
        resolved = resolver.resolve(requirements)
        return resolved
    except ResolutionImpossible as e:
        print("Conflict detected:")
        for conflict in e.causes:
            print(f"  {conflict}")
        
        # Try to suggest resolution
        suggestion = suggest_resolution(e.causes)
        print(f"Suggestion: {suggestion}")
        return None
```

## CI/CD Integration

### GitHub Actions Dependency Caching
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest
```

## Integration Points

- Coordinates with **TestEngineer** for version testing
- Supports **PerformanceOptimizer** with profiling tools
- Enables **DocumentationMaintainer** with doc dependencies
- Maintains environments for **CIAgent**

## Best Practices

1. **Pin major versions** for stability
2. **Test with minimum versions** regularly
3. **Update conservatively** in production
4. **Document version requirements** clearly
5. **Use lock files** for reproducibility
6. **Monitor security** vulnerabilities
7. **Test cross-platform** compatibility
8. **Cache dependencies** in CI/CD