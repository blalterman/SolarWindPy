#!/usr/bin/env python
"""Tests for units and constants containers."""

import math

import pandas as pd
import pytest

from solarwindpy.core import units_constants as uc

# Exact by definition of the 2019 SI.
PLANCK_H = 6.62607015e-34  # [J s]

# IAU 2015 Resolution B3 nominal solar radius, Prsa et al. (2016), AJ 152, 41,
# doi:10.3847/0004-6256/152/2/41.
IAU_2015_SOLAR_RADIUS = 695.7e6  # [m]


def test_hbar_is_h_over_two_pi():
    """ON FAILURE: `hbar` is not the SI-exact h / 2 pi; the code is wrong."""
    # Both sides are the same exact quantity; rel=1e-12 allows float rounding only.
    # abs=0 because approx's default abs=1e-12 would swamp a value of order 1e-34.
    assert uc.Constants().misc["hbar"] == pytest.approx(
        PLANCK_H / (2 * math.pi), rel=1e-12, abs=0
    )


def test_solar_radius_is_the_iau_2015_nominal_value():
    """ON FAILURE: `Rs [m]` is not the IAU 2015 nominal value; the code is wrong."""
    assert uc.Constants().misc["Rs [m]"] == IAU_2015_SOLAR_RADIUS


def test_units_attributes():
    u = uc.Units()
    assert hasattr(u, "b")
    assert isinstance(u.b, float)
    assert hasattr(u, "v")
    assert isinstance(u.v, float)


def test_constants_attributes():
    c = uc.Constants()
    assert hasattr(c, "kb")
    assert isinstance(c.kb, pd.Series)
    assert hasattr(c, "misc")
    assert isinstance(c.misc, pd.Series)


def test_heat_flux_display_unit_is_one_microwatt_per_square_metre():
    """ON FAILURE: `Units.qpar` is not 1 uW m^-2 expressed in W m^-2; the code is wrong."""
    assert uc.Units().qpar == 1e-6
