# Combined Test Plan with Checklist: Solar Activity - Overview

## Plan Metadata
- **Plan Name**: Combined Test Plan with Checklist: Solar Activity
- **Created**: 2025-08-03
- **Branch**: plan/solar-activity-testing
- **Implementation Branch**: feature/solar-activity-testing
- **PlanManager**: PlanManager
- **PlanImplementer**: PlanImplementer
- **Structure**: Multi-Phase
- **Total Phases**: 7
- **Dependencies**: None
- **Affects**: solarwindpy/solar_activity/*, tests/solar_activity/*
- **Estimated Duration**: 10.5-15.5 hours
- **Status**: In Progress

## Phase Overview
- [x] **Phase 1: Package Entry Point** (Est: 2 hours) - Test __init__.py and get_all_indices() functionality
  - Commit: `c145774`
  - Status: Completed
  - Tests: 14/14 passing with comprehensive mocking
- [x] **Phase 2: Core Base Classes** (Est: 2 hours) - Test base.py abstract classes and common functionality  
  - Commit: `2713d8a`
  - Status: Completed
  - Tests: 30/33 passing with extensive coverage
- [ ] **Phase 3: Plotting Helpers** (Est: 2 hours) - Test plots.py visualization utilities
- [ ] **Phase 4: LISIRD Sub-package** (Est: 3 hours) - Test LISIRD data interface and extrema calculator
- [ ] **Phase 5: Extrema Calculator** (Est: 2 hours) - Test solar activity extrema detection
- [ ] **Phase 6: Sunspot Number Sub-package** (Est: 3 hours) - Test SIDC interface and SSN extrema functionality
- [ ] **Phase 7: Sunspot Number Package Init** (Est: 0.5 hours) - Test sunspot_number/__init__.py package structure

## Phase Files
1. [1-Package-Entry-Point-__init__.py.md](./1-Package-Entry-Point-__init__.py.md)
2. [2-Core-Base-Classes-base.py.md](./2-Core-Base-Classes-base.py.md)
3. [3-Plotting-Helpers-plots.py.md](./3-Plotting-Helpers-plots.py.md)
4. [4-LISIRD-Sub-package.md](./4-LISIRD-Sub-package.md)
5. [5-Extrema-Calculator.md](./5-Extrema-Calculator.md)
6. [6-Sunspot-Number-Sub-package.md](./6-Sunspot-Number-Sub-package.md)
7. [7-Sunspot-Number-Init.py.md](./7-Sunspot-Number-Init.py.md)

## 🎯 Objective
Implement comprehensive test coverage for the `solarwindpy.solar_activity` submodule to ensure correctness, robustness, and maintain ≥95% code coverage for solar indices tracking, LISIRD interface, and sunspot number processing with proper mocking of external HTTP interactions.

## 🧠 Context
The `solarwindpy.solar_activity` submodule provides interfaces for tracking solar activity indices including Lyman-α, Ca-K, SSN, and Mg-II data from external sources (LISIRD, SIDC). The module requires comprehensive testing with mocked external interactions to verify behavior while isolating side effects from network dependencies.

## 🔧 Technical Requirements
- **Testing Framework**: pytest with unittest.mock for HTTP mocking
- **Dependencies**: pandas, numpy, urllib, requests
- **Mocking**: Network calls, file I/O, external data sources
- **Fixtures**: tmp_path, monkeypatch for side effect isolation
- **Style**: black (88 char line length), flake8 compliance
- **Coverage**: ≥95% code coverage requirement
- **Test Execution**: pytest -q (quiet mode), no skipped tests

## 📂 Affected Areas
- `solarwindpy/solar_activity/__init__.py` - Package entry point and aggregation functions
- `solarwindpy/solar_activity/base.py` - Abstract base classes
- `solarwindpy/solar_activity/plots.py` - Solar activity plotting utilities
- `solarwindpy/solar_activity/lisird/` - LISIRD data interface subpackage
- `solarwindpy/solar_activity/sunspot_number/sidc.py` - SIDC sunspot number interface
- `solarwindpy/solar_activity/sunspot_number/__init__.py` - Sunspot number package initialization
- `tests/solar_activity/` - All test files and fixtures

## ✅ Acceptance Criteria
- [ ] All 7 phases completed successfully
- [ ] All tests pass with pytest -q
- [ ] Code coverage maintained ≥95%
- [ ] All external HTTP interactions properly mocked
- [ ] File I/O operations isolated with tmp_path fixtures
- [ ] get_all_indices() aggregation function validated
- [ ] LISIRD interface tested with synthetic responses
- [ ] SIDC sunspot number processing validated
- [ ] Sunspot number package initialization tested
- [ ] Extrema calculation algorithms tested
- [ ] Error handling and edge cases covered

## 🧪 Testing Strategy
- **Mock Testing**: All external HTTP requests and file downloads
- **Unit Testing**: Individual class and method validation
- **Integration Testing**: Cross-module solar activity functionality
- **Fixture Isolation**: Use tmp_path and monkeypatch to prevent side effects
- **Data Validation**: Test time series aggregation and missing data handling
- **Error Simulation**: Network failures, malformed responses, missing files

## 📊 Progress Tracking

### Overall Status
- **Phases Completed**: 2/7
- **Tasks Completed**: 44/TBD (Phase 1: 14 tests, Phase 2: 30 tests)
- **Time Invested**: 4h of 10.5-15.5h (on track)
- **Last Updated**: 2025-08-12

### Implementation Notes
<!-- Running log of implementation decisions, blockers, changes -->

#### Phase 1 & 2 Completion (2025-08-12)
- **Comprehensive Mocking**: Successfully implemented professional mocking patterns for LISIRD and SIDC classes
- **Test Architecture**: Created robust test structure with proper fixtures and tmp_path isolation
- **DataFrame Structure**: Learned that extrema data requires `columns.names = ["kind"]` for stack/unstack operations
- **Coverage Achievement**: 44 test cases covering package entry point and all 5 base classes
- **Challenges Overcome**: Fixed extrema interval calculations, logger inheritance patterns, and abstract class testing
- **Quality**: All tests use proper pytest patterns with fixtures, mocking, and edge case handling

## 🔗 Related Plans
- Fitfunctions Testing Implementation (completed) - Similar testing patterns
- Test Directory Consolidation - Affects test file organization
- Infrastructure testing improvements

## 💬 Notes & Considerations

### Technical Considerations
- **Network Isolation**: All HTTP interactions must be mocked to prevent test flakiness
- **Data Freshness**: Tests should not depend on current solar activity data
- **Time Series Handling**: Complex datetime index operations require careful validation
- **External Dependencies**: LISIRD and SIDC interfaces can change, requiring robust mocking

### Testing Patterns
- Use unittest.mock.patch for urllib.request and HTTP operations
- Create synthetic DataFrames mimicking real solar activity data structure
- Test both successful data retrieval and graceful error handling
- Validate proper handling of missing or incomplete time series data

### Risk Mitigation
- **Network Dependencies**: Comprehensive mocking prevents external service failures from breaking tests
- **Data Format Changes**: Mock responses use known data structures to ensure test stability
- **Performance**: Avoid actual network calls to maintain fast test execution

---
*This multi-phase plan uses the plan-per-branch architecture where implementation occurs on feature/combined-test-solar-activity branch with progress tracked via commit checksums across phase files.*