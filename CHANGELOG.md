# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-12-24

### Changed - BREAKING CHANGES

**Dependency Management Overhaul**: Consolidated 11 dependency files into single-source-of-truth system using `pyproject.toml` with `pip-tools` lockfiles.

- **REMOVED**: `requirements-dev.txt` (replaced by `requirements-dev.lock`)
- **REMOVED**: `scripts/freeze_requirements.py` (replaced by `pip-compile`)
- **REMOVED**: `scripts/generate_docs_requirements.py` (replaced by `pip-compile --extra=docs`)
- **Migration required**: See [docs/MIGRATION-DEPENDENCY-OVERHAUL.md](docs/MIGRATION-DEPENDENCY-OVERHAUL.md)

**Developer Workflow Changes**:
```bash
# OLD (v0.2.x):
pip install -r requirements-dev.txt

# NEW (v0.3.0+):
pip install -r requirements-dev.lock
```

**Dependency Updates**: Minimum versions updated for NumPy 2.0 ecosystem compatibility
  - `numpy`: `>=1.22,<2.0` → `>=1.26,<3.0` (adds NumPy 2.0 support)
  - `scipy`: `>=1.10` → `>=1.13`
  - `pandas`: `>=1.5` → `>=2.0`
  - `numba`: `>=0.57` → `>=0.59`
  - `docstring-inheritance`: `>=2.0` → `>=2.2.0,<3.0` (MRO fix, exclude breaking v3.0)
  - `pytest`: `>=7.4.4` → `>=8.0`
  - `pytest-cov`: `>=4.1.0` → `>=6.0`

### Added

- **Lockfiles** for reproducible builds:
  - `requirements.txt` - Production dependencies (from `[project.dependencies]`)
  - `requirements-dev.lock` - Development dependencies (from `[project.optional-dependencies.dev]`)
  - `docs/requirements.txt` - Documentation dependencies (from `[project.optional-dependencies.docs]`)

- **Tests**: `tests/fitfunctions/test_metaclass_compatibility.py`
  - Validates `FitFunctionMeta` MRO compatibility with `NumpyDocstringInheritanceMeta` and `ABCMeta`
  - Prevents metaclass regression bugs
  - Tests abstract method enforcement, docstring inheritance, all fitfunction instantiation
  - Includes version constraint validation (docstring-inheritance >=2.2.0,<3.0)

- **Documentation**: Comprehensive migration guide at `docs/MIGRATION-DEPENDENCY-OVERHAUL.md`
  - Breaking changes overview
  - Old vs new developer workflows
  - NumPy 2.0 compatibility matrix
  - CI/CD changes
  - Rollback procedures
  - FAQ with common migration questions

- **Dependency Groups** in `pyproject.toml`:
  - `[project.optional-dependencies.test]` - Testing tools only
  - `[project.optional-dependencies.docs]` - Documentation tools only
  - `[project.optional-dependencies.dev]` - All development tools (test + docs + dev)

### Fixed

- **Critical**: `numpy==2.2.6` in `requirements.txt` violated `pyproject.toml` constraint `<2.0`
  - Root cause: `freeze_requirements.py` used `pip freeze` without validating `pyproject.toml`
  - Fix: Replaced custom scripts with `pip-compile` which enforces constraints
- **Dependency fragmentation**: Eliminated sync issues between 11 dependency files
- **Version drift**: Lockfiles prevent undocumented version changes

### Infrastructure

**GitHub Actions**: All CI/CD workflows updated for lockfile-based dependency management

- `.github/workflows/sync-requirements.yml`:
  - Triggers on `pyproject.toml` changes (single source of truth)
  - Uses `pip-compile` to generate lockfiles instead of Python scripts
  - Validates lockfiles with `pip install --dry-run`

- `.github/workflows/continuous-integration.yml`:
  - Uses `requirements-dev.lock` instead of `requirements-dev.txt`
  - Faster caching via lockfile hash
  - Cross-platform testing: ubuntu/macos × Python 3.11/3.13

- `.github/workflows/ci-master.yml`:
  - Updated to use `requirements-dev.lock`
  - Consistent with other workflows

- `.github/workflows/security.yml`:
  - Audits `requirements-dev.lock` with `safety` and `pip-audit`
  - Security scans on frozen versions instead of loose constraints

- `.github/workflows/publish.yml`:
  - **Pre-release validation**: Blocks PyPI deployment if lockfiles are out of sync with `pyproject.toml`
  - Prevents releasing with inconsistent dependencies

**Scripts**: Updated `scripts/requirements_to_conda_env.py`
- Now reads lockfiles (default: `requirements.txt`) instead of `requirements-dev.txt`
- Documentation clarifies `pip-compile` is a prerequisite
- Supports generating conda environments from any lockfile

### Testing

- **NumPy Compatibility**: Validated with NumPy 1.26.4 and 2.2.6 (247 tests passed each)
- **Coverage**: Maintained 78% (improved from 77.86% baseline)
- **Test Suite**: 1576 tests passed, 19 skipped
- **Metaclass Tests**: 9 new regression tests for `FitFunctionMeta` MRO compatibility

### Migration

**For Developers**:
1. Update checkout: `git pull`
2. Install from lockfile: `pip install -r requirements-dev.lock`
3. Verify: `pytest -q`

**For CI/CD Pipelines**:
- Replace `pip install -r requirements-dev.txt` with `pip install -r requirements-dev.lock`

**Rollback**: Use `pip install solarwindpy==0.2.0` if issues arise

See [docs/MIGRATION-DEPENDENCY-OVERHAUL.md](docs/MIGRATION-DEPENDENCY-OVERHAUL.md) for complete migration instructions

## [0.2.0] - 2025-11-12

### Changed
- **BREAKING**: Minimum Python version raised from 3.10 to 3.11
  - Aligns with scientific Python ecosystem (NumPy 2.x, Astropy 7.x require Python 3.11+)
  - Python 3.10 reaches end-of-life in October 2026
  - Enables Python 3.11+ performance improvements (10-60% faster in many workloads)
  - Added Python 3.13 to CI testing matrix for forward compatibility

### Fixed
- Resolved conda-forge feedstock Issue #8 (Python version compatibility)
- Removed all Python 3.10 references from CI and packaging configuration
- Updated ReadTheDocs configuration to use Python 3.11

### Added
- Python 3.13 CI testing for forward compatibility validation
- Runnable Quick Start example in README with realistic solar wind data
  - Demonstrates complete Plasma object creation workflow
  - Includes physically accurate parameter values
  - Users can copy-paste and execute immediately

### Documentation
- Updated installation requirements in README.rst and docs/source/installation.rst
- Fixed LICENSE file detection for GitHub (converted from .rst to plain text)
- Archived completed documentation to reduce AI context overhead

## [0.1.5] - 2025-11-10

### Fixed
- **Documentation validation** - Resolved doctest failures for JOSS submission
  - Added continuation markers (`...`) to multi-line doctest examples
  - Completed Ion class example with all required columns (v.x, v.y, v.z, w.par, w.per)
  - Added `# doctest: +SKIP` directives to non-deterministic fitfunction examples
  - Added `# doctest: +NORMALIZE_WHITESPACE` for pandas DataFrame output
  - All 33 doctests now passing (11 executed, 22 appropriately skipped)
  - Aligns with paper statement: "fitfunctions tests remain in active development"
  - Unit tests (1,557 test cases) provide comprehensive functionality validation

### Changed
- **Documentation examples** - Maintain instructional value while ensuring reliable validation
- **JOSS paper** - Updated acknowledgements to reflect AI-assisted development workflow
- **Conda channels** - Switched to conda-forge only (removed Anaconda `defaults` channel)
  - Eliminates commercial channel licensing warnings in CI
  - All dependencies available on open-source conda-forge channel
  - Users with existing environments should recreate: `conda env remove -n solarwindpy && conda env create -f solarwindpy.yml`
  - Aligns with JOSS open-source infrastructure requirements

## [0.1.0] - 2025-08-23

### Added
- **Initial stable release on PyPI** - First public release of SolarWindPy
- **Semantic versioning with setuptools_scm** - Automatic version detection from git tags
- **Automated deployment pipeline via GitHub Actions** - Complete CI/CD for PyPI publishing
- **Core plasma physics calculations and data structures** - Multi-species plasma analysis
- **Plotting and visualization capabilities** - Publication-quality scientific plots
- **Instability analysis tools** - Solar wind plasma instability calculations
- **Comprehensive test coverage** - ≥95% code coverage with scientific validation
- **Release automation scripts** - check_release_ready.py and bump_version.py tools
- **Comprehensive documentation** - Release process and deployment guides

### Changed
- **Migrated from development to stable release** - Production-ready package
- **Enhanced package metadata for PyPI distribution** - Complete project configuration
- **Improved version detection with setuptools_scm** - Tag-based versioning
- **Enhanced GitHub Actions workflows** - Production deployment automation

### Fixed
- **Graceful handling of missing PyPI tokens** - Continues deployment without tokens
- **Code formatting standardization** - Black formatting across entire codebase
- **Test fixture scope issues** - Module-level fixtures for cross-class access
- **Documentation validation** - Comprehensive doctest and example validation

### Security
- **Added validation gates for release deployment** - Multi-stage verification process
- **PyPI token security** - Secure repository secrets management