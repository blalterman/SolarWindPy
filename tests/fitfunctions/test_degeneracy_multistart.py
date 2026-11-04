# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Degeneracy warnings and multi-start fits of ``FitFunction.make_fit``.

A fit whose covariance holds a non-finite entry, or whose parameters are
correlated beyond ``degeneracy_threshold``, warns ``FitDegeneracyWarning``
naming the pairs and lists them in ``degenerate``. ``make_fit(starts=...)``
fits from several initial guesses and keeps the lowest
``least_squares`` cost, recording every start in ``multistart``.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeWarning

from solarwindpy.fitfunctions import trend_fits
from solarwindpy.fitfunctions.composite import GaussianPlusHeavySide
from solarwindpy.fitfunctions.core import FitDegeneracyWarning, FitFunction
from solarwindpy.fitfunctions.gaussians import Gaussian
from solarwindpy.fitfunctions.hinge import HingeSaturation
from solarwindpy.fitfunctions.lines import Line
from tests.tolerances import exact, noise_free


def _cosine(x, A, k):
    return A * np.cos(k * x)


class _Cosine(FitFunction):
    """``A cos(k x)`` started at ``A=1, k=1``: its cost has many minima in ``k``."""

    @property
    def function(self):
        return _cosine

    @property
    def p0(self):
        return [1.0, 1.0]

    @property
    def TeX_function(self):
        return r"f(x)=A \cos(k x)"


class _StrictLine(Line):
    """A line whose class threshold is 0.99, to show the class attribute is read."""

    degeneracy_threshold = 0.99


# Noise-free A cos(k x) with A=2, k=1.7. From the class's start k=1 the fit
# stops in a local minimum; a start at k=1.5 reaches the truth.
_COS_X = np.linspace(0, 10, 201)
_COS_TRUTH = {"A": 2.0, "k": 1.7}
_COS_Y = _cosine(_COS_X, **_COS_TRUTH)


def _one_branch_hinge():
    """A HingeSaturation fit to data on its rising branch only.

    y = 2 (x - 1) for 2 <= x <= 10, with the hinge guessed at (20, 38), on
    that line beyond the data. Every hinge on the line fits equally well, so
    xh and yh trade off exactly.
    """
    x = np.linspace(2, 10, 17)
    return HingeSaturation(x, 2 * (x - 1), guess_xh=20, guess_yh=38)


def _line_on(lo, seed):
    """A line 3x + 2 sampled on [lo, lo + 1] with 0.1 noise, weighted by it."""
    x = np.linspace(lo, lo + 1, 21)
    y = 3 * x + 2 + np.random.default_rng(seed).normal(0, 0.1, x.size)
    return Line(x, y, weights=np.full(x.size, 0.1))


def _correlation(fit, a, b):
    """Correlation of parameters ``a`` and ``b`` from the fit's ``pcov``."""
    i, j = fit.argnames.index(a), fit.argnames.index(b)
    c = fit.pcov
    return c[i, j] / np.sqrt(c[i, i] * c[j, j])


def test_hinge_with_data_on_one_branch_warns_that_xh_and_yh_are_degenerate():
    """Data on one hinge branch leave xh and yh trading off: a warning names them.

    The pair's correlation is 1 (the identity of a rank-deficient covariance),
    and ``degenerate`` lists the same pair.

    ON FAILURE: the code is wrong.
    """
    fit = _one_branch_hinge()
    with pytest.warns(FitDegeneracyWarning) as record:
        fit.make_fit()

    message = str(record[0].message)
    assert "xh and yh are degenerate (correlation 1.000000)" in message
    assert "their uncertainties are not meaningful" in message
    assert [pair[:2] for pair in fit.degenerate] == [("xh", "yh")]
    assert abs(fit.degenerate[0][2]) == noise_free(1.0)


def test_well_constrained_fit_does_not_warn_degeneracy():
    """A line sampled across x = 0 constrains slope and intercept: no warning.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(-0.5, seed=0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit()
    assert fit.degenerate == []


def test_degeneracy_warning_can_be_escalated_after_the_fit_is_stored():
    """Escalated to an error, the warning raises, and the fit is still stored.

    ON FAILURE: the code is wrong.
    """
    fit = _one_branch_hinge()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        with pytest.raises(FitDegeneracyWarning, match="xh and yh"):
            fit.make_fit()
    # The rising line y = 2 (x - 1) crosses zero at x1 = 1 (chosen input).
    assert fit.popt["x1"] == noise_free(1.0)
    assert [pair[:2] for pair in fit.degenerate] == [("xh", "yh")]


def test_degeneracy_warning_is_not_a_numpy_floating_point_warning():
    """Escalating ``RuntimeWarning`` (NumPy's floating-point warnings) leaves it a warning.

    ON FAILURE: the code is wrong.
    """
    assert not issubclass(FitDegeneracyWarning, RuntimeWarning)
    fit = _one_branch_hinge()
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with pytest.warns(FitDegeneracyWarning, match="xh and yh"):
            fit.make_fit()


def test_non_finite_covariance_warns_degeneracy():
    """Two points fix a line with no degree of freedom: pcov is infinite.

    ON FAILURE: the code is wrong.
    """
    fit = Line(np.array([0.0, 1.0]), np.array([2.0, 5.0]))
    with pytest.warns(FitDegeneracyWarning, match="m and b have a non-finite"):
        with pytest.warns(OptimizeWarning):
            fit.make_fit()
    assert [pair[:2] for pair in fit.degenerate] == [("m", "b")]
    assert np.isnan(fit.degenerate[0][2])


def test_degeneracy_is_none_before_a_fit():
    """``degenerate`` and ``multistart`` are None before ``make_fit``.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(-0.5, seed=0)
    assert fit.degenerate is None
    assert fit.multistart is None


def test_line_far_from_zero_separates_the_thresholds():
    """On x in [2, 3], slope and intercept correlate between 0.99 and 0.999.

    ON FAILURE: the fixture no longer separates the default threshold from
    0.99; fix the fixture.
    """
    fit = _line_on(2, seed=1)
    fit.make_fit()
    assert 0.99 < abs(_correlation(fit, "m", "b")) < 0.999


def test_degeneracy_threshold_keyword_sets_the_correlation_that_warns():
    """The default 0.999 accepts the fit; ``degeneracy_threshold=0.99`` warns.

    The warning prints the correlation computed from ``pcov``.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(2, seed=1)
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit()
    assert fit.degenerate == []

    with pytest.warns(FitDegeneracyWarning) as record:
        fit.make_fit(degeneracy_threshold=0.99)
    corr = _correlation(fit, "m", "b")
    assert f"m and b are degenerate (correlation {corr:.6f})" in str(record[0].message)
    assert fit.degenerate == [("m", "b", exact(corr))]


def test_degeneracy_threshold_class_attribute_is_the_default():
    """A subclass's ``degeneracy_threshold`` applies; the keyword overrides it.

    ON FAILURE: the code is wrong.
    """
    assert FitFunction.degeneracy_threshold == 0.999
    x = np.linspace(2, 3, 21)
    y = 3 * x + 2 + np.random.default_rng(1).normal(0, 0.1, x.size)

    fit = _StrictLine(x, y, weights=np.full(x.size, 0.1))
    with pytest.warns(FitDegeneracyWarning, match="m and b are degenerate"):
        fit.make_fit()

    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit(degeneracy_threshold=0.999)
    assert fit.degenerate == []


@pytest.mark.parametrize("threshold", [-0.1, 1.5, np.nan])
def test_degeneracy_threshold_outside_zero_to_one_raises(threshold):
    """A threshold that is not a correlation from 0 to 1 raises ValueError.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(-0.5, seed=0)
    with pytest.raises(ValueError, match="degeneracy_threshold"):
        fit.make_fit(degeneracy_threshold=threshold)


def test_cosine_default_start_stops_in_a_local_minimum():
    """From k=1 the fit misses k=1.7, with a nonzero cost.

    ON FAILURE: the fixture no longer separates the default start from the
    multi-start fit; fix the fixture.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    fit.make_fit()
    assert abs(fit.popt["k"] - _COS_TRUTH["k"]) > 0.5
    assert fit.fit_result.cost > 1


def test_starts_recover_the_global_minimum():
    """``starts={"k": [...]}`` keeps the start with the lowest cost.

    The kept fit recovers the generating parameters, its cost is the lowest
    of the starts, and ``multistart`` records each start (the class's ``A``
    with each listed ``k``) and its cost.

    ON FAILURE: the code is wrong.
    """
    default = _Cosine(_COS_X, _COS_Y)
    default.make_fit()

    fit = _Cosine(_COS_X, _COS_Y)
    fit.make_fit(starts={"k": [1.0, 1.5, 2.0]})

    assert fit.popt == noise_free(_COS_TRUTH)
    assert fit.fit_result.cost < default.fit_result.cost

    info = fit.multistart
    assert info.starts["k"].to_numpy() == exact([1.0, 1.5, 2.0])
    assert info.starts["A"].to_numpy() == exact([1.0, 1.0, 1.0])
    assert info.cost[info.best] == exact(fit.fit_result.cost)
    assert info.cost[info.best] == exact(info.cost.min())
    # The first start is the class's own start, k=1.
    assert info.cost[0] == exact(default.fit_result.cost)
    assert fit.initial_guess_info["k"].p0 == exact(info.starts["k"][info.best])


def test_starts_as_a_list_of_dicts_override_named_parameters():
    """Each dict in a list of starts overrides only the parameters it names.

    ON FAILURE: the code is wrong.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    fit.make_fit(starts=[{"k": 1.0}, {"A": 2.5, "k": 1.6}])

    assert fit.multistart.starts["A"].to_numpy() == exact([1.0, 2.5])
    assert fit.multistart.starts["k"].to_numpy() == exact([1.0, 1.6])
    assert fit.multistart.best == 1
    assert fit.popt == noise_free(_COS_TRUTH)


def test_starts_dict_values_are_zipped_not_crossed():
    """Two parameters in a starts dict give one start per position.

    ON FAILURE: the code is wrong.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    fit.make_fit(starts={"A": [1.0, 3.0], "k": [1.0, 1.5]})
    assert fit.multistart.starts["A"].to_numpy() == exact([1.0, 3.0])
    assert fit.multistart.starts["k"].to_numpy() == exact([1.0, 1.5])


def _gaussian():
    """A Gaussian with mu=1, sigma=0.8, A=3 and seeded noise."""
    rng = np.random.default_rng(0)
    x = np.linspace(-5, 5, 100)
    y = 3 * np.exp(-0.5 * ((x - 1) / 0.8) ** 2) + rng.normal(0, 0.1, x.size)
    return Gaussian(x, y)


def test_default_fit_is_unchanged_by_starts_none_or_the_default_start():
    """``starts=None`` and one start at the class's ``p0`` match the plain fit bit for bit.

    ON FAILURE: the code is wrong.
    """
    plain = _gaussian()
    plain.make_fit()
    assert plain.multistart is None

    none = _gaussian()
    none.make_fit(starts=None)
    assert none.multistart is None

    one = _gaussian()
    one.make_fit(starts=[{}])
    assert one.multistart.best == 0

    for other in (none, one):
        assert np.array_equal(list(other.popt.values()), list(plain.popt.values()))
        assert np.array_equal(list(other.psigma.values()), list(plain.psigma.values()))
        assert np.array_equal(other.pcov, plain.pcov)
        assert other.fit_result.cost == plain.fit_result.cost


def test_failed_starts_are_skipped():
    """A start whose fit raises is skipped, its cost recorded as NaN.

    ON FAILURE: the code is wrong.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    fit.make_fit(starts={"k": [np.nan, 1.5]})
    assert np.isnan(fit.multistart.cost[0])
    assert fit.multistart.best == 1
    assert fit.popt == noise_free(_COS_TRUTH)


def test_all_starts_failing_raises_the_last_error():
    """When every start fails, the last start's error is raised or returned.

    ON FAILURE: the code is wrong.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    with pytest.raises(ValueError, match="k=inf"):
        fit.make_fit(starts={"k": [np.nan, np.inf]})

    error = fit.make_fit(return_exception=True, starts={"k": [np.nan, np.inf]})
    assert isinstance(error, ValueError)
    assert "k=inf" in str(error)


@pytest.mark.parametrize(
    "starts, match",
    [
        ({"q": [1.0]}, r"\['q'\]"),
        ({"A": [1.0, 2.0], "k": [1.0]}, "same length"),
        ([], "no start"),
    ],
)
def test_malformed_starts_raise_value_error(starts, match):
    """An unknown name, unequal lengths, or no start raises ValueError.

    ON FAILURE: the code is wrong.
    """
    fit = _Cosine(_COS_X, _COS_Y)
    with pytest.raises(ValueError, match=match):
        fit.make_fit(starts=starts)


def test_trend_fit_passes_starts_to_its_fits():
    """``TrendFit.make_1dfits`` and ``trend_func.make_fit`` accept ``starts``.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(-5, 5, 41)
    data = {
        pd.Interval(0, 1): 3 * np.exp(-0.5 * ((x - 1) / 0.8) ** 2),
        pd.Interval(1, 2): 3 * np.exp(-0.5 * ((x - 2) / 0.8) ** 2),
        pd.Interval(2, 3): 3 * np.exp(-0.5 * ((x - 3) / 0.8) ** 2),
    }
    agged = pd.DataFrame(data, index=pd.IntervalIndex.from_breaks(np.append(x, 5.25)))
    tf = trend_fits.TrendFit(agged, Line)
    tf.make_ffunc1ds()
    tf.make_1dfits(starts={"mu": [0.0, 1.5]})
    assert len(tf.ffuncs) == 3
    for ffunc in tf.ffuncs:
        assert ffunc.multistart.starts["mu"].to_numpy() == exact([0.0, 1.5])

    tf.make_trend_func()
    tf.trend_func.make_fit(starts={"m": [0.0, 2.0]})
    assert tf.trend_func.multistart.starts["m"].to_numpy() == exact([0.0, 2.0])
    # The 1D fits recover mu = 1, 2, 3 at bin centres 0.5, 1.5, 2.5: m = 1.
    assert tf.trend_func.popt["m"] == noise_free(1.0)


def test_composite_scan_accepts_the_new_keywords():
    """GaussianPlusHeavySide's x0 scan passes neither new keyword to SciPy.

    ``starts`` applies to the refit after the scan: a start that does not
    name ``x0`` keeps the scanned step, here the gap midpoint 2.05 between
    the samples 2.0 and 2.1 that straddle the step.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0, 10, 101)
    truth = {"y0": 1.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    y = (
        truth["A"] * np.exp(-0.5 * ((x - truth["mu"]) / truth["sigma"]) ** 2)
        + truth["y1"] * (x < 2.05)
        + truth["y0"]
    )
    fit = GaussianPlusHeavySide(x, y)
    fit.make_fit(starts={"A": [3.0, 5.0]}, degeneracy_threshold=0.999)
    assert fit.multistart.starts["A"].to_numpy() == exact([3.0, 5.0])
    assert fit.popt["x0"] == noise_free(2.05)
    assert {k: fit.popt[k] for k in truth} == noise_free(truth)
