# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Branching Workflow

### CRITICAL: Branch-First Development

**Before ANY development work, Claude must:**

1. **List unmerged branches:**
   ```bash
   git branch -r --no-merged master
   ```

2. **Ask user for branch selection:**
   "Which branch should I use? Please specify branch name, or say 'search' if you want me to help find an appropriate branch, or say 'new' to create a new branch"

3. **Wait for explicit user instruction** - NEVER auto-select a branch

4. **If user says "search":** Help identify relevant branches by examining branch names and purposes

5. **If user says "new":** Create new branch using pattern:
   ```bash
   git checkout -b claude/YYYY-MM-DD-HH-MM-SS-module-feature-description
   git push -u origin claude/YYYY-MM-DD-HH-MM-SS-module-feature-description
   ```

### Branch Naming Convention

**Format:** `claude/YYYY-MM-DD-HH-MM-SS-module-feature-description`

**Examples:**
- `claude/2025-08-08-14-30-00-fitfunctions-add-robust-fitting`
- `claude/2025-08-08-15-15-00-plotting-improve-histogram-performance`
- `claude/2025-08-08-16-00-00-core-plasma-fix-thermal-speed-calc`

### Branch Management Rules

- **NEVER** work directly on master branch
- **ALWAYS** push feature branches for tracking: `git push -u origin <branch-name>`
- **ALWAYS** include "Generated with Claude Code" in commit messages
- **VERIFY** all tests pass before commits: `pytest -q`
- **FORMAT** code before commits: `black solarwindpy/` and `flake8`

### Merge Procedures

**When feature is complete:**

1. **Final validation:**
   ```bash
   pytest -q          # All tests must pass
   black solarwindpy/ # Format code
   flake8             # Check linting
   ```

2. **Create merge-ready commit:**
   ```bash
   git add .
   git commit -m "feat(module): descriptive commit message
   
   Generated with Claude Code
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

3. **Push and create PR:**
   ```bash
   git push origin <branch-name>
   # User creates PR through GitHub interface
   ```

### Benefits of This Workflow

- ✅ **Prevents master conflicts:** All work happens on feature branches
- ✅ **Avoids CI triggers:** GitHub Actions won't run on incomplete work
- ✅ **Enables parallel development:** Multiple features can be developed simultaneously
- ✅ **Provides audit trail:** Clear history of Claude contributions
- ✅ **Maintains clean history:** Each feature has dedicated branch and PR
- ✅ **Supports review process:** All changes go through PR review before merge

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