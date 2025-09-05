#!/bin/bash
# Setup required labels for GitHub Issues plan management
# This script ensures all required labels exist for the gh-plan-* scripts

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Setting up required GitHub labels for plan management...${NC}"
echo

# Check prerequisites
if ! command -v gh &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} GitHub CLI (gh) is not installed. Please install it first."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} GitHub CLI is not authenticated. Run 'gh auth login' first."
    exit 1
fi

echo -e "${YELLOW}Plan labels:${NC}"
gh label create "plan:overview" --description "Plan overview issue" --color "0e8a16" 2>/dev/null && echo "  ✓ plan:overview created" || echo "  • plan:overview exists"
gh label create "plan:phase" --description "Plan phase issue" --color "1d76db" 2>/dev/null && echo "  ✓ plan:phase created" || echo "  • plan:phase exists"  
gh label create "plan:closeout" --description "Plan closeout issue" --color "5319e7" 2>/dev/null && echo "  ✓ plan:closeout created" || echo "  • plan:closeout exists"

echo -e "\n${YELLOW}Priority labels:${NC}"
gh label create "priority:critical" --description "Critical priority - immediate attention required" --color "d73a49" 2>/dev/null && echo "  ✓ priority:critical created" || echo "  • priority:critical exists"
gh label create "priority:high" --description "High priority - address soon" --color "fd7e14" 2>/dev/null && echo "  ✓ priority:high created" || echo "  • priority:high exists"
gh label create "priority:medium" --description "Medium priority - normal timeline" --color "ffc107" 2>/dev/null && echo "  ✓ priority:medium created" || echo "  • priority:medium exists"
gh label create "priority:low" --description "Low priority - when time permits" --color "6c757d" 2>/dev/null && echo "  ✓ priority:low created" || echo "  • priority:low exists"

echo -e "\n${YELLOW}Status labels:${NC}"
gh label create "status:planning" --description "Currently in planning phase" --color "1f77b4" 2>/dev/null && echo "  ✓ status:planning created" || echo "  • status:planning exists"
gh label create "status:in-progress" --description "Currently being worked on" --color "2ca02c" 2>/dev/null && echo "  ✓ status:in-progress created" || echo "  • status:in-progress exists"
gh label create "status:blocked" --description "Blocked waiting for dependencies" --color "d62728" 2>/dev/null && echo "  ✓ status:blocked created" || echo "  • status:blocked exists"
gh label create "status:review" --description "Ready for review" --color "ff7f0e" 2>/dev/null && echo "  ✓ status:review created" || echo "  • status:review exists"
gh label create "status:completed" --description "Completed successfully" --color "17becf" 2>/dev/null && echo "  ✓ status:completed created" || echo "  • status:completed exists"

echo -e "\n${YELLOW}Domain labels:${NC}"
gh label create "domain:physics" --description "Physics-related plans" --color "d73a49" 2>/dev/null && echo "  ✓ domain:physics created" || echo "  • domain:physics exists"
gh label create "domain:data" --description "Data structure plans" --color "0e8a16" 2>/dev/null && echo "  ✓ domain:data created" || echo "  • domain:data exists"
gh label create "domain:plotting" --description "Plotting module plans" --color "1d76db" 2>/dev/null && echo "  ✓ domain:plotting created" || echo "  • domain:plotting exists"
gh label create "domain:testing" --description "Testing infrastructure plans" --color "fbca04" 2>/dev/null && echo "  ✓ domain:testing created" || echo "  • domain:testing exists"
gh label create "domain:infrastructure" --description "Infrastructure plans" --color "5319e7" 2>/dev/null && echo "  ✓ domain:infrastructure created" || echo "  • domain:infrastructure exists"
gh label create "domain:docs" --description "Documentation plans" --color "c5def5" 2>/dev/null && echo "  ✓ domain:docs created" || echo "  • domain:docs exists"

echo
echo -e "${GREEN}✓ All required labels are set up and ready for use${NC}"
echo -e "${BLUE}You can now use the gh-plan-* scripts to create properly labeled plans${NC}"