# GitHub Workflows Documentation

## Overview

This repository uses a comprehensive set of GitHub Actions workflows to ensure code quality, security, and automated deployment. All workflows have been designed with safety, security, and maintainability in mind.

## Active Workflows

### 1. CI (ci.yml) ✅ CRITICAL
**Purpose**: Core continuous integration for code quality and testing  
**Triggers**: All pushes and PRs to any branch  
**Matrix Testing**: Python 3.8-3.12 on Ubuntu, macOS, Windows (15 combinations)  
**Required for Merge**: Yes (branch protection enabled)

**Features**:
- Matrix testing across multiple Python versions and operating systems
- Automatic system dependency installation (HDF5 libraries on Linux)
- Enhanced pytables installation with verbose debugging
- Dependency caching for faster builds
- Code linting with flake8
- Documentation linting with doc8
- Test execution with pytest and comprehensive HTML reporting
- Coverage reporting with multiple formats (HTML, XML, raw)
- Circular import validation
- Coverage upload to Codecov (when token available)
- Enhanced artifacts: test results for all matrix combinations (leverages unlimited public repo storage)
- JUnit XML output for external integrations

**Success Criteria**: All 15 matrix combinations must pass

**Recent Enhancements** (August 2025):
- ✅ Fixed deprecated upload-artifact@v3 → v4 (resolves workflow blocking)
- ✅ Added system dependency management for pytables (HDF5 libraries)
- ✅ Expanded Python support to include 3.12 (Ubuntu 24.04 default)
- ✅ Enhanced artifact management with comprehensive debugging data
- ✅ Leveraged unlimited public repository storage for extensive test artifacts

### 2. Security Scan (security.yml) ⚠️ SECURITY
**Purpose**: Automated security vulnerability scanning  
**Triggers**: All pushes, PRs, and weekly schedule (Monday)  
**Tools**: Bandit, Safety, pip-audit  
**Required for Merge**: No (advisory only)

**Features**:
- Bandit security scan for Python code vulnerabilities
- Safety check for dependency vulnerabilities (CVE database)
- pip-audit for additional dependency security scanning
- Enhanced security report artifacts (90-day retention)
- Multiple report formats (JSON for automation, text for humans)
- Organized report structure in `security-results/` directory
- Critical vulnerability detection with build failure
- Automatic system dependency installation for complete scans

**Success Criteria**: No high-severity vulnerabilities detected

### 3. Documentation (docs.yml) 📚 REQUIRED
**Purpose**: Build and deploy documentation  
**Triggers**: All pushes and PRs  
**Deployment**: GitHub Pages (master branch only)  
**Required for Merge**: Yes (build must succeed)

**Features**:
- Documentation build testing on all branches
- Deployment to GitHub Pages from master (Python 3.12)
- Automatic system dependency installation for complete builds
- Dependency caching for faster builds
- Link checking with sphinx-link-checker (non-blocking)
- Documentation coverage reporting with summary generation
- Enhanced artifact uploads: HTML docs, doctrees, coverage, linkcheck results
- Enhanced Sphinx options with warning detection
- 90-day artifact retention for historical analysis

**Success Criteria**: Documentation builds without errors

### 4. Publish to PyPI (publish.yml) 🚀 TAG-BASED
**Purpose**: Automated PyPI package deployment  
**Triggers**: Version tags (v*) and manual dispatch  
**Security**: Tag-based only (no auto-publishing)  
**Ready for**: PYPI_API_TOKEN (available in ~2 weeks)

**Features**:
- Tag format verification (v*.*.* pattern)
- Full test suite execution before publishing
- Package verification with twine
- TestPyPI deployment for release candidates (RC tags)
- Production PyPI deployment for stable releases
- GitHub release creation with artifacts
- Dry-run option for testing
- Continue-on-error for missing tokens

**Success Criteria**: Tests pass, package validates, tag format correct

### 5. Doctest Validation (doctest_validation.yml) 📚 VALIDATION
**Purpose**: Validate code examples in documentation  
**Triggers**: Master/plan pushes, PRs, weekly schedule  
**Environment**: Complex conda setup with caching  

**Features**:
- Custom Python scripts for doctest discovery and validation
- Multi-level caching for conda environment
- Detailed coverage reports for documentation examples
- Validates examples execute correctly
- Prevents shipping docs with broken examples

**Success Criteria**: All documentation examples execute without errors

### 6. Sync Requirements (sync-requirements.yml) 🔄 MAINTENANCE
**Purpose**: Synchronize requirements across multiple files  
**Triggers**: Changes to requirements-dev.txt, pyproject.toml, monthly schedule  
**Safety**: Creates PRs instead of direct commits  

**Features**:
- Dynamic conda environment naming with timestamps
- File validation with dry-run checks
- Pull request creation for review
- Pip dependency caching
- Manual trigger with custom suffixes
- Automatic labeling and branch cleanup

**Success Criteria**: Generated files validate successfully

### 7. Claude Code Review (claude.yml & claude-code-review.yml) 🤖 AI-ASSISTANCE
**Purpose**: AI-powered code analysis and review  
**Triggers**: @claude mentions in issues/PRs, automatic PR reviews  
**Integration**: Uses Claude AI for code analysis and suggestions  

**Features**:
- Responds to @claude mentions in issues and PR comments  
- Automatic review of all PRs with AI analysis
- Code quality suggestions and issue detection
- Read-only repository access for security

**Success Criteria**: AI provides helpful analysis without spam

### 8. Dependabot (dependabot.yml) 🤖 AUTOMATION
**Purpose**: Automated dependency updates  
**Schedule**: Weekly (Python), Monthly (GitHub Actions)  
**Limits**: 5 open PRs maximum  

**Features**:
- Grouped updates for related packages
- Automatic labeling and conventional commits
- Separate handling for development and documentation dependencies
- Pull request limits to prevent spam

**Management**: Review and merge Dependabot PRs regularly

### 9. Performance Benchmark (benchmark.yml) ⚡ MONITORING
**Purpose**: Performance regression detection  
**Triggers**: master/main pushes, PRs, manual  
**Alert Threshold**: 150% (50% slowdown)  

**Features**:
- pytest-benchmark integration with histogram generation
- Memory profiling with memory_profiler
- Enhanced benchmark artifacts: JSON data, histograms, storage database
- Historical performance tracking with 90-day retention
- Automated alerts on regressions (50% slowdown threshold)
- Non-blocking alerts (continue-on-error)
- Automatic system dependency installation (Python 3.12)

**Success Criteria**: No significant performance regressions


## Public Repository Benefits

SolarWindPy benefits from being a **public repository** on GitHub, which provides:

### Unlimited Resources
- ✅ **Unlimited GitHub Actions minutes** on standard runners
- ✅ **Unlimited artifact storage** (leveraged for comprehensive debugging)
- ✅ **Parallel job execution** without cost constraints (15 CI matrix combinations)
- ✅ **90-day maximum artifact retention** for all workflows

### Enhanced Capabilities
- **Comprehensive Testing**: Full matrix testing across 5 Python versions × 3 operating systems
- **Rich Artifacts**: Test results, coverage data, security reports, documentation for all runs
- **Historical Analysis**: 90-day retention enables trend analysis and regression tracking
- **Debugging Support**: Extensive artifacts for troubleshooting failures across all environments

### Cost Optimization Strategy
Since resources are unlimited for public repositories, workflows are optimized for:
- **Quality over efficiency**: Comprehensive testing rather than minimal coverage
- **Debugging support**: Rich artifact generation for thorough analysis
- **Historical tracking**: Long retention periods for trend analysis
- **Developer experience**: Fast feedback through parallel execution

## Required Repository Secrets

### Essential (for PyPI deployment - available in ~2 weeks)
- `PYPI_API_TOKEN`: Production PyPI uploads
- `TEST_PYPI_API_TOKEN`: Test PyPI uploads (recommended)

### Optional (for enhanced features)
- `CODECOV_TOKEN`: Coverage reporting integration
- `PERSONAL_ACCESS_TOKEN`: For workflows creating PRs (can use GITHUB_TOKEN)

## Workflow Dependencies

```mermaid
graph LR
    A[Code Push] --> B[CI]
    A --> C[Security Scan]
    A --> D[Documentation]
    E[Tag Push] --> F[Publish to PyPI]
    G[Manual Release] --> H[Release Management]
    H --> E
    I[Requirements Change] --> J[Sync Requirements]
    K[Weekly/Monthly] --> L[Dependabot]
    K --> C
```

## Branch Protection Rules

When branch protection is enabled for master:

1. **Required Status Checks**:
   - CI (ubuntu-latest, 3.12)
   - CI (ubuntu-latest, 3.8)
   - Documentation / build
   - Security Scan / security

2. **Required Reviews**: 1 approving review
3. **Other Rules**: Dismiss stale reviews, no force pushes

## Success Metrics

### Daily Monitoring
- ✅ All CI builds passing across matrix
- ✅ No high-severity security vulnerabilities
- ✅ Documentation builds successfully
- ✅ No performance regressions detected

### Weekly Monitoring
- Review Dependabot PRs for dependency updates
- Check security scan results for new vulnerabilities
- Monitor performance benchmark trends

### Monthly Monitoring
- Review workflow effectiveness and performance
- Update documentation as needed
- Audit security reports and address issues

## Troubleshooting Guide

### Common Issues

#### CI Failures
1. **Matrix job failures**: Check specific OS/Python combination logs
2. **Dependency issues**: Clear cache, check requirements-dev.txt
3. **Test failures**: Run tests locally, check for platform-specific issues
4. **pytables installation failures**: 
   - **Error**: "Failed building wheel for tables" or "HDF5 library not found"
   - **Solution**: Workflow automatically installs `libhdf5-dev pkg-config` on Linux
   - **Local fix**: `sudo apt-get install libhdf5-dev pkg-config` (Ubuntu/Debian)
5. **Deprecated action warnings**:
   - **Error**: "This request has been automatically failed because it uses a deprecated version"
   - **Solution**: All workflows updated to use actions/upload-artifact@v4 (August 2025)

#### Security Scan Failures
1. **High severity issues**: Review Bandit report, address vulnerabilities
2. **Dependency vulnerabilities**: Update affected packages via Dependabot
3. **False positives**: Configure Bandit to ignore specific issues

#### Documentation Build Failures
1. **Sphinx errors**: Check SPHINXOPTS configuration, fix warnings
2. **Missing dependencies**: Verify docs/requirements.txt is current
3. **Link check failures**: Fix broken links or add to ignore list

#### Publish Workflow Issues
1. **Tag format errors**: Ensure tags match v*.*.* pattern
2. **Missing tokens**: Configure PYPI_API_TOKEN when available
3. **Test failures**: Fix issues before tagging

#### setuptools_scm Version Detection Issues
1. **Invalid version errors**: Check for non-semantic tags interfering with version detection
   - **Error**: `InvalidVersion: Invalid version: '20pct'`
   - **Cause**: Operational tags (like `compaction-*`) conflict with version tags
   - **Solution**: Use namespaced operational tags (`claude/compaction/*`)
2. **Build failures**: setuptools_scm configured to only recognize `v*` tags
   - Check `pyproject.toml` has proper `[tool.setuptools_scm]` configuration
   - Verify no conflicting tags exist with `git tag --list`
3. **Tag namespace separation**:
   - **Release tags**: `v1.0.0`, `v2.1.3-alpha` (for PyPI releases)
   - **Operational tags**: `claude/compaction/2025-08-19-20pct` (for session state)

### Recovery Procedures

#### Rollback Failed Release
```bash
# Remove problematic tag
git tag -d v1.0.0
git push origin :v1.0.0

# Create corrected tag
git tag v1.0.1
git push origin v1.0.1
```

#### Reset Branch Protection
Configure branch protection rules manually via GitHub repository Settings → Branches.

#### Emergency Disable Workflow
Rename workflow file (add .disabled extension) and commit to temporarily disable.

## Performance Optimization

### Caching Strategy
- Pip dependencies cached by requirements file hash
- Documentation dependencies cached separately
- Cache keys include OS and Python version for matrix builds

### Build Time Optimization
- Parallel matrix execution with fail-fast: false
- Conditional steps based on specific criteria
- Artifact reuse between jobs where possible

### Resource Management
- Artifact retention policies (7-90 days based on importance)
- Continue-on-error for non-critical steps
- Timeout limits to prevent stuck workflows

## Maintenance Schedule

### Weekly Tasks
- Review Dependabot PRs and merge approved updates
- Check security scan results and address high-priority issues
- Monitor performance benchmarks for trends

### Monthly Tasks
- Review workflow run statistics and performance
- Update workflow documentation
- Audit security reports comprehensively
- Review and update dependency management strategy

### Quarterly Tasks
- Comprehensive workflow effectiveness review
- Update Python version matrix if needed
- Review and update security scanning tools
- Evaluate new GitHub Actions features

## Integration with Development Workflow

### Pull Request Process
1. Create feature branch
2. Push changes → triggers CI, Security, Docs workflows
3. Create PR → triggers same workflows plus additional validation
4. Address any workflow failures
5. Request review (required by branch protection)
6. Merge after approval and passing checks

### Release Process
1. Use Release Management workflow to prepare release
2. Review generated changelog and release branch
3. Merge release branch to master
4. Tag automatically triggers PyPI deployment
5. Monitor deployment success and GitHub release creation

### Hotfix Process
1. Create hotfix branch from master
2. Apply fix and test with CI workflow
3. Use Release Management for patch version
4. Deploy via standard tag-based process

This comprehensive workflow system ensures code quality, security, and reliable deployment while maintaining developer productivity and project maintainability.