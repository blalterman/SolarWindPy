import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.container import ErrorbarContainer
from scipy.optimize import OptimizeWarning

from solarwindpy.fitfunctions import gaussians, trend_fits, lines
from solarwindpy.fitfunctions.core import InsufficientDataError
from solarwindpy.fitfunctions.plots import AxesLabels
from solarwindpy.plotting.labels.base import TeXlabel
from tests.tolerances import exact, noise_free


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
    """Properties return the inputs; a non-FitFunction class raises TypeError.

    ON FAILURE: the code is wrong.
    """
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
    """Each column gets a Gaussian; good fits stay and fill popt and psigma.

    ON FAILURE: the code is wrong.
    """
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
    """The trend function is the trend class; no 1D fits raises ValueError.

    ON FAILURE: the code is wrong.
    """
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
    # y - w and y + w, recomputed.
    assert segments[:, 0, 1] == exact(y - width, nan_ok=True)
    assert segments[:, 1, 1] == exact(y + width, nan_ok=True)

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
    """Setters store their values; shared labels move the trend's y and z to the 1D fits.

    ON FAILURE: the code is wrong.
    """
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
    """``set_agged`` refuses anything but a DataFrame.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(AssertionError):
        trend_fit.set_agged(42)


def test_labels_instance_and_update(trend_fit):
    """The trend plotter holds AxesLabels, which ``set_shared_labels`` replaces.

    ON FAILURE: the code is wrong.
    """
    # Labels are stored in the trend_func's plotter, not in TrendFit itself
    assert isinstance(trend_fit.trend_func.plotter.labels, AxesLabels)
    trend_fit.set_shared_labels(x="time", y="density", z="counts")
    assert trend_fit.trend_func.plotter.labels == AxesLabels(
        "time", "density", "counts"
    )


# Five columns of noise-free Gaussian counts on x-bin centers 0.5 ... 9.5, so
# each 1D fit recovers its chosen centroid and width. With the trend limited to
# y <= 6.5 and w >= 1.05, column 0 (mu 5, sigma 1.0) is out by its width only,
# column 4 (mu 7, sigma 1.2) by its centroid only, and columns 1-3 are in.
MUS = [5.0, 4.0, 5.5, 6.0, 7.0]
SIGMAS = [1.0, 1.1, 1.3, 1.2, 1.2]
IN_TREND = [False, True, True, True, False]
TREND_LIMITS = {"ymax": 6.5, "wmin": 1.05}


def _agged5():
    xbins = pd.interval_range(0, 10, periods=10)
    x = xbins.mid.values
    columns = pd.interval_range(0, 5, periods=5)
    return pd.DataFrame(
        {
            col: 10.0 * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
            for col, mu, sigma in zip(columns, MUS, SIGMAS)
        },
        index=xbins,
    )


def _trend5(trend_logx=False, **trend_kwargs):
    tf = trend_fits.TrendFit(_agged5(), lines.Line, trend_logx=trend_logx)
    tf.make_ffunc1ds()
    tf.make_1dfits()
    tf.make_trend_func(**{**TREND_LIMITS, **trend_kwargs})
    tf.trend_func.make_fit()
    return tf


@pytest.fixture
def trend5():
    yield _trend5()
    plt.close("all")


def test_the_fixture_recovers_its_centroids_and_selects_the_in_trend_columns(trend5):
    """The 1D fits recover MUS and SIGMAS; the trend uses columns 1-3 only.

    ON FAILURE: the fixture no longer separates in-trend from out-of-trend
    columns by centroid and by width; fix the fixture.
    """
    assert trend5.popt_1d["mu"].to_numpy() == noise_free(MUS)
    assert trend5.popt_1d["sigma"].to_numpy() == noise_free(SIGMAS)
    centers = pd.IntervalIndex(trend5.popt_1d.index).mid.values
    np.testing.assert_array_equal(
        trend5.trend_func.observations.used.x, centers[IN_TREND]
    )


def test_plot_all_ffuncs_titles_tell_in_trend_bins_from_the_others(trend5):
    """Out-of-trend bins share a title ending that the in-fit bins do not.

    A bin is out by its centroid or by its width.

    ON FAILURE: the code is wrong.
    """
    trend5.set_shared_labels(x=TeXlabel(("n", "", "p1")))
    axes = trend5.plot_all_ffuncs()
    last = [
        axes.loc[k, "hax"].get_legend().get_title().get_text().split("\n")[-1]
        for k in trend5.ffuncs.index
    ]
    in_fit = {t for t, keep in zip(last, IN_TREND) if keep}
    out = {t for t, keep in zip(last, IN_TREND) if not keep}
    assert len(in_fit) == 1 and len(out) == 1 and in_fit != out, last


def test_plot_all_popt_1d_draws_every_centroid_unless_limited_to_the_trend(trend5):
    """By default every 1D centroid is drawn; with the option, only the trend's.

    ON FAILURE: the code is wrong.
    """
    centers = pd.IntervalIndex(trend5.popt_1d.index).mid.values
    fig, ax = plt.subplots()
    line, _ = trend5.plot_all_popt_1d(ax)
    np.testing.assert_array_equal(line[0].get_xdata(), centers)

    fig, ax = plt.subplots()
    line, _ = trend5.plot_all_popt_1d(ax, only_plot_data_in_trend_fit=True)
    np.testing.assert_array_equal(line[0].get_xdata(), centers[IN_TREND])


def _window_y_span(window):
    """Lowest and highest y of the window polygon at each x it covers."""
    vertices = window.get_paths()[0].vertices
    span = {}
    for x, y in vertices:
        lo, hi = span.get(x, (np.inf, -np.inf))
        span[x] = (min(lo, y), max(hi, y))
    return span


def test_plot_all_popt_1d_window_defaults(trend5):
    """The window spans centroid +- width, in the line's colour at alpha 0.15.

    The author decided plot-styling defaults are pinned by tests: cyan for
    the line, its colour and 0.15 for the window, matplotlib's own line style.

    ON FAILURE: the code is wrong, unless the author changed a default.
    """
    fig, ax = plt.subplots()
    (line,), window = trend5.plot_all_popt_1d(ax)
    assert line.get_color() == "cyan"
    assert line.get_linestyle() == "-"
    assert line.get_label() == "1D Fits"
    assert window.get_facecolor()[0][:3] == exact(to_rgba("cyan")[:3])
    assert window.get_alpha() == 0.15

    centers = pd.IntervalIndex(trend5.popt_1d.index).mid.values
    y = trend5.popt_1d["mu"].to_numpy()
    w = trend5.popt_1d["sigma"].to_numpy()
    span = _window_y_span(window)
    for xi, yi, wi in zip(centers, y, w):
        assert span[xi] == exact((yi - wi, yi + wi))


def test_plot_all_popt_1d_window_options_reach_their_artists(trend5):
    """``ls``, line keywords and ``window_kwargs`` each reach their artist.

    ``ls`` is normalised to ``linestyle`` before it is read (the old code
    looked for ``ls`` after normalising and passed both to matplotlib).

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    (line,), window = trend5.plot_all_popt_1d(
        ax,
        ls=":",
        lw=3,
        color="magenta",
        window_kwargs=dict(color="red", alpha=0.4, hatch="//"),
    )
    assert line.get_linestyle() == ":"
    assert line.get_linewidth() == 3
    assert line.get_color() == "magenta"
    assert window.get_facecolor()[0][:3] == exact(to_rgba("red")[:3])
    assert window.get_alpha() == 0.4
    assert window.get_hatch() == "//"


def test_plot_all_popt_1d_errorbar_linestyle(trend5):
    """Without a window the centroids are dashed by default; ``ls`` replaces it.

    The data line and the error bars both take the style, and other line
    keywords reach the errorbar.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    data_line, _, (bars,) = trend5.plot_all_popt_1d(ax, plot_window=False)
    assert data_line.get_linestyle() == "--"

    fig, ax = plt.subplots()
    data_line, _, (bars,) = trend5.plot_all_popt_1d(ax, plot_window=False, ls=":", lw=3)
    assert data_line.get_linestyle() == ":"
    assert data_line.get_linewidth() == 3
    dotted = LineCollection([], linestyles=":", linewidths=bars.get_linewidths())
    assert bars.get_linestyle() == dotted.get_linestyle()


def test_trend_logx_fits_and_plots_against_ten_to_the_x(trend5):
    """Under ``trend_logx`` the trend's x is 10**center, on log x-axes.

    The author decided ``FitFunction.logx`` goes and TrendFit sets the
    plotter's log x itself. Without the option the axes stay linear.

    ON FAILURE: the code is wrong.
    """
    tf = _trend5(trend_logx=True)
    centers = pd.IntervalIndex(tf.popt_1d.index).mid.values
    np.testing.assert_array_equal(tf.trend_func.observations.raw.x, 10.0**centers)

    fig, ax = plt.subplots()
    line, _ = tf.plot_all_popt_1d(ax)
    np.testing.assert_array_equal(line[0].get_xdata(), 10.0**centers)

    hax, rax = tf.plot_trend_fit_resid()
    assert hax.get_xscale() == rax.get_xscale() == "log"
    assert tf.trend_func.plotter.log.x is True
    assert tf.plot_1d_popt_and_trend().get_xscale() == "log"

    hax, rax = trend5.plot_trend_fit_resid()
    assert hax.get_xscale() == rax.get_xscale() == "linear"
    assert trend5.trend_func.plotter.log.x is False


def test_plot_trend_fit_resid_defaults(trend5):
    """The annotation sits at (0.5, 0.1) bottom-aligned; used points are black.

    The author decided plot-styling defaults are pinned by tests; these are
    the defaults ``plot_trend_fit_resid`` documents, with matplotlib's
    ``"default"`` drawstyle for the observations.

    ON FAILURE: the code is wrong, unless the author changed a default.
    """
    hax, _ = trend5.plot_trend_fit_resid()
    (text,) = hax.texts
    assert text.get_position() == (0.5, 0.1)
    assert text.get_verticalalignment() == "bottom"
    drawn = {ln.get_label(): ln for ln in hax.get_lines()}
    assert drawn[r"$\mathrm{Used}$"].get_color() == "k"
    assert drawn[r"$\mathrm{Obs}$"].get_drawstyle() == "default"
    assert drawn[r"$\mathrm{Used}$"].get_drawstyle() == "default"


def test_plot_trend_fit_resid_options_and_unknown_keywords(trend5):
    """Each option replaces its default; an unknown keyword raises TypeError.

    ON FAILURE: the code is wrong.
    """
    hax, _ = trend5.plot_trend_fit_resid(
        annotate_kwargs=dict(xloc=0.2, yloc=0.7),
        used_kwargs=dict(color="red"),
        drawstyle="steps-mid",
    )
    (text,) = hax.texts
    assert text.get_position() == (0.2, 0.7)
    drawn = {ln.get_label(): ln for ln in hax.get_lines()}
    assert drawn[r"$\mathrm{Used}$"].get_color() == "red"
    assert drawn[r"$\mathrm{Obs}$"].get_drawstyle() == "steps-mid"

    with pytest.raises(TypeError, match="colour"):
        trend5.plot_trend_fit_resid(colour="red")


def test_plot_trend_and_resid_on_ffuncs_passes_options_and_places_the_legend(trend5):
    """Both keyword sets reach their plots; the legend is at the top, alpha 0.5.

    ON FAILURE: the code is wrong, unless the author changed the legend style.
    """
    hax, _ = trend5.plot_trend_and_resid_on_ffuncs(
        trend_kwargs=dict(drawstyle="steps-mid"),
        fit1d_kwargs=dict(color="magenta"),
    )
    drawn = {ln.get_label(): ln for ln in hax.get_lines()}
    assert drawn[r"$\mathrm{Obs}$"].get_drawstyle() == "steps-mid"
    assert drawn["1D Fits"].get_color() == "magenta"

    legend = hax.get_legend()
    assert legend.get_frame().get_alpha() == 0.5
    hax.figure.canvas.draw()
    box = legend.get_window_extent()
    axes_box = hax.get_window_extent()
    # Upper: nearer the axes' top edge than their bottom. The four-column
    # legend spans nearly the axes' width, so left and right do not separate.
    assert axes_box.y1 - box.y1 < box.y0 - axes_box.y0


def test_plot_1d_popt_and_trend_defaults_and_options(trend5):
    """The trend line is limegreen by default; every keyword set reaches its plot.

    ON FAILURE: the code is wrong, unless the author changed the default colour.
    """
    ax = trend5.plot_1d_popt_and_trend()
    drawn = {ln.get_label(): ln for ln in ax.get_lines()}
    assert drawn[r"$\mathrm{Fit}$"].get_color() == "limegreen"

    ax = trend5.plot_1d_popt_and_trend(
        kwargs_popt_1d=dict(color="magenta"),
        annotate_kwargs=dict(xloc=0.3, yloc=0.4),
        fit_kwargs=dict(color="red"),
        drawstyle="steps-mid",
    )
    drawn = {ln.get_label(): ln for ln in ax.get_lines()}
    assert drawn["1D Fits"].get_color() == "magenta"
    assert drawn[r"$\mathrm{Fit}$"].get_color() == "red"
    assert drawn[r"$\mathrm{Obs}$"].get_drawstyle() == "steps-mid"
    (text,) = ax.texts
    assert text.get_position() == (0.3, 0.4)


def test_keywords_reach_the_1d_and_trend_fit_functions():
    """Keywords given to each step reach the fit functions it builds or runs.

    ``ffunc1d`` picks the 1D class; ``xmax`` limits each 1D fit's and the
    trend's used x; ``max_nfev=1`` stops every 1D fit, moving all to
    ``bad_fits``; ``return_exception=False`` raises instead.

    ON FAILURE: the code is wrong.
    """
    tf = trend_fits.TrendFit(
        _agged5(), lines.Line, ffunc1d=gaussians.GaussianNormalized
    )
    assert tf.ffunc1d_class is gaussians.GaussianNormalized
    tf.make_ffunc1ds(xmax=7.0)
    for ff in tf.ffuncs:
        assert isinstance(ff, gaussians.GaussianNormalized)
        assert ff.observations.used.x.max() == 6.5

    tf.make_1dfits()
    tf.make_trend_func(xmax=2.0)
    assert tf.trend_func.observations.used.x.max() == 1.5

    stopped = trend_fits.TrendFit(_agged5(), lines.Line)
    stopped.make_ffunc1ds()
    stopped.make_1dfits(max_nfev=1)
    assert stopped.ffuncs.empty and len(stopped.bad_fits) == 5

    raising = trend_fits.TrendFit(_agged5(), lines.Line)
    raising.make_ffunc1ds(xmax=1.0)  # one point per column: too few
    with pytest.raises(InsufficientDataError):
        raising.make_1dfits(return_exception=False)
