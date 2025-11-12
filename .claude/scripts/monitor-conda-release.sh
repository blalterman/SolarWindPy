#!/bin/bash
# SolarWindPy Conda-forge Release Monitor
#
# Monitors the conda-forge release process for SolarWindPy by tracking:
# - Time elapsed since tracking issue creation
# - Conda-forge bot PR creation and status
# - CI check results
# - Package availability
#
# Usage: .claude/scripts/monitor-conda-release.sh <issue_number>
#
# Examples:
#   .claude/scripts/monitor-conda-release.sh 403        # Monitor v0.2.0 release
#   .claude/scripts/monitor-conda-release.sh 450        # Monitor future release
#
# Exit Codes:
#   0 - PR merged successfully or package available
#   1 - Normal waiting state (bot monitoring, CI pending, etc.)
#   2 - Action needed (>12h no PR, CI failures, etc.)
#
# Prerequisites:
#   - gh (GitHub CLI) installed and authenticated
#   - Internet connectivity
#
# Cross-platform: Works on macOS (BSD) and Linux (GNU)

set -euo pipefail

# Colors for output
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly RED='\033[0;31m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_WAITING=1
readonly EXIT_ACTION_NEEDED=2

# Time thresholds (in minutes)
readonly MIN_WAIT_MINUTES=120  # 2 hours - earliest expected PR
readonly MAX_WAIT_MINUTES=360  # 6 hours - latest typical PR
readonly CRITICAL_WAIT_MINUTES=720  # 12 hours - manual intervention recommended

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    local version="$1"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}   SolarWindPy ${version} Conda-forge Release Monitor${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
}

print_section() {
    local icon="$1"
    local title="$2"
    echo -e "${YELLOW}${icon} ${title}${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

usage() {
    cat <<EOF
Usage: $(basename "$0") <issue_number>

Monitor conda-forge release process for SolarWindPy.

Arguments:
    issue_number    GitHub issue number for conda-forge tracking (e.g., 403)

Examples:
    $(basename "$0") 403    # Monitor release from Issue #403
    $(basename "$0") 450    # Monitor release from Issue #450

Exit Codes:
    0 - PR merged successfully or package available
    1 - Normal waiting state (bot monitoring, CI pending, etc.)
    2 - Action needed (>12h no PR, CI failures, etc.)

Prerequisites:
    - gh (GitHub CLI) must be installed and authenticated
    - Run 'gh auth status' to verify authentication
EOF
}

# ============================================================================
# Validation Functions
# ============================================================================

check_prerequisites() {
    # Check for gh CLI
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        echo "Install via: brew install gh (macOS) or see https://cli.github.com"
        exit 2
    fi

    # Check gh authentication
    if ! gh auth status &> /dev/null; then
        print_error "GitHub CLI is not authenticated"
        echo "Run: gh auth login"
        exit 2
    fi
}

validate_issue() {
    local issue_num="$1"

    # Check if issue exists
    if ! gh issue view "$issue_num" &> /dev/null; then
        print_error "Issue #${issue_num} not found"
        echo "Verify the issue number and try again"
        exit 2
    fi

    # Check if issue has required labels
    local labels
    labels=$(gh issue view "$issue_num" --json labels --jq '.labels[].name' | tr '\n' ' ')

    if [[ ! "$labels" =~ conda-feedstock ]]; then
        print_warning "Issue #${issue_num} does not have 'conda-feedstock' label"
        echo "This may not be a conda-forge tracking issue"
        echo
    fi
}

# ============================================================================
# Data Extraction Functions
# ============================================================================

extract_version_from_issue() {
    local issue_num="$1"
    local body
    body=$(gh issue view "$issue_num" --json body --jq '.body')

    # Extract version from "**Version**: `X.Y.Z`" pattern
    if [[ "$body" =~ \*\*Version\*\*:[[:space:]]*\`([0-9]+\.[0-9]+\.[0-9]+)\` ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        print_error "Could not extract version from issue body"
        echo "Expected format: **Version**: \`X.Y.Z\`"
        exit 2
    fi
}

extract_sha256_from_issue() {
    local issue_num="$1"
    local body
    body=$(gh issue view "$issue_num" --json body --jq '.body')

    # Extract SHA256 from "**SHA256**: `hash`" pattern
    if [[ "$body" =~ \*\*SHA256\*\*:[[:space:]]*\`([a-f0-9]{64})\` ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "unknown"
    fi
}

extract_pypi_url_from_issue() {
    local issue_num="$1"
    local body
    body=$(gh issue view "$issue_num" --json body --jq '.body')

    # Extract PyPI URL from "**PyPI URL**: URL" pattern
    if [[ "$body" =~ \*\*PyPI\ URL\*\*:[[:space:]]*(https://[^[:space:]]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "https://pypi.org/project/solarwindpy/"
    fi
}

get_issue_created_time() {
    local issue_num="$1"
    gh issue view "$issue_num" --json createdAt --jq '.createdAt'
}

# ============================================================================
# Time Calculation Functions
# ============================================================================

calculate_elapsed_time() {
    local release_time="$1"
    local release_epoch
    local current_epoch

    # Cross-platform epoch conversion
    if date --version &> /dev/null 2>&1; then
        # GNU date (Linux)
        release_epoch=$(date -d "$release_time" +%s 2>/dev/null || echo "0")
    else
        # BSD date (macOS) - remove trailing Z and treat as UTC
        local time_without_z="${release_time%Z}"
        release_epoch=$(date -juf "%Y-%m-%dT%H:%M:%S" "$time_without_z" +%s 2>/dev/null || echo "0")
    fi

    current_epoch=$(date -u +%s)

    if [ "$release_epoch" -eq 0 ]; then
        print_error "Failed to parse timestamp: $release_time"
        exit 2
    fi

    local elapsed_seconds=$((current_epoch - release_epoch))
    local elapsed_minutes=$((elapsed_seconds / 60))

    echo "$elapsed_minutes"
}

format_elapsed_time() {
    local elapsed_minutes="$1"
    local hours=$((elapsed_minutes / 60))
    local minutes=$((elapsed_minutes % 60))

    if [ "$hours" -gt 0 ]; then
        echo "${hours}h ${minutes}m"
    else
        echo "${minutes}m"
    fi
}

get_time_status_message() {
    local elapsed_minutes="$1"

    if [ "$elapsed_minutes" -lt "$MIN_WAIT_MINUTES" ]; then
        local remaining=$((MIN_WAIT_MINUTES - elapsed_minutes))
        echo -e "${GREEN}Within normal window (${remaining}m until earliest expected)${NC}"
    elif [ "$elapsed_minutes" -lt "$MAX_WAIT_MINUTES" ]; then
        echo -e "${YELLOW}Bot should create PR soon (within expected 2-6h window)${NC}"
    elif [ "$elapsed_minutes" -lt "$CRITICAL_WAIT_MINUTES" ]; then
        local overtime=$((elapsed_minutes - MAX_WAIT_MINUTES))
        echo -e "${YELLOW}Outside typical window by ${overtime}m, still monitoring${NC}"
    else
        local overtime=$((elapsed_minutes - CRITICAL_WAIT_MINUTES))
        echo -e "${RED}⚠ Manual intervention recommended (${overtime}m past 12h threshold)${NC}"
    fi
}

# ============================================================================
# PR Detection Functions
# ============================================================================

find_prs_for_version() {
    local version="$1"

    # Search for PRs with version in title
    gh pr list --repo conda-forge/solarwindpy-feedstock \
        --state open \
        --json number,title,author,createdAt,url \
        --jq ".[] | select(.title | test(\"${version}\"; \"i\"))"
}

count_open_prs() {
    gh pr list --repo conda-forge/solarwindpy-feedstock \
        --state open \
        --json number \
        --jq '. | length'
}

get_pr_ci_status() {
    local pr_num="$1"

    # Get CI status, suppress errors if no checks yet
    gh pr checks "$pr_num" --repo conda-forge/solarwindpy-feedstock 2>/dev/null || echo "No CI checks yet"
}

check_pr_merged() {
    local version="$1"

    # Check if there's a merged PR for this version
    local merged_count
    merged_count=$(gh pr list --repo conda-forge/solarwindpy-feedstock \
        --state merged \
        --search "$version in:title" \
        --json number \
        --jq '. | length')

    [ "$merged_count" -gt 0 ]
}

# ============================================================================
# Display Functions
# ============================================================================

display_time_status() {
    local release_time="$1"
    local elapsed_minutes="$2"

    print_section "⏱️ " "Time Status"
    echo "   Release created: $release_time"
    echo "   Current time:    $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "   Time elapsed:    $(format_elapsed_time "$elapsed_minutes")"
    echo -n "   Status:          "
    get_time_status_message "$elapsed_minutes"
    echo
}

display_release_details() {
    local version="$1"
    local sha256="$2"
    local pypi_url="$3"

    print_section "📦" "Release Details"
    echo "   Version: $version"
    echo "   PyPI:    $pypi_url"
    if [ "$sha256" != "unknown" ]; then
        echo "   SHA256:  $sha256"
    fi
    echo
}

display_no_pr_status() {
    local elapsed_minutes="$1"

    print_section "🔍" "Conda-forge Feedstock Status"
    echo -e "   ${YELLOW}Open PRs: 0 (bot has not created PR yet)${NC}"
    echo "   Bot is unblocked and monitoring PyPI..."
    echo
}

display_pr_status() {
    local version="$1"
    local pr_data="$2"

    print_section "🔍" "Conda-forge Feedstock Status"

    local pr_count
    pr_count=$(echo "$pr_data" | jq -s 'length')
    echo -e "   ${GREEN}Open PRs: $pr_count${NC}"
    echo

    # Display each PR
    echo "$pr_data" | jq -r '. | "   PR #\(.number): \(.title)\n   Author: \(.author.login)\n   Created: \(.createdAt)\n   URL: \(.url)\n"'

    # Display CI status
    print_section "🔧" "CI Status"
    echo "$pr_data" | jq -r '.number' | while read -r pr_num; do
        echo "   PR #${pr_num}:"
        get_pr_ci_status "$pr_num" | sed 's/^/      /'
        echo
    done
}

display_next_steps_no_pr() {
    local elapsed_minutes="$1"

    print_section "📋" "Next Steps"

    if [ "$elapsed_minutes" -lt "$MIN_WAIT_MINUTES" ]; then
        echo "   • Wait for bot to create PR (typical: 2-6 hours from release)"
        echo "   • Run this script again in 30-60 minutes"
        echo "   • Bot checks PyPI every 2-6 hours"
    elif [ "$elapsed_minutes" -lt "$MAX_WAIT_MINUTES" ]; then
        echo "   • Bot should create PR within the next 1-2 hours"
        echo "   • Run this script again in 30 minutes"
        echo "   • Check feedstock for any related issues or announcements"
    elif [ "$elapsed_minutes" -lt "$CRITICAL_WAIT_MINUTES" ]; then
        echo "   • Continue monitoring, bot may be delayed"
        echo "   • Check conda-forge status: https://conda-forge.org/status/"
        echo "   • Run this script again in 1 hour"
    else
        echo -e "   ${RED}• Manual intervention recommended (>12h elapsed)${NC}"
        echo "   • Create manual PR (see RELEASING.md for steps)"
        echo "   • Check conda-forge Gitter for bot status"
        echo "   • Review feedstock issues for related problems"
    fi
}

display_next_steps_with_pr() {
    local pr_data="$1"

    print_section "📋" "Next Steps"
    echo "   1. Review PR content (version, SHA256, dependencies)"
    echo "   2. Monitor CI checks (15-30 minutes typical)"
    echo "   3. Check CI status: gh pr checks <PR_NUM> --repo conda-forge/solarwindpy-feedstock --watch"
    echo "   4. Review and approve, or wait for bot auto-merge"
    echo "   5. After merge, verify package (2-4 hours): conda search -c conda-forge solarwindpy"
    echo "   6. Close tracking issue with success comment"
}

display_next_steps_merged() {
    local version="$1"

    print_section "📋" "Next Steps"
    echo -e "   ${GREEN}✓ PR has been merged!${NC}"
    echo
    echo "   1. Wait 2-4 hours for conda package build"
    echo "   2. Verify package availability:"
    echo "      conda search -c conda-forge solarwindpy"
    echo "   3. Test installation:"
    echo "      conda create -n test-release python=3.11 -y"
    echo "      conda activate test-release"
    echo "      conda install -c conda-forge solarwindpy"
    echo "      python -c \"import solarwindpy; print(solarwindpy.__version__)\""
    echo "   4. Close tracking issue with success message"
}

display_quick_reference() {
    local issue_num="$1"
    local version="$2"

    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    print_section "📖" "Quick Reference Commands"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
    echo "# Re-run this monitor:"
    echo "  $(basename "$0") $issue_num"
    echo
    echo "# Check tracking issue:"
    echo "  gh issue view $issue_num"
    echo
    echo "# List feedstock PRs:"
    echo "  gh pr list --repo conda-forge/solarwindpy-feedstock --state open"
    echo
    echo "# Watch PR CI checks (when PR exists):"
    echo "  gh pr checks <PR_NUM> --repo conda-forge/solarwindpy-feedstock --watch"
    echo
    echo "# View PR details:"
    echo "  gh pr view <PR_NUM> --repo conda-forge/solarwindpy-feedstock"
    echo
    echo "# Check conda package availability:"
    echo "  conda search -c conda-forge solarwindpy"
    echo
    echo "# Close tracking issue (after success):"
    echo "  gh issue close $issue_num --comment 'v${version} successfully released to conda-forge'"
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# Main Logic
# ============================================================================

main() {
    # Parse arguments
    if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        usage
        exit 0
    fi

    local issue_num="$1"
    local exit_code=$EXIT_WAITING

    # Validate prerequisites and issue
    check_prerequisites
    validate_issue "$issue_num"

    # Extract data from issue
    local version
    local sha256
    local pypi_url
    local release_time

    version=$(extract_version_from_issue "$issue_num")
    sha256=$(extract_sha256_from_issue "$issue_num")
    pypi_url=$(extract_pypi_url_from_issue "$issue_num")
    release_time=$(get_issue_created_time "$issue_num")

    # Calculate elapsed time
    local elapsed_minutes
    elapsed_minutes=$(calculate_elapsed_time "$release_time")

    # Display header
    print_header "v${version}"

    # Display time status
    display_time_status "$release_time" "$elapsed_minutes"

    # Display release details
    display_release_details "$version" "$sha256" "$pypi_url"

    # Check for merged PR first
    if check_pr_merged "$version"; then
        print_section "🔍" "Conda-forge Feedstock Status"
        echo -e "   ${GREEN}✓ PR for v${version} has been merged!${NC}"
        echo
        display_next_steps_merged "$version"
        exit_code=$EXIT_SUCCESS
    else
        # Check for open PRs
        local pr_data
        pr_data=$(find_prs_for_version "$version")

        if [ -z "$pr_data" ]; then
            # No PR found
            display_no_pr_status "$elapsed_minutes"
            display_next_steps_no_pr "$elapsed_minutes"

            # Determine exit code based on elapsed time
            if [ "$elapsed_minutes" -gt "$CRITICAL_WAIT_MINUTES" ]; then
                exit_code=$EXIT_ACTION_NEEDED
            else
                exit_code=$EXIT_WAITING
            fi
        else
            # PR found
            display_pr_status "$version" "$pr_data"
            display_next_steps_with_pr "$pr_data"
            exit_code=$EXIT_WAITING
        fi
    fi

    # Display quick reference
    display_quick_reference "$issue_num" "$version"

    exit $exit_code
}

# Run main function
main "$@"
