# Spent-When: PERMANENT(SolarWindPy stops shipping example data)
# Supersedes: none
"""The example ``Plasma`` that docstring examples load, and Plasma's input logging.

Expected values are the example CSVs' own bytes (the chosen input):
``solarwindpy/core/data/example_{epoch,plasma,spacecraft}.csv``.
"""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from solarwindpy.core.plasma import Plasma
from solarwindpy.examples import load_plasma

REPO = Path(__file__).resolve().parents[1]

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
    ``core/data/*.csv`` in pyproject.toml; this test does not build one.

    ON FAILURE: the code is wrong; the loader must read its CSVs from the
    package (``importlib.resources``), not from a path outside it.
    """
    installed = tmp_path / "site-packages"
    shutil.copytree(
        REPO / "solarwindpy",
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
    )
    assert result.returncode == 0, result.stderr
    module_file, summary = result.stdout.splitlines()
    assert Path(module_file).is_relative_to(installed)
    assert summary == "('a', 'e', 'p1', 'p2') 3"


def test_load_plasma_holds_the_example_species_rows_and_spacecraft():
    """The example has species a, e, p1, p2, three rows, and the PSP trajectory.

    Values are the example CSVs: ``n||p1`` is 1, 2, 3; ``pos_HCI|x|`` is
    -42, -22, -34; ``v_HCI|y|`` is -80, -70, -90; ``Carr|lon|`` is -26, -36, -16.

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

    sc = plasma.spacecraft
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
    assert sc.position.data.loc[:, "x"].tolist() == [-42.0, -22.0, -34.0]
    assert sc.velocity.data.loc[:, "y"].tolist() == [-80.0, -70.0, -90.0]
    assert sc.carrington.loc[:, "lon"].tolist() == [-26.0, -36.0, -16.0]
    assert plasma.auxiliary_data is None


def test_plasma_no_longer_accepts_log_plasma_stats():
    """The removed ``log_plasma_stats`` argument raises ``TypeError``.

    ON FAILURE: the code is wrong; the plasma-statistics logging was removed
    and the argument must not be accepted silently.
    """
    data = load_plasma().data
    with pytest.raises(TypeError, match="log_plasma_stats"):
        Plasma(data, "p1", log_plasma_stats=True)


def test_plasma_logs_each_optional_input_not_passed(caplog):
    """Plasma logs "No <input> data passed to Plasma" for each None input only.

    ON FAILURE: the code is wrong; the INFO message for a missing optional
    input was lost, or is logged for an input that was passed.
    """
    plasma = load_plasma()
    flags = pd.DataFrame({("quality", "", ""): [0, 1, 0]}, index=plasma.epoch)
    flags.columns.names = ["M", "C", "S"]

    with caplog.at_level(logging.INFO, logger="solarwindpy"):
        Plasma(plasma.data, "p1")
    assert "No spacecraft data passed to Plasma" in caplog.messages
    assert "No auxiliary_data data passed to Plasma" in caplog.messages

    caplog.clear()
    with caplog.at_level(logging.INFO, logger="solarwindpy"):
        Plasma(plasma.data, "p1", spacecraft=plasma.spacecraft, auxiliary_data=flags)
    assert not [m for m in caplog.messages if m.startswith("No ")]
