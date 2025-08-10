# Fitfunctions Testing Implementation Plan

## Plan Metadata
- **Plan Name**: Fitfunctions Testing Implementation
- **Created**: 2025-08-10
- **Branch**: plan/fitfunctions-testing
- **Implementation Branch**: feature/fitfunctions-testing
- **Estimated Duration**: 12-15 hours
- **Status**: Planning

## 🎯 Objective

Implement comprehensive test coverage for the `solarwindpy.fitfunctions` submodule to ensure correctness, robustness, and maintain ≥95% code coverage. This plan consolidates and restructures the existing 749 lines of technical specifications into a compliant workflow.

## 🧠 Context

The `solarwindpy.fitfunctions` module provides mathematical fitting utilities for scientific data analysis, including:
- `FitFunction` base class with observation filtering and fitting workflows
- Specialized functions: `Gaussian`, `Exponential`, `Line`, `PowerLaw`, and variants
- `TrendFit` for higher-level trend analysis
- `FFPlot` for publication-quality visualization
- `TeXinfo` for LaTeX label generation

**Justification for comprehensive testing:**
1. **Safety and regression**: Non-public helpers guard data integrity
2. **Numerical correctness**: Fitting and parameter extraction must remain accurate  
3. **API contracts**: String formats (TeX), plotting behaviors, and property outputs must be stable
4. **Edge cases**: Zero-size data, insufficient observations, bad weights, solver failures—ensures graceful degradation

## 🔧 Technical Requirements

- **Testing Framework**: `pytest` with fixtures
- **Dependencies**: `numpy`, `pandas`, `scipy`, `matplotlib`
- **Style**: `black` (88 char line length), `flake8` compliance
- **Coverage**: ≥95% code coverage requirement
- **Test Execution**: `pytest -q` (quiet mode), no skipped tests

## 📂 Affected Areas

- `solarwindpy/fitfunctions/core.py` - FitFunction base class
- `solarwindpy/fitfunctions/gaussians.py` - Gaussian variants
- `solarwindpy/fitfunctions/exponentials.py` - Exponential variants
- `solarwindpy/fitfunctions/lines.py` - Linear functions
- `solarwindpy/fitfunctions/power_laws.py` - Power-law variants
- `solarwindpy/fitfunctions/trend_fits.py` - TrendFit class
- `solarwindpy/fitfunctions/plots.py` - FFPlot visualization
- `solarwindpy/fitfunctions/tex_info.py` - TeXinfo formatting
- `tests/fitfunctions/` - All test files and fixtures

## 📋 Implementation Plan

### Phase 1: Test Infrastructure Setup (Estimated: 2 hours)
- [ ] **Create test directory structure** (Est: 30 min) - Set up `tests/fitfunctions/` directory
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Set up pytest configuration** (Est: 30 min) - Configure pytest for fitfunctions module
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Create conftest.py with fixtures** (Est: 1 hour) - Implement shared test fixtures
  - Commit: `<checksum>`
  - Status: Pending

### Phase 2: Common Fixtures & Test Utilities (Estimated: 1.5 hours)
- [ ] **Implement simple_linear_data fixture** (Est: 30 min) - 1D arrays with noise: `x = linspace(0,1,20)`, `y = 2*x + 1 + noise`, `w = ones_like(x)`
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Implement gauss_data fixture** (Est: 30 min) - Sample x, generate `y = A·exp(-0.5((x-μ)/σ)²) + noise`
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Implement small_n fixture** (Est: 30 min) - Too few points to trigger `sufficient_data → ValueError`
  - Commit: `<checksum>`
  - Status: Pending

### Phase 3: Core FitFunction Class Testing (Estimated: 3 hours)
- [ ] **Test initialization and observation filtering** (Est: 1 hour) - `_clean_raw_obs`, `_build_one_obs_mask`, `_build_outside_mask`, `set_fit_obs`
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test argument introspection** (Est: 30 min) - `_set_argnames` with subclass known signature
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test fitting workflow** (Est: 1 hour) - `_run_least_squares`, `_calc_popt_pcov_psigma_chisq`, `make_fit`
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test public properties** (Est: 30 min) - `__str__`, `__call__`, all properties after dummy fit
  - Commit: `<checksum>`
  - Status: Pending

### Phase 4: Specialized Function Classes (Estimated: 4 hours)
- [ ] **Test Gaussian classes** (Est: 1 hour) - `Gaussian`, `GaussianNormalized`, `GaussianLn` signatures, p0, TeX_function, make_fit
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test Exponential classes** (Est: 1 hour) - `Exponential`, `ExponentialPlusC`, `ExponentialCDF` with amplitude helpers
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test Line class** (Est: 1 hour) - Signature, p0 with linear data, TeX_function, x_intercept property
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test PowerLaw classes** (Est: 1 hour) - `PowerLaw`, `PowerLawPlusC`, `PowerLawOffCenter` with numerical stability
  - Commit: `<checksum>`
  - Status: Pending

### Phase 5: Advanced Classes Testing (Estimated: 2.5 hours)
- [ ] **Test TrendFit class** (Est: 1.5 hours) - Initialization, properties, 1D-fit pipeline, trend fitting, plot helpers, label sharing
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Test TeXinfo class** (Est: 1 hour) - Construction, properties, formatting, static helpers
  - Commit: `<checksum>`
  - Status: Pending

### Phase 6: Plotting & Integration Testing (Estimated: 2 hours)
- [ ] **Test FFPlot class** (Est: 1.5 hours) - Initialization, path generation, state mutators, plot methods, label/style setters
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Integration and validation tests** (Est: 30 min) - End-to-end testing with real data scenarios
  - Commit: `<checksum>`
  - Status: Pending

## ✅ Acceptance Criteria

### Core FitFunction Class
- [ ] Test `_clean_raw_obs` for mismatched shapes (`ValueError`) and valid inputs
- [ ] Test `_build_one_obs_mask` with `xmin`, `xmax`, `None` (masks correct)
- [ ] Test `_build_outside_mask` with `outside=None` and valid tuple
- [ ] Test `set_fit_obs` for combined masks (`x`, `y`, `wmin`, `wmax`, `logy`)
- [ ] Test `_set_argnames` on subclass with known signature
- [ ] Test `_run_least_squares` with monkey-patched optimizer and kwargs validation
- [ ] Test `_calc_popt_pcov_psigma_chisq` with dummy results
- [ ] Test `make_fit` success path, insufficient data, and optimization failure
- [ ] Test all public properties and methods after dummy fit

### Specialized Function Classes
- [ ] Test function signatures and behavior on sample data for all classes
- [ ] Test `p0` initial guesses match true parameters within tolerance
- [ ] Test `p0` handles empty data appropriately (ValueError or None)
- [ ] Test `TeX_function` matches expected LaTeX string literals
- [ ] Verify numerical stability for edge cases (large values, divide-by-zero)
- [ ] Validate broadcasting and dtype handling (float32, float64)

### Advanced Classes
- [ ] Test TrendFit initialization, type enforcement, and error handling
- [ ] Test TrendFit properties and 1D-fit pipeline with bad fit handling
- [ ] Test TrendFit plotting helpers with stubbed axes
- [ ] Test TeXinfo construction, properties, and formatting methods
- [ ] Test TeXinfo static helpers and error cases

### Plotting & Visualization
- [ ] Test FFPlot initialization, properties, and path generation
- [ ] Test FFPlot plot methods with monkey-patched matplotlib
- [ ] Test FFPlot label/style setters and error handling
- [ ] Verify axes return and legend/text behavior

### Quality Standards
- [ ] All tests pass with `pytest -q`
- [ ] Code coverage maintained ≥95%
- [ ] No skipped tests
- [ ] Code style compliance with `black` and `flake8`
- [ ] Comprehensive edge case coverage
- [ ] Proper error handling and graceful degradation

## 🧪 Testing Strategy

1. **Fixture-Based Testing**: Use shared fixtures for consistent test data
2. **Monkey Patching**: Mock external dependencies (scipy.optimize, matplotlib)
3. **Edge Case Coverage**: Test zero-size data, invalid inputs, numerical edge cases
4. **Property Testing**: Verify all properties return expected types and shapes
5. **Integration Testing**: End-to-end scenarios with realistic data
6. **Error Path Testing**: Ensure proper exception handling and error messages

## 📊 Progress Tracking

### Overall Status
- **Phases Completed**: 0/6
- **Tasks Completed**: 0/16
- **Time Invested**: 0h of 12-15h
- **Last Updated**: 2025-08-10

### Implementation Notes
- Plan restructured from 10 fragmented files into compliant workflow format
- All 749 lines of technical content preserved and organized into logical phases
- Comprehensive acceptance criteria based on existing specifications
- Ready for Plan Manager + Plan Implementer (Research-Optimized) execution

## 🔗 Related Plans
- Infrastructure testing improvements
- Code coverage optimization initiatives
- Documentation generation automation

## 💬 Notes & Considerations

### Migration Notes
- Content consolidated from `combined_test_plan_with_checklist_fitfunctions/` directory
- Original fragmented files:
  - 1-Common-fixtures.md (59 lines)
  - 2-core.py-FitFunction.md (118 lines) 
  - 3-gaussians.py-Gaussian-GaussianNormalized-GaussianLn.md (69 lines)
  - 4-trend_fits.py-TrendFit.md (99 lines)
  - 5-plots.py-FFPlot.md (98 lines)
  - 6-tex_info.py-TeXinfo.md (79 lines)
  - 7-Justification.md (49 lines)
  - 8-exponentials.md (64 lines)
  - 9-lines.md (58 lines)
  - 10-power_laws.md (56 lines)

### Technical Considerations
- Numerical stability testing for large parameters and edge cases
- Proper handling of NaN/Inf values in data and calculations
- Memory efficiency for large datasets
- Backwards compatibility with existing API

### Agent Coordination
- **Recommended Pairing**: Plan Manager + Plan Implementer (Research-Optimized)
- **Complexity Level**: High - requires deep understanding of numerical methods
- **Session Strategy**: 2-3 implementation sessions with proper checkpointing

---
*This plan follows the plan-per-branch architecture where implementation occurs on feature/fitfunctions-testing branch with progress tracked via commit checksums.*