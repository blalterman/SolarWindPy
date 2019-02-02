#!/usr/bin/env python
"""
Name   : test_base.py
Author : B. L. Alterman
e-mail : balterma@umich.edu

Description
-----------
-Base class for tests.

Propodes Updates
----------------
-

Notes
-----
-

"""

import pdb

import re as re
import numpy as np
import pandas as pd
import unittest
import sys
import itertools

from numbers import Number
from pandas import MultiIndex as MI

import numpy.testing as npt
import pandas.util.testing as pdt

from abc import ABC, abstractproperty
from abc import abstractmethod, abstractstaticmethod, abstractclassmethod
from unittest import TestCase

from scipy import constants
from scipy.constants import physical_constants

# from plasma import Plasma, Ion, BField

pd.set_option("mode.chained_assignment", "raise")

class TestData(TestCase):
    @classmethod
    def setUpClass(cls):
        # print("TestData.setUpClass", flush=True)
        test_plasma = {
            ("b", "x", "", ""): {0: 0.5, 1: 0.6, 2: 0.7},
            ("b", "y", "", ""): {0: -0.25, 1: -0.26, 2: 0.27},
            ("b", "z", "", ""): {0: 0.3, 1: 0.4, 2: -0.7},
            ("b", "theta_rms", "", ""): {0: 0.01, 1: 0.07, 2: 0.03},
            ("b", "mag_rms", "", ""): {0: 0.1, 1: 0.2, 2: 0.3},

            ("n", "", "a", ""): {0: 0.5, 1: 1.0, 2: 1.5},
            ("n", "", "p1", ""): {0: 1.0, 1: 2.0, 2: 3.0},
            ("n", "", "p2", ""): {0: 2.0, 1: 3.0, 2: 4.0},

            ("v", "x", "a", ""): {0: 125.0, 1: 250.0, 2: 375.0},
            ("v", "x", "p1", ""): {0: 100.0, 1: 200.0, 2: 300.0},
            ("v", "x", "p2", ""): {0: 150.0, 1: 300.0, 2: 450.0},

            ("v", "y", "a", ""): {0: 250.0, 1: 375.0, 2: 750.0},
            ("v", "y", "p1", ""): {0: 200.0, 1: 300.0, 2: 600.0},
            ("v", "y", "p2", ""): {0: 300.0, 1: 450.0, 2: 900.0},

            ("v", "z", "a", ""): {0: 500.0, 1: 750.0, 2: 1000.0},
            ("v", "z", "p1", ""): {0: 400.0, 1: 600.0, 2: 800.0},
            ("v", "z", "p2", ""): {0: 600.0, 1: 900.0, 2: 1200.0},

            ("w", "par", "a", ""): {0: 3.0, 1: 4.0, 2: 5.0},
            ("w", "par", "p1", ""): {0: 10.0, 1: 20.0, 2: 30.0},
            ("w", "par", "p2", ""): {0: 7.5, 1: 15.0, 2: 22.5},

            ("w", "per", "a", ""): {0: 7.0, 1: 9.0, 2: 10.0},
            ("w", "per", "p1", ""): {0: 7.0, 1: 26.0, 2: 28.0},
            ("w", "per", "p2", ""): {0: 5.5, 1: 20.0, 2: 30.5},

            ("n", "", "p1", "mom"): {0: 1.0, 1: 2.0, 2: 3.0},
            ("v", "x", "p1", "mom"): {0: 100.0, 1: 200.0, 2: 300.0},
            ("v", "y", "p1", "mom"): {0: 200.0, 1: 300.0, 2: 600.0},
            ("v", "z", "p1", "mom"): {0: 400.0, 1: 600.0, 2: 800.0},
            ("w", "par", "p1", "mom"): {0: 10.0, 1: 20.0, 2: 30.0},
            ("w", "per", "p1", "mom"): {0: 7.0, 1: 26.0, 2: 28.0},
            ("w", "scalar", "p1", "mom"): {0: 5.5, 1: 20.0, 2: 30.5},
            ("n", "", "p1", "bimax"): {0: 1.0, 1: 2.0, 2: 3.0},
            ("v", "x", "p1", "bimax"): {0: 100.0, 1: 200.0, 2: 300.0},
            ("v", "y", "p1", "bimax"): {0: 200.0, 1: 300.0, 2: 600.0},
            ("v", "z", "p1", "bimax"): {0: 400.0, 1: 600.0, 2: 800.0},
            ("w", "par", "p1", "bimax"): {0: 10.0, 1: 20.0, 2: 30.0},
            ("w", "per", "p1", "bimax"): {0: 7.0, 1: 26.0, 2: 28.0},
            ("gse", "x", "", ""): {0: 230, 1: 235, 2: 240},
            ("gse", "y", "", ""): {0: 50, 1: 20, 2: 10},
            ("gse", "z", "", ""): {0: 30, 1: 25, 2: -50},

            ("n", "", "e", ""): {0: 2.0, 1:3.0, 2: 7.0},
            ("v", "x", "e", ""): {0: 130.0, 1: 230.0, 2: 380.0},
            ("v", "y", "e", ""): {0: 230.0, 1: 450.0, 2: 800.0},
            ("v", "z", "e", ""): {0: 700.0, 1: 800.0, 2: 900.0},
            ("w", "par", "e", ""): {0: 5.0, 1: 12.0, 2: 25.0},
            ("w", "per", "e", ""): {0: 6.0, 1: 22.0, 2: 15.0},

            ("dv", "", "p2", "P9"): {0: -13545, 1: 244, 2: -1457329},

            ("year", "", "", ""): {0: 1994, 1: 2005, 2: 2016},
            ("fdoy", "", "", ""): {0: 12.5, 1: 309.1, 2: 61.75}
            }

        test_plasma = pd.DataFrame.from_dict(test_plasma, orient="columns")
        test_plasma = test_plasma.astype(np.float64)
        test_plasma.columns.names = ["M", "C", "S", "N"]

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

class SWEData(TestData):
    @classmethod
    def setUpClass(cls):
        # print("SWEData.setUpClass", flush=True)
        super(SWEData, cls).setUpClass()
        # print(cls.data.iloc[:, :7])
        # print(cls.data.columns.values)
        cls.data = cls.data.xs("", axis=1, level="N")
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
    import sys

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

    try:
        unittest.main(verbosity=2)

    except (AssertionError, AttributeError, ValueError, TypeError, IndexError) as e:
        import sys
        import traceback as tb

        exc_info = sys.exc_info()
        tb.print_exception(*exc_info)
        pdb.post_mortem(exc_info[-1])
