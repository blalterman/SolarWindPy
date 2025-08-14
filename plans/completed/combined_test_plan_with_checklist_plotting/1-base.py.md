---
name: 'Combined Plan and Checklist: Base Plotting'
about: Unified documentation and checklist for tests covering base plotting utilities.
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

### 1.1 Class `Base` (abstract)

- Instantiation via subclass to ensure `_init_logger`, `_labels`, `_log`, and `path`
  setup.
- `__str__` returns the class name.
- Properties `data`, `clip`, `log`, `labels`, `path` reflect internal state.
- `set_log(x, y)` toggles `log.x` and `log.y`; cover defaults and explicit
  values.
- `set_labels(auto_update_path=True)` updates `labels` and regenerates `path`.
  Passing an unexpected kwarg raises `KeyError`.

## 🎯 Overview of the Task

Implement comprehensive tests for `base.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/base.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [x] Instantiate a minimal subclass of `Base` to verify `_init_logger`,
  `_labels`, `_log` and `path` are initialized
- [x] Verify that `__str__` returns the class name
- [x] Verify that `.data` property returns the internal `_data`
- [x] Verify that `.clip` property returns the internal `_clip`
- [x] Verify that `.log` property returns the internal `_log`
- [x] Verify that `.labels` property returns the internal `_labels`
- [x] Verify that `.path` property returns the internal `_path`
- [x] Test `set_log()` with defaults toggles `log.x` and `log.y` appropriately
- [x] Test `set_log(x=True, y=False)` correctly updates `log` axes
- [x] Test `set_labels()` updates labels and regenerates `path`
- [x] Verify that `set_labels(unexpected=…)` raises `KeyError`

**Commit**: `2f434e8`  
**Status**: Completed  
**Tests**: 51 passed  
**Time**: 0.5 hours

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
