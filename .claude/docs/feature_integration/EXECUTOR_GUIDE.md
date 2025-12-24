# Feature Integration Executor Guide

**🤖 AI Executors: Start Here**

This document provides step-by-step imperative instructions for implementing the SolarWindPy feature integration. If you are a generative AI tasked with executing this plan, **follow these steps sequentially**.

**For strategic context and design rationale**, see [INDEX.md](./INDEX.md).
**For detailed checklists**, see [integration_checklist.md](./appendices/integration_checklist.md).

---

## Quick Navigation

- [Prerequisites](#prerequisites)
- [Phase 0: Foundation (REQUIRED)](#phase-0-foundation-required)
- [Decision Gate 1](#decision-gate-1-phase-0--phase-1)
- [Phase 1: Automation (CONDITIONAL)](#phase-1-automation-conditional)
- [Decision Gate 2](#decision-gate-2-phase-1--phase-2)
- [Phase 2: Safety & Distribution (CONDITIONAL)](#phase-2-safety--distribution-conditional)
- [Decision Gate 3](#decision-gate-3-phase-2--phase-3)
- [Phase 3: Optimization (OPTIONAL)](#phase-3-optimization-optional)
- [Final Validation](#final-validation)

---

## Prerequisites

Before beginning implementation:

1. **Read for Context (30 min):**
   - [INDEX.md](./INDEX.md) - Strategic overview, phases, and features
   - [appendices/quick_reference.md](./appendices/quick_reference.md) - Stopping conditions and command syntax

2. **Understand the Phases:**
   - **Phase 0 (REQUIRED):** Foundation - Memory + Slash Commands
   - **Phase 1 (CONDITIONAL):** Automation - Skills + Subagents (only if Phase 0 succeeds)
   - **Phase 2 (CONDITIONAL):** Safety - Hooks + Checkpointing + Plugin (only if Phase 1 succeeds)
   - **Phase 3 (OPTIONAL):** Optimization - Output Styles (only if user feedback indicates need)

3. **Key Principle:** **Stop at each Decision Gate.** Do not proceed to next phase without meeting criteria.

---

## Phase 0: Foundation (REQUIRED)

**Goal:** Establish persistent context and manual command infrastructure.

**Time Estimate:** 27-40 hours

### Step 1: Implement Memory Hierarchy (19-30 hours)

**File:** [01_memory_hierarchy.md](./01_memory_hierarchy.md)

**Actions:**
1. Read 01_memory_hierarchy.md completely
2. Create 9 memory files in `.claude/memory/`:
   - `physics-constants.md` (≤1K tokens)
   - `dataframe-patterns.md` (≤3K tokens)
   - `testing-templates.md` (≤4K tokens)
   - `agent-coordination.md` (≤2K tokens)
   - `git-workflow.md` (≤1K tokens)
   - `code-style.md` (≤2K tokens)
   - `common-errors.md` (≤2K tokens)
   - `deployment-checklist.md` (≤2K tokens)
   - `project-overview.md` (≤3K tokens)
3. Implement stopping conditions:
   - Rate limiting: Max 20 memory file imports per session
   - Budget guard: Memory directory ≤20K tokens total
   - User override: Explicit requests bypass limits
4. Create token counting script: `.claude/scripts/count-memory-tokens.py`
5. Validate: Run `python .claude/scripts/count-memory-tokens.py` → Should show ≤20K total

**Success Criteria:**
- ✅ All 9 memory files exist and are populated
- ✅ Total memory directory ≤20K tokens
- ✅ Token counting script functional
- ✅ No errors when Claude Code loads memory files

### Step 2: Implement Slash Commands (8.5-12 hours)

**File:** [07_slash_commands.md](./07_slash_commands.md)

**Actions:**
1. Read 07_slash_commands.md completely
2. Create 10 slash command files in `.claude/commands/`:
   - `coverage.md` - Display test coverage report
   - `physics.md` - Run physics validation
   - `test-changed.md` - Test modified files only
   - `test-physics.md` - Run physics-specific tests
   - `clean.md` - Run cleanup operations
   - `breakdown.md` - Show capability breakdown
   - `physics-validate.md` - Validate physics constraints
   - `memory.md` - Display memory hierarchy
   - `checkpoint.md` - Show checkpoint status
   - `propositions.md` - Analyze with value propositions
3. Implement stopping conditions:
   - Timeout: 5-10 minutes per command (configurable)
   - Error recovery: Fallback chains for failed commands
   - User notification: Progress indicators for long-running commands
4. Validate: Run `/coverage` → Should display coverage report without errors

**Success Criteria:**
- ✅ All 10 slash command files exist
- ✅ Commands execute without errors
- ✅ Timeout handling works (test with long-running command)
- ✅ Error recovery graceful (test with invalid input)

---

## Decision Gate 1: Phase 0 → Phase 1

**⚠️ STOP HERE. Do not proceed to Phase 1 until these criteria are met.**

**See:** [DECISION_GATES.md](./DECISION_GATES.md#decision-gate-1) for detailed validation checklist.

### Metrics to Collect

1. **Token Reduction:**
   - Method: Compare 3 sessions before/after memory implementation
   - Track: Total tokens per session (conversation + tool outputs)
   - Calculate: (Baseline - With_Memory) / Baseline × 100%
   - Target: ≥30% reduction

2. **Time Savings:**
   - Method: Track time spent on repeated context-setting tasks
   - Measure: Minutes saved per session (no repeated explanations)
   - Frequency: Sessions per week × savings per session
   - Target: ≥60 minutes/week

### Decision Criteria

**✅ PROCEED to Phase 1 if:**
- Token reduction ≥30% (measured across 3+ sessions)
- Time savings ≥60 minutes/week
- Memory files load without errors
- Slash commands functional

**⚠️ PAUSE if:**
- Token reduction 20-29% → Refine memory file content, try again
- Time savings 40-59 min/week → Add more frequently-used content to memory

**❌ STOP if:**
- Token reduction <20% → Investigate root cause, memory system not providing value
- Time savings <40 min/week → Memory system overhead exceeds benefits
- Persistent technical issues → Rollback, reassess approach

**Action:** Document metrics in `.claude/logs/decision-gate-1.md` before proceeding.

---

## Phase 1: Automation (CONDITIONAL)

**Prerequisite:** ✅ Decision Gate 1 PASSED

**Goal:** Add automatic detection and isolated context windows.

**Time Estimate:** 21.5-32 hours

### Step 3: Implement Skills System (7-11 hours)

**File:** [02_skills_system.md](./02_skills_system.md)

**⚠️ Prerequisites:** Phase 0 complete (Memory Hierarchy + Slash Commands implemented).

**Actions:**
1. Read 02_skills_system.md completely
2. Create 4 skill YAML files in `.claude/skills/`:
   - `physics-validator.yaml` - Auto-detect physics calculations
   - `dataframe-architect.yaml` - Auto-detect MultiIndex operations
   - `test-engineer.yaml` - Auto-detect test coverage needs
   - `numerical-stability.yaml` - Auto-detect precision concerns
3. Implement stopping conditions:
   - Rate limiting: 5-12 activations/hour per skill
   - Activation accuracy tracking: Log true/false positive rates
   - User override: Disable skill with `@no-skill-name`
4. Validate: Mention "thermal speed calculation" in prompt → physics-validator should activate

**Success Criteria:**
- ✅ All 4 skills exist and parse without errors
- ✅ Skills auto-activate on appropriate triggers (test each)
- ✅ Rate limiting prevents over-activation
- ✅ User can disable skills when needed

### Step 4: Implement Subagents (14.5-21 hours)

**File:** [03_subagents.md](./03_subagents.md)

**⚠️ Prerequisites:** Phase 0 complete (Memory Hierarchy + Slash Commands implemented).

**Actions:**
1. Read 03_subagents.md completely
2. Create 3 subagent definitions (register with Claude Code):
   - DataFrameArchitect - Complex MultiIndex operations and DataFrame optimization
   - PlottingEngineer - Iterative visualization refinement
   - FitFunctionSpecialist - Statistical analysis and precision analysis in curve fitting
3. Implement stopping conditions:
   - Token budget: ≤50K tokens per subagent (25% of 200K session budget)
   - Approval gates: Request approval for operations >500-800 tokens
   - Display: Show estimated cost before executing subagent
   - Timeout: 10-25 minutes depending on complexity (with progress warnings)
4. Validate: Invoke DataFrameArchitect subagent → Should create isolated context window

**Success Criteria:**
- ✅ All 3 subagents registered and invocable
- ✅ Subagents create isolated context (don't pollute main conversation)
- ✅ Approval gates request confirmation for expensive operations
- ✅ Token budget respected (max 50K per subagent)

---

## Decision Gate 2: Phase 1 → Phase 2

**⚠️ STOP HERE. Do not proceed to Phase 2 until these criteria are met.**

**See:** [DECISION_GATES.md](./DECISION_GATES.md#decision-gate-2) for detailed validation checklist.

### Metrics to Collect

1. **Automation Rate:**
   - Method: Track skill activations vs. manual invocations
   - Calculate: Skill_Activations / (Skill_Activations + Manual_Commands) × 100%
   - Target: ≥40%

2. **Token Savings from Subagents:**
   - Method: Compare complex analysis tasks with/without subagents
   - Track: Context window usage for multi-step analyses
   - Calculate: (Without_Subagent - With_Subagent) / Without_Subagent × 100%
   - Target: ≥30% for complex tasks

3. **Team Satisfaction:**
   - Method: Survey or informal feedback
   - Ask: "Are skills helpful or annoying? Are subagents worth the approval overhead?"
   - Target: Positive feedback (>6/10 satisfaction)

### Decision Criteria

**✅ PROCEED to Phase 2 if:**
- Automation rate ≥40%
- Subagent token savings ≥30% for complex tasks
- Team feedback positive (skills helpful, subagents valuable)

**⚠️ PAUSE if:**
- Automation rate 30-39% → Adjust skill triggers, improve activation accuracy
- Subagent savings 20-29% → Refine subagent scope, reduce overhead

**❌ STOP (Revert to Phase 0) if:**
- Automation rate <30% → Skills over/under-activating, too much manual correction
- Team feedback negative → Skills annoying, subagent approvals disruptive
- Technical issues persistent → Phase 1 features not providing net value

**Action:** Document metrics in `.claude/logs/decision-gate-2.md` before proceeding.

---

## Phase 2: Safety & Distribution (CONDITIONAL)

**Prerequisite:** ✅ Decision Gate 2 PASSED

**Goal:** Add event-driven automation, edit tracking, and distribution capability.

**Time Estimate:** 17-25 hours

### Step 5: Implement Enhanced Hooks (5.5-8.5 hours)

**File:** [04_enhanced_hooks.md](./04_enhanced_hooks.md)

**⚠️ Prerequisites:** Phase 1 complete (Skills + Subagents implemented).

**Actions:**
1. Read 04_enhanced_hooks.md completely
2. Create 3 hook scripts in `.claude/hooks/`:
   - `session-start.sh` - Log session initiation, validate environment
   - `file-edit.sh` - Trigger on file modifications, run validators
   - `notification.sh` - Activity logging for debugging/audit
3. Implement stopping conditions:
   - Graceful degradation: Hooks fail silently, don't block operations
   - Error logging: Write failures to `.claude/logs/hooks-error.log`
   - User override: Disable hooks with environment variable
4. Validate: Edit a Python file → file-edit hook should trigger physics validation

**Success Criteria:**
- ✅ All 3 hooks exist and execute without blocking operations
- ✅ Hooks trigger on appropriate events
- ✅ Hook failures don't crash Claude Code session
- ✅ Error logs capture failures for debugging

### Step 6: Implement Checkpointing (3.5-4.5 hours)

**File:** [05_checkpointing.md](./05_checkpointing.md)

**⚠️ Prerequisites:** Phase 0 complete (no dependencies on Phase 1).

**Actions:**
1. Read 05_checkpointing.md completely
2. Document checkpoint usage patterns:
   - When checkpoints auto-create (approval gates >500 tokens)
   - How to revert to checkpoint
   - Checkpoint display format in approval prompts
3. Create optional checkpoint validator hook (if desired)
4. Validate: Trigger approval gate → Should show checkpoint indicator

**Success Criteria:**
- ✅ Checkpointing behavior documented
- ✅ Approval gates display checkpoint indicators
- ✅ Users can revert to checkpoint if needed
- ✅ Zero rollback friction (no manual git stash/unstash)

### Step 7: Implement Plugin Packaging (8-12 hours)

**File:** [08_plugin_packaging.md](./08_plugin_packaging.md)

**⚠️ Prerequisites:** All Phase 0-1 features complete.

**Actions:**
1. Read 08_plugin_packaging.md completely
2. Create plugin structure:
   - `plugin.json` - Metadata (name, version, author)
   - `commands/` - Copy 10 slash commands
   - `skills/` - Copy 4 skill YAML files
   - `agents/` - Copy 4 subagent definitions
   - `hooks/` - Copy 3 hook scripts
   - `README.md` - Installation and usage instructions
3. Test plugin locally:
   - Follow [Installation Testing Procedure](./08_plugin_packaging.md#installation-testing-procedure-objective-passfail-validation)
   - 8-step pass/fail validation checklist
   - Must achieve PASS on all 8 tests
4. Create marketplace entry (optional):
   - `marketplace.json` - Plugin listing metadata
   - Push to GitHub repository

**Success Criteria:**
- ✅ Plugin passes all 8 installation tests
- ✅ All commands/skills/agents/hooks functional in plugin form
- ✅ README clear and complete
- ✅ Plugin can be installed with single command

---

## Decision Gate 3: Phase 2 → Phase 3

**⚠️ STOP HERE. Evaluate whether Phase 3 is needed.**

**See:** [DECISION_GATES.md](./DECISION_GATES.md#decision-gate-3) for detailed validation checklist.

### Metrics to Collect

1. **User Feedback on Explanatory Output Style:**
   - Method: Survey team members
   - Ask: "Does the current Explanatory style provide enough physics domain context?"
   - Ask: "Do you need more physics-specific emphasis in AI responses?"

### Decision Criteria

**✅ PROCEED to Phase 3 if:**
- User feedback indicates Explanatory style insufficient for physics work
- Team explicitly requests more domain-specific output customization

**⚠️ SKIP (RECOMMENDED):**
- Current Explanatory style is satisfactory
- No strong need for custom physics-focused output style
- Team satisfied with Phase 0-2 features

**❌ STOP (Team Satisfied):**
- Phase 2 features meet all needs
- No desire for additional customization
- Project complete

**Action:** Document feedback in `.claude/logs/decision-gate-3.md`.

---

## Phase 3: Optimization (OPTIONAL)

**Prerequisite:** ✅ Decision Gate 3 indicates user need

**Goal:** Add custom physics-focused output style.

**Time Estimate:** 2.5-3.5 hours

### Step 8: Implement Output Styles (2.5-3.5 hours)

**File:** [06_output_styles.md](./06_output_styles.md)

**⚠️ Prerequisites:** Phase 2 complete (Hooks + Checkpointing + Plugin implemented).

**Actions:**
1. Read 06_output_styles.md completely
2. Create custom output style in `.claude/config.json`:
   - Name: "PhysicsFocused" style
   - Characteristics: Emphasize unit consistency, cite equations, validate constraints
3. Document style activation: How to enable/disable
4. Validate: Enable PhysicsFocused style → Responses should emphasize physics context

**Success Criteria:**
- ✅ Custom output style defined in config
- ✅ Style activates when selected
- ✅ Measurable difference in response quality for physics tasks
- ✅ Users can toggle style on/off

---

## Final Validation

**Before declaring implementation complete:**

### Completion Checklist

**Phase 0 (REQUIRED):**
- [ ] Memory files exist (9 files, ≤20K total)
- [ ] Token reduction ≥30% (verified across 3+ sessions)
- [ ] Slash commands functional (10 commands)
- [ ] Time savings ≥60 min/week (measured)

**Phase 1 (if implemented):**
- [ ] Skills auto-activate correctly (4 skills, ≥40% automation rate)
- [ ] Subagents operational (4 agents, ≤50K tokens each)
- [ ] Approval gates working

**Phase 2 (if implemented):**
- [ ] Hooks logging activity (3 hooks)
- [ ] Checkpointing functional
- [ ] Plugin packaged and tested (8-step validation PASSED)

**Phase 3 (if implemented):**
- [ ] Custom output style active
- [ ] User satisfaction confirmed

### Retrospective

**Action:** Complete retrospective using [templates/retrospective-template.md](./templates/retrospective-template.md).

Document:
- Quantitative metrics (token savings, time savings, break-even)
- Qualitative assessment (team satisfaction, workflow improvements)
- Technical debt (complexity added, maintenance burden)
- Lessons learned (success patterns, failure patterns, recommendations)

---

## Troubleshooting

### Common Issues

**Issue:** Memory files not loading
- **Solution:** Check `.claude/memory/` exists, files are valid markdown, total ≤20K tokens

**Issue:** Skills over-activating
- **Solution:** Adjust trigger phrases in skill YAML, increase specificity

**Issue:** Subagent approval gates too frequent
- **Solution:** Increase approval threshold (e.g., 800 tokens instead of 500)

**Issue:** Hooks causing errors
- **Solution:** Check hooks have execute permission (`chmod +x`), review error logs in `.claude/logs/`

**Issue:** Plugin installation failing
- **Solution:** Follow [Installation Testing Procedure](./08_plugin_packaging.md#installation-testing-procedure-objective-passfail-validation), check logs

### Getting Help

- **Documentation:** See [INDEX.md](./INDEX.md) for strategic context
- **Detailed checklists:** See [integration_checklist.md](./appendices/integration_checklist.md)
- **Decision gates:** See [DECISION_GATES.md](./DECISION_GATES.md)
- **Stopping conditions:** See [quick_reference.md](./appendices/quick_reference.md)

---

## Summary: Execution Order

**Critical:** Do NOT follow file numerical order (01→02→03...). Follow this phase order:

1. **Phase 0:** Read 01, implement. Then read 07, implement. **STOP.** Validate Decision Gate 1.
2. **Phase 1:** If Gate 1 passed, read 02, implement. Then read 03, implement. **STOP.** Validate Decision Gate 2.
3. **Phase 2:** If Gate 2 passed, read 04, implement. Then read 05, implement. Then read 08, implement. **STOP.** Validate Decision Gate 3.
4. **Phase 3:** If Gate 3 indicates need, read 06, implement.
5. **Final:** Complete retrospective, merge to master.

**File read order:** 01→07→[Gate1]→02→03→[Gate2]→04→05→08→[Gate3]→06

---

**Last Updated:** 2025-12-04
**Version:** 1.0
**Related:** [INDEX.md](./INDEX.md) | [DECISION_GATES.md](./DECISION_GATES.md) | [integration_checklist.md](./appendices/integration_checklist.md)
