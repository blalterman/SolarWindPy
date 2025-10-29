#!/usr/bin/env python3
"""
statusline.py - Enhanced SolarWindPy statusline for Claude Code (Max Plan Optimized)

This Python script generates a rich, color-coded statusline showing:
- Model name, current directory, conda environment, git branch
- Token usage with context window limit (200k for Max plan)
- Active plan branch indicator (SolarWindPy workflow)
- Git status (uncommitted changes, ahead/behind)
- Test coverage percentage (≥95% requirement)
- Session duration tracking (Max plan time management)

OPTIMIZED FOR CLAUDE MAX PLAN:
- No cost tracking (fixed monthly fee)
- Focus on token/context limits, not dollars
- SolarWindPy-specific workflow integration

Integration with Claude Code:
This script is wrapped by statusline.sh for easy Claude Code integration.
Configure in .claude/settings.json:
    "statusLine": {
      "type": "command",
      "command": ".claude/statusline.sh"
    }

Direct usage:
    echo '{}' | python3 statusline.py
"""
import json
import sys
import os
import subprocess
from pathlib import Path
import time
import re
from datetime import datetime, timezone


# ANSI color codes for terminal output
class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    @staticmethod
    def colorize(text, color):
        """Apply color to text if terminal supports it."""
        if os.getenv("NO_COLOR") or not sys.stdout.isatty():
            return text
        return f"{color}{text}{Colors.RESET}"

    @staticmethod
    def red(text):
        return Colors.colorize(text, Colors.RED)

    @staticmethod
    def yellow(text):
        return Colors.colorize(text, Colors.YELLOW)

    @staticmethod
    def green(text):
        return Colors.colorize(text, Colors.GREEN)


# Thresholds for Claude Max plan
class Thresholds:
    # Context window limits (Max plan: 200k tokens)
    CONTEXT_LIMIT = 200_000
    CONTEXT_YELLOW = 150_000  # 75% of context window
    CONTEXT_RED = 180_000     # 90% of context window

    # Coverage thresholds (SolarWindPy requirement: ≥95%)
    COVERAGE_EXCELLENT = 95.0  # Required minimum
    COVERAGE_WARNING = 90.0    # Below target

    # Session duration thresholds (hours)
    SESSION_YELLOW_HOURS = 4   # Long session
    SESSION_RED_HOURS = 8      # Very long session


def get_model_name(data):
    """Extract model display name from JSON data."""
    return data.get("model", {}).get("display_name", "Claude")


def get_current_dir(data):
    """Get basename of current directory."""
    current_dir = data.get("workspace", {}).get("current_dir", os.getcwd())
    return os.path.basename(current_dir)


def get_git_branch():
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip() or "main"
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_conda_env():
    """Get current conda environment name."""
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda_env and conda_env != "base":
        return conda_env
    return ""


def get_recent_compaction_info():
    """Get information about recent compactions to adjust token estimates."""
    try:
        # Look for compaction files in .claude directory
        claude_dir = Path(".claude")
        if not claude_dir.exists():
            return None

        # Find most recent compaction file
        compaction_files = list(claude_dir.glob("compaction-*.md"))
        if not compaction_files:
            return None

        # Get the most recently modified compaction file
        recent_compaction = max(compaction_files, key=lambda f: f.stat().st_mtime)

        # Check if it's recent (within last 10 minutes)
        file_age = time.time() - recent_compaction.stat().st_mtime
        if file_age > 600:  # 10 minutes
            return None

        # Parse the compaction file for target tokens
        with open(recent_compaction, "r") as f:
            content = f.read()

        # Extract target tokens from the compaction metadata
        target_match = re.search(r"Target Tokens.*?~(\d+(?:,\d+)*)", content)
        if target_match:
            target_tokens = int(target_match.group(1).replace(",", ""))
            return {
                "target_tokens": target_tokens,
                "file_age_minutes": file_age / 60,
                "filename": recent_compaction.name,
            }

        return None
    except Exception:
        return None


def estimate_token_usage(data):
    """Estimate token usage from transcript file with context limit display."""
    try:
        transcript_path = data.get("transcript_path", "")
        if not transcript_path or not os.path.exists(transcript_path):
            return "0/200k"

        # Rough estimate: ~4 chars per token
        file_size = os.path.getsize(transcript_path)
        estimated_tokens = file_size // 4

        # Check for recent compaction and adjust if needed
        compaction_info = get_recent_compaction_info()
        if compaction_info:
            target_with_buffer = compaction_info["target_tokens"] + (
                estimated_tokens * 0.1
            )
            if estimated_tokens > target_with_buffer:
                estimated_tokens = int(target_with_buffer)

        # Format with context limit
        if estimated_tokens > 1000:
            token_str = f"{estimated_tokens//1000:.0f}k"
        else:
            token_str = str(estimated_tokens)

        usage_display = f"{token_str}/200k"

        # Apply color coding based on context window thresholds
        if estimated_tokens >= Thresholds.CONTEXT_RED:
            return Colors.red(usage_display)
        elif estimated_tokens >= Thresholds.CONTEXT_YELLOW:
            return Colors.yellow(usage_display)
        else:
            return Colors.green(usage_display)
    except:
        return "0/200k"


def get_plan_info():
    """Check if on a plan branch and extract plan name."""
    branch = get_git_branch()
    if branch and branch.startswith("plan/"):
        plan_name = branch.replace("plan/", "")
        return plan_name
    return None


def get_git_status_indicators():
    """Get git status: uncommitted changes, ahead/behind."""
    indicators = []

    try:
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            indicators.append("●")  # Uncommitted changes

        # Check ahead/behind remote
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                ahead, behind = map(int, parts)
                if ahead > 0:
                    indicators.append(f"↑{ahead}")
                if behind > 0:
                    indicators.append(f"↓{behind}")
    except:
        pass

    return "".join(indicators) if indicators else ""


def get_coverage_percentage():
    """Get current test coverage from .coverage file."""
    try:
        from coverage import Coverage

        coverage_file = Path(".coverage")
        if not coverage_file.exists():
            return None

        # Load coverage data
        cov = Coverage()
        cov.load()

        # Get total coverage percentage
        total = cov.report(show_missing=False, file=open(os.devnull, 'w'))

        # Color code based on SolarWindPy requirements
        if total >= Thresholds.COVERAGE_EXCELLENT:
            return Colors.green(f"✓{total:.0f}%")
        elif total >= Thresholds.COVERAGE_WARNING:
            return Colors.yellow(f"⚠{total:.0f}%")
        else:
            return Colors.red(f"✗{total:.0f}%")
    except:
        return None


def get_session_duration(data):
    """Get human-readable session duration from API data."""
    duration_ms = data.get("cost", {}).get("total_duration_ms", 0)

    if duration_ms == 0:
        return "0m"

    hours = duration_ms // (1000 * 3600)
    minutes = (duration_ms % (1000 * 3600)) // (1000 * 60)

    # Format duration string
    if hours > 0:
        duration_str = f"{hours}h{minutes}m"
    else:
        duration_str = f"{minutes}m"

    # Color code based on session length
    if hours >= Thresholds.SESSION_RED_HOURS:
        return Colors.red(duration_str)
    elif hours >= Thresholds.SESSION_YELLOW_HOURS:
        return Colors.yellow(duration_str)
    else:
        return Colors.green(duration_str)


def create_status_line(data):
    """Create the enhanced status line (Max plan optimized)."""
    # Get all components
    model = get_model_name(data)
    current_dir = get_current_dir(data)
    conda_env = get_conda_env()
    git_branch = get_git_branch()
    git_status = get_git_status_indicators()
    plan_name = get_plan_info()
    tokens = estimate_token_usage(data)
    coverage = get_coverage_percentage()
    duration = get_session_duration(data)

    # Build status line components
    parts = [f"[{model}]", f"📁 {current_dir}"]

    # Add conda environment
    if conda_env:
        parts.append(f"🐍 {conda_env}")

    # Add git branch with status indicators
    if git_branch:
        branch_display = f"🌿 {git_branch}{git_status}"
        parts.append(branch_display)

    # Add plan indicator (if on plan branch)
    if plan_name:
        parts.append(f"📋 {plan_name}")

    # Add token usage (context window awareness)
    parts.append(f"🔤 {tokens}")

    # Add coverage (if available)
    if coverage:
        parts.append(f"🎯 {coverage}")

    # Add session duration
    parts.append(f"⏱️ {duration}")

    return " | ".join(parts)


if __name__ == "__main__":
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)
        print(create_status_line(data))
    except Exception as e:
        # Fallback status line
        print(f"[Claude] 📁 {os.path.basename(os.getcwd())} | ❌ Error")
