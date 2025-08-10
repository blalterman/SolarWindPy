"""Shared fixtures for fitfunction tests."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def simple_linear_data():
    """Noisy linear data with unit weights.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Tuple ``(x, y, w)`` where ``y`` follows ``2*x + 1`` with added
        Gaussian noise and ``w`` contains unit weights.
    """
    rng = np.random.default_rng(42)
    x = np.linspace(0.0, 1.0, 20)
    noise = rng.normal(scale=0.05, size=x.shape)
    y = 2.0 * x + 1.0 + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.fixture
def gauss_data():
    """Synthetic Gaussian data.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Tuple ``(x, y, w)`` where ``y`` is a Gaussian with additive noise
        and ``w`` contains unit weights.
    """
    rng = np.random.default_rng(42)
    amplitude = 1.0
    mean = 0.0
    sigma = 1.0
    x = np.linspace(-5.0, 5.0, 100)
    noise = rng.normal(scale=0.05, size=x.shape)
    y = amplitude * np.exp(-0.5 * ((x - mean) / sigma) ** 2) + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.fixture
def small_n():
    """Minimal dataset insufficient for fitting.

    Returns
    -------
    tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Tuple ``(x, y, w)`` containing a single observation.
    """
    x = np.linspace(0.0, 1.0, 1)
    y = 2.0 * x + 1.0
    w = np.ones_like(x)
    return x, y, w
