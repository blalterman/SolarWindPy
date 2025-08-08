# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create conda environment from provided YAML
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .

# Alternative: generate environment from requirements
python scripts/requirements_to_conda_env.py --name solarwindpy-dev
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy-dev
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Testing
```bash
# Run all tests (must pass, no skipping)
pytest -q

# Run specific test file
pytest solarwindpy/tests/test_plasma.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code with black
black solarwindpy/

# Lint with flake8 (configured in setup.cfg)
flake8 solarwindpy/

# Install pre-commit hooks (optional)
pre-commit install
```

### Conda Recipe Management
```bash
# Update recipe when version or dependencies change
python scripts/update_conda_recipe.py
```

## Architecture Overview

### Core Data Model
The package uses a hierarchical data structure centered around `pandas.DataFrame` with three-level `MultiIndex` columns labeled ("M", "C", "S") for measurement, component, and species:
- **Plasma** (`core/plasma.py`): Central container holding ions, magnetic field, and spacecraft data
- **Ion** (`core/ions.py`): Individual ion species with moments and properties
- **Base** (`core/base.py`): Abstract base providing logging, units, and constants to all objects
- **Spacecraft** (`core/spacecraft.py`): Trajectory and velocity information

### Module Organization
- `core/`: Fundamental physics classes (plasma, ions, vectors, tensors, spacecraft)
- `fitfunctions/`: Data fitting tools with abstract `FitFunction` base class
- `plotting/`: Visualization tools including histograms, scatter plots, and specialized labels
- `solar_activity/`: Solar indices tracking (LISIRD interface, sunspot numbers)
- `instabilities/`: Plasma instability calculations
- `tools/`: Utility functions

### Data Access Patterns
- Plasma objects provide convenient attribute access: `plasma.a` returns alpha particle Ion
- All data stored in DataFrames with datetime indices (typically "Epoch")
- Heavy use of DataFrame views via `.xs()` to minimize memory usage

## Key Development Patterns

### Testing Strategy
- Tests in `solarwindpy/tests/` mirror source structure
- Use `conftest.py` for shared fixtures
- Test data stored in CSV format under `tests/data/`
- Coverage target: ≥95%

### Documentation
- NumPy-style docstrings required for all public functions
- Sphinx documentation in `docs/source/`
- Examples should be included in docstrings

### Dependency Management
- Dependencies specified in `pyproject.toml` and `requirements*.txt`
- Do not unpin dependencies without justification
- Run `python scripts/update_conda_recipe.py` after dependency changes

## Special Considerations

### Physical Units
- The `units_constants` module provides conversion factors and physical constants
- Thermal speeds assume mw² = 2kT
- Careful handling of unit conversions throughout calculations

### Performance
- Uses numba for performance-critical calculations
- Leverages pandas/numpy vectorization where possible
- Memory optimization through DataFrame views rather than copies

### Commit Standards
Follow Conventional Commits format:
- `feat(module):` for new features
- `fix(module):` for bug fixes
- `test(module):` for test additions/changes
- `docs:` for documentation updates
- Reference issues when applicable