# PyPI Deployment Plan - TestPyPI First Strategy
**Date**: 2025-08-23  
**Branch**: master  
**Goal**: Deploy SolarWindPy v0.1.0 to PyPI with thorough TestPyPI validation

## Current Status
✅ **Tokens Configured**:
- PYPI_API_TOKEN: Added 2025-08-23T22:40:10Z  
- TEST_PYPI_API_TOKEN: Added 2025-08-23T22:40:37Z

✅ **Package Exists**:
- PyPI: solarwindpy v0.0.1.dev0
- TestPyPI: solarwindpy v0.0.1.dev0

## Deployment Todo List
1. ✅ Add PyPI tokens to GitHub repository secrets
2. ⏳ Test token configuration with dry-run deployment
3. ⏳ Clean up repository state (uncommitted files, tmp directory)
4. ⏳ Install missing build dependencies
5. ⏳ Fix any test failures and linting issues
6. ⏳ Update CHANGELOG.md for v0.1.0 release
7. ⏳ Create and test v0.1.0-rc1 release candidate on TestPyPI
8. ⏳ Validate RC installation and functionality from TestPyPI
9. ⏳ Deploy v0.1.0 production release to PyPI
10. ⏳ Validate successful PyPI deployment

## Phase 1: Repository Preparation

### Clean Repository State
```bash
# Check current status
git status

# Clean tmp directory but keep folder
rm -f tmp/github-issues-migration-update-plan.md  # Remove old plan
# Keep this plan file: tmp/pypi-deployment-plan-testfirst-2025-08-23.md

# Handle any uncommitted changes
git add -A
git commit -m "chore: prepare for v0.1.0 release"
```

### Install Build Dependencies
```bash
pip install build twine setuptools_scm
```

### Fix Code Quality
```bash
# Format code
black solarwindpy/ tests/

# Check and fix linting
flake8 solarwindpy/ tests/

# Run tests
pytest -q

# If changes made, commit
git add -A
git commit -m "style: apply black formatting and fix linting issues"
```

### Update CHANGELOG.md
Add to CHANGELOG.md:
```markdown
## [0.1.0] - 2025-08-23
### Added
- Initial stable release on PyPI
- Semantic versioning with setuptools_scm
- Automated deployment pipeline via GitHub Actions
- Complete test coverage (≥95%)
- Release automation scripts (check_release_ready.py, bump_version.py)
- Comprehensive documentation for release process

### Changed
- Migrated from development to stable release
- Enhanced package metadata for PyPI distribution
```

Commit:
```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v0.1.0 release"
```

### Verify Release Readiness
```bash
python scripts/check_release_ready.py --verbose
# All checks should pass
```

## Phase 2: TestPyPI Validation

### Test Workflow Configuration
```bash
# Dry-run test (no actual upload)
gh workflow run publish.yml -f target=testpypi -f dry_run=true

# Monitor
gh run watch
# Or check: gh run list --workflow=publish.yml --limit=1
```

### Deploy Release Candidate to TestPyPI
```bash
# Create RC tag
python scripts/bump_version.py rc --dry-run  # Preview
python scripts/bump_version.py rc             # Creates v0.1.0-rc1

# Push to trigger TestPyPI deployment
git push origin v0.1.0-rc1

# Monitor deployment
gh run list --workflow=publish.yml --limit=1
# Visit: https://github.com/blalterman/SolarWindPy/actions
```

### Validate TestPyPI Package
```bash
# Wait for deployment to complete (~2-3 minutes)
# Check: https://test.pypi.org/project/solarwindpy/0.1.0rc1/

# Create test environment
conda create -n testpypi-validation python=3.12 -y
conda activate testpypi-validation

# Install from TestPyPI with PyPI fallback for dependencies
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ solarwindpy==0.1.0rc1

# Validate installation
python -c "
import solarwindpy
print(f'✅ Version: {solarwindpy.__version__}')
assert '0.1.0rc1' in solarwindpy.__version__, 'Version mismatch!'
"

# Test core functionality
python -c "
from solarwindpy.core import plasma, ions
from solarwindpy.tools import units_constants as uc
import numpy as np

print('✅ Core modules imported')
print(f'✅ Constants accessible: k_B = {uc.k_B}')
print('✅ TestPyPI package validated successfully')
"

# Clean up test environment
conda deactivate
conda env remove -n testpypi-validation -y
```

### Deploy Additional RCs if Needed
If issues found:
```bash
# Fix issues and commit
git add -A
git commit -m "fix: address issues from RC1 testing"

# Create new RC
python scripts/bump_version.py rc  # Creates v0.1.0-rc2
git push origin v0.1.0-rc2

# Repeat validation
```

## Phase 3: Production PyPI Deployment

### Create Production Release
```bash
# Only after RC validation succeeds
python scripts/bump_version.py minor --dry-run  # Preview
python scripts/bump_version.py minor            # Creates v0.1.0

# Push to trigger PyPI deployment
git push origin v0.1.0

# Monitor deployment
gh run watch
# Visit: https://github.com/blalterman/SolarWindPy/actions
```

### Validate PyPI Package
```bash
# Wait for deployment (~2-3 minutes)
# Check: https://pypi.org/project/solarwindpy/0.1.0/

# Create clean production test environment
conda create -n pypi-validation python=3.12 -y
conda activate pypi-validation

# Install from PyPI
pip install solarwindpy==0.1.0

# Comprehensive validation
python -c "
import solarwindpy
print(f'✅ SolarWindPy {solarwindpy.__version__} installed from PyPI')
assert solarwindpy.__version__ == '0.1.0', 'Version mismatch!'

# Test imports
from solarwindpy.core import plasma, ions, base
from solarwindpy.tools import units_constants
from solarwindpy.plotting import plot_utils

print('✅ All core modules accessible')
print('✅ Production deployment validated successfully')
"

# Clean up
conda deactivate
conda env remove -n pypi-validation -y
```

## Phase 4: Post-Deployment

### Update GitHub Release Notes
```bash
gh release edit v0.1.0 --notes "
## 🎉 SolarWindPy v0.1.0 - First Stable Release on PyPI!

### Installation
\`\`\`bash
pip install solarwindpy
\`\`\`

### What's New
- First stable release on PyPI
- Semantic versioning with automated deployment
- Comprehensive test coverage (≥95%)
- Full documentation and examples

### Quick Start
\`\`\`python
import solarwindpy as swp
# Your solar wind analysis code here
\`\`\`

See [CHANGELOG.md](CHANGELOG.md) for detailed changes.
"
```

### Clean Up Release Candidates
```bash
# Optional: Remove RC tags after successful release
git tag -d v0.1.0-rc1
git push origin :v0.1.0-rc1

# Note: Keep TestPyPI packages for reference
```

## Rollback Procedures

### TestPyPI RC Issues
```bash
# Delete and recreate RC
git tag -d v0.1.0-rc1
git push origin :v0.1.0-rc1
# Fix and create new RC
```

### Production Issues
```bash
# Yank problematic version (cannot delete from PyPI)
pip install twine
twine yank solarwindpy 0.1.0 --reason "Critical issue, use 0.1.1"

# Create hotfix
git checkout -b hotfix/0.1.1 v0.1.0
# Apply fixes
python scripts/bump_version.py patch  # v0.1.1
git push origin v0.1.1
```

## Success Metrics
- [ ] Repository checks pass (check_release_ready.py)
- [ ] Dry-run workflow executes successfully
- [ ] RC deploys to TestPyPI without errors
- [ ] Package installs from TestPyPI
- [ ] Core functionality works from TestPyPI package
- [ ] Production release deploys to PyPI
- [ ] Package installs from PyPI
- [ ] Version shows as 0.1.0 (not dev)
- [ ] GitHub release created with artifacts

## Timeline Estimate
- Repository preparation: 20-30 minutes
- TestPyPI RC validation: 15-20 minutes
- Production deployment: 5-10 minutes
- Post-deployment tasks: 5 minutes
- **Total**: ~45-65 minutes

## Important Notes
1. **Test on TestPyPI first** - This validates the entire pipeline
2. **Use release candidates** - RC tags allow testing without affecting stable versions
3. **Verify each step** - Don't proceed until current step succeeds
4. **Keep RC packages** - TestPyPI RCs provide testing history
5. **Document issues** - Update this plan with any problems encountered

## Current Issues from check_release_ready.py
Based on initial check, need to address:
- Git status (uncommitted files)
- Version detection (need tag)
- CHANGELOG updates
- Test failures
- Linting issues
- Build package installation

All must be resolved before creating release tags.