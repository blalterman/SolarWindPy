# Spent-When: PERMANENT(SolarWindPy stops publishing wheels and sdists)
# Supersedes: none
"""Check that a built wheel and sdist ship only what each is meant to ship.

The wheel is what users install: it holds the ``solarwindpy`` package, its
package data, and its ``.dist-info``, and no file in it carries a
``Spent-When`` purge header. The sdist is what packagers such as conda-forge
rebuild from: it keeps ``tests/`` and ``docs/source/`` and drops
development-only material (``.claude/``, ``.github/``, ``docs/dispatches/``,
``tmp/``, ``spike/``), which ``MANIFEST.in`` prunes.

``tests/test_release_artifacts.py`` and the release workflows both read these
functions, so the test and CI apply one definition.

Usage::

    python scripts/check_release_artifacts.py dist/

Exits 1 and lists every problem when the directory's single wheel or sdist
holds something it should not.
"""

import sys
import tarfile
import zipfile
from pathlib import Path

PACKAGE = "solarwindpy"
SDIST_SRC = "src/"
SDIST_PACKAGE = f"{SDIST_SRC}{PACKAGE}/"
MARKER = b"Spent-When"
SDIST_REQUIRED = ("tests/", "docs/source/")
SDIST_PRUNED = (".claude/", ".github/", "docs/dispatches/", "tmp/", "spike/")


def wheel_stray_entries(wheel):
    """Return the wheel's top-level entries other than the package and its dist-info."""
    with zipfile.ZipFile(wheel) as zf:
        tops = {name.split("/", 1)[0] for name in zf.namelist()}
    return sorted(
        top
        for top in tops
        if top != PACKAGE
        and not (top.startswith(f"{PACKAGE}-") and top.endswith(".dist-info"))
    )


def wheel_spent_when_files(wheel):
    """Return the wheel members whose bytes contain ``Spent-When``."""
    with zipfile.ZipFile(wheel) as zf:
        return sorted(name for name in zf.namelist() if MARKER in zf.read(name))


def sdist_members(sdist):
    """Return the sdist's member paths with the ``<name>-<version>/`` prefix removed."""
    with tarfile.open(sdist) as tf:
        names = tf.getnames()
    return sorted({name.split("/", 1)[1] for name in names if "/" in name})


def sdist_missing(members):
    """Return the required sdist directories that hold no member."""
    return [d for d in SDIST_REQUIRED if not any(m.startswith(d) for m in members)]


def sdist_pruned_present(members):
    """Return the development-only directories the sdist still holds."""
    return [d for d in SDIST_PRUNED if any(m.startswith(d) for m in members)]


def wheel_missing_package_files(wheel, members):
    """Return the sdist's ``src/solarwindpy/`` files that the wheel does not install.

    Every package file the sdist carries, data files such as
    ``ssn_extrema.csv`` included, must reach the wheel; a data file that
    reaches only the sdist fails at import time for anyone who installs.
    The sdist holds the package under ``src/``; the wheel installs it at its
    top level, so ``src/solarwindpy/x`` in the sdist is ``solarwindpy/x`` in
    the wheel.
    """
    with zipfile.ZipFile(wheel) as zf:
        installed = set(zf.namelist())
    # sdist member lists name directories too, without a trailing slash.
    dirs = {m.rsplit("/", 1)[0] for m in members if "/" in m}
    return sorted(
        m
        for m in members
        if m.startswith(SDIST_PACKAGE)
        and m not in dirs
        and m.removeprefix(SDIST_SRC) not in installed
    )


def problems(dist_dir):
    """Return every problem found in ``dist_dir``'s single wheel and sdist."""
    dist_dir = Path(dist_dir)
    wheels = sorted(dist_dir.glob("*.whl"))
    sdists = sorted(dist_dir.glob("*.tar.gz"))
    found = []
    if len(wheels) != 1 or len(sdists) != 1:
        return [
            f"expected one wheel and one sdist in {dist_dir}, "
            f"found {len(wheels)} and {len(sdists)}"
        ]
    wheel, sdist = wheels[0], sdists[0]
    found += [
        f"{wheel.name}: stray top-level entry {e}" for e in wheel_stray_entries(wheel)
    ]
    found += [f"{wheel.name}: Spent-When in {f}" for f in wheel_spent_when_files(wheel)]
    members = sdist_members(sdist)
    found += [
        f"{wheel.name}: does not install {m}"
        for m in wheel_missing_package_files(wheel, members)
    ]
    found += [f"{sdist.name}: missing {d}" for d in sdist_missing(members)]
    found += [f"{sdist.name}: holds {d}" for d in sdist_pruned_present(members)]
    return found


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    found = problems(argv[1])
    for line in found:
        print(line)
    if not found:
        print(f"{argv[1]}: wheel and sdist contents OK")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
