import importlib.util
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def datetime_mod():
    """Load datetime label module without importing :mod:`solarwindpy`.

    Returns
    -------
    module
        The loaded ``datetime`` module.
    """
    root = Path(__file__).resolve().parents[3] / "solarwindpy" / "plotting" / "labels"

    pkg = types.ModuleType("solarwindpy")
    plotting = types.ModuleType("solarwindpy.plotting")
    labels_pkg = types.ModuleType("solarwindpy.plotting.labels")
    pkg.plotting = plotting
    plotting.labels = labels_pkg
    sys.modules["solarwindpy"] = pkg
    sys.modules["solarwindpy.plotting"] = plotting
    sys.modules["solarwindpy.plotting.labels"] = labels_pkg

    def load(name, filename):
        spec = importlib.util.spec_from_file_location(name, root / filename)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    labels_pkg.base = load("solarwindpy.plotting.labels.base", "base.py")
    labels_pkg.special = load("solarwindpy.plotting.labels.special", "special.py")
    dt_mod = load("solarwindpy.plotting.labels.datetime", "datetime.py")
    return dt_mod


def test_timedelta_latex_and_path(datetime_mod):
    """Verify ``Timedelta`` LaTeX and path string."""
    td = datetime_mod.Timedelta("2h")
    assert str(td.path) in ("dt-2h", "dt-2H")
    assert str(td) in ("$\\Delta t \\; [2 \\; \\mathrm{h}]$", "$\\Delta t \\; [2 \\; \\mathrm{H}]$")


def test_datetime_label(datetime_mod):
    """Verify ``DateTime`` label formatting."""
    dt = datetime_mod.DateTime("Day of Year")
    assert str(dt.path) == "day-of-year"
    assert str(dt) == "$\\mathrm{Day \\; of \\; Year}$"


def test_epoch_label(datetime_mod):
    """Verify ``Epoch`` label formatting."""
    epoch = datetime_mod.Epoch("Hour", "Day")
    assert str(epoch.path) == "Hour-of-Day"
    assert str(epoch) == "$\\mathrm{Hour \\, of \\, Day}$"


def test_frequency_label(datetime_mod):
    """Validate ``Frequency`` label output."""
    freq = datetime_mod.Frequency("1h")
    assert str(freq.path) in ("frequency_of_(1 \\; \\mathrm{h})^-1", "frequency_of_(1 \\; \\mathrm{H})^-1")
    assert str(freq) in ("$\\mathrm{Frequency} \\; [(1 \\; \\mathrm{h})^-1]$", "$\\mathrm{Frequency} \\; [(1 \\; \\mathrm{H})^-1]$")


def test_january1st_label(datetime_mod):
    """Validate ``January1st`` label output."""
    jan = datetime_mod.January1st()
    assert str(jan.path) == "January-1st-of-Year"
    assert str(jan) == "$\\mathrm{January \\; 1^{st} \\; of \\; Year}$"
