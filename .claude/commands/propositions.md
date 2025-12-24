---
description: Analyze task using 9 value propositions framework with AI execution assessment and recommendation
---

⚠️ **Important:** This analysis uses AI estimation, not calculated metrics.
Treat recommendations as preliminary exploration, not formal decisions.
For production plans, use `gh-plan-create.sh` with automated proposition generation.

**🤖 Proposition 9 (AI Execution Assessment)** provides actionable guidance on execution strategy, prompt improvements, agent selection, and clarifications needed to optimize AI execution success.

---

Analyze the following task using the comprehensive value propositions framework:

**Task:** $ARGUMENTS

When uncertain or missing information:
- Estimate alignment scores conservatively (favor lower end of range)
- Flag risks prominently (favor ⚠️ over ✅)
- Recommend MODIFY SCOPE over PROCEED when borderline
- Better to surface concerns early than approve problematic scope

Generate analysis covering these 9 propositions:

### 1. Value Proposition Analysis
- Scientific software development value (research efficiency, development quality)
- Developer productivity value (planning efficiency, token optimization)
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 2. Resource & Cost Analysis
- Development investment (time estimates with confidence intervals)
- Maintenance considerations (ongoing costs)
- Token economics (if applicable)
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 3. Risk Assessment & Mitigation
- Technical implementation risks
- Project management risks
- Scientific workflow risks
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 4. Security Proposition (Code-Level Only)
- Dependency vulnerability assessment
- Attack surface analysis
- Development workflow security
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 5. Scope Audit
- Estimate SolarWindPy alignment score (0-100)
- Module relevance assessment (core modules: solarwindpy/core, instabilities highest priority)
- Out-of-scope pattern detection (avoid: web dev, databases, GUI, cloud deployment, React/Angular, SQL)
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 6. Token Usage Optimization
- Context/planning efficiency impact
- Current vs optimized patterns
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 7. Time Investment Analysis
- Implementation breakdown
- Break-even calculation (if applicable)
- ROI timeline
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 8. Usage & Adoption Metrics
- Target use cases
- Success metrics definition
- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

### 9. AI Execution Assessment
Evaluate how effectively an AI agent can execute the task autonomously, identifying clarifications needed, decision points, and prompt optimizations for successful execution.

**Assessment Dimensions (0-100 scale each):**

**Requirement Clarity (Weight: 25%)**
- Ambiguity detection: Are terms concrete and measurable?
- Sufficiency: Are what/why/success-criteria/constraints specified?
- Executability: Can AI execute without clarification?
- **Scoring Bands:**
  - 90-100: Zero ambiguity, complete specification, immediate executability
  - 70-89: Minor ambiguity (1-2 clarifications), mostly complete
  - 50-69: Moderate ambiguity (2-3 clarifications), partial specification
  - 0-49: High ambiguity (3+ clarifications), incomplete specification

**Context Complexity (Weight: 15%)**
- Domain knowledge depth: Surface/moderate/deep expertise required?
- Module coupling: Single module or complex dependencies?
- Token budget impact: <5K, 5K-25K, or >25K tokens?
- **Scoring Bands:**
  - 90-100: Deep domain + high coupling + large token budget
  - 70-89: Deep domain OR high coupling OR large token budget
  - 50-69: Moderate across dimensions
  - 0-49: Surface-level + low coupling + small token budget

**Decision Points (Weight: 20%, INVERTED - lower score = more decisions)**
- Decision count: How many human decisions required?
- Decision complexity: Simple pattern selection or novel architectural?
- Reversibility: Code-only changes or irreversible schema changes?
- **Scoring Bands:**
  - 90-100: Zero decisions or all have clear precedent
  - 70-89: 1-2 simple decisions with documented tradeoffs
  - 50-69: 2-3 decisions OR 1 complex architectural decision
  - 0-49: 3+ decisions OR complex novel decisions OR irreversible

**Error Recovery Capability (Weight: 20%)**
- Error diagnosability: Clear actionable messages or cryptic failures?
- Self-correction feasibility: Can AI autonomously fix most errors?
- Feedback loop speed: Instant (<10s), moderate (1-5min), or slow (>5min)?
- **Scoring Bands:**
  - 90-100: Clear errors + self-correcting + fast feedback
  - 70-89: Clear errors + mostly self-correcting + moderate feedback
  - 50-69: Somewhat clear + partially self-correcting
  - 0-49: Cryptic errors + manual debugging + slow feedback

**Agent Coordination (Weight: 10%, INVERTED - lower score = more agents)**
- Agent count: Single agent, 2 agents, or 3+ agents?
- Handoff clarity: Explicit interfaces or ambiguous coordination?
- Parallel vs sequential: Independent work or tightly coupled?
- **Scoring Bands:**
  - 90-100: Single agent or no specialized agent
  - 70-89: 2 agents with clear handoff
  - 50-69: 2-3 agents with reasonable handoff clarity
  - 0-49: 3+ agents OR ambiguous handoffs OR tightly coupled

**Prompt Optimization (Weight: 10%)**
- Current prompt quality: Optimal, good, or poor?
- Improvement opportunities: None, minor, or major needed?
- Success-maximizing patterns: Follows all, most, or few best practices?
- **Scoring Bands:**
  - 90-100: Optimal (specific, examples, criteria, constraints, steps)
  - 70-89: Good (specific, criteria, constraints; missing 1-2 elements)
  - 50-69: Fair (specific but missing 2-3 elements)
  - 0-49: Poor (vague, missing multiple elements)

**Composite Score Formula:**
```
AI_Execution_Score = (
  Requirement_Clarity × 0.25 +
  Error_Recovery × 0.20 +
  Decision_Points × 0.20 +
  Context_Complexity × 0.15 +
  Agent_Coordination × 0.10 +
  Prompt_Optimization × 0.10
)
```

**Execution Mode Bands:**
- **90-100: AUTONOMOUS** - AI executes independently, no human intervention
- **70-89: GUIDED** - AI executes with 1-2 clarifications, minimal human input
- **50-69: COLLABORATIVE** - Significant human-AI collaboration, multiple decision points
- **0-49: HUMAN-LED** - Human leads, AI provides support only

**Flag Generation:**
- Requirement Clarity < 50 → 🚨 HIGH AMBIGUITY
- Requirement Clarity 50-69 → ⚠️ MODERATE AMBIGUITY
- Context Complexity > 80 → 🔬 DEEP DOMAIN
- Context Complexity 60-80 → 📚 MODERATE DOMAIN
- Decision Points < 50 → 🛑 HUMAN DECISION REQUIRED
- Decision Points 50-69 → 🤝 COLLABORATIVE DECISIONS
- Error Recovery < 50 → 🐛 MANUAL DEBUGGING
- Error Recovery 50-69 → 🔄 GUIDED RECOVERY
- Error Recovery ≥ 70 → 🤖 SELF-CORRECTING
- Agent Coordination < 60 → 👥 MULTI-AGENT COMPLEX
- Agent Coordination 60-79 → 🔗 MULTI-AGENT
- Agent Coordination ≥ 80 → 👤 SINGLE AGENT
- Prompt Optimization < 50 → 💡 MAJOR IMPROVEMENTS
- Prompt Optimization 50-69 → 📝 MINOR IMPROVEMENTS
- Prompt Optimization ≥ 70 → ✅ OPTIMIZED

**5 Prompt Improvement Patterns:**
1. **Add Concrete Examples** (for Clarity < 70): "e.g., convert Plasma.thermal_speed from CGS (cm/s) to SI (m/s)"
2. **Specify Success Criteria** (for Decisions < 70): "≥95% test coverage, zero breaking changes to public API"
3. **Enumerate Edge Cases** (for Recovery < 70): "NaN → preserve as NaN, empty → ValueError, partial → document limitation"
4. **Step-by-Step Breakdown** (for Complexity > 70): "1. Create Species class, 2. Refactor Ion, 3. Validate physics, 4. Update tests"
5. **Reference Existing Patterns** (universal): "Follow solarwindpy/plotting/hist1d.py pattern: accept Plasma object, use matplotlib defaults, return fig/ax"

**Output Format:**
For each dimension, provide:
- Score (0-100)
- Key findings (1-2 sentences)
- Flags raised

Then provide:
- **Composite AI Execution Score:** X/100 (MODE)
- **Recommended Execution Strategy:**
  - Mode: AUTONOMOUS/GUIDED/COLLABORATIVE/HUMAN-LED
  - Clarifications needed (if any)
  - Agent selection (which specialized agents to invoke)
  - Prompt improvements (which of the 5 patterns to apply)
  - Estimated token budget (including clarification overhead)
  - Expected execution flow

- **Assessment:** ✅ Positive / ⚠️ Caution / ❌ Negative / ➖ Neutral
- **Confidence:** 🟢 High / 🟡 Medium / 🔴 Low

---

## Summary Table

| Proposition | Key Finding | Assessment | Confidence | Implication |
|-------------|-------------|------------|------------|-------------|
| 1. Value | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 2. Resources | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 3. Risk | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 4. Security | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 5. Scope | [Estimated score] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 6. Tokens | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 7. Time | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| 8. Adoption | [Brief summary] | ✅/⚠️/❌/➖ | 🟢/🟡/🔴 | [Impact on decision] |
| **9. AI Execution** | **[Score/100, mode, flags]** | **✅/⚠️/❌/➖** | **🟢/🟡/🔴** | **[Execution strategy, clarifications, agent selection, prompt improvements]** |

**Confidence Legend:**
- 🟢 High confidence (clear, objective factors)
- 🟡 Medium confidence (estimated, reasonable assumptions)
- 🔴 Low confidence (speculative, many unknowns)

---

## Final Recommendation

**PROCEED** / **MODIFY SCOPE** / **DON'T PROCEED**

**Justification:**
- [3-4 bullet points referencing table findings]
- [Note any low-confidence assessments that affect recommendation]
- [Highlight critical factors (scope alignment, major risks)]
- **AI Execution (Prop 9):** [Execution mode] with [flags] - [Impact on implementation approach: autonomous execution vs guided vs collaborative]

**Suggested Next Steps:**
- [Immediate actions if proceeding]
- [Areas needing more information if confidence is low]
- [How to address flagged concerns]
- **Prompt Improvements (Prop 9):** [Apply patterns #1-5 as recommended: examples, success criteria, edge cases, step-by-step, existing patterns]
- **Agent Selection (Prop 9):** [Invoke specialized agents based on domain: DataFrameArchitect, FitFunctionSpecialist, PlottingEngineer, TestEngineer, UnifiedPlanCoordinator]
- **Clarifications Needed (Prop 9):** [List specific questions to ask based on Requirement Clarity dimension and decision points]
- **Execution Approach (Prop 9):** [AUTONOMOUS: proceed directly | GUIDED: clarify then execute | COLLABORATIVE: continuous feedback | HUMAN-LED: user drives, AI supports]

---

Ensure all 9 propositions are covered. Verify table accuracy matches detailed analysis.
Keep analysis concise and actionable (2-3 sentences per proposition).

**Proposition 9 (AI Execution) is particularly important:** It provides actionable guidance on execution strategy, prompt improvements, agent selection, and clarifications needed. Use its flags and recommendations to optimize AI execution success.
