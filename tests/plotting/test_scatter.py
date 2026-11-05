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

from solarwindpy.plotting.base import AxesLabels, ClipAxes, LogAxes  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402

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


def test_new_scatter_has_linear_axes_and_default_labels():
    """Defaults: linear axes, labels x and y, z labelled only when z is given.

    ON FAILURE: the code is wrong.
    """
    assert Scatter(X, Y).log == LogAxes(False, False)
    assert Scatter(X, Y).labels == AxesLabels("x", "y", None)
    assert Scatter(X, Y, Z).labels == AxesLabels("x", "y", "z")
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
    ret_ax, _, _, cbar = sc.make_plot(ax=ax)
    coll = ax.collections[0]
    np.testing.assert_array_equal(coll.get_array(), _col(KEPT, 3))
    assert ret_ax is ax
    assert isinstance(cbar, Colorbar)
    assert cbar.mappable is coll
    assert cbar.ax.get_ylabel() == "T"
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("Vx", "Np")


def test_two_valued_z_is_colour_mapped_with_a_colorbar(ax):
    """A z holding exactly two values is data: points are coloured, with a colorbar.

    Only a single z value means "no z"; two values already vary.

    ON FAILURE: the code is wrong.
    """
    z = pd.Series([0.5, 0.5, 0.9, 0.9, 0.5, 0.9])
    _, _, _, cbar = Scatter(X, Y, z).make_plot(ax=ax)
    kept_z = z.drop(1).to_numpy()  # row 1 has NaN y (ROWS)
    np.testing.assert_array_equal(ax.collections[0].get_array(), kept_z)
    assert isinstance(cbar, Colorbar)


@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=X.index)])
def test_absent_or_constant_z_gives_uncoloured_points_and_no_colorbar(ax, z):
    """With no z, or one z value for every point, nothing is colour-mapped.

    ON FAILURE: the code is wrong.
    """
    _, _, _, cbar = Scatter(X, Y, z).make_plot(ax=ax)
    assert ax.collections[0].get_array() is None
    assert cbar is None
    assert ax.figure.axes == [ax]


def test_cbar_false_colours_points_but_draws_no_colorbar(ax):
    """``cbar=False`` keeps the colour mapping and skips the colorbar.

    ON FAILURE: the code is wrong.
    """
    _, _, _, cbar = Scatter(X, Y, Z).make_plot(ax=ax, cbar=False)
    np.testing.assert_array_equal(ax.collections[0].get_array(), _col(KEPT, 3))
    assert cbar is None
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
    _, _, _, cbar = Scatter(X, Y, Z).make_plot(
        ax=ax, cbar_kwargs={"cax": cax, "label": "custom"}
    )
    assert cbar.ax is cax
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
            _, _, _, cbar2 = Scatter(X, Y, Z).make_plot(ax=ax2, cbar_kwargs=kwargs)
        if cbar2.ax.figure is not ax2.figure:
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
    _, _, _, cbar = sc.make_plot(ax=ax)
    keep = np.ones(z.size, dtype=bool)
    if lower is not None:
        keep &= z >= lower
    if upper is not None:
        keep &= z <= upper
    _assert_drawn(ax, cbar, keep)


def test_quantile_alim_thresholds_are_quantiles_of_the_finite_plotted_z(ax):
    """``kind="quantile"`` masks z outside np.quantile of the finite z.

    The +inf z is excluded from the quantile computation and, being above the
    upper threshold, is not drawn.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter(ALIM_X, ALIM_Y, ALIM_Z)
    sc.set_alim(0.2, 0.8, kind="quantile")
    _, _, _, cbar = sc.make_plot(ax=ax)
    lo, hi = np.quantile(ALIM_Z[np.isfinite(ALIM_Z)], [0.2, 0.8])
    keep = (ALIM_Z >= lo) & (ALIM_Z <= hi)
    assert 2 < keep.sum() < ALIM_Z.size - 2
    _assert_drawn(ax, cbar, keep)


def test_quantile_alim_of_zero_is_the_smallest_finite_z(ax):
    """A quantile limit of 0 is allowed and keeps the smallest finite z.

    ``set_alim`` documents quantiles in [0, 1], bounds inclusive; the 0th
    quantile of the finite z is their minimum, 0.0 in ``ALIM_Z``.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter(ALIM_X, ALIM_Y, ALIM_Z)
    sc.set_alim(0.0, 0.5, kind="quantile")
    _, _, _, cbar = sc.make_plot(ax=ax)
    hi = np.quantile(ALIM_Z[np.isfinite(ALIM_Z)], 0.5)
    _assert_drawn(ax, cbar, ALIM_Z <= hi)


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
# edges: line segments joining consecutive points, in source row order. EZ is
# chosen so each segment's mean z, (z[i] + z[i+1]) / 2, is distinct.
# ---------------------------------------------------------------------------

EX = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
EY = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
EZ = np.array([0.0, 2.0, 9.0, 6.0, 8.0])


def _segments(x, y, pairs):
    return [np.array([[x[i], y[i]], [x[j], y[j]]]) for i, j in pairs]


def _assert_segments(lc, x, y, pairs):
    got = lc.get_segments()
    assert len(got) == len(pairs)
    for g, e in zip(got, _segments(x, y, pairs)):
        np.testing.assert_array_equal(g, e)


def test_make_plot_returns_ax_points_edges_then_cbar(ax):
    """``(ax, points, edges, cbar)``; edges is None unless ``edges=True``.

    ON FAILURE: the code is wrong.
    """
    out = Scatter(EX, EY, EZ).make_plot(ax=ax)
    assert len(out) == 4
    assert out[0] is ax
    assert isinstance(out[1], PathCollection)
    assert out[2] is None
    assert isinstance(out[3], Colorbar)
    assert not any(isinstance(c, LineCollection) for c in ax.collections)

    out = Scatter(EX, EY, EZ).make_plot(ax=ax, edges=True)
    assert len(out) == 4
    assert isinstance(out[2], LineCollection)
    assert out[2] in ax.collections


def test_edges_join_each_pair_of_consecutive_points(ax):
    """n points in row order give n - 1 segments, point i to point i + 1.

    ON FAILURE: the code is wrong.
    """
    _, _, lc, _ = Scatter(EX, EY, EZ).make_plot(ax=ax, edges=True)
    _assert_segments(lc, EX, EY, [(0, 1), (1, 2), (2, 3), (3, 4)])


def test_edge_colour_is_the_mean_endpoint_z_through_the_points_cmap_and_norm(ax):
    """Segment i is ``cmap(norm((z[i] + z[i+1]) / 2))``: one colorbar serves both.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, cbar = Scatter(EX, EY, EZ).make_plot(
        ax=ax, edges=True, cmap="plasma"
    )
    mean = (EZ[:-1] + EZ[1:]) / 2
    np.testing.assert_array_equal(lc.get_array(), mean)
    assert lc.norm is points.norm
    assert lc.get_cmap() is points.get_cmap()
    assert (points.norm.vmin, points.norm.vmax) == (EZ.min(), EZ.max())
    lc.update_scalarmappable()
    expected = points.get_cmap()(points.norm(mean))
    np.testing.assert_allclose(lc.get_edgecolor(), expected)
    assert cbar.mappable is points


def test_edges_follow_a_norm_the_caller_passes(ax):
    """``vmin``/``vmax`` given to the points also set the edges' colours.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, _ = Scatter(EX, EY, EZ).make_plot(
        ax=ax, edges=True, vmin=0.0, vmax=20.0
    )
    assert lc.norm is points.norm
    assert (lc.norm.vmin, lc.norm.vmax) == (0.0, 20.0)


def test_a_point_with_nan_breaks_the_chain(ax):
    """A dropped NaN point removes both its segments; no segment bridges it.

    ON FAILURE: the code is wrong.
    """
    y = EY.copy()
    y[2] = np.nan
    _, _, lc, _ = Scatter(EX, y, EZ).make_plot(ax=ax, edges=True)
    _assert_segments(lc, EX, y, [(0, 1), (3, 4)])
    np.testing.assert_array_equal(lc.get_array(), [1.0, 7.0])


def test_a_point_outside_alim_breaks_the_chain(ax):
    """A point ``alim`` hides drops both its segments, as a NaN point does.

    EZ[2] = 9 is the only z above 8, so two segments go, not one.
    ON FAILURE: the code is wrong.
    """
    sc = Scatter(EX, EY, EZ)
    sc.set_alim(None, 8.0)
    _, _, lc, _ = sc.make_plot(ax=ax, edges=True)
    _assert_segments(lc, EX, EY, [(0, 1), (3, 4)])
    np.testing.assert_array_equal(lc.get_array(), [1.0, 7.0])


def test_a_masked_point_breaks_the_chain(ax):
    """A point ``mask`` excludes drops both its segments.

    ON FAILURE: the code is wrong.
    """
    mask = pd.Series([True, True, True, False, True])
    _, _, lc, _ = Scatter(EX, EY, EZ, mask=mask).make_plot(ax=ax, edges=True)
    _assert_segments(lc, EX, EY, [(0, 1), (1, 2)])


def test_consecutive_is_row_position_not_label(ax):
    """Rows are joined in the order given, even with repeated or unsorted labels.

    ON FAILURE: the code is wrong.
    """
    index = [3, 3, 1, 0, 2]
    x, y, z = (pd.Series(v, index=index) for v in (EX, EY, EZ))
    _, _, lc, _ = Scatter(x, y, z).make_plot(ax=ax, edges=True)
    _assert_segments(lc, EX, EY, [(0, 1), (1, 2), (2, 3), (3, 4)])


@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=range(EX.size))])
def test_edges_without_varying_z_have_one_colour(ax, z):
    """With no z, or a constant one, every segment has the points' colour.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, cbar = Scatter(EX, EY, z).make_plot(ax=ax, edges=True)
    assert cbar is None
    assert lc.get_array() is None
    _assert_segments(lc, EX, EY, [(0, 1), (1, 2), (2, 3), (3, 4)])
    colors = lc.get_edgecolor()
    assert len(colors) == 1
    np.testing.assert_array_equal(colors[0], points.get_facecolor()[0])


def test_edges_sit_below_the_points_and_take_edge_kwargs(ax):
    """Edges default to beneath the markers; ``edge_kwargs`` styles them.

    ON FAILURE: the code is wrong.
    """
    _, points, lc, _ = Scatter(EX, EY, EZ).make_plot(ax=ax, edges=True)
    assert lc.get_zorder() < points.get_zorder()

    kwargs = {"linewidth": 3.0, "alpha": 0.4, "zorder": 5}
    _, _, lc, _ = Scatter(EX, EY, EZ).make_plot(ax=ax, edges=True, edge_kwargs=kwargs)
    assert kwargs == {"linewidth": 3.0, "alpha": 0.4, "zorder": 5}
    np.testing.assert_array_equal(lc.get_linewidth(), [3.0])
    assert (lc.get_alpha(), lc.get_zorder()) == (0.4, 5)


def test_edges_do_not_change_the_axis_limits(ax):
    """The view fits the points with or without edges.

    ON FAILURE: the code is wrong.
    """
    Scatter(EX, EY, EZ).make_plot(ax=ax, edges=True)
    assert ax.get_xlim() == (EX.min(), EX.max())
    assert ax.get_ylim() == (EY.min(), EY.max())
