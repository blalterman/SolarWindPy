#!/usr/bin/env python
"""Generate docs/requirements.txt from requirements-dev.txt.

This script extracts documentation-specific dependencies from the main
requirements-dev.txt file to create a minimal requirements file for
documentation-only environments (like Read the Docs).

Examples
--------
Generate docs requirements::

    python scripts/generate_docs_requirements.py

This will create or update docs/requirements.txt with only the packages
needed for documentation builds.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def generate_docs_requirements(
    source_file: str = "requirements-dev.txt",
    target_file: str = "docs/requirements.txt",
) -> None:
    """Extract documentation dependencies from requirements-dev.txt.

    Parameters
    ----------
    source_file : str
        Path to the source requirements file.
    target_file : str
        Path to the target docs requirements file.
    """
    # Documentation-specific packages
    docs_packages = {
        "sphinx",
        "sphinx_rtd_theme",
        "sphinxcontrib-spelling",
        "sphinxcontrib-bibtex",
        "doc8",  # RST linting for documentation workflows
        "numpydoc",  # NumPy-style docstring extension for Sphinx
        "docstring-inheritance",  # Docstring inheritance for class hierarchies
    }

    source_path = Path(source_file)
    target_path = Path(target_file)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file {source_file} not found")

    # Read source requirements
    with open(source_path) as f:
        all_requirements = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]

    # Filter for documentation packages
    docs_requirements = [
        req
        for req in all_requirements
        if any(req.startswith(pkg) for pkg in docs_packages)
    ]

    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Write documentation requirements
    with open(target_path, "w") as f:
        f.write("# Documentation requirements generated from requirements-dev.txt\n")
        f.write(
            "# DO NOT EDIT MANUALLY - regenerate with scripts/generate_docs_requirements.py\n"
        )
        f.write("\n")
        for req in docs_requirements:
            f.write(f"{req}\n")

    print(
        f"Generated {target_file} with {len(docs_requirements)} documentation packages"
    )
    for req in docs_requirements:
        print(f"  - {req}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="requirements-dev.txt",
        help="Source requirements file (default: requirements-dev.txt)",
    )
    parser.add_argument(
        "--target",
        default="docs/requirements.txt",
        help="Target docs requirements file (default: docs/requirements.txt)",
    )
    args = parser.parse_args()

    generate_docs_requirements(args.source, args.target)


if __name__ == "__main__":
    main()
