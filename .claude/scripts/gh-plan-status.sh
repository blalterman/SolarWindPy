#!/bin/bash

# GitHub Issues Plan Status Dashboard
# Provides comprehensive overview of all active plans

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

print_subheader() {
    echo -e "\n${PURPLE}--- $1 ---${NC}"
}

# Check prerequisites
check_prerequisites() {
    if ! command -v gh &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} GitHub CLI (gh) is not installed. Please install it first."
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} GitHub CLI is not authenticated. Run 'gh auth login' first."
        exit 1
    fi
}

# Get status badge for issue
get_status_badge() {
    local labels="$1"
    
    if echo "$labels" | grep -q "status:completed"; then
        echo -e "${GREEN}[COMPLETED]${NC}"
    elif echo "$labels" | grep -q "status:in-progress"; then
        echo -e "${YELLOW}[IN-PROGRESS]${NC}"
    elif echo "$labels" | grep -q "status:blocked"; then
        echo -e "${RED}[BLOCKED]${NC}"
    elif echo "$labels" | grep -q "status:review"; then
        echo -e "${PURPLE}[REVIEW]${NC}"
    elif echo "$labels" | grep -q "status:planning"; then
        echo -e "${BLUE}[PLANNING]${NC}"
    else
        echo -e "${CYAN}[UNKNOWN]${NC}"
    fi
}

# Get priority badge
get_priority_badge() {
    local labels="$1"
    
    if echo "$labels" | grep -q "priority:critical"; then
        echo -e "${RED}[CRITICAL]${NC}"
    elif echo "$labels" | grep -q "priority:high"; then
        echo -e "${YELLOW}[HIGH]${NC}"
    elif echo "$labels" | grep -q "priority:medium"; then
        echo -e "${BLUE}[MEDIUM]${NC}"
    elif echo "$labels" | grep -q "priority:low"; then
        echo -e "${CYAN}[LOW]${NC}"
    else
        echo -e "[NO-PRIORITY]"
    fi
}

# Get domain badge
get_domain_badge() {
    local labels="$1"
    
    if echo "$labels" | grep -q "domain:physics"; then
        echo -e "${RED}[PHYSICS]${NC}"
    elif echo "$labels" | grep -q "domain:data"; then
        echo -e "${GREEN}[DATA]${NC}"
    elif echo "$labels" | grep -q "domain:plotting"; then
        echo -e "${BLUE}[PLOTTING]${NC}"
    elif echo "$labels" | grep -q "domain:testing"; then
        echo -e "${YELLOW}[TESTING]${NC}"
    elif echo "$labels" | grep -q "domain:infrastructure"; then
        echo -e "${PURPLE}[INFRA]${NC}"
    elif echo "$labels" | grep -q "domain:docs"; then
        echo -e "${CYAN}[DOCS]${NC}"
    else
        echo -e "[NO-DOMAIN]"
    fi
}

# Display plan overview issues
show_overview_issues() {
    print_header "Plan Overview Issues"
    
    local overviews=$(gh issue list --label "plan:overview" --json number,title,labels,assignees,updatedAt --jq '.[] | @base64')
    
    if [ -z "$overviews" ]; then
        log_info "No plan overview issues found"
        return
    fi
    
    echo -e "\n${BLUE}#${NC}     ${YELLOW}Status${NC}      ${YELLOW}Priority${NC}    ${YELLOW}Domain${NC}      ${YELLOW}Title${NC}"
    echo "----  -----------  ----------  ----------  ----------------------------------------"
    
    for overview in $overviews; do
        local issue_data=$(echo "$overview" | base64 --decode)
        local number=$(echo "$issue_data" | jq -r '.number')
        local title=$(echo "$issue_data" | jq -r '.title' | sed 's/\[Plan Overview\]: //')
        local labels=$(echo "$issue_data" | jq -r '.labels[].name' | tr '\n' ',' | sed 's/,$//')
        local assignee=$(echo "$issue_data" | jq -r '.assignees[0].login // "unassigned"')
        local updated=$(echo "$issue_data" | jq -r '.updatedAt' | cut -d'T' -f1)
        
        local status=$(get_status_badge "$labels")
        local priority=$(get_priority_badge "$labels")
        local domain=$(get_domain_badge "$labels")
        
        printf "%-4s  %-11s  %-10s  %-10s  %s\n" "#$number" "$status" "$priority" "$domain" "$title"
        printf "      %-60s %s\n" "Assignee: $assignee" "Updated: $updated"
        echo
    done
}

# Display phase issues for a specific overview
show_phase_issues() {
    local overview_number="$1"
    
    if [ -z "$overview_number" ]; then
        return
    fi
    
    print_subheader "Phase Issues for Plan #$overview_number"
    
    # Find phase issues that mention the overview issue
    local phases=$(gh issue list --label "plan:phase" --search "#$overview_number" --json number,title,labels | jq -r '.[] | @base64')
    
    if [ -z "$phases" ]; then
        log_info "No phase issues found for plan #$overview_number"
        return
    fi
    
    for phase in $phases; do
        local phase_data=$(echo "$phase" | base64 --decode)
        local number=$(echo "$phase_data" | jq -r '.number')
        local title=$(echo "$phase_data" | jq -r '.title' | sed 's/\[Phase\]: //')
        local labels=$(echo "$phase_data" | jq -r '.labels[].name' | tr '\n' ',' | sed 's/,$//')
        
        local status=$(get_status_badge "$labels")
        
        printf "  Phase #%-4s  %-11s  %s\n" "$number" "$status" "$title"
    done
    echo
}

# Display summary statistics
show_summary() {
    print_header "Plan Summary Statistics"
    
    local total_overviews=$(gh issue list --label "plan:overview" --json number | jq length)
    local active_overviews=$(gh issue list --label "plan:overview,status:in-progress" --json number | jq length)
    local completed_overviews=$(gh issue list --label "plan:overview,status:completed" --json number | jq length)
    local blocked_overviews=$(gh issue list --label "plan:overview,status:blocked" --json number | jq length)
    
    local total_phases=$(gh issue list --label "plan:phase" --json number | jq length)
    local active_phases=$(gh issue list --label "plan:phase,status:in-progress" --json number | jq length)
    local completed_phases=$(gh issue list --label "plan:phase,status:completed" --json number | jq length)
    
    echo
    echo -e "${BLUE}Overview Issues:${NC}"
    echo "  Total: $total_overviews"
    echo -e "  Active: ${YELLOW}$active_overviews${NC}"
    echo -e "  Completed: ${GREEN}$completed_overviews${NC}"
    echo -e "  Blocked: ${RED}$blocked_overviews${NC}"
    
    echo
    echo -e "${BLUE}Phase Issues:${NC}"
    echo "  Total: $total_phases"
    echo -e "  Active: ${YELLOW}$active_phases${NC}"
    echo -e "  Completed: ${GREEN}$completed_phases${NC}"
    
    # Domain distribution
    echo
    echo -e "${BLUE}By Domain:${NC}"
    for domain in physics data plotting testing infrastructure docs; do
        local count=$(gh issue list --label "plan:overview,domain:$domain" --json number | jq length)
        if [ "$count" -gt 0 ]; then
            echo "  $(echo $domain | tr '[:lower:]' '[:upper:]'): $count"
        fi
    done
    
    # Priority distribution  
    echo
    echo -e "${BLUE}By Priority:${NC}"
    for priority in critical high medium low; do
        local count=$(gh issue list --label "plan:overview,priority:$priority" --json number | jq length)
        if [ "$count" -gt 0 ]; then
            echo "  $(echo $priority | tr '[:lower:]' '[:upper:]'): $count"
        fi
    done
}

# Display active work recommendations
show_recommendations() {
    print_header "Recommended Actions"
    
    # Check for blocked issues
    local blocked=$(gh issue list --label "plan:overview,status:blocked" --json number,title)
    local blocked_count=$(echo "$blocked" | jq length)
    
    if [ "$blocked_count" -gt 0 ]; then
        echo -e "${RED}🚨 Blocked Plans:${NC}"
        echo "$blocked" | jq -r '.[] | "  #\(.number): \(.title | gsub("\\[Plan Overview\\]: "; ""))"'
        echo "  Action: Review and resolve blockers"
        echo
    fi
    
    # Check for reviews
    local reviews=$(gh issue list --label "plan:overview,status:review" --json number,title)
    local review_count=$(echo "$reviews" | jq length)
    
    if [ "$review_count" -gt 0 ]; then
        echo -e "${PURPLE}📋 Plans Ready for Review:${NC}"
        echo "$reviews" | jq -r '.[] | "  #\(.number): \(.title | gsub("\\[Plan Overview\\]: "; ""))"'
        echo "  Action: Conduct plan reviews and approval"
        echo
    fi
    
    # Check for critical priority
    local critical=$(gh issue list --label "plan:overview,priority:critical,status:in-progress" --json number,title)
    local critical_count=$(echo "$critical" | jq length)
    
    if [ "$critical_count" -gt 0 ]; then
        echo -e "${RED}🔥 Critical Priority Plans:${NC}"
        echo "$critical" | jq -r '.[] | "  #\(.number): \(.title | gsub("\\[Plan Overview\\]: "; ""))"'
        echo "  Action: Focus resources on critical items"
        echo
    fi
    
    # Suggest next actions
    local planning=$(gh issue list --label "plan:overview,status:planning" --json number,title)
    local planning_count=$(echo "$planning" | jq length)
    
    if [ "$planning_count" -gt 0 ]; then
        echo -e "${BLUE}📝 Plans in Planning Phase:${NC}"
        echo "$planning" | jq -r '.[] | "  #\(.number): \(.title | gsub("\\[Plan Overview\\]: "; ""))"'
        echo "  Action: Complete planning and move to implementation"
        echo
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -s, --summary       Show only summary statistics"
    echo "  -d, --detailed      Show detailed view with phase issues"
    echo "  -r, --recommendations Show only recommendations"
    echo "  -f, --filter STATUS Filter by status (planning|in-progress|blocked|review|completed)"
    echo
    echo "Examples:"
    echo "  $0                          # Show full dashboard"
    echo "  $0 -s                       # Show summary only"
    echo "  $0 -f in-progress           # Show only in-progress plans"
    echo "  $0 -r                       # Show recommendations only"
}

# Main execution
SHOW_SUMMARY=false
SHOW_DETAILED=false
SHOW_RECOMMENDATIONS=false
FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -s|--summary)
            SHOW_SUMMARY=true
            shift
            ;;
        -d|--detailed)
            SHOW_DETAILED=true
            shift
            ;;
        -r|--recommendations)
            SHOW_RECOMMENDATIONS=true
            shift
            ;;
        -f|--filter)
            FILTER="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites

# Header
echo -e "\n${CYAN}🚀 SolarWindPy GitHub Issues Plan Dashboard${NC}"
echo -e "${CYAN}===========================================${NC}"

# Execute based on options
if [ "$SHOW_SUMMARY" = true ]; then
    show_summary
elif [ "$SHOW_RECOMMENDATIONS" = true ]; then
    show_recommendations
elif [ "$SHOW_DETAILED" = true ]; then
    show_overview_issues
    
    # Show phases for each overview
    overviews=$(gh issue list --label "plan:overview" --json number | jq -r '.[].number')
    for overview in $overviews; do
        show_phase_issues "$overview"
    done
else
    # Default: show everything
    show_overview_issues
    show_summary
    show_recommendations
fi

echo