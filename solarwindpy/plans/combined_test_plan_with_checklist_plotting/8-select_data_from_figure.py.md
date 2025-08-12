---
name: 'Combined Plan and Checklist: Select Data From Figure'
about: Unified documentation and checklist for selecting data from interactive figures.
labels: [sweep, plotting]
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

## 🎯 Overview of the Task

Implement comprehensive tests for `select_data_from_figure.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/select_data_from_figure.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [x] Test `__init__(plotter,ax)` initializes selector and text objects
- [x] Verify `.ax`, `.corners`, `.date_axes`, `.is_multipanel` props
- [x] Verify `.selector` property exposes selector object
- [x] Verify `.text` property exposes text annotation
- [x] Test `_init_corners()` initializes corner coordinates
- [x] Test `_add_corners()` appends new corner tuples
- [x] Test `_finalize_text()` formats final selection text
- [x] Test `_update_text()` formats bounding-box extents
- [x] Test `onselect(press,release)` adds rectangle patch and updates
  corners/text
- [x] Test `disconnect()` calls `sample_data()`, `scatter_sample()`,
  `plot_failed_samples()`, disconnects events
- [x] Test `set_ax(ax, has_colorbar)` updates axis and colorbar state
- [x] Test `start_text()` initializes the annotation text object
- [x] Test `start_selector()` starts selection widget
- [x] Test `sample_data(n=3,random_state=…)` returns correct sampled indices
- [x] Verify `sample_data(frac=0.1)` raises `NotImplementedError`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.

**Status**: ✅ COMPLETED
**Commit**: 5b47880
**Tests Added**: 51 comprehensive test cases
**Time Invested**: 1 hour
**Test Results**: 51/51 passing (100% success rate)
