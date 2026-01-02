# Decision Gates Reference

**Purpose:** Formal validation checkpoints between implementation phases.

Each decision gate determines whether to proceed to the next phase, pause for refinement, or stop implementation. These gates prevent over-investment in features that don't provide sufficient value.

**Related:** [EXECUTOR_GUIDE.md](./EXECUTOR_GUIDE.md) | [INDEX.md](./INDEX.md) | [integration_checklist.md](./appendices/integration_checklist.md)

---

## Overview

| Gate | From → To | Timing | Criteria Summary |
|------|-----------|--------|------------------|
| [Gate 1](#decision-gate-1) | Phase 0 → Phase 1 | After Memory + Commands | ≥30% token reduction, ≥60 min/week saved |
| [Gate 2](#decision-gate-2) | Phase 1 → Phase 2 | After Skills + Subagents | ≥40% automation, positive feedback |
| [Gate 3](#decision-gate-3) | Phase 2 → Phase 3 | After Hooks + Plugin | User need for physics emphasis |
| [Gate 4](#decision-gate-4) | Phase 3 evaluation | After Output Styles | Measurable improvement confirmed |

---

## Decision Gate 1

### Phase 0 → Phase 1

**Timing:** After implementing Memory Hierarchy (01) and Slash Commands (07)

**Question:** Has Phase 0 provided sufficient value to justify continuing to Phase 1 (automation)?

### Metrics to Collect

#### 1. Token Reduction

**Method:**
- Compare token usage across 3+ sessions (before/after memory implementation)
- Track: Total tokens per session (conversation + tool outputs + subagents)
- Use Claude Code's token counter or context window monitoring

**Calculation:**
```
Token Reduction % = (Baseline - With_Memory) / Baseline × 100%
```

**Example:**
- Baseline session: 45K tokens
- With memory session: 30K tokens
- Reduction: (45K - 30K) / 45K × 100% = 33.3% ✅

**Target:** ≥30% reduction

#### 2. Time Savings

**Method:**
- Track time spent on repeated context-setting tasks
- Measure: Minutes saved per session (no repeated explanations of physics constants, dataframe patterns, etc.)
- Frequency: Sessions per week × savings per session

**Calculation:**
```
Weekly Savings = Sessions_Per_Week × Minutes_Saved_Per_Session
```

**Example:**
- 10 sessions/week
- 8 minutes saved/session (no context re-entry)
- Weekly savings: 10 × 8 = 80 min/week ✅

**Target:** ≥60 minutes/week

### Validation Checklist

Before making a decision, verify:

- [ ] **Memory files functional:**
  - All 9 memory files exist in `.claude/memory/`
  - Total directory size ≤20K tokens
  - Files load without errors when Claude Code starts

- [ ] **Slash commands operational:**
  - All 10 slash command files exist in `.claude/commands/`
  - Commands execute without errors
  - Timeout handling works

- [ ] **Metrics collected:**
  - Token reduction measured across ≥3 sessions
  - Time savings tracked for ≥1 week
  - Data documented in `.claude/logs/decision-gate-1.md`

### Decision Options

#### ✅ PROCEED to Phase 1 if:
- Token reduction ≥30% (measured)
- Time savings ≥60 minutes/week (measured)
- Memory files load without errors
- Slash commands functional
- **Confidence:** High value demonstrated, automation justified

**Next Steps:**
1. Document metrics in `.claude/logs/decision-gate-1.md`
2. Begin Phase 1: Skills System (02)
3. Monitor automation rate during Phase 1 implementation

#### ⚠️ PAUSE if:
- Token reduction 20-29% → **Action:** Refine memory file content, add more frequently-used context, re-measure after 1 week
- Time savings 40-59 min/week → **Action:** Add more command shortcuts, identify other repetitive tasks

**Re-evaluation:**
- Allow 1-2 weeks for refinement
- Re-measure metrics
- If still below target, consider STOP

#### ❌ STOP if:
- Token reduction <20% → **Reason:** Memory system not providing sufficient context optimization
- Time savings <40 min/week → **Reason:** Command overhead exceeds benefits
- Persistent technical issues → **Reason:** Infrastructure not stable

**Rollback Actions:**
1. Keep memory files (low maintenance cost)
2. Keep slash commands (already implemented)
3. Do NOT proceed to Phase 1 automation
4. Investigate root causes: Are memory files too generic? Wrong content? Commands poorly designed?

---

## Decision Gate 2

### Phase 1 → Phase 2

**Timing:** After implementing Skills System (02) and Subagents (03)

**Question:** Has automation (Phase 1) improved workflow enough to justify safety/distribution features (Phase 2)?

### Metrics to Collect

#### 1. Automation Rate

**Method:**
- Track skill activations vs. manual slash command invocations
- Period: 1-2 weeks of normal usage
- Log: Skill activation events + manual command executions

**Calculation:**
```
Automation Rate = Skill_Activations / (Skill_Activations + Manual_Commands) × 100%
```

**Example:**
- 40 skill activations in 2 weeks
- 60 manual command invocations
- Automation rate: 40 / (40 + 60) × 100% = 40% ✅

**Target:** ≥40%

#### 2. Subagent Token Savings

**Method:**
- Compare complex analysis tasks with/without subagents
- Track: Context window usage for multi-step analyses
- Focus: Tasks requiring deep physics validation or complex MultiIndex operations

**Calculation:**
```
Subagent Savings % = (Without_Subagent - With_Subagent) / Without_Subagent × 100%
```

**Example:**
- Complex analysis without subagent: 50K tokens (pollutes main context)
- Same analysis with subagent: 35K tokens (isolated context)
- Savings: (50K - 35K) / 50K × 100% = 30% ✅

**Target:** ≥30% for complex tasks

#### 3. Team Satisfaction

**Method:**
- Survey or informal feedback from team members
- Questions:
  - "Are skills activating appropriately (helpful vs. annoying)?"
  - "Do subagent approval gates feel worth the interruption?"
  - "Overall satisfaction with automation (1-10)?"

**Target:**
- Positive feedback (average >6/10)
- Skills considered helpful (not annoying)
- Subagent approvals acceptable overhead

### Validation Checklist

Before making a decision, verify:

- [ ] **Skills operational:**
  - All 4 skill YAML files parse without errors
  - Skills auto-activate on appropriate triggers
  - Rate limiting prevents over-activation
  - User can disable skills when needed

- [ ] **Subagents functional:**
  - All 4 subagent types invocable
  - Subagents create isolated context windows
  - Approval gates request confirmation for expensive operations
  - Token budget respected (≤50K per subagent)

- [ ] **Metrics collected:**
  - Automation rate tracked for ≥1 week
  - Subagent token savings measured on ≥3 complex tasks
  - Team feedback gathered (survey or interviews)
  - Data documented in `.claude/logs/decision-gate-2.md`

### Decision Options

#### ✅ PROCEED to Phase 2 if:
- Automation rate ≥40% (measured)
- Subagent token savings ≥30% for complex tasks (measured)
- Team feedback positive (>6/10 satisfaction, skills helpful, subagents valuable)
- **Confidence:** Automation providing net value, team satisfied

**Next Steps:**
1. Document metrics in `.claude/logs/decision-gate-2.md`
2. Begin Phase 2: Enhanced Hooks (04)
3. Continue tracking automation effectiveness

#### ⚠️ PAUSE if:
- Automation rate 30-39% → **Action:** Adjust skill triggers, improve activation accuracy, reduce false positives/negatives
- Subagent savings 20-29% → **Action:** Refine subagent scope, reduce approval overhead, optimize context isolation
- Mixed team feedback → **Action:** Address specific complaints (e.g., disable overly-active skills, adjust approval thresholds)

**Re-evaluation:**
- Allow 1-2 weeks for adjustments
- Re-measure metrics
- If still below target, consider STOP

#### ❌ STOP (Revert to Phase 0) if:
- Automation rate <30% → **Reason:** Skills over/under-activating, requiring constant manual correction
- Team feedback negative (<6/10) → **Reason:** Skills annoying, subagent approvals too disruptive
- Technical issues persistent → **Reason:** Phase 1 features not providing net value

**Rollback Actions:**
1. Disable skills (remove YAML files from `.claude/skills/` or comment out)
2. Stop using subagents (remove from agent registry)
3. Revert to Phase 0 (Memory + Slash Commands only)
4. Investigate root causes: Are skill triggers too broad? Subagent approvals too frequent? Wrong use cases?

---

## Decision Gate 3

### Phase 2 → Phase 3

**Timing:** After implementing Enhanced Hooks (04), Checkpointing (05), and Plugin Packaging (08)

**Question:** Do users need custom physics-focused output style, or is Explanatory style sufficient?

### Metrics to Collect

#### 1. User Feedback on Explanatory Style

**Method:**
- Survey team members after using Phase 0-2 features for 2-4 weeks
- Questions:
  - "Does the current Explanatory output style provide enough physics domain context?"
  - "Do you need more emphasis on unit consistency, equation citations, constraint validation?"
  - "Would a custom PhysicsFocused output style improve your productivity?"

**Target:**
- If feedback indicates Explanatory style is insufficient → PROCEED
- If feedback indicates current style is satisfactory → SKIP

### Validation Checklist

Before making a decision, verify:

- [ ] **Phase 2 complete:**
  - Enhanced Hooks functional (3 hooks executing)
  - Checkpointing operational (approval gates show checkpoint indicators)
  - Plugin packaged and tested (8-step validation PASSED)

- [ ] **Feedback collected:**
  - ≥3 team members surveyed
  - Specific pain points identified (if any)
  - Consensus on need for custom output style
  - Data documented in `.claude/logs/decision-gate-3.md`

### Decision Options

#### ✅ PROCEED to Phase 3 if:
- User feedback indicates Explanatory style insufficient for physics work
- Team explicitly requests more domain-specific output customization
- Specific use cases identified where PhysicsFocused style would help
- **Confidence:** Clear user need demonstrated

**Next Steps:**
1. Document feedback in `.claude/logs/decision-gate-3.md`
2. Begin Phase 3: Output Styles (06)
3. Define PhysicsFocused style characteristics based on user needs

#### ⚠️ SKIP (RECOMMENDED) if:
- Current Explanatory style is satisfactory
- No strong need for custom physics-focused output style
- Team satisfied with Phase 0-2 features
- **Reason:** Phase 3 is optimization, not core functionality

**Completion Actions:**
1. Declare implementation complete at Phase 2
2. Complete retrospective using [templates/retrospective-template.md](./templates/retrospective-template.md)
3. Merge to master
4. Distribute plugin (if applicable)

#### ❌ STOP (Team Satisfied) if:
- Phase 2 features meet all needs
- No desire for additional customization
- Project complete
- **Reason:** Further investment not justified by user need

**Completion Actions:**
- Same as SKIP above
- Phase 3 remains optional for future if needs change

---

## Decision Gate 4

### Phase 3 Evaluation

**Timing:** After implementing Output Styles (06)

**Question:** Was Phase 3 (custom output style) worth the investment?

### Metrics to Collect

#### 1. Measurable Improvement in Physics Tasks

**Method:**
- A/B testing: Same physics tasks with Explanatory vs. PhysicsFocused styles
- Measure:
  - Response quality (unit consistency, equation citations, constraint validation)
  - User satisfaction (1-10 rating)
  - Time saved (if applicable)

**Target:**
- Measurable improvement in response quality
- User satisfaction >7/10 with PhysicsFocused style
- Clear preference over Explanatory style

### Validation Checklist

Before making a decision, verify:

- [ ] **PhysicsFocused style implemented:**
  - Custom output style defined in `.claude/config.json`
  - Style activates when selected
  - Team trained on how to enable/disable

- [ ] **A/B testing completed:**
  - ≥5 physics tasks tested with both styles
  - User feedback collected
  - Preference documented
  - Data documented in `.claude/logs/decision-gate-4.md`

### Decision Options

#### ✅ SUCCESS if:
- Measurable improvement confirmed
- User satisfaction >7/10 with PhysicsFocused style
- Clear preference over Explanatory style
- **Action:** Keep PhysicsFocused style, document usage in CLAUDE.md

#### ⚠️ NEUTRAL if:
- Minimal improvement (not worth the effort)
- User satisfaction mixed (5-7/10)
- No clear preference
- **Action:** Revert to Explanatory style, Phase 3 was not necessary

#### ❌ FAILURE if:
- No measurable improvement
- User satisfaction <5/10
- Explanatory style preferred
- **Action:** Immediately revert to Explanatory style, document lesson learned

---

## Using This Reference

### For AI Executors

**At each decision gate:**
1. Collect all required metrics (document in `.claude/logs/decision-gate-N.md`)
2. Complete validation checklist
3. Evaluate against decision criteria
4. Document decision rationale
5. Proceed, pause, or stop as indicated

**Key Principle:** Never skip a decision gate. Always measure before proceeding.

### For Human Review

**Decision gates provide:**
- Objective stopping points
- Data-driven go/no-go decisions
- Rollback options at each phase
- Continuous validation of ROI

**Benefits:**
- Prevents over-investment in low-value features
- Enables early termination if Phase 0 doesn't deliver
- Provides clear success criteria
- Documents rationale for future projects

---

## Quick Reference

### Gate 1: Phase 0 → 1
- **Metric:** ≥30% token reduction, ≥60 min/week saved
- **Decision:** Proceed if both criteria met
- **Rollback:** Keep Phase 0, stop if insufficient value

### Gate 2: Phase 1 → 2
- **Metric:** ≥40% automation, positive team feedback
- **Decision:** Proceed if automation effective and team satisfied
- **Rollback:** Disable Phase 1, revert to Phase 0 if net negative

### Gate 3: Phase 2 → 3
- **Metric:** User feedback indicates need for physics emphasis
- **Decision:** SKIP recommended unless clear user need
- **Rollback:** Complete at Phase 2, Phase 3 optional

### Gate 4: Phase 3 evaluation
- **Metric:** Measurable improvement with PhysicsFocused style
- **Decision:** SUCCESS if preferred, revert if not
- **Rollback:** Remove PhysicsFocused style, use Explanatory

---

**Last Updated:** 2025-12-04
**Version:** 1.0
**Related:** [EXECUTOR_GUIDE.md](./EXECUTOR_GUIDE.md) | [INDEX.md](./INDEX.md) | [integration_checklist.md](./appendices/integration_checklist.md)
