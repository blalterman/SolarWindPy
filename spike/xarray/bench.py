# Spent-When: PERMANENT(the author decides the xarray question and the spike branch is deleted)
# Supersedes: none
"""Time mag, the b-parallel projection and R, pandas against xarray, and check views.

Run from the spike checkout:
    PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/bench.py

pandas timings call the real classes (Vector.mag, Vector.project, Ion.R,
Plasma.R) on objects built outside the timed region; xarray timings call the
xrseams functions on a Dataset built once. Construction and the boundary
conversions are timed separately.
"""

import logging
import sys
import timeit

import numpy as np
import pandas as pd

sys.path.insert(0, __import__("os").path.dirname(__file__))
import xrseams as xs  # noqa: E402

import solarwindpy as swp  # noqa: E402
from solarwindpy.core.plasma import Plasma  # noqa: E402

logging.getLogger("solarwindpy").setLevel(logging.ERROR)


def synthetic(nrows, seed=0):
    """A raw frame with the example's kept columns and ``nrows`` rows."""
    raw = swp.examples._read_example("plasma")
    species = sorted(s for s in raw.columns.get_level_values("S").unique() if s)
    cols = raw.columns.intersection(swp.examples.load_plasma().data.columns)
    rng = np.random.default_rng(seed)
    vals = rng.uniform(1.0, 100.0, size=(nrows, len(cols)))
    # Signed vector components, so angles and projections are not trivial.
    signed = cols.get_level_values("C").isin(["x", "y", "z"])
    vals[:, signed] -= 50.0
    idx = pd.date_range("2020-01-01", periods=nrows, freq="s", name="epoch")
    return pd.DataFrame(vals, index=idx, columns=cols), species


def best(fn, number, repeat=7):
    return min(timeit.repeat(fn, number=number, repeat=repeat)) / number


def bench(label, plasma, ds, number):
    b, ion = plasma.b, plasma.ions.loc["p1"]
    v = ion.v
    xb, xv = ds["b"], xs.select(ds["v"], "p1", "species")
    cases = [
        ("b.mag", lambda: b.mag, lambda: xs.mag(xb)),
        ("v.project(b)['par']", lambda: v.project(b)["par"],
         lambda: xs.project(xv, xb)["par"]),
        ("Ion(p1).R", lambda: ion.R, lambda: xs.ion_R(ds, "p1")),
        ("Plasma.R('a+p1')", lambda: plasma.R("a+p1"),
         lambda: xs.plasma_R(ds, "a+p1")),
    ]
    print(f"\n[{label}] rows={len(plasma.data)}  seconds per call (best of 7)")
    for name, fp, fx in cases:
        tp, tx = best(fp, number), best(fx, number)
        print(f"  {name:<22} pandas {tp:.3e}  xarray {tx:.3e}  pandas/xarray {tp/tx:5.2f}")
    t_conv = best(lambda: xs.to_dataset(plasma.data), max(1, number // 10), 3)
    m = xs.mag(xb)
    t_out = best(lambda: m.to_series(), number)
    print(f"  to_dataset(plasma.data) {t_conv:.3e}   mag.to_series() {t_out:.3e}")
    print(f"  memory: plasma.data {plasma.data.memory_usage(index=False).sum()/1e6:.1f} MB,"
          f" Dataset {ds.nbytes/1e6:.1f} MB (includes the time coordinate)")


def _pd_shares(sel, parent):
    """Whether any block of ``sel`` shares memory with any block of ``parent``.

    ``DataFrame.to_numpy()`` copies a multi-block frame, so compare blocks.
    """
    sb = [b.values for b in sel._mgr.blocks] if hasattr(sel, "_mgr") else [sel]
    if isinstance(sel, pd.Series):
        sb = [sel.to_numpy()]
    pb = [b.values for b in parent._mgr.blocks]
    return any(np.shares_memory(a, b) for a in sb for b in pb)


def views(plasma, ds):
    print("\n[views] shares memory with parent")
    bd, data = plasma.b.data, plasma.data
    print(f"  (pandas blocks: plasma.data {data._mgr.nblocks}, b.data {bd._mgr.nblocks})")
    rows = [
        ("pandas Vector('x') (seam xs)", _pd_shares(plasma.b("x"), bd)),
        ("pandas _select(b, ['x','y'], 'C') list",
         _pd_shares(plasma._select(bd, ["x", "y"], "C"), bd)),
        ("pandas _select(data, 'p1', 'S')",
         _pd_shares(plasma._select(data, "p1", "S"), data)),
        ("pandas _select(data, ['a','p1'], 'S') list",
         _pd_shares(plasma._select(data, ["a", "p1"], "S"), data)),
    ]
    for name, da, key in [
        ("xarray b.sel(component='x')", ds["b"], {"component": "x"}),
        ("xarray v.sel(species='p1')", ds["v"], {"species": "p1"}),
        ("xarray v.sel(component='x', species='p1')", ds["v"],
         {"component": "x", "species": "p1"}),
        ("xarray b.sel(time=slice)", ds["b"], {"time": slice(ds.time[0].values,
                                                             ds.time[-1].values)}),
        ("xarray b.sel(component=['x','y']) list", ds["b"], {"component": ["x", "y"]}),
        ("xarray v.sel(species=['a','p1']) list", ds["v"], {"species": ["a", "p1"]}),
    ]:
        rows.append((name, np.shares_memory(da.sel(key).values, da.values)))
    m = xs.mag(ds["b"])
    rows.append(("xarray mag.to_series()",
                 np.shares_memory(m.to_series().to_numpy(), m.values)))
    rows.append(("to_dataset copy: ds.b vs plasma.data",
                 _pd_shares(pd.DataFrame(ds["b"].values), data)))
    for name, shared in rows:
        print(f"  {name:<46} {shared}")


def main():
    small = swp.examples.load_plasma()
    ds_small = xs.to_dataset(small.data)
    bench("example", small, ds_small, number=200)

    raw, species = synthetic(1_000_000)
    big = Plasma(raw, *species)
    del raw
    ds_big = xs.to_dataset(big.data)
    bench("synthetic 1e6", big, ds_big, number=1)
    views(big, ds_big)


if __name__ == "__main__":
    main()
