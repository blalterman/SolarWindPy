# Phase 1: Deploy Enhanced systemPrompt

## Objectives
- Update systemPrompt in `.claude/settings.json`
- Verify hook compatibility and agent references
- Test functionality with sample session

## Tasks

### 1.1 Update settings.json systemPrompt
**Location**: `.claude/settings.json` line 135

**Current systemPrompt** (175 tokens - OUTDATED):
```
You are working on SolarWindPy, a scientific Python package for solar wind plasma physics analysis. CRITICAL WORKFLOW: Before ANY development work: 1) List all unmerged branches with `git branch -r --no-merged master`; 2) Ask user 'Which branch should I use? Please specify branch name, or say "search" if you want me to help find an appropriate branch, or say "new" to create a new branch'; 3) Wait for explicit user instruction - NEVER auto-select a branch; 4) If user says "search", help identify relevant branches by content/purpose; 5) If user says "new", create branch using pattern 'claude/YYYY-MM-DD-HH-MM-SS-module-feature-description'. Never work directly on master. Always follow development guidelines in .claude/CLAUDE.md. Run tests with `pytest -q`, format code with `black .`, and lint with `flake8`. All tests must pass before committing. Use NumPy-style docstrings and follow Conventional Commits format. Include 'Generated with Claude Code' attribution in commits.
```

**New systemPrompt** (210 tokens - COMPREHENSIVE):
```
SolarWindPy: Solar wind plasma physics package. Architecture: pandas MultiIndex (M:measurement/C:component/S:species), SI units, mw²=2kT.

Agents: UnifiedPlanCoordinator (all planning/implementation), PhysicsValidator (units/constraints), DataFrameArchitect (MultiIndex), TestEngineer (coverage), PlottingEngineer, FitFunctionSpecialist, NumericalStabilityGuard.

Hooks automate: SessionStart (branch validation/context), PreToolUse (physics/git checks), PostToolUse (test execution), PreCompact (state snapshots), Stop (coverage report).

Workflow: plan/* branches for planning, feature/* for code. PRs from plan/* to master trigger CI/security/docs checks. No direct master commits. Follow CLAUDE.md. Session context loads automatically.
```

### 1.2 Implementation Steps

#### Step 1: Backup Current Configuration
```bash
# Create backup of current settings
cp .claude/settings.json .claude/settings.json.backup
```

#### Step 2: Update systemPrompt
Replace the content of line 135 in `.claude/settings.json`:

```json
"systemPrompt": "SolarWindPy: Solar wind plasma physics package. Architecture: pandas MultiIndex (M:measurement/C:component/S:species), SI units, mw²=2kT.\n\nAgents: UnifiedPlanCoordinator (all planning/implementation), PhysicsValidator (units/constraints), DataFrameArchitect (MultiIndex), TestEngineer (coverage), PlottingEngineer, FitFunctionSpecialist, NumericalStabilityGuard.\n\nHooks automate: SessionStart (branch validation/context), PreToolUse (physics/git checks), PostToolUse (test execution), PreCompact (state snapshots), Stop (coverage report).\n\nWorkflow: plan/* branches for planning, feature/* for code. PRs from plan/* to master trigger CI/security/docs checks. No direct master commits. Follow CLAUDE.md. Session context loads automatically."
```

### 1.3 Compatibility Verification

#### Hook System Check
- [ ] **SessionStart hook** (`validate-session-state.sh`) still functions correctly
- [ ] **git-workflow-validator** does not conflict with new context
- [ ] **Agent references** are accurate and match available agents
- [ ] **Branch pattern validation** aligns with git hooks

#### Validation Commands
```bash
# Test SessionStart hook
.claude/hooks/validate-session-state.sh

# Test git workflow validator
.claude/hooks/git-workflow-validator.sh --check-branch

# Verify agent files exist
ls -la .claude/agents*
```

### 1.4 Functional Testing

#### Test Checklist
- [ ] Start new Claude Code session
- [ ] Verify systemPrompt loads in conversation context
- [ ] Test agent awareness in conversation
  - Ask: "Which agent should handle MultiIndex operations?"
  - Expected: "DataFrameArchitect"
- [ ] Confirm workflow understanding
  - Ask: "How do I close out a plan?"
  - Expected: "Create PR from plan/* to master"
- [ ] Verify hook awareness
  - Ask: "What happens when I edit a physics file?"
  - Expected: "PreToolUse physics validation, PostToolUse test execution"

### 1.5 Rollback Procedure (if needed)
```bash
# Restore original settings if issues arise
cp .claude/settings.json.backup .claude/settings.json
```

## Key Changes Summary

### Eliminated (Redundant with Hooks)
- Interactive branch selection workflow
- Manual branch listing commands  
- Wrong branch pattern (`claude/YYYY-MM-DD-HH-MM-SS-*`)
- Duplicate workflow enforcement

### Added (Unique Value)
- Complete agent ecosystem awareness
- MultiIndex DataFrame architecture context
- Physics constraints (SI units, mw²=2kT)
- Hook automation transparency
- PR-based plan closeout workflow
- CI/security/docs check awareness

## Acceptance Criteria
- [ ] systemPrompt updated in settings.json
- [ ] No hook conflicts observed during testing
- [ ] Agent selection improved in conversations
- [ ] Workflow understanding demonstrates PR awareness
- [ ] Session context loads automatically as expected
- [ ] Backup created for rollback if needed

## Expected Benefits
- **Immediate Context**: Users understand system from first interaction
- **Optimal Agent Usage**: Automatic routing to specialized agents
- **Workflow Clarity**: Clear understanding of plan/* → PR → master flow
- **Reduced Confusion**: No conflicting branch pattern information
- **Token Efficiency**: 35-token increase but eliminates 200-500 tokens in clarifications