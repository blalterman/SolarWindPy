# Requirements Management Consolidation & Documentation Completion Plan (DRAFT)

## Plan Metadata
- **Plan Name**: Requirements Management Consolidation & Documentation Completion
- **Created**: 2025-08-09
- **Branch**: plan/requirements-management-consolidation (future)
- **Implementation Branch**: feature/requirements-management-consolidation (future)
- **Estimated Duration**: 7-9 hours (with complexity buffers)
- **Status**: Planned (Draft)
- **Planning Methodology**: PlanManager-Streamlined

## 🎯 Objective
Consolidate SolarWindPy's requirements management into a unified single-source-of-truth system with automatic synchronization, complete the 90% finished documentation validation, and resolve discovered CI/CD workflow inconsistencies.

## 🧠 Context
**Current State Analysis:**
- **Fragmented Requirements**: Three manually-maintained files (requirements.txt, requirements-dev.txt, docs/requirements.txt) causing consistency issues
- **Workflow Inefficiencies**: Redundant installations (requirements.txt + requirements-dev.txt) and inconsistent doc8 patterns
- **90% Complete Task**: Documentation validation needs final Sphinx installation and testing
- **Discovery Issues**: CI workflow has proper doc8 ignore patterns, but documentation workflows lack them

**Strategic Value:**
- Eliminates manual synchronization overhead (estimated 2h/month saved)
- Prevents environment inconsistencies that cause CI failures
- Enables automatic dependency validation and security scanning
- Provides foundation for future automated dependency updates

## 🔧 Technical Requirements
- **Frameworks**: Existing conda/pip ecosystem, GitHub Actions, Sphinx documentation
- **Constraints**: Must maintain backward compatibility with existing conda environment workflow
- **Dependencies**: sphinx, sphinx_rtd_theme, doc8, existing scripts/requirements_to_conda_env.py

## 📂 Affected Areas
- `requirements-dev.txt` → Primary source of truth
- `requirements.txt` → Auto-generated frozen dependencies  
- `docs/requirements.txt` → Auto-generated documentation subset
- `*.yml` → Conda environment files (auto-updated)
- `.github/workflows/` → CI/CD pipeline optimizations
- `scripts/` → New generation scripts
- `claude_session_state.md` → Final task completion

## 📋 Implementation Plan

### Phase 1: Documentation Validation Completion (Est: 1.5-2h)
**Domain Specialist: DocumentationMaintainer**
- [ ] **Install Sphinx Dependencies** (Est: 30-45min) - Use conda install for sphinx packages in current environment
  - Commit: `<checksum>`
  - Status: Pending
  - Dependencies: Current solarwindpy-20250404 environment
- [ ] **Fix doc8 Ignore Patterns** (Est: 45-60min) - Standardize doc8 commands across all workflows with proper ignore patterns  
  - Commit: `<checksum>`
  - Status: Pending
  - Dependencies: CI workflow analysis
- [ ] **Test Documentation Build** (Est: 30-45min) - Validate `make html` with no errors/warnings
  - Commit: `<checksum>`
  - Status: Pending
  - Dependencies: Sphinx installation, ignore patterns

### Phase 2: Requirements Consolidation (Est: 3-4h)
**Domain Specialist: DependencyManager**
- [ ] **Audit & Consolidate requirements-dev.txt** (Est: 60-90min) - Add missing Sphinx deps, analyze current requirements.txt for missing dev tools
  - Commit: `<checksum>`
  - Status: Pending
  - Complexity: Medium (requires careful dependency analysis)
- [ ] **Create docs requirements generator** (Est: 45-60min) - Script to extract documentation-only dependencies from requirements-dev.txt
  - Commit: `<checksum>`
  - Status: Pending
  - Output: `scripts/generate_docs_requirements.py`
- [ ] **Create requirements freezer** (Est: 60-75min) - Script using pip freeze to generate locked requirements.txt from requirements-dev.txt
  - Commit: `<checksum>`
  - Status: Pending  
  - Output: `scripts/freeze_requirements.py`
- [ ] **Update conda environment** (Est: 30-45min) - Regenerate conda yml using existing requirements_to_conda_env.py
  - Commit: `<checksum>`
  - Status: Pending
  - Dependencies: Updated requirements-dev.txt

### Phase 3: Workflow Automation & Optimization (Est: 2.5-3h)
**Domain Specialists: DependencyManager + TestEngineer**
- [ ] **Create requirements sync workflow** (Est: 90-120min) - GitHub Actions workflow to auto-generate derived files when requirements-dev.txt changes
  - Commit: `<checksum>`
  - Status: Pending
  - Output: `.github/workflows/sync-requirements.yml`
  - Features: Auto-commit generated files, create PR for review
- [ ] **Optimize CI workflows** (Est: 60-90min) - Remove redundant installations, use appropriate requirements file per context
  - Commit: `<checksum>`
  - Status: Pending
  - Targets: ci.yml, publish.yml, doc-build.yml, deploy-docs.yml
- [ ] **Complete session state** (Est: 15-30min) - Update claude_session_state.md to mark 100% completion
  - Commit: `<checksum>`
  - Status: Pending

## ✅ Acceptance Criteria
- [ ] **Single Source of Truth**: requirements-dev.txt contains all development dependencies as primary source
- [ ] **Automatic Synchronization**: Changes to requirements-dev.txt trigger auto-generation of all derivative files
- [ ] **Documentation Success**: `make html` completes without errors or warnings
- [ ] **Workflow Optimization**: No redundant requirements installations in CI/CD pipelines
- [ ] **Consistency**: All workflows use standardized doc8 ignore patterns
- [ ] **Validation**: All tests pass (`pytest -q`) and code quality checks succeed (`black .`, `flake8`)
- [ ] **Environment Compatibility**: Generated conda environment creates successfully and contains all required dependencies
- [ ] **Session Completion**: claude_session_state.md reflects 100% task completion

## 🧪 Testing Strategy
- **Unit Testing**: Validate generation scripts produce correct output
- **Integration Testing**: Test complete workflow from requirements-dev.txt change → auto-generation → environment creation
- **Documentation Testing**: Ensure doc build succeeds in both local and CI environments  
- **Regression Testing**: Verify existing development workflows remain functional

## 📊 Progress Tracking

### Overall Status
- **Phases Completed**: 0/3
- **Tasks Completed**: 0/10
- **Time Invested**: 0h of 7-9h estimated
- **Last Updated**: 2025-08-09

### Time Estimation Intelligence
- **Historical Calibration**: Sphinx installation typically 30-60min, script development 45-90min
- **Complexity Buffers**: 25% buffer added for cross-system coordination challenges
- **Risk Factors**: Potential conda/pip conflicts, CI workflow interactions

## 💬 Strategic Considerations
**Cross-Plan Coordination:** This plan establishes infrastructure that will benefit future dependency management and CI/CD optimization initiatives.

**Domain Specialist Integration:**
- DocumentationMaintainer: Ensures documentation quality standards maintained
- DependencyManager: Provides expertise on conda/pip ecosystem compatibility
- TestEngineer: Validates that workflow changes don't break testing infrastructure

**Error Recovery:** Plan includes rollback mechanisms for each phase to maintain system stability if issues arise during implementation.

## 🔄 Implementation Activation

### To Activate This Plan:
1. **Create plan branch**: `git checkout -b plan/requirements-management-consolidation`
2. **Move this file**: Rename to `requirements-management-consolidation.md` (remove `-draft`)
3. **Create implementation branch**: `git checkout -b feature/requirements-management-consolidation`  
4. **Use Plan Implementer**: Coordinate with research-optimized Plan Implementer agent
5. **Track progress**: Update checksums as tasks complete

### Current Baseline State:
- requirements.txt: 91 pinned packages (appears to be pip freeze output)
- requirements-dev.txt: 18 unpinned direct dependencies (missing sphinx)
- docs/requirements.txt: 6 documentation packages
- Existing script: requirements_to_conda_env.py (functional)
- CI workflows: Inconsistent doc8 patterns and redundant installations

---
*This draft plan was created using PlanManager-Streamlined methodology and can be activated using the plan-per-branch architecture when ready for implementation.*