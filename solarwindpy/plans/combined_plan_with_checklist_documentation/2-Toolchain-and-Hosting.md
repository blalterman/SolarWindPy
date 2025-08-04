---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_plan_with_checklist_documentation.md

## 🧠 Context

Combined Documentation Plan and Task List for SolarWindPy (update-2025 branch)

## 🎯 Overview of the Task

- **Documentation generator**: Sphinx
  - Extensions: `sphinx.ext.autodoc`, `sphinx.ext.napoleon`, `sphinx.ext.mathjax`, `sphinx.ext.viewcode`, `sphinx.ext.githubpages`.
  - Theme: `sphinx_rtd_theme`.
- **Environment**:
  - `docs/requirements.txt` lists Sphinx and related extensions.
  - `docs/Makefile` and `docs/make.bat` provide `html`, `clean`, and `spellcheck` targets.
- **Hosting**:
  - Read the Docs for versioned builds.
  - GitHub Pages via a `gh-pages` branch.

## 🔧 Framework & Dependencies

- Sphinx
- Read the Docs
- GitHub Pages

## 📂 Affected Files and Paths

- docs/make.bat
- docs/requirements.txt

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Evaluate existing docs infrastructure under `docs/` (e.g., Sphinx config, extensions)
- [ ] Decide to continue with Sphinx versus evaluate alternatives
- [ ] Review benefits of plugins such as `sphinx.ext.viewcode` and `sphinx.ext.githubpages`
- [ ] Create `docs/requirements.txt` listing Sphinx and related extensions
- [ ] Update `docs/Makefile` and `docs/make.bat` to include `html`, `clean`, and `spellcheck` targets

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
