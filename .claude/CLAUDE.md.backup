# SolarWindPy Claude Code Configuration

## Quick Development Commands

### Essential Commands
```bash
# Test and quality assurance
pytest -q                           # Run all tests (must pass)
black .                             # Format code
flake8                              # Lint code
python scripts/update_conda_recipe.py  # Update conda recipe

# Environment setup
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .
```

## Development Workflow Priorities

### Always Required
1. All tests must pass: `pytest -q`
2. Code must be formatted: `black .`
3. No linting errors: `flake8`
4. NumPy-style docstrings required
5. Target ≥95% code coverage

### Key Validation Agents
- **PhysicsValidator**: Verify units, thermal speeds (mw² = 2kT), ion ratios
- **DataFrameArchitect**: Maintain MultiIndex ("M", "C", "S"), use .xs() views
- **TestEngineer**: Comprehensive tests, edge cases, fixtures in conftest.py
- **NumericalStabilityGuard**: Check overflow, matrix conditioning, convergence

## Critical Architecture Rules

### Data Structure
- MultiIndex columns: ("M", "C", "S") = measurement/component/species
- Use DataFrame.xs() for memory-efficient views
- DateTime indices, NaN for missing data (not 0 or -999)
- All classes inherit from Core base class

### Physics Constraints
- SI units internal, convert only for display
- Thermal speed: mw² = 2kT convention
- Time series chronological order maintained
- Quality flags propagated through analysis

### Code Quality
- Conventional Commits: feat(module):, fix(module):, test(module):, docs:
- Inherit from base classes (Core, FitFunction, PlotBase)
- Handle failures gracefully with NaN returns
- Profile performance-critical numba functions

## Testing Strategy
- Tests in `solarwindpy/tests/` mirror source structure
- Use fixtures from `conftest.py` for common test data
- Test edge cases: empty DataFrames, single points, extreme values
- Validate against known solutions in CSV test data

## Module-Specific Guidelines
- **core/**: Physics validation, DataFrame efficiency, base class inheritance
- **fitfunctions/**: Inherit from FitFunction, robust parameter guessing, graceful failures
- **plotting/**: matplotlib conventions, TeXlabel system, log-scale handling
- **solar_activity/**: LISIRD interface, time series gaps, datetime handling