# Spent-When: PERMANENT(agg stops counting cells with numpy.bincount)
# Supersedes: none
"""Tests for the count path of ``BinnedPlot.agg``.

A count needs no groupby: ``numpy.bincount`` of the rows' cell codes gives it.
``agg`` takes that path when the aggregation is a count with no keywords, and
its result must equal what a pandas groupby count gives, the reference here,
built in the test from the plot's own cell codes and run through the same
``clim``, ``axnorm`` and cell filter. Empty cells stay NaN.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

RNG = np.random.default_rng(11)
N = 2000
# A gap in x around 0 leaves empty bins in the middle of the grid.
_x = RNG.normal(size=N)
X = pd.Series(np.where(np.abs(_x) < 0.4, _x + 3, _x))
Y = pd.Series(RNG.normal(size=N))


def _plots():
    yield "Hist1D", Hist1D(X, nbins=20), ("t", "d")
    yield "Hist2D", Hist2D(X, Y, nbins=15), ("t", "d", "c", "r", "cd", "rd")
    yield (
        "SpiralPlot2D",
        SpiralPlot2D(X, Y, initial_bins=4, min_per_bin=60),
        ("t", "d"),
    )


def _groupby_reference(h):
    """agg("count") rebuilt with a pandas groupby on the plot's cell codes."""
    codes = np.asarray(h.binning.codes())
    inside = codes >= 0
    cnt = (
        pd.Series(np.ones(inside.sum(), dtype=np.int64)).groupby(codes[inside]).count()
    )
    agg = cnt.astype(np.int64)
    c0, c1 = h.clim
    if c0 is not None:
        agg = agg.where(cnt >= c0)
    if c1 is not None:
        agg = agg.where(cnt <= c1)
    agg = h.binning.postfilter(agg)
    cells = h.binning.cells
    positions = agg.index.to_numpy()
    agg = agg.set_axis(cells[positions])
    agg = h.binning.normalize(agg, h.axnorm, positions)
    return agg.reindex(cells)


CASES = [
    pytest.param(name, plot, axnorm, clim, id=f"{name}-{axnorm}-{clim}")
    for name, plot, norms in _plots()
    for axnorm in (None, *norms)
    for clim in (None, 5)
]


@pytest.mark.parametrize("name, h, axnorm, clim", CASES)
def test_count_equals_a_groupby_count(name, h, axnorm, clim):
    """``agg(fcn="count")`` equals the groupby reference, empty cells NaN.

    ON FAILURE: the code is wrong.
    """
    h.set_clim(clim, None)
    h.set_axnorm(axnorm)
    got = h.agg(fcn="count")
    expected = _groupby_reference(h)
    np.testing.assert_array_equal(got.to_numpy(), expected.to_numpy())
    assert got.index.equals(expected.index)
    assert got.isna().any()  # the gap leaves empty cells


def test_a_count_does_not_group_the_rows():
    """A count runs without ``_grouped_by_cell``; a mean still uses it.

    ON FAILURE: the code is wrong.
    """
    h = Hist2D(X, Y, nbins=15)

    def refuse(*args):
        raise AssertionError("count went through the groupby")

    h._grouped_by_cell = refuse
    counts = h.agg(fcn="count")
    assert counts.sum() == N
    with pytest.raises(AssertionError, match="groupby"):
        h.agg(fcn="mean")
