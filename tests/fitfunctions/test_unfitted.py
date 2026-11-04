# Spent-When: PERMANENT(FitFunction stops raising NotFittedError for a result read before make_fit)
# Supersedes: none
"""Contract tests for reading a fit result before, and after a failed, make_fit.

Every result raises one error before ``make_fit``: ``NotFittedError``, which
names ``make_fit``. After a failed fit, the values in ``results`` are NaN,
and what only a successful fit produces raises ``NotFittedError`` naming the
failure.
"""

import numpy as np
import pytest

from solarwindpy.fitfunctions.core import InsufficientDataError, NotFittedError
from solarwindpy.fitfunctions.lines import Line


# Each result, read from a fit.
READS = {
    "results": lambda f: f.results,
    "popt": lambda f: f.popt,
    "psigma": lambda f: f.psigma,
    "rsq": lambda f: f.rsq,
    "__call__": lambda f: f(np.arange(3.0)),
    "x_intercept": lambda f: f.x_intercept,
    "pcov": lambda f: f.pcov,
    "chisq_dof": lambda f: f.chisq_dof,
    "initial_guess_info": lambda f: f.initial_guess_info,
    "fit_result": lambda f: f.fit_result,
    "fit_bounds": lambda f: f.fit_bounds,
    "plotter": lambda f: f.plotter,
    "TeX_info": lambda f: f.TeX_info,
    "residuals": lambda f: f.residuals(),
}
# What only a successful fit produces.
SUCCESS_ONLY = ["initial_guess_info", "fit_result", "fit_bounds", "plotter", "TeX_info"]


def _line():
    x = np.arange(10.0)
    return Line(x, 2.0 * x + 1.0)


@pytest.mark.parametrize("name", list(READS))
def test_every_result_raises_not_fitted_before_make_fit(name):
    """Before ``make_fit``, each result raises NotFittedError naming make_fit.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(NotFittedError, match="make_fit"):
        READS[name](_line())


def test_error_raises_not_fitted_before_make_fit():
    """``error`` is a result too: before ``make_fit`` it raises, after one it is set.

    None before a fit would read as "no failure", the answer a success gives.

    ON FAILURE: the code is wrong.
    """
    fit = _line()
    with pytest.raises(NotFittedError, match="make_fit"):
        fit.error
    fit.make_fit()
    assert fit.error is None


def test_not_fitted_is_an_attribute_error():
    """NotFittedError is an AttributeError, so ``hasattr`` reports a missing result.

    ON FAILURE: the code is wrong.
    """
    assert issubclass(NotFittedError, AttributeError)
    assert not hasattr(_line(), "popt")


@pytest.mark.parametrize("name", SUCCESS_ONLY)
def test_after_a_failed_fit_success_only_results_raise_naming_the_failure(name):
    """A failed fit has no optimizer result: those reads name the failure.

    ON FAILURE: the code is wrong.
    """
    fit = Line(np.array([1.0]), np.array([2.0]))  # one point, two parameters
    with pytest.raises(InsufficientDataError):
        fit.make_fit()
    with pytest.raises(NotFittedError, match="InsufficientDataError"):
        READS[name](fit)


def test_after_a_failed_fit_the_values_are_nan():
    """A failed fit's values, covariance and quality are NaN, not missing.

    ON FAILURE: the code is wrong.
    """
    fit = Line(np.array([1.0]), np.array([2.0]))  # one point, two parameters
    with pytest.raises(InsufficientDataError):
        fit.make_fit()
    assert np.isnan(list(fit.popt.values())).all()
    assert np.isnan(fit.pcov).all() and fit.pcov.shape == (2, 2)
    assert np.isnan(fit.chisq_dof).all()
    assert np.isnan(fit.rsq)
