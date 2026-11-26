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

### Environment

1. Clone the repository and build the conda environment. Every dependency comes from
   conda-forge; pip only registers your checkout:

   ```bash
   git clone https://github.com/blalterman/SolarWindPy.git
   cd SolarWindPy
   conda env create -f solarwindpy.yml
   conda run -n solarwindpy pip install -e . --no-deps --no-build-isolation
   ```

   Without conda, `pip install -e ".[dev]"` installs SolarWindPy plus all dev tools from
   `pyproject.toml`.

2. Run every Python tool inside the `solarwindpy` env: `conda run -n solarwindpy <command>`,
   or activate the env first. Outside it, `python` is the base install and `pytest` and
   `lint-imports` are not on PATH.

3. Install the git hooks once per clone, and again after rebuilding the env (each hook names
   the env's Python by its version, so a rebuild onto a new Python leaves the hooks pointing
   at nothing):

   ```bash
   conda run -n solarwindpy pre-commit install --hook-type pre-commit --hook-type commit-msg
   ```

   Each commit then runs ruff, doc8, the commit-message check, and the full test suite with a
   coverage floor (`scripts/pre_commit_tests.sh`). The floor is a ratchet below measured
   coverage, not a target; raise it as coverage rises.

A stale env produces failures that look like code bugs. Before debugging a surprising
failure, check that the env imports your checkout and a pandas inside the `pyproject.toml`
range:

```bash
conda run -n solarwindpy python -c "import solarwindpy, pandas; print(solarwindpy.__file__, pandas.__version__)"
```

The editable install maps `solarwindpy` to one checkout's `src/`. `pytest` (and so the
commit hook) puts this checkout's `src/` first through `pythonpath` in `pyproject.toml`, but
`python -c` and `lint-imports` do not: in another git worktree, prefix those with
`PYTHONPATH=$PWD/src`.

### Checks

- Full suite: `conda run -n solarwindpy pytest -q` (about one minute).
- One file: `conda run -n solarwindpy pytest -q tests/core/test_plasma.py`
- Network and slow tests are skipped unless you pass `--run-drift` or set `SWP_RUN_DRIFT=1`.
- Import layering: `conda run -n solarwindpy lint-imports`
- Format and lint at the versions CI pins:
  `conda run -n solarwindpy pre-commit run ruff-check --files <paths>` and
  `conda run -n solarwindpy pre-commit run ruff-format --files <paths>`.
- Doctests: `conda run -n solarwindpy pytest --doctest-modules src/solarwindpy -q`
- Docs examples, which the suite and the source doctests do not run:
  `conda run -n solarwindpy pytest --doctest-glob='*.rst' docs/source -q` and
  `conda run -n solarwindpy pytest -p no:doctest -q README.rst docs/source/tutorial/quickstart.rst docs/source/installation.rst`.
- Documentation: `doc8 README.rst docs`, then `cd docs && make html`.

## Data model

- Columns are a three-level MultiIndex named `M` (measurement), `C` (component), `S`
  (species). An empty string means no component or no species.
- Select columns with `.xs()`, which shares the parent's data instead of copying it; the
  package relies on this to keep memory down. Load and compute paths do not call
  `.copy(deep=True)`. Under pandas 3 copy-on-write, writing to an `.xs()` result does not
  change the parent.

## Conventions

- Format with `ruff format` and lint with `ruff check` (which includes the pydocstyle rules);
  docstrings follow the NumPy style guide.
- Extract shared logic at the second copy.
- Cite scientific sources in docstrings: DOI or arXiv, plus the equation number when you
  implement a specific published result.
- External code: record its URL, license, and modifications in a comment. Copy only MIT, BSD,
  Apache 2.0, or public-domain code. When provenance or license is unclear, reimplement.
- Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`fix(core):`, `feat(plotting):`, `chore:`); the commit-msg hook rejects others.
- A public name, a column label, or a physical result changes only with the maintainer's
  agreement: propose it in an issue first.
- Tests follow `docs/TEST_PATTERNS.md`. Read it before writing or reviewing a test.
- Changes are test-first. Before a stage, list the tests it touches and classify each as guard
  (passes unchanged before and after), update, delete, or fragile (a pinned number with no
  source; rewrite it as a relation or a cited reference value). Land the target tests first as
  `pytest.mark.xfail(strict=True)`, then the code change that removes the marker.
- Releases follow `docs/RELEASING.md`.

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

`pyproject.toml` is the only dependency declaration; there are no lockfiles.
The conda environment file `solarwindpy.yml` is generated from it: after
editing it, run `pyproject2conda project -w force` and commit both files
(`tests/test_conda_env.py` fails until they agree). Then reinstall with
`pip install -e ".[dev]"`, or update the conda env, and run the suite.

### Dependency Guidelines

- **Runtime dependencies**: Keep minimal - only packages users need to import solarwindpy
- **Optional dependencies**: Group by purpose (`test`, `docs`, `dev`)
- **Version constraints**: Use lower bounds for compatibility, upper bounds for breaking changes
- **NumPy 2**: Ensure all dependencies support NumPy >=2.0,<3.0

### Dependency support

SolarWindPy follows [PHEP 3](https://github.com/heliophysicsPy/standards/blob/main/pheps/phep-0003.md):
it supports Python versions released in the last 36 months and core Scientific
Python packages released in the last 24 months. Three floors deliberately
deviate from it:

- **SciPy >=1.16**: the package uses SciPy's CODATA 2022 physical constants.
- **pandas >=3**: the code uses pandas-3-only API. pandas 2.3 leaves the PHEP 3
  window in mid-2027, which ends this deviation.
- **matplotlib >=3.11**: from 3.11, contour plots raise on an unknown keyword
  instead of ignoring it. Ends on 2026-12-14, when matplotlib 3.10 leaves the
  PHEP 3 window.

Otherwise each floor is the oldest version the test suite passes on. CI checks
both: `.github/workflows/dependencies.yml` runs the PHEP 3 compliance check, with
the deviations above as its only exceptions, and runs the suite on the lowest
version of each dependency that `pyproject.toml` allows.
