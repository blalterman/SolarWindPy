# Contributing

Thank you for considering contributing to SolarWindPy.

## Development workflow

1. Create a conda environment and install dependencies:

   ```bash
   conda env create -f solarwindpy.yml
   conda activate solarwindpy
   pip install -e .
   ```

   Alternatively, create a virtual environment with pip:

   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

2. Format code with `black` and lint with `flake8` (includes `flake8-docstrings`).
3. Ensure all docstrings follow the NumPy style guide.
4. Lint documentation with `doc8` and build docs:

   ```bash
   doc8 README.rst docs
   cd docs && make html
   ```

5. Run the test suite:

   ```bash
   pytest -q
   ```

6. Validate documentation examples (when adding new documentation):

   ```bash
   # For essential validation (recommended for most changes)
   python scripts/simple_doc_validation/doctest_runner.py solarwindpy/ --targeted --verbose
   
   # For full validation (when making extensive documentation changes)
   python scripts/simple_doc_validation/doctest_runner.py solarwindpy/ --verbose
   ```

## Documentation Guidelines

### Documentation Requirements

**Minimal Requirements for New Features:**
- Include at least one working code example for core functionality
- Ensure examples can execute without errors
- Use standard SolarWindPy imports and conventions
- Keep examples focused and concise (appropriate for scientific package)

**When Documentation Validation is Required:**
- **Required**: Adding new physics functionality to `core/` modules
- **Required**: Adding new scientific calculations to `instabilities/` module  
- **Recommended**: Adding new plotting or fitting examples
- **Optional**: Updating utility functions or minor enhancements

**Validation Complexity Guidelines:**
- Focus on physics correctness over comprehensive coverage
- Examples should demonstrate scientific accuracy
- Avoid over-engineering validation for simple utility functions
- Target 47 documentation examples appropriately (not enterprise-scale 1000+)

### Documentation Contribution Workflow

**Simple Three-Step Process:**
1. **Write Example**: Create clear, executable documentation examples
2. **Test Locally**: Run validation to ensure examples work
3. **Submit PR**: GitHub Actions will run essential validation checks

**Local Testing Commands:**
```bash
# Quick validation of critical modules only
python scripts/simple_doc_validation/doctest_runner.py solarwindpy/ --targeted

# Check essential imports and framework status
python scripts/simple_doc_validation/validation_utils.py --check-imports --framework-status

# View validation priorities and target modules
python scripts/simple_doc_validation/validation_utils.py --validation-priorities --targeted-modules
```

**Troubleshooting Common Issues:**
- **Import errors**: Ensure `pip install -e .` was run in development environment
- **Physics calculation failures**: Check units and verify against known results
- **Timeout issues**: Simplify examples or split into smaller components
- **Package import issues**: Use relative imports within solarwindpy modules

### Validation Framework Usage

**Framework Design Philosophy:**
- **Proportional complexity**: Tools match package scope (47 examples, not enterprise-scale)
- **Essential focus**: Physics correctness over comprehensive metrics
- **Sustainable maintenance**: Appropriate for research package team capacity
- **User-friendly**: Simple workflow for researchers and contributors

**Full vs. Minimal Validation:**
- **Targeted validation** (`--targeted`): Focuses on core physics modules - use for most contributions
- **Full validation**: Tests all modules - use when making extensive changes
- **CI validation**: Automated essential checks - runs on all pull requests

## Documentation reviews

Documentation should be reviewed quarterly. Open an issue using the
"Documentation Review" template under `.github/ISSUE_TEMPLATE` to track the
review. 

**Sustainable Review Process:**
- Focus on scientific accuracy of physics examples
- Verify core functionality examples still work
- Update validation approach if package scope changes significantly
- Annual assessment of validation framework appropriateness for current needs

## Validation Framework Maintenance

### Framework Sustainability Metrics
The validation framework has been right-sized for SolarWindPy's scope:
- **Framework size**: 570 lines (83% reduction from over-engineered 3,349 lines)
- **Execution time**: <5 minutes for full validation
- **Maintenance complexity**: Low (appropriate for research package team)
- **Example coverage**: 47 documentation examples (proportional tooling)

### Annual Framework Assessment
Review framework appropriateness annually:
1. **Scope verification**: Are we still at ~47 examples?
2. **Performance check**: Is validation completing in <5 minutes?
3. **Maintenance burden**: Can current team sustain framework complexity?
4. **Enhancement justification**: Are proposed additions necessary for current scope?

### Troubleshooting Validation Issues
**Common issues and solutions:**
- **Import errors**: Ensure `pip install -e .` in development environment
- **Physics calculation failures**: Check units and verify against known results
- **Timeout issues**: Use `--targeted` flag for faster critical module validation
- **Matplotlib compatibility**: Some doctest failures may be due to version differences (acceptable)

### Framework Enhancement Guidelines
Before adding complexity to validation framework:
1. **Justification**: Document why enhancement is needed for 47 examples
2. **Proportionality**: Will enhancement maintain appropriate complexity level?
3. **Sustainability**: Can research team maintain enhanced framework?
4. **Alternative**: Could issue be addressed through simpler means?

**Enhancement approval criteria:**
- Addresses actual problem with current 47 examples
- Maintains <5 minute execution time
- Complexity remains appropriate for research package
- Team can sustain maintenance burden
