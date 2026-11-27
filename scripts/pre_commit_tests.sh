#!/bin/bash
# Pre-Commit Test Automation Hook for SolarWindPy
# Automatically executes tests and enforces coverage before commits

set -e

echo "🧪 Running pre-commit test validation..."

# Run pytest from the solarwindpy env; see project_env.sh
ENV="$(dirname "$0")/project_env.sh"

# Check if pytest is available
if ! "$ENV" pytest --version &> /dev/null; then
    echo "❌ pytest not found. Rebuild the env from solarwindpy.yml (see CONTRIBUTING.md, Environment)"
    exit 1
fi

# Get list of staged Python files
staged_files=$(git diff --cached --name-only --diff-filter=ACMR | grep -E "\.py$" | grep -v __pycache__ || true)

if [[ -z "$staged_files" ]]; then
    echo "📋 No Python files staged for commit"
    exit 0
fi

echo "📁 Staged Python files:"
echo "$staged_files" | sed 's/^/   /'

# Run coverage analysis with required threshold.
# FLOOR is a ratchet set two points under the measured baseline (98%, measured
# with `pytest --cov=solarwindpy -q -p no:randomly` on 2026-11-19), not a
# target: it blocks regressions without blocking every commit. Raise it as
# coverage rises. A threshold above measured coverage never passes, so the hook
# only teaches people to pass --no-verify, which skips ruff along with it.
# `-n auto` runs the suite on one pytest-xdist worker per CPU; pytest-cov merges
# the workers' coverage before checking FLOOR. `--dist loadfile` keeps each test
# file on one worker, so a module fixture runs once: tests/test_release_artifacts.py
# builds the package in the repository root, and two workers building at once
# delete each other's staging directory.
FLOOR=96
echo "📊 Running coverage analysis (≥${FLOOR}% required)..."
if ! "$ENV" pytest -n auto --dist loadfile --cov=solarwindpy --cov-fail-under="$FLOOR" -q --tb=short; then
    echo ""
    echo "❌ Coverage below ${FLOOR}% threshold or tests failed"
    echo "💡 Fix failing tests and improve coverage before committing"
    echo "💡 Run 'pytest --cov=solarwindpy --cov-report=html' for detailed report"
    exit 1
fi

echo ""
echo "✅ Pre-commit test validation completed successfully"
echo "💡 Tip: Use 'pytest --cov=solarwindpy --cov-report=html' for detailed coverage"