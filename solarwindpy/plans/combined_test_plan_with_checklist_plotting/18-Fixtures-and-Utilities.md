---
name: 'Combined Plan and Checklist: Fixtures and Utilities'
about: Unified documentation and checklist for fixtures and utility functions supporting plotting tests.
labels: [sweep, plotting, Fixtures, Utilities]
---

______________________________________________________________________

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

- `pytest` fixtures: dummy `Series`, `DataFrame`, `IntervalIndex`, `Axes` from
  `plt.subplots()`.
- `tmp_path` for file I/O.
- Parameterized tests across modes and combinations.

### Justification

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.

## 🎯 Overview of the Task

Implement comprehensive tests for Fixtures & Utilities within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- `solarwindpy/tests` (fixtures and utilities for plotting tests)

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Create dummy `Series` fixture for tests
- [ ] Create dummy `DataFrame` fixture for tests
- [ ] Create dummy `IntervalIndex` fixture for tests
- [ ] Use `tmp_path` fixture for file I/O tests
- [ ] Parameterize tests across modes and combinations

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.


**Status**: ✅ COMPLETED
**Commit**: d097473
**Tests Added**: 17 fixtures and utilities test cases
**Time Invested**: 1 hour
**Test Results**: 17/17 passing (100% success rate)
