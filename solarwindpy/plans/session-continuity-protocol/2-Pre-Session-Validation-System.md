# Phase 2: Pre-Session Validation System

## Phase Tasks
- [ ] **Implement Session State Accuracy Verification** (Est: 1 hour) - Build validation checklist with git cross-reference
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Create Active Plan Status Assessment** (Est: 45 min) - Automated high-completion plan detection
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Build Development Context Priority Ranking** (Est: 45 min) - Priority assessment and decision system
  - Commit: `<checksum>`
  - Status: Pending

## Pre-Session Validation Checklist

### Step 1: Session State Accuracy Verification (5 min)
```bash
# Check git status and recent commits
git status
git log --oneline -10

# Review session state file
cat claude_session_state.md

# Cross-validate session state claims with git evidence
git log --grep="[claimed-work]" --oneline
```

**Validation Questions:**
- [ ] Does session state completion status match git commit evidence?
- [ ] Are "remaining tasks" actually remaining or completed in git history?
- [ ] Do git commit messages support session state timeline claims?
- [ ] Are file modification claims verifiable in git history?

### Step 2: Active Plan Status Assessment (5 min)
```bash
# Check for active plan branches
git branch -r --no-merged master

# Check for plan files in high completion states
find solarwindpy/plans -name "*.md" -exec grep -l "90%\|95%\|85%" {} \;

# Look for compacted states indicating active work
find solarwindpy/plans -name "compacted_state.md"
```

**Assessment Questions:**
- [ ] Are there any plans at 85%+ completion requiring finishing touches?
- [ ] Do any plan branches exist that need merging or continuation?
- [ ] Are there compacted states indicating interrupted development sessions?
- [ ] What infrastructure work is pending completion?

### Step 3: Development Context Priority Ranking (5 min)

**Priority 1: Critical Infrastructure Issues**
- CI/CD pipeline failures or warnings
- Build system problems or dependency conflicts
- Documentation build failures or validation issues
- Requirements management inconsistencies

**Priority 2: High-Completion Active Plans**
- Plans showing 85%+ completion in session state
- Work with only 1-2 remaining tasks to finish
- Infrastructure improvements with validated benefits

**Priority 3: New Feature Development**
- Planned features from project roadmap
- New analysis tools or visualization capabilities
- Performance optimization initiatives

**Priority 4: Enhancement Work** 
- Code quality improvements
- Documentation enhancements
- Refactoring for maintainability

## Navigation
- **Previous Phase**: [1-Core-Principles-Framework.md](./1-Core-Principles-Framework.md)
- **Next Phase**: [3-Context-Switching-Prevention.md](./3-Context-Switching-Prevention.md)
- **Overview**: [0-Overview.md](./0-Overview.md)