---
name: 'Combined Plan and Checklist: Base Labels'
about: Unified documentation and checklist for base label utilities in plotting.
labels: [sweep]
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

- Namedtuples: `LogAxes`, `AxesLabels`, `RangeLimits` with defaults and custom
  values.
- Class `Base`: shared logic with `plotting/base`.

## 🎯 Overview of the Task

Implement comprehensive tests for `labels/base.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/labels/base.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Verify `LogAxes`, `AxesLabels`, `RangeLimits` namedtuples have correct
  defaults
- [ ] (Shared with plotting/base) Repeat `Base` tests if context differs

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
