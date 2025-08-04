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

#### Class `OrbitPlot(ABC)`

- `__init__(orbit, *args)` validates `orbit` type; invalid types raise
  `TypeError`.
- Properties: `_disable_both`, `orbit`, `_orbit_key`, `grouped`.
- `set_path(*args, orbit=…)` appends orbit path.
- `set_orbit(new)` sorts orbits and validates type.
- `make_cut()` adds “Inbound”/“Outbound” (and “Both”) categories.

#### Class `OrbitHist1D(OrbitPlot, Hist1D)`

- `_format_axis(ax)` adds legend.
- `agg(**kwargs)` merges “Both” leg; disabled via `_disable_both`.
- `make_plot(ax, fcn, **kwargs)` calls `tools.subplots` and plots each leg.

#### Class `OrbitHist2D(OrbitPlot, Hist2D)`

- `_format_in_out_axes(inbound, outbound)`, `_prune_lower_yaxis_ticks`, and
  `_format_in_out_both_axes` manage axis formatting.

- `agg(**kwargs)` wraps and normalizes per-orbit.

- `project_1d(axis, project_counts, **kwargs)` returns an `OrbitHist1D`
  instance.

  inbound/outbound/both

______________________________________________________________________

## 🔧 Framework & Dependencies

None

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Verify invalid `orbit` type in `__init__` raises `TypeError`
- [ ] Verify `_disable_both` property is `True` by default
- [ ] Verify `.orbit` property returns the `IntervalIndex`
- [ ] Verify `_orbit_key` returns `"Orbit"`
- [ ] Verify `.grouped` groups by `_gb_axes` + `_orbit_key`
- [ ] Test `set_path(…, orbit=idx)` appends `orbit.path`
- [ ] Test `set_orbit(idx)` sorts and validates type
- [ ] Test `make_cut()` adds “Inbound”/“Outbound” (and “Both”) categories
- [ ] Verify `_format_axis(ax)` adds a legend
- [ ] Test `agg()` merges “Both” leg when `_disable_both=False`
- [ ] Test `make_plot(ax)` plots each orbit leg via `tools.subplots()`
- [ ] Test `_format_in_out_axes()` swaps x-limits and colors spines
- [ ] Test `_prune_lower_yaxis_ticks()` prunes ticks correctly
- [ ] Test `_format_in_out_both_axes()` aligns y-limits across
- [ ] Test `agg()` normalizes per-orbit legs
- [ ] Test `project_1d('x')` returns a valid `OrbitHist1D`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
