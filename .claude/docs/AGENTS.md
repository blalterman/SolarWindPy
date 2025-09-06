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