# Spent-When: PERMANENT(the tests/drift/ suite is retired)
# Supersedes: none
"""Mutation controls for the tests/drift/ predicates.

Unmarked, so this runs in the default suite every time. Each test calls a
predicate against deliberately wrong input and asserts it raises. This is
what separates a working drift-detection harness from a decorative one: a
check that has only ever been seen to pass is indistinguishable from one that
cannot fail.
"""

import pandas as pd
import pytest

from ._drift import (
    assert_columns_present,
    assert_head_ok,
    assert_set_equal,
    assert_skiprows_parses,
    assert_status,
)
from .test_drift_readthedocs import assert_python_satisfies_requires


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


def test_assert_python_satisfies_requires_raises_on_incompatible_version():
    with pytest.raises(AssertionError):
        assert_python_satisfies_requires("3.9", ">=3.11,<4")
