# Agent Ecosystem Consolidation (Aug 15, 2025)

**Date:** August 15, 2025
**Status:** Accepted
**Commit:** e4fc96a497262fb1c7274d80b3a697b99049c975

## Context

The SolarWindPy agent system initially grew to 14 agents during the exploration phase (July-August 2025). This created significant context overhead:

- **Agent context size:** 3,895 lines
- **Token burden:** High - agents loaded for every Task tool invocation
- **Redundancy:** Multiple agents handling mechanical/repetitive tasks
- **Hook system:** Introduced comprehensive automation capabilities (6-event system)

The feature integration planning documents (`.claude/docs/feature_integration/03_subagents.md` and `04_enhanced_hooks.md`) identified an opportunity to consolidate the agent system by:

1. Moving repetitive automation to hooks (no AI reasoning needed)
2. Retaining agents requiring domain expertise
3. Consolidating planning agents into unified coordinator

## Decision

**Reduce agent count from 14 to 7 specialized agents (-50%)**

### Agents Removed (6)

**Infrastructure/Automation Agents** (replaced by hooks):
1. **PerformanceOptimizer** - Computational performance profiling and optimization
2. **DocumentationMaintainer** - Sphinx builds, docstring validation, API docs
3. **DependencyManager** - Package dependency and conda recipe management
4. **GitIntegration** - Git operations and workflow management
5. **CompactionAgent** - Agent state compaction

**Planning Agents** (consolidated):
6. **PlanManager** - High-level plan creation
7. **PlanImplementer** - Plan execution
8. **PlanStatusAggregator** - Status tracking and reporting

**Index File:**
9. **agents-index.md** - Central agent registry

### Agents Retained (7)

**Domain Expertise Agents:**
1. **PhysicsValidator** - Solar wind physics validation (HIGH priority)
2. **DataFrameArchitect** - MultiIndex data structure management (HIGH priority)
3. **NumericalStabilityGuard** - Numerical precision and edge cases (HIGH priority)
4. **PlottingEngineer** - Publication-quality visualization (MEDIUM priority)
5. **FitFunctionSpecialist** - Statistical analysis and curve fitting (MEDIUM priority)
6. **TestEngineer** - Domain-specific testing strategies (MEDIUM priority)

**Planning Coordinator:**
7. **UnifiedPlanCoordinator** - Merged planning functionality (HIGH priority)

## Rationale

### Why Remove Infrastructure Agents?

**Hooks system handles repetitive automation more efficiently:**

- **PerformanceOptimizer**: Low-priority maintenance task; manual profiling on-demand is sufficient
- **DocumentationMaintainer**: Documentation work absorbed into general workflow; CI/CD handles builds
- **DependencyManager**: Infrequent updates; manual management via scripts adequate
- **GitIntegration**: Git operations integrated into UnifiedPlanCoordinator
- **CompactionAgent**: Manual compaction workflow sufficient

**Key insight**: These agents performed mechanical tasks that don't benefit from AI reasoning. Hooks provide faster, deterministic automation.

### Why Consolidate Planning Agents?

Original 3-agent planning system (PlanManager, PlanImplementer, PlanStatusAggregator) had overlapping responsibilities:

- **Coordination overhead**: Required inter-agent communication
- **Context duplication**: Shared plan state across multiple agents
- **Single responsibility**: Planning is cohesive enough for one agent

**UnifiedPlanCoordinator** provides:
- Complete planning lifecycle (creation → execution → monitoring)
- GitHub Issues integration
- Velocity intelligence
- Value propositions framework
- Hook integration (plan-value-generator.py, plan-scope-auditor.py)

### Why Retain Domain Agents?

Domain agents leverage AI reasoning for specialized expertise:

- **PhysicsValidator**: Validates complex solar wind physics constraints
- **DataFrameArchitect**: Optimizes MultiIndex patterns requiring pandas knowledge
- **NumericalStabilityGuard**: Identifies numerical edge cases and precision issues
- **PlottingEngineer**: Creates publication-quality scientific visualizations
- **FitFunctionSpecialist**: Designs statistical analysis and fitting strategies
- **TestEngineer**: Develops physics-specific test strategies

These agents require domain knowledge and contextual reasoning that hooks cannot provide.

## Consequences

### Positive

1. **54.4% context reduction** (3,895 → 1,776 lines)
   - Faster agent loading
   - Reduced token usage
   - Improved maintainability

2. **Clearer agent responsibilities**
   - Single agent per domain
   - Unified planning coordinator
   - No overlapping functionality

3. **Automation via hooks**
   - SessionStart: validate-session-state.sh
   - UserPromptSubmit: git-workflow-validator.sh
   - PreToolUse: physics-validation.py, git-workflow-validator.sh
   - PostToolUse: test-runner.sh --changed
   - PreCompact: create-compaction.py
   - Stop: coverage-monitor.py

4. **Improved agent selection**
   - Clear task-to-agent mapping
   - Fewer choices reduce decision fatigue
   - Better documentation in AGENTS.md

### Negative

1. **Manual work for removed agents**
   - Performance optimization on-demand only
   - Documentation updates manual (no automation)
   - Dependency management via scripts

2. **Loss of specialized context**
   - PerformanceOptimizer guidance available only in backup
   - No automated documentation coverage tracking
   - No automated dependency conflict detection

3. **Acceptable trade-offs**
   - These are low-frequency tasks (infrequent need)
   - Manual execution is sufficient for current needs
   - Can resurrect agents if needs change

## Implementation Notes

### Backup Strategy

All removed agents backed up to `.claude/agents.backup/`:
- Full agent definitions preserved
- agents-index.md includes "Planned Agents" section
- Can reference historical agents if needed

### Hook System Architecture

**6 active hooks** (3 future enhancements documented):
- Automated validation (physics, git workflow)
- Test execution after file changes
- Plan value/scope generation
- Session state validation
- Coverage monitoring

### Documentation Updates

- `.claude/docs/AGENTS.md`: Current 7-agent system
- `CLAUDE.md`: Agent selection matrix updated
- `.claude/agents/`: Individual agent specifications
- `.claude/agents.backup/`: Historical archive

## Reversal Criteria

Consider resurrecting agents if:

1. **PerformanceOptimizer**:
   - Performance becomes critical bottleneck
   - Profiling automation provides clear value
   - Manual optimization proves insufficient

2. **DocumentationMaintainer**:
   - Documentation debt accumulates significantly
   - Automated docstring validation needed
   - Sphinx build failures become frequent

3. **DependencyManager**:
   - Dependency conflicts become frequent
   - Complex multi-environment management needed
   - Manual workflow proves error-prone

## Related Documents

- **Strategic planning**: `.claude/docs/feature_integration/03_subagents.md`
- **Hook architecture**: `.claude/docs/feature_integration/04_enhanced_hooks.md`
- **Agent definitions**: `.claude/agents.backup/`
- **Current agents**: `.claude/docs/AGENTS.md`
- **Agent instructions**: `.claude/agents.md`

## Lessons Learned

1. **Validate necessity**: Not all planned agents need implementation
   - 4 agents listed as "Planned" were never built
   - SolarActivityTracker, IonSpeciesValidator, CIAgent, CodeRefactorer
   - Existing capabilities (modules, agents, base Claude Code) proved sufficient

2. **Automation hierarchy**: Choose appropriate automation layer
   - Hooks: Repetitive, deterministic tasks
   - Agents: Domain expertise, contextual reasoning
   - Manual: Infrequent, straightforward tasks

3. **Consolidation benefits**: Fewer specialized agents improves system coherence
   - Reduced context overhead
   - Clearer responsibilities
   - Easier maintenance

4. **Backup preservation**: Keep historical artifacts accessible
   - .backup/ directory for removed agents
   - Documentation of "Planned but not implemented"
   - Enables informed decisions about resurrection

## Metrics

### Before Consolidation
- Agents: 14 (including 3 planning variants)
- Context size: 3,895 lines
- Automation: Agent-based coordination

### After Consolidation
- Agents: 7 (including UnifiedPlanCoordinator)
- Context size: 1,776 lines
- Automation: Hook-based automation + agent expertise

### Reduction
- Agent count: -50% (14 → 7)
- Context size: -54.4% (3,895 → 1,776 lines)
- Token overhead: Significant reduction in agent loading time
