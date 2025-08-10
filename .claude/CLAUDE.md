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
# Create and activate conda environment:
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .

# Alternative: generate environment from requirements-dev.txt:
python scripts/requirements_to_conda_env.py --name solarwindpy-dev
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy-dev
pip install -e .
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

## Specialized Development Agents

When working with this codebase, consider these specialized validation and development focuses:

### Core Development Priorities
- **PhysicsValidator**: Verify physical units consistency, thermal speed calculations (mw² = 2kT), ion mass/charge ratios
- **DataFrameArchitect**: Maintain MultiIndex structure ("M", "C", "S"), use DataFrame.xs() for memory efficiency
- **TestEngineer**: Write comprehensive tests, maintain ≥95% coverage, test edge cases
- **NumericalStabilityGuard**: Check for overflow/underflow, validate matrix operations, ensure iterative convergence

### Domain-Specific Guidelines
- **FitFunctionSpecialist**: Inherit from FitFunction base, implement proper parameter guessing, handle failures gracefully
- **PlottingEngineer**: Maintain matplotlib conventions, support TeXlabel system, handle log-scale plotting
- **SolarActivityTracker**: Maintain LISIRD interface compatibility, handle missing time series data
- **PerformanceOptimizer**: Profile numba functions, optimize vectorized operations, monitor DataFrame memory usage

### Physics and Data Processing Rules
- Preserve SI units internally, convert only for display
- Missing data indicated by NaN, not zero or -999
- Time series must maintain chronological order
- Quality flags carried through analysis pipeline
- Instability thresholds depend on plasma beta and anisotropy

## Special Considerations

### Physical Units
- The `units_constants` module provides conversion factors and physical constants
- Thermal speeds assume mw² = 2kT
- Careful handling of unit conversions throughout calculations

### Performance
- Uses numba for performance-critical calculations
- Leverages pandas/numpy vectorization where possible
- Memory optimization through DataFrame views rather than copies

## Common Aliases

The package provides convenient aliases in the main namespace:
- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`
- `swp.at` → `solarwindpy.alfvenic_turbulence`

### Commit Standards
Follow Conventional Commits format:
- `feat(module):` for new features
- `fix(module):` for bug fixes
- `test(module):` for test additions/changes
- `docs:` for documentation updates
- Reference issues when applicable

## ✅ COMPLETED: Planning Agents Implementation (2025-08-09)
**Status:** Fully implemented and tested
**Total Implementation Time:** ~4.5 hours 
**All Tasks Completed:** 9/9 tasks with comprehensive testing and validation

### Key Achievements

**🎯 Complete Planning Agents Ecosystem:**
- **Plan Manager Agents**: Strategic planning with comprehensive (3,000 tokens) and streamlined (1,000 tokens) variants
- **Plan Implementer Agents**: Implementation execution with full (2,800), research-optimized (1,400), and minimal (300) token variants  
- **Plan Template System**: Standardized structure with `<checksum>` placeholder format for commit tracking
- **Status Tracking System**: Multi-source parsing with comprehensive CLI interface and JSON export

**🏗️ Plan-Per-Branch Architecture:**
- True plan isolation using dedicated `plan/<name>` branches
- Cross-branch coordination between planning and implementation
- Complete merge workflow: `feature/<name>` → `plan/<name>` → `master`
- Automated branch management and status synchronization

**📊 Status Tracking & CLI:**
- Multi-source status parsing (plan files, git branches, JSON)
- Interactive CLI with 4 commands: `list`, `status`, `summary`, `report`
- Real-time progress calculation and time estimation intelligence
- JSON export for external tool integration and automated reporting

**✅ Comprehensive Testing:**
- 10 automated tests validating entire planning architecture
- Branch isolation, checksum management, and merge workflow validation
- Integration with existing SolarWindPy test suite using pytest conventions
- 100% acceptance criteria met for plan-per-branch architecture

**⚡ Token Optimization:**
- Plan Manager: 66% reduction (3,000 → 1,000 tokens) while preserving all functionality
- Complete variant system with selection guides for optimal agent choice
- Enterprise, research, and minimal configurations for different team contexts