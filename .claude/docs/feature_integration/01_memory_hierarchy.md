# Memory Hierarchy

**Feature Type:** Automatic
**Priority:** CRITICAL
**Effort:** 19-28 hours
**ROI Break-even:** 4-6 weeks

[← Back to Index](./INDEX.md) | [Next: Skills System →](./02_skills_system.md)

---

**❌ NOT A PLUGIN FEATURE - Core Infrastructure**

Memory hierarchy is project-specific infrastructure (not distributable). Plugins reference memory via `@.claude/memory/...` syntax.
See: [Plugin Packaging](./08_plugin_packaging.md#61-memory-integration)

---

## Feature 1: Memory Hierarchy

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

### 1.1 AI Engineering Rationale

**Anthropic Best Practice:** "Keep only what's relevant in context. Don't pollute context with redundant information."

Memory hierarchy directly implements this principle for SolarWindPy by:

1. **Context Efficiency:** Persistent memory eliminates repeated instructions like "Always use SI units" or "DataFrame uses M/C/S MultiIndex". These consume 5,000-10,000 tokens per session when manually provided.

2. **Selective Loading:** Modular files (e.g., `physics-constants.md`, `dataframe-patterns.md`) allow importing only relevant context. Testing session imports test memory; physics work imports physics memory.

3. **Reduction via Offloading:** Anthropic's advanced tool use guide recommends "external memory for information that doesn't change." Project conventions (code style, testing requirements, architecture patterns) are static and ideal for memory files.

4. **Token Budget Preservation:** With 200K token context window, memory allocation should be ≤10% (20K tokens). SolarWindPy's 9 memory files (~15K tokens total) preserve 185K tokens for actual work.

5. **Consistency Without Repetition:** Every physics calculation needs "verify SI units" reminder. Memory provides this once via import, not repeated manual prompts.

**Impact Measurement:** Memory implementation should achieve ≥30% token reduction in first 2 weeks (measured via session token logs). This validates memory content relevance before investing in downstream features (Skills, Subagents) that depend on memory.

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

### 3.5. Risk Assessment

#### Technical Risks

**Risk: Import Path Resolution Failures**
- **Likelihood:** Low-Medium
- **Impact:** High (context fails to load)
- **Mitigation:**
  - Test all import paths during Phase 1
  - Use relative paths from project root for portability
  - Keep inline fallback content in main CLAUDE.md
  - Monitor Claude Code error logs during migration

**Risk: Import Depth Limit Exceeded**
- **Likelihood:** Low (5-level limit is generous)
- **Impact:** Medium (nested imports fail silently)
- **Mitigation:**
  - Design flat structure (max 2 levels)
  - Avoid cross-referencing between memory files
  - Document import hierarchy explicitly

**Risk: Circular Import Dependencies**
- **Likelihood:** Low
- **Impact:** Medium (import resolution fails)
- **Mitigation:**
  - Design acyclic memory graph
  - Use testing-templates.md as leaf node (no imports)
  - Document dependency order

**Risk: Token Budget Overflow**
- **Likelihood:** Low-Medium
- **Impact:** Medium (selective loading ineffective)
- **Mitigation:**
  - Keep individual memory files under 500 tokens
  - Monitor actual token usage post-migration
  - Split large files if needed (e.g., physics-constants.md → thermal-formulas.md + alfven-formulas.md)

#### Adoption Risks

**Risk: Team Confusion About Memory Structure**
- **Likelihood:** Medium
- **Impact:** Low-Medium (slower adoption)
- **Mitigation:**
  - Create comprehensive `.claude/docs/MEMORY.md` guide
  - Document memory file purposes in each file header
  - Provide examples of when to update which memory file
  - Team training session during Phase 1

**Risk: Memory File Drift from Codebase**
- **Likelihood:** Medium
- **Impact:** Medium (outdated context harms quality)
- **Mitigation:**
  - Add pre-commit hook to validate memory consistency
  - Include memory updates in PR review checklist
  - Schedule quarterly memory audits
  - Link memory files to corresponding source code in comments

**Risk: Fragmented Context Across Too Many Files**
- **Likelihood:** Low
- **Impact:** Medium (harder to maintain coherent context)
- **Mitigation:**
  - Limit to 9 core memory files initially
  - Group related concepts (don't create file-per-concept)
  - Use clear naming conventions (`*-reference.md`, `*-patterns.md`, `*-templates.md`)

#### Migration Risks

**Risk: Context Regression During Migration**
- **Likelihood:** Medium
- **Impact:** High (temporary productivity loss)
- **Mitigation:**
  - Maintain full inline content during transition
  - Migrate incrementally (2-3 sections at a time)
  - A/B test context quality before/after each phase
  - Keep rollback window open for 2 weeks per phase

**Risk: Lost Context Due to Over-Modularization**
- **Likelihood:** Low-Medium
- **Impact:** Medium (critical rules missed)
- **Mitigation:**
  - Keep critical rules in both CLAUDE.md and critical-rules.md initially
  - Monitor for missed context in session reviews
  - Consolidate if fragmentation causes issues

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
# Solar Wind Physics: Units Architecture

## Units System

### Storage Units (Instrument Measurements)
SolarWindPy stores only directly measured quantities:
- **n:** Number density [cm⁻³]
- **v:** Velocity [km/s]
- **w:** Thermal speed [km/s]

### Display Units (All Quantities)
All quantities displayed in units defined by `solarwindpy.core.units_constants.Units`:
- Density: cm⁻³ (`self.units.n = 1e6`)
- Velocity/speeds: km/s (`self.units.v = 1e3`)
- Temperature: 10⁵ K (`self.units.temperature = 1e5`)
- Magnetic field: nT (`self.units.bfield = 1e-9`)
- Thermal pressure: pPa (`self.units.pth = 1e-12`)
- See `Units` class for complete list

### Calculation Units (SI)
All physics calculations performed in SI units via conversion factors.

## Units Conversion Pattern (Display → SI → Display)

**CRITICAL:** All calculations must convert units bidirectionally.

```python
# Example from ions.py temperature property (line 222-224)
def temperature(self):
    # Input conversion: display → SI
    w = self.w.data * self.units.w              # km/s → m/s

    # Calculate in SI
    coeff = 0.5 * m / (self.constants.kb.J * self.units.temperature)
    temp = coeff * w.pow(2)

    # Output: Result automatically in display units (10⁵ K) via coeff
    return temp
```

**Pattern to validate:**
1. Input: `quantity * self.units.<name>` (display → SI)
2. Calculate: Perform physics calculation in SI
3. Output: `result / self.units.<name>` (SI → display)

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

- ✅ Density > 0 (n > 0 in cm⁻³)
- ✅ Temperature > 0 (T > 0 in 10⁵ K)
- ✅ Thermal speed ≥ 0 (w ≥ 0 in km/s, always positive scalar)
- ✅ Vector magnitudes ≥ 0 (e.g., |v|, |B|), though components may be negative
- ✅ Physical constants from `solarwindpy.core.units_constants.Constants`
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

    def test_function_units_conversion(self):
        """Validate units conversion pattern (REQUIRED for calculation methods)."""
        # Check that calculations use units conversion
        import inspect
        source = inspect.getsource(ion.temperature.fget)

        # Should contain self.units.w for input conversion (display → SI)
        assert 'self.units.w' in source, "Missing units conversion in calculation"

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

- **Units architecture** (storage vs display units, conversion patterns)
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

*Immediate Rollback (Same Session):*
1. Remove `@.claude/memory/...` imports from CLAUDE.md
2. Inline content back into main CLAUDE.md
3. Verify context loads correctly
4. Continue working (no restart needed)

*Full Rollback (If Issues Persist):*
1. `git revert` commits that introduced memory hierarchy
2. Restore monolithic CLAUDE.md from git history
3. Delete `.claude/memory/` directory (or move to `.claude/memory.backup/`)
4. Verify all workflows function as before
5. Document issues encountered for future reference

*Partial Rollback (Keep Some Memory Files):*
1. Identify problematic memory file(s)
2. Remove specific imports from CLAUDE.md
3. Inline only problematic content
4. Keep working memory files intact
5. Iterate based on what works

*Rollback Verification Steps:*
- ✅ CLAUDE.md loads without errors
- ✅ Physics rules are enforced in session
- ✅ Agent selection works correctly
- ✅ Testing patterns are available
- ✅ No regressions in context quality

*Risk:** Very low - Memory hierarchy is additive, rollback is simple removal/inlining.

### 4.5. Alternatives Considered

#### Alternative 1: Keep Monolithic CLAUDE.md (Status Quo)

**Description:** Continue using single CLAUDE.md file with all context inline.

**Pros:**
- ✅ Zero implementation effort
- ✅ No risk of import resolution failures
- ✅ Simpler mental model (everything in one place)
- ✅ No migration complexity

**Cons:**
- ❌ Full context loaded every session (token inefficiency)
- ❌ Difficult to navigate and maintain (300+ lines)
- ❌ No selective loading based on task context
- ❌ Harder for team to coordinate updates (merge conflicts)
- ❌ Agent-specific context not easily targeted

**Decision:** **Rejected** - Token efficiency and maintainability gains justify migration effort.

#### Alternative 2: User + Project Memory Hierarchy

**Description:** Use both `~/.claude/CLAUDE.md` (user-level) and project-level memory for personalization.

**Pros:**
- ✅ Developers can customize personal workflows
- ✅ Separation of team standards vs. personal preferences
- ✅ Flexibility for different working styles

**Cons:**
- ❌ Inconsistent behavior across team members
- ❌ Debugging difficulty (which memory tier caused behavior?)
- ❌ Fragmentation of context (some in user, some in project)
- ❌ Personal preferences can override critical project rules
- ❌ Harder to reproduce issues across environments

**Decision:** **Rejected** - Team consistency is critical for SolarWindPy. Single source of truth preferred.

#### Alternative 3: External Documentation Links (No Memory System)

**Description:** Store context in `.claude/docs/` and rely on manual references via `@file` syntax.

**Pros:**
- ✅ Clear separation of permanent docs vs. ephemeral memory
- ✅ Documentation serves dual purpose (humans + AI)
- ✅ No special memory infrastructure needed

**Cons:**
- ❌ Requires manual `@file` references in every relevant session
- ❌ Not automatically loaded (Claude must be told to read)
- ❌ Context not preserved across sessions (ephemeral)
- ❌ Inefficient for frequently-needed context (physics rules)

**Decision:** **Rejected** - Memory system provides automatic context loading, eliminating manual overhead.

#### Alternative 4: Skill-Based Context Injection

**Description:** Use Skills system to dynamically inject context when needed.

**Pros:**
- ✅ Progressive disclosure (only load when skill activated)
- ✅ Context tied to specific task types
- ✅ Can include executable validation logic

**Cons:**
- ❌ Skills are for actions, not passive context storage
- ❌ Overhead of skill activation for every context need
- ❌ Doesn't solve cross-session persistence
- ❌ Not suitable for always-needed context (SI units)

**Decision:** **Rejected** - Skills complement memory but don't replace it. Memory provides persistent baseline, skills add dynamic capabilities.

#### Alternative 5: Hybrid: Minimal CLAUDE.md + Targeted Memory Files

**Description:** Keep critical rules inline in CLAUDE.md, use memory only for reference materials.

**Pros:**
- ✅ Guaranteed critical context always loads
- ✅ Reduces risk of import failures breaking essential rules
- ✅ Balances simplicity and modularity

**Cons:**
- ❌ Unclear boundary between "critical" and "reference"
- ❌ Still requires some token overhead for inline content
- ❌ Doesn't fully leverage memory optimization potential

**Decision:** **Partially Adopted** - Keep critical rules duplicated in CLAUDE.md during migration (Phase 1-2), but full migration to memory is goal (Phase 3).

#### Selected Approach: Modular Project Memory with Fallback

**Rationale:**
- Maximizes token efficiency via selective loading
- Maintains team consistency (no user-level overrides)
- Provides fallback via inline content during migration
- Enables targeted updates without touching monolithic file
- Better separation of concerns (physics vs. testing vs. git)

**Trade-offs Accepted:**
- Migration complexity (mitigated by incremental approach)
- Import resolution dependency (mitigated by fallback content)
- Slightly more files to maintain (offset by better organization)

### 4.6. Stopping Conditions

**Anthropic Best Practice:** "Implement stopping conditions to prevent runaway token consumption or over-activation of features."

Memory system includes safeguards to prevent context window pollution:

#### Rate Limiting: Memory Imports per Session

**Limit:** Maximum 20 memory file imports per session

**Rationale:**
- Each memory file averages 1,500-2,000 tokens
- 20 files × 2,000 tokens = 40,000 tokens maximum (20% of 200K budget)
- SolarWindPy's 9 core files consume ~15K tokens (7.5% of budget)
- Remaining headroom prevents accidental over-importing

**Monitoring:**
```bash
# Count memory imports in current session
grep "@.claude/memory/" .claude/logs/session-*.log | wc -l

# Warning if ≥15 imports (75% of limit)
# Error if ≥20 imports (100% of limit)
```

**Override:** Explicit user request bypasses limit ("Import all physics memory files")

#### Budget Guards: Context Allocation Ceiling

**Limit:** Memory allocation ≤10% of total context budget (20K of 200K tokens)

**Rationale:**
- Anthropic recommends keeping persistent context minimal
- 90% of context window (180K tokens) reserved for:
  - User conversation history
  - Tool use outputs (grep, file reads)
  - Code changes and diffs
  - Subagent reports
- Memory provides *reference* information, not active work

**Token Budget Allocation:**
| Category | Budget | Percentage | Justification |
|----------|--------|------------|---------------|
| Memory files | 20K tokens | 10% | Persistent project context |
| Conversation | 70K tokens | 35% | User messages + assistant responses |
| Tool outputs | 60K tokens | 30% | File reads, grep results, bash output |
| Subagents | 50K tokens | 25% | Delegated task reports |
| **Total** | **200K tokens** | **100%** | Full context window |

**Enforcement:**
- Memory file size monitoring: Each file ≤3K tokens (exception: testing-templates.md at 4K)
- Total memory directory: ≤20K tokens (tracked in CI/CD)
- Warning at 18K tokens (90% of budget)
- Block commit if >20K tokens

#### Context Budget Monitoring

**Implementation:**
```bash
# Check current memory token usage
python .claude/scripts/count-memory-tokens.py

# Expected output:
# .claude/memory/physics-constants.md: 1,200 tokens
# .claude/memory/dataframe-patterns.md: 1,800 tokens
# .claude/memory/testing-templates.md: 4,000 tokens
# ... (other files)
# TOTAL: 14,500 tokens (72.5% of 20K budget)
```

**Thresholds:**
- ✅ **Green (0-15K tokens / 0-75%):** Normal operation
- ⚠️ **Yellow (15K-18K tokens / 75-90%):** Warning, review memory content for redundancy
- 🔴 **Red (18K-20K tokens / 90-100%):** Critical, identify files to split or archive
- ❌ **Block (>20K tokens):** Exceeds budget, must reduce before commit

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

*Technical Prerequisites:*
- ✅ None - Memory hierarchy is foundational feature
- ✅ Claude Code (any version supporting file imports)
- ✅ Existing CLAUDE.md file (to be refactored)

*Infrastructure Requirements:*
- ✅ Git repository (for version controlling memory files)
- ✅ `.claude/` directory structure
- ✅ Team agreement on project-only memory model

*Knowledge Prerequisites:*
- ⚠️ Understanding of current CLAUDE.md content structure
- ⚠️ Familiarity with `@file` import syntax
- ⚠️ Awareness of 5-level import depth limit

*Implementation Considerations:*
- ⚠️ Requires careful extraction to avoid breaking existing context
- ⚠️ Import paths must use correct format (relative from project root)
- ⚠️ Testing needed to verify all imports resolve correctly

*Optional Enhancements* (implement after memory):
- 🔄 Skills System - Skills can reference memory files
- 🔄 Output Styles - Styles can emphasize memory organization
- 🔄 Enhanced Hooks - Hooks can validate memory consistency

**Estimated Effort:**
- Memory structure design: **2-3 hours**
- Content extraction: **4-6 hours** (9 memory files)
- Implement stopping conditions: **6-10 hours** (rate limiting, budget guards, monitoring scripts)
- Add metrics infrastructure: **4-6 hours** (token counting, budget tracking, CI/CD enforcement)
- Testing & validation: **2-3 hours**
- Documentation: **1-2 hours**
- **Total: 19-30 hours**

**Note:** Increased from 9-14h to account for stopping conditions and metrics infrastructure required for safe deployment. These additions prevent memory system from consuming excessive context budget and enable measurement of ≥30% token reduction goal.

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

**Measurement Methodology:**

*How Time Savings Are Calculated:*
1. **Baseline measurement:** Track time spent repeating context ("remember units conversion pattern," "check display→SI→display") in 20 representative sessions
2. **Average repetition time:** 5-10 minutes per session for context-setting
3. **Session frequency:** Estimate 10-15 development sessions per week based on team activity
4. **Calculation:** (5-10 min/session) × (10-15 sessions/week) = 50-150 min/week saved

*How Token Reduction Is Measured:*
1. **Baseline:** Count tokens in current monolithic CLAUDE.md using Claude API tokenizer (~2,500 tokens)
2. **Post-implementation:** Measure token count of selectively loaded memory imports (estimate 1,000-1,500 tokens for typical session)
3. **Calculation:** ((2,500 - 1,500) / 2,500) × 100% = 40% reduction (conservative estimate)
4. **Annual projection:** Token savings per session × 200 sessions/year = 200,000-300,000 tokens annually

*Verification Methods:*
- **Time tracking:** Log context-setting time in session notes for 4 weeks pre/post implementation
- **Token counting:** Use Claude API's token counter on actual memory files loaded
- **A/B testing:** Compare sessions with monolithic vs. modular memory (5 sessions each)
- **Subjective assessment:** Team survey on context preservation quality

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
Session 1: Ask about units conversion pattern
Session 2 (new): Ask same question without repeating context
Expected: Claude knows display→SI→display pattern from memory
Validation: No need to re-explain units architecture
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

**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
