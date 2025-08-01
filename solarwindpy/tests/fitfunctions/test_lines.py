import numpy as np
from solarwindpy.fitfunctions.lines import Line


def test_line_fit_and_properties():
    x = np.linspace(0, 10, 20)
    m_true = 2.5
    b_true = -1.0
    y = m_true * x + b_true

    fit = Line(x, y)

    m0, b0 = fit.p0
    assert np.isclose(m0, m_true)
    assert np.isclose(b0, b_true)

    fit.make_fit()

    assert np.isclose(fit.popt["m"], m_true)
    assert np.isclose(fit.popt["b"], b_true)
    assert np.isclose(fit.x_intercept, -b_true / m_true)

    x_test = np.array([-1.0, 0.0, 4.0, 7.5])
    expected = m_true * x_test + b_true
    assert np.allclose(fit(x_test), expected)
