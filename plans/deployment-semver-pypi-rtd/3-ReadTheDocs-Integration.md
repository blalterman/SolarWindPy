# Phase 3: ReadTheDocs Integration

## Phase Metadata
- **Phase**: 3/4
- **Estimated Duration**: 2-3 hours
- **Dependencies**: Phase 1 (setuptools_scm), manual ReadTheDocs account setup
- **Status**: Not Started

## 🎯 Phase Objective
Implement comprehensive ReadTheDocs integration with versioned documentation, automated builds triggered by releases, and enhanced project metadata with proper badges and links for professional package presentation.

## 🧠 Phase Context
ReadTheDocs provides essential documentation hosting for scientific packages, allowing users to access version-specific documentation that matches their installed package version. This phase configures automatic documentation builds, multiple output formats, and integrates version detection from setuptools_scm.

## 📋 Implementation Tasks

### Task Group 1: ReadTheDocs Configuration Enhancement
- [ ] **Update .readthedocs.yaml with comprehensive build configuration** (Est: 30 min) - Enhance build process with multiple formats and version detection
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Add PDF/EPUB formats, improved build jobs, and setuptools_scm integration
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.readthedocs.yaml`

- [ ] **Configure documentation version detection** (Est: 15 min) - Ensure ReadTheDocs uses setuptools_scm for version information
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Add post_install job to display version information during builds
  - Files: `/Users/balterma/observatories/code/SolarWindPy/.readthedocs.yaml`

### Task Group 2: Project Metadata Enhancement
- [ ] **Update pyproject.toml URLs section** (Est: 10 min) - Add comprehensive project URLs including documentation links
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include homepage, documentation, changelog, and source URLs
  - Files: `/Users/balterma/observatories/code/SolarWindPy/pyproject.toml`

- [ ] **Update README.rst with comprehensive badges** (Est: 25 min) - Add professional badge collection for package status
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include PyPI, Conda, ReadTheDocs, build status, and version badges
  - Files: `/Users/balterma/observatories/code/SolarWindPy/README.rst`

### Task Group 3: Manual ReadTheDocs Setup
- [ ] **Create ReadTheDocs project account** (Est: 15 min) - Manual setup on readthedocs.org platform
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Import blalterman/SolarWindPy repository with proper configuration
  - Manual task: Access readthedocs.org dashboard

- [ ] **Configure ReadTheDocs project settings** (Est: 20 min) - Set project name, default branch, and build settings
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Configure solarwindpy project name, master branch, and versioning options
  - Manual task: ReadTheDocs admin panel configuration

### Task Group 4: Documentation Build Testing
- [ ] **Test local documentation build** (Est: 20 min) - Verify documentation builds correctly with new configuration
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Validate Sphinx configuration works with setuptools_scm version detection
  - Commands: `cd docs && make html`

- [ ] **Validate ReadTheDocs webhook integration** (Est: 15 min) - Ensure GitHub triggers ReadTheDocs builds on tag creation
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Test with development tag to verify automatic build triggering
  - Manual task: Check ReadTheDocs build logs

### Task Group 5: Integration Validation
- [ ] **Test version-specific documentation URLs** (Est: 15 min) - Verify versioned documentation accessibility
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Confirm URLs like solarwindpy.readthedocs.io/en/v0.1.0-rc1/ work correctly
  - Command: Test URL accessibility after builds

- [ ] **Validate badge functionality** (Est: 10 min) - Ensure all badges display correct status information
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Check PyPI, ReadTheDocs, and build status badges show accurate information
  - Command: View README.rst in GitHub to verify badge rendering

## ✅ Phase Acceptance Criteria
- [ ] .readthedocs.yaml builds documentation in multiple formats (HTML, PDF, EPUB)
- [ ] setuptools_scm version detection works in ReadTheDocs builds
- [ ] ReadTheDocs project successfully imports from GitHub repository
- [ ] Versioned documentation URLs are accessible (e.g., /en/v0.1.0-rc1/)
- [ ] GitHub webhook triggers ReadTheDocs builds on tag creation
- [ ] All badges in README.rst display correctly and show accurate status
- [ ] pyproject.toml URLs section includes comprehensive project links
- [ ] Documentation builds pass without critical warnings
- [ ] Local documentation build matches ReadTheDocs output
- [ ] Version information displays correctly in built documentation

## 🧪 Phase Testing Strategy
**Local Testing**: Documentation builds successfully in development environment
**Integration Testing**: ReadTheDocs builds triggered by GitHub tags and pushes
**Validation Method**: Manual verification of built documentation and automated badge checking

### Specific Test Cases
1. **Local Build**: `cd docs && make html` succeeds without errors
2. **Version Detection**: Documentation displays correct version from setuptools_scm
3. **ReadTheDocs Build**: Automatic build triggered by tag creation
4. **Multiple Formats**: PDF and EPUB generation alongside HTML
5. **Badge Accuracy**: All status badges reflect current repository state
6. **URL Accessibility**: Documentation URLs work for both latest and versioned docs

## 🔧 Phase Technical Requirements
**Dependencies**: setuptools_scm (Phase 1), Sphinx, existing docs infrastructure
**Environment**: ReadTheDocs build environment (Ubuntu 22.04, Python 3.11)
**Manual Requirements**: ReadTheDocs account access for project setup
**Constraints**: Documentation must build successfully before enabling strict warning failures

## 📂 Phase Affected Areas
- `/Users/balterma/observatories/code/SolarWindPy/.readthedocs.yaml` - Enhanced build configuration
- `/Users/balterma/observatories/code/SolarWindPy/pyproject.toml` - Updated URLs section
- `/Users/balterma/observatories/code/SolarWindPy/README.rst` - Professional badge collection
- ReadTheDocs project at https://readthedocs.org/projects/solarwindpy/
- Generated documentation at https://solarwindpy.readthedocs.io/

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/8
- **Time Invested**: 0h of 2-3h estimated
- **Completion Percentage**: 0%
- **Last Updated**: 2025-08-16

### Blockers & Issues
- **Manual Setup Required**: ReadTheDocs account and project configuration requires manual intervention
- **Dependency**: Requires Phase 1 setuptools_scm configuration for version detection

### Next Actions
1. Complete Phase 1 setuptools_scm configuration
2. Enhance .readthedocs.yaml with comprehensive build configuration
3. Update project metadata in pyproject.toml and README.rst
4. Perform manual ReadTheDocs project setup
5. Test documentation builds locally and on ReadTheDocs

## 💬 Phase Implementation Notes

### Implementation Decisions
- **Multiple Formats**: Enable PDF and EPUB for comprehensive documentation access
- **Version Integration**: Use setuptools_scm for consistent version information
- **Badge Strategy**: Comprehensive badge collection for professional package presentation
- **Build Safety**: Start with warnings allowed, enable strict mode after cleanup
- **Manual Setup**: ReadTheDocs requires manual account setup but automation handles builds

### Rollback Strategy
**Configuration Rollback**: .readthedocs.yaml changes are additive and can be easily reverted
**Metadata Rollback**: pyproject.toml and README.rst changes don't affect core functionality
**Documentation Safety**: Documentation failures don't impact package functionality
**ReadTheDocs Reset**: Project can be reconfigured or deleted/recreated if needed
**Risk Level**: Low - documentation changes are isolated from core package functionality

### Manual Setup Requirements
**ReadTheDocs Account Setup**:
1. Access https://readthedocs.org/dashboard/import/
2. Import blalterman/SolarWindPy repository
3. Configure project settings:
   - Name: solarwindpy
   - Default branch: master
   - Language: English
   - Programming Language: Python
4. Enable webhook integration for automatic builds
5. Configure versioning after first tag (set 'stable' to v0.1.0)

### Phase Dependencies Resolution
- **Requires from Phase 1**: setuptools_scm configuration for version detection in documentation
- **Provides for Phase 4**: Documentation infrastructure for release validation and user guidance
- **Manual Coordination**: ReadTheDocs setup enables documentation badges and professional presentation

---
*Phase 3 of 4 - SolarWindPy Deployment Pipeline - Last Updated: 2025-08-16*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*