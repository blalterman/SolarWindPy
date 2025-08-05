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
