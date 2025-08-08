# AGENTS-claude.md for SolarWindPy

## Core Development Agents

### General
**Applies to:** *  
**Priority:** Always Active  
**Instructions:**
- Use Python 3.11+; ensure conda environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- **CRITICAL GIT WORKFLOW:** Before ANY development:
  - List unmerged branches: `git branch -r --no-merged master`
  - Ask user to specify branch or request search/new branch creation
  - NEVER work directly on master branch
  - Use branch pattern: `claude/YYYY-MM-DD-HH-MM-SS-module-feature-description`
- Run `pytest -q` before ANY commit; all tests MUST pass
- Format with `black solarwindpy/` and lint with `flake8`
- Use NumPy-style docstrings for all public functions
- Follow Conventional Commits format (feat/fix/test/docs)
- Include "Generated with Claude Code" in commit messages
- Reference GitHub issues when applicable

### PhysicsValidator
**Applies to:** solarwindpy/core/**/*.py, solarwindpy/instabilities/**/*.py  
**Priority:** High  
**Instructions:**
- Verify physical units consistency using units_constants module
- Check thermal speed calculations (mw² = 2kT convention)
- Validate ion mass/charge ratios match physical constants
- Ensure magnetic field components maintain proper vector relationships
- Flag any calculations that violate conservation laws
- Verify Coulomb number calculations when spacecraft data present

### DataFrameArchitect
**Applies to:** solarwindpy/core/**/*.py  
**Priority:** High  
**Instructions:**
- Maintain MultiIndex structure: ("M", "C", "S") for measurement/component/species
- Use DataFrame.xs() for views to minimize memory usage
- Ensure datetime indices (typically "Epoch") are properly formatted
- Validate data alignment when combining plasma/spacecraft data
- Optimize memory usage through views rather than copies
- Check for pandas SettingWithCopyWarning issues

### TestEngineer
**Applies to:** solarwindpy/tests/**/*.py  
**Priority:** High  
**Instructions:**
- Write tests for all public functions using pytest
- Maintain ≥95% code coverage
- Use fixtures from conftest.py for common test data
- Test edge cases: empty DataFrames, single-point data, missing species
- Verify numerical accuracy against known solutions
- Test data I/O with CSV files in tests/data/
- Isolate tests; avoid unnecessary mocks

### FitFunctionSpecialist
**Applies to:** solarwindpy/fitfunctions/**/*.py  
**Priority:** Medium  
**Instructions:**
- Ensure all fit functions inherit from FitFunction base class
- Implement proper initial parameter guessing
- Handle fit failures gracefully (return NaN arrays)
- Verify chi-squared calculations for goodness of fit
- Test robust fitting options (Huber, soft_l1, Cauchy)
- Document mathematical forms in docstrings with LaTeX

### PlottingEngineer
**Applies to:** solarwindpy/plotting/**/*.py  
**Priority:** Medium  
**Instructions:**
- Maintain consistency with matplotlib conventions
- Ensure all plot classes inherit from appropriate base classes
- Implement proper label formatting via TeXlabel system
- Support both 1D and 2D histograms with consistent APIs
- Handle log-scale plotting correctly
- Test plot generation without displaying (for CI/CD)

### SolarActivityTracker
**Applies to:** solarwindpy/solar_activity/**/*.py  
**Priority:** Medium  
**Instructions:**
- Maintain LISIRD interface compatibility
- Update sunspot number data (ssn_extrema.csv) when needed
- Verify extrema calculations for solar cycles
- Handle missing data gracefully in time series
- Ensure proper datetime handling for solar indices
- Document data sources and update frequencies

### PerformanceOptimizer
**Applies to:** solarwindpy/core/**/*.py, solarwindpy/tools/**/*.py  
**Priority:** Medium  
**Instructions:**
- Profile numba-decorated functions for performance
- Optimize vectorized operations over loops
- Monitor memory usage in large DataFrame operations
- Cache expensive calculations where appropriate
- Use parallel processing for independent calculations
- Document performance considerations in comments

### DocumentationMaintainer
**Applies to:** docs/**/*.rst, **/*.py, README.rst  
**Priority:** Medium  
**Instructions:**
- Maintain NumPy-style docstrings for all public APIs
- Update Sphinx documentation when adding features
- Include usage examples in docstrings
- Keep README.rst current with installation instructions
- Document physical assumptions and limitations
- Generate API docs with proper cross-references

### DependencyManager
**Applies to:** requirements*.txt, pyproject.toml, setup.cfg, conda recipe/meta.yaml  
**Priority:** Low  
**Instructions:**
- Keep dependencies pinned for reproducibility
- Update conda recipe with `python scripts/update_conda_recipe.py`
- Test compatibility with minimum supported versions
- Document any version-specific workarounds
- Avoid adding unnecessary dependencies
- Maintain Python 3.7+ compatibility

### CodeRefactorer
**Applies to:** solarwindpy/**/*.py  
**Priority:** Low  
**Instructions:**
- Break functions >50 lines into smaller components
- Extract common patterns into utility functions
- Remove dead code and unused imports
- Preserve all public APIs (check __all__ exports)
- Improve variable naming for clarity
- Reduce cognitive complexity in nested conditions

### IonSpeciesValidator
**Applies to:** solarwindpy/core/ions.py, solarwindpy/core/plasma.py  
**Priority:** Medium  
**Instructions:**
- Validate species strings match expected patterns (p1, p2, a, etc.)
- Ensure mass/charge ratios are physically correct
- Check thermal/bulk velocity relationships
- Verify anisotropy calculations (parallel/perpendicular)
- Validate inter-species drift velocities
- Handle missing species data appropriately

### NumericalStabilityGuard
**Applies to:** solarwindpy/fitfunctions/**/*.py, solarwindpy/instabilities/**/*.py  
**Priority:** High  
**Instructions:**
- Check for numerical overflow/underflow conditions
- Validate matrix operations for conditioning
- Ensure iterative solvers converge properly
- Handle edge cases in logarithmic calculations
- Verify statistical measures with small sample sizes
- Test stability with extreme parameter values

### CIAgent
**Applies to:** .github/workflows/*.yml, tox.ini  
**Priority:** Low  
**Instructions:**
- Ensure GitHub Actions workflows are valid
- Test against multiple Python versions (3.8, 3.9+)
- Run full test suite in CI pipeline
- Check code coverage reports
- Validate documentation builds
- Monitor for deprecation warnings

## Agent Interaction Patterns

### Priority Cascade
1. **Always Active:** General → PhysicsValidator → DataFrameArchitect
2. **Feature Development:** TestEngineer → Domain Specialist → DocumentationMaintainer
3. **Code Quality:** CodeRefactorer → PerformanceOptimizer → NumericalStabilityGuard
4. **Release Prep:** DependencyManager → CIAgent → DocumentationMaintainer

### Collaboration Rules
- PhysicsValidator must approve all core physics changes
- TestEngineer validates all new code before merge
- DataFrameArchitect reviews all data structure modifications
- Multiple agents can work in parallel on independent modules
- Conflicts resolved by priority level (High > Medium > Low)

### Validation Checkpoints
- Pre-commit: Format (black) → Lint (flake8) → Test (pytest)
- Pre-merge: Coverage check → Documentation build → CI pass
- Post-merge: Performance regression → Numerical accuracy → API compatibility

## Domain-Specific Guidelines

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

### Data Corruption
1. Validate against known test data in `tests/data/`
2. Check MultiIndex integrity
3. Verify datetime index continuity
4. Restore from version control if necessary