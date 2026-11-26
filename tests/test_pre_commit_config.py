"""The local hooks in ``.pre-commit-config.yaml`` run scripts every clone holds.

A contributor who runs ``pre-commit install`` gets the hooks the configuration
lists, so each local hook's ``entry`` must name a script the repository
tracks. The repository's scripts live in ``scripts/``, beside
``check_conventional_commits.sh``, the first local hook.
"""

import subprocess
from pathlib import Path

import pytest
import yaml

from tests._tracked import REPO, tracked_files

CONFIG = REPO / ".pre-commit-config.yaml"


def local_hook_entries():
    """Return ``(hook id, script path)`` for each hook of the ``local`` repo."""
    config = yaml.safe_load(CONFIG.read_text())
    return [
        (hook["id"], hook["entry"].split()[0])
        for repo in config["repos"]
        if repo["repo"] == "local"
        for hook in repo["hooks"]
    ]


def test_the_config_has_local_hooks():
    """The scan below has hooks to check: the config lists local hooks.

    ON FAILURE: the config no longer has a ``local`` repo; the checks below
    check nothing, so retire them.
    """
    assert len(local_hook_entries()) >= 3


@pytest.mark.parametrize(("hook", "script"), local_hook_entries())
def test_each_local_hook_runs_a_tracked_executable_script_in_scripts(hook, script):
    """Each local hook's entry is an executable script tracked under ``scripts/``.

    ON FAILURE: the code is wrong; hook ``hook`` calls a script a fresh clone
    does not hold, or one git does not mark executable.
    """
    assert Path(script).parts[0] == "scripts", f"{hook} runs {script}, outside scripts/"
    assert REPO / script in tracked_files(script), f"{hook} runs untracked {script}"
    mode = subprocess.run(
        ["git", "ls-files", "-s", "--", script],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()[0]
    assert mode == "100755", f"{hook} runs {script}, which git does not mark executable"
