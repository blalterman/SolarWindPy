# 📋 Claude-Optimized Workflows for SolarWindPy

This document contains optimized workflows extracted and synthesized from the comprehensive plans in `solarwindpy/plans/`. These workflows are designed for direct execution by Claude Code.

## 🎯 **WORKFLOW-1: Documentation Implementation**

```markdown
## Documentation Build Workflow
Priority: High
Dependencies: Sphinx, sphinx_rtd_theme, napoleon

### Phase 1: Infrastructure Setup
1. Verify Sphinx configuration in `docs/source/conf.py`
   - Enable extensions: autodoc, napoleon, mathjax, viewcode
   - Set theme to sphinx_rtd_theme
   - Configure dynamic version retrieval

2. Create documentation structure:
   ```
   docs/
   ├── source/
   │   ├── conf.py
   │   ├── index.rst
   │   ├── installation.rst
   │   ├── usage.rst
   │   ├── tutorial/
   │   │   └── quickstart.rst
   │   └── api/
   ```

### Phase 2: Docstring Standardization
1. Audit all modules for NumPy-style docstrings
2. Update docstrings with required sections:
   - Parameters, Returns, Raises, Examples, Notes, References
3. Add mathematical notation using LaTeX where appropriate

### Phase 3: API Documentation
1. Run `sphinx-apidoc -o docs/source/api solarwindpy`
2. Enable autosummary_generate in conf.py
3. Build and validate: `cd docs && make clean && make html`

### Validation Checklist:
- [ ] All public functions have complete docstrings
- [ ] Examples in docstrings are executable
- [ ] Math rendering works correctly
- [ ] Cross-references resolve properly
- [ ] No Sphinx warnings during build
```

## 🧪 **WORKFLOW-2: Comprehensive Testing Implementation**

```markdown
## Testing Workflow for Module Coverage
Priority: Critical
Target Coverage: ≥95%

### Phase 1: Fixture Development
Create common fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def sample_plasma_data():
    """Standard plasma DataFrame with MultiIndex."""
    # M: measurement, C: component, S: species
    columns = pd.MultiIndex.from_tuples([
        ('n', '', 'p1'),    # density
        ('v', 'x', 'p1'),   # velocity
        ('b', 'x', ''),     # magnetic field
    ])
    # Generate synthetic data with realistic values
    n_points = 100
    times = pd.date_range('2020-01-01', periods=n_points, freq='1min')
    data = {
        ('n', '', 'p1'): np.random.uniform(1, 10, n_points),     # cm^-3
        ('v', 'x', 'p1'): np.random.uniform(300, 500, n_points), # km/s
        ('b', 'x', ''): np.random.normal(0, 5, n_points),        # nT
    }
    return pd.DataFrame(data, index=times, columns=columns)

@pytest.fixture
def edge_cases():
    """Edge case data: empty, single-point, extreme values."""
    return {
        'empty': pd.DataFrame(),
        'single': single_point_data,
        'extreme': extreme_values_data
    }
```

### Phase 2: Module Testing Strategy

#### Core Module Tests
1. **base.py**: Test abstract base class through concrete subclass
2. **plasma.py**: Test initialization, ion access, calculations
3. **ions.py**: Test species validation, thermal speeds, properties
4. **spacecraft.py**: Test trajectory integration

#### FitFunctions Module Tests
1. Test each fit type (Gaussian, PowerLaw, Exponential)
2. Verify convergence with known solutions
3. Test failure modes and error handling
4. Validate parameter bounds and constraints

#### Plotting Module Tests
1. Test plot generation without display (Agg backend)
2. Verify label formatting and TeX rendering
3. Test data aggregation and binning
4. Validate interactive features

### Phase 3: Test Execution Pattern
```bash
# Run with coverage
pytest --cov=solarwindpy --cov-report=html

# Run specific modules
pytest tests/core/ -v
pytest tests/fitfunctions/ -v

# Run with markers
pytest -m "not slow"
```

### Validation Points:
- [ ] All public methods have tests
- [ ] Edge cases covered (empty, single-point, extreme)
- [ ] Numerical accuracy validated
- [ ] Mock external dependencies
- [ ] Performance benchmarks included
```

## 🔧 **WORKFLOW-3: FitFunction Development**

```markdown
## FitFunction Implementation Workflow
Priority: Medium
Focus: Robust curve fitting with physical constraints

### Phase 1: Base Class Setup
1. Inherit from `FitFunction` abstract base
2. Implement required methods:
   ```python
   def _set_function(self):
       """Define mathematical form."""
       
   def _set_p0(self):
       """Intelligent initial parameter guess."""
       
   def _set_bounds(self):
       """Physical parameter constraints."""
   ```

### Phase 2: Fit Implementation
1. Data cleaning and validation
2. Mask construction (xmin, xmax, outside)
3. Optimization with scipy.optimize.least_squares
4. Error estimation from covariance matrix

### Phase 3: Quality Metrics
1. Calculate chi-squared per degree of freedom
2. Provide R-squared values
3. Generate confidence intervals
4. Create diagnostic plots

### Implementation Checklist:
- [ ] Function signature validated
- [ ] Initial guess algorithm tested
- [ ] Bounds physically reasonable
- [ ] Convergence monitored
- [ ] Failures handled gracefully
- [ ] TeX strings generated for plots
```

## 📊 **WORKFLOW-4: Data Structure Management**

```markdown
## DataFrame Architecture Workflow
Priority: High
Focus: Efficient MultiIndex data management

### Phase 1: Structure Validation
1. Enforce MultiIndex columns: ('M', 'C', 'S')
   - M: Measurement type (n, v, w, T, b)
   - C: Component (x, y, z) or empty
   - S: Species (p1, p2, a) or empty

2. Index requirements:
   - Primary: DatetimeIndex
   - No duplicates
   - Chronological order

### Phase 2: Memory Optimization
1. Use views via DataFrame.xs()
2. Optimize dtypes (float32 vs float64)
3. Implement chunking for large datasets
4. Clean up temporary DataFrames

### Phase 3: Data Operations
```python
# Good patterns
plasma_data = df.xs('v', level='M')  # View
ion_data = df.xs('p1', level='S', axis=1)

# Avoid
plasma_data = df[df.index.get_level_values('M') == 'v'].copy()
```

### Validation Checklist:
- [ ] MultiIndex structure correct
- [ ] Memory usage optimized
- [ ] No SettingWithCopyWarning
- [ ] Views used over copies
- [ ] Missing data handled (NaN, not 0)
```

## 🚀 **WORKFLOW-5: Performance Optimization**

```markdown
## Performance Optimization Workflow
Priority: Medium
Target: <5s for 1M point datasets

### Phase 1: Profiling
1. Profile with cProfile/line_profiler
2. Identify bottlenecks
3. Measure baseline performance

### Phase 2: Optimization Strategies
1. **Numba JIT Compilation**:
   ```python
   @njit(parallel=True, cache=True)
   def calculate_plasma_beta(n, T, B):
       # Vectorized calculation
       result = np.empty(len(n))
       for i in prange(len(n)):
           pressure = n[i] * k_B * T[i]
           mag_pressure = B[i]**2 / (2 * mu_0)
           result[i] = pressure / mag_pressure
       return result
   ```

2. **Vectorization**:
   - Replace loops with numpy operations
   - Use pandas built-in methods

3. **Caching**:
   - LRU cache for pure functions
   - Property caching for expensive calculations

### Phase 3: Validation
1. Verify numerical accuracy maintained
2. Run performance benchmarks
3. Check memory usage

### Performance Checklist:
- [ ] Hotspots identified and optimized
- [ ] Numba applied to numerical kernels
- [ ] Vectorized operations used
- [ ] Memory leaks eliminated
- [ ] Benchmarks show improvement
```

## 🔄 **WORKFLOW-6: CI/CD Integration**

```markdown
## CI/CD Workflow
Priority: Medium
Platform: GitHub Actions

### Phase 1: Test Pipeline
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        python: [3.8, 3.9, '3.10', 3.11]
        os: [ubuntu-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install -e .
    - name: Run tests
      run: pytest --cov=solarwindpy
```

### Phase 2: Documentation Build
```yaml
docs:
  steps:
  - name: Build docs
    run: |
      cd docs
      make html
      make linkcheck
```

### Phase 3: Quality Checks
1. Black formatting
2. Flake8 linting
3. Coverage thresholds
4. Performance benchmarks

### CI Checklist:
- [ ] Tests pass on all Python versions
- [ ] Documentation builds without warnings
- [ ] Coverage ≥95%
- [ ] No linting errors
- [ ] Performance benchmarks pass
```

## 📝 **WORKFLOW-7: Issue-to-Task Decomposition**

```markdown
## Task Decomposition Workflow
Use for: Breaking complex issues into manageable tasks

### Phase 1: Analysis
1. Identify scope and dependencies
2. List affected files
3. Define acceptance criteria

### Phase 2: Decomposition
Split into atomic tasks:
- Task 1: Create/update fixtures
- Task 2: Implement core functionality
- Task 3: Write tests
- Task 4: Update documentation
- Task 5: Integration testing

### Phase 3: Implementation Order
1. Dependencies first (fixtures, utilities)
2. Core implementation
3. Tests in parallel with implementation
4. Documentation updates
5. Final integration

### Template for Each Task:
```markdown
## Task: [Specific Action]
Files: [List of files to modify]
Dependencies: [What must be done first]
Acceptance: 
- [ ] Implementation complete
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No regressions
```
```

## 🎨 **WORKFLOW-8: Plotting and Visualization**

```markdown
## Plotting Implementation Workflow
Priority: Medium
Focus: Publication-quality scientific visualizations

### Phase 1: Base Infrastructure
1. Inherit from PlotBase class
2. Implement TeXlabel formatting
3. Set matplotlib rcParams for quality

### Phase 2: Plot Types
1. **Histograms**: 1D/2D with statistics
2. **Scatter**: With regression options
3. **Orbits**: 3D spacecraft trajectories
4. **Time Series**: With solar activity

### Phase 3: Features
1. Colorblind-friendly palettes
2. Log-scale handling
3. Interactive selection
4. Export to publication formats

### Implementation Checklist:
- [ ] Base class methods implemented
- [ ] Labels properly formatted
- [ ] Statistics overlays working
- [ ] Interactive features tested
- [ ] Memory efficient for large data
```

## 🔍 **Meta-Workflow: Choosing the Right Workflow**

```markdown
## Workflow Selection Guide

### By Task Type:
- **New Feature**: Use WORKFLOW-3 (FitFunction) or WORKFLOW-8 (Plotting)
- **Bug Fix**: Start with WORKFLOW-2 (Testing) to reproduce
- **Performance**: Use WORKFLOW-5 (Optimization)
- **Documentation**: Use WORKFLOW-1 (Documentation)
- **Data Issues**: Use WORKFLOW-4 (DataFrame)

### By Priority:
1. Critical: WORKFLOW-2 (Testing) → Fix → Test
2. High: WORKFLOW-4 (DataFrame) → WORKFLOW-1 (Docs)
3. Medium: WORKFLOW-3/5/8 based on need
4. Low: WORKFLOW-6 (CI/CD) maintenance

### By File Type:
- `core/*.py`: WORKFLOW-4 (DataFrame) + WORKFLOW-2 (Testing)
- `fitfunctions/*.py`: WORKFLOW-3 (FitFunction)
- `plotting/*.py`: WORKFLOW-8 (Plotting)
- `docs/*`: WORKFLOW-1 (Documentation)
- `tests/*`: WORKFLOW-2 (Testing)
```

## Source Information

These workflows were extracted and optimized from the comprehensive plans located in:
- `solarwindpy/plans/combined_plan_with_checklist_documentation.md`
- `solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md`
- `solarwindpy/plans/combined_test_plan_with_checklist_plotting.md`
- `solarwindpy/plans/combined_test_plan_with_checklist_solar_activity.md`
- `solarwindpy/plans/pre_combination_files/plan_automation_workflow.md`

Each workflow follows the established project conventions:
- NumPy-style docstrings
- pytest testing framework
- Black code formatting
- Flake8 linting
- Sphinx documentation
- MultiIndex DataFrame architecture