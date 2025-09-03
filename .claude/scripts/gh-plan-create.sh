#!/bin/bash

# GitHub Issues Plan Creation Script
# Creates a complete plan using GitHub Issues with propositions framework

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first."
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated. Run 'gh auth login' first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Main plan creation function
create_plan() {
    local plan_name="$1"
    local priority="$2"
    local domain="$3"
    
    log_info "Creating new plan: $plan_name"
    log_info "Priority: $priority, Domain: $domain"
    
    # Create overview issue
    log_info "Creating overview issue..."
    overview_url=$(gh issue create \
        --title "[Plan Overview]: $plan_name" \
        --body "Plan created using GitHub Issues migration system. Priority: $priority, Domain: $domain. Please fill out the complete propositions framework using the plan-overview.yml template structure." \
        --label "plan:overview" \
        --label "status:planning" \
        --label "priority:$(echo "$priority" | tr '[:upper:]' '[:lower:]')" \
        --label "domain:$(echo "$domain" | tr '[:upper:]' '[:lower:]')" \
        --assignee "@me")
    
    if [ $? -eq 0 ]; then
        log_success "Overview issue created: $overview_url"
        
        # Extract issue number from URL
        overview_issue=$(basename "$overview_url")
        
        # Create feature branch
        branch_name="feature/issue-${overview_issue}-$(echo "$plan_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')"
        log_info "Creating feature branch: $branch_name"
        
        git checkout -b "$branch_name" 2>/dev/null || {
            log_warning "Branch $branch_name already exists, switching to it"
            git checkout "$branch_name"
        }
        
        log_success "Feature branch created and checked out: $branch_name"
        
        echo
        log_success "Plan creation completed!"
        echo -e "Overview Issue: ${BLUE}$overview_url${NC}"
        echo -e "Feature Branch: ${BLUE}$branch_name${NC}"
        echo
        echo "Next steps:"
        echo "1. Fill out the overview issue with complete details"
        echo "2. Create phase issues using: gh-plan-phases.sh $overview_issue"
        echo "3. Begin implementation on the feature branch"
        
    else
        log_error "Failed to create overview issue"
        exit 1
    fi
}

# Interactive mode
interactive_create() {
    echo
    log_info "GitHub Issues Plan Creator"
    echo "=========================="
    echo
    
    # Get plan name
    read -p "Plan name: " plan_name
    if [ -z "$plan_name" ]; then
        log_error "Plan name is required"
        exit 1
    fi
    
    # Get priority
    echo
    echo "Priority levels:"
    echo "1) Critical"
    echo "2) High" 
    echo "3) Medium"
    echo "4) Low"
    echo
    read -p "Select priority (1-4): " priority_num
    
    case $priority_num in
        1) priority="Critical";;
        2) priority="High";;
        3) priority="Medium";;
        4) priority="Low";;
        *) log_error "Invalid priority selection"; exit 1;;
    esac
    
    # Get domain
    echo
    echo "Domain categories:"
    echo "1) Physics"
    echo "2) Data"
    echo "3) Plotting"
    echo "4) Testing"
    echo "5) Infrastructure"
    echo "6) Documentation"
    echo
    read -p "Select domain (1-6): " domain_num
    
    case $domain_num in
        1) domain="Physics";;
        2) domain="Data";;
        3) domain="Plotting";;
        4) domain="Testing";;
        5) domain="Infrastructure";;
        6) domain="Documentation";;
        *) log_error "Invalid domain selection"; exit 1;;
    esac
    
    create_plan "$plan_name" "$priority" "$domain"
}

# Command line mode
usage() {
    echo "Usage: $0 [OPTIONS] [PLAN_NAME]"
    echo
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -p, --priority LEVEL    Set priority (critical|high|medium|low)"
    echo "  -d, --domain DOMAIN     Set domain (physics|data|plotting|testing|infrastructure|docs)"
    echo "  -i, --interactive       Run in interactive mode"
    echo
    echo "Examples:"
    echo "  $0 \"Dark Mode Implementation\""
    echo "  $0 -p high -d infrastructure \"API Refactoring\""
    echo "  $0 -i"
}

# Parse command line arguments
INTERACTIVE=false
PRIORITY=""
DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--priority)
            PRIORITY="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -*|--*)
            log_error "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            PLAN_NAME="$1"
            shift
            ;;
    esac
done

# Main execution
check_prerequisites

if [ "$INTERACTIVE" = true ]; then
    interactive_create
elif [ -n "$PLAN_NAME" ]; then
    # Set defaults if not provided
    PRIORITY=${PRIORITY:-"Medium"}
    DOMAIN=${DOMAIN:-"Infrastructure"}
    
    create_plan "$PLAN_NAME" "$PRIORITY" "$DOMAIN"
else
    log_warning "No plan name provided. Running in interactive mode..."
    interactive_create
fi