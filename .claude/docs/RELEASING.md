# SolarWindPy Release Process

This document outlines the standardized process for creating SolarWindPy releases. Following these steps ensures consistent, automated releases with minimal manual intervention.

## Overview

SolarWindPy uses a highly automated release pipeline:
- **Version Management**: Git tags via `scripts/bump_version.py`
- **PyPI Publishing**: GitHub Actions workflow (`.github/workflows/publish.yml`)
- **Conda-forge Distribution**: Automated via regro-cf-autotick-bot
- **Documentation**: ReadTheDocs auto-builds on tag push
- **DOI**: Zenodo creates version DOI automatically

**Time Investment**: ~30-60 minutes active work (excluding monitoring periods)

**Related Documentation**:
- [MAINTENANCE.md](./MAINTENANCE.md) - Conda feedstock scripts, troubleshooting
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Code quality standards, testing requirements
- [PLANNING.md](./PLANNING.md) - GitHub Issues workflow for development planning

## Semantic Versioning

SolarWindPy follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** (x.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.x.0): New functionality, backward-compatible
- **PATCH** (0.0.x): Bug fixes, backward-compatible

**Pre-1.0.0 Special Rules**:
- Breaking changes increment MINOR (e.g., Python version requirement: v0.1.5 → v0.2.0)
- New features increment MINOR
- Bug fixes increment PATCH

## Pre-Release Checklist

### 1. Run Pre-Release Validation

```bash
# Check release readiness (9 automated checks)
python scripts/check_release_ready.py

# Run full test suite
pytest -v

# Check code quality (production code only)
flake8 solarwindpy/

# Apply code formatting if needed
black solarwindpy/ tests/
```

**Expected Results**:
- ✅ All tests pass
- ✅ No flake8 warnings in `solarwindpy/` (production code)
- ⚠️ Test code warnings acceptable (tracked separately via GitHub Issues)
- ✅ Coverage ≥95% (see [DEVELOPMENT.md](./DEVELOPMENT.md#testing-automated--testengineer-agent))

### 2. Update CHANGELOG.md

Add new version section between `[Unreleased]` and previous version following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features or capabilities

### Changed
- Changes to existing functionality
- **BREAKING**: Clearly mark breaking changes

### Fixed
- Bug fixes

### Removed
- Deprecated features removed

[X.Y.Z]: https://github.com/blalterman/SolarWindPy/compare/vX.Y.Z-1...vX.Y.Z
```

**Breaking Change Template**:
```markdown
### Changed
- **BREAKING**: [Description of breaking change]
  - [Migration guidance]
  - [Rationale for change]
  - [Performance/compatibility benefits]
```

**Example** (v0.2.0):
```markdown
### Changed
- **BREAKING**: Minimum Python version raised from 3.10 to 3.11
  - Aligns with scientific Python ecosystem (NumPy 2.x, Astropy 7.x require Python 3.11+)
  - Python 3.10 reaches end-of-life in October 2026
  - Enables Python 3.11+ performance improvements (10-60% faster in many workloads)
```

### 3. Commit CHANGELOG Updates

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): prepare vX.Y.Z release notes"
git push origin master
```

**Commit Message Format**: Follow [Conventional Commits](https://www.conventionalcommits.org/) as specified in [DEVELOPMENT.md](./DEVELOPMENT.md#git-workflow-automated-via-hooks).

### 4. Clean Working Directory

The release tag creation requires a clean git working directory:

```bash
# Check status
git status

# If untracked files exist, either:
# a) Add to .gitignore (preferred for temporary directories)
# b) Commit them
# c) Remove them

# Example: Add tmp/ to .gitignore
echo "tmp/" >> .gitignore
git add .gitignore
git commit -m "chore: add tmp/ to .gitignore"
git push origin master
```

## Release Execution

### 5. Create Version Tag

```bash
# Preview version bump (dry run)
python scripts/bump_version.py [major|minor|patch] --dry-run

# Create and push tag
python scripts/bump_version.py [major|minor|patch]
git push origin vX.Y.Z
```

**Example Output**:
```
Current version: v0.1.5
New version: v0.2.0
✅ Created tag: v0.2.0
```

**Tag Naming**: Tags must follow `vX.Y.Z` format (with 'v' prefix). See [MAINTENANCE.md](./MAINTENANCE.md#git-tag-management) for tag management guidelines.

### 6. Monitor GitHub Actions Workflow

The tag push automatically triggers `.github/workflows/publish.yml`:

```bash
# Watch workflow in real-time
gh run watch

# Alternative: View in browser
gh run list --limit 1
# Click URL in output
```

**Workflow Jobs**:
1. **build-and-publish** (~2-5 minutes):
   - Tag validation
   - Full test suite execution
   - Package build (source + wheel)
   - PyPI publication (via Trusted Publisher)
   - GitHub Release creation

2. **update-conda-feedstock** (~10-30 seconds):
   - Wait for PyPI availability
   - Calculate package SHA256
   - Create tracking issue

**Success Criteria**:
- ✅ Both jobs complete successfully
- ✅ PyPI shows new version (https://pypi.org/project/solarwindpy/)
- ✅ GitHub Release created (https://github.com/blalterman/SolarWindPy/releases)
- ✅ Tracking issue created for conda-forge update

## Post-Release Validation

### 7. Verify PyPI Publication

```bash
# Check PyPI metadata
curl -s https://pypi.org/pypi/solarwindpy/json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Version: {data['info']['version']}\")
print(f\"Python: {data['info']['requires_python']}\")
print(f\"Classifiers: {', '.join([c for c in data['info']['classifiers'] if 'Programming Language :: Python :: 3' in c])}\")"
```

**Expected Output**:
```
Version: X.Y.Z
Python: <4,>=3.11
Classifiers: Python :: 3.11, Python :: 3.12, Python :: 3.13
```

### 8. Enhance GitHub Release Notes (Optional)

For breaking changes, add migration guidance to GitHub Release:

```bash
# View current release
gh release view vX.Y.Z

# Edit release notes
gh release edit vX.Y.Z --notes-file tmp/enhanced-release-notes.md
```

**Breaking Change Release Template**:
```markdown
## 🚀 SolarWindPy Release vX.Y.Z

### ⚠️ BREAKING CHANGE: [Short Description]

**Migration Guide:**
- [Step-by-step migration instructions]
- [Environment setup commands]
- [Version upgrade commands]

**Why this change?**
- [Dependency alignment rationale]
- [End-of-life timeline]
- [Performance/compatibility benefits]

### Changes
- See [CHANGELOG](https://github.com/blalterman/SolarWindPy/blob/master/CHANGELOG.md#XYZ) for full details

### Installation
```bash
pip install --upgrade solarwindpy
```

### Documentation
https://solarwindpy.readthedocs.io/en/vX.Y.Z/
```

### 9. Monitor Automated Systems

**ReadTheDocs** (5-10 minutes):
- Builds triggered automatically by tag push
- Check: https://readthedocs.org/projects/solarwindpy/builds/
- Verify: https://solarwindpy.readthedocs.io/en/vX.Y.Z/

**Zenodo DOI** (1-24 hours):
- DOI created automatically via GitHub-Zenodo integration
- Check: https://zenodo.org/search?q=solarwindpy&sort=mostrecent

**PyPI Badges** (immediate):
- Version badge auto-updates: https://img.shields.io/pypi/v/solarwindpy
- Python version badge: https://img.shields.io/pypi/pyversions/solarwindpy

## Conda-forge Distribution

### Understanding the Autotick Bot

SolarWindPy uses the **regro-cf-autotick-bot** for automated conda-forge updates:

**How It Works**:
1. Bot monitors PyPI for new releases (checks every 2-6 hours)
2. Automatically creates PR in `conda-forge/solarwindpy-feedstock`
3. Updates version, SHA256, and dependencies
4. Runs CI checks across platforms
5. Auto-merges if CI passes (or waits for manual review)

**Bot Limitations**:
- **3 PR Limit**: Bot stops creating PRs when ≥3 open version update PRs exist
- **Solution**: Close outdated/duplicate PRs to unblock automation

**Related Scripts**: See [MAINTENANCE.md](./MAINTENANCE.md#conda-feedstock-automation) for `update_conda_feedstock.py` and `wait_for_pypi.py` usage.

### 10. Monitor Conda-forge Bot PR

The workflow creates a tracking issue (e.g., #403) with automation status.

**Automated Monitoring (Recommended)**:

Use the monitoring script for real-time status updates:

```bash
# Run automated monitor with tracking issue number
.claude/scripts/monitor-conda-release.sh 403

# The script provides:
# - Time elapsed since release
# - Bot PR creation status
# - CI check results
# - Contextual next steps
# - Exit codes: 0 (merged), 1 (waiting), 2 (action needed)

# Re-run periodically to check progress
# Typical workflow: Run every 30-60 minutes until PR appears
```

**Manual Monitoring (Alternative)**:

```bash
# Check for new PRs (bot typically creates within 2-6 hours)
gh pr list --repo conda-forge/solarwindpy-feedstock --state open

# Once PR appears, monitor CI checks
gh pr checks <PR_NUMBER> --repo conda-forge/solarwindpy-feedstock --watch
```

**When Bot PR Appears**:
1. **Verify PR Content**:
   - Version matches release
   - SHA256 matches tracking issue
   - Dependencies updated correctly

2. **Monitor CI** (15-30 minutes):
   - Linux (x86_64, aarch64, ppc64le)
   - macOS (x86_64, arm64)
   - Windows (x86_64)

3. **Review/Merge**:
   - If CI passes: Bot may auto-merge, or add comment `@conda-forge-admin, please rerender` to trigger
   - If CI fails: Investigate failures, may need manual feedstock PR

4. **Close Related Issues**:
   - Update tracking issue with PR link
   - Close any related feedstock issues resolved by update

### 11. Verify Conda Package Availability

After PR merge (2-4 hours for package build):

```bash
# Create test environment
conda create -n test-solarwindpy-release python=3.11 -y
conda activate test-solarwindpy-release

# Install from conda-forge
conda install -c conda-forge solarwindpy

# Verify version
python -c "import solarwindpy; print(solarwindpy.__version__)"

# Cleanup
conda deactivate
conda env remove -n test-solarwindpy-release
```

**Environment Setup**: See [DEVELOPMENT.md](./DEVELOPMENT.md#environment-setup) for detailed environment configuration.

## Rollback Procedures

### If PyPI Publish Fails

**Before GitHub Actions Completes**:
```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push origin :refs/tags/vX.Y.Z

# Fix issue, retry
```

**After GitHub Actions Completes**:
- PyPI uploads cannot be deleted, only "yanked"
- Create new patch release (vX.Y.Z+1) with fixes

### If Conda-forge PR Has Issues

**Option 1: Wait for next release** (preferred for minor issues)
- Bot will create new PR for next version
- Previous PR can be closed

**Option 2: Manual feedstock PR** (for critical issues):
1. Fork `conda-forge/solarwindpy-feedstock`
2. Create branch with fixes
3. Submit PR following conda-forge conventions
4. Reference original bot PR and tracking issue

## Common Issues

### Issue: Git Index Lock During Commits

**Symptom**: `fatal: Unable to create '.git/index.lock': File exists`

**Fix**:
```bash
# Wait briefly, retry
sleep 3 && git add <files> && git commit -m "..." && git push origin master
```

**Additional Troubleshooting**: See [MAINTENANCE.md](./MAINTENANCE.md#troubleshooting) for more git-related issues.

### Issue: bump_version.py Fails on Dirty Working Directory

**Symptom**: `Working directory has uncommitted changes`

**Fix**:
```bash
# Check what's untracked
git status

# Add to .gitignore or commit
echo "tmp/" >> .gitignore
git add .gitignore
git commit -m "chore: add tmp/ to .gitignore"
```

### Issue: Flake8 Warnings in Tests

**Symptom**: `check_release_ready.py` reports flake8 warnings

**Decision**:
- Production code (`solarwindpy/`) must be clean
- Test code warnings acceptable (CI only checks production)
- Create tracking issue for test code cleanup

**Rationale**: Publish workflow runs `flake8 solarwindpy/` (not `flake8 tests/`)

**Code Quality Standards**: See [DEVELOPMENT.md](./DEVELOPMENT.md#code-quality-standards) for comprehensive linting and formatting requirements.

### Issue: Conda-forge Bot Not Creating PR

**Check 1: Verify bot is unblocked**
```bash
# Count open version update PRs
gh pr list --repo conda-forge/solarwindpy-feedstock --state open | grep -i update

# If ≥3 PRs: Close outdated/duplicate PRs
gh pr close <PR_NUMBER> --repo conda-forge/solarwindpy-feedstock --comment "Closing to unblock autotick bot"
```

**Check 2: Wait longer**
- Bot checks every 2-6 hours
- May take up to 12 hours in rare cases

**Check 3: Manual feedstock PR**
- Last resort if bot fails after 24 hours
- Follow conda-forge contributing guide

## Timeline Summary

| Phase | Duration | Active/Passive |
|-------|----------|----------------|
| Pre-release checks | 15-30 min | Active |
| Tag creation & push | 2-5 min | Active |
| GitHub Actions workflow | 2-5 min | Passive (monitor) |
| PyPI validation | 5 min | Active |
| GitHub Release enhancement | 5-10 min | Active (if breaking) |
| ReadTheDocs build | 5-10 min | Passive (monitor) |
| Conda-forge bot PR creation | 2-6 hours | Passive (monitor) |
| Conda-forge CI checks | 15-30 min | Passive (monitor) |
| Conda package availability | 2-4 hours | Passive (verify) |

**Total Active Time**: ~30-60 minutes
**Total Elapsed Time**: ~8-12 hours (including monitoring)

## Automation Leverage

**Manual Steps** (~5-10 minutes):
1. Update CHANGELOG.md
2. Create version tag
3. Enhance GitHub Release notes (breaking changes only)
4. Monitor/review conda-forge bot PR

**Automated Steps** (~98% of process):
- Testing and validation
- Package building
- PyPI publishing
- GitHub Release creation
- Tracking issue creation
- Conda-forge PR creation
- CI testing across platforms
- Documentation builds
- DOI creation
- Badge updates

## Release Checklist

Use this checklist for each release:

### Pre-Release
- [ ] All tests passing locally (`pytest -v`)
- [ ] Production code linting clean (`flake8 solarwindpy/`)
- [ ] Coverage ≥95% ([DEVELOPMENT.md](./DEVELOPMENT.md#testing-automated--testengineer-agent))
- [ ] CHANGELOG.md updated with version section
- [ ] CHANGELOG committed and pushed
- [ ] Working directory clean (no untracked files)

### Release
- [ ] Version tag created (`python scripts/bump_version.py [major|minor|patch]`)
- [ ] Tag pushed to remote (`git push origin vX.Y.Z`)
- [ ] GitHub Actions workflow completed successfully
- [ ] PyPI shows new version
- [ ] GitHub Release created

### Post-Release
- [ ] PyPI metadata verified (version, Python requirement)
- [ ] GitHub Release notes enhanced (if breaking change)
- [ ] ReadTheDocs build successful
- [ ] Conda-forge tracking issue created
- [ ] Run monitoring script: `.claude/scripts/monitor-conda-release.sh <issue_number>`
- [ ] Conda-forge bot PR appeared (within 2-6 hours)
- [ ] Conda-forge CI passed
- [ ] Conda-forge PR merged
- [ ] Conda package available (`conda install -c conda-forge solarwindpy`)

### Cleanup
- [ ] Related feedstock issues closed
- [ ] Tracking issue updated and closed
- [ ] User communication sent (if breaking change)
- [ ] This document updated (if process changed)

## Reference

- **Scripts**: `scripts/bump_version.py`, `scripts/check_release_ready.py`, `.claude/scripts/monitor-conda-release.sh`
- **Workflows**: `.github/workflows/publish.yml`
- **Feedstock**: https://github.com/conda-forge/solarwindpy-feedstock
- **PyPI**: https://pypi.org/project/solarwindpy/
- **ReadTheDocs**: https://readthedocs.org/projects/solarwindpy/
- **Changelog Format**: https://keepachangelog.com/en/1.0.0/
- **Semantic Versioning**: https://semver.org/spec/v2.0.0.html
- **Conda-forge Docs**: https://conda-forge.org/docs/maintainer/updating_pkgs.html

## Questions?

For issues or questions about the release process:
1. Check this document first
2. Review [MAINTENANCE.md](./MAINTENANCE.md) for script usage and troubleshooting
3. Consult previous release tracking issues
4. Review GitHub Actions workflow logs
5. Ask in conda-forge Gitter channel (for feedstock issues)

---

**Last Updated**: 2025-11-12 (v0.2.0 release)
