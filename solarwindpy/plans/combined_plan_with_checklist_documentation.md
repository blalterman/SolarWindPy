# Combined Documentation Plan and Task List for SolarWindPy (update-2025 branch)

## Overview and Goals

- **Aim**: Provide clear, searchable, and versioned API documentation and tutorials.
- **Scope**:
  - Auto-generated API reference for all modules and subpackages.
  - User guide with installation, basic usage, and advanced examples.
  - Hosted primarily on Read the Docs and mirrored on GitHub Pages.

## Toolchain and Hosting

- **Documentation generator**: Sphinx
  - Extensions: `sphinx.ext.autodoc`, `sphinx.ext.napoleon`, `sphinx.ext.mathjax`, `sphinx.ext.viewcode`, `sphinx.ext.githubpages`.
  - Theme: `sphinx_rtd_theme`.
- **Environment**:
  - `docs/requirements.txt` lists Sphinx and related extensions.
  - `docs/Makefile` and `docs/make.bat` provide `html`, `clean`, and `spellcheck` targets.
- **Hosting**:
  - Read the Docs for versioned builds.
  - GitHub Pages via a `gh-pages` branch.

## Repository Structure

```
SolarWindPy/
├── docs/
│   ├── source/
│   │   ├── conf.py
│   │   ├── index.rst
│   │   ├── modules.rst
│   │   └── tutorial/
│   │       └── quickstart.rst
│   └── Makefile
├── solarwindpy/
│   └── ... (code packages)
└── documentation plans and checklist
```

## Configuration and Standards

- Update `docs/source/conf.py`:
  - Add Napoleon extension and enable `autosummary_generate = True`.
  - Confirm `html_theme = "sphinx_rtd_theme"`.
  - Ensure `flake8-docstrings` rules D205/D406 are enabled.
- Standardize docstrings to NumPy style across the codebase.
  - Include `Parameters`, `Returns`, `Raises`, and `Examples` sections.
  - Audit modules (`core/`, `fitfunctions/`, `instabilities/`, `plotting/`, etc.) for missing or incomplete docstrings.

## Documentation Content

- Create `docs/source/modules.rst` with a toctree covering core modules.
- Update `docs/source/index.rst` to reference:
  - `installation.rst`
  - `usage.rst`
  - `tutorial.rst`
  - `api_reference.rst`
- Add tutorial pages such as `docs/source/tutorial/quickstart.rst` for installation and basic workflow.
- Generate API reference pages with `sphinx-apidoc` and `autosummary`.

## CI/CD and Validation

- Add CI workflow `.github/workflows/doc-build.yml` to build documentation and fail on warnings.
- Use GitHub Actions to deploy to `gh-pages`.
- Configure Read the Docs with `.readthedocs.yaml`.
- Validate locally by running `sphinx-apidoc` and `make html` without errors or warnings and testing links and snippets.

## Maintenance

- Integrate `doc8` or similar tools for RST linting.
- Add docstring conventions and workflow guidelines to `CONTRIBUTING.md`.
- Include a documentation badge in `README.rst`.
- Schedule periodic reviews of documentation coverage.

## Task Checklist

| Task | Status | Owner | Due Date |
| --- | --- | --- | --- |
| Evaluate existing docs infrastructure under `docs/` (e.g., Sphinx config, extensions) | not started | | |
| Verify that `docs/source/conf.py` loads `autodoc`, `todo`, `mathjax`, `viewcode`, and `githubpages` | not started | | |
| Confirm that the theme `sphinx_rtd_theme` is set appropriately | not started | | |
| Check that the source file suffix is `.rst` and master doc is `index.rst` | not started | | |
| Decide to continue with Sphinx versus evaluate alternatives | not started | | |
| Add `sphinx.ext.napoleon` extension to parse NumPy/Google-style docstrings | not started | | |
| Review benefits of plugins such as `sphinx.ext.viewcode` and `sphinx.ext.githubpages` | not started | | |
| Create `docs/requirements.txt` listing Sphinx and related extensions | not started | | |
| Update `docs/Makefile` and `docs/make.bat` to include `html`, `clean`, and `spellcheck` targets | not started | | |
| Add CI workflow `.github/workflows/doc-build.yml` to install docs requirements and run `make html` | not started | | |
| Audit all public modules and classes for missing docstrings | not started | | |
| Standardize all existing docstrings to NumPy style | not started | | |
| Add missing sections such as `Examples`, `Notes`, and `Attributes` where relevant | not started | | |
| Remove or address any `TODO` placeholders related to documentation | not started | | |
| Update `docs/source/index.rst` to include `installation.rst`, `usage.rst`, `tutorial.rst`, and `api_reference.rst` | not started | | |
| Create `installation.rst` with installation instructions (pip, conda) | not started | | |
| Create `usage.rst` with basic usage examples | not started | | |
| Create `tutorial.rst` with a step-by-step tutorial | not started | | |
| Generate API reference via `sphinx-apidoc` and include in `api_reference.rst` | not started | | |
| Run `sphinx-apidoc` to regenerate module stub files | not started | | |
| Execute `make html` in `docs/` and confirm no errors or warnings | not started | | |
| Test links, code snippets, and formatting in the generated site | not started | | |
| Configure Read the Docs with `.readthedocs.yaml` | not started | | |
| Create `.github/workflows/deploy-docs.yml` to build and push to `gh-pages` | not started | | |
| Add a documentation badge to `README.rst` | not started | | |
| Document docstring conventions and update workflow in `CONTRIBUTING.md` | not started | | |
| Set up linting for documentation (e.g., `flake8-docstrings`, `rst-lint`) in CI | not started | | |
| Schedule periodic review of documentation coverage | not started | | |
