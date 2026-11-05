# Contributing

Thank you for considering contributing to SolarWindPy.

Everyone who takes part in SolarWindPy is expected to follow the
[Code of Conduct](https://github.com/blalterman/SolarWindPy/blob/master/CODE_OF_CONDUCT.md) (Contributor Covenant 2.1). Report
concerns to [blaltermanphd@gmail.com](mailto:blaltermanphd@gmail.com).

## When a contribution is not accepted

A pull request is not merged when:

- it is outside SolarWindPy's scope, *in situ* solar wind data analysis;
- its CI checks fail (tests, ruff, import layering, docs built with warnings
  as errors);
- it changes a public name, a column label, or a physical result without the
  maintainer's agreement. Open an issue to propose these first;
- it adds behavior without tests, or tests that cannot fail;
- it includes code under a license other than MIT, BSD, Apache 2.0, or public
  domain, or code whose provenance is unclear;
- it adds a dependency without a stated need.

A declined contribution can be revised and resubmitted.

## Development workflow

1. **Set up development environment**:

   ```bash
   git clone https://github.com/blalterman/SolarWindPy.git
   cd SolarWindPy
   pip install -e ".[dev]"  # SolarWindPy plus all dev tools, from pyproject.toml
   ```

   **Alternative (Conda environment)**:

   ```bash
   conda env create -f solarwindpy.yml
   conda activate solarwindpy
   pip install -e ".[dev]"
   ```

2. Format code with `ruff format` and lint with `ruff check` (includes the pydocstyle rules).
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
   pytest --doctest-modules src/solarwindpy -q
   pytest --doctest-glob='*.rst' docs/source -q
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

### Documentation Contribution Workflow

**Simple Three-Step Process:**
1. **Write Example**: Create clear, executable documentation examples
2. **Test Locally**: Run validation to ensure examples work
3. **Submit PR**: GitHub Actions will run essential validation checks

**Local Testing Commands:**
```bash
# Docstring examples in the package
pytest --doctest-modules src/solarwindpy -q

# Examples in the reStructuredText documentation
pytest --doctest-glob='*.rst' docs/source -q
```

**Troubleshooting Common Issues:**
- **Import errors**: Ensure `pip install -e ".[dev]"` was run in the development environment
- **Physics calculation failures**: Check units and verify against known results
- **Timeout issues**: Simplify examples or split into smaller components
- **Package import issues**: Use relative imports within solarwindpy modules

### Validation Framework Usage

**Framework Design Philosophy:**
- **Proportional complexity**: Tools match the package's scope
- **Essential focus**: Physics correctness over comprehensive metrics
- **Sustainable maintenance**: Appropriate for research package team capacity
- **User-friendly**: Simple workflow for researchers and contributors

**Local vs. CI Validation:**
- **Local validation**: The two commands under "Local Testing Commands" above
- **CI validation**: Automated essential checks - runs on all pull requests

## Dependency Management

SolarWindPy uses `pyproject.toml` as the single source of truth for dependencies.

### Adding or Updating Dependencies

**Runtime dependencies** (required by users):
```toml
# pyproject.toml
[project]
dependencies = [
  "somepackage>=X.Y",
]
```

**Development tools**:
```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
  "sometool>=X.Y",
]
```

Set a floor to the oldest version the test suite actually runs on.

`pyproject.toml` is the only dependency declaration; there are no lockfiles
to regenerate. After editing it, reinstall with `pip install -e ".[dev]"` and
run the suite.

### Dependency Guidelines

- **Runtime dependencies**: Keep minimal - only packages users need to import solarwindpy
- **Optional dependencies**: Group by purpose (`test`, `docs`, `dev`)
- **Version constraints**: Use lower bounds for compatibility, upper bounds for breaking changes
- **NumPy 2**: Ensure all dependencies support NumPy >=2.0,<3.0

