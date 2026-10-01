# Spent-When: PERMANENT(solarwindpy stops shipping its plotting package)
# Supersedes: none
"""Defects found in ``solarwindpy/plotting`` while documenting it.

Each test failed before its fix landed and passes after it.
"""

import operator

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402

from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402
from solarwindpy.plotting.labels.composition import ChargeStateRatio, Ion  # noqa: E402
from solarwindpy.plotting.labels.special import CountOther, Probability  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402

# ``clip_data`` clips each column to its 0.01st and 99.99th percentiles
# (``AggPlot.clip_data`` docstring); both quantiles are recomputed here with numpy.
Q_LOWER, Q_UPPER = 1e-4, 1 - 1e-4


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_scatter_with_clip_data_plots_points_clipped_to_percentiles():
    """``Scatter(..., clip_data=True).make_plot`` draws the clipped points.

    Before the fix, ``make_plot`` raised ``AttributeError: 'Scatter' object has
    no attribute 'clip_data'`` because only ``AggPlot`` defined ``clip_data``.
    The input is 0..10000 with one far outlier on each end, so clipping moves
    exactly those two points, onto numpy's 0.01st and 99.99th percentiles.

    ON FAILURE: the code is wrong.
    """
    raw = np.concatenate([[-1e6], np.arange(10001.0), [1e6]])
    x = pd.Series(raw)
    y = pd.Series(2.0 * raw)

    fig, ax = plt.subplots()
    ax, cbar = Scatter(x, y, clip_data=True).make_plot(ax=ax)

    offsets = ax.collections[0].get_offsets()
    expected_x = np.clip(raw, np.quantile(raw, Q_LOWER), np.quantile(raw, Q_UPPER))
    expected_y = np.clip(
        2.0 * raw, np.quantile(2.0 * raw, Q_LOWER), np.quantile(2.0 * raw, Q_UPPER)
    )
    # Clipping only replaces values; float64 in, float64 out, so exact.
    np.testing.assert_array_equal(np.asarray(offsets[:, 0]), expected_x)
    np.testing.assert_array_equal(np.asarray(offsets[:, 1]), expected_y)
    assert np.asarray(offsets[:, 0]).min() > -1e6
    assert np.asarray(offsets[:, 0]).max() < 1e6


def test_scatter_without_clip_data_plots_raw_points():
    """With ``clip_data=False`` the outliers are drawn unchanged.

    This separates the clipped test above from a scatter that never clips.

    ON FAILURE: the fixture no longer separates clipped from unclipped data; fix the fixture.
    """
    raw = np.concatenate([[-1e6], np.arange(10001.0), [1e6]])
    fig, ax = plt.subplots()
    ax, cbar = Scatter(pd.Series(raw), pd.Series(raw), clip_data=False).make_plot(ax=ax)
    np.testing.assert_array_equal(
        np.asarray(ax.collections[0].get_offsets()[:, 0]), raw
    )


@pytest.mark.parametrize("label_cls", [Probability, CountOther])
@pytest.mark.parametrize("tex_op, ascii_op", [(r"\lt", "<"), (r"\gt", ">")])
def test_comparison_path_names_tex_and_ascii_operator_alike(
    label_cls, tex_op, ascii_op
):
    r"""A TeX comparison operator names the same save path as its ASCII form.

    Before the fix, ``_build_path`` mapped ``\lt`` to ``GT``, so "less than 5"
    saved over "greater than 5".

    ON FAILURE: the code is wrong.
    """
    other = TeXlabel(("n", "", "p1"))
    tex_form = label_cls(other, comparison=f"{tex_op} 5")
    ascii_form = label_cls(other, comparison=f"{ascii_op} 5")
    assert tex_form.path == ascii_form.path


def test_label_less_equal_agrees_with_string_order():
    """``a <= b`` on labels agrees with ``str(a) <= str(b)``, including ``a <= a``.

    Labels compare by their string (``Base.__gt__`` and ``__eq__`` do). Before
    the fix, ``__le__`` returned ``str(self) < str(other)``, so ``a <= a`` was False.

    ON FAILURE: the code is wrong.
    """
    a = TeXlabel(("n", "", "a"))
    b = TeXlabel(("v", "x", "p1"))
    assert a <= a
    assert (a <= b) == (str(a) <= str(b))
    assert (b <= a) == (str(b) <= str(a))


@pytest.mark.parametrize(
    "op", [operator.lt, operator.le, operator.gt, operator.ge], ids=lambda f: f.__name__
)
def test_label_ordering_agrees_with_string_order(op):
    """Every rich comparison on labels agrees with comparing their strings.

    ``Base`` defines ``__gt__`` and ``__le__``; ``<`` and ``>=`` reach them by
    Python's reflection. The expected value is the same operator applied to
    ``str`` of each label (identity), over a pair and a label with itself.

    ON FAILURE: the code is wrong.
    """
    a = TeXlabel(("n", "", "a"))
    b = TeXlabel(("v", "x", "p1"))
    for left, right in [(a, b), (b, a), (a, a)]:
        assert op(left, right) == op(str(left), str(right))  # identity


def test_ion_path_is_the_same_for_int_and_str_charge():
    """``Ion("O", 6)`` and ``Ion("O", "6")`` name the same save path.

    ``Ion`` documents ``charge : int or str``. Before the fix, ``path`` called
    ``charge.replace`` and raised ``AttributeError`` for an int charge.

    ON FAILURE: the code is wrong.
    """
    assert Ion("O", 6).path == Ion("O", "6").path
    ratio_int = ChargeStateRatio(("O", 7), ("O", 6))
    ratio_str = ChargeStateRatio(("O", "7"), ("O", "6"))
    assert ratio_int.path == ratio_str.path
