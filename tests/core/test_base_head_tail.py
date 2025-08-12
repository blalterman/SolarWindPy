import pandas as pd
import pandas.testing as pdt
from unittest import TestCase

from solarwindpy.core import base

pd.set_option("mode.chained_assignment", "raise")


class DummyBase(base.Base):
    def set_data(self, new: pd.DataFrame) -> None:
        super().set_data(new)
        self._data = new


class TestBaseHeadTail(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.DataFrame(
            {"a": range(5)},
            index=pd.date_range("2020-01-01", periods=5, name="epoch"),
        )
        cls.instance = DummyBase(cls.df)

    def test_head(self):
        pdt.assert_frame_equal(self.df.head(), self.instance.head())

    def test_tail(self):
        pdt.assert_frame_equal(self.df.tail(), self.instance.tail())
