# Phase 4: Workflow Improvements

## Objective
Enhance the GitHub Actions documentation workflow to be more resilient, informative, and self-healing when encountering formatting issues.

## Current Workflow Analysis

### Workflow Structure
```yaml
name: Documentation
on: [push, pull_request, workflow_dispatch]
jobs:
  build:
    - Checkout
    - Setup Python
    - Install dependencies
    - Lint with doc8 (FAILS HERE)
    - Check links
    - Build documentation
    - Upload artifacts
```

### Current Issues
1. **Fails fast**: Single formatting error blocks entire pipeline
2. **No auto-fixing**: Could fix simple issues automatically
3. **Poor error reporting**: Errors not clearly communicated
4. **No gradual enforcement**: Same rules for all branches

## Improved Workflow Design

### 4.1 Enhanced Documentation Workflow

**Updated `.github/workflows/docs.yml`**:

```yaml
name: Documentation

on:
  push:
    branches: ['**']
  pull_request:
    branches: ['**']
  workflow_dispatch:
    inputs:
      auto_fix:
        description: 'Automatically fix formatting issues'
        required: false
        default: 'true'
        type: boolean

jobs:
  format-check:
    name: Check Documentation Formatting
    runs-on: ubuntu-latest
    outputs:
      has_issues: ${{ steps.check.outputs.has_issues }}
      error_report: ${{ steps.check.outputs.error_report }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for auto-fixes
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install doc8
        run: pip install doc8
      
      - name: Auto-fix formatting issues
        id: autofix
        if: github.event_name == 'pull_request' || inputs.auto_fix == 'true'
        run: |
          echo "🔧 Attempting to auto-fix documentation formatting issues..."
          
          # Fix trailing whitespace
          find docs -name "*.rst" -type f -exec sed -i 's/[[:space:]]*$//' {} \;
          
          # Ensure newline at end of files
          find docs -name "*.rst" -type f -exec sh -c 'tail -c1 {} | read -r _ || echo >> {}' \;
          
          # Check if fixes were made
          if git diff --quiet; then
            echo "✅ No formatting fixes needed"
            echo "fixes_made=false" >> $GITHUB_OUTPUT
          else
            echo "🔧 Formatting fixes applied"
            echo "fixes_made=true" >> $GITHUB_OUTPUT
            
            # Show what was fixed
            echo "### Files Fixed" >> $GITHUB_STEP_SUMMARY
            git diff --name-only | while read file; do
              echo "- $file" >> $GITHUB_STEP_SUMMARY
            done
          fi
      
      - name: Check documentation formatting
        id: check
        run: |
          echo "📝 Checking documentation formatting..."
          
          # Run doc8 and capture output
          if doc8 --config .doc8 README.rst docs CITATION.rst 2>&1 | tee doc8_output.txt; then
            echo "✅ Documentation formatting check passed"
            echo "has_issues=false" >> $GITHUB_OUTPUT
          else
            echo "❌ Documentation formatting issues found"
            echo "has_issues=true" >> $GITHUB_OUTPUT
            
            # Create error report
            echo "### Documentation Formatting Issues" >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
            cat doc8_output.txt >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
            
            # Save error report for PR comment
            echo "error_report<<EOF" >> $GITHUB_OUTPUT
            cat doc8_output.txt >> $GITHUB_OUTPUT
            echo "EOF" >> $GITHUB_OUTPUT
            
            # Fail only on main/master branch
            if [[ "${{ github.ref }}" == "refs/heads/main" ]] || [[ "${{ github.ref }}" == "refs/heads/master" ]]; then
              exit 1
            else
              echo "⚠️ Allowing build to continue (not on main branch)"
            fi
          fi
      
      - name: Upload formatting report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: formatting-report-${{ github.run_id }}
          path: doc8_output.txt
          retention-days: 7

  build:
    name: Build Documentation
    needs: format-check
    # Continue even if formatting has issues (except on main)
    if: |
      always() && 
      (needs.format-check.result == 'success' || 
       (github.ref != 'refs/heads/main' && github.ref != 'refs/heads/master'))
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-docs-${{ hashFiles('docs/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-docs-
      
      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y libhdf5-dev pkg-config
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip wheel
          pip install --verbose tables
          pip install -r docs/requirements.txt
          pip install -e .
      
      - name: Check documentation links
        run: |
          pip install sphinx-link-checker
          sphinx-build -b linkcheck docs docs/build/linkcheck
        continue-on-error: true
      
      - name: Build documentation
        id: build
        env:
          SPHINXOPTS: -W --keep-going -n
        working-directory: docs
        run: |
          echo "📚 Building documentation..."
          make clean
          
          if make html 2>&1 | tee build.log; then
            echo "✅ Documentation built successfully"
            echo "build_success=true" >> $GITHUB_OUTPUT
          else
            echo "❌ Documentation build failed"
            echo "build_success=false" >> $GITHUB_OUTPUT
            
            # Extract warnings and errors
            echo "### Build Issues" >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
            grep -E "WARNING|ERROR" build.log >> $GITHUB_STEP_SUMMARY || true
            echo '```' >> $GITHUB_STEP_SUMMARY
            
            exit 1
          fi
      
      - name: Upload documentation artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: documentation-${{ github.run_id }}
          path: |
            docs/build/html/
            docs/build/doctrees/
            docs/build/coverage/
            docs/build/linkcheck/
            docs/build.log
          retention-days: 90
      
      - name: Check documentation coverage
        run: |
          mkdir -p docs/build/coverage
          python -m sphinx.ext.coverage -d docs/build/doctrees -o docs/build/coverage docs
          echo "### Documentation Coverage" >> $GITHUB_STEP_SUMMARY
          find docs/build/coverage -name "*.txt" -exec cat {} \; >> $GITHUB_STEP_SUMMARY
        continue-on-error: true

  comment-pr:
    name: Comment on PR
    if: github.event_name == 'pull_request' && needs.format-check.outputs.has_issues == 'true'
    needs: [format-check, build]
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - name: Comment formatting issues on PR
        uses: actions/github-script@v7
        with:
          script: |
            const error_report = `${{ needs.format-check.outputs.error_report }}`;
            
            const comment = `## 📝 Documentation Formatting Issues
            
            This PR has documentation formatting issues that need to be fixed:
            
            \`\`\`
            ${error_report}
            \`\`\`
            
            ### How to Fix
            
            1. **Automatically** (recommended):
               \`\`\`bash
               # Install pre-commit hooks
               pip install pre-commit
               pre-commit install
               
               # Run auto-fixes
               pre-commit run --all-files
               \`\`\`
            
            2. **Manually**:
               - Remove trailing whitespace
               - Ensure files end with newline
               - Keep lines under 100 characters
            
            3. **Using doc8**:
               \`\`\`bash
               pip install doc8
               doc8 --config .doc8 docs
               \`\`\`
            
            These checks are required to pass on the main branch.`;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });

  deploy:
    needs: build
    if: github.ref == 'refs/heads/master' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      # [Previous deploy steps remain the same]
```

### 4.2 Key Improvements Explained

| Improvement | Description | Benefit |
|-------------|-------------|---------|
| **Auto-fixing** | Automatically fixes trailing whitespace and EOF | Reduces manual work |
| **Gradual enforcement** | Strict on main, warnings on branches | Smoother development |
| **Better reporting** | Detailed error summaries in GitHub UI | Easier debugging |
| **PR comments** | Automatic comments with fix instructions | Better developer experience |
| **Resilient building** | Continue building despite format issues | Get partial results |
| **Artifact preservation** | Save all outputs for debugging | Better troubleshooting |

## Implementation Steps

### Step 4.1: Backup Current Workflow (1 minute)

```bash
# Create backup
cp .github/workflows/docs.yml .github/workflows/docs.yml.backup

# Verify backup
ls -la .github/workflows/docs.yml*
```

### Step 4.2: Update Workflow File (5 minutes)

Replace the current workflow with the enhanced version above, or apply incremental improvements:

**Option A: Full replacement**
```bash
# Copy new workflow from plan
cp plans/documentation-workflow-fix/enhanced-docs.yml .github/workflows/docs.yml
```

**Option B: Incremental updates**
Add specific improvements one at a time and test.

### Step 4.3: Test Workflow (3 minutes)

```bash
# Create test branch
git checkout -b test/workflow-improvements

# Make small doc change
echo "" >> docs/source/index.rst

# Commit and push
git add .github/workflows/docs.yml docs/source/index.rst
git commit -m "test: workflow improvements"
git push origin test/workflow-improvements

# Monitor in GitHub Actions UI
```

### Step 4.4: Validate Improvements (2 minutes)

Check that:
- [ ] Workflow runs without syntax errors
- [ ] Auto-fixing works correctly
- [ ] Error reporting is clear
- [ ] PR comments appear (if applicable)
- [ ] Build continues despite format issues (on branches)

## Configuration Options

### Environment Variables

Add to workflow for customization:

```yaml
env:
  # Maximum line length for doc8
  DOC8_MAX_LINE_LENGTH: 100
  
  # Whether to auto-fix issues
  AUTO_FIX_DOCS: true
  
  # Strict mode (fail on any issue)
  STRICT_DOC_CHECK: ${{ github.ref == 'refs/heads/main' }}
```

### Workflow Dispatch Parameters

Allow manual control:

```yaml
workflow_dispatch:
  inputs:
    auto_fix:
      description: 'Auto-fix formatting'
      type: boolean
      default: true
    strict_check:
      description: 'Fail on any issue'
      type: boolean
      default: false
    verbose:
      description: 'Verbose output'
      type: boolean
      default: false
```

## Monitoring and Metrics

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Build success rate | 0% | 95% | GitHub Actions analytics |
| Auto-fix effectiveness | 0% | 80% | Fixed vs manual |
| Time to resolution | 10 min | 2 min | PR to merge time |
| Developer satisfaction | Low | High | Survey/feedback |

### Monitoring Dashboard

Create GitHub Actions badge:

```markdown
![Documentation](https://github.com/blalterman/SolarWindPy/workflows/Documentation/badge.svg)
```

### Weekly Review Checklist
- [ ] Review workflow run history
- [ ] Check auto-fix success rate
- [ ] Review PR comments effectiveness
- [ ] Gather developer feedback
- [ ] Adjust configuration as needed

## Rollback Plan

### Quick Rollback

```bash
# Restore backup
cp .github/workflows/docs.yml.backup .github/workflows/docs.yml

# Commit and push
git add .github/workflows/docs.yml
git commit -m "revert: restore previous documentation workflow"
git push
```

### Gradual Rollback

Remove features one at a time:
1. Disable auto-fixing
2. Remove PR comments
3. Restore strict checking
4. Remove enhanced reporting

## Next Steps

1. Implement workflow improvements
2. Test on feature branch
3. Monitor for 1 week
4. Gather team feedback
5. Adjust based on results
6. Proceed to Phase 5 (Documentation)

---

*This phase makes the CI/CD pipeline resilient and developer-friendly while maintaining quality standards.*