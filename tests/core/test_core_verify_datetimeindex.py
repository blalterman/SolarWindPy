"""Index checks every data-backed object runs when its data is set.

``Ion`` stands in for every ``Base`` subclass: setting data logs a warning for
an index that is not a ``DatetimeIndex``, and sorts rows out of time order with
one warning that counts and locates them, as ``Plasma``, ``Spacecraft``,
``Vector`` and ``Tensor`` do.
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
        (pd.to_datetime(["2020-01-02", "2020-01-01"]), set()),
        (pd.to_datetime(["2020-01-01", "2020-01-02"]), set()),
    ],
    ids=["range-index", "decreasing-datetimes", "increasing-datetimes"],
)
def test_ion_warns_about_exactly_the_index_problems_present(caplog, index, expected):
    """A non-datetime index is logged; a clean or merely out-of-order one is not.

    The inputs are chosen so each case has exactly the listed problems. Rows
    out of order are sorted with their own warning, not this module's two.

    ON FAILURE: the code is wrong.
    """
    with caplog.at_level(logging.WARNING):
        Ion(_ion_data(index), "p1")
    found = {msg for msg in (NOT_DATETIME, NOT_INCREASING) if msg in caplog.text}
    assert found == expected


def test_ion_sorts_out_of_order_rows_with_one_warning(caplog):
    """An Ion built directly from rows out of time order sorts them, warning once.

    The rows given in time order 2, 0, 1 come back in time order, with the
    values that came with each time, and the one warning counts them.

    ON FAILURE: the code is wrong.
    """
    times = pd.to_datetime(["2020-01-03", "2020-01-01", "2020-01-02"])
    data = _ion_data(times)
    data[("n", "")] = [3.0, 1.0, 2.0]
    with caplog.at_level(logging.WARNING):
        ion = Ion(data, "p1")
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warnings) == 1
    assert "1 of 3 rows are earlier than the row before them" in warnings[0]
    assert ion.data.index.equals(times.sort_values())
    assert ion.data[("n", "")].tolist() == [1.0, 2.0, 3.0]
