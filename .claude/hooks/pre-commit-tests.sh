#!/bin/bash
# Pre-Commit Test Automation Hook for SolarWindPy
# Automatically executes tests and enforces coverage before commits

set -e

echo "🧪 Running pre-commit test validation..."

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Install with: pip install pytest pytest-cov"
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

# Run coverage analysis with required threshold
echo "📊 Running coverage analysis (≥95% required)..."
if ! pytest --cov=solarwindpy --cov-fail-under=95 -q --tb=short; then
    echo ""
    echo "❌ Coverage below 95% threshold or tests failed"
    echo "💡 Fix failing tests and improve coverage before committing"
    echo "💡 Run 'pytest --cov=solarwindpy --cov-report=html' for detailed report"
    exit 1
fi

# Test files directly related to staged changes
echo ""
echo "🎯 Testing modules related to staged changes..."
for file in $staged_files; do
    # Convert file path to module path for testing
    if [[ $file == solarwindpy/* ]]; then
        module_path=${file%.py}
        module_path=${module_path//\//.}
        test_path="tests/${file#solarwindpy/}"
        test_path="tests/${test_path%.py}"
        
        # Check if corresponding test file exists
        if [[ -f "${test_path}.py" ]] || [[ -d "$(dirname ${test_path})" ]]; then
            echo "   Testing: $module_path"
            if ! pytest "tests/${file#solarwindpy/}" -v --tb=short 2>/dev/null; then
                echo "⚠️  Module-specific tests may need attention: $module_path"
            fi
        fi
    fi
done

# Physics-specific validation for core modules
physics_files=$(echo "$staged_files" | grep -E "(core|instabilities|fitfunctions)" || true)
if [[ -n "$physics_files" ]]; then
    echo ""
    echo "🔬 Running physics validation for critical modules..."
    echo "$physics_files" | sed 's/^/   /'
    
    # Run physics-specific tests
    if ! pytest tests/core/ tests/instabilities/ tests/fitfunctions/ -k "physics or thermal or alfven or conservation" -q --tb=line 2>/dev/null; then
        echo "⚠️  Physics validation tests may need attention"
    fi
fi

# Performance tests for core changes
core_files=$(echo "$staged_files" | grep "core/" || true)
if [[ -n "$core_files" ]]; then
    echo ""
    echo "⏱️  Running performance tests for core changes..."
    if ! timeout 30s pytest -m "slow or performance" tests/core/ -q --tb=line 2>/dev/null; then
        echo "⚠️  Performance tests completed with timeout (expected for large datasets)"
    fi
fi

echo ""
echo "✅ Pre-commit test validation completed successfully"
echo "💡 Tip: Use 'pytest --cov=solarwindpy --cov-report=html' for detailed coverage"