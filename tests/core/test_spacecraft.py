#!/usr/bin/env python
"""Tests for spacecraft handling."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
from scipy import constants
from unittest import TestCase
from abc import ABC, abstractclassmethod, abstractproperty

from . import test_base as base

from solarwindpy import vector
from solarwindpy import spacecraft

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
