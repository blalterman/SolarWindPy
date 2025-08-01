import numpy as np
import pytest

from solarwindpy.fitfunctions.core import FitFunction


class ConstantFF(FitFunction):
    """Minimal constant fit function used for testing."""

    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def const(x, a):
            return np.full_like(x, a, dtype=float)

        return const

    @property
    def p0(self):
        return [np.mean(self.observations.used.y)]

    @property
    def TeX_function(self):
        return r"f(x)=a"


def test_build_one_obs_mask():
    ff = ConstantFF([0], [1])
    x = np.array([1.0, 2.0, np.nan, np.inf, 0.5])
    mask = ff._build_one_obs_mask("x", x, 0.5, 2.0)
    assert mask.tolist() == [True, True, False, False, True]


def test_build_outside_mask():
    ff = ConstantFF([0], [1])
    x = np.array([1.0, 2.0, 3.0, 4.0])
    mask = ff._build_outside_mask("x", x, (1.5, 3.5))
    assert mask.tolist() == [True, False, False, True]
    assert ff._build_outside_mask("x", x, None).tolist() == [True] * 4


def test_residuals_and_make_fit():
    x = np.arange(5, dtype=float)
    y = np.full_like(x, 3.0)
    ff = ConstantFF(x, y)
    ff.make_fit()

    assert pytest.approx(3.0) == ff.popt["a"]
    assert pytest.approx(0.0) == ff.psigma["a"]
    assert pytest.approx(0.0) == ff.chisq_dof.linear

    res = ff.residuals()
    assert np.allclose(res, 0.0)
