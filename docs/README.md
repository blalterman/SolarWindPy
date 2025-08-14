# SolarWindPy Documentation

This directory contains the Sphinx documentation for SolarWindPy.

## Building Documentation

### Prerequisites
```bash
pip install -r requirements.txt
```

### Local Build
```bash
make html
```

This will:
1. Generate API documentation from source code using `sphinx-apidoc`
2. Add `:no-index:` directives to module files to prevent duplicate warnings
3. Build the HTML documentation

The built documentation will be available in `build/html/index.html`.

### Clean Build
```bash
make clean
make html
```

## Auto-Generated Files

The `source/api/` directory contains auto-generated RST files created by `sphinx-apidoc`. These files are:
- **Not tracked in git** (they are gitignored)
- **Regenerated on every build** from the source code
- **Post-processed** by `add_no_index.py` to prevent duplicate object warnings

If you need to view documentation locally, run `make html` to generate these files.

## Deployment

Documentation is automatically built and deployed to GitHub Pages via the `.github/workflows/deploy-docs.yml` workflow when changes are pushed to the `master` branch.