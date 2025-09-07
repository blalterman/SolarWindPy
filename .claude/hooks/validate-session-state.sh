#!/bin/bash
# Session State Validator for SolarWindPy
# Validates and restores session context on Claude Code startup

set -e

echo "🔍 Validating session state..."

# Check current branch
current_branch=$(git branch --show-current)
echo "📍 Current branch: $current_branch"

if [[ $current_branch == "master" ]]; then
    # Find active plan branches
    echo "⚠️  On master branch. Checking for active plans..."
    active_plans=$(git branch | grep "plan/" | head -5)
    if [[ -n "$active_plans" ]]; then
        echo "📋 Active plan branches found:"
        echo "$active_plans"
        echo "💡 Suggestion: Use 'git checkout plan/<name>' to continue a plan"
        echo "💡 Or create new plan: 'git checkout -b plan/<your-plan-name>'"
    else
        echo "📋 No active plan branches found"
        echo "💡 Create new plan: 'git checkout -b plan/<your-plan-name>'"
    fi
fi

# Load compacted state if exists
if [[ $current_branch == plan/* ]]; then
    plan_name="${current_branch#plan/}"
    compacted_state_file="plans/${plan_name}/compacted_state.md"
    
    if [[ -f "$compacted_state_file" ]]; then
        echo "📋 Loading compacted state for $plan_name"
        echo "📄 Compacted state preview:"
        head -15 "$compacted_state_file" | sed 's/^/   /'
        echo "   ..."
    else
        echo "📋 No compacted state found for $plan_name"
        if [[ -f "plans/${plan_name}/0-Overview.md" ]]; then
            echo "📄 Plan overview available: plans/${plan_name}/0-Overview.md"
        fi
    fi
fi

# Check for uncommitted changes
if ! git diff --quiet; then
    echo "⚠️  Uncommitted changes detected:"
    git status --short | head -10 | sed 's/^/   /'
    echo "💡 Review with 'git status' or commit with proper message"
fi

# Check for unstaged changes
if ! git diff --cached --quiet; then
    echo "📝 Staged changes ready for commit:"
    git diff --cached --name-only | head -5 | sed 's/^/   /'
fi

# Show recent commits for context
echo "📚 Recent commits:"
git log --oneline -3 | sed 's/^/   /'

echo "✅ Session state validation complete"

# Trigger startup briefing based on CLAUDE.md
echo ""
echo "📋 === PROJECT BRIEFING REQUIRED ==="
echo "Per CLAUDE.md requirements, provide:"
echo "1. SolarWindPy architecture (MultiIndex DataFrame, physics classes)"
echo "2. Agent system overview (7 specialized agents)"  
echo "3. Current branch: $current_branch and plan status"
echo "4. Critical rules (branch protection, script execution)"
echo "5. Reference CLAUDE.md for essential commands"
echo "=================================="