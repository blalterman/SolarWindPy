# SolarWindPy Claude Code Prompt Best Practices Checklist

Use this checklist to validate your prompts before submitting to Claude Code. Check off each applicable item to ensure comprehensive, effective prompts.

## ✅ Physics Domain Requirements

### Core Physics Principles
- ☐ **SI Units**: Specified "use SI units internally, convert only for display"
- ☐ **Thermal Convention**: Mentioned "mw² = 2kT convention" if temperature calculations involved
- ☐ **Missing Data**: Specified "use NaN for missing data, never 0 or -999"
- ☐ **Physical Bounds**: Included typical solar wind parameter ranges where relevant
- ☐ **Conservation Laws**: Considered energy, momentum, mass conservation where applicable

### Plasma Parameters
- ☐ **Density**: Specified ion number densities (n₁, n₂, nₐ) in cm⁻³ or m⁻³
- ☐ **Velocity**: Included velocity components (vₓ, vᵧ, v_z) and bulk flow considerations
- ☐ **Temperature**: Specified parallel/perpendicular temperatures if anisotropy relevant
- ☐ **Magnetic Field**: Included B field components and coordinate system
- ☐ **Ion Species**: Clearly identified p1, p2, alpha particles, or other species involved

### Physics Validation
- ☐ **Edge Cases**: Considered density nulls, magnetic nulls, extreme parameter values
- ☐ **Instabilities**: Referenced relevant instabilities (mirror, firehose, etc.) if applicable
- ☐ **Literature Values**: Included known parameter ranges from solar wind observations
- ☐ **Numerical Stability**: Addressed potential numerical issues (division by zero, etc.)

## ✅ SolarWindPy Architecture

### Data Structure
- ☐ **MultiIndex**: Referenced 3-level structure ("M", "C", "S")
- ☐ **DataFrame Access**: Specified use of .xs() for views, not copies
- ☐ **Column Access**: Proper level specification for MultiIndex operations
- ☐ **Data Integrity**: Maintained hierarchical structure throughout operations

### Core Classes
- ☐ **Plasma Class**: Referenced central container functionality
- ☐ **Ion Class**: Specified individual ion species operations
- ☐ **Base Class**: Mentioned abstract base for logging/units if extending
- ☐ **Spacecraft**: Included if working with observational data

### Module Structure
- ☐ **Core Module**: Referenced core/ for fundamental physics classes
- ☐ **FitFunctions**: Mentioned fitfunctions/ if statistical analysis involved
- ☐ **Plotting**: Referenced plotting/ for visualization requirements
- ☐ **Instabilities**: Included instabilities/ for plasma instability calculations
- ☐ **Tools**: Referenced tools/ for utility functions

## ✅ Agent Selection & Usage

### Specialized Agents
- ☐ **UnifiedPlanCoordinator**: For planning and implementation coordination
- ☐ **PhysicsValidator**: For unit consistency and physics validation
- ☐ **DataFrameArchitect**: For MultiIndex DataFrame optimization
- ☐ **NumericalStabilityGuard**: For edge cases and numerical stability
- ☐ **PlottingEngineer**: For scientific visualization tasks
- ☐ **FitFunctionSpecialist**: For curve fitting and statistical analysis
- ☐ **TestEngineer**: For physics-specific testing strategies

### Agent Application
- ☐ **Appropriate Selection**: Chose agent matching task complexity and domain
- ☐ **Clear Delegation**: Specified what the agent should focus on
- ☐ **Integration**: Considered how agent output integrates with existing code

## ✅ Development Workflow

### Git Workflow
- ☐ **Branch Strategy**: Specified plan/* for planning, feature/* for implementation
- ☐ **PR Flow**: Referenced feature → plan → PR → master workflow
- ☐ **Merge Strategy**: No direct master commits mentioned
- ☐ **Workflow Validation**: Included git-workflow-validator.sh hook usage

### Testing Requirements
- ☐ **Coverage Target**: Specified ≥95% test coverage requirement
- ☐ **Test Types**: Included unit tests, physics validation, edge cases
- ☐ **Test Generation**: Referenced .claude/scripts/generate-test.py if needed
- ☐ **Physics Tests**: Included .claude/hooks/test-runner.sh --physics
- ☐ **Performance Tests**: Added benchmarking if optimization involved

### Hook Validation
- ☐ **Physics Validation**: Referenced .claude/hooks/physics-validation.py
- ☐ **Coverage Monitoring**: Included .claude/hooks/coverage-monitor.py
- ☐ **Pre-commit Tests**: Referenced .claude/hooks/pre-commit-tests.sh
- ☐ **Session State**: Considered .claude/hooks/validate-session-state.sh

## ✅ Prompt Structure & Clarity

### XML Organization
- ☐ **Physics Context**: Included domain-specific physics background
- ☐ **Architecture Section**: Referenced SolarWindPy structure and patterns
- ☐ **Clear Instructions**: Numbered, specific, actionable steps
- ☐ **Git Workflow**: Specified branch strategy and testing requirements
- ☐ **Verification**: Included validation and testing steps

### Instruction Quality
- ☐ **Specificity**: Avoided vague requests, provided concrete objectives
- ☐ **Context**: Included motivation and intended audience
- ☐ **Examples**: Added 3-5 diverse examples for complex structured outputs
- ☐ **Chain of Thought**: Used `<thinking>` tags for complex analysis
- ☐ **Output Format**: Specified expected response structure

### Clarity & Completeness
- ☐ **Golden Rule**: Prompt would be clear to a colleague without context
- ☐ **Sequential Steps**: Logical order from setup to verification
- ☐ **Explicit Conventions**: Stated physics and coding conventions to follow
- ☐ **Success Criteria**: Defined how to measure task completion

## ✅ Verification & Quality Assurance

### Physics Verification
- ☐ **Unit Consistency**: Check dimensional analysis throughout
- ☐ **Physical Bounds**: Verify results within expected parameter ranges
- ☐ **Conservation Laws**: Validate energy, momentum, mass conservation
- ☐ **Literature Comparison**: Compare against known solar wind observations

### Code Quality
- ☐ **Style Consistency**: Follow existing SolarWindPy patterns
- ☐ **Backward Compatibility**: Maintain API compatibility where possible
- ☐ **Performance**: Consider computational efficiency and memory usage
- ☐ **Documentation**: Include docstrings and comments where appropriate

### Testing Strategy
- ☐ **Edge Cases**: Test boundary conditions and extreme parameters
- ☐ **Numerical Stability**: Validate behavior near singularities
- ☐ **Integration**: Test interaction with existing functionality
- ☐ **Regression**: Ensure changes don't break existing features

## 📝 Final Review Questions

Before submitting your prompt, ask yourself:

1. **Physics**: Would a plasma physicist understand the domain requirements?
2. **Architecture**: Does this respect SolarWindPy's design patterns?
3. **Testing**: Is the verification strategy comprehensive enough?
4. **Clarity**: Could Claude execute this prompt without additional clarification?
5. **Integration**: Will this work seamlessly with existing SolarWindPy features?

## ✅ Completion Checklist

- ☐ All relevant sections above have been reviewed
- ☐ Physics domain requirements are clearly specified
- ☐ SolarWindPy architecture patterns are referenced
- ☐ Appropriate specialized agent is selected
- ☐ Git workflow and testing requirements are included
- ☐ Verification steps ensure quality and correctness
- ☐ Prompt follows XML structure with clear sections
- ☐ Ready to submit to Claude Code