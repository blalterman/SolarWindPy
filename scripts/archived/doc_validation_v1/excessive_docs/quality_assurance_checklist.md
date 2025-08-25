# Documentation Review Checklist for SolarWindPy Maintainers

## Overview
This checklist ensures systematic review of documentation changes to maintain high quality, scientific accuracy, and consistency across the SolarWindPy project. Use this for all documentation-related pull requests and periodic quality audits.

## Pre-Review Setup

### Environment Preparation
- [ ] **Test Environment**: Set up clean conda environment from `solarwindpy-20250403.yml`
- [ ] **Validation Tools**: Ensure `doctest_physics_validator.py` and related tools are available
- [ ] **Branch Checkout**: Check out the branch/PR to review locally
- [ ] **Baseline Comparison**: Run validation on main branch for comparison

### Review Scope Assessment
- [ ] **Files Changed**: Identify all documentation files modified (.py docstrings, .rst, .md)
- [ ] **Example Count**: Count code examples added/modified/removed
- [ ] **Change Type**: Classify as new content, updates, fixes, or refactoring
- [ ] **Impact Assessment**: Determine potential user impact of changes

## Code Quality Review

### Syntax and Structure
- [ ] **Python Syntax**: All code blocks parse without syntax errors
  ```bash
  python -c "import ast; ast.parse(open('example.py').read())"
  ```
- [ ] **Import Completeness**: All necessary imports included at example start
- [ ] **Variable Definition**: No undefined variables or references
- [ ] **Code Organization**: Logical flow from imports → setup → usage → validation

### Import Consistency
- [ ] **Standard Aliases**: Uses `import solarwindpy as swp`, `import numpy as np`, `import pandas as pd`
- [ ] **Import Accuracy**: All imports resolve correctly in test environment
- [ ] **Dependency Availability**: All required packages available in conda environment
- [ ] **Import Efficiency**: Imports only what's needed, avoids wildcard imports

### Example Completeness
- [ ] **Self-Contained**: Examples run independently without external dependencies
- [ ] **Setup Inclusion**: Data setup/fixture creation included in examples
- [ ] **Result Verification**: Examples include assertions or output verification
- [ ] **Error Handling**: Appropriate error handling where relevant

## Physics Accuracy Review

### Thermal Speed Convention
- [ ] **Formula Adherence**: All thermal speed calculations use mw² = 2kT convention
- [ ] **Constant Values**: Boltzmann constant k_B = 1.380649e-23 J/K
- [ ] **Mass Values**: Proton mass m_p = 1.67262192e-27 kg
- [ ] **Unit Conversion**: Results converted to km/s for display

**Validation Command:**
```bash
python doctest_physics_validator.py changed_files.py --rule thermal_speed
```

### Unit Consistency
- [ ] **SI Internal**: All calculations performed in SI units
- [ ] **Display Units**: Results presented in conventional units (km/s, cm^-3, nT)
- [ ] **Conversion Accuracy**: Unit conversions mathematically correct
- [ ] **Unit Documentation**: Units clearly specified in comments and docstrings

### Missing Data Handling
- [ ] **NaN Usage**: Missing data represented with `np.nan` (never 0 or -999)
- [ ] **Missing Data Operations**: Proper handling with `.dropna()`, `~np.isnan()`
- [ ] **Validation**: No improper fill values or placeholder numbers
- [ ] **Documentation**: Missing data handling explained where relevant

### Physical Realism
- [ ] **Positive Quantities**: Densities, temperatures, speeds are positive
- [ ] **Realistic Ranges**: Values within typical solar wind parameter ranges
  - Proton density: 0.1-50 cm^-3
  - Bulk velocity: 200-800 km/s
  - Temperature: 10^4-10^7 K
  - Magnetic field: 1-50 nT
- [ ] **Physics Consistency**: Related quantities have consistent relationships

## Structure Compliance Review

### MultiIndex DataFrame Standards
- [ ] **Level Naming**: Columns use ('M', 'C', 'S') level names
  - M: Measurement type (n, v, w, b, T, etc.)
  - C: Component (x, y, z for vectors, empty for scalars)
  - S: Species (p1, p2, a, etc., empty for magnetic field)
- [ ] **Data Structure**: Follows established MultiIndex patterns
- [ ] **Index Validation**: Time series indices named 'Epoch'

**Structure Check:**
```python
# Validate MultiIndex structure
assert data.columns.names == ['M', 'C', 'S']
assert data.index.name == 'Epoch'
assert isinstance(data.index, pd.DatetimeIndex)
```

### Data Access Patterns
- [ ] **Efficient Access**: Uses `.xs()` method for MultiIndex operations
- [ ] **Level Specification**: Explicitly specifies level names in `.xs()` calls
- [ ] **Performance**: Avoids inefficient `.loc[]` operations for MultiIndex
- [ ] **Pattern Consistency**: Follows established access patterns

### Error Prevention
- [ ] **Robust Patterns**: Uses patterns less likely to break with data changes
- [ ] **Explicit Operations**: Avoids implicit operations that may fail
- [ ] **Defensive Coding**: Includes appropriate assertions and checks
- [ ] **Graceful Degradation**: Handles edge cases appropriately

## User Experience Review

### Clarity and Education
- [ ] **Learning Progression**: Examples build understanding incrementally
- [ ] **Clear Purpose**: Each example has clear educational objective
- [ ] **Realistic Usage**: Demonstrates actual usage patterns
- [ ] **Context**: Sufficient context for understanding when to use

### Documentation Quality
- [ ] **Complete Docstrings**: All functions have comprehensive docstrings
- [ ] **Parameter Documentation**: All parameters documented with types and units
- [ ] **Return Documentation**: Return values documented with types and descriptions
- [ ] **Example Integration**: Examples integrate well with function documentation

### Accessibility
- [ ] **Beginner Friendly**: Examples accessible to new users
- [ ] **Expert Relevant**: Advanced examples for experienced users
- [ ] **Cross-Reference**: Good linking between related examples
- [ ] **Troubleshooting**: Common issues addressed in examples or comments

## Automated Validation Review

### Framework Execution
- [ ] **Validation Success**: All examples pass automated validation
  ```bash
  python doctest_physics_validator.py changed_files/ --comprehensive
  ```
- [ ] **Physics Compliance**: No physics rule violations detected
- [ ] **Performance**: Validation completes in reasonable time (<2 minutes)
- [ ] **Clean Output**: No warnings or unexpected messages

### CI/CD Integration
- [ ] **Pipeline Success**: GitHub Actions validation passes
- [ ] **Multi-Python**: Tests pass on Python 3.9, 3.10, 3.11
- [ ] **Artifact Generation**: Reports and metrics generated successfully
- [ ] **Performance Monitoring**: Validation time within acceptable limits

### Coverage Assessment
- [ ] **Example Coverage**: All new functions have documented examples
- [ ] **Pattern Coverage**: Examples cover main usage patterns
- [ ] **Edge Case Coverage**: Important edge cases demonstrated
- [ ] **Integration Coverage**: Examples show integration between modules

## Scientific Accuracy Review

### Domain Expert Validation
- [ ] **Physics Correctness**: Calculations follow established physics principles
- [ ] **Scientific Conventions**: Uses accepted conventions in space physics
- [ ] **Literature Alignment**: Consistent with published scientific literature
- [ ] **Methodology Soundness**: Analysis methods scientifically appropriate

### Peer Review Process
- [ ] **Expert Review**: Domain expert has reviewed physics content
- [ ] **Calculation Verification**: Independent verification of key calculations
- [ ] **Convention Checking**: Verification of physics convention adherence
- [ ] **Accuracy Confirmation**: Confirmation of scientific accuracy

### Quality Metrics
- [ ] **Quantitative Validation**: Numbers checked against known results
- [ ] **Dimensional Analysis**: All equations dimensionally consistent
- [ ] **Sanity Checks**: Results pass basic physics sanity checks
- [ ] **Benchmark Comparison**: Where possible, compared against benchmarks

## Consistency and Standards Review

### Style Consistency
- [ ] **Code Style**: Follows established code formatting conventions
- [ ] **Documentation Style**: Consistent with existing documentation patterns
- [ ] **Naming Conventions**: Variable and function names follow project standards
- [ ] **Comment Style**: Comments follow established formatting and content guidelines

### Pattern Adherence
- [ ] **Example Templates**: Examples follow established templates
- [ ] **Import Patterns**: Imports follow project conventions
- [ ] **Data Setup Patterns**: Data creation follows standard patterns
- [ ] **Validation Patterns**: Result validation follows consistent approaches

### Integration Quality
- [ ] **Cross-Module Consistency**: Consistent patterns across different modules
- [ ] **API Alignment**: Examples align with current API design
- [ ] **Backward Compatibility**: Changes maintain backward compatibility
- [ ] **Future Compatibility**: Examples designed for future maintainability

## Performance and Efficiency Review

### Execution Performance
- [ ] **Example Speed**: Examples execute quickly (typically <1 second each)
- [ ] **Memory Usage**: Examples use reasonable amount of memory
- [ ] **Resource Efficiency**: No unnecessary resource consumption
- [ ] **Scalability**: Examples work well at different data sizes

### Validation Performance
- [ ] **Validation Speed**: Changes don't significantly slow validation
- [ ] **Framework Efficiency**: Efficient use of validation framework
- [ ] **Parallel Compatibility**: Examples work well with parallel validation
- [ ] **Caching Effectiveness**: Good interaction with validation caching

### Maintenance Efficiency
- [ ] **Update Ease**: Examples easy to update when APIs change
- [ ] **Debug Friendliness**: Examples provide useful information when failing
- [ ] **Monitoring Integration**: Good integration with monitoring/alerting systems
- [ ] **Documentation Maintenance**: Easy to maintain documentation quality

## Final Review Steps

### Comprehensive Testing
```bash
# Run full validation suite
python doctest_physics_validator.py solarwindpy/ --comprehensive \
  --output-report review_validation.json \
  --text-report review_validation.txt

# Check specific physics rules
python doctest_physics_validator.py solarwindpy/ --physics-only

# Test in clean environment
conda env create -f solarwindpy-20250403.yml -n review-env
conda activate review-env
pip install -e .
python -m pytest --doctest-modules solarwindpy/ -v
```

### Quality Metrics Verification
- [ ] **Success Rate**: >95% example execution success rate
- [ ] **Physics Compliance**: 100% physics rule compliance
- [ ] **Performance**: Validation completes in <2 minutes
- [ ] **Coverage**: All modified functions have examples

### Documentation Updates
- [ ] **Changelog**: Changes documented appropriately
- [ ] **Guidelines**: Any new patterns added to contributor guidelines
- [ ] **Troubleshooting**: New issues/solutions added to troubleshooting guide
- [ ] **Maintenance**: Maintenance procedures updated if needed

## Sign-Off Checklist

### Technical Approval
- [ ] **Code Quality**: All code quality checks pass
- [ ] **Physics Accuracy**: Domain expert approval obtained
- [ ] **Performance**: Performance requirements met
- [ ] **Integration**: Proper integration with existing codebase

### Documentation Approval
- [ ] **Completeness**: All documentation requirements met
- [ ] **Clarity**: Examples clear and educational
- [ ] **Accuracy**: Technical accuracy verified
- [ ] **Consistency**: Style and pattern consistency maintained

### Process Compliance
- [ ] **Review Process**: All review steps completed
- [ ] **Validation**: Automated validation passes
- [ ] **Testing**: Manual testing completed successfully
- [ ] **Standards**: All project standards met

## Post-Review Actions

### Merge Preparation
```bash
# Final validation before merge
python doctest_physics_validator.py solarwindpy/ --comprehensive
git status  # Verify no unexpected changes
git log --oneline -10  # Review commit history
```

### Monitoring Setup
- [ ] **Metric Baselines**: Update quality metrics baselines
- [ ] **Alert Thresholds**: Adjust monitoring alert thresholds if needed
- [ ] **Performance Tracking**: Set up tracking for any new performance metrics
- [ ] **Quality Monitoring**: Ensure ongoing quality monitoring includes changes

### Knowledge Transfer
- [ ] **Documentation Updates**: Update internal documentation as needed
- [ ] **Team Communication**: Communicate significant changes to team
- [ ] **Process Improvements**: Document any process improvements discovered
- [ ] **Training Updates**: Update training materials if needed

---

## Review Outcome Classifications

### ✅ Approved
All checklist items complete, meets all quality standards, ready for merge.

### ⚠️ Approved with Minor Issues  
Minor issues noted but don't block merge, follow-up tasks created.

### ❌ Changes Requested
Significant issues found, changes required before approval.

### 🔄 Under Review
Review in progress, additional time or expert input needed.

---

This checklist ensures thorough, consistent review of all documentation changes while maintaining SolarWindPy's high standards for scientific accuracy and user experience.