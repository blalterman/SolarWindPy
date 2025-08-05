import warnings
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeWarning

from solarwindpy.fitfunctions import core, gaussians, trend_fits, lines


@pytest.fixture
def agged():
    xbins = pd.interval_range(0, 5, periods=5)
    ybins = pd.interval_range(0, 2, periods=2)
    data = {
        ybins[0]: np.array([1, 2, 3, 4, 5]),
        ybins[1]: np.array([2, 3, 4, 5, 6]),
    }
    return pd.DataFrame(data, index=xbins)


@pytest.fixture
def agged_empty():
    xbins = pd.interval_range(0, 5, periods=5)
    return pd.DataFrame({}, index=xbins)


@pytest.fixture
def trend_fit(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    tf.make_1dfits()
    tf.make_trend_func()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=OptimizeWarning)
        tf.trend_func.make_fit()
    return tf


def test_type_enforcement_and_properties(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    assert tf.agged.equals(agged)
    assert tf.ffunc1d_class is gaussians.Gaussian
    assert tf.trendfunc_class is lines.Line
    assert str(tf) == "TrendFit"
    with pytest.raises(TypeError):
        trend_fits.TrendFit(agged, int)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(int, lines.Line)
    with pytest.raises(TypeError):
        tf.set_fitfunctions(gaussians.Gaussian, int)


def test_make_ffunc1ds_make_1dfits(agged):
    tf = trend_fits.TrendFit(agged, lines.Line)
    tf.make_ffunc1ds()
    assert isinstance(tf.ffuncs.iloc[0], gaussians.Gaussian)
    tf.make_1dfits()
    assert tf.bad_fits.empty
    assert not tf.popt_1d.empty
    assert not tf.psigma_1d.empty


def test_make_trend_func_success_and_failure(trend_fit, agged_empty):
    assert isinstance(trend_fit.trend_func, lines.Line)
    tf = trend_fits.TrendFit(agged_empty, lines.Line)
    tf.make_ffunc1ds()
    with pytest.raises(ValueError):
        tf.make_trend_func()


def test_plotting_methods_return_axes(monkeypatch, trend_fit):
    class DummyAx:
        def set_xscale(self, *_):
            pass

        def errorbar(self, *_, **__):
            line = SimpleNamespace(set_linestyle=lambda *_: None)
            return "pl", "cl", [line]

        def legend(self, *_, **__):
            pass

    ax1, ax2 = DummyAx(), DummyAx()
    monkeypatch.setattr(
        trend_fit.trend_func.plotter,
        "plot_raw_used_fit_resid",
        lambda *_, **__: (ax1, ax2),
    )
    h, r = trend_fit.plot_trend_fit_resid()
    assert h is ax1 and r is ax2

    monkeypatch.setattr(trend_fit, "plot_all_popt_1d", lambda *_, **__: (1, 2, 3))
    h2, r2 = trend_fit.plot_trend_and_resid_on_ffuncs()
    assert h2 is ax1 and r2 is ax2

    monkeypatch.setattr(
        trend_fit.trend_func.plotter, "plot_raw_used_fit", lambda *_, **__: None
    )
    monkeypatch.setattr(
        trend_fits.swp.pp, "subplots", lambda *_, **__: (None, DummyAx())
    )
    ax = trend_fit.plot_1d_popt_and_trend()
    assert isinstance(ax, DummyAx)


def test_set_agged_set_fitfunctions_set_shared_labels(trend_fit, agged):
    new_agged = agged * 2
    trend_fit.set_agged(new_agged)
    assert trend_fit.agged.equals(new_agged)
    trend_fit.set_fitfunctions(gaussians.GaussianNormalized, lines.Line)
    assert trend_fit.ffunc1d_class is gaussians.GaussianNormalized
    trend_fit.set_fitfunctions(gaussians.Gaussian, lines.Line)
    trend_fit.set_shared_labels(x="time", y="density", z="counts")
    assert trend_fit.trend_func.plotter.labels.x == "time"
    first_ff = trend_fit.ffuncs.iloc[0]
    assert first_ff.plotter.labels.x == "density"
    assert first_ff.plotter.labels.y == "counts"


def test_set_agged_rejects_non_dataframe(trend_fit):
    with pytest.raises(AssertionError):
        trend_fit.set_agged(42)


def test_labels_instance_and_update(trend_fit):
    assert isinstance(trend_fit.labels, core.AxesLabels)
    trend_fit.set_shared_labels(x="time", y="density", z="counts")
    assert trend_fit.labels == core.AxesLabels("time", "density", "counts")
