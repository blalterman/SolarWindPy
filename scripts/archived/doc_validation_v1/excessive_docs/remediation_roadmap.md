# Phase 4 Remediation Roadmap - Systematic Code Example Fixes

## Executive Summary
Based on Phase 3 validation results, this roadmap provides a systematic approach to fixing 18 failed examples (85.7% failure rate) to achieve 95%+ success rate target.

**Current State**: 3/21 examples working (14.3% success)
**Target State**: 20/21 examples working (95%+ success)
**Improvement Needed**: +17 examples fixed

## Error-Based Remediation Strategy

### Critical Priority Fixes (3 examples - Immediate Impact)

#### 1. Fix Deprecated Plasma Constructor (2 examples)
**Examples**: `rst_example_2` (usage.rst lines 34-47)
**Error**: `TypeError: Plasma.__init__() got an unexpected keyword argument 'epoch'`
**Impact**: Critical - Primary user-facing documentation
**Estimated Time**: 45 minutes

**Current Code**:
```python
plasma = swp.Plasma(epoch=epoch)
plasma.add_ion_species('p1', density=n_p, velocity=v_p, temperature=T_p)
```

**Fixed Code**:
```python
# Create MultiIndex DataFrame structure
columns = pd.MultiIndex.from_tuples([
    ('n', '', 'p1'),   # Proton density
    ('v', 'x', 'p1'),  ('v', 'y', 'p1'), ('v', 'z', 'p1'),  # Velocity components
    ('T', '', 'p1'),   # Temperature
], names=['M', 'C', 'S'])

# Combine data into DataFrame
data_arrays = [n_p, v_p[:, 0], v_p[:, 1], v_p[:, 2], T_p]
data = pd.DataFrame(np.column_stack(data_arrays), index=epoch, columns=columns)

# Create plasma object with current API
plasma = swp.Plasma(data, ['p1'])
```

**Validation**: Verify constructor signature in current codebase
**Dependencies**: Check if `add_ion_species` method exists or needs replacement

#### 2. Undefined Object Initialization (3 examples)
**Examples**: `rst_example_3`, `rst_example_4`, `doctest_example_13`
**Error**: `NameError: name 'plasma' is not defined`
**Impact**: High - Examples assume context that doesn't exist
**Estimated Time**: 30 minutes

**Fix Strategy**: Add proper object initialization before usage
- Use success pattern from working examples
- Ensure each example is self-contained
- Add minimal required setup context

### High Priority Fixes (12 examples - Systematic Impact)

#### 3. Doctest Syntax Conversion (10-12 examples)
**Examples**: All doctest examples with `SyntaxError`
**Error**: `SyntaxError: invalid syntax` (descriptive text, >>> prompts)
**Impact**: High - Core API documentation credibility
**Estimated Time**: 90 minutes (7-8 min per example)

**Conversion Strategy**:
```python
# Before (Invalid doctest syntax)
>>> plasma = Plasma(data, 'p1', 'a')  # Protons and alphas
>>> proton_density = plasma.p1.n      # Proton number density [cm^-3]
Complex DataFrame construction example

# After (Executable Python code)
import pandas as pd
import numpy as np

# Create sample DataFrame with MultiIndex structure
data = pd.DataFrame(...)  # Proper setup
plasma = Plasma(data, ['p1', 'a'])
proton_density = plasma.p1.n
```

**Pattern**: Convert each doctest to self-contained executable example using success templates

#### 4. Missing Variable Definition Cleanup (3 examples)
**Examples**: Examples using undefined `data`, `df`, `temperature_data` variables  
**Error**: `NameError: name 'variable' is not defined`
**Impact**: Medium - Prevents example execution
**Estimated Time**: 45 minutes

**Fix Strategy**:
- Add proper variable definitions before usage
- Use realistic sample data that demonstrates intended functionality
- Ensure data structures match expected MultiIndex format

### Medium Priority Fixes (Systematic Improvements)

#### 5. Method Existence Validation (1-2 examples)
**Examples**: Examples calling non-existent methods
**Error**: `AttributeError: object has no attribute 'method'`
**Impact**: Medium - API documentation accuracy
**Estimated Time**: 30 minutes

**Fix Strategy**:
- Audit all method calls against current codebase
- Update deprecated method names
- Remove or replace non-existent method calls
- Document actual available methods

#### 6. Import Standardization (Cross-cutting)
**Examples**: Inconsistent `sw` vs `swp` aliases across files
**Impact**: Low - Consistency and maintainability
**Estimated Time**: 20 minutes

**Fix Strategy**:
- Standardize on `import solarwindpy as swp` (matches successful examples)
- Update all usage.rst examples to use consistent alias
- Create style guide for future examples

## File-by-File Remediation Plan

### docs/source/usage.rst (7 examples, Priority: Critical)
**Current Success**: 1/7 (14.3%)
**Target Success**: 7/7 (100%)
**Estimated Time**: 2.5 hours

**Example-by-Example Fixes**:
1. ✅ `rst_example_1` - Already working (imports only)
2. 🔴 `rst_example_2` - **CRITICAL**: Fix Plasma constructor + add_ion_species
3. 🔴 `rst_example_3` - Add plasma object initialization context  
4. 🔴 `rst_example_4` - Add plasma object + method validation
5. 🔴 `rst_example_5` - Fix plotting import + validate time_series function
6. 🔴 `rst_example_6` - Add plasma setup + validate validate_physics method
7. 🔴 `rst_example_7` - Define temperature_data + validate import paths

### docs/source/installation.rst (1 example, Priority: Low)
**Current Success**: 1/1 (100%)
**Target Success**: 1/1 (100%)
**Status**: ✅ No fixes needed - already working

### Python Module Doctests (13 examples, Priority: High)
**Current Success**: 2/13 (15.4%)
**Target Success**: 12/13 (92%+)
**Estimated Time**: 2 hours

**Module-by-Module Strategy**:
- **solarwindpy/core/plasma.py**: Convert 3 doctest examples to executable code
- **solarwindpy/core/ions.py**: Fix undefined `df` variable in 1 example
- **solarwindpy/tools/__init__.py**: Fix 3 examples with undefined variables
- **solarwindpy/fitfunctions/tex_info.py**: ✅ Already working (1 example)
- **Other modules**: Convert descriptive text to executable examples

## Implementation Timeline

### Week 1: Critical Fixes (3 examples)
**Day 1-2**: Fix deprecated Plasma constructor in usage.rst
- Research current Plasma API
- Create proper MultiIndex setup pattern
- Test fixes with validation framework

**Day 3**: Add object initialization to NameError examples
- Apply successful template patterns
- Ensure self-contained examples

### Week 2: Systematic Fixes (12 examples)
**Day 1-3**: Convert doctest syntax to executable code
- Use success pattern templates
- Batch process similar examples
- Test each conversion

**Day 4-5**: Variable definition cleanup and method validation
- Add proper variable initialization
- Audit method calls against codebase
- Update deprecated API usage

### Week 3: Quality Assurance & Integration
**Day 1-2**: Comprehensive testing and validation
- Run validation framework on all fixes
- Achieve 95%+ success rate target
- Document remaining edge cases

**Day 3**: Documentation and integration
- Update Phase 4 completion report
- Prepare for Phase 5 physics validation
- Create maintenance documentation

## Success Metrics & Validation

### Target Metrics
- **Overall Success Rate**: 95%+ (from current 14.3%)
- **Critical Examples**: 100% success rate (usage.rst primary examples)
- **Doctest Examples**: 90%+ success rate (after syntax conversion)
- **API Accuracy**: 100% (all method calls verified against codebase)

### Validation Process
1. **Incremental Testing**: Run validation framework after each fix
2. **Regression Prevention**: Ensure fixes don't break working examples
3. **Integration Testing**: Test examples in actual documentation context
4. **User Acceptance**: Verify examples work in fresh environment

### Quality Gates
- ❌ **Phase 4 Incomplete** if success rate < 90%
- ⚠️ **Phase 4 Review Required** if success rate 90-94%
- ✅ **Phase 4 Complete** if success rate ≥ 95%

## Risk Mitigation

### High-Risk Items
1. **Plasma Constructor Changes**: May require significant API research
   - **Mitigation**: Start with current codebase exploration
   - **Fallback**: Create wrapper/adapter if needed

2. **Missing Methods**: Some called methods may not exist
   - **Mitigation**: Audit all method calls before fixing examples
   - **Fallback**: Document missing methods for future API development

3. **Complex MultiIndex Setup**: DataFrame construction may be complex
   - **Mitigation**: Use successful examples as templates
   - **Fallback**: Create simplified examples that demonstrate concepts

### Quality Assurance
- **Backup Strategy**: Keep original examples in comments during fixes
- **Rollback Plan**: Maintain git history for easy reversion
- **Testing Strategy**: Validate each fix independently before moving to next

## Resource Requirements

**Total Estimated Time**: 8-10 hours
- Critical fixes: 2 hours
- Systematic fixes: 4 hours  
- Quality assurance: 2 hours
- Documentation: 1-2 hours

**Skills Needed**:
- Python/pandas DataFrame construction
- SolarWindPy API knowledge
- Doctest conversion experience
- Git/version control management

**Tools Required**:
- Validation framework (Phase 2 deliverable)
- Current SolarWindPy codebase access
- Testing environment setup
- Documentation build system

## Phase 5 Transition Preparation

**Phase 4 Deliverables for Phase 5**:
- ✅ 95%+ working examples for physics validation
- ✅ Consistent API usage patterns
- ✅ Self-contained example structure
- ✅ Baseline success metrics for comparison

**Phase 5 Prerequisites**:
- Working examples that can be analyzed for physics compliance
- Proper data structure setup for MultiIndex validation
- Functional thermal speed and unit calculations for testing
- Established success patterns for physics validation integration