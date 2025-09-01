#!/usr/bin/env python3
"""
statusline.py - Advanced statusline for Claude Code

This Python script generates a rich, color-coded statusline showing:
- Model name, current directory, conda environment, git branch
- Token usage estimation with color-coded thresholds
- Context compaction indicator
- Session duration tracking

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


# Thresholds for Max plan limits (based on Claude Sonnet 4 limits)
class Thresholds:
    # Token limits (200k context window)
    TOKEN_YELLOW = 150_000  # 75% of 200k limit
    TOKEN_RED = 180_000  # 90% of 200k limit

    # Time limits (Max $100 plan: 140-280 hours/week, Max $200: 240-480 hours/week)
    TIME_YELLOW_HOURS = 200  # Weekly high usage threshold
    TIME_RED_HOURS = 400  # Weekly critical usage threshold

    # Session duration limits (in hours)
    SESSION_YELLOW_HOURS = 6  # Heavy usage
    SESSION_RED_HOURS = 12  # Very heavy usage

    # Compaction thresholds (file size based)
    COMPACTION_YELLOW_RATIO = 0.6  # 60% toward compaction
    COMPACTION_RED_RATIO = 0.8  # 80% toward compaction


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
    """Estimate token usage from transcript file with color coding and compaction
    adjustment."""
    try:
        transcript_path = data.get("transcript_path", "")
        if not transcript_path or not os.path.exists(transcript_path):
            return "0"

        # Rough estimate: ~4 chars per token
        file_size = os.path.getsize(transcript_path)
        estimated_tokens = file_size // 4

        # Check for recent compaction and adjust if needed
        compaction_info = get_recent_compaction_info()
        if compaction_info:
            # If compaction happened recently, use the smaller of:
            # 1. Current transcript estimate
            # 2. Target tokens from compaction + some buffer for new content
            target_with_buffer = compaction_info["target_tokens"] + (
                estimated_tokens * 0.1
            )
            if estimated_tokens > target_with_buffer:
                estimated_tokens = int(target_with_buffer)

        # Format token count
        if estimated_tokens > 1000000:
            token_str = f"{estimated_tokens//1000000:.1f}M"
        elif estimated_tokens > 1000:
            token_str = f"{estimated_tokens//1000:.0f}k"
        else:
            token_str = str(estimated_tokens)

        # Apply color coding based on thresholds
        if estimated_tokens >= Thresholds.TOKEN_RED:
            return Colors.red(token_str)
        elif estimated_tokens >= Thresholds.TOKEN_YELLOW:
            return Colors.yellow(token_str)
        else:
            return Colors.green(token_str)
    except:
        return "0"


def get_compaction_indicator(data):
    """Estimate time until context compaction based on file size with color coding."""
    try:
        transcript_path = data.get("transcript_path", "")
        if not transcript_path or not os.path.exists(transcript_path):
            return "∞"

        file_size = os.path.getsize(transcript_path)
        # Rough estimate: compaction around 200k tokens (~800KB)
        compaction_threshold = 800 * 1024
        ratio = file_size / compaction_threshold

        if ratio < 0.5:
            indicator = "●●●"  # Far from compaction
            return Colors.green(indicator)
        elif ratio < Thresholds.COMPACTION_YELLOW_RATIO:
            indicator = "●●○"  # Getting closer
            return Colors.green(indicator)
        elif ratio < Thresholds.COMPACTION_RED_RATIO:
            indicator = "●○○"  # Close to compaction
            return Colors.yellow(indicator)
        else:
            indicator = "○○○"  # Near compaction
            return Colors.red(indicator)
    except:
        return "?"


def get_usage_indicator():
    """Approximate usage indicator based on session duration with color coding."""
    try:
        # Check if there's a session start time file
        session_file = Path.home() / ".claude" / "session_start"
        if session_file.exists():
            start_time = float(session_file.read_text().strip())
            elapsed_hours = (time.time() - start_time) / 3600

            if elapsed_hours < 1:
                indicator = "█████"  # Fresh session
                return Colors.green(indicator)
            elif elapsed_hours < 3:
                indicator = "████○"  # Light usage
                return Colors.green(indicator)
            elif elapsed_hours < Thresholds.SESSION_YELLOW_HOURS:
                indicator = "███○○"  # Medium usage
                return Colors.yellow(indicator)
            elif elapsed_hours < Thresholds.SESSION_RED_HOURS:
                indicator = "██○○○"  # Heavy usage
                return Colors.red(indicator)
            else:
                indicator = "█○○○○"  # Very heavy usage
                return Colors.red(indicator)
        else:
            # Create session start file
            session_file.parent.mkdir(exist_ok=True)
            session_file.write_text(str(time.time()))
            indicator = "█████"
            return Colors.green(indicator)
    except:
        return "?????"


def create_status_line(data):
    """Create the formatted status line."""
    model = get_model_name(data)
    current_dir = get_current_dir(data)
    git_branch = get_git_branch()
    conda_env = get_conda_env()
    tokens = estimate_token_usage(data)
    compaction = get_compaction_indicator(data)
    usage = get_usage_indicator()

    # Build status line components
    parts = [f"[{model}]", f"📁 {current_dir}"]

    if conda_env:
        parts.append(f"🐍 {conda_env}")

    if git_branch:
        parts.append(f"🌿 {git_branch}")

    parts.extend([f"🔤 {tokens}", f"⏱️ {compaction}", f"📊 {usage}"])

    return " | ".join(parts)


if __name__ == "__main__":
    try:
        # Read JSON from stdin
        data = json.load(sys.stdin)
        print(create_status_line(data))
    except Exception as e:
        # Fallback status line
        print(f"[Claude] 📁 {os.path.basename(os.getcwd())} | ❌ Error")
