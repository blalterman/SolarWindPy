---
description: Analyze task using 8 value propositions framework with recommendation
---

⚠️ **Important:** This analysis uses AI estimation, not calculated metrics.
Treat recommendations as preliminary exploration, not formal decisions.
For production plans, use `gh-plan-create.sh` with automated proposition generation.

---

Analyze the following task using the comprehensive value propositions framework:

**Task:** $ARGUMENTS

When uncertain or missing information:
- Estimate alignment scores conservatively (favor lower end of range)
- Flag risks prominently (favor ⚠️ over ✅)
- Recommend MODIFY SCOPE over PROCEED when borderline
- Better to surface concerns early than approve problematic scope

Generate analysis covering these 8 propositions:

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

**Suggested Next Steps:**
- [Immediate actions if proceeding]
- [Areas needing more information if confidence is low]
- [How to address flagged concerns]

---

Ensure all 8 propositions are covered. Verify table accuracy matches detailed analysis.
Keep analysis concise and actionable (2-3 sentences per proposition).
