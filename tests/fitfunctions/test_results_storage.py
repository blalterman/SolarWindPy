# Spent-When: PERMANENT(FitFunction stops exposing its results as one table)
# Supersedes: none
"""Contract tests for how a fit stores its outcome and builds ``results``.

``make_fit`` stores the outcome as plain arrays and builds no table; the
``results`` table is built from them on first read, and a later
``make_fit`` replaces it. These tests pin that the table and the accessors
say the same thing for several fit classes and outcomes, that every read is
an independent copy, and that a table read before a refit does not outlive
it.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.fitfunctions.core import FitFailedError, InsufficientDataError
from solarwindpy.fitfunctions.exponentials import Exponential
from solarwindpy.fitfunctions.gaussians import Gaussian
from solarwindpy.fitfunctions.hinge import HingeAtPoint, HingeSaturation
from solarwindpy.fitfunctions.lines import Line
from tests.tolerances import exact, noise_free

X = np.linspace(0.0, 15.0, 61)

# (class, y, constructor keywords, generating parameters in argnames order).
# Each y is noise-free, so the fit recovers the generating parameters.
CASES = {
    "gaussian": (
        Gaussian,
        10.0 * np.exp(-0.5 * ((X - 7.0) / 2.0) ** 2),
        {},
        {"mu": 7.0, "sigma": 2.0, "A": 10.0},
    ),
    "line": (Line, 2.0 * X + 1.0, {}, {"m": 2.0, "b": 1.0}),
    "exponential": (
        Exponential,
        5.0 * np.exp(-0.3 * X),
        {},
        {"k": 0.3, "A": 5.0},
    ),
    "hinge_saturation": (
        HingeSaturation,
        np.where(X < 5.0, 2.0 * X, 10.0),
        {"guess_xh": 5.0},
        {"xh": 5.0, "yh": 10.0, "x1": 0.0, "m2": 0.0},
    ),
    "hinge_at_point": (
        HingeAtPoint,
        np.minimum(2.0 * X, -(X - 15.0)),
        {"guess_xh": 5.0},
        {"xh": 5.0, "yh": 10.0, "m1": 2.0, "m2": -1.0},
    ),
}


def _fit(case):
    cls, y, kwargs, truth = CASES[case]
    fit = cls(X, y, **kwargs)
    fit.make_fit()
    return fit, truth


def _failed_gaussian():
    """A Gaussian on two points: too few for three parameters."""
    fit = Gaussian(X[:2], X[:2])
    with pytest.raises(InsufficientDataError):
        fit.make_fit()
    return fit


def _quality(fit):
    return fit.results.iloc[0].loc[["chisq_dof", "rsq", "nobs", "dof", "status"]]


@pytest.mark.parametrize("case", list(CASES))
def test_results_hold_the_recovered_parameters_and_the_quality_accessors(case):
    """Each value column recovers its generating parameter; the rest match accessors.

    Every other column equals its accessor: psigma, chisq_dof, rsq, nobs, dof,
    status.

    ON FAILURE: the code is wrong.
    """
    fit, truth = _fit(case)
    res = fit.results

    assert list(res.columns) == list(fit.results_columns)
    assert list(res.columns.names) == ["P", "K"]
    row = res.iloc[0]
    for name in fit.argnames:
        assert row[(name, "value")] == noise_free(truth[name], scale=10.0)
        assert row[(name, "value")] == exact(fit.popt[name])
        assert row[(name, "uncertainty")] == exact(fit.psigma[name])
    assert row[("chisq_dof", "linear")] == exact(fit.chisq_dof.linear)
    assert row[("chisq_dof", "robust")] == exact(fit.chisq_dof.robust)
    assert row[("rsq", "")] == exact(fit.rsq)
    assert row[("nobs", "")] == X.size  # every chosen point is used
    assert row[("dof", "")] == X.size - len(truth)
    assert row[("status", "")] == "ok"


@pytest.mark.parametrize("case", list(CASES))
def test_results_columns_are_float_values_integer_counts_and_a_string_status(case):
    """Values and quality are float64, nobs and dof int64, status a string column.

    The status dtype is the one pandas gives a column of strings.

    ON FAILURE: the code is wrong.
    """
    fit, _ = _fit(case)
    dtypes = fit.results.dtypes
    counts = [("nobs", ""), ("dof", "")]
    floats = [c for c in fit.results_columns if c not in counts + [("status", "")]]
    assert (dtypes[floats] == np.float64).all()
    assert (dtypes[counts] == np.int64).all()
    assert dtypes[("status", "")] == pd.Series(["ok"]).dtype


def test_a_failed_fit_row_is_nan_with_integer_counts_and_the_failure_status():
    """A failed fit's row is NaN but for its counts, and its status names the failure.

    The values, uncertainties and quality are NaN; nobs and dof are the
    fit-time counts.

    ON FAILURE: the code is wrong.
    """
    fit = _failed_gaussian()
    row = fit.results.iloc[0]
    numbers = [c for c in fit.results_columns if c[0] not in ("nobs", "dof", "status")]
    assert row[numbers].astype(float).isna().all()
    assert row[("nobs", "")] == 2  # the two chosen points
    assert row[("dof", "")] == 2 - 3  # two points, three parameters
    assert row[("status", "")] == "InsufficientDataError"
    assert all(np.isnan(v) for v in fit.popt.values())
    assert all(np.isnan(v) for v in fit.psigma.values())
    assert np.isnan(fit.pcov).all() and fit.pcov.shape == (3, 3)


READ_ONLY = {
    "results": lambda f: f.results,
    "popt": lambda f: f.popt,
    "psigma": lambda f: f.psigma,
    "pcov": lambda f: f.pcov,
}


@pytest.mark.parametrize("name", list(READ_ONLY))
def test_each_result_read_is_a_copy_and_cannot_be_assigned(name):
    """Editing a read leaves the next read unchanged; assigning raises AttributeError.

    ON FAILURE: the code is wrong.
    """
    fit, _ = _fit("gaussian")
    read = READ_ONLY[name]
    first = read(fit)
    expected = read(fit)
    if isinstance(first, dict):
        first["mu"] = -1.0
        assert read(fit) == expected
    elif isinstance(first, pd.DataFrame):
        first.iloc[0, 0] = -1.0
        pd.testing.assert_frame_equal(read(fit), expected)
    else:
        first[...] = -1.0
        np.testing.assert_array_equal(read(fit), expected)
    with pytest.raises(AttributeError):
        setattr(fit, name, expected)


def test_a_table_read_before_a_refit_does_not_outlive_it():
    """Reading ``results`` and then refitting shows the refit, failed or ok.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.0, 4.0, 41)
    fit = Gaussian(x, 10.0 * np.exp(-0.5 * ((x - 2.0) / 0.5) ** 2))
    fit.make_fit()
    assert fit.results.loc[:, ("status", "")].item() == "ok"

    with pytest.raises(FitFailedError):
        fit.make_fit(max_nfev=1)
    assert fit.results.loc[:, ("status", "")].item() == "FitFailedError"
    assert fit.results.loc[:, ("mu", "value")].isna().item()

    fit.make_fit()
    assert fit.results.loc[:, ("status", "")].item() == "ok"
    assert fit.results.loc[:, ("mu", "value")].item() == noise_free(2.0)  # mu


def test_results_keep_the_fit_time_counts_after_new_observations():
    """``set_fit_obs`` after a fit leaves ``results`` describing that fit.

    ON FAILURE: the code is wrong.
    """
    fit, _ = _fit("line")
    fit.set_fit_obs(X[:10], 2.0 * X[:10] + 1.0, None)
    assert fit.nobs == 10
    assert fit.results.loc[:, ("nobs", "")].item() == X.size  # the fit's points
    assert fit.results.loc[:, ("dof", "")].item() == X.size - 2


class DataFrameBuiltError(AssertionError):
    """make_fit constructed a pandas DataFrame."""


@pytest.mark.parametrize("failing", [False, True], ids=["ok", "failed"])
def test_make_fit_constructs_no_dataframe(monkeypatch, failing):
    """``make_fit`` stores arrays and builds no DataFrame; ``results`` builds one.

    The author's ruling o16d asks for this pin directly, so the test counts
    ``pandas.DataFrame`` constructions, which the test standard otherwise
    leaves alone. Every construction still runs the real constructor.

    ON FAILURE: the code is wrong, unless the author withdraws ruling o16d.
    """
    built = []
    init = pd.DataFrame.__init__

    def counting_init(self, *args, **kwargs):
        built.append(1)
        init(self, *args, **kwargs)

    if failing:
        fit = Gaussian(X[:2], X[:2])
    else:
        fit = Gaussian(X, 10.0 * np.exp(-0.5 * ((X - 7.0) / 2.0) ** 2))
    monkeypatch.setattr(pd.DataFrame, "__init__", counting_init)
    try:
        fit.make_fit()
    except InsufficientDataError:
        assert failing
    if built:
        raise DataFrameBuiltError(f"make_fit built {len(built)} DataFrame(s)")

    fit.results
    assert built, "results built no table"


@pytest.mark.parametrize("case", list(CASES))
def test_results_quality_columns_satisfy_their_defining_identities(case):
    """On noisy unweighted data each quality column equals its definition.

    linear chisq_dof = sum(residuals**2) / dof; robust chisq_dof = twice the
    optimizer's cost over dof; rsq = 1 - SS_res / SS_tot; each uncertainty is
    the square root of the covariance diagonal. Noise keeps linear and robust
    apart, so a swap between them fails.

    ON FAILURE: the code is wrong.
    """
    cls, y, kwargs, _ = CASES[case]
    noise = np.random.default_rng(7).normal(0.0, 0.2, X.size)
    fit = cls(X, y + noise, **kwargs)
    fit.make_fit()
    row = fit.results.iloc[0]
    resid = fit.residuals()
    used_y = fit.observations.used.y
    dof = used_y.size - len(fit.argnames)

    assert row[("chisq_dof", "linear")] == exact((resid**2).sum() / dof)
    assert row[("chisq_dof", "robust")] == exact(2.0 * fit.fit_result.cost / dof)
    ss_tot = ((used_y - used_y.mean()) ** 2).sum()
    assert row[("rsq", "")] == exact(1.0 - (resid**2).sum() / ss_tot)
    sigma = np.sqrt(np.diag(fit.pcov))
    for name, s in zip(fit.argnames, sigma):
        assert row[(name, "uncertainty")] == exact(s)
