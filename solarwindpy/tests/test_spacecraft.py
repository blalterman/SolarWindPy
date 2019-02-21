#!/usr/bin/env python
r"""Test spacecraft class.
"""
import pdb
import numpy as np
import pandas as pd
import unittest
import pandas.util.testing as pdt
from unittest import TestCase
from abc import ABC, abstractmethod

pd.set_option("mode.chained_assignment", "raise")


class TestData(TestCase):
    @classmethod
    def setUpClass(cls):
        # print("TestData.setUpClass", flush=True)
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

        test_data = pd.DataFrame.from_dict(test_plasma, orient="columns")
        test_data = test_data.astype(np.float64)
        test_data.columns.names = ["M", "C", "S"]

        cls.data = test_plasma
        # print("Done with TestData", flush=True)

    @staticmethod
    def assert_series_not_equal(*args, **kwargs):
        try:
            pdt.assert_series_equal(*args, **kwargs)
        except AssertionError:
            # frames are not equal
            pass
        else:
            # frames are equal
            raise AssertionError

    @staticmethod
    def assert_frame_not_equal(*args, **kwargs):
        try:
            pdt.assert_frame_equal(*args, **kwargs)
        except AssertionError:
            # frames are not equal
            pass
        else:
            # frames are equal
            raise AssertionError


class TestGSE(TestData):
    # Has location, no velocity
    raise NotImplementedError


class TestHCI(TestData):
    # Has location and velocity
    raise NotImplementedError


class TestCarrington(TestData):
    raise NotImplementedError


class TestSpaceCraft(ABC, TestData):
    raise NotImplementedError

    def test_spacecraft_pos(self):
        raise NotImplementedError

    @abstractmethod
    def test_spacecraft_vel(self):
        raise NotImplementedError

    def test_spacecraft_frame(self):
        raise NotImplementedError


class TestWind(TestSpaceCraft):
    # Has only GSE
    raise NotImplementedError


class TestPSP(TestSpaceCraft):
    # Has HCI vel, pos and carrington
    raise NotImplementedError


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
