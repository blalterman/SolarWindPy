"""Tests for :mod:`solarwindpy.fitfunctions` initialization."""


def test_importable_symbols():
    """Ensure key classes are importable from the package."""
    from solarwindpy.fitfunctions import (
        FitFunction,
        Gaussian,
        Exponential,
        Line,
        PowerLaw,
        TrendFit,
    )

    expected = [FitFunction, Gaussian, Exponential, Line, PowerLaw, TrendFit]
    assert all(callable(obj) for obj in expected)
