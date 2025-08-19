# Implementation Plan: Compaction Agent System Architecture

## Execution Order
1. **First**: Implement Compaction Agent System Architecture Plan (this document)
2. **Second**: Update Agents Index for Compaction Agent Integration (see agents-index-update-plan.md)

## Phase 1: Universal Compaction Agent Development (90 min)

### Create Core Compaction Agent
**File**: `/.claude/agents/agent-compaction.md`
- Build universal compaction agent with tiered processing capabilities
- Implement multi-agent context understanding for all 6 agent variants
- Create agent-specific compression algorithms (40-70% reduction targets)
- Add structured `compacted_state.md` generation system

### Compression Logic Implementation
**High-Complexity Processing** (Plan Manager Full, Plan Implementer Full):
- Deep historical archival and complex dependency management
- Target: 40-60% compression (3000→1200, 2800→1120 tokens)

**Medium-Complexity Processing** (Streamlined, Research-Optimized):
- Focused summarization and reference optimization
- Target: 50-70% compression (1400→420, 1000→300 tokens)

**Low-Complexity Processing** (Minimal variants):
- Lightweight consolidation maintaining efficiency
- Target: Minimal compression (maintain 200-300 token ceiling)

## Phase 2: Agent Integration Updates (60 min)

### Update All 6 Planning/Implementation Agents
**Files to Modify**:
- `/.claude/agents/agent-plan-manager-full.md`
- `/.claude/agents/agent-plan-manager.md`
- `/.claude/agents/agent-plan-manager-minimal.md`
- `/.claude/agents/agent-plan-implementer.md`
- `/.claude/agents/agent-plan-implementer-full.md`
- `/.claude/agents/agent-plan-implementer-minimal.md`

**Integration Requirements** (~75-100 tokens per agent):
- Add compaction trigger monitoring (token thresholds + phase boundaries)
- Implement context formatting for compaction agent transfer
- Create compaction agent invocation protocol
- Add resumption summary integration capabilities

## Phase 3: File Structure & Git Integration (45 min)

### Plan-Specific Directory Structure
**Implementation**:
- Update compaction agent to create `solarwindpy/plans/<plan-name>/compacted_state.md`
- Ensure multi-developer safety with isolated compaction states
- Add directory creation logic for new plans

### Git Integration Protocol
**Commit Pattern**: `compaction: [plan] phase [N] - [ratio] reduction`
**Tagging System**: `compaction-[plan-name]-phase-[N]-[timestamp]`
**Files Committed**: Both plan updates and compacted_state.md

## Phase 4: Compacted State Template (30 min)

### Create Structured Template
**File Format** (`compacted_state.md`):
```markdown
# Compacted Context State - [Plan Name]
## Compaction Metadata
## Current State Summary
## Progress Snapshot
## Compacted Context Archive
## Resumption Instructions
```

**Dynamic Content Generation**:
- Agent-specific context processing
- Phase history compression
- Next session priority identification
- Quick win opportunity detection

## Phase 5: Testing & Validation (45 min)

### Comprehensive Testing
- Test compaction across all 6 agent complexity tiers
- Validate session resumption quality after compression
- Verify git integration with proper commits and tags
- Test parallel plan compaction (multi-developer scenarios)
- Performance test with various token thresholds

### Integration Validation
- Verify seamless compaction request/response workflow
- Test cross-agent coordination preservation
- Validate file isolation prevents conflicts
- Confirm target compression ratios achieved

## Success Criteria
- **Token Efficiency**: 350+ token savings vs integrated approach
- **Universal Compatibility**: Single agent handles all 6 planning/implementation variants  
- **Multi-Developer Safety**: No compaction file conflicts in parallel development
- **Quality Preservation**: Maintain development continuity across sessions
- **Architecture Cleanliness**: Clean separation between core agents and compaction service

## Implementation Approach
- Build universal compaction agent as centralized service
- Add minimal integration touchpoints to existing agents
- Use plan-specific subdirectories for conflict-free multi-developer workflow
- Implement tiered compression matching agent complexity levels
- Create seamless git integration with meaningful commit messages and tags

This service-oriented architecture will enable sustained development on complex plans while maintaining existing agent quality and coordination capabilities, with significant token efficiency improvements.