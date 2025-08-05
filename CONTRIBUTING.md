# Contributing

Thank you for considering contributing to SolarWindPy.

## Development workflow

1. Create a virtual environment and install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

2. Format code with `black` and lint with `flake8` (includes `flake8-docstrings`).
3. Ensure all docstrings follow the NumPy style guide.
4. Lint documentation with `doc8` and build docs:

   ```bash
   doc8 README.rst docs
   cd docs && make html
   ```

5. Run the test suite:

   ```bash
   pytest -q
   ```

## Documentation reviews

Documentation should be reviewed quarterly. Open an issue using the
"Documentation Review" template under `.github/ISSUE_TEMPLATE` to track the
review.
