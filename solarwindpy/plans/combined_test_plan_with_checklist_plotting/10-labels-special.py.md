---
name: 'Combined Plan and Checklist: Special Labels'
about: Unified documentation and checklist for special label utilities in plotting.
labels: [sweep, plotting, TeXlabel, LaTeX]
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

### Abstract `ArbitraryLabel(Base)`

- Cannot instantiate; subclass must implement `__str__`.

### `ManualLabel(tex, unit, path=None)`

- `set_tex` and `set_unit` strip `$` and map units via `base._inU`.
- `__str__` and `path` manage default vs. custom paths.

### Prebuilt labels

- `Vsw`, `CarringtonRotation(short_label)`, `Count(norm)`, `Power`,
  `Probability(other_label, comparison)` verify `tex`, `units`, `path`, and
  error on invalid input.

## 🎯 Overview of the Task

Implement comprehensive tests for `labels/special.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/labels/special.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Verify instantiating `ArbitraryLabel` directly raises `TypeError`
- [ ] Test `set_tex('$X$')` strips dollar signs
- [ ] Test `set_unit('km')` maps via `base._inU`
- [ ] Verify `__str__` formats `tex` and `unit` correctly
- [ ] Verify `.path` property returns default (from `tex`) and custom path
- [ ] Verify `Vsw.tex`, `Vsw.units`, `Vsw.path`
- [ ] Test `CarringtonRotation(short_label=False)` toggles `tex` output
- [ ] Test `Count(norm='d')` builds `tex` and `path` for density norm
- [ ] Test `Count(norm=None)` builds default count label
- [ ] Verify `Power` and `Probability(other_label,comparison)` produce correct
  `tex`,`units`,`path`
- [ ] Verify invalid `other_label` or `comparison` in `Probability` raises
  `AssertionError`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.
