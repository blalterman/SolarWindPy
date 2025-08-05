import importlib.util
from pathlib import Path
import pytest


@pytest.fixture(scope="module")
def labels_base():
    """Load :mod:`solarwindpy.plotting.labels.base` without side effects."""
    path = Path(__file__).resolve().parents[3] / "plotting" / "labels" / "base.py"
    spec = importlib.util.spec_from_file_location("swp_labels_base", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def texlabel_basic(labels_base):
    """Return a typical :class:`TeXlabel` instance."""
    return labels_base.TeXlabel(("v", "x", "p"))


@pytest.fixture()
def texlabel_ratio(labels_base):
    """Return a ratio :class:`TeXlabel` instance."""
    return labels_base.TeXlabel(("v", "x", "p"), ("n", "", "p"))


def test_run_species_substitution(labels_base):
    """Verify direct species substitution helper."""
    cases = {
        "p": ("p", 1),
        "p1+p2": ("p_1+p_2", 2),
        "a+p1": ("\\alpha+p_1", 2),
        "Fe": ("\\mathrm{Fe}", 1),
    }
    for pattern, expected in cases.items():
        assert labels_base._run_species_substitution(pattern) == expected


def test_texlabel_attributes(texlabel_basic):
    """Check attributes of a typical :class:`TeXlabel`."""
    assert texlabel_basic.tex == "{v}_{{X};{p}}"
    assert texlabel_basic.units == "\\mathrm{km \\; s^{-1}}"
    assert texlabel_basic.path == Path("v_x_p")
    assert (
        texlabel_basic.with_units
        == "${v}_{{X};{p}} \\; \\left[\\mathrm{km \\; s^{-1}}\\right]$"
    )


def test_texlabel_ratio_attributes(texlabel_ratio):
    """Check attributes of a ratio :class:`TeXlabel`."""
    assert texlabel_ratio.tex == "{v}_{{X};{p}}/n_{p}"
    assert texlabel_ratio.units == "\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}"
    assert texlabel_ratio.path == Path("v_x_p-OV-n_p")
    assert (
        texlabel_ratio.with_units
        == "${v}_{{X};{p}}/n_{p} \\; \\left[\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}\\right]$"
    )


def test_texlabel_equality_and_hash(texlabel_basic, texlabel_ratio, labels_base):
    """Ensure equality and hashing are based on ``str``."""
    same_basic = labels_base.TeXlabel(("v", "x", "p"))
    same_ratio = labels_base.TeXlabel(("v", "x", "p"), ("n", "", "p"))

    assert texlabel_basic == same_basic
    assert hash(texlabel_basic) == hash(same_basic)

    assert texlabel_ratio == same_ratio
    assert hash(texlabel_ratio) == hash(same_ratio)
