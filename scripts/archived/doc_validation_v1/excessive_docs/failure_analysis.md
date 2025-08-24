# Documentation Code Examples - Detailed Failure Analysis

## Execution Summary
- **Total Examples Validated**: 21 (Python code examples only)
- **Success Rate**: 14.3% (3 successful, 18 failed) 
- **Average Execution Time**: 0.00003s per example
- **Import Failures**: 0 (all imports resolved successfully)
- **Examples with Output**: 1

## Error Distribution Analysis

### SyntaxError (12 occurrences - 57.1%)
**Primary Issue**: Doctest examples with invalid Python syntax

**Examples**:
- `rst_example_5`: Uses incorrect method call syntax
- `rst_example_6`: Invalid method reference patterns  
- `rst_example_7`: Complex import/variable declaration issues
- **All doctest examples (10/12 SyntaxErrors)**: Contain non-executable doctest syntax

**Root Cause**: Many doctest blocks contain descriptive text, incomplete code fragments, or >>> prompt syntax that cannot be executed directly as Python code.

**Remediation Strategy**: 
- Convert doctest examples to executable Python code
- Remove >>> prompts and descriptive text
- Complete incomplete code fragments

### NameError (3 occurrences - 14.3%)
**Primary Issue**: Undefined variables used in examples

**Specific Cases**:
- `rst_example_3`: Undefined `plasma` object (missing initialization)
- `rst_example_4`: Missing `plasma` object setup
- `doctest_example_13`: Undefined `data` variable in plasma constructor

**Root Cause**: Examples assume context/setup that is not provided within the example code.

**Remediation Strategy**:
- Add proper variable initialization before usage
- Provide minimal working context for each example
- Ensure examples are self-contained

### TypeError (2 occurrences - 9.5%)
**Primary Issue**: API mismatches and deprecated constructor usage

**Specific Cases**:
- `rst_example_2`: `Plasma.__init__() got an unexpected keyword argument 'epoch'`
  - **Impact**: Critical - this is the main usage example in docs/source/usage.rst
  - **Issue**: Using deprecated constructor pattern
  - **Fix**: Update to use proper DataFrame-based constructor

**Root Cause**: Documentation examples use outdated API patterns.

**Remediation Strategy**:
- Update constructor calls to match current API
- Review all API usage for deprecation issues

### AttributeError (1 occurrence - 4.8%)
**Primary Issue**: Method calls on objects that don't support them

**Root Cause**: Calling non-existent methods or incorrect object types.

**Remediation Strategy**:
- Verify all method calls exist in current codebase
- Update method names to match actual implementation

## Success Pattern Analysis

### Successful Examples (3 examples - 14.3%)
1. **rst_example_1**: Basic imports (`import solarwindpy as swp`)
   - **Success Factor**: Simple import-only example
   - **Template Pattern**: Use for basic setup examples

2. **rst_example_8**: Installation version check
   - **Success Factor**: Simple attribute access
   - **Template Pattern**: Good for version/info examples

3. **doctest_example_12**: Simple function call
   - **Success Factor**: Self-contained function with defined inputs
   - **Template Pattern**: Best practice for utility function examples

### Common Success Characteristics
- **Self-contained**: No external dependencies or undefined variables
- **Simple operations**: Basic imports, attribute access, function calls
- **Proper setup**: All required variables defined within the example

## Critical Issues by File

### docs/source/usage.rst (7 examples, 1 success - 14.3%)
**Status**: Critical user-facing documentation with severe issues

**Failures**:
- **Example 2** (Lines 34-47): Deprecated `Plasma(epoch=)` constructor - **HIGH PRIORITY**
- **Examples 3-7**: Missing object initialization, undefined variables
- **Impact**: Primary user documentation is largely non-functional

**Required Actions**:
1. Fix Plasma constructor usage immediately
2. Add proper data setup context to all examples
3. Validate all method calls exist in current API

### solarwindpy/core/plasma.py (2 examples, 0 success - 0%)
**Status**: Core API documentation completely broken

**Failures**:
- **All doctest examples**: Syntax errors from descriptive text
- **undefined variables**: Missing `data` parameter setup

**Required Actions**:
1. Convert doctest descriptions to executable code
2. Provide proper DataFrame construction examples
3. Ensure all doctest examples can run independently

### Other Module Doctests (12 examples, 2 successes - 16.7%)
**Status**: Mixed success, mostly syntax issues

**Pattern**: Most failures are doctest syntax issues rather than API problems

**Required Actions**:
1. Systematic doctest syntax cleanup
2. Convert descriptive text to executable examples
3. Add proper variable setup for each example

## Remediation Priority Matrix

### Critical Priority (Fix Immediately)
1. **Plasma constructor in usage.rst** - breaks primary user workflow
2. **Core module doctests** - credibility of main API documentation
3. **Missing object initialization** - prevents examples from running

### High Priority (Fix Next)
4. **Doctest syntax cleanup** - 12 examples need conversion
5. **Undefined variable resolution** - add proper setup context
6. **Method existence validation** - ensure all called methods exist

### Medium Priority (Systematic Cleanup)
7. **Import alias standardization** - consistent swp vs sw usage
8. **Physics validation integration** - add constraint checking
9. **MultiIndex setup patterns** - proper DataFrame construction

## Physics Compliance Assessment

**Status**: Unable to assess physics compliance due to execution failures

**Next Steps**: 
- Physics validation can only be performed after basic execution issues are resolved
- Current 14.3% success rate too low for meaningful physics analysis
- Priority: Fix execution issues first, then apply physics validation

## Success Metrics Impact

**Baseline Established**:
- **Current Success Rate**: 14.3%
- **Target Success Rate**: 95.0% (improvement needed: 80.7%)
- **Import Resolution Rate**: 100.0% (imports work correctly)
- **Physics Compliance Rate**: Cannot assess (insufficient working examples)

**Improvement Strategy**:
1. **Phase 4 Goal**: Achieve 80%+ success rate through API fixes
2. **Phase 5 Goal**: Implement physics compliance validation 
3. **Phase 6 Goal**: Integrate doctest validation into CI/CD

## Next Phase Readiness

**Phase 4 Prerequisites Met**:
- ✅ Complete failure analysis with specific error types
- ✅ Detailed error categorization (Syntax/Name/Type/Attribute)
- ✅ Priority matrix for systematic remediation
- ✅ Success patterns identified for replication

**Phase 4 Action Items Generated**:
1. Fix deprecated Plasma constructor (critical)
2. Add proper variable initialization context (high)
3. Convert doctest syntax to executable code (high)
4. Validate all method calls exist in codebase (medium)
5. Standardize import aliases across all examples (medium)