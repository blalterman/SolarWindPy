#!/usr/bin/env bash
# Check commit message follows Conventional Commits format
# Usage: check-conventional-commits.sh <commit-msg-file>

commit_msg_file="$1"
commit_msg=$(cat "$commit_msg_file")

# Define pattern in variable (required for bash [[ =~ ]] to work correctly)
pattern='^(feat|fix|chore|docs|style|refactor|test|perf)(\(.+\))?: .+'

if [[ $commit_msg =~ $pattern ]]; then
    echo "✅ Valid conventional commit format"
    exit 0
else
    cat <<EOF
❌ Commit message must follow Conventional Commits format.

Format: <type>(<scope>): <description>

Types: feat, fix, docs, test, refactor, perf, chore
Scope: optional (e.g., 'labels', 'core', 'plotting')

Examples:
  feat(plotting): add new color scheme
  fix(core): correct thermal speed calculation
  docs: update README with installation steps

Your message:
  $commit_msg
EOF
    exit 1
fi
