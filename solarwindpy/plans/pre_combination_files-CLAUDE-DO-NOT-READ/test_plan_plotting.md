# Test Suite Plan for `solarwindpy.plotting` (branch `update-2025`)

## Overview

The `solarwindpy.plotting` subpackage offers high-level plotting utilities built on pandas and Matplotlib.  
This plan covers **every** class, method, property (including non-public elements), and helper function in:

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

Tests are grouped by module.  Each entry lists the API under test, the scenarios to cover (inputs, edge-cases, invalid calls), and **why** the test is necessary.

---

## `base.py`

### Class `Base` (abstract)
- **Instantiation via subclass**  
  - _Why_: ensure `_init_logger`, `_labels`, `_log`, `path` setup.
- **`__str__`**  
  - returns the class name.
- **Properties**  
  - `data`, `clip`, `log`, `labels`, `path` reflect internal state.
- **`set_log(x, y)`**  
  - toggles `log.x`, `log.y`; test defaults and explicit values.
- **`set_labels(auto_update_path=True)`**  
  - updates `labels` and regenerates `path`.
  - test with unexpected kwarg → `KeyError`.

---

## `agg_plot.py`

### Class `AggPlot(Base)`
- **Properties**  
  - `edges`, `categoricals`, `intervals`, `cut`, `clim`, `agg_axes`, `joint`, `grouped`, `axnorm`.
- **Static method `clip_data(data, clip)`**  
  - series vs. DataFrame, `'l'`, `'u'`, numeric clip.
  - invalid `clip` type → `TypeError`.
- **`set_clim(lower, upper)`**  
  - sets `_clim`.
- **Justification**: foundation for all histogram and heatmap classes.

---

## `histograms.py`

### Module exports
- Test that `AggPlot`, `Hist1D`, `Hist2D` are re-exported correctly.

### `hist1d.py` → class `Hist1D(AggPlot)`
- **`__init__(x, y=None, logx, axnorm, clip_data, nbins, bin_precision)`**  
  - default count vs. y-aggregation.
  - `logx=True` transforms data.
- **`_gb_axes`**  
  - returns `('x',)`.
- **`set_path(new, add_scale)`**  
  - `"auto"` vs. custom.
- **`set_data(x, y, clip)`**  
  - correct DataFrame shape; clip flag stored.
- **`set_axnorm(new)`**  
  - valid keys (`d`, `t`), invalid → `AssertionError`.
- **`construct_cdf(only_plotted)`**  
  - valid histogram → correct CDF; invalid data → `ValueError`.
- **`_axis_normalizer(agg)`**  
  - None, density, total, invalid → `ValueError`.
- **`agg(**kwargs)`**  
  - fcn count+`d` norm requires `fcn='count'`; else `ValueError`.
- **`set_labels(y=…)`**  
  - disallow `z` → `ValueError`.
- **`make_plot(ax, fcn, transpose_axes, **kwargs)`**  
  - returns `(ax, (pl, cl, bl))`; test errorbar params, transpose axes swap, invalid `fcn` → `ValueError`.

### `hist2d.py` → class `Hist2D(AggPlot, PlotWithZdata, CbarMaker)`
- **`__init__(x, y, z=None, logx, logy, clip_data, nbins, bin_precision)`**  
- **`_gb_axes`**, **`_maybe_convert_to_log_scale(x, y)`**  
- **`set_labels(z=…)`**, **`set_data(x, y, z, clip)`** — log transforms.  
- **`set_axnorm(new)`**: keys `c`, `r`, `t`, `d`; invalid → `AssertionError`.  
- **`_axis_normalizer(agg)`**: each norm branch, iter-norm; invalid → `ValueError`.  
- **`agg(**kwargs)`**: wraps `super().agg`, applies normalizer & reindex.  
- **`_make_cbar(mappable, **kwargs)`**: default ticks for `c`/`r`.  
- **`_limit_color_norm(norm)`**: percentile clipping.  
- **`make_plot(ax, cbar, limit_color_norm, cbar_kwargs, fcn, alpha_fcn, **kwargs)`**  
  - returns `(ax, Colorbar|QuadMesh)`.  
  - test with/without cbar, limit_color_norm, mask invalid data.

---

## `scatter.py`

### Class `Scatter(PlotWithZdata, CbarMaker)`
- **`__init__(x, y, z=None, clip_data)`**  
- **`_format_axis(ax, collection)`**: updates `sticky_edges` and data limits.  
- **`make_plot(ax, cbar, cbar_kwargs, **kwargs)`**  
  - single vs. multiple `z`; test cbar creation, correct kwargs, clip_data path.

---

## `spiral.py`

### Numba helpers
- **`get_counts_per_bin(bins, x, y)`**, **`calculate_bin_number_with_numba(mesh, x, y)`**  
  - small synthetic bins/data → correct counts and bin assignments.

### Class `SpiralMesh`
- **Properties**: `bin_id`, `cat`, `data`, `initial_edges`, `mesh`, `min_per_bin`, `cell_filter_thresholds`.  
- **`cell_filter`**: combinations of `density`/`size` thresholds.  
- **`set_cell_filter_thresholds(density, size)`**: valid/invalid kwargs → `KeyError`.  
- **`set_initial_edges`, `set_min_per_bin`, `set_data`**.  
- **`initialize_bins()`**: builds mesh of expected shape.

---

## `orbits.py`

### Class `OrbitPlot(ABC)`
- **`__init__(orbit, *args)`**: invalid `orbit` type → `TypeError`.  
- **Properties**: `_disable_both`, `orbit`, `_orbit_key`, `grouped`.  
- **`set_path(*args, orbit=…)`**: appends orbit path.  
- **`set_orbit(new)`**: sorts, type validation.  
- **`make_cut()`**: adds “Inbound”/“Outbound” (and “Both”) categories.

### Class `OrbitHist1D(OrbitPlot, Hist1D)`
- **`_format_axis(ax)`**: adds legend.  
- **`agg(**kwargs)`**: merges “Both” leg; disabled via `_disable_both`.  
- **`make_plot(ax, fcn, **kwargs)`**: calls `tools.subplots`, plots each leg.

### Class `OrbitHist2D(OrbitPlot, Hist2D)`
- **`_format_in_out_axes(inbound, outbound)`**, **`_prune_lower_yaxis_ticks`**, **`_format_in_out_both_axes`**.  
- **`agg(**kwargs)`**: wraps and normalizes per-orbit.  
- **`project_1d(axis, project_counts, **kwargs)`**: returns `OrbitHist1D` instance.

---

## `tools.py`

- **`subplots(nrows, ncols, scale_width, scale_height, **kwargs)`**  
  - figure size scales with grid shape.  
- **`save(fig, spath, add_info, log, pdf, png, **kwargs)`**  
  - writes both `.pdf`/`.png`, adds timestamp text; test with tempdir fixture.  
- **`joint_legend(*axes, idx_for_legend, **kwargs)`**  
  - merges legend entries from multiple axes; ensures no duplicates, sorted.  
- **`multipanel_figure_shared_cbar(...)`** (if present)  
  - grid with shared colorbar.

---

## `select_data_from_figure.py`

### Class `SelectFromPlot2D`
- **`__init__(plotter, ax, has_colorbar, xdate, ydate, text_kwargs)`**  
- **Properties**: `ax`, `corners`, `date_axes`, `is_multipanel`, `selector`, `text`, etc.  
- **`_init_corners`, `_add_corners`, `_finalize_text`, `_update_text`**  
- **`disconnect(other, scatter_kwargs, **kwargs)`**: calls `sample_data`, `scatter_sample`, `plot_failed_samples`.  
- **`onselect(press, release)`**: adds patch, updates corners & text.  
- **`set_ax(ax, has_colorbar)`**, **`start_text`**, **`start_selector`**, **`sample_data(n, random_state)`**: `NotImplementedError` on `frac`.

---

## `labels/base.py`

- **Namedtuples**: `LogAxes`, `AxesLabels`, `RangeLimits`. Test defaults & custom.  
- **Class `Base`**: shared logic with plotting/base.

---

## `labels/special.py`

### Abstract `ArbitraryLabel(Base)`
- cannot instantiate; subclass must implement `__str__`.

### `ManualLabel(tex, unit, path=None)`
- **`set_tex`, `set_unit`**: strip `$`, map unit via `base._inU`.  
- **`__str__`**, **`path`**: default vs. custom.

### Prebuilt labels
- **`Vsw`**, **`CarringtonRotation(short_label)`**, **`Count(norm)`**, **`Power`**, **`Probability(other_label, comparison)`**  
  - verify `tex`, `units`, `path`, `build_label()` logic, error on invalid.

---

## Fixtures & Utilities

- **`pytest`** fixtures: dummy `Series`, `DataFrame`, `IntervalIndex`, `Axes` from `plt.subplots()`.  
- **`tmp_path`** for file I/O.  
- **Parameterized** tests across modes and combinations.

---

## Justification

- Ensures **correct functionality**, **edge-case handling**, API stability, and protects **non-public internals**.

---

*Add this file as* `TEST_PLAN.md` *at the root of your repo.*