---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_plan_with_checklist_documentation.md

## 🧠 Context

Combined Documentation Plan and Task List for SolarWindPy (update-2025 branch)

## 🎯 Overview of the Task

- Create `docs/source/modules.rst` with a toctree covering core modules.
- Update `docs/source/index.rst` to reference:
  - `installation.rst`
  - `usage.rst`
  - `tutorial.rst`
  - `api_reference.rst`
- Add tutorial pages such as `docs/source/tutorial/quickstart.rst` for installation and basic workflow.
- Generate API reference pages with `sphinx-apidoc` and `autosummary`.

## 🔧 Framework & Dependencies

- Sphinx

## 📂 Affected Files and Paths

- docs/source/index.rst
- docs/source/modules.rst
- docs/source/tutorial/quickstart.rst

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Update `docs/source/index.rst` to include `installation.rst`, `usage.rst`, `tutorial.rst`, and `api_reference.rst`
- [ ] Create `installation.rst` with installation instructions (pip, conda)
- [ ] Create `usage.rst` with basic usage examples
- [ ] Create `tutorial.rst` with a step-by-step tutorial
- [ ] Generate API reference via `sphinx-apidoc` and include in `api_reference.rst`
- [ ] Run `sphinx-apidoc` to regenerate module stub files

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
