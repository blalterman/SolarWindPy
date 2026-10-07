#!/usr/bin/env python
"""Tests for the plot scaffolding in ``solarwindpy.plotting.base``.

``Base`` and its mixins exist to be subclassed. The public state they manage
(``data``, ``labels``, ``log``, ``path``, ``clip``) is tested on ``LinePlot``,
a minimal ``PlotWithZdata`` subclass. Axis formatting and colorbars are tested
through the package's own ``Hist1D`` and ``Scatter``, asserting on the real
matplotlib ``Axes`` and ``Colorbar`` on the Agg backend. Expected values
come from the hand-typed ``ROWS`` table or the ``_expected_path`` helper, which rebuilds the documented path
layout (class, x, y, z, scale) from ``pathlib`` alone.
"""

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402

from solarwindpy.plotting.base import (  # noqa: E402
    AxesLabels,
    Base,
    LogAxes,
    PlotWithZdata,
    RangeLimits,
)
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402

# ---------------------------------------------------------------------------
# Chosen input: index, x, y, z. Row 11 has NaN x, row 13 NaN y, row 14 NaN z,
# so each column's NaN is dropped separately. The dropped rows hold values
# outside the kept extent (y = 5, x = 9), so a kept NaN row widens the limits.
# The kept extremes sit in interior rows 12 and 14, so a first/last value taken
# for a min/max, or a swapped axis, changes the answer.
# ---------------------------------------------------------------------------

ROWS = [
    (10, 2.0, 45.0, 5.0),
    (11, np.nan, 5.0, 6.0),
    (12, 1.0, 20.0, 7.0),
    (13, 9.0, np.nan, 8.0),
    (14, 3.0, 50.0, np.nan),
    (15, 2.5, 35.0, 9.0),
]
KEPT = [r for r in ROWS if not any(np.isnan(v) for v in r[1:])]

INDEX = pd.Index([r[0] for r in ROWS])
X = pd.Series([r[1] for r in ROWS], index=INDEX)
Y = pd.Series([r[2] for r in ROWS], index=INDEX)
Z = pd.Series([r[3] for r in ROWS], index=INDEX)

# Positive values spanning three decades, for Hist1D(logx=True), which bins
# log10(x) and so needs x > 0.
DECADES = pd.Series([1.0, 10.0, 100.0, 1000.0])

# Label objects for the path tests: a plain x label and a column-normalized z
# label, whose path ends in "norm" and so takes set_path's norm branch.
PLAIN_XLABEL = TeXlabel(("v", "x", "p1"))
NORM_ZLABEL = TeXlabel(("n", "", "p1"), axnorm="c")


def _col(rows, i):
    return np.array([r[i] for r in rows])


def _scale(logx, logy):
    """Documented scale tag: ``logX``/``linX`` then ``logY``/``linY``."""
    return "{}X-{}Y".format("log" if logx else "lin", "log" if logy else "lin")


def _expected_path(cls_name, x, y, z, logx=False, logy=False):
    """Class name, then x, y, z labels, then the scale tag."""
    return Path(cls_name, x, y, z, _scale(logx, logy))


class LinePlot(PlotWithZdata):
    """Minimal concrete plot: points coloured by z."""

    def __init__(self, x, y, z=None, clip_data=False):
        super().__init__()
        self.set_data(x, y, z, clip_data)

    def make_plot(self, ax):
        d = self.data
        return ax.scatter(d["x"], d["y"], c=d["z"])


@pytest.fixture
def ax():
    _, axis = plt.subplots()
    yield axis
    plt.close("all")


# ---------------------------------------------------------------------------
# Named tuples and the abstract base
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls, given, expected",
    [
        (LogAxes, (True,), (True, False)),
        (AxesLabels, ("a", "b"), ("a", "b", None)),
        (RangeLimits, (3,), (3, None)),
    ],
)
def test_omitted_last_field_takes_its_neutral_default(cls, given, expected):
    """Omitting the last field gives linear y, no z label, no upper limit.

    Subclasses rely on this: ``Scatter`` builds ``AxesLabels`` without z when
    there is no z data, and ``RangeLimits(lower)`` is an open upper bound.

    ON FAILURE: the code is wrong.
    """
    assert tuple(cls(*given)) == expected


def test_base_and_an_incomplete_subclass_cannot_be_instantiated():
    """``Base`` is abstract, and so is a subclass missing ``make_plot``.

    ON FAILURE: the code is wrong.
    """

    class NoMakePlot(PlotWithZdata):
        def __init__(self):
            super().__init__()

    with pytest.raises(TypeError, match="abstract"):
        Base()
    with pytest.raises(TypeError, match="make_plot"):
        NoMakePlot()


def test_str_and_logger_name_the_concrete_class():
    """``str(plot)`` is the class name and the logger sits under the package.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    assert str(plot) == "LinePlot"
    assert isinstance(plot.logger, logging.Logger)
    assert plot.logger.name.startswith("solarwindpy.plotting.")
    assert plot.logger.name.endswith(".LinePlot")


# ---------------------------------------------------------------------------
# PlotWithZdata.set_data
# ---------------------------------------------------------------------------


def test_set_data_keeps_complete_rows_with_their_values_and_index():
    """Rows with NaN in x, y or z are dropped; the rest keep index and values.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    assert list(plot.data.columns) == ["x", "y", "z"]
    assert list(plot.data.index) == [r[0] for r in KEPT]
    for i, col in enumerate("xyz", start=1):
        np.testing.assert_array_equal(plot.data[col].to_numpy(), _col(KEPT, i))


def test_set_data_without_z_gives_every_point_z_equal_one():
    """With no z, each complete (x, y) row gets z = 1 (docstring).

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    complete = [r for r in ROWS if not (np.isnan(r[1]) or np.isnan(r[2]))]
    assert list(plot.data.index) == [r[0] for r in complete]
    np.testing.assert_array_equal(plot.data["z"].to_numpy(), np.ones(len(complete)))


def test_set_data_pairs_x_and_y_by_index_label_not_position():
    """Series with different indexes are matched on shared labels only.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, 2.0, 3.0], index=[0, 1, 2])
    y = pd.Series([20.0, 30.0, 40.0], index=[1, 2, 3])
    plot = LinePlot(x, y)
    assert list(plot.data.index) == [1, 2]
    np.testing.assert_array_equal(plot.data["x"].to_numpy(), [2.0, 3.0])
    np.testing.assert_array_equal(plot.data["y"].to_numpy(), [20.0, 30.0])


def test_set_data_with_only_nan_rows_raises_value_error_naming_the_class():
    """No complete row left raises ``ValueError`` (docstring).

    ON FAILURE: the code is wrong.
    """
    nan = pd.Series([np.nan, np.nan])
    with pytest.raises(ValueError, match="LinePlot.*exclusively NaNs"):
        LinePlot(nan, pd.Series([1.0, 2.0]))


@pytest.mark.parametrize("given, expected", [(0, False), (1, True), ("", False)])
def test_clip_is_the_truth_value_of_clip_data(given, expected):
    """``clip`` stores ``bool(clip_data)``.

    ON FAILURE: the code is wrong.
    """
    assert LinePlot(X, Y, clip_data=given).clip is expected


# ---------------------------------------------------------------------------
# set_log, set_labels
# ---------------------------------------------------------------------------


def test_set_log_coerces_to_bool_and_none_keeps_the_current_value():
    """Truthy/falsy values become bools; an omitted axis keeps its value.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    # base.py Base.__init__: LogAxes(x=False), y from the namedtuple default False
    assert plot.log == LogAxes(False, False)
    plot.set_log(x=1, y="yes")
    assert plot.log == LogAxes(True, True)
    assert all(type(v) is bool for v in plot.log)
    plot.set_log(y=0)
    assert plot.log == LogAxes(True, False)
    plot.set_log(x="")
    assert plot.log == LogAxes(False, False)


def test_set_labels_changes_only_the_labels_passed():
    """Labels not passed keep their current values (docstring).

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x="X1", y="Y1", z="Z1")
    plot.set_labels(y="Y2")
    assert plot.labels == AxesLabels("X1", "Y2", "Z1")
    plot.set_labels(z="Z3")
    assert plot.labels == AxesLabels("X1", "Y2", "Z3")


def test_set_labels_rejects_unknown_keywords_naming_each():
    """Any keyword other than x, y, z, auto_update_path raises ``KeyError``.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    with pytest.raises(KeyError, match="Unexpected kwarg") as err:
        plot.set_labels(x="ok", bad1=1, bad2=2)
    assert "bad1" in str(err.value) and "bad2" in str(err.value)
    assert plot.labels.x == "x"  # base.py Base.__init__: AxesLabels(x="x", y="y")


def test_set_labels_rebuilds_the_path_unless_told_not_to():
    """By default the save path follows the new labels; opt-out leaves it.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x="vx", y="np", z="T")
    assert plot.path == _expected_path("LinePlot", "vx", "np", "T")

    plot.set_labels(x="vy", auto_update_path=False)
    assert plot.labels.x == "vy"
    assert plot.path == _expected_path("LinePlot", "vx", "np", "T")


# ---------------------------------------------------------------------------
# set_path
# ---------------------------------------------------------------------------


def test_auto_path_is_class_then_labels_then_scale():
    """``set_path("auto")`` builds class/x/y/z/scale, scale read at call time.

    Spaces become hyphens; a missing or ``"None"`` label falls back to the
    axis name. The literal path was written by hand from reading
    ``Base.set_path`` and ``PlotWithZdata.set_path`` in ``base.py``: class
    name ``LinePlot``; ``"bulk speed"`` has its space replaced by a hyphen;
    ``"None"`` and ``None`` fall back to ``"y"`` and ``"z"``; ``add_scale``
    defaults to True, giving ``"logX"`` and ``"linY"`` joined by ``"-"`` and
    appended because ``"z"`` does not end in ``norm``.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x="bulk speed", y="None", z=None, auto_update_path=False)
    plot.set_log(x=True)
    plot.set_path("auto")
    assert plot.path == _expected_path("LinePlot", "bulk-speed", "y", "z", True)
    assert plot.path == Path("LinePlot/bulk-speed/y/z/logX-linY")  # hand-derived


def test_norm_label_path_ends_in_norm_and_plain_label_path_does_not():
    """The column-normalized z label reaches the norm branch; the x label not.

    ``set_path`` treats a path whose last part ends in ``norm`` specially, so
    the next test needs one label that does and one that does not.

    ON FAILURE: the fixture no longer separates a normalized label path from a plain one; fix the fixture.
    """
    assert NORM_ZLABEL.path.name.endswith("norm")
    assert not PLAIN_XLABEL.path.name.endswith("norm")


def test_auto_path_uses_texlabel_paths_and_puts_scale_before_norm():
    """A label object contributes its ``path``; a trailing norm stays last.

    With a column-normalized z label the scale tag is prefixed to the norm
    component, so the path reads x, y, z in order (``base.py`` comment).

    ON FAILURE: the code is wrong.
    """
    xl, zl = PLAIN_XLABEL, NORM_ZLABEL
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x=xl, y="y", z=zl)
    norm = "{}-{}".format(_scale(False, False), zl.path.name)
    expected = Path("LinePlot", xl.path, "y", zl.path.parent, norm)
    assert plot.path == expected


@pytest.mark.parametrize(
    "add_scale, expected",
    [
        (False, Path("figs", "run1")),
        (True, Path("figs/run1/linX-logY")),
    ],
)
def test_explicit_path_is_used_as_given_plus_optional_scale(add_scale, expected):
    """A path other than "auto" is used verbatim; ``add_scale`` appends scale.

    The expected paths were written by hand from reading ``set_path`` in
    ``base.py``: a non-"auto" ``new`` becomes ``Path(new)``, and with linear x
    and log y the scale tag is ``"linX"`` and ``"logY"`` joined by ``"-"``.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    plot.set_log(y=True)
    plot.set_path("figs/run1", add_scale=add_scale)
    assert plot.path == expected


# ---------------------------------------------------------------------------
# Axis formatting and colorbars, through Hist1D and Scatter on real Axes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("transpose", [False, True])
def test_hist1d_axes_carry_labels_scales_grid_and_ticks(ax, transpose):
    """Labels and log scales land on their axes, swapped when transposed.

    ``Hist1D(logx=True)`` gives log x and linear y; ``make_plot`` formats the
    axes through ``Base``, so grid lines are on and ticks point in and out.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(DECADES, logx=True, nbins=3)
    plot.set_labels(x="Vx", y="Np")
    plot.make_plot(ax, transpose_axes=transpose)

    xl, yl, xs, ys = ("Vx", "Np", "log", "linear")
    if transpose:
        xl, yl, xs, ys = yl, xl, ys, xs
    assert (ax.get_xlabel(), ax.get_ylabel()) == (xl, yl)
    assert (ax.get_xscale(), ax.get_yscale()) == (xs, ys)
    for axis in (ax.xaxis, ax.yaxis):
        ticks = axis.get_major_ticks()
        assert all(t.gridline.get_visible() for t in ticks)
        assert {t.get_tickdir() for t in ticks} == {"inout"}


def test_hist1d_leaves_a_none_label_blank(ax):
    """A ``None`` label is not written, so the axis label stays empty.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(DECADES, logx=True, nbins=3)
    plot.set_labels(x=None, y="Np")
    plot.make_plot(ax)
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("", "Np")


def test_scatter_colorbar_maps_the_plotted_collection_labelled_z(ax):
    """The colorbar maps the scatter collection and carries ``labels.z``.

    ON FAILURE: the code is wrong.
    """
    plot = Scatter(X, Y, Z)
    plot.set_labels(z="T")
    _, cbar = plot.make_plot(ax, cbar_kwargs={"ax": ax})
    assert isinstance(cbar, Colorbar)
    assert cbar.mappable is ax.collections[0]
    assert cbar.ax.get_ylabel() == "T"
    assert cbar.ax.figure is ax.figure


def test_scatter_colorbar_draws_into_a_given_cax_with_a_given_label(ax):
    """``cax`` receives the colorbar; ``label`` overrides ``labels.z``.

    ON FAILURE: the code is wrong.
    """
    cax = ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))
    plot = Scatter(X, Y, Z)
    plot.set_labels(z="T")
    _, cbar = plot.make_plot(ax, cbar_kwargs={"cax": cax, "label": "custom"})
    assert cbar.ax is cax
    assert cax.get_ylabel() == "custom"


def test_scatter_colorbar_accepts_a_list_of_axes(ax):
    """``ax`` may be a sequence of axes; the colorbar joins their figure.

    ON FAILURE: the code is wrong.
    """
    _, cbar = Scatter(X, Y, Z).make_plot(ax, cbar_kwargs={"ax": [ax]})
    assert cbar.ax.figure is ax.figure
    assert len(ax.figure.axes) == 2


def test_scatter_colorbar_given_both_ax_and_cax_raises_value_error(ax):
    """Passing both ``ax`` and ``cax`` for the colorbar raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    kwargs = {"ax": ax, "cax": ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))}
    with pytest.raises(ValueError, match="Can't pass ax and cax"):
        Scatter(X, Y, Z).make_plot(ax, cbar_kwargs=kwargs)


# ---------------------------------------------------------------------------
# ``cbar_kwargs`` belongs to the caller. Every public plot call that draws a
# colorbar must leave the caller's dict as it was, so one dict can style many
# plots. Chosen input: 12 points on a 2 x 2 grid whose cells hold 1, 2, 3 and
# 6 points, so counts, means and contours are all defined.
# ---------------------------------------------------------------------------

GRID_EDGES = np.array([0.0, 1.0, 2.0])
GRID_CELLS = [((0.5, 0.5), 1), ((1.5, 0.5), 2), ((0.5, 1.5), 3), ((1.5, 1.5), 6)]
GRID_X = pd.Series([c[0] for c, n in GRID_CELLS for _ in range(n)], dtype=float)
GRID_Y = pd.Series([c[1] for c, n in GRID_CELLS for _ in range(n)], dtype=float)
GRID_Z = pd.Series(np.arange(GRID_X.size, dtype=float) + 1.0)
LEVELS = [2.0, 3.0]  # inside the plotted counts and means, so contours draw


def _hist2d():
    from solarwindpy.plotting.hist2d import Hist2D

    return Hist2D(GRID_X, GRID_Y, nbins=[GRID_EDGES, GRID_EDGES])


def _spiral():
    from solarwindpy.plotting.spiral import SpiralPlot2D

    splot = SpiralPlot2D(
        GRID_X + 0.1 * np.arange(GRID_X.size) / GRID_X.size,
        GRID_Y,
        GRID_Z,
        initial_bins=(GRID_EDGES, GRID_EDGES),
    )
    splot.initialize_mesh(min_per_bin=100)
    splot.build_grouped()
    return splot


# Each entry draws one colorbar on ``ax`` and returns it.
CBAR_PLOTS = {
    "Scatter.make_plot": lambda ax, kw: Scatter(X, Y, Z).make_plot(
        ax=ax, cbar_kwargs=kw
    )[1],
    "Hist2D.make_plot": lambda ax, kw: _hist2d().make_plot(ax=ax, cbar_kwargs=kw)[1],
    "Hist2D.plot_hist_with_contours": lambda ax, kw: _hist2d().plot_hist_with_contours(
        ax=ax, cbar_kwargs=kw, levels=LEVELS
    )[1],
    "Hist2D.plot_contours": lambda ax, kw: _hist2d().plot_contours(
        ax=ax, cbar_kwargs=kw, levels=LEVELS
    )[1],
    "SpiralPlot2D.make_plot": lambda ax, kw: _spiral().make_plot(ax=ax, cbar_kwargs=kw)[
        1
    ],
    "SpiralPlot2D.plot_contours": lambda ax, kw: _spiral().plot_contours(
        ax=ax, cbar_kwargs=kw, levels=LEVELS, method="tricontour"
    )[1],
}


class CbarKwargsMutated(AssertionError):
    """A plot call changed the caller's ``cbar_kwargs`` dict."""


@pytest.mark.parametrize("plot", CBAR_PLOTS.values(), ids=CBAR_PLOTS.keys())
def test_plot_calls_leave_the_callers_cbar_kwargs_unchanged(plot):
    """After a plot call the caller's ``cbar_kwargs`` holds what it held before.

    ON FAILURE: the code is wrong.
    """
    kwargs = {"shrink": 0.5}
    _, ax = plt.subplots()
    try:
        plot(ax, kwargs)
    finally:
        plt.close("all")
    if kwargs != {"shrink": 0.5}:  # the dict the caller built, above
        raise CbarKwargsMutated(f"cbar_kwargs became {kwargs}")


def test_joint_plot_leaves_the_callers_cbar_kwargs_unchanged():
    """``make_joint_h2_h1_plot`` does not pop keys from the caller's dict.

    ON FAILURE: the code is wrong.
    """
    kwargs = {"orientation": "horizontal", "label": "custom"}
    try:
        _, _, _, cbar = _hist2d().make_joint_h2_h1_plot(cbar_kwargs=kwargs)
        assert cbar.ax.get_xlabel() == "custom"  # the label the caller passed
    finally:
        plt.close("all")
    if kwargs != {"orientation": "horizontal", "label": "custom"}:  # as built above
        raise CbarKwargsMutated(f"cbar_kwargs became {kwargs}")


@pytest.mark.parametrize("plot", CBAR_PLOTS.values(), ids=CBAR_PLOTS.keys())
def test_reused_cbar_kwargs_put_each_colorbar_beside_its_own_axes(plot):
    """One dict reused for plots on two figures: each colorbar joins its own.

    ON FAILURE: the code is wrong.
    """
    kwargs = {"shrink": 0.5}
    _, ax1 = plt.subplots()
    _, ax2 = plt.subplots()
    try:
        cbar1 = plot(ax1, kwargs)
        # The defect makes matplotlib warn about a cross-figure colorbar; keep
        # that warning from pre-empting the assertion under ``-W error``.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cbar2 = plot(ax2, kwargs)
        assert cbar1.ax.figure is ax1.figure  # the axes each call was given
        assert cbar2.ax.figure is ax2.figure
    finally:
        plt.close("all")


@pytest.mark.parametrize("plot", CBAR_PLOTS.values(), ids=CBAR_PLOTS.keys())
def test_cbar_kwargs_that_are_not_a_mapping_raise_type_error(plot):
    """A ``cbar_kwargs`` that is not a mapping is refused with ``TypeError``.

    ON FAILURE: the code is wrong.
    """
    _, ax = plt.subplots()
    try:
        with pytest.raises(TypeError, match="cbar_kwargs must be a mapping"):
            plot(ax, [("shrink", 0.5)])
    finally:
        plt.close("all")
