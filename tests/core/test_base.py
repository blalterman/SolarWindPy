#!/usr/bin/env python
"""Tests for basic synthetic data setup."""

import pandas as pd
from unittest import TestCase

from solarwindpy.examples import _read_example

pd.set_option("mode.chained_assignment", "raise")


class SyntheticData(object):
    """The example data behind ``solarwindpy.examples.load_plasma``, as frames.

    ``plasma_data`` keeps every column of the example CSV, including those
    ``Plasma`` drops; ``spacecraft_data`` holds both the HCI trajectory and
    the GSE position as ``(M, C)`` columns.
    """

    def __init__(self):
        self._plasma_data = _read_example("plasma")
        self._spacecraft_data = _read_example("spacecraft").xs("", axis=1, level="S")

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


class SWEData(TestCase):
    @classmethod
    def setUpClass(cls):
        data = SyntheticData()
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
