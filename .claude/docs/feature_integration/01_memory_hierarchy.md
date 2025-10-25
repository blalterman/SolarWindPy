# Memory Hierarchy

**Feature Type:** Automatic
**Priority:** CRITICAL
**Effort:** 9-14 hours
**ROI Break-even:** 4-6 weeks

[← Back to Index](./INDEX.md) | [Next: Skills System →](./02_skills_system.md)

---
## Feature 2: Memory Hierarchy

### 1. Feature Overview

**What It Is:**
A project-level persistent context management system that retains project guidelines, conventions, and knowledge across sessions. Memory eliminates the need to repeat common instructions.

**Core Capabilities:**
- **Project-only memory** - Single-tier architecture for consistency:
  - **Project** (`./CLAUDE.md` or `./.claude/CLAUDE.md`) - Team-shared, git-committed
- **File imports** - Modular composition via `@path/to/file` syntax (5-level depth)
- **Automatic discovery** - Recursive upward traversal from working directory
- **Markdown-based** - Simple text files, git-friendly

**Why Project Memory Only:**
SolarWindPy uses **only** project-level memory to ensure:
- **Consistency**: All team members work with identical configuration
- **Version Control**: Memory evolves with codebase, tracked in git
- **No Fragmentation**: No personal overrides creating inconsistent behavior across developers
- **Simplicity**: Single source of truth for all SolarWindPy conventions

**Maturity & Prerequisites:**
- ✅ Production-ready, core Claude Code feature
- ✅ No external dependencies
- ✅ Works with existing CLAUDE.md files
- ✅ Supports incremental adoption

**Technical Constraints:**
- Import depth limited to 5 levels
- Imports not evaluated inside code spans/blocks
- Project memory is the only tier (no user/local/enterprise overrides)
- Files discovered via recursive directory traversal from working directory

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

#### Project Memory Contents

**What Goes in Project Memory:**
All SolarWindPy-specific conventions, rules, and knowledge that should be consistent across all team members:

- **Physics constants and formulas** (thermal speed, Alfvén speed, etc.)
- **MultiIndex structure** (M/C/S levels, capitalization rules)
- **Testing requirements** (≥95% coverage, physics validation patterns)
- **DataFrame patterns** (efficient access with .xs(), avoiding SettingWithCopyWarning)
- **Git workflows** (branch naming, commit conventions, hook system)
- **Agent and skill usage** (when to use specialized agents)
- **Hook configurations** (validation scripts, test runners)

**What Does NOT Go in Project Memory:**
- Personal preferences that vary by developer (editor settings, alias commands)
- Experimental features not yet adopted by team
- User-specific shortcuts or workflow customizations

**Note:** SolarWindPy does NOT use `~/.claude/CLAUDE.md` (user-level) or `./CLAUDE.local.md` (local overrides). All configuration is project-level and version-controlled.

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
2. Document memory structure in `.claude/docs/MEMORY.md`
3. Measure token reduction and context quality
4. Update team documentation with memory file locations

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

#### Test 4: Backward Compatibility
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

