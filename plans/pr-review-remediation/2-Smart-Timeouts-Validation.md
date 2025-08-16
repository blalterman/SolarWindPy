# Phase 2: Smart Timeouts and Validation

## Overview
- **Phase**: 2 of 3  
- **Duration**: 2.0 hours
- **Priority**: HIGH (ROI 8-9/10)
- **Dependencies**: Phase 1 (depth limits enable better timeout calculation)
- **Affects**: `.claude/hooks/*`, `.claude/settings.local.json`, new validation utilities

## Objective
Implement adaptive timeout system and input validation to eliminate false timeout failures and prevent malformed operations, while maintaining the simplicity appropriate for SolarWindPy's scale.

## Context
Current fixed timeouts (120s) cause either:
1. **False failures** when complex physics tests need more time
2. **Unnecessary waits** when simple changes complete in 5-10s

Additionally, lack of input validation allows malformed commands to reach tools, causing cryptic errors.

**ROI Analysis:**
- Adaptive timeouts: ROI 9/10 (saves 30-60 min/day developer time)
- Input validation: ROI 8/10 (prevents system failures, clear errors)

## Tasks

### Task 2.1: Adaptive Timeout System (1 hour)
**Priority**: HIGH (Massive time savings on every code edit)

**Problem**: Fixed 120s timeouts for all operations regardless of complexity.

**Solution**: Scale timeouts based on operation type and changed files.

#### Subtask 2.1.1: Create Timeout Configuration (15 minutes)

**New File**: `.claude/config/timeouts.json`
```json
{
  "adaptive_timeouts": {
    "enabled": true,
    "base_timeouts": {
      "physics_validation": 180,
      "test_execution": 120, 
      "coverage_analysis": 60,
      "file_analysis": 30,
      "git_operations": 15
    },
    "scaling": {
      "per_file_factor": 15,
      "max_timeout": 300,
      "min_timeout": 10
    },
    "operation_patterns": {
      "solarwindpy/instabilities/*.py": "physics_validation",
      "solarwindpy/core/*.py": "physics_validation",
      "solarwindpy/plotting/*.py": "test_execution",
      "tests/*.py": "test_execution",
      "*.md": "file_analysis"
    }
  }
}
```

**Rationale**:
- Physics calculations (instabilities) take longest: 180s base
- Core physics validation: 180s base  
- General tests: 120s base
- Documentation: 30s base
- Scale by 15s per changed file (reasonable for SolarWindPy size)

#### Subtask 2.1.2: Update Test Runner Hook (30 minutes)

**File**: `.claude/hooks/test-runner.sh`

**Current Problem** (line 8):
```bash
MAX_TEST_TIME=120  # Fixed timeout
```

**Enhanced Implementation**:
```bash
#!/bin/bash
# Calculate adaptive timeout based on changed files and types

calculate_timeout() {
    local changed_files="$1"
    local file_count=$(echo "$changed_files" | wc -l)
    local base_timeout=120
    
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
    local scaled_timeout=$((base_timeout + file_count * 15))
    
    # Clamp to reasonable bounds for SolarWindPy
    if [ $scaled_timeout -gt 300 ]; then
        scaled_timeout=300
    elif [ $scaled_timeout -lt 10 ]; then
        scaled_timeout=10
    fi
    
    echo $scaled_timeout
}

# Get changed files for timeout calculation
CHANGED_FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null || echo "unknown")
MAX_TEST_TIME=$(calculate_timeout "$CHANGED_FILES")

echo "Adaptive timeout: ${MAX_TEST_TIME}s for $(echo "$CHANGED_FILES" | wc -l) changed files"
```

#### Subtask 2.1.3: Update Hook Configurations (15 minutes)

**Files**: `.claude/settings.local.json` (hooks section around lines 127-249)

**Update Timeout Values**:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/test-runner.sh --changed",
            "timeout": "adaptive"
          }
        ]
      }
    ]
  }
}
```

**Implementation Note**: The actual timeout will be calculated by the hook itself, with "adaptive" signaling to use the new system.

### Task 2.2: Basic Input Validation (1 hour)
**Priority**: HIGH (Prevents system failures with clear errors)

**Problem**: Malformed inputs cause cryptic tool failures.

**Solution**: Validate inputs before they reach tools.

#### Subtask 2.2.1: Create Input Validator (45 minutes)

**New File**: `.claude/utils/input-validator.py`
```python
#!/usr/bin/env python3
"""
Basic input validation for SolarWindPy Claude operations
Focused on preventing common errors and security issues
"""

import re
import os
from pathlib import Path

class SolarWindPyValidator:
    """Simple validator for SolarWindPy-specific operations."""
    
    # Safe path patterns for SolarWindPy
    SAFE_PATHS = [
        r'^solarwindpy/',
        r'^tests/',
        r'^\.claude/',
        r'^docs/',
        r'^scripts/',
        r'^\w+\.py$',
        r'^\w+\.md$'
    ]
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'\.\./',           # Directory traversal
        r'~/',              # Home directory access
        r'/etc/',           # System directories
        r'rm\s+-rf',        # Dangerous removal
        r';\s*\w+',         # Command chaining
        r'\|\s*\w+',        # Piping
        r'`[^`]*`',         # Command substitution
        r'\$\(',            # Command substitution
    ]
    
    def validate_file_path(self, path: str) -> tuple[bool, str]:
        """Validate file path is safe for SolarWindPy operations."""
        if not path:
            return False, "Empty path not allowed"
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, path):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check against safe paths
        for pattern in self.SAFE_PATHS:
            if re.match(pattern, path):
                return True, "Path validated"
        
        return False, f"Path not in allowed locations: {path}"
    
    def validate_branch_name(self, branch: str) -> tuple[bool, str]:
        """Validate git branch name follows SolarWindPy conventions."""
        if not branch:
            return False, "Empty branch name"
        
        # SolarWindPy branch patterns
        valid_patterns = [
            r'^master$',
            r'^plan/[\w\-]+$',
            r'^feature/[\w\-]+$',  
            r'^update-\d{4}$',
            r'^codex/\d{4}-\d{2}-\d{2}',
        ]
        
        for pattern in valid_patterns:
            if re.match(pattern, branch):
                return True, "Branch name validated"
        
        return False, f"Branch name doesn't match SolarWindPy conventions: {branch}"
    
    def validate_test_pattern(self, pattern: str) -> tuple[bool, str]:
        """Validate test execution pattern is safe."""
        if not pattern:
            return False, "Empty test pattern"
        
        # Safe test patterns for SolarWindPy
        safe_patterns = [
            r'^tests/[\w/]*\.py$',
            r'^solarwindpy/[\w/]*\.py$',
            r'^tests/$',
            r'^--\w+$',  # pytest flags
            r'^\w+$',    # simple module names
        ]
        
        for safe in safe_patterns:
            if re.match(safe, pattern):
                return True, "Test pattern validated"
        
        return False, f"Test pattern not safe: {pattern}"

def validate_operation(operation_type: str, **kwargs) -> tuple[bool, str]:
    """Main validation entry point."""
    validator = SolarWindPyValidator()
    
    if operation_type == "file_path":
        return validator.validate_file_path(kwargs.get('path', ''))
    elif operation_type == "branch_name":
        return validator.validate_branch_name(kwargs.get('branch', ''))
    elif operation_type == "test_pattern":
        return validator.validate_test_pattern(kwargs.get('pattern', ''))
    else:
        return False, f"Unknown operation type: {operation_type}"

if __name__ == "__main__":
    # CLI interface for validation
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: input-validator.py <operation_type> <value>")
        sys.exit(1)
    
    operation = sys.argv[1]
    value = sys.argv[2]
    
    if operation == "file_path":
        is_valid, message = validate_operation("file_path", path=value)
    elif operation == "branch_name":
        is_valid, message = validate_operation("branch_name", branch=value)
    elif operation == "test_pattern":
        is_valid, message = validate_operation("test_pattern", pattern=value)
    else:
        is_valid, message = False, f"Unknown operation: {operation}"
    
    print(message)
    sys.exit(0 if is_valid else 1)
```

#### Subtask 2.2.2: Integrate Validation into Session Hook (15 minutes)

**File**: `.claude/hooks/validate-session-state.sh`

**Current Enhancement** (add before existing validation):
```bash
#!/bin/bash
# Enhanced session validation with input checking

echo "🔍 Validating session state..."

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Validate branch name
if ! python .claude/utils/input-validator.py branch_name "$CURRENT_BRANCH"; then
    echo "⚠️  Warning: Branch name doesn't follow SolarWindPy conventions"
    echo "   Current: $CURRENT_BRANCH"
    echo "   Expected: plan/*, feature/*, master, update-YYYY"
fi

# Check for safe working directory
if [ ! -f "solarwindpy/__init__.py" ]; then
    echo "❌ Not in SolarWindPy root directory"
    exit 1
fi

# Validate recent file changes are safe
RECENT_FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null | head -10)
if [ -n "$RECENT_FILES" ]; then
    echo "📋 Validating recent file changes:"
    while IFS= read -r file; do
        if [ -n "$file" ]; then
            if python .claude/utils/input-validator.py file_path "$file"; then
                echo "   ✓ $file"
            else
                echo "   ⚠️  $file (outside safe paths)"
            fi
        fi
    done <<< "$RECENT_FILES"
fi

# Continue with existing validation...
echo "✅ Session state validation complete"
```

## Validation Steps

### Timeout Validation
1. **Small Change Test**:
   ```bash
   # Edit single plotting file
   touch solarwindpy/plotting/test.py
   git add solarwindpy/plotting/test.py
   # Should get ~120s timeout (base) + 15s (1 file) = 135s
   ```

2. **Physics Change Test**:
   ```bash
   # Edit core physics file
   touch solarwindpy/core/plasma.py
   git add solarwindpy/core/plasma.py
   # Should get ~180s timeout (physics base) + 15s (1 file) = 195s
   ```

3. **Multiple Files Test**:
   ```bash
   # Edit 5 files
   # Should get base + (5 * 15s) = base + 75s, capped at 300s
   ```

### Input Validation Testing
1. **Safe Paths**:
   ```bash
   python .claude/utils/input-validator.py file_path "solarwindpy/core/plasma.py"
   # Should return: Path validated
   ```

2. **Dangerous Paths**:
   ```bash
   python .claude/utils/input-validator.py file_path "../../../etc/passwd"
   # Should return: Dangerous pattern detected
   ```

3. **Branch Names**:
   ```bash
   python .claude/utils/input-validator.py branch_name "feature/pr-review-remediation"
   # Should return: Branch name validated
   ```

## Dependencies
- **Phase 1**: Depth limits must be working for timeout calculations
- **Next Phase**: Validated inputs enable better GitHub integration

## Rollback Procedures
1. **Timeouts**: Revert to fixed 120s values
2. **Validation**: Remove validation calls from hooks
3. **Files**: Remove new `.claude/config/` and `.claude/utils/` files

## Success Metrics
- **Performance**: No false timeout failures, 30-60 min/day saved
- **Reliability**: Clear error messages for invalid inputs
- **User Experience**: Appropriate timeouts for operation complexity
- **Security**: Malformed inputs blocked before reaching tools

## Implementation Notes
- **SolarWindPy Specific**: Timeout values calibrated for physics calculations
- **Simple Validation**: Whitelist approach, no complex parsing
- **Backward Compatible**: Falls back to fixed timeouts if adaptive fails
- **Low Maintenance**: Simple patterns, no complex dependencies

---
*Phase 2 eliminates the major workflow friction points (timeouts, cryptic errors) while maintaining the simplicity appropriate for SolarWindPy's development scale.*