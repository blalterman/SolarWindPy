# Output Styles

**Feature Type:** Manual
**Priority:** LOW
**Effort:** 2.5-3.5 hours
**ROI Break-even:** 8-12 weeks

[← Back to Index](./INDEX.md) | [Previous: Checkpointing ←](./05_checkpointing.md) | [Next: Slash Commands →](./07_slash_commands.md)

---
## Feature 6: Output Styles

### 1. Feature Overview

**What It Is:**
Output styles modify Claude Code's system prompt to adapt behavior beyond standard software engineering. They allow customization of response patterns, verbosity, and focus areas while preserving core tool capabilities.

**Core Capabilities:**
- **3 Built-in styles:** Default (software engineering), Explanatory (educational insights), Learning (collaborative with TODO markers)
- **Custom style creation** - Define via `/output-style:new` command or manual markdown files
- **System prompt override** - Completely replaces software engineering prompt with custom instructions
- **Project & user scopes** - Store in `.claude/output-styles/` (project) or `~/.claude/output-styles/` (user)
- **Persistent selection** - Saved to `.claude/settings.local.json`

**Current SolarWindPy Usage:**
✅ Using **Explanatory** style (educational insights between coding tasks)

**Maturity & Prerequisites:**
- ✅ Production-ready feature
- ✅ Already in use (Explanatory style active)
- 🆕 Opportunity for custom scientific/physics-focused style

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Context Preservation (LOW-MEDIUM IMPACT)**
*Current state:* Explanatory style provides educational insights
*With Custom Style:* Physics-focused style emphasizes scientific correctness
*Improvement:* Domain-specific behavior tailored to solar wind research

✅ **Agent Coordination (LOW IMPACT)**
*Current state:* Generic software engineering focus
*With Custom Style:* Style can emphasize when to use physics agents/skills
*Benefit:* Better automatic agent selection guidance

**Productivity Improvements:**
- Domain-specific response patterns
- Automatic emphasis on critical concerns (SI units, physics validation)
- Tailored verbosity (detailed for complex physics, concise for routine)

**Research Workflow Enhancements:**
- Physics-first mindset in all responses
- Scientific correctness emphasized over software patterns
- Educational insights focused on solar wind domain

### 3. Integration Strategy

**Architecture Fit:**

Custom output style enhances current Explanatory style:

```
Current: Explanatory (general educational insights)
├── Educational explanations
├── Implementation insights
└── General programming concepts

Proposed: Physics-Focused (SolarWindPy custom)
├── Physics correctness emphasis
├── SI unit validation reminders
├── Domain-specific educational insights
├── Agent/skill selection for scientific tasks
└── Research workflow optimization
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **Memory (CLAUDE.md)** | Output style references memory for physics rules |
| **Skills** | Style emphasizes automatic skill usage |
| **Agents** | Style includes agent selection guidance |
| **Hooks** | Style complements physics validation hooks |

**Backward Compatibility:**
✅ **Fully compatible** - Can switch back to Explanatory anytime
✅ **Non-invasive** - No changes to other systems
✅ **Optional adoption**

### 4. Implementation Specification

#### Proposed Custom Output Style

**File:** `.claude/output-styles/physics-focused.md`

```yaml
---
name: physics-focused
description: Solar wind physics research-oriented style emphasizing scientific correctness, SI units, and domain expertise.
---

You are Claude Code configured specifically for solar wind physics research and development. Your responses should prioritize scientific correctness, physics validation, and domain-specific best practices.

## Core Principles

1. **Physics First**
   - Always validate physics correctness before code elegance
   - SI units are mandatory (m/s, m⁻³, K, T)
   - Thermal speed: mw² = 2kT (never 3kT)
   - NaN for missing data (never sentinel values)

2. **Scientific Rigor**
   - Question assumptions about physical constraints
   - Validate that calculations make physical sense
   - Check dimensional analysis
   - Verify against canonical formulas

3. **Domain-Specific Insights**
   - Provide educational explanations focused on solar wind physics
   - Explain why certain approaches are physically sound or unsound
   - Connect code patterns to physical phenomena
   - Highlight research workflow implications

4. **Automatic Validation**
   - Proactively suggest physics-validator skill for calculations
   - Recommend dataframe-architect for MultiIndex operations
   - Emphasize test coverage for scientific correctness (≥95%)

## Response Patterns

### Before Writing Physics Code
Always include a physics validation insight:

"`★ Physics Check ─────────────────────────────`
[Verify formula, units, constraints before implementation]
`─────────────────────────────────────────────────`"

### After Implementing Calculations
Provide scientific validation:

"`★ Validation ────────────────────────────────────`
[Dimensional analysis, physical reasonableness, test coverage]
`─────────────────────────────────────────────────`"

### For DataFrame Operations
Emphasize MultiIndex structure:

"`★ MultiIndex Insight ────────────────────────`
[Efficiency, memory implications, view vs copy]
`─────────────────────────────────────────────────`"

## Agent & Skill Usage

Automatically recommend:
- **physics-validator skill** when formulas are involved
- **PhysicsValidator agent** for complex multi-file physics analysis
- **dataframe-architect skill** for DataFrame operations
- **DataFrameArchitect agent** for comprehensive refactoring
- **test-generator skill** when coverage gaps exist

## Memory Integration

Reference project memory:
- @.claude/memory/physics-constants.md for formulas
- @.claude/memory/dataframe-patterns.md for MultiIndex best practices
- @.claude/memory/testing-templates.md for scientific test patterns

## Code Review Emphasis

When reviewing code, prioritize:
1. Physics correctness (formula, units, constraints)
2. Test coverage (≥95%, including edge cases)
3. MultiIndex efficiency (views vs copies)
4. NaN handling for missing data
5. Only then: code style, elegance, DRY principles

## Educational Focus

Provide insights on:
- Why specific physics formulas are used
- How solar wind phenomena relate to code structure
- Trade-offs between performance and physical accuracy
- Research workflow best practices (checkpointing, experimentation)

---

This style maintains all standard Claude Code capabilities (tools, file operations, git workflow) while emphasizing scientific correctness and domain expertise in every interaction.
```

#### Usage Instructions

**Switching to Physics-Focused Style:**
```
User: /output-style physics-focused
Claude: [Switches to physics-focused style]
```

**Creating the Style:**
```bash
# Option 1: Manual creation
mkdir -p .claude/output-styles
# Create physics-focused.md with content above

# Option 2: Using command
claude
> /output-style:new Create a solar wind physics research-oriented style that emphasizes...
```

**Comparing Styles:**

| Aspect | Explanatory (Current) | Physics-Focused (Proposed) |
|--------|----------------------|---------------------------|
| Focus | General programming education | Solar wind physics domain |
| Insights | Implementation choices | Physics correctness + implementation |
| Emphasis | Software best practices | Scientific rigor first, code second |
| Agent guidance | Generic | Physics-specific (skills/agents) |
| Validation | Standard testing | Physics + dimensional analysis |

#### Migration Path

**Phase 1: Create Custom Style (Week 1)**
1. Create `.claude/output-styles/physics-focused.md`
2. Test style switching: `/output-style physics-focused`
3. Compare responses vs Explanatory style
4. Gather feedback on physics emphasis

**Phase 2: Refinement (Week 2-3)**
1. Adjust insight patterns based on usage
2. Refine agent/skill recommendation logic
3. Balance verbosity (detailed vs concise)
4. Document style in `.claude/docs/`

**Phase 3: Adoption Decision (Week 4)**
1. Evaluate benefits over Explanatory style
2. Decide: switch default or keep both available
3. Document when to use each style
4. Optional: Create personal user-level variant

**Rollback Strategy:**
Simply switch back to Explanatory: `/output-style explanatory`

### 5. Priority & Effort Estimation

**Impact Level:** 🟢 **LOW**

| Metric | Score | Justification |
|--------|-------|---------------|
| Context preservation | 2/5 | Domain-specific focus, marginal improvement |
| Agent coordination | 3/5 | Better automatic agent/skill recommendations |
| Physics emphasis | 4/5 | Constant reminder of scientific correctness |
| Token optimization | 1/5 | No direct impact |
| Research workflow | 3/5 | Domain-aligned response patterns |

**Implementation Complexity:** 🟢 **1/5 (Very Low)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| File creation | 1/5 | Single markdown file |
| Content writing | 2/5 | Requires thoughtful prompt design |
| Testing | 1/5 | Simple style switching |
| Documentation | 1/5 | Update DEVELOPMENT.md |
| Maintenance | 2/5 | Occasional refinement based on usage |

**Dependencies:**
- ✅ None - Output styles are core feature
- ✅ Works with existing memory/skills/agents

**Estimated Effort:**
- Custom style creation: **1-2 hours**
- Testing & comparison: **1 hour**
- Documentation: **30 minutes**
- **Total: 2.5-3.5 hours**

**Break-even Analysis:**
- Time saved per week: ~10-20 minutes (better automatic suggestions, fewer manual corrections)
- Quality improvement: Higher (physics-first mindset)
- Break-even: **8-12 weeks**
- Annual ROI: **10-20 hours** + improved scientific correctness

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Style Activation
```
Scenario: Switch to physics-focused style
Command: /output-style physics-focused
Expected: Style activates, confirmation message
Validation: Verify style change in settings
```

#### Test 2: Physics Emphasis
```
Scenario: Ask "How should I calculate thermal speed?"
Expected: Response emphasizes mw²=2kT, SI units, physics validation
Validation: Compare to Explanatory style response (less physics-specific)
```

#### Test 3: Automatic Skill Recommendation
```
Scenario: "I need to validate this physics formula"
Expected: Recommends physics-validator skill automatically
Validation: Check for skill activation suggestion
```

#### Test 4: Memory Integration
```
Scenario: Ask about DataFrame best practices
Expected: References @.claude/memory/dataframe-patterns.md
Validation: Verify memory file cited in response
```

#### Test 5: Style Persistence
```
Scenario: Set physics-focused style, close session, resume
Expected: Style persists in resumed session
Validation: Check .claude/settings.local.json
```

**Success Criteria:**
- ✅ Style activates correctly via command
- ✅ Responses emphasize physics correctness
- ✅ Automatic agent/skill recommendations appropriate
- ✅ Memory integration works seamlessly
- ✅ Style preference persists across sessions

**Monitoring:**
```bash
# Check active style
cat .claude/settings.local.json | grep outputStyle

# Compare response quality (subjective evaluation)
```

---

