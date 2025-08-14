---
name: 'Combined Plan and Checklist: Aggregate Plotting'
about: Unified documentation and checklist for testing aggregate plotting functions.
labels: [sweep, plotting, AggPlot]
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

### 2.1 Class `AggPlot(Base)`

- Properties `edges`, `categoricals`, `intervals`, `cut`, `clim`,
  `agg_axes`, `joint`, `grouped`, `axnorm`.
- Static method `clip_data(data, clip)` handles series vs. DataFrame, `'l'`, `'u'`,
  and numeric clipping. Invalid types raise `TypeError`.
- `set_clim(lower, upper)` sets `_clim`.
- *Justification*: foundation for all histogram and heatmap classes.

## 🎯 Overview of the Task

Implement comprehensive tests for `agg_plot.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/agg_plot.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [x] Verify `.edges` property constructs correct bin-edge arrays
- [x] Verify `.categoricals` property returns categorical bins mapping
- [x] Verify `.intervals` property returns correct `IntervalIndex` objects
- [x] Verify `.cut` property returns the internal `_cut` DataFrame
- [x] Verify `.clim` property returns the internal `_clim` tuple
- [x] Verify `.agg_axes` returns the correct aggregation column
- [x] Verify `.joint` returns a `Series` with a `MultiIndex`
- [x] Verify `.grouped` returns a `GroupBy` on the correct axes
- [x] Verify `.axnorm` returns the internal `_axnorm` value
- [x] Test `clip_data(pd.Series, 'l')`, `'u'`, numeric → correct clipping
- [x] Test `clip_data(pd.DataFrame, …)` with lower/upper modes
- [x] Verify `clip_data()` raises `TypeError` on unsupported input
- [x] Test `set_clim(2, 10)` sets `_clim` to `(2, 10)`

**Commit**: `991a842`  
**Status**: Completed  
**Tests**: 42 passed  
**Time**: 1.5 hours  
**Notes**: Comprehensive test suite with pandas deprecation handling

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
