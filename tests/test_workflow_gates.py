"""Releases, schedules and checks run only in the public repository.

Copies of this repository carry the same workflow files: a private
development copy, and contributors' forks. A release tag pushed to a copy
must never publish, and a copy must not spend its Actions minutes on the
platform matrix. So every job runs only when the repository is
``blalterman/SolarWindPy``, except ``ci-master.yml``: in the public
repository it checks master, and in a copy it checks every branch.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
PUBLIC = "github.repository == 'blalterman/SolarWindPy'"

if not WORKFLOWS.is_dir():
    pytest.skip(
        "CI workflows under .github/ are absent (e.g. testing from the sdist)",
        allow_module_level=True,
    )


def _jobs():
    """Return ``(workflow file name, job id, job)`` for every job but ci-master's."""
    return [
        (wf.name, job_id, job)
        for wf in sorted(WORKFLOWS.glob("*.yml"))
        if wf.name != "ci-master.yml"
        for job_id, job in yaml.safe_load(wf.read_text())["jobs"].items()
    ]


def test_the_scan_finds_the_publishing_job():
    """The scan below reads jobs: it finds publish.yml's build-and-publish.

    ON FAILURE: the workflows were renamed or restructured; point this
    control at the job that uploads to PyPI.
    """
    assert ("publish.yml", "build-and-publish") in {(w, j) for w, j, _ in _jobs()}


@pytest.mark.parametrize(
    ("workflow", "job_id", "job"),
    _jobs(),
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_each_job_runs_only_in_the_public_repository(workflow, job_id, job):
    """Each job's ``if`` requires the repository to be ``blalterman/SolarWindPy``.

    ON FAILURE: the code is wrong; a copy of the repository would run this
    job, and a release tag pushed to a copy could publish.
    """
    assert PUBLIC in str(job.get("if", "")), f"{workflow}:{job_id} runs in every copy"


def test_ci_master_checks_master_in_public_and_every_branch_in_a_copy():
    """ci-master.yml runs on every pushed branch, and in public only on master.

    ON FAILURE: the code is wrong; a private development copy would push
    commits no CI checks, or public would check branches other than master.
    """
    workflow = yaml.safe_load((WORKFLOWS / "ci-master.yml").read_text())
    # PyYAML reads the bare key ``on`` as the boolean True.
    assert workflow[True]["push"]["branches"] == ["**"]
    (job,) = workflow["jobs"].values()
    assert job["if"] == (
        "github.ref == 'refs/heads/master' || github.repository != 'blalterman/SolarWindPy'"
    )
