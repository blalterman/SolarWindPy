# Combined Test Plan with Checklist: Plotting - Overview

## Plan Metadata
- **Plan Name**: Combined Test Plan with Checklist: Plotting
- **Created**: 2025-08-03
- **Branch**: plan/combined-test-plotting
- **Implementation Branch**: feature/combined-test-plotting
- **PlanManager**: PlanManager
- **PlanImplementer**: PlanImplementer
- **Structure**: Multi-Phase
- **Total Phases**: 9
- **Dependencies**: None
- **Affects**: solarwindpy/plotting/*, tests/plotting/*
- **Estimated Duration**: 8-12 hours
- **Status**: In Progress

## Phase Overview
- [ ] **Phase 1: Base Plotting** (Est: 1.5 hours) - Test base.py abstract class functionality
- [ ] **Phase 2: Aggregate Plotting** (Est: 1 hour) - Test agg_plot.py utilities
- [ ] **Phase 3: Histograms** (Est: 1.5 hours) - Test histogram functionality across hist1d.py, hist2d.py
- [ ] **Phase 4: Orbits** (Est: 1 hour) - Test orbits.py plotting capabilities
- [ ] **Phase 5: Tools** (Est: 1 hour) - Test tools.py utility functions
- [ ] **Phase 6: Data Selection** (Est: 1 hour) - Test select_data_from_figure.py functionality
- [ ] **Phase 7: Base Labels** (Est: 1 hour) - Test labels/base.py label generation
- [ ] **Phase 8: Special Labels** (Est: 1 hour) - Test labels/special.py specialized labels
- [ ] **Phase 9: Fixtures and Utilities** (Est: 1 hour) - Test infrastructure and shared utilities

## Phase Files
1. [1-base.py.md](./1-base.py.md)
2. [2-agg_plot.py.md](./2-agg_plot.py.md)
3. [3-histograms.py.md](./3-histograms.py.md)
4. [4-orbits.py.md](./4-orbits.py.md)
5. [5-tools.py.md](./5-tools.py.md)
6. [6-select_data_from_figure.py.md](./6-select_data_from_figure.py.md)
7. [7-labels-base.py.md](./7-labels-base.py.md)
8. [8-labels-special.py.md](./8-labels-special.py.md)
9. [9-Fixtures-and-Utilities.md](./9-Fixtures-and-Utilities.md)

## 🎯 Objective
Implement comprehensive test coverage for the `solarwindpy.plotting` subpackage to ensure correctness, robustness, and maintain ≥95% code coverage for all plotting utilities built on pandas and Matplotlib.

## 🧠 Context
The `solarwindpy.plotting` subpackage provides high-level plotting utilities for scientific data visualization, including base classes, histogram generation, orbit plotting, data selection tools, and specialized label systems. This plan ensures comprehensive testing of all classes, methods, and properties including non-public interfaces.

## 🔧 Technical Requirements
- **Testing Framework**: pytest with fixtures
- **Dependencies**: pandas, matplotlib, numpy
- **Style**: black (88 char line length), flake8 compliance
- **Coverage**: ≥95% code coverage requirement
- **Test Execution**: pytest -q (quiet mode), no skipped tests

## 📂 Affected Areas
- `solarwindpy/plotting/base.py` - Abstract base class
- `solarwindpy/plotting/agg_plot.py` - Aggregate plotting utilities
- `solarwindpy/plotting/histograms.py` - Histogram functionality
- `solarwindpy/plotting/orbits.py` - Orbit plotting
- `solarwindpy/plotting/tools.py` - General plotting tools
- `solarwindpy/plotting/select_data_from_figure.py` - Interactive data selection
- `solarwindpy/plotting/labels/base.py` - Base label generation
- `solarwindpy/plotting/labels/special.py` - Specialized labels
- `tests/plotting/` - All test files and fixtures

## ✅ Acceptance Criteria
- [ ] All 9 phases completed successfully
- [ ] All tests pass with pytest -q
- [ ] Code coverage maintained ≥ 95%
- [ ] All plotting classes and methods tested
- [ ] Non-public interfaces validated
- [ ] Edge cases and error handling covered
- [ ] Integration with pandas and matplotlib validated
- [ ] Documentation examples tested

## 🧪 Testing Strategy
- **Unit Testing**: Individual class and method validation
- **Integration Testing**: Cross-module plotting functionality
- **Edge Case Testing**: Invalid inputs, empty data, boundary conditions
- **Mock Testing**: External dependencies (matplotlib backends)
- **Property Testing**: Dynamic attribute access and label generation
- **Visual Testing**: Plot generation without display (test mode)

## 📊 Progress Tracking

### Overall Status
- **Phases Completed**: 0/9
- **Tasks Completed**: 0/TBD
- **Time Invested**: 0h of 8-12h
- **Last Updated**: 2025-08-12

### Implementation Notes
<!-- Running log of implementation decisions, blockers, changes -->

## 🔗 Related Plans
- Fitfunctions Testing Implementation (completed) - Similar testing patterns
- Test Directory Consolidation - Affects test file organization
- Infrastructure testing improvements

## 💬 Notes & Considerations

### Technical Considerations
- **Matplotlib Backend**: Tests must work in headless environments
- **Data Dependencies**: Require realistic scientific data fixtures
- **Performance**: Plotting operations can be slow, optimize test execution
- **Cross-platform**: Ensure compatibility across different OS environments

### Testing Patterns
- Follow established patterns from completed fitfunctions testing
- Use pytest fixtures for common data and plotting setups
- Mock matplotlib show() calls to prevent GUI popups during testing
- Test both successful operations and graceful error handling

---
*This multi-phase plan uses the plan-per-branch architecture where implementation occurs on feature/combined-test-plotting branch with progress tracked via commit checksums across phase files.*