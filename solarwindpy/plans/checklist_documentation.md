# Documentation Task List for SolarWindPy (update-2025 branch)

## 1. Evaluate the current state

- [ ] Evaluate existing docs infrastructure under `docs/` (e.g., Sphinx config, extensions) (#PR_NUMBER)
- [ ] Verify that the config (`docs/source/conf.py`) loads the correct extensions: `autodoc`, `todo`, `mathjax`, `viewcode`, `githubpages` (#PR_NUMBER)
- [ ] Confirm that the theme (`sphinx_rtd_theme`) is set appropriately (#PR_NUMBER)
- [ ] Check that source file suffix is `.rst` and master doc is `index.rst` (#PR_NUMBER)

## 2. Choose a documentation generator

- [ ] Decide to continue with Sphinx versus evaluate alternatives (e.g., MkDocs, Docusaurus) (#PR_NUMBER)
- [ ] Add `sphinx.ext.napoleon` extension to parse NumPy/Google-style docstrings (#PR_NUMBER)
- [ ] Review benefits of plugins such as `sphinx.ext.viewcode` and `sphinx.ext.githubpages` (#PR_NUMBER)

## 3. Set up the documentation environment

- [ ] Create `docs/requirements.txt` listing `sphinx`, `sphinx_rtd_theme`, `sphinx.ext.napoleon`, etc. (#PR_NUMBER)
- [ ] Update `docs/Makefile` and `docs/make.bat` to include targets for `html`, `clean`, `spellcheck` (#PR_NUMBER)
- [ ] Add CI workflow in `.github/workflows/doc-build.yml` to install docs requirements and run `make html`, failing on warnings (#PR_NUMBER)

## 4. Improve docstrings

- [ ] Audit all public modules and classes for missing docstrings (#PR_NUMBER)
- [ ] Standardize all existing docstrings to NumPy style (`Parameters`, `Returns`, `Raises` sections) (#PR_NUMBER)
- [ ] Add missing sections (`Examples`, `Notes`, `Attributes`) where relevant (#PR_NUMBER)
- [ ] Remove or address any `TODO` placeholders in code related to documentation (#PR_NUMBER)

## 5. Organize documentation structure

- [ ] Update `docs/source/index.rst` to include:
  - [ ] `installation.rst` (#PR_NUMBER)
  - [ ] `usage.rst` (#PR_NUMBER)
  - [ ] `tutorial.rst` (#PR_NUMBER)
  - [ ] `api_reference.rst` (#PR_NUMBER)
- [ ] Create `installation.rst` with installation instructions (pip, conda) (#PR_NUMBER)
- [ ] Create `usage.rst` with basic usage examples (#PR_NUMBER)
- [ ] Create `tutorial.rst` with a step-by-step tutorial (#PR_NUMBER)
- [ ] Generate API reference via `sphinx-apidoc` and include in `api_reference.rst` (#PR_NUMBER)

## 6. Build and validate documentation locally

- [ ] Run `sphinx-apidoc` to regenerate module stub files (#PR_NUMBER)
- [ ] Execute `make html` in `docs/` and confirm no errors or warnings (#PR_NUMBER)
- [ ] Test links, code snippets, and formatting in the generated site (#PR_NUMBER)

## 7. Host documentation

- [ ] Configure Read the Docs by adding a `.readthedocs.yaml` with Python version and build commands (#PR_NUMBER)
- [ ] Or set up GitHub Pages deployment:
  - [ ] Create `.github/workflows/deploy-docs.yml` to build and push to `gh-pages` branch (#PR_NUMBER)
- [ ] Add a documentation badge to `README.rst` (#PR_NUMBER)

## 8. Documentation maintenance

- [ ] Document docstring conventions and update workflow in `CONTRIBUTING.md` (#PR_NUMBER)
- [ ] Set up linting for documentation (e.g., `flake8-docstrings`, `rst-lint`) in CI (#PR_NUMBER)
- [ ] Schedule periodic review of documentation coverage (#PR_NUMBER)