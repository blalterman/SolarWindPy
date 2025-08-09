# Agent Integration Guidelines - Compaction Workflows

## Overview

This guide provides standardized procedures for how planning and implementation agents integrate with the CompactionAgent to enable extended development sessions. These workflows ensure consistent, reliable context compression and session continuity across all agent variants.

## Compaction Integration Architecture

### Service-Oriented Model
- **CompactionAgent** operates as a universal service for all planning/implementation agents
- **Transparent Integration** - compaction occurs seamlessly within existing workflows
- **Automatic Triggers** - no manual intervention required for standard operations
- **Context Preservation** - essential development state maintained across compressions

## Trigger Mechanisms

### 1. Token Threshold Triggers (Primary)
**Threshold:** 80% of source agent token limit
- **PlanManager-Full:** 965 tokens (80% of 1,207)
- **PlanManager-Streamlined:** 781 tokens (80% of 976)
- **PlanManager-Minimal:** 442 tokens (80% of 553)
- **PlanImplementer-Full:** 1,215 tokens (80% of 1,519)
- **PlanImplementer (Research-Optimized):** 1,120 tokens (80% of 1,400)
- **PlanImplementer-Minimal:** 222 tokens (80% of 278)

### 2. Phase Boundary Triggers (Strategic)
**Natural Compaction Points:**
- Planning → Implementation transition
- Completed implementation phases (testing, validation, documentation)
- Specialist agent handoffs (PhysicsValidator, TestEngineer integration)
- Major milestone completions

### 3. Manual Triggers (On-Demand)
**User-Initiated Scenarios:**
- Session pause/resume requests
- Context optimization for performance
- Pre-emptive compression before complex work
- Error recovery and state preservation

### 4. Session Boundary Triggers (Automatic)
**End-of-Session Preservation:**
- Automatic compaction before session timeout
- State preservation for next session resumption
- Cross-session coordination maintenance

## Context Preparation Workflows

### Planning Agent Context Preparation

#### PlanManager-Full Context Format
```markdown
## Source Agent Metadata
- Agent Type: Plan Manager Full (Enterprise)
- Current Phase: [phase name and progress percentage]
- Token Count: [current usage]/1207 tokens
- Complexity Tier: High

## Context to Compress
### Strategic Planning State
- [Multi-phase plan structure with dependencies]
- [Cross-plan coordination requirements]
- [Time estimation and velocity tracking]
- [Risk assessment and mitigation strategies]

### Specialist Agent Coordination
- [Domain specialist integration points]
- [Quality assurance coordination]
- [Cross-agent handoff requirements]

### Implementation Readiness
- [Plan activation status and branch management]
- [Acceptance criteria and validation requirements]
- [Resource allocation and timeline constraints]
```

#### PlanManager-Streamlined Context Format
```markdown
## Source Agent Metadata  
- Agent Type: Plan Manager Streamlined (Pro-Optimized)
- Current Phase: [phase name and progress percentage]
- Token Count: [current usage]/976 tokens
- Complexity Tier: Medium

## Context to Compress
### Core Planning State
- [Current phase objectives and next tasks]
- [Implementation plan structure and dependencies]
- [Time estimates and progress tracking]

### Integration Requirements
- [Specialist agent coordination needs]
- [Quality checkpoints and validation]
- [Branch management and plan activation]
```

#### PlanManager-Minimal Context Format
```markdown
## Source Agent Metadata
- Agent Type: Plan Manager Minimal (Heavy Usage Optimized)
- Current Phase: [phase name and progress percentage] 
- Token Count: [current usage]/553 tokens
- Complexity Tier: Low

## Context to Compress
### Essential Planning State
- [Current objectives and immediate next tasks]
- [Basic plan structure and key dependencies]
- [Simple progress tracking and completion status]
```

### Implementation Agent Context Preparation

#### PlanImplementer-Full Context Format
```markdown
## Source Agent Metadata
- Agent Type: Plan Implementer Full (Enterprise)
- Current Phase: [implementation phase and status]
- Token Count: [current usage]/1519 tokens
- Complexity Tier: High

## Context to Compress
### Implementation State
- [Comprehensive implementation progress and status]
- [Quality assurance integration and validation results]
- [Complex dependency management and coordination]
- [Enterprise-grade testing and deployment status]

### Specialist Integration
- [PhysicsValidator, TestEngineer, DataFrameArchitect coordination]
- [Cross-module integration and testing status]
- [Performance optimization and validation results]
```

#### PlanImplementer (Research-Optimized) Context Format
```markdown
## Source Agent Metadata
- Agent Type: Plan Implementer (Research-Optimized)
- Current Phase: [implementation phase and status]
- Token Count: [current usage]/1400 tokens
- Complexity Tier: Medium

## Context to Compress
### Development State
- [Scientific implementation progress and status]
- [Research methodology and validation approach]
- [Physics correctness and numerical stability]
- [Testing integration and quality checkpoints]

### Technical Context
- [Algorithm implementation and optimization]
- [Data structure management and MultiIndex handling]
- [Specialist agent coordination and handoffs]
```

#### PlanImplementer-Minimal Context Format
```markdown
## Source Agent Metadata
- Agent Type: Plan Implementer Minimal (Lightweight)
- Current Phase: [implementation status]
- Token Count: [current usage]/278 tokens
- Complexity Tier: Low

## Context to Compress
### Essential Implementation State
- [Current task status and immediate next actions]
- [Basic progress tracking and completion markers]
- [Simple dependency and coordination requirements]
```

## Compaction Invocation Protocol

### Standard Invocation Sequence
```
1. Source Agent Detects Trigger (token threshold/phase boundary)
2. Source Agent Prepares Context using appropriate format
3. Source Agent Invokes CompactionAgent with structured request
4. CompactionAgent Processes context using appropriate complexity tier
5. CompactionAgent Creates compacted_state.md in plan-specific directory
6. CompactionAgent Executes git commit with metadata and tagging
7. CompactionAgent Returns resumption summary to source agent
8. Source Agent Continues workflow with reduced context footprint
```

### Error Handling Protocol
```
1. Compaction Request Validation
   └── Invalid format → Return error with correction guidance
2. Directory Creation Validation  
   └── Permission error → Attempt alternative location
3. Git Operation Validation
   └── Commit failure → Retry with minimal metadata
4. Context Processing Validation
   └── Corruption detected → Graceful degradation to essential-only
5. Recovery Procedures
   └── Complete failure → Return original context with warning
```

## Resumption Workflows

### Session Resumption Checklist
When resuming from compacted state:

1. **Read Compacted State File**
   - Location: `solarwindpy/plans/<plan-name>/compacted_state.md`
   - Verify compaction metadata and compression ratio
   - Review resumption instructions and next priorities

2. **Validate Git Context**
   - Check current branch alignment with plan branch
   - Verify recent commits match compacted state references
   - Ensure no conflicts or uncommitted changes

3. **Re-establish Agent Context**
   - Load appropriate planning/implementation agent based on compacted metadata
   - Initialize agent with resumption summary from compacted state
   - Verify token budget and compaction strategy alignment

4. **Restore Specialist Coordination**
   - Review integration points preserved in compacted state
   - Re-engage domain specialists as specified in resumption instructions
   - Validate cross-agent coordination and handoff requirements

5. **Continue Development Workflow**
   - Execute immediate next tasks from resumption priorities
   - Monitor token usage for next compaction trigger
   - Maintain quality standards and testing requirements

## Quality Assurance Integration

### Specialist Agent Coordination During Compaction
- **PhysicsValidator**: Physics correctness validation requirements preserved
- **TestEngineer**: Test coverage and quality checkpoint preservation
- **DataFrameArchitect**: MultiIndex structure and memory optimization context
- **PerformanceOptimizer**: Performance requirements and optimization context
- **DocumentationMaintainer**: Documentation standards and requirements

### Cross-Agent Handoff Protocols
```
1. Pre-Compaction Specialist State Capture
   - Current validation status and requirements
   - Integration points and coordination needs
   - Quality checkpoints and acceptance criteria

2. Compaction Processing with Specialist Context
   - Preserve specialist coordination requirements
   - Maintain quality standards and validation needs
   - Archive completed specialist validations

3. Post-Compaction Specialist Re-engagement
   - Restore specialist context from compacted state
   - Re-establish coordination and communication
   - Validate continued quality standards
```

## Performance Optimization

### Token Efficiency Targets
- **System Overhead:** <5% of total session token budget
- **Compression Ratios:** Meet or exceed targets for each complexity tier
- **Processing Speed:** <30 seconds per compaction operation
- **Context Accuracy:** 100% preservation of essential development state

### Memory and Storage Optimization
- **File Size Management:** Compacted states optimized for quick loading
- **Git Repository Impact:** Minimal repository size increase
- **Directory Organization:** Efficient plan-specific file structure
- **Cleanup Procedures:** Automatic archival of outdated compacted states

## Troubleshooting Guide

### Common Issues and Solutions

**Token Threshold Not Triggering Compaction:**
- Verify token counting accuracy in source agent
- Check for threshold configuration mismatches
- Validate trigger detection logic

**Context Loss During Compaction:**
- Review context preparation format compliance
- Check compaction tier appropriate for complexity
- Validate essential context identification

**Git Integration Failures:**
- Verify repository permissions and branch status
- Check directory creation and file write permissions
- Validate git configuration and commit message format

**Session Resumption Problems:**
- Verify compacted state file integrity and format
- Check git branch alignment and recent commit history
- Validate agent type matching and context restoration

**Performance Degradation:**
- Monitor compaction processing time and optimize if needed
- Check file system performance and storage availability
- Validate token budget calculations and efficiency metrics

This integration guide ensures consistent, reliable compaction workflows across all SolarWindPy development contexts while maintaining the high quality standards expected in scientific computing environments.