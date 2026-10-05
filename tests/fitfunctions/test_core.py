import numpy as np
import pandas as pd
import pytest

from scipy.optimize import OptimizeResult, least_squares

from solarwindpy.fitfunctions.core import (
    FitFunction,
    FitFailedError,
    InvalidParameterError,
    InsufficientDataError,
)
from solarwindpy.fitfunctions.plots import FFPlot
from solarwindpy.fitfunctions.tex_info import TeXinfo


def linear_function(x, m, b):
    return m * x + b


class LinearFit(FitFunction):
    @property
    def function(self):
        return linear_function

    @property
    def p0(self):
        # Use data-driven initial guess for robust convergence across platforms
        x, y = self.observations.used.x, self.observations.used.y
        if len(x) > 1:
            slope = (y[-1] - y[0]) / (x[-1] - x[0])
        else:
            slope = 1.0
        intercept = y.mean() - slope * x.mean()
        return [slope, intercept]

    @property
    def TeX_function(self):
        return "m x + b"


def test_mismatched_observation_lengths_raise_invalid_parameter_error():
    """``y`` or ``weights`` of a different length than ``x`` is rejected.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(InvalidParameterError, match="xobs and yobs"):
        LinearFit([0, 1], [1])
    with pytest.raises(InvalidParameterError, match="weights and xobs"):
        LinearFit([0, 1], [1, 2], weights=[1])


def test_raw_observations_are_the_inputs_as_arrays():
    """The raw observations are the given x, y and weights, unchanged.

    ON FAILURE: the code is wrong.
    """
    raw = LinearFit([0, 1], [1, 2], weights=[1, 1]).observations.raw
    assert np.array_equal(raw.x, np.array([0, 1]))
    assert np.array_equal(raw.y, np.array([1, 2]))
    assert np.array_equal(raw.w, np.array([1, 1]))


@pytest.mark.parametrize(
    "limits, expected",
    [
        ({"xmin": 0.5, "xmax": 1.5}, [1.0]),
        ({"xmax": 1.5}, [0.0, 1.0]),
        ({"xmin": 0.5}, [1.0, 2.0]),
    ],
    ids=["both", "xmax-only", "xmin-only"],
)
def test_x_limits_select_the_used_observations(limits, expected):
    """``xmin``/``xmax`` keep ``xmin <= x <= xmax``; a NaN ``x`` is never used.

    The input x = [0, 1, 2, NaN] is chosen so each limit drops a known sample.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, np.nan])
    lf = LinearFit(x, np.array([1.0, 2.0, 3.0, 4.0]), **limits)
    assert np.array_equal(lf.observations.used.x, np.array(expected))


def test_xoutside_excludes_the_open_interval():
    """``xoutside=(1, 3)`` drops only x = 2 from x = 0..4; the endpoints stay.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(5.0)
    assert np.array_equal(LinearFit(x, x).observations.used.x, x)
    lf = LinearFit(x, x, xoutside=(1, 3))
    assert np.array_equal(lf.observations.used.x, np.array([0.0, 1.0, 3.0, 4.0]))


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


@pytest.fixture
def line_with_outlier():
    """Weighted line ``y = 2x + 1`` on integer ``x`` with one +20 outlier.

    The outlier makes the robust (huber) and plain (linear) least-squares
    solutions differ, so the default ``loss`` is observable in ``popt``.
    """
    x = np.arange(10.0)
    y = 2.0 * x + 1.0
    y[7] += 20.0
    w = np.full_like(x, 2.0)
    return x, y, w


def _direct_least_squares(x, y, w, p0, **kwargs):
    """Solve the weighted problem with scipy directly, as ``curve_fit`` would."""

    def resid(p):
        return (linear_function(x, *p) - y) / w

    return least_squares(resid, p0, **kwargs).x


def test_make_fit_defaults_match_documented_least_squares_call(line_with_outlier):
    """make_fit's result equals scipy's least_squares with the documented defaults.

    The ``make_fit`` docstring lists method="trf", loss="huber",
    max_nfev=10000, f_scale=0.1, and weights act as ``sigma`` (residuals
    divided by ``w``). The same problem solved by calling scipy directly with
    those settings is the independent route. The outlier makes the huber and
    linear solutions differ by ~0.6 in slope, so a changed default loss fails.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    p0 = np.array(lf.p0)
    documented = _direct_least_squares(
        x, y, w, p0, method="trf", loss="huber", max_nfev=10000, f_scale=0.1
    )
    plain = _direct_least_squares(x, y, w, p0, method="trf", loss="linear")

    popt = np.array([lf.popt["m"], lf.popt["b"]])
    # rel=1e-6: noise-free comparison of two identical solver calls.
    assert popt == pytest.approx(documented, rel=1e-6, abs=0)
    # The fixture must separate huber from linear, else the check above is idle.
    assert popt != pytest.approx(plain, rel=1e-2, abs=0)


def test_make_fit_records_the_initial_guess_and_rejects_args(simple_linear_data):
    """After a fit ``initial_guess_info`` holds ``p0``; curve_fit's ``args`` is refused.

    ON FAILURE: the code is wrong.
    """
    x, y, w = simple_linear_data
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    guess = lf.initial_guess_info
    assert [guess["m"].p0, guess["b"].p0] == list(lf.p0)

    with pytest.raises(ValueError, match="'args' is not a supported keyword"):
        lf.make_fit(args=(1,))


def test_exact_line_fits_with_zero_uncertainty_and_chisq():
    """Three samples exactly on y = 2x + 1: popt is (2, 1); psigma and chi^2 vanish.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0])
    lf = LinearFit(x, 2.0 * x + 1.0)
    lf.make_fit()
    # Noise-free fit: rel=1e-6 is far above optimizer convergence, far below a bug.
    assert lf.popt == pytest.approx({"m": 2.0, "b": 1.0}, rel=1e-6, abs=0)
    # abs=1e-10: residuals of an exact fit are rounding error, so these are ~0.
    assert [lf.psigma["m"], lf.psigma["b"]] == pytest.approx([0, 0], abs=1e-10)
    assert lf.chisq_dof.linear == pytest.approx(0, abs=1e-10)
    assert lf.chisq_dof.robust == pytest.approx(0, abs=1e-10)


def test_make_fit_success_failure(simple_linear_data, small_n):
    """make_fit populates results on success and surfaces solver failure.

    Failure is real: ``max_nfev=1`` stops scipy before convergence, which
    make_fit reports as FitFailedError.

    ON FAILURE: the code is wrong.
    """
    x, y, w = simple_linear_data
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    assert isinstance(lf.fit_result, OptimizeResult)
    assert set(lf.popt) == {"m", "b"}
    assert set(lf.psigma) == {"m", "b"}
    assert lf.pcov.shape == (2, 2)
    assert lf.chisq_dof._fields == ("linear", "robust")
    assert isinstance(lf.plotter, FFPlot) and isinstance(lf.TeX_info, TeXinfo)

    x, y, w = small_n
    lf_small = LinearFit(x, y, weights=w)
    err = lf_small.make_fit(return_exception=True)
    assert isinstance(err, InsufficientDataError)

    x, y, w = simple_linear_data
    lf_fail = LinearFit(x, y, weights=w)
    err = lf_fail.make_fit(return_exception=True, max_nfev=1)
    assert isinstance(err, FitFailedError)
    assert "Optimal parameters not found" in str(err)
    with pytest.raises(FitFailedError, match="Optimal parameters not found"):
        lf_fail.make_fit(max_nfev=1)


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
    assert lf.chisq_dof._fields == ("linear", "robust")
    assert lf.dof == lf.observations.used.y.size - len(lf.p0)
    assert isinstance(lf.fit_result, OptimizeResult)
    assert lf.initial_guess_info["m"]._fields == ("p0", "bounds")
    assert lf.nobs == lf.observations.used.x.size
    assert isinstance(lf.plotter, FFPlot)
    assert set(lf.popt) == {"m", "b"}
    assert set(lf.psigma) == {"m", "b"}
    # combined_popt_psigma returns DataFrame; psigma_relative is trivially computable
    combined = lf.combined_popt_psigma
    assert isinstance(combined, pd.DataFrame)
    assert set(combined.columns) == {"popt", "psigma"}
    assert set(combined.index) == {"m", "b"}
    # Verify relative uncertainty is trivially computable from DataFrame
    psigma_relative = combined["psigma"] / combined["popt"]
    assert set(psigma_relative.index) == {"m", "b"}
    assert lf.pcov.shape == (2, 2)
    assert 0.0 <= lf.rsq <= 1.0
    assert lf.sufficient_data is True
    assert isinstance(lf.TeX_info, TeXinfo)


# ============================================================================
# Phase 6 Coverage Tests - Validated passing tests from temp file
# ============================================================================


class TestChisqDofBeforeFit:
    """Test chisq_dof property returns None before fit (lines 283-284)."""

    def test_chisq_dof_returns_none_before_fit(self, simple_linear_data):
        """Verify chisq_dof returns None when _chisq_dof attribute not set."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w)
        assert lf.chisq_dof is None


class TestInitialGuessInfoBeforeFit:
    """Test initial_guess_info property returns None before fit (lines 301-302)."""

    def test_initial_guess_info_returns_none_before_fit(self, simple_linear_data):
        """Verify initial_guess_info returns None when fit_bounds not set."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w)
        assert lf.initial_guess_info is None


class TestWeightShapeValidation:
    """Test weight shape validation in _clean_raw_obs (line 414)."""

    def test_weight_shape_mismatch_raises(self):
        """Verify InvalidParameterError when weights shape mismatches x shape."""
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([1.0, 2.0, 3.0])
        w = np.array([1.0, 1.0])  # Wrong shape

        with pytest.raises(
            InvalidParameterError, match="weights and xobs must have the same shape"
        ):
            LinearFit(x, y, weights=w)


class TestBoundsDictHandling:
    """A bounds dict keyed by parameter name constrains the fit."""

    def test_bounds_dict_constrains_parameter_and_is_recorded(self):
        """A binding upper bound on ``m`` given as a dict holds in ``popt``.

        Noise-free data from m=2, b=1 with ``m`` capped at 1.5: the optimum sits
        on the cap, and ``fit_bounds`` records the dict's limits per name.

        ON FAILURE: the code is wrong.
        """
        x = np.arange(10.0)
        lf = LinearFit(x, 2.0 * x + 1.0)
        # p0 must start inside the bounds; LinearFit's data-driven guess is m=2.
        lf.make_fit(p0=[1.0, 1.0], bounds={"m": (-10.0, 1.5), "b": (-5.0, 5.0)})

        # rel=1e-6: trf stops within its xtol of an active bound.
        assert lf.popt["m"] == pytest.approx(1.5, rel=1e-6, abs=0)
        assert tuple(lf.fit_bounds["m"]) == (-10.0, 1.5)
        assert tuple(lf.fit_bounds["b"]) == (-5.0, 5.0)


class TestCallableJacobian:
    """A callable jacobian is used in place of finite differences."""

    def test_callable_jac_is_used_and_weighted(self):
        """``res.jac`` is the caller's jacobian divided by the weights.

        The supplied jacobian is 3x the true one, so a finite-difference run
        would leave ``res.jac`` a factor 3 away. Weights of 2 act as ``sigma``,
        so each row is divided by 2 (curve_fit's transform). With loss="linear"
        and a model linear in its parameters, ``res.jac`` is that constant
        matrix.

        ON FAILURE: the code is wrong.
        """
        x = np.arange(10.0)
        w = np.full_like(x, 2.0)
        lf = LinearFit(x, 2.0 * x + 1.0, weights=w)

        def tripled_jac(x, m, b):
            return 3.0 * np.column_stack([x, np.ones_like(x)])

        lf.make_fit(jac=tripled_jac, loss="linear")
        expected = tripled_jac(x, 0.0, 0.0) / w[:, np.newaxis]
        # Exact: the same float operations on integer-valued inputs.
        np.testing.assert_array_equal(lf.fit_result.jac, expected)


class NeverEnoughData(LinearFit):
    """LinearFit whose ``sufficient_data`` override returns False.

    The base class raises from ``sufficient_data``; a subclass returning False
    instead must still stop the fit with InsufficientDataError.
    """

    @property
    def sufficient_data(self):
        return False


class InsufficientDataLeakedAsAssertion(AssertionError):
    """Raised by the test when make_fit lets a bare AssertionError escape."""


class TestMakeFitAssertionError:
    """A falsy ``sufficient_data`` becomes InsufficientDataError."""

    def test_make_fit_assertion_error_returned_as_insufficient_data(
        self, simple_linear_data
    ):
        """With return_exception=True the falsy check comes back converted.

        ON FAILURE: the code is wrong.
        """
        x, y, w = simple_linear_data
        lf = NeverEnoughData(x, y, weights=w)

        err = lf.make_fit(return_exception=True)
        assert isinstance(err, InsufficientDataError)
        assert "insufficient data to fit the model" in str(err)

    def test_make_fit_assertion_error_raised_as_insufficient_data(
        self, simple_linear_data
    ):
        """With return_exception=False the same InsufficientDataError is raised.

        ``return_exception`` chooses between returning and raising the
        exception, so both paths must carry the same type.

        ON FAILURE: the code is wrong.
        """
        x, y, w = simple_linear_data
        lf = NeverEnoughData(x, y, weights=w)

        try:
            lf.make_fit()
        except InsufficientDataError:
            return
        except AssertionError as e:
            raise InsufficientDataLeakedAsAssertion(repr(e)) from e
        pytest.fail("make_fit did not raise for insufficient data")


class TestAbsoluteSigmaNotImplemented:
    """Test absolute_sigma NotImplementedError (line 811)."""

    def test_make_fit_absolute_sigma_raises(self, simple_linear_data):
        """Verify make_fit raises NotImplementedError for absolute_sigma=True."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w)

        with pytest.raises(NotImplementedError, match="rescale fit errors"):
            lf.make_fit(absolute_sigma=True)


class TestResidualsAllOptions:
    """Test residuals method with all option combinations."""

    def test_residuals_use_all_true(self, simple_linear_data):
        """Verify residuals calculates for all original data when use_all=True."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w, xmin=0.2, xmax=0.8)
        lf.make_fit()

        r_used = lf.residuals(use_all=False)
        r_all = lf.residuals(use_all=True)

        assert len(r_all) > len(r_used)
        assert len(r_all) == len(x)

    def test_residuals_pct_true(self, simple_linear_data):
        """Verify residuals calculates percentage when pct=True."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w)
        lf.make_fit()

        r_abs = lf.residuals(pct=False)
        r_pct = lf.residuals(pct=True)

        assert not np.allclose(r_abs, r_pct)

    def test_residuals_pct_handles_zero_fitted(self):
        """Verify residuals handles division by zero in pct mode."""
        x = np.array([-1.0, 0.0, 1.0])
        y = np.array([-1.0, 0.0, 1.0])
        lf = LinearFit(x, y)
        lf.make_fit()

        r_pct = lf.residuals(pct=True)
        assert np.any(np.isnan(r_pct)) or np.allclose(r_pct, 0.0, atol=1e-10)

    def test_residuals_use_all_and_pct_together(self, simple_linear_data):
        """Verify residuals works with both use_all=True and pct=True."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w, xmin=0.2, xmax=0.8)
        lf.make_fit()

        r_all_pct = lf.residuals(use_all=True, pct=True)
        assert len(r_all_pct) == len(x)
