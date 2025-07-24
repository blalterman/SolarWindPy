import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from solarwindpy.plotting.labels.special import (
    ManualLabel,
    Vsw,
    CarringtonRotation,
    Count,
    Power,
    Probability,
    CountOther,
    MathFcn,
    SSN,
    ComparisonLable,
    Xcorr,
)


def test_manual_label_properties():
    """Check basic ManualLabel formatting."""
    lbl = ManualLabel("Manual Label", "dimless")
    assert lbl.tex == "Manual Label"
    assert lbl.unit == r"\mathrm{\#}"
    assert lbl.path == Path("Manual-Label")
    assert str(lbl) == r"$\mathrm{Manual \; Label} \; [\mathrm{\#}]$"


def test_manual_label_custom_path():
    """ManualLabel uses provided path value."""
    lbl = ManualLabel("Custom", "kms", path="alt")
    assert lbl.path == Path("alt")
    assert str(lbl) == r"$\mathrm{Custom} \; [\mathrm{km \; s^{-1}}]$"


def test_vsw_label():
    """Vsw label exposes tex, units, and path."""
    lbl = Vsw()
    assert lbl.tex == r"V_\mathrm{SW}"
    assert lbl.units == r"\mathrm{km \, s^{-1}}"
    assert lbl.path == Path("vsw")
    assert str(lbl) == r"$V_\mathrm{SW} \; \left[\mathrm{km \, s^{-1}}\right]$"


def test_carrington_rotation():
    """CarringtonRotation handles short and long labels."""
    short = CarringtonRotation()
    assert short.tex == r"\mathrm{CR}"
    assert str(short) == r"$\mathrm{CR} \; [\#]$"

    long = CarringtonRotation(short_label=False)
    assert long.tex == r"\mathrm{Carrington \; Rotation}"
    assert str(long) == r"$\mathrm{Carrington \; Rotation} \; [\#]$"
    assert short.path == long.path == Path("CarrRot")


def test_count_label():
    """Count label with and without normalization."""
    base_lbl = Count()
    assert base_lbl.tex == r"\mathrm{Count}"
    assert str(base_lbl) == r"$\mathrm{Count} \; [\#]$"
    assert base_lbl.path == Path("count")

    row_lbl = Count("r")
    assert row_lbl.tex == r"\mathrm{Row \, Norm \, Count}"
    assert row_lbl.path == Path("count/Rnorm")

    dens_lbl = Count("d")
    assert dens_lbl.tex == r"\mathrm{Probability \, Density}"
    assert dens_lbl.path == Path("count/Dnorm")

    with pytest.raises(AssertionError):
        Count("bad")


def test_power_label():
    """Power label formatting."""
    lbl = Power()
    assert lbl.tex == r"\mathrm{Power}"
    assert lbl.units == r"\mathrm{\#}"
    assert lbl.path == Path("power")
    assert str(lbl) == r"$\mathrm{Power} \; [\mathrm{\#}]$"


def test_probability_label():
    """Probability label uses other label and comparison."""
    base_lbl = Vsw()
    lbl = Probability(base_lbl, "> 0")
    assert lbl.tex == r"\mathrm{Prob.}(V_\mathrm{SW} \, > \, 0)"
    assert lbl.units == r"\%"
    assert lbl.path == Path("prob-vsw-GT_0")
    assert str(lbl) == r"$\mathrm{Prob.}(V_\mathrm{SW} \, > \, 0) \; [\%]$"


def test_count_other_label():
    """CountOther respects newline and comparison settings."""
    base_lbl = Vsw()
    lbl = CountOther(base_lbl, "> 1", new_line_for_units=True)
    assert "$\n$" in str(lbl)
    assert lbl.units == r"\#"
    assert lbl.path == Path("cnt-vsw-GT 1")


def test_mathfcn_label():
    """MathFcn handles dimensionless and non-dimensionless units."""
    base_lbl = Vsw()
    dim = MathFcn("log", base_lbl)
    assert dim.units == r"\mathrm{\#}"
    assert dim.path == Path("log-vsw")
    assert dim.tex == r"\mathrm{log}(V_\mathrm{SW})"

    nodim = MathFcn("sin", base_lbl, dimensionless=False)
    assert nodim.units == r"\mathrm{sin}\left(\mathrm{km \, s^{-1}}\right)"
    assert nodim.path == Path("sin-vsw")


def test_ssn_label():
    """SSN label for 13 month smoothed data."""
    lbl = SSN("M13")
    assert lbl.tex == r"\mathrm{13 \; Month \; Smoothed \; SSN}"
    assert lbl.path == Path("M13ssn")
    assert str(lbl) == r"$\mathrm{13 \; Month \; Smoothed \; SSN} \; [\#]$"


def test_comparison_lable():
    """ComparisonLable builds tex and path from two labels."""
    a = Vsw()
    b = Vsw()
    lbl = ComparisonLable(a, b, "subtract")
    assert lbl.tex == "{V_\\mathrm{SW}} - {V_\\mathrm{SW}}"
    assert lbl.units == r"\mathrm{km \, s^{-1}}"
    assert lbl.path == Path("subtract-vsw-vsw")
    assert str(lbl) == r"${V_\mathrm{SW}} - {V_\mathrm{SW}} \; [\mathrm{km \, s^{-1}}]$"

    with pytest.raises(ValueError):
        ComparisonLable(a, Power(), "add")


def test_xcorr_label():
    """Xcorr returns appropriate tex for short and long forms."""
    a = Vsw()
    b = Vsw()
    long = Xcorr(a, b, "pearson")
    assert long.tex == r"\mathrm{{Pearson}}(V_\mathrm{SW},V_\mathrm{SW})"
    assert long.path == Path("XcorrPearson-vsw-vsw")
    assert str(long) == r"$\mathrm{{Pearson}}(V_\mathrm{SW},V_\mathrm{SW}) \; [\#]$"

    short = Xcorr(a, b, "spearman", short_tex=True)
    assert short.tex == r"\rho_{S}(V_\mathrm{SW},V_\mathrm{SW})"
    assert short.path == Path("XcorrSpearman-vsw-vsw")
    assert str(short) == r"$\rho_{S}(V_\mathrm{SW},V_\mathrm{SW}) \; [\#]$"
