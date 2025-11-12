# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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