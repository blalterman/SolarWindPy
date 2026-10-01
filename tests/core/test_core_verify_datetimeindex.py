"""Index checks every data-backed object runs when its data is set.

``Ion`` stands in for every ``Base`` subclass: setting data logs a warning for
an index that is not a ``DatetimeIndex`` and for one that is not increasing.
"""

import logging

import numpy as np
import pandas as pd
import pytest

from solarwindpy.core.ions import Ion

NOT_DATETIME = "non-DatetimeIndex"
NOT_INCREASING = "not monotonically increasing"


def _ion_data(index):
    """Minimal valid (M, C) ion data, all ones, on ``index``."""
    columns = pd.MultiIndex.from_tuples(
        [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
            ("w", "scalar"),
        ],
        names=["M", "C"],
    )
    return pd.DataFrame(
        np.ones((len(index), len(columns))), index=index, columns=columns
    )


@pytest.mark.parametrize(
    "index, expected",
    [
        (pd.RangeIndex(2), {NOT_DATETIME}),
        (pd.to_datetime(["2020-01-02", "2020-01-01"]), {NOT_INCREASING}),
        (pd.to_datetime(["2020-01-01", "2020-01-02"]), set()),
    ],
    ids=["range-index", "decreasing-datetimes", "increasing-datetimes"],
)
def test_ion_warns_about_exactly_the_index_problems_present(caplog, index, expected):
    """A non-datetime or non-increasing index is logged; a clean one is not.

    The inputs are chosen so each case has exactly the listed problems.

    ON FAILURE: the code is wrong.
    """
    with caplog.at_level(logging.WARNING):
        Ion(_ion_data(index), "p1")
    found = {msg for msg in (NOT_DATETIME, NOT_INCREASING) if msg in caplog.text}
    assert found == expected
