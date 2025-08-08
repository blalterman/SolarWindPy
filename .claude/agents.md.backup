# SolarWindPy Development Agents

## Core Development Agents (Always Active)

### General
- Use Python 3.11+; ensure conda environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Run `pytest -q` before ANY commit; all tests MUST pass
- Format with `black .` and lint with `flake8`
- Use NumPy-style docstrings for all public functions
- Follow Conventional Commits format (feat/fix/test/docs)

### PhysicsValidator (HIGH PRIORITY)
**Applies to:** solarwindpy/core/**/*.py, solarwindpy/instabilities/**/*.py
- Verify physical units consistency using units_constants module
- Check thermal speed calculations (mw² = 2kT convention)
- Validate ion mass/charge ratios match physical constants
- Ensure magnetic field components maintain proper vector relationships
- Flag any calculations that violate conservation laws
- Verify Coulomb number calculations when spacecraft data present

### DataFrameArchitect (HIGH PRIORITY)
**Applies to:** solarwindpy/core/**/*.py
- Maintain MultiIndex structure: ("M", "C", "S") for measurement/component/species
- Use DataFrame.xs() for views to minimize memory usage
- Ensure datetime indices (typically "Epoch") are properly formatted
- Validate data alignment when combining plasma/spacecraft data
- Optimize memory usage through views rather than copies
- Check for pandas SettingWithCopyWarning issues

### TestEngineer (HIGH PRIORITY)
**Applies to:** solarwindpy/tests/**/*.py
- Write tests for all public functions using pytest
- Maintain ≥95% code coverage
- Use fixtures from conftest.py for common test data
- Test edge cases: empty DataFrames, single-point data, missing species
- Verify numerical accuracy against known solutions
- Test data I/O with CSV files in tests/data/
- Isolate tests; avoid unnecessary mocks

### NumericalStabilityGuard (HIGH PRIORITY)
**Applies to:** solarwindpy/fitfunctions/**/*.py, solarwindpy/instabilities/**/*.py
- Check for numerical overflow/underflow conditions
- Validate matrix operations for conditioning
- Ensure iterative solvers converge properly
- Handle edge cases in logarithmic calculations
- Verify statistical measures with small sample sizes
- Test stability with extreme parameter values

## Domain-Specific Agents (Medium Priority)

### FitFunctionSpecialist
**Applies to:** solarwindpy/fitfunctions/**/*.py
- Ensure all fit functions inherit from FitFunction base class
- Implement proper initial parameter guessing
- Handle fit failures gracefully (return NaN arrays)
- Verify chi-squared calculations for goodness of fit
- Test robust fitting options (Huber, soft_l1, Cauchy)
- Document mathematical forms in docstrings with LaTeX

### PlottingEngineer
**Applies to:** solarwindpy/plotting/**/*.py
- Maintain consistency with matplotlib conventions
- Ensure all plot classes inherit from appropriate base classes
- Implement proper label formatting via TeXlabel system
- Support both 1D and 2D histograms with consistent APIs
- Handle log-scale plotting correctly
- Test plot generation without displaying (for CI/CD)

### SolarActivityTracker
**Applies to:** solarwindpy/solar_activity/**/*.py
- Maintain LISIRD interface compatibility
- Update sunspot number data (ssn_extrema.csv) when needed
- Verify extrema calculations for solar cycles
- Handle missing data gracefully in time series
- Ensure proper datetime handling for solar indices
- Document data sources and update frequencies

### PerformanceOptimizer
**Applies to:** solarwindpy/core/**/*.py, solarwindpy/tools/**/*.py
- Profile numba-decorated functions for performance
- Optimize vectorized operations over loops
- Monitor memory usage in large DataFrame operations
- Cache expensive calculations where appropriate
- Use parallel processing for independent calculations
- Document performance considerations in comments

### IonSpeciesValidator
**Applies to:** solarwindpy/core/ions.py, solarwindpy/core/plasma.py
- Validate species strings match expected patterns (p1, p2, a, etc.)
- Ensure mass/charge ratios are physically correct
- Check thermal/bulk velocity relationships
- Verify anisotropy calculations (parallel/perpendicular)
- Validate inter-species drift velocities
- Handle missing species data appropriately

## Priority Cascade System

1. **Always Active:** General → PhysicsValidator → DataFrameArchitect
2. **Feature Development:** TestEngineer → Domain Specialist → DocumentationMaintainer
3. **Code Quality:** NumericalStabilityGuard → PerformanceOptimizer
4. **Release Prep:** DependencyManager → CI validation

## Physics Domain Rules

### Solar Wind Physics
- Alfvén speed calculations must account for ion composition
- Coulomb collisions require valid temperature/density ranges
- Instability thresholds depend on plasma beta and anisotropy
- Preserve SI units internally, convert for display only

### Data Processing
- Missing data indicated by NaN, not zero or -999
- Interpolation methods must preserve physical constraints
- Time series must maintain chronological order
- Quality flags carried through analysis pipeline

### Visualization Standards
- Default to publication-quality figures
- Support both interactive and static plotting
- Color schemes must be colorblind-friendly
- Axes labels include units when applicable

## Emergency Protocols

### Test Failure
1. Identify failing test(s) with `pytest -v`
2. Check recent changes with `git diff`
3. Verify environment with `conda list`
4. Run isolated test with `pytest path/to/test::specific_test`
5. If physics-related, consult PhysicsValidator agent

### Performance Degradation
1. Profile with `python -m cProfile`
2. Check DataFrame memory usage with `.memory_usage(deep=True)`
3. Review recent numba compilation
4. Consider algorithmic improvements before optimization