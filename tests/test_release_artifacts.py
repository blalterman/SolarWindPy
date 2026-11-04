# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The built wheel and sdist ship only what each is meant to ship.

Builds both artifacts once per module with ``python -m build --no-isolation``,
so the test needs no network, and checks them with
``scripts/check_release_artifacts.py``, the same check the release workflows
run. The build takes a few seconds, so this runs in the default suite.

It is skipped when ``build`` or the build backend's requirements are not
installed, and when the repository root is not a git checkout (an extracted
sdist), since setuptools_scm needs git to version the build.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

pytest.importorskip("build", reason="python -m build needs the 'build' package")
pytest.importorskip("setuptools_scm", reason="--no-isolation needs setuptools_scm")
pytest.importorskip("wheel", reason="--no-isolation needs wheel")
if not (REPO_ROOT / ".git").exists():
    pytest.skip("building needs a git checkout", allow_module_level=True)

_spec = importlib.util.spec_from_file_location(
    "check_release_artifacts", REPO_ROOT / "scripts" / "check_release_artifacts.py"
)
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


@pytest.fixture(scope="module")
def artifacts(tmp_path_factory):
    """Return ``(wheel, sdist)`` built from the working tree into a fresh directory."""
    out = tmp_path_factory.mktemp("dist")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(out),
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"python -m build failed:\n{result.stdout}\n{result.stderr}")
    (wheel,) = out.glob("*.whl")
    (sdist,) = out.glob("*.tar.gz")
    return wheel, sdist


def test_wheel_holds_only_the_package(artifacts):
    """The wheel's top level is ``solarwindpy/`` and its ``.dist-info``, nothing else."""
    wheel, _ = artifacts
    assert check.wheel_stray_entries(wheel) == []


def test_wheel_carries_no_spent_when(artifacts):
    """No file a user installs carries a purge-system header."""
    wheel, _ = artifacts
    assert check.wheel_spent_when_files(wheel) == []


def test_wheel_installs_every_package_file(artifacts):
    """Each ``solarwindpy/`` file in the sdist, data files included, is in the wheel."""
    wheel, sdist = artifacts
    members = check.sdist_members(sdist)
    assert "solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv" in members
    assert check.wheel_missing_package_files(wheel, members) == []


def test_a_package_file_missing_from_the_wheel_is_reported(artifacts):
    """Negative control: a package file absent from the wheel is named."""
    wheel, sdist = artifacts
    members = check.sdist_members(sdist) + ["solarwindpy/not_shipped.csv"]
    assert check.wheel_missing_package_files(wheel, members) == [
        "solarwindpy/not_shipped.csv"
    ]


def test_sdist_keeps_tests_and_docs_source(artifacts):
    """Packagers rebuilding from the sdist get the tests and the docs source."""
    _, sdist = artifacts
    assert check.sdist_missing(check.sdist_members(sdist)) == []


def test_sdist_prunes_development_material(artifacts):
    """The sdist holds none of .claude/, .github/, docs/dispatches/, tmp/, spike/."""
    _, sdist = artifacts
    assert check.sdist_pruned_present(check.sdist_members(sdist)) == []
