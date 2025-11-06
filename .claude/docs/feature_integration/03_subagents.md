# Subagents (Enhanced Agent System)

**Feature Type:** Automatic
**Priority:** MEDIUM-HIGH
**Effort:** 12-17 hours
**ROI Break-even:** 6-9 weeks

[← Back to Index](./INDEX.md) | [← Previous: Skills](./02_skills_system.md) | [Next: Enhanced Hooks →](./04_enhanced_hooks.md)

---

**✅ OFFICIAL PLUGIN FEATURE - Native Support**

Subagents (called "agents" in plugin spec) are officially supported as plugin components (plugin-name/agents/).
See: [Plugin Packaging](./08_plugin_packaging.md#subagents)

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

### 3.5. Risk Assessment

#### Technical Risks

**Risk: Context Isolation Too Restrictive**
- **Likelihood:** Medium
- **Impact:** High (subagent can't access needed information)
- **Mitigation:**
  - Explicitly pass file paths and critical context in invocation
  - Use Read tool within subagent to access codebase
  - Document what context needs explicit passing
  - Test common workflows for context availability
  - Fallback to Task agent if isolation causes issues

**Risk: Subagent Can't Modify Main Session State**
- **Likelihood:** High (by design)
- **Impact:** Medium (requires workflow adjustment)
- **Mitigation:**
  - Design subagents for analysis, not mutation
  - Have subagent return recommendations, main session applies changes
  - Document clear handoff patterns
  - Use Task agents for workflows requiring stateful coordination

**Risk: Plugin Packaging Complexity**
- **Likelihood:** Low-Medium
- **Impact:** Medium (distribution difficulties)
- **Mitigation:**
  - Test subagent markdown files in plugin context
  - Use relative paths only (no absolute paths)
  - Document plugin structure requirements
  - Validate across different project structures

**Risk: Subagent Name Conflicts**
- **Likelihood:** Low
- **Impact:** Medium (namespace collisions if using external plugins)
- **Mitigation:**
  - Use descriptive, SolarWindPy-specific names
  - Namespace with prefix if publishing: `swpy-physics-validator`
  - Check existing plugin marketplaces for name conflicts
  - Document naming conventions

#### Adoption Risks

**Risk: Confusion Between Task Agents and Subagents**
- **Likelihood:** High
- **Impact:** Medium (workflow inefficiency)
- **Mitigation:**
  - Clear naming: Keep existing Task agents, add "subagent" suffix to new ones
  - Document decision matrix in CLAUDE.md
  - Provide examples of when to use each type
  - Gradual migration (don't convert all at once)

**Risk: Over-Engineering with Unnecessary Isolation**
- **Likelihood:** Medium
- **Impact:** Low-Medium (added complexity without benefit)
- **Mitigation:**
  - Only convert agents that genuinely benefit from isolation
  - Measure actual performance improvements
  - Keep Task agents if no clear benefit from subagent conversion
  - Re-evaluate after 4-week pilot

**Risk: Team Adoption Resistance**
- **Likelihood:** Low
- **Impact:** Low (Task agents still work)
- **Mitigation:**
  - Make subagents optional enhancement, not replacement
  - Demonstrate clear benefits (faster, lower token usage)
  - Pilot with 1-2 subagents initially
  - Gather feedback before full rollout

#### Performance Risks

**Risk: Subagent Invocation Latency**
- **Likelihood:** Low
- **Impact:** Low (minor startup overhead)
- **Mitigation:**
  - Monitor invocation timing
  - Keep subagent prompts under 2000 tokens
  - Optimize YAML frontmatter and markdown structure
  - Measure vs. Task agent performance

**Risk: Multiple Subagent Coordination Overhead**
- **Likelihood:** Medium
- **Impact:** Medium (complex workflows slower)
- **Mitigation:**
  - Use subagents for independent analysis tasks
  - Avoid chaining multiple subagents
  - Use Task agents for workflows requiring tight coordination
  - Document coordination patterns

**Risk: Token Budget Exceeded with Isolated Contexts**
- **Likelihood:** Low
- **Impact:** Medium (can't complete analysis)
- **Mitigation:**
  - Design subagents for focused, scoped tasks
  - Pass minimal necessary context
  - Monitor token usage per subagent type
  - Split large tasks across multiple invocations if needed

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
   - M (Measurement): Physical quantity (examples: v, n, w, p, b, T, q, beta)
   - C (Component): Varies by measurement
     - Cartesian: x, y, z
     - RTN: R, T, N (uppercase)
     - Anisotropy: par, per, scalar
     - None (scalars)
   - S (Species): Particle identifier (examples: p, a, e, O, Fe, C)

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

*Immediate Disable (Test If Subagents Are The Problem):*
1. Rename `.claude/agents/` to `.claude/agents.disabled/`
2. Restart Claude Code session
3. Task agents (original 7) continue working unchanged
4. Verify issue resolves (confirms subagents were cause)

*Full Rollback (Local Implementation):*
1. Delete `.claude/agents/` directory entirely
2. `git revert` commits that added subagent definitions
3. Resume using Task tool for PhysicsValidator, DataFrameArchitect, etc.
4. No loss of functionality (Task agents provide same capabilities)

*Full Rollback (Plugin Installation):*
1. `/plugin uninstall solarwindpy-devtools`
2. Verify agents directory removed
3. Use Task tool for all agent invocations
4. Local `.claude/agents/` (if any) takes precedence over plugin

*Selective Rollback (Disable Specific Subagent):*
1. Rename problematic subagent: `.claude/agents/physics-validator.md` → `.claude/agents/physics-validator.md.disabled`
2. Other subagents continue working
3. Use Task agent for that specific workflow
4. Investigate and fix subagent prompt/scope

*Rollback Verification Steps:*
- ✅ Task agents invoke correctly via Task tool
- ✅ No subagent invocation errors
- ✅ Workflows function with explicit Task agent calls
- ✅ No performance degradation
- ✅ Context isolation not causing issues

*Risk:** Very low - Subagents are optional layer over Task agents. Rollback is simple deletion, Task agents are always available.

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

**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
