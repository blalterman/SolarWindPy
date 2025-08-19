#!/bin/bash
# Input Validation Helper for SolarWindPy Hooks
# Sanitizes and validates inputs to prevent injection attacks

sanitize_filename() {
    local filename="$1"
    # Remove dangerous characters and paths
    echo "$filename" | sed 's/[;&|`$()<>]//g' | sed 's/\.\.\///g'
}

sanitize_pattern() {
    local pattern="$1" 
    # Remove dangerous shell characters but keep regex valid
    echo "$pattern" | sed 's/[;&|`$()<>]//g'
}

validate_python_file() {
    local filepath="$1"
    
    # Check if file exists and has .py extension
    if [[ ! -f "$filepath" ]]; then
        echo "ERROR: File does not exist: $filepath" >&2
        return 1
    fi
    
    if [[ ! "$filepath" =~ \.py$ ]]; then
        echo "ERROR: Not a Python file: $filepath" >&2
        return 1
    fi
    
    # Check if file is in allowed directories
    if [[ ! "$filepath" =~ ^(solarwindpy|tests|\.claude)/ ]]; then
        echo "ERROR: File outside allowed directories: $filepath" >&2
        return 1
    fi
    
    return 0
}

validate_test_pattern() {
    local pattern="$1"
    
    # Check pattern length (prevent DoS)
    if [[ ${#pattern} -gt 100 ]]; then
        echo "ERROR: Test pattern too long (max 100 chars): $pattern" >&2
        return 1
    fi
    
    # Sanitize pattern
    pattern=$(sanitize_pattern "$pattern")
    
    # Check for dangerous patterns
    if [[ "$pattern" =~ (rm|delete|drop|truncate) ]]; then
        echo "ERROR: Dangerous pattern detected: $pattern" >&2
        return 1
    fi
    
    echo "$pattern"
    return 0
}

validate_git_command() {
    local command="$1"
    
    # Only allow safe git commands
    local allowed_commands="status diff log branch checkout add commit push pull"
    local cmd_word=$(echo "$command" | awk '{print $1}')
    
    if [[ ! " $allowed_commands " =~ " $cmd_word " ]]; then
        echo "ERROR: Git command not allowed: $cmd_word" >&2
        return 1
    fi
    
    # Check for dangerous flags
    if [[ "$command" =~ (--force|-f) ]] && [[ "$command" =~ (push|checkout) ]]; then
        echo "WARNING: Potentially dangerous git command: $command" >&2
    fi
    
    return 0
}

# Export functions for use in other hooks
export -f sanitize_filename
export -f sanitize_pattern  
export -f validate_python_file
export -f validate_test_pattern
export -f validate_git_command