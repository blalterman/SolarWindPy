# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The tolerance rule lives in ``tests/tolerances.py`` and nowhere else.

A test file that writes its own tolerance keyword (``rel``, ``abs``, ``rtol``
or ``atol`` followed by ``=``, in code or in a comment) restates or bends the
rule, so ``test_no_test_file_writes_a_tolerance_keyword`` fails on it. The
remaining tests show each helper accepts a value inside its tolerance and
rejects one shifted past it.
"""

import re
from pathlib import Path

import numpy as np
import pytest

from tests.tolerances import (
    assert_within_error_bars,
    exact,
    noise_free,
    printed,
)

TESTS = Path(__file__).resolve().parent
HELPER = TESTS / "tolerances.py"

# A keyword argument as black writes it: the name, then "=" with no space.
KEYWORD = re.compile(r"\b(?:rel|abs|rtol|atol)=(?!=)")


def tolerance_keywords(text):
    """Return ``(line number, line)`` for each line writing a tolerance keyword."""
    return [
        (n, line.strip())
        for n, line in enumerate(text.splitlines(), start=1)
        if KEYWORD.search(line)
    ]


def test_no_test_file_writes_a_tolerance_keyword():
    """No test file outside ``tests/tolerances.py`` writes a tolerance keyword.

    ON FAILURE: replace the keyword with ``exact``, ``printed``, ``noise_free``
    or ``assert_within_error_bars`` from ``tests/tolerances.py``; if none fits,
    the author decides whether the rule gains a kind.
    """
    found = [
        f"{path.relative_to(TESTS.parent)}:{n}: {line}"
        for path in sorted(TESTS.rglob("*.py"))
        if path != HELPER
        for n, line in tolerance_keywords(path.read_text(encoding="utf-8"))
    ]
    assert not found, "hand-written tolerances:\n" + "\n".join(found)


@pytest.mark.parametrize("name", ["rel", "abs", "rtol", "atol"])
def test_scanner_finds_a_hand_written_tolerance(name):
    """The scanner reports a call and a comment that write a tolerance keyword.

    ON FAILURE: the scanner no longer separates a hand-written tolerance from
    clean code; fix ``KEYWORD``.
    """
    call = "assert x == pytest.approx(y, " + name + "=1e-3)"
    comment = "# " + name + "=1e-6 is far above convergence"
    clean = "assert x == exact(y)\nrelative = 1\nabs_diff = abs(x - y)"
    assert tolerance_keywords(call) == [(1, call)]
    assert tolerance_keywords(comment) == [(1, comment)]
    assert tolerance_keywords(clean) == []


def test_exact_accepts_rounding_and_rejects_a_shift():
    """``exact`` accepts a relative error of 1e-13 and rejects 1e-11.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    assert 1.0 + 1e-13 == exact(1.0)
    assert 1.0 + 1e-11 != exact(1.0)
    assert 1e-34 != exact(2e-34)


def test_exact_scale_sets_the_margin_around_zero():
    """``exact(0, scale=s)`` accepts 1e-13 s and rejects 1e-11 s.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    assert 1e-13 * 400.0 == exact(0.0, scale=400.0)
    assert 1e-11 * 400.0 != exact(0.0, scale=400.0)
    assert 1e-300 != exact(0.0)


def test_exact_matches_nan_only_when_asked():
    """``exact`` matches NaN to NaN only with ``nan_ok=True``.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    values = np.array([1.0, np.nan])
    assert values == exact([1.0, np.nan], nan_ok=True)
    assert values != exact([1.0, np.nan])
    assert np.array([1.0, 2.0]) != exact([1.0, np.nan], nan_ok=True)


def test_printed_allows_half_the_last_digit():
    """``printed(267.6, decimals=1)`` accepts 267.649 and rejects 267.651.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    assert 267.649 == printed(267.6, decimals=1)
    assert 267.551 == printed(267.6, decimals=1)
    assert 267.651 != printed(267.6, decimals=1)
    assert 267.549 != printed(267.6, decimals=1)
    assert 1.2349 == printed(1.23, decimals=2)
    assert 1.2351 != printed(1.23, decimals=2)


def test_noise_free_accepts_convergence_and_rejects_a_shift():
    """``noise_free`` accepts a relative error of 1e-7 and rejects 1e-5.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    assert 2.0 * (1 + 1e-7) == noise_free(2.0)
    assert 2.0 * (1 + 1e-5) != noise_free(2.0)
    assert {"m": 2.0 * (1 + 1e-7)} == noise_free({"m": 2.0})
    assert 1e-7 * 3.0 == noise_free(0.0, scale=3.0)
    assert 1e-5 * 3.0 != noise_free(0.0, scale=3.0)


def test_error_bars_accept_four_and_reject_more():
    """``assert_within_error_bars`` accepts 3.9 error bars and rejects 4.1.

    ON FAILURE: the code is wrong (``tests/tolerances.py``).
    """
    assert_within_error_bars(1.39, 0.1, 1.0)
    assert_within_error_bars({"m": 0.61, "b": 5.0}, {"m": 0.1, "b": 1.0}, {"m": 1.0})
    with pytest.raises(AssertionError, match="outside error bars: 0:"):
        assert_within_error_bars(1.41, 0.1, 1.0)
    with pytest.raises(AssertionError, match="outside error bars: m:"):
        assert_within_error_bars({"m": 0.59}, {"m": 0.1}, {"m": 1.0})
    with pytest.raises(AssertionError, match="outside error bars: 1:"):
        assert_within_error_bars([1.0, 2.5], [0.1, 0.1], [1.0, 2.0])
    with pytest.raises(AssertionError, match="outside error bars"):
        assert_within_error_bars(1.0, np.nan, 1.0)
