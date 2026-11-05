# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
r"""A density's ``Count`` label states the units of the bins it is per.

``binning.normalize`` divides a density by the bin measure it is taken over:
"d" by each cell's width (1-D) or area (2-D), "cd" by each row's y-width
within a column, "rd" by each column's x-width within a row. On a log axis the
bins are measured in ``log10`` of the data. So the density's units are the
inverse of each such axis's units, ``dex^{-1}`` for a log axis, and an axis
whose label states no units contributes no factor.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.plotting.hist1d import Hist1D
from solarwindpy.plotting.hist2d import Hist2D
from solarwindpy.plotting.labels.base import TeXlabel
from solarwindpy.plotting.spiral import SpiralPlot2D

KMS = r"\left(\mathrm{km \; s^{-1}}\right)^{-1}"
PER_CC = r"\left(\mathrm{cm}^{-3}\right)^{-1}"
DEX = r"\mathrm{dex}^{-1}"
V = TeXlabel(("v", "", "p1"))
N = TeXlabel(("n", "", "p1"))


def _data():
    rng = np.random.default_rng(3)
    v = pd.Series(rng.normal(400, 50, 2000), name="v")
    n = pd.Series(10 ** rng.normal(0.8, 0.2, 2000), name="n")
    return v, n


@pytest.mark.parametrize(
    "axnorm, logy, units",
    [
        ("d", False, rf"{KMS} \, {PER_CC}"),
        ("d", True, rf"{KMS} \, {DEX}"),
        ("cd", False, PER_CC),
        ("cd", True, DEX),
        ("rd", True, KMS),
    ],
)
def test_hist2d_density_units(axnorm, logy, units):
    """A 2-D density is per x and y units; "cd" per y, "rd" per x.

    ON FAILURE: the code is wrong.
    """
    v, n = _data()
    h = Hist2D(v, n, logy=logy, nbins=10, axnorm=axnorm)
    h.set_labels(x=V, y=N)
    assert h.labels.z.units == units
    assert str(h.labels.z).endswith(r"\; \left[%s\right]$" % units)


@pytest.mark.parametrize("logx, units", [(False, KMS), (True, DEX)])
def test_hist1d_density_units(logx, units):
    """A 1-D density is per x units, or per dex on a log axis.

    ON FAILURE: the code is wrong.
    """
    v, _ = _data()
    h = Hist1D(v, logx=logx, nbins=10, axnorm="d")
    h.set_labels(x=V)
    assert h.labels.y.units == units


def test_spiral_density_units():
    """An adaptive-mesh density is per cell area, x units times y units.

    ON FAILURE: the code is wrong.
    """
    v, n = _data()
    sp = SpiralPlot2D(v, n, logy=True, axnorm="d", min_per_bin=100)
    sp.set_labels(x=V, y=N)
    assert sp.labels.z.units == rf"{KMS} \, {DEX}"


def test_axis_without_units_contributes_no_factor():
    """An axis labelled by a plain string has no known units; it is left out.

    A log axis is per dex whatever its label.

    ON FAILURE: the code is wrong.
    """
    v, n = _data()
    linear = Hist2D(v, n, nbins=10, axnorm="d")
    assert linear.labels.z.units == ""
    assert str(linear.labels.z) == r"$\mathrm{Probability \, Density}$"
    logy = Hist2D(v, n, logy=True, nbins=10, axnorm="d")
    assert logy.labels.z.units == DEX


def test_units_follow_axis_labels_set_later():
    """Setting the axis labels after the plot is built updates the density units.

    ON FAILURE: the code is wrong.
    """
    v, n = _data()
    h = Hist2D(v, n, nbins=10, axnorm="d")
    assert h.labels.z.units == ""
    h.set_labels(x=V)
    assert h.labels.z.units == KMS
    h.set_labels(y=N)
    assert h.labels.z.units == rf"{KMS} \, {PER_CC}"


def test_non_density_normalizations_are_unchanged():
    """A count divided by a maximum stays a pure number.

    ON FAILURE: the code is wrong.
    """
    v, n = _data()
    h = Hist2D(v, n, nbins=10, axnorm="t")
    h.set_labels(x=V, y=N)
    assert h.labels.z.units == r"\#"
