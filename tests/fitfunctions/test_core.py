import warnings

import numpy as np
import pandas as pd
import pytest

from scipy.linalg import cholesky, solve_triangular
from scipy.optimize import OptimizeResult, OptimizeWarning, curve_fit, least_squares

from solarwindpy.fitfunctions.core import (
    FitFunction,
    FitFailedError,
    InvalidParameterError,
    InsufficientDataError,
)
from solarwindpy.fitfunctions.plots import FFPlot
from solarwindpy.fitfunctions.tex_info import TeXinfo
from tests.tolerances import NOISE_FREE_REL, exact, noise_free


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
    assert popt == noise_free(documented)
    # The fixture must separate huber from linear (~0.6 in slope) by over
    # 1e4x the fit tolerance, else the check above is idle.
    gap = np.max(np.abs(popt / plain - 1))
    assert gap > 1e4 * NOISE_FREE_REL


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
    assert lf.popt == noise_free({"m": 2.0, "b": 1.0})
    # An exact fit leaves rounding only: zero on the scale of m = 2, y <= 5.
    assert [lf.psigma["m"], lf.psigma["b"]] == exact([0, 0], scale=2.0)
    assert lf.chisq_dof.linear == exact(0, scale=25.0)
    assert lf.chisq_dof.robust == exact(0, scale=25.0)


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
    """str names the model; calling evaluates m x + b at popt; properties hold.

    ON FAILURE: the code is wrong.
    """
    lf = fitted_linear
    s = str(lf)
    assert "LinearFit" in s and "m x + b" in s
    xnew = np.array([0.0, 0.5])
    ypred = lf(xnew)
    assert ypred == exact(lf.popt["m"] * xnew + lf.popt["b"])
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
        """``initial_guess_info`` is None on a fresh object that has not been fitted.

        ON FAILURE: the code is wrong -- an unfitted object reports a start.
        """
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

        assert lf.popt["m"] == noise_free(1.5)
        assert tuple(lf.fit_bounds["m"]) == (-10.0, 1.5)
        assert tuple(lf.fit_bounds["b"]) == (-5.0, 5.0)


class TestBoundsLowerUpper:
    """``_bounds_lower_upper`` broadcasts bounds with public NumPy, not scipy's private helper."""

    @pytest.mark.parametrize(
        "bounds, lower, upper",
        [
            pytest.param((-np.inf, np.inf), [-np.inf] * 2, [np.inf] * 2, id="scalar"),
            pytest.param(([0.0, -1.0], [2.0, 3.0]), [0.0, -1.0], [2.0, 3.0], id="list"),
            pytest.param(
                {"m": (0.0, 2.0), "b": (-1.0, 3.0)}, [0.0, -1.0], [2.0, 3.0], id="dict"
            ),
        ],
    )
    def test_bounds_broadcast_to_one_value_per_parameter(self, bounds, lower, upper):
        """Each form ``make_fit`` accepts gives writable lower and upper arrays of length n.

        ON FAILURE: the code is wrong.
        """
        lf = LinearFit(np.arange(5.0), np.arange(5.0))
        lb, ub = lf._bounds_lower_upper(bounds, 2)
        assert lb == exact(lower)
        assert ub == exact(upper)
        # Writable copies: PowerLawOffCenter.make_fit edits the upper bound.
        lb[0] = 7.0
        assert lb[0] == exact(7.0)

    def test_bound_of_the_wrong_length_raises(self):
        """A bound that does not broadcast to n values raises ValueError.

        ON FAILURE: the code is wrong.
        """
        lf = LinearFit(np.arange(5.0), np.arange(5.0))
        with pytest.raises(ValueError):
            lf._bounds_lower_upper(([0.0, 1.0, 2.0], np.inf), 2)

    def test_core_does_not_use_the_private_scipy_bounds_helper(self):
        """``core`` no longer imports ``scipy.optimize._lsq``'s ``prepare_bounds``.

        A private SciPy module can move or be renamed in any release.

        ON FAILURE: the code is wrong.
        """
        import solarwindpy.fitfunctions.core as core

        assert not hasattr(core, "prepare_bounds")


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
        """Percent residuals where the fit is zero are NaN, the rest zero.

        ON FAILURE: the code is wrong.
        """
        x = np.array([-1.0, 0.0, 1.0])
        y = np.array([-1.0, 0.0, 1.0])
        lf = LinearFit(x, y)
        lf.make_fit()

        r_pct = lf.residuals(pct=True)
        # An exact fit: zero on the scale of 100 percent.
        assert np.any(np.isnan(r_pct)) or r_pct == exact(0.0, scale=100.0)

    def test_residuals_use_all_and_pct_together(self, simple_linear_data):
        """Verify residuals works with both use_all=True and pct=True."""
        x, y, w = simple_linear_data
        lf = LinearFit(x, y, weights=w, xmin=0.2, xmax=0.8)
        lf.make_fit()

        r_all_pct = lf.residuals(use_all=True, pct=True)
        assert len(r_all_pct) == len(x)


# ============================================================================
# set_fit_obs selection edges
# ============================================================================


@pytest.mark.parametrize(
    "limits, expected",
    [
        ({"ymin": 20.0}, [1.0, 2.0, 3.0]),
        ({"ymax": 20.0}, [0.0, 1.0]),
        ({"youtside": (10.0, 30.0)}, [0.0, 2.0, 3.0]),
    ],
    ids=["ymin-only", "ymax-only", "youtside"],
)
def test_y_limits_select_the_used_observations(limits, expected):
    """``ymin``/``ymax`` keep ``ymin <= y <= ymax``; ``youtside`` drops the open interval.

    y = [10, 20, 30, 40] at x = [0, 1, 2, 3]. Each limit sits on a sample, so
    an ignored limit or an exclusive bound changes which x are used: ymin=20
    keeps y = 20, 30, 40; ymax=20 keeps y = 10, 20; youtside=(10, 30) drops
    only y = 20, the endpoints staying (class docstring: bounds inclusive).

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([10.0, 20.0, 30.0, 40.0])
    lf = LinearFit(x, y, **limits)
    assert np.array_equal(lf.observations.used.x, np.array(expected))


def test_wmin_alone_drops_smaller_weights():
    """``wmin`` with no ``wmax`` keeps ``w >= wmin``.

    w = [1, 2, 3, 4] with wmin=2: the sample with w = 1 is dropped and the
    one on the bound stays.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(4.0)
    lf = LinearFit(x, x, weights=np.array([1.0, 2.0, 3.0, 4.0]), wmin=2.0)
    assert np.array_equal(lf.observations.used.x, np.array([1.0, 2.0, 3.0]))


def test_logy_selects_on_the_uncertainty_of_log10_y():
    """With ``logy`` the weight limits apply to ``w / (y ln 10)``.

    ``w / (y ln 10)`` is the one-sigma uncertainty of log10(y) propagated from
    a one-sigma ``w`` on ``y`` (d log10 y = dy / (y ln 10)), as the class
    docstring states. With y = 1 and w = ln(10) * [0.5, 0.97, 1.0, 1.03, 2.0]
    that uncertainty is [0.5, 0.97, 1.0, 1.03, 2.0], so wmin=0.99, wmax=1.01
    keep only the middle sample. Any other logarithm base moves 1.0 out of
    the window (ln 10 / ln 11 = 0.96).

    ON FAILURE: the code is wrong.
    """
    x = np.arange(5.0)
    y = np.ones(5)
    w = np.log(10.0) * np.array([0.5, 0.97, 1.0, 1.03, 2.0])
    lf = LinearFit(x, y, weights=w, wmin=0.99, wmax=1.01, logy=True)
    assert np.array_equal(lf.observations.used.x, np.array([2.0]))


def test_set_fit_obs_selects_on_raw_weights_unless_logy_is_given():
    """Called without ``logy``, ``set_fit_obs`` applies ``wmin`` to the weights as given.

    y = 10 and w = [1, 2, 3] with wmin=1.5 keep w = 2 and 3. Under log
    selection the compared values would be w / (10 ln 10) < 0.14 and nothing
    would be kept, so the default is observable.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(3.0)
    y = np.full(3, 10.0)
    w = np.array([1.0, 2.0, 3.0])
    lf = LinearFit(x, y, weights=w)
    lf.set_fit_obs(x, y, w, wmin=1.5)
    assert np.array_equal(lf.observations.used.w, np.array([2.0, 3.0]))


# ============================================================================
# make_fit passes the caller's keywords to scipy
# ============================================================================


def test_make_fit_passes_the_method_to_scipy(line_with_outlier):
    """``method`` reaches least_squares, and "lm" fits as scipy's own "lm" does.

    scipy's "lm" accepts only loss="linear", so with the default huber loss
    method="lm" must raise ValueError while method="trf" on the same problem
    does not; only the method differs, so the error shows it reached scipy.
    With loss="linear" the result equals scipy's least_squares(method="lm")
    on the same weighted problem.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    lf = LinearFit(x, y, weights=w)
    lf.make_fit(method="trf")
    with pytest.raises(ValueError):
        lf.make_fit(method="lm")

    lf.make_fit(method="lm", loss="linear")
    expected = _direct_least_squares(x, y, w, np.array(lf.p0), method="lm")
    assert np.array([lf.popt["m"], lf.popt["b"]]) == noise_free(expected)


def test_make_fit_passes_f_scale_to_scipy(line_with_outlier):
    """A caller's ``f_scale`` replaces the documented default of 0.1.

    The independent route is scipy's least_squares with the documented
    defaults and f_scale=1.0. The outlier makes the huber solution depend on
    f_scale (slope moves ~3%), so a dropped f_scale fails the comparison.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    lf = LinearFit(x, y, weights=w)
    lf.make_fit(f_scale=1.0)
    p0 = np.array(lf.p0)
    defaults = dict(method="trf", loss="huber", max_nfev=10000)
    expected = _direct_least_squares(x, y, w, p0, f_scale=1.0, **defaults)
    default = _direct_least_squares(x, y, w, p0, f_scale=0.1, **defaults)

    assert np.array([lf.popt["m"], lf.popt["b"]]) == noise_free(expected)
    # The fixture must separate f_scale=1 from 0.1, else the check is idle.
    assert np.max(np.abs(expected / default - 1)) > 1e4 * NOISE_FREE_REL


def test_make_fit_passes_other_keywords_to_scipy(line_with_outlier):
    """Keywords make_fit does not name (here the three tolerances) reach least_squares.

    Tolerances of 0.5 stop scipy after a few evaluations, far from the
    converged solution (the intercept moves by about 200%). make_fit's result
    equals scipy's least_squares with the documented defaults and the same
    tolerances.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    loose = dict(ftol=0.5, xtol=0.5, gtol=0.5)
    lf = LinearFit(x, y, weights=w)
    lf.make_fit(**loose)
    p0 = np.array(lf.p0)
    defaults = dict(method="trf", loss="huber", max_nfev=10000, f_scale=0.1)
    expected = _direct_least_squares(x, y, w, p0, **defaults, **loose)
    converged = _direct_least_squares(x, y, w, p0, **defaults)

    assert np.array([lf.popt["m"], lf.popt["b"]]) == noise_free(expected)
    # The fixture must separate loose from default tolerances.
    assert np.max(np.abs(expected / converged - 1)) > 1e4 * NOISE_FREE_REL


# ============================================================================
# Covariance, parameter uncertainty and chi-square
# ============================================================================


def test_linear_loss_statistics_match_a_hand_computed_weighted_line():
    """Weighted least squares on four points gives the hand-computed popt, pcov and chi^2.

    x = [0, 1, 2, 3], y = [0, 1, 1, 3], every w = 2, loss="linear". By hand:
    xbar = 1.5, Sxx = 5, Sxy = 4.5, so m = 0.9 and b = 1.25 - 1.35 = -0.1.
    The residuals y - (m x + b) are [0.1, 0.2, -0.7, 0.4]; their sum of
    squares is 0.7, so with 2 degrees of freedom
    chi^2/dof = 0.7 / 2^2 / 2 = 0.0875, and with the linear loss the robust
    value 2 cost / dof is the same number. The covariance is
    (J^T J)^-1 s^2 with J = [x, 1] / w and s^2 = 0.0875 (curve_fit's
    absolute_sigma=False convention): (A^T A)^-1 = [[0.2, -0.3], [-0.3, 0.7]]
    times 4 x 0.0875 = 0.35, i.e. [[0.07, -0.105], [-0.105, 0.245]].

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([0.0, 1.0, 1.0, 3.0])
    lf = LinearFit(x, y, weights=np.full(4, 2.0))
    lf.make_fit(loss="linear")

    assert lf.popt == noise_free({"m": 0.9, "b": -0.1})
    assert lf.chisq_dof.linear == noise_free(0.0875)
    assert lf.chisq_dof.robust == noise_free(0.0875)
    assert lf.pcov == noise_free(np.array([[0.07, -0.105], [-0.105, 0.245]]))
    assert lf.psigma == noise_free({"m": np.sqrt(0.07), "b": np.sqrt(0.245)})


def test_huber_statistics_match_curve_fit_and_the_huber_cost(line_with_outlier):
    """With the default huber loss, pcov equals curve_fit's and chi^2 follows its definitions.

    scipy.optimize.curve_fit with the same sigma, loss and f_scale is the
    independent route to pcov (it scales by the robust cost, as make_fit
    documents). The robust chi^2/dof is 2 cost / dof, where scipy defines the
    huber cost as 0.5 f_scale^2 sum(rho(z)), z = (r / f_scale)^2,
    rho(z) = z for z <= 1 and 2 sqrt(z) - 1 otherwise. The linear chi^2/dof
    is sum((f(x) - y) / w)^2 / dof.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    lf = LinearFit(x, y, weights=w)
    lf.make_fit()
    p0 = np.array(lf.p0)
    _, pcov = curve_fit(
        linear_function,
        x,
        y,
        p0=p0,
        sigma=w,
        method="trf",
        loss="huber",
        f_scale=0.1,
        max_nfev=10000,
    )
    assert lf.pcov == noise_free(pcov)
    expected_psigma = {"m": np.sqrt(pcov[0, 0]), "b": np.sqrt(pcov[1, 1])}
    assert lf.psigma == noise_free(expected_psigma)

    r = (linear_function(x, lf.popt["m"], lf.popt["b"]) - y) / w
    dof = x.size - 2
    z = (r / 0.1) ** 2
    rho = np.where(z <= 1, z, 2 * np.sqrt(z) - 1)
    assert lf.chisq_dof.linear == noise_free((r**2).sum() / dof)
    assert lf.chisq_dof.robust == noise_free(0.1**2 * rho.sum() / dof)


def _sum_slope(x, a, b):
    return (a + b) * x


def _sum_slope_jac(x, a, b):
    return np.column_stack([x, x])


class SumSlopeFit(FitFunction):
    """A model whose two parameters enter only as their sum: rank-deficient."""

    @property
    def function(self):
        return _sum_slope

    @property
    def p0(self):
        return [1.0, 2.0]

    @property
    def TeX_function(self):
        return "(a + b) x"


def test_degenerate_parameters_get_the_pseudo_inverse_covariance():
    """A rank-1 jacobian gives the Moore-Penrose covariance, not a huge one.

    f = (a + b) x with the exact jacobian [x, x]. Its second singular value
    is zero up to rounding and must be discarded. Keeping only
    s0 = sqrt(2 sum x^2) with right vector (1, 1)/sqrt(2) gives
    pcov = s^2 [[1, 1], [1, 1]] / (4 sum x^2). By hand, in units of 1e3:
    x = [1, 2, 3, 4], y = [3, 6.5, 8.5, 12.5], best a + b = 91.5 / 30 = 3.05,
    residuals [-0.05, 0.4, -0.65, 0.3], sum of squares 0.675e6,
    s^2 = 0.675e6 / 2, and pcov = 0.3375e6 / 120e6 = 0.0028125 everywhere.
    curve_fit, given the same jacobian, agrees. The large x makes the first
    singular value large, so a threshold that does not scale with it would
    keep the rounding-level second one.

    ON FAILURE: the code is wrong.
    """
    x = 1e3 * np.array([1.0, 2.0, 3.0, 4.0])
    y = 1e3 * np.array([3.0, 6.5, 8.5, 12.5])
    fit = SumSlopeFit(x, y)
    # Killing the `eps / m` threshold mutant relies on a rounding-level second
    # singular value; that may not hold on another BLAS or platform.
    fit.make_fit(loss="linear", jac=_sum_slope_jac)

    assert fit.pcov == noise_free(np.full((2, 2), 0.0028125))
    _, pcov = curve_fit(
        _sum_slope, x, y, p0=[1.0, 2.0], jac=_sum_slope_jac, method="trf"
    )
    assert fit.pcov == noise_free(pcov)


def _ignores_parameters(x, a, b):
    return x + 0.0 * a + 0.0 * b


class FlatModelFit(FitFunction):
    """A model that does not depend on its parameters: an all-zero jacobian."""

    @property
    def function(self):
        return _ignores_parameters

    @property
    def p0(self):
        return [1.0, 2.0]

    @property
    def TeX_function(self):
        return "x"


def test_zero_singular_values_are_discarded():
    """A jacobian of zeros has only zero singular values, all discarded: pcov is 0.

    The code documents its covariance as the Moore-Penrose inverse
    "discarding zero singular values"; the pseudo-inverse of a zero matrix is
    zero. curve_fit, on the same model, returns the same zero matrix.

    ON FAILURE: the code is wrong.
    """
    x = np.arange(5.0)
    y = x + np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    fit = FlatModelFit(x, y)
    fit.make_fit()

    _, pcov = curve_fit(_ignores_parameters, x, y, p0=[1.0, 2.0], method="trf")
    assert pcov == exact(np.zeros((2, 2)), scale=1.0)
    assert fit.pcov == exact(pcov, scale=1.0)


def test_a_well_posed_fit_emits_no_optimize_warning(line_with_outlier):
    """More samples than parameters: make_fit raises no OptimizeWarning.

    ON FAILURE: the code is wrong.
    """
    x, y, w = line_with_outlier
    lf = LinearFit(x, y, weights=w)
    with warnings.catch_warnings():
        warnings.simplefilter("error", OptimizeWarning)
        lf.make_fit()
    assert np.isfinite(lf.pcov).all()


def test_as_many_samples_as_parameters_leaves_the_covariance_infinite():
    """Two samples for two parameters: pcov and psigma are +inf, with an OptimizeWarning.

    With no degree of freedom the residual variance is undefined. curve_fit's
    convention, which make_fit follows, fills pcov with +inf and warns; the
    linear chi^2/dof is +inf (division by zero dof) and the robust one NaN.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1.0])
    lf = LinearFit(x, 2.0 * x + 1.0)
    with pytest.warns(OptimizeWarning, match="could not be estimated"):
        lf.make_fit()

    assert lf.popt == noise_free({"m": 2.0, "b": 1.0})
    assert np.all(lf.pcov == np.inf)
    assert lf.psigma == {"m": np.inf, "b": np.inf}
    assert lf.chisq_dof.linear == np.inf
    assert np.isnan(lf.chisq_dof.robust)


# ============================================================================
# Correlated uncertainties: a full covariance matrix as ``weights``
# ============================================================================


@pytest.fixture
def correlated_line():
    """Six samples of y = 2x + 1 with fixed offsets and a full covariance matrix.

    Variances grow along x and neighbours correlate as 0.6^|i - j|, so the
    lower and upper Cholesky factors whiten the residuals differently.
    """
    x = np.arange(6.0)
    y = 2.0 * x + 1.0 + np.array([0.3, -0.2, 0.5, -0.4, 0.1, 0.2])
    sd = 0.5 + 0.2 * x
    lag = np.abs(np.subtract.outer(np.arange(6), np.arange(6)))
    cov = np.outer(sd, sd) * 0.6**lag
    return x, y, cov


def _gls(x, y, cov):
    """Generalised least squares (A^T C^-1 A)^-1 A^T C^-1 y and its r^T C^-1 r."""
    a = np.column_stack([x, np.ones_like(x)])
    cinv = np.linalg.inv(cov)
    beta = np.linalg.solve(a.T @ cinv @ a, a.T @ cinv @ y)
    r = a @ beta - y
    return beta, r @ cinv @ r


def _whitened_by(factor, lower, x, y):
    """Least squares on the line after solving ``factor z = r`` for the residuals."""
    a = np.column_stack([x, np.ones_like(x)])
    aw = solve_triangular(factor, a, lower=lower)
    yw = solve_triangular(factor, y, lower=lower)
    return np.linalg.lstsq(aw, yw, rcond=None)[0]


def test_correlated_fixture_separates_the_cholesky_orientations(correlated_line):
    """Whitening by L (L L^T = C) gives the GLS answer; whitening by U (U^T U = C) does not.

    Without this separation the covariance-weights test below could not tell
    the two orientations apart.

    ON FAILURE: the fixture no longer separates the lower from the upper
    Cholesky factor; fix the fixture.
    """
    x, y, cov = correlated_line
    gls, _ = _gls(x, y, cov)
    by_lower = _whitened_by(cholesky(cov, lower=True), True, x, y)
    by_upper = _whitened_by(cholesky(cov, lower=False), False, x, y)
    assert by_lower == noise_free(gls)
    assert np.max(np.abs(by_upper / gls - 1)) > 1e4 * NOISE_FREE_REL


@pytest.mark.xfail(
    strict=True,
    raises=InvalidParameterError,
    reason=(
        "FitFunction documents a 2-d `weights` as a covariance matrix, but "
        "_clean_raw_obs (solarwindpy/fitfunctions/core.py) requires "
        "weights.shape == xobs.shape; 'weights and xobs must have the same "
        "shape'. Behind it, set_fit_obs selects rows only (weights_raw[mask]) "
        "and _calc_popt_pcov_psigma_chisq divides residuals by the matrix "
        "(r /= sigma raises ValueError). Remove this marker when FitFunction "
        "accepts an (n, n) covariance for n observations through all three."
    ),
)
def test_a_covariance_matrix_as_weights_gives_the_gls_fit(correlated_line):
    """A full covariance matrix as ``weights`` fits as generalised least squares.

    The class docstring: "If 2-d, must be positive definite covariance
    matrix." With loss="linear" the fit must equal the closed-form GLS
    estimate (A^T C^-1 A)^-1 A^T C^-1 y; pcov must equal curve_fit's with
    the same full ``sigma``; the linear chi^2/dof is r^T C^-1 r / dof.

    ON FAILURE: (unexpected pass) FitFunction now accepts a covariance
    matrix; drop the xfail marker.
    """
    x, y, cov = correlated_line
    gls, chisq = _gls(x, y, cov)
    lf = LinearFit(x, y, weights=cov)
    lf.make_fit(loss="linear")

    assert np.array([lf.popt["m"], lf.popt["b"]]) == noise_free(gls)
    _, pcov = curve_fit(linear_function, x, y, sigma=cov)
    assert lf.pcov == noise_free(pcov)
    assert lf.chisq_dof.linear == noise_free(chisq / (x.size - 2))
