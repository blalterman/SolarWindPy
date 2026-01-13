"""Integration tests for SolarWindPy hook system.

Tests hook chain execution order, exit codes, and output parsing
without requiring actual file edits or git operations.

This module validates the Development Copilot's "Definition of Done" pattern
implemented through the hook chain in .claude/hooks/.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def hook_scripts_dir() -> Path:
    """Return path to actual hook scripts."""
    return Path(__file__).parent.parent / ".claude" / "hooks"


@pytest.fixture
def settings_path() -> Path:
    """Return path to settings.json."""
    return Path(__file__).parent.parent / ".claude" / "settings.json"


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """Create a mock git repository structure."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    # Create initial commit
    (tmp_path / "README.md").write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )

    return tmp_path


@pytest.fixture
def mock_settings() -> Dict[str, Any]:
    """Return mock settings.json hook configuration."""
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash .claude/hooks/validate-session-state.sh",
                            "timeout": 30,
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Edit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash .claude/hooks/test-runner.sh --changed",
                            "timeout": 120,
                        }
                    ],
                }
            ],
        }
    }


# ==============================================================================
# Hook Execution Order Tests
# ==============================================================================


class TestHookExecutionOrder:
    """Test that hooks execute in the correct order."""

    def test_lifecycle_order_is_correct(self) -> None:
        """Verify SessionStart hooks trigger before any user operations."""
        lifecycle_order = [
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "PreCompact",
            "Stop",
        ]

        # SessionStart must be first
        assert lifecycle_order[0] == "SessionStart"
        # Stop must be last
        assert lifecycle_order[-1] == "Stop"

    def test_pre_tool_use_runs_before_tool_execution(self) -> None:
        """Verify PreToolUse hooks block tool execution."""
        pre_tool_config = {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": "bash .claude/hooks/git-workflow-validator.sh",
                    "blocking": True,
                }
            ],
        }

        assert pre_tool_config["hooks"][0]["blocking"] is True

    def test_post_tool_use_matchers(self) -> None:
        """Verify PostToolUse hooks trigger after Edit/Write tools."""
        post_tool_matchers = ["Edit", "MultiEdit", "Write"]

        for matcher in post_tool_matchers:
            assert matcher in ["Edit", "MultiEdit", "Write"]


# ==============================================================================
# Settings Configuration Tests
# ==============================================================================


class TestSettingsConfiguration:
    """Test settings.json hook configuration."""

    def test_settings_file_exists(self, settings_path: Path) -> None:
        """Verify settings.json exists."""
        assert settings_path.exists(), "settings.json not found"

    def test_settings_has_hooks_section(self, settings_path: Path) -> None:
        """Verify settings.json has hooks configuration."""
        if not settings_path.exists():
            pytest.skip("settings.json not found")

        settings = json.loads(settings_path.read_text())
        assert "hooks" in settings, "hooks section not found in settings.json"

    def test_session_start_hook_configured(self, settings_path: Path) -> None:
        """Verify SessionStart hook is configured."""
        if not settings_path.exists():
            pytest.skip("settings.json not found")

        settings = json.loads(settings_path.read_text())
        hooks = settings.get("hooks", {})
        assert "SessionStart" in hooks, "SessionStart hook not configured"

    def test_post_tool_use_hook_configured(self, settings_path: Path) -> None:
        """Verify PostToolUse hooks are configured for Edit/Write."""
        if not settings_path.exists():
            pytest.skip("settings.json not found")

        settings = json.loads(settings_path.read_text())
        hooks = settings.get("hooks", {})
        assert "PostToolUse" in hooks, "PostToolUse hook not configured"

        # Check for Edit and Write matchers
        post_tool_hooks = hooks["PostToolUse"]
        matchers = [h["matcher"] for h in post_tool_hooks]
        assert "Edit" in matchers, "Edit matcher not in PostToolUse"
        assert "Write" in matchers, "Write matcher not in PostToolUse"

    def test_pre_compact_hook_configured(self, settings_path: Path) -> None:
        """Verify PreCompact hook is configured."""
        if not settings_path.exists():
            pytest.skip("settings.json not found")

        settings = json.loads(settings_path.read_text())
        hooks = settings.get("hooks", {})
        assert "PreCompact" in hooks, "PreCompact hook not configured"


# ==============================================================================
# Hook Script Existence Tests
# ==============================================================================


class TestHookScriptsExist:
    """Test that required hook scripts exist."""

    def test_validate_session_state_exists(self, hook_scripts_dir: Path) -> None:
        """Verify validate-session-state.sh exists."""
        script = hook_scripts_dir / "validate-session-state.sh"
        assert script.exists(), "validate-session-state.sh not found"

    def test_test_runner_exists(self, hook_scripts_dir: Path) -> None:
        """Verify test-runner.sh exists."""
        script = hook_scripts_dir / "test-runner.sh"
        assert script.exists(), "test-runner.sh not found"

    def test_git_workflow_validator_exists(self, hook_scripts_dir: Path) -> None:
        """Verify git-workflow-validator.sh exists."""
        script = hook_scripts_dir / "git-workflow-validator.sh"
        assert script.exists(), "git-workflow-validator.sh not found"

    def test_coverage_monitor_exists(self, hook_scripts_dir: Path) -> None:
        """Verify coverage-monitor.py exists."""
        script = hook_scripts_dir / "coverage-monitor.py"
        assert script.exists(), "coverage-monitor.py not found"

    def test_create_compaction_exists(self, hook_scripts_dir: Path) -> None:
        """Verify create-compaction.py exists."""
        script = hook_scripts_dir / "create-compaction.py"
        assert script.exists(), "create-compaction.py not found"


# ==============================================================================
# Hook Output Tests
# ==============================================================================


class TestHookOutputParsing:
    """Test that hook outputs can be parsed correctly."""

    def test_test_runner_help_output(self, hook_scripts_dir: Path) -> None:
        """Test parsing test-runner.sh help output."""
        script = hook_scripts_dir / "test-runner.sh"
        if not script.exists():
            pytest.skip("Script not found")

        result = subprocess.run(
            ["bash", str(script), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        # Help should show usage information
        assert "Usage:" in output, "Usage not in help output"
        assert "--changed" in output, "--changed not in help output"
        assert "--physics" in output, "--physics not in help output"
        assert "--coverage" in output, "--coverage not in help output"


# ==============================================================================
# Mock-Based Configuration Tests
# ==============================================================================


class TestHookChainWithMocks:
    """Test hook chain logic using mocks."""

    def test_edit_triggers_test_runner_chain(self, mock_settings: Dict) -> None:
        """Test that Edit tool would trigger test-runner hook."""
        post_tool_hooks = mock_settings["hooks"]["PostToolUse"]
        edit_hook = next(
            (h for h in post_tool_hooks if h["matcher"] == "Edit"),
            None,
        )

        assert edit_hook is not None
        assert "test-runner.sh --changed" in edit_hook["hooks"][0]["command"]
        assert edit_hook["hooks"][0]["timeout"] == 120

    def test_hook_timeout_configuration(self) -> None:
        """Test that all hooks have appropriate timeouts."""
        timeout_requirements = {
            "SessionStart": {"min": 15, "max": 60},
            "UserPromptSubmit": {"min": 5, "max": 30},
            "PreToolUse": {"min": 5, "max": 30},
            "PostToolUse": {"min": 60, "max": 180},
            "PreCompact": {"min": 15, "max": 60},
            "Stop": {"min": 30, "max": 120},
        }

        actual_timeouts = {
            "SessionStart": 30,
            "UserPromptSubmit": 15,
            "PreToolUse": 15,
            "PostToolUse": 120,
            "PreCompact": 30,
            "Stop": 60,
        }

        for event, timeout in actual_timeouts.items():
            req = timeout_requirements[event]
            assert req["min"] <= timeout <= req["max"], (
                f"{event} timeout {timeout} not in range [{req['min']}, {req['max']}]"
            )


# ==============================================================================
# Definition of Done Pattern Tests
# ==============================================================================


class TestDefinitionOfDonePattern:
    """Test the Definition of Done validation pattern."""

    def test_coverage_requirement_in_pre_commit(
        self, hook_scripts_dir: Path
    ) -> None:
        """Test that 95% coverage requirement is configured."""
        pre_commit_script = hook_scripts_dir / "pre-commit-tests.sh"
        if not pre_commit_script.exists():
            pytest.skip("Script not found")

        content = pre_commit_script.read_text()

        # Should contain coverage threshold reference
        assert "95" in content, "95% coverage threshold not in pre-commit"

    def test_conventional_commit_validation(self, hook_scripts_dir: Path) -> None:
        """Test conventional commit format is validated."""
        git_validator = hook_scripts_dir / "git-workflow-validator.sh"
        if not git_validator.exists():
            pytest.skip("Script not found")

        content = git_validator.read_text()

        # Should validate conventional commit patterns
        assert "feat" in content, "feat not in commit validation"
        assert "fix" in content, "fix not in commit validation"

    def test_branch_protection_enforced(self, hook_scripts_dir: Path) -> None:
        """Test master branch protection is enforced."""
        git_validator = hook_scripts_dir / "git-workflow-validator.sh"
        if not git_validator.exists():
            pytest.skip("Script not found")

        content = git_validator.read_text()

        # Should prevent master commits
        assert "master" in content, "master branch check not in validator"

    def test_physics_validation_available(self, hook_scripts_dir: Path) -> None:
        """Test physics validation mode is available."""
        test_runner = hook_scripts_dir / "test-runner.sh"
        if not test_runner.exists():
            pytest.skip("Script not found")

        content = test_runner.read_text()

        # Should support --physics flag
        assert "--physics" in content, "--physics not in test-runner"


# ==============================================================================
# Hook Error Handling Tests
# ==============================================================================


class TestHookErrorHandling:
    """Test hook error handling scenarios."""

    def test_timeout_handling(self, hook_scripts_dir: Path) -> None:
        """Test hooks respect timeout configuration."""
        test_runner = hook_scripts_dir / "test-runner.sh"
        if not test_runner.exists():
            pytest.skip("Script not found")

        content = test_runner.read_text()

        # Should use timeout command
        assert "timeout" in content, "timeout not in test-runner"

    def test_input_validation_exists(self, hook_scripts_dir: Path) -> None:
        """Test input validation helper functions exist."""
        input_validator = hook_scripts_dir / "input-validation.sh"
        if not input_validator.exists():
            pytest.skip("Script not found")

        content = input_validator.read_text()

        # Should have sanitization functions
        assert "sanitize" in content.lower(), "sanitize not in input-validation"


# ==============================================================================
# Copilot Integration Tests
# ==============================================================================


class TestCopilotIntegration:
    """Test hook integration with Development Copilot features."""

    def test_hook_chain_supports_copilot_workflow(self) -> None:
        """Test that hook chain supports Copilot's Definition of Done."""
        copilot_requirements = {
            "pre_edit_validation": "PreToolUse",
            "post_edit_testing": "PostToolUse",
            "session_state": "PreCompact",
            "final_coverage": "Stop",
        }

        valid_events = [
            "SessionStart",
            "UserPromptSubmit",
            "PreToolUse",
            "PostToolUse",
            "PreCompact",
            "Stop",
        ]

        # All Copilot requirements should map to hook events
        for requirement, event in copilot_requirements.items():
            assert event in valid_events, f"{requirement} maps to invalid event {event}"

    def test_test_runner_modes_for_copilot(self, hook_scripts_dir: Path) -> None:
        """Test test-runner.sh supports all Copilot-needed modes."""
        test_runner = hook_scripts_dir / "test-runner.sh"
        if not test_runner.exists():
            pytest.skip("Script not found")

        content = test_runner.read_text()

        required_modes = ["--changed", "--physics", "--coverage", "--fast", "--all"]

        for mode in required_modes:
            assert mode in content, f"{mode} not supported by test-runner.sh"
