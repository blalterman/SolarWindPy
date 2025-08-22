# Phase 3: Pre-commit Hook Integration

## Objective
Implement pre-commit hooks to catch and fix documentation formatting issues before they reach the repository, preventing CI/CD failures.

## Rationale

### Why Pre-commit Hooks
- **Shift-left approach**: Catch issues at the earliest point
- **Automatic fixing**: Many issues can be auto-corrected
- **Developer efficiency**: No need to remember formatting rules
- **CI/CD protection**: Reduces load on build systems
- **Consistency**: Same rules for all contributors

### Expected Benefits
- 90% reduction in formatting-related CI failures
- Zero-friction formatting compliance
- Automatic issue resolution
- Improved developer experience

## Pre-commit Configuration Design

### 3.1 Create Pre-commit Configuration

**File**: `/.pre-commit-config.yaml`

```yaml
# Pre-commit hooks for SolarWindPy
# Ensures code and documentation quality before commits

# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks

# To install: pip install pre-commit && pre-commit install
# To run manually: pre-commit run --all-files

default_language_version:
  python: python3

repos:
  # General file fixes
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # Fix trailing whitespace
      - id: trailing-whitespace
        types: [text]
        exclude: \.md$|\.rst$  # Handle separately for docs
      
      # Ensure files end with newline
      - id: end-of-file-fixer
        types: [text]
      
      # Check for large files
      - id: check-added-large-files
        args: ['--maxkb=1000']
      
      # Fix mixed line endings
      - id: mixed-line-ending
        args: ['--fix=lf']
      
      # Check YAML syntax
      - id: check-yaml
      
      # Check JSON syntax
      - id: check-json

  # Documentation-specific hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # Documentation-specific trailing whitespace
      - id: trailing-whitespace
        name: Fix RST trailing whitespace
        files: \.(rst|txt)$
        exclude: docs/source/api/
      
      # Documentation-specific EOF fixer
      - id: end-of-file-fixer
        name: Fix RST file endings
        files: \.(rst|txt)$
        exclude: docs/source/api/

  # RST specific linting with doc8
  - repo: https://github.com/PyCQA/doc8
    rev: v1.1.1
    hooks:
      - id: doc8
        name: Check RST documentation formatting
        args: [
          '--max-line-length=100',
          '--ignore=D000',
          '--ignore-path=docs/build',
          '--ignore-path=docs/source/api',
          '--ignore-path=docs/_build'
        ]
        files: \.(rst|txt)$
        exclude: docs/source/api/

  # Python code formatting (optional but recommended)
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        exclude: docs/

  # Python linting (optional but recommended)
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--config=setup.cfg']
        exclude: docs/
```

### 3.2 Simplified Minimal Configuration

For teams wanting to start simple:

```yaml
# Minimal pre-commit configuration for documentation
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer

  - repo: https://github.com/PyCQA/doc8
    rev: v1.1.1
    hooks:
      - id: doc8
        args: ['--config=.doc8']
```

## Implementation Steps

### Step 3.1: Install Pre-commit (3 minutes)

**For developers**:
```bash
# Install pre-commit package
pip install pre-commit

# Or add to requirements-dev.txt
echo "pre-commit>=3.5.0" >> requirements-dev.txt
pip install -r requirements-dev.txt
```

### Step 3.2: Create Configuration File (2 minutes)

```bash
# Create the configuration file
cat > .pre-commit-config.yaml << 'EOF'
# [Insert configuration from 3.1 above]
EOF

# Verify file created
ls -la .pre-commit-config.yaml
```

### Step 3.3: Install Git Hooks (2 minutes)

```bash
# Install the git hook scripts
pre-commit install

# Verify installation
ls -la .git/hooks/pre-commit

# Expected output shows symlink or script
```

### Step 3.4: Initial Run and Fixes (5 minutes)

```bash
# Run on all files to establish baseline
pre-commit run --all-files

# This will:
# 1. Download required tools
# 2. Check all files
# 3. Auto-fix what it can
# 4. Report what needs manual fixing

# Run again to verify all issues fixed
pre-commit run --all-files
```

### Step 3.5: Configure CI Integration (3 minutes)

**Add to `.github/workflows/docs.yml`**:

```yaml
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Run pre-commit
        uses: pre-commit/action@v3.0.0
```

Or as a step in existing job:

```yaml
      - name: Run pre-commit checks
        run: |
          pip install pre-commit
          pre-commit run --all-files --show-diff-on-failure
```

## Developer Workflow

### Standard Workflow
1. **Make changes** to documentation
2. **Stage changes**: `git add docs/`
3. **Commit**: `git commit -m "docs: update"`
4. **Pre-commit runs automatically**
   - Fixes issues if possible
   - Blocks commit if manual fixes needed
5. **Review changes** if any made
6. **Commit succeeds** if all checks pass

### Manual Usage
```bash
# Check specific files
pre-commit run --files docs/source/index.rst

# Check all staged files
pre-commit run

# Check everything
pre-commit run --all-files

# Update hook versions
pre-commit autoupdate
```

### Bypassing Hooks (Emergency Only)
```bash
# Skip pre-commit hooks (use sparingly)
git commit --no-verify -m "emergency: critical fix"

# Or set environment variable
SKIP=doc8 git commit -m "docs: update"
```

## Team Adoption Strategy

### Gradual Rollout
1. **Week 1**: Optional - developers can install if desired
2. **Week 2**: Recommended - encourage installation
3. **Week 3**: Expected - soft requirement
4. **Week 4**: Required - add to CI/CD

### Developer Onboarding
```markdown
# Add to CONTRIBUTING.md

## Pre-commit Hooks

This project uses pre-commit hooks to maintain code and documentation quality.

### Setup (one-time)
```bash
pip install pre-commit
pre-commit install
```

### Usage
Hooks run automatically on `git commit`. To run manually:
```bash
pre-commit run --all-files
```
```

### Training Materials
- Quick setup guide (5 minutes)
- Common issues and solutions
- Benefits explanation
- Demo video/GIF

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "pre-commit: command not found" | Not installed | `pip install pre-commit` |
| Hooks not running | Not installed in repo | `pre-commit install` |
| Hooks failing on old files | Historical issues | `pre-commit run --all-files` then commit fixes |
| Slow first run | Downloading tools | One-time delay, cached after |
| Can't commit urgent fix | Hooks blocking | Use `--no-verify` flag (sparingly) |

### Debug Commands
```bash
# Verbose output
pre-commit run --all-files --verbose

# Show diff of changes
pre-commit run --all-files --show-diff-on-failure

# Check specific hook
pre-commit run doc8 --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

## Metrics and Monitoring

### Success Metrics
| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Formatting failures in CI | 100% | <5% | GitHub Actions logs |
| Time to fix formatting | 10 min | 0 min | Automatic |
| Developer adoption | 0% | 90% | Survey/git hooks |
| PR rejections for formatting | High | Near zero | PR reviews |

### Monitoring
- Track CI/CD failure rate for doc8
- Survey developers on experience
- Monitor pre-commit skip usage
- Review commit patterns

## Rollback Plan

### Partial Rollback
```bash
# Disable specific hooks
# Edit .pre-commit-config.yaml and comment out problematic hooks

# Uninstall from local repo
pre-commit uninstall
```

### Complete Rollback
```bash
# Remove configuration
rm .pre-commit-config.yaml

# Uninstall hooks
pre-commit uninstall

# Remove from requirements
sed -i '/pre-commit/d' requirements-dev.txt
```

## Cost-Benefit Analysis

### Costs
- Initial setup: 15 minutes per developer
- Learning curve: 1-2 days to adapt
- Occasional bypass needed: 1-2 times/month

### Benefits
- Prevent 95% of formatting issues
- Save 10 minutes per PR
- Reduce CI/CD failures by 50%
- Improve code review focus on content

### ROI
- Break-even: After 2 prevented failures
- Monthly savings: 5 hours team-wide
- Annual savings: 60 hours

## Next Steps

1. Create and test configuration
2. Document in CONTRIBUTING.md
3. Announce to team with benefits
4. Provide setup support
5. Monitor adoption and effectiveness
6. Proceed to Phase 4 (Workflow improvements)

---

*This phase provides proactive protection against documentation formatting issues at the source.*