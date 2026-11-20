# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""``solarwindpy.yml`` is generated from ``pyproject.toml``.

``pyproject.toml`` is the one list of dependencies. ``pyproject2conda project``
writes the conda environment file from it, using the settings in
``[tool.pyproject2conda]``; this test regenerates it and compares.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _environment(text):
    """The name, channels and set of dependencies of an environment file."""
    env = yaml.safe_load(text)
    return env["name"], env["channels"], set(env["dependencies"])


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="solarwindpy.yml is still the hand-kept list; remove this marker when "
    "the generated file is committed",
)
def test_solarwindpy_yml_is_generated_from_pyproject():
    """The committed ``solarwindpy.yml`` holds what ``pyproject.toml`` generates.

    Compared as name, channels and the set of dependencies, so the generator's
    header comment and line endings do not matter.

    ON FAILURE: the code is wrong; run ``pyproject2conda project -w force`` in
    the solarwindpy env and commit ``solarwindpy.yml`` with the pyproject.toml
    change.
    """
    pytest.importorskip(
        "pyproject2conda", reason="pyproject2conda is in the dev extra only"
    )
    generated = subprocess.run(
        [sys.executable, "-m", "pyproject2conda", "project", "--dry"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    committed = (ROOT / "solarwindpy.yml").read_text(encoding="utf-8")
    assert _environment(committed) == _environment(generated)
