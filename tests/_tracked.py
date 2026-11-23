"""The git-tracked files of this checkout, for tests that scan source text.

A scan that walks the directory tree also reads untracked work, such as a
scratch file or a draft beside the code, so its verdict depends on what
happens to be on disk. A scan reads the tracked set instead, the files a
commit holds::

    from tests._tracked import tracked_files

    for path in tracked_files("tests/*.py"):
        ...

Outside a git checkout, such as an unpacked sdist, there is no tracked set,
and the calling test skips.
"""

import subprocess
from pathlib import Path

import pytest

#: The root of the checkout.
REPO = Path(__file__).resolve().parents[1]


def tracked_files(*pathspecs):
    """Return the tracked files matching ``pathspecs``, sorted, as absolute paths.

    Each pathspec is read as git reads it: ``"tests/*.py"`` matches every
    ``.py`` file under ``tests/``, subfolders included, and a directory matches
    every file below it. A tracked file deleted from the working tree is left
    out.

    Outside a git checkout, skips the calling test, or the calling module when
    called at import. Raises ``AssertionError`` when no file matches, so a scan
    over a mistyped pathspec fails instead of passing on nothing.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", *pathspecs],
            cwd=REPO,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout", allow_module_level=True)
    paths = sorted(REPO / p for p in out.decode("utf-8").split("\0") if p)
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise AssertionError(f"git ls-files matched no file for {pathspecs}")
    return paths
