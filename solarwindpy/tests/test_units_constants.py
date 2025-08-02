#!/usr/bin/env python
"""Tests for units and constants containers."""

import pandas as pd

from solarwindpy.core import units_constants as uc


def test_units_attributes():
    u = uc.Units()
    attrs = [
        "bfield",
        "b",
        "v",
        "w",
        "dv",
        "ca",
        "cs",
        "cfms",
        "pth",
        "temperature",
        "n",
        "rho",
        "beta",
        "lnlambda",
        "nuc",
        "nc",
        "qpar",
        "distance2sun",
        "specific_entropy",
    ]
    for attr in attrs:
        assert hasattr(u, attr)
        assert isinstance(getattr(u, attr), float)


def test_constants_attributes():
    c = uc.Constants()
    attrs = [
        "misc",
        "kb",
        "m_in_mp",
        "m",
        "m_amu",
        "charges",
        "charge_states",
        "polytropic_index",
    ]
    for attr in attrs:
        assert hasattr(c, attr)
        assert isinstance(getattr(c, attr), pd.Series)
