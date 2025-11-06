# Slash Commands

**Feature Type:** Manual
**Priority:** HIGH
**Effort:** 5.5-8 hours
**ROI Break-even:** 3-4 weeks

[← Back to Index](./INDEX.md) | [← Previous: Output Styles](./06_output_styles.md)

---

**✅ OFFICIAL PLUGIN FEATURE - Native Support**

Slash commands are officially supported as plugin components (plugin-name/commands/).
See: [Plugin Packaging](./08_plugin_packaging.md#slash-commands)

---

## Executive Summary

Slash commands are **user-invoked prompt shortcuts** that complement the automatic Skills system. While Skills activate automatically based on context, slash commands provide **explicit control** for frequently-repeated workflows where you want deterministic triggering.

### Quick Comparison: Slash Commands vs Skills

| Aspect | Slash Commands | Skills |
|--------|---------------|--------|
| **Invocation** | Manual (`/command`) | Automatic (context-based) |
| **Control** | Explicit, deterministic | Probabilistic (85%+ accuracy) |
| **Complexity** | Single markdown file | Multi-file with scripts/templates |
| **Use Case** | Frequent manual workflows | Automatic workflow integration |
| **Best For** | "I want to run this NOW" | "Claude should detect when to do this" |

### Relevance to SolarWindPy

✅ **HIGHLY RELEVANT** for:
- Frequently-repeated physics validation checks you want to trigger manually
- Quick access to testing workflows (coverage, physics-specific tests)
- Plan creation workflows (explicit invocation preferred over automatic)
- Code review checklists (run on-demand, not automatically)
- Git workflow helpers (branch creation, commit message templates)

---

## Feature Overview

### What Slash Commands Are

User-invoked prompt shortcuts stored as markdown files in `.claude/commands/` (project) or `~/.claude/commands/` (personal). When you type `/command-name`, Claude expands the content as if you typed it manually.

### Core Capabilities

- **Arguments:** `$ARGUMENTS` (all), `$1`, `$2` (positional)
- **Bash execution:** Prefix with `!` to run shell commands
- **File references:** `@path/to/file` includes file contents
- **Frontmatter metadata:** `description`, `allowed-tools`, `model`, character budget
- **Three storage tiers:** Project (`.claude/commands/`), Personal (`~/.claude/commands/`), Plugin-based

### Technical Constraints

- Filename becomes command name (`.claude/commands/review.md` → `/review`)
- Supports YAML frontmatter (optional)
- Can execute bash commands with `!` prefix
- SlashCommand tool allows Claude to invoke programmatically

### Current SolarWindPy Usage

❌ **No slash commands defined yet** - Opportunity to add high-value commands

---

## Value Proposition

### Pain Points Addressed

✅ **Repetitive Task Automation (HIGH IMPACT)**
*Current state:* Manually typing long prompts for common workflows (coverage check, physics validation, plan creation)
*With Slash Commands:* `/coverage`, `/physics`, `/plan` trigger full workflows
*Time savings:* 2-5 minutes per invocation × 10-20 times/week = **20-100 min/week**

✅ **Plan Execution Efficiency (MEDIUM-HIGH IMPACT)**
*Current state:* Manual GitHub Issues plan creation with long script paths
*With Slash Commands:* `/plan-create`, `/plan-phases`, `/plan-status` for instant access
*Improvement:* Zero cognitive overhead for planning workflow

✅ **Context Preservation (MEDIUM IMPACT)**
*Current state:* Repeated explanations of testing requirements, review criteria
*With Slash Commands:* Standardized templates ensure consistency
*Benefit:* Consistent quality, no forgotten checklist items

✅ **Agent Coordination (LOW-MEDIUM IMPACT)**
*Current state:* Manually crafting agent invocation prompts
*With Slash Commands:* Pre-defined agent workflows (`/validate-physics`, `/optimize-dataframes`)
*Improvement:* Faster, more accurate agent delegation

### Productivity Improvements

- **Instant access** to common workflows (no typing, no memory recall)
- **Consistency** through standardized templates
- **Reduced errors** (checklists ensure completeness)
- **Faster onboarding** (team members discover commands via `/help`)

### Research Workflow Enhancements

- Quick physics validation checks during development
- Standardized code review process
- Consistent testing procedures
- Streamlined plan management

---

## Integration Strategy

### Architecture Fit

Slash commands complement existing SolarWindPy infrastructure:

```
Automation Continuum:

Manual Workflow
├── Type full prompt
├── 🆕 Slash Command (/command) ← Explicit user trigger
├── Skill (auto-activates) ← Claude detects context
└── Hook (event-based) ← Automatic on tool use

Decision Matrix:
- Want explicit control? → Slash Command
- Want automatic activation? → Skill
- Trigger on events? → Hook
```

### Relationship to Existing Systems

| System Component | Integration Approach |
|------------------|---------------------|
| **Skills** | Commands for explicit control; Skills for automatic |
| **Agents** | Commands can invoke specific agents (e.g., `/validate-physics` → PhysicsValidator) |
| **Hooks** | Commands can trigger hook-checked workflows |
| **Scripts** | Commands can execute `.claude/scripts/*.sh` with bash prefix |
| **Memory** | Commands reference memory files via `@.claude/memory/...` |
| **GitHub Issues** | Commands streamline plan creation workflow |

### When to Use Slash Commands vs Skills

**Use Slash Command when:**
- ✅ You want **explicit control** over when it runs
- ✅ It's a **frequent manual workflow** (run 5+ times/week)
- ✅ You need **immediate invocation** (not context-dependent)
- ✅ It's a **team-shared template** everyone should use

**Use Skill when:**
- ✅ Claude should **automatically detect** when to activate
- ✅ It's part of **continuous workflow** (not discrete manual task)
- ✅ Requires **multi-file organization** (scripts, templates)
- ✅ Activation accuracy is more important than explicit control

**Examples:**
- `/coverage` (Slash Command - manual check on-demand)
- `physics-validator` (Skill - auto-activates during calculations)
- `/review` (Slash Command - explicit code review request)
- `test-generator` (Skill - auto-activates when coverage drops)

### Backward Compatibility

✅ **Fully compatible** - Slash commands are additive
✅ **No migration needed** - Start with zero, add incrementally
✅ **Coexists with everything** - Skills, hooks, agents unchanged

### Risk Assessment

#### Technical Risks

**Risk: Command Name Conflicts**
- **Likelihood:** Low
- **Impact:** Medium (command overwrites built-in or plugin command)
- **Mitigation:**
  - Check existing commands with `/help` before creating new
  - Use descriptive, SolarWindPy-specific names
  - Namespace with prefix if publishing: `swpy-coverage`, `swpy-physics`
  - Document command inventory in CLAUDE.md
  - Test for conflicts after adding new commands

**Risk: Bash Execution Security**
- **Likelihood:** Low
- **Impact:** High (malicious commands if sharing plugins)
- **Mitigation:**
  - Review all `!` bash executions in commands
  - Avoid user-controlled input in bash execution
  - Test commands in safe environment first
  - Document security guidelines for custom commands
  - Trust chain: Only use project commands from trusted sources

**Risk: Command Maintenance Drift**
- **Likelihood:** Medium
- **Impact:** Medium (outdated commands cause confusion/errors)
- **Mitigation:**
  - Include commands in code review process
  - Test commands as part of CI/CD
  - Version control in git
  - Schedule quarterly command audit
  - Document command dependencies clearly

**Risk: Plugin Distribution of Local-Only Commands**
- **Likelihood:** Low-Medium
- **Impact:** Low (commands work locally but fail in plugins)
- **Mitigation:**
  - Use relative paths from project root
  - Avoid absolute paths (`/Users/...`)
  - Test commands in different project structures
  - Document any local dependencies
  - Provide installation instructions for plugin users

#### Adoption Risks

**Risk: Command Name Recall Difficulty**
- **Likelihood:** Medium
- **Impact:** Low (use regular prompts instead)
- **Mitigation:**
  - Use intuitive, descriptive names (`/coverage`, `/test`, `/physics`)
  - Keep commands short (≤15 characters)
  - Create quick reference card
  - Document all commands in CLAUDE.md
  - Use `/help` to list available commands

**Risk: Over-Creation of Similar Commands**
- **Likelihood:** Medium
- **Impact:** Low-Medium (namespace pollution, confusion)
- **Mitigation:**
  - Limit to 10-15 high-value commands initially
  - Consolidate similar functionality
  - Use arguments instead of separate commands (`/test $1` vs `/test-physics`, `/test-all`)
  - Review command library monthly
  - Deprecate redundant commands

**Risk: Team Unfamiliarity with Slash Commands**
- **Likelihood:** Low
- **Impact:** Low (miss productivity boost)
- **Mitigation:**
  - Include in onboarding documentation
  - Demo commands in team sessions
  - Create cheat sheet
  - Encourage experimentation
  - Celebrate command usage wins

#### Performance Risks

**Risk: Long-Running Bash Commands Block Workflow**
- **Likelihood:** Low-Medium
- **Impact:** Medium (user waits for command completion)
- **Mitigation:**
  - Keep bash commands under 5 seconds
  - Use background processes for slow operations (test suites)
  - Provide progress indicators where possible
  - Timeout commands (set reasonable limits)
  - Document expected execution times

**Risk: Complex Commands Hard to Debug**
- **Likelihood:** Low
- **Impact:** Medium (command fails, unclear why)
- **Mitigation:**
  - Add error handling to bash scripts
  - Log command execution details
  - Provide clear error messages
  - Test commands independently
  - Document troubleshooting steps

---

## Implementation Specification

### Proposed Slash Commands Library

We recommend **10 high-value slash commands** organized into 5 categories:

#### Category 1: Testing & Quality (3 commands)

##### 1. `/coverage` - Quick Coverage Check

**File:** `.claude/commands/coverage.md`

```yaml
---
description: Run pytest with coverage report and identify gaps below 95%
allowed-tools: [Bash]
---

Run the full test suite with coverage analysis and report any modules below 95% threshold.

Steps:
1. Run: `pytest --cov=solarwindpy --cov-report=term -q`
2. Parse coverage output
3. List any modules below 95% coverage
4. Suggest which files need more test coverage
5. Optionally run: `python .claude/scripts/generate-test.py` for low-coverage files

Format output as:
- ✅ Modules at ≥95%
- ⚠️ Modules below 95% (with percentage)
- 💡 Suggestions for improving coverage
```

**Usage:** `/coverage`
**Frequency:** 10-15 times/week
**Time saved:** 2-3 min/invocation

##### 2. `/physics` - Physics Validation Check

**File:** `.claude/commands/physics.md`

```yaml
---
description: Run physics validation on changed files or specified paths
allowed-tools: [Bash, Read, Grep]
---

Validate solar wind physics correctness in the codebase.

Arguments:
- If `$ARGUMENTS` provided: Run on specified files
- If empty: Run on recently changed files (git diff)

Validation checklist:
1. Run: `python .claude/hooks/physics-validation.py $ARGUMENTS`
2. Check thermal speed formula: mw² = 2kT (NOT 3kT)
3. Verify SI units: m/s, m⁻³, K, T
4. Ensure NaN for missing data (not 0, -999)
5. Validate physical constraints (positive densities, temperatures)

Report format:
- ✅ Physics correctness verified
- ❌ Issues found (with file:line references)
- 💡 Recommendations
```

**Usage:**
- `/physics` (validate changed files)
- `/physics solarwindpy/core/ion.py` (validate specific file)

**Frequency:** 8-12 times/week
**Time saved:** 3-5 min/invocation

##### 3. `/test` - Smart Test Runner

**File:** `.claude/commands/test.md`

```yaml
---
description: Run tests with smart mode selection (changed, physics, fast, all)
allowed-tools: [Bash]
---

Run tests using the test-runner.sh hook with intelligent mode selection.

Arguments:
- `$1`: Mode (changed|physics|fast|all|coverage) - default: changed

Execute:
!.claude/hooks/test-runner.sh --$1

Modes:
- **changed**: Test only modified files (fastest)
- **physics**: Physics validation tests only
- **fast**: Quick smoke test run
- **all**: Complete test suite
- **coverage**: Full suite with detailed coverage report

After tests complete:
- Report pass/fail status
- Show any test failures with details
- Suggest fixes if failures detected
```

**Usage:**
- `/test` (test changed files)
- `/test physics` (physics validation tests)
- `/test coverage` (full coverage report)

**Frequency:** 15-20 times/week
**Time saved:** 1-2 min/invocation

#### Category 2: Code Review (2 commands)

##### 4. `/review` - Code Review Checklist

**File:** `.claude/commands/review.md`

```yaml
---
description: Perform comprehensive code review using SolarWindPy standards
allowed-tools: [Read, Grep, Bash]
---

Conduct systematic code review using SolarWindPy quality standards.

If `$ARGUMENTS` provided: Review specified files
If empty: Review files in current git diff

Review Checklist:

**1. Physics Correctness (CRITICAL)**
- [ ] Thermal speed: mw² = 2kT ✓
- [ ] SI units: m/s, m⁻³, K, T ✓
- [ ] NaN for missing data ✓
- [ ] Physical constraints valid ✓

**2. Test Coverage (REQUIRED)**
- [ ] Test coverage ≥95% ✓
- [ ] Physics validation tests included ✓
- [ ] Edge cases covered ✓
- [ ] Error handling tested ✓

**3. DataFrame Best Practices**
- [ ] Use .xs() for MultiIndex cross-sections ✓
- [ ] Avoid chained indexing ✓
- [ ] No unnecessary copies ✓
- [ ] Memory-efficient patterns ✓

**4. Documentation**
- [ ] NumPy-style docstrings ✓
- [ ] Parameters and returns documented ✓
- [ ] Examples included for public API ✓
- [ ] Units specified in docstrings ✓

**5. Code Quality**
- [ ] Black formatted (88 char line length) ✓
- [ ] Flake8 passes ✓
- [ ] No magic numbers (use named constants) ✓
- [ ] Type hints where appropriate ✓

Report findings with:
- ✅ Approved items
- ⚠️ Warnings (should fix)
- ❌ Blockers (must fix before merge)
- 💡 Suggestions (optional improvements)
```

**Usage:**
- `/review` (review current changes)
- `/review solarwindpy/core/plasma.py` (review specific file)

**Frequency:** 5-8 times/week
**Time saved:** 5-10 min/invocation

##### 5. `/refactor` - Refactoring Assistant

**File:** `.claude/commands/refactor.md`

```yaml
---
description: Guide systematic refactoring with safety checklist and testing
allowed-tools: [Read, Edit, Write, Bash]
---

Assist with safe refactoring following SolarWindPy best practices.

Target: $ARGUMENTS (required - specify what to refactor)

Refactoring Protocol:

**Phase 1: Analysis**
1. Read target code
2. Identify refactoring opportunities:
   - Code duplication (DRY violations)
   - Complex functions (>50 lines)
   - Poor naming
   - DataFrame inefficiencies
   - Missing abstractions

**Phase 2: Safety Checks**
1. Verify test coverage ≥95% exists
2. Run tests to establish baseline: `pytest -q`
3. Note current test status

**Phase 3: Refactoring**
1. Make incremental changes
2. Run tests after EACH change
3. Ensure physics correctness maintained
4. Preserve backward compatibility

**Phase 4: Validation**
1. Run full test suite: `pytest --cov=solarwindpy -q`
2. Verify coverage still ≥95%
3. Run physics validation: `python .claude/hooks/physics-validation.py`
4. Check performance (if applicable)

**Phase 5: Review**
1. Show before/after comparison
2. List improvements made
3. Confirm no regressions
4. Suggest commit message

Output refactoring plan BEFORE making changes, wait for approval.
```

**Usage:** `/refactor solarwindpy/core/ion.py:thermal_speed()`

**Frequency:** 3-5 times/week
**Time saved:** 10-15 min/invocation

#### Category 3: Planning (3 commands)

##### 6. `/plan-create` - Create GitHub Issues Plan

**File:** `.claude/commands/plan-create.md`

```yaml
---
description: Create GitHub Issues overview plan with value propositions
allowed-tools: [Bash]
---

Create a new GitHub Issues plan using gh-plan-create.sh with full value propositions framework.

Required arguments: $1 (priority), $2 (domain), $3+ (plan title)

Priority: critical|high|medium|low
Domain: physics|data|plotting|testing|infrastructure|docs

Execute:
!.claude/scripts/gh-plan-create.sh -p $1 -d $2 "$3"

The script will:
1. Create overview issue with plan title
2. Auto-generate value propositions (via hooks):
   - 📊 Value Proposition Analysis
   - 💰 Resource & Cost Analysis
   - ⚠️ Risk Assessment & Mitigation
   - 🔒 Security Proposition
   - 🎯 Scope Audit (≥80/100 required)
   - 💾 Token Usage Optimization
   - ⏱️ Time Investment Analysis
   - 🎯 Usage & Adoption Metrics
3. Return issue number for phase creation

After creation:
- Display issue URL
- Show issue number
- Suggest: "Use /plan-phases <issue_number> to add phases"
```

**Usage:** `/plan-create high infrastructure "Dark Mode Implementation"`

**Frequency:** 2-4 times/week
**Time saved:** 5-10 min/invocation

##### 7. `/plan-phases` - Add Plan Phases

**File:** `.claude/commands/plan-phases.md`

```yaml
---
description: Add phase issues to existing plan using batch mode
allowed-tools: [Bash, Write]
---

Add implementation phases to an existing GitHub Issues plan.

Required argument: $1 (overview issue number)

Interactive workflow:
1. Ask user for phases (one per line in format: "Phase Name|Duration|Dependencies")
2. Create temporary config file: `tmp/phases.conf`
3. Execute: `!.claude/scripts/gh-plan-phases.sh -b tmp/phases.conf $1`
4. Clean up: `!rm -f tmp/phases.conf`

Phase format:
```
Phase Name|Estimated Duration|Dependencies
Foundation Setup|2-3 hours|None
Core Implementation|4-5 hours|Phase 1
Testing & Validation|1-2 hours|Phase 2
```

Example interaction:
> Please provide phases (format: Name|Duration|Dependencies):
>
> Foundation Setup|2-3 hours|None
> Core Implementation|4-5 hours|Phase 1
> Testing|1-2 hours|Phase 2
> [empty line to finish]

After creation:
- List all created phase issues with numbers
- Display plan overview URL
- Suggest: "Use /plan-status to monitor progress"
```

**Usage:** `/plan-phases 123`

**Frequency:** 2-4 times/week
**Time saved:** 5-8 min/invocation

##### 8. `/plan-status` - Show Plan Status

**File:** `.claude/commands/plan-status.md`

```yaml
---
description: Display status of all active GitHub Issues plans
allowed-tools: [Bash]
---

Show comprehensive status of all active plans using gh-plan-status.sh.

Execute:
!.claude/scripts/gh-plan-status.sh

The script displays:
- All overview issues (plan/* branches or plan: label)
- Phase completion status
- Current active plan branches
- Suggested next actions

Format output to show:
1. **Active Plans** (overview issues)
   - Issue #, title, priority, domain
   - Completion percentage
   - Last updated

2. **Plan Branches**
   - Branch names (plan/*)
   - Associated issue numbers
   - Status (ahead/behind master)

3. **Recommendations**
   - Which plan to continue
   - Stale plans to close
   - Branches to merge or delete
```

**Usage:** `/plan-status`

**Frequency:** 5-10 times/week
**Time saved:** 1-2 min/invocation

#### Category 4: Git Workflow (2 commands)

##### 9. `/commit` - Smart Commit Helper

**File:** `.claude/commands/commit.md`

```yaml
---
description: Create well-formatted commit with conventional commits and co-author
allowed-tools: [Bash, Read]
---

Create a properly formatted git commit following SolarWindPy conventions.

Workflow:
1. Run: `!git status` to show changes
2. Run: `!git diff` to review modifications
3. Analyze changes and suggest commit type:
   - **feat**: New feature
   - **fix**: Bug fix
   - **docs**: Documentation only
   - **test**: Adding tests
   - **refactor**: Code change (no behavior change)
   - **perf**: Performance improvement
   - **chore**: Maintenance (deps, config)

4. Draft commit message format:
```
<type>(<scope>): <description>

[Optional body with details]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

5. Ask user to confirm or modify
6. Execute commit with heredoc format

Show commit message preview BEFORE committing.
Wait for explicit approval.
```

**Usage:** `/commit`

**Frequency:** 8-15 times/week
**Time saved:** 2-3 min/invocation

##### 10. `/branch` - Smart Branch Creation

**File:** `.claude/commands/branch.md`

```yaml
---
description: Create appropriately named feature or plan branch
allowed-tools: [Bash]
---

Create a new git branch following SolarWindPy naming conventions.

Arguments: $1 (type), $2+ (description)

Branch Types:
- **feature**: feature/description-here
- **fix**: fix/description-here
- **plan**: plan/description-here
- **test**: test/description-here
- **refactor**: refactor/description-here

Steps:
1. Verify on master: `!git branch --show-current`
2. If not on master, ask: "Currently on {branch}. Switch to master first? (y/n)"
3. Pull latest: `!git pull origin master`
4. Create branch: `!git checkout -b $1/$2`
5. Confirm creation
6. If plan branch: Suggest "Use /plan-create to create associated GitHub Issue"

Safety checks:
- Don't create from master if uncommitted changes exist
- Validate branch name format (lowercase, hyphens, no spaces)
```

**Usage:**
- `/branch feature dark-mode-implementation`
- `/branch plan cicd-architecture-redesign`

**Frequency:** 3-6 times/week
**Time saved:** 1-2 min/invocation

---

## Usage Patterns & Examples

### Pattern 1: Daily Development Workflow

```bash
# Morning: Check status
/plan-status

# Start work on plan
/branch feature api-refactoring

# During development
/physics solarwindpy/core/ion.py  # Validate physics
/test changed                      # Quick test run
/coverage                          # Check coverage

# Before commit
/review                            # Code review checklist
/commit                            # Create formatted commit
```

**Time saved:** ~15-20 minutes/day

### Pattern 2: Code Review Workflow

```bash
# Reviewer checks out PR
git checkout feature/new-calculation

# Run comprehensive review
/review

# Check tests
/test all
/coverage

# Physics validation
/physics

# Provide feedback or approve
```

**Time saved:** ~10-15 minutes/review

### Pattern 3: Planning Workflow

```bash
# Check current plans
/plan-status

# Create new plan
/plan-create high physics "Improve Thermal Speed Calculation"
# Returns: Issue #145

# Add phases
/plan-phases 145
> Foundation Setup|2-3 hours|None
> Core Implementation|4-5 hours|Phase 1
> Testing|1-2 hours|Phase 2

# Create branch
/branch plan thermal-speed-refactor
```

**Time saved:** ~10-15 minutes/plan

### Pattern 4: Refactoring Workflow

```bash
# Identify refactoring target
/review solarwindpy/core/plasma.py

# Plan refactoring
/refactor solarwindpy/core/plasma.py:calculate_density()

# After refactoring
/test all
/physics
/coverage

# Commit
/commit
```

**Time saved:** ~15-20 minutes/refactoring session

---

## Migration Path

### Phase 1: Core Commands (Week 1)

Create highest-value commands first:

1. **Testing commands** (3): `/coverage`, `/physics`, `/test`
2. **Planning commands** (3): `/plan-create`, `/plan-phases`, `/plan-status`

**Effort:** 3-4 hours
**Immediate value:** 30-60 min/week savings

### Phase 2: Quality Commands (Week 2)

Add code quality workflows:

3. **Review commands** (2): `/review`, `/refactor`

**Effort:** 2-3 hours
**Cumulative value:** 60-100 min/week savings

### Phase 3: Git Helpers (Week 3)

Streamline git operations:

4. **Git commands** (2): `/commit`, `/branch`

**Effort:** 1-2 hours
**Total value:** 80-140 min/week savings

### Phase 4: Custom Commands (Week 4+)

Add team-specific or personal commands based on usage patterns:

- `/deploy` - Deployment workflow
- `/docs` - Documentation generation
- `/benchmark` - Performance benchmarking
- Personal commands in `~/.claude/commands/`

**Ongoing effort:** 1-2 hours/month for maintenance and new commands

---

## Integration with Other Features

### Slash Commands + Skills (Complementary)

| Task | Use Slash Command | Use Skill |
|------|-------------------|-----------|
| Quick coverage check | `/coverage` ✓ | - |
| Auto-detect coverage gaps | - | `test-generator` ✓ |
| Manual physics validation | `/physics` ✓ | - |
| Auto-validate during edits | - | `physics-validator` ✓ |
| Explicit plan creation | `/plan-create` ✓ | - |
| Auto-suggest planning | - | `plan-executor` ✓ |

### Slash Commands + Memory

Commands can reference memory files:

```yaml
# In /review command
Review checklist:
@.claude/memory/critical-rules.md
@.claude/memory/testing-templates.md
```

### Slash Commands + Hooks

Commands trigger hook validation:

```bash
/commit
# → PreToolUse hook: git-workflow-validator.sh
# → Validates commit message format
```

### Slash Commands + Subagents

Commands can invoke subagents explicitly:

```yaml
# In /validate-physics command
Use the physics-validator subagent to perform deep analysis on $ARGUMENTS.
```

---

## Priority & Effort Estimation

### Impact Level: 🔴 **HIGH**

| Metric | Score | Justification |
|--------|-------|---------------|
| Repetitive automation | 5/5 | Eliminates manual typing of frequent workflows |
| Plan efficiency | 5/5 | Streamlines GitHub Issues planning dramatically |
| Context preservation | 3/5 | Standardized templates ensure consistency |
| Agent coordination | 3/5 | Explicit agent invocation helpers |
| Token optimization | 2/5 | Minimal direct impact (slight increase from command expansion) |

### Implementation Complexity: 🟢 **2/5 (Low)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| File creation | 1/5 | Simple markdown files |
| Content writing | 2/5 | Define clear instructions per command |
| Testing | 2/5 | Manual invocation validation |
| Documentation | 2/5 | Document in team guide |
| Maintenance | 2/5 | Occasional refinement |

**Dependencies:**

*Technical Prerequisites:*
- ✅ None - Slash commands are self-contained feature
- ✅ Claude Code with slash command support (core feature)
- ✅ No other features required

*Infrastructure Requirements:*
- ✅ `.claude/commands/` directory OR plugin installation capability
- ✅ Git repository (if version controlling commands or distributing via plugin)
- ✅ Bash shell access (for commands using `!` execution prefix)

*Knowledge Prerequisites:*
- ⚠️ Understanding of markdown with YAML frontmatter
- ⚠️ Familiarity with argument passing syntax (`$1`, `$2`, `$ARGUMENTS`)
- ⚠️ Basic bash scripting (for commands that execute shell commands)
- ⚠️ Knowledge of file reference syntax (`@path/to/file`)

*Recommended But Optional:*
- 🔄 Memory Hierarchy - Commands can reference memory files via `@.claude/memory/...`
- 🔄 Skills System - Commands complement skills (explicit vs. automatic invocation)
- 🔄 Enhanced Hooks - Hooks can log command usage via Notification event
- 🔄 Existing scripts - Understanding of `.claude/scripts/*.sh` and `.claude/hooks/*.sh` helps design commands

*Implementation Considerations:*
- ⚠️ Command names must be unique (no conflicts with built-in or plugin commands)
- ⚠️ Bash execution (`!` prefix) requires security review
- ⚠️ File references must use correct paths (relative from project root)
- ⚠️ Testing requires manual invocation and verification

*Plugin-Specific Dependencies:*
- 🔌 Plugin Packaging feature (if distributing to team/community)
- 🔌 GitHub repository for marketplace hosting
- 🔌 `plugin.json` manifest file

### Estimated Effort

**Initial Implementation:**
- 10 commands × 20-30 min each = **3.5-5 hours**
- Testing & validation = **1-2 hours**
- Documentation = **1 hour**
- **Total: 5.5-8 hours**

**Break-even Analysis:**
- Time saved per week: **80-140 minutes** (1.3-2.3 hours)
- Break-even: **3-4 weeks**
- Annual ROI: **70-120 hours** of productive development time

**ROI Breakdown by Category:**
- Testing commands (3): 25-40 min/week
- Planning commands (3): 30-50 min/week
- Review commands (2): 15-30 min/week
- Git commands (2): 10-20 min/week

**Measurement Methodology:**

*How Time Savings Per Invocation (2-5 minutes) Are Measured:*
1. **Baseline:** Time manual prompt typing for equivalent workflow
2. **Example - Coverage check:** Type full prompt ("Run pytest with coverage, show me files below 95%, suggest which to prioritize") = ~45-60 seconds + cognitive load
3. **Slash command:** `/coverage` = ~2-3 seconds typing
4. **Savings per invocation:** 40-55 seconds typing + 60-120 seconds context recall = **2-3 minutes total**
5. **Verification:** Screen recording time analysis of 20 manual vs. 20 slash command invocations

*How Invocation Frequency (10-20 times/week) Is Estimated:*
1. **Historical analysis:** Review past session logs for repetitive prompt patterns
2. **Task categorization:** Identify how often testing, planning, review, git workflows occur
3. **Team survey:** Ask developers how often they perform common tasks
4. **Conservative estimate:**
   - Testing/validation: 4-6 times/week
   - Planning: 2-3 times/week
   - Code review: 2-3 times/week
   - Git operations: 2-4 times/week
5. **Total:** 10-16 times/week (round to 10-20 for safety margin)

*How Weekly Savings (80-140 minutes) Are Calculated:*
1. **Formula:** (Savings per invocation) × (Invocation frequency) × (10 commands)
2. **Conservative:** (2 min) × (10 invocations) = 20 min/week
3. **Moderate:** (3 min) × (15 invocations) = 45 min/week × 10 commands / weighted average = 80-100 min/week
4. **Aggressive:** (5 min) × (20 invocations) = 100 min/week
5. **Reality check:** Not all commands used equally; weight by category frequency

*How Category-Specific ROI Is Measured:*
1. **Testing commands (25-40 min/week):**
   - `/coverage`, `/physics`, `/test` used 4-6 times/week each = 12-18 total
   - Average 2-3 min saved per invocation = 24-54 min/week (conservative: 25-40)

2. **Planning commands (30-50 min/week):**
   - `/plan-create`, `/plan-phases`, `/plan-status` used 2-3 times/week each = 6-9 total
   - Average 5-8 min saved per invocation (longer prompts) = 30-72 min/week (conservative: 30-50)

3. **Review commands (15-30 min/week):**
   - `/review`, `/refactor` used 2-3 times/week each = 4-6 total
   - Average 3-5 min saved per invocation = 12-30 min/week

4. **Git commands (10-20 min/week):**
   - `/commit`, `/branch` used 2-4 times/week each = 4-8 total
   - Average 2-3 min saved per invocation = 8-24 min/week (conservative: 10-20)

*Verification Methods:*
- **Usage tracking:** Log slash command invocations via hooks
- **Time studies:** Measure actual time from command invocation to result
- **Team feedback:** Survey on perceived time savings after 4-week pilot
- **Comparison analysis:** A/B test 10 sessions with vs. without slash commands

---

## Testing Strategy

### Validation Approach

#### Test 1: Command Invocation
```
Scenario: Type /coverage in Claude Code
Expected: Command expands and executes coverage check
Validation: Coverage report displayed
```

#### Test 2: Argument Passing
```
Scenario: /physics solarwindpy/core/ion.py
Expected: Physics validation runs on specified file
Validation: Validation report for ion.py only
```

#### Test 3: Bash Execution
```
Scenario: /plan-status
Expected: gh-plan-status.sh executes
Validation: Plan status output displayed
```

#### Test 4: File References
```
Scenario: /review (which references memory files)
Expected: Memory files loaded and checklist expanded
Validation: Full review checklist appears
```

#### Test 5: Team Consistency
```
Scenario: Multiple team members use /commit
Expected: Consistent commit message format
Validation: All commits follow conventional commits + Claude footer
```

### Success Criteria

- ✅ All 10 commands execute correctly
- ✅ Arguments pass to scripts/prompts properly
- ✅ Bash commands execute with `!` prefix
- ✅ File references (`@`) resolve correctly
- ✅ Time savings ≥60 minutes/week measured
- ✅ Team adoption ≥80% within 2 weeks

### Monitoring

```bash
# Track command usage (if logging added to commands)
# Could add to each command:
# !echo "$(date) - /command-name used" >> .claude/logs/command-usage.log

# Analyze most-used commands
grep -c "/coverage" .claude/logs/command-usage.log
grep -c "/physics" .claude/logs/command-usage.log
```

---

## Comparison: Slash Commands vs Skills vs Hooks vs Agents

### Decision Matrix

```
Need explicit control over when it runs?
├─ YES → Slash Command
└─ NO → Continue...

Should it run automatically based on context?
├─ YES → Skill
└─ NO → Continue...

Should it trigger on specific tool/event?
├─ YES → Hook
└─ NO → Continue...

Complex multi-step analysis needed?
├─ YES → Agent/Subagent
└─ NO → Manual prompt
```

### Example Mapping for Common Tasks

| Task | Best Solution | Rationale |
|------|---------------|-----------|
| "Check coverage now" | `/coverage` | Explicit on-demand check |
| Auto-detect coverage gaps | `test-generator` skill | Automatic when coverage drops |
| Test after every edit | PostToolUse hook | Event-based automatic |
| Deep physics refactoring | PhysicsValidator subagent | Complex isolated analysis |
| Quick physics check | `/physics` | Explicit validation request |
| Physics validation during edits | PreToolUse hook | Automatic prevention |
| Create GitHub plan | `/plan-create` | Explicit planning action |
| Suggest planning | `plan-executor` skill | Automatic context detection |

---

## Recommended Slash Commands (Summary)

### High Priority (Implement First)

1. **`/coverage`** - Coverage check (10-15×/week, 2-3 min saved)
2. **`/physics`** - Physics validation (8-12×/week, 3-5 min saved)
3. **`/test`** - Smart test runner (15-20×/week, 1-2 min saved)
4. **`/plan-create`** - GitHub Issues plan (2-4×/week, 5-10 min saved)
5. **`/plan-status`** - Plan status (5-10×/week, 1-2 min saved)

**Subtotal: 30-50 uses/week, 60-100 minutes saved**

### Medium Priority (Implement Second)

6. **`/review`** - Code review (5-8×/week, 5-10 min saved)
7. **`/commit`** - Smart commit (8-15×/week, 2-3 min saved)
8. **`/plan-phases`** - Add phases (2-4×/week, 5-8 min saved)

**Subtotal: 15-27 uses/week, 40-70 minutes saved**

### Lower Priority (Implement Third)

9. **`/refactor`** - Refactoring helper (3-5×/week, 10-15 min saved)
10. **`/branch`** - Branch creation (3-6×/week, 1-2 min saved)

**Subtotal: 6-11 uses/week, 20-35 minutes saved**

### Total Impact

- **Usage:** 51-88 invocations/week
- **Time saved:** 120-205 minutes/week (2-3.4 hours)
- **Annual ROI:** 100-180 hours

---

## Appendix: Quick Reference

### Creating Slash Commands

```bash
# Create project-level command (shared with team)
mkdir -p .claude/commands
cat > .claude/commands/mycommand.md <<'EOF'
---
description: Short description of what this command does
---

Command instructions here.
Can use $ARGUMENTS, $1, $2 for arguments.
Can use @path/to/file to include files.
Can use !bash commands to execute shell commands.
EOF

# Now invoke with: /mycommand
```

### Command Syntax Reference

```yaml
# Frontmatter (optional)
---
description: What the command does
allowed-tools: [Bash, Read, Write]  # Restrict tools
model: sonnet  # Force specific model
---

# Command body
Instructions for Claude.

# Special syntax:
$ARGUMENTS - All arguments as single string
$1, $2, $3 - Positional arguments
@file/path - Include file contents
!command - Execute bash command
```

### Built-in Commands

```bash
/help         # Show help
/clear        # Clear conversation
/memory       # Edit memory files
/init         # Initialize project memory
/agents       # Manage subagents
/output-style # Change output style
/hooks        # Manage hooks
```

---

## Next Steps

1. **Review Proposed Commands** - Decide which 10 commands to implement
2. **Prioritize** - Start with testing + planning commands (highest frequency)
3. **Create Commands** - Follow implementation specification above
4. **Test** - Validate each command works as expected
5. **Document** - Add to team documentation
6. **Iterate** - Refine based on usage, add custom commands

**Ready to implement?** Start with Phase 1 (6 commands, 3-4 hours) for immediate 30-60 min/week savings.

---

**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
