# GitHub Issues Plan Management Scripts

This directory contains CLI automation scripts for managing SolarWindPy plans using GitHub Issues with comprehensive propositions framework.

## Prerequisites

Before using the GitHub Issues plan scripts, ensure all required labels are set up:

```bash
# One-time setup: Create all required labels
bash .claude/scripts/setup-labels.sh

# Verify labels exist
gh label list | grep -E "^(plan:|domain:|priority:|status:)"
```

### Required Labels

All GitHub Issues plans require these labels:

#### Plan Types (required)
- `plan:overview` - Main plan overview issue
- `plan:phase` - Phase implementation issue  
- `plan:closeout` - Plan closeout issue

#### Priority (required for overview)
- `priority:critical`, `priority:high`, `priority:medium`, `priority:low`

#### Status (required)
- `status:planning`, `status:in-progress`, `status:blocked`, `status:review`, `status:completed`

#### Domain (required for overview)
- `domain:physics`, `domain:data`, `domain:plotting`, `domain:testing`, `domain:infrastructure`, `domain:docs`

## Quick Start

### 1. Create New Plan
```bash
# Interactive mode
.claude/scripts/gh-plan-create.sh

# Direct creation
.claude/scripts/gh-plan-create.sh "Dark Mode Implementation" -p high -d infrastructure

# Command-line options
.claude/scripts/gh-plan-create.sh -p critical -d physics "Thermal Speed Validation"
```

### 2. Create Implementation Phases
```bash
# Interactive phase creation
.claude/scripts/gh-plan-phases.sh 123

# Quick phase creation
.claude/scripts/gh-plan-phases.sh -q "Setup,Implementation,Testing" 123

# With closeout issue
.claude/scripts/gh-plan-phases.sh -c 123
```

### 3. Monitor Plan Status
```bash
# Full dashboard
.claude/scripts/gh-plan-status.sh

# Summary only
.claude/scripts/gh-plan-status.sh -s

# Recommendations
.claude/scripts/gh-plan-status.sh -r

# Filter by status
.claude/scripts/gh-plan-status.sh -f in-progress
```

## Scripts Overview

### gh-plan-create.sh
**Purpose**: Create comprehensive plan overview issues with complete propositions framework

**Features**:
- Interactive and command-line modes
- 25 GitHub labels across 5 categories (priority, status, type, plan, domain)
- Automatic feature branch creation
- Complete propositions framework integration

**Usage**:
```bash
./gh-plan-create.sh [OPTIONS] [PLAN_NAME]

Options:
  -h, --help              Show help message
  -p, --priority LEVEL    Set priority (critical|high|medium|low)
  -d, --domain DOMAIN     Set domain (physics|data|plotting|testing|infrastructure|docs)
  -i, --interactive       Run in interactive mode
```

### gh-plan-status.sh
**Purpose**: Comprehensive plan monitoring and status dashboard

**Features**:
- Multi-plan overview with status badges
- Summary statistics and domain distribution
- Actionable recommendations for blocked/critical plans
- Colored output for easy visual scanning

**Usage**:
```bash
./gh-plan-status.sh [OPTIONS]

Options:
  -h, --help          Show help message
  -s, --summary       Show only summary statistics
  -d, --detailed      Show detailed view with phase issues
  -r, --recommendations Show only recommendations
  -f, --filter STATUS Filter by status
```

### gh-plan-phases.sh
**Purpose**: Create and link phase issues to plan overview

**Features**:
- Interactive, batch, and quick creation modes
- Automatic cross-linking between overview and phase issues
- Optional closeout issue creation
- Configuration file support for batch operations

**Usage**:
```bash
./gh-plan-phases.sh [OPTIONS] OVERVIEW_ISSUE

Options:
  -h, --help          Show help message
  -i, --interactive   Interactive phase creation (default)
  -b, --batch FILE    Batch create from configuration file
  -c, --closeout      Also create closeout issue
  -q, --quick PHASES  Quick create (comma-separated names)
```

## Issue Templates

### Plan Overview Template (plan-overview.yml)
Comprehensive planning template with 8 required sections:
- **🎯 Objective**: Clear goal statement
- **🧠 Context**: Background and motivation
- **🔧 Technical Requirements**: Dependencies and constraints
- **📂 Affected Areas**: Files and components
- **✅ Acceptance Criteria**: Measurable completion criteria
- **📊 Value Proposition Analysis**: Scientific and productivity value
- **💰 Resource & Cost Analysis**: Time investment and ROI
- **⚠️ Risk Assessment**: Technical and project risks
- **🔒 Security Proposition**: Code-level security (NO FAIR compliance)
- **🎯 Scope Audit**: SolarWindPy alignment validation
- **💾 Token Usage Optimization**: Claude session efficiency
- **⏱️ Time Investment Analysis**: Development time breakdown
- **🎯 Usage & Adoption Metrics**: Success criteria and adoption strategy

### Plan Phase Template (plan-phase.yml)
Detailed implementation template with:
- **📋 Implementation Tasks**: Task breakdown with time estimates
- **✅ Phase Acceptance Criteria**: Phase-specific completion criteria
- **🧪 Phase Testing Strategy**: Testing approach for this phase
- **🔧 Phase Technical Requirements**: Phase-specific tools and frameworks
- **📂 Phase Affected Areas**: Files modified in this phase
- **📊 Phase Progress Tracking**: Real-time status monitoring
- **🔄 Context Management Points**: Session break points for token management

### Plan Closeout Template (plan-closeout.yml)
Comprehensive completion documentation with:
- **📦 Final Deliverables**: Complete delivery list
- **✅ Acceptance Criteria Review**: Status of all original criteria
- **🧠 Implementation Decisions**: 85% decision capture target
- **📚 Lessons Learned**: What worked, challenges, and improvements
- **⏱️ Actual vs Estimated Analysis**: Time accuracy and velocity learning
- **💰 Value Realization Assessment**: Did the plan deliver expected value?
- **🔍 Quality Metrics**: Code quality, coverage, and technical debt
- **🎯 Follow-up Actions**: Next steps and future enhancements
- **📁 Plan Archival Information**: Knowledge preservation and searchability
- **👥 Team Feedback & Recognition**: Process feedback and contributor recognition

## GitHub Labels System

### Priority Labels
- `priority:critical` - Critical priority - immediate attention required
- `priority:high` - High priority - address soon
- `priority:medium` - Medium priority - normal timeline
- `priority:low` - Low priority - when time permits

### Status Labels
- `status:planning` - Currently in planning phase
- `status:in-progress` - Currently being worked on
- `status:blocked` - Blocked waiting for dependencies
- `status:review` - Ready for review
- `status:completed` - Completed successfully

### Type Labels
- `type:feature` - New feature development
- `type:bugfix` - Bug fix
- `type:refactor` - Code refactoring
- `type:docs` - Documentation changes
- `type:test` - Testing improvements
- `type:infrastructure` - Infrastructure and tooling
- `type:chore` - Maintenance and chores

### Plan Structure Labels
- `plan:overview` - Plan overview issue
- `plan:phase` - Plan phase issue
- `plan:closeout` - Plan closeout issue

### Domain Labels
- `domain:physics` - Solar wind physics calculations
- `domain:data` - Data structures and processing
- `domain:plotting` - Visualization and plotting
- `domain:testing` - Testing and validation
- `domain:infrastructure` - Development infrastructure
- `domain:docs` - Documentation and guides

## Multi-Computer Workflow

### Benefits
- **Instant Access**: Plans available immediately on all 3 development computers
- **No Synchronization**: No branch sync overhead or context switching friction
- **Real-time Updates**: GitHub Issues provide live status across machines
- **Searchable History**: Complete plan history with GitHub's powerful search

### Setup Requirements
1. **GitHub CLI**: Install `gh` on all development machines
2. **Authentication**: Run `gh auth login` on each machine
3. **Repository Access**: Ensure write access to repository
4. **Script Access**: Copy scripts to all machines or use shared network location

### Typical Workflow
1. **Create Plan**: Use `gh-plan-create.sh` from any machine
2. **Phase Creation**: Use `gh-plan-phases.sh` to break down implementation
3. **Switch Machines**: Plan instantly accessible on any development computer
4. **Implementation**: Work on feature branch, update issues with progress
5. **Monitoring**: Use `gh-plan-status.sh` to track overall progress
6. **Completion**: Create closeout issue with comprehensive documentation

## Integration with Existing SolarWindPy Workflow

### UnifiedPlanCoordinator Integration
The GitHub Issues system integrates seamlessly with the existing UnifiedPlanCoordinator agent:
- Agent extended with GitHub Issues capabilities
- Automatic cross-issue coordination and linking
- Integration with existing hooks and validation systems
- Preserves all sophisticated planning capabilities

### Hook System Compatibility
- Existing physics validation hooks continue to work
- Token management handled through natural session boundaries
- Quality validation (pytest, black, flake8) integrated into phase tracking
- Velocity learning captured in closeout issues

### Scientific Workflow Preservation
- All propositions framework elements preserved in GitHub templates
- 85% implementation decision capture maintained
- Comprehensive value analysis for scientific software development
- SolarWindPy scope alignment validation in every plan

## Troubleshooting

### Common Issues

#### Label-Related Errors
1. **"Missing required labels" error**:
   ```bash
   # Solution: Run the setup script
   bash .claude/scripts/setup-labels.sh
   ```

2. **"No plan overview issues found"**: 
   - Ensure your overview issue has `plan:overview` label
   - Check with: `gh issue view YOUR_ISSUE --json labels`

3. **gh-plan-status.sh shows empty results**:
   - Labels are missing on existing issues
   - Run: `gh issue edit ISSUE_NUMBER --add-label "plan:overview,domain:YOUR_DOMAIN"`

#### General Issues
4. **GitHub CLI not authenticated**: Run `gh auth login`
5. **Template not found**: Ensure you're in repository root directory
6. **Permission denied**: Check repository write access
7. **Issue creation failed**: Verify network connection and GitHub status
8. **Invalid priority/domain**: Use one of the supported values listed in Prerequisites

### Script Debugging
- Add `-x` to bash scripts for verbose debugging: `bash -x gh-plan-create.sh`
- Check GitHub CLI status: `gh auth status`
- Verify repository context: `gh repo view`

### Multi-Computer Issues
- Ensure same GitHub authentication on all machines
- Verify script permissions: `chmod +x .claude/scripts/*.sh`
- Check network connectivity to GitHub
- Confirm repository access from each machine

## Advanced Usage

### Custom Batch Configuration
Create a configuration file for batch phase creation:
```
Foundation Setup|2-3 hours|None
Core Implementation|4-5 hours|Phase 1
Testing & Validation|1-2 hours|Phase 2
Documentation|1 hour|Phase 3
```

Then use: `gh-plan-phases.sh -b phases.conf 123`

### GitHub CLI Power Usage
```bash
# Find all physics domain plans
gh issue list --label "domain:physics,plan:overview"

# Critical plans that need attention
gh issue list --label "priority:critical,status:blocked"

# Plans updated in the last week
gh issue list --search "label:plan:overview updated:>$(date -d '7 days ago' +%Y-%m-%d)"

# Export plan data to JSON
gh issue list --label "plan:overview" --json number,title,labels,assignees > plans.json
```

---

For more information, see the main CLAUDE.md file and the UnifiedPlanCoordinator agent documentation.