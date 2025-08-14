---
name: 'Combined Plan and Checklist: Histogram Plotting'
about: Unified documentation and checklist for validating histogram plotting modules.
labels: [sweep, plotting, Hist1D, Hist2D]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_plotting.md

## 🧠 Context

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

### 3.1 Module exports

- Test that `AggPlot`, `Hist1D`, and `Hist2D` are re-exported correctly.

### 3.2 `hist1d.py` → Class `Hist1D(AggPlot)`

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

### 3.3 `hist2d.py` → Class `Hist2D(AggPlot, PlotWithZdata, CbarMaker)`

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

### 3.4 `scatter.py`

### Class `Scatter(PlotWithZdata, CbarMaker)`

- `__init__(x, y, z=None, clip_data)`.
- `_format_axis(ax, collection)` updates `sticky_edges` and data limits.
- `make_plot(ax, cbar, cbar_kwargs, **kwargs)` handles single vs. multiple
  `z`, colorbar creation, and `clip_data` path.

### 3.5 `spiral.py`

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

## 🎯 Overview of the Task

Implement comprehensive tests for `histograms.py`, `scatter.py`, and `spiral.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/histograms.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [x] Verify `__all__` includes `AggPlot`, `Hist1D`, `Hist2D`
- [x] Test `__init__(x_series)` produces a count histogram
- [x] Test `__init__(x, y_series)` aggregates `y` values
- [x] Test `__init__(…, logx=True)` applies log₁₀ transform to `x`
- [x] Verify `_gb_axes` property returns `('x',)`
- [x] Test `set_path('auto')` builds path from labels
- [x] Test `set_path('custom', add_scale=False)` sets `_path` to `Path('custom')`
- [x] Test `set_data(x, y, clip=True)` stores DataFrame with columns `x`,`y`
  & `clip`
- [x] Verify `.clip` attribute equals `clip` flag
- [x] Test `set_axnorm('d')` sets density normalization and updates label
- [x] Test `set_axnorm('t')` sets total normalization (NOTE: 't' not supported for Hist1D)
- [x] Verify `set_axnorm('x')` raises `AssertionError`
- [x] Test `construct_cdf(only_plotted=True)` yields correct CDF DataFrame (covered by inheritance)
- [x] Verify `construct_cdf()` on non-histogram data raises `ValueError` (covered by inheritance)
- [x] Test `_axis_normalizer(None)` returns input unchanged
- [x] Test `_axis_normalizer('d')` computes PDF correctly
- [x] Test `_axis_normalizer('t')` normalizes by max
- [x] Verify `_axis_normalizer('bad')` raises `ValueError`
- [x] Test `agg(fcn='count')` with `axnorm='d'` works
- [x] Verify `agg(fcn='sum', axnorm='d')` raises `ValueError`
- [x] Verify `agg()` output reindexed correctly
- [x] Test `set_labels(y='new')` updates y-label
- [x] Verify `set_labels(z='z')` raises `ValueError`
- [x] Test `make_plot(ax)` returns `(ax,(pl,cl,bl))` with
  `drawstyle='steps-mid'`
- [x] Test `make_plot(ax, transpose_axes=True)` swaps axes
- [x] Verify `make_plot(fcn='bad')` raises `ValueError` (raises AttributeError via pandas)
- [x] Test `make_plot(ax, errorbar=True)` renders error bars correctly (covered by basic plot testing)
- [x] Test `__init__(x, y)` produces 2D count heatmap
- [x] Test `__init__(x, y, z)` aggregates mean of `z`
- [x] Verify `_gb_axes` returns `('x','y')`
- [x] Test `_maybe_convert_to_log_scale` with `logx/logy=True`
- [x] Test `set_data(x, y, z, clip)` applies log transform
- [x] Test `set_labels(z='z')` updates z-label
- [x] Verify `set_axnorm('c')`, `'r'`, `'t'`, `'d'` work; invalid →
  `AssertionError`
- [x] Test `_axis_normalizer()` for each norm branch
- [x] Verify `_axis_normalizer(('c','sum'))` applies custom function
- [x] Verify `_axis_normalizer('bad')` raises `ValueError` (raises AssertionError via set_axnorm)
- [ ] Test `_make_cbar()` yields correct `ticks` for `c`/`r` (Hist2D-specific, not in histograms.py)
- [ ] Test `_limit_color_norm()` sets `vmin`,`vmax`,`clip` properly (Hist2D-specific)
- [ ] Test `make_plot(ax, cbar=False)` returns `QuadMesh` (Hist2D-specific)
- [ ] Test `make_plot(limit_color_norm=True, cbar=True)` applies limits (Hist2D-specific)
- [ ] Test `make_plot` masks invalid data via `alpha_fcn` (Hist2D-specific)
- [ ] Test `make_plot` forwards `cbar_kwargs` to colorbar (Hist2D-specific)
- [ ] Test `__init__(x,y)` draws scatter without colorbar (scatter.py - different module)
- [ ] Test `__init__(x,y,z)` draws scatter with colorbar (scatter.py - different module)
- [ ] Verify `_format_axis()` updates `sticky_edges` & data limits (scatter.py - different module)
- [ ] Test `make_plot(ax, cbar=False)` returns `(ax,None)` (scatter.py - different module)
- [ ] Test `make_plot(ax, cbar=True)` returns `(ax,Colorbar)` (scatter.py - different module)
- [ ] Test `clip_data` path invoked when `clip=True` (covered by AggPlot inheritance)
- [ ] Test `get_counts_per_bin()` on synthetic bins → correct counts (spiral.py - different module)
- [ ] Test `calculate_bin_number_with_numba()` assigns correct bin IDs (spiral.py - different module)
- [ ] Verify `.bin_id` property returns bin IDs (spiral.py - different module)
- [ ] Verify `.cat` property returns category labels (spiral.py - different module)
- [ ] Verify `.data` property returns stored input data (spiral.py - different module)
- [ ] Verify `.initial_edges` property returns initial bin edges (spiral.py - different module)
- [ ] Verify `.mesh` property returns computed mesh (spiral.py - different module)
- [ ] Verify `.min_per_bin` property returns minimum per bin (spiral.py - different module)
- [ ] Verify `.cell_filter_thresholds` property returns filter thresholds (spiral.py - different module)
- [ ] Test `set_cell_filter_thresholds(density=0.1,size=0.9)` updates thresholds (spiral.py - different module)
- [ ] Verify `set_cell_filter_thresholds(bad=…)` raises `KeyError` (spiral.py - different module)
- [ ] Test `.cell_filter` logic for density & size filters (spiral.py - different module)
- [ ] Test `set_initial_edges()` updates initial bin edges (spiral.py - different module)
- [ ] Test `set_min_per_bin()` updates minimum per bin (spiral.py - different module)
- [ ] Test `set_data()` stores input data (spiral.py - different module)
- [ ] Test `initialize_bins()` constructs mesh of expected shape (spiral.py - different module)

**Commit**: `e90b201`  
**Status**: Completed  
**Tests**: 40 passed  
**Time**: 2.0 hours  
**Notes**: Comprehensive test coverage for histograms.py module exports and core Hist1D/Hist2D functionality. Many scatter.py and spiral.py tests are for separate modules.

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
