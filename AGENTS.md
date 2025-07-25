# SolarWindPy AGENTS Guidelines

These instructions apply to the entire repository and describe how automated or human contributors should work with SolarWindPy.

## Development Workflow

1. Create and activate a Python virtual environment.
2. Install development dependencies with:

   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run the test suite using `pytest -q` before committing. You may skip this step only when your changes modify **only** documentation or comments.
4. Format all Python code with [Black](https://github.com/psf/black) and check style with `flake8`. A pre-commit configuration is provided to automate these checks:

   ```bash
   pre-commit install
   ```

5. Use NumPy-style docstrings for all public functions, classes and modules.
6. Ensure new or modified documentation in `docs/` builds successfully with Sphinx (`make html`).

## Commit Messages and Pull Requests

- Write concise commit summaries in the imperative mood (e.g., "Add new parser").
- Describe why the change was made in the body if additional context is helpful.

