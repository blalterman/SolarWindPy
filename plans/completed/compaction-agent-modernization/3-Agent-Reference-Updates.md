# Phase 3: Agent Reference Updates  

## Metadata
- **Phase**: 3 of 7
- **Estimated Time**: 45 minutes
- **Dependencies**: Phase 2 (Token Baseline Recalibration)
- **Status**: Pending
- **Completion**: 0%

## Objective
Fix all non-existent agent file references and update to current agent inventory, replacing obsolete 6-agent system references with accurate 3-agent architecture.

## Current Agent Inventory (Validated)

### Existing Agent Files
```bash
# Verified existing files:
.claude/agents/agent-plan-manager.md           # PlanManager (1,200 tokens)
.claude/agents/agent-plan-implementer.md       # PlanImplementer (1,200 tokens)  
.claude/agents/agent-plan-status-aggregator.md # PlanStatusAggregator (~400 tokens)
.claude/agents/agent-git-integration.md        # GitIntegration service
.claude/agents/agent-compaction.md            # CompactionAgent (target for updates)
```

### Non-Existent References in CompactionAgent
```bash
# CompactionAgent currently references (ALL NON-EXISTENT):
agent-plan-manager-full.md                    # Does not exist
agent-plan-manager-streamlined.md             # Does not exist  
agent-plan-manager-minimal.md                 # Does not exist
agent-plan-implementer-full.md                # Does not exist
agent-plan-implementer-research-optimized.md  # Does not exist
agent-plan-implementer-minimal.md             # Does not exist
```

## File Reference Correction Tasks

### Lines 25-47: Agent Type Classifications
```markdown
# CURRENT (OBSOLETE):
- **Context Parsing**: Extract and structure context from all 6 planning/implementation agent variants
- **High-Complexity Sources** (Plan Manager Full, Plan Implementer Full)
- **Medium-Complexity Sources** (Streamlined, Research-Optimized)
- **Low-Complexity Sources** (Minimal variants)

# UPDATED (MODERNIZED):
- **Context Parsing**: Extract and structure context from current planning agents
- **PlanManager Processing** (Strategic planning with velocity tracking)  
- **PlanImplementer Processing** (Execution with git integration)
- **PlanStatusAggregator Processing** (Cross-plan monitoring)
```

### Lines 56-60: File Coordination References
```markdown
# CURRENT (OBSOLETE):
- **Affects**: .claude/agents/, solarwindpy/plans/*/compacted_state.md, all planning agents

# UPDATED (MODERNIZED):
- **Affects**: .claude/agents/agent-compaction.md, solarwindpy/plans/*/compacted_state.md, 
             PlanManager, PlanImplementer, PlanStatusAggregator integration
```

### Lines 102-116: Integration Protocol
```markdown
# CURRENT (OBSOLETE):
## Source Agent Metadata
- Agent Type: [Full/Streamlined/Minimal]
- Agent Category: [Plan Manager/Plan Implementer]

# UPDATED (MODERNIZED):
## Source Agent Metadata
- Agent Type: [PlanManager/PlanImplementer/PlanStatusAggregator]
- Current Token Usage: [tokens used of 1200/1200/400 limit]
- Compression Urgency: [approaching limit?]
```

### Lines 271-275: System Integration Claims
```markdown
# CURRENT (OBSOLETE):
- Seamless operation with all 6 planning/implementation agents
- All 6 planning agents successfully integrated with <50 tokens compaction logic each

# UPDATED (MODERNIZED):  
- Seamless operation with PlanManager, PlanImplementer, and PlanStatusAggregator
- All 3 planning agents successfully integrated with minimal compaction overhead
```

## Specific Update Tasks

### Agent Reference Corrections
- [ ] **T3.1**: Replace "6 planning/implementation agent variants" → "3 current planning agents" (Line 25) - 5 min
- [ ] **T3.2**: Update compression tier names from Full/Streamlined/Minimal → PlanManager/PlanImplementer/StatusAggregator (Lines 30-46) - 10 min  
- [ ] **T3.3**: Fix integration protocol metadata format (Lines 102-116) - 10 min
- [ ] **T3.4**: Correct system integration claims (Lines 271-275) - 5 min
- [ ] **T3.5**: Update agent coordination documentation (Lines 203-218) - 10 min
- [ ] **T3.6**: Verify all file path references point to existing files - 5 min

### Integration Point Updates
```markdown
# Current Integration Points to Update:

Line 208: "Cross-Agent Compatibility: Universal service for all agent variants"
→ "Cross-Agent Compatibility: Universal service for current planning agents"

Line 272: "System Integration: Seamless operation with all 6 planning/implementation agents"  
→ "System Integration: Seamless operation with PlanManager, PlanImplementer, and PlanStatusAggregator"

Line 62: "All 6 planning/implementation agents"
→ "PlanManager, PlanImplementer, and PlanStatusAggregator agents"
```

### Template Updates for Current Architecture

#### Compaction Request Format (Lines 102-116)
```markdown
# UPDATED FORMAT:
## Source Agent Metadata
- **Agent Type**: PlanManager | PlanImplementer | PlanStatusAggregator
- **Current Phase**: [phase name and progress] (for PlanManager/PlanImplementer)
- **Monitoring Scope**: [plans tracked] (for PlanStatusAggregator)
- **Token Usage**: [current] of [1200|1200|400] limit
- **Compression Trigger**: [threshold reached | manual request | session boundary]

## Context to Compress
- [Agent-specific structured context]
- [Phase/monitoring history and completion status]
- [Current objectives and next tasks]  
- [Dependencies and coordination requirements]
```

## Agent Workflow Integration Updates

### PlanManager Integration
- **Context Elements**: Plan discovery, creation workflows, time estimation, status tracking
- **Preservation Priorities**: Current phase, next tasks, velocity metrics, time estimates
- **Compression Focus**: Archive completed phases, compress verbose descriptions

### PlanImplementer Integration  
- **Context Elements**: Cross-branch coordination, checksum management, QA validation
- **Preservation Priorities**: Active branch state, pending tasks, integration points
- **Compression Focus**: Archive completed implementations, compress commit history

### PlanStatusAggregator Integration
- **Context Elements**: Cross-plan monitoring, dependency analysis, bottleneck identification
- **Preservation Priorities**: Critical dependencies, plan coordination, status summaries
- **Compression Focus**: Archive historical status, compress detailed analyses

## File Validation Checklist
- [ ] **Verify Existence**: All referenced agent files exist at specified paths
- [ ] **Update References**: No obsolete agent variant names remain  
- [ ] **Path Accuracy**: All file paths are absolute and correct
- [ ] **Integration Logic**: Agent-specific integration matches actual capabilities
- [ ] **Template Alignment**: Compaction formats align with actual agent structures

## Success Criteria
- [ ] All agent file references point to existing files
- [ ] Agent type classifications match current 3-agent architecture
- [ ] Integration protocol updated for current agent capabilities
- [ ] System integration claims accurate for PlanManager/PlanImplementer/StatusAggregator
- [ ] No references to obsolete Full/Streamlined/Minimal agent variants
- [ ] Template formats align with current agent structures

## Quality Validation
- [ ] **Reference Accuracy**: All file paths validated to exist
- [ ] **Agent Capability Alignment**: Integration logic matches actual agent features
- [ ] **Naming Consistency**: Agent names consistent throughout document
- [ ] **Template Compatibility**: Compaction formats work with current agent outputs

## Risk Mitigation
- **Path Verification**: Check all file references before updating
- **Agent Capability Validation**: Ensure integration logic matches actual agent features  
- **Backward Compatibility**: Preserve existing compacted_state.md functionality
- **Testing Preparation**: Set up for Phase 7 integration testing

## Next Phase Dependencies
Phase 4 (Compression Algorithm Modernization) depends on:
- Corrected agent references and integration points
- Validated file paths and agent capabilities
- Updated template formats for current architecture
- Aligned integration protocols

**Estimated Completion**: 4b9a253
**Time Invested**: 0.5h of 0.75h
**Status**: Completed