# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Project Overview

SolarWindPy is a Python package for solar wind data analysis, focused on in situ solar wind measurements with additional tools for context (solar activity indices) and plotting methods. The package is designed for scientific research in plasma physics and space weather.

## Development Environment Setup

1. **Create and activate conda environment:**
   ```bash
   conda env create -f solarwindpy-20250403.yml
   conda activate solarwindpy-20250403
   pip install -e .
   ```

   Or generate environment from requirements-dev.txt:
   ```bash
   python scripts/requirements_to_conda_env.py --name solarwindpy-dev
   conda env create -f solarwindpy-dev.yml
   conda activate solarwindpy-dev
   pip install -e .
   ```

## Testing and Quality Assurance

- **Run tests:** `pytest -q` (use `-q` for quiet mode)
- **Run single test:** `pytest solarwindpy/tests/test_specific_file.py::test_function_name`
- **Code formatting:** Uses `black` with 88 character line length
- **Linting:** Uses `flake8` with custom configuration in setup.cfg
- **Pre-commit hooks:** `pre-commit install` (runs black and flake8 automatically)  
- **Tox testing:** Supports Python 3.8 and 3.9 via `tox`
- **Format code:** `black .`
- **Check linting:** `flake8`

## Build and Packaging

- **Update conda recipe:** `python scripts/update_conda_recipe.py` (when version or dependencies change)
- **Package structure:** Uses setuptools with pyproject.toml configuration
- **Version management:** Uses setuptools_scm for automatic versioning

## Architecture Overview

### Core Module Structure

1. **solarwindpy.core:** Foundation classes and data structures
   - `Base`/`Core`: Abstract base classes with logging, units, and constants
   - `Plasma`: Main class for solar wind plasma data analysis
   - `Vector`/`Tensor`: Mathematical representations for field/plasma quantities
   - `Ion`: Individual ion species handling
   - `Spacecraft`: Spacecraft-specific data and transformations
   - `AlfvenicTurbulence`: Specialized turbulence analysis

2. **solarwindpy.fitfunctions:** Mathematical fitting utilities
   - `FitFunction`: Base class for all fitting functions
   - Specialized functions: `Gaussian`, `Exponential`, `Line`, `PowerLaw`, `Moyal`
   - `TrendFit`: Higher-level trend analysis
   - Plotting and LaTeX support for mathematical expressions

3. **solarwindpy.plotting:** Publication-quality visualization
   - `histograms`: 1D/2D histogram plotting (`Hist1D`, `Hist2D`)
   - `labels`: LaTeX label generation for physics quantities
   - `scatter`, `spiral`, `orbits`: Specialized plot types
   - `tools`: Utility functions for subplot management and figure saving

4. **solarwindpy.solar_activity:** Solar activity indices and data
   - `lisird`: Interface to LISIRD solar data
   - `sunspot_number`: Sunspot number data and extrema calculation

5. **solarwindpy.instabilities:** Plasma instability analysis
   - Beta-anisotropy analysis
   - Instability thresholds and boundaries

### Key Design Patterns

- **Inheritance hierarchy:** All classes inherit from `Core` base class providing logging, units, and constants
- **DataFrame-centric:** Uses pandas DataFrame as primary data container with MultiIndex support
- **Units and constants:** Centralized unit conversion and physical constants via `units_constants` module
- **Modular plotting:** Separate plotting classes that can work with core data objects
- **Scientific reproducibility:** Extensive test coverage and validation

### Important Configuration

- **Pandas configuration:** `mode.chained_assignment = "raise"` for strict data handling
- **Code style:** Black formatting with 88-char line length, flake8 with custom ignores (E501, W503, D202, D205, D302, D400)
- **Dependencies:** Scientific stack (numpy, scipy, pandas, matplotlib, astropy, numba)
- **Test data:** Located in `solarwindpy/tests/data/` (epoch.csv, plasma.csv, spacecraft.csv)

## Common Aliases

The package provides convenient aliases in the main namespace:
- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`
- `swp.at` → `solarwindpy.alfvenic_turbulence`

## Development Guidelines

- Follow Conventional Commits format for commit messages (`feat(module):`, `fix(module):`, `test(module):`, `docs:`)
- Run all tests and linters before committing: `pytest -q && black . && flake8`
- Use the existing class hierarchy and inherit from `Core` for new classes
- Maintain DataFrame-based data structures with proper MultiIndex usage
- Follow the existing pattern of units/constants injection via base class
- Add comprehensive tests for new functionality, especially mathematical functions
- Use NumPy-style docstrings for all public functions with Parameters, Returns, Raises, Examples sections
- Target ≥95% code coverage for all new code

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

## File Organization and Key Locations

- **Main package:** `solarwindpy/` contains all source code
- **Tests:** Located in `solarwindpy/tests/` with pytest fixtures in `conftest.py`
- **Scripts:** Utility scripts in `scripts/` for environment setup and conda recipe updates
- **Documentation:** Sphinx docs in `docs/` directory
- **Conda environment:** Pre-configured in `solarwindpy-20250403.yml`
- **Configuration files:**
  - `pyproject.toml`: Package metadata and build configuration
  - `setup.cfg`: Flake8 linting rules and setuptools options
  - `tox.ini`: Multi-version testing configuration