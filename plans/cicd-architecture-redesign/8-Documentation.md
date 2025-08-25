# Phase 8: Documentation

## Overview
Update project documentation to reflect the new CI/CD architecture and create comprehensive release procedures for future SolarWindPy releases.

## Objectives
- Update CLAUDE.md with new workflow information
- Create RELEASE.md with deployment procedures
- Document version tag strategy
- Establish release management best practices
- Provide clear guidance for future releases

## Tasks

### Task 8.1: Update CLAUDE.md (15 minutes)
**Purpose**: Reflect new CI/CD architecture in development documentation

**Implementation Steps:**
```bash
# Open CLAUDE.md for editing
code CLAUDE.md
```

**Required Updates:**

**1. Git Workflow Section Updates:**
- Replace references to broken ci.yml and publish.yml
- Document new release-pipeline.yml and continuous-integration.yml
- Update workflow trigger descriptions

**2. New CI/CD Architecture Section:**
```markdown
### CI/CD Workflows (Updated for v0.1.0+)

#### release-pipeline.yml
- **Trigger**: Version tags (v*) on master branch
- **Purpose**: Production and RC deployments
- **Flow**: Tag Detection → Quality Checks → Release Branch → TestPyPI → [PyPI if not RC]
- **Features**: Progressive deployment, RC detection, audit trail

#### continuous-integration.yml
- **Trigger**: Pull requests and non-master branches
- **Purpose**: Lightweight PR validation
- **Flow**: Quick tests with Python 3.12 on Ubuntu
```

**3. Version Tag Strategy:**
```markdown
### Release Tag Strategy
- **Release Candidates** (`v*.*.*-rc*`): Deploy to TestPyPI only
- **Production Releases** (`v*.*.*`): Full pipeline - TestPyPI → PyPI → Conda
- **Examples**: v0.1.0-rc5 (TestPyPI only), v0.1.0 (full deployment)
```

**4. Update Quick Commands:**
```markdown
# Release Management:
.github/workflows/release-pipeline.yml    # Production deployment
.github/workflows/continuous-integration.yml # PR validation
git tag v0.2.0-rc1; git push origin v0.2.0-rc1  # RC release
git tag v0.2.0; git push origin v0.2.0           # Production release
```

### Task 8.2: Create RELEASE.md (10 minutes)
**Purpose**: Comprehensive release procedures for maintainers

**Implementation Steps:**
```bash
# Create new release documentation
touch RELEASE.md
```

**RELEASE.md Content Structure:**
```markdown
# SolarWindPy Release Procedures

## Overview
This document describes the complete release process for SolarWindPy using the automated CI/CD pipeline established with v0.1.0.

## Release Types

### Release Candidates (Testing)
**Pattern**: `v{major}.{minor}.{patch}-rc{number}`
**Examples**: `v0.2.0-rc1`, `v1.0.0-rc5`
**Deployment**: TestPyPI only
**Purpose**: Safe testing before production

### Production Releases (Stable)
**Pattern**: `v{major}.{minor}.{patch}`
**Examples**: `v0.2.0`, `v1.0.0`
**Deployment**: TestPyPI → PyPI → GitHub Release → Conda-forge
**Purpose**: Official stable releases

## Release Process

### Phase 1: Pre-Release Validation
1. Ensure all tests pass on master
2. Update version in setup.py/pyproject.toml
3. Update CHANGELOG.md with release notes
4. Commit version bump: `git commit -m "chore: bump version to v0.2.0"`

### Phase 2: Release Candidate Testing
1. Create RC tag: `git tag -a v0.2.0-rc1 -m "Release candidate for v0.2.0"`
2. Push tag: `git push origin v0.2.0-rc1`
3. Monitor workflow execution
4. Test installation from TestPyPI
5. Validate functionality

### Phase 3: Production Release
1. Create production tag: `git tag -a v0.2.0 -m "SolarWindPy v0.2.0 release"`
2. Push tag: `git push origin v0.2.0`
3. Monitor full pipeline deployment
4. Validate PyPI deployment
5. Confirm GitHub Release creation
6. Monitor conda-forge update

### Phase 4: Post-Release
1. Announce release to community
2. Update documentation links
3. Plan next development cycle

## Troubleshooting

### Common Issues
- **Workflow doesn't trigger**: Check tag format and repository permissions
- **Quality checks fail**: Review test matrix and platform-specific issues
- **PyPI upload fails**: Verify secrets configuration and version conflicts
- **Conda-forge not updating**: Check issue creation and feedstock status

### Emergency Procedures
- **Bad release deployed**: Delete PyPI release, create patch version
- **Workflow fails**: Use manual `twine upload` as fallback
- **Critical bug discovered**: Immediately create patch release

## Monitoring and Validation

### Release Pipeline Monitoring
1. GitHub Actions workflow execution
2. TestPyPI deployment verification
3. PyPI deployment confirmation
4. GitHub Release creation
5. Conda-forge issue tracking

### Installation Testing
```bash
# Test PyPI installation
pip install solarwindpy==x.y.z

# Test conda installation (after conda-forge update)
conda install -c conda-forge solarwindpy
```
```

### Task 8.3: Document Integration Points (5 minutes)
**Purpose**: Clarify how new workflows integrate with existing development

**Add to CLAUDE.md Development Workflow Section:**
```markdown
### CI/CD Integration
- **PRs**: Trigger continuous-integration.yml for validation
- **Tags**: Trigger release-pipeline.yml for deployment
- **Master**: Protected branch, requires PR approval
- **Release Branches**: Auto-created by release-pipeline for audit trail

### Branch Strategy
- `master`: Stable development branch
- `feature/*`: Development work (triggers CI on PRs)
- `plan/*`: Planning and tracking branches
- `release/*`: Auto-created for each version tag (audit trail)
```

## Documentation Validation

### Task 8.4: Review and Consistency Check (5 minutes)
**Validation Checklist:**

**CLAUDE.md Updates:**
- [ ] CI/CD section reflects new workflows
- [ ] Version tag strategy documented clearly
- [ ] Quick commands updated for new processes
- [ ] Integration with existing development workflow explained

**RELEASE.md Completeness:**
- [ ] Complete release process documented
- [ ] Both RC and production procedures covered
- [ ] Troubleshooting section included
- [ ] Monitoring and validation steps provided

**Consistency Check:**
- [ ] Version tag patterns match between documents
- [ ] Workflow names consistent across documentation
- [ ] Procedures align with actual CI/CD implementation
- [ ] Examples use realistic version numbers

## File Updates Summary

### CLAUDE.md Changes
- **Section**: CI/CD Workflows → Updated architecture description
- **Section**: Git Workflow → Updated with new workflow files
- **Section**: Quick Commands → Added release management commands
- **Section**: Development Workflow → Added CI/CD integration points

### New Files Created
- **RELEASE.md**: Complete release management procedures
- **Content**: Process documentation, troubleshooting, validation

## Acceptance Criteria

### Documentation Accuracy ✅
- [ ] CLAUDE.md reflects new CI/CD architecture
- [ ] Version tag strategy documented consistently
- [ ] Workflow triggers and purposes clearly explained
- [ ] Integration with development workflow clarified

### Release Procedures ✅
- [ ] RELEASE.md provides complete release guidance
- [ ] Both RC and production processes documented
- [ ] Troubleshooting and emergency procedures included
- [ ] Monitoring and validation steps detailed

### Consistency and Quality ✅
- [ ] Documentation internally consistent
- [ ] Matches actual CI/CD implementation
- [ ] Uses clear, actionable language
- [ ] Includes practical examples

## Risk Mitigation

### Documentation Accuracy
- **Implementation Review**: Cross-check against actual workflow files
- **Version Validation**: Ensure tag patterns match regex in workflows
- **Process Testing**: Validate procedures against v0.1.0 release experience

### Future Maintainability
- **Clear Procedures**: Step-by-step instructions for complex processes
- **Troubleshooting Guides**: Common issues and resolution steps
- **Integration Documentation**: How CI/CD fits with development workflow

## Progress Tracking
- [ ] Task 8.1: CLAUDE.md updated with new CI/CD architecture
- [ ] Task 8.2: RELEASE.md created with comprehensive procedures
- [ ] Task 8.3: Integration points documented clearly
- [ ] Task 8.4: Documentation reviewed for consistency and completeness
- [ ] All acceptance criteria met
- [ ] Documentation committed and pushed
- [ ] Ready for Phase 9: Closeout

## Time Estimate
**Total: 30 minutes**
- Task 8.1: 15 minutes
- Task 8.2: 10 minutes
- Task 8.3: 5 minutes
- Task 8.4: 5 minutes (overlapping review)

## Commit Message
```bash
git add CLAUDE.md RELEASE.md
git commit -m "docs: update CI/CD documentation for new workflow architecture

- CLAUDE.md: Updated with release-pipeline.yml and continuous-integration.yml
- RELEASE.md: Added comprehensive release management procedures
- Documented version tag strategy (RC vs production)
- Included troubleshooting and monitoring guidance
- Reflects successful v0.1.0 deployment architecture"
git push origin master
```

## Future Maintenance

### Regular Updates
- **Workflow Changes**: Update documentation when CI/CD changes
- **Process Improvements**: Incorporate lessons from future releases
- **Tool Updates**: Reflect changes in GitHub Actions or PyPI processes

### Version-Specific Updates
- **Major Releases**: May require procedure updates
- **Breaking Changes**: Update compatibility documentation
- **New Features**: Reflect in release process as needed

## Notes
- Documentation reflects the successful v0.1.0 release process
- Procedures are based on proven, working CI/CD implementation
- Both developer (CLAUDE.md) and maintainer (RELEASE.md) perspectives covered
- Future releases will benefit from clear, tested procedures
- Documentation enables consistent, reliable release management