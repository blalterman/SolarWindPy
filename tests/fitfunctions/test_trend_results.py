# Spent-When: PERMANENT(TrendFit stops exposing its per-bin results as one table)
# Supersedes: none
"""Contract tests for TrendFit's two levels and its per-bin results table.

TrendFit fits one function in each column of a 2-D histogram (the bin level),
then a second function to the trend of one bin-level column across the
columns (the trend level). The bin level's results are one table, the
concatenation of each bin fit's ``results``; the trend reads its ``y`` and
``yerr`` from that table by ``(P, K)`` name, with no default.
"""

import warnings

import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions import trend_fits
from solarwindpy.fitfunctions.core import (
    FitDegeneracyWarning,
    InsufficientDataError,
    NotFittedError,
)
from solarwindpy.fitfunctions.gaussians import Gaussian
from solarwindpy.fitfunctions.hinge import HingeAtPoint
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.fitfunctions.trend_fits import TrendFit
from tests.tolerances import exact, noise_free


# A synthetic hinge that generates the data, not Hinge's reference start:
# (h, yh) = (433, 4.12), rising with slope yh / (433 - 250) and flattening to
# a tenth of that slope past the hinge, so mu stays positive on [250, 650].
H, YH = 433.0, 4.12
M1 = YH / (H - 250.0)
M2 = 0.1 * M1


def _hinge_mu(v):
    return np.minimum(YH + M1 * (v - H), YH + M2 * (v - H))


def _hinge_agged():
    """Noise-free Gaussian columns whose centers follow the reference hinge.

    Twenty speed bins in [250, 650] are the columns; 200 bins in [0, 10] are
    the index. Each column is a Gaussian with ``mu`` on the hinge and a width
    growing with speed, so a Gaussian per column recovers both exactly.
    """
    columns = pd.interval_range(250, 650, periods=20)
    v = columns.mid.to_numpy()
    sigma = 0.3 + 0.001 * (v - 250.0)
    index = pd.interval_range(0, 10, periods=200)
    y = index.mid.to_numpy()
    data = {
        c: 100.0 * np.exp(-0.5 * ((y - m) / s) ** 2)
        for c, m, s in zip(columns, _hinge_mu(v), sigma)
    }
    return pd.DataFrame(data, index=index), v, sigma


# Five columns of noise-free Gaussian counts; with the trend limited to
# y <= 6.5 and w >= 1.05, columns 1-3 are in the trend, column 0 is out by
# its width and column 4 by its centroid.
MUS = [5.0, 4.0, 5.5, 6.0, 7.0]
SIGMAS = [1.0, 1.1, 1.3, 1.2, 1.2]
IN_TREND = [False, True, True, True, False]


def _agged5():
    xbins = pd.interval_range(0, 10, periods=10)
    x = xbins.mid.to_numpy()
    columns = pd.interval_range(0, 5, periods=5)
    return pd.DataFrame(
        {
            col: 10.0 * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
            for col, mu, sigma in zip(columns, MUS, SIGMAS)
        },
        index=xbins,
    )


def _noisy_agged5():
    """``_agged5`` plus seeded noise, so each ``mu`` has a nonzero uncertainty."""
    agged = _agged5()
    rng = np.random.default_rng(5)
    return agged + rng.normal(0, 0.1, agged.shape)


def _trend5(**kwargs):
    kwargs.setdefault("y", ("mu", "value"))
    kwargs.setdefault("yerr", ("sigma", "value"))
    kwargs.setdefault("trend_kwargs", {"ymax": 6.5, "wmin": 1.05})
    tf = TrendFit(_agged5(), Gaussian, Line, **kwargs)
    tf.make_fit()
    return tf


def test_the_authors_example_recovers_the_generating_hinge():
    """A Gaussian per column, then a hinge on mu with yerr = sigma, finds (433, 4.12).

    This is the author's reference use: x is the column center, y each
    column's ``mu`` and yerr each column's width ``sigma``.

    ON FAILURE: the code is wrong.
    """
    agged, v, sigma = _hinge_agged()
    tf = TrendFit(
        agged,
        Gaussian,
        HingeAtPoint,
        y=("mu", "value"),
        yerr=("sigma", "value"),
        trend_kwargs={"guess_xh": 433.0},
    )
    tf.make_fit()

    assert tf.bin_results.loc[:, ("mu", "value")].to_numpy() == noise_free(_hinge_mu(v))
    np.testing.assert_array_equal(tf.trend.observations.raw.x, v)  # column centers
    np.testing.assert_array_equal(
        tf.trend.observations.raw.w, tf.bin_results.loc[:, ("sigma", "value")]
    )
    hinge = tf.trend.results.xs("value", level="K", axis=1).iloc[0]
    assert [hinge["xh"], hinge["yh"]] == noise_free([H, YH])  # the generating hinge
    assert (tf.bin_results.loc[:, ("in_trend", "")]).all()


def test_bin_results_is_the_concatenation_of_each_bin_fits_results():
    """Row k of ``bin_results`` is bin k's ``results``, indexed by the columns.

    ON FAILURE: the code is wrong.
    """
    tf = _trend5()
    res = tf.bin_results
    assert res.index.equals(tf.agged.columns)
    assert list(res.columns.names) == ["P", "K"]
    for key, fit in tf.bin_fits.items():
        expected = fit.results.iloc[0]
        got = res.loc[key, expected.index]
        assert list(got.index) == list(expected.index)
        assert got[("status", "")] == expected[("status", "")]
        values = expected.drop(("status", "")).astype(float).to_numpy()
        assert got.drop(("status", "")).astype(float).to_numpy() == exact(values)
    assert res.loc[:, ("mu", "value")].to_numpy() == noise_free(MUS)
    assert res.loc[:, ("sigma", "value")].to_numpy() == noise_free(SIGMAS)


def _concatenated_bin_results(tf):
    """``bin_results`` rebuilt from each bin fit's public one-row ``results``.

    Concatenate the rows, index them by the columns, and add the trend's
    ``in_trend`` selection: the table ``bin_results`` documents, built
    independently of how ``make_fit`` builds it.
    """
    res = pd.concat([fit.results for fit in tf.bin_fits])
    res.index = tf.agged.columns
    res[("in_trend", "")] = tf.trend.observations.tk_observed
    return res


def _hinge_trend():
    agged = _hinge_agged()[0]
    tf = TrendFit(
        agged,
        Gaussian,
        HingeAtPoint,
        y=("mu", "value"),
        yerr=("sigma", "value"),
        trend_kwargs={"guess_xh": 433.0},
    )
    tf.make_fit()
    return tf


def _failed_bins_trend():
    """Column 1 too sparse to fit; column 3 degenerate, escalated to a failure.

    Column 3's counts sum to zero, so its Gaussian has no estimate and the fit
    from ones leaves mu and sigma degenerate; the escalated
    FitDegeneracyWarning records that bin as failed.
    """
    agged = _agged5()
    sparse, degenerate = agged.columns[1], agged.columns[3]
    agged[sparse] = np.where(np.arange(agged.shape[0]) < 8, np.nan, agged[sparse])
    agged[degenerate] = np.tile([1.0, -1.0], agged.shape[0] // 2)
    tf = TrendFit(agged, Gaussian, Line, y=("mu", "value"), yerr=("sigma", "value"))
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        tf.make_fit()
    status = tf.bin_results.loc[:, ("status", "")]
    assert status[sparse] == "InsufficientDataError"  # the fixture's failures
    assert status[degenerate] == "FitDegeneracyWarning"
    return tf


@pytest.mark.parametrize(
    "build",
    [_trend5, _hinge_trend, _failed_bins_trend],
    ids=["line-trend", "hinge-trend", "failed-bins"],
)
def test_bin_results_equals_the_concatenated_bin_fit_results(build):
    """``bin_results`` is exactly the concatenation of the bin fits' ``results``.

    Values, column MultiIndex, dtypes, index, and failed bins' NaN rows and
    statuses, with Line and HingeAtPoint trends and with failed bins.

    ON FAILURE: the code is wrong.
    """
    tf = build()
    pd.testing.assert_frame_equal(
        tf.bin_results, _concatenated_bin_results(tf), check_exact=True
    )


def test_in_trend_marks_the_bins_the_trend_fit_used():
    """``in_trend`` is the trend fit's own selection of bins.

    ON FAILURE: the code is wrong.
    """
    tf = _trend5()
    in_trend = tf.bin_results.loc[:, ("in_trend", "")].to_numpy()
    np.testing.assert_array_equal(in_trend, IN_TREND)
    np.testing.assert_array_equal(in_trend, tf.trend.observations.tk_observed)


def test_a_failed_bin_keeps_a_nan_row_and_stays_out_of_the_trend():
    """A column too sparse to fit keeps its row, NaN with its status, and is not in the trend.

    ON FAILURE: the code is wrong.
    """
    agged = _agged5()
    sparse = agged.columns[2]
    agged[sparse] = np.where(np.arange(agged.shape[0]) < 8, np.nan, agged[sparse])
    tf = TrendFit(agged, Gaussian, Line, y=("mu", "value"), yerr=("sigma", "value"))
    tf.make_fit()

    res = tf.bin_results
    assert res.index.equals(agged.columns)
    assert res.loc[sparse, ("status", "")] == "InsufficientDataError"
    assert np.isnan(res.loc[sparse, ("mu", "value")])
    assert not res.loc[sparse, ("in_trend", "")]
    ok = res.index != sparse
    assert (res.loc[ok, ("status", "")] == "ok").all()
    assert list(tf.bin_fits.index) == list(agged.columns)


def test_y_and_yerr_have_no_default():
    """The trend's y and yerr are the scientist's choice: both must be named.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="yerr"):
        TrendFit(_agged5(), Gaussian, Line, y=("mu", "value"))
    with pytest.raises(TypeError, match="'y'"):
        TrendFit(_agged5(), Gaussian, Line, yerr=("sigma", "value"))


def test_yerr_can_be_the_uncertainty_of_mu_or_none():
    """``yerr=("mu", "uncertainty")`` weights by psigma of mu; None leaves the trend unweighted.

    ON FAILURE: the code is wrong.
    """
    tf = TrendFit(
        _noisy_agged5(), Gaussian, Line, y=("mu", "value"), yerr=("mu", "uncertainty")
    )
    tf.make_fit()
    psigma = tf.bin_results.loc[:, ("mu", "uncertainty")]
    assert (psigma > 0).all()  # the noise exists to make these nonzero
    np.testing.assert_array_equal(tf.trend.observations.raw.w, psigma)

    unweighted = TrendFit(_agged5(), Gaussian, Line, y=("mu", "value"), yerr=None)
    unweighted.make_fit()
    assert unweighted.trend.observations.raw.w is None


def test_an_unknown_key_raises_naming_the_available_ones():
    """A y or yerr that is not a results column raises KeyError listing the choices.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(KeyError, match=r"\('sigma', 'value'\)"):
        TrendFit(_agged5(), Gaussian, Line, y=("width", "value"), yerr=None)
    with pytest.raises(KeyError, match="psigma"):
        TrendFit(_agged5(), Gaussian, Line, y=("mu", "value"), yerr=("mu", "psigma"))


def test_two_setups_compare_by_concatenating_their_trend_results():
    """yerr = sigma and yerr = psigma of mu give two trend rows in one frame.

    ON FAILURE: the code is wrong.
    """
    setup = dict(y=("mu", "value"), trend_kwargs={})
    width = TrendFit(_noisy_agged5(), Gaussian, Line, yerr=("sigma", "value"), **setup)
    width.make_fit()
    psigma = TrendFit(
        _noisy_agged5(), Gaussian, Line, yerr=("mu", "uncertainty"), **setup
    )
    psigma.make_fit()
    cmp = pd.concat(
        {"width": width.trend.results, "psigma": psigma.trend.results},
        names=["setup"],
    )
    assert list(cmp.index.get_level_values("setup")) == ["width", "psigma"]
    assert list(cmp.columns) == list(width.trend.results.columns)

    per_bin = pd.concat(
        {"width": width.bin_results, "psigma": psigma.bin_results}, axis=1
    )
    assert per_bin.index.equals(width.agged.columns)


def test_results_before_make_fit_raise_not_fitted():
    """``bin_results`` and ``trend`` do not exist before ``make_fit``.

    ON FAILURE: the code is wrong.
    """
    tf = TrendFit(_agged5(), Gaussian, Line, y=("mu", "value"), yerr=None)
    with pytest.raises(NotFittedError, match="make_fit"):
        tf.bin_results
    with pytest.raises(NotFittedError, match="make_fit"):
        tf.trend


def test_keywords_reach_each_level():
    """Construction keywords reach each level's fit function; fit keywords each fit.

    ``bin_kwargs`` limits each bin fit's x, ``trend_kwargs`` the trend's x,
    and ``max_nfev=1`` in ``bin_fit_kwargs`` stops every bin fit, which
    leaves the trend no data.

    ON FAILURE: the code is wrong.
    """
    tf = TrendFit(
        _agged5(),
        Gaussian,
        Line,
        y=("mu", "value"),
        yerr=None,
        bin_kwargs={"xmax": 7.0},
        trend_kwargs={"xmax": 2.0},
    )
    # The trend's two used bins leave its covariance not finite.
    with pytest.warns(FitDegeneracyWarning, match="m and b have a non-finite"):
        tf.make_fit()
    for fit in tf.bin_fits:
        assert fit.observations.used.x.max() == 6.5  # the last center <= 7
    assert tf.trend.observations.used.x.max() == 1.5  # the last center <= 2

    stopped = TrendFit(_agged5(), Gaussian, Line, y=("mu", "value"), yerr=None)
    with pytest.raises(InsufficientDataError):
        stopped.make_fit(bin_fit_kwargs={"max_nfev": 1})
    assert (stopped.bin_results.loc[:, ("status", "")] == "FitFailedError").all()
    assert stopped.trend.results.loc[:, ("status", "")].item() == (
        "InsufficientDataError"
    )


def test_logx_fits_the_trend_against_ten_to_the_center():
    """Under ``logx`` the trend's x is 10**center.

    ON FAILURE: the code is wrong.
    """
    tf = _trend5(logx=True)
    centers = tf.agged.columns.mid.to_numpy()
    np.testing.assert_array_equal(tf.trend.observations.raw.x, 10.0**centers)


def test_the_per_bin_spellings_are_gone():
    """One per-bin table replaces popt_1d, psigma_1d, popt1d_keys and the rest.

    ON FAILURE: the code is wrong.
    """
    gone = {
        "popt_1d",
        "psigma_1d",
        "popt1d_keys",
        "ffuncs",
        "bad_fits",
        "trend_func",
        "ffunc1d_class",
        "trendfunc_class",
        "make_ffunc1ds",
        "make_1dfits",
        "make_trend_func",
        "trend_logx",
    }
    assert not gone & set(dir(TrendFit))
    assert "Popt1DKeys" not in trend_fits.__all__
