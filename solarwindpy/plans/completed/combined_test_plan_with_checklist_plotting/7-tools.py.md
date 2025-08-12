---
name: 'Combined Plan and Checklist: Plotting Tools'
about: Unified documentation and checklist for helper tools used in plotting.
labels: [sweep, plotting, utils]
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

- `subplots(nrows, ncols, scale_width, scale_height, **kwargs)` scales figure
  size with grid shape.
- `save(fig, spath, add_info, log, pdf, png, **kwargs)` writes `.pdf` and `.png`
  files, adds timestamp text, and supports optional logging.
- `joint_legend(*axes, idx_for_legend, **kwargs)` merges legend entries without
  duplicates and sorts them.
- `multipanel_figure_shared_cbar(...)` (if present) creates grid with shared
  colorbar.

## 🎯 Overview of the Task

Implement comprehensive tests for `tools.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/tools.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Test `subplots(2,2,scale_width=1.5,scale_height=0.5)` returns 2×2 axes with
  correct figsize
- [ ] Test `save(fig, path, pdf=True,png=True)` writes both `.pdf` and `.png`
  files
- [ ] Test PNG version includes timestamp text
- [ ] Test `save(..., log=False)` skips logging calls
- [ ] Test `joint_legend(ax1,ax2)` merges legend entries, no duplicates, sorted
- [ ] (If present) Test `multipanel_figure_shared_cbar(...)` arranges shared
  colorbar correctly

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.

**Status**: ✅ COMPLETED
**Commit**: fe1e348
**Tests Added**: 42 comprehensive test cases (41 passing, 1 skipped)
**Time Invested**: 1 hour
**Test Results**: 41/42 passing (97.6% success rate)
