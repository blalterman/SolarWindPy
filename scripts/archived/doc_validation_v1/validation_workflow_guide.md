# Documentation Validation Workflow Guide

## Overview
This workflow ensures all documentation changes maintain high quality and scientific accuracy through automated and manual validation processes. Follow this guide for consistent, reliable documentation maintenance.

## Pre-Submission Validation

### 1. Local Testing (Required)

#### Quick Validation
```bash
# Test specific files you've changed
python doctest_physics_validator.py solarwindpy/your_module.py
python -m pytest --doctest-modules solarwindpy/your_module.py -v

# For documentation files (.rst, .md)
python validate_examples.py --file docs/source/your_file.rst
```

#### Comprehensive Validation
```bash
# Full codebase validation (use before major submissions)
python doctest_physics_validator.py solarwindpy/ --comprehensive
python -m pytest --doctest-modules solarwindpy/ --tb=short

# Generate detailed report
python doctest_physics_validator.py solarwindpy/ \
  --output-report validation_report.json \
  --text-report validation_report.txt
```

#### Physics-Specific Checks
```bash
# Focus on physics rule validation
python doctest_physics_validator.py solarwindpy/ --physics-only

# Check thermal speed calculations specifically
grep -r "thermal_speed\|w_thermal" solarwindpy/ | \
  xargs python doctest_physics_validator.py --thermal-speed-check
```

### 2. Manual Review Checklist

Before submitting any documentation changes, verify:

#### Code Quality
- [ ] All examples include necessary imports (`import solarwindpy as swp`, etc.)
- [ ] Variables are defined before use (no undefined references)
- [ ] Examples use standardized data setup patterns (fixtures)
- [ ] Code follows PEP 8 style guidelines
- [ ] No syntax errors in any code blocks

#### Physics Compliance
- [ ] Thermal speed calculations follow mw² = 2kT convention
- [ ] Units are consistent (SI internal, display units for interface)
- [ ] Missing data uses NaN (never 0 or -999)
- [ ] Physical quantities are positive where required
- [ ] Results are in realistic ranges for solar wind parameters

#### Structure Compliance
- [ ] MultiIndex DataFrames use (M, C, S) level naming
- [ ] Data access uses .xs() patterns appropriately
- [ ] Time series indices are named 'Epoch'
- [ ] DataFrame structures follow established patterns

#### User Experience
- [ ] Examples are self-contained and educational
- [ ] Code demonstrates realistic usage patterns
- [ ] Examples build understanding incrementally
- [ ] Error handling is appropriate and informative

## CI/CD Automated Validation

### GitHub Actions Workflow

The automated validation runs on every push and pull request:

#### Validation Steps
1. **Environment Setup**: Creates isolated test environment with dependencies
2. **Syntax Validation**: Parses all code blocks for Python syntax errors
3. **Import Resolution**: Verifies all imports resolve in test environment
4. **Execution Testing**: Runs all examples in isolated environments
5. **Physics Validation**: Applies physics rules to all calculations
6. **Performance Monitoring**: Ensures validation completes in <2 minutes

#### Multi-Python Testing
- **Python 3.9**: Baseline compatibility
- **Python 3.10**: Current stable version
- **Python 3.11**: Latest features support

#### Artifact Collection
- **Test Results**: JUnit XML for integration with development tools
- **Physics Reports**: JSON and text reports of validation results  
- **Performance Metrics**: Timing and resource usage data
- **Coverage Reports**: Doctest coverage analysis

### Failure Handling

#### Syntax Errors
```
Error: Invalid Python syntax in example
File: solarwindpy/core/plasma.py, line 45
Issue: Unclosed parenthesis in function call

Fix: Review and correct Python syntax
```

#### Import Errors  
```
Error: Module import failed
File: docs/user_guide.rst, example 3
Issue: 'from solarwindpy.plotting import nonexistent_function'

Fix: Use correct import: 'import solarwindpy.plotting as swpp'
```

#### Runtime Errors
```
Error: Example execution failed
File: solarwindpy/core/ions.py, line 123
Issue: NameError: name 'undefined_variable' is not defined

Fix: Define variable or use fixture: 'data = create_example_plasma_data()'
```

#### Physics Violations
```
Error: Physics rule violation
Type: thermal_speed_hardcoded
Message: Thermal speed should be calculated from temperature using mw² = 2kT

Fix: Use plasma.p1.thermal_speed() or calculate from first principles
```

## Development Workflow Integration

### Feature Development
```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Develop with validation
# Edit code and documentation
python doctest_physics_validator.py changed_file.py

# 3. Test before commit
python doctest_physics_validator.py --quick-check
git add .
git commit -m "feat: your feature description"

# 4. Final validation before push
python doctest_physics_validator.py solarwindpy/ --comprehensive
git push origin feature/your-feature
```

### Documentation Updates
```bash
# 1. Update documentation
# Edit .rst files or docstrings

# 2. Extract and test examples
python validate_examples.py --file docs/your_file.rst --extract-test

# 3. Physics validation
python doctest_physics_validator.py --physics-rules

# 4. Commit with validation
git add docs/
git commit -m "docs: update examples with physics compliance"
```

### Hotfixes
```bash
# 1. Quick validation for urgent fixes
python doctest_physics_validator.py affected_file.py --quick-check

# 2. Targeted testing
python -m pytest --doctest-modules affected_file.py

# 3. Deploy with confidence
git add affected_file.py
git commit -m "fix: urgent documentation correction"
```

## Maintenance Procedures

### Daily Operations

#### Automated Monitoring
```bash
# GitHub Actions automatically run on:
# - Every push to main/master branch
# - Every pull request
# - Weekly scheduled runs (Sundays at 6 AM UTC)

# Manual trigger when needed:
gh workflow run "Doctest Validation" --ref main
```

#### Issue Response
1. **Validation Failures**: Check GitHub Actions logs for detailed error information
2. **User Reports**: Validate specific examples mentioned in user issues
3. **Performance Issues**: Monitor validation execution time and resource usage

### Weekly Maintenance

#### Comprehensive Validation
```bash
# Full codebase scan
python doctest_physics_validator.py solarwindpy/ \
  --comprehensive \
  --output-report weekly_report.json \
  --text-report weekly_report.txt

# Trend analysis
python analyze_validation_trends.py weekly_report.json
```

#### Metrics Review
```bash
# Check validation performance
grep "validation_time" validation_logs/*.json | \
  python calculate_performance_metrics.py

# Physics compliance trends
grep "physics_violations" validation_logs/*.json | \
  python analyze_physics_trends.py
```

### Monthly Review

#### Framework Assessment
1. **Performance Analysis**: Review validation execution times and resource usage
2. **Rule Effectiveness**: Assess physics rule detection rates and false positives
3. **User Feedback**: Collect and analyze contributor experience feedback
4. **Framework Updates**: Plan and implement validation framework improvements

#### Documentation Quality
1. **Coverage Analysis**: Ensure comprehensive example coverage across modules
2. **User Experience**: Assess example clarity and educational value
3. **Scientific Accuracy**: Domain expert review of physics content
4. **Consistency Audit**: Verify pattern consistency across documentation

### Quarterly Assessment

#### Strategic Review
1. **Framework Effectiveness**: Comprehensive audit of validation framework impact
2. **User Impact Analysis**: Measure documentation quality improvements
3. **Performance Benchmarking**: Compare against baseline metrics
4. **Enhancement Planning**: Strategic planning for validation framework growth

#### Process Optimization
1. **Workflow Efficiency**: Streamline validation processes based on usage patterns
2. **Automation Enhancement**: Identify opportunities for increased automation
3. **Integration Improvement**: Enhance integration with development tools
4. **Training Updates**: Update contributor guidelines based on common issues

## Troubleshooting Common Issues

### Validation Framework Issues

#### Slow Validation Performance
```bash
# Check resource usage
python doctest_physics_validator.py --profile solarwindpy/

# Optimize for speed
python doctest_physics_validator.py --quick-check --parallel solarwindpy/

# Skip expensive checks during development
python doctest_physics_validator.py --skip-physics solarwindpy/
```

#### Import Resolution Problems
```bash
# Check environment
python -c "import solarwindpy; print(solarwindpy.__version__)"
pip list | grep -E "(numpy|pandas|matplotlib)"

# Recreate environment
conda env remove -n solarwindpy-dev
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .
```

#### Physics Rule False Positives
```bash
# Review specific rule
python doctest_physics_validator.py --rule thermal_speed --verbose

# Adjust sensitivity
python doctest_physics_validator.py --tolerance 0.05 solarwindpy/

# Report false positive
python report_validation_issue.py --type false_positive --file affected_file.py
```

### Development Integration Issues

#### CI/CD Pipeline Failures
1. **Check GitHub Actions logs**: Review detailed execution logs
2. **Local reproduction**: Run same validation commands locally
3. **Environment differences**: Compare local vs. CI environment
4. **Resource limitations**: Check for memory/time limit issues

#### Performance Degradation
1. **Profile validation time**: Use timing analysis tools
2. **Optimize test patterns**: Reduce redundant validation
3. **Parallel execution**: Enable multi-process validation
4. **Selective validation**: Focus on changed files during development

#### False Negative Detection
1. **Review validation rules**: Ensure comprehensive coverage
2. **Update rule sensitivity**: Adjust detection thresholds
3. **Add missing patterns**: Extend validation to cover new cases
4. **Community feedback**: Gather user reports of missed issues

## Integration with Development Tools

### IDE Integration

#### VS Code
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Documentation",
      "type": "shell",
      "command": "python",
      "args": ["doctest_physics_validator.py", "${file}", "--quick-check"],
      "group": "test"
    }
  ]
}
```

#### PyCharm
```xml
<!-- External Tools configuration -->
<tool name="Doctest Validator"
      program="python"
      parameters="doctest_physics_validator.py $FilePath$ --quick-check"
      workingDirectory="$ProjectFileDir$" />
```

### Git Hooks

#### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get list of modified Python files
PYTHON_FILES=$(git diff --cached --name-only | grep '\.py$')

if [ -n "$PYTHON_FILES" ]; then
    echo "Validating documentation examples..."
    python doctest_physics_validator.py $PYTHON_FILES --quick-check
    
    if [ $? -ne 0 ]; then
        echo "Documentation validation failed. Commit aborted."
        exit 1
    fi
fi

exit 0
```

#### Pre-push Hook
```bash
#!/bin/bash
# .git/hooks/pre-push

echo "Running comprehensive documentation validation..."
python doctest_physics_validator.py solarwindpy/ --comprehensive

if [ $? -ne 0 ]; then
    echo "Comprehensive validation failed. Push aborted."
    echo "Run 'python doctest_physics_validator.py solarwindpy/ --fix' to auto-correct issues."
    exit 1
fi

exit 0
```

## Performance Optimization

### Validation Speed
- **Parallel Processing**: Use `--parallel` flag for multi-file validation
- **Selective Testing**: Use `--changed-only` during development
- **Caching**: Validation results cached for unchanged files
- **Quick Checks**: Use `--quick-check` for rapid feedback

### Resource Management
- **Memory Usage**: Monitor and optimize for large codebases
- **CPU Utilization**: Balance parallelism with system resources
- **I/O Optimization**: Efficient file reading and report generation
- **Network Usage**: Minimize external dependency checks

### Continuous Improvement
- **Performance Profiling**: Regular analysis of validation bottlenecks
- **Algorithm Optimization**: Improve validation algorithm efficiency
- **Tool Integration**: Leverage external tools for better performance
- **User Feedback**: Incorporate contributor suggestions for workflow improvements

---

This workflow guide provides comprehensive procedures for maintaining high-quality documentation through systematic validation. Regular adherence to these processes ensures sustained documentation excellence and scientific accuracy.