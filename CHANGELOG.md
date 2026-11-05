# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A quickstart page that runs end to end on `solarwindpy.examples.load_plasma`: the
  `M`/`C`/`S` columns, derived quantities with their units, an `"a+p1"` total, a `Hist2D`
  and a `Line` fit's `results`. It replaces the tutorial stub.

### Changed

- `pre-commit install` now installs the commit-message hook as well as the pre-commit hook
  (`default_install_hook_types` in `.pre-commit-config.yaml`), so the conventional-commit
  check runs without a separate `pre-commit install --hook-type commit-msg`.

## [0.4.0] - 2026-11-05

### Changed - BREAKING CHANGES

- One import path per public object: every public object is imported from the module that
  defines it, e.g. `from solarwindpy.core.plasma import Plasma` or
  `solarwindpy.plotting.hist2d.Hist2D`. Packages no longer re-export objects; their
  `__all__` lists submodules (and objects the package file itself defines, such as
  `fitfunctions.available`). `solarwindpy.pp` (for `solarwindpy.plotting`) is the one
  temporary nickname. `plotting/histograms.py` and `plotting/agg_plot.py` are removed. Two
  misspelled names are corrected and several internal helpers are private. No aliases are
  kept; an old path raises `AttributeError` or `ImportError`. Every removed 0.3.0 path and
  its replacement:

  | Old path | New path |
  |---|---|
  | `solarwindpy.units_constants` | `solarwindpy.core.units_constants` |
  | `solarwindpy.base` | `solarwindpy.core.base` |
  | `solarwindpy.vector` | `solarwindpy.core.vector` |
  | `solarwindpy.tensor` | `solarwindpy.core.tensor` |
  | `solarwindpy.ions` | `solarwindpy.core.ions` |
  | `solarwindpy.plasma` | `solarwindpy.core.plasma` |
  | `solarwindpy.spacecraft` | `solarwindpy.core.spacecraft` |
  | `solarwindpy.alfvenic_turbulence` | `solarwindpy.core.alfvenic_turbulence` |
  | `solarwindpy.Plasma` | `solarwindpy.core.plasma.Plasma` |
  | `solarwindpy.at` | `solarwindpy.core.alfvenic_turbulence` |
  | `solarwindpy.sc` | `solarwindpy.core.spacecraft` |
  | `solarwindpy.sa` | `solarwindpy.solar_activity` |
  | `solarwindpy.Hist1D` | `solarwindpy.plotting.hist1d.Hist1D` |
  | `solarwindpy.Hist2D` | `solarwindpy.plotting.hist2d.Hist2D` |
  | `solarwindpy.TeXlabel` | `solarwindpy.plotting.labels.base.TeXlabel` |
  | `solarwindpy.core.Base` | `solarwindpy.core.base.Base` |
  | `solarwindpy.core.Core` | `solarwindpy.core.base.Core` |
  | `solarwindpy.core.Vector` | `solarwindpy.core.vector.Vector` |
  | `solarwindpy.core.Tensor` | `solarwindpy.core.tensor.Tensor` |
  | `solarwindpy.core.Ion` | `solarwindpy.core.ions.Ion` |
  | `solarwindpy.core.Plasma` | `solarwindpy.core.plasma.Plasma` |
  | `solarwindpy.core.Spacecraft` | `solarwindpy.core.spacecraft.Spacecraft` |
  | `solarwindpy.core.Units` | `solarwindpy.core.units_constants.Units` |
  | `solarwindpy.core.Constants` | `solarwindpy.core.units_constants.Constants` |
  | `solarwindpy.core.AlfvenicTurbulence` | `solarwindpy.core.alfvenic_turbulence.AlfvenicTurbulence` |
  | `solarwindpy.fitfunctions.FitFunction` | `solarwindpy.fitfunctions.core.FitFunction` |
  | `solarwindpy.fitfunctions.TrendFit` | `solarwindpy.fitfunctions.trend_fits.TrendFit` |
  | `solarwindpy.fitfunctions.Exponential` | `solarwindpy.fitfunctions.exponentials.Exponential` |
  | `solarwindpy.fitfunctions.Gaussian` | `solarwindpy.fitfunctions.gaussians.Gaussian` |
  | `solarwindpy.fitfunctions.Line` | `solarwindpy.fitfunctions.lines.Line` |
  | `solarwindpy.fitfunctions.PowerLaw` | `solarwindpy.fitfunctions.power_laws.PowerLaw` |
  | `solarwindpy.fitfunctions.Moyal` | none (removed; see Removed) |
  | `solarwindpy.fitfunctions.moyal` | none (removed; see Removed) |
  | `solarwindpy.fitfunctions.exponentials.ExponentialCDF` | none (removed; see Removed) |
  | `solarwindpy.fitfunctions.FitFunctionError` | `solarwindpy.fitfunctions.core.FitFunctionError` |
  | `solarwindpy.fitfunctions.InsufficientDataError` | `solarwindpy.fitfunctions.core.InsufficientDataError` |
  | `solarwindpy.fitfunctions.FitFailedError` | `solarwindpy.fitfunctions.core.FitFailedError` |
  | `solarwindpy.fitfunctions.InvalidParameterError` | `solarwindpy.fitfunctions.core.InvalidParameterError` |
  | `solarwindpy.plotting.subplots` | `solarwindpy.plotting.tools.subplots` |
  | `solarwindpy.plotting.save` | `solarwindpy.plotting.tools.save` |
  | `solarwindpy.plotting.agg_plot` | `solarwindpy.plotting.base` (`BinnedPlot`) and `solarwindpy.plotting.binning` |
  | `solarwindpy.plotting.agg_plot.AggPlot` | `solarwindpy.plotting.base.BinnedPlot` |
  | `solarwindpy.plotting.histograms.agg_plot` | `solarwindpy.plotting.base` (`BinnedPlot`) and `solarwindpy.plotting.binning` |
  | `solarwindpy.plotting.histograms.hist1d` | `solarwindpy.plotting.hist1d` |
  | `solarwindpy.plotting.histograms.hist2d` | `solarwindpy.plotting.hist2d` |
  | `solarwindpy.plotting.histograms.AggPlot` | `solarwindpy.plotting.base.BinnedPlot` |
  | `solarwindpy.plotting.histograms.Hist1D` | `solarwindpy.plotting.hist1d.Hist1D` |
  | `solarwindpy.plotting.histograms.Hist2D` | `solarwindpy.plotting.hist2d.Hist2D` |
  | `solarwindpy.plotting.base.PlotWithZdata` | `solarwindpy.plotting.base.ColorPlot` |
  | `solarwindpy.plotting.base.CbarMaker` | `solarwindpy.plotting.base.ColorPlot` (merged into it) |
  | `solarwindpy.plotting.labels.TeXlabel` | `solarwindpy.plotting.labels.base.TeXlabel` |
  | `solarwindpy.plotting.labels.Vsw` | `solarwindpy.plotting.labels.special.Vsw` |
  | `solarwindpy.plotting.labels.Count` | `solarwindpy.plotting.labels.special.Count` |
  | `solarwindpy.plotting.labels.Ion` | `solarwindpy.plotting.labels.composition.Ion` |
  | `solarwindpy.plotting.labels.ChargeStateRatio` | `solarwindpy.plotting.labels.composition.ChargeStateRatio` |
  | `solarwindpy.plotting.labels.ElementalAbundance` | `solarwindpy.plotting.labels.elemental_abundance.ElementalAbundance` |
  | `solarwindpy.plotting.labels.available_labels` | `solarwindpy.plotting.labels.available` |
  | `solarwindpy.plotting.tools.multipanel_figure_shared_cbar` | `solarwindpy.plotting.tools.build_ax_array_with_common_colorbar` |
  | `solarwindpy.solar_activity.ssn` | `solarwindpy.solar_activity.sunspot_number` |
  | `solarwindpy.solar_activity.lisird.LISIRD` | none (removed; see Removed) |
  | `solarwindpy.solar_activity.lisird.ExtremaCalculator` | none (removed; see Removed) |
  | `solarwindpy.solar_activity.sunspot_number.sidc.Base` | `solarwindpy.solar_activity.base.Base` |
  | `solarwindpy.core.alfvenic_turbulence.AlvenicTurbAveraging` | `solarwindpy.core.alfvenic_turbulence.AlfvenicTurbAveraging` |
  | `solarwindpy.plotting.labels.special.ComparisonLable` | `solarwindpy.plotting.labels.special.ComparisonLabel` |
  | `solarwindpy.fitfunctions.core.Observations` | `solarwindpy.fitfunctions.core._Observations` (private) |
  | `solarwindpy.fitfunctions.core.UsedRawObs` | `solarwindpy.fitfunctions.core._UsedRawObs` (private) |
  | `solarwindpy.fitfunctions.core.InitialGuessInfo` | `solarwindpy.fitfunctions.core._InitialGuessInfo` (private) |
  | `solarwindpy.fitfunctions.core.ChisqPerDegreeOfFreedom` | `solarwindpy.fitfunctions.core._ChisqPerDegreeOfFreedom` (private) |
  | `solarwindpy.fitfunctions.core.FitBounds` | `solarwindpy.fitfunctions.core._FitBounds` (private) |
  | `solarwindpy.plotting.labels.base.MCS` | `solarwindpy.plotting.labels.base._MCS` (private) |
  | `solarwindpy.plotting.base.DataLimFormatter` | none (removed; nothing used it) |
  | `solarwindpy.plotting.tools.calculate_nrows_ncols` | none (removed; it had no callers) |
  | `solarwindpy.plotting.spiral.InitialSpiralEdges` | `solarwindpy.plotting.spiral._InitialSpiralEdges` (private) |
  | `solarwindpy.plotting.spiral.SpiralMeshBinID` | `solarwindpy.plotting.spiral._SpiralMeshBinID` (private) |
  | `solarwindpy.plotting.spiral.SpiralFilterThresholds` | `solarwindpy.plotting.spiral._SpiralFilterThresholds` (private) |
  | `solarwindpy.plotting.spiral.get_counts_per_bin` | `solarwindpy.plotting.spiral._get_counts_per_bin` (private) |
  | `solarwindpy.plotting.spiral.calculate_bin_number_with_numba` | `solarwindpy.plotting.spiral._calculate_bin_number_with_numba` (private) |
  | `solarwindpy.plotting.labels.species_translation` | none (removed; it was `labels.base._run_species_substitution`) |

- Python 3.12 or newer is required (was 3.11).
- pandas 3 is required: the supported range is `pandas>=3,<4` (was `>=2.0`). The suite
  also passes on pandas 2.2 and 2.3, but only one major version is tested and declared.
- Other dependency floors: `scipy>=1.16` (was `>=1.13`), `matplotlib>=3.10` (was `>=3.5`)
  and `astropy>=8` (was `>=5.0`), so the download cache has one location,
  `~/.cache/solarwindpy`. PyTables (`tables`), which `Plasma.save` and
  `Plasma.load_from_file` need, is required. `h5py` and `pyyaml` are no longer runtime
  dependencies; `pyyaml` moves to the `test` and `dev` extras.
- `pyproject.toml` is the only dependency declaration. `requirements.txt`,
  `requirements-dev.lock`, and `docs/requirements.txt` are removed; install with
  `pip install -e ".[dev]"` (or `".[docs]"` for documentation). `solarwindpy.yml`
  remains the conda development environment.
- The in-repository conda recipe (`recipe/`) is removed. The conda-forge feedstock,
  `conda-forge/solarwindpy-feedstock`, is the only recipe.
- Fit-function help text inheritance uses `docstring-inheritance` 3.x (`>=3.0,<4`; was
  `>=2.2.0,<3.0`). Importing `solarwindpy` sets `DOCSTRING_INHERITANCE_ENABLE=1` unless
  the variable is already set, and warns if `docstring_inheritance` was imported earlier
  with inheritance off.
- Plot value limits (`alim`) are reworked:
  - `limit_color_norm` is removed from `Hist2D.make_plot` and `Hist2D.plot_contours`, and
    from `SpiralPlot2D.make_plot` and `SpiralPlot2D.plot_contours`. To limit a plot to the
    bulk of its values use `set_alim(lower, upper, kind="quantile")`, e.g.
    `set_alim(0.01, 0.99, kind="quantile")`, which masks bins outside those quantiles
    instead of clipping the colour scale. Passing `limit_color_norm=` now fails in
    matplotlib (`AttributeError`) or with `ValueError` in `SpiralPlot2D`;
    `Hist2D.plot_contours` only warns that the keyword was unused.
  - Removing `limit_color_norm` and the contour-labelling parameters (see Removed) moves
    every later positional parameter of those methods left, e.g.
    `make_plot(ax, cbar, cbar_kwargs, fcn, alpha_fcn)` and
    `Hist2D.plot_contours(ax, cbar, cbar_kwargs, fcn, plot_edges, ...)`. Pass them by
    keyword to be safe. `plot_contours` takes `levels` as a named last parameter.
  - `Hist1D` no longer has `alim` or `set_alim`; it never applied it. `SpiralPlot2D`
    and `Scatter` gain `alim` and `set_alim`.
  - `Hist1D.clim`, `Hist2D.clim` and `Hist2D.alim` are `RangeLimits`, as
    `SpiralPlot2D.clim` already was, not tuples; the new `alim` of `SpiralPlot2D` and
    `Scatter` is one too.
  - `Hist2D.plot_contours` colours densities (`axnorm` of `"d"`, `"cd"`, `"rd"`) with
    a log norm by default, as `make_plot` already did, so density contours default to
    log colour bands. `SpiralPlot2D.plot_contours` with `axnorm="d"` likewise colours on
    a `LogNorm` unless `norm=` is passed.
- `Probability`, `CountOther`, `MathFcn` and `AbsoluteValue` in
  `solarwindpy.plotting.labels.special` raise `TypeError` at construction when
  `other_label` is a plain `str`. A string was never usable (it failed later with
  `AttributeError`); wrap raw TeX in `ManualLabel`.
- `Hist1D` no longer accepts `axnorm` words beyond `"d"`/`"t"` (e.g. `"density"`, which
  was truncated to `"d"`). An invalid `axnorm` on `Hist1D` or `Hist2D` raises `TypeError`
  (not a string or None) or `ValueError` (unknown key) instead of `AssertionError`.
- A species' moments stand or fall together: where any of its density, velocity
  components or thermal-speed components is missing, `Plasma.set_data` masks every
  measurement of that species to NaN at that time and logs a warning with the count per
  species. The new User Guide page "Missing data" states the missing-data rules.
- `GaussianLn` raises `ValueError` when any used x is ≤ 0 (ln x is undefined there), at
  construction and when `set_fit_obs` selects new observations, instead of fitting
  with `p0` None.
- `Plasma` puts its data in time order. Rows earlier than the row before them log one
  warning with their count and first positions, then the data are sorted with a stable
  sort, so rows sharing a timestamp keep their order; methods may assume sorted data.
  Spacecraft and auxiliary data passed with the plasma on the same index are sorted with
  it, without a second warning. Repeated timestamps log a warning and are kept. A
  standalone `Spacecraft` sorts out-of-order data the same way, with one warning, and its
  `pos` and `v` do not repeat the order warning.
- Missing timestamps (`NaT`) are refused: `Plasma`, `Spacecraft`, `Ion`, `Vector`,
  `Tensor` and `BField` raise `ValueError: <Class> data time index has N of M timestamps
  missing (NaT); drop those rows first`, at construction and in `set_data`. They were
  previously kept, with an order warning.
- `Plasma.set_data`, `set_sc` and `set_aux` refuse data at other times than the plasma's
  with `ValueError` naming the row counts or the first differing row. `set_data` called
  directly sorts out-of-order rows with a warning. While spacecraft or auxiliary data are
  attached, it instead raises `ValueError` for rows out of order, since sorting would
  misalign the attached frames. It also raises then for rows at other times than the
  current index.
- `set_aux` refuses `NaT`. It reorders auxiliary data holding the plasma's times in
  another order to the plasma's, with a warning.
- `set_sc` and `set_aux` raise `ValueError` instead of `AssertionError` for a mismatched
  time index or wrong column-level names, and wrong level names in `Plasma` data raise
  `ValueError` instead of `KeyError`. Plasma data's levels may come in any order;
  spacecraft data's must be exactly `("M", "C")` and auxiliary data's `("M", "C", "S")`.
- `Plasma(...)`, `Plasma.set_data`, `Spacecraft(...)` and `Spacecraft.set_data` raise
  `TypeError: <X> data must be a pandas DataFrame, not <type>` for other input, instead
  of `AttributeError`.
- A `Vector`, `BField` or `Tensor` built from columns whose species level `S` holds more
  than one species raises `ValueError` naming them; previously a `Vector` silently
  computed `.mag`, `.rho`, `project` and `cos_theta` across every species. Select one
  species first, e.g. `data.xs("p1", axis=1, level="S")`.
- `Hist2D.take_data_in_yrange_across_x` raises `ValueError` ("Need left < right ..." or
  "Need bottom < top ...") for a zero-width or inverted range, instead of
  `AssertionError`.
- Every plot class (`Hist1D`, `Hist2D`, `BetaRPlot`, `Scatter`, `SpiralPlot2D`) draws its
  data through one path, a `BinnedData` it shares or builds from its own columns (see
  Added). Every output not listed here is unchanged:
  - `Hist1D` drops rows where x or y is NaN, as `Hist2D` does:
    - `Hist1D.data` and every `Hist1D` selection exclude those rows.
    - Edges from an integer or string `nbins` are computed from the remaining rows.
    - The `construct_cdf` docstring no longer says y is ignored: rows whose y is NaN are
      dropped, so their x is not in the CDF.
    - A `Hist1D` whose y is all NaN raises `ValueError` ("exclusively NaNs").
    - `project_1d(only_plotted=False)` no longer carries NaN-y placeholders. Its
      aggregates are unchanged.
  - One clip name, `clip`: the constructor keyword `clip_data` of `Hist1D`, `Hist2D`,
    `Scatter` and `SpiralPlot2D` (and so `BetaRPlot`) and the `set_data` keyword are
    `clip`. No `clip_data` alias is kept; `clip_data=` raises `TypeError`.
    `Base.clip_data`, the clipping function, keeps its name.
  - A plot's `clip` is a `ClipAxes(x, y, z)` record (z is used by `Scatter` only, whose
    `make_plot` clips every column), and the `clip` argument takes a scalar, applied to
    every binned axis, or a per-axis mapping such as `clip={"y": "u"}`. `Hist1D` clips x
    only. Test a field (`h.clip.y`), not the record: `ClipAxes(False, False)` is truthy.
  - `logx`, `logy` and `clip` default to None. Without a `BinnedData`, None means False,
    as before. With one passed as `nbins`, None inherits its setting for the column named
    like the input; an explicit, differing value raises `ValueError`, as does a non-None
    `bin_precision`. `BetaRPlot` defaults to log axes only when `nbins` is not a
    `BinnedData`.
  - A plot's `data` is built on each access. In-place edits to it no longer persist, and
    the arrays of its columns are read-only. A built plot is a snapshot: pandas
    copy-on-write keeps later edits to the caller's frame or Series out of it. One case
    is not guarded: writing into a NumPy array that a Series wraps without a copy
    (`pd.Series(arr, copy=False)`) after the plot is built changes its `data`, though not
    its bins.
  - `set_data` is private, `_set_data`, and called only by the constructor; a second call
    raises `ValueError`. To plot other data, build a new plot. The stale-plot case
    (`set_data` followed by `agg()` without rebinning, which raised `KeyError`) no longer
    exists. A subclass of `solarwindpy.plotting.base.Base` implements `_set_data`
    instead of `set_data`; no alias is kept.
  - The constructor bins: `Hist1D.calc_bins_intervals`, `Hist2D.calc_bins_intervals` and
    `make_cut` are removed. `SpiralPlot2D(..., min_per_bin=n)` builds its mesh in the
    constructor, replacing `SpiralPlot2D(...).initialize_mesh(min_per_bin=n)` and
    `build_grouped()`. `SpiralPlot2D.calc_initial_bins(nbins)` is removed; the initial
    edges are internal, and `initial_bins` still reads them.
  - Integer x or y with a log axis gives the float `log10` values. It previously raised a
    pandas 3 `TypeError`.
  - `SpiralPlot2D.make_plot` draws one `matplotlib.collections.PolyCollection` built from
    a single vertex array, instead of one `Rectangle` per cell gathered into a
    `PatchCollection`. Each cell's vertices are its mesh edges exactly, where a
    `Rectangle` placed its far corners at the lower-left corner plus the width and height.
    Colours and the cells drawn are unchanged.
  - Bins are stored once as an `IntervalIndex`: `intervals` and the levels of `agg()`'s
    index are `IntervalIndex`, not `CategoricalIndex`. `edges` is a float `pd.Index` of the
    bin edges. `Hist1D.categoricals` and `Hist2D.categoricals` are removed; use
    `intervals`.
  - `Hist2D.agg()` returns the full bin grid, one row per (x, y) bin pair, with NaN where a
    bin is empty, as its docstring states. It previously returned the occupied bins only,
    so the length of `agg()` changes for every caller, and a count grid with an empty bin
    is float. Values in occupied bins, the arrays `make_plot` and `plot_contours` draw, and
    every selection are unchanged.
  - `set_log` on a built plot raises `ValueError` if it would change the log of an axis
    its data and bins were built on (x for `Hist1D`; x and y for `Hist2D` and
    `SpiralPlot2D`). Build a new plot or `BinnedData` instead. Axes only drawn on a log
    scale (`Hist1D` y, `Scatter`) can still be changed, and repeating the current
    setting is allowed.
  - `Hist2D.project_1d(..., bin_precision=...)` raises `ValueError`: the projection's
    bins are the parent's and are not re-rounded.
- Plot constructor signatures (pass arguments by keyword to be safe):
  - `Hist2D(x, y, z, axnorm, logx, logy, clip_data, nbins, bin_precision)` is
    `Hist2D(x, y, z, logx, logy, axnorm, clip, nbins, bin_precision, mask)`.
  - `SpiralPlot2D(x, y, z, logx, logy, initial_bins, clip_data)` is
    `SpiralPlot2D(x, y, z, logx, logy, axnorm, clip, initial_bins, min_per_bin, mask, *,
    progress)`.
  - `Scatter(x, y, z, clip_data)` is `Scatter(x, y, z, logx, logy, clip, mask)`; `logx`
    and `logy` set the axis scales only.
- Plot methods return what they draw, with the colorbar last:
  - `Hist2D.make_plot`, `SpiralPlot2D.make_plot` and `BetaRPlot.make_plot` return
    `(ax, mappable, cbar_or_None)` instead of `(ax, cbar_or_mappable)` (`(ax, cbar)` for
    `BetaRPlot`).
  - `Scatter.make_plot` returns `(ax, collection, cbar_or_None)` instead of
    `(ax, cbar)`.
  - `Hist2D.plot_contours` and `SpiralPlot2D.plot_contours` return
    `(ax, qset, cbar_or_None)` instead of `(ax, lbls, cbar_or_mappable, qset)`.
  - `Hist1D.make_plot` returns `(ax, line, band_or_None, None)` instead of
    `(ax, container)` or `(ax, (line, band))`; with `plot_window`, `line` is a `Line2D`,
    not a one-item list.
  - `IndicatorPlot.make_plot` and `SSNPlot.make_plot` return `(ax, line, None)` instead
    of nothing.
  - `StabilityContours.plot_contours` returns `(ax, lines, None)`, with `lines` a dict of
    `(growth_rate, instability)` to `Line2D`, and `SIDC.plot_on_colorbar` returns
    `(cax, underlay, overlay, None)`; both returned nothing.
- A plot's `path` is a read-only property derived on each read (`set_path` is removed;
  see Removed):
  - It follows `set_log`, `set_labels` and `set_axnorm` made after construction, instead
    of keeping the value from build time.
  - `Scatter.path` is `Scatter/x/y[/z]/linX-linY` instead of a bare scale tag
    (`linX-linY`).
  - `Hist1D.path` is `Hist1D/x/count/linX-linY[-Tnorm]`, with both axis scales, instead
    of `Hist1D/x/count[/Tnorm]/linX`.
  - A plot without a z label leaves the z part out of its path, instead of writing a
    literal `z`.
- `SpiralPlot2D` no longer logs its mesh-building progress table as warnings; the default
  is silent. `SpiralPlot2D(..., progress=True)` writes the table to stderr, as
  `SpiralMesh.generate_mesh(progress=True)` does.
- `SpiralPlot2D.make_plot` ignores `alpha_fcn`, with a warning, on a count plot, as
  `Hist2D` does.
- Specific entropy is removed: `Ion.specific_entropy`, `Ion.S`, `Plasma.specific_entropy`,
  `Plasma.S` and `Units.specific_entropy`, with the `"S"` and `"entropy"` plot label keys.
  No alias is kept; the old names raise `AttributeError`. The name `S` collided with the
  species level of the column MultiIndex.
- Quantity names converge on one canonical short name per quantity, the same at every
  layer (method, Series name, column label, registry key). The short names already
  existed; the long aliases are removed with no deprecation shim:
  - `Units.temperature` -> `Units.T`, `Units.bfield` -> `Units.b`. Every `Units` field
    reads its default from `solarwindpy.core.quantities.QUANTITIES`, and `Units` gains
    fields for every quantity `Plasma` stores (`rho`, `w`, `dv`, `cs`, `ca`, `Wk`, `gse`,
    `hci`). Its constructor parameters are in a new order, `Units(gse, hci, distance2sun,
    b, n, rho, v, w, dv, cs, ca, pth, T, qpar, Wk, beta, lnlambda, nuc, nc)`; pass them by
    keyword. `Units().cfms` is removed.
  - `Plasma`: `number_density` -> `n`, `mass_density` -> `rho`, `velocity` -> `v`,
    `thermal_speed` -> `w`, `bfield` -> `b`, `sound_speed` -> `cs`,
    `kinetic_energy_flux` -> `Wk`, `temperature` -> `T`, `anisotropy` -> `R`,
    `heat_flux` -> `qpar`, `pdynamic` -> `pdv`, `spacecraft` -> `sc`,
    `auxiliary_data` -> `aux`. `afsq` and `caani` take `pdv=` instead of `pdynamic=`, and
    `Plasma.pdv(...).name` is `"pdv"`.
  - `Plasma.set_spacecraft` -> `Plasma.set_sc` and `Plasma.set_auxiliary_data` ->
    `Plasma.set_aux`; `Plasma(spacecraft=, auxiliary_data=)` -> `Plasma(sc=, aux=)`, as
    are the keywords `load_from_file` passes on; `Plasma.save(akey=)` and
    `Plasma.load_from_file(akey=)` -> `auxkey=`. The default file keys, and so saved
    files, are unchanged.
  - `Ion`: `number_density` -> `n`, `mass_density` -> `rho`, `velocity` -> `v`,
    `thermal_speed` -> `w`, `kinetic_energy_flux` -> `Wk`, `temperature` -> `T`,
    `anisotropy` -> `R` (Series name `"RT"` -> `"R"`); `Ion.set_species` ->
    `Ion._set_species` (private).
  - `Vector`: `magnitude` and `r` -> `mag`, `colatitude` -> `colat`, `latitude` -> `lat`,
    `longitude` -> `lon` (Series names follow), `unit_vector` -> `uv`; `BField.pressure`
    -> `pb`; `Tensor.magnitude` -> `mag`.
  - `Spacecraft`: `position` and `r` -> `pos` (`pos` is the position `Vector`, the `M`
    label the position is stored under; distance is `pos.mag`), `velocity` -> `v`,
    `carrington` -> `carr`. The label key `("pos", c, "")` renders `\mathbf{r}_c`.
  - `AlfvenicTurbulence`: `velocity` -> `v`, `bfield` -> `b`, `z_plus` -> `zp`,
    `z_minus` -> `zm`, `e_plus` -> `ep`, `e_minus` -> `em`, `kinetic_energy` -> `ev`,
    `magnetic_energy` -> `eb`, `total_energy` -> `etot`, `residual_energy` -> `eres`,
    `normalized_residual_energy` and `eres_norm` -> `sigma_r`,
    `normalized_cross_helicity` -> `sigma_c`, `alfven_ratio` -> `rA`,
    `elsasser_ratio` -> `rE`. `ep`, `em`, `ev`, `eb`, `etot`, `eres`, `sigma_r`,
    `sigma_c`, `cross_helicity`, `rA` and `rE`, and `Vector.cos_theta`, return Series
    named after the attribute (e.g. `turbulence.rA.name == "rA"`) instead of unnamed
    Series.
  - `AlfvenicTurbulence` and `AlfvenicTurbulence.set_data` take the `Spacecraft` for
    `raffaella_version` as `sc` instead of `sc_vector`, as does
    `Plasma.build_alfvenic_turbulence`, which forwards it. With `raffaella_version=True`,
    the only case that reads it, passing `sc_vector=` instead raises the existing
    `ValueError` asking for the SC-Sun distance.
  - `StabilityContours.plot_contours(plot_gamma=)` -> `plot_contours(growth_rate=)`; the
    `insta_params` index level `"Growth Rate"` -> `"growth_rate"`.
  - `StabilityCondition(growth_rate, beta, anisotropy)` ->
    `StabilityCondition(growth_rate, beta, R)`, and `StabilityCondition.anisotropy` ->
    `R`; `BetaRPlot(beta, ani, species)` -> `BetaRPlot(beta, R, species)`.
- Plot labels follow the quantity registry:
  - The TeX and units of each quantity live in `solarwindpy.core.quantities.QUANTITIES`;
    `plotting.labels.base._trans_measurement`, `_templates` and `_trans_units` are
    removed.
  - The label keys `("q", "par", s)` -> `("qpar", "", s)`, `("VDFratio", ...)` ->
    `("vdf_ratio", ...)`, and `xhel`, `ra` and `re` -> `cross_helicity`, `rA` and `rE`,
    matching `AlfvenicTurbulence.cross_helicity`, `rA` and `rE`.
  - `TeXlabel` renders the species `a_bimax` as `\alpha,\mathrm{bimax}`, `p_bimax` as
    `p,\mathrm{bimax}` (was `p`) and `pm` as `p,\mathrm{moment}`.
  - The magnetic-pressure label renders `P_B` instead of `p_B`.
  - Unit brackets in every label render as `\left[ \right]`.
  - `BetaRPlot` axis labels keep a fit species' `_bimax` suffix.
- The Earth equatorial radius and the solar radius moved from `Constants().misc`
  (`"Re [m]"`, `"Rs [m]"`) to the quantity registry, as `QUANTITIES["gse"].si` and
  `QUANTITIES["hci"].si`; `Constants().misc["Re [m]"]` and `Constants().misc["Rs [m]"]`
  raise `KeyError`. `Spacecraft.distance2sun` reads the radius from the registry.
- `StabilityCondition.stability_bin` is an integer Series, as documented, not float64.
- Fit-function parameters are renamed and reordered so that every model takes its
  amplitude `A` last. A positional `p0` or bounds, and positional arguments to
  `function`, follow the new order, and `popt`, `psigma` and the `results` columns list
  the parameters in it. Code that passes parameters by name needs only the renames:
  - `Exponential`: `f(x, c, A)` -> `f(x, k, A)`; the rate is `k`.
  - `ExponentialPlusC`: `f(x, c, A, d)` -> `f(x, k, y0, A)`; the rate is `k` and the
    additive constant `y0`. Code reading `popt["c"]` read the rate in 0.3.0; it now
    raises `KeyError`. Read `popt["k"]`.
  - `PowerLaw`: `f(x, A, b)` -> `f(x, alpha, A)`; the exponent is `alpha`.
  - `PowerLawPlusC`: `f(x, A, b, c)` -> `f(x, alpha, y0, A)`.
  - `PowerLawOffCenter`: `f(x, A, b, x0)` -> `f(x, alpha, x0, A)`.
  - `GaussianLn`: `m` and `s` -> `mu` and `sigma`. `GaussianLn.normal_parameters`
    returns `{"mean", "std"}`, not `{"mu", "sigma"}`, and the optional TeX report labels
    them mean(x) and std(x).
  - The TeX fit report (`TeX_popt`, annotations) writes the offset parameters of
    `ExponentialPlusC`, `PowerLawPlusC`, `PowerLawOffCenter` and `LineXintercept` as
    `y_0` and `x_0`, matching their model strings; `popt` keys are `x0` and `y0`.
- Fit results:
  - `FitFunction.combined_popt_psigma` -> `FitFunction.results`, a one-row (P, K) table
    with quality and status columns.
  - `FitFunction.make_fit(return_exception=True)` is removed: `make_fit()` raises after
    recording the failure; read `FitFunction.error` and `results[("status", "")]`.
  - A failed fit left no record; `results` now holds NaN values and status the exception
    class name, and calling the fit returns NaN.
  - Before a fit, `FitFunction.chisq_dof` and `FitFunction.initial_guess_info` raise
    `NotFittedError` instead of returning None, and every other fit result raises
    `NotFittedError` (an `AttributeError` subclass) naming `make_fit` instead of a bare
    `AttributeError`.
- `TrendFit` is rebuilt around bin fits and a trend fit:
  - `TrendFit(agged, trendfunc, trend_logx=False, ykey1d="mu", wkey1d="sigma",
    ffunc1d=None)` -> `TrendFit(agged, bin_function, trend_function, *, y, yerr,
    logx=False, bin_kwargs=None, trend_kwargs=None)`.
  - `make_ffunc1ds()`, `make_1dfits()`, `make_trend_func()` and `trend_func.make_fit()`
    -> `make_fit(bin_fit_kwargs=None, trend_fit_kwargs=None)`.
  - `popt_1d`, `psigma_1d` and `bad_fits` -> `bin_results` (failed bins are NaN rows with
    a status).
  - `ffuncs` -> `bin_fits`; `trend_func` -> `trend`; `ffunc1d_class` -> `bin_function`;
    `trendfunc_class` -> `trend_function`; `trend_logx` -> `logx`; `popt1d_keys` and
    `Popt1DKeys` -> `y` and `yerr`.
  - `plot_all_ffuncs` -> `plot_bin_fits`; `plot_all_popt_1d` -> `plot_bin_results`
    (`only_plot_data_in_trend_fit` -> `only_in_trend`; the `wkey` keyword goes);
    `plot_trend_and_resid_on_ffuncs(trend_kwargs, fit1d_kwargs)` ->
    `plot_trend_and_resid_on_bins(trend_plot_kwargs, bin_plot_kwargs)`;
    `plot_1d_popt_and_trend(kwargs_popt_1d=)` ->
    `plot_bin_results_and_trend(bin_plot_kwargs=)`.
  - `set_agged` and `set_fitfunctions` are removed; build a new `TrendFit` instead.
- `FFPlot.residuals` and `FFPlot.plot_residuals` (simple, percent and robust) return
  observed minus fitted, the sign of `FitFunction.residuals`; they returned model minus
  observed. Robust residuals are `-fit_result.fun`. `FFPlot` takes a required keyword-only
  `residuals_func`, which `FitFunction.plotter` supplies. `FFPlot.plot_residuals`
  draws the simple residuals by default (`kind="simple"`; was `"both"`).
- `AxesLabels` and `LogAxes` in `fitfunctions.plots` are the `plotting.base` classes. They
  remain importable from `fitfunctions.plots` but leave its `__all__`, so
  `from solarwindpy.fitfunctions.plots import *` no longer brings them.
- Hemispheric sunspot columns `totalstd_error`, `northstd_error` and `southstd_error` become
  `total_std_error`, `north_std_error` and `south_std_error`.
- `ActivityIndicator` subclasses call `self._interpolate(source_data, target_index)`, the
  shared engine; the abstract `interpolate_data` takes `(target_index, ...)`, matching how
  `SIDC` is called.
- SIDC sunspot-number data are cached in SolarWindPy's download cache
  (`~/.cache/solarwindpy`) instead of `~/solarwindpy/data/sidc/<key>/YYYYMMDD.csv`, and
  downloaded again once the cached copy is more than one day old. If that download fails,
  the cached series is loaded with a `StaleCacheWarning` naming its age.

### Changed

- A plot that drops rows no longer copies the kept rows' labels to aggregate, find bin
  edges or project. At 1M rows with 10% NaN, `Hist2D.project_1d` is about 25% faster,
  and `agg()` and construction about 15-20% faster.
- `FitFunction.rsq` returns NaN when the fitted `y` have no spread (a single point, or
  constant data), where R^2 is undefined. It previously divided by zero, warning and
  returning -inf or NaN.
- `Line.p0` and `LineXintercept.p0` return `None` (no initial estimate) for repeated `x`
  without a divide-by-zero warning. `LineXintercept.p0` also returns `None` when the
  estimated slope is zero, since a flat line has no x-intercept; it previously returned
  an x-intercept of -inf or NaN, and a NaN initial guess made `make_fit` fail.
- Every fit function's `p0` follows one contract, stated in `FitFunction.p0`: it returns
  one finite guess per parameter, or `None` when the data make a guess impossible, and
  `make_fit` then starts from the feasible start (ones when unbounded), as `curve_fit`
  does. `None` replaces NaN or infinite guesses in the Gaussian fit functions (for
  example, `y` summing to zero).
- Every fit function's class help (`help(cls)` and the API pages) lists its constructor
  arguments again: docstring inheritance had deleted each class docstring's Parameters
  section. `FitFunction`'s arguments (`xmin`, `weights`, `logy` and the rest) are
  documented in its class docstring and inherited by every fit function, and
  `FitFunction.__init__` no longer carries a docstring of its own. `Exponential`,
  `ExponentialPlusC`, `Gaussian`, `GaussianNormalized`, `Line`,
  `LineXintercept`, `PowerLaw`, `PowerLawPlusC` and `PowerLawOffCenter` no longer define
  an `__init__` that only forwarded `xobs`, `yobs` and `**kwargs`; their signatures now
  show every `FitFunction` argument.
- `make_fit` reads the class's `p0` only when the caller passes no `p0=`.
- `GaussianLn.p0` estimates in ln x, the space of its model: `mu` and `sigma` are the
  y-weighted mean and standard deviation of ln x, and `A` is the peak `y` (not logged).
  It previously returned the logs of the mean and variance of `x` and of the peak, which
  match none of the model's parameters.
- The Gaussian fit functions (`Gaussian`, `GaussianNormalized` and `GaussianLn`) return
  `p0 = None` when the estimated width is under half the smallest spacing between
  distinct `x`, including all the weight at one `x`. That width cannot be resolved by the
  samples; a zero width previously made `make_fit` fail with "Residuals are not finite in
  the initial point".
- `make_fit` rejects an initial guess holding NaN or infinity, from `p0` or the caller's
  `p0=`, with `ValueError: <Class> initial guess is not finite: <name>=<value>. A p0 that
  cannot make a guess returns None, and the fit then starts from the feasible default.`
  scipy previously reported it as "Initial guess is outside of provided bounds".
- Too little data for an initial guess raises `InsufficientDataError` under `python -O`
  as well; the check was an `assert`, which `-O` removes.
- `Hist2D.plot_edges` documents its `xlim` and `ylim` keywords as inclusive: a vertex
  exactly on a limit is kept. Behaviour is unchanged.
- `Plasma.qpar` documents its quantity precisely: the parallel-parallel component of
  the heat flux tensor in the center-of-mass frame of the requested species,
  rho (U^3 + 3/2 U w_par^2) for a drifting bi-Maxwellian. It is not the total energy
  flux along the field. Behaviour is unchanged.
- `FitFunction.initial_guess_info` reports the start the last fit used: a caller's `p0`,
  the class `p0` as `make_fit` adjusted it, or the feasible default when `p0` is None. It
  previously returned None for a caller's `p0` and for `p0` None; it is None only before
  a fit succeeds.
- Fit-function class docstrings list their sections in numpydoc order in `help()`.
- `AlfvenicTurbulence` logs its unequal-index warnings with `Logger.warning`, not the
  deprecated `Logger.warn`.
- `fitfunctions` no longer imports scipy's private `prepare_bounds`; bounds are broadcast
  with public NumPy.
- `GaussianLn.TeX_function` includes the exponent's minus sign and spaces `\cdot` from
  `\exp`: A exp[-(ln x - mu)^2 / (2 sigma^2)].
- `StabilityContours.plot_contours` with `tk_kind` keeps the table legend's layout: cells
  of unplotted instabilities are blank instead of dropped with a matplotlib warning.
- The `Hist2D.plot_contours` docstring links to `plot_edges` instead of printing a
  literal method repr.
- A `Plasma` logs each time-index problem once. The Ions, BField, Vectors and Tensors it
  builds from its checked data no longer repeat the checks (a Plasma on a
  non-DatetimeIndex logged that warning 14 times); a child whose index differs from its
  parent's is checked like a directly built object.
- A missing `Plasma` attribute raises `AttributeError` naming it (was "'super' object has
  no attribute '__getattr__'"), so `hasattr` and `getattr` with a default work.
- `Hist1D` and `Hist2D` `nbins` accept a `pandas.IntervalIndex`, keeping its bins and
  closure. It must be non-empty, contiguous, increasing, and closed `"left"` or
  `"right"`, else `ValueError`; its edges are rounded only when `bin_precision` is given.
- `SIDC.cut_spec_by_ssn_band` raises a `KeyError` naming a column `interpolated` lacks,
  instead of a `TypeError` from `np.isnan`.
- `FitFunction`'s `weights` docstring no longer promises covariance-matrix weights, which
  were never accepted: `weights` holds one 1-sigma uncertainty per observation, in
  `xobs`'s shape, and the `InvalidParameterError` for any other shape says a covariance
  matrix is not supported.
- CI no longer installs the HDF5 system packages (`libhdf5-dev`, `pkg-config`); the
  `tables` wheels bundle HDF5. `publish.yml`'s Linux cells keep the step, with a
  5-minute timeout and apt retries, so a dead mirror fails fast instead of hanging.
- Plots build faster and hold less memory (measured on pandas 3.1):
  - Building a plot from its own columns takes about 0.4 to 0.6 times the previous time at
    1M rows.
  - Building a plot from a shared `BinnedData` takes about 0.08 times the previous time.
  - `SpiralPlot2D`'s mesh builds in about 0.74 s instead of 31.7 s at 4.6M rows, with the
    same split order, midpoints and cells.
  - Each plot retains about 3 bytes per row instead of about 31: it stores which rows it
    keeps and their bin codes, not a copy of its data.
- `Plasma.load_from_file` releases the file's frame before reading the auxiliary table,
  and masking invalid species writes to the plasma's own data, not a view. Peak memory
  loading the Wind bimax file drops from 6.8 to 4.8 GB and the load from 2.43 to 2.03 s;
  loaded values are bitwise identical.
- `Spacecraft` defines its supported names (PSP, WIND) and frames (GSE, HCI) in one table,
  and an unsupported name or frame raises `NotImplementedError` naming the supported values.
- `SSNPlot` scales its y axis to the plotted peak rounded up to 100 (at least 100), instead
  of a fixed 0 to 200 that clipped cycles above 200. `SIDC.plot_on_colorbar` shares the
  rule through `SIDC.ssn_scale_top`.

### Added

- Hinge fit functions in `solarwindpy.fitfunctions.hinge`: `HingeSaturation`
  (`xh, yh, x1, m2`), `TwoLine` (`x1, x2, m1, m2`), `Saturation` (`x1, xh, yh, theta`),
  `HingeMin` and `HingeMax` (`m1, x1, x2, xh`) and `HingeAtPoint` (`xh, yh, m1, m2`).
  Each takes `guess_xh=None`, an initial guess for the hinge x, and subclasses one parent,
  `Hinge`, which holds the estimate-or-reference control flow of `p0` and the shared help
  text. When the data give no estimate (no data on one side of the hinge, repeated `x`,
  a zero slope where an x-intercept is needed, or rising-region points sharing one x),
  every class logs a warning and its `p0` returns the reference hinge, the author's
  Wind:SWE helium abundance fit (doi:10.3847/2041-8213/adb48e), translated to its
  parameters: (x_h, y_h) = (433, 4.19), vanishing speed x_1 = 302 and fast-wind slope
  m_2 = 0.0010, so m_1 = 4.19 / 131 and x_2 = -3757. `HingeMax` starts from the same
  two lines as `HingeMin`, combined with the maximum. The TeX
  report writes `xh`, `yh`, `x1`, `x2`, `m1`, `m2` and `theta` as `x_h`, `y_h`, `x_1`,
  `x_2`, `m_1`, `m_2` and `\theta`.
- `FitFunction.results`, a one-row table of every parameter's value and uncertainty with
  quality and status columns; `FitFunction.results_columns`; `FitFunction.error`, the
  exception that failed the last fit; and `fitfunctions.core.NotFittedError`.
- `FitFunction.make_fit` warns `fitfunctions.core.FitDegeneracyWarning` (a
  `UserWarning`) when a fit leaves parameters unconstrained: a non-finite covariance
  entry, or two parameters whose correlation from `pcov` exceeds
  `FitFunction.degeneracy_threshold` (0.99999; a subclass may set its own, and
  `make_fit(degeneracy_threshold=...)` overrides it for one fit). The warning names each
  pair, e.g. "xh and yh are degenerate (correlation 1.000000); their uncertainties are
  not meaningful", and `FitFunction.degenerate` lists the same pairs (it raises
  `NotFittedError` before a successful fit). The warning comes after the fit is stored:
  escalated to an error, it raises and the fit stays a successful fit. In
  `TrendFit.make_fit`, a bin fit's escalated warning records that bin as a failed fit,
  left out of the trend.
- `solarwindpy.fitfunctions.available()` lists the fit functions.
- `solarwindpy.tools.normal_parameters(m, s, base=np.e)`: `base` gives the log base of
  `m` and `s`, e.g. `base=10` for a base-10 log-normal. The default is unchanged.
- `solarwindpy.core.abundances.ReferenceAbundances()`, the Asplund et al. (2021) Table 2
  photospheric and CI chondrite abundances (doi:10.1051/0004-6361/202140445), with
  `get_element`, `abundance_ratio` and `get_comment`, and the `Abundance` namedtuple.
  `get_element` names its Series by atomic number.
- `Hist1D.set_axnorm("t")` (and `Hist1D(axnorm="t")`) divides the histogram by its
  maximum, so the peak equals 1, as `Hist2D` does. It previously raised `AssertionError`.
- `Hist2D.plot_hist_with_contours`, which draws the histogram and its contours on one
  axis and returns `(ax, mesh, qset, cbar_or_None)`.
- `SpiralPlot2D` gains `axnorm` `"t"` and `"d"` (keyword `axnorm=`, `set_axnorm`),
  `get_plotted_data_boolean_series` and `get_subset_above_threshold`, and its `agg`
  accepts aggregation keywords. `Hist1D`, `Hist2D` and `SpiralPlot2D` gain a `binning`
  property.
- A `description=` keyword on the plot label classes.
- `CITATION.cff` gives the Zenodo concept DOI and the author's ORCID in Citation File
  Format, so GitHub and Zenodo can read the citation.
- Python 3.14 is supported and declared; the full suite passes on it.
- `solarwindpy.examples.load_plasma()` returns a small example `Plasma`: three rows with
  species `a`, `e`, `p1` and `p2`, and a Parker Solar Probe trajectory in HCI. The data
  ships in `core/data/example_*.csv`; docstring examples start from it.
- `solarwindpy.plotting.binned.BinnedData(frame, bins, *, log=None, clip=None,
  mask=None, precision=None)` holds columns of a frame, their explicit bins (edges or a
  `pandas.IntervalIndex` per column, with per-column `log` and `clip`) and the bin of
  every row, computed once and cached as int8 codes (int16 above 127 bins). Pass it as
  `nbins` to `Hist1D`, `Hist2D` or `BetaRPlot`, e.g.
  `Hist2D(joint.sc_raw, joint.ahe, z=joint.vsw, nbins=b)`, and the plots share its bins
  and codes instead of each binning, and copying, the same columns. A plot finds its
  columns by `x.name` and `y.name` and takes the rows of `x.index`: an unknown name raises
  `KeyError`, and an index that is not a subset of the `BinnedData`'s raises
  `ValueError`. Integer and string bin rules are refused with `TypeError`, since their
  edges depend on which rows each plot keeps; pass those to the plot's `nbins`.
  `SpiralPlot2D` refuses a `BinnedData` with `TypeError`, because its mesh adapts to its
  own data. Its read-only API is `columns`, `index`, `log_of`, `clip_of`, `edges`,
  `intervals`, `codes` and `categorical`.
- `mask=` on every plot constructor (`Hist1D`, `Hist2D`, `BetaRPlot`, `Scatter`,
  `SpiralPlot2D`) and on `BinnedData`: a boolean `pandas.Series` aligned by label to the
  data's index, which keeps a row where it is True. It replaces subsets made beforehand
  with `x.loc[idx]` or `x.drop(idx)`, and selections return the original labels. A
  missing label or a NaN raises `ValueError`; neither is ever treated as False. A plot
  sharing a `BinnedData` also drops the rows that object's own mask excludes.
- `solarwindpy.plotting.base.ClipAxes(x, y, z)`, the per-axis clip record a plot's
  `clip` returns, exported next to `LogAxes`.
- `solarwindpy.solar_activity.cache`, one download cache for every solar-activity
  source. `fetch(url, max_age)` uses the cached copy inside its freshness window,
  downloads again past it, and if that download fails uses the cached copy with a
  `StaleCacheWarning` that names its age; `DownloadError` is raised only when nothing is
  cached. `DownloadError.status`, `fetch(..., fallback=False)` and
  `fall_back(url, error)` let callers tell an HTTP 404 from a network failure.
  `cache_contents()` is a table of each cached URL with its local path and age. Files
  live in astropy's download cache for package `solarwindpy` (`~/.cache/solarwindpy`);
  remove entries with `astropy.utils.data.clear_download_cache(url, pkgname="solarwindpy")`.
- `solarwindpy.solar_activity.icme.icmecat.ICMECAT`, access to the HELIO4CAST ICME
  catalog (pinned v23, `ICMECAT_URL`), with `filter`, `contains`, `summary`,
  `get_events_in_range`, `strict_intervals` and `estimated_intervals`. It caches the
  catalog in SolarWindPy's download cache, downloads it again once the cached copy is
  more than 30 days old, and falls back to the cached copy with a `StaleCacheWarning` if
  that download fails. When v23 answers 404 it probes v24 to v28, records the loaded
  catalog in `ICMECAT.version`, and warns about spacecraft names outside
  `SPACECRAFT_NAMES`. `ICMECATDownloadError` subclasses
  `solarwindpy.solar_activity.cache.DownloadError` (still a `RuntimeError`) and tells
  users to edit `solarwindpy.solar_activity.icme.icmecat.ICMECAT_URL`.
- `Spacecraft.pos_units`, the TeX of the position unit for the spacecraft's frame, read
  from the quantity registry (Earth radii in GSE, solar radii in HCI).

### Fixed

These change computed values; rerun any analysis that used them.

- `Plasma.qpar` (0.3.0 also `heat_flux`) is now reported in uW m^-2, matching its
  docstring and plot label. The previous factor produced values in units of 1e-7 W m^-2
  while the label said mW cm^-2, a factor of 1e8 apart; values are now 10 times smaller
  than before.
- `Ion.Wk` / `Plasma.Wk` (0.3.0 also `kinetic_energy_flux`) raised `AttributeError` on
  every call; it now returns uW m^-2.
- `Hist2D.id_data_above_contour` no longer raises `TypeError: Categorical is not ordered
  for operation min` for bin specifications whose bins came out unordered.
- `Hist2D.get_border`, and so `plot_edges`, returns the highest and lowest occupied y bin
  in each x bin. When some y bin was empty in every x bin, it returned the last- and
  first-listed bins in order of first appearance instead, which could be a middle bin.
- `Hist1D.construct_cdf` returns its rows indexed by the original row labels, sorted by x
  with ties in input order, instead of a reset 0..n-1 index. The `x` and `position`
  values are unchanged; `position` is computed from each row's rank.
- `Hist1D.take_data_in_yrange_across_x` raises `ValueError` instead of failing an
  `assert` when `ranges_by_x` names x bins the histogram does not have, and, like
  `Hist2D`, logs a warning and selects within the named bins when `ranges_by_x` omits
  some of them.
- Plots keep no row whose x, y or z is +-inf, in the input or after `log10(abs())` on a
  logarithmic axis (so a 0 there), just as they drop NaN. This applies to `Hist1D`,
  `Hist2D`, `BetaRPlot`, `Scatter` and `SpiralPlot2D`, including plots sharing a
  `BinnedData`. `BinnedData` codes +-inf as -1 even when clipped or when an edge is
  infinite.
- `Base.clip_data` computes its quantiles over finite values only, so +inf no longer
  makes the upper quantile NaN. +-inf is clipped to the quantile on the clipped tail; NaN
  is unchanged.
- `SpiralMesh.generate_mesh` (and so building a `SpiralPlot2D`) raises `ValueError`
  instead of never terminating when more than `min_per_bin` points are identical in x and
  y. The message names the points and the usual causes (duplicated rows, fill values,
  clipping both axes). Meshes of other inputs are unchanged.
- `Hist1D.take_data_in_yrange_across_x`, `Hist2D.take_data_in_yrange_across_x` and
  `Hist2D.id_data_above_contour` compare each binned axis on the side its bins close:
  `[a, b)` for an integer `nbins`, with the last bin also holding its right edge, and
  `(a, b]` for explicit edges. They previously always compared `(a, b]`. `Hist1D`'s y
  range, which is not binned, stays `(bottom, top]`.
- `get_subset_above_threshold` returns the caller's values on the kept rows. It
  previously applied `10**` to every axis flagged as log, which inflated a linear y
  after `project_1d` and dropped the sign of a logged axis.
- `Hist2D.project_1d` reuses the parent's bins and bin codes, so the side panels bin each
  row exactly as the 2-D plot does, including rows clipped into an edge bin, and the
  projected counts are the parent's marginal sums. It averages the measured z or
  other-axis values in linear units, sign included; a log other axis was previously
  passed as `log10|x|`. A log other axis now sets the projection's `log.y` whichever
  axis is projected, and with `only_plotted=False` rows outside the other axis's bins
  are dropped, as documented.
- `Hist2D.project_1d` keeps the parent's bins and their closure. An integer-`nbins`
  (including log-binned) parent bins like numpy, but the projection rebinned on
  right-closed edges, so a sample on an edge moved bin or was dropped: for x = [0, 1, 2,
  3, 4, 4] and two bins the parent counts [2, 4] and the projection gave [2, 3].
- `Hist2D.project_1d(only_plotted=False)` sets y to NaN where the parent does not bin
  it. It kept a y on the bottom edge of right-closed bins.
- `clip` accepts True/False and the strings "l", "lower", "u", "upper" and "both", in
  any case. `Hist2D(clip="l")` and `clip="u"` clip only the lower or upper tail; in
  0.3.0, `Hist2D(clip_data="l")` and `"u"` clipped both, because the value was coerced to
  bool. Any other string, the empty one included, raises `ValueError` naming them, from
  every plot constructor, `BinnedData` and `Base.clip_data`. Previously `""` raised
  `IndexError`, an unknown string clipped both tails, and any string starting with "l"
  or "u" (e.g. "lo") was accepted.
- x, y and z whose indexes differ, where a column to be aligned repeats a label, raise a
  `ValueError` naming that column and saying the alignment is ambiguous, instead of
  pandas' "cannot reindex on an axis with duplicate labels". Identical indexes with
  repeated labels, and unique labels aligned onto repeated ones, work as before.
- Edges from an integer `nbins` enclose every sample when the data are so large that
  `10**-precision` is below their float spacing (above about 9e10 at the default
  precision). Previously the extreme sample could fall outside the edges and go
  uncounted.
- An object-dtype column of numbers is binned, logged and checked for NaN and +-inf as
  the numeric column it holds. Previously an inf in it was kept (e.g. a bin mean of
  inf), and integer `nbins` or `logx` raised `AttributeError` or `TypeError`.
- `hbar` is scipy's exact h/2pi (was the CODATA 2014 value), and the solar radius is
  the IAU 2015 nominal 695.7e6 m (was 695.508e6 m), shifting distances in solar radii
  by 0.028%.
- Kinetic energy flux has a plot label, `"Wk"`, rendered W_K in uW m^-2.
- `Vector.lat` and `Vector.colat` (0.3.0 also `latitude` and `colatitude`) were
  swapped. Latitude is now the angle above the xy-plane, `arctan2(z, rho)` in [-90, 90];
  colatitude is the angle from +z, `arctan2(rho, z)` in [0, 180]. A vector along +z has
  latitude 90 and colatitude 0 (previously the reverse); each old value converts as
  `new = 90 - old`.
- `Tensor.mag` (0.3.0 `Tensor.magnitude`) raised `ValueError` on every Tensor the package
  builds. It now returns the scalar thermal speed sqrt((w_par^2 + 2 w_per^2) / 3), which
  combines the components through the temperatures and matches the stored `scalar`
  column.
- `Vector.project` and `Vector.cos_theta` returned 0 (a perpendicular answer) on rows
  present in only one of the two vectors, or with a NaN component. They now return NaN
  there. The `Plasma` methods built on `project` change the same way on such rows.
- Plot labels for a latitude component (`"lat"`) now render as lambda and a colatitude
  component (`"colat"`) as theta; the two symbols were swapped.
- `Plasma.estimate_electrons` now sets the electron temperature equal to the (core)
  proton scalar temperature, as its docstring states: w_e^2 = (m_p / m_e) w_p^2. It
  previously multiplied by n_p / n_e, so with alphas or other ions present the electron
  thermal speed was too small by sqrt(n_p / n_e) (about 4% at n_a / n_p = 0.04) and the
  temperature by n_p / n_e. Proton-only plasmas are unchanged.
- The `Ion` returned by `Plasma.estimate_electrons` carries the scalar thermal speed
  (equal to `par` and `per`), so its `w`, `T` and other thermal properties work; they
  raised `ValueError` before.
- A species sum in `Plasma.qpar` and `Plasma.Wk` (e.g. `"a+p1"`) is NaN on rows where no
  species is present, e.g. where b is missing for `qpar`. It was 0. Rows with some
  species present remain partial sums over those species.
- `Plasma.vdf_ratio` is NaN where the beam drift cannot be projected onto b, e.g. where b
  is missing. It previously dropped the drift term there and returned
  ln(n2 w1^3 / n1 w2^3).
- Any missing component makes a `Plasma` value NaN: the scalar thermal speed where w_par
  or w_per is missing, `pdv`'s dv^2 and `afsq`'s B^2.
- A species missing at a time has NaN `w`, `pth` and `T` there; they were 0.
- `Plasma` totals over species (`n`, `rho`, `pth`, `T`, `pdv`) sum the species present at
  a time and are NaN only where none is (were 0); `v` and `estimate_electrons` average
  over the species present.
- Pair quantities need both species: `nuc` and the reduced mass of
  `pdv(project_m2q=True)` are NaN where either species is missing.
- Missing components give NaN, following the rule in the missing-data docs: a quantity
  built from a fixed set of inputs needs every input.
  - `Plasma.R` is NaN for a species missing its parallel or perpendicular component, and
    NaN where no species is present (it was 1.0). A species-partial total such as
    `"a+p1"` stays partial over the species present.
  - `Spacecraft.distance2sun` is NaN at a missing position component, as `Vector.mag`
    is, so `Plasma.nc` is NaN there too.
  - `AlfvenicTurbulence` energies and `cross_helicity` are NaN at a missing component.
  - The Raffaella polarity, and the field built from it, are NaN at a missing `v_y` or
    `b_y`.
- `PowerLawOffCenter.make_fit` bounds `x0` below the smallest used x, where the model is
  defined, within any caller bounds; a caller bound or `p0` that leaves `x0` no room below
  the data, or a `p0` whose `x0` is below its lower bound or not finite, raises `ValueError`.
- `PowerLawOffCenter.p0` starts `x0` below the smallest used x when any used x is ≤ 0, and
  `make_fit` clips that start into the caller's bounds on `x0`, so such data and bounds fit
  instead of starting outside the `x0` bound.
- `SIDC.cut_spec_by_ssn_band` no longer fails with "Overlapping IntervalIndex is not
  accepted" for narrow bands (e.g. `dssn=0.05`), where rounding made neighbouring bands
  overlap; the bands now share one edge.
- Solar cycle 25's maximum in `ssn_extrema.csv` is 2024-10-01, the peak (160.9) of the
  SILSO 13-month smoothed sunspot number, replacing the placeholder 2030-12-01. Epochs
  after 2024-10 are now on cycle 25's falling edge (`SIDC` `edge` is `"Fall"`, and
  `SSNExtrema.cycle_intervals` Fall runs from the maximum to today), and `SIDC`
  `extremum` labels those below half the cycle maximum `"26-Min"` instead of `"25-Min"`.
- `Vector` and `Tensor` calls return the named component, e.g. `plasma.b("x")` or
  `ion.w("par")`; they previously always raised `AttributeError`. An unknown component
  raises `KeyError` listing the available components.
- `tools.swap_protons` now checks that the core (`p1`) density is at least the beam (`p2`)
  density after the swap, and raises if not. The previous check compared `n_p2` with itself
  and could never fail.
- The `beta_ani_inst` docstring example now uses the published A/IC fit at
  `gamma / Omega_p = 10^-4` (Verscharen et al. 2016, Table 1). It had passed the FM/W `a` as
  `b`, so it printed thresholds for no published instability.
- An `IndicatorPlot` subclass that never calls `set_labels` no longer raises
  `AttributeError` on `path`.
- The wheel no longer installs a stray top-level `tests` package beside solarwindpy.
- `SpiralPlot2D.plot_contours` triangulates the cell centers in plot coordinates (log10 on
  a log axis), each axis scaled to its span, instead of in data units, where one axis
  dominated and the contours misplaced the outer levels. It raises a `ValueError` naming
  the problem when fewer than 3 cells hold finite values, or when the occupied cells'
  centers all lie on one line along any direction, instead of failing inside
  matplotlib's `Triangulation` with a length error about its x and y arrays or a qhull
  `RuntimeError`.
- After a successful fit, a `make_fit` call that raises an exception other than the recorded
  fit failures (`FitFunctionError`, `RuntimeError`, `ValueError`) now leaves the fit unfitted,
  with every result raising `NotFittedError`, instead of `popt`, `psigma`, `pcov`, `rsq` and
  `chisq_dof` still reporting the earlier fit. A `FitFunctionError`, `RuntimeError` or
  `ValueError` raised while computing R² is now recorded as a failed fit, like one raised by
  the optimizer.
- A fit function's `make_fit` no longer leaves a half-updated fit when a step after the
  optimizer raises. An error while building `TeX_info` or the plotter used to leave the
  fit looking successful with those results missing; a recorded failure there
  (`ValueError`, `RuntimeError`, or a `FitFunctionError`) is now recorded as a failed fit,
  and any other exception leaves the fit unfitted. `fit_bounds` no longer answers after a
  fit that failed after the optimizer ran. `TrendFit.make_fit` interrupted by an
  unexpected exception no longer keeps the previous `bin_results` and `trend`; the
  `TrendFit` and its bin fits are left unfitted.
- `GaussianLn.set_TeX_report_normal_parameters` and the TeX annotation's mean and std no
  longer silence an `AttributeError` raised inside `TeX_info` or `normal_parameters`; only
  `NotFittedError` is taken to mean the fit has not run.
- Every warning SolarWindPy issues now names the line of the caller's own code that
  triggered it, at any call depth. The `OptimizeWarning` from `make_fit`, for example,
  previously named `solarwindpy/fitfunctions/core.py`.

### Removed

- `solarwindpy.plotting.select_data_from_figure` and its `SelectFromPlot2D` class. It
  passed the `rectprops` keyword, which current matplotlib's `RectangleSelector` no
  longer accepts, so construction raised `TypeError` (verified on matplotlib 3.10.8).
  Interactive selection of data from a plot is available in [glue](https://glueviz.org).
- `solarwindpy.plotting.orbits` (`OrbitPlot`, `OrbitHist1D`, `OrbitHist2D`), which nothing
  used; last available at commit e790d95f.
- The `"Q"` plot label key. It was commented as a heating rate, carried a heat flux
  unit, and nothing in the package computes a heating rate. Heat flux is labelled
  `"qpar"`.
- `Hist2D`: removed the undocumented, unreachable tuple `axnorm` branch; `set_axnorm`
  already rejected tuples and still does.
- `solarwindpy.solar_activity.lisird` (`LISIRD`, `ExtremaCalculator`) and
  `solarwindpy.solar_activity.get_all_indices` removed (unused); last available at
  commit beb10945.
- The `"Lalpha"`, `"f10.7"`, `"CaK"`, and `"MgII"` plot label keys, which existed only
  for the removed LISIRD indices.
- The `Moyal` fit function (`solarwindpy.fitfunctions.moyal`). Its function computed
  A*(exp(exp((z**2 - exp(z**2))/2)) - 1), not the Moyal density (Moyal 1955,
  doi:10.1080/14786440308521076), and its `TeX_function` matched neither.
- `solarwindpy.fitfunctions.exponentials.ExponentialCDF`. No alias is kept; importing it
  raises `ImportError`.
- `FitFunction.psigma_relative`; compute `results` uncertainties over values instead.
- The `logx` argument of `FitFunction` and `set_fit_obs`, which was never used.
- `TeXinfo.npts` and `TeXinfo.set_npts`.
- `StabilityCondition.fill`, the `-9999.0` label of a point outside every stability bin.
  No point can carry it: every point is stable or falls in one of the four other bins.
- `solarwindpy.plotting.labels.available_labels()`; call `available()`.
- `solarwindpy.plotting.tools.multipanel_figure_shared_cbar`, a wrapper of
  `build_ax_array_with_common_colorbar`; call that directly.
- `Plasma` plasma-statistics logging: the `log_plasma_stats` argument (of `Plasma` and
  `Plasma.load_from_file`), the `log_plasma_at_init` property and `set_log_plasma_stats`.
  Nothing used them, and turning them on raised `AttributeError` on pandas 3
  (`DataFrame.applymap` is gone). Passing `log_plasma_stats=` raises `TypeError`. `Plasma`
  still logs "No spacecraft data passed to Plasma" (and likewise for auxiliary data) at
  INFO when that input is `None`.
- Contour labelling is removed from `Hist2D.plot_contours` and
  `SpiralPlot2D.plot_contours`: the `label_levels`, `clabel_kwargs` and `skip_max_clbl`
  parameters are gone, and the methods draw no labels (for their return values see
  Changed - BREAKING CHANGES). Passing a removed keyword raises an error from
  matplotlib. Filled contours no longer emit matplotlib's `clabel` deprecation warning.
  `SpiralPlot2D.plot_contours` also no longer takes `plot_edges` or `edges_kwargs`.
- The comma split of a single species string in `Plasma._set_ions`, which was
  unreachable: `Plasma(data, "a,p1")` already fails in `set_data`.
- `.github/WORKFLOWS.md`, which described a stale CI setup; the workflow files are the
  reference.
- `solar_activity/sunspot_number/ssn_extrema.csv.silso`, an unread older copy of
  `ssn_extrema.csv` (cycle 25 maximum still the 2030-12-01 placeholder). Nothing read
  it; `SSNExtrema` reads `ssn_extrema.csv`.
- `DataLoader.data_path`, `get_data_ctime`, `get_data_age`, `maybe_update_stale_data` and
  `download_data(new_data_path, old_data_path)`. A `DataLoader` subclass now defines `max_age`
  (a `pandas.Timedelta`) and `read_data(path)`, which parses the downloaded file;
  `SIDCLoader.download_data` became `SIDCLoader.read_data(path)`.
- `set_path(new, add_scale)` from every plot; `path` is now a read-only property derived on
  each read. To save elsewhere, join it: `Path("figs") / plot.path`.
- The `auto_update_path` keyword of `set_labels`; passing it now raises `KeyError`.

### Migration

- Development checkouts: the package source moved from `solarwindpy/` to
  `src/solarwindpy/`; `import solarwindpy` is unchanged, and installs from PyPI or
  conda-forge need nothing. After pulling, in each checkout move anything untracked out
  of the root `solarwindpy/` folder, delete what remains of it (a leftover folder makes
  `import solarwindpy` find an empty namespace package), and reinstall with
  `pip install -e ".[dev]"`.
- Imports: replace every path in the table under Changed - BREAKING CHANGES with its new
  path; nothing is re-exported.
- Fit functions: pass `p0`, bounds and `function` arguments by name, or reorder them so
  `A` comes last, and read `popt` with the new names (`k`, `y0`, `alpha`, `mu`, `sigma`).
- Catch `ValueError` where you caught `AssertionError` or `KeyError` from
  `set_sc`, `set_aux`, the column-level-name checks and
  `Hist2D.take_data_in_yrange_across_x` (a zero-width or inverted range).
- Catch `TypeError` where you caught `AttributeError` for input that is not a
  `pandas.DataFrame`.
- Drop rows with missing timestamps (`NaT`) before building a `Plasma`, `Spacecraft`,
  `Ion`, `Vector`, `Tensor` or `BField`, e.g. `data = data.loc[data.index.notna()]`.
- Plotting: rename `clip_data=` to `clip=`; pass `True`/`False` or one of "l", "lower",
  "u", "upper", "both" (a prefix such as "lo" raises).
- Plotting: edit the source data before building a plot, not `h.data`. `h.data` is
  rebuilt on each access, so edits to it are silently lost.
- Plotting: build a new plot instead of calling `set_data`, or `set_log` on a binned
  axis. A `Base` subclass implements `_set_data`.
- Plotting: replace subsets built with `x.loc[idx]` or `x.drop(idx)` with `mask=`, and
  share bins across many histograms by passing one `BinnedData` as `nbins`.
- Plotting: `Hist2D.agg()` returns every bin; call `.dropna()` for the occupied bins
  only. Its index levels are `IntervalIndex`.
- Upgrade notes: downloaded solar-activity data (the SILSO sunspot numbers `SIDC` reads,
  and the `ICMECAT` catalog) live in astropy's download cache for package `solarwindpy`,
  `~/.cache/solarwindpy` by default. Files under `~/solarwindpy/data` are not migrated
  (they hold processed tables; the new cache holds SILSO's raw download). The first
  `SIDC(...)` after upgrading downloads again; delete `~/solarwindpy/data` afterwards.

## [0.3.0] - 2025-12-24

### Changed - BREAKING CHANGES

**Dependency Management Overhaul**: Consolidated 11 dependency files into single-source-of-truth system using `pyproject.toml` with `pip-tools` lockfiles.

- **REMOVED**: `requirements-dev.txt` (replaced by `requirements-dev.lock`)
- **REMOVED**: `scripts/freeze_requirements.py` (replaced by `pip-compile`)
- **REMOVED**: `scripts/generate_docs_requirements.py` (replaced by `pip-compile --extra=docs`)
- **Migration required**: See [the v0.3.0 migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md)

**Developer Workflow Changes**:
```bash
# OLD (v0.2.x):
pip install -r requirements-dev.txt

# NEW (v0.3.0+):
pip install -r requirements-dev.lock
```

**Dependency Updates**: Minimum versions updated for NumPy 2.0 ecosystem compatibility
  - `numpy`: `>=1.22,<2.0` → `>=1.26,<3.0` (adds NumPy 2.0 support)
  - `scipy`: `>=1.10` → `>=1.13`
  - `pandas`: `>=1.5` → `>=2.0`
  - `numba`: `>=0.57` → `>=0.59`
  - `docstring-inheritance`: `>=2.0` → `>=2.2.0,<3.0` (MRO fix, exclude breaking v3.0)
  - `pytest`: `>=7.4.4` → `>=8.0`
  - `pytest-cov`: `>=4.1.0` → `>=6.0`

### Added

- **Lockfiles** for reproducible builds:
  - `requirements.txt` - Production dependencies (from `[project.dependencies]`)
  - `requirements-dev.lock` - Development dependencies (from `[project.optional-dependencies.dev]`)
  - `docs/requirements.txt` - Documentation dependencies (from `[project.optional-dependencies.docs]`)

- **Tests**: `tests/fitfunctions/test_metaclass_compatibility.py`
  - Validates `FitFunctionMeta` MRO compatibility with `NumpyDocstringInheritanceMeta` and `ABCMeta`
  - Prevents metaclass regression bugs
  - Tests abstract method enforcement, docstring inheritance, all fitfunction instantiation
  - Includes version constraint validation (docstring-inheritance >=2.2.0,<3.0)

- **Documentation**: Comprehensive [migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md) (retired from the tree; kept at the v0.3.0 tag)
  - Breaking changes overview
  - Old vs new developer workflows
  - NumPy 2.0 compatibility matrix
  - CI/CD changes
  - Rollback procedures
  - FAQ with common migration questions

- **Dependency Groups** in `pyproject.toml`:
  - `[project.optional-dependencies.test]` - Testing tools only
  - `[project.optional-dependencies.docs]` - Documentation tools only
  - `[project.optional-dependencies.dev]` - All development tools (test + docs + dev)

### Fixed

- **Critical**: `numpy==2.2.6` in `requirements.txt` violated `pyproject.toml` constraint `<2.0`
  - Root cause: `freeze_requirements.py` used `pip freeze` without validating `pyproject.toml`
  - Fix: Replaced custom scripts with `pip-compile` which enforces constraints
- **Dependency fragmentation**: Eliminated sync issues between 11 dependency files
- **Version drift**: Lockfiles prevent undocumented version changes

### Infrastructure

**GitHub Actions**: All CI/CD workflows updated for lockfile-based dependency management

- `.github/workflows/sync-requirements.yml`:
  - Triggers on `pyproject.toml` changes (single source of truth)
  - Uses `pip-compile` to generate lockfiles instead of Python scripts
  - Validates lockfiles with `pip install --dry-run`

- `.github/workflows/continuous-integration.yml`:
  - Uses `requirements-dev.lock` instead of `requirements-dev.txt`
  - Faster caching via lockfile hash
  - Cross-platform testing: ubuntu/macos × Python 3.11/3.13

- `.github/workflows/ci-master.yml`:
  - Updated to use `requirements-dev.lock`
  - Consistent with other workflows

- `.github/workflows/security.yml`:
  - Audits `requirements-dev.lock` with `safety` and `pip-audit`
  - Security scans on frozen versions instead of loose constraints

- `.github/workflows/publish.yml`:
  - **Pre-release validation**: Blocks PyPI deployment if lockfiles are out of sync with `pyproject.toml`
  - Prevents releasing with inconsistent dependencies

**Scripts**: Updated `scripts/requirements_to_conda_env.py`
- Now reads lockfiles (default: `requirements.txt`) instead of `requirements-dev.txt`
- Documentation clarifies `pip-compile` is a prerequisite
- Supports generating conda environments from any lockfile

### Testing

- **NumPy Compatibility**: Validated with NumPy 1.26.4 and 2.2.6 (247 tests passed each)
- **Coverage**: Maintained 78% (improved from 77.86% baseline)
- **Test Suite**: 1576 tests passed, 19 skipped
- **Metaclass Tests**: 9 new regression tests for `FitFunctionMeta` MRO compatibility

### Migration

**For Developers**:
1. Update checkout: `git pull`
2. Install from lockfile: `pip install -r requirements-dev.lock`
3. Verify: `pytest -q`

**For CI/CD Pipelines**:
- Replace `pip install -r requirements-dev.txt` with `pip install -r requirements-dev.lock`

**Rollback**: Use `pip install solarwindpy==0.2.0` if issues arise

See [the v0.3.0 migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md) for complete migration instructions

## [0.2.0] - 2025-11-12

### Changed
- **BREAKING**: Minimum Python version raised from 3.10 to 3.11
  - Aligns with scientific Python ecosystem (NumPy 2.x, Astropy 7.x require Python 3.11+)
  - Python 3.10 reaches end-of-life in October 2026
  - Enables Python 3.11+ performance improvements (10-60% faster in many workloads)
  - Added Python 3.13 to CI testing matrix for forward compatibility

### Fixed
- Resolved conda-forge feedstock Issue #8 (Python version compatibility)
- Removed all Python 3.10 references from CI and packaging configuration
- Updated ReadTheDocs configuration to use Python 3.11

### Added
- Python 3.13 CI testing for forward compatibility validation
- Runnable Quick Start example in README with realistic solar wind data
  - Demonstrates complete Plasma object creation workflow
  - Includes physically accurate parameter values
  - Users can copy-paste and execute immediately

### Documentation
- Updated installation requirements in README.rst and docs/source/installation.rst
- Fixed LICENSE file detection for GitHub (converted from .rst to plain text)
- Archived completed documentation to reduce AI context overhead

## [0.1.5] - 2025-11-10

### Fixed
- **Documentation validation** - Resolved doctest failures for JOSS submission
  - Added continuation markers (`...`) to multi-line doctest examples
  - Completed Ion class example with all required columns (v.x, v.y, v.z, w.par, w.per)
  - Added `# doctest: +SKIP` directives to non-deterministic fitfunction examples
  - Added `# doctest: +NORMALIZE_WHITESPACE` for pandas DataFrame output
  - All 33 doctests now passing (11 executed, 22 appropriately skipped)
  - Aligns with paper statement: "fitfunctions tests remain in active development"
  - Unit tests (1,557 test cases) provide comprehensive functionality validation

### Changed
- **Documentation examples** - Maintain instructional value while ensuring reliable validation
- **JOSS paper** - Updated acknowledgements to reflect AI-assisted development workflow
- **Conda channels** - Switched to conda-forge only (removed Anaconda `defaults` channel)
  - Eliminates commercial channel licensing warnings in CI
  - All dependencies available on open-source conda-forge channel
  - Users with existing environments should recreate: `conda env remove -n solarwindpy && conda env create -f solarwindpy.yml`
  - Aligns with JOSS open-source infrastructure requirements

## [0.1.0] - 2025-08-23

### Added
- **Initial stable release on PyPI** - First public release of SolarWindPy
- **Semantic versioning with setuptools_scm** - Automatic version detection from git tags
- **Automated deployment pipeline via GitHub Actions** - Complete CI/CD for PyPI publishing
- **Core plasma physics calculations and data structures** - Multi-species plasma analysis
- **Plotting and visualization capabilities** - Publication-quality scientific plots
- **Instability analysis tools** - Solar wind plasma instability calculations
- **Comprehensive test coverage** - ≥95% code coverage with scientific validation
- **Release automation scripts** - check_release_ready.py and bump_version.py tools
- **Comprehensive documentation** - Release process and deployment guides

### Changed
- **Migrated from development to stable release** - Production-ready package
- **Enhanced package metadata for PyPI distribution** - Complete project configuration
- **Improved version detection with setuptools_scm** - Tag-based versioning
- **Enhanced GitHub Actions workflows** - Production deployment automation

### Fixed
- **Graceful handling of missing PyPI tokens** - Continues deployment without tokens
- **Code formatting standardization** - Black formatting across entire codebase
- **Test fixture scope issues** - Module-level fixtures for cross-class access
- **Documentation validation** - Comprehensive doctest and example validation

### Security
- **Added validation gates for release deployment** - Multi-stage verification process
- **PyPI token security** - Secure repository secrets management