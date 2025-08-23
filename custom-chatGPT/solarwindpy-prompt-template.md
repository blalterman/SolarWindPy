# SolarWindPy Claude Code Prompt Template

Use this template to create well-structured prompts for SolarWindPy development. Fill in the sections based on your specific task requirements.

## Template Structure

```xml
<physics_context>
<!-- Describe the solar wind physics domain context -->
<!-- Example: "Calculate ion thermal anisotropy for mirror instability analysis" -->
[DESCRIBE YOUR PHYSICS OBJECTIVE HERE]

<!-- Specify relevant plasma parameters -->
Plasma parameters: [density (n), velocity (v), temperature (T), magnetic field (B)]
Ion species: [p1 (protons), p2 (secondary protons), a (alphas), etc.]
Physical regime: [MHD, kinetic, hybrid]
Constraints: [conservation laws, physical bounds, typical solar wind ranges]

<!-- Units convention -->
Units: SI internally (specify display units if different)
Missing data: NaN (never 0 or -999)
</physics_context>

<solarwindpy_architecture>
<!-- Specify which parts of SolarWindPy are involved -->
Core classes: [Plasma, Ion, Spacecraft, Base]
Modules: [core/, fitfunctions/, plotting/, instabilities/, tools/]
DataFrame structure: MultiIndex ("M", "C", "S") - [describe access pattern]

<!-- Existing patterns to follow -->
Existing functionality: [reference similar methods/classes if extending]
Data access: Use .xs() for DataFrame views, not copies
Conventions: [thermal speed mw² = 2kT, Alfvén speed V_A = B/√(μ₀ρ)]
</solarwindpy_architecture>

<instructions>
1. [PRIMARY OBJECTIVE - be explicit and specific]
2. [AGENT SELECTION - choose appropriate specialized agent]:
   - UnifiedPlanCoordinator: for planning and implementation coordination
   - PhysicsValidator: for unit consistency and physics validation
   - DataFrameArchitect: for MultiIndex DataFrame optimization
   - NumericalStabilityGuard: for edge cases and numerical stability
   - PlottingEngineer: for scientific visualization
   - FitFunctionSpecialist: for curve fitting and statistical analysis
   - TestEngineer: for physics-specific testing strategies

3. [PHYSICS REQUIREMENTS]:
   - Maintain SI units internally
   - Apply appropriate physical conventions
   - Handle edge cases (density/field nulls, extreme parameters)
   - Validate against known solar wind behavior

4. [TECHNICAL REQUIREMENTS]:
   - Follow DataFrame MultiIndex patterns
   - Use .xs() for efficient data access
   - Maintain backward compatibility
   - Follow existing code style and patterns

5. [OUTPUT FORMAT]:
   - [Specify desired output structure]
   - [Any plotting or visualization requirements]
   - [File formats or data structures needed]
</instructions>

<git_workflow>
<!-- Specify branch strategy -->
Branch strategy: [plan/your-feature-name OR feature/your-feature-name]
Target: [feature → plan → PR → master workflow]

<!-- Testing requirements -->
Test coverage: ≥95% required
Test types: [unit tests, physics validation, edge cases, performance tests]
Hook validation: [physics-validation.py, coverage-monitor.py, git-workflow-validator.sh]
</git_workflow>

<thinking>
<!-- For complex tasks: guide Claude through reasoning -->
[FOR COMPLEX PHYSICS CALCULATIONS]:
- Verify unit consistency at each step
- Check conservation laws and physical constraints
- Consider numerical stability for extreme parameters
- Validate against literature values or known solutions

[FOR ARCHITECTURE CHANGES]:
- Consider impact on existing functionality
- Plan for backward compatibility
- Identify potential performance implications
- Design for extensibility and maintainability
</thinking>

<examples>
<!-- Include 3-5 relevant examples if needed for complex tasks -->
<example>
# Example 1: [Brief description]
[Show expected input/output pattern]
[Demonstrate physics conventions]
</example>

<example>
# Example 2: [Brief description - show variation]
[Different scenario or edge case]
[Alternative approach or parameter range]
</example>

<!-- Add more examples as needed for complex structured outputs -->
</examples>

<verification>
<!-- How Claude should verify its work -->
1. Physics validation:
   - Run: python .claude/hooks/physics-validation.py
   - Check: Unit consistency throughout calculations
   - Verify: Physical bounds and conservation laws
   - Validate: Against known solar wind parameter ranges

2. Code quality:
   - Run: pytest --cov=solarwindpy (ensure ≥95% coverage)
   - Run: .claude/hooks/test-runner.sh --physics
   - Check: Numerical stability with edge cases
   - Verify: Backward compatibility with existing tests

3. Architecture compliance:
   - Confirm: MultiIndex DataFrame structure maintained
   - Check: Proper use of .xs() for data access
   - Verify: Following existing code patterns and conventions
   - Validate: Integration with specialized agents as appropriate

4. Performance (if applicable):
   - Benchmark: Compare against existing implementation
   - Memory: Monitor peak usage and efficiency
   - Scalability: Test with large datasets (1M+ points)
</verification>
```

## Usage Notes

- **Fill in all bracketed placeholders** with your specific requirements
- **Choose appropriate sections** - not every prompt needs all sections
- **Be specific about physics** - include actual parameter values and ranges when known
- **Reference existing code** - mention similar functionality to maintain consistency
- **Specify the right agent** - each specialized agent has different expertise
- **Include verification steps** - especially important for physics calculations