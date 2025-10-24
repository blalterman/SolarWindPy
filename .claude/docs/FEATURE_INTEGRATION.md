# Claude Code Feature Integration Guide

**Version:** 1.0
**Date:** 2025-10-23
**Status:** Planning & Design Phase

## Executive Summary

This document provides comprehensive analysis and implementation strategy for integrating recent Claude Code native features into SolarWindPy's development workflow. Based on extensive research of Claude Code documentation and analysis of current SolarWindPy architecture, we've identified 6 major features that directly address identified workflow pain points.

### Quick Reference: Feature-to-Pain Point Mapping

| Pain Point | Primary Solution | Secondary Support |
|------------|------------------|-------------------|
| Agent coordination overhead | Skills System | Subagents, Memory |
| Context preservation across sessions | Memory Hierarchy | Checkpointing |
| Repetitive task automation | Skills System | Enhanced Hooks |
| Plan execution efficiency | Subagents, Memory | Skills, Hooks |
| Token usage optimization | Memory, Checkpointing | Skills auto-activation |

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
# Level M: Measurement (velocity, density, temperature)
# Level C: Component (x, y, z, r, t, n)
# Level S: Species (protons, alphas, electrons)
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

## Feature 2: Memory Hierarchy

### 1. Feature Overview

**What It Is:**
A 4-tier persistent context management system that retains project guidelines, user preferences, and organizational policies across sessions. Memory eliminates the need to repeat common instructions.

**Core Capabilities:**
- **Four-tier hierarchy** with cascading priority:
  1. **Enterprise** (`/Library/Application Support/ClaudeCode/CLAUDE.md`, etc.) - Org-wide
  2. **Project** (`./CLAUDE.md` or `./.claude/CLAUDE.md`) - Team-shared
  3. **User** (`~/.claude/CLAUDE.md`) - Personal cross-project
  4. **Local** (`./CLAUDE.local.md`) - Project-specific personal (deprecated)
- **File imports** - Modular composition via `@path/to/file` syntax (5-level depth)
- **Automatic discovery** - Recursive upward traversal from working directory
- **Markdown-based** - Simple text files, git-friendly

**Maturity & Prerequisites:**
- ✅ Production-ready, core Claude Code feature
- ✅ No external dependencies
- ✅ Works with existing CLAUDE.md files
- ✅ Supports incremental adoption

**Technical Constraints:**
- Import depth limited to 5 levels
- Imports not evaluated inside code spans/blocks
- Higher tiers load first (enterprise → project → user → local)
- Files discovered via recursive directory traversal

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Context Preservation Across Sessions (CRITICAL IMPACT)**
*Current state:* SolarWindPy context (physics rules, MultiIndex structure, testing requirements) loaded via single monolithic CLAUDE.md
*With Memory:* Modular memory files for physics constants, DataFrame patterns, testing templates, git workflows
*Improvement:* Instant context restoration across sessions, no repeated explanations

✅ **Token Usage Optimization (HIGH IMPACT)**
*Current state:* Full CLAUDE.md (currently ~300 lines) loaded every session
*With Memory:* Granular imports load only needed context
*Token savings:* 30-50% reduction through selective memory loading

✅ **Agent Coordination (MEDIUM IMPACT)**
*Current state:* Agent selection matrix embedded in CLAUDE.md
*With Memory:* Dedicated memory files for each agent's usage patterns
*Benefit:* Better context for when to use agents vs. skills

**Productivity Improvements:**
- Zero repeated context-setting ("remember to use SI units...")
- Faster onboarding for new contributors (clear memory structure)
- Consistent conventions across all development sessions

**Research Workflow Enhancements:**
- Physics constants/formulas instantly available
- DataFrame access patterns as reusable templates
- Testing strategies documented and auto-loaded

### 3. Integration Strategy

**Architecture Fit:**

Memory hierarchy enhances existing documentation structure:

```
Current: CLAUDE.md (monolithic)
├── Critical Rules
├── Agent Selection Matrix
├── Essential Commands
└── Prompt Improvement Protocol

Enhanced: CLAUDE.md (orchestrator with imports)
├── @.claude/memory/critical-rules.md
├── @.claude/memory/agent-selection.md
├── @.claude/memory/essential-commands.md
├── @.claude/memory/physics-constants.md
├── @.claude/memory/dataframe-patterns.md
└── @.claude/memory/testing-templates.md
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **CLAUDE.md** | Refactor as orchestrator with imports (backward compatible) |
| **7 Specialized Agents** | Each agent gets dedicated memory file with usage patterns |
| **Hook System** | Hooks documented in `.claude/memory/hooks-reference.md` |
| **Skills** | Skill activation patterns in `.claude/memory/skills-usage.md` |
| **Testing** | Test templates and coverage requirements in dedicated memory |

**Backward Compatibility:**
✅ **Fully compatible** - Claude Code reads CLAUDE.md with or without imports
✅ **Incremental migration** - Can add imports gradually
✅ **Fallback** - If imports fail, main CLAUDE.md content still loads

### 4. Implementation Specification

#### Proposed Memory Structure

```
.claude/memory/
├── critical-rules.md           # Branch protection, test requirements
├── agent-selection.md          # When to use which agent/skill
├── physics-constants.md        # Solar wind physics reference
├── dataframe-patterns.md       # MultiIndex best practices
├── testing-templates.md        # Test patterns for ≥95% coverage
├── git-workflows.md            # Branch naming, commit conventions
├── hooks-reference.md          # Hook system quick reference
├── skills-usage.md             # Skill activation patterns
└── plan-workflows.md           # GitHub Issues planning process
```

#### Memory File Examples

##### Memory File 1: Physics Constants

**File:** `.claude/memory/physics-constants.md`

```markdown
# Solar Wind Physics Constants & Formulas

## Critical Formulas

### Thermal Speed
**CORRECT:** `mw² = 2kT`
**INCORRECT:** `mw² = 3kT` ❌

Where:
- `m` = particle mass (kg)
- `w` = thermal speed (m/s)
- `k` = Boltzmann constant (1.380649 × 10⁻²³ J/K)
- `T` = temperature (K)

### Alfvén Speed
```
v_A = B / √(μ₀ρ)
```
- `B` = magnetic field strength (T)
- `μ₀` = permeability of free space (4π × 10⁻⁷ H/m)
- `ρ` = mass density (kg/m³)

## SI Units (MANDATORY)

| Quantity | Unit | Symbol |
|----------|------|--------|
| Velocity | meters/second | m/s |
| Density | per cubic meter | m⁻³ |
| Temperature | Kelvin | K |
| Magnetic Field | Tesla | T |
| Energy | Joules | J |

## Missing Data Convention
**ALWAYS use NaN** for missing/invalid data.
**NEVER use** 0, -999, -1, or other sentinel values.

```python
import numpy as np

# ✅ CORRECT
velocity_missing = np.nan

# ❌ INCORRECT
velocity_missing = -999  # NO!
velocity_missing = 0     # NO!
```

## Physical Constraints

- ✅ Density > 0 (particles/m³)
- ✅ Temperature > 0 (K)
- ✅ Speed ≥ 0 (m/s)
- ✅ Thermal speed uses factor of 2, not 3
```

##### Memory File 2: DataFrame Patterns

**File:** `.claude/memory/dataframe-patterns.md`

```markdown
# SolarWindPy MultiIndex DataFrame Patterns

## Structure Overview

```python
# Three-level MultiIndex (M, C, S)
levels = {
    'M': ['Np', 'Vp', 'Tp', 'Na', 'Va', 'Ta'],  # Measurement
    'C': ['x', 'y', 'z', 'r', 't', 'n'],        # Component
    'S': ['p', 'a', 'e']                         # Species (p=proton, a=alpha, e=electron)
}
```

## Efficient Access Patterns

### ✅ BEST: Use .xs() for Cross-Sections (Returns Views)
```python
# Single level access
proton_data = df.xs('p', level='S')

# Multi-level access
proton_velocity_x = df.xs(('Vp', 'x'), level=('M', 'C'))

# Complex cross-section
proton_velocities = df.xs('p', level='S').xs('V', level='M', drop_level=False)
```

### ✅ GOOD: Use .loc for Single Access
```python
# Single cell
value = df.loc[('Np', 'x', 'p'), 'column_name']

# Slicing with .loc
subset = df.loc[('Np', slice(None), 'p'), :]
```

### ❌ AVOID: Chained Indexing (Creates Copies)
```python
# BAD - Each step creates a copy
df_bad = df.loc['Np'].loc['x'].loc['p']

# GOOD - Single operation
df_good = df.xs(('Np', 'x', 'p'), level=('M', 'C', 'S'))
```

### ✅ EFFICIENT: Use .query() for Complex Filters
```python
# Complex filtering
result = df.query('M == "Vp" and C in ["x", "y", "z"] and S == "p"')
```

## Memory Optimization

### View vs. Copy
```python
# Returns VIEW (no memory copy)
view = df.xs('p', level='S')
view.memory_usage()  # Minimal additional memory

# Returns COPY (doubles memory)
copy = df[df.index.get_level_values('S') == 'p'].copy()
copy.memory_usage()  # Full DataFrame size
```

### Downcast for Memory Savings
```python
# Convert float64 → float32 where appropriate (check precision needs first!)
df_optimized = df.astype({col: 'float32' for col in float_cols})
```

## Common Pitfalls

### ❌ Incorrect: SettingWithCopyWarning
```python
# BAD
subset = df[df['Np'] > 5]  # This might be a view or copy (ambiguous)
subset['new_col'] = 0      # SettingWithCopyWarning!
```

### ✅ Correct: Explicit Copy or Direct Assignment
```python
# GOOD Option 1: Explicit copy
subset = df[df['Np'] > 5].copy()
subset['new_col'] = 0

# GOOD Option 2: Direct assignment
df.loc[df['Np'] > 5, 'new_col'] = 0
```
```

##### Memory File 3: Testing Templates

**File:** `.claude/memory/testing-templates.md`

```markdown
# SolarWindPy Testing Templates

## Coverage Requirement
**MANDATORY: ≥95% test coverage** enforced by pre-commit hooks.

## Standard Test Structure

```python
import pytest
import numpy as np
from solarwindpy.core import Plasma, Ion

class TestClassName:
    """Test suite for ClassName functionality."""

    def test_function_happy_path(self):
        """Test standard valid inputs (REQUIRED)."""
        # Arrange
        expected = ...
        input_data = ...

        # Act
        result = function(input_data)

        # Assert
        assert result == expected

    def test_function_edge_cases(self):
        """Test boundary conditions (REQUIRED)."""
        # Empty arrays
        result_empty = function(np.array([]))
        assert len(result_empty) == 0

        # Single element
        result_single = function(np.array([1.0]))
        assert result_single.shape == (1,)

        # Large arrays
        result_large = function(np.random.rand(10000))
        assert len(result_large) == 10000

    def test_function_physics_validation(self):
        """Validate physics correctness (REQUIRED for scientific functions)."""
        # Thermal speed formula check
        ion = Ion(temperature=1e5, mass=1.67e-27)
        thermal_speed = ion.thermal_speed()

        # Verify mw² = 2kT
        k_B = 1.380649e-23
        expected = np.sqrt(2 * k_B * 1e5 / 1.67e-27)
        np.testing.assert_allclose(thermal_speed, expected, rtol=1e-6)

    def test_function_error_handling(self):
        """Test invalid inputs raise appropriate errors (REQUIRED)."""
        with pytest.raises(ValueError, match="must be positive"):
            function(negative_value=-1.0)

        with pytest.raises(TypeError, match="expected array"):
            function(invalid_type="string")

    def test_function_nan_handling(self):
        """Test NaN handling for missing data (REQUIRED)."""
        input_with_nan = np.array([1.0, np.nan, 3.0])
        result = function(input_with_nan)

        # NaN should propagate or be handled explicitly
        assert np.isnan(result[1]) or np.isfinite(result[1])
```

## Physics-Specific Test Patterns

### Testing Physical Constraints
```python
def test_density_positive():
    """Density must always be positive."""
    plasma = Plasma(density=-1.0)  # Should raise

    # Or if silently clamped:
    plasma = Plasma(density=-1.0)
    assert plasma.density > 0

def test_temperature_positive():
    """Temperature must always be positive (K)."""
    ion = Ion(temperature=0.0)
    with pytest.raises(ValueError, match="Temperature must be positive"):
        ion.validate()
```

### Testing Unit Consistency
```python
def test_velocity_si_units():
    """Velocity must be in m/s (SI units)."""
    plasma = Plasma(velocity=400)  # Assuming km/s would be wrong
    # Should be 400000 m/s or raise error
    assert plasma.velocity > 1000  # In m/s range
```

## Running Tests

```bash
# Quick test (changed files only)
.claude/hooks/test-runner.sh --changed

# Full test suite with coverage
pytest --cov=solarwindpy --cov-report=term -q

# Generate HTML coverage report
pytest --cov=solarwindpy --cov-report=html -q
open htmlcov/index.html

# Physics-specific tests
.claude/hooks/test-runner.sh --physics
```

## Auto-generating Tests

```bash
# Generate test template for new module
python .claude/scripts/generate-test.py solarwindpy/core/new_module.py

# Output: tests/test_new_module.py with structure above
```
```

#### Updated CLAUDE.md with Imports

**File:** `CLAUDE.md` (refactored version)

```markdown
# CLAUDE.md - Essential Claude AI Instructions

This file provides essential guidance to Claude Code when working with the SolarWindPy repository.

## Critical Rules
@.claude/memory/critical-rules.md

## Agent & Skills Selection
@.claude/memory/agent-selection.md

## Physics Reference
@.claude/memory/physics-constants.md

## DataFrame Patterns
@.claude/memory/dataframe-patterns.md

## Testing Guidelines
@.claude/memory/testing-templates.md

## Git Workflows
@.claude/memory/git-workflows.md

## Essential Commands
@.claude/memory/essential-commands.md

## Hook System
@.claude/memory/hooks-reference.md

## Planning Workflow
@.claude/memory/plan-workflows.md

---

**For detailed documentation beyond these essentials:**
- Development standards → .claude/docs/DEVELOPMENT.md
- Agent specifications → .claude/docs/AGENTS.md
- Feature integration → .claude/docs/FEATURE_INTEGRATION.md
```

#### User-Level Personal Memory

**File:** `~/.claude/CLAUDE.md` (example for personal preferences)

```markdown
# Personal Development Preferences

## Code Style
- Prefer explicit type hints over implicit
- Max line length: 88 (Black default)
- Sort imports with isort

## Testing Preferences
- Use pytest fixtures for common setup
- Prefer parametrize over multiple test functions
- Always include docstrings in test functions

## Git Preferences
- Commit message format: `<type>(<scope>): <description>`
- Types: feat, fix, docs, test, refactor, chore
- Always include "Generated with Claude Code" footer

## Workflow Preferences
- Run Black formatter before committing
- Check flake8 before push
- Prefer small, focused commits over large changesets
```

#### Migration Path

**Phase 1: Create Memory Structure (Week 1)**
1. Create `.claude/memory/` directory
2. Extract sections from current CLAUDE.md into dedicated memory files
3. Test import syntax: `@.claude/memory/physics-constants.md`
4. Verify backward compatibility (CLAUDE.md still works without imports)

**Phase 2: Incremental Adoption (Week 2)**
1. Update CLAUDE.md to use imports for 2-3 sections
2. Monitor for any loading issues or missing context
3. Gather feedback on context preservation quality
4. Refine memory file content based on usage

**Phase 3: Full Migration (Week 3)**
1. Convert all CLAUDE.md sections to imported memory files
2. Create user-level personal memory (`~/.claude/CLAUDE.md`)
3. Document memory structure in `.claude/docs/MEMORY.md`
4. Measure token reduction and context quality

**Phase 4: Optimization (Week 4+)**
1. Add advanced memory features (conditional imports, context-specific memories)
2. Create team shared memories for collaboration patterns
3. Monitor memory effectiveness and iterate

**Rollback Strategy:**
Keep current CLAUDE.md content as fallback. If imports fail, inline content provides full context.

### 5. Priority & Effort Estimation

**Impact Level:** 🔴 **CRITICAL**

| Metric | Score | Justification |
|--------|-------|---------------|
| Context preservation | 5/5 | Eliminates repeated context-setting across sessions |
| Token optimization | 5/5 | 30-50% reduction through selective loading |
| Agent coordination | 4/5 | Better context for agent/skill selection |
| Repetitive automation | 3/5 | Templates reduce manual documentation lookup |
| Plan efficiency | 4/5 | Planning workflows documented once, referenced always |

**Implementation Complexity:** 🟡 **3/5 (Medium)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| File creation | 2/5 | Extract content from CLAUDE.md into separate files |
| Import syntax | 1/5 | Simple `@path` references |
| Testing | 3/5 | Ensure all imports resolve correctly |
| Documentation | 4/5 | Requires thoughtful content organization |
| Maintenance | 3/5 | Keep memories synchronized with codebase evolution |

**Dependencies:**
- ✅ None - Memory is core Claude Code feature
- ⚠️ Requires careful extraction to avoid breaking existing context
- ⚠️ Import paths must be correct (relative or absolute)

**Estimated Effort:**
- Memory structure design: **2-3 hours**
- Content extraction: **4-6 hours** (9 memory files)
- Testing & validation: **2-3 hours**
- Documentation: **1-2 hours**
- **Total: 9-14 hours**

**Break-even Analysis:**
- Time saved per session: ~5-10 minutes (no repeated context-setting)
- Sessions per week: ~10-15
- Weekly savings: **50-150 minutes** (0.8-2.5 hours)
- Break-even: **4-6 weeks**
- Annual ROI: **40-120 hours** of productive development time

**Token Savings:**
- Current CLAUDE.md: ~2,500 tokens per session load
- Optimized selective imports: ~1,000-1,500 tokens
- Savings: **40-60% token reduction** per session
- Annual: **~500,000-750,000 tokens saved** (assuming 200 sessions/year)

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Import Resolution
```bash
# Verify all imports resolve correctly
claude --mode headless -p "List all memory files loaded" > /tmp/memory_check.txt
grep "@.claude/memory" /tmp/memory_check.txt
# Expected: All 9 memory files listed and loaded
```

#### Test 2: Context Preservation
```
Session 1: Ask about thermal speed formula
Session 2 (new): Ask same question without repeating context
Expected: Claude knows thermal speed is mw²=2kT from memory
Validation: No need to re-explain physics rules
```

#### Test 3: Selective Loading
```
Scenario: Request DataFrame optimization help
Expected: dataframe-patterns.md loaded, physics-constants.md not needed
Validation: Monitor which memory files Claude references
```

#### Test 4: Cascading Priority
```
Setup: Create conflicting rules in project vs. user memory
Expected: Project memory (higher tier) takes precedence
Validation: Claude follows project rule, not user preference
```

#### Test 5: Backward Compatibility
```
Scenario: Temporarily remove .claude/memory/ directory
Expected: Inline CLAUDE.md content provides full fallback
Validation: No degradation in context quality
```

**Success Criteria:**
- ✅ All 9 memory files load without errors
- ✅ Import depth ≤5 levels maintained
- ✅ Context preservation verified across 5+ sessions
- ✅ Token reduction of 30-50% measured
- ✅ Zero regressions in existing workflow

**Monitoring:**
```bash
# Check memory file access patterns (if logging added)
grep "Loading memory" .claude/logs/memory-access.log

# Measure token usage reduction
# Compare session transcripts before/after memory optimization
```

---

## Feature 3: Subagents (Enhanced Agent System)

### 1. Feature Overview

**What It Is:**
Subagents are specialized AI assistants with independent context windows and custom system prompts. Unlike the Task tool (which delegates to named agent types within the main conversation), subagents operate in isolation with separate memory.

**Core Capabilities:**
- **Independent context** - Each subagent has its own conversation window (prevents main context pollution)
- **Custom system prompts** - Tailored expertise instructions per subagent
- **Granular tool access** - Per-subagent tool restrictions via frontmatter
- **Model selection** - Choose specific models (sonnet, opus, haiku) or inherit
- **Reusable** - Share across projects via `.claude/agents/` or `~/.claude/agents/`

**Distinction from Task Tool:**

| Aspect | Task Tool (Current) | Subagents |
|--------|---------------------|-----------|
| Context | Shares main conversation context | Independent context window |
| Invocation | Named agent types (PhysicsValidator, etc.) | Custom agent files |
| Memory | Accumulates in main conversation | Isolated, doesn't pollute main |
| Tool Access | Inherits all tools | Configurable per subagent |
| Complexity | Simpler, for straightforward delegation | Better for complex isolated tasks |

**Maturity & Prerequisites:**
- ✅ Production-ready feature
- ✅ No external dependencies
- ✅ Works with existing Task-based agents
- ⚠️ Adds latency (subagent starts with clean slate)

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Agent Coordination Overhead (MEDIUM-HIGH IMPACT)**
*Current state:* All agent interactions accumulate in main conversation context
*With Subagents:* Complex physics analysis or DataFrame refactoring runs in isolated context
*Improvement:* 30-40% reduction in main conversation token bloat from multi-step agent tasks

✅ **Token Usage Optimization (HIGH IMPACT)**
*Current state:* Agent outputs add to growing main context
*With Subagents:* Agent work happens in separate window, only final report returns
*Token savings:* 40-60% for complex agent tasks (isolates intermediate steps)

✅ **Context Preservation (MEDIUM IMPACT)**
*Current state:* Lengthy agent operations can dilute main conversation focus
*With Subagents:* Main conversation stays focused on user intent
*Benefit:* Cleaner context, better coherence in main session

**Productivity Improvements:**
- Parallel subagent execution (multiple isolated tasks simultaneously)
- Cleaner main conversation (less agent "noise")
- Specialized expertise without polluting general context

**Research Workflow Enhancements:**
- Deep physics analysis without cluttering main session
- Complex DataFrame transformations in isolation
- Multi-step test generation without context bloat

### 3. Integration Strategy

**Architecture Fit:**

Subagents complement the existing Task-based agent system:

```
Decision Tree:
├── Simple routine task (< 3 steps, straightforward)
│   └── Use Skill (automatic activation)
├── Moderate complexity (3-5 steps, well-defined)
│   └── Use Task agent (shares context, quick delegation)
└── Complex isolated task (multi-step, exploratory, or context-heavy)
    └── Use Subagent (independent context, deep expertise)

Examples:
- "Validate thermal speed formula" → Skill (physics-validator)
- "Check physics correctness in ion.py" → Task (PhysicsValidator)
- "Refactor entire Plasma class for better memory efficiency, analyze trade-offs" → Subagent (dataframe-architect)
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **7 Task Agents** | Convert 4-5 agents to subagents (keep UnifiedPlanCoordinator as Task) |
| **Skills** | Skills for routine, subagents for complex isolated work |
| **Memory** | Subagents can access project memory via system prompts |
| **Hooks** | Subagent completion can trigger SubagentStop hooks |

**Which Agents to Convert:**

✅ **Good Subagent Candidates:**
- **PhysicsValidator** - Deep analysis, formula derivation (context-heavy)
- **DataFrameArchitect** - Complex refactoring, memory profiling (multi-step)
- **PlottingEngineer** - Iterative plot refinement (exploratory)
- **FitFunctionSpecialist** - Statistical analysis, optimization (isolated work)

⚠️ **Keep as Task Agents:**
- **UnifiedPlanCoordinator** - Needs to execute CLI scripts in main context
- **TestEngineer** - Integrates tightly with main workflow
- **NumericalStabilityGuard** - Quick checks, not worth isolation overhead

**Backward Compatibility:**
✅ **Fully compatible** - Task agents continue working unchanged
✅ **Incremental adoption** - Convert one agent at a time
✅ **Fallback** - Can always use Task agent if subagent unavailable

### 4. Implementation Specification

#### Proposed Subagent Definitions

##### Subagent 1: PhysicsValidator

**File:** `.claude/agents/physics-validator.md`

```yaml
---
name: physics-validator
description: Deep physics analysis specialist for solar wind calculations. Validates thermal speed formulas, unit consistency, physical constraints, and scientific correctness across multiple files.
tools: [Read, Grep, Bash(python .claude/hooks/physics-validation.py*), Bash(pytest*)]
model: sonnet
---

# Physics Validator Subagent

You are a solar wind physics expert specializing in validating scientific correctness in SolarWindPy.

## Core Responsibilities

1. **Formula Validation**
   - Thermal speed: mw² = 2kT (NOT 3kT)
   - Alfvén speed: v_A = B / √(μ₀ρ)
   - Plasma frequency: ωₚ = √(nₑe²/(ε₀mₑ))

2. **Unit Consistency (SI Units MANDATORY)**
   - Velocity: m/s
   - Density: m⁻³
   - Temperature: K
   - Magnetic Field: T

3. **Physical Constraints**
   - All densities, temperatures, speeds > 0
   - NaN for missing data (NEVER 0, -999, or sentinels)
   - Proton mass: 1.6726219 × 10⁻²⁷ kg
   - Boltzmann constant: 1.380649 × 10⁻²³ J/K

4. **Multi-file Analysis**
   - Cross-reference formulas across modules
   - Identify inconsistencies in physics implementations
   - Suggest refactoring for scientific accuracy

## Validation Process

1. Read target files using Read tool
2. Search for physics formulas using Grep
3. Validate against canonical formulas (above)
4. Run physics validation script: `python .claude/hooks/physics-validation.py`
5. Report findings with:
   - ✅ Correct implementations
   - ⚠️ Warnings (potential issues)
   - ❌ Errors (must fix)
   - 💡 Recommendations

## Output Format

Return a structured report:

```markdown
# Physics Validation Report

## Summary
- Files analyzed: N
- Issues found: X errors, Y warnings
- Overall status: PASS/FAIL

## Detailed Findings

### ✅ Correct Implementations
- `file.py:line` - Description

### ❌ Errors (MUST FIX)
- `file.py:line` - Issue description
  - Current: ...
  - Expected: ...
  - Fix: ...

### ⚠️ Warnings
- `file.py:line` - Potential issue

### 💡 Recommendations
- Refactoring suggestion 1
- Optimization suggestion 2
```

## Context Access
@.claude/memory/physics-constants.md
@.claude/memory/dataframe-patterns.md
```

##### Subagent 2: DataFrameArchitect

**File:** `.claude/agents/dataframe-architect.md`

```yaml
---
name: dataframe-architect
description: Pandas MultiIndex optimization specialist. Refactors DataFrame operations for efficiency, manages memory, and ensures proper use of SolarWindPy's (M/C/S) structure.
tools: [Read, Grep, Edit, Write, Bash(pytest*)]
model: sonnet
---

# DataFrame Architect Subagent

You are a pandas expert specializing in optimizing MultiIndex DataFrame operations for SolarWindPy's three-level (M/C/S) structure.

## Core Responsibilities

1. **MultiIndex Structure Optimization**
   - M (Measurement): Physical quantity type
   - C (Component): Spatial components (x, y, z, r, t, n)
   - S (Species): Particle species (p, a, e)

2. **Access Pattern Optimization**
   - Prefer `.xs()` for cross-sections (returns views)
   - Use `.loc` for single access
   - Avoid chained indexing (creates copies)
   - Use `.query()` for complex filters

3. **Memory Management**
   - Profile memory usage before/after optimizations
   - Identify unnecessary copies
   - Recommend dtype optimizations (float64 → float32 where safe)
   - Suggest view vs copy trade-offs

4. **Performance Analysis**
   - Benchmark before/after refactoring
   - Identify bottlenecks in DataFrame operations
   - Recommend vectorization opportunities

## Optimization Process

1. **Analyze Current Code**
   - Read target files
   - Grep for DataFrame operations (`.loc`, `.iloc`, `[]`, etc.)
   - Profile memory usage patterns

2. **Identify Issues**
   - Chained indexing creating copies
   - Inefficient loops vs vectorization opportunities
   - Unnecessary full DataFrame copies

3. **Propose Refactoring**
   - Show before/after code examples
   - Estimate memory savings
   - Benchmark performance improvements

4. **Validate Changes**
   - Run tests to ensure correctness
   - Measure actual memory/performance gains

## Anti-Patterns to Flag

```python
# ❌ BAD: Chained indexing
df_bad = df.loc['Np'].loc['x'].loc['p']

# ❌ BAD: Iterating over rows
for idx, row in df.iterrows():
    result.append(row['value'] * 2)

# ❌ BAD: Unnecessary copy
df_copy = df[df['Np'] > 5].copy()  # If you don't need a copy

# ✅ GOOD: Single operation
df_good = df.xs(('Np', 'x', 'p'), level=('M', 'C', 'S'))

# ✅ GOOD: Vectorization
result = df['value'] * 2

# ✅ GOOD: View when possible
df_view = df.xs('p', level='S')  # Returns view
```

## Output Format

Return a structured refactoring plan:

```markdown
# DataFrame Optimization Report

## Summary
- Files analyzed: N
- Optimization opportunities: X
- Estimated memory savings: Y MB
- Estimated performance improvement: Z%

## Current Issues
1. Issue description
   - Location: `file.py:line`
   - Problem: ...
   - Impact: Memory/Performance

## Proposed Refactoring

### Optimization 1: [Description]
**Current:**
\```python
# Current inefficient code
\```

**Proposed:**
\```python
# Optimized code
\```

**Benefits:**
- Memory savings: X MB
- Performance: Y% faster
- Correctness: Maintained (tested)

### Optimization 2: ...

## Implementation Plan
1. Step 1
2. Step 2
3. Testing & validation
```

## Context Access
@.claude/memory/dataframe-patterns.md
@.claude/memory/testing-templates.md
```

##### Subagent 3: PlottingEngineer

**File:** `.claude/agents/plotting-engineer.md`

```yaml
---
name: plotting-engineer
description: Scientific visualization specialist for publication-quality matplotlib figures. Creates plots for solar wind data with proper labels, units, and styling.
tools: [Read, Write, Edit, Bash(pytest*), Bash(python*)]
model: sonnet
---

# Plotting Engineer Subagent

You are a scientific visualization expert specializing in publication-quality matplotlib figures for solar wind research.

## Core Responsibilities

1. **Publication-Quality Standards**
   - Clear axis labels with SI units
   - Descriptive titles and legends
   - Appropriate color schemes (colorblind-friendly)
   - Vector formats (SVG, PDF) for publications

2. **Solar Wind Visualization Patterns**
   - Time series plots (velocity, density, temperature)
   - Multi-panel figures for species comparison
   - Scatter plots for correlations
   - Histograms for distributions

3. **Matplotlib Best Practices**
   - Use `fig, ax = plt.subplots()` pattern
   - Set figure size for publication: `figsize=(10, 6)`
   - Use context managers for style consistency
   - Include proper metadata in saved figures

## Plotting Process

1. **Understand Data Context**
   - What measurement? (velocity, density, temperature)
   - What species? (protons, alphas, electrons)
   - What components? (x, y, z, r, t, n)

2. **Design Plot Layout**
   - Single panel or multi-panel?
   - What comparison to highlight?
   - Color scheme selection

3. **Create Figure**
   - Generate matplotlib code
   - Include proper labels, units, legends
   - Add annotations if needed

4. **Validation**
   - Check units displayed correctly
   - Verify data range makes physical sense
   - Test different figure sizes

## Standard Plot Templates

### Time Series Plot
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(time, velocity_x, label='V_x', color='C0')
ax.plot(time, velocity_y, label='V_y', color='C1')
ax.plot(time, velocity_z, label='V_z', color='C2')

ax.set_xlabel('Time (s)', fontsize=12)
ax.set_ylabel('Velocity (m/s)', fontsize=12)
ax.set_title('Solar Wind Velocity Components', fontsize=14)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('velocity_timeseries.pdf', dpi=300, bbox_inches='tight')
plt.show()
```

### Multi-Species Comparison
```python
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Protons
axes[0].plot(time, density_protons, label='Protons', color='C0')
axes[0].set_ylabel('Density (m⁻³)', fontsize=12)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Alphas
axes[1].plot(time, density_alphas, label='Alphas', color='C1')
axes[1].set_xlabel('Time (s)', fontsize=12)
axes[1].set_ylabel('Density (m⁻³)', fontsize=12)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.suptitle('Multi-Species Density Comparison', fontsize=14)
plt.tight_layout()
plt.savefig('species_comparison.pdf', dpi=300, bbox_inches='tight')
```

## Output Format

Provide complete plotting code with:
- Import statements
- Data loading/preparation
- Figure creation with proper styling
- Saving instructions (PDF/SVG for publication)
- Usage documentation

## Context Access
@.claude/memory/physics-constants.md (for SI units)
```

##### Subagent 4: FitFunctionSpecialist

**File:** `.claude/agents/fit-function-specialist.md`

```yaml
---
name: fit-function-specialist
description: Statistical analysis and curve fitting expert. Performs optimization, regression analysis, and statistical modeling for solar wind data.
tools: [Read, Write, Edit, Bash(python*), Bash(pytest*)]
model: sonnet
---

# Fit Function Specialist Subagent

You are a statistical analysis expert specializing in curve fitting and optimization for solar wind research.

## Core Responsibilities

1. **Curve Fitting**
   - Linear, polynomial, exponential fits
   - Custom physics-based model fitting
   - Uncertainty quantification
   - Goodness-of-fit metrics (R², χ², residuals)

2. **Optimization**
   - Parameter optimization for physics models
   - Constraint handling (positivity, bounds)
   - Multi-parameter fitting with scipy.optimize

3. **Statistical Analysis**
   - Correlation analysis
   - Distribution fitting
   - Hypothesis testing
   - Confidence intervals

4. **SolarWindPy Integration**
   - Abstract base class patterns for fit functions
   - Proper error propagation
   - Physics-aware constraints

## Fitting Process

1. **Data Preparation**
   - Load and validate data
   - Handle NaN values appropriately
   - Check for outliers

2. **Model Selection**
   - Choose appropriate model (linear, nonlinear, physics-based)
   - Define fit function with proper signature
   - Set parameter bounds if needed

3. **Fitting Execution**
   - Use scipy.optimize.curve_fit or minimize
   - Apply constraints (positive parameters, etc.)
   - Calculate uncertainties

4. **Validation**
   - Compute goodness-of-fit metrics
   - Plot residuals
   - Check physical reasonableness

## Standard Fitting Templates

### Linear Fit with Uncertainties
```python
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def linear_model(x, a, b):
    """Linear model: y = ax + b"""
    return a * x + b

# Fit
params, covariance = curve_fit(linear_model, x_data, y_data)
a_fit, b_fit = params
a_err, b_err = np.sqrt(np.diag(covariance))

# Goodness of fit
y_fit = linear_model(x_data, *params)
residuals = y_data - y_fit
r_squared = 1 - (np.sum(residuals**2) / np.sum((y_data - np.mean(y_data))**2))

print(f"a = {a_fit:.3f} ± {a_err:.3f}")
print(f"b = {b_fit:.3f} ± {b_err:.3f}")
print(f"R² = {r_squared:.3f}")
```

### Physics-Based Model Fitting
```python
def thermal_speed_model(T, mass):
    """Thermal speed: w = √(2kT/m)"""
    k_B = 1.380649e-23  # J/K
    return np.sqrt(2 * k_B * T / mass)

# Fit thermal speed data to extract mass
def fit_func(T, mass):
    return thermal_speed_model(T, mass)

mass_fit, mass_cov = curve_fit(
    fit_func,
    temperatures,
    measured_speeds,
    bounds=(0, np.inf)  # Mass must be positive
)

mass_err = np.sqrt(mass_cov[0, 0])
print(f"Fitted mass: {mass_fit[0]:.3e} ± {mass_err:.3e} kg")

# Compare to known proton mass
proton_mass = 1.6726219e-27  # kg
print(f"Difference from proton mass: {abs(mass_fit[0] - proton_mass) / proton_mass * 100:.1f}%")
```

## Output Format

Provide complete analysis including:
- Model definition
- Fitting code
- Parameter results with uncertainties
- Goodness-of-fit metrics
- Visualization (data + fit + residuals)
- Physical interpretation

## Context Access
@.claude/memory/physics-constants.md
@.claude/memory/testing-templates.md
```

#### Invoking Subagents

**Automatic Invocation** (Claude decides based on description):
```
User: "I need a comprehensive analysis of thermal speed calculations across all ion classes, checking for formula consistency and proposing refactoring if needed."

Claude: [Automatically invokes physics-validator subagent due to "comprehensive analysis" + "thermal speed" + "formula consistency"]
```

**Explicit Invocation:**
```
User: "Use the physics-validator subagent to analyze ion.py for thermal speed correctness."

Claude: [Explicitly invokes physics-validator subagent]
```

#### Migration Path

**Phase 1: Create Subagent Definitions (Week 1)**
1. Create `.claude/agents/` directory
2. Define 4 subagents (physics-validator, dataframe-architect, plotting-engineer, fit-function-specialist)
3. Test invocation with simple tasks
4. Verify independent context windows

**Phase 2: Parallel Operation (Weeks 2-3)**
1. Run subagents alongside existing Task agents
2. Compare results and context pollution
3. Gather metrics on token usage (subagent vs Task)
4. Document which scenarios benefit from subagents

**Phase 3: Gradual Migration (Weeks 4-5)**
1. Update documentation to recommend subagents for complex isolated tasks
2. Keep Task agents for simpler delegation
3. Train on appropriate selection (Skill → Task → Subagent continuum)

**Phase 4: Optimization (Week 6+)**
1. Refine subagent system prompts based on usage
2. Add more specialized subagents if needed
3. Measure impact on token usage and productivity

**Rollback Strategy:**
Subagents are additive. Can always fall back to Task agents by simply not creating subagent files.

### 5. Priority & Effort Estimation

**Impact Level:** 🟡 **MEDIUM-HIGH**

| Metric | Score | Justification |
|--------|-------|---------------|
| Agent coordination | 4/5 | Reduces context pollution from complex agent tasks |
| Token optimization | 5/5 | 40-60% savings for complex isolated work |
| Context preservation | 4/5 | Main conversation stays focused |
| Repetitive automation | 2/5 | Skills better for repetition; subagents for complexity |
| Plan efficiency | 3/5 | Can parallelize independent subagent tasks |

**Implementation Complexity:** 🟡 **3/5 (Medium)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| File creation | 2/5 | Markdown files with YAML frontmatter + system prompts |
| System prompt writing | 4/5 | Requires thoughtful expertise encoding |
| Testing | 3/5 | Validate isolation, tool access, context independence |
| Integration | 3/5 | Coexist with Task agents, document selection criteria |
| Maintenance | 3/5 | Refine prompts based on usage patterns |

**Dependencies:**
- ✅ None - Subagents are core feature
- ⚠️ Requires well-designed system prompts for effectiveness
- ⚠️ Need clear guidelines for when to use subagent vs Task vs Skill

**Estimated Effort:**
- Subagent definition creation: **6-8 hours** (4 subagents × 1.5-2 hours each)
- System prompt refinement: **3-4 hours**
- Testing & validation: **2-3 hours**
- Documentation (selection criteria): **1-2 hours**
- **Total: 12-17 hours**

**Break-even Analysis:**
- Time saved per week: ~1-2 hours (cleaner context, less token management)
- Token cost savings: ~30-40% for complex tasks (10-20% overall)
- Break-even: **6-9 weeks**
- Annual ROI: **50-100 hours** of productive development time

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Context Isolation
```
Scenario: Invoke physics-validator subagent for complex multi-file analysis
Expected: Subagent context separate from main conversation
Validation: Main conversation doesn't include intermediate physics analysis steps
```

#### Test 2: Tool Access Restrictions
```
Scenario: physics-validator subagent attempts to use Edit tool (not in allowed-tools)
Expected: Tool access denied or restricted
Validation: Only Read, Grep, Bash(physics-validation) available
```

#### Test 3: Independent Execution
```
Scenario: Invoke dataframe-architect while physics-validator still running
Expected: Both execute independently in parallel
Validation: No interference between subagent contexts
```

#### Test 4: Return Value Integration
```
Scenario: Subagent completes complex analysis
Expected: Final report returned to main conversation, intermediate steps discarded
Validation: Main context contains only summary, not full subagent conversation
```

#### Test 5: Token Savings Measurement
```
Scenario: Complex physics refactoring (50+ file analysis)
Comparison: Task agent vs Subagent token usage
Expected: Subagent uses 40-60% fewer tokens in main conversation
Validation: Measure before/after context sizes
```

**Success Criteria:**
- ✅ Subagent context remains isolated (no pollution in main conversation)
- ✅ Tool restrictions enforced correctly
- ✅ Parallel subagent execution works
- ✅ Token savings of 40-60% for complex isolated tasks
- ✅ Quality of subagent output equals or exceeds Task agents

**Monitoring:**
```bash
# Track subagent invocations (if SubagentStop hook added)
grep '\[SUBAGENT COMPLETED\]' .claude/logs/subagent-activity.log

# Compare token usage
# Analyze session transcripts for token consumption patterns
```

---

## Feature 4: Enhanced Hooks System

### 1. Feature Overview

**What It Is:**
Claude Code's hook system provides 9 event lifecycle triggers for executing shell commands at designated points. The enhanced system includes newer events (Notification, SubagentStop, SessionEnd) beyond what SolarWindPy currently uses.

**Core Capabilities:**
- **9 Event Types:** PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, SubagentStop, PreCompact, SessionStart, SessionEnd
- **Conditional execution** - JavaScript-like conditions (e.g., `${command.startsWith('git ')}`)
- **Tool matchers** - Target specific tools (Bash, Edit, Write) or all (*)
- **Timeout control** - Per-hook timeout limits (5-120 seconds)
- **Blocking capability** - Hooks can prevent tool execution (PreToolUse)

**Current SolarWindPy Usage:**
✅ Using: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop
❌ Not using: Notification, SubagentStop, SessionEnd

**Maturity & Prerequisites:**
- ✅ Production-ready core feature
- ✅ Currently implemented in `.claude/settings.json`
- ✅ 6/9 events already in use
- 🆕 3 new events available for adoption

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Repetitive Task Automation (MEDIUM IMPACT)**
*Current state:* Manual monitoring of skill/subagent activity
*With Enhanced Hooks:* Automatic logging via Notification and SubagentStop hooks
*Improvement:* 100% automated tracking, zero manual logging overhead

✅ **Context Preservation (LOW-MEDIUM IMPACT)**
*Current state:* Session end cleanup is ad-hoc
*With Enhanced Hooks:* SessionEnd hook for final state preservation
*Improvement:* Consistent session archival, better cross-session continuity

✅ **Token Usage Optimization (LOW IMPACT)**
*Current state:* PreCompact hook handles token boundary compression
*With Enhanced Hooks:* Additional metrics and monitoring
*Improvement:* Better visibility into compaction effectiveness

**Productivity Improvements:**
- Automated activity logging (skills, subagents, notifications)
- Session lifecycle management (SessionEnd cleanup)
- Real-time monitoring without manual intervention

**Research Workflow Enhancements:**
- Audit trail for all skill/subagent activations
- Session summaries for research notebooks
- Automated metrics collection

### 3. Integration Strategy

**Architecture Fit:**

Enhanced hooks build on existing SolarWindPy hook infrastructure:

```
Current Hooks (6/9):
✅ SessionStart → validate-session-state.sh
✅ UserPromptSubmit → git-workflow-validator.sh
✅ PreToolUse → physics-validation.py, git-workflow-validator.sh
✅ PostToolUse → test-runner.sh --changed
✅ PreCompact → create-compaction.py
✅ Stop → coverage-monitor.py

New Hooks (3/9):
🆕 Notification → activity-logger.sh (NEW)
🆕 SubagentStop → subagent-report.sh (NEW)
🆕 SessionEnd → session-archival.sh (NEW)
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **Skills** | Notification hook logs skill activations |
| **Subagents** | SubagentStop hook captures completion reports |
| **Memory** | SessionEnd hook updates session history |
| **Coverage Monitoring** | SessionEnd hook creates final coverage snapshot |
| **Plan System** | Notification hook tracks plan-related events |

**Backward Compatibility:**
✅ **Fully compatible** - New hooks are additive
✅ **Optional adoption** - Existing 6 hooks continue unchanged
✅ **No breaking changes**

### 4. Implementation Specification

#### Enhanced Hook Configuration

**Updated `.claude/settings.json`** (additions only):

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*skill*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/activity-logger.sh skill",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "*plan*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/activity-logger.sh plan",
            "timeout": 5
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/subagent-report.sh",
            "args": ["${subagent_name}", "${duration}"],
            "timeout": 10
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/session-archival.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

#### New Hook Scripts

##### Hook Script 1: Activity Logger

**File:** `.claude/hooks/activity-logger.sh`

```bash
#!/usr/bin/env bash
# Activity Logger Hook
# Logs skill activations, plan events, and notifications

set -euo pipefail

ACTIVITY_TYPE="${1:-unknown}"
LOG_DIR=".claude/logs"
LOG_FILE="${LOG_DIR}/activity.log"

# Create log directory if needed
mkdir -p "${LOG_DIR}"

# Timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log entry
case "${ACTIVITY_TYPE}" in
    skill)
        echo "[${TIMESTAMP}] [SKILL ACTIVATED] Context: ${2:-unknown}" >> "${LOG_FILE}"
        ;;
    plan)
        echo "[${TIMESTAMP}] [PLAN EVENT] Context: ${2:-unknown}" >> "${LOG_FILE}"
        ;;
    *)
        echo "[${TIMESTAMP}] [NOTIFICATION] ${ACTIVITY_TYPE}" >> "${LOG_FILE}"
        ;;
esac

# Optional: Keep only last 1000 lines
tail -n 1000 "${LOG_FILE}" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "${LOG_FILE}"

exit 0
```

**Purpose:** Track skill activations, plan-related events, and general notifications for activity monitoring.

##### Hook Script 2: Subagent Report

**File:** `.claude/hooks/subagent-report.sh`

```bash
#!/usr/bin/env bash
# Subagent Report Hook
# Logs subagent completions with timing and context

set -euo pipefail

SUBAGENT_NAME="${1:-unknown}"
DURATION="${2:-0}"
LOG_DIR=".claude/logs"
LOG_FILE="${LOG_DIR}/subagent-activity.log"

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log subagent completion
echo "[${TIMESTAMP}] [SUBAGENT COMPLETED] Name: ${SUBAGENT_NAME} | Duration: ${DURATION}s" >> "${LOG_FILE}"

# Optional: Generate metrics
TOTAL_INVOCATIONS=$(grep -c "\[SUBAGENT COMPLETED\]" "${LOG_FILE}" 2>/dev/null || echo "0")
AVG_DURATION=$(grep "\[SUBAGENT COMPLETED\]" "${LOG_FILE}" | \
    grep -oP 'Duration: \K[0-9]+' | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

# Update metrics file
cat > "${LOG_DIR}/subagent-metrics.txt" <<EOF
Total Subagent Invocations: ${TOTAL_INVOCATIONS}
Average Duration: ${AVG_DURATION}s
Last Update: ${TIMESTAMP}
EOF

exit 0
```

**Purpose:** Track subagent usage patterns, measure execution time, maintain metrics.

##### Hook Script 3: Session Archival

**File:** `.claude/hooks/session-archival.sh`

```bash
#!/usr/bin/env bash
# Session Archival Hook
# Creates session summary and archives state at session end

set -euo pipefail

ARCHIVE_DIR=".claude/logs/sessions"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
SESSION_FILE="${ARCHIVE_DIR}/session-${TIMESTAMP}.md"

mkdir -p "${ARCHIVE_DIR}"

# Gather session summary
cat > "${SESSION_FILE}" <<EOF
# Session Summary

**Date:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Branch:** $(git branch --show-current 2>/dev/null || echo "unknown")

## Changes
\`\`\`
$(git status --short 2>/dev/null || echo "No git repository")
\`\`\`

## Test Coverage
EOF

# Append coverage if available
if [ -f "coverage.json" ]; then
    COVERAGE=$(python -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])" 2>/dev/null || echo "N/A")
    echo "**Coverage:** ${COVERAGE}%" >> "${SESSION_FILE}"
fi

# Append activity summary if logs exist
if [ -f ".claude/logs/activity.log" ]; then
    echo -e "\n## Activity Summary" >> "${SESSION_FILE}"
    echo "\`\`\`" >> "${SESSION_FILE}"
    tail -n 20 ".claude/logs/activity.log" >> "${SESSION_FILE}"
    echo "\`\`\`" >> "${SESSION_FILE}"
fi

# Cleanup old sessions (keep last 30)
ls -t "${ARCHIVE_DIR}"/session-*.md 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "✅ Session archived: ${SESSION_FILE}"

exit 0
```

**Purpose:** Create comprehensive session summaries for research notebooks and cross-session continuity.

#### Migration Path

**Phase 1: Add New Hooks (Week 1)**
1. Create 3 new hook scripts (activity-logger, subagent-report, session-archival)
2. Make scripts executable: `chmod +x .claude/hooks/*.sh`
3. Add hook configurations to `.claude/settings.json`
4. Test individual hooks with simple scenarios

**Phase 2: Validate Integration (Week 2)**
1. Monitor activity logs for skill activations
2. Check subagent metrics after several invocations
3. Review session archival quality
4. Adjust log retention and format as needed

**Phase 3: Optimization (Week 3+)**
1. Refine log formats based on usage
2. Add custom metrics (e.g., token usage per skill)
3. Create analytics dashboard from log data
4. Document hook system enhancements

**Rollback Strategy:**
Simply remove new hook configurations from `.claude/settings.json`. Existing 6 hooks continue unchanged.

### 5. Priority & Effort Estimation

**Impact Level:** 🟢 **LOW-MEDIUM**

| Metric | Score | Justification |
|--------|-------|---------------|
| Repetitive automation | 4/5 | 100% automated logging |
| Context preservation | 3/5 | Better session continuity |
| Agent coordination | 2/5 | Indirect benefit (activity tracking) |
| Token optimization | 2/5 | Metrics visibility only |
| Plan efficiency | 2/5 | Plan event tracking |

**Implementation Complexity:** 🟢 **2/5 (Low)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Hook script creation | 2/5 | Simple bash scripts |
| Settings.json updates | 1/5 | JSON configuration additions |
| Testing | 2/5 | Verify hooks trigger correctly |
| Documentation | 1/5 | Update HOOKS.md with new events |
| Maintenance | 2/5 | Log file management, retention |

**Dependencies:**
- ✅ None - Hooks are core feature
- ✅ No external tools required
- ✅ Bash scripts only (portable)

**Estimated Effort:**
- Hook script creation: **2-3 hours** (3 scripts × 40-60 min)
- Settings configuration: **30 minutes**
- Testing & validation: **1-2 hours**
- Documentation update: **30 minutes**
- **Total: 4-6 hours**

**Break-even Analysis:**
- Time saved per week: ~30-60 minutes (automated logging vs manual tracking)
- Break-even: **4-6 weeks**
- Annual ROI: **25-50 hours** of time otherwise spent on manual activity tracking

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Notification Hook Activation
```
Scenario: Skill activation (e.g., physics-validator)
Expected: activity-logger.sh logs "[SKILL ACTIVATED]"
Validation: Check .claude/logs/activity.log for entry
```

#### Test 2: SubagentStop Hook
```
Scenario: Complete subagent task (physics-validator subagent)
Expected: subagent-report.sh logs completion with duration
Validation: Check .claude/logs/subagent-activity.log and metrics file
```

#### Test 3: SessionEnd Hook
```
Scenario: End Claude Code session
Expected: session-archival.sh creates session summary
Validation: Check .claude/logs/sessions/ for new summary file
```

#### Test 4: Log Retention
```
Scenario: Generate 35+ sessions
Expected: Only last 30 session files retained
Validation: Verify old session files automatically deleted
```

#### Test 5: Hook Timeout
```
Scenario: Hook takes longer than timeout
Expected: Hook terminates gracefully, main workflow continues
Validation: Session doesn't hang on slow hooks
```

**Success Criteria:**
- ✅ All 3 new hooks trigger correctly at designated events
- ✅ Log files created and populated with expected format
- ✅ Log retention policies enforce (1000 lines for activity, 30 files for sessions)
- ✅ Hooks complete within timeout limits
- ✅ No degradation in main workflow performance

**Monitoring:**
```bash
# View recent activity
tail -f .claude/logs/activity.log

# Check subagent metrics
cat .claude/logs/subagent-metrics.txt

# Review last session
ls -t .claude/logs/sessions/ | head -1 | xargs cat
```

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
- Optional checkpoint-validator hook: **1 hour**
- Testing & validation: **30 minutes**
- **Total: 2-3.5 hours**

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

## Summary: Feature Integration Priorities

### Recommended Adoption Order

| Priority | Feature | Effort | Impact | Timeline |
|----------|---------|--------|--------|----------|
| 🥇 **1** | **Memory Hierarchy** | 9-14h | CRITICAL | Weeks 1-3 |
| 🥈 **2** | **Skills System** | 7-11h | HIGH | Weeks 2-4 |
| 🥉 **3** | **Subagents** | 12-17h | MEDIUM-HIGH | Weeks 4-7 |
| **4** | **Enhanced Hooks** | 4-6h | LOW-MEDIUM | Week 5-6 |
| **5** | **Checkpointing** | 2-3.5h | LOW-MEDIUM | Week 6 |
| **6** | **Output Styles** | 2.5-3.5h | LOW | Week 7 |

**Total Estimated Effort:** 37-55 hours (5-7 weeks if working ~8 hours/week on integration)

### Cumulative Impact Analysis

**Token Optimization (Primary Goal):**
- Memory Hierarchy: 30-50% reduction per session
- Skills System: 20-30% reduction in agent-related tokens
- Subagents: 40-60% savings for complex isolated tasks
- **Combined: 50-70% overall token reduction** (varies by task type)

**Workflow Efficiency Gains:**
- Memory: 50-150 min/week (context preservation)
- Skills: 120-180 min/week (automation)
- Subagents: 60-120 min/week (cleaner context)
- Enhanced Hooks: 30-60 min/week (automated logging)
- Checkpointing: 20-40 min/week (experiment management)
- Output Styles: 10-20 min/week (better suggestions)
- **Total: 290-570 min/week (4.8-9.5 hours/week)**

**Annual ROI:**
- Implementation cost: 37-55 hours upfront
- Weekly savings: 4.8-9.5 hours
- **Break-even: 4-8 weeks**
- **Annual benefit: 250-490 hours** of productive development time

### Phased Rollout Plan

**Phase 1: Foundation (Weeks 1-3)**
- ✅ Memory Hierarchy (highest impact, enables others)
- ✅ Skills System (high automation value)
- ✅ Enhanced Hooks (supports activity tracking)

**Phase 2: Advanced Coordination (Weeks 4-7)**
- ✅ Subagents (complex task isolation)
- ✅ Checkpointing (experiment safety net)
- ✅ Output Styles (domain customization)

**Phase 3: Optimization (Weeks 8+)**
- Refine based on usage metrics
- Add advanced skills/subagents
- Expand memory library
- Iterate on custom output style

### Success Metrics

**Quantitative:**
- [ ] Token usage reduction ≥50% measured over 2-week period
- [ ] Time savings ≥4 hours/week measured via activity logs
- [ ] Skill activation accuracy ≥85% for clear triggers
- [ ] Test coverage maintained ≥95%
- [ ] Zero workflow regressions

**Qualitative:**
- [ ] Reduced cognitive overhead (less manual agent selection)
- [ ] Improved context continuity across sessions
- [ ] Enhanced scientific correctness emphasis
- [ ] Smoother research workflow integration

---

## Appendix A: Quick Reference Commands

### Skills
```bash
# Skills auto-activate, no commands needed
# Location: .claude/skills/<skill-name>/SKILL.md
```

### Memory
```bash
# Add memory entry quickly
claude
> #[Enter text, select destination]

# Edit memory files
claude
> /memory

# Initialize project memory
claude
> /init
```

### Subagents
```bash
# Subagents invoke automatically or explicitly
# Location: .claude/agents/<agent-name>.md
```

### Hooks
```bash
# Hook configuration in .claude/settings.json
# View activity logs
tail -f .claude/logs/activity.log

# View subagent metrics
cat .claude/logs/subagent-metrics.txt
```

### Checkpointing
```bash
# Automatic - no commands needed
# Use Claude Code UI to revert to checkpoints
```

### Output Styles
```bash
# List available styles
claude
> /output-style

# Switch style
claude
> /output-style physics-focused

# Create new style
claude
> /output-style:new <description>
```

---

## Appendix B: Integration Checklist

**Pre-Integration:**
- [ ] Review current CLAUDE.md and `.claude/` structure
- [ ] Backup current configuration
- [ ] Ensure git repository clean state
- [ ] Review current pain points and prioritize features

**Phase 1: Memory Hierarchy (Weeks 1-3):**
- [ ] Create `.claude/memory/` directory structure
- [ ] Extract CLAUDE.md sections into dedicated memory files
- [ ] Update CLAUDE.md with imports (`@.claude/memory/...`)
- [ ] Test import resolution and context loading
- [ ] Measure token usage before/after
- [ ] Document memory structure in `.claude/docs/MEMORY.md`

**Phase 2: Skills System (Weeks 2-4):**
- [ ] Create `.claude/skills/` directory
- [ ] Implement 4 core skills (physics-validator, multiindex-architect, test-generator, plan-executor)
- [ ] Test skill activation with clear trigger phrases
- [ ] Monitor activation accuracy (target ≥85%)
- [ ] Refine skill descriptions based on usage
- [ ] Update CLAUDE.md with skill usage patterns

**Phase 3: Subagents (Weeks 4-7):**
- [ ] Create `.claude/agents/` directory
- [ ] Implement 4 subagents (physics-validator, dataframe-architect, plotting-engineer, fit-function-specialist)
- [ ] Test context isolation and tool restrictions
- [ ] Compare token usage (subagent vs Task agent)
- [ ] Document subagent vs Task vs Skill selection criteria
- [ ] Update `.claude/docs/AGENTS.md`

**Phase 4: Enhanced Hooks (Weeks 5-6):**
- [ ] Create 3 new hook scripts (activity-logger, subagent-report, session-archival)
- [ ] Add Notification, SubagentStop, SessionEnd hooks to settings.json
- [ ] Test hook triggering and log generation
- [ ] Verify log retention policies
- [ ] Update `.claude/docs/HOOKS.md`

**Phase 5: Checkpointing (Week 6):**
- [ ] Document checkpointing usage in `.claude/docs/DEVELOPMENT.md`
- [ ] Create checkpoint-validator hook (optional)
- [ ] Test checkpoint creation and reversion
- [ ] Verify limitations (bash commands, manual edits)

**Phase 6: Output Styles (Week 7):**
- [ ] Create `.claude/output-styles/physics-focused.md`
- [ ] Test style switching and response patterns
- [ ] Compare to Explanatory style
- [ ] Refine based on usage
- [ ] Document in `.claude/docs/`

**Post-Integration:**
- [ ] Measure cumulative token savings
- [ ] Track weekly time savings
- [ ] Gather subjective quality feedback
- [ ] Iterate on skill descriptions, memory organization
- [ ] Create advanced skills/subagents as needed
- [ ] Document lessons learned

---

**End of Document**

*Last Updated: 2025-10-23*
*Version: 1.0*
*Status: Planning & Design Phase*
