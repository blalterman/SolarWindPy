# Phase 3: CLI Integration & Automation

## Phase Metadata
- **Phase**: 3/5
- **Estimated Duration**: 4-5 hours
- **Dependencies**: Phase 2 (PropositionsAwareMigrator)
- **Status**: Not Started

## 🎯 Phase Objective
Integrate PropositionsAwareMigrator with GitHub CLI (`gh`) scripts, replace Python-based `.claude/hooks/` with shell scripts, and create automated workflows for plan lifecycle management in GitHub Issues.

## 🧠 Phase Context
This phase transforms the manual migration tool into an automated workflow system. The existing `.claude/hooks/` Python scripts need replacement with `gh` CLI-based shell scripts that integrate seamlessly with GitHub Issues while preserving all validation and automation capabilities.

## 📋 Implementation Tasks

### Task Group 1: GitHub CLI Script Development
- [ ] **Create plan creation script** (Est: 45 min) - `gh-create-plan.sh` for new GitHub issue plans
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Interactive plan creation with propositions framework
- [ ] **Create plan status script** (Est: 30 min) - `gh-plan-status.sh` for cross-plan monitoring
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Dashboard generation using GitHub API and CLI
- [ ] **Create plan migration script** (Est: 40 min) - `gh-migrate-plans.sh` wrapper for PropositionsAwareMigrator
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Batch migration with progress reporting
- [ ] **Create plan completion script** (Est: 35 min) - `gh-complete-plan.sh` for automatic closeout
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Implementation decision capture and archival

### Task Group 2: Hook System Replacement
- [ ] **Replace plan-completion-manager.py** (Est: 50 min) - Convert to gh CLI-based shell script
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Automatic plan completion detection and GitHub integration
- [ ] **Update git-workflow-validator.sh** (Est: 25 min) - Add GitHub Issues validation
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Ensure plan/* branches have corresponding GitHub issues
- [ ] **Create gh-workflow-hooks.sh** (Est: 40 min) - Central GitHub workflow validation
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Pre-commit and post-merge GitHub Issues synchronization
- [ ] **Update session validation scripts** (Est: 20 min) - GitHub Issues context loading
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Load active plans from GitHub Issues into session context

### Task Group 3: Automation Workflows
- [ ] **Create automated labeling system** (Est: 35 min) - Auto-apply labels based on content analysis
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Domain detection, complexity estimation, propositions validation
- [ ] **Implement cross-plan dependency automation** (Est: 45 min) - Automatic issue linking and conflict detection
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Resource conflict detection using GitHub API
- [ ] **Create velocity tracking automation** (Est: 40 min) - Automatic time tracking and metrics updates
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: GitHub issue metadata updates for velocity learning
- [ ] **Implement notification system** (Est: 30 min) - Automated status updates and alerts
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Slack/email integration for plan status changes

### Task Group 4: Integration Testing & Validation
- [ ] **Test CLI script integration** (Est: 35 min) - Validate all gh CLI scripts work correctly
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: End-to-end workflow testing with real GitHub repository
- [ ] **Validate hook replacement** (Est: 25 min) - Ensure Python hook functionality preserved
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Compare old vs new hook behavior and outcomes
- [ ] **Test automation workflows** (Est: 30 min) - Validate automated labeling and linking
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Cross-plan coordination and conflict detection accuracy
- [ ] **Performance testing** (Est: 20 min) - GitHub API efficiency and response times
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Large-scale operation performance validation

## ✅ Phase Acceptance Criteria
- [ ] All `.claude/hooks/` Python scripts replaced with equivalent gh CLI functionality
- [ ] Plan creation, status, migration, and completion scripts fully functional
- [ ] Automated labeling system accurately categorizes plans across 46 labels
- [ ] Cross-plan dependency detection and conflict resolution automated
- [ ] Velocity tracking integration maintains historical data accuracy
- [ ] Git workflow validation seamlessly integrates GitHub Issues
- [ ] Performance meets or exceeds current Python-based hook system
- [ ] All automation workflows tested and validated with real scenarios
- [ ] Documentation updated for new CLI-based workflow
- [ ] Team training materials prepared for transition

## 🧪 Phase Testing Strategy
**CLI Script Testing**:
- Individual script functionality validation
- Parameter passing and error handling testing
- GitHub API integration and authentication testing
- Progress reporting and user interaction validation

**Automation Workflow Testing**:
- Automated labeling accuracy across diverse plan content
- Cross-plan dependency detection with complex scenarios
- Velocity tracking data integrity and update accuracy
- Notification system reliability and appropriate triggering

**Integration Testing**:
- End-to-end plan lifecycle testing (create → implement → complete)
- Git workflow integration with GitHub Issues synchronization
- Performance comparison with existing Python-based system
- Error handling and recovery testing for various failure modes

## 🔧 Phase Technical Requirements
**Core Dependencies**:
- GitHub CLI (`gh`) 2.0+ with full API support
- Bash 4.0+ for advanced shell scripting features
- `jq` for JSON processing and GitHub API response handling
- `curl` for direct API calls when gh CLI insufficient

**GitHub Integration**:
- Repository admin permissions for automated operations
- GitHub Actions workflow integration (optional)
- Webhook configuration for real-time synchronization
- API rate limit monitoring and management

**System Integration**:
- Existing `.claude/hooks/` directory structure preservation
- Git hook integration points maintained
- Session validation system compatibility
- Cross-platform shell script compatibility (macOS, Linux)

## 📂 Phase Affected Areas
- `.claude/hooks/` - Replace Python scripts with gh CLI shell scripts
- `.claude/scripts/` - New CLI utilities and automation workflows
- Git hooks - Integration with GitHub Issues workflow
- Session validation - GitHub Issues context loading
- Team workflow - New CLI-based plan management procedures

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/14
- **Time Invested**: 0h of 4.5h estimated
- **Completion Percentage**: 0%
- **Last Updated**: 2025-08-19

### Blockers & Issues
- Dependency: Phase 2 PropositionsAwareMigrator completion required
- Risk: GitHub CLI API coverage may require additional curl scripting
- Risk: Shell script complexity for advanced automation features

### Next Actions
- Begin with basic CLI scripts (create, status, migrate)
- Test GitHub CLI capabilities thoroughly before implementation
- Develop automation workflows incrementally with validation
- Ensure cross-platform compatibility throughout development

## 💬 Phase Implementation Notes

### Implementation Decisions
- GitHub CLI chosen over direct API calls for maintainability and authentication
- Shell scripts preferred over Python for reduced dependencies and faster execution
- Modular script design enables incremental adoption and testing
- Automation workflows designed to be optional and configurable

### Lessons Learned
*Will be updated during implementation*

### Phase Dependencies Resolution
- Requires Phase 2 PropositionsAwareMigrator for migration functionality
- Provides automation foundation for Phase 4 validated migration
- Establishes CLI workflow for Phase 5 documentation and training

---
*Phase 3 of 5 - GitHub Issues Migration with Propositions Framework - Last Updated: 2025-08-19*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*