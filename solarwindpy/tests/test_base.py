#!/usr/bin/env python
r"""Test setup with *Wind/SWE/FC*.
"""
import pdb
import numpy as np
import pandas as pd
import unittest
from unittest import TestCase

pd.set_option("mode.chained_assignment", "raise")


class TestData(object):
    def __init__(self):
        self.set_plasma_data()
        self.set_spacecraft_data()

    @property
    def epoch(self):
        epoch = pd.Series(
            # One date in early Wind mission and two dates outside. The long separation
            # allows us to test Alfvenic Turbulence rolling to ensure NaNs pop up. The
            # dates outside of the Wind mission help test for future compatibility.
            {
                0: pd.to_datetime("1995-01-01 12:35:00"),
                1: pd.to_datetime("2022-03-23 19:29:09"),
                2: pd.to_datetime("2022-10-09 01:47:01.23456"),
            },
            name="epoch",
        )
        return epoch

    @property
    def spacecraft_data(self):
        return self._spacecraft_data

    @property
    def plasma_data(self):
        return self._plasma_data

    @property
    def combined_data(self):
        sc = pd.concat(
            {"sc": self.spacecraft_data}, axis=1, names=["S"], sort=True
        ).reorder_levels(["M", "C", "S"], axis=1)
        out = pd.concat([self.plasma_data, sc], axis=1, sort=True)
        return out

    def set_spacecraft_data(self):
        test_data = {
            ("pos_HCI", "x", ""): {0: -42, 1: -22, 2: -34},
            ("pos_HCI", "y", ""): {0: 23, 1: 31, 2: 11},
            ("pos_HCI", "z", ""): {0: 35, 1: 27, 2: 49},
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
            test_data, orient="columns", dtype=np.float64
        )
        test_data.columns.names = ["M", "C", "S"]
        test_data.index = self.epoch
        self._spacecraft_data = test_data.xs("", axis=1, level="S")

    def set_plasma_data(self):
        test_plasma = {
            ("b", "x", ""): {0: 0.5, 1: 0.6, 2: 0.7},
            ("b", "y", ""): {0: -0.25, 1: -0.26, 2: 0.27},
            ("b", "z", ""): {0: 0.3, 1: 0.4, 2: -0.7},
            ("b", "theta_rms", ""): {0: 0.01, 1: 0.07, 2: 0.03},
            ("b", "mag_rms", ""): {0: 0.1, 1: 0.2, 2: 0.3},
            ("n", "", "a"): {0: 0.5, 1: 1.0, 2: 1.5},
            ("n", "", "p1"): {0: 1.0, 1: 2.0, 2: 3.0},
            ("n", "", "p2"): {0: 2.0, 1: 3.0, 2: 4.0},
            ("v", "x", "a"): {0: 125.0, 1: 250.0, 2: 375.0},
            ("v", "x", "p1"): {0: 100.0, 1: 200.0, 2: 300.0},
            ("v", "x", "p2"): {0: 150.0, 1: 300.0, 2: 450.0},
            ("v", "y", "a"): {0: 250.0, 1: 375.0, 2: 750.0},
            ("v", "y", "p1"): {0: 200.0, 1: 300.0, 2: 600.0},
            ("v", "y", "p2"): {0: 300.0, 1: 450.0, 2: 900.0},
            ("v", "z", "a"): {0: 500.0, 1: 750.0, 2: 1000.0},
            ("v", "z", "p1"): {0: 400.0, 1: 600.0, 2: 800.0},
            ("v", "z", "p2"): {0: 600.0, 1: 900.0, 2: 1200.0},
            ("w", "par", "a"): {0: 3.0, 1: 4.0, 2: 5.0},
            ("w", "par", "p1"): {0: 10.0, 1: 20.0, 2: 30.0},
            ("w", "par", "p2"): {0: 7.5, 1: 15.0, 2: 22.5},
            ("w", "per", "a"): {0: 7.0, 1: 9.0, 2: 10.0},
            ("w", "per", "p1"): {0: 7.0, 1: 26.0, 2: 28.0},
            ("w", "per", "p2"): {0: 5.5, 1: 20.0, 2: 30.5},
            ("n", "", "e"): {0: 2.0, 1: 3.0, 2: 7.0},
            ("v", "x", "e"): {0: 130.0, 1: 230.0, 2: 380.0},
            ("v", "y", "e"): {0: 230.0, 1: 450.0, 2: 800.0},
            ("v", "z", "e"): {0: 700.0, 1: 800.0, 2: 900.0},
            ("w", "par", "e"): {0: 5.0, 1: 12.0, 2: 25.0},
            ("w", "per", "e"): {0: 6.0, 1: 22.0, 2: 15.0},
        }

        test_plasma = pd.DataFrame.from_dict(test_plasma, orient="columns")
        test_plasma = test_plasma.astype(np.float64)
        test_plasma.columns.names = ["M", "C", "S"]

        test_plasma.index = self.epoch
        test_plasma = test_plasma.sort_index(axis=1)

        self._plasma_data = test_plasma


class SWEData(TestCase):
    @classmethod
    def setUpClass(cls):
        data = TestData()
        cls.data = data.plasma_data.sort_index(axis=1)
        cls.set_object_testing()


class AlphaTest(object):
    @property
    def species(self):
        return "a"


class P1Test(object):
    @property
    def species(self):
        return "p1"


class P2Test(object):
    @property
    def species(self):
        return "p2"


class AlphaP1Test(object):
    @property
    def species(self):
        return "a+p1"


class AlphaP2Test(object):
    @property
    def species(self):
        return "a+p2"


class P1P2Test(object):
    @property
    def species(self):
        return "p1+p2"


class AlphaP1P2Test(object):
    @property
    def species(self):
        return "a+p1+p2"


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
