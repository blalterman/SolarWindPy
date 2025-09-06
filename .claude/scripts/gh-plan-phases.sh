#!/bin/bash

# GitHub Issues Phase Creator
# Creates phase issues linked to a plan overview

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
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed. Please install it first."
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI is not authenticated. Run 'gh auth login' first."
        exit 1
    fi
}

# Validate required labels exist
validate_labels() {
    log_info "Validating required labels exist..."
    
    local missing_labels=()
    
    # Get all labels once for efficiency (with pagination)
    local all_labels=$(gh label list --limit 100 --json name | jq -r '.[].name')
    log_info "Found $(echo "$all_labels" | wc -l) labels in repository" >&2
    
    # Check plan labels (phases.sh specifically needs plan:phase and plan:closeout)
    for label in "plan:phase" "plan:closeout"; do
        if ! echo "$all_labels" | grep -q "^${label}$"; then
            missing_labels+=("$label")
        fi
    done
    
    # Check status labels
    for status in planning in-progress blocked review completed; do
        if ! echo "$all_labels" | grep -q "^status:${status}$"; then
            missing_labels+=("status:$status")
        fi
    done
    
    if [ ${#missing_labels[@]} -gt 0 ]; then
        log_error "Missing required labels:"
        for label in "${missing_labels[@]}"; do
            echo "  - $label"
        done
        echo
        log_warning "Run the following to create them:"
        echo "  bash .claude/scripts/setup-labels.sh"
        exit 1
    fi
    
    log_success "All required labels are available"
}

# Validate overview issue exists
validate_overview() {
    local overview_issue="$1"
    
    log_info "Validating overview issue #$overview_issue..."
    
    local issue_info=$(gh issue view "$overview_issue" --json labels,title 2>/dev/null || true)
    
    if [ -z "$issue_info" ]; then
        log_error "Issue #$overview_issue not found"
        exit 1
    fi
    
    local has_overview_label=$(echo "$issue_info" | jq -r '.labels[] | select(.name == "plan:overview") | .name' || true)
    
    if [ -z "$has_overview_label" ]; then
        log_error "Issue #$overview_issue is not a plan overview issue (missing plan:overview label)"
        exit 1
    fi
    
    local title=$(echo "$issue_info" | jq -r '.title')
    log_success "Valid overview issue found: $title"
    
    echo "$title"
}

# Generate comprehensive phase content
generate_phase_content() {
    local overview_issue="$1"
    local phase_number="$2"
    local phase_name="$3"
    local estimated_duration="$4"
    local dependencies="$5"
    
    # Get overview issue title for context
    local plan_title=$(gh issue view "$overview_issue" --json title --jq '.title' 2>/dev/null | sed 's/\[Plan Overview\]: //g' || echo "Unknown Plan")
    
    cat <<EOF
# Phase $phase_number: $phase_name

## 🎯 Phase Objective
Implement $phase_name as part of the overall plan: $plan_title

## 🧠 Phase Context
This is Phase $phase_number of the implementation plan. It focuses on $phase_name with an estimated duration of $estimated_duration.

## 📋 Implementation Tasks

### Task Group 1: Core Implementation
- [ ] **Design and Architecture** (Est: 2 hours) - Define technical approach and design patterns
  - Commit: \`<checksum>\`
  - Status: Pending
  - Notes: Create technical design document and validate approach

- [ ] **Core Implementation** (Est: 4-6 hours) - Implement main functionality
  - Commit: \`<checksum>\`
  - Status: Pending  
  - Notes: Follow SolarWindPy coding conventions and physics validation requirements

- [ ] **Integration Testing** (Est: 2 hours) - Validate integration with existing system
  - Commit: \`<checksum>\`
  - Status: Pending
  - Notes: Ensure compatibility with existing physics calculations and data structures

### Task Group 2: Quality Assurance  
- [ ] **Unit Tests** (Est: 2 hours) - Create comprehensive test coverage
  - Commit: \`<checksum>\`
  - Status: Pending
  - Notes: Target ≥95% coverage following SolarWindPy testing standards

- [ ] **Documentation** (Est: 1 hour) - Update documentation and examples
  - Commit: \`<checksum>\`
  - Status: Pending
  - Notes: Include NumPy-style docstrings and usage examples

## ✅ Phase Acceptance Criteria
- [ ] All task group implementations completed and tested
- [ ] Integration tests passing with existing SolarWindPy modules
- [ ] Code coverage ≥95% for new functionality
- [ ] Documentation updated with clear examples
- [ ] Physics validation requirements satisfied (if applicable)
- [ ] Pre-commit hooks passing (black, flake8, pytest)

## 🧪 Phase Testing Strategy
**Testing Approach:**
- Unit tests for individual functions and classes
- Integration tests with existing SolarWindPy components
- Physics validation tests (if applicable)
- Performance benchmarks for critical paths

**Test Categories:**
- Functional correctness
- Edge case handling  
- Error condition management
- Scientific accuracy validation

## 🔧 Phase Technical Requirements
**Dependencies:** $dependencies
**Duration:** $estimated_duration
**Priority:** Phase $phase_number implementation

**Technical Constraints:**
- Follow SolarWindPy hierarchical DataFrame patterns
- Maintain SI unit conventions internally
- Preserve NaN handling for missing data
- Ensure backward compatibility

## 📂 Phase Affected Areas
**Primary Impact:**
- Implementation area specific to $phase_name

**Secondary Impact:**
- Related testing modules
- Documentation and examples
- Integration points with existing functionality

## 📊 Phase Progress Tracking
**Completion Status:** 0% (0/10 tasks completed)

**Progress Metrics:**
- [ ] Design complete
- [ ] Implementation complete  
- [ ] Testing complete
- [ ] Documentation complete
- [ ] Integration validated

## 💬 Phase Implementation Notes
**Implementation Priority:** Sequential execution recommended
**Key Considerations:**
- Maintain SolarWindPy coding standards throughout
- Coordinate with physics validation if core modules affected
- Update cross-references to overview issue #$overview_issue

## 🔄 Context Management Points
**Session Boundaries:**
- Complete task groups as atomic units
- Create compacted states after significant milestones
- Preserve implementation decision rationale

**Token Optimization:**
- Use structured progress updates
- Link commits to specific tasks for efficient context
- Maintain clear success criteria for each task

## 👤 Phase Completion Instructions
**When Ready to Mark Complete:**
1. Verify all acceptance criteria met
2. Update progress tracking to 100%
3. Link all commits to respective tasks
4. Update overview issue #$overview_issue with completion status
5. Create compacted state for session continuity

## 🔗 Related Issues
**Plan Overview:** #$overview_issue
**Dependencies:** $dependencies
**Next Phase:** Will be determined based on overall plan structure

---
*This phase is part of the comprehensive GitHub Issues Plan Management System. Use structured task tracking to maintain implementation quality and progress visibility.*
EOF
}

# Create a single phase issue
create_phase() {
    local overview_issue="$1"
    local phase_number="$2"
    local phase_name="$3"
    local estimated_duration="$4"
    local dependencies="$5"
    
    log_info "Creating Phase $phase_number: $phase_name"
    
    # Generate comprehensive phase content
    local phase_body
    phase_body=$(generate_phase_content "$overview_issue" "$phase_number" "$phase_name" "$estimated_duration" "$dependencies")
    
    # Create phase issue with comprehensive content
    local phase_url=$(gh issue create \
        --title "[Phase]: Phase $phase_number - $phase_name" \
        --body "$phase_body" \
        --label "plan:phase" \
        --label "status:planning" \
        --assignee "@me")
    
    if [ $? -eq 0 ]; then
        local phase_issue=$(basename "$phase_url")
        log_success "Phase issue created: $phase_url"
        
        # Add comment to overview linking to phase
        gh issue comment "$overview_issue" --body "Phase $phase_number: #$phase_issue - $phase_name"
        
        # Add comment to phase linking to overview
        gh issue comment "$phase_issue" --body "Part of Plan Overview: #$overview_issue"
        
        echo "$phase_issue"
    else
        log_error "Failed to create phase issue"
        return 1
    fi
}

# Interactive phase creation
interactive_phase_creation() {
    local overview_issue="$1"
    local plan_title="$2"
    
    echo
    log_info "Creating phases for: $plan_title"
    echo "=================================="
    
    local phase_issues=()
    local phase_num=1
    
    while true; do
        echo
        log_info "Phase $phase_num Configuration"
        echo "-----------------------------"
        
        read -p "Phase name (or 'done' to finish): " phase_name
        
        if [ "$phase_name" = "done" ] || [ -z "$phase_name" ]; then
            break
        fi
        
        read -p "Estimated duration (e.g., 2-3 hours): " duration
        if [ -z "$duration" ]; then
            duration="TBD"
        fi
        
        read -p "Dependencies (optional): " dependencies
        
        local phase_issue=$(create_phase "$overview_issue" "$phase_num" "$phase_name" "$duration" "$dependencies")
        
        if [ $? -eq 0 ]; then
            phase_issues+=("$phase_issue")
            ((phase_num++))
        else
            log_warning "Failed to create phase, continuing..."
        fi
    done
    
    if [ ${#phase_issues[@]} -eq 0 ]; then
        log_warning "No phases were created"
        return
    fi
    
    echo
    log_success "Phase creation completed!"
    echo -e "Created ${#phase_issues[@]} phases for plan #$overview_issue"
    echo
    echo "Phase Issues:"
    for i in "${!phase_issues[@]}"; do
        local phase_num=$((i + 1))
        echo "  Phase $phase_num: #${phase_issues[$i]}"
    done
    
    echo
    echo "Next steps:"
    echo "1. Fill out each phase issue with detailed tasks"
    echo "2. Set dependencies between phases if needed"
    echo "3. Begin implementation starting with Phase 1"
    echo "4. Use 'gh-plan-status.sh' to monitor progress"
}

# Batch phase creation from configuration
batch_phase_creation() {
    local overview_issue="$1"
    local config_file="$2"
    
    if [ ! -f "$config_file" ]; then
        log_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    log_info "Creating phases from configuration file: $config_file"
    
    local phase_issues=()
    local phase_num=1
    
    while IFS='|' read -r phase_name duration dependencies; do
        # Skip empty lines and comments
        if [[ -z "$phase_name" || "$phase_name" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        local phase_issue=$(create_phase "$overview_issue" "$phase_num" "$phase_name" "$duration" "$dependencies")
        
        if [ $? -eq 0 ]; then
            phase_issues+=("$phase_issue")
            ((phase_num++))
        else
            log_warning "Failed to create phase: $phase_name"
        fi
    done < "$config_file"
    
    log_success "Batch phase creation completed!"
    echo -e "Created ${#phase_issues[@]} phases from configuration"
}

# Create closeout issue
create_closeout() {
    local overview_issue="$1"
    local plan_title="$2"
    
    log_info "Creating closeout issue for: $plan_title"
    
    local closeout_url=$(gh issue create \
        --template plan-closeout.yml \
        --title "[Closeout]: $plan_title" \
        --label "plan:closeout,status:planning" \
        --assignee "@me")
    
    if [ $? -eq 0 ]; then
        local closeout_issue=$(basename "$closeout_url")
        log_success "Closeout issue created: $closeout_url"
        
        # Link to overview
        gh issue comment "$overview_issue" --body "Closeout Issue: #$closeout_issue"
        gh issue comment "$closeout_issue" --body "Plan Overview: #$overview_issue"
        
        echo "$closeout_issue"
    else
        log_error "Failed to create closeout issue"
        return 1
    fi
}

# Usage information
usage() {
    echo "Usage: $0 [OPTIONS] OVERVIEW_ISSUE"
    echo
    echo "Create phase issues linked to a plan overview issue"
    echo
    echo "Arguments:"
    echo "  OVERVIEW_ISSUE      GitHub issue number of the plan overview"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -i, --interactive   Interactive phase creation (default)"
    echo "  -b, --batch FILE    Batch create phases from configuration file"
    echo "  -c, --closeout      Also create a closeout issue"
    echo
    echo "Configuration file format (for batch mode):"
    echo "  phase_name|estimated_duration|dependencies"
    echo "  Foundation Setup|2-3 hours|None"
    echo "  Core Implementation|4-5 hours|Phase 1"
    echo "  Testing & Validation|1-2 hours|Phase 2"
    echo
    echo "Examples:"
    echo "  $0 123                              # Interactive mode"
    echo "  $0 -i 123                           # Interactive mode (explicit)"
    echo "  $0 -b phases.conf 123               # Batch mode from file"
    echo "  $0 -c 123                           # Interactive + closeout"
}

# Parse command line arguments
INTERACTIVE=true
BATCH_FILE=""
CREATE_CLOSEOUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -b|--batch)
            BATCH_FILE="$2"
            INTERACTIVE=false
            shift 2
            ;;
        -c|--closeout)
            CREATE_CLOSEOUT=true
            shift
            ;;
        -*|--*)
            log_error "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            OVERVIEW_ISSUE="$1"
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$OVERVIEW_ISSUE" ]; then
    log_error "Overview issue number is required"
    usage
    exit 1
fi

# Main execution
check_prerequisites
validate_labels

plan_title=$(validate_overview "$OVERVIEW_ISSUE")

if [ "$INTERACTIVE" = true ]; then
    interactive_phase_creation "$OVERVIEW_ISSUE" "$plan_title"
elif [ -n "$BATCH_FILE" ]; then
    batch_phase_creation "$OVERVIEW_ISSUE" "$BATCH_FILE"
fi

# Create closeout issue if requested
if [ "$CREATE_CLOSEOUT" = true ]; then
    echo
    create_closeout "$OVERVIEW_ISSUE" "$plan_title"
fi

echo
log_info "Phase creation process completed!"
log_info "Use 'gh-plan-status.sh' to view the updated plan status"