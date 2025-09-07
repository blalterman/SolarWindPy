# Maintenance & Troubleshooting

Maintenance commands and troubleshooting procedures for SolarWindPy development.

## GitHub Actions Workflow Management

### Skipped Runs: Expected Behavior
The Claude Code workflow creates "skipped" runs for every issue/comment without "@claude".

**Root Cause**: GitHub Actions architectural limitation - all trigger events create runs, conditionally executed

**Impact**: UI clutter (cosmetic only), no resource consumption, full audit trail preserved

**Trade-off Decision**: Accept skipped runs as optimal trade-off
- Preserves excellent @claude user experience (automatic responses)
- Zero implementation risk or complexity  
- Simple mitigation via periodic cleanup commands
- Cost-benefit analysis strongly favors status quo ($10/year vs $2,500+/year alternatives)

### Cleanup Commands

```bash
# Clean up skipped GitHub Actions workflow runs (use occasionally)
gh run list -s skipped --limit 100 --json databaseId -q ".[].databaseId" | \
  xargs -I {} gh run delete {} 2>/dev/null

# With confirmation (recommended):
count=$(gh run list -s skipped --limit 100 | wc -l)
[[ $count -gt 0 ]] && echo "Delete $count skipped runs? (y/n)" && \
  read -r response && [[ "$response" == "y" ]] && \
  gh run list -s skipped --limit 100 --json databaseId -q ".[].databaseId" | \
  xargs -I {} gh run delete {}

# For large cleanups (300+ runs):
count=$(gh run list -s skipped --limit 500 | wc -l)
[[ $count -gt 0 ]] && echo "Delete $count skipped runs? (y/n)" && \
  read -r response && [[ "$response" == "y" ]] && \
  gh run list -s skipped --limit 500 --json databaseId -q ".[].databaseId" | \
  xargs -I {} gh run delete {}
```

## Recipe and Environment Management

```bash
# Update conda recipe for new versions
python scripts/update_conda_recipe.py

# Generate conda environment from requirements
python scripts/requirements_to_conda_env.py
python scripts/requirements_to_conda_env.py --name solarwindpy-dev

# Create and activate environments
conda env create -f solarwindpy.yml
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy
pip install -e .
```

## Conda Feedstock Automation

```bash
# Test feedstock update process
python scripts/update_conda_feedstock.py v0.1.5 --dry-run

# Check PyPI availability for new releases
python scripts/wait_for_pypi.py v0.1.5 --timeout 300

# Full feedstock update workflow
python scripts/update_conda_feedstock.py v0.1.5
```

## Testing and Coverage Maintenance

```bash
# Generate test scaffolding for new modules
python .claude/scripts/generate-test.py
python .claude/scripts/generate-test.py solarwindpy/new_module.py

# Run comprehensive test suite with coverage
pytest --cov=solarwindpy --cov-report=html -q
pytest --cov=solarwindpy --cov-report=term -q --tb=short

# Monitor coverage trends
python .claude/hooks/coverage-monitor.py

# Smart test execution for development
.claude/hooks/test-runner.sh --changed    # Only changed files
.claude/hooks/test-runner.sh --physics    # Physics validation
.claude/hooks/test-runner.sh --fast       # Quick validation
.claude/hooks/test-runner.sh --coverage   # Full coverage analysis
```

## Hook System Maintenance

```bash
# Validate session state manually
bash .claude/hooks/validate-session-state.sh

# Check git workflow compliance  
bash .claude/hooks/git-workflow-validator.sh

# Run physics validation on specific files
python .claude/hooks/physics-validation.py solarwindpy/core/plasma.py
python .claude/hooks/physics-validation.py --strict
python .claude/hooks/physics-validation.py --report

# Create manual compaction for token management
python .claude/hooks/create-compaction.py

# Validate plan completeness
python .claude/hooks/plan-value-validator.py --plan-file plans/active-plan/0-Overview.md
```

## Directory Structure Maintenance

```bash
# Ensure required directories exist
mkdir -p .claude/logs
mkdir -p .claude/backups  
mkdir -p tmp
touch .claude/logs/security-audit.log

# Clean up temporary files
rm -f tmp/phases.conf
rm -f tmp/*.tmp

# Verify hook permissions
find .claude/hooks/ -name "*.sh" -type f -executable
```

## Git Tag Management

### Release Tags Only (Semantic Versioning)
- **Pattern**: `v{major}.{minor}.{patch}[-{prerelease}]`
- **Examples**: `v1.0.0`, `v2.1.3-alpha`, `v1.5.0-beta.2`
- **Purpose**: Official package releases, PyPI distribution
- **Automation**: GitHub workflow creates these for releases

### Session State: File-Based (No Git Tags)
- **Location**: `.claude/compacted_state.md` and timestamped backups
- **Pattern**: `compaction-{date}-{time}-{compression}pct.md`  
- **Purpose**: Session state preservation at token boundaries
- **Storage**: File-based system, setuptools_scm ignores non-v* tags

## Troubleshooting

### Hook Failures
- Check hook permissions: `ls -la .claude/hooks/*.sh`
- Review timeout settings in `.claude/settings.json`
- Run hooks manually for debugging

### Test Failures  
- Use `.claude/hooks/test-runner.sh --changed` for focused testing
- Check coverage requirements: must be ≥95%
- Review physics validation output for constraint violations

### Plan Creation Issues
- Verify GitHub CLI authentication: `gh auth status`
- Check required labels exist in repository
- Use interactive mode: `.claude/scripts/gh-plan-create.sh -i`

### Compaction Problems
- Check available disk space for .claude/ directory
- Verify git repository status for context generation
- Manual compaction: `python .claude/hooks/create-compaction.py`

## Performance Monitoring

### Token Usage Tracking
- Monitor compaction efficiency (target 60-80% reduction)
- Track plan creation savings (1,500 → 300 tokens typical)
- Review session length improvements via file-based state

### Coverage Trends
- Maintain ≥95% coverage requirement
- Monitor test execution time with smart runner
- Track physics validation pass rates