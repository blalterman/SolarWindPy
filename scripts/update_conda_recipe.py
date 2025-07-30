#!/usr/bin/env python
"""Update the conda-forge recipe based on ``pyproject.toml``.

This script builds the source distribution and rewrites ``recipe/meta.yaml`` so
that the version, SHA256 digest, and run dependencies match the current
``pyproject.toml`` configuration.

Examples
--------
Run the script after modifying ``pyproject.toml``::

    python scripts/update_conda_recipe.py
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib


def build_sdist(out_dir: Path) -> Path:
    """Build the source distribution.

    Parameters
    ----------
    out_dir : Path
        Directory where the sdist will be placed.

    Returns
    -------
    Path
        Path to the built sdist archive.
    """
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(out_dir)],
        check=True,
    )
    sdists = sorted(out_dir.glob("*.tar.gz"))
    if not sdists:
        raise RuntimeError("sdist not produced")
    return sdists[-1]


def sha256_digest(path: Path) -> str:
    """Return the SHA256 digest of a file.

    Parameters
    ----------
    path : Path
        File to hash.

    Returns
    -------
    str
        Hexadecimal SHA256 digest.
    """

    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_dependencies(pyproject: Path) -> tuple[str, list[str]]:
    """Return the project name and dependencies.

    Parameters
    ----------
    pyproject : Path
        Path to ``pyproject.toml``.

    Returns
    -------
    tuple[str, list[str]]
        The project name and a list of run dependencies.
    """

    data = tomllib.loads(pyproject.read_text())
    project = data["project"]
    name = project["name"]
    deps = [d.strip() for d in project.get("dependencies", [])]
    return name, deps


def render_meta(name: str, version: str, sha256: str, deps: list[str]) -> str:
    """Generate the ``meta.yaml`` file content.

    Parameters
    ----------
    name : str
        Project name.
    version : str
        Version string.
    sha256 : str
        SHA256 digest of the source archive.
    deps : list[str]
        Run dependencies.

    Returns
    -------
    str
        Rendered recipe text.
    """

    dep_lines = "\n".join(f"    - {d}" for d in ["python"] + deps)
    return f"""{{% set name = \"{name}\" %}}
{{% set version = \"{version}\" %}}

package:
  name: {{{{ name|lower }}}}
  version: {{{{ version }}}}

source:
  url: https://pypi.io/packages/source/{{{{ name[0] }}}}/{{{{ name }}}}/{{{{ name }}}}-{{{{ version }}}}.tar.gz
  sha256: {sha256}

build:
  noarch: python
  number: 0
  script: "{{{{ PYTHON }}}} -m pip install . -vv"

requirements:
  host:
    - python
    - pip
  run:
{dep_lines}

test:
  imports:
    - {name}

about:
  home: https://github.com/blalterman/SolarWindPy
  license: BSD-3-Clause
  license_file: LICENSE.rst
  summary: "Python package for solar wind data analysis."

extra:
  recipe-maintainers:
    - blalterman
"""


def main() -> None:
    project = Path("pyproject.toml")
    recipe_dir = Path("recipe")
    recipe_dir.mkdir(exist_ok=True)
    name, deps = parse_dependencies(project)

    sdist = build_sdist(Path("dist"))
    prefix = len(f"{name}-")
    version = sdist.name[prefix:-7]
    digest = sha256_digest(sdist)

    meta = render_meta(name, version, digest, deps)
    (recipe_dir / "meta.yaml").write_text(meta)


if __name__ == "__main__":
    main()
