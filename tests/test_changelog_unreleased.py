# Spent-When: PERMANENT(CHANGELOG.md stops carrying an Unreleased section)
# Supersedes: none
"""The newest changelog section names only paths that resolve as it says.

Users read the newest section of ``CHANGELOG.md`` as the migration guide: the
``## [Unreleased]`` section while it has entries, otherwise the latest release.
Every mapping in it must state the final state: the new name resolves in this
checkout and the old name does not.

Checked:

- every row of the import-path table: each backticked ``solarwindpy.`` path in
  the new-path cell resolves, and the old path does not;
- every prose mapping of the form ``solarwindpy.a.b`` -> ``solarwindpy.c.d``
  (both sides backticked, fully qualified): the new path resolves, the old one
  does not;
- every backticked fully qualified ``solarwindpy.`` path in the Added
  subsection resolves (a trailing call such as ``(frame, ...)`` is ignored);
- every attribute rename on a class listed in ``_CLASSES``, written as
  ``Cls.old`` -> ``Cls.new``, ``Cls.old`` -> ``new``, or as ``old`` -> ``new``
  (also ``a`` and ``b`` -> ``new``) inside a bullet that opens with ``Cls``
  followed by a colon: the class has the new attribute and lacks the old one.

Skipped, because they cannot be resolved unambiguously from the text:

- mappings on classes outside ``_CLASSES``, and bullets with no class prefix
  (the ``TrendFit`` sub-bullets, the label-key bullet);
- anything holding parentheses, ``=`` or quotes: signatures and keywords
  (``f(x, k, y0, A)``, ``plot_contours(growth_rate=)``), Series names
  (``"RT"`` -> ``"R"``) and plot label keys (``("qpar", "", s)``);
- file paths and dependency pins;
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

# Classes whose attribute renames the changelog states relative to the class.
_CLASSES = {
    "Units": "solarwindpy.core.units_constants.Units",
    "Plasma": "solarwindpy.core.plasma.Plasma",
    "Ion": "solarwindpy.core.ions.Ion",
    "Vector": "solarwindpy.core.vector.Vector",
    "BField": "solarwindpy.core.vector.BField",
    "Tensor": "solarwindpy.core.tensor.Tensor",
    "Spacecraft": "solarwindpy.core.spacecraft.Spacecraft",
    "AlfvenicTurbulence": "solarwindpy.core.alfvenic_turbulence.AlfvenicTurbulence",
    "StabilityCondition": "solarwindpy.instabilities.verscharen2016.StabilityCondition",
    "FitFunction": "solarwindpy.fitfunctions.core.FitFunction",
}
_NAME = r"[A-Za-z_][\w.]*"
_CLASS_ARROW = re.compile(
    r"(?:`(%s)` and )?`(%s)`\s*->\s*`(%s)`" % (_NAME, _NAME, _NAME)
)
_BULLET_CLASS = re.compile(r"^-\s+`(\w+)`:")

# Raw markers each parser must account for, so a parser regression that
# matches nothing cannot pass silently, whatever the section's size.
_RAW_TABLE_ROW = re.compile(r"^\s*\|\s*`solarwindpy\.", re.MULTILINE)


def _unreleased():
    """The newest section with entries: Unreleased if it has any, else the latest release."""
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index("## [Unreleased]")
    while True:
        stop = text.find("\n## [", start + 1)
        section = text[start : stop if stop >= 0 else len(text)]
        if re.search(r"^\s*[-|]", section, re.MULTILINE) or stop < 0:
            return section
        start = stop + 1


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
    """Every import-path table row in the section parses.

    ON FAILURE: the code is wrong if the table's layout changed; update the
    pattern.
    """
    assert len(_table_rows()) == len(_RAW_TABLE_ROW.findall(_unreleased()))


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


def _bullets(section):
    """Each bullet of ``section`` as one line, its continuation lines joined."""
    bullets = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped)
        elif stripped and bullets and not stripped.startswith("|"):
            bullets[-1] += " " + stripped
    return bullets


def _split(name, default):
    """``(class, attribute)`` for ``Cls.attr`` or a bare ``attr`` under ``default``."""
    head, _, tail = name.partition(".")
    if tail and head in _CLASSES:
        return head, tail
    if not tail and default:
        return default, name
    return None, None


def _class_renames():
    """``(class, old, new)`` for every class-relative rename the section states."""
    renames = []
    for bullet in _bullets(_unreleased()):
        match = _BULLET_CLASS.match(bullet)
        default = match.group(1) if match and match.group(1) in _CLASSES else None
        for first, old, new in _CLASS_ARROW.findall(bullet):
            for left in filter(None, (first, old)):
                cls, attr = _split(left, default)
                if cls is None:
                    continue
                new_cls, new_attr = _split(new, cls)
                if new_cls != cls:
                    continue
                renames.append((cls, attr, new_attr))
    return renames


def test_class_renames_are_found():
    """A section with class-relative renames parses at least one of them.

    ON FAILURE: the code is wrong if the bullets' layout changed; update the
    patterns.
    """
    stated = any(_BULLET_CLASS.match(b) and "->" in b for b in _bullets(_unreleased()))
    assert len(_class_renames()) >= int(stated)


@pytest.mark.parametrize("cls,old,new", _class_renames(), ids=lambda v: str(v))
def test_class_rename_is_the_final_state(cls, old, new):
    """The class has the new attribute and no longer has the old one.

    ON FAILURE: the changelog is wrong; state the rename as 0.3.0 name -> final
    name.
    """
    target = importlib.import_module(_CLASSES[cls].rsplit(".", 1)[0])
    target = getattr(target, _CLASSES[cls].rsplit(".", 1)[1])
    assert hasattr(target, new), "%s.%s does not exist" % (cls, new)
    assert not hasattr(target, old), "%s.%s still exists" % (cls, old)


def test_added_paths_resolve():
    """Every fully qualified path the Added subsection names exists.

    ON FAILURE: the changelog is wrong; correct the path.
    """
    section = _unreleased()
    if "### Added\n" not in section:
        pytest.skip("the newest section has no Added subsection")
    paths = sorted(set(_TICKED_PATH.findall(_subsection(section, "Added"))))
    missing = [p for p in paths if not _resolves(p)]
    assert not missing, missing
