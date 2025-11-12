# AGENTS-claude.md for SolarWindPy

**Last Synchronized:** November 12, 2025
**Status:** Aligned with `.claude/agents/` implementation (7 active agents)

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
  - Use GitHub Issues workflow: feature/* branches created directly from GitHub Issues
  - Follow GitHub Issues → feature/* → PR → master progression
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

### UnifiedPlanCoordinator
**Applies to:** All planning and implementation
**Priority:** High
**Instructions:**
- Execute CLI scripts directly (.claude/scripts/gh-plan-*.sh)
- Use batch mode for phase creation (tmp/phases.conf)
- Integrate with hooks (plan-value-generator.py, plan-scope-auditor.py)
- Create GitHub Issues for plans, not text descriptions
- Track velocity and provide time estimates
- Follow value propositions framework

## Agent Interaction Patterns

### Priority Cascade
1. **Always Active:** General → PhysicsValidator → DataFrameArchitect
2. **Feature Development:** TestEngineer → Domain Specialist
3. **Code Quality:** NumericalStabilityGuard
4. **Planning:** UnifiedPlanCoordinator

### Collaboration Rules
- PhysicsValidator must approve all core physics changes
- TestEngineer validates all new code before merge
- DataFrameArchitect reviews all data structure modifications
- Multiple agents can work in parallel on independent modules
- Conflicts resolved by priority level (High > Medium > Low)

### Validation Checkpoints
- Pre-commit: Format (black) → Lint (flake8) → Test (pytest)
- Pre-merge: Coverage check → Documentation build → CI pass
- Post-merge: Numerical accuracy → API compatibility

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

### Data Corruption
1. Validate against known test data in `tests/data/`
2. Check MultiIndex integrity
3. Verify datetime index continuity
4. Restore from version control if necessary

## Historical Note

For information on removed agents (PerformanceOptimizer, DocumentationMaintainer, DependencyManager) and never-implemented agents (SolarActivityTracker, CodeRefactorer, IonSpeciesValidator, CIAgent), see `.claude/docs/AGENTS.md`.