# Checkpointing

**Feature Type:** Automatic
**Priority:** LOW-MEDIUM
**Effort:** 3-4.5 hours
**ROI Break-even:** 3-5 weeks

[← Back to Index](./INDEX.md) | [Previous: Enhanced Hooks ←](./04_enhanced_hooks.md) | [Next: Output Styles →](./06_output_styles.md)

---

**⚠️ PREREQUISITES: PHASE 2 (CONDITIONAL)**

**Note:** Checkpointing has no technical dependencies but is part of Phase 2 organizational structure.

**Recommended to complete Phase 1 first:**
- ✅ Memory Hierarchy (01) + Slash Commands (07) implemented (Phase 0)
- ✅ Skills System (02) + Subagents (03) implemented (Phase 1)
- ✅ Decision Gate 2 PASSED (≥40% automation, positive team feedback)

**See [EXECUTOR_GUIDE.md](./EXECUTOR_GUIDE.md) for correct implementation sequence.**

---

**ℹ️ NOT A PLUGIN FEATURE - Core Claude Code Capability**

Checkpointing is a built-in Claude Code feature (automatic edit tracking). Not configurable or plugin-related.

---

## Feature 5: Checkpointing

### 1. Feature Overview

**What It Is:**
Automatic tracking system that captures code states before each edit operation. Functions as "local undo" for file modifications within Claude Code sessions, independent of git version control.

**Core Capabilities:**
- **Automatic tracking** - Every Edit/Write creates checkpoint before modification
- **Session persistence** - Checkpoints survive across resumed conversations
- **Independent rewind** - Revert code OR conversation independently
- **30-day retention** - Auto-cleanup after 30 days (configurable)
- **Safety net** - Quickly undo changes that broke functionality

**What It Doesn't Track:**
❌ Bash command modifications (file deletions, moves, copies)
❌ Manual edits outside Claude Code
❌ Changes from concurrent sessions

**Maturity & Prerequisites:**
- ✅ Production-ready feature
- ✅ No configuration required (works out-of-the-box)
- ✅ Zero setup overhead
- ⚠️ Not a replacement for git (local undo only)

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Repetitive Task Automation (LOW IMPACT)**
*Current state:* Manual git stash/commit for experimental changes
*With Checkpointing:* Automatic checkpoint before each edit
*Improvement:* Zero-overhead safety net for experimentation

✅ **Context Preservation (MEDIUM IMPACT)**
*Current state:* Context lost when reverting code changes
*With Checkpointing:* Can keep conversation context while reverting code
*Benefit:* Maintain discussion thread even when undoing implementation

✅ **Agent Coordination (LOW IMPACT)**
*Current state:* Agent refactoring mistakes require manual rollback
*With Checkpointing:* Quick revert to pre-agent state
*Improvement:* Safer delegation (easy rollback if agent makes errors)

**Productivity Improvements:**
- Fearless experimentation (easy revert)
- Faster iteration (try approaches without git ceremony)
- Reduced git pollution (avoid temporary commits for experiments)

**Research Workflow Enhancements:**
- Try multiple analysis approaches
- Compare implementation variants
- Quick rollback when approach doesn't work

### 3. Integration Strategy

**Architecture Fit:**

Checkpointing complements git workflow:

```
Git (Permanent History)
├── Feature branches
├── Commits
└── Push to remote

Checkpointing (Local Undo)
├── Automatic before edits
├── Session-scoped
└── 30-day retention

Use Cases:
- Git: Permanent record, team collaboration
- Checkpoints: Temporary experiments, quick undo
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **Git Workflow** | Checkpoints are pre-commit safety net |
| **Agent Edits** | Automatic checkpoint before agent modifications |
| **Hook System** | PostToolUse hooks could validate checkpoints |
| **Testing** | Revert to checkpoint if tests fail |

**Backward Compatibility:**
✅ **Fully compatible** - Checkpointing is automatic, non-invasive
✅ **No configuration needed**
✅ **Coexists with git** (orthogonal systems)

#### Approval Gate Integration

**Purpose:** Checkpointing reduces risk of expensive subagent operations, making approval gates less of a barrier to experimentation.

**Checkpoint-Before-Expensive-Operation Pattern:**

When a subagent operation triggers an approval gate (e.g., PhysicsValidator with >800 token threshold), Claude Code automatically creates a checkpoint before proceeding. This provides:

1. **Safety net:** If subagent edits break functionality, revert to pre-operation state instantly
2. **Confidence boost:** Approval becomes lower-stakes decision ("I can always undo this")
3. **Exploration enablement:** Try expensive analysis without fear of irreversible changes

**Workflow Example:**

```
User: "Validate all physics calculations across the entire codebase"
    ↓
Approval Gate Triggers:
⚠️ PhysicsValidator Activation Request
   Estimated tokens: 12,000 (24% of session budget)
   Estimated time: 18-22 minutes (timeout: 25 min)
   Files to analyze: 15 physics modules

   💾 Automatic checkpoint will be created before operation

   [Proceed] [Skip] [Reduce Scope]
    ↓
User: [Proceed]
    ↓
Claude creates checkpoint → Invokes PhysicsValidator subagent
    ↓
Subagent completes, suggests refactoring in 8 files
    ↓
User reviews changes:
  Option A: Accept → Commit changes to git
  Option B: Reject → Revert to checkpoint (immediate undo)
```

**Modified Approval Gate Display:**

```
⚠️ SubagentActivation Request
   Subagent: FitFunctionSpecialist
   Estimated context: 7,500 tokens (15% of budget)
   Estimated time: 12-15 minutes

   💾 Checkpoint: Automatic before operation
   🔄 Rollback: Available via "Revert to checkpoint" if needed

   Risk: Low (checkpointed, reversible, budget < 20%)

   [Proceed] [Skip] [Reduce Scope]
```

**Integration Benefits:**

- **Psychological safety:** "Can always revert" mindset encourages experimentation
- **Reduced friction:** Approval gates feel less consequential with automatic rollback
- **Exploratory analysis:** Try expensive subagent operations without permanent code changes
- **Learning opportunity:** Safe to test subagent behavior without breaking existing code

### 3.5. Risk Assessment

#### Technical Risks

**Risk: Checkpoint Storage Accumulation**
- **Likelihood:** Medium
- **Impact:** Low (disk space consumption)
- **Mitigation:**
  - Claude Code manages checkpoint lifecycle automatically
  - Checkpoints are ephemeral (not long-term storage)
  - Monitor `.claude/checkpoints/` directory size if exposed
  - Trust automatic cleanup mechanisms
  - No action required from user

**Risk: Checkpoint Restoration Failures**
- **Likelihood:** Low
- **Impact:** High (can't undo problematic changes)
- **Mitigation:**
  - Test checkpoint restoration in safe scenarios
  - Maintain git commits as primary rollback mechanism
  - Don't rely solely on checkpoints for critical changes
  - Document checkpoint limitations
  - Use git for permanent version control

**Risk: Confusion Between Checkpoints and Git Commits**
- **Likelihood:** Medium
- **Impact:** Low-Medium (workflow inefficiency)
- **Mitigation:**
  - Document clear distinction: checkpoints = session-level, git = permanent
  - Use checkpoints for iterative exploration
  - Use git commits for validated changes
  - Train team on dual-system model
  - Emphasize checkpoints as safety net, not primary versioning

**Risk: Checkpoint Overhead in Large Codebases**
- **Likelihood:** Low
- **Impact:** Low (minor latency)
- **Mitigation:**
  - Checkpointing is optimized by Anthropic
  - Automatic, no user intervention
  - Monitor for any performance degradation
  - Trust native implementation efficiency

#### Adoption Risks

**Risk: Over-Reliance on Checkpoints**
- **Likelihood:** Medium
- **Impact:** Medium (skip proper git commits)
- **Mitigation:**
  - Emphasize checkpoints as ephemeral
  - Enforce git commit discipline via hooks
  - Document checkpoint expiration behavior
  - Use pre-commit hooks to require commits
  - Training: "Checkpoints for sessions, commits for history"

**Risk: Unawareness of Checkpointing Feature**
- **Likelihood:** High
- **Impact:** Low (missed opportunity, not harmful)
- **Mitigation:**
  - Include in onboarding documentation
  - Demonstrate checkpoint usage in training
  - Provide `/checkpoint` command examples
  - Document recovery scenarios
  - Create quick reference guide

#### Operational Risks

**Risk: Checkpoint Restoration Without Context**
- **Likelihood:** Low
- **Impact:** Medium (restore to unexpected state)
- **Mitigation:**
  - Always review checkpoint details before restoring
  - Use descriptive checkpoint names
  - Check git status before and after restoration
  - Test in isolated branch if uncertain
  - Document common restoration scenarios

**Risk: No Visibility Into Checkpoint Status**
- **Likelihood:** Medium
- **Impact:** Low (uncertainty about checkpoint coverage)
- **Mitigation:**
  - Use `/checkpoint list` to view available checkpoints
  - Document checkpoint viewing commands
  - Create mental model: Claude handles it automatically
  - Trust automatic checkpoint creation at key moments
  - Focus on git for explicit control

### 4. Implementation Specification

#### No Implementation Required

Checkpointing works out-of-the-box. This section documents **usage patterns** and **integration best practices** for SolarWindPy workflow.

#### Usage Patterns

##### Pattern 1: Experimental Refactoring
```
Scenario: Agent proposes DataFrame optimization
1. Agent creates checkpoint automatically before Edit
2. Agent implements optimization
3. Run tests: pytest --cov=solarwindpy -q
4. If tests fail → Revert to checkpoint
5. If tests pass → Keep changes, commit to git
```

##### Pattern 2: Multi-Approach Comparison
```
Scenario: Try 3 different physics validation approaches
1. Implement Approach 1 (checkpoint auto-created)
2. Test and measure performance
3. Revert to checkpoint
4. Implement Approach 2 (new checkpoint)
5. Test and measure
6. Revert to checkpoint
7. Implement Approach 3 (new checkpoint)
8. Compare results, keep best approach
9. Commit winner to git
```

##### Pattern 3: Conversation-Code Decoupling
```
Scenario: Long discussion about implementation, want to revert code but keep conversation
1. Extended discussion with multiple edit attempts
2. Code evolves through several checkpoints
3. Decide to revert code to initial state
4. Use checkpoint rewind (code-only) → Reverts code, keeps conversation
5. Continue discussion with fresh code state
```

#### Integration with Testing Workflow

**Enhanced PostToolUse Hook (Optional):**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/test-runner.sh --changed",
            "timeout": 120
          },
          {
            "type": "command",
            "command": "bash .claude/hooks/checkpoint-validator.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**New Script:** `.claude/hooks/checkpoint-validator.sh`

```bash
#!/usr/bin/env bash
# Checkpoint Validator Hook
# Suggests revert if tests fail after edit

set -euo pipefail

# Check if tests passed (from previous hook)
# This is illustrative - actual implementation depends on test-runner.sh exit code

if [ -f ".claude/logs/last-test-status.txt" ]; then
    TEST_STATUS=$(cat ".claude/logs/last-test-status.txt")

    if [ "${TEST_STATUS}" = "FAILED" ]; then
        echo "⚠️  Tests failed after edit. Consider reverting to last checkpoint."
        echo "💡 Use Claude Code checkpoint rewind feature to undo changes."
    else
        echo "✅ Tests passed. Checkpoint validated."
    fi
fi

exit 0
```

#### Documentation Addition

**Update:** `.claude/docs/DEVELOPMENT.md` (add section)

```markdown
## Checkpointing Workflow

### Automatic Checkpoints
Every Edit/Write operation creates a checkpoint. No manual action required.

### When to Use Checkpoints vs Git
- **Checkpoints:** Temporary experiments, quick undo, iteration
- **Git commits:** Permanent record, team collaboration, backup

### Common Patterns
1. **Safe Experimentation:** Try refactoring, revert if tests fail
2. **Approach Comparison:** Implement multiple solutions, compare, keep best
3. **Agent Safety Net:** Let agents edit, easy rollback if mistakes

### Limitations
- ❌ Doesn't track bash command changes (rm, mv, cp)
- ❌ Doesn't track manual edits outside Claude Code
- ❌ Not a git replacement (local only, 30-day retention)
```

#### Migration Path

**Phase 1: Documentation (Week 1)**
1. Document checkpointing in `.claude/docs/DEVELOPMENT.md`
2. Add usage examples to CLAUDE.md memory
3. Create quick reference guide

**Phase 2: Workflow Integration (Week 2)**
1. Train on checkpoint usage patterns (experimental refactoring, etc.)
2. Integrate with testing workflow (suggest revert on test failures)
3. Optional: Add checkpoint-validator.sh hook

**Phase 3: Monitoring (Week 3+)**
1. Track checkpoint usage frequency
2. Measure time saved (vs manual git stash workflows)
3. Document common checkpoint scenarios

**No Rollback Needed** - Checkpointing is automatic and non-invasive.

### 5. Priority & Effort Estimation

**Impact Level:** 🟢 **LOW-MEDIUM**

| Metric | Score | Justification |
|--------|-------|---------------|
| Repetitive automation | 3/5 | Eliminates manual git stash for experiments |
| Context preservation | 4/5 | Can revert code while keeping conversation |
| Agent coordination | 3/5 | Safety net for agent edits |
| Token optimization | 1/5 | Minimal impact |
| Plan efficiency | 2/5 | Faster iteration on implementation |

**Implementation Complexity:** 🟢 **1/5 (Very Low)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Setup | 0/5 | Already works automatically |
| Documentation | 2/5 | Document usage patterns |
| Workflow integration | 1/5 | Optional hook addition |
| Testing | 1/5 | Just verify it works as expected |
| Maintenance | 1/5 | Zero ongoing maintenance |

**Dependencies:**
- ✅ None - Checkpointing is automatic
- ✅ No configuration needed
- ✅ No external tools

**Estimated Effort:**
- Documentation: **1-2 hours**
- Approval gate integration documentation: **1 hour**
- Optional checkpoint-validator hook: **1 hour**
- Testing & validation: **30 minutes**
- **Total: 3.5-4.5 hours**

**Break-even Analysis:**
- Time saved per week: ~20-40 minutes (vs manual git stash/unstash)
- Break-even: **3-5 weeks**
- Annual ROI: **15-30 hours** of time otherwise spent on manual experiment management

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Automatic Checkpoint Creation
```
Scenario: Edit solarwindpy/core/ion.py
Expected: Checkpoint created automatically before edit
Validation: Verify checkpoint exists in Claude Code UI
```

#### Test 2: Code Revert (Keep Conversation)
```
Scenario: Multi-edit session with discussion
Action: Revert code to checkpoint, keep conversation
Expected: Code reverted, conversation context preserved
Validation: Check file contents vs conversation history
```

#### Test 3: Checkpoint Persistence
```
Scenario: Create checkpoints, close session, resume later
Expected: Checkpoints available in resumed session
Validation: Can revert to checkpoints created in previous session
```

#### Test 4: Bash Command Limitation
```
Scenario: Delete file with `rm`, try to checkpoint-revert
Expected: Checkpoint doesn't restore bash-deleted files
Validation: Confirms limitation documented correctly
```

#### Test 5: 30-Day Retention
```
Scenario: Create checkpoint, wait 30+ days (or adjust retention config)
Expected: Old checkpoint auto-deleted
Validation: Confirms cleanup policy works
```

**Success Criteria:**
- ✅ Checkpoints created automatically before Edit/Write
- ✅ Can revert code independently from conversation
- ✅ Checkpoints persist across session resume
- ✅ Limitations (bash commands, manual edits) confirmed
- ✅ Retention policy enforced

**Monitoring:**
```bash
# Checkpoints are managed by Claude Code internal system
# No manual monitoring needed, but can track usage in workflow documentation
```

---


**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
