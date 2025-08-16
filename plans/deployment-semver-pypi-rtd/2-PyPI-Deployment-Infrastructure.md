# Phase 2: PyPI Deployment Infrastructure

## Phase Metadata
- **Phase**: 2/4
- **Estimated Duration**: 2-3 hours
- **Dependencies**: Phase 1 (setuptools_scm configuration)
- **Status**: Not Started

## 🎯 Phase Objective
Enhance the existing PyPI publishing workflow with robust version validation, graceful token handling during the 10-day delay period, and comprehensive error reporting for production-ready automated deployment.

## 🧠 Phase Context
The current publish.yml workflow has basic functionality but needs enhancement for production deployment. Key improvements include using latest GitHub Actions versions, implementing strict version validation, and graceful degradation when PyPI tokens are unavailable during the 10-day delay period.

## 📋 Implementation Tasks

### Task Group 1: Workflow Foundation Updates
- [ ] **Update GitHub Actions to latest versions** (Est: 10 min) - Modernize action versions for security and features
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Update checkout@v3 to v4, setup-python to v5, use Python 3.12
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

- [ ] **Add fetch-depth: 0 for setuptools_scm** (Est: 5 min) - Ensure full git history for accurate version detection
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: setuptools_scm needs full history to determine version from tags
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

### Task Group 2: Version Validation Enhancement
- [ ] **Implement comprehensive version enforcement** (Est: 45 min) - Add strict semantic version validation with setuptools_scm integration
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Validate tag format, version consistency, and setuptools_scm compatibility
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

- [ ] **Add version mismatch detection** (Est: 20 min) - Ensure tag version matches setuptools_scm detected version
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Prevent deployment when tag and code versions don't align
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

### Task Group 3: Graceful Token Handling
- [ ] **Add PyPI token status checking** (Est: 25 min) - Implement informative error handling for missing tokens
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Provide clear guidance when tokens are unavailable during 10-day delay
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

- [ ] **Enhance error messaging for token failures** (Est: 15 min) - Add helpful warnings and next steps for token configuration
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Guide users through token setup process with actionable messages
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

### Task Group 4: Release Creation Enhancement
- [ ] **Improve GitHub release automation** (Est: 20 min) - Enhance release creation with better metadata and artifact handling
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include proper prerelease detection and release notes generation
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml`

### Task Group 5: Integration Testing
- [ ] **Test workflow with manual dispatch** (Est: 30 min) - Validate workflow functionality without requiring tags
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Use workflow_dispatch to test build and validation steps
  - Command: Test via GitHub Actions manual trigger

- [ ] **Validate error handling paths** (Est: 25 min) - Test graceful failures for various error conditions
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Verify informative error messages for token issues, validation failures
  - Command: Test with intentionally broken configurations

## ✅ Phase Acceptance Criteria
- [ ] GitHub Actions use latest secure versions (checkout@v4, setup-python@v5)
- [ ] setuptools_scm version detection works with full git history
- [ ] Semantic version validation rejects invalid tag formats
- [ ] Version mismatch detection prevents inconsistent deployments
- [ ] PyPI token failures provide clear, actionable error messages
- [ ] GitHub releases are created automatically for all valid tags
- [ ] Prerelease detection works correctly for RC/beta/alpha versions
- [ ] TestPyPI receives release candidates when tokens are available
- [ ] Production PyPI receives stable releases when tokens are available
- [ ] Workflow can be tested safely via manual dispatch
- [ ] All error conditions fail gracefully with helpful guidance

## 🧪 Phase Testing Strategy
**Unit Testing**: Individual workflow steps tested in isolation
**Integration Testing**: End-to-end workflow testing with various tag formats
**Validation Method**: GitHub Actions execution with both valid and invalid scenarios

### Specific Test Scenarios
1. **Valid Release Tag**: v0.1.0-rc1 → TestPyPI + GitHub Release
2. **Valid Stable Tag**: v0.1.0 → PyPI + GitHub Release (when tokens available)
3. **Invalid Tag Format**: fail-test → Workflow rejection with clear error
4. **Manual Dispatch**: Build-only testing without publishing
5. **Token Unavailable**: Graceful failure with actionable guidance

## 🔧 Phase Technical Requirements
**Dependencies**: setuptools_scm (from Phase 1), build, twine, packaging
**Environment**: Ubuntu-latest with Python 3.12 for GitHub Actions
**Constraints**: Must handle missing PyPI tokens gracefully for 10-day delay period
**Services**: GitHub Actions (unlimited), PyPI/TestPyPI (tokens pending)

## 📂 Phase Affected Areas
- `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/publish.yml` - Major workflow enhancements
- Package artifacts in `dist/` during workflow execution
- GitHub Releases at https://github.com/blalterman/SolarWindPy/releases
- PyPI/TestPyPI packages (when tokens become available)

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/8
- **Time Invested**: 0h of 2-3h estimated
- **Completion Percentage**: 0%
- **Last Updated**: 2025-08-16

### Blockers & Issues
- **PyPI Token Delay**: Expected 10-day delay for token availability (graceful degradation implemented)
- **Dependency**: Requires Phase 1 setuptools_scm configuration completion

### Next Actions
1. Complete Phase 1 setuptools_scm configuration
2. Update GitHub Actions versions and checkout configuration
3. Implement comprehensive version validation logic
4. Add graceful token handling with informative error messages
5. Test workflow with manual dispatch for validation

## 💬 Phase Implementation Notes

### Implementation Decisions
- **Action Versions**: Use latest stable versions for security and feature improvements
- **Python Version**: Standardize on 3.12 for consistency and latest features
- **Error Strategy**: continue-on-error for PyPI steps during token delay period
- **Release Strategy**: Automatic GitHub releases for all tags, PyPI only when tokens available
- **Validation Timing**: Pre-upload validation to catch errors early in workflow

### Rollback Strategy
**Workflow Rollback**: git revert to previous publish.yml version maintains existing functionality
**Incremental Updates**: Each task group can be individually reverted if issues arise
**Token Handling**: Graceful degradation means no functionality is lost during token delay
**Testing Safety**: Manual dispatch allows validation without affecting production systems
**Risk Level**: Medium - workflow changes affect deployment but include safety measures

### 10-Day Token Delay Mitigation
**Immediate Capabilities** (without tokens):
- Version validation and semantic version enforcement
- GitHub release creation with proper artifacts
- Workflow testing via manual dispatch
- Clear error messaging about token requirements

**Future Capabilities** (with tokens):
- Automated PyPI publishing for stable releases
- TestPyPI publishing for release candidates
- Complete hands-off deployment pipeline

### Phase Dependencies Resolution
- **Requires from Phase 1**: setuptools_scm configuration for version detection
- **Provides for Phase 3**: Release automation for documentation version triggers
- **Provides for Phase 4**: Foundation for release validation and helper scripts

---
*Phase 2 of 4 - SolarWindPy Deployment Pipeline - Last Updated: 2025-08-16*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*