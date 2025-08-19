#!/bin/bash
# Smart Test Runner Hook for SolarWindPy
# Intelligently selects and runs tests based on changes and context

set -e

# Configuration
PARALLEL_JOBS=4

# Calculate adaptive timeout based on file types and count
calculate_timeout() {
    local changed_files="$1"
    local file_count=0
    local base_timeout=120
    
    if [[ -n "$changed_files" ]]; then
        file_count=$(echo "$changed_files" | wc -l | tr -d ' ')
        
        # Check for physics files (need more time)
        if echo "$changed_files" | grep -q "solarwindpy/instabilities/\|solarwindpy/core/"; then
            base_timeout=180
        elif echo "$changed_files" | grep -q "solarwindpy/plotting/"; then
            base_timeout=120
        elif echo "$changed_files" | grep -q "tests/"; then
            base_timeout=120
        else
            base_timeout=60
        fi
        
        # Scale by file count (15s per file)
        local timeout=$((base_timeout + file_count * 15))
        
        # Apply bounds
        if [[ $timeout -gt 300 ]]; then
            timeout=300
        elif [[ $timeout -lt 30 ]]; then
            timeout=30
        fi
        
        echo $timeout
    else
        echo 120  # Default for all tests
    fi
}

# Default timeout (will be overridden by adaptive calculation)
MAX_TEST_TIME=120

show_help() {
    echo "SolarWindPy Smart Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [PATTERN]"
    echo ""
    echo "Options:"
    echo "  --all          Run all tests"
    echo "  --changed      Run tests for changed files only"
    echo "  --physics      Run physics validation tests"
    echo "  --fast         Skip slow tests"
    echo "  --coverage     Include coverage analysis"
    echo "  --help         Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --changed           # Test only changed modules"
    echo "  $0 --physics           # Run physics validation"
    echo "  $0 test_plasma         # Run specific test pattern"
    echo "  $0 --coverage --fast   # Fast tests with coverage"
}

# Parse arguments
RUN_ALL=false
RUN_CHANGED=false
RUN_PHYSICS=false
SKIP_SLOW=false
WITH_COVERAGE=false
PATTERN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --changed)
            RUN_CHANGED=true
            shift
            ;;
        --physics)
            RUN_PHYSICS=true
            shift
            ;;
        --fast)
            SKIP_SLOW=true
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            PATTERN="$1"
            shift
            ;;
    esac
done

echo "🧪 SolarWindPy Smart Test Runner"
echo "⏱️  Timeout: ${MAX_TEST_TIME}s (adaptive) | Parallel: ${PARALLEL_JOBS} jobs"

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS="-n $PARALLEL_JOBS --tb=short"

# Add coverage if requested
if [[ "$WITH_COVERAGE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=solarwindpy --cov-report=term-missing"
    echo "📊 Coverage analysis enabled"
fi

# Skip slow tests if requested
if [[ "$SKIP_SLOW" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
    echo "⚡ Skipping slow tests"
fi

# Determine what tests to run
TEST_TARGETS=""

if [[ "$RUN_ALL" == "true" ]]; then
    echo "🎯 Running all tests"
    TEST_TARGETS="tests/"
    
elif [[ "$RUN_CHANGED" == "true" ]]; then
    echo "🎯 Running tests for changed files"
    
    # Get changed files (staged + unstaged)
    changed_files=$(git diff --name-only HEAD^ HEAD 2>/dev/null || git diff --name-only)
    changed_py_files=$(echo "$changed_files" | grep -E "\.py$" | grep -v __pycache__ || true)
    
    if [[ -z "$changed_py_files" ]]; then
        echo "📋 No Python files changed"
        exit 0
    fi
    
    # Calculate adaptive timeout based on changed files
    MAX_TEST_TIME=$(calculate_timeout "$changed_py_files")
    
    echo "📁 Changed files:"
    echo "$changed_py_files" | sed 's/^/   /'
    
    # Convert source files to test targets
    for file in $changed_py_files; do
        if [[ $file == solarwindpy/* ]]; then
            # Map source file to test file
            test_file="tests/${file#solarwindpy/}"
            test_dir=$(dirname "$test_file")
            
            # Add test targets (file or directory)
            if [[ -f "$test_file" ]]; then
                TEST_TARGETS="$TEST_TARGETS $test_file"
            elif [[ -d "$test_dir" ]]; then
                TEST_TARGETS="$TEST_TARGETS $test_dir"
            fi
        elif [[ $file == tests/* ]]; then
            # Direct test file
            TEST_TARGETS="$TEST_TARGETS $file"
        fi
    done
    
    if [[ -z "$TEST_TARGETS" ]]; then
        echo "📋 No corresponding tests found for changed files"
        exit 0
    fi
    
elif [[ "$RUN_PHYSICS" == "true" ]]; then
    echo "🔬 Running physics validation tests"
    TEST_TARGETS="tests/core/ tests/instabilities/"
    PYTEST_ARGS="$PYTEST_ARGS -k 'physics or thermal or alfven or conservation or instability'"
    # Physics tests need more time
    MAX_TEST_TIME=180
    
elif [[ -n "$PATTERN" ]]; then
    echo "🔍 Running tests matching pattern: $PATTERN"
    TEST_TARGETS="tests/"
    PYTEST_ARGS="$PYTEST_ARGS -k '$PATTERN'"
    
else
    echo "🎯 Running default test suite (core + essential)"
    # Use default timeout for full test suite
    MAX_TEST_TIME=120
    TEST_TARGETS="tests/core/ tests/fitfunctions/"
fi

# Final command construction
FULL_CMD="timeout ${MAX_TEST_TIME}s $PYTEST_CMD $PYTEST_ARGS $TEST_TARGETS"

echo ""
echo "🚀 Executing: $FULL_CMD"
echo ""

# Run tests with proper error handling
if eval "$FULL_CMD"; then
    echo ""
    echo "✅ Tests completed successfully"
    
    # Show summary if coverage was run
    if [[ "$WITH_COVERAGE" == "true" ]]; then
        echo ""
        echo "📊 Coverage summary available"
        echo "💡 Use 'pytest --cov=solarwindpy --cov-report=html' for detailed report"
    fi
    
else
    exit_code=$?
    echo ""
    
    if [[ $exit_code == 124 ]]; then
        echo "⏱️  Tests timed out after ${MAX_TEST_TIME}s"
        echo "💡 Consider running smaller test subsets or optimizing slow tests"
    else
        echo "❌ Tests failed with exit code: $exit_code"
        echo ""
        echo "💡 Debugging suggestions:"
        echo "   - Run with -v for verbose output"
        echo "   - Use -x to stop on first failure"
        echo "   - Run specific test: pytest tests/path/to/test.py::test_function"
        echo "   - Check physics constraints and numerical stability"
    fi
    
    exit $exit_code
fi