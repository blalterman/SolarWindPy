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

### Checklist

- [ ] Evaluate existing docs infrastructure under `docs/` (e.g., Sphinx config, extensions) (#PR_NUMBER)
- [ ] Decide to continue with Sphinx versus evaluate alternatives (#PR_NUMBER)
- [ ] Review benefits of plugins such as `sphinx.ext.viewcode` and `sphinx.ext.githubpages` (#PR_NUMBER)
- [ ] Create `docs/requirements.txt` listing Sphinx and related extensions (#PR_NUMBER)
- [ ] Update `docs/Makefile` and `docs/make.bat` to include `html`, `clean`, and `spellcheck` targets (#PR_NUMBER)

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
└── plans/combined_plan_with_checklist_documentation.md
```

## Configuration and Standards

- Update `docs/source/conf.py`:
  - Add Napoleon extension and enable `autosummary_generate = True`.
  - Confirm `html_theme = "sphinx_rtd_theme"`.
  - Ensure `flake8-docstrings` rules D205/D406 are enabled.
  - Retrieve `version` from package metadata instead of hardcoding it.
- Standardize docstrings to NumPy style across the codebase.
  - Include `Parameters`, `Returns`, `Raises`, and `Examples` sections.
  - Audit modules (`core/`, `fitfunctions/`, `instabilities/`, `plotting/`, etc.) for missing or incomplete docstrings.

### Checklist

- [ ] Verify that `docs/source/conf.py` loads `autodoc`, `todo`, `mathjax`, `viewcode`, and `githubpages` (#PR_NUMBER)
- [ ] Retrieve package `version` dynamically in `docs/source/conf.py` (#PR_NUMBER)
- [ ] Confirm that the theme `sphinx_rtd_theme` is set appropriately (#PR_NUMBER)
- [ ] Check that the source file suffix is `.rst` and master doc is `index.rst` (#PR_NUMBER)
- [ ] Add `sphinx.ext.napoleon` extension to parse NumPy/Google-style docstrings (#PR_NUMBER)
- [ ] Audit all public modules and classes for missing docstrings (#PR_NUMBER)
- [ ] Standardize all existing docstrings to NumPy style (#PR_NUMBER)
- [ ] Add missing sections such as `Examples`, `Notes`, and `Attributes` where relevant (#PR_NUMBER)
- [ ] Remove or address any `TODO` placeholders related to documentation (#PR_NUMBER)
- [ ] Ensure `flake8-docstrings` rules D205/D406 are enabled in `setup.cfg` (#PR_NUMBER)

## Documentation Content

- Create `docs/source/modules.rst` with a toctree covering core modules.
- Update `docs/source/index.rst` to reference:
  - `installation.rst`
  - `usage.rst`
  - `tutorial.rst`
  - `api_reference.rst`
- Add tutorial pages such as `docs/source/tutorial/quickstart.rst` for installation and basic workflow.
- Generate API reference pages with `sphinx-apidoc` and `autosummary`.

### Checklist

- [ ] Update `docs/source/index.rst` to include `installation.rst`, `usage.rst`, `tutorial.rst`, and `api_reference.rst` (#PR_NUMBER)
- [ ] Create `installation.rst` with installation instructions (pip, conda) (#PR_NUMBER)
- [ ] Create `usage.rst` with basic usage examples (#PR_NUMBER)
- [ ] Create `tutorial.rst` with a step-by-step tutorial (#PR_NUMBER)
- [ ] Generate API reference via `sphinx-apidoc` and include in `api_reference.rst` (#PR_NUMBER)
- [ ] Run `sphinx-apidoc` to regenerate module stub files (#PR_NUMBER)

## CI/CD and Validation

- Add CI workflow `.github/workflows/doc-build.yml` to build documentation and fail on warnings.
- Use GitHub Actions to deploy to `gh-pages`.
- Configure Read the Docs with `.readthedocs.yaml`.
- Validate locally by running `sphinx-apidoc` and `make html` without errors or warnings and testing links and snippets.

### Checklist

- [ ] Add CI workflow `.github/workflows/doc-build.yml` to install docs requirements and run `make html` (#PR_NUMBER)
- [ ] Execute `make html` in `docs/` and confirm no errors or warnings (#PR_NUMBER)
- [ ] Test links, code snippets, and formatting in the generated site (#PR_NUMBER)
- [ ] Configure Read the Docs with `.readthedocs.yaml` (#PR_NUMBER)
- [ ] Create `.github/workflows/deploy-docs.yml` to build and push to `gh-pages` (#PR_NUMBER)

## Maintenance

- Integrate `doc8` or similar tools for RST linting.
- Add docstring conventions and workflow guidelines to `CONTRIBUTING.md`.
- Create a pull request template that reminds contributors to update docstrings.
- Include a documentation badge in `README.rst`.
- Schedule periodic reviews of documentation coverage.

### Checklist

- [ ] Add a documentation badge to `README.rst` (#PR_NUMBER)
- [ ] Document docstring conventions and update workflow in `CONTRIBUTING.md` (#PR_NUMBER)
- [ ] Set up linting for documentation (e.g., `flake8-docstrings`, `rst-lint`, `doc8`) in CI (#PR_NUMBER)
- [ ] Schedule periodic review of documentation coverage (#PR_NUMBER)
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md` to prompt docstring updates (#PR_NUMBER)
