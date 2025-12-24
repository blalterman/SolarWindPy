# Dependency Management Migration Guide (v0.2.x → v0.3.0)

**Migration Type**: Breaking Changes
**Release**: v0.3.0
**Date**: 2025-12-23

---

## Executive Summary

SolarWindPy v0.3.0 consolidates dependency management from 11 fragmented files into a single-source-of-truth system using `pyproject.toml` with `pip-tools` lockfiles. This migration fixes critical version conflicts, adds NumPy 2.0 support, and modernizes the development workflow.

**Critical Breaking Changes**:
- ❌ **Removed**: `requirements-dev.txt` (replaced by `requirements-dev.lock`)
- ❌ **Removed**: `scripts/freeze_requirements.py` (replaced by `pip-compile`)
- ❌ **Removed**: `scripts/generate_docs_requirements.py` (replaced by `pip-compile --extra=docs`)
- ⚠️ **NumPy constraint**: `<2.0` → `<3.0` (adds NumPy 2.0 support)

---

## What Changed and Why

### Problem: Dependency Fragmentation

**Before v0.3.0** (11 files):
```
pyproject.toml           # Loose constraints (e.g., numpy>=1.22,<2.0)
requirements-dev.txt     # Manual developer dependencies
requirements.txt         # Auto-generated frozen versions
docs/requirements.txt    # Auto-generated docs dependencies
setup.py, setup.cfg      # Legacy packaging metadata
conda-recipe/*.yaml      # Conda-specific files
solarwindpy.yml          # Auto-generated conda environment
```

**Critical Issue Discovered**:
```bash
# pyproject.toml specified:
numpy>=1.22,<2.0

# But requirements.txt contained:
numpy==2.2.6  # VIOLATION!
```

This happened because `freeze_requirements.py` used `pip freeze` without validating `pyproject.toml` constraints.

### Solution: Single Source of Truth

**After v0.3.0** (4 files):
```
pyproject.toml           # SINGLE SOURCE: All dependency definitions
requirements.txt         # Lockfile (auto-generated via pip-compile)
requirements-dev.lock    # Dev lockfile (auto-generated via pip-compile)
docs/requirements.txt    # Docs lockfile (auto-generated via pip-compile)
```

**Workflow**:
```bash
# 1. Edit dependencies in pyproject.toml
# 2. Regenerate lockfiles
pip-compile pyproject.toml --output-file=requirements.txt
pip-compile --extra=dev pyproject.toml --output-file=requirements-dev.lock
pip-compile --extra=docs pyproject.toml --output-file=docs/requirements.txt

# 3. Install from lockfile
pip install -r requirements-dev.lock
```

---

## Breaking Changes

### 1. Developer Installation Workflow

#### ❌ Old Workflow (v0.2.x)
```bash
git clone https://github.com/blalterman/SolarWindPy.git
cd SolarWindPy
pip install -r requirements-dev.txt
pip install -e .
```

#### ✅ New Workflow (v0.3.0+)
```bash
git clone https://github.com/blalterman/SolarWindPy.git
cd SolarWindPy
pip install -r requirements-dev.lock
pip install -e .
```

**Why**: `requirements-dev.txt` is deleted; use `requirements-dev.lock` instead.

---

### 2. Updating Dependencies

#### ❌ Old Workflow (v0.2.x)
```bash
# Edit requirements-dev.txt manually
echo "new-package>=1.0" >> requirements-dev.txt

# Regenerate frozen files
python scripts/freeze_requirements.py
python scripts/generate_docs_requirements.py
```

#### ✅ New Workflow (v0.3.0+)
```bash
# Edit pyproject.toml [project.dependencies] or [project.optional-dependencies]
# Then regenerate lockfiles:
pip-compile pyproject.toml --output-file=requirements.txt --upgrade
pip-compile --extra=dev pyproject.toml --output-file=requirements-dev.lock --upgrade
pip-compile --extra=docs pyproject.toml --output-file=docs/requirements.txt --upgrade

# Install updated dependencies
pip install -r requirements-dev.lock
```

**Why**: Custom Python scripts replaced by industry-standard `pip-tools`.

---

### 3. Dependency Groups Reorganization

#### Before (v0.2.x)
All dev dependencies in one flat `requirements-dev.txt` file.

#### After (v0.3.0+)
Dependencies organized by purpose in `pyproject.toml`:

```toml
[project.dependencies]
# Runtime dependencies (required for users)
numpy>=1.26,<3.0
scipy>=1.13
pandas>=2.0
...

[project.optional-dependencies.test]
# Testing dependencies
pytest>=8.0
pytest-cov>=6.0

[project.optional-dependencies.docs]
# Documentation dependencies
sphinx>=7.0
numpydoc>=1.6
...

[project.optional-dependencies.dev]
# Development dependencies (includes test + docs)
solarwindpy[test,docs]
black>=24.0
flake8>=7.0
...
```

**Install specific groups**:
```bash
pip install -e .[test]       # Runtime + testing
pip install -e .[docs]       # Runtime + docs
pip install -e .[dev]        # Runtime + test + docs + dev tools
```

---

## NumPy 2.0 Migration

### Updated Constraints

| Package | v0.2.x | v0.3.0 | Reason |
|---------|--------|--------|--------|
| **numpy** | `>=1.22,<2.0` | `>=1.26,<3.0` | NumPy 2.0 support |
| **scipy** | `>=1.10` | `>=1.13` | NumPy 2.0 compatibility |
| **pandas** | `>=1.5` | `>=2.0` | NumPy 2.0 compatibility |
| **numba** | `>=0.57` | `>=0.59` | Minimum for NumPy 2.0 |
| **docstring-inheritance** | `>=2.0` | `>=2.2.0,<3.0` | MRO fix + exclude breaking v3.0 |
| **pytest** | `>=7.4.4` | `>=8.0` | Ecosystem update |
| **pytest-cov** | `>=4.1.0` | `>=6.0` | Ecosystem update |

### Compatibility Matrix

| NumPy Version | Status | Tests Passed | Notes |
|---------------|--------|--------------|-------|
| 1.26.4 | ✅ Tested | 247/247 | Minimum supported |
| 2.0.0 | ⚠️ Build Issues | N/A | No pre-built wheel for some platforms |
| 2.2.6 | ✅ Tested | 247/247 | Current ecosystem standard |

**Recommendation**: Let pip install the latest compatible version from lockfiles (typically 2.2.x or 2.3.x).

---

## CI/CD Changes

### GitHub Workflows Updated

| Workflow | Old Trigger | New Trigger | Key Changes |
|----------|-------------|-------------|-------------|
| `sync-requirements.yml` | `requirements-dev.txt` | `pyproject.toml` | Uses `pip-compile` instead of Python scripts |
| `continuous-integration.yml` | Used `requirements-dev.txt` | Uses `requirements-dev.lock` | Faster caching via lockfile hash |
| `security.yml` | Audited `requirements-dev.txt` | Audits `requirements-dev.lock` | Scans frozen versions |
| `publish.yml` | No validation | **Pre-release lockfile validation** | Blocks releases with out-of-sync lockfiles |
| `ci-master.yml` | Used `requirements-dev.txt` | Uses `requirements-dev.lock` | Consistent with other workflows |

### Dependabot Updates

**Before**: Dependabot updated `requirements-dev.txt` → `sync-requirements` workflow regenerated files

**After**: Dependabot updates `pyproject.toml` → `sync-requirements` workflow runs `pip-compile` → Creates PR with updated lockfiles

**Action Required**: Close any open Dependabot PRs for `requirements-dev.txt` - they're obsolete.

---

## Migration Steps

### For Developers

1. **Pull latest code**:
   ```bash
   git checkout master
   git pull
   ```

2. **Update your environment**:
   ```bash
   # Remove old environment (optional but recommended)
   conda deactivate
   conda env remove -n solarwindpy

   # Create fresh environment
   conda env create -f solarwindpy.yml
   conda activate solarwindpy

   # Install from new lockfile
   pip install -r requirements-dev.lock
   pip install -e .
   ```

3. **Verify installation**:
   ```bash
   python -c "import solarwindpy; import numpy; print(f'SolarWindPy: {solarwindpy.__version__}, NumPy: {numpy.__version__}')"
   pytest -q
   ```

### For CI/CD Pipelines

If you have custom CI that references old files:

**Replace**:
```yaml
pip install -r requirements-dev.txt
```

**With**:
```yaml
pip install -r requirements-dev.lock
```

---

## Rollback Procedure

### If v0.3.0 Causes Issues

**Option 1: Use v0.2.0**
```bash
pip install solarwindpy==0.2.0
```

**Option 2: Revert to v0.2.x branch**
```bash
git checkout v0.2.0
pip install -r requirements-dev.txt
pip install -e .
```

**Option 3: Pin NumPy <2.0 if NumPy 2.x causes issues**
```bash
# Temporary workaround
pip install "numpy<2.0"
```

---

## Frequently Asked Questions

### Q: Why were requirements-dev.txt and freeze_requirements.py deleted?

**A**: These files were redundant and error-prone. `pip-tools` is the industry standard for lockfile management and integrates directly with `pyproject.toml` (PEP 621). The old workflow had no validation to catch constraint violations like the numpy==2.2.6 issue.

### Q: Can I still use Conda?

**A**: Yes! The `solarwindpy.yml` conda environment file is still generated automatically. It's now created from `requirements.txt` instead of `requirements-dev.txt`:

```bash
python scripts/requirements_to_conda_env.py requirements.txt --name solarwindpy
conda env create -f solarwindpy.yml
```

### Q: What if I want to add a new dependency?

**A**: Edit `pyproject.toml` in the appropriate section, then regenerate lockfiles:

```toml
# For runtime dependencies
[project.dependencies]
new-package>=1.0

# For development tools
[project.optional-dependencies.dev]
new-dev-tool>=2.0
```

Then:
```bash
pip-compile pyproject.toml --output-file=requirements.txt --upgrade
pip-compile --extra=dev pyproject.toml --output-file=requirements-dev.lock --upgrade
```

### Q: Why does pip-compile sometimes pick different versions than pip install?

**A**: `pip-compile` resolves all dependencies at once and picks versions that satisfy all constraints. Regular `pip install` uses a greedy resolver. Lockfiles ensure reproducible builds across environments.

### Q: Do I need to install pip-tools as a user?

**A**: No, users only need `pip install solarwindpy`. Developers need `pip-tools` to regenerate lockfiles, but it's included in `requirements-dev.lock`:

```bash
pip install -r requirements-dev.lock  # Includes pip-tools
```

### Q: What about setup.py and setup.cfg?

**A**: Currently kept for compatibility, but may be removed in a future version. Modern Python packaging uses `pyproject.toml` exclusively (PEP 517/518/621).

---

## Resources

- **PEP 621**: [Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- **pip-tools documentation**: [https://pip-tools.readthedocs.io/](https://pip-tools.readthedocs.io/)
- **NumPy 2.0 migration guide**: [https://numpy.org/devdocs/numpy_2_0_migration_guide.html](https://numpy.org/devdocs/numpy_2_0_migration_guide.html)
- **SolarWindPy contributing guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Support

If you encounter issues after upgrading:

1. **Check compatibility**: Verify your environment meets minimum requirements (Python ≥3.11)
2. **Fresh install**: Try creating a new virtual environment from scratch
3. **Report bugs**: [GitHub Issues](https://github.com/blalterman/SolarWindPy/issues)
4. **Rollback**: Use v0.2.0 if needed (see Rollback Procedure above)

---

**Last Updated**: 2025-12-23
**Migration Status**: Complete
**Breaking Changes**: Yes - requires workflow updates
