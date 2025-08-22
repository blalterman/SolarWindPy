#!/bin/bash
# Tag Validation Hook for SolarWindPy
# Validates that git tags follow proper conventions:
# - Release tags: v{major}.{minor}.{patch}[-{prerelease}] (semantic versioning)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏷️  Validating git tag conventions...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get all tags
ALL_TAGS=$(git tag --list 2>/dev/null || echo "")

if [ -z "$ALL_TAGS" ]; then
    echo -e "${GREEN}✅ No tags found - validation passed${NC}"
    exit 0
fi

# Validation patterns
VERSION_TAG_PATTERN="^v[0-9]+\.[0-9]+\.[0-9]+(-.+)?$"

# Counters
VALID_VERSION_TAGS=0
INVALID_TAGS=0

echo -e "${BLUE}📋 Analyzing tags...${NC}"

# Validate each tag - only check version tags, ignore non-version tags
while IFS= read -r tag; do
    if [[ $tag =~ $VERSION_TAG_PATTERN ]]; then
        echo -e "${GREEN}✅ Version tag: $tag${NC}"
        ((VALID_VERSION_TAGS++))
    elif [[ $tag =~ ^claude/compaction/ ]]; then
        # Silently skip compaction tags (operational, not for validation)
        continue
    else
        # Only flag truly invalid tags, not operational ones
        if [[ ! $tag =~ ^claude/ ]]; then
            echo -e "${RED}❌ Invalid tag: $tag${NC}"
            echo -e "${YELLOW}   Expected format: v1.0.0, v2.1.3-alpha, v1.5.0-beta.2${NC}"
            ((INVALID_TAGS++))
        fi
    fi
done <<< "$ALL_TAGS"

echo ""
echo -e "${BLUE}📊 Validation Summary:${NC}"
echo -e "${GREEN}   ✅ Valid version tags: $VALID_VERSION_TAGS${NC}"

if [ $INVALID_TAGS -gt 0 ]; then
    echo -e "${RED}   ❌ Invalid tags: $INVALID_TAGS${NC}"
    echo ""
    echo -e "${YELLOW}🔧 To fix invalid tags:${NC}"
    echo -e "${YELLOW}   1. Delete problematic tags: git tag -d <tag-name>${NC}"
    echo -e "${YELLOW}   2. Create properly formatted tags${NC}"
    echo -e "${YELLOW}   3. Re-run validation: .claude/hooks/validate-tags.sh${NC}"
    echo ""
    exit 1
else
    echo -e "${GREEN}   🎉 All tags follow proper conventions!${NC}"
fi

echo ""
echo -e "${BLUE}🔍 setuptools_scm Configuration Check:${NC}"

# Check if setuptools_scm configuration exists
if grep -q "\[tool\.setuptools_scm\]" pyproject.toml 2>/dev/null; then
    echo -e "${GREEN}✅ setuptools_scm is configured in pyproject.toml${NC}"
    
    # Check for version tag filtering
    if grep -q "tag_regex.*v.*" pyproject.toml 2>/dev/null; then
        echo -e "${GREEN}✅ Version tag filtering is configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Version tag filtering not found${NC}"
    fi
    
    # Check for git describe command filtering
    if grep -q "git_describe_command.*match.*v" pyproject.toml 2>/dev/null; then
        echo -e "${GREEN}✅ Git describe filtering is configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Git describe filtering not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  setuptools_scm not configured in pyproject.toml${NC}"
    echo -e "${YELLOW}   Consider adding [tool.setuptools_scm] section for version management${NC}"
fi

echo ""
echo -e "${GREEN}✅ Tag validation complete${NC}"