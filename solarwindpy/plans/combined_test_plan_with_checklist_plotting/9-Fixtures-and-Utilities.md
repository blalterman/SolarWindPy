---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_plotting.md

## 🧠 Context

Combined Test Plan for `solarwindpy.plotting` (branch `update-2025`)

Overview

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

## 🎯 Overview of the Task

- `pytest` fixtures: dummy `Series`, `DataFrame`, `IntervalIndex`, `Axes` from
  `plt.subplots()`.
- `tmp_path` for file I/O.
- Parameterized tests across modes and combinations.

### Justification

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.

## 🔧 Framework & Dependencies

- pytest

## 📂 Affected Files and Paths

None

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

None
