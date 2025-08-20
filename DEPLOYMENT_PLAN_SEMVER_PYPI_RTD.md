# Unified Implementation Plan: Semantic Versioning, PyPI, and ReadTheDocs

## Overview
This plan integrates semantic versioning enforcement with PyPI and ReadTheDocs deployment, ensuring a robust release pipeline for SolarWindPy.

## Part 1: Semantic Versioning Foundation

### 1.1 Configure setuptools_scm
**File**: `pyproject.toml`

Add after the `[build-system]` section:
```toml
[tool.setuptools_scm]
# Enforce semantic versioning format
version_scheme = "no-guess-dev"
local_scheme = "node-and-date"
write_to = "solarwindpy/_version.py"
write_to_template = '''
"""Version information for solarwindpy."""
__version__ = "{version}"
__version_tuple__ = {version_tuple}
'''
tag_regex = "^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+.*)$"

[tool.setuptools_scm.version_scheme]
# Ensure proper version formatting
```

### 1.2 Update .gitignore
Add to `.gitignore`:
```
# Auto-generated version file
solarwindpy/_version.py
```

### 1.3 Create CHANGELOG.md
```markdown
# Changelog

All notable changes to SolarWindPy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release
- Core plasma physics calculations
- Solar wind data analysis tools
- Comprehensive documentation
- PyPI package distribution
- ReadTheDocs integration
- GitHub Actions CI/CD pipeline

## [0.1.0] - 2025-08-XX

### Added
- Initial release with core functionality

[Unreleased]: https://github.com/blalterman/SolarWindPy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/blalterman/SolarWindPy/releases/tag/v0.1.0
```

## Part 2: PyPI Deployment Setup

### 2.1 Fix publish.yml
**File**: `.github/workflows/publish.yml`

Update these sections:
```yaml
# Line 27: Update checkout action
- uses: actions/checkout@v4  # Updated from v3
  with:
    fetch-depth: 0  # Need full history for setuptools_scm

# Line 32-33: Update Python version
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Updated from 3.11

# After line 35, add version enforcement
- name: Enforce semantic versioning
  run: |
    # Install setuptools_scm to verify version
    pip install setuptools_scm packaging
    
    # Get version from setuptools_scm
    VERSION=$(python -c "from setuptools_scm import get_version; print(get_version())")
    echo "Detected version: $VERSION"
    echo "VERSION=$VERSION" >> $GITHUB_ENV
    
    # For tags, ensure version matches tag
    if [[ "$GITHUB_REF" == refs/tags/* ]]; then
      TAG=${GITHUB_REF#refs/tags/}
      TAG_VERSION=${TAG#v}
      
      # Strict semver validation
      if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+[0-9]*)?$ ]]; then
        echo "❌ Invalid tag format: $TAG"
        echo "Expected: v{major}.{minor}.{patch}[-prerelease]"
        exit 1
      fi
      
      # Version must match tag
      python -c "
from packaging import version
detected = version.parse('$VERSION')
expected = version.parse('$TAG_VERSION')
if str(detected).replace('rc', '-rc') != str(expected).replace('rc', '-rc'):
    print(f'❌ Version mismatch: tag={expected}, detected={detected}')
    exit 1)
print(f'✅ Version validated: {detected}')
      "
    fi

# After line 86, add informative message for missing token
- name: Check PyPI Token Status
  if: failure() && (contains(github.ref, 'refs/tags/') || github.event_name == 'workflow_dispatch')
  run: |
    echo "::warning::PyPI deployment failed - likely missing API token"
    echo "::warning::Add PYPI_API_TOKEN and TEST_PYPI_API_TOKEN secrets when available"
    echo "::notice::Package artifacts are still available in GitHub Release"
    echo "::notice::Version ${{ env.VERSION }} was built successfully"
```

## Part 3: ReadTheDocs Configuration

### 3.1 Enhanced .readthedocs.yaml
**File**: `.readthedocs.yaml` (update existing)

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"
  
  # Better build process
  jobs:
    post_create_environment:
      - pip install --upgrade pip setuptools wheel setuptools_scm
    post_install:
      - pip list
      - python -c "from setuptools_scm import get_version; print(f'Building docs for version {get_version()}')"

# Build additional formats
formats:
  - pdf
  - epub
  - htmlzip

python:
  install:
    - requirements: requirements.txt
    - requirements: docs/requirements.txt
    - method: pip
      path: .
      extra_requirements:
        - docs

sphinx:
  configuration: docs/source/conf.py
  fail_on_warning: false  # Set to true once warnings are fixed

# Version configuration handled automatically via tags
```

### 3.2 Update README.rst
**File**: `README.rst`

Replace line 5 badges with:
```rst
|PyPI| |Conda| |RTD| |Build Status| |License| |Black Code| |Version|

.. |PyPI| image:: https://img.shields.io/pypi/v/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
   :alt: PyPI Version

.. |Conda| image:: https://img.shields.io/conda/vn/conda-forge/solarwindpy.svg
   :target: https://anaconda.org/conda-forge/solarwindpy
   :alt: Conda Version

.. |RTD| image:: https://readthedocs.org/projects/solarwindpy/badge/?version=latest
   :target: https://solarwindpy.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |Version| image:: https://img.shields.io/github/v/tag/blalterman/SolarWindPy?label=version
   :target: https://github.com/blalterman/SolarWindPy/releases
   :alt: Latest Version
```

### 3.3 Update pyproject.toml URLs
**File**: `pyproject.toml`

Update `[project.urls]` section:
```toml
[project.urls]
"Homepage" = "https://solarwindpy.github.io"
"Documentation" = "https://solarwindpy.readthedocs.io"
"Bug Tracker" = "https://github.com/blalterman/SolarWindPy/issues"
"Source" = "https://github.com/blalterman/SolarWindPy"
"Changelog" = "https://github.com/blalterman/SolarWindPy/blob/master/CHANGELOG.md"
```

## Part 4: Automation Workflows

### 4.1 Create Semantic Version Check
**File**: `.github/workflows/semver-check.yml`

```yaml
name: Semantic Version Check

on:
  push:
    tags:
      - '*'

jobs:
  validate-version:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install setuptools_scm packaging
      
      - name: Validate tag format
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          
          # Must match v{major}.{minor}.{patch}[-prerelease]
          if ! [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-z]+[0-9]*)?$ ]]; then
            echo "❌ Invalid tag format: $TAG"
            echo ""
            echo "✅ Valid formats:"
            echo "  - v1.0.0 (stable release)"
            echo "  - v1.0.0-rc1 (release candidate)"
            echo "  - v1.0.0-beta1 (beta release)"
            echo "  - v1.0.0-alpha (alpha release)"
            exit 1
          fi
          
          echo "✅ Valid semantic version: $TAG"
          
          # Verify setuptools_scm can parse it
          VERSION=$(python -c "from setuptools_scm import get_version; print(get_version())")
          echo "setuptools_scm version: $VERSION"
```

## Part 5: Helper Scripts

### 5.1 Release Readiness Checker
**File**: `scripts/check_release_ready.py`

```python
#!/usr/bin/env python3
"""Verify project is ready for release."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def check_release_readiness():
    """Check if project is ready for release."""
    checks = []
    
    # 1. Check for uncommitted changes
    success, stdout, _ = run_command("git status --porcelain")
    checks.append({
        "name": "Clean working directory",
        "passed": len(stdout.strip()) == 0,
        "message": "No uncommitted changes" if len(stdout.strip()) == 0 else f"Uncommitted files found"
    })
    
    # 2. Check we're on master branch
    success, stdout, _ = run_command("git branch --show-current")
    branch = stdout.strip()
    checks.append({
        "name": "On master branch",
        "passed": branch == "master",
        "message": f"On {branch}" if branch == "master" else f"Not on master (current: {branch})"
    })
    
    # 3. Check version can be determined
    success, stdout, _ = run_command("python -c 'from setuptools_scm import get_version; print(get_version())'")
    checks.append({
        "name": "Version detectable",
        "passed": success,
        "message": f"Version: {stdout.strip()}" if success else "Cannot determine version"
    })
    
    # 4. Check CHANGELOG exists and has content
    changelog = Path("CHANGELOG.md")
    has_unreleased = False
    if changelog.exists():
        content = changelog.read_text()
        has_unreleased = "## [Unreleased]" in content and len(content.split("## [Unreleased]")[1].strip()) > 50
    
    checks.append({
        "name": "CHANGELOG updated",
        "passed": changelog.exists() and has_unreleased,
        "message": "CHANGELOG has unreleased content" if has_unreleased else "CHANGELOG needs updates"
    })
    
    # 5. Check tests pass
    success, _, _ = run_command("pytest -q --co")  # Just collect tests for speed
    checks.append({
        "name": "Tests collected",
        "passed": success,
        "message": "Tests can be collected" if success else "Test collection failed"
    })
    
    # 6. Check PyPI token configured (informational)
    success, stdout, _ = run_command("gh secret list 2>/dev/null | grep -q PYPI_API_TOKEN")
    checks.append({
        "name": "PyPI token (optional)",
        "passed": success,
        "message": "Token configured" if success else "Token not configured (deployment will fail)"
    })
    
    # Print results
    print("\n📋 Release Readiness Checklist\n")
    all_passed = True
    required_passed = True
    
    for i, check in enumerate(checks):
        is_optional = "optional" in check["name"].lower()
        icon = "✅" if check["passed"] else ("⚠️" if is_optional else "❌")
        print(f"{icon} {check['name']}: {check['message']}")
        
        if not is_optional and not check["passed"]:
            required_passed = False
        all_passed = all_passed and check["passed"]
    
    if required_passed:
        print("\n🎉 Ready for release!")
        print("\nNext steps:")
        print("1. Update CHANGELOG.md with release date")
        print("2. Create tag: git tag v0.1.0 -m 'Initial release'")
        print("3. Push tag: git push origin v0.1.0")
        print("4. Monitor GitHub Actions for deployment")
        return 0
    else:
        print("\n⚠️ Not ready for release. Fix required issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(check_release_readiness())
```

### 5.2 Version Bump Helper
**File**: `scripts/bump_version.py`

```python
#!/usr/bin/env python3
"""Helper script to create version tags following semver."""

import argparse
import subprocess
import re
from packaging import version

def get_latest_tag():
    """Get the latest version tag."""
    cmd = "git describe --tags --abbrev=0 --match='v*'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return "v0.0.0"  # First version

def bump_version(current, bump_type):
    """Bump version based on type."""
    # Handle first release
    if current == "v0.0.0":
        if bump_type in ["rc", "beta", "alpha"]:
            return f"v0.1.0-{bump_type}1"
        return "v0.1.0"
    
    # Parse current version
    v = version.parse(current.lstrip('v'))
    major, minor, patch = v.major, v.minor, v.micro
    
    if bump_type == "major":
        return f"v{major + 1}.0.0"
    elif bump_type == "minor":
        return f"v{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    else:  # prerelease
        base = f"v{major}.{minor}.{patch}"
        if v.is_prerelease:
            # Increment existing prerelease
            match = re.search(r'-([a-z]+)(\d+)', current)
            if match:
                prefix = match.group(1)
                if prefix == bump_type:
                    num = int(match.group(2)) + 1
                    return f"{base}-{bump_type}{num}"
        # New prerelease
        return f"{base}-{bump_type}1"

def main():
    parser = argparse.ArgumentParser(description="Bump version following semver")
    parser.add_argument("type", choices=["major", "minor", "patch", "rc", "beta", "alpha"],
                       help="Type of version bump")
    parser.add_argument("-m", "--message", help="Tag message")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without creating tag")
    
    args = parser.parse_args()
    
    current = get_latest_tag()
    new_version = bump_version(current, args.type)
    
    print(f"Current version: {current}")
    print(f"New version: {new_version}")
    
    if not args.dry_run:
        message = args.message or f"Release {new_version}"
        cmd = f'git tag -a {new_version} -m "{message}"'
        subprocess.run(cmd, shell=True)
        print(f"✅ Created tag {new_version}")
        print(f"Push with: git push origin {new_version}")
    else:
        print("(dry run - no tag created)")

if __name__ == "__main__":
    main()
```

## Part 6: Manual ReadTheDocs Setup

### Required manual steps on readthedocs.org:

1. **Import Project**:
   - Go to https://readthedocs.org/dashboard/import/
   - Select "blalterman/SolarWindPy"
   - Click "Continue"

2. **Configure Project**:
   ```
   Name: solarwindpy
   Repository URL: https://github.com/blalterman/SolarWindPy
   Default branch: master
   Default version: latest (will become 'stable' after v0.1.0)
   Language: English
   Programming Language: Python
   Project homepage: https://solarwindpy.github.io
   ```

3. **Advanced Settings**:
   - Build pull requests: ✓ Yes
   - Privacy Level: Public
   - Single version: ✗ No (we want versioned docs)

4. **After First Tag** (v0.1.0):
   - Set default version to "stable"
   - Point "stable" to v0.1.0

## Implementation Timeline

### Day 1 (Immediate - No Token Required)
1. **Hour 1**: Semantic Versioning Setup
   - [ ] Add setuptools_scm configuration to pyproject.toml
   - [ ] Update .gitignore
   - [ ] Create CHANGELOG.md

2. **Hour 2**: PyPI Workflow Updates
   - [ ] Update publish.yml with v4 actions and version validation
   - [ ] Add Python 3.12 and error handling

3. **Hour 3**: ReadTheDocs Setup
   - [ ] Update .readthedocs.yaml
   - [ ] Setup ReadTheDocs project online
   - [ ] Update README.rst badges

4. **Hour 4**: Helper Scripts & Testing
   - [ ] Create check_release_ready.py
   - [ ] Create bump_version.py
   - [ ] Create semver-check.yml workflow
   - [ ] Test with v0.1.0-rc1 tag

### Day 10+ (After PyPI Token)
1. Add secrets to GitHub:
   - [ ] PYPI_API_TOKEN
   - [ ] TEST_PYPI_API_TOKEN
2. Remove `continue-on-error: true` from publish.yml
3. Create v0.1.0 release

## Testing Plan

### Test 1: Version Detection
```bash
# Should show dev version
python -c "from setuptools_scm import get_version; print(get_version())"
# Expected: 0.1.dev607+gc0bc6b5
```

### Test 2: Release Readiness
```bash
python scripts/check_release_ready.py
# Should show checklist with current status
```

### Test 3: Create Test Tag
```bash
# Dry run first
python scripts/bump_version.py rc --dry-run

# Create actual RC tag
git tag v0.1.0-rc1 -m "First release candidate for testing"
git push origin v0.1.0-rc1

# This will:
# - Trigger semver-check workflow ✅
# - Trigger publish workflow (will fail at PyPI upload) ⚠️
# - Create GitHub release with artifacts ✅
# - Trigger ReadTheDocs build ✅
```

### Test 4: Verify Deployments
- GitHub Release: Check https://github.com/blalterman/SolarWindPy/releases
- ReadTheDocs: Check https://solarwindpy.readthedocs.io/en/v0.1.0-rc1/
- PyPI: Will show warning in Actions (expected until token added)

## Success Criteria

### Immediate Success (Without PyPI Token):
- ✅ Semantic versioning enforced via setuptools_scm
- ✅ Version validation in workflows
- ✅ GitHub releases created with artifacts
- ✅ ReadTheDocs building versioned documentation
- ⚠️ PyPI upload fails gracefully with clear message

### Full Success (With PyPI Token):
- ✅ All of the above, plus:
- ✅ PyPI receives releases automatically
- ✅ TestPyPI receives RC versions
- ✅ All badges show green status

This unified plan provides a complete path from development to distribution with proper versioning throughout.