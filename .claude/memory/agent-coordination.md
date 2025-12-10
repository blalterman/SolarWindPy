# SolarWindPy Agent Coordination Guide

**Scope:** Agent selection, coordination patterns, and routing for SolarWindPy's 6 specialized agents
**See also:** CLAUDE.md for agent selection matrix, .claude/agents.md for detailed agent instructions

## Agent Overview

**SolarWindPy uses 6 domain-specific agents** organized by priority:

**Priority 1: Coordination**
- **UnifiedPlanCoordinator** - Planning, implementation, project management
  - **Use for:** Multi-step tasks, complex implementations, cross-module coordination
  - **Must execute:** CLI scripts directly (`.claude/scripts/gh-plan-*.sh`)

**Priority 2: Domain Specialists**
- **DataFrameArchitect** - MultiIndex operations, pandas optimization, memory efficiency
  - **Use for:** DataFrame structure, `.xs()` views, memory optimization
  - **Files:** `core/plasma.py`, `core/ions.py`, `core/spacecraft.py`

- **NumericalStabilityGuard** - Numerical validation, edge cases, stability analysis
  - **Use for:** Overflow/underflow, matrix conditioning, iterative convergence
  - **Files:** `instabilities/*.py`, `fitfunctions/*.py`

- **PlottingEngineer** - Visualization, matplotlib expertise, publication-quality figures
  - **Use for:** Scientific visualizations, colorblind-friendly plots
  - **Files:** `plotting/*.py`

- **FitFunctionSpecialist** - Curve fitting, statistical analysis, data modeling
  - **Use for:** Regression analysis, parameter optimization, inherit from FitFunction base
  - **Files:** `fitfunctions/*.py`

**Priority 3: Quality Assurance**
- **TestEngineer** - Test coverage, quality assurance (≥95% requirement)
  - **Use for:** Test design, pytest fixtures, edge case validation
  - **Files:** `tests/*.py`, `.claude/hooks/*.py`

## Coordination Patterns

### Single Agent Tasks

**Direct invocation** when task clearly maps to one agent:

```
User: "Optimize MultiIndex operations in plasma.py"
→ DataFrameArchitect (DataFrame optimization requiring pandas expertise)

User: "Create publication-quality plots"
→ PlottingEngineer (visualization task requiring matplotlib expertise)

User: "Implement robust fitting for power law distribution"
→ FitFunctionSpecialist (curve fitting with error handling)
```

### Multi-Agent Coordination

**UnifiedPlanCoordinator manages** when multiple specialists needed:

```
User: "Implement plasma instability analysis with visualization and testing"
→ UnifiedPlanCoordinator orchestrates:
  1. NumericalStabilityGuard - Validates numerical stability
  2. PlottingEngineer - Creates visualizations
  3. TestEngineer - Implements tests
```

**Handoff protocol:** UnifiedPlanCoordinator manages transitions between specialists

### Priority Cascade

**When multiple agents match:**
1. Priority 1 (UnifiedPlanCoordinator) takes lead for coordination
2. Priority 2 specialists work in parallel on independent modules
3. Priority 3 (TestEngineer) validates after implementation

## Routing Triggers

### File Pattern Examples

**Representative examples** (see .claude/agent-routing.json for complete mappings):

| File Pattern | Routed Agents |
|--------------|---------------|
| `solarwindpy/core/plasma.py` | DataFrameArchitect |
| `solarwindpy/instabilities/*.py` | NumericalStabilityGuard |
| `solarwindpy/plotting/*.py` | PlottingEngineer |
| `solarwindpy/fitfunctions/*.py` | FitFunctionSpecialist, NumericalStabilityGuard |
| `tests/*.py` | TestEngineer |

### Keyword Triggers

| Keywords | Routed Agent |
|----------|--------------|
| plan, planning, implement | UnifiedPlanCoordinator |
| dataframe, multiindex, pandas | DataFrameArchitect |
| numerical, stability, precision | NumericalStabilityGuard |
| plot, visualization, figure | PlottingEngineer |
| fit, curve, regression, optimization | FitFunctionSpecialist |
| test, coverage, pytest | TestEngineer |

### Context Triggers

**Route based on task complexity:**
- Multi-step task → UnifiedPlanCoordinator
- Data analysis → DataFrameArchitect
- Numerical tasks → NumericalStabilityGuard
- Visualization tasks → PlottingEngineer

## Common Anti-Patterns

### ❌ Don't: Route to Single Agent for Multi-Domain Task

**Problem:**
```
User: "Implement instability analysis with plots and tests"
→ NumericalStabilityGuard only
Result: Missing visualization and testing expertise
```

**Solution:**
```
User: "Implement instability analysis with plots and tests"
→ UnifiedPlanCoordinator orchestrates NumericalStabilityGuard, PlottingEngineer, TestEngineer
```

### ❌ Don't: Skip TestEngineer for New Features

**Problem:**
```
User: "Add new plasma parameter calculation"
→ Implementation proceeds without tests
Result: Coverage drops below 95% requirement
```

**Solution:**
```
User: "Add new plasma parameter calculation"
→ DataFrameArchitect + TestEngineer
```

### ❌ Don't: Use DataFrameArchitect for Numerical Validation

**Problem:**
```
User: "Fix numerical overflow in instability calculation"
→ DataFrameArchitect (because file is in core/)
Result: DataFrame optimization without numerical stability analysis
```

**Solution:**
```
User: "Fix numerical overflow in instability calculation"
→ NumericalStabilityGuard (numerical issue) + DataFrameArchitect (if DataFrame structure changes)
```

## Agent Interaction Rules

### Collaboration Requirements

**Unit patterns must follow code-style.md:**
- SI units for internal calculations (lines 248-271)
- Inline unit conversion comments (km/s → m/s pattern)

**TestEngineer validates:**
- All new code before merge (coverage ≥95%, edge cases tested)

**DataFrameArchitect reviews:**
- All data structure modifications (MultiIndex operations, memory-intensive operations)

### Parallel Execution

**Agents can work in parallel on independent modules:**
- NumericalStabilityGuard on numerical algorithms
- PlottingEngineer on visualization
- TestEngineer on test suite
- Coordinated by UnifiedPlanCoordinator

## Usage Examples

### Example 1: Numerical Stability Issue

**Input:** "Fix overflow in instability growth rate calculation"

**Routing:**
- Primary: NumericalStabilityGuard
- File pattern match: `solarwindpy/instabilities/*.py`
- Keyword match: "overflow" → NumericalStabilityGuard

**Execution:**
1. NumericalStabilityGuard identifies overflow conditions
2. Implements numerical safeguards (log-space calculations, clamping)
3. Validates edge cases (extreme parameter values)
4. Coordinates with TestEngineer for edge case tests

### Example 2: Multi-Agent (Complex Implementation)

**Input:** "Implement plasma instability analysis with visualization and testing"

**Routing:**
- Primary: UnifiedPlanCoordinator
- Supporting: NumericalStabilityGuard, PlottingEngineer, TestEngineer

**Execution:**
1. UnifiedPlanCoordinator creates plan
2. NumericalStabilityGuard ensures numerical stability
3. PlottingEngineer creates publication-quality figures
4. TestEngineer implements comprehensive tests
5. UnifiedPlanCoordinator coordinates handoffs

### Example 3: DataFrame Optimization

**Input:** "Optimize MultiIndex operations in plasma.py"

**Routing:**
- Primary: DataFrameArchitect
- File pattern match: `solarwindpy/core/plasma.py`
- Keyword match: "multiindex"

**Execution:**
1. DataFrameArchitect analyzes current structure
2. Identifies memory inefficiencies
3. Proposes `.xs()` views instead of copies
4. Updates code with memory-efficient patterns

## Common Patterns Summary

1. **DataFrame operations** → DataFrameArchitect
2. **Multi-domain tasks** → UnifiedPlanCoordinator orchestrates
3. **Instability analysis** → NumericalStabilityGuard
4. **Curve fitting** → FitFunctionSpecialist + NumericalStabilityGuard
5. **Visualization** → PlottingEngineer
6. **Testing** → TestEngineer (for all new features)
7. **Planning** → UnifiedPlanCoordinator
8. **Priority cascade** → 1 (coordination) > 2 (specialists) > 3 (testing)

## See Also

- **CLAUDE.md** - Agent selection matrix and essential commands
- **.claude/agents.md** - Detailed agent instructions and interaction patterns
- **.claude/agent-routing.json** - Complete routing configuration
- **code-style.md** - SI units convention and unit conversion patterns
- **testing-templates.md** - TestEngineer patterns and coverage requirements
