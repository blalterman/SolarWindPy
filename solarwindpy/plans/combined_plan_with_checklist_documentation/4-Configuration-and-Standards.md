---
name: Combined Plan and Checklist Documentation – Configuration and Standards
about: Sets configuration choices and documentation standards for the project.
labels: [sweep, Docs, config]
---

> Extracted from solarwindpy/plans/combined_plan_with_checklist_documentation.md

## 🧠 Context

Sets configuration choices and documentation standards for the project.

## 🎯 Overview of the Task

- Update `docs/source/conf.py`:
  - Add Napoleon extension and enable `autosummary_generate = True`.
  - Confirm `html_theme = "sphinx_rtd_theme"`.
  - Ensure `flake8-docstrings` rules D205/D406 are enabled.
  - Retrieve `version` from package metadata instead of hardcoding it.
- Standardize docstrings to NumPy style across the codebase.
  - Include `Parameters`, `Returns`, `Raises`, and `Examples` sections.
  - Audit modules (`core/`, `fitfunctions/`, `instabilities/`, `plotting/`,
    etc.) for missing or incomplete docstrings.

## 🔧 Framework & Dependencies

- `sphinx.ext.napoleon`
- `flake8-docstrings`
- `sphinx_rtd_theme`

## 📂 Affected Files and Paths

- `docs/source/conf.py`
- `setup.cfg`
- `core/`
- `fitfunctions/`
- `instabilities/`
- `plotting/`

## 📊 Figures, Diagrams, or Artifacts (Optional)

N/A

## ✅ Acceptance Criteria

- [ ] Verify that `docs/source/conf.py` loads `autodoc`, `todo`, `mathjax`,
  `viewcode`, and `githubpages`.
- [ ] Retrieve package `version` dynamically in `docs/source/conf.py`.
- [ ] Confirm that the theme `sphinx_rtd_theme` is set appropriately.
- [ ] Check that the source file suffix is `.rst` and master doc is `index.rst`.
- [ ] Add `sphinx.ext.napoleon` extension to parse NumPy/Google-style
  docstrings.
- [ ] Audit all public modules and classes for missing docstrings.
- [ ] Standardize all existing docstrings to NumPy style.
- [ ] Add missing sections such as `Examples`, `Notes`, and `Attributes` where
  relevant.
- [ ] Remove or address any `TODO` placeholders related to documentation.
- [ ] Ensure `flake8-docstrings` rules D205/D406 are enabled in `setup.cfg`.

## 🧩 Decomposition Instructions (Optional)

N/A

## 🤖 Sweep Agent Instructions (Optional)

N/A

## 💬 Additional Notes

N/A
