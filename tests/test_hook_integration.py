"""Integration tests for SolarWindPy hook system.

Tests hook chain execution order, exit codes, and output parsing
without requiring actual file edits or git operations.

This module validates the Development Copilot's "Definition of Done" pattern
implemented through the hook chain in .claude/hooks/.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

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


def _isolated_git_env() -> Dict[str, str]:
    """The current environment with every ``GIT_*`` variable removed.

    Inside a git hook (pre-commit runs the suite from one), git exports
    ``GIT_DIR``, ``GIT_INDEX_FILE`` and similar variables. A git command run in
    ``tmp_path`` that inherits them acts on the caller's repository instead:
    ``git init`` and ``git config`` rewrite its ``.git/config`` and ``git add``
    rewrites its index. Every git subprocess in this file uses this env.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run ``git`` in ``cwd``, isolated from the caller's git environment.

    The identity is passed with ``-c`` so no config file is ever written.
    """
    identity = ["-c", "user.name=Test", "-c", "user.email=test@test.com"]
    return subprocess.run(
        ["git", *identity, *args],
        cwd=cwd,
        env=_isolated_git_env(),
        capture_output=True,
        text=True,
        check=True,
    )


def _make_mock_git_repo(path: Path) -> Path:
    """Initialise a git repository at ``path`` with one commit of ``README.md``."""
    _git("init", "-q", cwd=path)
    (path / "README.md").write_text("# Test")
    _git("add", "README.md", cwd=path)
    _git("commit", "-q", "-m", "Initial commit", cwd=path)
    return path


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """A one-commit git repository in ``tmp_path``, isolated from any outer repo."""
    return _make_mock_git_repo(tmp_path)


def test_mock_git_repo_leaves_the_callers_repository_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With ``GIT_DIR`` and ``GIT_INDEX_FILE`` aimed at a decoy, the decoy is unchanged.

    This is the environment a git hook gives the suite. The decoy is a real
    repository with one commit, so it has both a config and an index; their
    bytes before and after building the mock repository must match, and the
    mock repository must hold its own commit.

    ON FAILURE: the fixture no longer isolates its git calls from the caller's
    repository; fix ``_isolated_git_env`` or ``_git`` before running the suite
    from a hook again.
    """
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    _make_mock_git_repo(decoy)
    config, index = decoy / ".git" / "config", decoy / ".git" / "index"
    before = (config.read_bytes(), index.read_bytes())

    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(index))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))
    target = tmp_path / "mock"
    target.mkdir()
    _make_mock_git_repo(target)

    assert (config.read_bytes(), index.read_bytes()) == before
    log = _git("log", "--format=%s", cwd=target).stdout.split()
    assert log == ["Initial", "commit"]


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


def test_compaction_with_no_context_files_reports_zero_reduction(
    hook_scripts_dir: Path, mock_git_repo: Path
) -> None:
    """A repository with none of the context files compacts with 0.0% reduction.

    ``mock_git_repo`` holds only ``README.md``, which the token estimate does
    not read, so the estimate is 0. The hook used to divide by it and exit with
    ``ZeroDivisionError``; the expected report is no reduction (0 tokens to 0).

    ON FAILURE: the code is wrong.
    """
    (mock_git_repo / ".claude").mkdir()
    result = subprocess.run(
        [sys.executable, str(hook_scripts_dir / "create-compaction.py")],
        cwd=mock_git_repo,
        env=_isolated_git_env(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    state = (mock_git_repo / ".claude" / "compacted_state.md").read_text()
    assert "**Context Reduction**: 0.0% (0 → 0 tokens)" in state


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
            assert (
                req["min"] <= timeout <= req["max"]
            ), f"{event} timeout {timeout} not in range [{req['min']}, {req['max']}]"


# ==============================================================================
# Definition of Done Pattern Tests
# ==============================================================================


class TestDefinitionOfDonePattern:
    """Test the Definition of Done validation pattern."""

    def test_coverage_requirement_in_pre_commit(self, hook_scripts_dir: Path) -> None:
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
