# Spent-When: PERMANENT(Hist1D stops offering alim)
# Supersedes: none
"""Tests for ``alim`` on ``Hist1D``, the same limits every binned plot has.

``alim`` limits the aggregated value of a bin after ``axnorm`` and ``clim``,
bounds inclusive, read as values or as quantiles of the aggregated values.
The bins below hold 3, 2 and 1 rows by hand (edges 0, 1, 2, 3, right-closed).
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from tests.tolerances import exact  # noqa: E402

_NEW = pytest.mark.xfail(strict=True, reason="Hist1D has no alim yet")

X = pd.Series([0.2, 0.5, 0.8, 1.3, 1.7, 2.5], index=[10, 11, 12, 13, 14, 15])
EDGES = np.array([0.0, 1.0, 2.0, 3.0])


def _hist():
    return Hist1D(X, nbins=EDGES)


@_NEW
def test_alim_masks_the_bins_outside_it():
    """alim (2, None) keeps the bins of 3 and 2 rows; the bin of 1 is NaN.

    ON FAILURE: the code is wrong.
    """
    h = _hist()
    h.set_alim(2, None)
    assert h.agg().to_numpy() == exact([3.0, 2.0, np.nan], nan_ok=True)


@_NEW
def test_alim_applies_after_axnorm():
    """With axnorm "t" the bins read 1, 2/3, 1/3; alim (0.5, None) keeps two.

    ON FAILURE: the code is wrong.
    """
    h = _hist()
    h.set_axnorm("t")
    h.set_alim(0.5, None)
    assert h.agg().to_numpy() == exact([1.0, 2.0 / 3.0, np.nan], nan_ok=True)


@_NEW
def test_get_plotted_data_honours_alim():
    """The rows of the bins alim keeps: labels 10 to 14.

    ON FAILURE: the code is wrong.
    """
    h = _hist()
    h.set_alim(2, None)
    assert h.get_plotted_data().index.tolist() == [10, 11, 12, 13, 14]


@_NEW
def test_a_quantile_alim_reads_quantiles_of_the_bins():
    """The 0.5 quantile of the counts 3, 2, 1 is 2: the upper bound keeps 2 and 1.

    ON FAILURE: the code is wrong.
    """
    h = _hist()
    h.set_alim(None, 0.5, kind="quantile")
    assert h.agg().to_numpy() == exact([np.nan, 2.0, 1.0], nan_ok=True)


@_NEW
def test_every_plot_shares_one_alim():
    """Hist1D, Hist2D and Scatter set and apply alim with the same methods.

    ON FAILURE: the code is wrong.
    """
    for name in ("set_alim", "_apply_alim", "alim", "alim_kind"):
        assert getattr(Hist1D, name) is getattr(Hist2D, name) is getattr(Scatter, name)


@_NEW
def test_hist1d_repr_shows_its_alim():
    """A set alim appears in the repr, as on the colour plots.

    ON FAILURE: the code is wrong.
    """
    h = _hist()
    h.set_alim(2, None)
    assert "  alim: lower=2, upper=None (value)" in repr(h).splitlines()
