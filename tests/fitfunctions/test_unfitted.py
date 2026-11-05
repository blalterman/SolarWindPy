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


def _refit_raising(exc):
    """A Line fit once successfully, then refit with the optimizer raising ``exc``."""
    fit = _line()
    fit.make_fit()

    def fail(**kwargs):
        raise exc

    fit._run_least_squares = fail
    with pytest.raises(type(exc)):
        fit.make_fit()
    return fit


@pytest.mark.parametrize("name", [*READS, "error"])
def test_an_unexpected_refit_error_leaves_no_result_from_the_earlier_fit(name):
    """A refit raising outside the recorded failures leaves the fit unfitted.

    Chosen input: a TypeError, which make_fit does not record as a failed
    fit. The earlier success must not survive as status "ok" beside a missing
    optimizer result.

    ON FAILURE: the code is wrong.
    """
    fit = _refit_raising(TypeError("bad keyword"))
    reads = {**READS, "error": lambda f: f.error}
    with pytest.raises(NotFittedError, match="call make_fit first"):
        reads[name](fit)


class LeftHalfFitted(AssertionError):
    """A read answered after make_fit should have left the fit without that result."""


def _reads_that_answer(fit, names):
    """The reads in ``names`` that return instead of raising NotFittedError."""
    reads = {**READS, "error": lambda f: f.error}
    answered = []
    for name in names:
        try:
            reads[name](fit)
        except NotFittedError:
            continue
        answered.append(name)
    return answered


def _refit_with_step_raising(step, exc):
    """A Line fit once successfully, then refit with method ``step`` raising ``exc``.

    Replacing a method of the fit itself is not a boundary fake: it is the
    only way to make a step after the optimizer raise, which the brief for
    this test asks for.
    """
    fit = _line()
    fit.make_fit()

    def fail(*args, **kwargs):
        raise exc

    setattr(fit, step, fail)
    with pytest.raises(type(exc)):
        fit.make_fit()
    return fit


@pytest.mark.parametrize("step", ["_calc_rsq", "build_TeX_info", "build_plotter"])
def test_an_unexpected_error_after_the_optimizer_leaves_the_fit_unfitted(step):
    """A refit raising after the optimizer ran leaves every result unread.

    Chosen input: a TypeError, which make_fit does not record as a failed
    fit, from each step after the optimizer. The refit must not leave a
    status "ok" beside a missing TeX_info or plotter, nor bounds without a fit.

    ON FAILURE: the code is wrong.
    """
    fit = _refit_with_step_raising(step, TypeError(step))
    answered = _reads_that_answer(fit, [*READS, "error"])
    if answered:
        raise LeftHalfFitted(answered)


@pytest.mark.parametrize("step", ["_calc_rsq", "build_TeX_info", "build_plotter"])
def test_a_recorded_failure_after_the_optimizer_leaves_no_success_only_result(step):
    """A refit failing with a recorded error after the optimizer is a failed fit.

    Chosen input: a RuntimeError, one of the failures make_fit records, from
    each step after the optimizer. The status names it, and every result only
    a success produces raises.

    ON FAILURE: the code is wrong.
    """
    fit = _refit_with_step_raising(step, RuntimeError(step))
    if fit.results.loc[:, ("status", "")].item() != "RuntimeError":
        raise LeftHalfFitted(["results"])
    answered = _reads_that_answer(fit, SUCCESS_ONLY)
    if answered:
        raise LeftHalfFitted(answered)
