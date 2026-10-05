# Spent-When: PERMANENT(the repository stops shipping Claude Code hooks)
# Supersedes: none
"""Tests of the Claude Code hook scripts and their registration in settings.json.

These test developer tooling under ``.claude/``, not the solarwindpy package.
They live in ``tests/`` so the suite, the pre-commit hook and CI run them.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

CLAUDE_DIR = Path(__file__).resolve().parents[1] / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS = CLAUDE_DIR / "settings.json"


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


def _hooks() -> dict:
    """The ``hooks`` mapping of ``.claude/settings.json``."""
    return json.loads(SETTINGS.read_text())["hooks"]


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
    log = _git("log", "--format=%s", cwd=target).stdout.strip()
    assert log == "Initial commit"


def test_compaction_with_no_context_files_reports_zero_reduction(
    mock_git_repo: Path,
) -> None:
    """A repository with none of the context files compacts with 0.0% reduction.

    ``mock_git_repo`` holds only ``README.md``, which the token estimate does
    not read, so the estimate is 0. The hook used to divide by it and exit with
    ``ZeroDivisionError``; the expected report is no reduction (0 tokens to 0).

    ON FAILURE: the code is wrong.
    """
    (mock_git_repo / ".claude").mkdir()
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "create-compaction.py")],
        cwd=mock_git_repo,
        env=_isolated_git_env(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    state = (mock_git_repo / ".claude" / "compacted_state.md").read_text()
    assert "**Context Reduction**: 0.0% (0 → 0 tokens)" in state


def test_settings_file_exists() -> None:
    """``.claude/settings.json`` exists, so Claude Code loads the hooks below.

    ON FAILURE: the hook registration file was removed or moved; restore it,
    unless the author retired the hooks, in which case delete this file.
    """
    assert SETTINGS.is_file()


def test_settings_has_hooks_section() -> None:
    """``settings.json`` parses as JSON and has a ``hooks`` mapping.

    ON FAILURE: settings.json is malformed or lost its hooks section; fix
    settings.json, unless the author retired the hooks.
    """
    assert isinstance(json.loads(SETTINGS.read_text()).get("hooks"), dict)


def test_post_tool_use_hook_configured() -> None:
    """Every file-writing tool (Edit, MultiEdit, Write) runs the changed-file tests.

    ON FAILURE: an edit tool no longer triggers ``test-runner.sh --changed``;
    fix the PostToolUse entries in settings.json, unless the author dropped
    the per-edit test run.
    """
    entries = _hooks()["PostToolUse"]
    for tool in ("Edit", "MultiEdit", "Write"):
        # Claude Code matchers are regular expressions, e.g. "Edit|MultiEdit|Write".
        commands = [
            h["command"]
            for entry in entries
            if re.fullmatch(entry["matcher"], tool)
            for h in entry["hooks"]
        ]
        assert any(
            "test-runner.sh --changed" in c for c in commands
        ), f"{tool} does not run test-runner.sh --changed"


def test_pre_compact_hook_configured() -> None:
    """PreCompact runs ``create-compaction.py``, a script that exists.

    ON FAILURE: compaction no longer saves session state; fix the PreCompact
    entry in settings.json, unless the author retired the compaction hook.
    """
    commands = [h["command"] for e in _hooks()["PreCompact"] for h in e["hooks"]]
    assert any("create-compaction.py" in c for c in commands), commands
    assert (HOOKS_DIR / "create-compaction.py").is_file()
