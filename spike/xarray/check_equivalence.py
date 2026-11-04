# Spent-When: PERMANENT(the author decides the xarray question and the spike branch is deleted)
# Supersedes: none
"""Check every xarray seam result against the pandas implementation.

Run from the spike checkout:
    PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/check_equivalence.py

Each comparison reports whether the NaN masks are identical and whether the
values are bit-identical; if not bit-identical, the max relative difference.
"""

import logging
import sys

import numpy as np
import pandas as pd
import xarray as xr

sys.path.insert(0, __import__("os").path.dirname(__file__))
import xrseams as xs  # noqa: E402

import solarwindpy as swp  # noqa: E402
from solarwindpy.core.plasma import Plasma  # noqa: E402
from solarwindpy.core.vector import Vector  # noqa: E402

logging.getLogger("solarwindpy").setLevel(logging.ERROR)

RESULTS = []


def compare(name, pd_obj, xr_obj):
    a = np.asarray(pd_obj.to_numpy() if hasattr(pd_obj, "to_numpy") else pd_obj, float)
    b = np.asarray(xr_obj, float)
    if a.shape != b.shape:
        RESULTS.append((name, False, False, f"shape {a.shape} vs {b.shape}"))
        return
    nan_same = bool(np.array_equal(np.isnan(a), np.isnan(b)))
    exact = bool(np.array_equal(a, b, equal_nan=True))
    finite = ~np.isnan(a) & ~np.isnan(b)
    rel = (
        float(np.max(np.abs(a[finite] - b[finite]) / np.abs(a[finite])))
        if finite.any() and not exact
        else 0.0
    )
    RESULTS.append((name, nan_same, exact, f"nan={int(np.isnan(a).sum())} rel={rel:.1e}"))


def species_frame_to_array(df, species):
    """pandas multi-species result (columns S) to an array ordered (time, species)."""
    return df.loc[:, list(species)].to_numpy()


def run_case(label, raw):
    species = sorted(s for s in raw.columns.get_level_values("S").unique() if s)
    plasma = Plasma(raw.copy(), *species)
    ds = xs.to_dataset(plasma.data)

    # Masking: xarray masking of the raw frame equals Plasma's load-time masking.
    # Plasma keeps only these columns (and derives w scalar), so compare those.
    kept = raw.loc[:, raw.columns.intersection(plasma.data.columns)]
    ds_raw = xs.mask_invalid_species(xs.to_dataset(kept), species)
    for m in ("n", "v", "w", "b"):
        ours, theirs = ds_raw[m], ds[m]
        if m == "w":
            ours, theirs = (d.sel(tcomponent=["par", "per"]) for d in (ours, theirs))
        compare(f"{label}: mask_invalid_species {m}", theirs.values.ravel(), ours.values.ravel())

    b = plasma.b
    v = plasma.ions.loc["p1"].v
    for name in ("mag", "rho", "colat", "lat", "lon"):
        fn = xs.rho_xy if name == "rho" else getattr(xs, name)
        compare(f"{label}: b.{name}", getattr(b, name), fn(ds["b"]))
        compare(
            f"{label}: v(p1).{name}",
            getattr(v, name),
            fn(xs.select(ds["v"], "p1", "species")),
        )
    proj_pd = v.project(b)
    proj_xr = xs.project(xs.select(ds["v"], "p1", "species"), ds["b"])
    compare(f"{label}: v(p1).project(b) par", proj_pd["par"], proj_xr["par"])
    compare(f"{label}: v(p1).project(b) per", proj_pd["per"], proj_xr["per"])

    for s in ("a", "p1"):
        compare(f"{label}: Ion({s}).R", plasma.ions.loc[s].R, xs.ion_R(ds, s))
    compare(f"{label}: Plasma.R('a+p1')", plasma.R("a+p1"), xs.plasma_R(ds, "a+p1"))
    compare(
        f"{label}: Plasma.R('a', 'p1')",
        species_frame_to_array(plasma.R("a", "p1"), ["a", "p1"]),
        xs.plasma_R(ds, "a", "p1").transpose("time", "species"),
    )
    compare(
        f"{label}: Plasma.pth('a+p1')",
        plasma.pth("a+p1").loc[:, ["par", "per", "scalar"]],
        xs.species_total(xs.pth(ds, ["a", "p1"])).transpose("time", "tcomponent"),
    )
    return plasma, ds


def main():
    raw = swp.examples._read_example("plasma")
    run_case("clean", raw)

    masked = raw.copy()
    t = masked.index
    # Row 0: one component of one species' moment -> Plasma masks all of 'a';
    # the a+p1 total is p1 alone there.
    masked.loc[t[0], ("w", "per", "a")] = np.nan
    # Row 1: both a and p1 lose a moment -> a+p1 total is NaN (min_count=1);
    # without min_count it would be 0.0 and R would be 0/0 or inf.
    masked.loc[t[1], ("n", "", "a")] = np.nan
    masked.loc[t[1], ("v", "x", "p1")] = np.nan
    # Row 2: one b component -> strict mag and projection are NaN.
    masked.loc[t[2], ("b", "z", "")] = np.nan
    plasma, ds = run_case("masked", masked)

    # Without min_count the species total gives 0.0 where pandas gives NaN.
    p = xs.pth(ds, ["a", "p1"])
    naive = p.sum("species").sel(tcomponent="par").values
    print("naive species sum at row 1 (pandas has NaN):", naive[1])

    # Shared component coordinate across v and w: strict reduce becomes all NaN.
    v = xs.select(ds["v"], "p1", "species")
    padded = v.reindex(component=["x", "y", "z", "par", "per", "scalar"])
    print(
        "padded_component_breaks_strict_reduce: NaN count of |v| over a "
        "shared 6-label component dim:",
        int(np.isnan(np.sqrt((padded**2).sum("component", skipna=False))).sum()),
        "of",
        v.sizes["time"],
    )

    # Alignment: pandas projects on the union of indices, xarray's default
    # arithmetic join is inner.
    b_short = Vector(plasma.b.data.iloc[:2])
    pd_len = len(plasma.ions.loc["p1"].v.project(b_short))
    bx = ds["b"].isel(time=slice(0, 2))
    xr_inner = xs.project(v, bx, join="inner").sizes["time"]
    xr_outer = xs.project(v, bx, join="outer").sizes["time"]
    print(f"alignment: pandas rows={pd_len}, xarray inner={xr_inner}, outer={xr_outer}")

    width = max(len(r[0]) for r in RESULTS)
    ok = True
    for name, nan_same, exact, note in RESULTS:
        ok &= nan_same
        print(f"{name:<{width}}  nan_identical={nan_same!s:<5} exact={exact!s:<5} {note}")
    n_exact = sum(r[2] for r in RESULTS)
    print(f"\n{len(RESULTS)} comparisons, NaN placement identical in "
          f"{sum(r[1] for r in RESULTS)}, bit-identical in {n_exact}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
