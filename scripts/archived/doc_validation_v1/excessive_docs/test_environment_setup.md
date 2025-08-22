# Test Environment Setup for Documentation Code Audit

## Overview

This document describes the testing infrastructure established for systematically validating all code examples in the SolarWindPy documentation.

## Environment Requirements

### Python Environment
- **Python Version**: 3.9+ (compatible with SolarWindPy requirements)
- **SolarWindPy**: Development installation (`pip install -e .`)
- **Core Dependencies**: numpy, pandas, matplotlib
- **Testing Tools**: pytest, doctest, ast (built-in)

### Environment Verification Commands

```bash
# Check SolarWindPy installation and version
python -c "import solarwindpy as swp; print(f'SolarWindPy version: {swp.__version__}')"

# Verify core dependencies
python -c "import numpy, pandas, matplotlib; print('Dependencies OK')"

# Test basic SolarWindPy functionality
python -c "import solarwindpy as swp; print('Core imports working')"

# Check testing frameworks
python -c "import pytest, doctest; print('Testing frameworks available')"
```

## Testing Infrastructure Components

### 1. Example Extraction (`extract_examples.py`)

**Purpose**: Extract all code examples from documentation files
**Features**:
- RST code-block parsing with regex pattern matching
- Python docstring doctest extraction
- Syntax validation without execution
- Import dependency analysis
- JSON inventory generation

**Usage**:
```bash
python extract_examples.py
# Generates: example_extraction_results.json
```

### 2. Example Validation (`validate_examples.py`)

**Purpose**: Execute examples in isolated environments with error capture
**Features**:
- Isolated execution with timeout protection (30s default)
- Stdout/stderr capture
- Import resolution validation
- Comprehensive error reporting
- Non-interactive matplotlib backend for CI compatibility

**Usage**:
```bash
python validate_examples.py
# Reads: docs_audit_inventory.json
# Generates: validation_results.json
```

### 3. Physics Validation (`physics_validator.py`)

**Purpose**: Validate outputs against physics rules and conventions
**Features**:
- Thermal speed convention validation (mw² = 2kT)
- Units consistency checking (SI internal, display external)
- Missing data validation (NaN vs fill values)
- MultiIndex structure compliance
- Physics constant definitions

**Usage**:
```bash
# Integrated into validate_examples.py
# Or standalone testing:
python physics_validator.py
```

## Validation Workflow

### Phase 2 Execution Steps

1. **Environment Verification** ✅
   ```bash
   # Verify SolarWindPy installation
   python -c "import solarwindpy as swp; print('OK')"
   ```

2. **Example Extraction** ✅ 
   ```bash
   # Extract all examples from documentation
   python extract_examples.py
   ```

3. **Systematic Validation** (Phase 3)
   ```bash
   # Execute all examples with physics validation
   python validate_examples.py
   ```

4. **Report Generation** (Phase 3)
   ```bash
   # Comprehensive validation report created automatically
   # Output: validation_results.json
   ```

## Error Handling and Safety

### Execution Safety Features
- **Timeout Protection**: 30-second limit per example prevents hanging
- **Isolated Namespaces**: Each example runs in clean environment
- **Error Containment**: Failures don't affect subsequent examples
- **Resource Limits**: Memory and CPU usage monitored
- **Non-Interactive Backend**: matplotlib.use('Agg') for CI compatibility

### Error Categories Captured
1. **SyntaxError**: Python parsing failures
2. **ImportError**: Missing modules or incorrect references  
3. **NameError**: Undefined variables
4. **AttributeError**: Non-existent methods or attributes
5. **TimeoutError**: Execution exceeds time limit
6. **PhysicsViolation**: Outputs violate scientific constraints

## Validation Metrics

### Success Criteria
- **Syntax Validation**: 100% of examples must parse without errors
- **Import Resolution**: All dependencies must be available
- **Execution Success**: Target >95% successful execution rate
- **Physics Compliance**: 100% of relevant examples follow physics rules
- **Performance**: Complete validation in <2 minutes total

### Expected Results (Phase 1 Baseline)
- **Total Examples**: 47 across 13 files
- **Expected Success Rate**: ~11% (based on Phase 1 inventory)
- **Critical Issues**: 8 (deprecated APIs, missing methods)
- **High Impact Issues**: 15 (missing imports, undefined variables)

## Integration Points

### With Phase 1 Inventory
- Loads example catalog from `docs_audit_inventory.json`
- Maps validation results back to inventory classifications
- Validates Phase 1 predictions against actual execution

### With Phase 3 Systematic Validation
- Provides execution framework for comprehensive testing
- Captures detailed failure analysis for remediation planning
- Establishes baseline metrics for measuring improvement

### With CI/CD Pipeline (Phase 6)
- Framework designed for automated integration
- JSON output format compatible with GitHub Actions
- Performance optimized for continuous validation

## File Outputs

### Generated Files
- `example_extraction_results.json`: Alternative extraction results
- `validation_results.json`: Comprehensive validation report
- `test_environment_setup.md`: This documentation file

### Report Structure
```json
{
  "validation_timestamp": "2025-08-21T06:00:00Z",
  "summary": {
    "total_examples": 47,
    "successful_executions": 5,
    "success_rate": 10.6,
    "import_failures": 15,
    "common_error_types": {
      "AttributeError": 12,
      "NameError": 8,
      "ImportError": 6
    }
  },
  "detailed_results": [...]
}
```

## Troubleshooting

### Common Issues

1. **Import Errors for SolarWindPy Modules**
   ```bash
   # Solution: Ensure development installation
   pip install -e .
   ```

2. **Matplotlib Backend Issues**
   ```python
   # Already handled in validate_examples.py
   import matplotlib
   matplotlib.use('Agg')  # Non-interactive backend
   ```

3. **Memory Issues with Large Examples**
   ```python
   # Timeout and namespace isolation prevent this
   # Adjust timeout if needed: ExampleValidator(timeout=60.0)
   ```

4. **Physics Validation False Positives**
   ```python
   # Adjust tolerance in physics validator
   validator = PhysicsValidator(tolerance=0.10)  # 10% tolerance
   ```

## Next Steps

After Phase 2 completion, the infrastructure will be ready for:

1. **Phase 3**: Systematic validation of all 47 examples
2. **Phase 4**: Targeted remediation based on validation results
3. **Phase 5**: Physics compliance validation and enforcement
4. **Phase 6**: Integration into CI/CD pipeline for automated testing

The testing infrastructure provides a solid foundation for comprehensive documentation quality assurance and ongoing maintenance.