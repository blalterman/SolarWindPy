# Spent-When: PERMANENT(the plotting migration and invariant suites stop using shared cases)
# Supersedes: none
"""Seeded synthetic inputs shared by the plotting migration and invariant tests.

Every case is built in memory from ``np.random.default_rng(<seed>)`` with a
seed of its own, so a case does not change when another is added. No file is
read. Each case holds the series a caller passes to a plot (x, y and an
optional z) plus the options that matter for binning: a caller mask, the log
flags and ``clip_data``.

``nbins_spec`` builds each bin specification the histograms accept, and
``spiral_bins_spec`` the initial bins ``SpiralPlot2D`` accepts. Explicit edges
come from the case's own values on the binned scale (``log10|v|`` on a log
axis), between their 2nd and 98th percentiles, so some values fall outside
the bins on purpose.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

#: Rows per case.
N = 400

#: Names of the ``nbins`` specifications ``nbins_spec`` builds.
NBINS = ("int", "auto", "edges", "intervals_left", "mixed", "knuth")

#: Names of the initial-bin specifications ``spiral_bins_spec`` builds.
SPIRAL_NBINS = ("int", "mixed")


@dataclass(frozen=True)
class Case:
    """One synthetic input: the series a caller passes and the binning options.

    Attributes
    ----------
    name : str
        Identifier used in test ids.
    x, y : pd.Series
        Coordinates.
    z : pd.Series or None
        Value to aggregate; None means the plot counts points.
    mask : pd.Series or None
        Boolean series aligned to the index of ``x``: True keeps the row.
    logx, logy : bool
        Log flags passed to the plot.
    clip_data : bool or str
        ``clip_data`` passed to the plot.
    """

    name: str
    x: pd.Series
    y: pd.Series
    z: pd.Series = None
    mask: pd.Series = None
    logx: bool = False
    logy: bool = False
    clip_data: object = False

    def inputs(self):
        """Return ``(x, y, z)`` with the mask applied by subsetting each series.

        This is how a caller selects rows before a plot takes a ``mask``.
        """
        if self.mask is None:
            return self.x, self.y, self.z
        keep = self.mask[self.mask].index
        x = self.x.loc[keep]
        y = self.y.loc[keep]
        z = None if self.z is None else self.z.loc[keep]
        return x, y, z

    def __repr__(self):
        return f"Case({self.name})"


def _draw(seed, index=None):
    """Return correlated ``(x, y, z)`` series of ``N`` rows on ``index``."""
    rng = np.random.default_rng(seed)
    if index is None:
        index = pd.RangeIndex(N)
    x = rng.gamma(4.0, 1.0, N) + 0.5
    y = 0.5 * x + rng.normal(0.0, 1.0, N)
    z = 10.0 + 2.0 * rng.standard_normal(N)
    return (
        pd.Series(x, index=index, name="x"),
        pd.Series(y, index=index, name="y"),
        pd.Series(z, index=index, name="z"),
        rng,
    )


def _with_nan(series, rng, fraction=0.1):
    """Return a copy of ``series`` with ``fraction`` of its rows set to NaN."""
    out = series.copy()
    hit = rng.choice(series.size, size=int(fraction * series.size), replace=False)
    out.iloc[hit] = np.nan
    return out


def _counts():
    x, y, _, _ = _draw(101)
    return Case("counts", x, y)


def _clean():
    x, y, z, _ = _draw(102)
    return Case("clean", x, y, z)


def _nan_x():
    x, y, z, rng = _draw(103)
    return Case("nan_x", _with_nan(x, rng), y, z)


def _nan_y():
    x, y, z, rng = _draw(104)
    return Case("nan_y", x, _with_nan(y, rng), z)


def _nan_z():
    x, y, z, rng = _draw(105)
    return Case("nan_z", x, y, _with_nan(z, rng))


def _mask():
    x, y, z, rng = _draw(106)
    mask = pd.Series(rng.random(N) < 0.8, index=x.index)
    return Case("mask", x, y, z, mask=mask)


def _log_zero_negative():
    """Zeros and negative values on both axes, binned in log space."""
    x, y, z, rng = _draw(107)
    x = x.copy()
    y = y.copy()
    picks = rng.choice(N, size=30, replace=False)
    x.iloc[picks[:5]] = 0.0
    x.iloc[picks[5:15]] = -x.iloc[picks[5:15]]
    y.iloc[picks[15:20]] = 0.0
    y.iloc[picks[20:]] = -np.abs(y.iloc[picks[20:]])
    return Case("log_zero_negative", x, y, z, logx=True, logy=True)


def _clip_outlier():
    """A few extreme values far outside the bulk, with ``clip_data=True``."""
    x, y, z, rng = _draw(108)
    x = x.copy()
    y = y.copy()
    picks = rng.choice(N, size=4, replace=False)
    x.iloc[picks[:3]] = x.iloc[picks[:3]] * 1.0e3
    y.iloc[picks[3]] = -1.0e3
    return Case("clip_outlier", x, y, z, clip_data=True)


def _multiindex():
    """A ``(source, time)`` index in which every timestamp repeats across sources."""
    times = pd.date_range("2020-01-01", periods=N // 2, freq="min")
    index = pd.MultiIndex.from_product([["a", "b"], times], names=["source", "time"])
    x, y, z, _ = _draw(109, index=index)
    return Case("multiindex", x, y, z)


def _mismatched_index():
    """y is indexed 40 labels later than x and z, so the union has gaps."""
    x, y, z, _ = _draw(110)
    y = y.set_axis(pd.RangeIndex(40, N + 40))
    return Case("mismatched_index", x, y, z)


def _integer_z():
    x, y, _, rng = _draw(111)
    z = pd.Series(rng.integers(0, 6, N), index=x.index, name="z")
    return Case("integer_z", x, y, z)


#: Every case, by name.
CASES = {
    case.name: case
    for case in (
        _counts(),
        _clean(),
        _nan_x(),
        _nan_y(),
        _nan_z(),
        _mask(),
        _log_zero_negative(),
        _clip_outlier(),
        _multiindex(),
        _mismatched_index(),
        _integer_z(),
    )
}


def binned_values(case, axis, log):
    """Return the finite values a plot bins on ``axis``: ``log10|v|`` if ``log``."""
    x, y, _ = case.inputs()
    values = (x if axis == "x" else y).to_numpy(dtype=float)
    if log:
        with np.errstate(divide="ignore"):
            values = np.log10(np.abs(values))
    return values[np.isfinite(values)]


def _edges(values, n_edges=9):
    """Return ``n_edges`` edges between the 2nd and 98th percentiles of ``values``."""
    lo, hi = np.percentile(values, [2.0, 98.0])
    edges = np.unique(np.linspace(lo, hi, n_edges).round(3))
    return edges


def nbins_spec(name, case, axes, log):
    """Build the ``nbins`` specification ``name`` for ``case``.

    Parameters
    ----------
    name : str
        One of ``NBINS``.
    case : Case
        The input the plot bins.
    axes : tuple of str
        The binned axes, ``("x",)`` or ``("x", "y")``.
    log : dict
        Maps each axis to whether the plot bins it in log space.

    Returns
    -------
    int, str, np.ndarray, pd.IntervalIndex or tuple
        ``"int"``: 7 bins. ``"auto"`` and ``"knuth"``: the rule name.
        ``"edges"``: one edge array spanning every binned axis.
        ``"intervals_left"``: the same edges as a left-closed
        ``IntervalIndex``. ``"mixed"``: one entry per axis, an integer for x
        and a left-closed ``IntervalIndex`` of y's own edges for y; with one
        axis, a 1-tuple holding x's edge array.
    """
    if name == "int":
        return 7
    if name in ("auto", "knuth"):
        return name
    pooled = np.concatenate([binned_values(case, k, log[k]) for k in axes])
    if name == "edges":
        return _edges(pooled)
    if name == "intervals_left":
        return pd.IntervalIndex.from_breaks(_edges(pooled), closed="left")
    if name == "mixed":
        if axes == ("x",):
            return (_edges(binned_values(case, "x", log["x"])),)
        y_edges = _edges(binned_values(case, "y", log["y"]))
        return (6, pd.IntervalIndex.from_breaks(y_edges, closed="left"))
    raise ValueError(f"unknown nbins spec {name!r}")


def spiral_bins_spec(name, case, log):
    """Build the ``SpiralPlot2D`` initial-bin specification ``name`` for ``case``.

    ``"int"``: 3 bins per axis. ``"mixed"``: x's own edge array and 4 bins
    for y.
    """
    if name == "int":
        return 3
    if name == "mixed":
        return (_edges(binned_values(case, "x", log["x"]), n_edges=5), 4)
    raise ValueError(f"unknown spiral bins spec {name!r}")
