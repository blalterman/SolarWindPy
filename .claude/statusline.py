#!/usr/bin/env python3
"""
statusline.py - Enhanced SolarWindPy statusline for Claude Code

This Python script generates a rich, color-coded statusline showing:
- Model name with visual indicators (Opus=green, Haiku=yellow, Sonnet=default)
- Current directory, conda environment, git branch with status
- REAL token usage from Claude API (not file size estimation)
- Prompt cache efficiency percentage (hit rate)
- Code edit activity (lines added/removed per session)
- Test coverage percentage (≥95% requirement)
- Session duration tracking with color coding

OPTIMIZED FOR CLAUDE CODE API DATA:
- Uses actual context_window.current_usage data from API
- Prompt caching analytics (cache_read / total_input)
- Model-agnostic (adapts to different context window sizes)
- Graceful degradation if data unavailable

NEW IN THIS VERSION:
- Real API token counts (replaces transcript file estimation)
- Cache efficiency indicator (shows prompt caching performance)
- Edit activity tracker (productivity metrics)
- Enhanced model detection with color coding

Integration with Claude Code:
This script is wrapped by statusline.sh for easy Claude Code integration.
Configure in .claude/settings.json:
    "statusLine": {
      "type": "command",
      "command": ".claude/statusline.sh"
    }

Direct usage:
    echo '{"context_window": {...}, "cost": {...}}' | python3 statusline.py
"""
import json
import sys
import os
import subprocess
from pathlib import Path


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


# Configuration for optional status line features
class Config:
    """Feature toggles for status line components.

    Set to False to disable specific indicators and reduce status line length.
    """

    # Phase 3: Optional advanced components (disabled by default)
    SHOW_API_EFFICIENCY = False  # API time vs total time ratio
    SHOW_SESSION_SOURCE = False  # How session started (resume/compact/fresh)

    # Core components (always enabled)
    SHOW_MODEL = True
    SHOW_DIRECTORY = True
    SHOW_CONDA_ENV = True
    SHOW_GIT_BRANCH = True
    SHOW_PLAN_NAME = True
    SHOW_TOKENS = True
    SHOW_CACHE_EFFICIENCY = True
    SHOW_EDIT_ACTIVITY = True
    SHOW_COVERAGE = True
    SHOW_DURATION = True


# Thresholds for status line indicators
class Thresholds:
    # Context window limits (dynamic based on model)
    CONTEXT_YELLOW_RATIO = 0.75  # 75% of context window
    CONTEXT_RED_RATIO = 0.90  # 90% of context window

    # Cache efficiency thresholds
    CACHE_EXCELLENT = 0.50  # ≥50% cache hit rate (green)
    CACHE_GOOD = 0.20  # ≥20% cache hit rate (yellow)
    MIN_CACHE_DISPLAY = 0.10  # Only show cache if ≥10% hit rate

    # API efficiency thresholds
    API_EXCELLENT = 0.50  # >50% time in API calls (expected for coding)
    API_LOW = 0.20  # <20% time in API calls (lots of thinking/tools)
    MIN_SESSION_DURATION_SECS = 60  # Only show after 1 minute

    # Coverage thresholds (SolarWindPy requirement: ≥95%)
    COVERAGE_EXCELLENT = 95.0  # Required minimum
    COVERAGE_WARNING = 90.0  # Below target

    # Session duration thresholds (hours)
    SESSION_YELLOW_HOURS = 4  # Long session
    SESSION_RED_HOURS = 8  # Very long session


def get_model_name(data):
    """Extract and format model display name with color coding.

    Different models have different capabilities and costs. This provides
    a visual indicator of which model is currently active:
    - Opus: Most capable (green)
    - Sonnet: Balanced performance (default, no color)
    - Haiku: Fast/economical (yellow)

    Args:
        data: Status line JSON data from Claude Code

    Returns:
        Formatted model name with optional color coding
    """
    model_id = data.get("model", {}).get("id", "")
    display_name = data.get("model", {}).get("display_name", "Claude")

    # Detect model family and apply color coding
    if "opus" in model_id.lower():
        return Colors.green(display_name)  # Premium model
    elif "haiku" in model_id.lower():
        return Colors.yellow(display_name)  # Economy model
    else:
        return display_name  # Sonnet or unknown (no color)


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


def get_conversation_token_usage(data):
    """Get actual conversation token usage from Claude API data.

    This replaces the old transcript file size estimation with real
    token counts from the Claude API, including prompt caching data.

    Args:
        data: Status line JSON data from Claude Code

    Returns:
        Formatted token usage string with color coding (e.g., "44k/200k")
        or "0/200k" if no usage data available
    """
    try:
        context = data.get("context_window", {})
        current = context.get("current_usage")

        # If no messages yet (fresh session), return zero
        if current is None:
            context_limit = context.get("context_window_size", 200_000)
            limit_str = f"{context_limit // 1000}k"
            return f"0/{limit_str}"

        # Get actual token counts from API
        input_tokens = current.get("input_tokens", 0)
        cache_creation = current.get("cache_creation_input_tokens", 0)
        cache_read = current.get("cache_read_input_tokens", 0)

        # Total context = input + cache creation + cache read
        # All three occupy space in the context window
        total_context_tokens = input_tokens + cache_creation + cache_read

        # Get context limit from model (supports different models)
        context_limit = context.get("context_window_size", 200_000)

        # Format display with k suffix for readability
        if total_context_tokens > 1000:
            token_str = f"{total_context_tokens // 1000}k"
        else:
            token_str = str(total_context_tokens)

        limit_str = f"{context_limit // 1000}k"
        usage_display = f"{token_str}/{limit_str}"

        # Apply color coding based on context window usage ratio
        usage_ratio = total_context_tokens / context_limit if context_limit > 0 else 0
        if usage_ratio >= Thresholds.CONTEXT_RED_RATIO:
            return Colors.red(usage_display)
        elif usage_ratio >= Thresholds.CONTEXT_YELLOW_RATIO:
            return Colors.yellow(usage_display)
        else:
            return Colors.green(usage_display)

    except Exception:
        # Graceful fallback if API data format changes
        return "0/200k"


def get_cache_efficiency(data):
    """Calculate and display prompt cache efficiency.

    Prompt caching reduces costs by reusing context. This shows the
    percentage of input tokens that were served from cache (75% discount)
    vs processed fresh (full cost).

    Args:
        data: Status line JSON data from Claude Code

    Returns:
        Formatted cache efficiency string (e.g., "💾 68%") with color coding,
        or None if caching is not active or negligible
    """
    try:
        current = data.get("context_window", {}).get("current_usage")
        if not current:
            return None

        # Get cache statistics
        cache_read = current.get("cache_read_input_tokens", 0)
        cache_write = current.get("cache_creation_input_tokens", 0)
        input_tokens = current.get("input_tokens", 0)

        # Total input processed (all sources)
        total_input = input_tokens + cache_write + cache_read

        # Skip if no input yet or no caching active
        if total_input == 0 or cache_read == 0:
            return None

        # Calculate cache hit rate
        cache_hit_rate = cache_read / total_input

        # Only show if cache hit rate is meaningful (≥10%)
        if cache_hit_rate < Thresholds.MIN_CACHE_DISPLAY:
            return None

        # Format as percentage
        cache_pct_str = f"{cache_hit_rate: .0%}"

        # Color code based on cache efficiency
        if cache_hit_rate >= Thresholds.CACHE_EXCELLENT:
            return Colors.green(f"💾 {cache_pct_str}")
        elif cache_hit_rate >= Thresholds.CACHE_GOOD:
            return Colors.yellow(f"💾 {cache_pct_str}")
        else:
            return f"💾 {cache_pct_str}"  # No color for low rates

    except Exception:
        return None


def get_edit_activity(data):
    """Display code edit productivity metrics.

    Shows cumulative lines added and removed during the session,
    providing a quick indicator of coding activity and velocity.

    Args:
        data: Status line JSON data from Claude Code

    Returns:
        Formatted edit activity string (e.g., "✏️ +156/-23") with color coding,
        or None if no edits have been made
    """
    try:
        cost = data.get("cost", {})
        lines_added = cost.get("total_lines_added", 0)
        lines_removed = cost.get("total_lines_removed", 0)

        # Skip if no edits yet
        if lines_added == 0 and lines_removed == 0:
            return None

        # Format display
        activity_str = f"✏️ +{lines_added}/-{lines_removed}"

        # Calculate net change for color coding
        net_change = lines_added - lines_removed

        # Color code based on type of activity
        if net_change > 100:
            # Significant additions - new feature work (green)
            return Colors.green(activity_str)
        elif net_change > 0:
            # Moderate additions - normal development (no color)
            return activity_str
        elif net_change > -50:
            # Minor refactoring (no color)
            return activity_str
        else:
            # Heavy refactoring/deletion (yellow for awareness)
            return Colors.yellow(activity_str)

    except Exception:
        return None


def get_api_efficiency(data):
    """Calculate API time vs total session time ratio (Phase 3: Optional).

    High ratios indicate lots of local processing (thinking, tool execution).
    Low ratios indicate more time in API calls (generating responses).

    Args:
        data: Status line JSON data from Claude Code

    Returns:
        Formatted efficiency ratio (e.g., "⚡ 45%") or None if insufficient data
    """
    try:
        cost = data.get("cost", {})
        total_duration = cost.get("total_duration_ms", 0)
        api_duration = cost.get("total_api_duration_ms", 0)

        # Skip if session just started
        if total_duration < (Thresholds.MIN_SESSION_DURATION_SECS * 1000):
            return None

        # Calculate API efficiency (what % of time is API calls)
        api_ratio = api_duration / total_duration if total_duration > 0 else 0

        # Format as percentage
        efficiency_str = f"⚡ {api_ratio: .0%}"

        # Color code based on typical patterns
        if api_ratio > Thresholds.API_EXCELLENT:
            # >50% in API = mostly generating (expected for coding)
            return Colors.green(efficiency_str)
        elif api_ratio > Thresholds.API_LOW:
            # 20-50% = balanced (tools + generation)
            return efficiency_str
        else:
            # <20% = lots of thinking/tool time (yellow for awareness)
            return Colors.yellow(efficiency_str)

    except Exception:
        return None


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
    except Exception:
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
        total = cov.report(show_missing=False, file=open(os.devnull, "w"))

        # Color code based on SolarWindPy requirements
        if total >= Thresholds.COVERAGE_EXCELLENT:
            return Colors.green(f"✓{total: .0f}%")
        elif total >= Thresholds.COVERAGE_WARNING:
            return Colors.yellow(f"⚠{total: .0f}%")
        else:
            return Colors.red(f"✗{total: .0f}%")
    except Exception:
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
    """Create the enhanced status line with real API data."""
    # Get all components
    model = get_model_name(data) if Config.SHOW_MODEL else None
    current_dir = get_current_dir(data) if Config.SHOW_DIRECTORY else None
    conda_env = get_conda_env() if Config.SHOW_CONDA_ENV else None
    git_branch = get_git_branch() if Config.SHOW_GIT_BRANCH else None
    git_status = get_git_status_indicators() if Config.SHOW_GIT_BRANCH else ""
    plan_name = get_plan_info() if Config.SHOW_PLAN_NAME else None
    tokens = get_conversation_token_usage(data) if Config.SHOW_TOKENS else None
    cache = get_cache_efficiency(data) if Config.SHOW_CACHE_EFFICIENCY else None
    edits = get_edit_activity(data) if Config.SHOW_EDIT_ACTIVITY else None
    api_eff = get_api_efficiency(data) if Config.SHOW_API_EFFICIENCY else None
    coverage = get_coverage_percentage() if Config.SHOW_COVERAGE else None
    duration = get_session_duration(data) if Config.SHOW_DURATION else None

    # Build status line components
    parts = []

    # Core identification
    if model:
        parts.append(f"[{model}]")
    if current_dir:
        parts.append(f"📁 {current_dir}")

    # Environment
    if conda_env:
        parts.append(f"🐍 {conda_env}")

    # Git info
    if git_branch:
        branch_display = f"🌿 {git_branch}{git_status}"
        parts.append(branch_display)

    # Plan indicator (if on plan branch)
    if plan_name:
        parts.append(f"📋 {plan_name}")

    # Performance metrics
    if tokens:
        parts.append(f"🔤 {tokens}")

    if cache:
        parts.append(cache)

    if edits:
        parts.append(edits)

    # Phase 3: Optional API efficiency
    if api_eff:
        parts.append(api_eff)

    # Quality metrics
    if coverage:
        parts.append(f"🎯 {coverage}")

    # Session info
    if duration:
        parts.append(f"⏱️ {duration}")

    return " | ".join(parts)


if __name__ == "__main__":
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)
        print(create_status_line(data))
    except Exception:
        # Fallback status line
        print(f"[Claude] 📁 {os.path.basename(os.getcwd())} | ❌ Error")
