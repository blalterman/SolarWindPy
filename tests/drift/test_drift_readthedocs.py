# Spent-When: PERMANENT(SolarWindPy stops publishing docs via Read the Docs)
# Supersedes: none
"""Drift assertion: the configured Read the Docs Python satisfies requires-python.

Needs no network -- both files are local -- but lives here per the harness
convention that cross-cutting repository facts (as opposed to module facts)
belong in tests/drift/.

Scope: only the Python version is checked against pyproject.toml. Whether
``ubuntu-22.04`` is a currently-supported Read the Docs build image is not
checked here; RTD's supported-image list exists only upstream and is not a
locally-verifiable fact.
"""

import tomllib

import pytest
import yaml
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from ._drift import drift_message

pytestmark = pytest.mark.drift


def assert_python_satisfies_requires(rtd_python: str, requires_python: str) -> None:
    """Assert the RTD build Python version satisfies requires-python."""
    specifier = SpecifierSet(requires_python)
    version = Version(rtd_python)
    if not specifier.contains(version, prereleases=True):
        raise AssertionError(
            drift_message(
                fact="Read the Docs build Python satisfies pyproject requires-python",
                pinned=f"requires-python = {requires_python!r}",
                observed=f"build.tools.python = {rtd_python!r}",
                location=".readthedocs.yaml: build.tools.python",
                remedy="update build.tools.python or requires-python to agree",
            )
        )


def test_readthedocs_python_satisfies_requires_python(repo_root):
    rtd_config = yaml.safe_load((repo_root / ".readthedocs.yaml").read_text())
    rtd_python = rtd_config["build"]["tools"]["python"]

    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text())
    requires_python = pyproject["project"]["requires-python"]

    assert_python_satisfies_requires(rtd_python, requires_python)
