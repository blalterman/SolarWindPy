# Skills System

**Feature Type:** Automatic
**Priority:** HIGH
**Effort:** 7-11 hours
**ROI Break-even:** 3-4 weeks

[← Back to Index](./INDEX.md) | [Next: Subagents →](./03_subagents.md)

---
## Feature 1: Skills System

### 1. Feature Overview

**What It Is:**
Skills are model-invoked capability packages that Claude autonomously activates based on context matching. Unlike slash commands (user-invoked) or Task agents (explicitly requested), Skills automatically deploy when task descriptions match their defined triggers.

**Core Capabilities:**
- **Automatic activation** - Claude evaluates and deploys based on relevance
- **Modular structure** - `SKILL.md` + optional supporting files (scripts, templates)
- **Scoped tool access** - `allowed-tools` frontmatter restricts available tools
- **Three storage tiers** - Personal (`~/.claude/skills/`), Project (`.claude/skills/`), Plugin-based

**Maturity & Prerequisites:**
- ✅ Production-ready feature in Claude Code
- ✅ No external dependencies required
- ✅ Git-friendly (project skills sync with version control)
- ⚠️ Requires clear, specific descriptions for reliable activation

**Technical Constraints:**
- Name: lowercase, numbers, hyphens only (max 64 chars)
- Description: max 1024 characters (critical for activation matching)
- YAML frontmatter required in `SKILL.md`
- Progressive file loading (efficient context management)

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Agent Coordination Overhead (HIGH IMPACT)**
*Current state:* Manual agent selection via Task tool requires explicit prompts like "Use PhysicsValidator to verify thermal speed calculations"
*With Skills:* Automatic activation when user requests physics validation, thermal speed checks, or unit verification
*Reduction:* 40-60% decrease in explicit agent invocation overhead

✅ **Repetitive Task Automation (HIGH IMPACT)**
*Current state:* Repeated manual execution of testing, validation, formatting workflows
*With Skills:* Auto-trigger on context cues (e.g., "check coverage" activates test-generator skill)
*Efficiency gain:* 5-10 hours/month saved on repetitive workflow invocations

✅ **Token Usage Optimization (MEDIUM IMPACT)**
*Current state:* Full agent system prompts loaded even for simple tasks
*With Skills:* Targeted skill activation with scoped context
*Token savings:* 20-30% reduction in agent-related token consumption

**Productivity Improvements:**
- Seamless workflow integration (no mental overhead for agent selection)
- Faster task execution (automatic vs. explicit invocation)
- Lower cognitive load (focus on task, not tooling)

**Research Workflow Enhancements:**
- Physics validation happens automatically during calculations
- MultiIndex operations trigger DataFrame expertise automatically
- Test generation activates when coverage concerns arise

### 3. Integration Strategy

**Architecture Fit:**

Skills complement the existing 7-agent system by providing automatic invocation layer:

```
Current Architecture:
User Request → Manual Task Selection → Agent Execution → Result

Enhanced Architecture:
User Request → Skill Auto-Detection → [Skill OR Task Agent] → Result
                                    ↓
                              Skills handle 60-70% of routine tasks
                              Task agents for complex/multi-step work
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **7 Specialized Agents** | Agents become "deep expertise" for complex tasks; Skills handle routine operations |
| **Hook System** | Skills can trigger hooks; hooks can validate skill outputs |
| **GitHub Issues Planning** | Planning skill automates gh-plan-*.sh execution patterns |
| **Memory (CLAUDE.md)** | Skills reference memory; memory documents when to use skills |
| **Testing Framework** | Test generation skill complements TestEngineer agent |

**Backward Compatibility:**
✅ **Fully backward compatible** - Skills layer atop existing infrastructure
✅ **No migration required** - Can adopt incrementally
✅ **Task agents preserved** - For cases requiring explicit control or complex coordination

### 4. Implementation Specification

#### Proposed Skills Library

##### Skill 1: Physics Validator (`physics-validator`)

**File:** `.claude/skills/physics-validator/SKILL.md`

```yaml
---
name: physics-validator
description: Automatically validates solar wind physics calculations including thermal speed (mw²=2kT), SI unit consistency, proper NaN handling for missing data, and physical constraint verification. Activates when user mentions physics validation, unit checking, thermal speed, or scientific correctness.
allowed-tools: [Read, Grep, Bash(python .claude/hooks/physics-validation.py*)]
---

# Physics Validation Skill

## Purpose
Ensures all physics calculations in SolarWindPy maintain scientific correctness.

## Automatic Activation Triggers
- "validate physics"
- "check thermal speed"
- "verify units"
- "ensure SI units"
- "physics correctness"
- Code changes to `solarwindpy/core/ion.py` or `solarwindpy/core/plasma.py`

## Validation Checklist
1. **Thermal Speed Formula:** mw² = 2kT (not 3kT)
2. **SI Units:** velocity (m/s), density (m⁻³), temperature (K)
3. **NaN Handling:** Missing data as NaN, never 0 or -999
4. **Physical Constraints:** Positive densities, temperatures, speeds

## Execution Pattern
```bash
# Run physics validation on changed files
python .claude/hooks/physics-validation.py ${modified_files}

# Generate validation report
python .claude/hooks/physics-validation.py --report
```

## Integration with PhysicsValidator Agent
- **Skill:** Quick validation checks, pre-commit verification
- **Agent:** Deep analysis, formula derivation, multi-file refactoring
```

**Supporting Files:**
- `.claude/skills/physics-validator/examples/thermal_speed_correct.py`
- `.claude/skills/physics-validator/examples/thermal_speed_incorrect.py`

##### Skill 2: MultiIndex Architect (`multiindex-architect`)

**File:** `.claude/skills/multiindex-architect/SKILL.md`

```yaml
---
name: multiindex-architect
description: Optimizes pandas MultiIndex DataFrame operations for SolarWindPy's (M/C/S) structure. Recommends .xs() for views, prevents unnecessary copying, manages memory efficiently. Activates for DataFrame operations, MultiIndex queries, performance optimization, or memory management tasks.
allowed-tools: [Read, Grep, Edit, Write]
---

# MultiIndex Architect Skill

## Purpose
Ensures efficient pandas MultiIndex operations maintaining SolarWindPy's three-level structure.

## Automatic Activation Triggers
- "optimize DataFrame"
- "MultiIndex operation"
- "improve performance"
- "memory usage"
- ".loc vs .xs"
- Code changes to files with DataFrame operations

## MultiIndex Structure
```python
# Level M: Measurement - Physical quantity type
#   Examples: v, n, w, p, b, T, q, beta, cs, ca, rho, flux, ...
#   (50+ measurements - use df.index.get_level_values('M').unique() to see all)
#
# Level C: Component (measurement-dependent)
#   - Cartesian: x, y, z (lowercase)
#   - RTN coordinates: R, T, N (uppercase) — "T" is tangential, not temperature
#   - Anisotropy: par, per, scalar (lowercase)
#   - None (for scalar measurements)
#
# Level S: Species - Particle type
#   Examples: p, a, e, O, Fe, C, He, Ne, ...
#   (use df.index.get_level_values('S').unique() to see all)
```

## Best Practices
1. **Use .xs() for cross-sections** (returns views, not copies)
2. **Avoid chained indexing** (df[...][...] creates copies)
3. **Prefer .loc for single access**
4. **Use .query() for complex filters**

## Anti-Patterns to Flag
```python
# ❌ BAD - Creates unnecessary copies
df_subset = df.loc[measurement].loc[component]

# ✅ GOOD - Efficient view
df_subset = df.xs((measurement, component), level=(0, 1))
```

## Integration with DataFrameArchitect Agent
- **Skill:** Quick fixes, pattern recognition, local optimization
- **Agent:** Architecture redesign, complex refactoring, memory profiling
```

**Supporting Files:**
- `.claude/skills/multiindex-architect/templates/efficient_access_patterns.py`
- `.claude/skills/multiindex-architect/templates/memory_optimization_checklist.md`

##### Skill 3: Test Generator (`test-generator`)

**File:** `.claude/skills/test-generator/SKILL.md`

```yaml
---
name: test-generator
description: Automatically generates pytest test cases for SolarWindPy functions ensuring ≥95% coverage. Creates physics-specific tests, edge cases, and validates scientific correctness. Activates when coverage gaps identified or new functions added.
allowed-tools: [Read, Write, Bash(python .claude/scripts/generate-test.py*), Bash(pytest*)]
---

# Test Generator Skill

## Purpose
Maintains ≥95% test coverage through intelligent test generation.

## Automatic Activation Triggers
- "generate tests"
- "improve coverage"
- "test this function"
- "add test cases"
- Coverage drops below 95%
- New functions detected without tests

## Test Generation Strategy
1. **Happy path** - Standard valid inputs
2. **Edge cases** - Boundaries, empty arrays, single elements
3. **Physics validation** - Scientific correctness checks
4. **Error conditions** - Invalid inputs, type errors

## Execution Pattern
```bash
# Generate tests for specific file
python .claude/scripts/generate-test.py solarwindpy/core/ion.py

# Check coverage
pytest --cov=solarwindpy --cov-report=term -q

# Run only new tests
pytest tests/test_ion_generated.py -v
```

## Test Template
```python
def test_function_name_happy_path():
    """Test standard valid inputs."""
    # Arrange
    expected = ...

    # Act
    result = function_name(valid_input)

    # Assert
    assert result == expected

def test_function_name_physics():
    """Validate physics correctness."""
    # Physics-specific assertions
    assert thermal_speed_formula_check(result)
```

## Integration with TestEngineer Agent
- **Skill:** Generate individual test cases, quick coverage fixes
- **Agent:** Design comprehensive test strategies, framework architecture
```

**Supporting Files:**
- `.claude/skills/test-generator/templates/pytest_template.py`
- `.claude/skills/test-generator/examples/physics_test_examples.py`

##### Skill 4: Plan Executor (`plan-executor`)

**File:** `.claude/skills/plan-executor/SKILL.md`

```yaml
---
name: plan-executor
description: Automates GitHub Issues plan creation using gh-plan-create.sh and gh-plan-phases.sh. Handles batch mode phase creation, value proposition generation, and scope auditing. Activates when planning new features or creating implementation roadmaps.
allowed-tools: [Bash(.claude/scripts/gh-plan-*.sh*), Bash(mkdir*), Bash(cat*), Read, Write]
---

# Plan Executor Skill

## Purpose
Streamlines GitHub Issues planning workflow with automated script execution.

## Automatic Activation Triggers
- "create plan for"
- "plan implementation"
- "generate GitHub Issues"
- "new feature plan"
- "add phases to plan"

## Workflow Automation

### Step 1: Create Overview Issue
```bash
.claude/scripts/gh-plan-create.sh -p <priority> -d <domain> "Title"
# priority: critical|high|medium|low
# domain: physics|data|plotting|testing|infrastructure|docs
```

### Step 2: Generate Phases (Batch Mode)
```bash
mkdir -p tmp
cat > tmp/phases.conf <<'EOF'
Phase Name|Estimated Duration|Dependencies
Foundation Setup|2-3 hours|None
Core Implementation|4-5 hours|Phase 1
Testing & Validation|1-2 hours|Phase 2
EOF

.claude/scripts/gh-plan-phases.sh -b tmp/phases.conf $OVERVIEW_ISSUE
rm -f tmp/phases.conf
```

### Step 3: Verify Creation
```bash
gh issue view $OVERVIEW_ISSUE
.claude/scripts/gh-plan-status.sh
```

## Integration with UnifiedPlanCoordinator Agent
- **Skill:** Execute standard planning patterns, routine plan creation
- **Agent:** Complex multi-phase planning, strategic architecture, custom workflows
```

**Supporting Files:**
- `.claude/skills/plan-executor/templates/phase_config_template.conf`
- `.claude/skills/plan-executor/examples/sample_plans.md`

#### Migration Path from Current System

**Phase 1: Co-existence (Weeks 1-2)**
1. Create 4 core skills (physics-validator, multiindex-architect, test-generator, plan-executor)
2. Test skills in parallel with existing Task agents
3. Monitor activation accuracy and adjust descriptions
4. Document which tasks skills handle vs. agents

**Phase 2: Gradual Adoption (Weeks 3-4)**
1. Add skills to project memory (CLAUDE.md) for awareness
2. Update agent documentation to clarify skill vs. agent usage
3. Create user guide for when to rely on automatic vs. explicit
4. Gather metrics on time savings and token reduction

**Phase 3: Optimization (Week 5+)**
1. Refine skill descriptions based on activation patterns
2. Add advanced skills for specialized workflows
3. Create personal skills for individual developer preferences
4. Measure impact: coordination overhead, token usage, time savings

**Rollback Strategy:**
Skills can be disabled by removing/renaming `.claude/skills/` directory. All Task agents continue functioning unchanged.

#### Configuration Changes

**No changes required to `.claude/settings.json`** - Skills work out-of-the-box.

**Optional enhancement** to track skill activations:
```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*skill*",
        "hooks": [{
          "type": "command",
          "command": "echo '[SKILL ACTIVATED]' >> .claude/logs/skill-activity.log",
          "timeout": 5
        }]
      }
    ]
  }
}
```

### 5. Priority & Effort Estimation

**Impact Level:** 🔴 **HIGH**

| Metric | Score | Justification |
|--------|-------|---------------|
| Reduces coordination overhead | 5/5 | Eliminates 40-60% of manual agent selection |
| Improves automation | 5/5 | Automatic activation for routine tasks |
| Token optimization | 4/5 | 20-30% reduction in agent-related tokens |
| Context preservation | 3/5 | Indirect benefit through scoped activation |
| Plan efficiency | 4/5 | Plan executor automates repetitive workflow |

**Implementation Complexity:** 🟡 **2/5 (Low-Medium)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| File creation | 1/5 | Simple markdown files with YAML frontmatter |
| Integration | 2/5 | No code changes, additive only |
| Testing | 2/5 | Validate activation through usage |
| Documentation | 3/5 | Requires clear description writing |
| Maintenance | 2/5 | Occasional description refinement |

**Dependencies:**
- ✅ None - Skills are self-contained
- ✅ No tool changes required
- ✅ No hook modifications needed
- ⚠️ Quality depends on description clarity

**Estimated Effort:**
- Skill creation: **4-6 hours** (1-1.5 hours per skill × 4 skills)
- Testing & refinement: **2-3 hours**
- Documentation: **1-2 hours**
- **Total: 7-11 hours**

**Break-even Analysis:**
- Time saved per week: ~2-3 hours (coordination + repetitive tasks)
- Break-even: **3-4 weeks**
- Annual ROI: **90-140 hours** of productive development time

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Activation Accuracy
```
Scenario: User mentions "validate physics in ion.py"
Expected: physics-validator skill activates
Validation: Check for physics-validation.py execution
```

#### Test 2: Tool Restriction
```
Scenario: physics-validator skill active
Expected: Only allowed tools (Read, Grep, Bash(physics-validation)) available
Validation: Attempt Edit operation, should be restricted
```

#### Test 3: Skill vs. Agent Boundary
```
Scenario: User requests "comprehensive physics refactoring across 10 files"
Expected: PhysicsValidator agent (Task) activates, not skill
Validation: Complex multi-step tasks should still use agents
```

#### Test 4: Auto-activation on File Changes
```
Scenario: Edit solarwindpy/core/ion.py (thermal speed calculation)
Expected: physics-validator skill triggers post-edit
Validation: Verify physics validation report generated
```

#### Test 5: Plan Executor Workflow
```
Scenario: User says "create plan for dark mode implementation"
Expected: plan-executor skill runs gh-plan-create.sh
Validation: GitHub Issue created with proper labels
```

**Success Criteria:**
- ✅ Activation accuracy ≥ 85% for clear trigger phrases
- ✅ Tool restrictions enforced (no unauthorized tool access)
- ✅ Skills handle routine tasks, agents handle complex work
- ✅ Token usage reduction of 20-30% measured over 2-week period
- ✅ No regressions in existing workflow functionality

**Monitoring:**
```bash
# Track skill activations (if Notification hook added)
grep '\[SKILL ACTIVATED\]' .claude/logs/skill-activity.log | wc -l

# Monitor token usage trends
# Compare session token consumption before/after skills deployment
```

---

