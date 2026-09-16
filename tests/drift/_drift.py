# Spent-When: PERMANENT(the tests/drift/ suite is retired)
# Supersedes: none
"""Shared reporting helper and predicate functions for tests/drift/.

Every assertion in tests/drift/ is an importable predicate function taking
its input as a parameter, with the test a thin caller. This is what lets
tests/drift/test_drift_controls.py demonstrate each predicate firing on
deliberately wrong input, using the same code path a passing run exercises.
"""

from typing import Iterable, Mapping, Optional

import pandas as pd


def drift_message(
    *,
    fact: str,
    pinned: str,
    observed: str,
    location: str,
    remedy: str,
) -> str:
    """Render a drift report with the five mandatory fields.

    Parameters
    ----------
    fact : str
        One-line description of what drifted, e.g.
        "HELIO4CAST published ICMECAT v24".
    pinned : str
        What this repository currently records.
    observed : str
        What was actually observed.
    location : str
        ``path:line (symbol)`` naming where the pin lives.
    remedy : str
        What to do about it.

    Returns
    -------
    str
        A multi-line, human-readable report.
    """
    return (
        f"DRIFT DETECTED: {fact}\n"
        f"  pinned: {pinned}\n"
        f"  observed: {observed}\n"
        f"  pinned at: {location}\n"
        f"  to update: {remedy}"
    )


def assert_head_ok(
    head_info: Mapping[str, object],
    *,
    min_content_length: int,
    content_type_substr: str = "csv",
    fact: str = "pinned URL is reachable",
    location: str = "",
    remedy: str = "",
) -> None:
    """Assert a HEAD response looks like a healthy CSV download.

    Parameters
    ----------
    head_info : Mapping
        Must supply ``status`` (int), ``content_type`` (str or None), and
        ``content_length`` (int or None) -- the shape returned by the
        ``head_status`` fixture in tests/drift/conftest.py.
    min_content_length : int
        Minimum acceptable ``Content-Length``, exclusive.
    content_type_substr : str
        Substring that must appear (case-insensitively) in ``Content-Type``.
    """
    status = head_info.get("status")
    if status != 200:
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned="HTTP 200",
                observed=f"HTTP {status}",
                location=location,
                remedy=remedy or "verify the URL is still valid",
            )
        )

    content_type = (head_info.get("content_type") or "").lower()
    if content_type_substr not in content_type:
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=f"Content-Type containing {content_type_substr!r}",
                observed=f"Content-Type={content_type!r}",
                location=location,
                remedy=remedy or "verify the URL still serves CSV",
            )
        )

    content_length = head_info.get("content_length")
    if content_length is None or content_length <= min_content_length:
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=f"Content-Length > {min_content_length}",
                observed=f"Content-Length={content_length!r}",
                location=location,
                remedy=remedy or "verify the URL still serves the full catalog",
            )
        )


def assert_status(
    head_info: Mapping[str, object],
    expected_status: int,
    *,
    fact: str = "URL status matches expectation",
    location: str = "",
    remedy: str = "",
) -> None:
    """Assert a HEAD response's status code matches ``expected_status``."""
    status = head_info.get("status")
    if status != expected_status:
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=f"HTTP {expected_status}",
                observed=f"HTTP {status}",
                location=location,
                remedy=remedy,
            )
        )


def assert_columns_present(
    df: pd.DataFrame,
    columns: Iterable[str],
    *,
    fact: str = "required columns are present",
    location: str = "",
    remedy: str = "",
) -> None:
    """Assert every column in ``columns`` is present in ``df``."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=f"columns include {sorted(columns)}",
                observed=f"missing {missing}",
                location=location,
                remedy=remedy or "re-verify the schema against the new catalog",
            )
        )


def assert_set_equal(
    expected: Iterable[str],
    observed: Iterable[str],
    *,
    fact: str = "sets match exactly",
    location: str = "",
    remedy: str = "",
) -> None:
    """Assert ``expected`` and ``observed``, as sets, are exactly equal."""
    expected_set = set(expected)
    observed_set = set(observed)
    if expected_set != observed_set:
        missing = expected_set - observed_set
        added = observed_set - expected_set
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=sorted(expected_set),
                observed=(f"missing={sorted(missing)!r} added={sorted(added)!r}"),
                location=location,
                remedy=remedy,
            )
        )


def find_line_index(path, prefix: str) -> Optional[int]:
    """Return the 0-based index of the first line starting with ``prefix``.

    Returns ``None`` if no such line exists.
    """
    with open(path, "r") as f:
        for i, line in enumerate(f):
            if line.startswith(prefix):
                return i
    return None


def assert_skiprows_parses(
    path,
    skiprows: int,
    expected_columns: Iterable[str],
    *,
    fact: str = "skiprows lands on the header line",
    location: str = "",
    remedy: str = "",
) -> None:
    """Assert a parse of ``path`` at ``skiprows`` produces ``expected_columns``.

    Runs ``pd.read_csv(path, header=0, skiprows=skiprows, ...)`` and compares
    the resulting columns.
    """
    df = pd.read_csv(path, header=0, skiprows=skiprows, index_col=0, nrows=1)
    observed = list(df.columns)
    if observed != list(expected_columns):
        raise AssertionError(
            drift_message(
                fact=fact,
                pinned=f"columns == {list(expected_columns)}",
                observed=f"columns == {observed}",
                location=location,
                remedy=remedy or "re-measure the header offset",
            )
        )
