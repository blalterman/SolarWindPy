# Session Continuity Protocol - Plan Manager Integration

## Overview

This protocol is now **integrated into the enhanced Plan Manager agent** which provides systematic procedures to maintain development focus and prevent context switching. The Plan Manager automatically handles session state validation and productive development continuity.

## Integration Note

**Primary Implementation**: Enhanced Plan Manager agent (`/.claude/agents/agent-plan-manager.md`)  
**This Document**: Reference protocol for understanding the systematic approach now built into Plan Manager

## Core Principles

### 1. Git-First Validation
**Philosophy:** Git commit history is the authoritative source of truth for project state
- Session state files are **secondary indicators** that may become stale
- Always cross-reference session state claims with actual git commits
- Resolve discrepancies by favoring git evidence over session file content

### 2. Infrastructure Priority Framework  
**Development Priority Order:**
1. **Critical Infrastructure** (CI/CD failures, build system issues)
2. **Active Plans** (90%+ complete work requiring finishing touches)  
3. **New Features** (planned feature development)
4. **Enhancements** (optimization, refactoring, documentation improvements)

### 3. Context Switching Prevention
**Rule:** Complete active work before starting new initiatives
- Finish partially completed infrastructure work first
- Avoid abandoning high-completion work for new projects
- Use compaction system to extend sessions rather than switching contexts

## Pre-Session Validation Checklist

### Step 1: Session State Accuracy Verification (5 min)
```bash
# Check git status and recent commits
git status
git log --oneline -10

# Review session state file
cat claude_session_state.md

# Cross-validate session state claims with git evidence
git log --grep="[claimed-work]" --oneline
```

**Validation Questions:**
- [ ] Does session state completion status match git commit evidence?
- [ ] Are "remaining tasks" actually remaining or completed in git history?
- [ ] Do git commit messages support session state timeline claims?
- [ ] Are file modification claims verifiable in git history?

### Step 2: Active Plan Status Assessment (5 min)
```bash
# Check for active plan branches
git branch -r --no-merged master

# Check for plan files in high completion states
find solarwindpy/plans -name "*.md" -exec grep -l "90%\|95%\|85%" {} \;

# Look for compacted states indicating active work
find solarwindpy/plans -name "compacted_state.md"
```

**Assessment Questions:**
- [ ] Are there any plans at 85%+ completion requiring finishing touches?
- [ ] Do any plan branches exist that need merging or continuation?
- [ ] Are there compacted states indicating interrupted development sessions?
- [ ] What infrastructure work is pending completion?

### Step 3: Development Context Priority Ranking (5 min)

**Priority 1: Critical Infrastructure Issues**
- CI/CD pipeline failures or warnings
- Build system problems or dependency conflicts
- Documentation build failures or validation issues
- Requirements management inconsistencies

**Priority 2: High-Completion Active Plans**
- Plans showing 85%+ completion in session state
- Work with only 1-2 remaining tasks to finish
- Infrastructure improvements with validated benefits

**Priority 3: New Feature Development**
- Planned features from project roadmap
- New analysis tools or visualization capabilities
- Performance optimization initiatives

**Priority 4: Enhancement Work** 
- Code quality improvements
- Documentation enhancements
- Refactoring for maintainability

## Context Switching Prevention Framework

### Decision Matrix for New Work Requests

```
Is there Critical Infrastructure work pending?
├── YES → Complete infrastructure first (Priority 1)
└── NO ↓

Is there Active Plan work at 85%+ completion?
├── YES → Complete active plan first (Priority 2)  
└── NO ↓

Is requested work aligned with current development context?
├── YES → Proceed with new work (Priority 3/4)
└── NO → Use compaction system to preserve current context, then proceed
```

### Context Preservation Before Switching

When context switching is unavoidable:

1. **Document Current State** (10 min)
   - Update session state with accurate completion percentage
   - Reference specific git commits proving completion status
   - Document exact remaining tasks with time estimates

2. **Use Compaction System** (5 min)
   - Invoke appropriate planning/implementation agent pairing
   - Trigger compaction to preserve current context
   - Verify compacted state creation and git commit

3. **Create Resumption Plan** (5 min)
   - Document resumption priorities and next immediate tasks
   - Identify required specialist agents for continuation
   - Set timeline expectations for returning to preserved work

## Git-Integrated Progress Tracking

### Session State Synchronization Protocol

**After Each Major Milestone:**
1. **Git Commit Evidence**
   ```bash
   git add .
   git commit -m "milestone: complete [specific work] 
   
   [Description of completion]
   
   Generated with Claude Code
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

2. **Session State Update**
   - Reference specific git commit hashes as evidence
   - Update completion percentages based on git evidence
   - Remove outdated "remaining tasks" that are now committed

3. **Cross-Validation**
   ```bash
   # Verify session state claims match git reality
   git log --grep="[claimed-work]" --stat
   git diff [previous-commit] HEAD --name-only
   ```

### Automated Validation Triggers

**After Every 3 Commits:**
- Cross-check session state against git history
- Identify and correct any discrepancies
- Update completion percentages based on actual progress

**Before Starting New Major Work:**
- Run full pre-session validation checklist
- Resolve any session state inaccuracies
- Confirm priority alignment with development framework

## Session Continuity Optimization

### Extended Session Management

**Token Budget Awareness:**
- Monitor token usage and plan compaction triggers
- Use appropriate agent pairings for optimal efficiency
- Leverage compaction system for 2-3x session extension

**Quality Maintenance During Extended Sessions:**
- Maintain testing standards throughout extended sessions
- Preserve specialist agent coordination across compressions
- Ensure physics validation and numerical stability checks

**Compaction Timing Strategy:**
- Trigger compaction at phase boundaries for optimal context preservation
- Use manual compaction before complex multi-phase work
- Preserve specialist integration points during compression

### Cross-Session Workflow Optimization

**Session Handoff Preparation:**
1. Complete validation of all session state claims
2. Update session state with git commit references
3. Create compacted state for complex active work
4. Document clear resumption priorities and context

**Session Resumption Best Practices:**
1. Run pre-session validation checklist
2. Verify git branch alignment and recent commits  
3. Load appropriate agent pairing based on work context
4. Re-establish specialist agent coordination as needed

## Error Recovery Procedures

### Session State Corruption Recovery
1. **Identify Corruption Indicators**
   - Session state claims contradicted by git evidence
   - Impossible completion percentages or timelines
   - Missing or incorrect file modification references

2. **Recovery Process**
   - Discard corrupted session state content
   - Reconstruct accurate state from git commit history
   - Cross-validate reconstruction with actual file states
   - Document recovery process for future reference

### Development Context Loss Recovery
1. **Assess Context Loss Scope**
   - Determine what development context was lost
   - Identify impact on current and planned work
   - Evaluate recovery effort required

2. **Context Reconstruction**
   - Use git history to reconstruct development timeline
   - Review recent commits and branch history for clues
   - Re-establish specialist agent coordination as needed
   - Resume development with reconstructed context

## Success Metrics

### Session Continuity Quality Indicators
- **Context Accuracy:** Session state matches git evidence 100% of time
- **Development Velocity:** Maintained or improved development speed
- **Work Completion:** High-completion work (85%+) finished before new work starts
- **Infrastructure Priority:** Critical infrastructure addressed before feature work

### Productivity Optimization Metrics  
- **Session Extension:** 2-3x longer productive sessions via compaction
- **Context Switching:** Minimized unproductive context switches
- **Work Completion Rate:** Improved completion rate for started initiatives
- **Quality Maintenance:** Maintained code quality and testing standards

This protocol ensures sustained, focused development while maintaining the high-quality standards expected in scientific computing environments. By validating session state against git reality and prioritizing infrastructure work, it prevents the productivity losses associated with context switching and incomplete work.