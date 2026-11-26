"""Public releases are named by date, and the package version comes from those tags.

A release tag is the release date, ``YEAR.MONTH.DAY`` without leading zeros
(``2026.12.3``), so the tag, the PyPI version, ``CITATION.cff`` and the
Zenodo record all read the same. A second release on one day adds a serial
(``2026.12.3.1``), and a release candidate adds ``rcN``. Other tags, such as
semver milestone labels, never set the version. The release tags public
carried before the switch, ``v0.1.0`` through ``v0.7.0``, still set it until
the first date release.

``scripts/bump_version.py`` holds the tag rule; ``pyproject.toml`` holds the
``setuptools_scm`` configuration that reads the tags.
"""

import datetime
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "bump_version", REPO_ROOT / "scripts" / "bump_version.py"
)
bump = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bump)

pytest.importorskip("setuptools_scm")

DEC_3 = datetime.date(2026, 12, 3)


@pytest.mark.parametrize(
    "tag", ["2026.12.3", "2026.1.31", "2026.12.3.1", "2026.12.3rc1", "2026.12.3.1rc2"]
)
def test_a_date_tag_is_a_release_tag(tag):
    """The release date without leading zeros, an optional serial and rc, is a tag.

    ON FAILURE: the code is wrong.
    """
    assert bump.is_release_tag(tag)


@pytest.mark.parametrize(
    "tag",
    ["2026.12.03", "2026.13.1", "2026.2.30", "v0.8.0", "v1.0.0", "1.0.0", "internal/x"],
)
def test_other_tags_are_not_release_tags(tag):
    """A zero-padded, impossible or semver tag is not a release tag.

    ON FAILURE: the code is wrong.
    """
    assert not bump.is_release_tag(tag)


@pytest.mark.parametrize(
    ("existing", "rc", "expected"),
    [
        ([], False, "2026.12.3"),
        (["2026.12.3"], False, "2026.12.3.1"),
        (["2026.12.3", "2026.12.3.1"], False, "2026.12.3.2"),
        ([], True, "2026.12.3rc1"),
        (["2026.12.3rc1"], True, "2026.12.3rc2"),
        (["2026.12.3rc1", "2026.12.3rc2"], False, "2026.12.3"),
        (["2026.12.3"], True, "2026.12.3.1rc1"),
        (["2026.12.2", "v0.7.0"], False, "2026.12.3"),
    ],
)
def test_the_next_tag_counts_the_days_releases(existing, rc, expected):
    """The next tag is the date, then a serial per further release that day.

    Chosen inputs: the tags already made, on 2026-12-03.

    ON FAILURE: the code is wrong.
    """
    assert bump.next_tag(DEC_3, existing, rc=rc) == expected


def _scm_version(tmp_path, monkeypatch, tags_by_commit):
    """Return setuptools_scm's version of a repo whose commits carry the given tags."""
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def git(*args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    git("init", "-q", "-b", "master")
    for tags in tags_by_commit:
        git("commit", "-q", "--allow-empty", "-m", "c")
        for tag in tags:
            git("tag", "-a", tag, "-m", tag)
    # setuptools_scm's own command line reads pyproject.toml as a build does.
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "setuptools_scm",
            "-r",
            str(tmp_path),
            "-c",
            str(REPO_ROOT / "pyproject.toml"),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_a_date_tag_sets_the_version(tmp_path, monkeypatch):
    """A commit tagged ``2026.12.3`` builds as version ``2026.12.3``.

    ON FAILURE: the code is wrong; pyproject.toml's setuptools_scm settings do
    not read date tags.
    """
    assert _scm_version(tmp_path, monkeypatch, [["2026.12.3"]]) == "2026.12.3"


def test_a_semver_label_does_not_set_the_version(tmp_path, monkeypatch):
    """A semver label on a later commit leaves the version to the date tag.

    ON FAILURE: the code is wrong; a private milestone label would set the
    version a build reports.
    """
    version = _scm_version(tmp_path, monkeypatch, [["2026.12.3"], ["v1.0.0"]])
    assert Version(version) > Version("2026.12.3")
    assert Version(version).release[0] == 2026


def test_the_last_semver_release_sets_the_version_until_a_date_release(
    tmp_path, monkeypatch
):
    """With only ``v0.7.0`` behind it, a commit builds as a 0.7 development version.

    ON FAILURE: the code is wrong; builds before the first date release lose
    their place after 0.7.0.
    """
    version = Version(_scm_version(tmp_path, monkeypatch, [["v0.7.0"], []]))
    assert version > Version("0.7.0")
    assert version.release[:2] == (0, 7)


def test_publish_runs_on_date_tags_and_checks_them_with_the_tag_rule():
    """publish.yml runs on date tags only, and checks each with bump_version.py.

    ON FAILURE: the code is wrong; a semver label pushed to public would start
    a release, or the workflow and the tag rule disagree.
    """
    text = (REPO_ROOT / ".github" / "workflows" / "publish.yml").read_text()
    # PyYAML reads the bare key ``on`` as the boolean True.
    assert yaml.safe_load(text)[True]["push"]["tags"] == ["20*"]
    assert "refs/tags/v" not in text
    assert "scripts/bump_version.py --check" in text
