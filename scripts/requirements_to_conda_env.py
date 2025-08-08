#!/usr/bin/env python
"""Generate a Conda environment file from a requirements list.

This script reads ``requirements.txt`` or a user-specified file and
produces ``<env_name>.yml`` suitable for ``conda env create``.

Examples
--------
Run with the default requirements file::

    python scripts/requirements_to_conda_env.py
    conda env create -f solarwindpy-dev.yml

Specify a different requirements file and environment name::

    python scripts/requirements_to_conda_env.py custom.txt --name my-env
    conda env create -f my-env.yml
"""

from __future__ import annotations

import argparse
import yaml

from pathlib import Path


def generate_environment(req_path: str, env_name: str) -> None:
    """Create ``<env_name>.yml`` from a requirements file.

    Parameters
    ----------
    req_path : str
        Path to the requirements file.
    env_name : str
        Name of the Conda environment.
    """
    with open(req_path) as req_file:
        packages = [
            line.strip()
            for line in req_file
            if line.strip() and not line.startswith("#")
        ]

    env = {
        "name": env_name,
        "channels": ["conda-forge", "defaults"],
        "dependencies": packages,
    }

    target_name = Path(f"{env_name}.yml")

    if target_name.exists():
        raise ValueError("Target environment name exists. Please pick a new name.")

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
        default="solarwindpy-dev",
        help="Name of the Conda environment.",
    )
    args = parser.parse_args()

    generate_environment(args.requirements, args.name)


if __name__ == "__main__":
    main()
