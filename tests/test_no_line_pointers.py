# Spent-When: PERMANENT(live files may again cite code by line number)
# Supersedes: none
"""Live files point to code and tests by name, never by line number.

A pointer such as ``module.py`` followed by a colon and a line number goes
stale the moment the file above that line changes. Point at code as
``module.symbol`` or ``path/file.py::symbol``, and at tests by their pytest id.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNED_PATHS = ["solarwindpy", "tests", "docs/source", "README.rst", "CLAUDE.md"]

# Assembled from two pieces so this file's own source never matches it.
LINE_POINTER = re.compile(r"[A-Za-z_/]+\.py" + r":[0-9]+")


def _tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "-z", "--", *SCANNED_PATHS],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout
    return [REPO_ROOT / p.decode() for p in out.split(b"\0") if p]


def find_line_pointers():
    """Return ``path:line: match`` for every pointer in a tracked live file."""
    hits = []
    for path in _tracked_files():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for match in LINE_POINTER.finditer(line):
                rel = path.relative_to(REPO_ROOT)
                hits.append(f"{rel}:{lineno}: {match.group(0)}")
    return hits


@pytest.mark.xfail(strict=True, reason="pointers: live files still name lines")
def test_no_line_number_pointers():
    """No tracked live file names a ``file.py`` line number."""
    hits = find_line_pointers()
    assert not hits, "line-number pointers found:\n" + "\n".join(hits)
