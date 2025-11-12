# Agent System Documentation

Specialized AI agents for SolarWindPy development using the Task tool.

## Agent Overview

### UnifiedPlanCoordinator
- **Purpose**: All planning, implementation, and status coordination
- **Capabilities**: GitHub Issues integration, velocity intelligence
- **Critical**: MUST execute CLI scripts, not describe them
- **Usage**: `"Use UnifiedPlanCoordinator to create GitHub Issues plan for <feature>"`

### PhysicsValidator  
- **Purpose**: Physics correctness and unit validation
- **Capabilities**: Solar wind physics constraints, scientific validation
- **Critical**: Thermal speed mw² = 2kT, SI units, NaN for missing data
- **Usage**: `"Use PhysicsValidator to verify thermal speed calculations"`

### DataFrameArchitect
- **Purpose**: MultiIndex data structure management  
- **Capabilities**: Pandas performance optimization, memory management
- **Critical**: Use .xs() for views, (M/C/S) level structure
- **Usage**: `"Use DataFrameArchitect to optimize MultiIndex operations"`

### NumericalStabilityGuard
- **Purpose**: Numerical validation and edge cases
- **Capabilities**: Prevents numerical errors, ensures stable computations
- **Critical**: Handles edge cases, precision issues
- **Usage**: `"Use NumericalStabilityGuard for computational stability"`

### PlottingEngineer
- **Purpose**: Visualization and plotting functionality  
- **Capabilities**: Matplotlib expertise, publication-quality figures
- **Critical**: Scientific visualization standards
- **Usage**: `"Use PlottingEngineer to create publication-quality figures"`

### FitFunctionSpecialist
- **Purpose**: Curve fitting and statistical analysis
- **Capabilities**: Statistical analysis, optimization algorithms
- **Critical**: Data fitting patterns, abstract base classes
- **Usage**: `"Use FitFunctionSpecialist for statistical analysis"`

### TestEngineer
- **Purpose**: Test coverage and quality assurance
- **Capabilities**: Physics-specific testing, scientific validation
- **Critical**: ≥95% coverage requirement
- **Usage**: `"Use TestEngineer to design physics-specific test strategies"`

## Agent Execution Requirements

### Critical Rules
1. **Agents MUST execute CLI scripts when requested, not describe them**
2. **If an agent returns text instead of creating issues, execution has FAILED**  
3. **Manual fallback**: Run `.claude/scripts/gh-plan-create.sh` directly

### UnifiedPlanCoordinator Specifics
- **Batch Mode Required**: Use temporary config files
- **Script Execution**: Must run gh-plan-create.sh and gh-plan-phases.sh
- **Config Format**: `Phase Name|Duration|Dependencies`
- **Never use quick mode**: Always provide specific durations
- **Hook Integration**: Calls plan-value-generator.py and plan-scope-auditor.py

## Usage Examples

```python
# Planning and implementation with GitHub Issues  
"Use UnifiedPlanCoordinator to create GitHub Issues plan for dark mode implementation"

# Domain-specific work
"Use PhysicsValidator to verify thermal speed calculations"
"Use DataFrameArchitect to optimize MultiIndex operations"  
"Use PlottingEngineer to create publication-quality figures"
"Use TestEngineer to design physics-specific test strategies"
```

## Agent Selection Guidelines
- **Planning tasks** → UnifiedPlanCoordinator
- **Physics calculations** → PhysicsValidator
- **Data structure optimization** → DataFrameArchitect  
- **Numerical precision** → NumericalStabilityGuard
- **Visualization** → PlottingEngineer
- **Statistical analysis** → FitFunctionSpecialist
- **Test design** → TestEngineer

## Integration with Hooks
Agents work seamlessly with the automated hook system:
- **Pre-tool validation** ensures physics correctness
- **Post-tool testing** runs automatically after changes
- **Plan value generation** happens via UnifiedPlanCoordinator hooks
- **Coverage monitoring** integrates with TestEngineer strategies

## Removed Agents (Aug 15, 2025 Consolidation)

The following agents were strategically removed during the agent ecosystem optimization (commit e4fc96a) that reduced the system from 14 to 7 agents, achieving a 54.4% context reduction (3,895 → 1,776 lines).

### PerformanceOptimizer
- **Original purpose**: Computational performance optimization (numba, vectorization, profiling)
- **Removal rationale**: Low-priority maintenance work; manual optimization on-demand is sufficient
- **Functionality status**: Retired - numba/vectorization guidance available in `.claude/agents.backup/agent-performance-optimizer.md`
- **When to reference**: If performance becomes a critical bottleneck

### DocumentationMaintainer
- **Original purpose**: Documentation maintenance, Sphinx builds, docstring validation
- **Removal rationale**: Documentation work absorbed into general development workflow
- **Functionality status**: Manual documentation work; CI/CD handles Sphinx builds automatically
- **When to reference**: If documentation debt accumulates significantly

### DependencyManager
- **Original purpose**: Package dependency management, conda/pip compatibility, version constraints
- **Removal rationale**: Low-frequency task (dependencies updated infrequently); manual management sufficient
- **Functionality status**: Manual management via `scripts/update_conda_recipe.py`
- **When to reference**: For complex dependency conflicts or major version updates

**Strategic Context**: These agents were replaced by a comprehensive hooks system that automates repetitive validation and testing tasks. The consolidation prioritized agents requiring domain expertise (physics, data structures, numerical analysis) over those handling mechanical tasks (performance profiling, documentation builds, dependency updates).

**See also**:
- Full agent definitions: `.claude/agents.backup/`
- Consolidation commit: `e4fc96a497262fb1c7274d80b3a697b99049c975`
- Strategic planning: `.claude/docs/feature_integration/03_subagents.md`, `04_enhanced_hooks.md`

## Planned But Not Implemented

The following agents were documented as "Planned Agents" in `.claude/agents.backup/agents-index.md` (lines 253-256) but were intentionally not implemented based on strategic assessment.

### SolarActivityTracker
- **Planned purpose**: Specialized solar indices management for `solarwindpy/solar_activity/` module
- **Decision rationale**: Module is self-sufficient and straightforward; dedicated agent would be redundant
- **Current status**: `solarwindpy/solar_activity/` functions independently without agent support
- **Implementation**: No agent needed - direct module work is more efficient

### IonSpeciesValidator
- **Planned purpose**: Ion-specific physics validation (thermal speeds, mass/charge ratios, anisotropies)
- **Decision rationale**: Functionality fully covered by existing PhysicsValidator agent
- **Current status**: PhysicsValidator handles all ion validation requirements
- **Implementation**: No separate agent needed - PhysicsValidator is comprehensive

### CIAgent
- **Planned purpose**: Continuous integration management for GitHub Actions workflows
- **Decision rationale**: CI/CD is already fully automated; workflow file editing is infrequent and straightforward
- **Current status**: GitHub Actions handles CI/CD automatically; manual workflow editing when needed
- **Implementation**: No agent needed - CI/CD configuration changes are rare

### CodeRefactorer
- **Planned purpose**: Automated refactoring suggestions for code structure and patterns
- **Decision rationale**: Base Claude Code capabilities already handle refactoring excellently
- **Current status**: General-purpose refactoring via standard Claude Code interaction
- **Implementation**: No specialized agent needed - Claude Code's core capabilities are sufficient

**Strategic Context**: These agents represent thoughtful planning followed by pragmatic decision-making. Rather than over-engineering the agent system, we validated that existing capabilities (modules, agents, base Claude Code) already addressed these needs. This "plan but validate necessity" approach prevented agent proliferation.

**See also**: `.claude/agents.backup/agents-index.md` for original "Planned Agents" documentation