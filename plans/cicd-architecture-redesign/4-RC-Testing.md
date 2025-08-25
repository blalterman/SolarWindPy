# Phase 4: Release Candidate Testing

## Overview
Test the new CI/CD workflows using v0.1.0-rc5 release candidate to validate tag detection, deployment gates, and TestPyPI integration before production deployment.

## Objectives
- Commit new workflows to master branch
- Create and test v0.1.0-rc5 release candidate
- Verify RC-specific deployment behavior
- Validate TestPyPI deployment process
- Confirm production gates remain closed
- Document any issues for resolution

## Tasks

### Task 4.1: Commit New Workflows (15 minutes)
**Implementation Steps:**
```bash
# Ensure workflows are ready
ls -la .github/workflows/
# Should show: release-pipeline.yml, continuous-integration.yml

# Add and commit new workflows
git add .github/workflows/release-pipeline.yml
git add .github/workflows/continuous-integration.yml
git commit -m "feat: add new CI/CD workflows with RC support

- release-pipeline.yml: Progressive deployment with RC detection
- continuous-integration.yml: Lightweight PR validation  
- Bypasses GitHub cache corruption in legacy workflows
- Enables v0.1.0 release to PyPI"

# Push to master
git push origin master
```

### Task 4.2: Create v0.1.0-rc5 Tag (10 minutes)
**Implementation Steps:**
```bash
# Ensure on master with latest changes
git checkout master
git pull origin master

# Create release candidate tag
git tag -a v0.1.0-rc5 -m "Release candidate 5 for SolarWindPy v0.1.0

- Test new CI/CD workflows
- Validate TestPyPI deployment
- Verify RC-specific behavior"

# Push tag to trigger workflow
git push origin v0.1.0-rc5
```

### Task 4.3: Monitor Workflow Execution (20 minutes)
**Verification Checklist:**

**GitHub Actions Monitoring:**
1. Navigate to repository Actions tab
2. Verify `release-pipeline` workflow triggered
3. Monitor job progression:
   - Tag detection identifies RC correctly
   - Quality checks run across full matrix
   - Release branch created
   - TestPyPI deployment executes
   - Production deployments skip

**Expected Workflow Behavior:**
```
✅ Tag Detection: "Release candidate detected: v0.1.0-rc5"
✅ Quality Checks: 12 jobs (3 OS × 4 Python versions)
✅ Release Branch: Creates "release/v0.1.0-rc5"
✅ TestPyPI: Package deployment succeeds
❌ PyPI: Skipped (RC detected)
❌ Conda: Skipped (RC detected)  
❌ GitHub Release: Skipped (RC detected)
```

### Task 4.4: Validate Release Branch Creation (5 minutes)
**Verification Steps:**
```bash
# Check if release branch was created
git fetch origin
git branch -r | grep release/v0.1.0-rc5

# Should return: origin/release/v0.1.0-rc5

# Inspect branch content
git checkout release/v0.1.0-rc5
git log --oneline -3
# Should show recent commits leading to RC tag
```

### Task 4.5: Verify TestPyPI Deployment (10 minutes)
**Validation Steps:**
1. **Check TestPyPI Package Page:**
   - Visit: https://test.pypi.org/project/solarwindpy/
   - Confirm v0.1.0rc5 appears in version history
   - Verify metadata and description

2. **Test Installation:**
```bash
# Create clean test environment
conda create -n test-rc python=3.12 -y
conda activate test-rc

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            solarwindpy==0.1.0rc5

# Verify installation
python -c "import solarwindpy; print(solarwindpy.__version__)"
# Expected output: 0.1.0rc5

# Cleanup
conda deactivate
conda env remove -n test-rc
```

## Success Validation

### Must Succeed ✅
- [ ] Workflows commit successfully to master
- [ ] v0.1.0-rc5 tag creation triggers workflow
- [ ] Version detection identifies as release candidate
- [ ] Quality checks pass across all platforms
- [ ] Release branch `release/v0.1.0-rc5` created
- [ ] TestPyPI deployment completes successfully
- [ ] Package installable from TestPyPI
- [ ] Version number reports correctly (0.1.0rc5)

### Must Skip ⚠️
- [ ] PyPI deployment skipped (conditional logic works)
- [ ] Conda-forge issue creation skipped
- [ ] GitHub Release creation skipped
- [ ] No production environment changes

## Acceptance Criteria
- [ ] New workflows operational without GitHub cache issues
- [ ] RC detection logic working correctly
- [ ] TestPyPI deployment pipeline functional
- [ ] Production deployment gates properly closed
- [ ] Release branch audit trail created
- [ ] Package installation validates successfully
- [ ] Ready for production release testing

## Risk Mitigation
- **Workflow Monitoring**: Real-time observation of execution
- **Branch Protection**: Release branches preserve state for debugging
- **TestPyPI Safety**: No impact on production PyPI
- **Version Validation**: Confirm correct RC number format
- **Installation Testing**: Verify package functionality

## Troubleshooting

### If Workflow Fails to Trigger
- Check tag format matches `v*` pattern
- Verify tag pushed to correct repository
- Review GitHub Actions permissions

### If Quality Checks Fail
- Review test matrix configuration
- Check for platform-specific issues
- Validate conda environment setup

### If TestPyPI Deployment Fails
- Verify TEST_PYPI_API_TOKEN secret configured
- Check package build process
- Review upload permissions

## Progress Tracking
- [ ] Task 4.1: New workflows committed to master
- [ ] Task 4.2: v0.1.0-rc5 tag created and pushed
- [ ] Task 4.3: Workflow execution monitored and validated
- [ ] Task 4.4: Release branch creation confirmed
- [ ] Task 4.5: TestPyPI deployment verified
- [ ] All success criteria met
- [ ] Ready for Phase 5: TestPyPI Validation

## Time Estimate
**Total: 1 hour**
- Task 4.1: 15 minutes
- Task 4.2: 10 minutes  
- Task 4.3: 20 minutes
- Task 4.4: 5 minutes
- Task 4.5: 10 minutes

## Notes
- This phase proves the new workflow architecture works
- RC testing provides safe validation before production
- TestPyPI deployment confirms packaging process
- Release branch creation establishes audit trail
- Success here enables confident v0.1.0 production release