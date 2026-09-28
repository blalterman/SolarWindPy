# Spent-When: PERMANENT(pyproject.toml stops being the single declaration of supported Python versions)
# Supersedes: none
"""Every Python version the repository declares satisfies ``requires-python``.

``pyproject.toml`` is the single declaration of what the package supports.
Classifiers, the tox envlist, Read the Docs, the conda recipe, and the GitHub
workflows each restate a Python version; this module reads each site locally
and checks it against ``requires-python``, so a floor that moves in one place
and not the others fails the default suite rather than a later release.
"""

import re
import tomllib
from pathlib import Path

import yaml
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]


def _requires_python():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return pyproject["project"]["requires-python"]


def _floor(requires_python):
    floors = [s.version for s in SpecifierSet(requires_python) if s.operator == ">="]
    assert len(floors) == 1, f"expected one >= bound in {requires_python!r}"
    return Version(floors[0])


def _workflow_versions(node, path, found):
    """Collect python-version / PYTHON_VERSION values from a workflow tree."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("python-version", "PYTHON_VERSION"):
                values = value if isinstance(value, list) else [value]
                for v in values:
                    v = str(v)
                    if "${{" not in v:
                        found.append((f"{path}: {key}", v))
            else:
                _workflow_versions(value, path, found)
    elif isinstance(node, list):
        for item in node:
            _workflow_versions(item, path, found)


def declared_python_versions():
    """Return ``(site, version)`` for every Python version the repo declares."""
    found = []

    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    for c in pyproject["project"]["classifiers"]:
        m = re.fullmatch(r"Programming Language :: Python :: (3\.\d+)", c)
        if m:
            found.append(("pyproject.toml: classifiers", m.group(1)))

    tox = (REPO_ROOT / "tox.ini").read_text()
    envlist = re.search(r"^envlist\s*=\s*(.+)$", tox, re.MULTILINE).group(1)
    for major, minor in re.findall(r"py(\d)(\d+)", envlist):
        found.append(("tox.ini: envlist", f"{major}.{minor}"))

    rtd = yaml.safe_load((REPO_ROOT / ".readthedocs.yaml").read_text())
    found.append(
        (".readthedocs.yaml: build.tools.python", str(rtd["build"]["tools"]["python"]))
    )

    for wf in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        _workflow_versions(
            yaml.safe_load(wf.read_text()), f".github/workflows/{wf.name}", found
        )

    return found


def declared_python_floors():
    """Return ``(site, version)`` for every declared minimum Python version."""
    recipe = (REPO_ROOT / "recipe" / "meta.yaml").read_text()
    return [
        ("recipe/meta.yaml: python >=", v)
        for v in re.findall(r"^\s*-\s*python\s*>=\s*([\d.]+)", recipe, re.MULTILINE)
    ]


def test_requires_python_sites_are_found():
    """The scan reaches every source it claims to read.

    An empty scan and a consistent repository look identical to the tests
    below, so each source must contribute at least one version.

    ON FAILURE: the fixture no longer separates a consistent repository from
    an unread one; fix the fixture (the site readers above).
    """
    sites = {site.split(":")[0] for site, _ in declared_python_versions()}
    assert {"pyproject.toml", "tox.ini", ".readthedocs.yaml"} <= sites
    assert any(s.startswith(".github/workflows/") for s in sites)
    assert declared_python_floors()


def test_declared_versions_satisfy_requires_python():
    """Every declared Python version satisfies ``requires-python``.

    ON FAILURE: the code is wrong; update the listed sites or requires-python
    in pyproject.toml so they agree.
    """
    spec = SpecifierSet(_requires_python())
    drift = [
        f"{site} = {v!r}"
        for site, v in declared_python_versions()
        if not spec.contains(Version(v), prereleases=True)
    ]
    assert not drift, f"outside requires-python {spec}: " + "; ".join(drift)


def test_declared_floors_equal_requires_python_floor():
    """Every declared minimum Python equals the ``requires-python`` floor.

    ON FAILURE: the code is wrong; carry the requires-python floor to the
    listed sites.
    """
    floor = _floor(_requires_python())
    drift = [
        f"{site} {v!r}" for site, v in declared_python_floors() if Version(v) != floor
    ]
    assert not drift, f"differs from requires-python floor {floor}: " + "; ".join(drift)


def test_lowest_classifier_is_requires_python_floor():
    """The lowest Python classifier is the ``requires-python`` floor.

    ON FAILURE: the code is wrong; add or remove classifiers so the lowest
    equals the requires-python floor.
    """
    classifiers = [
        Version(v)
        for site, v in declared_python_versions()
        if site == "pyproject.toml: classifiers"
    ]
    assert min(classifiers) == _floor(_requires_python())
