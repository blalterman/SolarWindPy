# CLAUDE.md - Essential Claude AI Instructions

This file provides essential guidance to Claude Code when working with the SolarWindPy repository.

## Critical Rules (ALWAYS ENFORCE)
1. **Branch Protection**: Never work on master - always request branch selection first
2. **Script Execution**: Agents MUST execute CLI scripts, never just describe them
3. **Test Before Commit**: All tests must pass before any commit
4. **Follow Conventions**: NumPy docstrings, conventional commits, 'Generated with Claude Code'
5. **Startup Briefing**: Provide project overview including agents, workflows, current state

## Quick Reference

### Agent Selection Matrix
| Task Type | Agent | Critical Requirement |
|-----------|-------|---------------------|
| Planning | UnifiedPlanCoordinator | MUST execute gh-plan-*.sh scripts directly |
| Physics | PhysicsValidator | Verify units, constraints, thermal speed |
| Data | DataFrameArchitect | MultiIndex (M/C/S), use .xs() for views |
| Numerical | NumericalStabilityGuard | Edge cases, precision |
| Plotting | PlottingEngineer | Publication quality, matplotlib |
| Fitting | FitFunctionSpecialist | Statistical analysis |
| Testing | TestEngineer | ≥95% coverage requirement |

### Critical Workflow Paths
```
GitHub Issues → feature/* → PR → master
Plan Creation → gh-plan-create.sh → gh-plan-phases.sh → Value Props
File Edit → Physics Hook → Test Runner Hook → Coverage Check
```

## Essential Commands (EXACT SYNTAX REQUIRED)

### Plan Creation
```bash
# Create overview with required flags
.claude/scripts/gh-plan-create.sh -p <priority> -d <domain> "Plan Title"
# priority: critical|high|medium|low  
# domain: physics|data|plotting|testing|infrastructure|docs

# Example:
.claude/scripts/gh-plan-create.sh -p high -d infrastructure "API Refactoring"
```

### Phase Creation (UnifiedPlanCoordinator MUST use batch mode)
```bash
# Step 1: Create config in repo tmp/
mkdir -p tmp
cat > tmp/phases.conf <<'EOF'
Phase Name|Estimated Duration|Dependencies
Foundation Setup|2-3 hours|None
Core Implementation|4-5 hours|Phase 1
Testing & Validation|1-2 hours|Phase 2
EOF

# Step 2: Execute batch mode
.claude/scripts/gh-plan-phases.sh -b tmp/phases.conf <issue_number>
```

### Testing & Quality
```bash
.claude/hooks/test-runner.sh --changed     # Test changed files only
.claude/hooks/test-runner.sh --physics     # Physics validation
pytest -q                                   # Quick test run
black solarwindpy/ tests/                  # Format code
flake8 solarwindpy/ tests/                 # Lint check
```

## Project Architecture Summary
- **Core Data Model**: MultiIndex DataFrame (M: measurement, C: component, S: species)
- **Key Classes**: Plasma (container), Ion (species), Base (abstract)
- **Hook System**: Automated validation at .claude/hooks/
- **Plan System**: GitHub Issues with value propositions framework
- **Coverage**: ≥95% required, enforced by pre-commit

## UnifiedPlanCoordinator Execution Protocol

CRITICAL: Agent MUST execute these commands, not describe them.

1. **Overview Issue Creation:**
   ```bash
   .claude/scripts/gh-plan-create.sh -p <priority> -d <domain> "Title"
   ```

2. **Phase Issues Creation:**
   ```bash
   mkdir -p tmp
   cat > tmp/phases.conf <<'EOF'
   <phase_name>|<duration>|<dependencies>
   EOF
   .claude/scripts/gh-plan-phases.sh -b tmp/phases.conf $OVERVIEW_ISSUE
   ```

3. **Validation**: If text output instead of GitHub Issues → EXECUTION FAILED

## Detailed Documentation
For comprehensive information beyond these essentials:
- Development standards → .claude/docs/DEVELOPMENT.md
- Agent specifications → .claude/docs/AGENTS.md  
- Hook reference → .claude/docs/HOOKS.md
- Planning workflow → .claude/docs/PLANNING.md
- Maintenance → .claude/docs/MAINTENANCE.md