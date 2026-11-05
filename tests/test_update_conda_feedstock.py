# Spent-When: PERMANENT(scripts/update_conda_feedstock.py is deleted)
# Supersedes: none
"""``scripts/update_conda_feedstock.py`` reads PyPI reliably and fills its issue.

The release workflow runs the script right after the upload, when PyPI may not
yet list the release or its sdist. The script reads the sdist's SHA256 from
PyPI's JSON API, retrying with a bounded backoff, and never downloads the file.

The network is the boundary: ``requests.get`` is replaced by a scripted
sequence of responses, ``subprocess.run`` by a stub where the test would run
``gh`` or the dependency comparison, and the backoff's sleep by a recorder.
The commit SHA is checked against a real annotated tag in a temporary repo.
"""

import importlib.util
import os
import re
import subprocess
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "update_conda_feedstock", REPO_ROOT / "scripts" / "update_conda_feedstock.py"
)
feedstock = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(feedstock)

VERSION = "0.5.0"
SHA = "ab" * 32
JSON_URL = f"https://pypi.org/pypi/solarwindpy/{VERSION}/json"
SDIST = {
    "packagetype": "sdist",
    "url": f"https://files.pythonhosted.org/packages/xx/solarwindpy-{VERSION}.tar.gz",
    "digests": {"sha256": SHA},
}
WHEEL = {"packagetype": "bdist_wheel", "digests": {"sha256": "cd" * 32}}


class Response:
    """The parts of ``requests.Response`` the script reads."""

    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def released(*urls):
    return Response(200, {"info": {"version": VERSION}, "urls": list(urls)})


@pytest.fixture
def updater():
    """An updater whose sleeps are recorded, not waited."""
    u = feedstock.CondaFeedstockUpdater(fork_owner="someone")
    u.slept = []
    u._sleep = u.slept.append
    return u


@pytest.fixture
def pypi(monkeypatch):
    """Serve ``requests.get`` from a list of responses; record the URLs asked for."""
    calls = []
    responses = []

    def get(url, timeout):
        calls.append(url)
        r = responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr(feedstock.requests, "get", get)
    return responses, calls


def test_a_404_is_retried_with_backoff_until_the_release_is_listed(updater, pypi):
    """The CDN-style 404s right after an upload are waited out, not fatal.

    ON FAILURE: the code is wrong.
    """
    responses, calls = pypi
    responses += [Response(404), Response(404), released(WHEEL, SDIST)]
    assert updater.get_sdist_sha256(VERSION) == SHA
    assert calls == [JSON_URL] * 3
    assert updater.slept == [15, 30]


def test_a_release_without_its_sdist_yet_is_retried(updater, pypi):
    """PyPI listing the wheel before the sdist is not yet ready.

    ON FAILURE: the code is wrong.
    """
    responses, _ = pypi
    responses += [
        released(WHEEL),
        requests.ConnectionError("reset"),
        released(WHEEL, SDIST),
    ]
    assert updater.get_sdist_sha256(VERSION) == SHA
    assert updater.slept == [15, 30]


def test_the_wait_is_bounded(updater, pypi):
    """A release that never appears gives up after ``RELEASE_WAIT`` seconds.

    ON FAILURE: the code is wrong.
    """
    responses, calls = pypi
    responses += [Response(404)] * 50
    assert updater.get_sdist_sha256(VERSION) is None
    assert updater.slept == [15, 30, 60, 120, 120, 120, 120, 15]
    assert sum(updater.slept) == feedstock.RELEASE_WAIT
    assert len(calls) == len(updater.slept) + 1


def test_the_sha256_is_read_from_the_json_without_downloading_the_sdist(updater, pypi):
    """Only the JSON API is requested; the digest is PyPI's, not recomputed.

    ON FAILURE: the code is wrong.
    """
    responses, calls = pypi
    responses += [released(SDIST)]
    assert updater.get_sdist_sha256(VERSION) == SHA
    assert calls == [JSON_URL]


def test_validation_waits_for_the_release_and_checks_its_version(updater, pypi):
    """``validate_pypi_release`` shares the retrying fetch and checks the version.

    ON FAILURE: the code is wrong.
    """
    responses, _ = pypi
    responses += [Response(404), released(SDIST)]
    assert updater.validate_pypi_release(VERSION)
    assert updater.slept == [15]

    responses += [Response(200, {"info": {"version": "0.4.1"}, "urls": [SDIST]})]
    assert not updater.validate_pypi_release(VERSION)


def test_a_prerelease_is_refused_without_asking_pypi(updater, pypi):
    """ON FAILURE: the code is wrong."""
    _, calls = pypi
    assert not updater.validate_pypi_release("0.6.0rc1")
    assert calls == []


def test_the_issue_body_fills_every_placeholder(updater, monkeypatch):
    """The issue names the version, package, hash and commit, and the comparison.

    ON FAILURE: the code is wrong.
    """
    table = "DEPENDENCY COMPARISON\nnumpy>=2 | numpy >=2"
    created = {}

    def run(cmd, **kwargs):
        if cmd[0] == "gh":
            created["body"] = cmd[cmd.index("--body") + 1]
            return subprocess.CompletedProcess(cmd, 0, stdout="https://issue\n")
        assert cmd[-1] == "scripts/compare_feedstock_deps.py"
        return subprocess.CompletedProcess(cmd, 0, stdout=table)

    monkeypatch.setattr(feedstock.subprocess, "run", run)
    url = updater.create_tracking_issue(VERSION, SHA, commit_sha="c0ffee")
    assert url == "https://issue"
    body = created["body"]
    assert re.findall(r"\{[^{}\s]*\}", body) == []
    assert table in body
    for text in (VERSION, SHA, "c0ffee", "solarwindpy-feedstock"):
        assert text in body


def test_the_commit_sha_is_the_tagged_commit_not_the_tag_object(tmp_path, monkeypatch):
    """An annotated tag is its own object; the issue reports the commit it names.

    Under a git hook, ``GIT_DIR``, ``GIT_INDEX_FILE`` and the like name the
    repository being committed to; every git call here, the script's too,
    would act on it, not on ``tmp_path``. They are cleared first.
    ON FAILURE: the code is wrong.
    """
    for name in [n for n in os.environ if n.startswith("GIT_")]:
        monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    git("init", "-q", "-b", "master")
    git("commit", "-q", "--allow-empty", "-m", "release")
    git("tag", "-a", f"v{VERSION}", "-m", "the release")
    head = git("rev-parse", "HEAD")
    assert git("rev-parse", f"v{VERSION}") != head

    u = feedstock.CondaFeedstockUpdater(fork_owner="someone")
    u.project_root = tmp_path
    assert u.verify_git_tag_provenance(VERSION) == (True, head)
