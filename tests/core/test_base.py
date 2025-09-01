#!/usr/bin/env python
"""Tests for basic synthetic data setup."""
import numpy as np
import pandas as pd
from pathlib import Path
from unittest import TestCase

pd.set_option("mode.chained_assignment", "raise")

DATA_PATH = Path(__file__).parent.parent / "data"


class TestData(object):
    def __init__(self):
        self.set_plasma_data()
        self.set_spacecraft_data()

    @property
    def epoch(self):
        path = DATA_PATH / "epoch.csv"
        epoch = pd.read_csv(path)["epoch"].map(pd.to_datetime)
        epoch.name = "epoch"
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
        path = DATA_PATH / "spacecraft.csv"
        test_data = pd.read_csv(path)
        test_data.columns = pd.MultiIndex.from_tuples(
            [tuple(c.split("|")) for c in test_data.columns]
        )
        test_data.columns.names = ["M", "C", "S"]
        test_data = test_data.astype(np.float64).sort_index(axis=1)
        test_data.index = self.epoch
        self._spacecraft_data = test_data.xs("", axis=1, level="S")

    def set_plasma_data(self):
        path = DATA_PATH / "plasma.csv"
        test_plasma = pd.read_csv(path)
        test_plasma.columns = pd.MultiIndex.from_tuples(
            [tuple(c.split("|")) for c in test_plasma.columns]
        )
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
