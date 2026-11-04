# Spent-When: PERMANENT(the author decides the xarray question and the spike branch is deleted)
# Supersedes: none
"""pth with pint-xarray units attached: no per-function SI coefficients.

Run from the spike checkout:
    PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/units_pint.py

The registry (core/quantities.py) stores TeX units and an ``si`` float, not
pint unit strings, so a small mapping is needed: that mapping is the cost.
"""

import logging
import sys

import numpy as np
import pint_xarray  # noqa: F401  (registers the .pint accessor)
import xarray as xr
from pint import UnitRegistry

sys.path.insert(0, __import__("os").path.dirname(__file__))
import xrseams as xs  # noqa: E402

import solarwindpy as swp  # noqa: E402

logging.getLogger("solarwindpy").setLevel(logging.ERROR)

ureg = UnitRegistry(force_ndarray_like=True)
#: The mapping the registry would need: M label -> pint unit string.
PINT_UNITS = {"n": "cm**-3", "w": "km/s", "v": "km/s", "b": "nT", "pth": "pPa"}


def pth_with_units(ds, species):
    """0.5 rho w^2 with units carried: no _UNITS.rho, _UNITS.w, _UNITS.pth."""
    q = ds[["n", "w"]].pint.quantify(
        {k: PINT_UNITS[k] for k in ("n", "w")}, unit_registry=ureg
    )
    sp = list(species)
    m = xr.DataArray(
        swp.examples.load_plasma().constants.m_in_mp.loc[sp].to_numpy(),
        dims="species", coords={"species": sp},
    ).pint.quantify("proton_mass", unit_registry=ureg)
    rho = q["n"].sel(species=sp) * m
    return (0.5 * rho * q["w"].sel(species=sp) ** 2).pint.to(PINT_UNITS["pth"])


def main():
    plasma = swp.examples.load_plasma()
    ds = xs.to_dataset(plasma.data)
    sp = ["a", "p1"]
    with_units = pth_with_units(ds, sp)
    print("units:", with_units.pint.units)
    plain = xs.pth(ds, sp)
    a, b = with_units.pint.dequantify().transpose(*plain.dims).values, plain.values
    rel = np.nanmax(np.abs(a - b) / np.abs(b))
    print("vs xrseams.pth (registry si floats): max rel diff", f"{rel:.1e}")
    for s in sp:
        pd_pth = plasma.ions.loc[s].pth.loc[:, ["par", "per", "scalar"]].to_numpy()
        got = with_units.sel(species=s).transpose("time", "tcomponent").pint.dequantify()
        r = np.nanmax(np.abs(got.values - pd_pth) / np.abs(pd_pth))
        print(f"vs pandas Ion({s}).pth: max rel diff {r:.1e}")
    # The species total with min_count keeps units.
    tot = with_units.sum("species", min_count=1)
    print("species_total keeps units:", tot.pint.units)
    p1 = with_units.sel(species="p1")
    try:
        xs.anisotropy(p1)
        print("seam-form R (prod of pth**[-1, 1]) under pint: ok")
    except Exception as exc:
        print("seam-form R (prod of pth**[-1, 1]) under pint: FAIL", type(exc).__name__)
    R = p1.sel(tcomponent="per") / p1.sel(tcomponent="par")
    ref = plasma.ions.loc["p1"].R.to_numpy()
    print("R = per / par units:", R.pint.units, " max rel diff vs Ion(p1).R:",
          f"{np.nanmax(np.abs(R.pint.dequantify().values / ref - 1)):.1e}")

if __name__ == "__main__":
    main()
