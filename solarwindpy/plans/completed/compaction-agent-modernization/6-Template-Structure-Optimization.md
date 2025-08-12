# Phase 6: Template Structure Optimization

## Metadata
- **Phase**: 6 of 7
- **Estimated Time**: 60 minutes
- **Dependencies**: Phase 5 (Workflow Integration Streamlining)
- **Status**: Pending
- **Completion**: 0%

## Objective
Optimize the compacted state template structure for streamlined 2-agent workflow efficiency, removing obsolete complexity while enhancing session continuity capabilities for current architecture.

## Current Template Analysis (Lines 139-201)

### Template Complexity Issues
```markdown
# Current Compacted State Template (276 lines total):
- **Metadata Section** (Lines 142-151): References obsolete agent types
- **Progress Snapshot** (Lines 160-166): Git validation logic sound but verbose
- **Context Archive** (Lines 168-183): Generic phase structure, not agent-optimized  
- **Resumption Instructions** (Lines 184-201): Complex specialist coordination

# Optimization Opportunities:
- Agent-specific template sections for PlanManager vs PlanImplementer
- Streamlined metadata for 3-agent system
- Optimized resumption workflows for current architecture
- Enhanced git-first validation capabilities
```

## Template Modernization Tasks

### Core Template Structure Updates
- [ ] **T6.1**: Modernize metadata section for current agent architecture (Lines 142-151) - 15 min
- [ ] **T6.2**: Optimize progress snapshot for git-first validation (Lines 160-166) - 15 min
- [ ] **T6.3**: Create agent-specific context archive sections - 20 min
- [ ] **T6.4**: Streamline resumption instructions for 2-agent workflows (Lines 184-201) - 10 min

### Enhanced Metadata Section (Lines 142-151)
```markdown
# CURRENT (OBSOLETE):
## Compaction Metadata
- **Plan Name**: [plan-name]  
- **Current Phase**: [phase-name] ([N]/[total])
- **Compaction Timestamp**: [ISO-8601 timestamp]
- **Token Efficiency**: [original] → [compressed] tokens ([percentage]% reduction)
- **Source Agent**: [agent-type] ([Full/Streamlined/Minimal])
- **Compaction Tier**: [High/Medium/Low-Complexity]
- **Git Sync Status**: ✅ Validated | ⚠️ Pending | ❌ Conflicted
- **Evidence Commits**: [commit-hash-list] validating progress claims

# OPTIMIZED (MODERNIZED):
## Compaction Metadata  
- **Plan Name**: [plan-name]
- **Source Agent**: PlanManager | PlanImplementer | PlanStatusAggregator
- **Agent Context**: [planning/implementation/monitoring] workflow state
- **Compaction Timestamp**: [ISO-8601 timestamp]  
- **Token Efficiency**: [original] → [compressed] tokens ([percentage]% reduction)
- **Session Extension**: [effective capacity increase] ([multiplier]x session length)
- **Git Validation**: ✅ Commits verified | ⚠️ Sync pending | ❌ Conflicts detected
- **Resumption Quality**: [High/Medium/Low] based on context preservation
```

### Enhanced Git-First Validation (Lines 160-166)
```markdown
# CURRENT (BASIC):
## Progress Snapshot (Git-Validated)
- **Completed Phases**: [phase-1] ✓ (commits: [hash-list]), [phase-2] ✓ (commits: [hash-list])
- **Current Progress**: [X]/[total] tasks completed ([percentage]%) - verified by git evidence
- **Key Achievements**: [significant milestones] with commit references: [commit-hash-list]
- **Velocity Metrics**: [estimated vs actual time] validated against git commit timing
- **Time Investment**: [hours invested] of [estimated total] hours
- **Git Evidence**: [N] commits validate progress claims, session state accuracy: ✅

# ENHANCED (OPTIMIZED):
## Progress Snapshot (Git-Validated)
- **Branch State**: [plan/name ↔ feature/name] sync status with commit alignment
- **Verified Completion**: [X]/[total] tasks ✓ with commit evidence: [recent-commits]  
- **Velocity Intelligence**: [estimated vs actual] hours with learning calibration
- **Progress Quality**: [implementation/testing/integration] status with QA validation
- **Session Continuity**: [next session priorities] with git-validated foundation
- **Evidence Integrity**: [N] commits confirm accuracy, [M] specialist validations preserved
```

### Agent-Specific Context Archive Sections
- [ ] **T6.5**: Design PlanManager-specific archive format - 10 min
- [ ] **T6.6**: Design PlanImplementer-specific archive format - 10 min  
- [ ] **T6.7**: Design PlanStatusAggregator-specific archive format - 5 min

#### PlanManager Context Archive
```markdown
## PlanManager Compacted Context

### Plan Management State
- **Active Plans**: [plan-inventory] with progress, priorities, and dependencies
- **Current Focus**: [plan-name] Phase [N]: [current tasks and estimates] 
- **Velocity Intelligence**: [learning data] from [completed phases] for time calibration
- **Plan Dependencies**: [cross-plan coordination] and [integration requirements]

### Archived Planning Context (Compressed)
- **Completed Planning**: [Phase-1: outcomes, Phase-2: outcomes] with commit refs
- **Historical Estimates**: [estimation learning] compressed to [calibration data]
- **Discovery Archive**: [plan exploration] compressed to [current plan inventory]

### Resumption Priorities
- **Next Planning Tasks**: [immediate planning priorities] with [time estimates]
- **Dependency Resolution**: [blocking coordination] requiring [PlanImplementer sync]
- **Velocity Focus**: [calibration opportunities] for [improved estimation]
```

#### PlanImplementer Context Archive
```markdown
## PlanImplementer Compacted Context

### Implementation State  
- **Active Implementation**: [current phase] on [feature/name] branch
- **Branch Coordination**: [plan ↔ feature] sync with [commit alignment]
- **QA Status**: [test results, validation status] and [performance benchmarks]
- **Integration Points**: [specialist coordination] and [dependency management]

### Archived Implementation Context (Compressed)
- **Completed Implementation**: [Phase-1: commits, Phase-2: commits] with QA validation
- **Historical Progress**: [implementation velocity] compressed to [performance metrics]
- **Branch Management Archive**: [completed merges] compressed to [current state]

### Resumption Priorities
- **Next Implementation**: [immediate tasks] with [QA requirements] and [time estimates]
- **Branch Operations**: [sync requirements] and [merge planning]  
- **Quality Focus**: [testing priorities] and [specialist coordination needs]
```

### Streamlined Resumption Instructions (Lines 184-201)
```markdown
# CURRENT (COMPLEX):
## Resumption Instructions
### Next Session Priorities
1. **Immediate Action**: [first task to tackle]
2. **Quick Wins**: [2-3 achievable tasks for momentum]  
3. **Critical Path**: [essential tasks for plan progression]

### Context Recovery
- **Branch Operations**: [git commands to resume work environment]
- **Specialist Coordination**: [agents to re-engage and coordination points]
- **Integration Requirements**: [cross-component dependencies to validate]

### Session Startup Checklist
- [ ] Switch to appropriate branch: `git checkout [branch-name]`
- [ ] Review recent commits and current state  
- [ ] Re-engage specialist agents: [list specific agents]
- [ ] Validate integration points and dependencies
- [ ] Begin with [specific next task]

# STREAMLINED (OPTIMIZED):
## Resumption Instructions

### Immediate Session Startup ([estimated time])
1. **Git Recovery**: `git checkout [branch]` and validate [sync status]
2. **Context Restoration**: Resume [agent-type] workflow at [specific task]  
3. **Priority Validation**: Confirm [next 1-3 tasks] align with [time available]

### Agent-Specific Resumption  
- **PlanManager**: Restore [plan inventory], review [velocity data], prioritize [next planning]
- **PlanImplementer**: Sync [feature branch], validate [QA status], continue [implementation phase]
- **StatusAggregator**: Update [monitoring scope], resolve [dependencies], report [bottlenecks]

### Quality Continuity Checklist
- [ ] Agent context fully restored with [specific validation]
- [ ] Git state validated: [branch status] and [sync requirements]  
- [ ] Session priorities confirmed: [immediate tasks] within [token budget]
- [ ] Specialist integration ready: [domain experts] available as needed
```

## Template Efficiency Optimization

### Token Efficiency Improvements
- [ ] **T6.8**: Reduce template overhead from ~150 to ~75-100 tokens - 10 min
- [ ] **T6.9**: Optimize section structure for faster parsing - 10 min
- [ ] **T6.10**: Enhance readability for rapid context recovery - 5 min

### Compression Quality Enhancements
```markdown
Template Optimization Results:
- **Metadata Efficiency**: Agent-specific fields reduce irrelevant information
- **Archive Optimization**: Tailored compression for planning vs implementation contexts
- **Resumption Speed**: Streamlined startup instructions for faster session recovery  
- **Git Integration**: Enhanced validation capabilities with commit-linked verification
- **Session Quality**: Improved continuity through better context preservation
```

## Template Validation Framework

### Template Testing Requirements  
- [ ] **Token Efficiency**: Validate template overhead stays <100 tokens
- [ ] **Context Preservation**: Ensure essential information preserved through compression
- [ ] **Resumption Quality**: Test session startup speed and context recovery
- [ ] **Agent Compatibility**: Validate template works with PlanManager/PlanImplementer outputs
- [ ] **Git Integration**: Confirm commit-linked validation functionality

### Quality Metrics
```markdown
Template Quality Standards:
- **Resumption Speed**: <2 minutes to restore full context from compacted state
- **Information Density**: >80% essential information preserved in compressed format  
- **Session Extension**: Enable 2-3x longer productive sessions
- **Git Accuracy**: 100% commit-linked validation for progress claims
- **Agent Compatibility**: Works with all current planning agent outputs
```

## Success Criteria
- [ ] Template metadata optimized for current 3-agent architecture
- [ ] Progress snapshot enhanced with improved git-first validation  
- [ ] Agent-specific context archive sections implemented
- [ ] Resumption instructions streamlined for 2-agent workflow efficiency
- [ ] Template overhead reduced to <100 tokens while improving functionality
- [ ] Session continuity quality improved through optimized structure
- [ ] Git integration capabilities enhanced for better progress validation
- [ ] Template compatibility validated with current agent outputs

## Quality Validation
- [ ] **Template Efficiency**: Overhead minimized while enhancing functionality
- [ ] **Context Quality**: Essential information preservation improved  
- [ ] **Resumption Speed**: Session startup optimized for rapid context recovery
- [ ] **Agent Alignment**: Template structure matches actual agent capabilities
- [ ] **Git Integration**: Commit-linked validation enhanced and verified

## Risk Mitigation  
- **Backward Compatibility**: Existing compacted_state.md files remain functional
- **Gradual Enhancement**: Template improvements preserve existing functionality
- **Quality Monitoring**: Validate resumption quality meets or exceeds current standards
- **Agent Testing**: Ensure optimized template works with actual agent outputs

## Next Phase Dependencies
Phase 7 (Integration Testing & Validation) depends on:
- Optimized template structure for current architecture
- Enhanced git-first validation capabilities
- Agent-specific context archive formats
- Streamlined resumption instruction workflows

**Estimated Completion**: <checksum>
**Time Invested**: 0h of 1h
**Status**: Pending → In Progress → Completed