# Spent-When: PERMANENT(scripts/update_conda_feedstock.py is deleted)
# Supersedes: none
"""``scripts/update_conda_feedstock.py`` fills its tracking issue.

``subprocess.run`` is replaced by a stub where the test would run ``gh`` or the
dependency comparison. The commit SHA is checked against a real annotated tag
in a temporary repo.
"""

import importlib.util
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "update_conda_feedstock", REPO_ROOT / "scripts" / "update_conda_feedstock.py"
)
feedstock = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(feedstock)

VERSION = "0.5.0"
SHA = "ab" * 32


@pytest.fixture
def updater():
    return feedstock.CondaFeedstockUpdater(fork_owner="someone")


def test_the_issue_body_fills_every_placeholder(updater, monkeypatch):
    """The issue names the version, package, hash and commit, and the comparison.

    ON FAILURE: the code is wrong.
    """
    table = "DEPENDENCY COMPARISON\nnumpy>=2 | numpy >=2"
    created = {}

    def run(cmd, **kwargs):
        if cmd[0] == "gh":
            created["body"] = cmd[cmd.index("--body") + 1]
            return subprocess.CompletedProcess(cmd, 0, stdout="https://issue\n")
        assert cmd[-1] == "scripts/compare_feedstock_deps.py"
        return subprocess.CompletedProcess(cmd, 0, stdout=table)

    monkeypatch.setattr(feedstock.subprocess, "run", run)
    url = updater.create_tracking_issue(VERSION, SHA, commit_sha="c0ffee")
    assert url == "https://issue"
    body = created["body"]
    assert re.findall(r"\{[^{}\s]*\}", body) == []
    assert table in body
    for text in (VERSION, SHA, "c0ffee", "solarwindpy-feedstock"):
        assert text in body


def test_the_commit_sha_is_the_tagged_commit_not_the_tag_object(tmp_path, monkeypatch):
    """An annotated tag is its own object; the issue reports the commit it names.

    Under a git hook, ``GIT_DIR``, ``GIT_INDEX_FILE`` and the like name the
    repository being committed to; every git call here, the script's too,
    would act on it, not on ``tmp_path``. They are cleared first.
    ON FAILURE: the code is wrong.
    """
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    git("init", "-q", "-b", "master")
    git("commit", "-q", "--allow-empty", "-m", "release")
    git("tag", "-a", f"v{VERSION}", "-m", "the release")
    head = git("rev-parse", "HEAD")
    assert git("rev-parse", f"v{VERSION}") != head

    u = feedstock.CondaFeedstockUpdater(fork_owner="someone")
    u.project_root = tmp_path
    assert u.verify_git_tag_provenance(VERSION) == (True, head)
