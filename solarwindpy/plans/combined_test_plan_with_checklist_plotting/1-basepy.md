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

#### 1.1 Class `Base` (abstract)

- Instantiation via subclass to ensure `_init_logger`, `_labels`, `_log`, and `path`
  setup.

- `__str__` returns the class name.

- Properties `data`, `clip`, `log`, `labels`, `path` reflect internal state.

- `set_log(x, y)` toggles `log.x` and `log.y`; cover defaults and explicit
  values.

- `set_labels(auto_update_path=True)` updates `labels` and regenerates `path`.
  Passing an unexpected kwarg raises `KeyError`.

  `_labels`, `_log` and `path` are initialized

______________________________________________________________________

## 🔧 Framework & Dependencies

None

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Instantiate a minimal subclass of `Base` to verify `_init_logger`,
- [ ] Verify that `__str__` returns the class name
- [ ] Verify that `.data` property returns the internal `_data`
- [ ] Verify that `.clip` property returns the internal `_clip`
- [ ] Verify that `.log` property returns the internal `_log`
- [ ] Verify that `.labels` property returns the internal `_labels`
- [ ] Verify that `.path` property returns the internal `_path`
- [ ] Test `set_log()` with defaults toggles `log.x` and `log.y` appropriately
- [ ] Test `set_log(x=True, y=False)` correctly updates `log` axes
- [ ] Test `set_labels()` updates labels and regenerates `path`
- [ ] Verify that `set_labels(unexpected=…)` raises `KeyError`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
