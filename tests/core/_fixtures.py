# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Inputs and reference values shared by the tests in ``tests/core``.

The pytest-free classes here build the example data behind
``solarwindpy.examples.load_plasma`` (read through the private
``_read_example`` loader) and name the species a test class runs on. Test
modules import this module and mix the classes into their own ``Test*``
classes; nothing here is collected.
"""

from unittest import TestCase

import numpy as np
import pandas as pd

import solarwindpy as swp
from solarwindpy.core.plasma import Plasma
from solarwindpy.examples import _read_example

# IAU 2015 Resolution B3 nominal values, Prsa et al. (2016), AJ 152, 41,
# doi:10.3847/0004-6256/152/2/41.
IAU_2015_SOLAR_RADIUS = 695.7e6  # [m]
IAU_2015_EARTH_EQUATORIAL_RADIUS = 6.3781e6  # [m]


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


def _species_masked_plasma():
    r"""Example plasma with p1 missing at row 0, a at row 1, and both at row 2."""
    base = swp.examples.load_plasma()
    data = base.data.copy()
    t = data.index
    data.loc[t[0], ("w", "par", "p1")] = np.nan
    data.loc[t[1], ("w", "per", "a")] = np.nan
    data.loc[t[2], ("w", "par", "p1")] = np.nan
    data.loc[t[2], ("w", "per", "a")] = np.nan
    return Plasma(data, *base.species, sc=base.sc)
