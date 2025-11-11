#!/usr/bin/env python
"""Generate a Conda environment file from a requirements list.

This script reads ``requirements.txt`` or a user-specified file and
produces ``<env_name>.yml`` suitable for ``conda env create``.

The script automatically handles package name differences between pip and conda:
- PyTables: pip uses 'tables', conda uses 'pytables' 
- This translation ensures requirements files can use pip names while
  generating correct conda environment files

Examples
--------
Run with the default requirements file::

    python scripts/requirements_to_conda_env.py
    conda env create -f solarwindpy.yml

Specify a different requirements file and environment name::

    python scripts/requirements_to_conda_env.py custom.txt --name my-env
    conda env create -f my-env.yml
"""

from __future__ import annotations

import argparse
import yaml

from pathlib import Path

# Package name translation map: pip_name -> conda_name
# This handles cases where pip and conda use different package names
PIP_TO_CONDA_NAMES = {
    "tables": "pytables",  # PyTables: pip uses 'tables', conda uses 'pytables'
}


def translate_package_name(pip_name: str) -> str:
    """Translate pip package names to conda package names.

    Parameters
    ----------
    pip_name : str
        Package name as used by pip (may include version specifiers)

    Returns
    -------
    str
        Package name translated for conda, preserving version specifiers

    Notes
    -----
    This function handles the package naming differences between pip and conda.
    For example, PyTables is installed as 'pip install tables' but
    'conda install pytables'.
    """
    # Handle version specifiers (e.g., "package>=1.0.0")
    for operator in [">=", "<=", "==", "!=", ">", "<", "~="]:
        if operator in pip_name:
            package, version = pip_name.split(operator, 1)
            translated_package = PIP_TO_CONDA_NAMES.get(
                package.strip(), package.strip()
            )
            return f"{translated_package}{operator}{version}"

    # No version specifier, direct translation
    return PIP_TO_CONDA_NAMES.get(pip_name.strip(), pip_name.strip())


def generate_environment(req_path: str, env_name: str, overwrite: bool = False) -> None:
    """Create ``<env_name>.yml`` from a requirements file.

    Automatically translates pip package names to conda equivalents where needed.

    Parameters
    ----------
    req_path : str
        Path to the requirements file.
    env_name : str
        Name of the Conda environment.
    overwrite : bool
        Whether to overwrite existing environment files.
    """
    with open(req_path) as req_file:
        pip_packages = [
            line.strip()
            for line in req_file
            if line.strip() and not line.startswith("#")
        ]

    # Translate pip package names to conda equivalents
    conda_packages = [translate_package_name(pkg) for pkg in pip_packages]

    env = {
        "name": env_name,
        "channels": ["conda-forge"],
        "dependencies": conda_packages,
    }

    target_name = Path(f"{env_name}.yml")

    if target_name.exists() and not overwrite:
        print(f"Error: {target_name} already exists. Use --overwrite to replace it.")
        raise FileExistsError(f"{target_name} already exists")

    with open(target_name, "w") as out_file:
        yaml.safe_dump(env, out_file, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "requirements",
        nargs="?",
        default="requirements-dev.txt",
        help="Path to the requirements file.",
    )
    parser.add_argument(
        "--name",
        default="solarwindpy",
        help="Name of the Conda environment.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing environment files.",
    )
    args = parser.parse_args()

    generate_environment(args.requirements, args.name, args.overwrite)


if __name__ == "__main__":
    main()
