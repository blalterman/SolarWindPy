# Plan to Fix Release Pipeline and Deploy v0.1.0-rc5

**Date**: 2025-09-01  
**Purpose**: Fix workflow permissions issue and successfully deploy v0.1.0-rc5 to TestPyPI  
**Status**: Step 1 Complete ✅

## Problem Analysis

The release pipeline failed with this error:
```
refusing to allow a GitHub App to create or update workflow 
`.github/workflows/ci.yml` without `workflows` permission
```

**Root Cause**: The GitHub Actions bot doesn't have permission to push branches that modify workflow files. When creating the release branch, it's trying to push a branch that contains workflow changes.

## Current Situation

- ✅ **Step 1 Complete**: Local and remote master are now synced with ci.yml fixes
- **Workflow permissions issue**: Can't push branches with workflow changes from Actions
- **Tag exists**: v0.1.0-rc5 already pushed but workflow failed

## Solution Plan

### ✅ Step 1: Sync Local with Remote Master (COMPLETE)
- Pull/merge completed to get the ci.yml fixes from remote
- Local master now has all necessary changes

### Step 2: Fix Release Pipeline Permissions (5 min)

**Option A: Skip Release Branch Creation** (Recommended - Simplest)
Comment out or remove the release branch creation step that's causing the permission issue.

Edit `.github/workflows/release-pipeline.yml`:
```yaml
# Comment out lines 53-58 that create and push release branch
# - name: Create release branch for audit trail
#   run: |
#     git config --global user.name 'GitHub Actions'
#     git config --global user.email 'actions@github.com'  
#     git checkout -b ${{ steps.version.outputs.release_branch }}
#     git push origin ${{ steps.version.outputs.release_branch }}
```

**Option B: Add Workflow Permissions** (More Complex)
Would require repository settings changes:
- Settings → Actions → General → Workflow permissions
- Select "Read and write permissions"
- Check "Allow GitHub Actions to create and approve pull requests"

### Step 3: Update and Re-tag (3 min)

```bash
# Delete the old tag locally and remotely
git tag -d v0.1.0-rc5
git push origin :refs/tags/v0.1.0-rc5

# Commit the workflow fix (if using Option A)
git add .github/workflows/release-pipeline.yml
git commit -m "fix: disable release branch creation to avoid workflow permission issues

Temporary workaround for GitHub Actions permission error.
The tag itself provides sufficient audit trail."

# Push to origin
git push origin master

# Re-create and push the tag
git tag -a v0.1.0-rc5 -m "Release candidate 5 for SolarWindPy v0.1.0

Testing new CI/CD workflows:
- Progressive deployment (TestPyPI → PyPI)
- RC detection logic
- Bypass GitHub cache issues"

git push origin v0.1.0-rc5
```

### Step 4: Monitor Workflow (10 min)

Visit GitHub Actions tab and verify:
- ✅ Workflow triggers on v0.1.0-rc5 tag
- ✅ Version detected as RC (is_rc=true)
- ✅ Quality checks pass on Python 3.10, 3.11, 3.12
- ✅ TestPyPI deployment succeeds
- ❌ PyPI deployment skipped (RC detection working)
- ❌ GitHub Release skipped (RC detection working)

### Step 5: Verify TestPyPI Deployment (5 min)

```bash
# Check package on TestPyPI
# Visit: https://test.pypi.org/project/solarwindpy/0.1.0rc5/

# Test installation
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            solarwindpy==0.1.0rc5

# Verify import
python -c "import solarwindpy as swp; print(f'SolarWindPy {swp.__version__}')"
```

## Alternative Quick Fix

If you want to test immediately without modifying the workflow:

**Grant workflow write permissions in GitHub Settings**:
1. Go to repository Settings
2. Actions → General
3. Under "Workflow permissions", select "Read and write permissions"
4. Save changes
5. Re-run the failed workflow from Actions tab

## Expected Outcome

- Release pipeline runs without permission errors
- v0.1.0-rc5 deploys to TestPyPI only
- Production gates remain closed (RC detection)
- Can proceed with production v0.1.0 release after validation

## Risk Assessment

- **Low risk**: Release branches are nice-to-have, not critical
- **Tag provides audit**: The git tag already marks the release point
- **Can add back later**: Once permissions are sorted, can re-enable release branches
- **No impact on deployment**: Core functionality remains intact

## Next Steps After Success

1. **Phase 5**: TestPyPI validation (30 min)
2. **Phase 6**: Production release v0.1.0 (1 hour)
3. **Phase 7**: Cleanup old workflows (30 min)
4. **Phase 8**: Documentation (30 min)

---
*This plan ensures v0.1.0-rc5 deploys successfully while maintaining CI/CD architecture integrity.*