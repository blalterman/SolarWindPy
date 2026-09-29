#!/usr/bin/env python
"""Tests for the plot scaffolding in ``solarwindpy.plotting.base``.

``Base`` and its mixins exist to be subclassed, so the tests subclass them the
way the package's own plots do: ``LinePlot`` and ``LimPlot`` below implement
the abstract methods with a few lines each and call the inherited hooks
(``_format_axis``, ``_make_cbar``) exactly as ``Scatter`` and ``Hist1D`` do.
Every assertion is on public state (``data``, ``labels``, ``log``, ``path``,
``clip``) or on the real matplotlib ``Axes`` and ``Colorbar`` the hooks
produced on the Agg backend. Expected values come from the hand-typed ``ROWS``
table or the ``_expected_path`` helper, which rebuilds the documented path
layout (class, x, y, z, scale) from ``pathlib`` alone.
"""

import logging
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
    CbarMaker,
    DataLimFormatter,
    LogAxes,
    PlotWithZdata,
    RangeLimits,
)
from solarwindpy.plotting.labels import TeXlabel  # noqa: E402

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


def _col(rows, i):
    return np.array([r[i] for r in rows])


def _scale(logx, logy):
    """Documented scale tag: ``logX``/``linX`` then ``logY``/``linY``."""
    return "{}X-{}Y".format("log" if logx else "lin", "log" if logy else "lin")


def _expected_path(cls_name, x, y, z, logx=False, logy=False):
    """Class name, then x, y, z labels, then the scale tag."""
    return Path(cls_name, x, y, z, _scale(logx, logy))


class LinePlot(PlotWithZdata, CbarMaker):
    """Minimal concrete plot: points coloured by z, then the shared hooks."""

    def __init__(self, x, y, z=None, clip_data=False):
        super().__init__()
        self.set_data(x, y, z, clip_data)

    def make_plot(self, ax, transpose_axes=False, cbar_kwargs=None):
        d = self.data
        coll = ax.scatter(d["x"], d["y"], c=d["z"])
        self._format_axis(ax, transpose_axes=transpose_axes)
        cbar = None
        if cbar_kwargs is not None:
            cbar = self._make_cbar(coll, **cbar_kwargs)
        return coll, cbar


class LimPlot(DataLimFormatter, PlotWithZdata):
    """Minimal plot using the ``DataLimFormatter`` mixin."""

    def __init__(self, x, y):
        super().__init__()
        self.set_data(x, y)

    def make_plot(self, ax):
        coll = ax.scatter(self.data["x"], self.data["y"])
        self._format_axis(ax, coll)
        return coll


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
    assert plot.labels.x == "x"


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
    axis name.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x="bulk speed", y="None", z=None, auto_update_path=False)
    plot.set_log(x=True)
    plot.set_path("auto")
    assert plot.path == _expected_path("LinePlot", "bulk-speed", "y", "z", True)


def test_auto_path_uses_texlabel_paths_and_puts_scale_before_norm():
    """A label object contributes its ``path``; a trailing norm stays last.

    With a column-normalized z label the scale tag is prefixed to the norm
    component, so the path reads x, y, z in order (``base.py`` comment).

    ON FAILURE: the code is wrong.
    """
    xl = TeXlabel(("v", "x", "p1"))
    zl = TeXlabel(("n", "", "p1"), axnorm="c")
    assert zl.path.name.endswith("norm")  # the fixture exercises the norm branch

    plot = LinePlot(X, Y, Z)
    plot.set_labels(x=xl, y="y", z=zl)
    norm = "{}-{}".format(_scale(False, False), zl.path.name)
    expected = Path("LinePlot", xl.path, "y", zl.path.parent, norm)
    assert plot.path == expected


@pytest.mark.parametrize(
    "add_scale, expected",
    [
        (False, Path("figs", "run1")),
        (True, Path("figs", "run1", _scale(False, True))),
    ],
)
def test_explicit_path_is_used_as_given_plus_optional_scale(add_scale, expected):
    """A path other than "auto" is used verbatim; ``add_scale`` appends scale.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    plot.set_log(y=True)
    plot.set_path("figs/run1", add_scale=add_scale)
    assert plot.path == expected


# ---------------------------------------------------------------------------
# _format_axis, _make_cbar, DataLimFormatter, on real Axes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("transpose", [False, True])
def test_format_axis_applies_labels_scales_grid_and_ticks(ax, transpose):
    """Labels and log scales land on their axes, swapped when transposed.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(x="Vx", y="Np")
    plot.set_log(x=True, y=False)
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


def test_format_axis_leaves_a_none_label_blank(ax):
    """A ``None`` label is not written, so the axis label stays empty.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y)
    plot.set_labels(x=None, y="Np")
    plot.make_plot(ax)
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("", "Np")


def test_make_cbar_draws_a_colorbar_for_the_mappable_labelled_z(ax):
    """The colorbar maps the plotted collection and carries ``labels.z``.

    ON FAILURE: the code is wrong.
    """
    plot = LinePlot(X, Y, Z)
    plot.set_labels(z="T")
    coll, cbar = plot.make_plot(ax, cbar_kwargs={"ax": ax})
    assert isinstance(cbar, Colorbar)
    assert cbar.mappable is coll
    assert cbar.ax.get_ylabel() == "T"
    assert cbar.ax.figure is ax.figure


def test_make_cbar_draws_into_a_given_cax_with_a_given_label(ax):
    """``cax`` receives the colorbar; ``label`` overrides ``labels.z``.

    ON FAILURE: the code is wrong.
    """
    cax = ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))
    plot = LinePlot(X, Y, Z)
    plot.set_labels(z="T")
    _, cbar = plot.make_plot(ax, cbar_kwargs={"cax": cax, "label": "custom"})
    assert cbar.ax is cax
    assert cax.get_ylabel() == "custom"


def test_make_cbar_accepts_a_list_of_axes(ax):
    """``ax`` may be a sequence of axes; the colorbar joins their figure.

    ON FAILURE: the code is wrong.
    """
    _, cbar = LinePlot(X, Y, Z).make_plot(ax, cbar_kwargs={"ax": [ax]})
    assert cbar.ax.figure is ax.figure
    assert len(ax.figure.axes) == 2


@pytest.mark.parametrize(
    "which, match",
    [("both", "Can't pass ax and cax"), ("neither", "You must pass `ax` or `cax`")],
)
def test_make_cbar_needs_exactly_one_of_ax_and_cax(ax, which, match):
    """Both or neither of ``ax``/``cax`` raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    kwargs = {}
    if which == "both":
        kwargs = {"ax": ax, "cax": ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))}
    with pytest.raises(ValueError, match=match):
        LinePlot(X, Y, Z).make_plot(ax, cbar_kwargs=kwargs)


def test_data_lim_formatter_pins_limits_to_the_data_extent(ax):
    """Axis limits are the min and max of the kept data, with no margin.

    Also formats the axis through ``Base`` (labels are applied).

    ON FAILURE: the code is wrong.
    """
    plot = LimPlot(X, Y)
    plot.set_labels(x="Vx", y="Np")
    plot.make_plot(ax)
    complete = [r for r in ROWS if not (np.isnan(r[1]) or np.isnan(r[2]))]
    xs, ys = _col(complete, 1), _col(complete, 2)
    assert ax.get_xlim() == (xs.min(), xs.max())
    assert ax.get_ylim() == (ys.min(), ys.max())
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("Vx", "Np")
