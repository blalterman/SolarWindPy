# Spent-When: PERMANENT(the repository stops shipping .claude/settings.json)
# Supersedes: none
"""Tests of the Claude Code project settings in ``.claude/settings.json``.

These test developer tooling under ``.claude/``, not the solarwindpy package.
They live in ``tests/`` so the suite, the pre-commit hook and CI run them.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict

import pytest

CLAUDE_DIR = Path(__file__).resolve().parents[1] / ".claude"
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


def _settings() -> dict:
    """The parsed contents of ``.claude/settings.json``."""
    return json.loads(SETTINGS.read_text())


def test_settings_file_exists() -> None:
    """``.claude/settings.json`` exists, so Claude Code loads the project settings.

    ON FAILURE: the shared project settings file was removed or moved; restore
    it, unless the author retired it, in which case delete this file.
    """
    assert SETTINGS.is_file()


# Top-level keys this repository may set. Each is listed in the settings
# index at https://code.claude.com/docs/en/settings-reference.md, except
# ``$schema``, which https://code.claude.com/docs/en/settings.md documents for
# editor validation. Extend the set from those pages when a new key is needed.
_DOCUMENTED_KEYS = {
    "$schema",
    "permissions",
    "hooks",
    "model",
    "env",
    "enabledPlugins",
}


def test_settings_uses_only_documented_keys() -> None:
    """Every top-level key of ``settings.json`` is a documented settings key.

    A key Claude Code does not define is ignored or reported as a settings
    error, so it promises behaviour that nothing applies.

    ON FAILURE: remove the undocumented key, or, if the settings reference now
    documents it, add it to ``_DOCUMENTED_KEYS`` with its source.
    """
    assert set(_settings()) <= _DOCUMENTED_KEYS, sorted(
        set(_settings()) - _DOCUMENTED_KEYS
    )


def test_no_hooks_registered() -> None:
    """``settings.json`` registers no Claude Code hooks.

    The PostToolUse, PreCompact and Stop registrations were removed because
    their scripts could not run tests or produce output Claude sees.

    ON FAILURE: a hook was registered; replace this test with one that runs
    the hook and checks the outcome Claude sees, not only its registration.
    """
    assert "hooks" not in _settings()


def test_git_push_asks_and_is_not_allowed() -> None:
    """Every ``git push`` prompts: an ``ask`` rule covers it and no ``allow`` rule does.

    Rules are evaluated deny, then ask, then allow, and ``Bash(git push *)``
    also matches a bare ``git push``
    (https://code.claude.com/docs/en/permissions.md).

    ON FAILURE: pushes run without a prompt; move the push rule back to ``ask``.
    """
    permissions = _settings()["permissions"]
    assert "Bash(git push *)" in permissions.get("ask", [])
    assert not [r for r in permissions["allow"] if r.startswith("Bash(git push")]


def test_etc_deny_rule_is_absolute() -> None:
    """The ``/etc`` read guard uses ``//``, the absolute-path form.

    A rule that starts with a single ``/`` anchors at the project root, so
    ``Read(/etc/**)`` guards ``<repo>/etc`` instead
    (https://code.claude.com/docs/en/permissions.md).

    ON FAILURE: restore ``Read(//etc/**)`` in the deny list.
    """
    deny = _settings()["permissions"]["deny"]
    assert "Read(//etc/**)" in deny
    assert "Read(/etc/**)" not in deny
