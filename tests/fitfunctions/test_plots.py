"""Tests for :class:`solarwindpy.fitfunctions.plots.FFPlot`.

The fixture is a ``Line`` fitted to ``y = 2x + 1`` at x = 0..5 with unit
weights and ``1 <= x <= 3``, so the used observations are x = 1, 2, 3 and the
raw ones extend past them on both sides. The plotter is given a hand-chosen
model ``Y_FIT`` and residual vector ``FUN`` so every residual is known.
"""

import io
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.colors import to_rgba
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions import plots
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.fitfunctions.plots import FFPlot, AxesLabels, LogAxes
from solarwindpy.fitfunctions.tex_info import TeXinfo
from tests.tolerances import exact

#: Model at raw x = 0..5. At the used x = 1, 2, 3 the observations are
#: y = 3, 5, 7, so the simple residuals (model - observation) are 1, -1, 7
#: and the percent residuals 100 * (1/4, -1/4, 7/14) = 25, -25, 50.
Y_FIT = np.array([1.0, 4.0, 4.0, 14.0, 9.0, 11.0])
SIMPLE = np.array([1.0, -1.0, 7.0])
SIMPLE_PCT = np.array([25.0, -25.0, 50.0])
#: Chosen robust residual vector, in units of the (unit) uncertainty.
FUN = np.array([0.25, -0.5, 1.0])

#: The styles each plot draws by default (batch A: plot-styling defaults are
#: pinned by tests).
PINNED_STYLES = {
    "raw": {"color": "k", "label": r"$\mathrm{Obs}$"},
    "used": {
        "color": "forestgreen",
        "marker": "P",
        "markerfacecolor": "none",
        "markersize": 8,
        "label": r"$\mathrm{Used}$",
    },
    "fit": {
        "color": "darkorange",
        "linestyle": (0, (7, 3, 1, 3, 1, 3, 1, 3)),
        "label": r"$\mathrm{Fit}$",
    },
    "simple_residuals": {
        "color": "forestgreen",
        "marker": "P",
        "linestyle": "-",
        "drawstyle": "steps-mid",
        "markerfacecolor": "none",
        "markersize": 8,
    },
    "robust_residuals": {
        "color": "darkorange",
        "marker": "X",
        "linestyle": "-",
        "drawstyle": "steps-mid",
        "markerfacecolor": "none",
        "markersize": 8,
    },
}


def _fit(n=6, xmin=1, xmax=3, weights=True):
    x = np.arange(float(n))
    w = np.ones_like(x) if weights else None
    fit = Line(x, 2.0 * x + 1.0, weights=w, xmin=xmin, xmax=xmax)
    fit.make_fit()
    return fit


def make_texinfo(m=2.0):
    """Real TeXinfo for the line the fixture plots."""
    return TeXinfo(
        {"m": m, "b": 1.0}, {"m": 0.1, "b": 0.1}, "m x + b", _fit().chisq_dof, 1.0
    )


def make_ffplot(y_fit=Y_FIT, fun=FUN, weights=True):
    """FFPlot of the fixture fit with model ``y_fit`` and residuals ``fun``."""
    obs = _fit(weights=weights).observations
    tex = make_texinfo()
    plot = FFPlot(obs, y_fit, tex, OptimizeResult(fun=fun), fitfunction_name="dummy")
    return plot, tex, obs


def make_ffplot_of_size(n):
    """FFPlot of an exact line on x = 0..n-1 using its lower half."""
    fit = _fit(n=n, xmin=None, xmax=(n - 1) // 2)
    obs = fit.observations
    return FFPlot(obs, obs.raw.y, make_texinfo(), OptimizeResult(fun=None))


def annotations(ax, tex):
    """Texts on ``ax`` whose content is the TeXinfo annotation."""
    return [t for t in ax.texts if t.get_text() == str(tex)]


def line_labelled(ax, label):
    (line,) = [ln for ln in ax.get_lines() if ln.get_label() == label]
    return line


def render(fig):
    """RGBA pixels of ``fig`` drawn by the Agg renderer."""
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    return np.asarray(canvas.buffer_rgba()).copy()


def grid_is_on(ax):
    lines = ax.get_xgridlines() + ax.get_ygridlines()
    return bool(lines) and all(gl.get_visible() for gl in lines)


class Label:
    """Label with a ``path``, as ``solarwindpy.plotting.labels`` provide."""

    def __init__(self, label, path):
        self.label = label
        self.path = path

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# Construction, setters, and path
# ---------------------------------------------------------------------------


def test_str_is_the_class_name():
    """``str(FFPlot)`` is ``"FFPlot"``.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    assert str(plot) == "FFPlot"


def test_properties_return_what_was_set():
    """Construction and every setter are read back through the properties.

    ON FAILURE: the code is wrong.
    """
    plot, tex, obs = make_ffplot()
    assert plot.observations is obs
    np.testing.assert_array_equal(plot.y_fit, Y_FIT)
    assert plot.TeX_info is tex
    assert plot.fitfunction_name == "dummy"
    assert plot.labels == AxesLabels("x", "y")
    assert plot.log == LogAxes(False, False)

    plot.set_fitfunction_name("new")
    assert plot.fitfunction_name == "new"
    res = OptimizeResult(x=np.array([1.0]))
    plot.set_fit_result(res)
    assert plot.fit_result is res
    tex2 = make_texinfo(m=3.0)
    plot.set_TeX_info(tex2)
    assert plot.TeX_info is tex2

    obs2 = _fit(n=8).observations
    plot.set_observations(obs2, obs2.raw.y)
    assert plot.observations is obs2
    np.testing.assert_array_equal(plot.y_fit, obs2.raw.y)


@pytest.mark.parametrize("extra", [1, -1])
def test_set_observations_refuses_a_y_fit_of_another_length(extra):
    """A model longer or shorter than the raw observations is refused.

    ON FAILURE: the code is wrong.
    """
    plot, _, obs = make_ffplot()
    with pytest.raises(AssertionError):
        plot.set_observations(obs, np.ones(obs.raw.x.size + extra))


@pytest.mark.parametrize(
    "labels, log, expected",
    [
        ({}, {}, Path("FFPlot/dummy/x/y/linX_linY")),
        ({}, {"y": True}, Path("FFPlot/dummy/x/y/linX_logY")),
        ({}, {"x": True}, Path("FFPlot/dummy/x/y/logX_linY")),
        (
            {"x": Label("X", "xp"), "y": Label("Y", "yp"), "z": "Z"},
            {"x": True, "y": True},
            Path("FFPlot/dummy/xp/yp/Z/logX_logY"),
        ),
        (
            {"x": Label("X", "xp"), "y": Label("Y", "yp"), "z": Label("Z", "zp")},
            {},
            Path("FFPlot/dummy/xp/yp/zp/linX_linY"),
        ),
    ],
)
def test_path_names_the_labels_and_axis_scales(labels, log, expected):
    """``path`` joins class, fit name, label paths, and ``{lin,log}{X,Y}``.

    A label with a ``path`` contributes it; any other label its ``str``.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    plot.set_labels(**labels)
    plot.set_log(**log)
    assert plot.path == expected


def test_set_labels_keeps_the_labels_it_is_not_given():
    """``set_labels`` changes only the labels it is passed.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    plot.set_labels(y="Y", z="Z")
    plot.set_labels(x="X")
    assert plot.labels == AxesLabels("X", "Y", "Z")


def test_set_labels_refuses_an_unknown_label_naming_it():
    """An unknown label raises KeyError naming each unexpected keyword.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    with pytest.raises(KeyError, match=r"Unexpected kwarg[\s\S]*q: 1[\s\S]*r: 2"):
        plot.set_labels(q=1, r=2)


def test_set_log_changes_only_the_axes_it_is_given():
    """``set_log(x=True)`` leaves ``y`` as it was.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    plot.set_log(y=True)
    plot.set_log(x=True)
    assert plot.log == LogAxes(True, True)


# ---------------------------------------------------------------------------
# Default styles
# ---------------------------------------------------------------------------


def _draw(plot, kind, ax, **kwargs):
    if kind == "raw":
        plot.plot_raw(ax, plot_window=False, **kwargs)
    elif kind == "used":
        plot.plot_used(ax, plot_window=False, **kwargs)
    elif kind == "fit":
        plot.plot_fit(ax, annotate=False, **kwargs)
    else:
        plot.plot_residuals(ax, pct=False, kind=kind.split("_")[0], **kwargs)


@pytest.mark.parametrize("kind", sorted(PINNED_STYLES))
def test_each_plot_draws_its_pinned_default_style(kind):
    """Each default style is the pinned one.

    A plot drawn with no style keywords is pixel-identical to one given
    the pinned style explicitly.

    ON FAILURE: the code is wrong, unless the author changed the default style.
    """
    plot, *_ = make_ffplot()
    fig1, ax1 = plt.subplots()
    _draw(plot, kind, ax1)
    fig2, ax2 = plt.subplots()
    _draw(plot, kind, ax2, **PINNED_STYLES[kind])
    np.testing.assert_array_equal(render(fig1), render(fig2))


@pytest.mark.parametrize("kind", ["raw", "used", "fit"])
def test_each_plot_draws_its_pinned_default_label(kind):
    """Observation and fit lines carry the pinned legend labels.

    ON FAILURE: the code is wrong, unless the author changed the default style.
    """
    plot, *_ = make_ffplot()
    fig, ax = plt.subplots()
    _draw(plot, kind, ax)
    assert ax.get_legend_handles_labels()[1] == [PINNED_STYLES[kind]["label"]]


def test_default_style_table_is_the_single_source_of_plot_styles():
    """``_DEFAULT_STYLES`` holds exactly the pinned styles the plots draw.

    Together with ``test_each_plot_draws_its_pinned_default_style`` this
    keeps the table and the drawn plots from drifting apart.

    ON FAILURE: the code is wrong.
    """
    assert plots._DEFAULT_STYLES == PINNED_STYLES


@pytest.mark.parametrize("kind", sorted(PINNED_STYLES))
def test_caller_keywords_override_the_default_style_by_alias(kind):
    """A Line2D alias (``c``, ``lw``) overrides the default; the rest stays.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    fig, ax = plt.subplots()
    _draw(plot, kind, ax, c="r", lw=5)
    line = ax.get_lines()[0]
    assert to_rgba(line.get_color()) == to_rgba("r")
    assert line.get_linewidth() == 5
    if "marker" in PINNED_STYLES[kind]:
        assert line.get_marker() == PINNED_STYLES[kind]["marker"]


# ---------------------------------------------------------------------------
# Observation plots
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kind", ["raw", "used"])
def test_observation_plots_draw_their_observations(kind):
    """``plot_raw`` draws every raw point; ``plot_used`` the used subset.

    ON FAILURE: the code is wrong.
    """
    plot, _, obs = make_ffplot()
    method = getattr(plot, f"plot_{kind}")
    ax, (line, *_) = method()
    expected = getattr(obs, kind)
    np.testing.assert_array_equal(line[0].get_xdata(), expected.x)
    np.testing.assert_array_equal(line[0].get_ydata(), expected.y)


@pytest.mark.parametrize("kind", ["raw", "used"])
def test_window_spans_y_minus_w_to_y_plus_w(kind):
    """The window fills ``y - w`` to ``y + w``.

    It is drawn in the line colour at alpha 0.15, and ``edge_kwargs`` draws those two bounds as lines.

    ON FAILURE: the code is wrong.
    """
    plot, _, obs = make_ffplot()
    o = getattr(plot.observations, kind)
    ax, (line, window, edges) = getattr(plot, f"plot_{kind}")(edge_kwargs={})
    vy = window.get_paths()[0].vertices[:, 1]
    assert vy.min() == o.y.min() - 1.0  # unit weights
    assert vy.max() == o.y.max() + 1.0
    assert window.get_alpha() == 0.15
    color = to_rgba(PINNED_STYLES[kind]["color"])
    assert tuple(window.get_facecolor()[0][:3]) == color[:3]
    (lo,), (hi,) = edges
    np.testing.assert_array_equal(lo.get_ydata(), o.y - 1.0)
    np.testing.assert_array_equal(hi.get_ydata(), o.y + 1.0)
    np.testing.assert_array_equal(lo.get_xdata(), o.x)
    assert to_rgba(lo.get_color()) == color


@pytest.mark.parametrize("kind", ["raw", "used"])
def test_window_and_edge_keywords_take_effect(kind):
    """``window_kwargs`` restyles the window; ``edge_kwargs`` the edges.

    ``edge_kwargs`` takes the window's own vocabulary (``ec``) as well as Line2D keywords.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    method = getattr(plot, f"plot_{kind}")
    _, (_, window, edges) = method(
        window_kwargs={"color": "b", "alpha": 0.5},
        edge_kwargs={"ec": "r", "ls": "--"},
    )
    assert window.get_alpha() == 0.5
    assert tuple(window.get_facecolor()[0][:3]) == to_rgba("b")[:3]
    for (edge,) in edges:
        assert to_rgba(edge.get_color()) == to_rgba("r")
        assert edge.get_linestyle() == "--"

    _, (_, _, edges) = method(window_kwargs={"color": "b"}, edge_kwargs={"lw": 4})
    for (edge,) in edges:
        assert to_rgba(edge.get_color()) == to_rgba("b")
        assert edge.get_linewidth() == 4


@pytest.mark.parametrize("kind", ["raw", "used"])
def test_without_weights_the_window_collapses_onto_the_line(kind, caplog):
    """No weights logs a warning and draws a zero-width window.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot(weights=False)
    o = getattr(plot.observations, kind)
    with caplog.at_level(logging.WARNING):
        _, (_, window, _) = getattr(plot, f"plot_{kind}")()
    assert "No weights" in caplog.text
    vy = window.get_paths()[0].vertices[:, 1]
    assert vy.min() == o.y.min()
    assert vy.max() == o.y.max()


@pytest.mark.parametrize("kind", ["raw", "used"])
def test_without_a_window_error_bars_span_the_weights(kind):
    """``plot_window=False`` draws error bars from ``y - w`` to ``y + w``.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    o = getattr(plot.observations, kind)
    _, container = getattr(plot, f"plot_{kind}")(plot_window=False, c="b")
    (bars,) = container.lines[2]
    segments = np.array(bars.get_segments())
    np.testing.assert_array_equal(segments[:, 0, 1], o.y - 1.0)
    np.testing.assert_array_equal(segments[:, 1, 1], o.y + 1.0)
    assert to_rgba(container.lines[0].get_color()) == to_rgba("b")


@pytest.mark.parametrize("n, expected", [(5, None), (1000, 10)])
def test_plot_used_marks_every_tenth_of_the_used_points_decade(n, expected):
    """``plot_used`` marks every 10**(floor(log10 N) - 1)-th of N used points.

    Hand-computed: N = 3 gives 10**-1, truncated to 0, so every point
    (``None``); N = 500 gives 10**1 = 10. An explicit ``markevery`` wins.

    ON FAILURE: the code is wrong.
    """
    plot = make_ffplot_of_size(n)
    fig, ax = plt.subplots()
    plot.plot_used(ax, plot_window=False)
    plot.plot_used(ax, plot_window=False, markevery=3)
    first, second = ax.get_lines()
    assert first.get_markevery() == expected
    assert second.get_markevery() == 3


def test_plot_axes_carry_labels_scales_and_grid():
    """Observation plots format their axes.

    They label both axes, apply ``set_log``, draw a major grid, and extend the x data limits to the raw range without touching y.

    ON FAILURE: the code is wrong.
    """
    plot, _, obs = make_ffplot()
    plot.set_labels(x="time", y="value")
    plot.set_log(y=True)
    fig, ax = plt.subplots()
    plot.plot_used(ax, plot_window=False)
    assert ax.get_xlabel() == "time"
    assert ax.get_ylabel() == "value"
    assert ax.get_xscale() == "linear"
    assert ax.get_yscale() == "log"
    assert grid_is_on(ax)
    assert tuple(ax.dataLim.intervalx) == (obs.raw.x[0], obs.raw.x[-1])
    assert ax.dataLim.intervaly[0] == obs.used.y.min() - 1.0

    plot.set_log(x=True, y=False)
    fig, ax = plt.subplots()
    plot.plot_raw(ax, plot_window=False)
    assert ax.get_xscale() == "log"
    assert ax.get_yscale() == "linear"


# ---------------------------------------------------------------------------
# Fit plots
# ---------------------------------------------------------------------------


def test_plot_fit_draws_the_model_and_annotates_on_request():
    """``plot_fit`` draws ``y_fit`` over the raw x and annotates it.

    The TeXinfo annotation goes where ``annotate_kwargs`` put it.

    ON FAILURE: the code is wrong.
    """
    plot, tex, obs = make_ffplot()
    ax = plot.plot_fit(annotate_kwargs={"xloc": 0.2, "yloc": 0.3})
    (line,) = ax.get_lines()
    np.testing.assert_array_equal(line.get_xdata(), obs.raw.x)
    np.testing.assert_array_equal(line.get_ydata(), Y_FIT)
    (text,) = annotations(ax, tex)
    assert text.get_position() == (0.2, 0.3)
    assert annotations(plot.plot_fit(annotate=False), tex) == []


def test_plot_raw_used_fit_draws_all_three_with_a_legend():
    """The combined plot draws raw, used and fit with a legend.

    The fit is at zorder 2.2, each observation line in ``steps-mid``, an annotation, and a frameless legend.

    ON FAILURE: the code is wrong.
    """
    plot, tex, _ = make_ffplot()
    ax = plot.plot_raw_used_fit()
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == [r"$\mathrm{Obs}$", r"$\mathrm{Used}$", r"$\mathrm{Fit}$"]
    assert ax.get_legend().get_frame().get_alpha() == 0
    assert line_labelled(ax, r"$\mathrm{Fit}$").get_zorder() == 2.2
    for label in (r"$\mathrm{Obs}$", r"$\mathrm{Used}$"):
        assert line_labelled(ax, label).get_drawstyle() == "steps-mid"
    assert len(annotations(ax, tex)) == 1


def test_plot_raw_used_fit_passes_each_keyword_set_to_its_plot():
    """Each keyword set reaches its own plot.

    ``drawstyle``, ``raw_kwargs``, ``used_kwargs``, ``fit_kwargs`` and
    ``annotate_kwargs`` each reach their own plot.

    ON FAILURE: the code is wrong.
    """
    plot, tex, _ = make_ffplot()
    ax = plot.plot_raw_used_fit(
        drawstyle="steps-post",
        raw_kwargs={"color": "r"},
        used_kwargs={"color": "b"},
        fit_kwargs={"color": "m"},
        annotate_kwargs={"xloc": 0.2},
    )
    raw = line_labelled(ax, r"$\mathrm{Obs}$")
    used = line_labelled(ax, r"$\mathrm{Used}$")
    fit = line_labelled(ax, r"$\mathrm{Fit}$")
    assert raw.get_drawstyle() == used.get_drawstyle() == "steps-post"
    assert to_rgba(raw.get_color()) == to_rgba("r")
    assert to_rgba(used.get_color()) == to_rgba("b")
    assert to_rgba(fit.get_color()) == to_rgba("m")
    (text,) = annotations(ax, tex)
    assert text.get_position()[0] == 0.2
    assert annotations(plot.plot_raw_used_fit(annotate=False), tex) == []


# ---------------------------------------------------------------------------
# Residuals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pct, expected", [(False, SIMPLE), (True, SIMPLE_PCT)])
def test_simple_residuals_are_model_minus_observation(pct, expected):
    """``residuals`` and ``plot_residuals`` give the hand-computed values.

    ON FAILURE: the code is wrong.
    """
    plot, _, obs = make_ffplot()
    assert plot.residuals(pct=pct) == exact(expected)
    ax = plot.plot_residuals(pct=pct)
    (line,) = ax.get_lines()
    np.testing.assert_array_equal(line.get_xdata(), obs.used.x)
    assert line.get_ydata() == exact(expected)


def test_percent_residuals_are_nan_where_the_model_is_zero():
    """Model 0, 4, 14 at y = 3, 5, 7 gives percent residuals NaN, -25, 50.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot(y_fit=np.array([1.0, 0.0, 4.0, 14.0, 9.0, 11.0]))
    assert plot.residuals(pct=True) == exact([np.nan, -25.0, 50.0], nan_ok=True)


def test_robust_residuals_are_the_fit_results_residual_vector():
    """``robust=True`` gives ``fit_result.fun``, and ``kind="robust"`` draws it.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    np.testing.assert_array_equal(plot.residuals(robust=True), FUN)
    ax = plot.plot_residuals(kind="robust", pct=False)
    (line,) = ax.get_lines()
    np.testing.assert_array_equal(line.get_ydata(), FUN)


@pytest.mark.parametrize("kind", ["robust", "both", "ROBUST"])
def test_robust_residuals_in_percent_are_refused(kind):
    """Robust residuals in percent are a ValueError.

    Robust residuals are in units of sigma; the error is raised before anything is drawn.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    with pytest.raises(ValueError, match="pct=False"):
        plot.residuals(pct=True, robust=True)
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="pct=False"):
        plot.plot_residuals(ax, pct=True, kind=kind)
    assert ax.get_lines() == []


def test_an_unknown_residual_kind_is_refused():
    """``kind`` outside simple/robust/both raises ValueError naming it.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    with pytest.raises(ValueError, match="'sideways'"):
        plot.plot_residuals(kind="sideways")


def test_both_draws_simple_then_robust_residuals():
    """``kind="both"`` draws the simple and the robust residuals.

    They are labelled Simple and Robust, each in its own default style.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    ax = plot.plot_residuals(kind="both", pct=False)
    simple, robust = ax.get_lines()
    assert simple.get_ydata() == exact(SIMPLE)
    np.testing.assert_array_equal(robust.get_ydata(), FUN)
    assert simple.get_label() == r"$\mathrm{ \; Simple}$"
    assert robust.get_label() == r"$\mathrm{ \; Robust}$"
    assert robust.get_marker() == "X"
    assert to_rgba(robust.get_color()) == to_rgba("darkorange")


@pytest.mark.parametrize("fit_result", [None, OptimizeResult()])
def test_both_skips_robust_residuals_when_the_fit_holds_none(fit_result):
    """Without a fit result or its ``fun``, ``both`` draws the simple line.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    plot.set_fit_result(fit_result)
    ax = plot.plot_residuals(kind="both", pct=False)
    (line,) = ax.get_lines()
    assert line.get_label() == r"$\mathrm{ \; Simple}$"


class _Unplottable:
    """A residual vector whose conversion to an array fails."""

    def __array__(self, *args, **kwargs):
        raise AttributeError("not the missing-result case")

    def __len__(self):
        return 3


def test_both_lets_other_attribute_errors_through():
    """Only a missing result is skipped.

    Any other AttributeError raised while drawing the robust residuals reaches the caller.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot(fun=_Unplottable())
    with pytest.raises(AttributeError, match="not the missing-result case"):
        plot.plot_residuals(kind="both", pct=False)


@pytest.mark.parametrize("label", ["Test", r"$\mathrm{Test}$", r"\alpha"])
def test_residual_labels_keep_the_callers_label_whole(label):
    """The caller's label prefixes Simple/Robust intact.

    It is the same for ``kind="simple"`` alone as for ``kind="both"``.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    (alone,) = plot.plot_residuals(kind="simple", label=label).get_lines()
    simple, robust = plot.plot_residuals(
        kind="both", pct=False, label=label
    ).get_lines()
    inner = label.strip("$")
    assert alone.get_label() == simple.get_label()
    assert alone.get_label() == r"$\mathrm{%s \; Simple}$" % inner
    assert robust.get_label() == r"$\mathrm{%s \; Robust}$" % inner


@pytest.mark.parametrize("n, expected", [(5, None), (1000, 10)])
def test_residuals_mark_every_tenth_of_the_used_points_decade(n, expected):
    """Residual lines share ``plot_used``'s marker spacing (see that test).

    ON FAILURE: the code is wrong.
    """
    plot = make_ffplot_of_size(n)
    ax = plot.plot_residuals(pct=False)
    assert ax.get_lines()[0].get_markevery() == expected


def test_residual_axes_carry_labels_scales_and_grid():
    """Residual axes carry labels, scales and a grid.

    Percent residuals use symlog (linthresh 10) within +-100 %; counts a
    linear axis. Both label x, grid, and span the raw x range.

    ON FAILURE: the code is wrong, unless the author reworded the residual labels.
    """
    plot, _, obs = make_ffplot()
    plot.set_labels(x="time", y="value")
    plot.set_log(x=True)

    rax = plot.plot_residuals(pct=True)
    assert rax.get_xlabel() == "time"
    assert rax.get_ylabel() == r"$\mathrm{Residual} \; [\%]$"
    assert rax.get_xscale() == "log"
    assert rax.get_yscale() == "symlog"
    assert rax.yaxis.get_transform().linthresh == 10
    assert rax.get_ylim() == (-100, 100)
    assert grid_is_on(rax)

    plot.set_log(x=False)
    rax = plot.plot_residuals(pct=False)
    assert rax.get_ylabel() == r"$\mathrm{Residual} \; [\#]$"
    assert rax.get_yscale() == "linear"
    assert tuple(rax.dataLim.intervalx) == (obs.raw.x[0], obs.raw.x[-1])
    assert rax.dataLim.intervaly[0] == SIMPLE.min()

    plot.set_fit_result(OptimizeResult(fun=np.array([1.0, 2.0, 3.0])))
    rax = plot.plot_residuals(pct=False, kind="robust")
    assert rax.dataLim.intervaly[0] == 1.0  # the x-range extension adds no y = 0


def test_plot_residuals_makes_its_figure_from_subplots_kwargs():
    """Without ``ax``, ``subplots_kwargs`` shapes the new figure.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    ax = plot.plot_residuals(subplots_kwargs={"figsize": (8, 6)})
    assert tuple(ax.get_figure().get_size_inches()) == (8, 6)


# ---------------------------------------------------------------------------
# Stacked fit and residual plot
# ---------------------------------------------------------------------------


def test_stacked_plot_is_a_3_to_1_fit_over_residual_layout():
    """The default stack is a 3:1 fit-over-residual layout.

    It is a 6x4 figure: fit axes three times the residual axes' height, 0.1 mean heights apart, sharing x, with the fit axes'
    x label and tick labels hidden.

    ON FAILURE: the code is wrong, unless the author changed the layout.
    """
    plot, tex, _ = make_ffplot()
    hax, rax = plot.plot_raw_used_fit_resid()
    assert hax.figure is rax.figure
    assert tuple(hax.figure.get_size_inches()) == (6, 4)
    h, r = hax.get_position(), rax.get_position()
    assert h.height / r.height == exact(3.0)
    assert (h.y0 - r.y1) / ((h.height + r.height) / 2) == exact(0.1)
    assert (h.x0, h.width) == (r.x0, r.width)
    assert hax.get_shared_x_axes().joined(hax, rax)
    assert not hax.xaxis.get_label().get_visible()
    assert not any(t.get_visible() for t in hax.xaxis.get_ticklabels())

    labels = [t.get_text() for t in hax.get_legend().get_texts()]
    assert labels == [r"$\mathrm{Obs}$", r"$\mathrm{Used}$", r"$\mathrm{Fit}$"]
    assert len(annotations(hax, tex)) == 1
    assert rax.get_ylabel() == r"$\mathrm{Residual} \; [\%]$"
    hax2, _ = plot.plot_raw_used_fit_resid(annotate=False)
    assert annotations(hax2, tex) == []


def test_stacked_plot_passes_keywords_through():
    """The stacked plot passes its keywords through.

    ``resid_kwargs`` (with ``resid_pct``) reach the residuals, other
    keywords the fit plot, given axes are used, and the caller's dict is
    left unchanged.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    fig, (hax, rax) = plt.subplots(2, 1)
    resid_kwargs = {"resid_pct": False, "color": "r"}
    out = plot.plot_raw_used_fit_resid(
        fit_resid_axes=(hax, rax),
        resid_kwargs=resid_kwargs,
        raw_kwargs={"color": "b"},
    )
    assert out == (hax, rax)
    assert resid_kwargs == {"resid_pct": False, "color": "r"}
    (resid,) = rax.get_lines()
    assert resid.get_ydata() == exact(SIMPLE)
    assert to_rgba(resid.get_color()) == to_rgba("r")
    assert rax.get_ylabel() == r"$\mathrm{Residual} \; [\#]$"
    raw = line_labelled(hax, r"$\mathrm{Obs}$")
    assert to_rgba(raw.get_color()) == to_rgba("b")


def test_stacked_plot_hides_the_fit_axes_x_ticks_on_free_axes():
    """The fit axes' x ticks are hidden on free axes too.

    Given axes outside any grid, where ``label_outer`` hides nothing, the
    fit axes' x label and tick labels are still hidden.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    fig = plt.figure()
    hax = fig.add_axes((0.1, 0.4, 0.8, 0.5))
    rax = fig.add_axes((0.1, 0.1, 0.8, 0.25))
    plot.plot_raw_used_fit_resid(fit_resid_axes=(hax, rax))
    assert not hax.xaxis.get_label().get_visible()
    assert not any(t.get_visible() for t in hax.xaxis.get_ticklabels())
    assert any(t.get_visible() for t in rax.xaxis.get_ticklabels())


def test_an_ffplot_figure_renders_to_png():
    """A complete stacked FFPlot figure draws to an in-memory Agg PNG.

    ON FAILURE: the code is wrong.
    """
    plot, *_ = make_ffplot()
    hax, _ = plot.plot_raw_used_fit_resid()
    buf = io.BytesIO()
    FigureCanvasAgg(hax.figure).print_png(buf)
    assert buf.getvalue().startswith(b"\x89PNG\r\n\x1a\n")
    pixels = render(hax.figure)
    assert len(np.unique(pixels.reshape(-1, 4), axis=0)) > 2
