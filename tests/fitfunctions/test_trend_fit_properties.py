import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions import trend_fits, lines


@pytest.fixture
def agged():
    xbins = pd.interval_range(0, 5, periods=5)
    ybins = pd.interval_range(0, 2, periods=2)
    data = {
        ybins[0]: np.array([1, 2, 3, 4, 5]),
        ybins[1]: np.array([2, 3, 4, 5, 6]),
    }
    return pd.DataFrame(data, index=xbins)


def test_popt1d_keys_property(agged):
    trend_fit = trend_fits.TrendFit(agged, lines.Line)
    assert trend_fit.popt1d_keys == trend_fits.Popt1DKeys("mu", "sigma")


def test_trend_logx_true_make_trend_func(agged):
    """Ensure ``trend_logx`` propagates to the trend function."""
    trend_fit = trend_fits.TrendFit(agged, lines.Line, trend_logx=True)
    assert trend_fit.trend_logx is True
    trend_fit.make_ffunc1ds()
    trend_fit.make_1dfits()
    trend_fit.make_trend_func()
    assert isinstance(trend_fit.trend_func, lines.Line)
