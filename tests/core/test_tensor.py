# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Tests for :mod:`solarwindpy.core.tensor`: ``Tensor``."""

from abc import abstractproperty

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from . import _fixtures as fixtures

from solarwindpy.core import tensor
from solarwindpy.core import plasma
from tests.tolerances import exact


#####
# Tensors
#####
class TensorTestBase(fixtures.QuantityTestBase):
    def test_components(self):
        """The par, per and scalar components are the input columns.

        ON FAILURE: the code is wrong.
        """
        t = self.data
        ot = self.object_testing.data
        pdt.assert_series_equal(t.par, ot.par)
        pdt.assert_series_equal(t.per, ot.per)
        pdt.assert_series_equal(t.scalar, ot.scalar)


class ThermalSpeedTestBase(TensorTestBase):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.w.xs(cls().species, axis=1, level="S")
        coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
        scalar = (
            data.pow(2).multiply(coeff, axis=1, level="C").sum(axis=1).pipe(np.sqrt)
        )
        scalar.name = "scalar"
        data = pd.concat([data, scalar], axis=1).sort_index(axis=1)
        w = tensor.Tensor(data)
        cls.object_testing = w
        cls.data = data

    @abstractproperty
    def species(self):
        pass


class TestThermalSpeedAlpha(fixtures.AlphaTest, ThermalSpeedTestBase, fixtures.SWEData):
    pass


class TestThermalSpeedP1(fixtures.P1Test, ThermalSpeedTestBase, fixtures.SWEData):
    pass


class TestThermalSpeedP2(fixtures.P2Test, ThermalSpeedTestBase, fixtures.SWEData):
    pass


class TestTensorMagnitude:
    """Tensor.mag is the thermal-speed scalar sqrt((par^2 + 2 per^2) / 3).

    Thermal speeds combine through the temperatures, T = (T_par + 2 T_per) / 3 with
    T proportional to w^2, so w = sqrt((w_par^2 + 2 w_per^2) / 3) (author decision).
    """

    def test_magnitude_of_hand_tensors(self):
        """magnitude is sqrt(3) for (par=3, per=0), sqrt(6) for (0, 3), w for par=per=w.

        The scalar column is deliberately inconsistent (-1) so a magnitude that reads
        it fails, and par != per in two rows so the trace form (par + 2 per) / 3
        (1, 2) and a swapped weighting (sqrt(3) <-> sqrt(6)) fail.

        ON FAILURE: the code is wrong.
        """
        cols = pd.Index(["par", "per", "scalar"], name="C")
        data = pd.DataFrame(
            [[3.0, 0.0, -1.0], [0.0, 3.0, -1.0], [4.0, 4.0, -1.0]], columns=cols
        )
        expected = [np.sqrt(3.0), np.sqrt(6.0), 4.0]
        assert tensor.Tensor(data).mag.to_numpy() == exact(expected)

    def test_magnitude_of_plasma_thermal_speed(self):
        """A Plasma-built p1 thermal-speed Tensor's magnitude is its own scalar column.

        Plasma stores w_scalar = sqrt((w_par^2 + 2 w_per^2) / 3), the same thermal-speed
        identity, so magnitude must reproduce it row by row on the package's own
        Tensor layout (flat par/per/scalar columns from Ion.w).

        ON FAILURE: the code is wrong.
        """
        p = plasma.Plasma(fixtures.SyntheticData().plasma_data, "p1", "a")
        w = p.p1.w
        assert w.mag.to_numpy() == exact(w.data.loc[:, "scalar"].to_numpy())
        pdt.assert_index_equal(w.mag.index, w.data.index)


class TestTensorSetting:
    """What ``Tensor`` stores and refuses when its data are set."""

    @staticmethod
    def _tensor_data(columns, scale=1.0):
        """Three hourly rows of ``columns``; row i holds ``scale * i``."""
        index = pd.date_range("2020-01-01", periods=3, freq="h")
        values = scale * np.repeat(np.arange(3.0)[:, None], len(columns), axis=1)
        return pd.DataFrame(values, index=index, columns=columns)

    def test_set_data_stores_the_new_data(self):
        """``Tensor.set_data`` replaces the data the tensor reports.

        Chosen input: new data ten times the old.

        ON FAILURE: the code is wrong.
        """
        columns = ["par", "per", "scalar"]
        t = tensor.Tensor(self._tensor_data(columns))
        new = self._tensor_data(columns, scale=10.0)
        t.set_data(new)
        pdt.assert_frame_equal(t.data, new)

    def test_missing_columns_are_named(self):
        """A tensor without a ``scalar`` column raises ValueError naming it.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=r"Missing required columns: \['scalar'\]"):
            tensor.Tensor(self._tensor_data(["par", "per"]))
