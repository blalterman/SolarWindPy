# Spent-When: PERMANENT(the Usage guide stops quoting BinnedData timings)
# Supersedes: none
"""Measure what sharing one ``BinnedData`` across plots saves.

Builds and aggregates ten ``Hist2D`` of different ``z`` over one 70 by 50 grid
of 10**6 points, once with a shared ``BinnedData`` and once with each plot
binning its own columns. Prints the median wall time of three runs, and, from
:mod:`tracemalloc` (Python and NumPy allocations), the memory the ten plots
and their aggregates keep and the peak during the build.

The Usage guide ("Share bins across plots") quotes these numbers. Run it from
the repository root in the ``solarwindpy`` environment::

    python scripts/benchmark_binned_data.py
"""

import gc
import platform
import statistics
import time
import tracemalloc

import numpy as np
import pandas as pd

from solarwindpy.plotting.binned import BinnedData
from solarwindpy.plotting.hist2d import Hist2D

N = 1_000_000
N_PLOTS = 10
RUNS = 3
EDGES = {"v": np.linspace(150, 950, 71), "n": np.linspace(-0.5, 2.0, 51)}


def make_frame(seed=0):
    """Return ``N`` rows of ``v``, ``n`` and ``N_PLOTS`` z columns."""
    rng = np.random.default_rng(seed)
    fast = rng.random(N) < 0.3
    v = np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N))
    columns = {
        "v": v,
        "n": 8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N)),
    }
    for i in range(N_PLOTS):
        columns[f"z{i}"] = rng.normal(i, 1, N)
    return pd.DataFrame(columns)


def build_shared(frame):
    """Ten plots on one ``BinnedData``; return the plots and their aggregates."""
    binned = BinnedData(frame[["v", "n"]], EDGES, log={"n": True})
    plots = [
        Hist2D(frame["v"], frame["n"], frame[f"z{i}"], nbins=binned)
        for i in range(N_PLOTS)
    ]
    return plots, [p.agg() for p in plots]


def build_separate(frame):
    """Ten plots that each bin their own columns on the same edges."""
    nbins = (EDGES["v"], EDGES["n"])
    plots = [
        Hist2D(frame["v"], frame["n"], frame[f"z{i}"], nbins=nbins, logy=True)
        for i in range(N_PLOTS)
    ]
    return plots, [p.agg() for p in plots]


def wall_time(build, frame):
    """Median seconds of ``RUNS`` builds."""
    times = []
    for _ in range(RUNS):
        gc.collect()
        start = time.perf_counter()
        build(frame)
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def memory(build, frame):
    """MB kept by the result and MB at the peak of one build."""
    gc.collect()
    tracemalloc.start()
    kept = build(frame)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del kept
    return current / 1e6, peak / 1e6


def main():
    frame = make_frame()
    print(
        f"{platform.machine()} Python {platform.python_version()}, "
        f"pandas {pd.__version__}, NumPy {np.__version__}"
    )
    for name, build in [("shared", build_shared), ("separate", build_separate)]:
        seconds = wall_time(build, frame)
        kept, peak = memory(build, frame)
        print(f"{name:9s} {seconds:.2f} s  kept {kept:.0f} MB  peak {peak:.0f} MB")


if __name__ == "__main__":
    main()
