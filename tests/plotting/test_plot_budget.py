# Spent-When: PERMANENT(the plot classes stop promising a memory and build-time budget)
# Supersedes: none
"""Memory and build-time budget of the plot classes.

These tests run in every suite run, CI included: the file takes about 4 s, and a
budget that is skipped by default never guards anything.

Memory is the bytes still held, per input row, while the built plot is alive,
measured with :mod:`tracemalloc` after ``gc.collect()``. The input frame is
built before tracing starts, so only what the plot itself keeps is counted.

Time is never compared in seconds. Each build is timed against a reference
that does the same binning job with numpy on the same arrays in the same
process, so a slower or faster machine moves both sides together. Each side
is the best of several repeats, which discards scheduler and cache noise.

Every bound is an inequality on a ratio or a per-row count, so no comparison
needs a tolerance helper. Each bound's line says where it comes from: the
storage the design promises (representation arithmetic), the author's ruling
in the binned-data plan, or the figure measured on this machine at 1,000,000
rows (step 9a) plus the stated headroom.
"""

import gc
import time
import tracemalloc

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.plotting.binned import BinnedData  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

# The plan's budget size: large enough that per-row storage dwarfs the fixed
# cost of a plot object, small enough that the file runs in seconds.
N = 500_000
# 50 bins per axis: codes fit in int8, as in the step 9a measurements.
EDGES = np.linspace(-5.0, 5.0, 51)
# Best-of repeats for each side of a timing ratio.
REPEATS = 7
# Spiral mesh scaling is measured from N to SCALE * N rows.
SCALE = 4


def _frame(n, *, nan_fraction, seed):
    """Standard-normal x and y; each axis loses ``nan_fraction / 2`` to NaN."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, n)
    y = rng.normal(0.0, 1.0, n)
    if nan_fraction:
        x[rng.random(n) < nan_fraction / 2] = np.nan
        y[rng.random(n) < nan_fraction / 2] = np.nan
    return pd.DataFrame({"x": x, "y": y})


@pytest.fixture(scope="module")
def with_nan():
    """About 10% of rows hold a NaN in x or y, as in the step 9a figures."""
    return _frame(N, nan_fraction=0.1, seed=20261103)


@pytest.fixture(scope="module")
def no_nan():
    """Every row is finite, so no plot needs to store which rows it dropped."""
    return _frame(N, nan_fraction=0.0, seed=20261104)


@pytest.fixture(scope="module", autouse=True)
def _warm():
    """Build each class once on a small frame before anything is measured.

    The first build imports lazily-loaded modules and compiles numba kernels;
    that one-off cost is neither memory a plot keeps nor build time.
    """
    small = _frame(20_000, nan_fraction=0.1, seed=1)
    Hist2D(small.x, small.y, nbins=(EDGES, EDGES))
    Hist2D(small.x, small.y, nbins=50)
    Hist2D(small.x, small.y, nbins=BinnedData(small, {"x": EDGES, "y": EDGES}))
    Scatter(small.x, small.y)
    SpiralPlot2D(small.x, small.y).make_plot()
    plt.close("all")
    yield
    plt.close("all")


def _retained_per_row(build, n=N):
    """Bytes per row still traced after ``build()`` returns, holding its result."""
    gc.collect()
    tracemalloc.start()
    try:
        before = tracemalloc.get_traced_memory()[0]
        kept = build()
        gc.collect()
        after = tracemalloc.get_traced_memory()[0]
    finally:
        tracemalloc.stop()
    del kept
    return (after - before) / n


def _best_seconds(fn, repeats=REPEATS):
    """Fastest of ``repeats`` wall-clock runs of ``fn``."""
    best = np.inf
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - start)
    return best


def _spiral(frame):
    return SpiralPlot2D(frame.x, frame.y)


class TestRetainedMemory:
    """A built plot keeps a few bytes per row, not a copy of its columns."""

    def test_private_hist2d_with_nan_keeps_codes_and_a_row_mask(self, with_nan):
        """Hist2D on its own bins keeps at most 4 B/row when rows are dropped.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        f = with_nan
        per_row = _retained_per_row(lambda: Hist2D(f.x, f.y, nbins=(EDGES, EDGES)))
        # int8 code per axis (2 B) + 1 B kept-row mask = 3 B/row, plus 1 B
        # headroom: the plan's budget of 4 (measured 3.04 at 1M rows).
        assert per_row <= 4.0, f"{per_row:.2f} B/row"

    def test_private_hist2d_without_nan_keeps_only_codes(self, no_nan):
        """Hist2D keeps at most 2.5 B/row when no row is dropped.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        f = no_nan
        per_row = _retained_per_row(lambda: Hist2D(f.x, f.y, nbins=(EDGES, EDGES)))
        # int8 code per axis (2 B), no mask when nothing is dropped, plus
        # 0.5 B headroom: the plan's budget of 2.5.
        assert per_row <= 2.5, f"{per_row:.2f} B/row"

    def test_plots_on_one_shared_binned_data_cost_about_one_byte_per_row_each(
        self, with_nan
    ):
        """Each extra Hist2D on a shared BinnedData keeps at most 1.5 B/row.

        The BinnedData is built before tracing, so the traced bytes are the
        plots' own; four plots show the cost is per plot, not a one-off.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        f = with_nan
        shared = BinnedData(f, {"x": EDGES, "y": EDGES})
        plots = 4
        per_row = _retained_per_row(
            lambda: [Hist2D(f.x, f.y, nbins=shared) for _ in range(plots)]
        )
        # Codes are the BinnedData's; a plot adds its 1 B kept-row mask, plus
        # 0.5 B headroom: the plan's 1.5 per extra plot (measured 1.02).
        assert per_row / plots <= 1.5, f"{per_row / plots:.2f} B/row per plot"

    def test_scatter_keeps_only_a_row_mask(self, with_nan):
        """Scatter keeps at most 1.5 B/row: a mask, not a copy of x and y.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        f = with_nan
        per_row = _retained_per_row(lambda: Scatter(f.x, f.y))
        # 1 B kept-row mask, plus 0.5 B headroom (measured 1.01 at 1M rows);
        # a copy of x and y would be 16 B/row.
        assert per_row <= 1.5, f"{per_row:.2f} B/row"

    def test_reading_data_retains_nothing_per_row(self, with_nan):
        """Reading ``h.data`` and dropping it leaves no per-row storage behind.

        ON FAILURE: the code is wrong; ``data`` is being cached on the plot.
        """
        f = with_nan
        h = Hist2D(f.x, f.y, nbins=(EDGES, EDGES))

        def read():
            data = h.data
            del data
            return None

        per_row = _retained_per_row(read)
        # Ideal 0; 0.1 B/row (50 kB at N) allows fixed-size caches but not a
        # kept column, which is at least 1 B/row (measured 0.001-0.04 at 500k).
        assert per_row <= 0.1, f"{per_row:.3f} B/row"

    def test_spiral_mesh_without_nan_shares_the_source_columns(self, no_nan):
        """A built SpiralPlot2D keeps at most 13 B/row, no NaN.

        With every row kept and both axes linear, the mesh reads the source
        columns instead of a copy, so x and y (16 B/row) are not counted.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        per_row = _retained_per_row(lambda: _spiral(no_nan))
        # Measured 10.4 at 1M rows (int32 bin_id 4 B + cell order and
        # categories), plus 25% headroom; a copy of x and y alone is 16 B.
        assert per_row <= 13.0, f"{per_row:.2f} B/row"

    def test_spiral_mesh_with_nan_keeps_one_copy_of_the_kept_points(self, with_nan):
        """A built SpiralPlot2D keeps at most 36 B/row with NaN.

        ON FAILURE: the code is wrong, unless the author changes the budget.
        """
        per_row = _retained_per_row(lambda: _spiral(with_nan))
        # Measured 32.0 at 1M rows (the copy of the kept x, y and index plus
        # the no-NaN cost), plus 12% headroom.
        assert per_row <= 36.0, f"{per_row:.2f} B/row"


class TestBuildTime:
    """Build time, as a ratio to numpy doing the same binning job."""

    @pytest.fixture(scope="class")
    def reference(self, with_nan):
        """Best-of seconds for ``np.histogram2d`` on the same columns and edges.

        ``np.histogram2d`` bins both columns into the same 50 x 50 grid and
        ignores NaN, so it is the same job done by an independent, stable
        numpy routine. At 1M rows it costs about what the pre-rewrite Hist2D
        did (about 70 ms), so ratio 1.0 stands in for the author's ruling that
        a private build is no slower than legacy.
        """
        x = with_nan.x.to_numpy()
        y = with_nan.y.to_numpy()
        return _best_seconds(lambda: np.histogram2d(x, y, bins=(EDGES, EDGES)))

    @pytest.mark.parametrize(
        "nbins",
        [pytest.param("edges", id="explicit-edges"), pytest.param(50, id="nbins-50")],
    )
    def test_private_hist2d_build_is_no_slower_than_numpy_histogram2d(
        self, with_nan, reference, nbins
    ):
        """A private-path Hist2D build costs at most 1.0x ``np.histogram2d``.

        ON FAILURE: the code is wrong, unless the author changes the ruling.
        """
        f = with_nan
        spec = (EDGES, EDGES) if nbins == "edges" else nbins
        build = _best_seconds(lambda: Hist2D(f.x, f.y, nbins=spec))
        ratio = build / reference
        # Author's ruling: no slower than legacy, and legacy ~ np.histogram2d
        # (see the fixture). Measured 0.41 (edges) and 0.60 (nbins=50) at 500k.
        assert ratio <= 1.0, f"{build * 1e3:.1f} ms = {ratio:.2f} x reference"

    def test_shared_binned_data_build_is_faster_than_a_private_build(self, with_nan):
        """A Hist2D on a shared BinnedData builds in under half a private build.

        The shared path skips binning, the costly step, so it must be well
        under a private build of the same plot on the same bins.

        ON FAILURE: the code is wrong; the shared path is re-binning.
        """
        f = with_nan
        shared = BinnedData(f, {"x": EDGES, "y": EDGES})
        private = _best_seconds(lambda: Hist2D(f.x, f.y, nbins=(EDGES, EDGES)))
        reused = _best_seconds(lambda: Hist2D(f.x, f.y, nbins=shared))
        ratio = reused / private
        # Author's ruling: shared is faster than private; 0.5 makes "faster"
        # mean skipping the binning (measured 0.07 at 500k, 0.21 at 1M).
        assert ratio <= 0.5, f"shared {reused * 1e3:.1f} ms = {ratio:.2f} x private"

    def test_spiral_mesh_build_scales_about_linearly_in_rows(self):
        """Building a SpiralPlot2D on 4x the rows costs at most 6x the time.

        With ``min_per_bin`` fixed the cell count grows with the rows, so a
        cost of cells x points would grow 16x. Linear growth is 4x; numpy's own
        sorting is n log n (about 4.8x here). 6x leaves room for that and for
        cache effects, and still fails a return to cells x points.

        ON FAILURE: the code is wrong; the mesh build has gone superlinear.
        """
        small = _frame(N, nan_fraction=0.0, seed=7)
        large = _frame(SCALE * N, nan_fraction=0.0, seed=8)
        t_small = _best_seconds(lambda: SpiralPlot2D(small.x, small.y), 3)
        t_large = _best_seconds(lambda: SpiralPlot2D(large.x, large.y), 3)
        ratio = t_large / t_small
        # Linear = SCALE (4x); cells x points = SCALE**2 (16x). Bound 6x,
        # 1.5 x linear (measured 3.86-4.34 at 500k -> 2M; 0.14 s -> 0.74 s at
        # 1M -> 4.6M in step 9a is 5.3x for 4.6x rows).
        assert ratio <= 1.5 * SCALE, (
            f"{t_small:.3f} s -> {t_large:.3f} s = {ratio:.2f}x"
        )
