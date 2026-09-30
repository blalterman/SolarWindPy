import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import LineCollection
from matplotlib.container import ErrorbarContainer
from scipy.optimize import OptimizeWarning

from solarwindpy.fitfunctions import gaussians, trend_fits, lines
from solarwindpy.fitfunctions.core import InsufficientDataError
from solarwindpy.fitfunctions.plots import AxesLabels
from solarwindpy.plotting.labels import TeXlabel


@pytest.fixture
def agged():
    xbins = pd.interval_range(0, 5, periods=5)
    ybins = pd.interval_range(0, 2, periods=2)
    data = {
        ybins[0]: np.array([1, 2, 3, 4, 5]),
        ybins[1]: np.array([2, 3, 4, 5, 6]),
    }
    return pd.DataFrame(data, index=xbins)


@pytest.fixture
def agged_empty():
    xbins = pd.interval_range(0, 5, periods=5)
    return pd.DataFrame({}, index=xbins)


@pytest.fixture
def trend_fit(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    tf.make_1dfits()
    tf.make_trend_func()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=OptimizeWarning)
        tf.trend_func.make_fit()
    return tf


def test_type_enforcement_and_properties(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    assert tf.agged.equals(agged)
    assert tf.ffunc1d_class is gaussians.Gaussian
    assert tf.trendfunc_class is lines.Line
    assert str(tf) == "TrendFit"
    with pytest.raises(TypeError):
        trend_fits.TrendFit(agged, int)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(int, lines.Line)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(gaussians.Gaussian, int)


def test_make_ffunc1ds_make_1dfits(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    assert isinstance(tf.ffuncs.iloc[0], gaussians.Gaussian)
    tf.make_1dfits()
    assert tf.bad_fits.empty
    assert not tf.popt_1d.empty
    assert not tf.psigma_1d.empty


class FailedFitKeptInFfuncs(AssertionError):
    """make_1dfits left a failed 1D fit in ffuncs instead of bad_fits."""


def test_make_1dfits_moves_bad_fit():
    """A column with fewer points than Gaussian parameters moves to bad_fits.

    Three NaNs leave two finite points for a three-parameter Gaussian, so the
    real make_fit returns InsufficientDataError for that column only.

    ON FAILURE: the code is wrong.
    """
    xbins = pd.interval_range(0, 5, periods=5)
    ybins = pd.interval_range(0, 2, periods=2)
    data = {
        ybins[0]: np.array([1, 2, 3, 4, 5]),
        ybins[1]: np.array([np.nan, np.nan, np.nan, 5, 6]),
    }
    agged = pd.DataFrame(data, index=xbins)
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    tf.make_1dfits()

    if ybins[1] in tf.ffuncs.index:
        raise FailedFitKeptInFfuncs(repr(ybins[1]))
    assert list(tf.bad_fits.index) == [ybins[1]]
    assert list(tf.ffuncs.index) == [ybins[0]]
    bad = tf.bad_fits.loc[ybins[1]]
    assert isinstance(bad.make_fit(return_exception=True), InsufficientDataError)


def test_make_trend_func_success_and_failure(trend_fit, agged_empty):
    assert isinstance(trend_fit.trend_func, lines.Line)
    tf = trend_fits.TrendFit(agged_empty, lines.Line)
    tf.make_ffunc1ds()
    with pytest.raises(ValueError):
        tf.make_trend_func()


def _lines_by_label(ax):
    """Map each Line2D label on ``ax`` to its ``(x, y)`` data."""
    return {ln.get_label(): (ln.get_xdata(), ln.get_ydata()) for ln in ax.get_lines()}


def _popt_1d_xy(tf):
    """Bin centers and 1D-fit centroids, derived from ``popt_1d`` directly."""
    ykey, _ = tf.popt1d_keys
    return pd.IntervalIndex(tf.popt_1d.index).mid.values, tf.popt_1d[ykey].values


def test_plot_trend_fit_resid_draws_the_1d_centroids(trend_fit):
    """The trend plot's observations are the 1D-fit centroids at bin centers.

    ON FAILURE: the code is wrong.
    """
    hax, rax = trend_fit.plot_trend_fit_resid()
    assert isinstance(hax, plt.Axes) and isinstance(rax, plt.Axes)
    assert hax.figure is rax.figure

    x, y = _popt_1d_xy(trend_fit)
    obs_x, obs_y = _lines_by_label(hax)[r"$\mathrm{Obs}$"]
    np.testing.assert_array_equal(obs_x, x)
    np.testing.assert_array_equal(obs_y, y)
    fit_x, fit_y = _lines_by_label(hax)[r"$\mathrm{Fit}$"]
    np.testing.assert_array_equal(fit_y, trend_fit.trend_func(fit_x))
    assert len(rax.get_lines()) > 0


def test_plot_trend_and_resid_on_ffuncs_overlays_1d_fits(trend_fit):
    """The overlay adds the 1D-fit centroids to the trend axes.

    ON FAILURE: the code is wrong.
    """
    hax, rax = trend_fit.plot_trend_and_resid_on_ffuncs()
    assert hax.figure is rax.figure

    x, y = _popt_1d_xy(trend_fit)
    fits_x, fits_y = _lines_by_label(hax)["1D Fits"]
    np.testing.assert_array_equal(fits_x, x)
    np.testing.assert_array_equal(fits_y, y)
    assert r"$\mathrm{Fit}$" in _lines_by_label(hax)


def test_plot_1d_popt_and_trend_on_new_axes(trend_fit):
    """Without ``ax``, the 1D fits and trend fit share one new axes.

    ON FAILURE: the code is wrong.
    """
    ax = trend_fit.plot_1d_popt_and_trend()
    assert isinstance(ax, plt.Axes)
    drawn = _lines_by_label(ax)

    x, y = _popt_1d_xy(trend_fit)
    np.testing.assert_array_equal(drawn["1D Fits"][0], x)
    np.testing.assert_array_equal(drawn["1D Fits"][1], y)
    fit_x, fit_y = drawn[r"$\mathrm{Fit}$"]
    np.testing.assert_array_equal(fit_y, trend_fit.trend_func(fit_x))


def test_plot_all_popt_1d_returns_errorbar_artists(agged):
    """Without a window, plot_all_popt_1d draws centroid +/- width errorbars.

    Points sit at bin centers with the 1D centroid as y; each bar spans
    centroid - width to centroid + width; the caller's color and label hold,
    and the bars take the default dashed style.

    ON FAILURE: the code is wrong.
    """
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    tf.make_1dfits()
    tf.make_trend_func()

    fig, ax = plt.subplots()
    plotted = tf.plot_all_popt_1d(
        ax, color="magenta", label="1D Fits", plot_window=False
    )
    assert isinstance(plotted, ErrorbarContainer)
    data_line, _, (bars,) = plotted

    x, y = _popt_1d_xy(tf)
    _, wkey = tf.popt1d_keys
    width = tf.popt_1d[wkey].values
    np.testing.assert_array_equal(data_line.get_xdata(), x)
    np.testing.assert_array_equal(np.asarray(data_line.get_ydata(), float), y)
    assert data_line.get_color() == "magenta"
    assert plotted.get_label() == "1D Fits"

    segments = np.array(bars.get_segments())
    np.testing.assert_array_equal(segments[:, 0, 0], x)
    # rel=1e-12: y - w and y + w recomputed by the same float operations.
    np.testing.assert_allclose(segments[:, 0, 1], y - width, rtol=1e-12, atol=0)
    np.testing.assert_allclose(segments[:, 1, 1], y + width, rtol=1e-12, atol=0)

    dashed = LineCollection([], linestyles="--", linewidths=bars.get_linewidths())
    assert bars.get_linestyle() == dashed.get_linestyle()


def test_plot_all_ffuncs(trend_fit):
    """One (hax, rax) row per 1D fit, each drawing that fit's own slice.

    The legend title carries the bin center and, because the trend fit here
    uses every 1D fit, the in-fit marker for each.

    ON FAILURE: the code is wrong.
    """
    xlabel = TeXlabel(("n", "", "p1"))
    trend_fit.set_shared_labels(x=xlabel)
    axes = trend_fit.plot_all_ffuncs(legend_title_fmt="%.1f")

    assert list(axes.index) == list(trend_fit.ffuncs.index)
    xmid = pd.IntervalIndex(trend_fit.agged.index).mid.values
    for key in trend_fit.ffuncs.index:
        hax, rax = axes.loc[key, "hax"], axes.loc[key, "rax"]
        assert hax.figure is rax.figure
        obs_x, obs_y = _lines_by_label(hax)[r"$\mathrm{Obs}$"]
        np.testing.assert_array_equal(obs_x, xmid)
        np.testing.assert_array_equal(obs_y, trend_fit.agged[key].values)

        title = hax.get_legend().get_title().get_text()
        assert xlabel.tex in title and xlabel.units in title
        assert f"{key.mid:.1f}" in title
        assert title.endswith("\nIn Fit")
    figures = {id(axes.loc[k, "hax"].figure) for k in axes.index}
    assert len(figures) == len(axes.index)


def test_set_agged_set_fitfunctions_set_shared_labels(trend_fit, agged):
    new_agged = agged * 2
    trend_fit.set_agged(new_agged)
    assert trend_fit.agged.equals(new_agged)
    trend_fit.set_fitfunctions(gaussians.GaussianNormalized, lines.Line)
    assert trend_fit.ffunc1d_class is gaussians.GaussianNormalized
    trend_fit.set_fitfunctions(gaussians.Gaussian, lines.Line)
    trend_fit.set_shared_labels(x="time", y="density", z="counts")
    assert trend_fit.trend_func.plotter.labels.x == "time"
    first_ff = trend_fit.ffuncs.iloc[0]
    assert first_ff.plotter.labels.x == "density"
    assert first_ff.plotter.labels.y == "counts"


def test_set_agged_rejects_non_dataframe(trend_fit):
    with pytest.raises(AssertionError):
        trend_fit.set_agged(42)


def test_labels_instance_and_update(trend_fit):
    # Labels are stored in the trend_func's plotter, not in TrendFit itself
    assert isinstance(trend_fit.trend_func.plotter.labels, AxesLabels)
    trend_fit.set_shared_labels(x="time", y="density", z="counts")
    assert trend_fit.trend_func.plotter.labels == AxesLabels(
        "time", "density", "counts"
    )
