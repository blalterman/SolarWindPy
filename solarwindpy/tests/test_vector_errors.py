import pandas as pd
import pytest

from solarwindpy import vector


def test_set_data_missing_column_raises():
    index = pd.date_range("2020-01-01", periods=1)
    valid = pd.DataFrame({"x": [0.0], "y": [1.0], "z": [2.0]}, index=index)
    vec = vector.Vector(valid)

    missing = pd.DataFrame({"x": [0.0], "y": [1.0]}, index=index)
    with pytest.raises(ValueError, match=r"Required columns: .*\nProvided: .*"):
        vec.set_data(missing)
