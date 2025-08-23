# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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