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

#### Class `SelectFromPlot2D`

- `__init__(plotter, ax, has_colorbar, xdate, ydate, text_kwargs)`.

- Properties: `ax`, `corners`, `date_axes`, `is_multipanel`, `selector`, `text`,
  and more.

- `_init_corners`, `_add_corners`, `_finalize_text`, `_update_text` manage
  corner selection and text updates.

- `disconnect(other, scatter_kwargs, **kwargs)` calls `sample_data`,
  `scatter_sample`, and `plot_failed_samples`.

- `onselect(press, release)` adds patch, updates corners and text.

- `set_ax(ax, has_colorbar)`, `start_text`, `start_selector`, `sample_data(n, random_state)`; `sample_data(frac=…)` raises `NotImplementedError`.

  corners/text
  `plot_failed_samples()`, disconnects events

______________________________________________________________________

## 🔧 Framework & Dependencies

None

## 📂 Affected Files and Paths

None

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Test `__init__(plotter,ax)` initializes selector and text objects
- [ ] Verify `.ax`, `.corners`, `.date_axes`, `.is_multipanel` props
- [ ] Verify `.selector` property exposes selector object
- [ ] Verify `.text` property exposes text annotation
- [ ] Test `_init_corners()` initializes corner coordinates
- [ ] Test `_add_corners()` appends new corner tuples
- [ ] Test `_finalize_text()` formats final selection text
- [ ] Test `_update_text()` formats bounding-box extents
- [ ] Test `onselect(press,release)` adds rectangle patch and updates
- [ ] Test `disconnect()` calls `sample_data()`, `scatter_sample()`,
- [ ] Test `set_ax(ax, has_colorbar)` updates axis and colorbar state
- [ ] Test `start_text()` initializes the annotation text object
- [ ] Test `start_selector()` starts selection widget
- [ ] Test `sample_data(n=3,random_state=…)` returns correct sampled indices
- [ ] Verify `sample_data(frac=0.1)` raises `NotImplementedError`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
