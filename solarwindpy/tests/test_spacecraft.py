#!/usr/bin/env python
r"""Test spacecraft class.
"""
import pdb
import numpy as np
import pandas as pd
import unittest
import pandas.util.testing as pdt
from unittest import TestCase
from abc import ABC, abstractmethod, abstractclassmethod

from solarwindpy.vector import Vector
from solarwindpy.spacecraft import Spacecraft

pd.set_option("mode.chained_assignment", "raise")


class TestBase(ABC, TestCase):
    @classmethod
    def setUpClass(cls):
        # print("TestBase.setUpClass", flush=True)
        test_plasma = {
            ("pos_HCI", "x", ""): {0: -4000000, 1: -200000, 2: -300000},
            ("pos_HCI", "y", ""): {0: 20000000, 1: 30000000, 2: 10000000},
            ("pos_HCI", "z", ""): {0: 300000, 1: 200000, 2: 400000},
            ("v_HCI", "x", ""): {0: 9.0, 1: 10.0, 2: 8.0},
            ("v_HCI", "y", ""): {0: -80.0, 1: -70.0, 2: -90.0},
            ("v_HCI", "z", ""): {0: -0.5, 1: 0.5, 2: 1.5},
            ("Carr", "lat", ""): {0: -2.0, 1: -1.0, 2: 3.0},
            ("Carr", "lon", ""): {0: -26.0, 1: -36.0, 2: -16.0},
            ("gse", "x", ""): {0: 230, 1: 235, 2: 240},
            ("gse", "y", ""): {0: 50, 1: 20, 2: 10},
            ("gse", "z", ""): {0: 30, 1: 25, 2: -50},
        }

        test_data = pd.DataFrame.from_dict(
            test_plasma, orient="columns", dtype=np.float64
        )

        test_data.columns.names = ["M", "C", "S"]
        cls.data = test_data
        cls.set_object_testing()
        # print("Done with TestBase", flush=True)

    @abstractclassmethod
    def set_object_testing(cls):
        pass

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def frame(self):
        pass

    def test_data(self):
        ot = self.object_testing
        pdt.assert_frame_equal(self.data, ot.data)

    def test_name(self):
        ot = self.object_testing
        self.assertEqual(self.name, ot.name)

    def test_frame(self):
        ot = self.object_testing
        self.assertEqual(self.frame, ot.frame)

    @abstractmethod
    def test_position(self):
        cols = pd.Index(("x", "y", "z"))

        ot = self.object_testing
        pdt.assert_index_equal(cols, ot.position.columns)
        self.assertIsInstance(ot.position, Vector)
        self.assertEqual(ot.position, ot.pos)
        return ot

    @abstractmethod
    def test_velocity(self):
        cols = pd.Index(("x", "y", "z"))

        ot = self.object_testing
        pdt.assert_index_equal(cols, ot.velocity.columns)
        self.assertIsInstance(ot.velocity, Vector)
        self.assertEqual(ot.velocity, ot.v)
        return ot


class TestWind(TestBase):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.xs("gse", axis=1, level="M").xs("", level="S")
        sc = Spacecraft(data, "wind", "gse", velocity=None, carrington=None)

        cls.object_testing = sc

    @property
    def frame(self):
        return "GSE"

    @property
    def name(self):
        return "WIND"

    def test_position(self):
        super(TestWind, self).test_position()

        pos = self.data.xs("gse", axis=1, level="M").xs("", axis=1, level="S")
        ot = self.object_testing
        pdt.assert_frame_equal(pos, ot.position.data)

    def test_velocity(self):
        with self.assertRaises(NotImplementedError):
            self.object_testing.velocity
        with self.assertRaises(NotImplementedError):
            self.object_testing.v


class TestPSP(TestBase):
    @classmethod
    def set_object_testing(cls):
        pos = cls.data.xs("pos_HCI", axis=1, level="M")
        v = cls.data.xs("v_HCI", axis=1, level="M")
        carr = cls.data.xs("Carr", axis=1, level="M")
        sc = Spacecraft(pos, "psp", "hci", velocity=v, carrington=carr)
        cls.object_testing = sc

    @property
    def frame(self):
        return "HCI"

    @property
    def name(self):
        return "PSP"

    def test_position(self):
        super(TestPSP, self).test_position()

        pos = self.data.xs("pos_HCI", axis=1, level="M").xs("", axis=1, level="S")
        ot = self.object_testing
        pdt.assert_frame_equal(pos, ot.position.data)

    def test_velocity(self):
        super(TestPSP, self).test_velocity()

        v = self.data.xs("v_HCI", axis=1, level="M").xs("", axis=1, level="S")
        ot = self.object_testing
        pdt.assert_frame_equal(v, ot.velocity)

    def test_carrington(self):
        cols = pd.Index(("lat", "lon"))
        carr = self.data.xs("Carr", axis=1, level="M").xs("", axis=1, level="S")

        ot = self.object_testing
        pdt.assert_index_equal(cols, ot.carrington.columns)
        self.assertIsInstance(ot.carrington, pd.DataFrame)
        self.assertEqual(carr, ot.carrington)


if __name__ == "__main__":

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

    try:
        unittest.main(verbosity=2)

    except (  # noqa: 841
        AssertionError,
        AttributeError,
        ValueError,
        TypeError,
        IndexError,
    ) as e:
        import sys
        import traceback as tb

        exc_info = sys.exc_info()
        tb.print_exception(*exc_info)
        pdb.post_mortem(exc_info[-1])
