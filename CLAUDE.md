# CLAUDE.md - Essential Claude AI Instructions

This file provides essential guidance to Claude Code when working with the SolarWindPy repository.

## Critical Rules (ALWAYS ENFORCE)
1. **Branch Protection**: Never work on master - always request branch selection first
2. **Script Execution**: Agents MUST execute CLI scripts, never just describe them
3. **Test Before Commit**: All tests must pass before any commit
4. **Follow Conventions**: NumPy docstrings, conventional commits, 'Generated with Claude Code'
5. **Startup Briefing**: Provide project overview including agents, workflows, current state
6. **Prompt Improvement**: For moderate/complex tasks, proactively suggest prompt improvements before execution
7. **Code Attribution**: Follow attribution protocol (.claude/docs/ATTRIBUTION.md)
   - AI-generated code: Include "Generated with Claude Code" in commit messages
   - External sources: Add source attribution in code comments (URL, license, modifications)
   - Scientific algorithms: Cite papers in docstrings (DOI, arXiv, equation numbers)
   - When uncertain: Ask user, prefer reimplementation from scratch

## Context Management Rules
1. **Archive Exclusion**: NEVER search, read, or glob the following compressed archives:
   - `plans/completed-plans-archive-2025.tar.gz` - Historical completed plans (190KB from 976KB)
   - `plans/abandoned-plans-archive-2025.tar.gz` - Historical abandoned plans (72KB from 312KB)
   - `plans/root-stale-docs-archive-2025.tar.gz` - Superseded root documentation (8.7KB from 24KB)
   - `plans/agents-architecture-archive-2025.tar.gz` - Legacy agent architecture (39KB from 156KB)
   - `plans/custom-gpt-archive-2025.tar.gz` - Pre-Claude Code ChatGPT artifacts (6.1KB from 20KB)
   - `plans/completed-plans-minimal-archive-2025.tar.gz` - Additional completed plans (30KB from 120KB)
   - `plans/completed-plans-documentation-archive-2025.tar.gz` - Completed 2025 Q3 documentation/infrastructure plans (190KB from 992KB)
2. **Active Plans Only**: Focus all searches on:
   - Root-level plan files in `plans/` directory (`*.md` files)
   - Active plan subdirectories (not archived)
   - Template and guide files for reference
3. **Active Documentation Preserved**: The following are intentionally NOT archived:
   - `.claude/docs/feature_integration/` - Active implementation phase (256KB)
   - `.claude/ecosystem-documentation.md` - Documents 45KB of active config files
   - `plans/tests-audit/` - Active reference for ongoing test improvements (90KB)
   - `plans/github-issues-migration/` - Active planning system infrastructure documentation (124KB)
4. **Rationale**: Archives contain 536KB compressed from 2,600KB original (79% compression), reducing context noise by ~320,000 tokens while preserving all historical information. Archives are binary files that cannot be read directly; extract only when historical review is necessary.
5. **Archive Access**: To extract archived content if needed:
   ```bash
   tar -xzf plans/root-stale-docs-archive-2025.tar.gz
   tar -xzf plans/agents-architecture-archive-2025.tar.gz
   tar -xzf plans/custom-gpt-archive-2025.tar.gz
   tar -xzf plans/completed-plans-minimal-archive-2025.tar.gz
   tar -xzf plans/completed-plans-documentation-archive-2025.tar.gz
   tar -xzf plans/completed-plans-archive-2025.tar.gz
   tar -xzf plans/abandoned-plans-archive-2025.tar.gz
   ```

## Prompt Improvement Protocol

### When to Analyze Prompts
Provide proactive improvement suggestions for **moderate and complex tasks**:

**Moderate Complexity (2-4 steps):**
- Multi-step workflows with some ambiguity
- Tasks requiring sequential tool use
- Requests that could benefit from more specificity

**Complex Complexity (strategic/multi-domain):**
- Planning, implementation, or architectural tasks
- Multi-phase or multi-module work
- Ambiguous scope requiring interpretation
- Tasks needing agent coordination
- Physics/scientific validation requirements
- Debugging requiring root cause analysis

**Exclude simple tasks:**
- Single file reads or documentation lookups
- Direct git/bash commands (status, log, etc.)
- Single glob/grep operations
- Clear, specific, single-step requests

### Improvement Focus Areas
Analyze prompts for opportunities in all areas:

1. **Clarity & Specificity**
   - Remove ambiguities and undefined scope
   - Add missing requirements or success criteria
   - Specify integration points and module targets

2. **Context & Constraints**
   - Add relevant domain context (physics, data structure)
   - Specify constraints (backward compatibility, performance)
   - Include data format expectations (MultiIndex structure)

3. **SolarWindPy Integration**
   - Suggest appropriate agent selection (PhysicsValidator, DataFrameArchitect, etc.)
   - Reference hooks, workflows, and automation
   - Link to project conventions (≥95% coverage, SI units, etc.)

4. **Efficiency Optimization**
   - Suggest parallel operations where applicable
   - Recommend context-saving approaches
   - Identify opportunities for batch operations

### Improvement Presentation Format
Use structured format for suggestions:

```
📝 Prompt Improvement Suggestion

Original Intent: [Confirm understanding of request]

Suggested Improvements:
- [Specific addition/clarification 1]
- [Specific addition/clarification 2]
- [Agent or workflow suggestion]
- [Missing constraint or context]

Enhanced Prompt Example:
"[Concrete example of improved version]"

Expected Benefits:
- [How improvement enhances execution quality]
- [Reduced ambiguity or better agent selection]
- [Efficiency or context preservation gains]

Proceed with:
[A] Original prompt as-is
[B] Enhanced version
[C] Custom modification (please specify)
```

### Integration with Workflow
- Prompt analysis occurs **before** task execution
- Works naturally with plan mode workflow
- User approves original or enhanced version before proceeding
- Builds better prompting patterns over time

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
- Code attribution guidelines → .claude/docs/ATTRIBUTION.md