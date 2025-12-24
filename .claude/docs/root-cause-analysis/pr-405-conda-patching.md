# PR #405: CI Conda Environment Resolution Issues

**Status**: Resolved (December 2024)
**Impact**: Critical - CI workflows failing with dependency resolution errors
**Final Solution**: Unversioned packages in conda environment file
**Related**: Five cascading bugs (comments → syntax → patching → PyYAML → version mismatch)

---

## Problem Summary

CI workflows failed with conda resolution errors:
```
error libmamba Could not solve for environment specs
  ├─ numexpr =2.11.0 * does not exist (perhaps a typo or a missing channel);
  └─ tzdata =2025.3 * does not exist (perhaps a typo or a missing channel).
```

---

## Root Cause

**PyPI/conda-forge version mismatch**: pip-compile pins exact PyPI versions, but those versions don't exist on conda-forge:

| Package | PyPI Version | conda-forge | Issue |
|---------|-------------|-------------|-------|
| numexpr | 2.11.0 | 2.10.2, 2.12.1+ | **2.11.x skipped entirely** |
| tzdata | 2025.3 | 2025a, 2025b, 2025c | **Different versioning scheme** |

The error format (`numexpr =2.11.0 *`) is conda's internal display—the version simply doesn't exist on the configured channels.

---

## Solution: Unversioned Packages

**Final approach**: Strip ALL version pins from conda environment file.

**`solarwindpy.yml`**:
```yaml
dependencies:
- astropy      # No version - conda resolves to latest
- numexpr      # No version - avoids PyPI/conda-forge mismatch
- numpy
- pandas
- tzdata       # No version - different scheme on conda-forge
```

**Why this works**:
1. **Conda** just needs packages present, resolves to latest from conda-forge
2. **`pip install -e .`** enforces `pyproject.toml`'s minimum requirements
3. Eliminates entire class of PyPI/conda-forge version mismatch bugs
4. **setup-miniconda patching is harmless** with unversioned packages

**Implementation**: `scripts/requirements_to_conda_env.py` with `STRIP_EXACT_VERSIONS = True`

---

## Timeline: Cascading Bug Series

Five cascading bugs discovered in PR #405, each masked by the previous:

| Bug # | Symptom | Root Cause | Fix | Status |
|-------|---------|------------|-----|--------|
| **1** | `# [==astropy...]` errors | Indented comments not filtered | `line.strip().startswith("#")` | ✅ Active |
| **2** | `==` syntax errors | pip `==` vs conda `=` | Convert `==` → `=` | ⚠️ Dead code* |
| **3** | Patching corrupts syntax | setup-miniconda patching | Dynamic generation | ❌ Removed** |
| **4** | `ModuleNotFoundError: yaml` | PyYAML not installed | `pip install pyyaml` | ❌ Removed** |
| **5** | Version doesn't exist | PyPI/conda-forge mismatch | Strip all versions | ✅ **Core fix** |

*Bug #2 code is never executed when `STRIP_EXACT_VERSIONS = True` but kept as fallback.

**Bugs #3 and #4 were removed after testing showed unversioned packages make patching harmless. Verified with Python 3.11 and 3.12 matrix tests (commit d8f66dea).

---

## Key Insight

With **unversioned packages**, setup-miniconda patching is harmless:
- Patching adds version constraints and `*` wildcards
- With no versions to corrupt, patching either does nothing or adds harmless wildcards
- No need for dynamic environment file generation workaround

This simplification removed 56 lines of workflow complexity.

---

## Files Modified

1. **`solarwindpy.yml`**: Unversioned package list with explanatory header
2. **`scripts/requirements_to_conda_env.py`**: `STRIP_EXACT_VERSIONS = True`
3. **`.github/workflows/doctest_validation.yml`**: Simplified (removed dynamic generation)

---

## References

**Upstream Issues**:
- [setup-miniconda #114: Python version pinning](https://github.com/conda-incubator/setup-miniconda/issues/114)

**SolarWindPy PR #405 Key Commits**:
- `e37bc407`: Bug #1 fix (comment filtering)
- `6bcbf944`: Bug #5 fix (strip all versions)
- `d8f66dea`: Remove Bug #3/4 (dynamic generation no longer needed)

---

*Last updated: December 2024*
*Status: Resolved - unversioned packages eliminate version mismatch issues*
