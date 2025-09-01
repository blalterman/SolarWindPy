# Phase 6: Production Release

## Overview
Execute the full production release of SolarWindPy v0.1.0 to PyPI, creating the first official stable release with complete CI/CD pipeline validation.

## Objectives
- Create v0.1.0 production release tag
- Trigger full deployment pipeline
- Validate production PyPI deployment
- Confirm GitHub Release creation
- Initiate conda-forge update process
- Establish v0.1.0 as stable baseline

## Tasks

### Task 6.1: Create Production Release Tag (10 minutes)
**Implementation Steps:**
```bash
# Ensure on master with all changes
git checkout master
git pull origin master

# Verify RC testing completed successfully
git tag --list | grep v0.1.0
# Should show: v0.1.0-rc5 (and any previous RCs)

# Create production release tag
git tag -a v0.1.0 -m "SolarWindPy v0.1.0 - First Stable Release

Major Features:
- Solar wind plasma analysis toolkit
- MultiIndex DataFrame architecture for efficient data handling
- Physics validation and instability calculations
- Comprehensive plotting and visualization tools
- Full test coverage and documentation

Tested via:
- Release candidate v0.1.0-rc5 validation
- TestPyPI deployment verification
- Cross-platform compatibility testing
- Complete CI/CD pipeline validation"

# Push production tag to trigger full pipeline
git push origin v0.1.0
echo "Production release v0.1.0 tag pushed - monitoring workflow..."
```

### Task 6.2: Monitor Full Pipeline Execution (30 minutes)
**Expected Workflow Sequence:**

**1. Tag Detection (2 minutes)**
```
✅ Version Detection: "Production release detected: v0.1.0"
✅ is_prerelease=false set correctly
```

**2. Quality Checks (15 minutes)**
```
✅ Test Matrix: 12 jobs (3 OS × 4 Python versions)
✅ Ubuntu: Python 3.9, 3.10, 3.11, 3.12
✅ macOS: Python 3.9, 3.10, 3.11, 3.12  
✅ Windows: Python 3.9, 3.10, 3.11, 3.12
✅ Code formatting (black)
✅ Linting (flake8)
✅ Package building
```

**3. Release Branch Creation (1 minute)**
```
✅ Branch: release/v0.1.0 created
✅ Audit trail established
```

**4. TestPyPI Deployment (3 minutes)**
```
✅ Package built successfully
✅ Uploaded to TestPyPI
✅ Version 0.1.0 available at test.pypi.org
```

**5. Production PyPI Deployment (5 minutes)**
```
✅ Condition check: is_prerelease == 'false' ✓
✅ Package uploaded to PyPI
✅ Version 0.1.0 live at pypi.org/project/solarwindpy/
✅ Production deployment successful
```

**6. GitHub Release Creation (2 minutes)**
```
✅ Release created: https://github.com/[repo]/releases/tag/v0.1.0
✅ Release notes populated
✅ Assets attached (if configured)
```

**7. Conda-Forge Integration (2 minutes)**
```
✅ Issue created in conda-forge/solarwindpy-feedstock
✅ Automatic PR process initiated
✅ Community package update triggered
```

### Task 6.3: Validate Production PyPI Deployment (10 minutes)
**Verification Steps:**

**Check PyPI Package Page:**
1. Visit: https://pypi.org/project/solarwindpy/
2. Confirm v0.1.0 is latest version
3. Verify metadata, description, and links
4. Check download statistics

**Test Production Installation:**
```bash
# Create fresh test environment
conda create -n prod-test python=3.12 -y
conda activate prod-test

# Install from production PyPI (should work without --index-url)
pip install solarwindpy==0.1.0

# Verify installation
python -c "import solarwindpy; print(f'Production version: {solarwindpy.__version__}')"
# Expected: Production version: 0.1.0

# Test core functionality
python -c "
import solarwindpy as swp
from solarwindpy.core import Plasma, Ion
print('Production release functional test passed')
"

# Cleanup
conda deactivate
conda env remove -n prod-test
```

### Task 6.4: Verify GitHub Release (5 minutes)
**Release Validation:**
1. Navigate to repository releases page
2. Confirm v0.1.0 release created
3. Verify release notes content
4. Check asset attachments (if applicable)
5. Validate release permalink functionality

**Expected GitHub Release Content:**
- **Tag**: v0.1.0
- **Title**: SolarWindPy v0.1.0 - First Stable Release
- **Body**: Generated from tag message or template
- **Assets**: Source code archives (auto-generated)
- **Status**: Published (not draft)

### Task 6.5: Monitor Conda-Forge Process (5 minutes)
**Community Package Tracking:**

**Check Conda-Forge Issue:**
1. Visit conda-forge/solarwindpy-feedstock repository
2. Look for new issue titled "Update solarwindpy to v0.1.0"
3. Verify issue contains PyPI link
4. Monitor for community maintainer response

**Expected Timeline:**
- **Immediate**: Issue created automatically
- **1-7 days**: Maintainer creates update PR
- **3-14 days**: PR reviewed and merged
- **Post-merge**: Package available via `conda install solarwindpy`

## Success Validation Matrix

| Component | Expected Behavior | Validation Method |
|-----------|------------------|------------------|
| Tag Detection | is_prerelease=false | GitHub Actions logs |
| Quality Checks | All 12 jobs pass | Actions status page |
| TestPyPI | v0.1.0 deployed | test.pypi.org/project/solarwindpy |
| PyPI | v0.1.0 deployed | pypi.org/project/solarwindpy |
| GitHub Release | Release created | github.com/[repo]/releases |
| Conda-Forge | Issue opened | conda-forge/solarwindpy-feedstock |
| Installation | pip install works | Clean environment test |

## Acceptance Criteria

### Pipeline Execution ✅
- [ ] v0.1.0 tag triggers workflow successfully
- [ ] Production release detected correctly
- [ ] All quality checks pass
- [ ] Release branch created: release/v0.1.0

### Deployment Success ✅
- [ ] TestPyPI deployment completes
- [ ] PyPI production deployment completes
- [ ] GitHub Release created with correct content
- [ ] Conda-forge issue opened automatically

### Validation Confirmation ✅
- [ ] Package installable from PyPI without index-url
- [ ] Version reports as 0.1.0 (no rc suffix)
- [ ] Core functionality works in clean environment
- [ ] GitHub Release accessible and complete
- [ ] Community package process initiated

## Risk Mitigation

### Deployment Failures
- **TestPyPI First**: Validates packaging before production
- **Conditional Logic**: Production deployment only after TestPyPI success
- **Rollback Plan**: Can delete PyPI release if critical issues found
- **Manual Fallback**: twine upload available as backup

### Quality Issues
- **Comprehensive Testing**: 12-job matrix validates cross-platform
- **RC Validation**: v0.1.0-rc5 testing provided confidence
- **Immediate Verification**: Post-deployment installation testing

### Community Impact
- **Stable Foundation**: Establishes v0.1.0 as baseline for future releases
- **Package Discovery**: PyPI listing enables community adoption
- **Documentation**: Release notes provide clear feature summary

## Troubleshooting

### Pipeline Failures
1. **Quality Checks Fail**: Review specific platform/Python issues
2. **TestPyPI Fails**: Check packaging configuration and secrets
3. **PyPI Fails**: Verify PYPI_API_TOKEN and no version conflicts
4. **GitHub Release Fails**: Check repository permissions and token scope

### Post-Deployment Issues
1. **Installation Problems**: Check dependency versions and conflicts
2. **Functionality Issues**: Review package contents and imports
3. **Metadata Problems**: Update setup.py/pyproject.toml and re-release

## Progress Tracking
- [ ] Task 6.1: v0.1.0 production tag created and pushed
- [ ] Task 6.2: Full pipeline execution monitored and validated
- [ ] Task 6.3: Production PyPI deployment verified
- [ ] Task 6.4: GitHub Release confirmed functional
- [ ] Task 6.5: Conda-forge process initiated
- [ ] All acceptance criteria met
- [ ] v0.1.0 stable release established
- [ ] Ready for Phase 7: Cleanup

## Time Estimate
**Total: 1 hour**
- Task 6.1: 10 minutes
- Task 6.2: 30 minutes
- Task 6.3: 10 minutes
- Task 6.4: 5 minutes
- Task 6.5: 5 minutes

## Milestone Achievement
This phase completes the primary objective: **SolarWindPy v0.1.0 successfully released to PyPI**

**Impact:**
- First stable release available to scientific community
- Complete CI/CD pipeline proven functional
- Foundation established for future releases
- Community adoption enabled through PyPI and conda-forge

## Notes
- This is the critical production deployment phase
- Success here validates the entire CI/CD redesign effort
- v0.1.0 becomes the stable baseline for all future development
- Community visibility significantly increased through PyPI listing
- Conda-forge integration enables broader scientific community access