#!/usr/bin/env python
"""Tests for :mod:`solarwindpy.fitfunctions.plots`."""

import numpy as np
from types import SimpleNamespace
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from solarwindpy.fitfunctions.core import Observations, UsedRawObs
from solarwindpy.fitfunctions.plots import FFPlot
from solarwindpy.fitfunctions.tex_info import TeXinfo


def make_plotter():
    """Return a simple ``FFPlot`` instance for testing."""
    plt.switch_backend("Agg")

    x_raw = np.arange(5.0)
    y_fit = 2.0 * x_raw + 1.0
    y_raw = y_fit.copy()
    mask = np.array([False, True, True, True, False])

    used = Observations(x_raw[mask], y_raw[mask] + 0.5, np.full(mask.sum(), 0.1))
    raw = Observations(x_raw, y_raw, np.full_like(x_raw, 0.1))
    obs = UsedRawObs(used=used, raw=raw, tk_observed=mask)

    tex_info = TeXinfo({"a": 0.0}, {"a": 0.0}, "f(x)", 0.0, 1.0)
    fit_result = SimpleNamespace(fun=np.zeros(mask.sum()))

    return FFPlot(obs, y_fit, tex_info, fit_result)


def test_plot_raw_returns_axes():
    plotter = make_plotter()
    ax, *_ = plotter.plot_raw()
    assert isinstance(ax, Axes)


def test_plot_used_returns_axes():
    plotter = make_plotter()
    ax, *_ = plotter.plot_used()
    assert isinstance(ax, Axes)


def test_plot_fit_returns_axes():
    plotter = make_plotter()
    ax = plotter.plot_fit(annotate=False)
    assert isinstance(ax, Axes)


def test_plot_residuals_returns_axes():
    plotter = make_plotter()
    ax = plotter.plot_residuals()
    assert isinstance(ax, Axes)


def test_residuals_computation():
    plotter = make_plotter()
    mask = plotter.observations.tk_observed
    expected_abs = plotter.y_fit[mask] - plotter.observations.used.y
    np.testing.assert_allclose(plotter.residuals(pct=False), expected_abs)

    expected_pct = 100.0 * expected_abs / plotter.y_fit[mask]
    np.testing.assert_allclose(plotter.residuals(pct=True), expected_pct)
