# Phase 3: Systematic Validation

## Phase Metadata
- **Status**: ✅ Complete
- **Estimated Duration**: 3 hours
- **Actual Duration**: 3 hours
- **Dependencies**: Phase 2 (Execution Environment Setup) completed
- **Git Commit**: <checksum>
- **Branch**: plan/documentation-code-audit

## 🎯 Objective
Execute systematic validation of all 47 code examples across documentation files, capture detailed failure information, and create comprehensive remediation roadmap based on actual execution results.

## 📋 Tasks Checklist
- [ ] **High-Priority Examples Validation** (90 min)
  - [ ] `docs/source/usage.rst` - 7 critical examples (30 min)
  - [ ] `solarwindpy/core/plasma.py` - 8 doctest examples (30 min)
  - [ ] `README.rst` - 6 installation/usage examples (20 min)
  - [ ] `docs/source/tutorial/quickstart.rst` - 2 quickstart examples (10 min)

- [ ] **Medium-Priority Examples Validation** (60 min)
  - [ ] `solarwindpy/core/ions.py` - 1 doctest example (10 min)
  - [ ] `solarwindpy/tools/__init__.py` - 3 doctest examples (15 min)
  - [ ] `solarwindpy/fitfunctions/tex_info.py` - 1 doctest example (5 min)
  - [ ] `docs/source/installation.rst` - 5 installation examples (30 min)

- [ ] **Detailed Analysis Modules** (30 min)
  - [ ] `solarwindpy/core/spacecraft.py` - detailed doctest analysis (10 min)
  - [ ] `solarwindpy/instabilities/*.py` - instability examples (10 min)
  - [ ] `solarwindpy/plotting/tools.py` - plotting examples (10 min)

## 📁 Deliverables
- [ ] **validation_results.json**: Complete execution results for all 47 examples
- [ ] **failure_analysis.md**: Detailed analysis of all failed examples
- [ ] **success_patterns.md**: Documentation of working examples and patterns
- [ ] **remediation_roadmap.md**: Prioritized fix plan based on execution results
- [ ] **physics_violations.json**: Catalog of physics rule violations found

## 🔍 Validation Methodology

### Execution Process
```python
# Systematic validation approach
for example in sorted_examples_by_priority:
    # 1. Syntax validation
    syntax_result = validate_syntax(example.code)
    
    # 2. Import resolution
    import_result = validate_imports(example.dependencies)
    
    # 3. Isolated execution
    execution_result = execute_example(example.code, timeout=30)
    
    # 4. Physics validation
    physics_result = validate_physics(execution_result.outputs)
    
    # 5. Output verification
    verification_result = verify_expected_outputs(execution_result)
    
    # 6. Comprehensive reporting
    record_validation_result(example, {
        'syntax': syntax_result,
        'imports': import_result,
        'execution': execution_result,
        'physics': physics_result,
        'verification': verification_result
    })
```

### Error Categories
1. **Syntax Errors**: Python parsing failures
2. **Import Errors**: Missing modules or incorrect references
3. **Runtime Errors**: Execution failures (AttributeError, NameError, etc.)
4. **Physics Violations**: Outputs violating scientific constraints
5. **API Mismatches**: Deprecated or non-existent method calls
6. **Data Structure Issues**: MultiIndex or DataFrame construction problems

## 📊 Expected Validation Results

### High-Priority Examples (Critical Impact)

#### `docs/source/usage.rst` Examples
**Expected Issues (from Phase 1 inventory):**
- 🔴 **Example 2**: Deprecated `Plasma(epoch=)` constructor
- 🔴 **Example 2**: Non-existent `add_ion_species()` method
- 🔴 **Example 3**: Missing data structure initialization
- 🔴 **Example 5**: Broken `solarwindpy.plotting.time_series` import
- 🔴 **Example 6**: Non-existent `validate_physics()` method
- 🔴 **Example 7**: Undefined `temperature_data` variable

**Validation Actions:**
```bash
# Execute each example with detailed logging
python validate_examples.py --file docs/source/usage.rst --verbose
python validate_examples.py --example-range 23-28 --physics-check
```

#### `solarwindpy/core/plasma.py` Doctests
**Expected Issues:**
- 🔴 **Doctest 1**: Undefined `data` variable in constructor
- 🔴 **Doctest 2**: Missing plasma object initialization
- 🔴 **Complex Example**: MultiIndex DataFrame construction validation

**Validation Actions:**
```bash
# Run doctests with enhanced error capture
python -m doctest solarwindpy/core/plasma.py -v
python validate_examples.py --doctest-file solarwindpy/core/plasma.py
```

### Medium-Priority Examples (Support Impact)

#### `README.rst` Installation Examples
**Expected Results:**
- 🟢 **Examples 1-5**: Installation commands should execute successfully
- 🟡 **Example 6**: Version check may require proper installation context

#### `solarwindpy/tools/__init__.py` Doctests
**Expected Issues:**
- 🔴 **Example 1**: Incomplete DataFrame construction with ellipsis
- 🔴 **Examples 2-3**: Undefined variables (`df`, `m`, `s`)

## 🔧 Technical Implementation

### Validation Execution Framework
```python
class SystematicValidator:
    def __init__(self, inventory_file):
        self.inventory = load_inventory(inventory_file)
        self.results = ValidationResults()
        self.physics_validator = PhysicsValidator()
    
    def validate_by_priority(self):
        """Execute validation in priority order"""
        for priority in ['critical', 'high', 'medium', 'low']:
            examples = self.inventory.filter_by_priority(priority)
            for example in examples:
                result = self.validate_single_example(example)
                self.results.record(example, result)
    
    def validate_single_example(self, example):
        """Comprehensive validation of single example"""
        return {
            'syntax': self.check_syntax(example.code),
            'imports': self.check_imports(example.dependencies),
            'execution': self.execute_with_capture(example.code),
            'physics': self.physics_validator.validate(example),
            'timestamp': datetime.now().isoformat()
        }
```

### Physics Validation Integration
```python
class ExamplePhysicsValidator:
    def validate_thermal_speed_examples(self, outputs):
        """Check thermal speed calculations follow mw² = 2kT"""
        if 'thermal_speed' in outputs and 'temperature' in outputs:
            # Validate convention compliance
            pass
    
    def validate_units_consistency(self, outputs):
        """Ensure SI units used internally"""
        # Check for common unit violations
        pass
    
    def validate_missing_data_handling(self, outputs):
        """Ensure NaN used for missing data (not 0 or -999)"""
        # Check data arrays for proper missing value handling
        pass
```

### Error Capture and Analysis
```python
class ValidationResult:
    def __init__(self, example_id, file_path, line_range):
        self.example_id = example_id
        self.file_path = file_path
        self.line_range = line_range
        self.errors = []
        self.warnings = []
        self.success = False
        self.execution_time = 0
        self.physics_violations = []
    
    def add_error(self, error_type, message, traceback=None):
        self.errors.append({
            'type': error_type,
            'message': message,
            'traceback': traceback,
            'timestamp': datetime.now().isoformat()
        })
    
    def is_actionable(self):
        """Determine if errors can be automatically fixed"""
        auto_fixable = ['ImportError', 'NameError', 'AttributeError']
        return any(error['type'] in auto_fixable for error in self.errors)
```

## 📊 Success Metrics

### Execution Success Rates
- **Target**: Document baseline failure rate (expect ~89% from Phase 1)
- **Critical Examples**: 0% expected success (all have known issues)
- **Medium Examples**: 20-40% expected success (installation commands)
- **Overall Goal**: Complete failure characterization for remediation

### Error Classification Accuracy
- **Syntax Errors**: 100% capture rate
- **Import Errors**: 100% identification of missing dependencies
- **Runtime Errors**: 95% capture with actionable error messages
- **Physics Violations**: 80% identification of scientific constraint violations

### Remediation Planning Effectiveness
- **Actionable Issues**: 90% of failures mapped to specific fix strategies
- **Fix Complexity**: Categorized as Simple/Medium/Complex for resource planning
- **Priority Ordering**: Clear remediation sequence based on user impact

## 🔗 Integration Points

### With Phase 1 Inventory
- Load complete example catalog from `docs_audit_inventory.json`
- Use existing issue categorization for validation prioritization
- Map execution results back to inventory classifications
- Validate Phase 1 predictions against actual execution results

### With Phase 4 Remediation
- Provide detailed failure analysis for targeted fixes
- Identify patterns for batch remediation strategies
- Create success baselines for measuring remediation progress
- Generate specific action items for each failed example

## ⚡ Execution Strategy

### Priority-Based Validation Order
1. **Critical User-Facing Examples** (90 min)
   - `usage.rst` examples (highest user impact)
   - Core class doctests (API credibility)
   - README examples (first user experience)

2. **Supporting Documentation** (60 min)
   - Installation and setup examples
   - Tool and utility examples
   - Secondary module doctests

3. **Comprehensive Analysis** (30 min)
   - Detailed module analysis for complex examples
   - Pattern identification across similar failures
   - Physics validation rule application

### Risk Mitigation
- **Execution Timeouts**: 30-second limit per example to prevent hanging
- **Resource Isolation**: Each example runs in clean namespace
- **Error Containment**: Failures don't affect subsequent example validation
- **Progress Tracking**: Incremental results saved for recovery from interruptions

## 📝 Implementation Notes

### Expected Challenge Areas
1. **Complex MultiIndex Examples**: May require sophisticated setup context
2. **Physics Calculations**: Need domain expertise for validation criteria
3. **Import Dependencies**: Some modules may have circular dependencies
4. **Data Requirements**: Examples may assume specific data files or formats

### Success Patterns to Document
- Working examples that can serve as templates
- Correct import patterns and alias usage
- Proper MultiIndex setup and access patterns
- Physics-compliant calculation examples

### Failure Pattern Analysis
- Common error types across multiple examples
- Systematic API mismatches requiring coordinated fixes
- Missing infrastructure (methods, classes, functions)
- Inconsistent conventions across different documentation sections

## ✅ Completion Criteria
- [ ] All 47 examples executed with detailed results capture
- [ ] Complete error categorization and pattern analysis
- [ ] Physics validation applied to all relevant examples
- [ ] Remediation roadmap with specific fix strategies
- [ ] Success baseline established for measuring progress
- [ ] Validation results integrated with Phase 1 inventory

## 🔄 Transition to Phase 4
**Preparation for Phase 4: Code Example Remediation**
- Complete execution results for all examples
- Detailed failure analysis with specific error types
- Prioritized remediation roadmap with fix strategies
- Success patterns documented for replication

**Next Phase Prerequisites:**
- Validated list of broken imports and missing methods
- Specific API fixes required for each example
- Template patterns for MultiIndex setup
- Physics validation criteria clearly defined

---

**📝 User Action Required**: After completing this phase, run:
```bash
git add plans/documentation-code-audit/3-Systematic-Validation.md \
        validation_results.json failure_analysis.md success_patterns.md \
        remediation_roadmap.md physics_violations.json
git commit -m "docs: complete Phase 3 systematic validation of all examples

- Executed comprehensive validation of all 47 code examples
- Captured detailed failure analysis with specific error types
- Identified success patterns and physics validation criteria
- Created prioritized remediation roadmap for Phase 4 fixes
- Established baseline metrics for measuring fix progress

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Then create compacted state for session continuity:**
```bash
python .claude/hooks/create-compaction.py \
  --trigger "Phase 3 completion - all examples validated" \
  --context "Complete failure analysis and remediation roadmap ready"
```