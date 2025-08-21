# Phase 2: Execution Environment Setup

## Phase Metadata
- **Status**: 🔄 In Progress
- **Estimated Duration**: 1 hour
- **Actual Duration**: _TBD_
- **Dependencies**: Phase 1 (Discovery & Inventory) completed
- **Git Commit**: <checksum>
- **Branch**: plan/documentation-code-audit

## 🎯 Objective
Establish a robust testing environment and validation infrastructure for systematically executing and verifying all code examples found in the documentation audit.

## 📋 Tasks Checklist
- [ ] **Environment Verification** (10 min)
  - [ ] Verify conda environment: `solarwindpy-20250403`
  - [ ] Confirm SolarWindPy installation: `pip install -e .`
  - [ ] Test basic imports: `import solarwindpy as swp`
  - [ ] Validate test runner: `pytest --version`

- [ ] **Example Extraction Tools** (25 min)
  - [ ] Create RST code block extractor script
  - [ ] Implement docstring example parser
  - [ ] Add syntax validation checker
  - [ ] Test extraction on sample files

- [ ] **Execution Framework** (15 min)
  - [ ] Design isolated execution environment
  - [ ] Create example runner with error capture
  - [ ] Implement output validation framework
  - [ ] Add timeout and resource management

- [ ] **Validation Infrastructure** (10 min)
  - [ ] Set up physics constraint checking
  - [ ] Create MultiIndex structure validator
  - [ ] Implement import resolution verification
  - [ ] Design success/failure reporting system

## 📁 Deliverables
- [ ] **extract_examples.py**: Tool to extract code blocks from RST and docstrings
- [ ] **validate_examples.py**: Framework for executing and validating examples
- [ ] **physics_validator.py**: Physics constraint and rule checking
- [ ] **test_environment_setup.md**: Documentation for testing infrastructure
- [ ] **validation_report_template.json**: Standardized reporting format

## 🔧 Technical Implementation

### RST Code Block Extractor
```python
# extract_examples.py structure
class RSTExtractor:
    def extract_code_blocks(self, rst_file):
        """Extract all code-block:: python directives"""
        pass
    
    def parse_docstring_examples(self, python_file):
        """Extract doctest examples from Python files"""
        pass
    
    def validate_syntax(self, code_string):
        """Check Python syntax without execution"""
        pass
```

### Example Validation Framework
```python
# validate_examples.py structure
class ExampleValidator:
    def __init__(self, physics_validator=None):
        self.physics = physics_validator
        self.results = []
    
    def execute_example(self, code, context=None):
        """Execute code in isolated environment"""
        pass
    
    def validate_physics(self, result):
        """Check outputs against physics constraints"""
        pass
    
    def generate_report(self):
        """Create detailed validation report"""
        pass
```

### Physics Constraint Validator
```python
# physics_validator.py structure
class PhysicsValidator:
    def check_thermal_speed_convention(self, thermal_speed, temperature):
        """Validate mw² = 2kT convention"""
        pass
    
    def validate_units(self, data, expected_units):
        """Check SI unit compliance"""
        pass
    
    def check_missing_data_handling(self, data):
        """Ensure NaN used for missing data (not 0 or -999)"""
        pass
```

## 🔍 Environment Setup Requirements

### Conda Environment Validation
```bash
# Verify environment is active and complete
conda env list | grep solarwindpy-20250403
python -c "import solarwindpy; print(solarwindpy.__version__)"
python -c "import numpy, pandas, matplotlib; print('Dependencies OK')"
```

### Required Dependencies
- **Core**: `solarwindpy` (development installation)
- **Scientific**: `numpy`, `pandas`, `matplotlib`
- **Testing**: `pytest`, `doctest`
- **Parsing**: `docutils`, `sphinx` (for RST processing)
- **Validation**: `ast`, `compile` (syntax checking)

### Testing Infrastructure
```python
# Example test runner structure
def run_validation_suite():
    """Execute complete validation of all examples"""
    extractor = RSTExtractor()
    validator = ExampleValidator(PhysicsValidator())
    
    # Extract all examples from inventory
    examples = extractor.load_from_inventory('docs_audit_inventory.json')
    
    # Validate each example
    for example in examples:
        result = validator.execute_example(example.code)
        validator.validate_physics(result)
    
    # Generate comprehensive report
    return validator.generate_report()
```

## 📊 Success Metrics

### Environment Readiness
- [ ] All required packages importable without errors
- [ ] SolarWindPy core functionality accessible
- [ ] Test framework can execute basic examples
- [ ] Physics validation rules operational

### Tool Functionality
- [ ] RST extractor processes all inventory files correctly
- [ ] Docstring parser handles doctest format properly
- [ ] Example executor provides detailed error capture
- [ ] Physics validator identifies constraint violations

### Validation Framework
- [ ] Isolated execution prevents cross-contamination
- [ ] Timeout handling prevents infinite loops
- [ ] Error reporting captures actionable information
- [ ] Success criteria clearly defined and measurable

## 🔗 Integration Points

### With Existing Infrastructure
- **Physics Rules**: Leverage existing thermal speed and unit conventions
- **MultiIndex Patterns**: Use established data structure validation
- **Testing Framework**: Integrate with current pytest infrastructure
- **CI/CD Hooks**: Prepare for future automated validation

### With Inventory Data
- **Load Example Catalog**: Read from `docs_audit_inventory.json`
- **Priority Processing**: Execute examples by severity classification
- **Issue Tracking**: Map validation results back to inventory issues
- **Progress Monitoring**: Track remediation success rates

## ⚡ Execution Strategy

### Phase 2 Implementation Order
1. **Environment Verification** (10 min)
   - Quick validation of development environment
   - Ensure all dependencies are available
   - Test basic SolarWindPy functionality

2. **Core Tool Development** (25 min)
   - RST code block extraction (highest priority)
   - Docstring example parsing (medium priority)
   - Syntax validation (quick safety check)

3. **Validation Framework** (15 min)
   - Example execution with error capture
   - Physics constraint integration
   - Output validation and reporting

4. **Testing and Validation** (10 min)
   - Test tools on sample examples from inventory
   - Verify error capture and reporting works
   - Prepare for Phase 3 systematic validation

### Risk Mitigation
- **Tool Development**: Start with simple extraction, add complexity incrementally
- **Environment Issues**: Have fallback to basic Python environment if conda issues
- **Physics Validation**: Begin with simple checks, expand based on example complexity
- **Execution Safety**: Implement timeouts and resource limits early

## 📝 Implementation Notes

### Key Design Decisions
1. **Modular Architecture**: Separate extraction, execution, and validation for flexibility
2. **Error Isolation**: Each example runs independently to prevent cascade failures
3. **Comprehensive Logging**: Detailed error capture for efficient debugging
4. **Physics Integration**: Built-in validation of scientific computing conventions

### Expected Challenges
- **Complex Examples**: MultiIndex setup examples may require sophisticated context
- **Import Dependencies**: Some examples may require specific data files or setup
- **Physics Validation**: Balancing strictness with flexibility for edge cases
- **Performance**: 47 examples need reasonable execution time for iterative testing

## ✅ Completion Criteria
- [ ] Testing environment fully operational
- [ ] Example extraction tools working for all file types
- [ ] Validation framework handles success and failure cases
- [ ] Physics constraint checking integrated
- [ ] All tools tested on sample inventory examples
- [ ] Ready to execute Phase 3 systematic validation

## 🔄 Transition to Phase 3
**Preparation for Phase 3: Systematic Validation**
- Testing infrastructure operational
- All extraction and validation tools ready
- Physics constraint checking integrated
- Sample validation runs successful

**Next Phase Prerequisites:**
- Complete example extraction capability
- Robust error capture and reporting
- Physics validation framework operational
- Success metrics clearly defined

---

**📝 User Action Required**: After completing this phase, run:
```bash
git add plans/documentation-code-audit/2-Execution-Environment-Setup.md \
        extract_examples.py validate_examples.py physics_validator.py \
        test_environment_setup.md validation_report_template.json
git commit -m "docs: complete Phase 2 execution environment setup

- Created comprehensive example extraction and validation tools
- Established isolated testing environment with physics validation
- Implemented RST and docstring code block extraction
- Set up validation framework with error capture and reporting
- Ready for Phase 3: Systematic Validation of all 47 examples

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Then create compacted state for session continuity:**
```bash
python .claude/hooks/create-compaction.py \
  --trigger "Phase 2 completion - testing infrastructure ready" \
  --context "Documentation audit validation tools operational"
```