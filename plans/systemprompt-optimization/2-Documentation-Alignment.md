# Phase 2: Documentation Alignment

## Objectives
- Update CLAUDE.md with comprehensive PR workflow details
- Enhance hook system descriptions to match systemPrompt
- Add agent selection guidelines for immediate productivity

## Tasks

### 2.1 Update CLAUDE.md PR Workflow Section

**Location**: After existing "Git Workflow (Automated via Hooks)" section in CLAUDE.md

**Add New Section**:
```markdown
### PR Workflow & Plan Closeout
Plans are closed via Pull Requests with comprehensive automated checks:

#### Workflow Steps
1. **Complete Implementation**: Finish work on `feature/*` branch
2. **Merge to Plan**: `git checkout plan/<name>` → `git merge feature/<name>`
3. **Create PR**: `gh pr create` from `plan/*` → `master`
4. **Automated Validation**: GitHub Actions automatically execute:
   - **CI Tests**: Python 3.8-3.12 across Ubuntu/macOS/Windows (15 combinations)
   - **Security Scans**: Bandit, Safety, pip-audit for vulnerability detection
   - **Documentation Build**: Sphinx build verification and link checking
   - **Coverage Analysis**: Test coverage reporting and enforcement
5. **Branch Protection**: All checks must pass before merge allowed
6. **Plan Completion**: Merge PR to close plan and deploy to master

#### Claude Integration
- Claude handles PR creation with full awareness of automated checks
- systemPrompt includes CI/security/docs check context
- Hook system enforces PR source branch validation (plan/* only)
- Automated metrics collection for plan completion tracking
```

### 2.2 Enhance Hook System Documentation

**Location**: Replace existing "Automated Validation" section in CLAUDE.md

**Enhanced Hook Descriptions**:
```markdown
### Hook System Details

Hook system provides automatic validation at key interaction points:

#### SessionStart Hook (`validate-session-state.sh`)
- **Purpose**: Validates session context and branch state
- **Actions**: 
  - Checks current branch and suggests plan branches if on master
  - Loads compacted state for active plans
  - Displays recent commits and uncommitted changes
  - Provides workflow guidance
- **User Impact**: Immediate context orientation, no manual setup

#### PreToolUse Hooks
- **Edit/Write/MultiEdit Operations**:
  - **Physics Validation** (`physics-validation.py`): Units consistency, constraint checking
  - **Target**: All Python files in solarwindpy/ directory
  - **Timeout**: 45 seconds for complex validation

- **Bash Git Operations**:
  - **Workflow Validation** (`git-workflow-validator.sh`): Branch protection, PR validation
  - **Target**: All git and gh commands
  - **Blocking**: Prevents invalid operations (commits to master, wrong PR sources)

#### PostToolUse Hooks
- **Edit/Write/MultiEdit**:
  - **Smart Test Runner** (`test-runner.sh --changed`): Runs tests for modified files
  - **Coverage**: Maintains ≥95% coverage requirement
  - **Timeout**: 120 seconds for comprehensive testing

- **Bash Operations**:
  - **Pre-commit Tests** (`pre-commit-tests.sh`): Final validation before commits
  - **Quality Gates**: Ensures all tests pass before git operations

#### PreCompact Hook (`create-compaction.py`)
- **Purpose**: Session state preservation at token boundaries
- **Actions**: Creates compressed session snapshots with git integration
- **Artifacts**: Tagged compaction states for session continuity

#### Stop Hook (`coverage-monitor.py`)
- **Purpose**: Session completion metrics and coverage reporting
- **Actions**: Final coverage analysis, session metrics collection
- **Output**: Detailed reports for continuous improvement
```

### 2.3 Add Agent Selection Guidelines

**Location**: New section in CLAUDE.md after "Common Aliases"

**Agent Selection Quick Reference**:
```markdown
### Agent Selection Quick Reference

Claude Code uses specialized agents for optimal task execution:

#### Primary Coordination
- **UnifiedPlanCoordinator**: Use for ALL planning and implementation coordination
  - Multi-phase project planning
  - Cross-module integration tasks  
  - Plan status tracking and completion

#### Domain Specialists
- **PhysicsValidator**: Physics calculations and scientific validation
  - Unit consistency checking (SI units, thermal speed mw²=2kT)
  - Scientific constraint validation
  - Physics equation verification

- **DataFrameArchitect**: pandas MultiIndex optimization and patterns
  - MultiIndex DataFrame operations (M:measurement/C:component/S:species)
  - Data structure efficiency
  - Memory optimization patterns

- **TestEngineer**: Comprehensive testing strategy and coverage
  - Test design and implementation
  - Coverage analysis and improvement
  - Physics-specific test validation

#### Specialized Functions
- **PlottingEngineer**: Visualization and matplotlib operations
  - Publication-quality figure creation
  - Scientific plotting standards
  - Visual validation of results

- **FitFunctionSpecialist**: Curve fitting and statistical analysis
  - Mathematical function fitting
  - Statistical validation
  - Optimization algorithms

- **NumericalStabilityGuard**: Numerical validation and edge case handling
  - Floating-point precision issues
  - Numerical algorithm stability
  - Edge case validation

#### Usage Examples
```python
# For planning any complex task
"Use UnifiedPlanCoordinator to create implementation plan for dark mode feature"

# For domain-specific work  
"Use PhysicsValidator to verify thermal speed calculations in Ion class"
"Use DataFrameArchitect to optimize MultiIndex operations in Plasma.moments()"
"Use TestEngineer to design test strategy for fitfunctions module"
```
```

### 2.4 Update Development Workflow Section

**Location**: Enhance existing "Git Workflow (Automated via Hooks)" section

**Add PR Context**:
```markdown
#### PR Creation and Management
- **Source Validation**: PRs MUST be created from `plan/*` branches (enforced by hooks)
- **Automated Checks**: CI, security, and documentation checks run automatically
- **Branch Protection**: All checks required to pass before merge
- **Plan Metrics**: Completion metrics automatically recorded
- **Cleanup**: Plan and feature branches preserved for audit trail
```

## Implementation Steps

### Step 1: Backup Current CLAUDE.md
```bash
cp CLAUDE.md CLAUDE.md.backup
```

### Step 2: Apply Documentation Updates
Use the content above to update the specified sections in CLAUDE.md

### Step 3: Verify Alignment
Ensure new documentation aligns with:
- systemPrompt content (agent names, hook descriptions)
- Existing hook implementations
- Current workflow patterns

## Acceptance Criteria
- [ ] CLAUDE.md fully documents PR workflow with automated checks
- [ ] Hook descriptions match systemPrompt context
- [ ] Agent selection guidelines clear and actionable  
- [ ] Documentation aligns with existing infrastructure
- [ ] Examples provided for immediate usability
- [ ] Backup created for rollback

## Benefits of Documentation Alignment
- **Consistency**: systemPrompt and documentation provide same context
- **Completeness**: Full workflow understanding from multiple sources
- **Usability**: Quick reference for agent selection and hook behavior
- **Onboarding**: New users understand system immediately
- **Maintenance**: Single source of truth for workflow changes

## Validation Steps
1. **Cross-Reference Check**: Verify agent names match between systemPrompt and CLAUDE.md
2. **Hook Accuracy**: Ensure hook descriptions reflect actual behavior
3. **Workflow Consistency**: Confirm PR process aligns with git-workflow-validator
4. **Example Validation**: Test that provided examples work as described