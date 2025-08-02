import pandas as pd
import pandas.testing as pdt

from solarwindpy.core.base import Base


def test_mi_tuples_returns_index_with_names():
    tuples = (("v", "x", "p"), ("b", "y", ""))
    result = Base.mi_tuples(tuples)
    expected = pd.MultiIndex.from_tuples(tuples, names=["M", "C", "S"])
    pdt.assert_index_equal(result, expected)
