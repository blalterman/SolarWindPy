import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions import TrendFit, Line, Gaussian


@pytest.fixture()
def example_df():
    x_bins = pd.interval_range(0, 5, periods=5)
    cols = pd.interval_range(0, 2, periods=2)
    mu = [1.5, 3.0]
    sigma = [0.5, 0.8]
    amp = [2.0, 1.0]
    df = pd.DataFrame(index=x_bins)
    for c, m, s, a in zip(cols, mu, sigma, amp):
        df[c] = a * np.exp(-0.5 * ((x_bins.mid - m) / s) ** 2)
    return df


def test_trendfit_workflow(example_df):
    tf = TrendFit(example_df, Line, ffunc1d=Gaussian)
    tf.make_ffunc1ds()
    assert len(tf.ffuncs) == example_df.shape[1]

    tf.make_1dfits()
    assert tf.bad_fits.empty
    popt = tf.popt_1d
    assert {"mu", "sigma", "A"} <= set(popt.columns)
    assert np.all(np.isfinite(popt.values))

    tf.make_trend_func()
    tf.trend_func.make_fit()
    params = tf.trend_func.popt
    assert {"m", "b"} <= params.keys()
    assert np.all(np.isfinite(list(params.values())))


def test_set_fitfunctions_type_error(example_df):
    tf = TrendFit(example_df, Line, ffunc1d=Gaussian)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(int, Line)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(Gaussian, int)
