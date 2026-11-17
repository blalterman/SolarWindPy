# Spent-When: PERMANENT(solarwindpy.plotting stops drawing marker size and alpha through scale objects)
# Supersedes: none
"""Tests for ``SizeScale`` and ``AlphaScale``, built on their own.

Each holds one marker channel of a ``Scatter``: a norm from the data to
[0, 1], a range from [0, 1] to the marker's area (pt²) or alpha, and the
settings of its guide. Both are checked when built and print one
``key: value`` line per setting. How a plot draws with them is tested in
``tests/plotting/test_scatter.py``.
"""

import numpy as np
import pytest
from matplotlib.colors import LogNorm, Normalize

from solarwindpy.plotting import scales


@pytest.mark.parametrize(
    "name, settings, error, match",
    [
        ("SizeScale", {"norm": 3}, TypeError, "norm must be"),
        ("SizeScale", {"range": (9,)}, TypeError, "range must be two numbers"),
        ("SizeScale", {"range": "ab"}, TypeError, "range must be two numbers"),
        ("SizeScale", {"range": (9, np.inf)}, ValueError, "finite"),
        ("SizeScale", {"range": (-1, 144)}, ValueError, "areas must be >= 0"),
        ("AlphaScale", {"range": (0.15, 1.5)}, ValueError, r"in \[0, 1\]"),
        ("AlphaScale", {"range": (-0.1, 1)}, ValueError, r"in \[0, 1\]"),
        ("SizeScale", {"key": "big"}, TypeError, "key must be"),
        ("SizeScale", {"key": [1, np.nan]}, ValueError, "key values must be finite"),
        ("SizeScale", {"key": []}, ValueError, "at least one"),
        ("SizeScale", {"key_kwargs": [("loc", 1)]}, TypeError, "key_kwargs must be"),
        ("AlphaScale", {"cbar": 1}, TypeError, "cbar must be"),
        ("AlphaScale", {"cbar_kwargs": [("shrink", 1)]}, TypeError, "cbar_kwargs must"),
    ],
    ids=[
        "norm",
        "short-range",
        "str-range",
        "infinite-range",
        "negative-area",
        "alpha-above-1",
        "alpha-below-0",
        "str-key",
        "nan-key",
        "empty-key",
        "key_kwargs",
        "cbar",
        "cbar_kwargs",
    ],
)
def test_marker_scales_reject_invalid_settings_when_built(name, settings, error, match):
    """A bad norm, range, key or guide setting raises when the scale is built.

    ON FAILURE: the code is wrong.
    """
    cls = getattr(scales, name)
    with pytest.raises(error, match=match):
        cls(**settings)


def test_marker_scales_hold_reversed_ranges_scale_name_norms_and_key_values():
    """A reversed range is kept as given; a scale name becomes matplotlib's norm.

    ON FAILURE: the code is wrong.
    """
    assert scales.SizeScale(range=(144, 9)).range == (144.0, 9.0)
    assert scales.AlphaScale(range=(1, 0)).range == (1.0, 0.0)
    assert isinstance(scales.AlphaScale(norm="log").norm, LogNorm)
    assert scales.SizeScale(key=np.array([2, 5])).key == (2.0, 5.0)
    assert scales.SizeScale(key=None).key is False


def test_marker_scale_str_shows_norm_limits_range_with_units_and_guide():
    """``print(scale)`` lists the norm with its limits, the range with its units, the guide.

    ON FAILURE: the code is wrong.
    """
    size = scales.SizeScale(norm=LogNorm(1, 100), range=(10, 30), key=[1, 10])
    assert str(size) == (
        "SizeScale\n"
        "  norm: LogNorm(vmin=1, vmax=100)\n"
        "  range: (10, 30) pt² area\n"
        "  key: (1, 10)\n"
        "  key_kwargs: {}"
    )
    alpha = scales.AlphaScale(norm=Normalize(), cbar_kwargs={"shrink": 0.5})
    assert repr(alpha) == (
        "AlphaScale\n"
        "  norm: Normalize(vmin=None, vmax=None)\n"
        "  range: (0.15, 1) alpha\n"
        "  cbar: True\n"
        "  cbar_kwargs: {'shrink': 0.5}"
    )
