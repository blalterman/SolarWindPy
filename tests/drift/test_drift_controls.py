# Spent-When: PERMANENT(the tests/drift/ suite is retired)
# Supersedes: none
"""Mutation controls for the tests/drift/ predicates.

Unmarked, so this runs in the default suite every time. Each test calls a
predicate against deliberately wrong input and asserts it raises. This is
what separates a working drift-detection harness from a decorative one: a
check that has only ever been seen to pass is indistinguishable from one that
cannot fail.

The last control drives ``tests/test_declared_versions.py``, the default-suite
check that superseded the Read the Docs drift predicate, against a repository
whose Read the Docs Python violates ``requires-python``.
"""

import pandas as pd
import pytest

from tests import test_declared_versions

from ._drift import (
    assert_columns_present,
    assert_head_ok,
    assert_set_equal,
    assert_skiprows_parses,
    assert_status,
)


def test_assert_head_ok_raises_on_wrong_status():
    info = {"status": 404, "content_type": "text/csv", "content_length": 500_000}
    with pytest.raises(AssertionError):
        assert_head_ok(info, min_content_length=100_000)


def test_assert_head_ok_raises_on_wrong_content_type():
    info = {"status": 200, "content_type": "text/html", "content_length": 500_000}
    with pytest.raises(AssertionError):
        assert_head_ok(info, min_content_length=100_000)


def test_assert_head_ok_raises_on_short_content_length():
    info = {
        "status": 200,
        "content_type": "text/csv; charset=utf-8",
        "content_length": 10,
    }
    with pytest.raises(AssertionError):
        assert_head_ok(info, min_content_length=100_000)


def test_assert_status_raises_on_mismatch():
    with pytest.raises(AssertionError):
        assert_status({"status": 200}, 404)


def test_assert_columns_present_raises_on_missing_column(tmp_path):
    csv_path = tmp_path / "wrong_columns.csv"
    csv_path.write_text("a,b\n1,2\n")
    df = pd.read_csv(csv_path)
    with pytest.raises(AssertionError):
        assert_columns_present(df, ["a", "b", "c"])


def test_assert_set_equal_raises_on_mismatch():
    with pytest.raises(AssertionError):
        assert_set_equal({"A", "B"}, {"A", "C"})


def test_assert_skiprows_parses_raises_on_wrong_header(tmp_path):
    csv_path = tmp_path / "wrong_header.csv"
    csv_path.write_text("x,y\n1,2\n3,4\n")
    with pytest.raises(AssertionError):
        assert_skiprows_parses(csv_path, 0, ["Min", "Max"])


def _write_declaring_repo(root, rtd_python):
    """Write the files ``test_declared_versions`` reads, floor 3.11 throughout."""
    (root / "pyproject.toml").write_text(
        "[project]\n"
        'requires-python = ">=3.11,<4"\n'
        'classifiers = ["Programming Language :: Python :: 3.11"]\n'
    )
    (root / "tox.ini").write_text("[tox]\nenvlist = py311\n")
    (root / ".readthedocs.yaml").write_text(
        f'version: 2\nbuild:\n  tools:\n    python: "{rtd_python}"\n'
    )


def test_declared_versions_check_raises_on_readthedocs_below_floor(
    tmp_path, monkeypatch
):
    """The declared-versions check fails when only Read the Docs violates the floor.

    The same repository with Read the Docs at the floor passes, so the failure
    is attributable to ``.readthedocs.yaml`` and nothing else.

    ON FAILURE: tests/test_declared_versions.py no longer reads or checks
    .readthedocs.yaml build.tools.python; the retired
    tests/drift/test_drift_readthedocs.py assertion is uncovered.
    """
    check = test_declared_versions.test_declared_versions_satisfy_requires_python
    good, bad = tmp_path / "good", tmp_path / "bad"
    for root, rtd_python in ((good, "3.11"), (bad, "3.9")):
        root.mkdir()
        _write_declaring_repo(root, rtd_python)

    monkeypatch.setattr(test_declared_versions, "REPO_ROOT", good)
    check()

    monkeypatch.setattr(test_declared_versions, "REPO_ROOT", bad)
    with pytest.raises(AssertionError, match=r"\.readthedocs\.yaml.*'3\.9'"):
        check()
