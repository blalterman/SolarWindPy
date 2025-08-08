# Claude Code Workflow Template

## Feature Development Workflow

This template provides a step-by-step process for Claude Code feature development with proper branch management.

### Step 1: Branch Assessment

**Claude automatically runs:**
```bash
git branch -r --no-merged master
```

**Claude asks user:**
> "Which branch should I use? Please specify branch name, or say 'search' if you want me to help find an appropriate branch, or say 'new' to create a new branch"

### Step 2: User Response Options

#### Option A: Specify Existing Branch
**User says:** `origin/existing-branch-name`
**Claude does:**
```bash
git checkout existing-branch-name
git pull origin existing-branch-name
```

#### Option B: Search for Appropriate Branch  
**User says:** `search`
**Claude does:**
1. Examines branch names and recent commits
2. Presents 3-5 most relevant branches with descriptions
3. Asks user to choose or create new branch

#### Option C: Create New Branch
**User says:** `new`
**Claude creates:**
```bash
TIMESTAMP=$(date +"%Y-%m-%d-%H-%M-%S")
BRANCH_NAME="claude/${TIMESTAMP}-module-feature-description"
git checkout -b ${BRANCH_NAME}
git push -u origin ${BRANCH_NAME}
```

### Step 3: Development Work

**Claude follows standard development:**
1. Write/modify code following SolarWindPy conventions
2. Write comprehensive tests
3. Update documentation as needed
4. Ensure physics validation (units, calculations)

### Step 4: Quality Assurance

**Before any commit:**
```bash
pytest -q                    # All tests must pass
black solarwindpy/          # Format code  
flake8                      # Check linting
```

### Step 5: Commit with Attribution

**Commit format:**
```bash
git add .
git commit -m "feat(module): descriptive summary

Detailed description of changes and rationale.

Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 6: Push and Track

**Push branch:**
```bash
git push origin <branch-name>
```

### Step 7: Completion Notice

**Claude provides:**
- Summary of changes made
- Branch name for user reference  
- Reminder that user should create PR when ready
- Any additional validation needed

## Branch Naming Examples

### Good Branch Names
- `claude/2025-08-08-14-30-00-fitfunctions-add-robust-fitting`
- `claude/2025-08-08-15-15-00-plotting-improve-histogram-performance`
- `claude/2025-08-08-16-00-00-core-plasma-fix-thermal-speed-calc`
- `claude/2025-08-08-17-45-00-tests-increase-coverage-instabilities`

### Branch Components
- `claude/` - Identifier for Claude-generated branches
- `YYYY-MM-DD-HH-MM-SS` - Timestamp for uniqueness
- `module` - Primary module being modified (core, plotting, fitfunctions, etc.)
- `feature-description` - Brief description with hyphens

## Emergency Procedures

### If Working on Wrong Branch
```bash
git stash                           # Save current work
git checkout correct-branch         # Switch to correct branch
git stash pop                       # Restore work
```

### If Need to Merge Latest Master
```bash
git checkout master
git pull origin master
git checkout feature-branch
git merge master                    # Resolve conflicts if any
```

### If Branch Becomes Obsolete
```bash
git checkout master
git branch -d local-branch-name
git push origin --delete remote-branch-name
```

## Quality Gates

### Pre-Commit Checklist
- [ ] All tests pass (`pytest -q`)
- [ ] Code formatted (`black solarwindpy/`)
- [ ] No linting errors (`flake8`)
- [ ] Physics validation complete (units, calculations)
- [ ] Documentation updated if needed
- [ ] Commit message follows Conventional Commits format

### Pre-PR Checklist  
- [ ] Branch pushed to origin
- [ ] All quality gates passed
- [ ] Feature complete and tested
- [ ] Ready for user review and merge

## Benefits Summary

This workflow ensures:
- ✅ **No master branch conflicts** - All work isolated to feature branches
- ✅ **No premature CI triggers** - GitHub Actions only run on complete features
- ✅ **Parallel development support** - Multiple features can be developed simultaneously  
- ✅ **Clear audit trail** - Every Claude contribution tracked and attributed
- ✅ **Clean git history** - Each feature gets dedicated branch and PR
- ✅ **Review-ready code** - All changes go through proper validation before merge