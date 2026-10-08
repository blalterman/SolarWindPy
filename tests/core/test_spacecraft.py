#!/usr/bin/env python
"""Tests for spacecraft handling."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from scipy import constants
from unittest import TestCase
from abc import ABC, abstractclassmethod, abstractproperty

from . import test_base as base

import solarwindpy as swp
from solarwindpy.core import vector
from solarwindpy.core import spacecraft
from tests.tolerances import exact

pd.set_option("mode.chained_assignment", "raise")


class SpacecraftTestBase(ABC):
    @classmethod
    def setUpClass(cls):
        data = base.SyntheticData()
        cls.data = data.spacecraft_data
        cls.set_object_testing()

    @abstractclassmethod
    def set_object_testing(cls):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def frame(self):
        pass

    def test_position(self):
        cols = pd.Index(("x", "y", "z"), name="C")
        ot = self.object_testing
        pdt.assert_index_equal(cols, ot.position.data.columns)
        self.assertIsInstance(ot.position, vector.Vector)
        self.assertEqual(ot.position, ot.r)
        self.assertEqual(ot.position, ot.pos)
        return ot

    def test_velocity(self):
        cols = pd.Index(("x", "y", "z"), name="C")
        ot = self.object_testing
        pdt.assert_index_equal(cols, ot.velocity.data.columns)
        self.assertIsInstance(ot.velocity, vector.Vector)
        self.assertEqual(ot.velocity, ot.v)
        return ot

    def test_data(self):
        ot = self.object_testing
        pdt.assert_frame_equal(self.data, ot.data)

    def test_name(self):
        ot = self.object_testing
        self.assertEqual(self.name, ot.name)

    def test_frame(self):
        ot = self.object_testing
        self.assertEqual(self.frame, ot.frame)

    def test_distance2sun(self):
        ot = self.object_testing

        frame = self.frame
        pos = self.data.loc[:, "pos"]
        if frame == "GSE":
            # Origin is Earth, so we need to transform x-component to sun-centered.
            assert pos.columns.equals(pd.Index(("x", "y", "z"), name="C"))
            au = constants.au  # 1 AU in meters
            re = 6378.1e3  # Earth radius in meters
            sign_x = re * pd.Series(
                [-1.0, 1.0, 1.0], index=pd.Index(("x", "y", "z"), name="C")
            )
            change_origin = pd.Series(
                [au, 0.0, 0.0], index=pd.Index(("x", "y", "z"), name="C")
            )
            pos = pos.multiply(sign_x, axis=1).add(change_origin, axis=1)

        elif frame == "HCI":
            # Origin is sun and propagationd distance is just magnitude
            assert pos.columns.equals(pd.Index(("x", "y", "z"), name="C"))
            rs = 695.7e6  # IAU 2015 nominal solar radius [m], doi:10.3847/0004-6256/152/2/41
            pos = pos.multiply(rs)

        else:
            raise NotImplementedError("No test written for frame {}".format(frame))

        dist = pos.pow(2).sum(axis=1).pipe(np.sqrt)
        dist.name = "distance2sun"
        pdt.assert_series_equal(dist, ot.distance2sun)


class TestWind(SpacecraftTestBase, TestCase):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.xs("gse", axis=1, level="M")
        data = pd.concat({"pos": data}, axis=1, names=["M"], sort=True).sort_index(
            axis=1
        )
        cls.data = data
        sc = spacecraft.Spacecraft(data, "wind", "gse")

        cls.object_testing = sc

    @property
    def frame(self):
        return "GSE"

    @property
    def name(self):
        return "WIND"

    def test_position(self):
        super(TestWind, self).test_position()
        pos = self.data.xs("pos", axis=1, level="M")
        ot = self.object_testing
        pdt.assert_frame_equal(pos, ot.position.data)

    def test_velocity(self):
        with self.assertRaises(KeyError):
            self.object_testing.velocity
        with self.assertRaises(KeyError):
            self.object_testing.v

    def test_carrington(self):
        with self.assertRaises(KeyError):
            self.object_testing.carrington


class TestPSP(SpacecraftTestBase, TestCase):
    @classmethod
    def set_object_testing(cls):
        p = cls.data.xs("pos_HCI", axis=1, level="M")
        v = cls.data.xs("v_HCI", axis=1, level="M")
        c = cls.data.xs("Carr", axis=1, level="M")

        data = pd.concat(
            {"v": v, "pos": p, "carr": c}, axis=1, names=["M"], sort=True
        ).sort_index(axis=1)
        sc = spacecraft.Spacecraft(data, "psp", "hci")
        cls.object_testing = sc
        cls.data = data

    @property
    def frame(self):
        return "HCI"

    @property
    def name(self):
        return "PSP"

    def test_position(self):
        super(TestPSP, self).test_position()

        pos = self.data.xs("pos", axis=1, level="M")
        ot = self.object_testing
        pdt.assert_frame_equal(pos, ot.position.data)

    def test_velocity(self):
        super(TestPSP, self).test_velocity()

        v = self.data.xs("v", axis=1, level="M")
        ot = self.object_testing
        pdt.assert_frame_equal(v, ot.velocity.data)

    def test_carrington(self):
        cols = pd.Index(("lat", "lon"), name="C")
        carr = self.data.xs("carr", axis=1, level="M")

        ot = self.object_testing
        self.assertIsInstance(ot.carrington, pd.DataFrame)
        pdt.assert_index_equal(cols, ot.carrington.columns)
        pdt.assert_frame_equal(carr, ot.carrington)


def _warnings(caplog):
    return [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]


def test_out_of_order_spacecraft_data_warn_once_then_sort(caplog):
    r"""Out-of-order spacecraft data warn once when built, are sorted, and warn no more.

    The example trajectory's rows are passed in order 2, 0, 1. Per the author, a
    standalone `Spacecraft` follows `Plasma`'s time rule: one warning reporting
    1 of 3 rows out of order, then the rows sorted, so the x position reads the
    example's [-42, -22, -34] in time order. Accessors built from the sorted
    data log nothing, however often they are called.

    ON FAILURE: the code is wrong.
    """
    ref = swp.examples.load_plasma().spacecraft
    with caplog.at_level("WARNING", logger="solarwindpy"):
        sc = spacecraft.Spacecraft(ref.data.iloc[[2, 0, 1]], "PSP", "HCI")
    (message,) = _warnings(caplog)
    assert "1 of 3 rows are earlier than the row before them" in message

    caplog.clear()
    with caplog.at_level("WARNING", logger="solarwindpy"):
        for _ in range(2):
            sc.position, sc.pos, sc.r, sc.velocity, sc.v, sc.distance2sun
    assert _warnings(caplog) == []

    assert sc.data.index.equals(ref.data.index)
    assert sc.position.data.loc[:, "x"].to_numpy() == exact([-42.0, -22.0, -34.0])


@pytest.mark.parametrize(
    "build",
    [
        lambda sc, values: spacecraft.Spacecraft(values, "PSP", "HCI"),
        lambda sc, values: sc.set_data(values),
    ],
    ids=["constructor", "set_data"],
)
def test_data_that_is_not_a_dataframe_raise_type_error_naming_the_type(build):
    r"""Spacecraft data given as an array raise TypeError naming both types.

    The example spacecraft's values as a numpy array are refused, at
    construction and by `set_data` called directly alike, with a message
    naming the expected DataFrame and the ndarray received, as `Plasma`
    refuses its data.

    ON FAILURE: the code is wrong.
    """
    sc = swp.examples.load_plasma().spacecraft
    with pytest.raises(
        TypeError, match=r"^Spacecraft data must be a pandas DataFrame, not ndarray$"
    ):
        build(sc, sc.data.to_numpy())


def test_spacecraft_refuses_missing_timestamps():
    r"""A spacecraft whose time index holds NaT raises ValueError naming the count.

    ON FAILURE: the code is wrong.
    """
    data = swp.examples.load_plasma().spacecraft.data
    times = pd.DatetimeIndex([data.index[0], pd.NaT, data.index[2]])
    with pytest.raises(
        ValueError, match=r"1 of 3 timestamps missing \(NaT\); drop those rows first"
    ):
        spacecraft.Spacecraft(data.set_axis(times, axis=0), "PSP", "HCI")
