# Skills System

**Feature Type:** Automatic
**Priority:** HIGH
**Effort:** 7-11 hours
**ROI Break-even:** 3-4 weeks

[← Back to Index](./INDEX.md) | [Next: Subagents →](./03_subagents.md)

---

**⚠️ PREREQUISITES: PHASE 1 (CONDITIONAL)**

**Complete Phase 0 before implementing this feature:**
- ✅ Memory Hierarchy (01_memory_hierarchy.md) implemented
- ✅ Slash Commands (07_slash_commands.md) implemented
- ✅ Decision Gate 1 PASSED (≥30% token reduction, ≥60 min/week saved)

**See [EXECUTOR_GUIDE.md](./EXECUTOR_GUIDE.md) for correct implementation sequence.**

---

**✅ OFFICIAL PLUGIN FEATURE - Native Support**

Skills are officially supported as plugin components and can be packaged for distribution.
See: [Plugin Packaging](./08_plugin_packaging.md#skills)

---

## Feature 2: Skills System

### 1. Feature Overview

**What It Is:**
Skills are model-invoked capability packages that Claude autonomously activates based on context matching. Officially launched as "Agent Skills" in October 2025, they are a core plugin component that enables automatic, context-aware tool deployment.

**Core Capabilities:**
- **Automatic activation** - Claude evaluates and deploys based on relevance (progressive disclosure)
- **Modular structure** - `SKILL.md` + optional supporting files (scripts, templates)
- **Scoped tool access** - `allowed-tools` frontmatter restricts available tools
- **Plugin-packageable** - Can distribute via plugin system for team/community sharing
- **Three storage locations** - Personal (`~/.claude/skills/`), Project (`.claude/skills/`), Plugin (`plugin-name/skills/`)

**Maturity & Prerequisites:**
- ✅ Production-ready (official Anthropic feature, Oct 2025)
- ✅ Native plugin support (package in `plugin-name/skills/`)
- ✅ No external dependencies required
- ✅ Git-friendly (project skills OR plugin distribution)
- ⚠️ Requires clear, specific descriptions for reliable activation

**Technical Constraints:**
- Name: lowercase, numbers, hyphens only (max 64 chars)
- Description: max 1024 characters (critical for activation matching)
- YAML frontmatter required in `SKILL.md`
- Progressive file loading (efficient context management)

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Agent Coordination Overhead (HIGH IMPACT)**
*Current state:* Manual agent selection via Task tool requires explicit prompts like "Use DataFrameArchitect to optimize MultiIndex operations"
*With Skills:* Automatic activation when user requests DataFrame optimization, MultiIndex pattern checks, or performance improvements
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

### 3.5. Risk Assessment

#### Technical Risks

**Risk: Skill Activation False Positives/Negatives**
- **Likelihood:** Medium
- **Impact:** Medium (wrong tool activated or nothing activates)
- **Mitigation:**
  - Write highly specific activation descriptions (1024 char limit)
  - Test activation patterns with diverse prompts
  - Monitor skill activation logs
  - Refine descriptions based on false trigger patterns
  - Provide fallback to manual Task agent invocation

**Risk: Description Character Limit Constraints**
- **Likelihood:** Low
- **Impact:** Low-Medium (activation accuracy reduced)
- **Mitigation:**
  - Prioritize key trigger phrases in first 500 characters
  - Use concise, specific language
  - Test truncated descriptions for activation quality
  - Split complex skills if description exceeds optimal length

**Risk: Tool Scope Limitations**
- **Likelihood:** Low
- **Impact:** Medium (skill can't complete intended task)
- **Mitigation:**
  - Carefully plan `allowed-tools` per skill
  - Test edge cases requiring tools outside scope
  - Document tool limitations in SKILL.md
  - Provide clear handoff to Task agents for out-of-scope operations

**Risk: Plugin Distribution Compatibility**
- **Likelihood:** Low
- **Impact:** Low (skills work locally but fail as plugin)
- **Mitigation:**
  - Test skills in both project and plugin contexts
  - Avoid absolute paths in skill definitions
  - Use relative references from project root
  - Document plugin packaging requirements

#### Adoption Risks

**Risk: Over-Reliance on Automatic Activation**
- **Likelihood:** Medium
- **Impact:** Medium (tasks fail when skill doesn't activate)
- **Mitigation:**
  - Document explicit Task agent invocation patterns
  - Train team to recognize when manual control needed
  - Provide clear error messages when skills can't handle task
  - Maintain Task agent workflows as primary fallback

**Risk: Skill-Agent Role Confusion**
- **Likelihood:** Medium
- **Impact:** Low-Medium (inefficient tool selection)
- **Mitigation:**
  - Create decision matrix: "Use skill for X, agent for Y"
  - Document in project memory (CLAUDE.md)
  - Provide examples of skill vs. agent scenarios
  - Include handoff logic in skill definitions

**Risk: Team Learning Curve**
- **Likelihood:** Low
- **Impact:** Low (temporary productivity dip)
- **Mitigation:**
  - Pilot with 2 skills initially (physics-validator, multiindex-architect)
  - Provide activation pattern examples
  - Demo sessions showing automatic vs. manual workflows
  - Document common pitfalls and solutions

#### Performance Risks

**Risk: Skill Activation Latency**
- **Likelihood:** Low
- **Impact:** Low (minor delay before execution)
- **Mitigation:**
  - Keep SKILL.md files under 1000 tokens
  - Use progressive disclosure (load supporting files only when needed)
  - Monitor activation timing
  - Optimize skill structure if latency detected

**Risk: Token Budget with Multiple Skills**
- **Likelihood:** Low
- **Impact:** Low-Medium (context window pressure)
- **Mitigation:**
  - Limit to 4 core skills initially
  - Evaluate activation patterns before adding more
  - Use skill-specific tool scoping to minimize context
  - Monitor total token usage across skills

### 4. Implementation Specification

#### Proposed Skills Library

##### Skill 1: MultiIndex Architect (`multiindex-architect`)

**File:** `.claude/skills/multiindex-architect/SKILL.md`

```yaml
---
name: multiindex-architect
description: Optimizes pandas MultiIndex DataFrame operations for SolarWindPy's (M/C/S) structure. Recommends .xs() for views, prevents unnecessary copying, manages memory efficiently. Activates for DataFrame operations, MultiIndex queries, performance optimization, or memory management tasks.
allowed-tools: [Read, Grep, Edit, Write]
max_activations_per_hour: 8
rate_limit_message: "MultiIndex architect activated 8 times this hour. Limit prevents repetitive DataFrame suggestions. Override: explicitly request 'optimize all DataFrame operations' to bypass."
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

##### Skill 2: Test Generator (`test-generator`)

**File:** `.claude/skills/test-generator/SKILL.md`

```yaml
---
name: test-generator
description: Automatically generates pytest test cases for SolarWindPy functions ensuring ≥95% coverage. Creates physics-specific tests, edge cases, and validates scientific correctness. Activates when coverage gaps identified or new functions added.
allowed-tools: [Read, Write, Bash(python .claude/scripts/generate-test.py*), Bash(pytest*)]
max_activations_per_hour: 12
rate_limit_message: "Test generator activated 12 times this hour. Limit prevents excessive test creation. Override: explicitly request 'generate tests for all uncovered functions' to bypass."
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
    assert units_conversion_pattern_check(result)
```

## Integration with TestEngineer Agent
- **Skill:** Generate individual test cases, quick coverage fixes
- **Agent:** Design comprehensive test strategies, framework architecture
```

**Supporting Files:**
- `.claude/skills/test-generator/templates/pytest_template.py`
- `.claude/skills/test-generator/examples/physics_test_examples.py`

##### Skill 3: Plan Executor (`plan-executor`)

**File:** `.claude/skills/plan-executor/SKILL.md`

```yaml
---
name: test-generator
description: Automatically generates pytest test cases for SolarWindPy functions ensuring ≥95% coverage. Creates physics-specific tests, edge cases, and validates scientific correctness. Activates when coverage gaps identified or new functions added.
allowed-tools: [Read, Write, Bash(python .claude/scripts/generate-test.py*), Bash(pytest*)]
max_activations_per_hour: 12
rate_limit_message: "Test generator activated 12 times this hour. Limit prevents excessive test creation. Override: explicitly request 'generate tests for all uncovered functions' to bypass."
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
    assert units_conversion_pattern_check(result)
```

## Integration with TestEngineer Agent
- **Skill:** Generate individual test cases, quick coverage fixes
- **Agent:** Design comprehensive test strategies, framework architecture
```

**Supporting Files:**
- `.claude/skills/test-generator/templates/pytest_template.py`
- `.claude/skills/test-generator/examples/physics_test_examples.py`

*Note: Skill numbering reflects current 3-skill implementation after agent consolidation*

**File:** `.claude/skills/plan-executor/SKILL.md`

```yaml
---
name: plan-executor
description: Automates GitHub Issues plan creation using gh-plan-create.sh and gh-plan-phases.sh. Handles batch mode phase creation, value proposition generation, and scope auditing. Activates when planning new features or creating implementation roadmaps.
allowed-tools: [Bash(.claude/scripts/gh-plan-*.sh*), Bash(mkdir*), Bash(cat*), Read, Write]
max_activations_per_hour: 5
rate_limit_message: "Plan executor activated 5 times this hour. Limit prevents excessive planning overhead. Override: explicitly request 'create all pending plans' to bypass."
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

#### Error Recovery and Fallback Chains

**Anthropic Best Practice:** "Build fallback chains to handle failures gracefully. Skills should degrade to manual alternatives rather than block workflow."

Skills provide automatic activation, but failures must not block user progress. Implement 4-level fallback pattern:

##### Fallback Chain Pattern

```
Primary: Skill Auto-Activation
    ↓ (if skill fails or rate-limited)
Fallback 1: Manual Slash Command
    ↓ (if command unavailable or fails)
Fallback 2: Subagent Invocation
    ↓ (if subagent unavailable)
Manual Override: Direct user action
```

##### Example: Physics Validation Fallback Chain

**Scenario:** Physics validator skill fails during ion.py calculation review

**Step 1: Primary (Skill Auto-Activation)**
- User: "Check if thermal speed calculation uses correct units"
- System: Attempts physics-validator skill activation
- **Failure modes:** Rate limit hit (10/hour exceeded), skill not found, allowed-tools restriction

**Step 2: Fallback 1 (Manual Slash Command)**
- System: "Physics validator skill unavailable. Using manual command..."
- Executes: `/physics` slash command
- **Fallback trigger:** If `/physics` command not defined

**Step 3: Fallback 2 (Subagent Invocation)**
- System: "Manual command unavailable. Invoking DataFrameArchitect subagent..."
- Launches: physics-validator subagent with isolated context
- **Fallback trigger:** If subagent system not configured

**Step 4: Manual Override (Direct Action)**
- System: "All automatic validation unavailable. Manual review required:"
- Provides: Validation checklist, reference links, manual verification steps

##### Error Rate Thresholds

**Monitoring:** Track skill activation success/failure rates per session

| Success Rate | Status | Action Required |
|--------------|--------|-----------------|
| ≥90% | ✅ **Good** | No action needed, skill descriptions are accurate |
| 80-90% | ⚠️ **Review** | Check skill descriptions for clarity, adjust triggers |
| <80% | 🔴 **Too Aggressive** | Skill activating incorrectly, revise description or disable |

**Example Metrics:**
```bash
# Session summary
physics-validator: 8 activations, 7 success, 1 fallback → 87.5% (⚠️ Review)
multiindex-architect: 5 activations, 5 success, 0 fallback → 100% (✅ Good)
test-generator: 3 activations, 1 success, 2 fallback → 33% (🔴 Too Aggressive)
plan-executor: 2 activations, 2 success, 0 fallback → 100% (✅ Good)
```

**Corrective Actions:**
- **<80% success:** Revise skill description to be more specific, reduce false activations
- **0 activations in 5 sessions:** Description too narrow, broaden activation triggers
- **>15 activations/session:** Too aggressive, increase rate limits or narrow scope

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

*Immediate Disable (Test If Skills Are The Problem):*
1. Rename `.claude/skills/` to `.claude/skills.disabled/`
2. Start new Claude Code session
3. Skills won't activate, Task agents continue working
4. Verify issue resolves (confirms skills were cause)

*Full Rollback (Local Implementation):*
1. Delete `.claude/skills/` directory entirely
2. `git revert` commits that added skills
3. Resume using explicit Task agent invocations
4. No other changes needed (skills are fully independent)

*Full Rollback (Plugin Installation):*
1. `/plugin uninstall solarwindpy-devtools`
2. Verify skills directory removed
3. Resume using Task agents
4. Local `.claude/skills/` (if any) takes precedence

*Selective Rollback (Disable Specific Skill):*
1. Rename problematic skill: `.claude/skills/physics-validator/` → `.claude/skills/physics-validator.disabled/`
2. Other skills continue working
3. Use Task agent for that specific workflow
4. Investigate and fix skill description/logic

*Rollback Verification Steps:*
- ✅ Skills no longer auto-activate (test with trigger phrases)
- ✅ Task agents work via explicit invocation
- ✅ No activation logging in Notification hooks
- ✅ Workflows function with manual agent selection
- ✅ No performance degradation

*Risk:** Very low - Skills are completely independent, disable anytime without side effects.

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

### 4.5. Alternatives Considered

#### Alternative 1: Manual Task Agent Invocation Only (Status Quo)

**Description:** Continue using explicit `Task` tool invocations for all agent-based workflows.

**Pros:**
- ✅ Zero implementation effort
- ✅ Full control over agent selection
- ✅ No false activation risk
- ✅ Familiar workflow

**Cons:**
- ❌ High cognitive overhead (remember which agent for which task)
- ❌ Manual invocation every time (repetitive)
- ❌ Slower execution (explicit vs. automatic)
- ❌ Misses progressive disclosure benefits

**Decision:** **Rejected** - Automation benefits (40-60% reduction in coordination overhead) justify implementation effort.

#### Alternative 2: Slash Commands Instead of Skills

**Description:** Use slash commands (e.g., `/physics`, `/test`, `/optimize`) to trigger workflows.

**Pros:**
- ✅ Explicit, predictable invocation
- ✅ User controls when tool activates
- ✅ Simpler than skills (no activation matching)
- ✅ Can package in plugins

**Cons:**
- ❌ Requires manual typing (not automatic)
- ❌ Cognitive load to remember command names
- ❌ Doesn't integrate seamlessly into natural language workflow
- ❌ No progressive disclosure (always explicit)

**Decision:** **Complementary** - Skills for automatic activation, slash commands for explicit control. Both implemented (see Feature 7).

#### Alternative 3: Unified Agent with Multi-Domain Expertise

**Description:** Replace 7 specialized agents with one agent that has all domain knowledge.

**Pros:**
- ✅ Single invocation pattern
- ✅ No agent selection decisions
- ✅ Simplified architecture

**Cons:**
- ❌ Massive context window (all domains loaded)
- ❌ Token inefficiency (load physics expertise for testing tasks)
- ❌ Reduced specialization depth
- ❌ Difficult to maintain (monolithic prompt)

**Decision:** **Rejected** - Specialized agents + skills provide better context efficiency and expertise depth.

#### Alternative 4: MCP Server for Tool Integration

**Description:** Use Model Context Protocol servers to provide capabilities instead of skills.

**Pros:**
- ✅ External process isolation
- ✅ Can integrate third-party services
- ✅ Reusable across projects

**Cons:**
- ❌ Overhead of server setup and maintenance
- ❌ Not suitable for simple script execution
- ❌ No automatic activation (requires explicit tool call)
- ❌ Overkill for SolarWindPy's internal workflows

**Decision:** **Future Enhancement** - MCP for external data sources (CDAWeb, SPDF), skills for internal workflows.

#### Alternative 5: Hook-Triggered Automation

**Description:** Use pre/post hooks to trigger validation and testing automatically.

**Pros:**
- ✅ Automatic execution on events
- ✅ No manual invocation needed
- ✅ Enforces quality gates

**Cons:**
- ❌ Only event-driven (not context-aware)
- ❌ Can't respond to natural language requests
- ❌ Fixed trigger patterns (no semantic matching)
- ❌ Interrupt-driven (may slow workflow)

**Decision:** **Complementary** - Hooks for event-driven automation (pre-commit), skills for context-aware assistance (during development).

#### Selected Approach: Skills + Task Agents Hybrid

**Rationale:**
- Skills handle routine, repetitive tasks automatically (60-70%)
- Task agents provide deep expertise for complex work (30-40%)
- Slash commands offer explicit control when needed
- Hooks enforce quality gates at checkpoints

**Trade-offs Accepted:**
- Slight complexity from multiple invocation patterns (mitigated by clear documentation)
- Activation tuning required (mitigated by iterative refinement)
- Learning curve for team (mitigated by gradual rollout)

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

*Technical Prerequisites:*
- ✅ None - Skills are self-contained feature
- ✅ Claude Code with Agent Skills support (October 2025+)
- ✅ No other features required

*Infrastructure Requirements:*
- ✅ `.claude/skills/` directory OR plugin installation capability
- ✅ Git repository (if distributing via plugin)
- ✅ Access to Claude Code plugin marketplace (for distribution)

*Knowledge Prerequisites:*
- ⚠️ Understanding of YAML frontmatter syntax
- ⚠️ Familiarity with progressive disclosure concept
- ⚠️ Clear understanding of when to use Skills vs. Task agents
- ⚠️ Skill description writing (critical for auto-activation accuracy)

*Recommended But Optional:*
- 🔄 Memory Hierarchy - Skills reference memory files for context
- 🔄 Enhanced Hooks - Notification hook can log skill activations
- 🔄 Existing Task Agents - Understanding current agent workflows helps design skills

*Implementation Considerations:*
- ⚠️ Quality depends heavily on description clarity (1024 char limit)
- ⚠️ Testing requires diverse prompts to validate activation patterns
- ⚠️ `allowed-tools` must be carefully scoped per skill

*Plugin-Specific Dependencies:*
- 🔌 Plugin Packaging feature (if distributing to team/community)
- 🔌 GitHub repository for marketplace hosting
- 🔌 `plugin.json` manifest file

**Estimated Effort:**
- Skill creation: **3-5 hours** (0.75-1.25 hours per skill × 4 skills, faster with official spec)
- Rate limiting implementation: **1-2 hours** (add max_activations_per_hour to each skill)
- Error recovery documentation: **1-1.5 hours** (fallback chains, monitoring thresholds)
- Testing & refinement: **1-2 hours** (plugin installation simplifies testing)
- Documentation: **0.5-1 hour** (plugin README)
- **Total: 7-11 hours**

**Note:** Increased from 5-8h to account for rate limiting and error recovery patterns required for safe automatic activation. These additions prevent skill over-activation and ensure graceful degradation when skills fail.

**Detailed Breakdown of Plugin Savings:**

*Where 2-3 Hours Are Saved:*

1. **Skill Structure Research (Saved: 1-1.5h)**
   - *Local:* Research best practices, create custom structure = 1.5-2h
   - *Plugin:* Official YAML frontmatter spec provided = 0.5h to read spec
   - *Savings:* 1-1.5h

2. **Distribution Infrastructure (Saved: 0.5-1h)**
   - *Local:* Design how to share skills across team (git structure, docs) = 1-1.5h
   - *Plugin:* Built-in marketplace distribution, just create plugin.json = 0.5h
   - *Savings:* 0.5-1h

3. **Testing Complexity (Saved: 0.5h)**
   - *Local:* Test skills in multiple developer environments = 1h
   - *Plugin:* Test plugin installation once, works everywhere = 0.5h
   - *Savings:* 0.5h

4. **Documentation Overhead (Saved: 0.5h)**
   - *Local:* Write custom README for skill installation, usage = 1.5h
   - *Plugin:* Standard plugin README format, auto-discovery via `/help` = 1h
   - *Savings:* 0.5h

**Total Savings: 2.5-3h**

*Why Plugin Is Faster:*
- Official spec eliminates research/experimentation
- Built-in distribution removes custom infrastructure design
- Standard formats reduce documentation needs
- Single installation command vs. manual file copying
- Marketplace provides discoverability (no custom sharing mechanism)

**Break-even Analysis:**
- Time saved per week: ~2-3 hours (coordination + repetitive tasks)
- Break-even: **3-4 weeks**
- Annual ROI: **90-140 hours** of productive development time
- **Bonus:** Community distribution capability via marketplace

**Measurement Methodology:**

*How Coordination Overhead Reduction (40-60%) Is Measured:*
1. **Baseline:** Count explicit Task agent invocations in 20 sessions pre-skills implementation
2. **Track:** "Use DataFrameArchitect to..." type prompts (manual agent selection)
3. **Post-implementation:** Count same pattern after skills deployed
4. **Calculation:** (Baseline invocations - Post invocations) / Baseline invocations × 100%
5. **Example:** 25 manual invocations → 12 after skills = (25-12)/25 = 52% reduction

*How Token Reduction (20-30%) Is Measured:*
1. **Baseline:** Measure total tokens consumed by Task agent invocations (include agent prompts + context)
2. **Skills alternative:** Measure tokens consumed by skill activations (scoped context only)
3. **Sampling:** Compare 50 equivalent tasks (25 via Task agents, 25 via Skills)
4. **Calculation:** (Agent tokens - Skill tokens) / Agent tokens × 100%
5. **Verification:** API token usage logs over 2-week period

*How Routine Task Coverage (60-70%) Is Measured:*
1. **Task classification:** Categorize 100 development tasks as "routine" vs. "complex"
2. **Routine criteria:** Single-domain, repetitive pattern, no multi-step coordination required
3. **Skill coverage test:** Attempt each routine task with skills only (no manual agent selection)
4. **Success rate:** Count tasks successfully completed via automatic skill activation
5. **Calculation:** Successful skill activations / Total routine tasks × 100%

*How Time Savings (2-3 hours/week) Are Measured:*
1. **Time task execution:** Track time from task start to completion
2. **Compare:** Manual agent selection (explicit prompt + Task invocation) vs. automatic skill activation
3. **Average savings per task:** Estimated 3-5 minutes for coordination overhead
4. **Frequency:** Estimate 40-60 routine tasks per week based on team velocity
5. **Calculation:** (3-5 min/task) × (40-60 tasks/week) = 120-300 min/week = 2-5 hours/week (conservative: 2-3h)

*Verification Methods:*
- **Activity logging:** Enable skill activation logging (Notification hook)
- **Before/after comparison:** Team survey on coordination effort pre/post skills
- **Token usage:** Claude API usage reports comparing agent vs. skill token consumption
- **Activation accuracy:** Monitor false positives/negatives in skill activation over 4 weeks

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
Expected: DataFrameArchitect agent (Task) activates, not skill
Validation: Complex multi-step tasks should still use agents
```

#### Test 4: Auto-activation on File Changes
```
Scenario: Edit solarwindpy/core/ion.py (physics calculation method)
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

**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
