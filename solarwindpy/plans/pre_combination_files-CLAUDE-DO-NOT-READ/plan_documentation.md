# Documentation Plan for SolarWindPy (update-2025 branch)

This document outlines the steps needed to generate and maintain a comprehensive documentation website for the `update-2025` branch of the SolarWindPy package.

---

## 1. Overview and Goals

- **Aim**: Provide clear, searchable, and versioned API docs and tutorials for SolarWindPy.
- **Scope**:
  - Auto-generated API reference for all modules and subpackages.
  - User guide for installation, basic usage, and advanced examples.
  - Hosted via Read the Docs (RTD) and mirrored on GitHub Pages.

## 2. Toolchain Selection

- **Documentation generator**: Sphinx
  - Leverage `sphinx.ext.autodoc` for API docs.
  - Use `sphinx.ext.napoleon` to parse NumPy- and Google-style docstrings.
  - Enable `sphinx_rtd_theme` for a polished, responsive layout.
- **Hosting**:
  - Primary: Read the Docs (free CI/CD, versioned builds).
  - Secondary: GitHub Pages via `gh-pages` branch.

## 3. Repository Structure

```
SolarWindPy/
├── docs/
│   ├── source/
│   │   ├── conf.py
│   │   ├── index.rst
│   │   ├── modules.rst
│   │   └── tutorial/   ← new folder for examples
│   │       └── quickstart.rst
│   └── Makefile
├── solarwindpy/
│   └── ... (code packages)
└── DOCUMENTATION_PLAN.md  ← this file
```

## 4. Configuration Changes

1. ``:

   - Add Napoleon:
     ```python
     extensions = [
       "sphinx.ext.autodoc",
       "sphinx.ext.napoleon",
       "sphinx.ext.mathjax",
       "sphinx.ext.viewcode",
       "sphinx.ext.githubpages",
     ]
     ```
   - Set `autosummary_generate = True` and enable `sphinx.ext.autosummary`.
   - Confirm `html_theme = "sphinx_rtd_theme"`.

2. ``:

   - Ensure that docstring conventions (`flake8-docstrings`) include D205/D406 for Napoleon compatibility.

## 5. Docstring Standardization

- **Adopt NumPy style**:
  - Sections: `Parameters`, `Returns`, `Raises`, `Examples`.
  - Use double backticks for code and references (e.g. ``:class:`Vector` ``).
- **Audit codebase**:
  - Search for missing or incomplete docstrings.
  - Standardize across modules: `core/`, `fitfunctions/`, `instabilities/`, `plotting/`, etc.
- **Add examples** under `Examples` section where helpful.

## 6. Generating API Reference

1. Create `docs/source/modules.rst` with:
   ```rst
   .. toctree::
      :maxdepth: 4
      :caption: API Reference

      solarwindpy.core
      solarwindpy.fitfunctions
      solarwindpy.instabilities
      solarwindpy.plotting
      solarwindpy.tools
   ```
2. Enable `autosummary` to pre-generate summary pages for each module.

## 7. Writing Tutorials and Guides

- Add a `docs/source/tutorial/quickstart.rst`:
  - Installation instructions.
  - Basic workflow: loading data, computing a vector, plotting results.
- Regularly update with new use cases (e.g., fitting functions, instability thresholds).

## 8. CI/CD Integration

- **Read the Docs**:
  - Connect GitHub repo, enable builds for each branch (including `update-2025`).
- **GitHub Actions**:
  - Add workflow to build docs on push to `update-2025` and deploy to `gh-pages`.
  - Use `actions/setup-python` and `sphinx-build` to verify documentation builds without errors.

## 9. Maintenance and Updates

- **Pull request template**:
  - Remind contributors to update docstrings when adding or changing public APIs.
- **Documentation linting**:
  - Integrate `doc8` to enforce RST style.
  - Run `make doc8` as part of CI.
- **Versioning**:
  - Read the Docs will auto-version; ensure `version` variable in `conf.py` is set dynamically from package metadata.

## 10. Next Steps

1. Commit this `DOCUMENTATION_PLAN.md` to the repo root.
2. Update `conf.py` and `setup.cfg` as outlined.
3. Audit and refactor docstrings for consistency.
4. Create initial tutorial pages under `docs/source/tutorial/`.
5. Configure Read the Docs and GitHub Actions.
6. Review and merge via pull request.

---

*End of documentation plan.*

