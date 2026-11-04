# Spent-When: PERMANENT(FitFunction stops exposing its results as one table)
# Supersedes: none
"""Contract tests for the one results table every fit exposes.

``FitFunction.results`` is a one-row DataFrame whose columns are a
``(P, K)`` MultiIndex: each parameter's ``value`` and ``uncertainty``, then
the fit-quality columns and a ``status``. A failed fit leaves the same row
with NaN values and the failure's class name as its status.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions.core import FitFailedError, InsufficientDataError
from solarwindpy.fitfunctions.gaussians import Gaussian
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.fitfunctions.power_laws import PowerLawOffCenter
from tests.tolerances import exact, noise_free

# The quality and status columns that follow the parameter columns, in order.
QUALITY = [
    ("chisq_dof", "linear"),
    ("chisq_dof", "robust"),
    ("rsq", ""),
    ("nobs", ""),
    ("dof", ""),
    ("status", ""),
]


def _gaussian(n=41):
    """Noise-free Gaussian with mu=2, sigma=0.5, A=10 on n points in [0, 4]."""
    x = np.linspace(0.0, 4.0, n)
    return x, 10.0 * np.exp(-0.5 * ((x - 2.0) / 0.5) ** 2)


def test_results_is_one_row_of_parameter_value_uncertainty_then_quality_columns():
    """The table's columns are (P, K): each parameter's value and uncertainty, then quality.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)
    fit.make_fit()
    res = fit.results

    assert isinstance(res, pd.DataFrame)
    assert res.shape[0] == 1
    assert list(res.columns.names) == ["P", "K"]
    params = [(p, k) for p in ["mu", "sigma", "A"] for k in ["value", "uncertainty"]]
    assert list(res.columns) == params + QUALITY


def test_results_hold_the_recovered_parameters_and_ok_status():
    """A noise-free Gaussian's row recovers mu=2, sigma=0.5, A=10 with status ok.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)
    fit.make_fit()
    row = fit.results.iloc[0]

    values = row.xs("value", level="K").astype(float).to_numpy()
    assert values == noise_free([2.0, 0.5, 10.0])  # the generating parameters
    assert row[("status", "")] == "ok"
    assert row[("nobs", "")] == x.size  # every point is used
    assert row[("dof", "")] == x.size - 3  # three parameters
    assert row[("rsq", "")] == noise_free(1.0)  # a perfect fit
    assert fit.error is None


def test_popt_and_psigma_read_the_results_table():
    """``popt``, ``psigma`` and ``chisq_dof`` are read from the table.

    ON FAILURE: the code is wrong.
    """
    rng = np.random.default_rng(7)
    x = np.linspace(0.0, 10.0, 30)
    fit = Line(x, 3.0 * x - 1.0 + rng.normal(0, 0.2, x.size))
    fit.make_fit()
    row = fit.results.iloc[0]
    for name in fit.argnames:
        assert fit.popt[name] == exact(row[(name, "value")])
        assert fit.psigma[name] == exact(row[(name, "uncertainty")])
    linear, robust = fit.chisq_dof
    assert linear == exact(row[("chisq_dof", "linear")])
    assert robust == exact(row[("chisq_dof", "robust")])


def test_a_fit_with_too_few_points_raises_and_leaves_a_nan_row_with_its_status():
    """Two points cannot fit three parameters: make_fit raises and records why.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0])
    fit = Gaussian(x, np.ones_like(x))
    with pytest.raises(InsufficientDataError):
        fit.make_fit()

    row = fit.results.iloc[0]
    assert np.isnan(row.xs("value", level="K").astype(float)).all()
    assert np.isnan(row.xs("uncertainty", level="K").astype(float)).all()
    assert row[("status", "")] == "InsufficientDataError"
    assert row[("nobs", "")] == 2  # the observations are still counted
    assert isinstance(fit.error, InsufficientDataError)


def test_a_failed_fit_evaluates_to_nans_the_shape_of_x():
    """Calling a failed fit returns NaN in ``x``'s shape, as the class docstring says.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0])
    fit = Gaussian(x, np.ones_like(x))
    with pytest.raises(InsufficientDataError):
        fit.make_fit()
    out = fit(np.linspace(0, 1, 7))
    assert out.shape == (7,)
    assert np.isnan(out).all()
    assert all(np.isnan(v) for v in fit.popt.values())


def test_an_optimizer_failure_is_recorded_as_fit_failed():
    """One function evaluation stops the optimizer; the status names FitFailedError.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)
    with pytest.raises(FitFailedError):
        fit.make_fit(max_nfev=1)
    assert fit.results.loc[:, ("status", "")].item() == "FitFailedError"
    assert isinstance(fit.error, FitFailedError)


def test_a_subclass_precheck_failure_is_recorded_too():
    """PowerLawOffCenter's own bound check fails through the same status row.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(1.0, 5.0, 20)
    fit = PowerLawOffCenter(x, 2.0 * x**1.5)
    with pytest.raises(ValueError, match="needs x0 below"):
        fit.make_fit(bounds=([-np.inf, -np.inf, 2.0], [np.inf, np.inf, np.inf]))
    assert fit.results.loc[:, ("status", "")].item() == "ValueError"


def test_a_failed_refit_replaces_a_successful_one():
    """A later failure shows as failed; a later success clears it.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)
    fit.make_fit()
    with pytest.raises(FitFailedError):
        fit.make_fit(max_nfev=1)
    assert fit.results.loc[:, ("status", "")].item() == "FitFailedError"
    assert np.isnan(fit.popt["mu"])

    fit.make_fit()
    assert fit.results.loc[:, ("status", "")].item() == "ok"
    assert fit.error is None
    assert fit.popt["mu"] == noise_free(2.0)  # the generating mu


def test_results_before_a_fit_raise_not_fitted():
    """Before ``make_fit`` there is no table: ``results`` raises NotFittedError.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.fitfunctions.core import NotFittedError

    x, y = _gaussian()
    with pytest.raises(NotFittedError, match="make_fit"):
        Gaussian(x, y).results


def test_two_fits_compare_by_concatenating_their_tables():
    """Tables from two setups concatenate into one frame keyed by setup.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    whole = Gaussian(x, y)
    whole.make_fit()
    core = Gaussian(x, y, xmin=1.0, xmax=3.0)
    core.make_fit()

    cmp = pd.concat({"whole": whole.results, "core": core.results}, names=["setup"])
    assert cmp.shape[0] == 2
    assert list(cmp.columns) == list(whole.results.columns)
    nobs = cmp.loc[:, ("nobs", "")].droplevel(-1)
    assert nobs["whole"] == x.size
    assert nobs["core"] == ((x >= 1.0) & (x <= 3.0)).sum()  # the xmin/xmax window


def test_combined_popt_psigma_is_gone():
    """``results`` replaces ``combined_popt_psigma``: one table, one name.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)
    fit.make_fit()
    assert "combined_popt_psigma" not in dir(fit)
    assert "results" in dir(fit)


@pytest.mark.xfail(strict=True, reason="_calc_rsq runs outside make_fit's try")
def test_a_failure_computing_rsq_is_recorded_as_a_failed_fit():
    """R² is part of the fit: a failure computing it is recorded like the others.

    Chosen input: ``_calc_rsq`` replaced by one raising RuntimeError, one of
    the failures make_fit records.

    ON FAILURE: the code is wrong.
    """
    x, y = _gaussian()
    fit = Gaussian(x, y)

    def fail(popt):
        raise RuntimeError("rsq")

    fit._calc_rsq = fail
    with pytest.raises(RuntimeError, match="rsq"):
        fit.make_fit()
    assert fit.results.loc[:, ("status", "")].item() == "RuntimeError"
    assert isinstance(fit.error, RuntimeError)
