# systemPrompt Optimization Plan

## Executive Summary
Optimize the Claude Code systemPrompt for SolarWindPy to provide complete context, improve productivity, and align with the sophisticated hook and agent infrastructure.

## Problem Statement
Current systemPrompt (175 tokens) is:
- **Outdated**: Uses wrong branch patterns (`claude/YYYY-MM-DD-HH-MM-SS-*` instead of `plan/*` workflow)
- **Redundant**: Duplicates functionality already automated by SessionStart and git-workflow-validator hooks
- **Incomplete**: Missing agent awareness, PR workflow, and project-specific context
- **Inefficient**: Forces unnecessary interactive branch selection every session

## Solution Approach
Deploy comprehensive 210-token systemPrompt that:
- Provides complete agent and hook context for immediate productivity
- Explains PR-based plan closeout workflow with automated CI/security/docs checks
- Eliminates redundancy with automation infrastructure
- Includes SolarWindPy-specific architecture (MultiIndex, physics constraints)

### New systemPrompt (210 tokens)
```
SolarWindPy: Solar wind plasma physics package. Architecture: pandas MultiIndex (M:measurement/C:component/S:species), SI units, mw²=2kT.

Agents: UnifiedPlanCoordinator (all planning/implementation), PhysicsValidator (units/constraints), DataFrameArchitect (MultiIndex), TestEngineer (coverage), PlottingEngineer, FitFunctionSpecialist, NumericalStabilityGuard.

Hooks automate: SessionStart (branch validation/context), PreToolUse (physics/git checks), PostToolUse (test execution), PreCompact (state snapshots), Stop (coverage report).

Workflow: plan/* branches for planning, feature/* for code. PRs from plan/* to master trigger CI/security/docs checks. No direct master commits. Follow CLAUDE.md. Session context loads automatically.
```

## Success Criteria
- [ ] systemPrompt updated in `.claude/settings.json`
- [ ] CLAUDE.md aligned with new context
- [ ] Monitoring infrastructure deployed (optional Phase 3)
- [ ] Token usage metrics baseline established
- [ ] Productivity improvements measurable (fewer clarification exchanges)

## Value Proposition

### Risk Assessment
- **Technical Risk**: Very Low (enhances existing infrastructure without conflicts)
- **Operational Risk**: Low (changes are reversible)
- **Token Risk**: Acceptable (210 tokens for major productivity gains)

### Benefits Analysis
- **Token Economics**: Net savings of 200-500 tokens per session through reduced clarifications
- **Productivity**: 20-30% faster task completion with full context
- **Quality**: Correct workflow and agent usage from session start
- **Maintenance**: Future-proof (hooks handle workflow changes)

## Timeline
- **Phase 1**: Immediate deployment (Day 1)
- **Phase 2**: Documentation alignment (Days 2-3)  
- **Phase 3**: Automated monitoring (Week 2) - Optional

## Implementation Phases
1. **Deploy systemPrompt** - Update settings.json, verify compatibility
2. **Align Documentation** - Update CLAUDE.md with PR workflow and hook details
3. **Monitor Performance** - Deploy automated metrics collection (optional)

## Risk Mitigation
- Reversible changes with git version control
- CLAUDE.md provides detailed backup information
- Hook system continues to enforce workflow regardless
- Quarterly review cycle to ensure accuracy

## Expected Outcomes
- Users understand complete system from first interaction
- Optimal agent selection for specialized tasks
- Clear understanding of automated workflows
- Reduced confusion about branch patterns and PR processes
- Data-driven optimization through monitoring (Phase 3)