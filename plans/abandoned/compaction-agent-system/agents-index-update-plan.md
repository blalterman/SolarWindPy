# Update Agents Index for Compaction Agent Integration

## Objective
Update the agents index (`/.claude/agents/agents-index.md`) to properly integrate the new CompactionAgent into the SolarWindPy agent ecosystem with appropriate categorization, workflows, and coordination protocols.

## Integration Strategy

### Category Placement
**Add to Planning & Implementation Category**: The CompactionAgent is a service agent that supports planning and implementation workflows, making this the natural fit.

### Priority Assessment
**Medium Priority**: CompactionAgent is called by other agents rather than being a primary decision-maker, so it falls between High (core workflow) and Low (maintenance) priority.

## Updates Required

### 1. Agent Categories Section
**Add to Planning & Implementation category**:
```markdown
### 🎯 Planning & Implementation
- **[CompactionAgent](./agent-compaction.md)** - Context compression and session continuity service
```

### 2. Quick Reference Table
**Add new row**:
```markdown
| CompactionAgent | Medium | Context compression & session continuity | `solarwindpy/plans/*/compacted_state.md` |
```

### 3. Agent Coordination Workflows
**Add new workflow diagram**:
```mermaid
### Long-Duration Development Session
graph LR
    A[Planning Agent] --> B[Implementation Work]
    B --> C{Token Threshold?}
    C -->|Yes| D[CompactionAgent]
    D --> E[Compacted State + Git Commit]
    E --> F[Session Resume]
    C -->|No| G[Continue Work]
```

### 4. Agent Communication Protocol
**Add CompactionAgent usage rules**:
- **Automatic Triggers**: Token thresholds (80% of agent limit), phase boundaries
- **Service Model**: Called by planning/implementation agents, not directly invoked
- **Cross-Session Bridge**: Enables session continuity across token limit boundaries

### 5. Common Tasks Section
**Add new task category**:
```markdown
### Managing Long Development Sessions
1. **PlanningAgent/ImplementationAgent**: Detect compaction triggers
2. **CompactionAgent**: Compress context and preserve essential state
3. **Git Integration**: Commit compacted state with metadata
4. **Session Resumption**: Restore compressed context for continuation
```

### 6. Agent Expertise Matrix
**Add compaction-related tasks**:
```markdown
| Context compression | CompactionAgent | Planning/Implementation Agents |
| Session continuity | CompactionAgent | All agents |
| Long-term state management | CompactionAgent | PlanManager variants |
```

### 7. Best Practices Section
**Add compaction considerations**:
```markdown
### Code Review Checklist
- [ ] CompactionAgent: Session continuity preserved?
- [ ] CompactionAgent: Essential context maintained?
```

### 8. Future Enhancements Section
**Move CompactionAgent from "Planned" to current agents**:
```markdown
### Recently Added Agents
- **CompactionAgent**: Context compression and session continuity (2025-08-09)
```

## Implementation Tasks

### Phase 1: Document Structure Updates (30 min)
- Add CompactionAgent to Planning & Implementation category
- Update Quick Reference Table with priority and file focus
- Add CompactionAgent to Agent Communication Protocol

### Phase 2: Workflow Integration (20 min)
- Create Long-Duration Development Session workflow diagram
- Add CompactionAgent usage rules and trigger conditions
- Update collaboration rules for service agent model

### Phase 3: Task & Expertise Updates (20 min)
- Add "Managing Long Development Sessions" to Common Tasks
- Update Agent Expertise Matrix with compaction tasks
- Add compaction considerations to Best Practices

### Phase 4: Validation & Formatting (10 min)
- Verify Mermaid diagram syntax
- Check markdown formatting and table alignment
- Validate links and references

## Success Criteria
- **Proper Categorization**: CompactionAgent correctly placed in Planning & Implementation
- **Clear Service Model**: Documentation shows CompactionAgent as service called by others
- **Complete Integration**: All relevant sections updated with compaction workflows
- **Consistent Formatting**: Maintains existing document style and structure

This update establishes CompactionAgent as a first-class citizen in the agent ecosystem while clearly defining its service role and integration points with the existing planning and implementation workflow.