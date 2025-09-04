# Phase 2: Plan Creation System

## Phase Metadata
- **Phase**: 2/3
- **Estimated Duration**: 2-3 hours
- **Dependencies**: Phase 1 (Foundation & Labels)
- **Status**: Not Started

## 🎯 Phase Objective
Create GitHub Issues-based plan creation system by extending UnifiedPlanCoordinator agent and developing issue template automation workflows. Focus on preserving the comprehensive propositions framework while enabling multi-computer synchronization for new plans.

## 🧠 Phase Context
This phase transforms the planning workflow from local files to GitHub Issues without requiring migration of existing plans. The UnifiedPlanCoordinator agent will be extended to support GitHub Issues creation, and template workflows will automate the Overview → Phases → Closeout issue structure.

## 📋 Implementation Tasks

### Task Group 1: UnifiedPlanCoordinator Agent Extension
- [x] **Extend agent capabilities** (Est: 60 min) - Add GitHub Issues integration section to agent
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Direct feature branch creation from GitHub Issues, remove plan branch coordination - comprehensive GitHub Issues section added
- [x] **Add GitHub CLI integration** (Est: 30 min) - CLI command coordination for issue operations
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Issue creation, labeling, milestone management via gh CLI - full integration section added to agent
- [x] **Implement propositions framework support** (Est: 45 min) - Integration with existing value proposition generation
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Adapt plan-value-generator.py output for GitHub Issues templates - propositions preserved in issue template structure

### Task Group 2: GitHub Issue Templates Development
- [x] **Create Overview template** (Est: 45 min) - plan-overview.yml with complete propositions framework
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: YAML frontmatter with value, cost, risk, token, usage sections - 8 comprehensive propositions sections implemented
- [x] **Create Phase template** (Est: 30 min) - plan-phase.yml for individual phase tracking
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Task checklist, acceptance criteria, progress monitoring - comprehensive phase tracking template created
- [x] **Create Closeout template** (Est: 30 min) - plan-closeout.yml for implementation decisions
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Decision capture, lessons learned, 85% automation target - 12-section comprehensive closeout template

### Task Group 3: Template Automation Workflows
- [x] **Create issue creation automation** (Est: 30 min) - Script to generate linked issue chains
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Overview → multiple Phases → Closeout linking automation - gh-plan-create.sh and gh-plan-phases.sh scripts created
- [x] **Implement cross-issue coordination** (Est: 25 min) - Issue linking and milestone management
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Automatic issue references and progress coordination - cross-linking implemented in phase creation script
- [x] **Add template validation** (Est: 20 min) - Validate issue templates render correctly
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Test propositions framework display and YAML parsing - templates validated through test plan creation

### 🔄 Context Management Point
**IMPORTANT**: After completing Task Group 3, if approaching token limits, the user can naturally end the session and resume with fresh context. The git commits and plan file updates preserve all implementation decisions.

**Optional Session Break**: If needed, end session and resume with: "Continue GitHub Issues migration - Phase 2 Plan Creation System. Read current progress from plans/github-issues-migration/2-Plan-Creation-System.md"

**Context Preserved Automatically**:
- UnifiedPlanCoordinator extension decisions in commit history
- GitHub Issues integration details in updated agent file
- Template automation workflows in .github/ISSUE_TEMPLATE/ files
- Progress tracking in updated phase files

### Task Group 4: Phase Completion
- [x] **Create phase completion git commit** (Est: 10 min) - Milestone commit capturing all Phase 2 deliverables
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Commit message: "feat: complete GitHub Issues Plan Management System implementation" - comprehensive milestone commit
- [x] **Update overview progress tracking** (Est: 5 min) - Mark Phase 2 as completed with commit reference
  - Commit: `ad05b1d`
  - Status: Completed
  - Notes: Update 0-Overview.md with phase completion status and milestone commit hash - progress tracking updated

## ✅ Phase Acceptance Criteria
- [ ] UnifiedPlanCoordinator extended with GitHub Issues integration capabilities
- [ ] Agent size remains manageable (~13,500 bytes, within safe zone)
- [ ] 3 issue templates render correctly with full propositions framework
- [ ] Template automation creates properly linked issue chains
- [ ] Cross-issue coordination functional for multi-phase plans
- [ ] Integration with existing hook system (plan-value-generator.py) functional
- [ ] Issue templates preserve 85% implementation decision capture capability
- [ ] GitHub CLI integration works seamlessly with extended agent
- [ ] Phase 2 milestone git commit created with all deliverables
- [ ] Overview progress tracking updated with phase completion status

## 🧪 Phase Testing Strategy
**Agent Extension Testing**:
- UnifiedPlanCoordinator functionality validation with GitHub Issues support
- Agent size and performance monitoring (target <15,000 bytes)
- Integration testing with existing specialized agents

**Template Testing**:
- Issue template rendering across all propositions categories
- YAML frontmatter parsing and metadata extraction
- Cross-template consistency and formatting validation

**Automation Testing**:
- Issue creation workflow end-to-end testing
- Cross-issue linking and coordination validation
- Integration with GitHub CLI commands and authentication

## 🔧 Phase Technical Requirements
**Agent Development**:
- Extension of existing UnifiedPlanCoordinator agent file
- GitHub CLI (`gh`) integration for issue operations
- Preservation of existing agent capabilities and tools

**Template Development**:
- GitHub Issue Template YAML syntax
- Propositions framework structure preservation
- Cross-issue reference and linking capabilities

**Integration Requirements**:
- Compatibility with existing `.claude/hooks/` system
- Seamless workflow with plan-value-generator.py
- Multi-computer GitHub authentication via gh CLI

## 📂 Phase Affected Areas
- `.claude/agents/agent-unified-plan-coordinator.md` - Agent extension
- `.github/ISSUE_TEMPLATE/` - New template files (3 templates)
- `.claude/hooks/plan-value-generator.py` - Output format adaptation
- `.claude/scripts/` - New template automation utilities

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/11
- **Time Invested**: 0h of 2.75h estimated
- **Completion Percentage**: 0%
- **Last Updated**: 2025-09-03

### Blockers & Issues
- Dependency: Phase 1 completion required for GitHub labels and infrastructure
- Risk: Agent size increase must remain within manageable limits
- Risk: Template complexity may require iteration for optimal UX

### Next Actions
- Begin with UnifiedPlanCoordinator extension design
- Create issue templates with comprehensive propositions framework
- Validate template automation workflows with test data
- Ensure seamless integration with existing hook system

## 💬 Phase Implementation Notes

### Implementation Decisions
- Extend existing agent rather than create new specialized agent
- Maintain all existing UnifiedPlanCoordinator capabilities
- Focus on creation workflows rather than migration complexity
- Preserve propositions framework through structured issue templates

### Lessons Learned
*Will be updated during implementation*

### Phase Dependencies Resolution
- Requires Phase 1 GitHub infrastructure (labels, repository configuration)
- Provides plan creation capability for Phase 3 CLI integration and documentation
- Establishes foundation for team adoption of new GitHub Issues workflow

## 👤 User Instructions for Phase 2 Completion

After Claude completes all Phase 2 tasks:

### Step 1: Verify Phase 2 Deliverables
- [ ] All 11 phase tasks marked as completed in this file
- [ ] Phase 2 milestone git commit created with message: "feat: complete Phase 2 - Plan Creation System - GitHub Issues migration"
- [ ] 0-Overview.md updated with Phase 2 completion status
- [ ] UnifiedPlanCoordinator agent extended with GitHub Issues capabilities
- [ ] All 3 issue templates created and validated

### Step 2: Session Management
- [ ] End this Claude Code session naturally when Phase 2 is complete
- [ ] To continue with Phase 3: Start new session with prompt:
  **"Continue GitHub Issues migration plan - begin Phase 3: CLI Integration & Documentation. Read current status from plans/github-issues-migration/ directory."**

### Step 3: Context Preservation
✅ **Automatic**: Git commit, agent extensions, and issue templates provide all context needed for Phase 3  
❌ **Not needed**: No manual compaction or special preservation steps required

Claude will read the plan files, updated agent, and created templates to continue seamlessly with Phase 3.

---
*Phase 2 of 4 - GitHub Issues Plan Management System - Last Updated: 2025-09-03*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*