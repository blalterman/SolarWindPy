#!/bin/bash
#
# Physics compliance validation script for CI/CD integration.
#
# This script validates SolarWindPy code for physics correctness and can be
# integrated into GitHub Actions, pre-commit hooks, or other CI/CD systems.
#

set -e  # Exit on any error

# Configuration
VALIDATOR_SCRIPT="physics_compliance_validator.py"
FAST_MODE="--fast"
TOLERANCE="--tolerance 0.1"
OUTPUT_DIR="validation_reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    case $2 in
        "error")   echo -e "${RED}✗ $1${NC}" ;;
        "success") echo -e "${GREEN}✓ $1${NC}" ;;
        "warning") echo -e "${YELLOW}⚠ $1${NC}" ;;
        *)         echo "$1" ;;
    esac
}

# Function to run validation
run_validation() {
    local description="$1"
    local pattern="$2"
    local output_file="$3"
    
    echo "Validating $description..."
    
    if python "$VALIDATOR_SCRIPT" "$pattern" $FAST_MODE $TOLERANCE --output "$output_file" 2>/dev/null; then
        print_status "$description: COMPLIANT" "success"
        return 0
    else
        print_status "$description: NON-COMPLIANT" "error"
        return 1
    fi
}

# Main validation function
main() {
    print_status "SolarWindPy Physics Compliance Validation" ""
    echo "=========================================="
    
    # Check if validator exists
    if [[ ! -f "$VALIDATOR_SCRIPT" ]]; then
        print_status "Validator script not found: $VALIDATOR_SCRIPT" "error"
        exit 1
    fi
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Track overall success
    overall_success=0
    
    # Validate documentation
    if [[ -f "docs/source/usage.rst" ]]; then
        if run_validation "Documentation examples" "docs/source/usage.rst" "$OUTPUT_DIR/documentation.txt"; then
            ((overall_success++))
        fi
    else
        print_status "Documentation not found, skipping" "warning"
    fi
    
    # Validate core modules
    if run_validation "Core modules" "solarwindpy/core/*.py" "$OUTPUT_DIR/core_modules.txt"; then
        ((overall_success++))
    fi
    
    # Validate plotting modules
    if run_validation "Plotting modules" "solarwindpy/plotting/*.py" "$OUTPUT_DIR/plotting_modules.txt"; then
        ((overall_success++))
    fi
    
    # Validate fitfunctions modules
    if run_validation "Fitfunctions modules" "solarwindpy/fitfunctions/*.py" "$OUTPUT_DIR/fitfunctions_modules.txt"; then
        ((overall_success++))
    fi
    
    # Generate summary
    echo ""
    echo "Validation Summary:"
    echo "=================="
    
    if [[ $overall_success -eq 4 ]]; then
        print_status "All validations passed!" "success"
        echo "Reports saved in: $OUTPUT_DIR/"
        exit 0
    elif [[ $overall_success -ge 2 ]]; then
        print_status "Most validations passed, some issues found" "warning"
        echo "Check reports in: $OUTPUT_DIR/"
        exit 0
    else
        print_status "Multiple validation failures detected" "error"
        echo "Check reports in: $OUTPUT_DIR/"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --strict       Use strict tolerance (0.05)"
        echo "  --lenient      Use lenient tolerance (0.15)"
        echo "  --no-fast      Disable fast mode (run full analysis)"
        echo ""
        echo "Environment variables:"
        echo "  PHYSICS_TOLERANCE  Override default tolerance"
        echo "  PHYSICS_OUTPUT_DIR Override output directory"
        exit 0
        ;;
    "--strict")
        TOLERANCE="--tolerance 0.05"
        print_status "Using strict tolerance (5%)" "warning"
        ;;
    "--lenient")
        TOLERANCE="--tolerance 0.15"
        print_status "Using lenient tolerance (15%)" "warning"
        ;;
    "--no-fast")
        FAST_MODE=""
        print_status "Full analysis mode enabled" "warning"
        ;;
esac

# Override with environment variables if set
if [[ -n "${PHYSICS_TOLERANCE:-}" ]]; then
    TOLERANCE="--tolerance $PHYSICS_TOLERANCE"
fi

if [[ -n "${PHYSICS_OUTPUT_DIR:-}" ]]; then
    OUTPUT_DIR="$PHYSICS_OUTPUT_DIR"
fi

# Run main validation
main