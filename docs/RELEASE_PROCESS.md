# SolarWindPy Release Process

This document describes the complete release process for SolarWindPy, including preparation, execution, validation, and rollback procedures.

## Quick Release Checklist

```bash
# 1. Check release readiness
python scripts/check_release_ready.py

# 2. Create release tag
python scripts/bump_version.py [major|minor|patch|rc|beta|alpha]

# 3. Push tag to trigger deployment
git push origin <tag>

# 4. Monitor GitHub Actions
# Visit: https://github.com/blalterman/SolarWindPy/actions

# 5. Verify release
# Visit: https://github.com/blalterman/SolarWindPy/releases
```

## Detailed Release Process

### 1. Pre-Release Preparation

#### 1.1 Development Completion
- [ ] All features for the release are complete and merged
- [ ] All tests are passing
- [ ] Code quality checks pass (flake8, black)
- [ ] Documentation is up to date

#### 1.2 Release Readiness Validation
Run the release readiness checker to validate all prerequisites:

```bash
python scripts/check_release_ready.py --verbose
```

This script validates:
- **Git Status**: Working directory is clean (no uncommitted changes)
- **Branch**: On appropriate release branch (master/main)
- **Version Detection**: setuptools_scm can detect current version
- **Changelog**: CHANGELOG.md is properly formatted
- **Tests**: All tests pass
- **Code Quality**: No linting errors
- **Build System**: Package can be built
- **GitHub Access**: Repository is properly configured
- **PyPI Tokens**: Status check (informational during token delay)

#### 1.3 Changelog Update
Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/) format:

1. Move items from `[Unreleased]` to a new version section
2. Add release date
3. Ensure proper categorization (Added, Changed, Deprecated, Removed, Fixed, Security)

Example:
```markdown
## [Unreleased]

## [1.0.0] - 2025-08-20
### Added
- Initial release with semantic versioning
- Automated PyPI deployment pipeline
### Fixed
- Version detection with setuptools_scm
```

### 2. Version Management

#### 2.1 Semantic Versioning
SolarWindPy follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (X.Y.0): New functionality, backwards compatible
- **PATCH** (X.Y.Z): Bug fixes, backwards compatible
- **PRERELEASE** (X.Y.Z-rc1): Pre-release versions

#### 2.2 Version Bumping
Use the automated version bump script:

```bash
# Patch release (bug fixes)
python scripts/bump_version.py patch

# Minor release (new features)
python scripts/bump_version.py minor

# Major release (breaking changes)
python scripts/bump_version.py major

# Release candidate
python scripts/bump_version.py rc

# Beta release
python scripts/bump_version.py beta

# Alpha release
python scripts/bump_version.py alpha
```

#### 2.3 Dry Run Testing
Always test version bumps with dry-run first:

```bash
python scripts/bump_version.py patch --dry-run
```

### 3. Release Execution

#### 3.1 Tag Creation
The version bump script creates annotated git tags:

```bash
# Example: Create v1.0.0 tag
python scripts/bump_version.py major
# Creates tag with message: "Release v1.0.0"
```

#### 3.2 Tag Push and Deployment Trigger
Push the tag to trigger the automated deployment pipeline:

```bash
git push origin v1.0.0
```

This triggers the GitHub Actions workflow that:
1. Validates tag format (v*.*.* pattern)
2. Verifies version consistency with setuptools_scm
3. Runs complete test suite
4. Builds package (source + wheel)
5. Creates GitHub release with artifacts
6. Publishes to PyPI (when tokens available)

#### 3.3 Deployment Validation
Monitor the deployment process:

1. **GitHub Actions**: https://github.com/blalterman/SolarWindPy/actions
   - Check workflow execution
   - Verify all steps complete successfully
   - Review any error messages

2. **GitHub Releases**: https://github.com/blalterman/SolarWindPy/releases
   - Confirm release is created
   - Verify artifacts are attached (source + wheel)
   - Check release notes and metadata

3. **PyPI Status** (when tokens available):
   - **TestPyPI**: https://test.pypi.org/project/solarwindpy/ (for RC releases)
   - **Production PyPI**: https://pypi.org/project/solarwindpy/ (for stable releases)

### 4. Post-Release Validation

#### 4.1 Installation Testing
Test the released package:

```bash
# Create clean environment
conda create -n test-install python=3.12
conda activate test-install

# Install from PyPI (when available)
pip install solarwindpy==1.0.0

# Verify installation
python -c "import solarwindpy; print(solarwindpy.__version__)"
```

#### 4.2 Version Verification
Confirm setuptools_scm detects the correct version:

```bash
python -c "from setuptools_scm import get_version; print(get_version())"
# Should output: 1.0.0 (without 'dev' suffix)
```

### 5. Rollback Procedures

#### 5.1 Tag Rollback
If a release tag needs to be removed:

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag (if already pushed)
git push origin :v1.0.0

# OR use GitHub CLI
gh api -X DELETE repos/blalterman/SolarWindPy/git/refs/tags/v1.0.0
```

#### 5.2 GitHub Release Rollback
If a GitHub release needs to be removed:

```bash
# List releases
gh release list

# Delete release (keeps tag)
gh release delete v1.0.0

# OR delete release and tag
gh release delete v1.0.0 --cleanup-tag
```

#### 5.3 PyPI Rollback
**Important**: PyPI releases cannot be deleted, only yanked.

```bash
# Install twine if needed
pip install twine

# Yank release (makes it unavailable for new installs)
twine yank solarwindpy 1.0.0 --reason "Release yanked due to critical bug"
```

### 6. Troubleshooting

#### 6.1 Common Issues

**Version Detection Failed**
```bash
# Check setuptools_scm configuration
python -c "from setuptools_scm import get_version; print(get_version())"

# Verify git tags
git tag -l 'v*' --sort=-version:refname

# Check pyproject.toml configuration
grep -A 10 "\[tool.setuptools_scm\]" pyproject.toml
```

**Tag Format Rejected**
```bash
# Verify tag follows v*.*.* pattern
git tag -l 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+.*$'

# Check setuptools_scm tag regex
grep "tag_regex" pyproject.toml
```

**Tests Failing**
```bash
# Run tests with verbose output
pytest -v

# Run specific test modules
pytest tests/core/ -v

# Check code quality
flake8
black --check .
```

**Build Failures**
```bash
# Verify build dependencies
pip install build twine

# Test local build
python -m build

# Check package contents
tar -tzf dist/*.tar.gz | head -20
```

#### 6.2 GitHub Actions Debugging
If the deployment workflow fails:

1. Check workflow logs in GitHub Actions
2. Verify repository secrets are configured (for PyPI)
3. Check for rate limits or service outages
4. Validate tag format and permissions

#### 6.3 PyPI Token Issues
During the 10-day token delay period:

1. **Expected**: PyPI publishing fails gracefully
2. **Validation**: Check error messages provide setup guidance
3. **Workaround**: Manual upload with twine after token setup

```bash
# Manual PyPI upload (after token setup)
twine upload dist/*
```

### 7. Release Types and Timing

#### 7.1 Regular Releases
- **Patch releases**: Bug fixes, documentation updates
- **Minor releases**: New features, enhancements
- **Major releases**: Breaking changes, major milestones

#### 7.2 Pre-releases
- **Release Candidates (rc)**: Feature-complete, final testing
- **Beta releases**: Feature testing, API stabilization
- **Alpha releases**: Early feature previews

#### 7.3 Hotfix Releases
For critical bug fixes:

1. Create hotfix branch from release tag
2. Apply minimal fix
3. Use patch version bump
4. Fast-track release process

### 8. Release Communication

#### 8.1 Internal Communication
- Update CHANGELOG.md with all changes
- Document breaking changes prominently
- Include migration guides for major releases

#### 8.2 External Communication
- GitHub release notes are auto-generated
- Include installation instructions
- Link to documentation and examples

### 9. Automation Status

#### 9.1 Currently Automated
- ✅ Semantic version validation
- ✅ Tag format enforcement
- ✅ Test execution
- ✅ Package building
- ✅ GitHub release creation
- ✅ Release notes generation

#### 9.2 Requiring Manual Setup
- ⚠️ PyPI token configuration (10-day delay)
- ⚠️ TestPyPI token configuration (optional)

#### 9.3 Future Enhancements
- 🔄 Automated changelog generation
- 🔄 Release announcement automation
- 🔄 Documentation version updates

---

*Last updated: 2025-08-20*
*For questions or issues, see: https://github.com/blalterman/SolarWindPy/issues*