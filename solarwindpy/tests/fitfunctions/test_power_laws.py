import numpy as np

from solarwindpy.fitfunctions.power_laws import (
    PowerLaw,
    PowerLawPlusC,
    PowerLawOffCenter,
)


def test_power_law_fit():
    x = np.linspace(1, 10, 20)
    A_true = 2.5
    b_true = 1.2
    y = A_true * x**b_true
    pl = PowerLaw(x, y)
    assert pl.p0 == [1, 1]
    pl.make_fit()
    popt = pl.popt
    assert np.allclose(popt["A"], A_true, rtol=1e-2)
    assert np.allclose(popt["b"], b_true, rtol=1e-2)


def test_power_law_plus_c_fit():
    x = np.linspace(2, 12, 20)
    A_true = 3.0
    b_true = 0.8
    c_true = 1.5
    y = A_true * x**b_true + c_true
    pl = PowerLawPlusC(x, y)
    assert pl.p0 == [1, 1, 0]
    pl.make_fit()
    popt = pl.popt
    assert np.allclose(popt["A"], A_true, rtol=1e-2)
    assert np.allclose(popt["b"], b_true, rtol=1e-2)
    assert np.allclose(popt["c"], c_true, rtol=1e-2)


def test_power_law_off_center_fit():
    x = np.linspace(2, 10, 20)
    A_true = 4.0
    b_true = 1.5
    x0_true = 1.0
    y = A_true * (x - x0_true) ** b_true
    pl = PowerLawOffCenter(x, y)
    assert pl.p0 == [1, 1, 0]
    pl.make_fit()
    popt = pl.popt
    assert np.allclose(popt["A"], A_true, rtol=1e-2)
    assert np.allclose(popt["b"], b_true, rtol=1e-2)
    assert np.allclose(popt["x0"], x0_true, rtol=1e-2)
