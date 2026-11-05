# Spent-When: PERMANENT(the repository stops checking commit messages)
# Supersedes: none
"""The commit-msg hook accepts every Conventional Commits form the project uses."""

import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "check_conventional_commits.sh"
)


# Resolve bash on PATH. A bare "bash" makes Windows search System32 before
# PATH and run the WSL launcher, which cannot see this Windows path.
BASH = shutil.which("bash")


def _check(tmp_path, message):
    if BASH is None:
        pytest.skip("bash is not on PATH")
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text(message)
    return subprocess.run([BASH, str(SCRIPT), str(msg)], capture_output=True).returncode


@pytest.mark.parametrize(
    "message", ["fix(core): x", "docs: x", "refactor(plotting): x"]
)
def test_plain_conventional_subjects_pass(tmp_path, message):
    """Guard: the forms already accepted stay accepted."""
    assert _check(tmp_path, message) == 0


@pytest.mark.parametrize(
    "message",
    ["refactor(core)!: x", "feat!: x", "build(deps): x", "ci: x", "revert: x"],
)
def test_breaking_marker_and_standard_types_pass(tmp_path, message):
    """The breaking-change marker and the build, ci and revert types are valid."""
    assert _check(tmp_path, message) == 0


@pytest.mark.parametrize("message", ["update stuff", "fix core: x", "feature(core): x"])
def test_malformed_subjects_fail(tmp_path, message):
    """Guard: messages outside the format are still refused."""
    assert _check(tmp_path, message) == 1
