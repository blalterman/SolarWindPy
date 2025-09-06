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
