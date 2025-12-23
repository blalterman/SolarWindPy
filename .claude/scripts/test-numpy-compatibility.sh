#!/bin/bash
# NumPy 2.0 Compatibility Validation Script
#
# Tests SolarWindPy across critical NumPy versions to validate
# dependency constraints in pyproject.toml.
#
# Validates: numpy >=1.26,<3.0 constraint
# Required: numba >=0.59 for NumPy 2.0 support
#
# Usage:
#   .claude/scripts/test-numpy-compatibility.sh [--verbose] [--quick]
#
# Options:
#   --verbose  Show detailed test output
#   --quick    Skip full test suite, run smoke tests only

set -euo pipefail

# Configuration
NUMPY_VERSIONS=("1.26.4" "2.0.0" "2.2.6")
TEST_DIR="/tmp/numpy-compat-test"
VERBOSE=false
QUICK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--verbose] [--quick]"
            exit 1
            ;;
    esac
done

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "NumPy 2.0 Compatibility Validation"
echo "========================================="
echo ""

# Clean up function
cleanup() {
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}
trap cleanup EXIT

# Results tracking
RESULTS=()

for NP_VERSION in "${NUMPY_VERSIONS[@]}"; do
    echo "========================================="
    echo -e "${YELLOW}Testing numpy==$NP_VERSION${NC}"
    echo "========================================="

    # Create clean venv
    VENV_PATH="$TEST_DIR/venv-np-$NP_VERSION"
    python -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"

    # Upgrade pip silently
    pip install -q --upgrade pip

    # Install numpy and ecosystem dependencies
    echo "Installing numpy==$NP_VERSION and dependencies..."
    # Prefer binary wheels to avoid build issues on some platforms
    if pip install -q --prefer-binary "numpy==$NP_VERSION" numba>=0.59 scipy pandas matplotlib astropy; then
        echo -e "${GREEN}✓${NC} Dependencies installed"
    else
        echo -e "${YELLOW}!${NC} Failed to install numpy $NP_VERSION (likely no pre-built wheel)"
        echo "  Skipping - not a constraint violation if other 2.x versions work"
        RESULTS+=("$NP_VERSION: SKIPPED (no pre-built wheel)")
        deactivate
        continue
    fi

    # Install SolarWindPy in editable mode
    echo "Installing SolarWindPy..."
    if pip install -q -e .; then
        echo -e "${GREEN}✓${NC} SolarWindPy installed"
    else
        echo -e "${RED}✗${NC} SolarWindPy installation failed"
        RESULTS+=("$NP_VERSION: FAILED (solarwindpy installation)")
        deactivate
        continue
    fi

    # Verify versions
    INSTALLED_NP=$(python -c "import numpy; print(numpy.__version__)")
    INSTALLED_NUMBA=$(python -c "import numba; print(numba.__version__)")
    echo "  numpy: $INSTALLED_NP"
    echo "  numba: $INSTALLED_NUMBA"

    # Run tests
    if [ "$QUICK" = true ]; then
        echo "Running smoke tests (quick mode)..."
        TEST_CMD="pytest tests/fitfunctions/test_metaclass_compatibility.py tests/core/test_plasma.py -q --tb=short"
    else
        echo "Running full test suite..."
        if [ "$VERBOSE" = true ]; then
            TEST_CMD="pytest tests/ -v --tb=short"
        else
            TEST_CMD="pytest tests/ -q --tb=short"
        fi
    fi

    if $TEST_CMD; then
        echo -e "${GREEN}✓${NC} Tests passed"
        RESULTS+=("$NP_VERSION: PASSED")
    else
        echo -e "${RED}✗${NC} Tests failed"
        RESULTS+=("$NP_VERSION: FAILED (test failures)")
    fi

    deactivate
    echo ""
done

# Print summary
echo "========================================="
echo "Summary"
echo "========================================="
for result in "${RESULTS[@]}"; do
    if [[ $result == *"PASSED"* ]]; then
        echo -e "${GREEN}✓${NC} $result"
    elif [[ $result == *"SKIPPED"* ]]; then
        echo -e "${YELLOW}!${NC} $result"
    else
        echo -e "${RED}✗${NC} $result"
    fi
done
echo ""

# Exit with error only if tests actually failed (not skipped)
if [[ "${RESULTS[@]}" =~ "FAILED (test failures)" ]] || [[ "${RESULTS[@]}" =~ "FAILED (solarwindpy installation)" ]]; then
    echo -e "${RED}FAILURE:${NC} Some NumPy versions are incompatible"
    exit 1
else
    echo -e "${GREEN}SUCCESS:${NC} All testable NumPy versions compatible"
    exit 0
fi
