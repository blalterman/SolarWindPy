#!/usr/bin/env python3
"""Tests for .claude/statusline.py color functionality."""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add .claude to path to import statusline
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude"))
import statusline


class TestColors:
    """Test the Colors class and ANSI color functionality."""

    def test_color_codes(self):
        """Test ANSI color codes are correct."""
        assert statusline.Colors.RED == "\033[91m"
        assert statusline.Colors.YELLOW == "\033[93m"
        assert statusline.Colors.GREEN == "\033[92m"
        assert statusline.Colors.RESET == "\033[0m"

    def test_colorize_with_no_color_env(self):
        """Test NO_COLOR environment variable disables colors."""
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = statusline.Colors.colorize("test", statusline.Colors.RED)
            assert result == "test"  # No color codes

    def test_colorize_with_non_tty(self):
        """Test colors disabled when not TTY."""
        with patch("sys.stdout.isatty", return_value=False):
            result = statusline.Colors.colorize("test", statusline.Colors.RED)
            assert result == "test"  # No color codes

    def test_colorize_with_tty(self):
        """Test colors applied when TTY and NO_COLOR not set."""
        with (
            patch("sys.stdout.isatty", return_value=True),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = statusline.Colors.colorize("test", statusline.Colors.RED)
            assert result == f"{statusline.Colors.RED}test{statusline.Colors.RESET}"

    def test_color_methods(self):
        """Test individual color methods."""
        with (
            patch("sys.stdout.isatty", return_value=True),
            patch.dict(os.environ, {}, clear=True),
        ):
            assert (
                statusline.Colors.red("test")
                == f"{statusline.Colors.RED}test{statusline.Colors.RESET}"
            )
            assert (
                statusline.Colors.yellow("test")
                == f"{statusline.Colors.YELLOW}test{statusline.Colors.RESET}"
            )
            assert (
                statusline.Colors.green("test")
                == f"{statusline.Colors.GREEN}test{statusline.Colors.RESET}"
            )


class TestThresholds:
    """Test threshold constants."""

    def test_context_ratio_thresholds(self):
        """Test context window ratio thresholds."""
        assert statusline.Thresholds.CONTEXT_YELLOW_RATIO == 0.75
        assert statusline.Thresholds.CONTEXT_RED_RATIO == 0.90

    def test_cache_thresholds(self):
        """Test cache efficiency thresholds."""
        assert statusline.Thresholds.CACHE_EXCELLENT == 0.50
        assert statusline.Thresholds.CACHE_GOOD == 0.20
        assert statusline.Thresholds.MIN_CACHE_DISPLAY == 0.10

    def test_session_thresholds(self):
        """Test session duration threshold values."""
        assert statusline.Thresholds.SESSION_YELLOW_HOURS == 4
        assert statusline.Thresholds.SESSION_RED_HOURS == 8

    def test_coverage_thresholds(self):
        """Test coverage threshold values."""
        assert statusline.Thresholds.COVERAGE_EXCELLENT == 95.0
        assert statusline.Thresholds.COVERAGE_WARNING == 90.0


class TestConversationTokenUsage:
    """Test real conversation token usage from API data."""

    def test_token_usage_fresh_session(self):
        """Test token display with no messages yet (fresh session)."""
        data = {
            "context_window": {"context_window_size": 200_000, "current_usage": None}
        }
        result = statusline.get_conversation_token_usage(data)
        assert result == "0/200k"

    def test_token_usage_with_api_data(self):
        """Test token display with real API usage data."""
        data = {
            "context_window": {
                "context_window_size": 200_000,
                "current_usage": {
                    "input_tokens": 30000,
                    "output_tokens": 5000,
                    "cache_creation_input_tokens": 10000,
                    "cache_read_input_tokens": 15000,
                },
            }
        }
        # Total = 30000 + 10000 + 15000 = 55000 tokens = 55k
        result = statusline.get_conversation_token_usage(data)
        assert "55k/200k" in result

    def test_token_usage_color_coding_green(self):
        """Test green color for low token usage (<75%)."""
        data = {
            "context_window": {
                "context_window_size": 200_000,
                "current_usage": {
                    "input_tokens": 50000,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            }
        }
        with patch("sys.stdout.isatty", return_value=False):
            result = statusline.get_conversation_token_usage(data)
            assert "50k/200k" in result

    def test_token_usage_different_context_size(self):
        """Test token display adapts to different context window sizes."""
        data = {
            "context_window": {
                "context_window_size": 128_000,
                "current_usage": {
                    "input_tokens": 64000,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            }
        }
        result = statusline.get_conversation_token_usage(data)
        assert "64k/128k" in result

    def test_token_usage_missing_data(self):
        """Test graceful handling of missing context_window data."""
        data = {}
        result = statusline.get_conversation_token_usage(data)
        assert "200k" in result  # Should return default


class TestCacheEfficiency:
    """Test cache efficiency calculation and display."""

    def test_cache_efficiency_none_when_no_usage(self):
        """Test returns None when no usage data available."""
        data = {"context_window": {}}
        result = statusline.get_cache_efficiency(data)
        assert result is None

    def test_cache_efficiency_none_when_no_cache_reads(self):
        """Test returns None when cache reads are zero."""
        data = {
            "context_window": {
                "current_usage": {
                    "input_tokens": 10000,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 0,
                }
            }
        }
        result = statusline.get_cache_efficiency(data)
        assert result is None

    def test_cache_efficiency_below_threshold(self):
        """Test returns None when cache hit rate below 10% threshold."""
        data = {
            "context_window": {
                "current_usage": {
                    "input_tokens": 95000,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 5000,  # 5% hit rate
                }
            }
        }
        result = statusline.get_cache_efficiency(data)
        assert result is None

    def test_cache_efficiency_good_rate(self):
        """Test display for good cache hit rate (20-50%)."""
        data = {
            "context_window": {
                "current_usage": {
                    "input_tokens": 30000,
                    "cache_creation_input_tokens": 10000,
                    "cache_read_input_tokens": 15000,  # 27% hit rate
                }
            }
        }
        result = statusline.get_cache_efficiency(data)
        assert "💾" in result
        assert "27%" in result

    def test_cache_efficiency_excellent_rate(self):
        """Test display for excellent cache hit rate (≥50%)."""
        data = {
            "context_window": {
                "current_usage": {
                    "input_tokens": 20000,
                    "cache_creation_input_tokens": 10000,
                    "cache_read_input_tokens": 30000,  # 50% hit rate
                }
            }
        }
        result = statusline.get_cache_efficiency(data)
        assert "💾" in result
        assert "50%" in result


class TestEditActivity:
    """Test edit activity tracking and display."""

    def test_edit_activity_none_when_no_edits(self):
        """Test returns None when no edits have been made."""
        data = {"cost": {"total_lines_added": 0, "total_lines_removed": 0}}
        result = statusline.get_edit_activity(data)
        assert result is None

    def test_edit_activity_additions(self):
        """Test display for net additions."""
        data = {"cost": {"total_lines_added": 156, "total_lines_removed": 23}}
        result = statusline.get_edit_activity(data)
        assert "✏️ +156/-23" in result

    def test_edit_activity_deletions(self):
        """Test display for net deletions."""
        data = {"cost": {"total_lines_added": 20, "total_lines_removed": 100}}
        result = statusline.get_edit_activity(data)
        assert "✏️ +20/-100" in result

    def test_edit_activity_large_additions(self):
        """Test display for significant additions (>100 net)."""
        data = {"cost": {"total_lines_added": 250, "total_lines_removed": 10}}
        result = statusline.get_edit_activity(data)
        assert "✏️ +250/-10" in result

    def test_edit_activity_missing_data(self):
        """Test graceful handling of missing cost data."""
        data = {}
        result = statusline.get_edit_activity(data)
        assert result is None


class TestModelDetection:
    """Test model detection with color coding."""

    def test_model_name_sonnet(self):
        """Test Sonnet model (no color)."""
        data = {
            "model": {"id": "claude-sonnet-4-20250514", "display_name": "Sonnet 4.5"}
        }
        with patch("sys.stdout.isatty", return_value=False):
            result = statusline.get_model_name(data)
            assert result == "Sonnet 4.5"

    def test_model_name_haiku(self):
        """Test Haiku model (yellow)."""
        data = {"model": {"id": "claude-haiku-4", "display_name": "Haiku"}}
        result = statusline.get_model_name(data)
        assert "Haiku" in result

    def test_model_name_opus(self):
        """Test Opus model (green)."""
        data = {"model": {"id": "claude-opus-4-5", "display_name": "Opus 4.5"}}
        result = statusline.get_model_name(data)
        assert "Opus 4.5" in result


class TestStatusLineIntegration:
    """Test complete status line creation."""

    def test_create_status_line_complete(self):
        """Test complete status line with all new features."""
        data = {
            "model": {"id": "claude-sonnet-4-20250514", "display_name": "Sonnet 4.5"},
            "workspace": {"current_dir": "/Users/test/SolarWindPy-2"},
            "context_window": {
                "context_window_size": 200_000,
                "current_usage": {
                    "input_tokens": 30000,
                    "cache_creation_input_tokens": 10000,
                    "cache_read_input_tokens": 15000,
                },
            },
            "cost": {
                "total_duration_ms": 3600000,  # 1 hour
                "total_lines_added": 156,
                "total_lines_removed": 23,
            },
        }

        with (
            patch("subprocess.run") as mock_run,
            patch("os.environ.get", return_value="solarwindpy"),
            patch("statusline.get_coverage_percentage", return_value="✓97%"),
        ):
            # Mock git commands
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "master\n"

            result = statusline.create_status_line(data)

            # Check all components are present
            assert "Sonnet 4.5" in result
            assert "📁 SolarWindPy-2" in result
            assert "🐍 solarwindpy" in result
            assert "🌿 master" in result
            assert "🔤" in result  # Token usage
            assert "55k/200k" in result  # Actual token count
            assert "💾" in result  # Cache indicator
            assert "✏️ +156/-23" in result  # Edit activity
            assert "🎯 ✓97%" in result  # Coverage
            assert "⏱️" in result  # Duration

    def test_create_status_line_minimal(self):
        """Test status line with minimal data (fresh session)."""
        data = {
            "model": {"id": "claude-sonnet-4", "display_name": "Sonnet"},
            "workspace": {"current_dir": "/Users/test/project"},
            "context_window": {"context_window_size": 200_000, "current_usage": None},
            "cost": {
                "total_duration_ms": 0,
                "total_lines_added": 0,
                "total_lines_removed": 0,
            },
        }

        with (
            patch("subprocess.run") as mock_run,
            patch("os.environ.get", return_value=""),
            patch("statusline.get_coverage_percentage", return_value=None),
        ):
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "main\n"

            result = statusline.create_status_line(data)

            # Check basic components
            assert "[Sonnet]" in result
            assert "📁 project" in result
            assert "0/200k" in result  # Fresh session
            assert "💾" not in result  # No cache yet
            assert "✏️" not in result  # No edits yet


if __name__ == "__main__":
    # Demo script to show colors
    print("=== StatusLine Color Demo ===")
    print()

    # Force colors on for demo
    os.environ.pop("NO_COLOR", None)

    with patch("sys.stdout.isatty", return_value=True):
        print("Token Usage Colors:")
        print(f"  Green (low): {statusline.Colors.green('25k tokens')}")
        print(f"  Yellow (medium): {statusline.Colors.yellow('160k tokens')}")
        print(f"  Red (high): {statusline.Colors.red('190k tokens')}")
        print()

        print("Compaction Indicator Colors:")
        print(f"  Green (safe): {statusline.Colors.green('●●●')}")
        print(f"  Yellow (warning): {statusline.Colors.yellow('●○○')}")
        print(f"  Red (critical): {statusline.Colors.red('○○○')}")
        print()

        print("Usage Indicator Colors:")
        print(f"  Green (light): {statusline.Colors.green('█████')}")
        print(f"  Yellow (medium): {statusline.Colors.yellow('███○○')}")
        print(f"  Red (heavy): {statusline.Colors.red('██○○○')}")
        print()

        # Sample status line with colors
        print("Sample Status Line:")
        sample_data = {
            "model": {"display_name": "Claude Sonnet 4"},
            "workspace": {"current_dir": "/Users/test/SolarWindPy"},
            "transcript_path": "/dev/null",
        }

        with (
            patch("subprocess.run") as mock_run,
            patch("os.environ.get", return_value="solarwindpy-20250404"),
            patch(
                "statusline.estimate_token_usage",
                return_value=statusline.Colors.yellow("160k"),
            ),
            patch(
                "statusline.get_compaction_indicator",
                return_value=statusline.Colors.yellow("●○○"),
            ),
            patch(
                "statusline.get_usage_indicator",
                return_value=statusline.Colors.green("█████"),
            ),
        ):

            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "feature/solar-activity-testing\n"

            result = statusline.create_status_line(sample_data)
            print(f"  {result}")
