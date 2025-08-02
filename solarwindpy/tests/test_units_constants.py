#!/usr/bin/env python
"""Tests for units and constants containers."""

import pandas as pd

from solarwindpy.core import units_constants as uc


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
