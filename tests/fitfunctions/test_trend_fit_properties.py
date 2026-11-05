import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions import gaussians, trend_fits, lines
from solarwindpy.fitfunctions.core import FitDegeneracyWarning

# The trend's y and yerr: each column's Gaussian centroid and width.
MU = ("mu", "value")
SIGMA = ("sigma", "value")


@pytest.fixture
def agged():
    xbins = pd.interval_range(0, 5, periods=5)
    ybins = pd.interval_range(0, 2, periods=2)
    data = {
        ybins[0]: np.array([1, 2, 3, 4, 5]),
        ybins[1]: np.array([2, 3, 4, 5, 6]),
    }
    return pd.DataFrame(data, index=xbins)


def test_logx_true_make_fit(agged):
    """Ensure ``logx`` propagates to the trend function."""
    trend_fit = trend_fits.TrendFit(
        agged, gaussians.Gaussian, lines.Line, y=MU, yerr=SIGMA, logx=True
    )
    assert trend_fit.logx is True
    # Two bins for a two-parameter trend: the covariance is not finite.
    with pytest.warns(FitDegeneracyWarning, match="m and b have a non-finite"):
        trend_fit.make_fit()
    assert isinstance(trend_fit.trend, lines.Line)
