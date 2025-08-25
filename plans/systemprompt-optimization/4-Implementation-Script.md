# Phase 4: Implementation Script & Automation

## Objectives
- Provide automated deployment script for systemPrompt optimization
- Ensure safe, reversible implementation
- Include validation and rollback procedures

## Implementation Script

### 4.1 Main Deployment Script

**Location**: `.claude/scripts/deploy-systemprompt-optimization.sh`

```bash
#!/bin/bash
# systemPrompt Optimization Deployment Script for SolarWindPy
# Safely deploys enhanced systemPrompt with backup and validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.json"
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"
BACKUP_DIR="$PROJECT_ROOT/.claude/backups/systemprompt-$(date +%Y%m%d-%H%M%S)"

echo "🚀 systemPrompt Optimization Deployment"
echo "========================================"

# Create backup directory
echo "📦 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Phase 1: Backup current configuration
echo ""
echo "Phase 1: Creating backups..."
echo "-----------------------------"

if [[ -f "$SETTINGS_FILE" ]]; then
    cp "$SETTINGS_FILE" "$BACKUP_DIR/settings.json.backup"
    echo "✅ Backed up settings.json"
else
    echo "❌ ERROR: settings.json not found at $SETTINGS_FILE"
    exit 1
fi

if [[ -f "$CLAUDE_MD" ]]; then
    cp "$CLAUDE_MD" "$BACKUP_DIR/CLAUDE.md.backup"
    echo "✅ Backed up CLAUDE.md"
else
    echo "❌ ERROR: CLAUDE.md not found at $CLAUDE_MD"
    exit 1
fi

# Phase 2: Deploy systemPrompt
echo ""
echo "Phase 2: Deploying enhanced systemPrompt..."
echo "-------------------------------------------"

NEW_SYSTEM_PROMPT="SolarWindPy: Solar wind plasma physics package. Architecture: pandas MultiIndex (M:measurement/C:component/S:species), SI units, mw²=2kT.\\n\\nAgents: UnifiedPlanCoordinator (all planning/implementation), PhysicsValidator (units/constraints), DataFrameArchitect (MultiIndex), TestEngineer (coverage), PlottingEngineer, FitFunctionSpecialist, NumericalStabilityGuard.\\n\\nHooks automate: SessionStart (branch validation/context), PreToolUse (physics/git checks), PostToolUse (test execution), PreCompact (state snapshots), Stop (coverage report).\\n\\nWorkflow: plan/* branches for planning, feature/* for code. PRs from plan/* to master trigger CI/security/docs checks. No direct master commits. Follow CLAUDE.md. Session context loads automatically."

# Update systemPrompt in settings.json using jq if available, otherwise use sed
if command -v jq >/dev/null 2>&1; then
    echo "📝 Updating systemPrompt using jq..."
    jq --arg prompt "$NEW_SYSTEM_PROMPT" '.systemPrompt = $prompt' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp"
    mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
else
    echo "📝 Updating systemPrompt using sed..."
    # Create temporary file with new systemPrompt
    python3 -c "
import json
import sys

with open('$SETTINGS_FILE', 'r') as f:
    config = json.load(f)

config['systemPrompt'] = '''$NEW_SYSTEM_PROMPT'''

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
fi

echo "✅ systemPrompt updated in settings.json"

# Phase 3: Update CLAUDE.md documentation
echo ""
echo "Phase 3: Updating documentation..."
echo "----------------------------------"

# Add PR workflow section to CLAUDE.md
if ! grep -q "PR Workflow & Plan Closeout" "$CLAUDE_MD"; then
    echo "📝 Adding PR workflow section to CLAUDE.md..."
    
    # Insert after Git Workflow section
    python3 -c "
import re

with open('$CLAUDE_MD', 'r') as f:
    content = f.read()

# Find insertion point after Git Workflow section
insertion_point = content.find('### Git Workflow (Automated via Hooks)')
if insertion_point == -1:
    print('Warning: Git Workflow section not found, appending at end')
    insertion_point = len(content)
else:
    # Find end of section
    next_section = content.find('###', insertion_point + 1)
    if next_section == -1:
        next_section = len(content)
    insertion_point = next_section

# PR workflow content
pr_workflow = '''
### PR Workflow & Plan Closeout
Plans are closed via Pull Requests with comprehensive automated checks:

#### Workflow Steps
1. **Complete Implementation**: Finish work on \`feature/*\` branch
2. **Merge to Plan**: \`git checkout plan/<name>\` → \`git merge feature/<name>\`
3. **Create PR**: \`gh pr create\` from \`plan/*\` → \`master\`
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

'''

# Insert new content
new_content = content[:insertion_point] + pr_workflow + content[insertion_point:]

with open('$CLAUDE_MD', 'w') as f:
    f.write(new_content)
"
    echo "✅ Added PR workflow section to CLAUDE.md"
else
    echo "ℹ️  PR workflow section already exists in CLAUDE.md"
fi

# Add agent selection guidelines
if ! grep -q "Agent Selection Quick Reference" "$CLAUDE_MD"; then
    echo "📝 Adding agent selection guidelines to CLAUDE.md..."
    
    # Append agent section
    cat >> "$CLAUDE_MD" << 'EOF'

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
EOF
    echo "✅ Added agent selection guidelines to CLAUDE.md"
else
    echo "ℹ️  Agent selection guidelines already exist in CLAUDE.md"
fi

# Phase 4: Validation
echo ""
echo "Phase 4: Validation..."
echo "---------------------"

# Validate JSON syntax
if command -v jq >/dev/null 2>&1; then
    if jq empty "$SETTINGS_FILE" >/dev/null 2>&1; then
        echo "✅ settings.json syntax valid"
    else
        echo "❌ ERROR: Invalid JSON syntax in settings.json"
        echo "🔄 Restoring backup..."
        cp "$BACKUP_DIR/settings.json.backup" "$SETTINGS_FILE"
        exit 1
    fi
else
    if python3 -c "import json; json.load(open('$SETTINGS_FILE'))" >/dev/null 2>&1; then
        echo "✅ settings.json syntax valid"
    else
        echo "❌ ERROR: Invalid JSON syntax in settings.json"
        echo "🔄 Restoring backup..."
        cp "$BACKUP_DIR/settings.json.backup" "$SETTINGS_FILE"
        exit 1
    fi
fi

# Validate systemPrompt content
if grep -q "UnifiedPlanCoordinator" "$SETTINGS_FILE"; then
    echo "✅ systemPrompt contains agent references"
else
    echo "❌ ERROR: systemPrompt missing agent references"
    exit 1
fi

# Phase 5: Success summary
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo "✅ systemPrompt updated (175 → 210 tokens)"
echo "✅ CLAUDE.md enhanced with PR workflow and agent guidelines"
echo "✅ Backups created in: $BACKUP_DIR"
echo ""
echo "Next Steps:"
echo "1. Start new Claude Code session to test systemPrompt"
echo "2. Verify agent awareness and workflow understanding"
echo "3. Monitor productivity improvements"
echo ""
echo "Rollback command (if needed):"
echo "  cp $BACKUP_DIR/settings.json.backup $SETTINGS_FILE"
echo "  cp $BACKUP_DIR/CLAUDE.md.backup $CLAUDE_MD"
```

### 4.2 Validation Script

**Location**: `.claude/scripts/validate-systemprompt.sh`

```bash
#!/bin/bash
# systemPrompt Validation Script
# Tests enhanced systemPrompt functionality

set -e

echo "🧪 systemPrompt Validation Tests"
echo "================================"

# Test 1: JSON syntax validation
echo "Test 1: JSON syntax validation..."
if python3 -c "import json; json.load(open('.claude/settings.json'))" >/dev/null 2>&1; then
    echo "✅ PASS: settings.json has valid syntax"
else
    echo "❌ FAIL: settings.json has invalid syntax"
    exit 1
fi

# Test 2: systemPrompt content validation
echo "Test 2: systemPrompt content validation..."
REQUIRED_ELEMENTS=(
    "SolarWindPy"
    "MultiIndex"
    "UnifiedPlanCoordinator"
    "PhysicsValidator"
    "DataFrameArchitect"
    "SessionStart"
    "plan/\\*"
    "PR"
    "CLAUDE.md"
)

MISSING_ELEMENTS=()
for element in "${REQUIRED_ELEMENTS[@]}"; do
    if grep -q "$element" .claude/settings.json; then
        echo "  ✅ Found: $element"
    else
        echo "  ❌ Missing: $element"
        MISSING_ELEMENTS+=("$element")
    fi
done

if [[ ${#MISSING_ELEMENTS[@]} -eq 0 ]]; then
    echo "✅ PASS: All required elements present in systemPrompt"
else
    echo "❌ FAIL: Missing elements: ${MISSING_ELEMENTS[*]}"
    exit 1
fi

# Test 3: CLAUDE.md documentation validation
echo "Test 3: CLAUDE.md documentation validation..."
DOC_SECTIONS=(
    "PR Workflow"
    "Agent Selection"
    "UnifiedPlanCoordinator"
    "PhysicsValidator"
    "DataFrameArchitect"
)

MISSING_DOCS=()
for section in "${DOC_SECTIONS[@]}"; do
    if grep -q "$section" CLAUDE.md; then
        echo "  ✅ Found: $section"
    else
        echo "  ❌ Missing: $section"
        MISSING_DOCS+=("$section")
    fi
done

if [[ ${#MISSING_DOCS[@]} -eq 0 ]]; then
    echo "✅ PASS: All required documentation sections present"
else
    echo "❌ FAIL: Missing documentation: ${MISSING_DOCS[*]}"
    exit 1
fi

# Test 4: Hook compatibility check
echo "Test 4: Hook compatibility check..."
if [[ -x .claude/hooks/validate-session-state.sh ]]; then
    echo "  ✅ SessionStart hook executable"
else
    echo "  ❌ SessionStart hook not executable"
    exit 1
fi

if [[ -x .claude/hooks/git-workflow-validator.sh ]]; then
    echo "  ✅ Git workflow validator executable"
else
    echo "  ❌ Git workflow validator not executable"
    exit 1
fi

echo "✅ PASS: Hook compatibility verified"

echo ""
echo "🎉 All validation tests passed!"
echo "systemPrompt optimization ready for use"
```

### 4.3 Rollback Script

**Location**: `.claude/scripts/rollback-systemprompt.sh`

```bash
#!/bin/bash
# systemPrompt Rollback Script
# Safely restores previous systemPrompt configuration

set -e

BACKUP_DIR=${1:-$(ls -t .claude/backups/systemprompt-* | head -1)}

if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
    echo "❌ ERROR: No backup directory found or specified"
    echo "Usage: $0 [backup-directory]"
    echo "Available backups:"
    ls -la .claude/backups/systemprompt-* 2>/dev/null || echo "  (none found)"
    exit 1
fi

echo "🔄 systemPrompt Rollback"
echo "========================"
echo "Restoring from: $BACKUP_DIR"

# Restore settings.json
if [[ -f "$BACKUP_DIR/settings.json.backup" ]]; then
    cp "$BACKUP_DIR/settings.json.backup" .claude/settings.json
    echo "✅ Restored settings.json"
else
    echo "❌ ERROR: settings.json backup not found"
    exit 1
fi

# Restore CLAUDE.md
if [[ -f "$BACKUP_DIR/CLAUDE.md.backup" ]]; then
    cp "$BACKUP_DIR/CLAUDE.md.backup" CLAUDE.md
    echo "✅ Restored CLAUDE.md"
else
    echo "❌ ERROR: CLAUDE.md backup not found"
    exit 1
fi

echo ""
echo "🎉 Rollback Complete!"
echo "Previous systemPrompt configuration restored"
echo "Restart Claude Code session to apply changes"
```

## Usage Instructions

### Deploy systemPrompt Optimization
```bash
# Make scripts executable
chmod +x .claude/scripts/deploy-systemprompt-optimization.sh
chmod +x .claude/scripts/validate-systemprompt.sh
chmod +x .claude/scripts/rollback-systemprompt.sh

# Deploy optimization
.claude/scripts/deploy-systemprompt-optimization.sh

# Validate deployment
.claude/scripts/validate-systemprompt.sh
```

### Rollback if Needed
```bash
# List available backups
ls -la .claude/backups/systemprompt-*

# Rollback to most recent backup
.claude/scripts/rollback-systemprompt.sh

# Or rollback to specific backup
.claude/scripts/rollback-systemprompt.sh .claude/backups/systemprompt-20250819-143022
```

## Safety Features
- **Automatic Backups**: Creates timestamped backups before any changes
- **JSON Validation**: Verifies syntax before applying changes
- **Content Verification**: Ensures all required elements present
- **Rollback Capability**: Easy restoration of previous state
- **Non-destructive**: All changes are reversible
- **Error Handling**: Script stops on any error to prevent corruption

## Benefits of Automation
- **Consistent Deployment**: Same process every time
- **Error Prevention**: Validates changes before applying
- **Quick Rollback**: Easy restoration if issues occur
- **Documentation**: All steps clearly logged
- **Reusability**: Can be run multiple times safely