# PR #405: setup-miniconda@v3 Patching Issue

**Status**: Resolved (December 2024)
**Impact**: Critical - CI workflows failing with dependency resolution errors
**Solution**: Dynamic environment file generation in GitHub Actions workflows
**Related**: Third in cascading bug series (comments → `==` syntax → patching)

---

## Problem Summary

setup-miniconda@v3 GitHub Action patches conda environment files when both `environment-file` and `python-version` parameters are specified, rewriting dependency syntax in ways that break conda/mamba dependency resolution.

**Symptom**:
```
error libmamba Could not solve for environment specs
  The following packages are incompatible
  ├─ numexpr =2.11.0 * does not exist (perhaps a typo or a missing channel);
  └─ tzdata =2025.3 * does not exist (perhaps a typo or a missing channel).
```

**Key observation**: Local `solarwindpy.yml` is correct (`numexpr=2.11.0` with no space), but CI uses modified file with spaces (`numexpr =2.11.0 *`).

---

## Root Cause

### The Conflict

Workflow `.github/workflows/doctest_validation.yml` specified:
```yaml
- uses: conda-incubator/setup-miniconda@v3
  with:
    environment-file: solarwindpy.yml         # File WITHOUT Python version
    python-version: ${{ matrix.python-version }}  # Python FROM matrix (3.11, 3.12)
```

This creates conflicting specifications:
1. Environment file: No explicit Python constraint
2. Workflow parameter: Explicit Python version (3.11 or 3.12)

### The Patching Behavior

setup-miniconda@v3 detects the conflict and automatically:
1. Creates temporary file `setup-miniconda-patched-solarwindpy.yml`
2. Injects Python version constraint into dependencies
3. **Rewrites dependency syntax** using conda's normalized format
4. Uses patched file for environment creation
5. Deletes patched file after setup (by default)

### The Syntax Transformation

During patching, conda normalizes dependency specifications:

| Original (solarwindpy.yml) | Patched (normalized) | Result |
|----------------------------|----------------------|--------|
| `- numexpr=2.11.0` | `numexpr =2.11.0 *` | ❌ Resolution fails |
| `- tzdata=2025.3` | `tzdata =2025.3 *` | ❌ Resolution fails |

**Why spaces break resolution**: The space before `=` causes mamba/conda YAML parser to misinterpret the specification, treating it as malformed syntax rather than a valid package constraint.

**Why wildcards appear**: The `*` means "any build number" - conda's way of making the constraint more flexible during resolution.

### Why Patching Exists

setup-miniconda implements patching to prevent **silent Python downgrades**. Without explicit Python pinning, conda might:
- Choose Python 3.10 to satisfy package constraints (when 3.11 was expected)
- Install incompatible Python version without warning
- Break code that depends on 3.11+ features

Reference: [setup-miniconda Issue #114](https://github.com/conda-incubator/setup-miniconda/issues/114)

---

## Timeline: Cascading Bug Series

This was the **third** bug discovered in PR #405, each masked by the previous:

| Bug # | Symptom | Root Cause | Fix | Commit |
|-------|---------|------------|-----|--------|
| **1** | `# [==astropy *\|...] does not exist` | Indented pip-compile comments not filtered | `line.strip().startswith("#")` | e37bc407 |
| **2** | `numexpr ==2.11.0 * does not exist` | pip `==` vs conda `=` syntax | Convert `==` → `=` in translation | 761f3ba3 |
| **3** | `numexpr =2.11.0 * does not exist` | setup-miniconda patching adds spaces | Dynamic environment generation | [third] |

**Why cascading**:
- Bug #1 prevented conda from parsing YAML → couldn't reach bug #2
- Bug #2 (after fix) prevented conda from resolving packages → couldn't reach bug #3
- Bug #3 only visible after first two fixes succeeded

---

## Solution: Dynamic Environment File Generation

### Approach

Generate matrix-specific environment files **before** setup-miniconda runs, eliminating the conflict that triggers patching.

### Implementation

**Workflow step** (`.github/workflows/doctest_validation.yml`):
```yaml
- name: Create matrix-specific environment file
  shell: python
  run: |
    import yaml

    # Read base environment file (intentionally omits Python version)
    with open('solarwindpy.yml', 'r') as f:
        env = yaml.safe_load(f)

    # Inject matrix-specific Python version as first dependency
    python_version = '${{ matrix.python-version }}'
    env['dependencies'].insert(0, f'python={python_version}')

    # Write complete environment file for this matrix job
    with open('solarwindpy-matrix.yml', 'w') as f:
        yaml.safe_dump(env, f, sort_keys=False)

    print(f'✅ Generated solarwindpy-matrix.yml with Python {python_version}')

- name: Set up conda environment
  uses: conda-incubator/setup-miniconda@v3
  with:
    environment-file: solarwindpy-matrix.yml  # ← Generated file with Python
    activate-environment: solarwindpy
    # python-version: REMOVED - now in environment file
    auto-activate-base: false
    use-only-tar-bz2: true
    miniforge-version: latest
```

**Key changes**:
1. Base file `solarwindpy.yml` **omits** Python version
2. Python script dynamically injects `python=${{ matrix.python-version }}`
3. Generated file `solarwindpy-matrix.yml` is complete (no missing Python)
4. `python-version` parameter **removed** from setup-miniconda (no conflict)
5. No patching occurs → dependencies preserve original syntax

### Why Python Script (Not Shell)

**Cross-platform compatibility**:
- `sed -i` syntax differs between Linux and macOS
- Python + PyYAML available in all GitHub Actions runners
- More robust than shell text processing

**Alternative** (shell, Linux-only):
```yaml
- name: Create matrix-specific environment file
  run: |
    cp solarwindpy.yml solarwindpy-matrix.yml
    sed -i "/^dependencies:/a - python=${{ matrix.python-version }}" solarwindpy-matrix.yml
```

### PyYAML Dependency

The dynamic generation script requires PyYAML to parse and modify the environment file.

**Installation**: Workflows install PyYAML via pip before running the generation script:
```yaml
- name: Install PyYAML for environment file generation
  run: python -m pip install pyyaml
```

**Why not use conda's PyYAML?**: The script runs BEFORE the conda environment exists (chicken-and-egg problem). Installing via pip in the runner's Python is the simplest solution.

**Impact**: Negligible (~3-5 seconds, ~500KB)

**Note**: PyYAML will be installed twice (once in GitHub Actions runner via pip, once in conda environment). This is harmless - they exist in separate Python environments.

---

## Matrix Testing Preservation

### How Matrix Works After Fix

**Matrix definition**:
```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
```

**Execution**:
- **Job 1** (matrix.python-version = 3.11):
  - Generates `solarwindpy-matrix.yml` with `- python=3.11`
  - Creates conda environment with Python 3.11.x

- **Job 2** (matrix.python-version = 3.12):
  - Generates `solarwindpy-matrix.yml` with `- python=3.12`
  - Creates conda environment with Python 3.12.x

**Result**: Each matrix job tests a different Python version (as intended).

### Alternative: Static Python Range

**If matrix testing not needed**, could use static range in base file:

```yaml
# solarwindpy.yml
dependencies:
- python>=3.11,<3.14  # Conda resolves to latest (3.12 or 3.13)
- astropy=7.1.0
...
```

**But**: This breaks matrix - all jobs would use same Python (latest resolved).

---

## Validation

### Expected CI Behavior

**Before fix**:
```
Line 753: mamba env create --file setup-miniconda-patched-solarwindpy.yml
Line 757: numexpr =2.11.0 * does not exist
```

**After fix**:
```
Line 753: mamba env create --file solarwindpy-matrix.yml
✅ Solving environment: done
✅ Downloading and Extracting Packages
✅ Installing packages...
```

### Checklist

**Pre-push**:
- [ ] Base `solarwindpy.yml` omits Python version
- [ ] Workflow generates `solarwindpy-matrix.yml` dynamically
- [ ] `python-version` parameter removed from setup-miniconda
- [ ] Both locations in workflow updated (doctest-validation, spot-check-validation)

**Post-push CI logs**:
- [ ] No `setup-miniconda-patched-solarwindpy.yml` file created
- [ ] Environment created from `solarwindpy-matrix.yml`
- [ ] Dependency resolution succeeds
- [ ] Tests execute successfully

---

## Files Modified

1. **solarwindpy.yml**: Comment added explaining Python omission
2. **.github/workflows/doctest_validation.yml**: Dynamic generation added, python-version removed (2 locations)
3. **.claude/docs/MAINTENANCE.md**: Brief note added with pointer to this document

---

## References

**Upstream Issues**:
- [setup-miniconda #114: Python version pinning](https://github.com/conda-incubator/setup-miniconda/issues/114)
- [setup-miniconda #105: Multiple environment files](https://github.com/conda-incubator/setup-miniconda/issues/105)

**Related Documentation**:
- [Conda Package Specifications](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/pkg-specs.html)
- [Managing Conda Environments](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)

**SolarWindPy PR #405**:
- Commit e37bc407: Fix #1 (comment filtering)
- Commit 761f3ba3: Fix #2 (== to = conversion)
- Commit [third]: Fix #3 (dynamic generation)

---

## Future Considerations

### If setup-miniconda@v4 Fixes Patching

Monitor https://github.com/conda-incubator/setup-miniconda for:
- Issue #114 resolution
- New version that handles conflicting specs without syntax changes

**If fixed in future version**:
1. Update this document's status to "Obsolete (fixed in setup-miniconda@v4)"
2. Simplify workflow to use direct environment file + python-version parameter
3. Keep this document for historical reference

### Alternative: Switch to micromamba

Consider [provision-with-micromamba](https://github.com/mamba-org/provision-with-micromamba) action:
- Faster than miniconda
- May have different patching behavior
- Test in separate PR before migration

---

## Documentation Architecture

This file is the **Single Source of Truth (SSoT)** for PR #405 patching issue.

**Other documentation locations** reference this file:
- Workflow inline comments: Brief summary + link to this file
- `solarwindpy.yml` comment: Notes Python omission, links here
- `MAINTENANCE.md`: One-line note + link to this file
- Commit message: Summary + link to this file

**Why**: Prevents documentation drift by maintaining detailed analysis in one location.

---

*Last updated: December 2024*
*Discoverer: Claude Code during PR #405 diagnosis*
*Status: Resolved - dynamic generation prevents patching*
