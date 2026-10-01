import logging

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pathlib import Path

from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions.plots import FFPlot, AxesLabels, LogAxes
from solarwindpy.fitfunctions.core import (
    _ChisqPerDegreeOfFreedom,
    _Observations,
    _UsedRawObs,
)
from solarwindpy.fitfunctions.tex_info import TeXinfo


def make_texinfo(m=2.0, b=1.0):
    """Real TeXinfo for the line ``m x + b`` the helpers below plot."""
    return TeXinfo(
        {"m": m, "b": b},
        {"m": 0.1, "b": 0.1},
        "m x + b",
        _ChisqPerDegreeOfFreedom(0.0, 0.0),
        1.0,
    )


def annotations(ax, tex):
    """Texts on ``ax`` whose content is the TeXinfo annotation."""
    return [t for t in ax.texts if t.get_text() == str(tex)]


def line_data(ax):
    """``(x, y)`` arrays of every Line2D on ``ax``, in drawing order."""
    return [(ln.get_xdata(), ln.get_ydata()) for ln in ax.get_lines()]


class Label:
    """Helper label providing a ``path`` attribute for testing ``FFPlot.path``."""

    def __init__(self, label, path):
        self.label = label
        self.path = path

    def __str__(self):
        return self.label


def make_observations(n, include_weights=True):
    """Build ``_UsedRawObs`` with ``n`` raw points and every other point used.

    Parameters
    ----------
    n : int
        Number of points.
    include_weights : bool
        If True, include weights. If False, weights are None.
    """
    x = np.arange(float(n))
    y = 2.0 * x + 1.0
    w = np.ones_like(x) if include_weights else None
    mask = np.zeros_like(x, dtype=bool)
    mask[::2] = True
    raw = _Observations(x, y, w)
    if include_weights:
        used = _Observations(x[mask], y[mask], w[mask])
    else:
        used = _Observations(x[mask], y[mask], None)
    return _UsedRawObs(used, raw, mask), y


def make_ffplot(n=5, include_weights=True):
    """Create FFPlot for testing."""
    obs, y_fit = make_observations(n, include_weights=include_weights)
    tex = make_texinfo()
    fit_res = OptimizeResult(fun=y_fit[obs.tk_observed] - obs.used.y)
    plot = FFPlot(obs, y_fit, tex, fit_res, fitfunction_name="dummy")
    return plot, tex, obs, y_fit


def test_str_returns_class_name():
    """Ensure ``FFPlot.__str__`` yields the class name."""

    plot, *_ = make_ffplot()
    assert str(plot) == plot.__class__.__name__ == "FFPlot"


def test_initial_properties_and_path():
    plot, tex, obs, y_fit = make_ffplot()
    assert plot.observations is obs
    assert np.all(plot.y_fit == y_fit)
    assert plot.TeX_info is tex
    assert plot.labels == AxesLabels("x", "y")
    assert plot.log == LogAxes(False, False)
    expected = Path("FFPlot") / "dummy" / "x" / "y" / "linX_logY"
    assert plot.path == expected

    plot.set_labels(x=Label("X", "xp"), y=Label("Y", "yp"), z="Z")
    plot.set_log(x=True, y=True)
    plot.set_fitfunction_name("name")
    expected = Path("FFPlot") / "name" / "xp" / "yp" / "Z" / "logX_logY"
    assert plot.path == expected


def test_setters():
    plot, tex, obs, y_fit = make_ffplot()
    plot.set_fitfunction_name("new")
    assert plot.fitfunction_name == "new"

    res = OptimizeResult(x=np.array([1.0]))
    plot.set_fit_result(res)
    assert plot.fit_result is res

    obs2, y_fit2 = make_observations(6)
    plot.set_observations(obs2, y_fit2)
    assert plot.observations is obs2
    assert np.all(plot.y_fit == y_fit2)


def test_set_observations_mismatched_length():
    plot, *_ = make_ffplot()
    obs = plot.observations
    bad_y_fit = np.ones(obs.raw.x.size + 1)
    with pytest.raises(AssertionError):
        plot.set_observations(obs, bad_y_fit)


def test_set_observations_short_y_fit():
    """Ensure shorter ``y_fit`` arrays trigger an assertion."""
    plot, *_ = make_ffplot()
    obs = plot.observations
    bad_y_fit = np.ones(obs.raw.x.size - 1)
    with pytest.raises(AssertionError):
        plot.set_observations(obs, bad_y_fit)


def test_estimate_markevery():
    plot, *_ = make_ffplot(n=5)
    assert plot._estimate_markevery() is None
    plot_big, *_ = make_ffplot(n=1000)
    assert plot_big._estimate_markevery() == 10


def test_format_helpers():
    plot, *_ = make_ffplot()
    plot.set_labels(x="time", y="value")
    plot.set_log(x=True, y=False)

    fig, ax = plt.subplots()
    plot._format_hax(ax)
    assert ax.get_xlabel() == "time"
    assert ax.get_ylabel() == "value"
    assert ax.get_xscale() == "log"
    assert ax.get_yscale() == "linear"

    fig2, rax = plt.subplots()
    plot._format_rax(rax, pct=True)
    assert rax.get_ylabel() == r"$\mathrm{Residual} \; [\%]$"
    assert rax.get_xscale() == "log"
    assert rax.get_yscale() == "symlog"
    assert rax.get_ylim() == (-100, 100)

    fig3, rax2 = plt.subplots()
    plot._format_rax(rax2, pct=False)
    assert rax2.get_ylabel() == r"$\mathrm{Residual} \; [\#]$"


def test_plot_methods_draw_their_data_and_annotate():
    """Each plot method draws its own observations and annotates on request.

    raw draws every point, used draws the every-other subset make_observations
    keeps, fit draws ``y_fit`` over raw x, and annotate toggles the TeXinfo
    text. Without ``ax`` each call makes a fresh figure.

    ON FAILURE: the code is wrong.
    """
    plot, tex, obs, y_fit = make_ffplot()

    ax_raw, _ = plot.plot_raw()
    ((x, y),) = line_data(ax_raw)
    np.testing.assert_array_equal(x, obs.raw.x)
    np.testing.assert_array_equal(y, obs.raw.y)

    ax_used, _ = plot.plot_used()
    ((x, y),) = line_data(ax_used)
    np.testing.assert_array_equal(x, obs.used.x)
    np.testing.assert_array_equal(y, obs.used.y)
    assert ax_used.figure is not ax_raw.figure

    ax_fit = plot.plot_fit()
    ((x, y),) = line_data(ax_fit)
    np.testing.assert_array_equal(x, obs.raw.x)
    np.testing.assert_array_equal(y, y_fit)
    assert len(annotations(ax_fit, tex)) == 1

    assert annotations(plot.plot_fit(annotate=False), tex) == []

    ax = plot.plot_raw_used_fit()
    labels = {t.get_text() for t in ax.get_legend().get_texts()}
    assert labels == {r"$\mathrm{Obs}$", r"$\mathrm{Used}$", r"$\mathrm{Fit}$"}

    ax_resid = plot.plot_residuals(kind="simple", pct=False)
    ((x, y),) = line_data(ax_resid)
    np.testing.assert_array_equal(x, obs.used.x)
    np.testing.assert_array_equal(y, y_fit[obs.tk_observed] - obs.used.y)
    assert ax_resid.figure is not ax_fit.figure


def test_plot_raw_used_fit_resid():
    """The stacked plot puts data on ``hax``, residuals on ``rax``.

    ON FAILURE: the code is wrong.
    """
    plot, tex, *_ = make_ffplot()

    hax, rax = plot.plot_raw_used_fit_resid()
    assert isinstance(hax, plt.Axes)
    assert isinstance(rax, plt.Axes)
    assert hax.figure is rax.figure
    labels = {t.get_text() for t in hax.get_legend().get_texts()}
    assert labels == {r"$\mathrm{Obs}$", r"$\mathrm{Used}$", r"$\mathrm{Fit}$"}
    assert len(annotations(hax, tex)) == 1

    hax2, _ = plot.plot_raw_used_fit_resid(annotate=False)
    assert annotations(hax2, tex) == []


def test_label_log_texinfo():
    plot, tex, *_ = make_ffplot()
    plot.set_labels(y="Y")
    assert plot.labels == AxesLabels("x", "Y")
    with pytest.raises(KeyError):
        plot.set_labels(q="bad")

    plot.set_log(x=True)
    assert plot.log == LogAxes(True, False)

    tex2 = make_texinfo(m=3.0)
    plot.set_TeX_info(tex2)
    assert plot.TeX_info is tex2


def test_plot_residuals_simple_pct_false():
    plot, *_ = make_ffplot()
    ax = plot.plot_residuals(kind="simple", pct=False)
    assert isinstance(ax, plt.Axes)
    line = ax.get_lines()[0]
    expected = plot.y_fit[plot.observations.tk_observed] - plot.observations.used.y
    assert np.allclose(line.get_ydata(), expected)
    assert ax.get_ylabel() == r"$\mathrm{Residual} \; [\#]$"
    ax.legend()
    labels = {t.get_text() for t in ax.get_legend().get_texts()}
    assert labels == {r"$\mathrm{ \; Simple}$"}


def test_plot_residuals_robust():
    plot, *_ = make_ffplot()
    ax = plot.plot_residuals(kind="robust")
    assert isinstance(ax, plt.Axes)
    line = ax.get_lines()[0]
    y_fit_used = plot.y_fit[plot.observations.tk_observed]
    expected = 100.0 * (plot.fit_result.fun / y_fit_used)
    assert np.allclose(line.get_ydata(), expected)
    ax.legend()
    labels = {t.get_text() for t in ax.get_legend().get_texts()}
    assert labels == {r"$\mathrm{ \; Robust}$"}
    assert ax.get_ylabel() == r"$\mathrm{Residual} \; [\%]$"


def test_plot_residuals_missing_fun_no_exception():
    plot, *_ = make_ffplot()
    plot.set_fit_result(OptimizeResult())
    ax = plot.plot_residuals(kind="both")
    assert isinstance(ax, plt.Axes)
    lines = ax.get_lines()
    assert len(lines) == 1
    ax.legend()
    labels = {t.get_text() for t in ax.get_legend().get_texts()}
    assert labels == {r"$\mathrm{ \; Simple}$"}
    assert ax.get_ylabel() == r"$\mathrm{Residual} \; [\%]$"


# ============================================================================
# Phase 6 Coverage Tests
# ============================================================================


class TestFormatHaxLogY:
    """Test log y-scale in _format_hax (line 163)."""

    def test_format_hax_with_log_y(self):
        """Verify _format_hax sets y-axis to log scale when log.y is True."""
        plot, *_ = make_ffplot()
        plot.set_log(y=True)

        fig, ax = plt.subplots()
        plot._format_hax(ax)

        assert ax.get_yscale() == "log"
        plt.close(fig)


class TestPlotRawNoWeights:
    """Test warning when weights are None in plot_raw (lines 264-267)."""

    def test_plot_raw_no_weights_logs_warning(self, caplog):
        """Verify plot_raw logs warning when w is None and plot_window=True."""
        plot, *_ = make_ffplot(include_weights=False)

        with caplog.at_level(logging.WARNING):
            ax, plotted = plot.plot_raw(plot_window=True)

        assert "No weights" in caplog.text
        assert "Setting w to 0" in caplog.text
        plt.close()


class TestPlotRawEdgeKwargs:
    """Test edge_kwargs handling in plot_raw (lines 253-260, 290-294)."""

    def test_plot_raw_with_edge_kwargs(self):
        """Verify plot_raw plots edges when edge_kwargs is provided."""
        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        edge_kwargs = {"linestyle": "--", "alpha": 0.5}
        ax, plotted = plot.plot_raw(ax=ax, plot_window=True, edge_kwargs=edge_kwargs)

        assert len(plotted) == 3
        line, window, edges = plotted
        assert isinstance(edges, (list, tuple))
        assert len(edges) == 2
        plt.close(fig)


class TestPlotRawNoWindow:
    """Test errorbar path in plot_raw when plot_window=False (line 300)."""

    def test_plot_raw_no_window_uses_errorbar(self):
        """Verify plot_raw uses errorbar when plot_window=False."""
        from matplotlib.container import ErrorbarContainer

        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        ax, plotted = plot.plot_raw(ax=ax, plot_window=False)

        assert isinstance(plotted, ErrorbarContainer)
        plt.close(fig)


class TestPlotUsedNoWeights:
    """Test warning when weights are None in plot_used (lines 343-346)."""

    def test_plot_used_no_weights_logs_warning(self, caplog):
        """Verify plot_used logs warning when w is None and plot_window=True."""
        plot, *_ = make_ffplot(include_weights=False)

        with caplog.at_level(logging.WARNING):
            ax, plotted = plot.plot_used(plot_window=True)

        assert "No weights" in caplog.text
        assert "Setting w to 0" in caplog.text
        plt.close()


class TestPlotUsedEdgeKwargs:
    """Test edge_kwargs handling in plot_used (lines 380-394)."""

    def test_plot_used_with_edge_kwargs(self):
        """Verify plot_used plots edges when edge_kwargs is provided."""
        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        edge_kwargs = {"linestyle": "--", "alpha": 0.5}
        ax, plotted = plot.plot_used(ax=ax, plot_window=True, edge_kwargs=edge_kwargs)

        assert len(plotted) == 3
        line, window, edges = plotted
        assert isinstance(edges, (list, tuple))
        assert len(edges) == 2
        plt.close(fig)


class TestPlotUsedNoWindow:
    """Test errorbar path in plot_used when plot_window=False (line 410)."""

    def test_plot_used_no_window_uses_errorbar(self):
        """Verify plot_used uses errorbar when plot_window=False."""
        from matplotlib.container import ErrorbarContainer

        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        ax, plotted = plot.plot_used(ax=ax, plot_window=False)

        assert isinstance(plotted, ErrorbarContainer)
        plt.close(fig)


class TestPlotResidualsLabelFormatting:
    """Test label formatting with non-empty label (lines 591-592)."""

    def test_plot_residuals_simple_with_label(self):
        """Verify plot_residuals formats label correctly when provided."""
        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        ax = plot.plot_residuals(ax=ax, kind="simple", label=r"$\mathrm{Test}$")

        ax.legend()
        labels = [t.get_text() for t in ax.get_legend().get_texts()]
        assert len(labels) == 1
        assert "Simple" in labels[0]
        plt.close(fig)


class TestPlotRawUsedFitResidWithAxes:
    """Test plot_raw_used_fit_resid with provided axes (line 696)."""

    def test_plot_raw_used_fit_resid_with_provided_axes(self):
        """Verify plot_raw_used_fit_resid uses provided axes."""
        plot, *_ = make_ffplot()

        fig, (hax, rax) = plt.subplots(2, 1, figsize=(6, 4))

        result_hax, result_rax = plot.plot_raw_used_fit_resid(fit_resid_axes=(hax, rax))

        assert result_hax is hax
        assert result_rax is rax
        plt.close(fig)


class TestPlotRawUsedFitDrawstyle:
    """Test plot_raw_used_fit with custom drawstyle."""

    def test_plot_raw_used_fit_custom_drawstyle(self):
        """Verify plot_raw_used_fit passes drawstyle to sub-methods."""
        plot, *_ = make_ffplot()

        fig, ax = plt.subplots()
        result_ax = plot.plot_raw_used_fit(ax=ax, drawstyle="steps-post")

        assert result_ax is ax
        plt.close(fig)


class TestPathWithLabelZ:
    """Test path property with z label."""

    def test_path_with_z_label_as_label_object(self):
        """Verify path includes z label from Label object."""
        plot, *_ = make_ffplot()
        plot.set_labels(
            x=Label("X", "xp"),
            y=Label("Y", "yp"),
            z=Label("Z", "zp"),
        )

        expected = Path("FFPlot") / "dummy" / "xp" / "yp" / "zp" / "linX_logY"
        assert plot.path == expected


class TestGetDefaultPlotStyle:
    """Test _get_default_plot_style method."""

    def test_get_default_plot_style_raw(self):
        """Verify default style for raw plots."""
        plot, *_ = make_ffplot()
        style = plot._get_default_plot_style("raw")
        assert style["color"] == "k"
        assert style["label"] == r"$\mathrm{Obs}$"

    def test_get_default_plot_style_unknown(self):
        """Verify empty dict for unknown plot type."""
        plot, *_ = make_ffplot()
        style = plot._get_default_plot_style("unknown")
        assert style == {}


class TestPlotResidualsSubplotsKwargs:
    """Test plot_residuals with subplots_kwargs."""

    def test_plot_residuals_with_subplots_kwargs(self):
        """Verify plot_residuals passes subplots_kwargs when creating axes."""
        plot, *_ = make_ffplot()

        ax = plot.plot_residuals(
            ax=None,
            subplots_kwargs={"figsize": (8, 6)},
        )

        assert isinstance(ax, plt.Axes)
        fig = ax.get_figure()
        assert fig.get_figwidth() == 8
        assert fig.get_figheight() == 6
        plt.close(fig)
