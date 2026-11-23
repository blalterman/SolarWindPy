"""The example ``Plasma`` that docstring examples load.

Expected values are the example CSVs' own bytes (the chosen input):
``src/solarwindpy/examples/data/example_{epoch,plasma,spacecraft}.csv``.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from solarwindpy.examples import load_plasma

REPO = Path(__file__).resolve().parents[2]

PROBE = """\
import solarwindpy
from solarwindpy.examples import load_plasma

plasma = load_plasma()
print(solarwindpy.__file__)
print(plasma.species, plasma.data.shape[0])
"""


def test_load_plasma_finds_its_data_through_the_package(tmp_path):
    """``load_plasma`` works from a copy of the package alone.

    The copy is the ``solarwindpy`` directory without the rest of the
    repository, imported from an empty working directory, so a loader that
    reads from ``tests/`` or any path outside the package, found relative to
    the package file or the working directory, fails here. A wheel ships
    the CSVs through the ``[tool.setuptools.package-data]`` glob
    ``examples/data/*.csv`` in pyproject.toml; this test does not build one.

    ON FAILURE: the code is wrong; the loader must read its CSVs from the
    package (``importlib.resources``), not from a path outside it.
    """
    installed = tmp_path / "site-packages"
    shutil.copytree(
        REPO / "src" / "solarwindpy",
        installed / "solarwindpy",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    workdir = tmp_path / "work"
    workdir.mkdir()
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=workdir,
        env={**os.environ, "PYTHONPATH": str(installed)},
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    module_file, summary = result.stdout.splitlines()
    assert Path(module_file).is_relative_to(installed)
    assert summary == "('a', 'e', 'p1', 'p2') 3"


def test_load_plasma_holds_the_example_species_rows_and_spacecraft():
    """The example has species a, e, p1, p2, three rows, and the PSP trajectory.

    Values are the example CSVs: ``n||p1`` is 1, 2, 3; ``pos|x|`` is
    -42, -22, -34; ``v|y|`` is -80, -70, -90; ``carr|lon|`` is -26, -36, -16.

    ON FAILURE: the code is wrong, unless the author changed the example
    CSVs; then update the values here.
    """
    plasma = load_plasma()

    assert plasma.species == ("a", "e", "p1", "p2")
    assert plasma.epoch.strftime("%Y-%m-%d %H:%M:%S.%f").tolist() == [
        "1995-01-01 12:35:00.000000",
        "2022-03-23 19:29:09.000000",
        "2022-10-09 01:47:01.234560",
    ]
    assert plasma.data.loc[:, ("n", "", "p1")].tolist() == [1.0, 2.0, 3.0]

    sc = plasma.sc
    assert (sc.name, sc.frame) == ("PSP", "HCI")
    assert sc.data.columns.tolist() == [
        ("carr", "lat"),
        ("carr", "lon"),
        ("pos", "x"),
        ("pos", "y"),
        ("pos", "z"),
        ("v", "x"),
        ("v", "y"),
        ("v", "z"),
    ]
    assert sc.data.index.equals(plasma.epoch)
    assert sc.pos.data.loc[:, "x"].tolist() == [-42.0, -22.0, -34.0]
    assert sc.v.data.loc[:, "y"].tolist() == [-80.0, -70.0, -90.0]
    assert sc.carr.loc[:, "lon"].tolist() == [-26.0, -36.0, -16.0]
    assert plasma.aux is None
