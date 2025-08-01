#!/usr/bin/env python
"""Tests for exponential fit functions."""

import numpy as np
import numpy.testing as npt

from solarwindpy.fitfunctions.exponentials import (
    Exponential,
    ExponentialPlusC,
    ExponentialCDF,
)


def test_exponential_p0_and_tex():
    x = np.arange(4, dtype=float)
    y = np.array([1.0, 2.0, 3.0, 4.0])
    ff = Exponential(x, y)
    assert ff.p0 == [1.0, 4.0]
    assert ff.TeX_function == r"f(x)=A \cdot e^{-cx}"


def test_exponentialplusc_p0_and_tex():
    x = np.arange(4, dtype=float)
    y = np.array([1.0, 2.0, 3.0, 4.0])
    ff = ExponentialPlusC(x, y)
    assert ff.p0 == [1.0, 4.0, 0.0]
    assert ff.TeX_function == r"f(x)=A \cdot e^{-cx} + d"


def test_exponentialcdf_p0_tex_and_set_y0():
    x = np.arange(4, dtype=float)
    y = np.array([1.0, 2.0, 3.0, 4.0])
    ff = ExponentialCDF(x, y)
    assert ff.p0 == [2.5]
    assert ff.TeX_function == r"f(x)=A \left(1 - e^{-cx}\right)"

    ff.set_y0(10.0)
    func = ff.function
    result = func(np.array([0.0, 1.0]), 2.0)
    expected = 10.0 * (1.0 - np.exp(-2.0 * np.array([0.0, 1.0])))
    npt.assert_allclose(result, expected)
