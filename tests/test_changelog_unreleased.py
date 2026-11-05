# Spent-When: PERMANENT(CHANGELOG.md stops carrying an Unreleased section)
# Supersedes: none
"""The Unreleased changelog names only paths that resolve as it says.

Users read the ``## [Unreleased]`` section of ``CHANGELOG.md`` as the migration
guide from the last release, so every mapping in it must state the final state:
the new name resolves in this checkout and the old name does not.

Checked:

- every row of the import-path table: each backticked ``solarwindpy.`` path in
  the new-path cell resolves, and the old path does not;
- every prose mapping of the form ``solarwindpy.a.b`` -> ``solarwindpy.c.d``
  (both sides backticked, fully qualified): the new path resolves, the old one
  does not;
- every backticked fully qualified ``solarwindpy.`` path in the Added
  subsection resolves (a trailing call such as ``(frame, ...)`` is ignored).

Skipped, because they cannot be resolved unambiguously from the text:

- class-relative names (``Units.T``, ``Plasma.n``, ``plot_contours(growth_rate=)``);
- signatures and parameter names (``f(x, k, y0, A)``, ``popt["y0"]``);
- plot label keys (``("qpar", "", s)``), file paths and dependency pins;
- table cells reading "none (removed; ...)", which have no new path to check.
"""

import importlib
import re
from pathlib import Path

import pytest

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"

_PATH = r"solarwindpy(?:\.\w+)+"
_TICKED_PATH = re.compile(r"`(%s)" % _PATH)
_ARROW = re.compile(r"`(%s)`\s*->\s*`(%s)`" % (_PATH, _PATH))
_TABLE_ROW = re.compile(r"^\s*\|\s*`(%s)`\s*\|(.*)\|\s*$" % _PATH, re.MULTILINE)

# Lower bounds on how many names each check covers, so a parser regression
# that matches nothing cannot pass silently.
_MIN_TABLE_ROWS = 60
_MIN_ADDED_PATHS = 8


def _unreleased():
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index("## [Unreleased]")
    stop = text.index("\n## [", start + 1)
    return text[start:stop]


def _subsection(section, title):
    start = section.index("### %s\n" % title)
    stop = section.find("\n### ", start + 1)
    return section[start : stop if stop >= 0 else len(section)]


def _resolves(path):
    """True when ``path`` imports as a module or is an attribute chain of one."""
    parts = path.split(".")
    for i in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:i]))
        except ImportError:
            continue
        for name in parts[i:]:
            if not hasattr(obj, name):
                return False
            obj = getattr(obj, name)
        return True
    return False


def _table_rows():
    return [(old, cell) for old, cell in _TABLE_ROW.findall(_unreleased())]


def test_the_table_is_found():
    """The import-path table parses into at least the expected number of rows.

    ON FAILURE: the code is wrong if the table's layout changed; update the
    pattern. The changelog is wrong if rows were dropped by mistake.
    """
    assert len(_table_rows()) >= _MIN_TABLE_ROWS


@pytest.mark.parametrize("old,cell", _table_rows(), ids=lambda v: str(v)[:60])
def test_table_row_maps_a_gone_path_to_a_live_one(old, cell):
    """The old path no longer resolves; every new path in the row does.

    ON FAILURE: the changelog is wrong; correct the row to name the path that
    exists in this checkout, or remove a row whose old path still resolves.
    """
    assert not _resolves(old), "%s still resolves" % old
    new = _TICKED_PATH.findall(cell)
    if not new:
        assert cell.strip().startswith("none"), cell
    for path in new:
        assert _resolves(path), "%s does not resolve" % path


def test_prose_mappings_name_live_targets():
    """Every fully qualified prose mapping maps a gone path to a live one.

    ON FAILURE: the changelog is wrong; correct the mapping.
    """
    for old, new in _ARROW.findall(_unreleased()):
        assert not _resolves(old), "%s still resolves" % old
        assert _resolves(new), "%s does not resolve" % new


def test_added_paths_resolve():
    """Every fully qualified path the Added subsection names exists.

    ON FAILURE: the changelog is wrong; correct the path.
    """
    paths = sorted(set(_TICKED_PATH.findall(_subsection(_unreleased(), "Added"))))
    assert len(paths) >= _MIN_ADDED_PATHS, paths
    missing = [p for p in paths if not _resolves(p)]
    assert not missing, missing
