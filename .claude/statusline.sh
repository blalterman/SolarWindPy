#!/bin/bash
# statusline.sh - Shell wrapper for Claude Code statusline integration
# 
# This script provides a shell interface to the Python statusline script
# for compatibility with Claude Code's statusLine configuration.
#
# Usage in .claude/settings.json:
#   "statusLine": {
#     "type": "command",
#     "command": ".claude/statusline.sh"
#   }

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Call the Python statusline script, passing stdin through
python3 "${SCRIPT_DIR}/statusline.py"