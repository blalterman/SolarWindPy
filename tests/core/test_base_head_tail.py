"""``head`` and ``tail`` of a data-backed object return its first and last rows."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from solarwindpy.core.ions import Ion

# Eight rows, more than the five ``head``/``tail`` return, each row distinct
# (row i holds i), so first and last five differ and a swap is visible.
_COLUMNS = pd.MultiIndex.from_tuples(
    [("n", ""), ("v", "x"), ("v", "y"), ("v", "z"), ("w", "par"), ("w", "per")],
    names=["M", "C"],
)
_DATA = pd.DataFrame(
    np.repeat(np.arange(1.0, 9.0)[:, None], len(_COLUMNS), axis=1),
    index=pd.date_range("2020-01-01", periods=8, name="epoch"),
    columns=_COLUMNS,
)


@pytest.mark.parametrize("method", ["head", "tail"])
def test_head_and_tail_are_the_first_and_last_five_rows(method):
    """``Ion(...).head()`` is rows 1-5 and ``tail()`` rows 4-8 of its data.

    The expected frames are pandas' own ``head``/``tail`` of the input.

    ON FAILURE: the code is wrong.
    """
    ion = Ion(_DATA, "p1")
    expected = getattr(_DATA, method)()
    pdt.assert_frame_equal(getattr(ion, method)(), expected)
