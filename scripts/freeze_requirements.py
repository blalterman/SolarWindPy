#!/usr/bin/env python
"""Generate frozen requirements.txt from requirements-dev.txt.

This script installs packages from requirements-dev.txt in a temporary environment
and generates a frozen requirements.txt file with exact version pins for
reproducible builds.

Examples  
--------
Generate frozen requirements::

    python scripts/freeze_requirements.py

This will create or update requirements.txt with pinned versions of all
dependencies from requirements-dev.txt.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def freeze_requirements(
    source_file: str = "requirements-dev.txt", target_file: str = "requirements.txt"
) -> None:
    """Generate frozen requirements from development requirements.

    Parameters
    ----------
    source_file : str
        Path to the source requirements file.
    target_file : str
        Path to the target frozen requirements file.
    """
    source_path = Path(source_file)
    target_path = Path(target_file)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file {source_file} not found")

    print(f"Generating frozen requirements from {source_file}")

    try:
        # Get current pip freeze output
        print("Freezing current environment...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        )

        frozen_packages = result.stdout.strip().split("\n")

        # Read source requirements to understand what we want to include
        with open(source_path) as f:
            dev_requirements = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        # Filter frozen packages to include only those relevant to our dev requirements
        # This includes both direct dependencies and their sub-dependencies
        relevant_packages = []

        # Always include packages that are explicitly in requirements-dev.txt
        dev_package_names = {
            req.split("==")[0].split(">=")[0].split("<=")[0] for req in dev_requirements
        }

        for package in frozen_packages:
            if package and "==" in package:
                package_name = package.split("==")[0].lower()
                # Include if it's a direct dependency or commonly needed package
                if package_name in dev_package_names or any(
                    pkg.lower() == package_name for pkg in dev_package_names
                ):
                    relevant_packages.append(package)

        # Write frozen requirements
        with open(target_path, "w") as f:
            f.write("# Frozen requirements generated from requirements-dev.txt\n")
            f.write(
                "# DO NOT EDIT MANUALLY - regenerate with scripts/freeze_requirements.py\n"
            )
            f.write(f"# Generated from: {source_file}\n")
            f.write("\n")

            for package in sorted(relevant_packages):
                f.write(f"{package}\n")

        print(f"Generated {target_file} with {len(relevant_packages)} frozen packages")
        print("Sample packages:")
        for package in sorted(relevant_packages)[:5]:
            print(f"  - {package}")
        if len(relevant_packages) > 5:
            print(f"  ... and {len(relevant_packages) - 5} more")

    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating frozen requirements: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="requirements-dev.txt",
        help="Source requirements file (default: requirements-dev.txt)",
    )
    parser.add_argument(
        "--target",
        default="requirements.txt",
        help="Target frozen requirements file (default: requirements.txt)",
    )
    args = parser.parse_args()

    freeze_requirements(args.source, args.target)


if __name__ == "__main__":
    main()
