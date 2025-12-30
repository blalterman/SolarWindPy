# Conda Feedstock Update Automation

This document describes the automated conda-forge feedstock update system for SolarWindPy, which streamlines the process of publishing new releases to the conda-forge ecosystem.

## Overview

The conda feedstock automation system automatically handles the initial steps of updating the conda-forge feedstock when new PyPI releases are published. It provides:

- **Automated PyPI availability checking** with exponential backoff
- **SHA256 calculation** from PyPI source distributions
- **GitHub issue tracking** for each feedstock update
- **Release candidate filtering** to only process stable releases
- **Integration with existing GitHub Actions** publish workflow

## Architecture

```
GitHub Release (v*) → PyPI Publish → Wait for PyPI → Calculate SHA256 → Create Tracking Issue
                                         ↓
                                  Manual Steps:
                                  Fork → Update → PR → Review → Merge
```

### Components

1. **`scripts/wait_for_pypi.py`** - PyPI availability checker
2. **`scripts/update_conda_feedstock.py`** - Main automation orchestrator
3. **`scripts/conda_config.py`** - Configuration and constants
4. **`.github/workflows/publish.yml`** - GitHub Actions integration

## Automated Features

### PyPI Availability Checking

The system waits for new releases to become available on PyPI before proceeding:

```bash
python scripts/wait_for_pypi.py v0.1.5 --timeout 600 --interval 30
```

**Features:**
- Exponential backoff with configurable intervals
- Version format validation
- Release candidate detection and filtering
- Timeout handling with clear error messages

### SHA256 Calculation

Automatically downloads and calculates SHA256 hashes for conda recipe updates:

```python
# Automatically downloads from PyPI and calculates hash
sha256_hash = updater.calculate_sha256("0.1.5")
print(sha256_hash)  # e.g., "7b13d799d0c1399ec13e653632065f03a524cb57eeb8e2a0e2a41dab54897dfe"
```

### GitHub Issue Tracking

Creates structured tracking issues with:
- PyPI release verification
- SHA256 hash for reference
- Manual step checklist
- Links to relevant resources
- Automation status updates

## GitHub Actions Integration

The automation is integrated into the existing publish workflow as a separate job:

```yaml
update-conda-feedstock:
  needs: build-and-publish
  runs-on: ubuntu-latest
  # Only for stable releases (no RC, beta, alpha)
  if: |
    github.event_name == 'push' && 
    startsWith(github.ref, 'refs/tags/v') && 
    !contains(github.ref, 'rc')
```

### Workflow Steps

1. **Wait for PyPI availability** (up to 10 minutes)
2. **Calculate SHA256** hash from PyPI source
3. **Create GitHub tracking issue** with all details
4. **Generate workflow summary** with next steps

## Manual Steps (Still Required)

The automation handles the initial preparation, but conda-forge updates still require manual steps:

### 1. Fork and Clone Feedstock

```bash
gh repo fork conda-forge/solarwindpy-feedstock --clone
cd solarwindpy-feedstock
```

### 2. Update Recipe

```bash
# Create update branch
git checkout -b update-0.1.5

# Edit recipe/meta.yaml:
# - Update {% set version = "0.1.5" %}
# - Update sha256: [hash from tracking issue]
```

### 3. Create Pull Request

```bash
git add recipe/meta.yaml
git commit -m "Update solarwindpy to v0.1.5"
git push origin update-0.1.5
gh pr create --title "Update solarwindpy to v0.1.5" --body "Update to latest PyPI release"
```

### 4. Monitor and Merge

- Wait for conda-forge bot checks to pass
- Address any linting issues if they arise
- Merge when approved by conda-forge maintainers

## Autotick Bot Limitations and Dependency Management

### Understanding the regro-cf-autotick-bot

The **regro-cf-autotick-bot** provides **partial automation**:

| Task | Automated? | Notes |
|------|-----------|-------|
| Version detection | ✅ Yes | Monitors PyPI every 2-6 hours |
| SHA256 calculation | ✅ Yes | Downloads source and computes hash |
| PR creation | ✅ Yes | Creates update PR automatically |
| CI triggering | ✅ Yes | Azure Pipelines runs tests |
| **Dependency updates** | ❌ **NO** | **Requires manual intervention** |
| Test updates | ❌ No | Only if imports change |
| Build number reset | ✅ Yes | Resets to 0 for new version |

### Why Manual Dependency Updates Are Necessary

**Root Cause:** The bot uses a simple regex-based approach:
1. Detects new version on PyPI
2. Downloads source tarball
3. Calculates SHA256
4. Updates `{% set version = "X.Y.Z" %}` and `sha256:` fields
5. Creates PR

**What it doesn't do:**
- Parse `pyproject.toml`, `setup.py`, or `requirements.txt`
- Detect dependency version changes
- Update `requirements.run` section
- Validate dependency compatibility

**Consequence:** Feedstock can drift from upstream requirements, causing build failures.

### Our Automated Detection System

SolarWindPy implements automated dependency drift detection:

#### 1. Automatic Comparison in Tracking Issues

When a release is created, the tracking issue **automatically includes a dependency comparison table**:

```
================================================================================
DEPENDENCY COMPARISON
================================================================================

pyproject.toml                           | feedstock meta.yaml
-----------------------------------------+-----------------------------------------
⚠️ numpy>=1.26,<3.0                       | numpy >=1.22,<2.0
⚠️ scipy>=1.13                            | scipy >=1.10
⚠️ pandas>=2.0                            | pandas >=1.5
  ...
================================================================================
```

- **⚠️ Different** - Version constraints changed
- **➕ Added** - New dependency in pyproject.toml
- **➖ Removed** - Dependency only in feedstock

#### 2. Manual Comparison Tool

Check alignment anytime:

```bash
# Quick visual comparison
python scripts/compare_feedstock_deps.py
```

Output shows side-by-side comparison with markers indicating changes.

### Manual Dependency Update Workflow

When the tracking issue shows dependency changes:

#### Step 1: Wait for Bot PR

Bot typically creates PR within 2-6 hours of PyPI release:

```bash
gh pr list --repo conda-forge/solarwindpy-feedstock --state open
```

#### Step 2: Review Dependency Changes

1. Open the tracking issue created during release
2. Review the dependency comparison table
3. Note all ⚠️ markers indicating changes
4. Verify version compatibility (especially NumPy ecosystem changes)

#### Step 3: Update Feedstock

```bash
# Checkout bot's PR branch
gh pr checkout <PR_NUMBER> --repo conda-forge/solarwindpy-feedstock

# Edit recipe/meta.yaml requirements.run section
# Update changed dependencies from comparison table

# Commit changes
git add recipe/meta.yaml
git commit -m "Update runtime dependencies

Align with pyproject.toml changes from upstream release.
See tracking issue for full dependency diff."

# Push to bot's branch
git push
```

#### Step 4: Monitor CI

```bash
gh pr checks <PR_NUMBER> --repo conda-forge/solarwindpy-feedstock --watch
```

CI runs for all platforms (~15-30 minutes).

#### Step 5: Merge

```bash
# When CI passes
gh pr merge <PR_NUMBER> --squash
```

### Common Scenarios

#### Scenario A: No Dependency Changes

- Tracking issue shows "No changes detected"
- Bot PR is complete as-is
- Proceed directly to CI monitoring

#### Scenario B: Minor Version Bumps

- Changes like `scipy >=1.10 → >=1.13`
- Low risk - usually backward compatible
- Update feedstock and verify CI passes

#### Scenario C: Major Ecosystem Updates

Example: NumPy 2.0 migration (v0.3.0):
- Multiple dependencies updated for NumPy 2.0 compatibility
- `numpy >=1.22,<2.0 → >=1.26,<3.0`
- Requires careful review of downstream compatibility
- May need extended testing before merge

#### Scenario D: Package Name Differences

Conda uses different names for some packages:
- `matplotlib` → `matplotlib-base`
- `astropy` → `astropy-base`

These appear as ➕/➖ in comparison table - update manually with `-base` suffix.

### Timeline Expectations

| Stage | Duration | Notes |
|-------|----------|-------|
| PyPI publish | Instant | Triggered by tag push |
| Bot detection | 2-6 hours | Depends on bot schedule |
| Bot PR creation | 5-10 min | After detection |
| **Manual update** | **5-15 min** | **If deps changed** |
| CI checks | 15-30 min | Platform builds |
| Merge to availability | 10 min | Package distribution |
| **Total (no deps)** | **3-7 hours** | Fully automated |
| **Total (with deps)** | **3-7 hours** | +15 min manual work |

### Troubleshooting Dependency Updates

**Problem:** CI fails with "nothing provides numpy >=1.26"

**Cause:** Dependency not yet available on conda-forge

**Solution:**
1. Check `conda-forge/numpy-feedstock` for version availability
2. Wait for dependency to be released on conda-forge
3. Or adjust constraint to currently available version

---

**Problem:** Comparison table shows unexpected changes

**Cause:** Parsing differences (spacing, package name normalization)

**Solution:**
1. Manually review `pyproject.toml`
2. Verify changes make sense
3. Update feedstock accordingly

---

**Problem:** Bot PR already has correct dependencies

**Cause:** Another maintainer already updated the PR

**Solution:**
1. Verify changes match tracking issue
2. Proceed to CI monitoring
3. No action needed

## Configuration

The system is configured via `scripts/conda_config.py`:

```python
# Timeout settings (seconds)
TIMEOUTS = {
    'pypi_check': 10,           # PyPI API requests
    'download': 60,             # Package downloads
    'pypi_availability': 300,   # Wait for PyPI (5 minutes)
}

# Automation settings
AUTOMATION_CONFIG = {
    'enabled_for_prereleases': False,   # Skip RC versions
    'create_tracking_issues': True,     # Create GitHub issues
}
```

### Environment Variables

- `CONDA_AUTOMATION_TIMEOUT`: Override default timeouts
- `CONDA_AUTOMATION_DRY_RUN`: Set default dry run mode
- `CONDA_AUTOMATION_DEBUG`: Enable debug logging
- `GITHUB_TOKEN`: Required for GitHub API operations

## Usage Examples

### Command Line Usage

```bash
# Dry run (recommended for testing)
python scripts/update_conda_feedstock.py v0.1.5 --dry-run

# Full automation
python scripts/update_conda_feedstock.py v0.1.5

# Check PyPI availability only
python scripts/wait_for_pypi.py v0.1.5 --timeout 300

# Custom package (if extending to other packages)
python scripts/update_conda_feedstock.py 0.2.0 --package mypackage
```

### GitHub Actions (Automatic)

```bash
# Create and push a release tag
git tag v0.1.5
git push origin v0.1.5

# GitHub Actions will automatically:
# 1. Build and publish to PyPI
# 2. Wait for PyPI availability
# 3. Calculate SHA256
# 4. Create tracking issue
```

## Release Types and Filtering

### Processed Releases (Stable)

✅ `v1.0.0` - Major release  
✅ `v0.1.5` - Minor/patch release  
✅ `v2.3.1` - Standard semantic version  

### Skipped Releases (Pre-releases)

❌ `v1.0.0rc1` - Release candidate  
❌ `v0.2.0beta1` - Beta release  
❌ `v1.0.0alpha1` - Alpha release  
❌ `v0.1.5dev1` - Development release  

Pre-releases are automatically filtered out to prevent conda-forge updates for unstable versions.

## Error Handling and Troubleshooting

### Common Issues

#### PyPI Availability Timeout

```
❌ Timeout: solarwindpy v0.1.5 not available after 300s
```

**Solution:** Check PyPI status and manual verification:
```bash
curl -s https://pypi.org/pypi/solarwindpy/0.1.5/json | jq '.info.version'
```

#### GitHub API Authentication

```
❌ Failed to create GitHub issue: authentication required
```

**Solution:** Ensure GitHub CLI is authenticated:
```bash
gh auth login
# or set GITHUB_TOKEN environment variable
```

#### SHA256 Calculation Failure

```
❌ Failed to calculate SHA256: HTTP 404
```

**Solution:** Verify PyPI URL and package availability:
```bash
curl -I https://pypi.org/packages/source/s/solarwindpy/solarwindpy-0.1.5.tar.gz
```

### Recovery Procedures

#### Manual SHA256 Calculation

```bash
VERSION=0.1.5
wget https://pypi.org/packages/source/s/solarwindpy/solarwindpy-${VERSION}.tar.gz
sha256sum solarwindpy-${VERSION}.tar.gz
```

#### Manual Issue Creation

```bash
# Create issue with basic template
gh issue create \
  --title "Manual conda feedstock update for v0.1.5" \
  --body "PyPI: v0.1.5, SHA256: [calculate manually]" \
  --label "conda-feedstock,automation"
```

## Monitoring and Maintenance

### GitHub Actions Monitoring

Monitor the `update-conda-feedstock` job in GitHub Actions:

1. Check workflow run status after tag pushes
2. Review job summaries for success/failure details
3. Examine logs for any error messages
4. Verify tracking issues are created correctly

### Periodic Maintenance

**Monthly:**
- Review successful automation runs
- Check for any failed updates requiring manual intervention
- Update dependencies if needed (`requests`, `packaging`, etc.)

**Quarterly:**
- Review and update timeout settings if needed
- Check conda-forge policy changes that might affect automation
- Test dry-run functionality with recent releases

### Metrics and Success Indicators

**Successful Automation:**
- ✅ PyPI availability confirmed within timeout
- ✅ SHA256 calculated successfully
- ✅ GitHub tracking issue created
- ✅ No manual intervention required for initial setup

**Performance Targets:**
- PyPI availability: < 5 minutes after tag push
- SHA256 calculation: < 30 seconds
- Issue creation: < 10 seconds
- End-to-end automation: < 10 minutes

## Future Enhancements

### Potential Improvements

1. **Full PR Automation** - Automatically create conda-forge PRs (requires more complex setup)
2. **Dependency Updates** - Automatically sync dependencies from `pyproject.toml`
3. **Multi-package Support** - Extend to other packages in the repository
4. **Slack/Email Notifications** - Alert maintainers of successful automation
5. **Advanced Retry Logic** - More sophisticated error recovery

### Implementation Considerations

- **Security**: Ensure GitHub tokens have minimal required permissions
- **Rate Limiting**: Respect PyPI and GitHub API rate limits
- **Testing**: Comprehensive test coverage for edge cases
- **Documentation**: Keep this document updated with any changes

## Security Considerations

### GitHub Token Permissions

The automation requires these GitHub permissions:
- `issues:write` - Create tracking issues
- `contents:read` - Access repository contents
- `metadata:read` - Basic repository access

### Safe Practices

- Never store credentials in code or configuration files
- Use environment variables for sensitive data
- Regularly rotate GitHub tokens if using personal access tokens
- Monitor automation logs for any unusual activity

### PyPI Security

- Always verify SHA256 hashes match PyPI source distributions
- Never skip hash validation in production automation
- Monitor PyPI package integrity and report any discrepancies

## Related Documentation

- [conda-forge Documentation](https://conda-forge.org/docs/maintainer/updating_pkgs.html)
- [SolarWindPy Release Process](../CLAUDE.md#git-workflow)
- [GitHub Actions Workflows](../.github/workflows/)
- [PyPI Publishing Workflow](../docs/pypi-publishing.md)

---

*This documentation is maintained as part of the SolarWindPy conda feedstock automation system.*
