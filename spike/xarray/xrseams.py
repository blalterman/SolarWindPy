# Spent-When: PERMANENT(the author decides the xarray question and the spike branch is deleted)
# Supersedes: none
"""xarray versions of the core seams, and the physics built on them.

Spike code, never merged. Run with PYTHONPATH set to the spike checkout root,
so that ``import solarwindpy`` resolves to this branch rather than the editable
install (which points at the main checkout).

Data model
----------
One Dataset variable per M label. Dimensions:

- ``time``: the row index.
- ``species``: particle species; absent on spacecraft-frame quantities (``b``).
- ``component``: Cartesian x, y, z (``b``, ``v``).
- ``tcomponent``: thermal-speed tensor par, per, scalar (``w``).

A Dataset requires one coordinate per dimension name across all variables,
so ``v``'s (x, y, z) and ``w``'s (par, per, scalar) cannot share a
``component`` dimension without being outer-joined to six labels and padded
with NaN. See ``padded_component_breaks_strict_reduce`` in check_equivalence.py.
"""

import os

import numpy as np
import pandas as pd
import xarray as xr

import solarwindpy as swp
from solarwindpy.core.quantities import QUANTITIES

_SPIKE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
assert os.path.realpath(swp.__file__).startswith(
    os.path.realpath(_SPIKE_ROOT)
), f"solarwindpy imported from {swp.__file__}, not the spike checkout"

#: Component dimension name by the component labels a variable holds.
CART = ("x", "y", "z")
TENSOR = ("par", "per", "scalar")
COMPONENT_DIMS = ("component", "tcomponent")


def _component_dim_for(labels):
    labels = tuple(sorted(labels))
    if set(labels) <= set(CART):
        return "component"
    if set(labels) <= set(TENSOR):
        return "tcomponent"
    raise ValueError(f"No component dimension for labels {labels}")


# --------------------------------------------------------------------------
# Conversion at the boundary.
# --------------------------------------------------------------------------
def to_dataset(frame: pd.DataFrame) -> xr.Dataset:
    """Convert an (M, C, S) frame into a Dataset, one variable per M.

    Each variable gets only the dimensions it has: no ``species`` when its S
    labels are all empty, no component dimension when its C labels are all
    empty. Within a variable, absent (C, S) combinations are NaN-padded
    (ragged species per variable). Units from the registry go into attrs.
    This copies once: each variable is a fresh contiguous array.
    """
    if list(frame.columns.names) != ["M", "C", "S"]:
        raise ValueError(f"Expected (M, C, S) columns, got {frame.columns.names}")
    time = frame.index.rename("time")
    data_vars = {}
    for m in frame.columns.unique(level="M"):
        sub = frame.xs(m, axis=1, level="M")
        cs = sub.columns.unique(level="C").tolist()
        ss = sub.columns.unique(level="S").tolist()
        has_c = cs != [""]
        has_s = ss != [""]
        full = pd.MultiIndex.from_product([cs, ss], names=["C", "S"])
        arr = sub.reindex(columns=full).to_numpy().reshape(len(time), len(cs), len(ss))
        dims, coords = ["time"], {"time": time}
        if has_c:
            cdim = _component_dim_for(cs)
            dims.append(cdim)
            coords[cdim] = cs
        else:
            arr = arr[:, 0, :]
        if has_s:
            dims.append("species")
            coords["species"] = ss
        else:
            arr = arr[..., 0]
        q = QUANTITIES.get(m)
        attrs = {} if q is None else {"units_tex": q.units, "si": q.si}
        data_vars[m] = xr.DataArray(
            np.ascontiguousarray(arr), dims=dims, coords=coords, attrs=attrs
        )
    return xr.Dataset(data_vars)


# --------------------------------------------------------------------------
# The seams.
# --------------------------------------------------------------------------
def select(da: xr.DataArray, key, dim: str):
    """``Core._select``: label(s) ``key`` on the named dimension.

    One label drops the dimension; a list keeps it, in the order given.
    """
    if dim not in da.dims:
        raise ValueError(f"Expected dimension {dim!r}; this has {list(da.dims)}")
    labels = da.indexes[dim]
    keys = list(key) if isinstance(key, (list, tuple, pd.Index, np.ndarray)) else [key]
    absent = [k for k in keys if k not in labels]
    if absent:
        raise KeyError(f"Unknown {dim} {absent[0]!r}. Available: {labels.tolist()}")
    return da.sel({dim: key})


def component_dim(da: xr.DataArray) -> str:
    dims = [d for d in COMPONENT_DIMS if d in da.dims]
    if len(dims) != 1:
        raise ValueError(f"Expected one component dimension; {list(da.dims)}")
    return dims[0]


def component_reduce(da: xr.DataArray, how: str = "sum", dim: str | None = None):
    """``Core._component_reduce``: strict, NaN where any component is."""
    dim = dim or component_dim(da)
    if how == "all":
        # xarray's all() has no skipna; NaN is truthy, as in numpy.
        return da.all(dim)
    return getattr(da, how)(dim, skipna=False)


def species_total(da: xr.DataArray):
    """``Core._species_total``: species present, NaN where none is."""
    return da.sum("species", min_count=1)


def mask_invalid_species(ds: xr.Dataset, species) -> xr.Dataset:
    """``Plasma._mask_invalid_species``: a species with any missing moment is
    NaN in every moment at that time."""
    parts = []
    for m in ("n", "v", "w"):
        da = ds[m].sel(species=list(species))
        if "tcomponent" in da.dims:
            da = da.sel(tcomponent=["par", "per"])
        other = [d for d in da.dims if d not in ("time", "species")]
        parts.append(da.isnull().any(other) if other else da.isnull())
    invalid = xr.concat(parts, "moment").any("moment")
    out = ds.copy()
    for m, da in ds.data_vars.items():
        if "species" in da.dims:
            bad = invalid.reindex(species=da.species, fill_value=False)
            out[m] = da.where(~bad)
    return out


# --------------------------------------------------------------------------
# Vector.
# --------------------------------------------------------------------------
def mag(vec: xr.DataArray) -> xr.DataArray:
    cart = select(vec, list(CART), "component")
    return np.sqrt(component_reduce(cart**2)).rename("mag")


def rho_xy(vec):
    xy = select(vec, ["x", "y"], "component")
    return np.sqrt(component_reduce(xy**2)).rename("rho")


def colat(vec):
    out = np.rad2deg(np.arctan2(rho_xy(vec), select(vec, "z", "component")))
    return out.drop_vars("component", errors="ignore").rename("colat")


def lat(vec):
    out = np.rad2deg(np.arctan2(select(vec, "z", "component"), rho_xy(vec)))
    return out.drop_vars("component", errors="ignore").rename("lat")


def lon(vec):
    out = np.rad2deg(
        np.arctan2(select(vec, "y", "component"), select(vec, "x", "component"))
    )
    return out.drop_vars("component", errors="ignore").rename("lon")


def uv(vec):
    return select(vec, list(CART), "component") / mag(vec)


def project(vec, other, join="outer"):
    """``Vector.project``: par and per components of ``vec`` along ``other``.

    pandas aligns on the union of the two indices; xarray's default
    arithmetic join is inner, so ``join="outer"`` is passed to match.
    """
    with xr.set_options(arithmetic_join=join):
        u = uv(other)
        cart = select(vec, list(CART), "component")
        par = component_reduce(cart * u)
        per = np.sqrt(component_reduce((cart - u * par) ** 2))
    return xr.Dataset({"par": par, "per": per})


# --------------------------------------------------------------------------
# Ion and Plasma.
# --------------------------------------------------------------------------
_UNITS = swp.core.units_constants.Units()
_CONST = swp.core.units_constants.Constants()


def pth(ds: xr.Dataset, species) -> xr.DataArray:
    """Per-species thermal pressure, 0.5 rho w^2, in display units."""
    sp = list(species)
    m_in_mp = xr.DataArray(
        _CONST.m_in_mp.loc[sp].to_numpy(), dims="species", coords={"species": sp}
    )
    rho = select(ds["n"], sp, "species") * m_in_mp * _UNITS.rho
    w = select(ds["w"], sp, "species") * _UNITS.w
    return ((0.5 / _UNITS.pth) * w**2 * rho).rename("pth")


_EXP = xr.DataArray([-1.0, 1.0], dims="tcomponent", coords={"tcomponent": ["par", "per"]})


def anisotropy(p: xr.DataArray) -> xr.DataArray:
    """R = per / par, as the seam computes it: product over C of pth**[-1, 1]."""
    p = select(p, ["par", "per"], "tcomponent")
    return component_reduce(p**_EXP, "prod").rename("R")


def ion_R(ds, s):
    return anisotropy(select(pth(ds, [s]), s, "species"))


def plasma_R(ds, *species):
    """``Plasma.R``: one "a+p1" string sums pth over species first."""
    if len(species) == 1:
        sp = sorted(species[0].split("+"))
        return anisotropy(species_total(pth(ds, sp))).rename(species[0])
    return anisotropy(pth(ds, sorted(species)))
