<!--
Spent-When: PERMANENT(the author decides the xarray question and the spike branch is deleted)
Supersedes: none
-->
# xarray spike: the (M, C, S) seams on named dimensions

Exploratory evidence for the data-model decision. Never merged. Labels: **[measured]** means
run here, with the script named; **[inferred]** means reasoned from named premises.

Environment: throwaway clone of the `solarwindpy` env with xarray 2026.9.0, pint 0.26.2,
pint-xarray 0.6.1, h5netcdf (added for the IO probe); pandas 3.1.0, numpy 2.5.4. The
cloned env's editable install points at the main checkout, so every script runs with
`PYTHONPATH` set to this checkout and `xrseams.py` asserts `solarwindpy` imports from it.

## Recommendation

Keep the (M, C, S) pandas frame behind the seams; do not migrate `core` to xarray now.
Confidence: moderate. The deciding evidence:

- Equivalence is achievable and was achieved [measured], so xarray is not ruled out on
  correctness.
- It buys no speed: parity within about 20% either way at 1e6 rows [measured].
- The readability win is real but small once the seams exist. `da.sum("species", min_count=1)`
  names its dimension, but so does `_species_total(frame)` today. The pandas seam block in
  `base.py` is 136 lines with docstrings; the xarray seams are 27 non-blank lines with short docstrings [measured line counts].
  The seams already deliver the author's principle (every operation names its dimension) to
  every caller [inferred from the call-site counts below: every core reduction goes through them].
- The costs are structural: two component dimensions, list selections that copy, an inner
  default join, a new IO dependency, and about 350 lines of core and core-test code touching
  MultiIndex structure directly [measured counts; the effort they imply is inferred].

What would change the answer: wanting units carried through `core` (the one qualitative gain,
section 5), or wanting netCDF as the on-disk format. If either becomes a goal, the seams make
the migration a bounded rewrite of `base.py` plus the sites counted in section 4.

## 1. What was built

`xrseams.py`: `to_dataset(frame)` (one variable per M, each with only the dimensions it has,
registry units in attrs) and the seams `select(da, key, dim)`,
`component_reduce(da, how)` (`skipna=False`), and `species_total(da)` (`min_count=1`).
On top of these: `mask_invalid_species`, Vector `mag`, `rho`, `colat`, `lat`, `lon`, `uv`,
`project` (par and per), `pth`, Ion `R`, and Plasma `R` for `"a+p1"` and for `("a", "p1")`.

## 2. Equivalence [measured, `check_equivalence.py`]

There are 42 comparisons against the real pandas classes, on the clean example and on a
masked copy. The masked copy has these NaNs:

- row 0: one `w per` of `a`, so Plasma masks all of `a` and the a+p1 total is p1 alone;
- row 1: `n` of `a` and `v x` of `p1`, so both species are masked and the total is NaN;
- row 2: `b z`, so the strict magnitude and the projection are NaN.

Results:

- NaN placement is identical in all 42.
- 32 are bit-identical (masking, every Vector quantity, both projection components).
- The other 10 (`pth`, Ion and Plasma `R`) differ by at most 1.8e-16 relative. That is
  multiplication order, about 1 ulp.
- xarray `mask_invalid_species` applied to the raw frame reproduces Plasma's load-time
  masking exactly.

These checks also discriminate:

- A plain `sum("species")` without `min_count` gives 0.0 at row 1, where pandas gives NaN.
- Projecting onto a `b` with one row fewer gives 3 rows in pandas (union), 2 in xarray's
  default inner join, and 3 with `join="outer"`.

## 3. Performance and memory [measured, `bench.py`]

Seconds per call, best of 7. The pandas side calls the real classes, built outside the timed
region. Two runs agreed to within the spread shown.

| operation | 3 rows pandas | 3 rows xarray | 1e6 rows pandas | 1e6 rows xarray | pandas/xarray at 1e6 |
|---|---|---|---|---|---|
| `b.mag` | 1.8e-4 | 1.8e-4 | 9.5e-3 | 7.9e-3 | 1.19 to 1.25 |
| `v.project(b)["par"]` | 1.2e-3 | 1.3e-3 | 3.2e-2 | 3.5e-2 | 0.85 to 0.92 |
| `Ion(p1).R` | 9.8e-4 | 1.1e-3 | 2.1e-2 | 2.2e-2 | 0.93 to 1.03 |
| `Plasma.R("a+p1")` | 2.4e-3 | 1.2e-3 | 9.8e-2 | 8.1e-2 | 1.21 to 1.22 |

The boundary costs:

- `to_dataset(plasma.data)` costs 4.7e-2 s at 1e6 rows. This is one full copy: the Dataset
  shares no memory with the frame.
- `mag.to_series()` costs 4.6e-4 s and copies, because pandas 3's Series constructor copies.
- Footprint: 248 MB for the frame and 256 MB for the Dataset. The difference is the 8 MB time
  coordinate. The example data has no ragged padding.

Views, checked with `np.shares_memory` (block-wise on the pandas side, since `to_numpy()`
copies a multi-block frame):

- Scalar-label and slice `.sel` in xarray are views, on component, on species, and on both.
- **xarray list `.sel` copies** (fancy indexing), for `component=["x","y"]` and
  `species=["a","p1"]`.
- The pandas seam's list selections *share* memory under pandas 3 copy-on-write. So the view
  property CLAUDE.md protects is weaker under xarray on exactly the path `cartesian`, `rho`
  and the `["par","per"]` selection use. Contiguous label slices would avoid the copy;
  arbitrary lists cannot.

## 4. Blast radius [measured line counts; migration effort inferred]

Seam call sites in `solarwindpy/core` outside `base.py` (`git grep -F -c '<name>(' -- solarwindpy/core`):

| seam | lines | where |
|---|---|---|
| `_select(` | 30 | plasma 17, spacecraft 6, alfvenic_turbulence 3, ions 2, vector 2 |
| `_component_reduce(` | 22 | alfvenic_turbulence 8, plasma 7, vector 5, ions 1, spacecraft 1 |
| `_species_total(` | 10 | plasma 10 |

The 62 call sites keep their shape under xarray: only the seam bodies change [inferred].

Structural MultiIndex access left in `core`, which would be rewritten (the union of
`MultiIndex|from_tuples|from_product|.xs(|level="[MCS]"|names=["M"|.loc[:, (|columns.names|columns.levels|get_level_values|IndexSlice|reorder_levels|.loc[:, "`
in `git grep -e`): **94 lines**. By pattern:

- `pd.concat`: 19, 16 of them in plasma, which builds (C, S) frames per species;
- `MultiIndex`: 22;
- `level="C"/"S"`: 16;
- `.xs(`: 14;
- `.loc[:, "v"]`-style positional M access: 11 (ions 3, plasma 3, alfvenic_turbulence 3,
  spacecraft 2);
- `sort_index(axis=1)`: 10;
- `level="M"`: 8;
- `get_level_values`: 6;
- `reorder_levels`: 4;
- `IndexSlice`: 2.

These lines overlap. The concentration is `plasma.py`: the per-species `pd.concat(...,
names=["S"])` then `reorder_levels(["C","S"])` pattern in `w`, `pth`, `T` and the rest,
which a Dataset replaces with one `.sel(species=...)`.

Tests in `tests/core` that construct or inspect MultiIndex frames, with the same pattern
(the one above, without `IndexSlice`, `reorder_levels` and the M-string `.loc`):

- **255 lines in 14 files** out of 8749 lines and 338 test functions.
- By file: test_plasma 148, test_quantities 27, test_abundances 14, test_plasma_io 11,
  test_base 11, test_alfvenic_turbulence 11, test_spacecraft 10, test_ions 9.

Outside `core`, the same pattern hits 34 lines in 9 `solarwindpy/` files (plotting and the
other pandas consumers, which stay on pandas through `.to_dataframe()`) and 32 lines in 10
test files.

Migration estimate [inferred from the counts above]:

- Rewrite the `base.py` seam block.
- Rewrite about 94 structural lines in core, mostly in plasma.
- Rewrite the IO path.
- Change about 255 test lines, most of them in test_plasma.
- The 62 seam call sites need little change.
- About 66 consumer lines stay pandas only if `Plasma.data` keeps returning an (M, C, S)
  frame, which means a `to_dataframe` shim that rebuilds the MultiIndex and copies on every
  access.

## 5. pint-xarray units [measured, `units_pint.py`]

- `pth = 0.5 * rho * w**2` on quantified `n` (cm^-3) and `w` (km/s), with `.pint.to("pPa")`,
  needs none of the `units.rho`, `units.w` and `units.pth` coefficients. It matches pandas
  `Ion.pth` to 4.5e-16 relative.
- The species total with `min_count=1` keeps `picopascal`.
- **The seam's form of R fails under pint.** The product over C of `pth**[-1, +1]` raises
  `DimensionalityError`, because array exponents need a dimensionless base. Written as
  `per / par` it is dimensionless and matches `Ion.R` to 1.1e-16.

So units force some seam-shaped code back into named-label form, which arguably fits the
principle better [inferred]. The registry holds TeX and an `si` float, not pint strings, so
a units mapping is new surface. pint-xarray's single maintainer is a dependency risk
[from the earlier units spike].

## 6. What was awkward

- **Ragged components force two component dimensions** [measured]. A Dataset has one
  coordinate per dimension name, so `v` (x, y, z) and `w` (par, per, scalar) cannot share
  `component`. Outer-joining them to six labels makes the strict magnitude NaN at 3 of 3
  rows. The prototype uses `component` and `tcomponent`. A generic "reduce over C" then has
  to discover which one a variable carries (`component_dim`). The pandas level `C` is one
  name for both.
- **The M level becoming variables** [measured]. This is mostly natural. But the raw
  example's `b` also carries `mag_rms` and `theta_rms` under C, which fit neither component
  dimension; Plasma drops them today. Mixed scalar diagnostics under a vector M need their
  own variables.
- **Ragged species per variable** [inferred]. `b` has no species, which is fine because
  variables carry only their own dimensions. A species missing from one variable but present
  in others is NaN-padded within that variable. `min_count=1` and the strict reduce both
  handle that correctly.
- **Alignment default** [measured]. xarray arithmetic is an inner join by default. pandas
  `project` returns the union. Matching it needs `xr.set_options(arithmetic_join="outer")`
  at every binary op site, or rows silently drop.
- **List selections copy** (section 3).
- **IO** [measured]:
  - The env had no netCDF4 or h5netcdf. The scipy engine (netCDF3) refuses int64 time.
  - With h5netcdf the Dataset round-trips `identical`.
  - `Plasma.save` writes PyTables HDF5 (`FC`, `SC` groups). xarray opens that file, but sees
    only PyTables internals (`axis0_level0`, `block0_items_*`). Existing files need
    `pd.read_hdf` then `to_dataset`.
  - Writing netCDF adds a dependency and a second on-disk format.
- `"all"` reductions [inferred]. xarray's `.all` has no `skipna`, and NaN is truthy. The one
  core use (`plasma.py:1341`, on a boolean `notna()` frame) is unaffected.

## Reproduce

```bash
cd <spike checkout>
PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/check_equivalence.py
PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/bench.py
PYTHONPATH=$PWD conda run -n swp-xarray-spike python spike/xarray/units_pint.py
```
