#!/usr/bin/env python
"""Tests for Gaussian fit functions."""

import numpy as np

from solarwindpy.fitfunctions.gaussians import (
    Gaussian,
    GaussianNormalized,
    GaussianLn,
)


def test_gaussian_p0():
    """Gaussian.p0 should recover mean, std, and amplitude."""
    mu = 0.0
    sigma = 1.0
    amplitude = 2.0
    x = np.linspace(-5, 5, 101)
    y = amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    fit = Gaussian(x, y)
    p0 = fit.p0
    expected = [mu, sigma, amplitude]
    np.testing.assert_allclose(p0, expected, rtol=1e-4, atol=1e-12)


def test_gaussian_normalized_p0():
    """GaussianNormalized.p0 should estimate n from amplitude and sigma."""
    mu = 0.0
    sigma = 1.0
    amplitude = 2.0
    x = np.linspace(-5, 5, 101)
    y = amplitude * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    fit = GaussianNormalized(x, y)
    p0 = fit.p0
    n_expected = amplitude * sigma * np.sqrt(2 * np.pi)
    expected = [mu, sigma, n_expected]
    np.testing.assert_allclose(p0, expected, rtol=1e-4, atol=1e-12)


def test_gaussianln_normal_parameters_and_flag():
    """GaussianLn.normal_parameters and flag behaviour."""
    x = np.linspace(0.1, 2.0, 50)
    y = np.ones_like(x)
    fit = GaussianLn(x, y)

    m = 1.0
    s = 0.5
    a = 2.0
    fit._popt = [("m", m), ("s", s), ("A", a)]

    params = fit.normal_parameters
    mu_expected = np.exp(m + 0.5 * s**2)
    sigma_expected = np.exp(s**2 + 2 * m) * (np.exp(s**2) - 1)
    sigma_expected = np.sqrt(sigma_expected)
    np.testing.assert_allclose(
        [params["mu"], params["sigma"]],
        [mu_expected, sigma_expected],
    )

    assert fit.TeX_report_normal_parameters is False
    fit.set_TeX_report_normal_parameters(True)
    assert fit.TeX_report_normal_parameters is True
