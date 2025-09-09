import numpy as np
import pytest
from types import SimpleNamespace

from solarwindpy.fitfunctions.core import (
    FitFunction,
    ChisqPerDegreeOfFreedom,
    InitialGuessInfo,
    InvalidParameterError,
    InsufficientDataError,
)


def linear_function(x, m, b):
    return m * x + b


class LinearFit(FitFunction):
    @property
    def function(self):
        return linear_function

    @property
    def p0(self):
        return [0.0, 0.0]

    @property
    def TeX_function(self):
        return "m x + b"


def test_clean_raw_obs():
    lf = LinearFit([0, 1], [1, 2])
    with pytest.raises(InvalidParameterError):
        lf._clean_raw_obs([0, 1], [1], None)
    x, y, w = lf._clean_raw_obs([0, 1], [1, 2], [1, 1])
    assert np.array_equal(x, np.array([0, 1]))
    assert np.array_equal(y, np.array([1, 2]))
    assert np.array_equal(w, np.array([1, 1]))


def test_build_one_obs_mask():
    lf = LinearFit([0, 1], [1, 2])
    x = np.array([0.0, 1.0, 2.0, np.nan])
    mask = lf._build_one_obs_mask("xobs", x, 0.5, 1.5)
    assert np.array_equal(mask, np.array([False, True, False, False]))
    mask = lf._build_one_obs_mask("xobs", x, None, 1.5)
    assert np.array_equal(mask, np.array([True, True, False, False]))
    mask = lf._build_one_obs_mask("xobs", x, 0.5, None)
    assert np.array_equal(mask, np.array([False, True, True, False]))


def test_build_outside_mask():
    lf = LinearFit([0, 1], [1, 2])
    x = np.arange(5)
    mask = lf._build_outside_mask("x", x, None)
    assert np.array_equal(mask, np.ones_like(x, dtype=bool))
    mask = lf._build_outside_mask("x", x, (1, 3))
    assert np.array_equal(mask, np.array([True, True, False, True, True]))


def test_set_fit_obs_combined_masks():
    x = np.array([0, 1, 2, 3, 4], dtype=float)
    y = np.array([10, 20, 30, 40, 50], dtype=float)
    w = np.array([0.5, 1, 2, 3, 4], dtype=float)
    lf = LinearFit(x, y, weights=w)
    lf.set_fit_obs(
        x,
        y,
        w,
        xmin=1,
        xmax=3,
        ymin=15,
        ymax=45,
        wmin=0.02,
        wmax=0.03,
        logy=True,
    )
    assert np.array_equal(lf.observations.used.x, np.array([1.0, 2.0]))
    assert np.array_equal(lf.observations.used.y, np.array([20.0, 30.0]))
    assert np.array_equal(lf.observations.used.w, np.array([1.0, 2.0]))
    assert np.array_equal(
        lf.observations.tk_observed, np.array([False, True, True, False, False])
    )


def test_set_argnames():
    lf = LinearFit([0, 1], [1, 2])
    assert lf.argnames == ["m", "b"]


def test_run_least_squares(monkeypatch, simple_linear_data):
    x, y, w = simple_linear_data
    lf = LinearFit(x, y, weights=w)
    captured = {}

    def fake_ls(func, p0, **kwargs):
        captured.update(kwargs)
        jac = np.eye(lf.observations.used.x.size, len(p0))
        return SimpleNamespace(
            success=True, x=p0, cost=0.0, jac=jac, fun=np.zeros(lf.nobs)
        )

    from solarwindpy.fitfunctions import core as core_module

    monkeypatch.setattr(core_module, "least_squares", fake_ls)
    res, p0 = lf._run_least_squares()
    assert captured["method"] == "trf"
    assert captured["loss"] == "huber"
    assert captured["max_nfev"] == 10000
    assert captured["f_scale"] == 0.1
    assert captured["jac"] == "2-point"
    assert np.array_equal(p0, np.array(lf.p0))

    with pytest.raises(ValueError):
        lf._run_least_squares(args=(1,))


def test_calc_popt_pcov_psigma_chisq():
    x = np.array([0.0, 1.0, 2.0])
    y = 2.0 * x + 1.0
    lf = LinearFit(x, y)
    jac = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
    res = SimpleNamespace(
        x=np.array([2.0, 1.0]), cost=0.0, fun=np.zeros_like(x), jac=jac
    )
    popt, pcov, psigma, chisq = lf._calc_popt_pcov_psigma_chisq(
        res, p0=np.array([0.0, 0.0])
    )
    assert np.allclose(popt, np.array([2.0, 1.0]))
    assert np.array_equal(pcov, np.zeros((2, 2)))
    assert np.array_equal(psigma, np.zeros(2))
    assert chisq.linear == 0.0 and chisq.robust == 0.0


def test_make_fit_success_failure(monkeypatch, simple_linear_data, small_n):
    x, y, w = simple_linear_data
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    assert isinstance(lf.fit_result, object)
    assert set(lf.popt) == {"m", "b"}
    assert set(lf.psigma) == {"m", "b"}
    assert lf.pcov.shape == (2, 2)
    assert isinstance(lf.chisq_dof, ChisqPerDegreeOfFreedom)
    assert lf.plotter is not None and lf.TeX_info is not None

    x, y, w = small_n
    lf_small = LinearFit(x, y, weights=w)
    err = lf_small.make_fit(return_exception=True)
    assert isinstance(err, InsufficientDataError)

    def fail_run(*_, **__):
        raise RuntimeError("fail")

    x, y, w = simple_linear_data
    lf_fail = LinearFit(x, y, weights=w)
    monkeypatch.setattr(LinearFit, "_run_least_squares", fail_run)
    err = lf_fail.make_fit(return_exception=True)
    assert isinstance(err, RuntimeError)
    with pytest.raises(RuntimeError):
        lf_fail.make_fit()


@pytest.fixture
def fitted_linear(simple_linear_data):
    x, y, w = simple_linear_data
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    return lf


def test_str_call_and_properties(fitted_linear):
    lf = fitted_linear
    s = str(lf)
    assert "LinearFit" in s and "m x + b" in s
    xnew = np.array([0.0, 0.5])
    ypred = lf(xnew)
    assert np.allclose(ypred, lf.popt["m"] * xnew + lf.popt["b"], rtol=1e-2, atol=1e-2)
    assert lf.argnames == ["m", "b"]
    assert isinstance(lf.fit_bounds, dict)
    assert isinstance(lf.chisq_dof, ChisqPerDegreeOfFreedom)
    assert lf.dof == lf.observations.used.y.size - len(lf.p0)
    assert lf.fit_result is not None
    assert isinstance(lf.initial_guess_info["m"], InitialGuessInfo)
    assert lf.nobs == lf.observations.used.x.size
    assert lf.plotter is not None
    assert set(lf.popt) == {"m", "b"}
    assert set(lf.psigma) == {"m", "b"}
    assert set(lf.psigma_relative) == {"m", "b"}
    combined = lf.combined_popt_psigma
    assert set(combined) == {"popt", "psigma", "psigma_relative"}
    assert lf.pcov.shape == (2, 2)
    assert 0.0 <= lf.rsq <= 1.0
    assert lf.sufficient_data is True
    assert lf.TeX_info is not None
