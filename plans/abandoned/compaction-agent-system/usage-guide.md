# Compaction Agent System - Usage Guide

## Overview

The compaction agent system provides automatic context compression and session continuity for long development workflows. This system enables 2-3x longer productive sessions by compressing context at phase boundaries while preserving all essential information.

## System Components

### Universal Compaction Agent
- **Location**: `/.claude/agents/agent-compaction.md`
- **Role**: Service-oriented universal compressor for all planning/implementation agents
- **Capabilities**: 40-70% context reduction with structured state preservation

### Enhanced Planning/Implementation Agents
All 6 agent variants now include compaction integration:
- Plan Manager: Full, Streamlined, Minimal
- Plan Implementer: Full, Research-Optimized, Minimal

## How It Works

### Automatic Triggers
1. **Token Threshold**: Compaction activates at 80% of agent token limit
2. **Phase Boundaries**: Natural compaction points between development phases  
3. **Manual Request**: User-initiated compaction commands
4. **Session End**: State preservation for next session

### Compaction Process
```
Current Session Context → CompactionAgent → Compacted State File
     (3000 tokens)           (Processing)        (1200 tokens)
                                ↓
                         Git Commit + Tag
                                ↓
                        Session Continuation
```

## File Structure

### Directory Organization
```
solarwindpy/plans/
├── <plan-name>/
│   ├── compacted_state.md          # CompactionAgent output
│   ├── [plan-name].md             # Original plan file
│   └── [other-plan-files]         # Supporting docs
└── compaction-agent-system/       # This system's docs
```

### Multi-Developer Safety
- Plan-specific subdirectories prevent file conflicts
- Isolated compaction states for different plans
- Git integration with proper branching support

## Usage Instructions

### For Planning Sessions
1. Use any Plan Manager variant (Full/Streamlined/Minimal)
2. System automatically monitors token usage
3. At 80% threshold, compaction is triggered automatically
4. Compacted state saved to `plans/<plan-name>/compacted_state.md`
5. Git commit created with metadata
6. Session continues with reduced context

### For Implementation Sessions  
1. Use any Plan Implementer variant (Full/Research-Optimized/Minimal)
2. System tracks implementation progress and token usage
3. Phase boundary compaction preserves completed work
4. Resume with context optimized for next phase
5. Cross-agent coordination maintained

### Manual Compaction
When you need to manually trigger compaction:
1. Request compaction from your current planning/implementation agent
2. Agent will invoke CompactionAgent automatically  
3. Compacted state will be saved and committed
4. Receive resumption summary for continuation

## Token Efficiency

### Compression Targets by Agent Type

**High-Complexity Sources** (Plan Manager Full, Plan Implementer Full):
- Target: 40-60% reduction
- Example: 3000 → 1200 tokens, 2800 → 1120 tokens

**Medium-Complexity Sources** (Streamlined, Research-Optimized):  
- Target: 50-70% reduction
- Example: 1400 → 420 tokens, 1000 → 300 tokens

**Low-Complexity Sources** (Minimal variants):
- Target: Maintain efficiency 
- Example: 300 → 200-250 tokens

## Session Continuity

### Context Recovery
When resuming a session after compaction:
1. Read the `compacted_state.md` file from your plan directory
2. Review "Next Session Priorities" section
3. Check "Session Startup Checklist" 
4. Switch to appropriate git branch if needed
5. Re-engage any required specialist agents

### Information Preserved
- Current objectives and immediate next tasks
- Critical dependencies and blockers  
- Progress status and completion percentages
- Key commits and deliverables
- Integration points with specialist agents

### Information Archived  
- Verbose historical descriptions
- Auxiliary context and background information
- Completed phase details (summarized)
- Debug information and exploration notes

## Git Integration

### Commit Format
```
compaction: <plan-name> phase <N> - <percentage>% reduction

- Compressed context from <original-tokens> to <compressed-tokens> tokens  
- Phase: <current-phase-name>
- Compaction tier: <High/Medium/Low>-complexity processing

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Tagging System
Tags follow format: `compaction-<plan-name>-phase-<N>-<timestamp>`

Example: `compaction-solar-activity-enhancement-phase-3-20250809-143022`

## Best Practices

### Planning Phase
- Use appropriate agent variant for complexity level
- Allow natural phase boundaries for optimal compaction timing
- Maintain clear phase structure for better compression
- Document critical dependencies clearly

### Implementation Phase
- Follow established plan structure for consistent compaction
- Test and validate before phase boundaries
- Use specialist agents for domain expertise
- Maintain clear commit patterns

### Multi-Session Development
- Always review compacted state before continuing
- Validate git branch status and recent commits
- Re-establish specialist agent coordination
- Check for any dependency changes

## Troubleshooting

### Common Issues

**Compaction Fails**:
- Check directory permissions for plan subdirectory creation
- Verify git status and resolve any conflicts
- Ensure proper git branch state

**Context Loss**:  
- Check compacted_state.md for preserved information
- Review git commit message for compaction details
- Use git history to trace recent changes

**File Conflicts**:
- Plan-specific directories should prevent conflicts
- If conflicts occur, use git merge tools
- Contact system administrator for persistent issues

### Recovery Procedures

**Corrupted Compacted State**:
1. Check git history for last known good state
2. Use `git log --oneline | grep compaction` to find compaction commits
3. Restore from backup compaction commit if needed

**Missing Context**:
1. Review plan file and recent commits for context clues
2. Check specialist agent coordination points
3. Restart implementation phase if necessary

## Performance Metrics

### Success Indicators
- Session length increased 2-3x over baseline
- No workflow interruption during compaction
- Successful context recovery in next session
- Maintained specialist agent coordination

### Quality Metrics  
- Zero critical context loss affecting continuation
- Preserved integration points with domain specialists
- Maintained project momentum across session boundaries
- Proper git history with meaningful commit messages

## Support

For issues with the compaction system:
1. Check this usage guide for common solutions
2. Review the compacted_state.md file for context clues
3. Check git history for recent compaction commits
4. Review the implementation plan at `solarwindpy/plans/compaction-agent-system/implementation-plan.md`

The compaction agent system transforms long development sessions from context-limited to session-spanning, enabling sustained work on complex projects while maintaining quality and coordination.