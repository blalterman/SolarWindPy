# Combined Test Plan for `solarwindpy.plotting` (branch `update-2025`)

## Overview

The `solarwindpy.plotting` subpackage offers high-level plotting utilities built on pandas
and Matplotlib. This unified plan combines the narrative test rationale and the
actionable checklist for validating every class, method, property (including non-public
interfaces), and helper function across:

- `base.py`
- `agg_plot.py`
- `histograms.py` (`hist1d.py`, `hist2d.py`)
- `scatter.py`
- `spiral.py`
- `orbits.py`
- `tools.py`
- `select_data_from_figure.py`
- `labels/base.py`
- `labels/special.py`

Tests are grouped by module. Each module section includes context from the original
narrative plan followed by a deduplicated checklist of actionable items.

______________________________________________________________________

## `base.py`

### Class `Base` (abstract)

- Instantiation via subclass to ensure `_init_logger`, `_labels`, `_log`, and `path`
  setup.
- `__str__` returns the class name.
- Properties `data`, `clip`, `log`, `labels`, `path` reflect internal state.
- `set_log(x, y)` toggles `log.x` and `log.y`; cover defaults and explicit
  values.
- `set_labels(auto_update_path=True)` updates `labels` and regenerates `path`.
  Passing an unexpected kwarg raises `KeyError`.

### Checklist

- [ ] Instantiate a minimal subclass of `Base` to verify `_init_logger`,
  `_labels`, `_log` and `path` are initialized (#PR_NUMBER)
- [ ] Verify that `__str__` returns the class name (#PR_NUMBER)
- [ ] Verify that `.data` property returns the internal `_data` (#PR_NUMBER)
- [ ] Verify that `.clip` property returns the internal `_clip` (#PR_NUMBER)
- [ ] Verify that `.log` property returns the internal `_log` (#PR_NUMBER)
- [ ] Verify that `.labels` property returns the internal `_labels`
  (#PR_NUMBER)
- [ ] Verify that `.path` property returns the internal `_path` (#PR_NUMBER)
- [ ] Test `set_log()` with defaults toggles `log.x` and `log.y` appropriately
  (#PR_NUMBER)
- [ ] Test `set_log(x=True, y=False)` correctly updates `log` axes
  (#PR_NUMBER)
- [ ] Test `set_labels()` updates labels and regenerates `path` (#PR_NUMBER)
- [ ] Verify that `set_labels(unexpected=…)` raises `KeyError` (#PR_NUMBER)

______________________________________________________________________

## `agg_plot.py`

### Class `AggPlot(Base)`

- Properties `edges`, `categoricals`, `intervals`, `cut`, `clim`,
  `agg_axes`, `joint`, `grouped`, `axnorm`.
- Static method `clip_data(data, clip)` handles series vs. DataFrame, `'l'`, `'u'`,
  and numeric clipping. Invalid types raise `TypeError`.
- `set_clim(lower, upper)` sets `_clim`.
- *Justification*: foundation for all histogram and heatmap classes.

### Checklist

- [ ] Verify `.edges` property constructs correct bin-edge arrays (#PR_NUMBER)
- [ ] Verify `.categoricals` property returns categorical bins mapping
  (#PR_NUMBER)
- [ ] Verify `.intervals` property returns correct `IntervalIndex` objects
  (#PR_NUMBER)
- [ ] Verify `.cut` property returns the internal `_cut` DataFrame
  (#PR_NUMBER)
- [ ] Verify `.clim` property returns the internal `_clim` tuple (#PR_NUMBER)
- [ ] Verify `.agg_axes` returns the correct aggregation column (#PR_NUMBER)
- [ ] Verify `.joint` returns a `Series` with a `MultiIndex` (#PR_NUMBER)
- [ ] Verify `.grouped` returns a `GroupBy` on the correct axes (#PR_NUMBER)
- [ ] Verify `.axnorm` returns the internal `_axnorm` value (#PR_NUMBER)
- [ ] Test `clip_data(pd.Series, 'l')`, `'u'`, numeric → correct clipping
  (#PR_NUMBER)
- [ ] Test `clip_data(pd.DataFrame, …)` with lower/upper modes (#PR_NUMBER)
- [ ] Verify `clip_data()` raises `TypeError` on unsupported input
  (#PR_NUMBER)
- [ ] Test `set_clim(2, 10)` sets `_clim` to `(2, 10)` (#PR_NUMBER)

______________________________________________________________________

## `histograms.py`

### Module exports

- Test that `AggPlot`, `Hist1D`, and `Hist2D` are re-exported correctly.

### Checklist

- [ ] Verify `__all__` includes `AggPlot`, `Hist1D`, `Hist2D` (#PR_NUMBER)

### `hist1d.py` → Class `Hist1D(AggPlot)`

- `__init__(x, y=None, logx, axnorm, clip_data, nbins, bin_precision)`
  handles default count vs. y-aggregation and `logx=True` transforms data.
- `_gb_axes` returns `('x',)`.
- `set_path(new, add_scale)` accepts `"auto"` vs. custom paths.
- `set_data(x, y, clip)` ensures correct DataFrame shape and stores clip flag.
- `set_axnorm(new)` validates keys (`d`, `t`); invalid keys raise
  `AssertionError`.
- `construct_cdf(only_plotted)` produces a CDF or raises `ValueError` for
  invalid data.
- `_axis_normalizer(agg)` supports None, density, total; invalid values raise
  `ValueError`.
- `agg(**kwargs)` requires `fcn='count'` with density normalization; otherwise
  raises `ValueError`.
- `set_labels(y=…)` updates labels; providing `z` raises `ValueError`.
- `make_plot(ax, fcn, transpose_axes, **kwargs)` returns `(ax, (pl, cl, bl))`.
  Test error bar parameters, transpose axes, and invalid `fcn`.

### Checklist

- [ ] Test `__init__(x_series)` produces a count histogram (#PR_NUMBER)
- [ ] Test `__init__(x, y_series)` aggregates `y` values (#PR_NUMBER)
- [ ] Test `__init__(…, logx=True)` applies log₁₀ transform to `x`
  (#PR_NUMBER)
- [ ] Verify `_gb_axes` property returns `('x',)` (#PR_NUMBER)
- [ ] Test `set_path('auto')` builds path from labels (#PR_NUMBER)
- [ ] Test `set_path('custom', add_scale=False)` sets `_path` to `Path('custom')`
  (#PR_NUMBER)
- [ ] Test `set_data(x, y, clip=True)` stores DataFrame with columns `x`,`y`
  & `clip` (#PR_NUMBER)
- [ ] Verify `.clip` attribute equals `clip` flag (#PR_NUMBER)
- [ ] Test `set_axnorm('d')` sets density normalization and updates label
  (#PR_NUMBER)
- [ ] Test `set_axnorm('t')` sets total normalization (#PR_NUMBER)
- [ ] Verify `set_axnorm('x')` raises `AssertionError` (#PR_NUMBER)
- [ ] Test `construct_cdf(only_plotted=True)` yields correct CDF DataFrame
  (#PR_NUMBER)
- [ ] Verify `construct_cdf()` on non-histogram data raises `ValueError`
  (#PR_NUMBER)
- [ ] Test `_axis_normalizer(None)` returns input unchanged (#PR_NUMBER)
- [ ] Test `_axis_normalizer('d')` computes PDF correctly (#PR_NUMBER)
- [ ] Test `_axis_normalizer('t')` normalizes by max (#PR_NUMBER)
- [ ] Verify `_axis_normalizer('bad')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `agg(fcn='count')` with `axnorm='d'` works (#PR_NUMBER)
- [ ] Verify `agg(fcn='sum', axnorm='d')` raises `ValueError`
  (#PR_NUMBER)
- [ ] Verify `agg()` output reindexed correctly (#PR_NUMBER)
- [ ] Test `set_labels(y='new')` updates y-label (#PR_NUMBER)
- [ ] Verify `set_labels(z='z')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `make_plot(ax)` returns `(ax,(pl,cl,bl))` with
  `drawstyle='steps-mid'` (#PR_NUMBER)
- [ ] Test `make_plot(ax, transpose_axes=True)` swaps axes (#PR_NUMBER)
- [ ] Verify `make_plot(fcn='bad')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `make_plot(ax, errorbar=True)` renders error bars correctly
  (#PR_NUMBER)

### `hist2d.py` → Class `Hist2D(AggPlot, PlotWithZdata, CbarMaker)`

- `__init__(x, y, z=None, logx, logy, clip_data, nbins, bin_precision)`.
- `_gb_axes` and `_maybe_convert_to_log_scale(x, y)`.
- `set_labels(z=…)` and `set_data(x, y, z, clip)` including log transforms.
- `set_axnorm(new)` accepts `c`, `r`, `t`, `d`; invalid keys raise
  `AssertionError`.
- `_axis_normalizer(agg)` handles each normalization branch and iter-norm;
  invalid values raise `ValueError`.
- `agg(**kwargs)` wraps `super().agg`, applies normalizer, and reindexes.
- `_make_cbar(mappable, **kwargs)` provides default ticks for `c`/`r` norms.
- `_limit_color_norm(norm)` applies percentile clipping.
- `make_plot(ax, cbar, limit_color_norm, cbar_kwargs, fcn, alpha_fcn, **kwargs)`
  returns `(ax, Colorbar|QuadMesh)` and masks invalid data.

### Checklist

- [ ] Test `__init__(x, y)` produces 2D count heatmap (#PR_NUMBER)
- [ ] Test `__init__(x, y, z)` aggregates mean of `z` (#PR_NUMBER)
- [ ] Verify `_gb_axes` returns `('x','y')` (#PR_NUMBER)
- [ ] Test `_maybe_convert_to_log_scale` with `logx/logy=True` (#PR_NUMBER)
- [ ] Test `set_data(x, y, z, clip)` applies log transform (#PR_NUMBER)
- [ ] Test `set_labels(z='z')` updates z-label (#PR_NUMBER)
- [ ] Verify `set_axnorm('c')`, `'r'`, `'t'`, `'d'` work; invalid →
  `AssertionError` (#PR_NUMBER)
- [ ] Test `_axis_normalizer()` for each norm branch (#PR_NUMBER)
- [ ] Verify `_axis_normalizer(('c','sum'))` applies custom function
  (#PR_NUMBER)
- [ ] Verify `_axis_normalizer('bad')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `_make_cbar()` yields correct `ticks` for `c`/`r` (#PR_NUMBER)
- [ ] Test `_limit_color_norm()` sets `vmin`,`vmax`,`clip` properly
  (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=False)` returns `QuadMesh` (#PR_NUMBER)
- [ ] Test `make_plot(limit_color_norm=True, cbar=True)` applies limits
  (#PR_NUMBER)
- [ ] Test `make_plot` masks invalid data via `alpha_fcn` (#PR_NUMBER)
- [ ] Test `make_plot` forwards `cbar_kwargs` to colorbar (#PR_NUMBER)

______________________________________________________________________

## `scatter.py`

### Class `Scatter(PlotWithZdata, CbarMaker)`

- `__init__(x, y, z=None, clip_data)`.
- `_format_axis(ax, collection)` updates `sticky_edges` and data limits.
- `make_plot(ax, cbar, cbar_kwargs, **kwargs)` handles single vs. multiple
  `z`, colorbar creation, and `clip_data` path.

### Checklist

- [ ] Test `__init__(x,y)` draws scatter without colorbar (#PR_NUMBER)
- [ ] Test `__init__(x,y,z)` draws scatter with colorbar (#PR_NUMBER)
- [ ] Verify `_format_axis()` updates `sticky_edges` & data limits (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=False)` returns `(ax,None)` (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=True)` returns `(ax,Colorbar)` (#PR_NUMBER)
- [ ] Test `clip_data` path invoked when `clip=True` (#PR_NUMBER)

______________________________________________________________________

## `spiral.py`

### Numba helpers

- `get_counts_per_bin(bins, x, y)` and `calculate_bin_number_with_numba(mesh, x, y)`
  operate on small synthetic bins/data to produce correct counts and bin
  assignments.

### Class `SpiralMesh`

- Properties: `bin_id`, `cat`, `data`, `initial_edges`, `mesh`, `min_per_bin`,
  `cell_filter_thresholds`.
- `cell_filter` combines `density` and `size` thresholds.
- `set_cell_filter_thresholds(density, size)` validates kwargs; invalid keys
  raise `KeyError`.
- `set_initial_edges`, `set_min_per_bin`, and `set_data` update internal state.
- `initialize_bins()` builds mesh of expected shape.

### Checklist

- [ ] Test `get_counts_per_bin()` on synthetic bins → correct counts (#PR_NUMBER)
- [ ] Test `calculate_bin_number_with_numba()` assigns correct bin IDs
  (#PR_NUMBER)
- [ ] Verify `.bin_id` property returns bin IDs (#PR_NUMBER)
- [ ] Verify `.cat` property returns category labels (#PR_NUMBER)
- [ ] Verify `.data` property returns stored input data (#PR_NUMBER)
- [ ] Verify `.initial_edges` property returns initial bin edges (#PR_NUMBER)
- [ ] Verify `.mesh` property returns computed mesh (#PR_NUMBER)
- [ ] Verify `.min_per_bin` property returns minimum per bin (#PR_NUMBER)
- [ ] Verify `.cell_filter_thresholds` property returns filter thresholds (#PR_NUMBER)
- [ ] Test `set_cell_filter_thresholds(density=0.1,size=0.9)` updates thresholds
  (#PR_NUMBER)
- [ ] Verify `set_cell_filter_thresholds(bad=…)` raises `KeyError`
  (#PR_NUMBER)
- [ ] Test `.cell_filter` logic for density & size filters (#PR_NUMBER)
- [ ] Test `set_initial_edges()` updates initial bin edges (#PR_NUMBER)
- [ ] Test `set_min_per_bin()` updates minimum per bin (#PR_NUMBER)
- [ ] Test `set_data()` stores input data (#PR_NUMBER)
- [ ] Test `initialize_bins()` constructs mesh of expected shape (#PR_NUMBER)

______________________________________________________________________

## `orbits.py`

### Class `OrbitPlot(ABC)`

- `__init__(orbit, *args)` validates `orbit` type; invalid types raise
  `TypeError`.
- Properties: `_disable_both`, `orbit`, `_orbit_key`, `grouped`.
- `set_path(*args, orbit=…)` appends orbit path.
- `set_orbit(new)` sorts orbits and validates type.
- `make_cut()` adds “Inbound”/“Outbound” (and “Both”) categories.

### Class `OrbitHist1D(OrbitPlot, Hist1D)`

- `_format_axis(ax)` adds legend.
- `agg(**kwargs)` merges “Both” leg; disabled via `_disable_both`.
- `make_plot(ax, fcn, **kwargs)` calls `tools.subplots` and plots each leg.

### Class `OrbitHist2D(OrbitPlot, Hist2D)`

- `_format_in_out_axes(inbound, outbound)`, `_prune_lower_yaxis_ticks`, and
  `_format_in_out_both_axes` manage axis formatting.
- `agg(**kwargs)` wraps and normalizes per-orbit.
- `project_1d(axis, project_counts, **kwargs)` returns an `OrbitHist1D`
  instance.

### Checklist

- [ ] Verify invalid `orbit` type in `__init__` raises `TypeError`
  (#PR_NUMBER)
- [ ] Verify `_disable_both` property is `True` by default (#PR_NUMBER)
- [ ] Verify `.orbit` property returns the `IntervalIndex` (#PR_NUMBER)
- [ ] Verify `_orbit_key` returns `"Orbit"` (#PR_NUMBER)
- [ ] Verify `.grouped` groups by `_gb_axes` + `_orbit_key` (#PR_NUMBER)
- [ ] Test `set_path(…, orbit=idx)` appends `orbit.path` (#PR_NUMBER)
- [ ] Test `set_orbit(idx)` sorts and validates type (#PR_NUMBER)
- [ ] Test `make_cut()` adds “Inbound”/“Outbound” (and “Both”) categories
  (#PR_NUMBER)
- [ ] Verify `_format_axis(ax)` adds a legend (#PR_NUMBER)
- [ ] Test `agg()` merges “Both” leg when `_disable_both=False` (#PR_NUMBER)
- [ ] Test `make_plot(ax)` plots each orbit leg via `tools.subplots()`
  (#PR_NUMBER)
- [ ] Test `_format_in_out_axes()` swaps x-limits and colors spines
  (#PR_NUMBER)
- [ ] Test `_prune_lower_yaxis_ticks()` prunes ticks correctly (#PR_NUMBER)
- [ ] Test `_format_in_out_both_axes()` aligns y-limits across
  inbound/outbound/both (#PR_NUMBER)
- [ ] Test `agg()` normalizes per-orbit legs (#PR_NUMBER)
- [ ] Test `project_1d('x')` returns a valid `OrbitHist1D` (#PR_NUMBER)

______________________________________________________________________

## `tools.py`

- `subplots(nrows, ncols, scale_width, scale_height, **kwargs)` scales figure
  size with grid shape.
- `save(fig, spath, add_info, log, pdf, png, **kwargs)` writes `.pdf` and `.png`
  files, adds timestamp text, and supports optional logging.
- `joint_legend(*axes, idx_for_legend, **kwargs)` merges legend entries without
  duplicates and sorts them.
- `multipanel_figure_shared_cbar(...)` (if present) creates grid with shared
  colorbar.

### Checklist

- [ ] Test `subplots(2,2,scale_width=1.5,scale_height=0.5)` returns 2×2 axes with
  correct figsize (#PR_NUMBER)
- [ ] Test `save(fig, path, pdf=True,png=True)` writes both `.pdf` and `.png`
  files (#PR_NUMBER)
- [ ] Test PNG version includes timestamp text (#PR_NUMBER)
- [ ] Test `save(..., log=False)` skips logging calls (#PR_NUMBER)
- [ ] Test `joint_legend(ax1,ax2)` merges legend entries, no duplicates, sorted
  (#PR_NUMBER)
- [ ] (If present) Test `multipanel_figure_shared_cbar(...)` arranges shared
  colorbar correctly (#PR_NUMBER)

______________________________________________________________________

## `select_data_from_figure.py`

### Class `SelectFromPlot2D`

- `__init__(plotter, ax, has_colorbar, xdate, ydate, text_kwargs)`.
- Properties: `ax`, `corners`, `date_axes`, `is_multipanel`, `selector`, `text`,
  and more.
- `_init_corners`, `_add_corners`, `_finalize_text`, `_update_text` manage
  corner selection and text updates.
- `disconnect(other, scatter_kwargs, **kwargs)` calls `sample_data`,
  `scatter_sample`, and `plot_failed_samples`.
- `onselect(press, release)` adds patch, updates corners and text.
- `set_ax(ax, has_colorbar)`, `start_text`, `start_selector`, `sample_data(n, random_state)`; `sample_data(frac=…)` raises `NotImplementedError`.

### Checklist

- [ ] Test `__init__(plotter,ax)` initializes selector and text objects
  (#PR_NUMBER)
- [ ] Verify `.ax`, `.corners`, `.date_axes`, `.is_multipanel` props
  (#PR_NUMBER)
- [ ] Verify `.selector` property exposes selector object (#PR_NUMBER)
- [ ] Verify `.text` property exposes text annotation (#PR_NUMBER)
- [ ] Test `_init_corners()` initializes corner coordinates (#PR_NUMBER)
- [ ] Test `_add_corners()` appends new corner tuples (#PR_NUMBER)
- [ ] Test `_finalize_text()` formats final selection text (#PR_NUMBER)
- [ ] Test `_update_text()` formats bounding-box extents (#PR_NUMBER)
- [ ] Test `onselect(press,release)` adds rectangle patch and updates
  corners/text (#PR_NUMBER)
- [ ] Test `disconnect()` calls `sample_data()`, `scatter_sample()`,
  `plot_failed_samples()`, disconnects events (#PR_NUMBER)
- [ ] Test `set_ax(ax, has_colorbar)` updates axis and colorbar state
  (#PR_NUMBER)
- [ ] Test `start_text()` initializes the annotation text object (#PR_NUMBER)
- [ ] Test `start_selector()` starts selection widget (#PR_NUMBER)
- [ ] Test `sample_data(n=3,random_state=…)` returns correct sampled indices
  (#PR_NUMBER)
- [ ] Verify `sample_data(frac=0.1)` raises `NotImplementedError` (#PR_NUMBER)

______________________________________________________________________

## `labels/base.py`

- Namedtuples: `LogAxes`, `AxesLabels`, `RangeLimits` with defaults and custom
  values.
- Class `Base`: shared logic with `plotting/base`.

### Checklist

- [ ] Verify `LogAxes`, `AxesLabels`, `RangeLimits` namedtuples have correct
  defaults (#PR_NUMBER)
- [ ] (Shared with plotting/base) Repeat `Base` tests if context differs
  (#PR_NUMBER)

______________________________________________________________________

## `labels/special.py`

### Abstract `ArbitraryLabel(Base)`

- Cannot instantiate; subclass must implement `__str__`.

### `ManualLabel(tex, unit, path=None)`

- `set_tex` and `set_unit` strip `$` and map units via `base._inU`.
- `__str__` and `path` manage default vs. custom paths.

### Prebuilt labels

- `Vsw`, `CarringtonRotation(short_label)`, `Count(norm)`, `Power`,
  `Probability(other_label, comparison)` verify `tex`, `units`, `path`, and
  error on invalid input.

### Checklist

- [ ] Verify instantiating `ArbitraryLabel` directly raises `TypeError`
  (#PR_NUMBER)
- [ ] Test `set_tex('$X$')` strips dollar signs (#PR_NUMBER)
- [ ] Test `set_unit('km')` maps via `base._inU` (#PR_NUMBER)
- [ ] Verify `__str__` formats `tex` and `unit` correctly (#PR_NUMBER)
- [ ] Verify `.path` property returns default (from `tex`) and custom path
  (#PR_NUMBER)
- [ ] Verify `Vsw.tex`, `Vsw.units`, `Vsw.path` (#PR_NUMBER)
- [ ] Test `CarringtonRotation(short_label=False)` toggles `tex` output
  (#PR_NUMBER)
- [ ] Test `Count(norm='d')` builds `tex` and `path` for density norm
  (#PR_NUMBER)
- [ ] Test `Count(norm=None)` builds default count label (#PR_NUMBER)
- [ ] Verify `Power` and `Probability(other_label,comparison)` produce correct
  `tex`,`units`,`path` (#PR_NUMBER)
- [ ] Verify invalid `other_label` or `comparison` in `Probability` raises
  `AssertionError` (#PR_NUMBER)

______________________________________________________________________

## Fixtures & Utilities

- `pytest` fixtures: dummy `Series`, `DataFrame`, `IntervalIndex`, `Axes` from
  `plt.subplots()`.
- `tmp_path` for file I/O.
- Parameterized tests across modes and combinations.

## Justification

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
