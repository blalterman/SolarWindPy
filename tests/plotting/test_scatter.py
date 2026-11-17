#!/usr/bin/env python
"""Tests for ``solarwindpy.plotting.scatter.Scatter``.

A scatter plot hands matplotlib one point per complete (x, y, z) row, coloured
by z when z varies, with a colorbar labelled ``labels.z``. Expectations come
from the hand-typed ``ROWS`` table; assertions read the real ``PathCollection``
(offsets, colour array, sizes), ``Axes`` and ``Colorbar`` on the Agg backend.

Clipping both tails (``clip=True``) is tested in
``tests/test_source_plotting_defects.py``, beside the defect it fixed; the
one-tailed ``"l"`` and ``"u"`` are tested here.
"""

import io
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.collections import LineCollection, PathCollection  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402
from matplotlib.colors import LogNorm, Normalize, to_rgb  # noqa: E402

from solarwindpy.plotting import base, scales  # noqa: E402
from solarwindpy.plotting.base import ClipAxes, LogAxes  # noqa: E402
from solarwindpy.plotting.labels.base import (  # noqa: E402
    PlainStringLabelWarning,
    TeXlabel,
)
from solarwindpy.plotting.labels.special import ManualLabel  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# Tests here pass plain str labels on purpose, to exercise that path; they opt
# out of PlainStringLabelWarning the deliberate way its message describes.
pytestmark = pytest.mark.filterwarnings(
    "ignore::solarwindpy.plotting.labels.base.PlainStringLabelWarning"
)


# ---------------------------------------------------------------------------
# Chosen input: index, x, y, z. Row 1 lacks y and row 3 lacks z; both hold
# values outside the kept extent (x = 9, y = 99) so keeping either shows up in
# the offsets and the axis limits. Extremes of the kept rows are interior.
# ---------------------------------------------------------------------------

ROWS = [
    (0, 2.0, 30.0, 0.5),
    (1, 9.0, np.nan, 0.7),
    (2, 1.0, 50.0, 0.9),
    (3, 3.0, 99.0, np.nan),
    (4, 4.0, 10.0, 0.2),
    (5, 2.5, 40.0, 0.4),
]
KEPT = [r for r in ROWS if not any(np.isnan(v) for v in r[1:])]
XY_KEPT = [r for r in ROWS if not (np.isnan(r[1]) or np.isnan(r[2]))]

X = pd.Series([r[1] for r in ROWS])
Y = pd.Series([r[2] for r in ROWS])
Z = pd.Series([r[3] for r in ROWS])


def _col(rows, i):
    return np.array([r[i] for r in rows])


@pytest.fixture
def ax():
    _, axis = plt.subplots()
    yield axis
    plt.close("all")


XFAIL_F = pytest.mark.xfail(
    strict=True,
    raises=(AttributeError, KeyError),
    reason="SizeScale, AlphaScale, ScatterLabels and make_plot's size_scale, "
    "alpha_scale and draw_order are not in the package yet (AttributeError; "
    "set_labels(size=) raises KeyError 'Unexpected kwarg'); remove this marker "
    "when Stage F lands",
)


@XFAIL_F
def test_new_scatter_has_linear_axes_and_default_labels():
    """Defaults: linear axes, labels x and y; z, size, alpha labelled only when given.

    ON FAILURE: the code is wrong.
    """
    labels = base.ScatterLabels
    assert Scatter(X, Y).log == LogAxes(False, False)
    assert Scatter(X, Y).labels == labels("x", "y", None, None, None)
    assert Scatter(X, Y, Z).labels == labels("x", "y", "z", None, None)
    assert Scatter(X, Y, size=Z, alpha=Z).labels == labels(
        "x", "y", None, "size", "alpha"
    )
    assert Scatter(X, Y).clip == ClipAxes(x=False, y=False, z=False)


def test_points_handed_to_matplotlib_are_the_complete_rows(ax):
    """Offsets are (x, y) of every row with no NaN, in input order.

    ON FAILURE: the code is wrong.
    """
    Scatter(X, Y, Z).make_plot(ax=ax)
    offsets = ax.collections[0].get_offsets()
    np.testing.assert_array_equal(offsets, np.c_[_col(KEPT, 1), _col(KEPT, 2)])


def test_varying_z_colours_points_and_draws_a_labelled_colorbar(ax):
    """Colour array is z row for row; the colorbar maps it and shows labels.z.

    ON FAILURE: the code is wrong.
    """
    sc = Scatter(X, Y, Z)
    sc.set_labels(x="Vx", y="Np", z="T")
    ret_ax, _, _, guides = sc.make_plot(ax=ax)
    coll = ax.collections[0]
    np.testing.assert_array_equal(coll.get_array(), _col(KEPT, 3))
    assert ret_ax is ax
    assert isinstance(guides.color, Colorbar)
    assert guides.color.mappable is coll
    assert guides.color.ax.get_ylabel() == "T"
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("Vx", "Np")


def test_two_valued_z_is_colour_mapped_with_a_colorbar(ax):
    """A z holding exactly two values is data: points are coloured, with a colorbar.

    Only a single z value means "no z"; two values already vary.

    ON FAILURE: the code is wrong.
    """
    z = pd.Series([0.5, 0.5, 0.9, 0.9, 0.5, 0.9])
    _, _, _, guides = Scatter(X, Y, z).make_plot(ax=ax)
    kept_z = z.drop(1).to_numpy()  # row 1 has NaN y (ROWS)
    np.testing.assert_array_equal(ax.collections[0].get_array(), kept_z)
    assert isinstance(guides.color, Colorbar)


@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=X.index)])
def test_absent_or_constant_z_gives_uncoloured_points_and_no_colorbar(ax, z):
    """With no z, or one z value for every point, nothing is colour-mapped.

    ON FAILURE: the code is wrong.
    """
    _, _, _, guides = Scatter(X, Y, z).make_plot(ax=ax)
    assert ax.collections[0].get_array() is None
    assert guides.color is None
    assert ax.figure.axes == [ax]


def test_cbar_false_colours_points_but_draws_no_colorbar(ax):
    """``cbar=False`` keeps the colour mapping and skips the colorbar.

    ON FAILURE: the code is wrong.
    """
    _, _, _, guides = Scatter(X, Y, Z).make_plot(ax=ax, cbar=False)
    np.testing.assert_array_equal(ax.collections[0].get_array(), _col(KEPT, 3))
    assert guides.color is None
    assert ax.figure.axes == [ax]


def test_without_ax_a_new_figure_is_made():
    """``ax=None`` plots on fresh axes in a new figure (docstring).

    ON FAILURE: the code is wrong.
    """
    existing, _ = plt.subplots()
    try:
        new_ax, _, _, _ = Scatter(X, Y).make_plot()
        assert isinstance(new_ax, Axes)
        assert new_ax.figure is not existing
        assert len(new_ax.collections) == 1
        assert len(existing.axes[0].collections) == 0
    finally:
        plt.close("all")


def test_extra_keywords_reach_ax_scatter(ax):
    """Keywords like ``s`` and ``alpha`` are passed through to matplotlib.

    ON FAILURE: the code is wrong.
    """
    Scatter(X, Y).make_plot(ax=ax, s=50.0, alpha=0.3)
    coll = ax.collections[0]
    np.testing.assert_array_equal(coll.get_sizes(), [50.0])
    assert coll.get_alpha() == 0.3


def test_cbar_kwargs_reach_the_colorbar(ax):
    """``cbar_kwargs`` routes the colorbar to ``cax`` with a custom label.

    ON FAILURE: the code is wrong.
    """
    cax = ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))
    _, _, _, guides = Scatter(X, Y, Z).make_plot(
        ax=ax, cbar_kwargs={"cax": cax, "label": "custom"}
    )
    assert guides.color.ax is cax
    assert cax.get_ylabel() == "custom"


def test_cbar_kwargs_with_ax_and_cax_raise_value_error(ax):
    """Passing both ``ax`` and ``cax`` for the colorbar is refused.

    ON FAILURE: the code is wrong.
    """
    cax = ax.figure.add_axes((0.9, 0.1, 0.03, 0.8))
    with pytest.raises(ValueError, match="Can't pass ax and cax"):
        Scatter(X, Y, Z).make_plot(ax=ax, cbar_kwargs={"ax": ax, "cax": cax})


def test_axis_limits_hug_the_plotted_points(ax):
    """Limits are the kept data's min and max; dropped rows do not widen them.

    ON FAILURE: the code is wrong.
    """
    Scatter(X, Y, Z).make_plot(ax=ax)
    xs, ys = _col(KEPT, 1), _col(KEPT, 2)
    assert ax.get_xlim() == (xs.min(), xs.max())
    assert ax.get_ylim() == (ys.min(), ys.max())


@pytest.mark.parametrize(
    "axis, expected",
    [("x", ("log", "linear")), ("y", ("linear", "log"))],
)
def test_set_log_makes_the_plotted_axis_logarithmic(ax, axis, expected):
    """``set_log(<axis>=True)`` makes that axis log and leaves the other linear.

    ON FAILURE: the code is wrong.
    """
    sc = Scatter(X, Y)
    sc.set_log(**{axis: True})
    sc.make_plot(ax=ax)
    assert (ax.get_xscale(), ax.get_yscale()) == expected


def test_list_inputs_plot_the_same_points_as_series(ax):
    """Plain lists are accepted and plotted as the equivalent Series.

    The lists are ``ROWS``, so they carry a NaN in y and a NaN in z; as with
    Series, both rows are dropped and the offsets are the complete rows.

    ON FAILURE: the code is wrong.
    """
    Scatter(list(X), list(Y), list(Z)).make_plot(ax=ax)
    np.testing.assert_array_equal(
        ax.collections[0].get_offsets(), np.c_[_col(KEPT, 1), _col(KEPT, 2)]
    )
    np.testing.assert_array_equal(ax.collections[0].get_array(), _col(KEPT, 3))


class CbarKwargsMutated(AssertionError):
    """A second plot's colorbar went to the axes of an earlier plot."""


def test_reused_cbar_kwargs_put_each_colorbar_beside_its_own_axes():
    """One ``cbar_kwargs`` dict reused for two plots: each gets its colorbar.

    ON FAILURE: the code is wrong.
    """
    kwargs = {"shrink": 0.5}
    _, ax1 = plt.subplots()
    _, ax2 = plt.subplots()
    try:
        Scatter(X, Y, Z).make_plot(ax=ax1, cbar_kwargs=kwargs)
        # The defect makes matplotlib warn about a cross-figure colorbar; keep
        # that warning from pre-empting the assertion under ``-W error``.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            _, _, _, guides2 = Scatter(X, Y, Z).make_plot(ax=ax2, cbar_kwargs=kwargs)
        if guides2.color.ax.figure is not ax2.figure:
            raise CbarKwargsMutated("second colorbar drawn in the first plot's figure")
    finally:
        plt.close("all")


# ---------------------------------------------------------------------------
# alim: hand-built points whose z is known, x and y distinct per point so the
# offsets identify which points were drawn. The last z is +inf: a quantile
# limit must ignore it when computing thresholds.
# ---------------------------------------------------------------------------

ALIM_Z = np.array([5.0, 1.0, 8.0, 3.0, 9.0, 2.0, 7.0, 4.0, 6.0, 0.0, np.inf])
ALIM_X = np.arange(ALIM_Z.size, dtype=float)
ALIM_Y = 10.0 * ALIM_X + 1.0


def _assert_drawn(ax, cbar, keep):
    keep = np.r_[keep, np.zeros(ALIM_Z.size - keep.size, dtype=bool)]
    coll = ax.collections[0]
    np.testing.assert_array_equal(coll.get_offsets(), np.c_[ALIM_X[keep], ALIM_Y[keep]])
    np.testing.assert_array_equal(coll.get_array(), ALIM_Z[keep])
    assert (cbar.mappable.norm.vmin, cbar.mappable.norm.vmax) == (
        ALIM_Z[keep].min(),
        ALIM_Z[keep].max(),
    )
    assert ax.get_xlim() == (ALIM_X[keep].min(), ALIM_X[keep].max())


@pytest.mark.parametrize(
    "lower, upper",
    [(3.0, 7.0), (3.0, None), (None, 7.0)],
    ids=["both", "lower", "upper"],
)
def test_value_alim_draws_only_points_with_z_inside_the_limits(ax, lower, upper):
    """``set_alim(lo, hi)`` draws a point iff lo <= z <= hi; bounds inclusive.

    Masked points are absent from the offsets, the colour array, the colour
    scale and the axis limits. Only the finite points are used here.
    ON FAILURE: the code is wrong.
    """
    z = ALIM_Z[:-1]
    sc = Scatter(ALIM_X[:-1], ALIM_Y[:-1], z)
    sc.set_alim(lower, upper)
    _, _, _, guides = sc.make_plot(ax=ax)
    keep = np.ones(z.size, dtype=bool)
    if lower is not None:
        keep &= z >= lower
    if upper is not None:
        keep &= z <= upper
    _assert_drawn(ax, guides.color, keep)


def test_quantile_alim_thresholds_are_quantiles_of_the_finite_plotted_z(ax):
    """``kind="quantile"`` masks z outside np.quantile of the finite z.

    The +inf z is excluded from the quantile computation and, being above the
    upper threshold, is not drawn.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter(ALIM_X, ALIM_Y, ALIM_Z)
    sc.set_alim(0.2, 0.8, kind="quantile")
    _, _, _, guides = sc.make_plot(ax=ax)
    lo, hi = np.quantile(ALIM_Z[np.isfinite(ALIM_Z)], [0.2, 0.8])
    keep = (ALIM_Z >= lo) & (ALIM_Z <= hi)
    assert 2 < keep.sum() < ALIM_Z.size - 2
    _assert_drawn(ax, guides.color, keep)


def test_quantile_alim_of_zero_is_the_smallest_finite_z(ax):
    """A quantile limit of 0 is allowed and keeps the smallest finite z.

    ``set_alim`` documents quantiles in [0, 1], bounds inclusive; the 0th
    quantile of the finite z is their minimum, 0.0 in ``ALIM_Z``.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter(ALIM_X, ALIM_Y, ALIM_Z)
    sc.set_alim(0.0, 0.5, kind="quantile")
    _, _, _, guides = sc.make_plot(ax=ax)
    hi = np.quantile(ALIM_Z[np.isfinite(ALIM_Z)], 0.5)
    _assert_drawn(ax, guides.color, ALIM_Z <= hi)


def test_quantile_alim_with_one_finite_z_still_masks_the_infinite_ones(ax):
    """With one finite z, its quantiles are that value, and +inf lies above them.

    Points 1 and 2 have z = +inf, outside every quantile limit of the finite
    z, which is [1.0]; only point 0 is drawn.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter([0.0, 1.0, 2.0], [5.0, 6.0, 7.0], [1.0, np.inf, np.inf])
    sc.set_alim(None, 0.5, kind="quantile")
    sc.make_plot(ax=ax)
    np.testing.assert_array_equal(ax.collections[0].get_offsets(), [[0.0, 5.0]])


@pytest.mark.parametrize("clip", ["l", "u"])
def test_one_tailed_clip_clips_only_that_tail(ax, clip):
    """``"l"`` clips only the low tail of each column, ``"u"`` only the high.

    The input is 0..10000 with one far outlier on each end. The clipped tail
    is raised or lowered to numpy's 0.01st or 99.99th percentile; the other
    tail, outlier included, is drawn unchanged.
    ON FAILURE: the code is wrong.
    """
    raw = np.concatenate([[-1e6], np.arange(10001.0), [1e6]])
    Scatter(pd.Series(raw), pd.Series(raw), clip=clip).make_plot(ax=ax)
    # Percentiles from the Base.clip_data docstring.
    if clip == "l":
        expected = np.clip(raw, np.quantile(raw, 1e-4), None)
        assert expected[-1] == 1e6
    else:
        expected = np.clip(raw, None, np.quantile(raw, 1 - 1e-4))
        assert expected[0] == -1e6
    np.testing.assert_array_equal(
        np.asarray(ax.collections[0].get_offsets()), np.c_[expected, expected]
    )


def test_scatter_figure_renders_to_png():
    """A coloured scatter with its colorbar renders to an in-memory PNG.

    Building artists does not run every matplotlib check; rendering does.
    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    try:
        Scatter(X, Y, Z).make_plot(ax=ax)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png")
    finally:
        plt.close("all")
    assert buffer.getvalue().startswith(b"\x89PNG\r\n\x1a\n")  # PNG signature


# ---------------------------------------------------------------------------
# connect: line segments joining the drawn points in increasing z, row order
# without a varying z. EZ is not sorted, so z order differs from row order:
# rows by increasing z are 0, 1, 3, 4, 2, and each segment's mean z is
# distinct.
# ---------------------------------------------------------------------------

EX = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
EY = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
EZ = np.array([0.0, 2.0, 9.0, 6.0, 8.0])
Z_ORDER = [(0, 1), (1, 3), (3, 4), (4, 2)]


def _segments(x, y, pairs):
    return [np.array([[x[i], y[i]], [x[j], y[j]]]) for i, j in pairs]


def _assert_segments(lc, x, y, pairs):
    got = lc.get_segments()
    assert len(got) == len(pairs)
    for g, e in zip(got, _segments(x, y, pairs)):
        np.testing.assert_array_equal(g, e)


def _mean_z(z, pairs):
    return [(z[i] + z[j]) / 2 for i, j in pairs]


def test_make_plot_returns_ax_points_segments_then_guides(ax):
    """``(ax, points, segments, guides)``; segments is None unless ``connect=True``.

    ON FAILURE: the code is wrong.
    """
    out = Scatter(EX, EY, EZ).make_plot(ax=ax)
    assert len(out) == 4
    assert out[0] is ax
    assert isinstance(out[1], PathCollection)
    assert out[2] is None
    assert isinstance(out[3].color, Colorbar)
    assert not any(isinstance(c, LineCollection) for c in ax.collections)

    out = Scatter(EX, EY, EZ).make_plot(ax=ax, connect=True)
    assert len(out) == 4
    assert isinstance(out[2], LineCollection)
    assert out[2] in ax.collections


def test_connect_joins_the_points_in_increasing_z(ax):
    """n drawn points give n - 1 segments, each to the point next in z.

    ON FAILURE: the code is wrong.
    """
    _, _, lc, _ = Scatter(EX, EY, EZ).make_plot(ax=ax, connect=True)
    _assert_segments(lc, EX, EY, Z_ORDER)


def test_connect_does_not_depend_on_row_order(ax):
    """Shuffled rows, with shuffled labels, give the same segments in z order.

    ON FAILURE: the code is wrong.
    """
    perm = np.array([3, 0, 4, 2, 1])
    x, y, z = (pd.Series(v[perm], index=perm[::-1]) for v in (EX, EY, EZ))
    _, _, lc, _ = Scatter(x, y, z).make_plot(ax=ax, connect=True)
    _assert_segments(lc, EX, EY, Z_ORDER)
    np.testing.assert_array_equal(lc.get_array(), _mean_z(EZ, Z_ORDER))


def test_points_with_equal_z_keep_their_row_order(ax):
    """The sort on z is stable: tied points are joined in the order given.

    ON FAILURE: the code is wrong.
    """
    z = np.array([1.0, 0.0, 1.0, 0.0, 2.0])
    _, _, lc, _ = Scatter(EX, EY, z).make_plot(ax=ax, connect=True)
    _assert_segments(lc, EX, EY, [(1, 3), (3, 0), (0, 2), (2, 4)])


def test_segment_colour_is_the_mean_endpoint_z_through_the_points_cmap_and_norm(
    ax,
):
    """A segment is ``cmap(norm((z_a + z_b) / 2))``: one colorbar serves both.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, guides = Scatter(EX, EY, EZ).make_plot(
        ax=ax, connect=True, cmap="plasma"
    )
    mean = _mean_z(EZ, Z_ORDER)
    np.testing.assert_array_equal(lc.get_array(), mean)
    assert lc.norm is points.norm
    assert lc.get_cmap() is points.get_cmap()
    assert (points.norm.vmin, points.norm.vmax) == (EZ.min(), EZ.max())
    lc.update_scalarmappable()
    expected = points.get_cmap()(points.norm(mean))
    np.testing.assert_allclose(lc.get_edgecolor(), expected)
    assert guides.color.mappable is points


def test_segments_follow_a_norm_the_caller_passes(ax):
    """``vmin``/``vmax`` given to the points also set the segments' colours.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, _ = Scatter(EX, EY, EZ).make_plot(
        ax=ax, connect=True, vmin=0.0, vmax=20.0
    )
    assert lc.norm is points.norm
    assert (lc.norm.vmin, lc.norm.vmax) == (0.0, 20.0)


def _nan_y_at_3():
    y = EY.copy()
    y[3] = np.nan
    return Scatter(EX, y, EZ), EX, y


def _alim_hides_2():
    sc = Scatter(EX, EY, EZ)
    sc.set_alim(None, 8.0)
    return sc, EX, EY


def _mask_drops_1():
    mask = pd.Series([True, False, True, True, True])
    return Scatter(EX, EY, EZ, mask=mask), EX, EY


def _log_x_drops_3():
    x = EX + 1.0
    x[3] = -1.0
    sc = Scatter(x, EY, EZ)
    sc.set_log(x=True)
    return sc, x, EY


@pytest.mark.parametrize(
    "build, pairs",
    [
        (_nan_y_at_3, [(0, 1), (1, 4), (4, 2)]),
        (_alim_hides_2, [(0, 1), (1, 3), (3, 4)]),
        (_mask_drops_1, [(0, 3), (3, 4), (4, 2)]),
        (_log_x_drops_3, [(0, 1), (1, 4), (4, 2)]),
    ],
    ids=["nan", "alim", "mask", "log-nonpositive"],
)
def test_a_point_not_drawn_is_skipped_not_a_gap(ax, build, pairs):
    """A point that is not drawn is left out: its z neighbours are joined.

    ON FAILURE: the code is wrong.
    """
    sc, x, y = build()
    _, _, lc, _ = sc.make_plot(ax=ax, connect=True)
    _assert_segments(lc, x, y, pairs)
    np.testing.assert_array_equal(lc.get_array(), _mean_z(EZ, pairs))


@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=range(EX.size))])
def test_without_varying_z_points_are_joined_in_row_order_in_one_colour(ax, z):
    """With no z, or a constant one, segments follow the rows, in the points' colour.

    A point that is not drawn (here a NaN y) is skipped there too.
    ON FAILURE: the code is wrong.
    """
    y = EY.copy()
    y[2] = np.nan
    _, points, lc, guides = Scatter(EX, y, z).make_plot(ax=ax, connect=True)
    assert guides.color is None
    assert lc.get_array() is None
    _assert_segments(lc, EX, y, [(0, 1), (1, 3), (3, 4)])
    colors = lc.get_edgecolor()
    assert len(colors) == 1
    np.testing.assert_array_equal(colors[0], points.get_facecolor()[0])


def test_segments_sit_below_the_points_and_take_connect_kwargs(ax):
    """Segments default to beneath the markers; ``connect_kwargs`` styles them.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, _ = Scatter(EX, EY, EZ).make_plot(ax=ax, connect=True)
    assert lc.get_zorder() < points.get_zorder()

    kwargs = {"linewidth": 3.0, "alpha": 0.4, "zorder": 5}
    _, _, lc, _ = Scatter(EX, EY, EZ).make_plot(
        ax=ax, connect=True, connect_kwargs=kwargs
    )
    assert kwargs == {"linewidth": 3.0, "alpha": 0.4, "zorder": 5}
    np.testing.assert_array_equal(lc.get_linewidth(), [3.0])
    assert (lc.get_alpha(), lc.get_zorder()) == (0.4, 5)


def test_segments_do_not_change_the_axis_limits(ax):
    """The view fits the points with or without segments.

    ON FAILURE: the code is wrong.
    """
    Scatter(EX, EY, EZ).make_plot(ax=ax, connect=True)
    assert ax.get_xlim() == (EX.min(), EX.max())
    assert ax.get_ylim() == (EY.min(), EY.max())


# ---------------------------------------------------------------------------
# A colour in connect_kwargs: with a varying z the segments are colour-mapped,
# so the colour is dropped with a warning naming the key the caller typed;
# otherwise it is the segments' one colour, under any of its spellings.
# ---------------------------------------------------------------------------

COLOR_KEYS = ["color", "c", "colors", "edgecolor", "edgecolors", "ec"]


@pytest.mark.parametrize("key", COLOR_KEYS)
def test_connect_colour_with_varying_z_warns_and_is_ignored(ax, key):
    """With a varying z the segments keep the colormap; the colour key is named.

    ON FAILURE: the code is wrong.
    """
    kwargs = {key: "red"}
    with pytest.warns(UserWarning, match=rf"connect_kwargs\['{key}'\]") as record:
        _, points, lc, _ = Scatter(EX, EY, EZ).make_plot(
            ax=ax, connect=True, connect_kwargs=kwargs
        )
    assert kwargs == {key: "red"}
    assert len(record) == 1
    assert record[0].filename == __file__
    assert "colormap" in str(record[0].message)
    ax.figure.canvas.draw()
    expected = points.get_cmap()(points.norm(_mean_z(EZ, Z_ORDER)))
    np.testing.assert_allclose(lc.get_edgecolor(), expected)


@pytest.mark.parametrize("key", COLOR_KEYS)
@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=range(EX.size))])
def test_connect_colour_without_varying_z_is_honoured(ax, key, z):
    """With no z, or a constant one, every spelling of the colour sets the segments'.

    ON FAILURE: the code is wrong.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, _, lc, _ = Scatter(EX, EY, z).make_plot(
            ax=ax, connect=True, connect_kwargs={key: "red"}
        )
    ax.figure.canvas.draw()
    np.testing.assert_array_equal(lc.get_edgecolor(), [[1.0, 0.0, 0.0, 1.0]])


@pytest.mark.parametrize("z", [None, EZ])
def test_connect_without_a_colour_key_does_not_warn(ax, z):
    """Styling the segments without a colour issues no warning.

    ON FAILURE: the code is wrong.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Scatter(EX, EY, z).make_plot(
            ax=ax, connect=True, connect_kwargs={"linewidth": 2.0}
        )


def test_connect_refuses_two_colour_keys(ax):
    """Two spellings of the colour are ambiguous, as matplotlib's aliases are.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="'color'.*'ec'"):
        Scatter(EX, EY).make_plot(
            ax=ax, connect=True, connect_kwargs={"color": "red", "ec": "blue"}
        )


# ---------------------------------------------------------------------------
# size and alpha variables: a SizeScale or AlphaScale maps each drawn value to
# f = norm(value), clipped to [0, 1], then ``lo + f * (hi - lo)`` gives the
# marker area (pt^2) or alpha, with (lo, hi) the scale's ``range``. Expected
# values are hand computed from the chosen inputs on each line.
# ---------------------------------------------------------------------------

SX = np.array([0.0, 1.0, 2.0])
SY = np.array([5.0, 6.0, 7.0])


@XFAIL_F
def test_size_maps_linearly_onto_the_size_scales_range(ax):
    """size 1, 2, 3 autoscale to f = 0, 1/2, 1, so areas 10, 20, 30 on (10, 30).

    ON FAILURE: the code is wrong.
    """
    _, points, _, _ = Scatter(SX, SY, size=[1.0, 2.0, 3.0]).make_plot(
        ax=ax, size_scale=scales.SizeScale(range=(10, 30))
    )
    assert points.get_sizes().tolist() == exact([10.0, 20.0, 30.0])


@XFAIL_F
@pytest.mark.parametrize(
    "ends, expected",
    [
        ((0.2, 1.0), [0.2, 0.6, 1.0]),  # 0.2 + (0, 1/2, 1) * 0.8
        ((1.0, 0.2), [1.0, 0.6, 0.2]),  # reversed: 1 + (0, 1/2, 1) * -0.8
    ],
)
def test_alpha_maps_linearly_onto_the_alpha_scales_range_and_a_reversed_range_inverts(
    ax, ends, expected
):
    """alpha 0, 5, 10 autoscale to f = 0, 1/2, 1; a reversed range fades high values.

    ON FAILURE: the code is wrong.
    """
    _, points, _, _ = Scatter(SX, SY, alpha=[0.0, 5.0, 10.0]).make_plot(
        ax=ax, alpha_scale=scales.AlphaScale(range=ends)
    )
    assert points.get_alpha().tolist() == exact(expected)


@XFAIL_F
def test_a_scales_norm_is_used_and_a_value_it_masks_is_not_drawn(ax):
    """LogNorm puts 1, 10, 100 at f = 0, 1/2, 1; it masks 0, so that point is not drawn.

    The undrawn point's alpha, 100, does not enter the alpha norm either: the
    drawn alphas 0, 5, 10 autoscale to 0.2, 0.6, 1 on (0.2, 1).

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([4.0, 5.0, 6.0, 7.0])
    sc = Scatter(x, y, size=[0.0, 1.0, 10.0, 100.0], alpha=[100.0, 0.0, 5.0, 10.0])
    _, points, _, _ = sc.make_plot(
        ax=ax,
        size_scale=scales.SizeScale(norm=LogNorm(), range=(10, 30)),
        alpha_scale=scales.AlphaScale(range=(0.2, 1.0)),
    )
    assert points.get_sizes().tolist() == exact([10.0, 20.0, 30.0])
    assert points.get_alpha().tolist() == exact([0.2, 0.6, 1.0])
    np.testing.assert_array_equal(points.get_offsets(), np.c_[x[1:], y[1:]])


@XFAIL_F
def test_values_outside_the_norms_limits_saturate_at_the_range_ends(ax):
    """With vmin 1 and vmax 3, -5 lands on 10 and 50 on 30, as 1 and 3 do.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(5.0)
    scale = scales.SizeScale(norm=Normalize(vmin=1, vmax=3), range=(10, 30))
    _, points, _, _ = Scatter(x, x, size=[-5.0, 1.0, 2.0, 3.0, 50.0]).make_plot(
        ax=ax, size_scale=scale
    )
    assert points.get_sizes().tolist() == exact([10.0, 10.0, 20.0, 30.0, 30.0])


def test_default_ranges_put_the_extreme_drawn_values_at_9_144_and_0p15_1(ax):
    """Defaults: area 9 to 144 pt^2 (marker 3 to 12 pt), alpha 0.15 to 1.

    The midpoint gives (9 + 144) / 2 = 76.5 and (0.15 + 1) / 2 = 0.575.
    ON FAILURE: the code is wrong, unless the author changes the defaults.
    """
    v = [1.0, 2.0, 3.0]
    _, points, _, _ = Scatter(SX, SY, size=v, alpha=v).make_plot(ax=ax)
    assert points.get_sizes().tolist() == exact([9.0, 76.5, 144.0])
    assert points.get_alpha().tolist() == exact([0.15, 0.575, 1.0])


def test_size_aligns_by_label_and_a_nan_drops_its_point(ax):
    """size is aligned to x and y by label; the row whose size is NaN is not drawn.

    size labelled 2, 1, 0 holds 3, NaN, 1: row 0 is smallest (9 pt^2), row 2
    largest (144 pt^2).
    ON FAILURE: the code is wrong.
    """
    size = pd.Series([3.0, np.nan, 1.0], index=[2, 1, 0])
    sc = Scatter(pd.Series(SX), pd.Series(SY), size=size)
    _, points, _, _ = sc.make_plot(ax=ax)
    np.testing.assert_array_equal(points.get_offsets(), np.c_[SX[[0, 2]], SY[[0, 2]]])
    assert points.get_sizes().tolist() == exact([9.0, 144.0])
    assert "size" in sc.data.columns
    assert "alpha" not in sc.data.columns


@XFAIL_F
def test_size_key_marker_areas_are_the_areas_points_get_at_its_values(ax):
    """Key entries at 1, 10, 100 have the areas the points of size 1, 10, 100 get.

    LogNorm over 1 to 100 on (10, 30) gives 10, 20, 30 pt^2. The key is an
    opaque Legend on ``ax``, labelled with the values, and takes ``key_kwargs``.

    ON FAILURE: the code is wrong.
    """
    scale = scales.SizeScale(
        norm=LogNorm(), range=(10, 30), key=[1, 10, 100], key_kwargs={"frameon": False}
    )
    _, points, _, guides = Scatter(SX, SY, size=[1.0, 10.0, 100.0]).make_plot(
        ax=ax, size_scale=scale
    )
    key = guides.size
    areas = [h.get_markersize() ** 2 for h in key.legend_handles]
    assert areas == exact(points.get_sizes().tolist())
    assert areas == exact([10.0, 20.0, 30.0])
    assert [t.get_text() for t in key.get_texts()] == ["1", "10", "100"]
    assert [h.get_alpha() for h in key.legend_handles] == [1, 1, 1]
    assert ax.get_legend() is key
    assert key.get_frame_on() is False


@XFAIL_F
@pytest.mark.parametrize(
    "norm, size, expected",
    [
        # 1.5 to 40 holds one decade, 10, so the 1-2-5 steps within it.
        (LogNorm, [1.5, 40.0], [2.0, 5.0, 10.0, 20.0]),
        # MaxNLocator(4) over 0 to 1 steps by 0.25.
        (Normalize, [0.0, 1.0], [0.0, 0.25, 0.5, 0.75, 1.0]),
    ],
    ids=["LogNorm", "Normalize"],
)
def test_automatic_size_key_steps_through_the_norms_limits(ax, norm, size, expected):
    """``key=True`` picks round values between the norm's autoscaled vmin and vmax.

    ON FAILURE: the code is wrong, unless the author changes the documented rule.
    """
    scale = scales.SizeScale(norm=norm())
    _, _, _, guides = Scatter(SX[:2], SY[:2], size=size).make_plot(
        ax=ax, size_scale=scale
    )
    assert [float(t.get_text()) for t in guides.size.get_texts()] == exact(expected)


@XFAIL_F
@pytest.mark.parametrize("z", [None, [1.0, 2.0, 3.0]], ids=["no-z", "z"])
def test_alpha_bar_ramps_one_colour_over_the_range_on_the_scales_norm(ax, z):
    """The alpha bar reads the scale's norm through one colour whose alpha runs lo to hi.

    The colour is black when z colours the points, else the points' own.

    ON FAILURE: the code is wrong.
    """
    scale = scales.AlphaScale(norm=Normalize(0, 10), range=(0.3, 0.9))
    sc = Scatter(SX, SY, z, alpha=[0.0, 5.0, 10.0])
    _, points, _, guides = sc.make_plot(ax=ax, alpha_scale=scale)
    bar = guides.alpha
    assert bar.norm is scale.norm
    low, high = bar.cmap(0.0), bar.cmap(1.0)
    assert (low[3], high[3]) == exact((0.3, 0.9))
    rgb = (0.0, 0.0, 0.0) if z else to_rgb(points.get_facecolor()[0])
    assert low[:3] == high[:3] == exact(rgb)
    assert (guides.color is None) == (z is None)


@XFAIL_F
def test_draw_order_sorts_the_drawn_points_by_marker_value_not_the_segments():
    """draw_order sorts by area or opacity; segments keep row order.

    alpha 1, 2, 3 on the reversed range (1, 0.15) gives opacities 1, 0.575,
    0.15, so ascending opacity draws rows 2, 1, 0: the order of the marker
    value, not of the data. size 3, 1, 2 ascending draws rows 1, 2, 0.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    faint_last = scales.AlphaScale(range=(1, 0.15))
    cases = [
        ({"alpha": [1.0, 2.0, 3.0]}, {"draw_order": "alpha"}, [2, 1, 0]),
        (
            {"alpha": [1.0, 2.0, 3.0]},
            {"draw_order": "alpha", "draw_ascending": False},
            [0, 1, 2],
        ),
        ({"size": [3.0, 1.0, 2.0]}, {"draw_order": "size", "connect": True}, [1, 2, 0]),
        ({"size": [3.0, 1.0, 2.0]}, {}, [0, 1, 2]),
    ]
    for variables, order, rows in cases:
        _, axis = plt.subplots()
        scale = {"alpha_scale": faint_last} if "alpha" in variables else {}
        _, points, segments, _ = Scatter(x, SY, **variables).make_plot(
            ax=axis, **scale, **order
        )
        np.testing.assert_array_equal(points.get_offsets(), np.c_[x[rows], SY[rows]])
        if segments is not None:
            _assert_segments(segments, x, SY, [(0, 1), (1, 2)])
    plt.close("all")


@XFAIL_F
def test_size_and_alpha_labels_title_the_key_and_the_alpha_bar_and_join_the_path(ax):
    """``set_labels(size=, alpha=)`` titles the key and labels the bar; ``path`` gains both.

    ON FAILURE: the code is wrong.
    """
    n = TeXlabel(("n", "", "p1"))
    spread = ManualLabel(r"\delta w / w", "dimless")
    sc = Scatter(SX, SY, size=[1.0, 2.0, 3.0], alpha=[1.0, 2.0, 3.0])
    sc.set_labels(size=n, alpha=spread)
    _, _, _, guides = sc.make_plot(ax=ax)
    assert guides.size.get_title().get_text() == str(n)
    assert guides.alpha.ax.get_ylabel() == str(spread)
    assert sc.path == Path("Scatter", "x", "y", n.path, spread.path, "linX-linY")
    with pytest.warns(PlainStringLabelWarning, match="size='n'"):
        sc.set_labels(size="n")
    unlabelled = Scatter(SX, SY, size=[1.0, 2.0, 3.0], alpha=[1.0, 2.0, 3.0])
    assert unlabelled.path == Path("Scatter", "x", "y", "size", "alpha", "linX-linY")


@pytest.mark.parametrize(
    "variables, plot_kwargs, error, match",
    [
        ({"size": [1.0, 2.0, 3.0]}, {"s": 20.0}, TypeError, r"s= .*size variable"),
        (
            {"alpha": [1.0, 2.0, 3.0]},
            {"alpha": 0.5},
            TypeError,
            r"alpha= .*alpha variable",
        ),
        pytest.param(
            {},
            {"size_scale": "SizeScale"},
            TypeError,
            r"size_scale .*without a size variable",
            marks=XFAIL_F,
        ),
        pytest.param(
            {},
            {"alpha_scale": "AlphaScale"},
            TypeError,
            r"alpha_scale .*without an alpha variable",
            marks=XFAIL_F,
        ),
        pytest.param(
            {"size": [1.0, 2.0, 3.0]},
            {"size_scale": "AlphaScale"},
            TypeError,
            r"size_scale must be a SizeScale",
            marks=XFAIL_F,
        ),
        pytest.param(
            {"alpha": [1.0, 2.0, 3.0]},
            {"connect": True},
            TypeError,
            r"connect=True .*alpha variable",
            marks=pytest.mark.xfail(
                strict=True,
                reason="the interim Scatter joins points with an alpha variable; "
                "DID NOT RAISE; remove this marker when Stage F lands",
            ),
        ),
        pytest.param(
            {},
            {"draw_order": "alpha"},
            TypeError,
            r"draw_order='alpha' .*without an alpha variable",
            marks=XFAIL_F,
        ),
        pytest.param(
            {"size": [1.0, 2.0, 3.0]},
            {"draw_order": "area"},
            ValueError,
            r"draw_order must be None, 'size' or 'alpha'",
            marks=XFAIL_F,
        ),
    ],
    ids=[
        "s",
        "alpha",
        "orphan-size_scale",
        "orphan-alpha_scale",
        "wrong-scale",
        "connect-alpha",
        "orphan-draw_order",
        "unknown-draw_order",
    ],
)
def test_conflicting_or_orphaned_size_and_alpha_settings_raise(
    ax, variables, plot_kwargs, error, match
):
    """``s=``/``alpha=`` beside their variable, a scale or draw_order without one, raise.

    Also ``connect=True`` with an alpha variable, a scale of the other
    channel, and a draw_order naming no channel.

    ON FAILURE: the code is wrong.
    """
    kwargs = {
        k: getattr(scales, v)() if k.endswith("_scale") else v
        for k, v in plot_kwargs.items()
    }
    with pytest.raises(error, match=match):
        Scatter(SX, SY, **variables).make_plot(ax=ax, **kwargs)
