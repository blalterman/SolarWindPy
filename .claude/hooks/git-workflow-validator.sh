#!/bin/bash
# Git Workflow Validator for SolarWindPy
# Enforces branch naming and workflow rules

set -e

command="$*"
branch=$(git branch --show-current)

echo "🔍 Validating git operation: $command"
echo "📍 Current branch: $branch"

# Prevent direct master commits
if [[ $branch == "master" ]] && [[ $command == *"commit"* ]]; then
    echo "❌ ERROR: Cannot commit directly to master branch"
    echo "💡 Workflow: Create a plan branch first"
    echo "   git checkout -b plan/<your-plan-name>"
    echo "   # or continue existing plan"
    echo "   git checkout plan/<existing-plan>"
    exit 1
fi

# Enforce branch naming conventions
if [[ $command == *"checkout -b"* ]]; then
    new_branch=$(echo "$command" | grep -o 'checkout -b [^ ]*' | cut -d' ' -f3)
    if [[ ! $new_branch =~ ^(plan|feature|claude)/[a-z0-9-]+$ ]]; then
        echo "⚠️  WARNING: Non-standard branch name: $new_branch"
        echo "💡 Recommended patterns:"
        echo "   plan/<name>     - for planning phases"
        echo "   feature/<name>  - for implementation"
        echo "   claude/<name>   - for temporary work"
        echo ""
        echo "Continue anyway? (y/N)"
        read -r response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            echo "❌ Operation cancelled"
            exit 1
        fi
    else
        echo "✅ Valid branch name: $new_branch"
    fi
fi

# Track plan progression and metrics
if [[ $command == *"merge"* ]] && [[ $branch == "plan/"* ]]; then
    echo "📊 Recording plan completion metrics..."
    plan_name="${branch#plan/}"
    
    # Count commits in this plan
    commit_count=$(git rev-list --count HEAD ^master 2>/dev/null || echo "unknown")
    
    # Record metrics (simple append to log)
    metrics_file=".claude/velocity-metrics.log"
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "$timestamp,$plan_name,merge,$commit_count" >> "$metrics_file"
    
    echo "✅ Metrics recorded for plan: $plan_name"
    
    # Check for completed plans and auto-archive
    echo "🔍 Checking for completed plans to archive..."
    if python3 .claude/hooks/plan-completion-manager.py 2>/dev/null; then
        echo "✅ Plan completion scan completed"
    else
        echo "⚠️  Plan completion scan failed (non-critical)"
    fi
fi

# Validate feature branch operations
if [[ $branch == "feature/"* ]]; then
    plan_name="${branch#feature/}"
    corresponding_plan="plan/$plan_name"
    
    # Check if corresponding plan branch exists
    if git show-ref --verify --quiet "refs/heads/$corresponding_plan"; then
        echo "✅ Corresponding plan branch exists: $corresponding_plan"
    else
        echo "⚠️  WARNING: No corresponding plan branch found: $corresponding_plan"
        echo "💡 Consider creating plan branch for better workflow tracking"
    fi
fi

# Validate PR creation source branch
if [[ $command == *"gh pr create"* ]] || [[ $command == *"hub pull-request"* ]]; then
    if [[ $branch == "feature/"* ]]; then
        echo "❌ ERROR: Cannot create PR from feature branch"
        echo "📋 Workflow: PRs must be created from plan branches"
        echo "💡 Steps to fix:"
        echo "   1. Merge feature branch to plan branch:"
        echo "      git checkout plan/${branch#feature/}"
        echo "      git merge $branch"
        echo "   2. Push plan branch:"
        echo "      git push origin plan/${branch#feature/}"
        echo "   3. Create PR from plan branch"
        exit 1
    elif [[ ! $branch == "plan/"* ]] && [[ ! $branch == "master" ]]; then
        echo "⚠️  WARNING: Creating PR from non-standard branch: $branch"
        echo "💡 Recommended: Use plan/* branches for PRs"
    else
        echo "✅ PR creation from plan branch approved"
    fi
fi

# Commit message validation for conventional commits
if [[ $command == *"commit"* ]] && [[ $command == *"-m"* ]]; then
    commit_msg=$(echo "$command" | sed -n 's/.*-m[[:space:]]*["\'"'"']\([^"'"'"']*\)["\'"'"'].*/\1/p')
    
    if [[ -n "$commit_msg" ]]; then
        # Check for conventional commit format
        if [[ $commit_msg =~ ^(feat|fix|docs|test|refactor|perf|chore)(\(.+\))?: ]]; then
            echo "✅ Valid conventional commit format"
        else
            echo "⚠️  Commit message doesn't follow conventional format"
            echo "💡 Recommended: feat(module): description"
            echo "   Types: feat, fix, docs, test, refactor, perf, chore"
        fi
    fi
fi

# Prevent deletion of plan and feature branches (preserve for auditing)
if [[ $command == *"branch -d"* ]] || [[ $command == *"branch -D"* ]]; then
    branch_to_delete=$(echo "$command" | sed -n 's/.*branch -[dD] \([^ ]*\).*/\1/p')
    if [[ $branch_to_delete =~ ^(plan|feature)/ ]]; then
        echo "❌ ERROR: Cannot delete plan or feature branches"
        echo "🔒 Branches preserved for auditing purposes"
        echo "💡 If you need to clean up, use: git branch --move $branch_to_delete archived/$branch_to_delete"
        exit 1
    fi
fi

# Prevent deletion of remote plan and feature branches
if [[ $command == *"push"* ]] && [[ $command == *"--delete"* ]]; then
    branch_to_delete=$(echo "$command" | sed -n 's/.*--delete \([^ ]*\).*/\1/p')
    if [[ $branch_to_delete =~ ^(plan|feature)/ ]]; then
        echo "❌ ERROR: Cannot delete remote plan or feature branches"
        echo "🔒 Branches preserved for auditing purposes"
        echo "💡 Remote branches will remain for audit trail"
        exit 1
    fi
fi

echo "✅ Git workflow validation passed"