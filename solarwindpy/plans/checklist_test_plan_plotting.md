## 📦 `solarwindpy.plotting` Test Plan (branch `update-2025`)

### 🧩 `base.py`

#### Class `Base` (abstract)

- [ ] Instantiate a minimal subclass of `Base` to verify `_init_logger`, `_labels`, `_log` and `path` are initialized (#PR_NUMBER)
- [ ] Verify that `__str__` returns the class name (#PR_NUMBER)
- [ ] Verify that `.data` property returns the internal `_data` (#PR_NUMBER)
- [ ] Verify that `.clip` property returns the internal `_clip` (#PR_NUMBER)
- [ ] Verify that `.log` property returns the internal `_log` (#PR_NUMBER)
- [ ] Verify that `.labels` property returns the internal `_labels` (#PR_NUMBER)
- [ ] Verify that `.path` property returns the internal `_path` (#PR_NUMBER)
- [ ] Test `set_log()` with defaults toggles `log.x` and `log.y` appropriately (#PR_NUMBER)
- [ ] Test `set_log(x=True, y=False)` correctly updates `log` axes (#PR_NUMBER)
- [ ] Test `set_labels()` updates labels and regenerates `path` (#PR_NUMBER)
- [ ] Verify that `set_labels(unexpected=…)` raises `KeyError` (#PR_NUMBER)

______________________________________________________________________

### 🔢 `agg_plot.py`

#### Class `AggPlot(Base)`

- [ ] Verify `.edges` property constructs correct bin-edge arrays (#PR_NUMBER)
- [ ] Verify `.categoricals` property returns categorical bins mapping (#PR_NUMBER)
- [ ] Verify `.intervals` property returns correct `IntervalIndex` objects (#PR_NUMBER)
- [ ] Verify `.cut` property returns the internal `_cut` DataFrame (#PR_NUMBER)
- [ ] Verify `.clim` property returns the internal `_clim` tuple (#PR_NUMBER)
- [ ] Verify `.agg_axes` returns the correct aggregation column (#PR_NUMBER)
- [ ] Verify `.joint` returns a `Series` with a `MultiIndex` (#PR_NUMBER)
- [ ] Verify `.grouped` returns a `GroupBy` on the correct axes (#PR_NUMBER)
- [ ] Verify `.axnorm` returns the internal `_axnorm` value (#PR_NUMBER)
- [ ] Test `clip_data(pd.Series, 'l')`, `'u'`, numeric → correct clipping (#PR_NUMBER)
- [ ] Test `clip_data(pd.DataFrame, …)` with lower/upper modes (#PR_NUMBER)
- [ ] Verify `clip_data()` raises `TypeError` on unsupported input (#PR_NUMBER)
- [ ] Test `set_clim(2, 10)` sets `_clim` to `(2, 10)` (#PR_NUMBER)

______________________________________________________________________

### 📊 `histograms.py`

#### Module exports

- [ ] Verify `__all__` includes `AggPlot`, `Hist1D`, `Hist2D` (#PR_NUMBER)

#### `hist1d.py` → Class `Hist1D(AggPlot)`

- [ ] Test `__init__(x_series)` produces a count histogram (#PR_NUMBER)
- [ ] Test `__init__(x, y_series)` aggregates `y` values (#PR_NUMBER)
- [ ] Test `__init__(…, logx=True)` applies log₁₀ transform to `x` (#PR_NUMBER)
- [ ] Verify `_gb_axes` property returns `('x',)` (#PR_NUMBER)
- [ ] Test `set_path('auto')` builds path from labels (#PR_NUMBER)
- [ ] Test `set_path('custom', add_scale=False)` sets `_path` to `Path('custom')` (#PR_NUMBER)
- [ ] Test `set_data(x, y, clip=True)` stores DataFrame with columns `x`,`y` & `clip` (#PR_NUMBER)
- [ ] Verify `.clip` attribute equals `clip` flag (#PR_NUMBER)
- [ ] Test `set_axnorm('d')` sets density normalization and updates label (#PR_NUMBER)
- [ ] Test `set_axnorm('t')` sets total normalization (#PR_NUMBER)
- [ ] Verify `set_axnorm('x')` raises `AssertionError` (#PR_NUMBER)
- [ ] Test `construct_cdf(only_plotted=True)` yields correct CDF DataFrame (#PR_NUMBER)
- [ ] Verify `construct_cdf()` on non-histogram data raises `ValueError` (#PR_NUMBER)
- [ ] Test `_axis_normalizer(None)` returns input unchanged (#PR_NUMBER)
- [ ] Test `_axis_normalizer(‘d’)` computes PDF correctly (#PR_NUMBER)
- [ ] Test `_axis_normalizer(‘t’)` normalizes by max (#PR_NUMBER)
- [ ] Verify `_axis_normalizer('bad')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `agg(fcn='count')` with `axnorm='d'` works (#PR_NUMBER)
- [ ] Verify `agg(fcn='sum', axnorm='d')` raises `ValueError` (#PR_NUMBER)
- [ ] Verify `agg()` output reindexed correctly (#PR_NUMBER)
- [ ] Test `set_labels(y='new')` updates y-label (#PR_NUMBER)
- [ ] Verify `set_labels(z='z')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `make_plot(ax)` returns `(ax,(pl,cl,bl))` with `drawstyle='steps-mid'` (#PR_NUMBER)
- [ ] Test `make_plot(ax, transpose_axes=True)` swaps axes (#PR_NUMBER)
- [ ] Verify `make_plot(fcn='bad')` raises `ValueError` (#PR_NUMBER)

#### `hist2d.py` → Class `Hist2D(AggPlot, PlotWithZdata, CbarMaker)`

- [ ] Test `__init__(x, y)` produces 2D count heatmap (#PR_NUMBER)
- [ ] Test `__init__(x, y, z)` aggregates mean of `z` (#PR_NUMBER)
- [ ] Verify `_gb_axes` returns `('x','y')` (#PR_NUMBER)
- [ ] Test `_maybe_convert_to_log_scale` with `logx/logy=True` (#PR_NUMBER)
- [ ] Test `set_data(x, y, z, clip)` applies log transform (#PR_NUMBER)
- [ ] Test `set_labels(z='z')` updates z-label (#PR_NUMBER)
- [ ] Verify `set_axnorm('c')`, `'r'`, `'t'`, `'d'` work; invalid → AssertionError (#PR_NUMBER)
- [ ] Test `_axis_normalizer()` for each norm branch (#PR_NUMBER)
- [ ] Verify `_axis_normalizer(('c','sum'))` applies custom function (#PR_NUMBER)
- [ ] Verify `_axis_normalizer('bad')` raises `ValueError` (#PR_NUMBER)
- [ ] Test `_make_cbar()` yields correct `ticks` for `c`/`r` (#PR_NUMBER)
- [ ] Test `_limit_color_norm()` sets `vmin`,`vmax`,`clip` properly (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=False)` returns `QuadMesh` (#PR_NUMBER)
- [ ] Test `make_plot(limit_color_norm=True, cbar=True)` applies limits (#PR_NUMBER)

______________________________________________________________________

### 🖌️ `scatter.py`

#### Class `Scatter(PlotWithZdata, CbarMaker)`

- [ ] Test `__init__(x,y)` draws scatter without colorbar (#PR_NUMBER)
- [ ] Test `__init__(x,y,z)` draws scatter with colorbar (#PR_NUMBER)
- [ ] Verify `_format_axis()` updates `sticky_edges` & data limits (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=False)` returns `(ax,None)` (#PR_NUMBER)
- [ ] Test `make_plot(ax, cbar=True)` returns `(ax,Colorbar)` (#PR_NUMBER)
- [ ] Test `clip_data` path invoked when `clip=True` (#PR_NUMBER)

______________________________________________________________________

### 🌀 `spiral.py`

#### Numba helpers

- [ ] Test `get_counts_per_bin()` on synthetic bins → correct counts (#PR_NUMBER)
- [ ] Test `calculate_bin_number_with_numba()` assigns correct bin IDs (#PR_NUMBER)

#### Class `SpiralMesh`

- [ ] Verify `.bin_id`, `.cat`, `.data`, `.initial_edges`, `.mesh`, `.min_per_bin`, `.cell_filter_thresholds` props (#PR_NUMBER)
- [ ] Test `set_cell_filter_thresholds(density=0.1,size=0.9)` updates thresholds (#PR_NUMBER)
- [ ] Verify `set_cell_filter_thresholds(bad=…)` raises `KeyError` (#PR_NUMBER)
- [ ] Test `.cell_filter` logic for density & size filters (#PR_NUMBER)
- [ ] Test `set_initial_edges(edges)` updates initial edge intervals (#PR_NUMBER)
- [ ] Test `set_min_per_bin(5)` updates `min_per_bin` (#PR_NUMBER)
- [ ] Test `set_data(df)` stores provided DataFrame (#PR_NUMBER)
- [ ] Test `initialize_bins()` constructs mesh of expected shape (#PR_NUMBER)

______________________________________________________________________

### 🌠 `orbits.py`

#### Class `OrbitPlot(ABC)`

- [ ] Verify invalid `orbit` type in `__init__` raises `TypeError` (#PR_NUMBER)
- [ ] Verify `_disable_both` property is `True` by default (#PR_NUMBER)
- [ ] Verify `.orbit` property returns the `IntervalIndex` (#PR_NUMBER)
- [ ] Verify `_orbit_key` returns `"Orbit"` (#PR_NUMBER)
- [ ] Verify `.grouped` groups by `_gb_axes` + `_orbit_key` (#PR_NUMBER)
- [ ] Test `set_path(…, orbit=idx)` appends `orbit.path` (#PR_NUMBER)
- [ ] Test `set_orbit(idx)` sorts and validates type (#PR_NUMBER)
- [ ] Test `make_cut()` adds “Inbound”/“Outbound” (and “Both”) categories (#PR_NUMBER)

#### Class `OrbitHist1D(OrbitPlot, Hist1D)`

- [ ] Verify `_format_axis(ax)` adds a legend (#PR_NUMBER)
- [ ] Test `agg()` merges “Both” leg when `_disable_both=False` (#PR_NUMBER)
- [ ] Test `make_plot(ax)` plots each orbit leg via `tools.subplots()` (#PR_NUMBER)

#### Class `OrbitHist2D(OrbitPlot, Hist2D)`

- [ ] Test `_format_in_out_axes()` swaps x-limits and colors spines (#PR_NUMBER)
- [ ] Test `_prune_lower_yaxis_ticks()` prunes ticks correctly (#PR_NUMBER)
- [ ] Test `_format_in_out_both_axes()` aligns y-limits across inbound/outbound/both (#PR_NUMBER)
- [ ] Test `agg()` normalizes per-orbit legs (#PR_NUMBER)
- [ ] Test `project_1d('x')` returns a valid `OrbitHist1D` (#PR_NUMBER)

______________________________________________________________________

### 🛠️ `tools.py`

- [ ] Test `subplots(2,2,scale_width=1.5,scale_height=0.5)` returns 2×2 axes with correct figsize (#PR_NUMBER)
- [ ] Test `save(fig, path, pdf=True,png=True)` writes both `.pdf` and `.png` files (#PR_NUMBER)
- [ ] Test PNG version includes timestamp text (#PR_NUMBER)
- [ ] Test `save(..., log=False)` skips logging calls (#PR_NUMBER)
- [ ] Test `joint_legend(ax1,ax2)` merges legend entries, no duplicates, sorted (#PR_NUMBER)
- [ ] (If present) Test `multipanel_figure_shared_cbar(...)` arranges shared colorbar correctly (#PR_NUMBER)

______________________________________________________________________

### 🎨 `select_data_from_figure.py`

#### Class `SelectFromPlot2D`

- [ ] Test `__init__(plotter,ax,has_colorbar,xdate,ydate,text_kwargs)` stores flags and initializes selector and text (#PR_NUMBER)
- [ ] Verify `.ax`, `.corners`, `.date_axes`, `.is_multipanel`, `.selector`, `.text` props (#PR_NUMBER)
- [ ] Test `_add_corners()` appends new corner tuples (#PR_NUMBER)
- [ ] Test `_update_text()` formats bounding-box extents (#PR_NUMBER)
- [ ] Test `_init_corners()` resets corners list (#PR_NUMBER)
- [ ] Test `_finalize_text()` applies final formatting (#PR_NUMBER)
- [ ] Test `set_ax(new_ax,has_colorbar=True)` updates axes and colorbar flag (#PR_NUMBER)
- [ ] Test `start_text()` creates text annotation (#PR_NUMBER)
- [ ] Test `start_selector()` attaches selector widget (#PR_NUMBER)
- [ ] Test `onselect(press,release)` adds rectangle patch and updates corners/text (#PR_NUMBER)
- [ ] Test `disconnect()` calls `sample_data()`, `scatter_sample()`, `plot_failed_samples()`, disconnects events (#PR_NUMBER)
- [ ] Test `sample_data(n=3,random_state=…)` returns correct sampled indices (#PR_NUMBER)
- [ ] Verify `sample_data(frac=0.1)` raises `NotImplementedError` (#PR_NUMBER)

______________________________________________________________________

### 🏷️ `labels/base.py`

- [ ] Verify `LogAxes`, `AxesLabels`, `RangeLimits` namedtuples have correct defaults (#PR_NUMBER)
- [ ] Verify namedtuples accept custom values (#PR_NUMBER)
- [ ] (Shared with plotting/base) Repeat `Base` tests if context differs (#PR_NUMBER)

______________________________________________________________________

### 🏷️ `labels/special.py`

#### Abstract `ArbitraryLabel(Base)`

- [ ] Verify instantiating `ArbitraryLabel` directly raises `TypeError` (#PR_NUMBER)

#### `ManualLabel(tex,unit,path=None)`

- [ ] Test `set_tex('$X$')` strips dollar signs (#PR_NUMBER)
- [ ] Test `set_unit('km')` maps via `base._inU` (#PR_NUMBER)
- [ ] Verify `__str__` formats `tex` and `unit` correctly (#PR_NUMBER)
- [ ] Verify `.path` property returns default (from `tex`) and custom path (#PR_NUMBER)

#### Built-in labels: `Vsw`, `CarringtonRotation`, `Count`, `Power`, `Probability`

- [ ] Verify `Vsw.tex`, `Vsw.units`, `Vsw.path` (#PR_NUMBER)
- [ ] Test `CarringtonRotation(short_label=False)` toggles `tex` output (#PR_NUMBER)
- [ ] Test `Count(norm='d')` builds `tex` and `path` for density norm (#PR_NUMBER)
- [ ] Test `Count(norm=None)` builds default count label (#PR_NUMBER)
- [ ] Verify `Power` and `Probability(other_label,comparison)` produce correct `tex`,`units`,`path` (#PR_NUMBER)
- [ ] Verify invalid `other_label` or `comparison` in `Probability` raises `AssertionError` (#PR_NUMBER)
