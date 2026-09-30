#!/usr/bin/env python
"""Tests for ``solarwindpy.plotting.scatter.Scatter``.

A scatter plot hands matplotlib one point per complete (x, y, z) row, coloured
by z when z varies, with a colorbar labelled ``labels.z``. Expectations come
from the hand-typed ``ROWS`` table; assertions read the real ``PathCollection``
(offsets, colour array, sizes), ``Axes`` and ``Colorbar`` on the Agg backend.

The ``Scatter(..., clip_data=True)`` path is not tested here: its
``make_plot`` calls ``self.clip_data``, which ``Scatter`` lacks, so it raises
``AttributeError``. The fix to ``scatter.py`` carries its own test.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402

from solarwindpy.plotting.base import AxesLabels, LogAxes  # noqa: E402
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
    assert Scatter(X, Y).clip is False


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
    ret_ax, cbar = sc.make_plot(ax=ax)
    coll = ax.collections[0]
    np.testing.assert_array_equal(coll.get_array(), _col(KEPT, 3))
    assert ret_ax is ax
    assert isinstance(cbar, Colorbar)
    assert cbar.mappable is coll
    assert cbar.ax.get_ylabel() == "T"
    assert (ax.get_xlabel(), ax.get_ylabel()) == ("Vx", "Np")


@pytest.mark.parametrize("z", [None, pd.Series(7.0, index=X.index)])
def test_absent_or_constant_z_gives_uncoloured_points_and_no_colorbar(ax, z):
    """With no z, or one z value for every point, nothing is colour-mapped.

    ON FAILURE: the code is wrong.
    """
    _, cbar = Scatter(X, Y, z).make_plot(ax=ax)
    assert ax.collections[0].get_array() is None
    assert cbar is None
    assert ax.figure.axes == [ax]


def test_cbar_false_colours_points_but_draws_no_colorbar(ax):
    """``cbar=False`` keeps the colour mapping and skips the colorbar.

    ON FAILURE: the code is wrong.
    """
    _, cbar = Scatter(X, Y, Z).make_plot(ax=ax, cbar=False)
    np.testing.assert_array_equal(ax.collections[0].get_array(), _col(KEPT, 3))
    assert cbar is None
    assert ax.figure.axes == [ax]


def test_without_ax_a_new_figure_is_made():
    """``ax=None`` plots on fresh axes in a new figure (docstring).

    ON FAILURE: the code is wrong.
    """
    existing, _ = plt.subplots()
    try:
        new_ax, _ = Scatter(X, Y).make_plot()
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
    _, cbar = Scatter(X, Y, Z).make_plot(
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

    ON FAILURE: the code is wrong.
    """
    Scatter([1.0, 2.0, 3.0], [6.0, 4.0, 5.0], [0.1, 0.2, 0.3]).make_plot(ax=ax)
    np.testing.assert_array_equal(
        ax.collections[0].get_offsets(), [[1.0, 6.0], [2.0, 4.0], [3.0, 5.0]]
    )


class CbarKwargsMutated(AssertionError):
    """A second plot's colorbar went to the axes of an earlier plot."""


@pytest.mark.xfail(
    strict=True,
    raises=CbarKwargsMutated,
    reason="scatter.py Scatter.make_plot writes cbar_kwargs['ax'] = ax into "
    "the caller's dict, so reusing that dict sends a later colorbar to the "
    "first axes' figure; remove this marker when make_plot copies "
    "cbar_kwargs before adding 'ax'",
)
def test_reused_cbar_kwargs_put_each_colorbar_beside_its_own_axes():
    """One ``cbar_kwargs`` dict reused for two plots: each gets its colorbar.

    ON FAILURE: (unexpected pass) make_plot no longer mutates cbar_kwargs;
    drop the xfail marker.
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
            _, cbar2 = Scatter(X, Y, Z).make_plot(ax=ax2, cbar_kwargs=kwargs)
        if cbar2.ax.figure is not ax2.figure:
            raise CbarKwargsMutated("second colorbar drawn in the first plot's figure")
    finally:
        plt.close("all")
