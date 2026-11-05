# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Degeneracy warnings of ``FitFunction.make_fit``.

A fit whose covariance holds a non-finite entry, or whose parameters are
correlated beyond ``degeneracy_threshold``, warns ``FitDegeneracyWarning``
naming the pairs, attributed to the caller's line, and lists them in
``degenerate``.
"""

import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeWarning

from solarwindpy.fitfunctions import trend_fits
from solarwindpy.fitfunctions.composite import GaussianPlusHeavySide
from solarwindpy.fitfunctions.core import (
    FitDegeneracyWarning,
    FitFunction,
    InsufficientDataError,
)
from solarwindpy.fitfunctions.hinge import HingeSaturation
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.fitfunctions.power_laws import PowerLawOffCenter
from tests.tolerances import exact, noise_free


class _StrictLine(Line):
    """A line whose class threshold is 0.99, to show the class attribute is read."""

    degeneracy_threshold = 0.99


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
    """``degenerate`` is None before ``make_fit``.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(-0.5, seed=0)
    assert fit.degenerate is None


def test_line_far_from_zero_separates_the_thresholds():
    """On x in [2, 3], slope and intercept correlate between 0.99 and 0.99999.

    ON FAILURE: the fixture no longer separates the default threshold from
    0.99; fix the fixture.
    """
    fit = _line_on(2, seed=1)
    fit.make_fit()
    assert 0.99 < abs(_correlation(fit, "m", "b")) < 0.99999


def test_degeneracy_threshold_keyword_sets_the_correlation_that_warns():
    """The default 0.99999 accepts the fit; ``degeneracy_threshold=0.99`` warns.

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
    assert FitFunction.degeneracy_threshold == 0.99999
    x = np.linspace(2, 3, 21)
    y = 3 * x + 2 + np.random.default_rng(1).normal(0, 0.1, x.size)

    fit = _StrictLine(x, y, weights=np.full(x.size, 0.1))
    with pytest.warns(FitDegeneracyWarning, match="m and b are degenerate"):
        fit.make_fit()

    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit(degeneracy_threshold=0.99999)
    assert fit.degenerate == []


def test_identifiable_power_law_warns_only_below_the_default_threshold():
    """A noise-free 16 / x^2 on x = 1, 2, 4, 8 is identifiable: no warning by default.

    Its A and x0 correlate near -0.99987 (from ``pcov``), above 0.999 and
    below the default 0.99999, so ``degeneracy_threshold=0.999`` warns.

    ON FAILURE: the code is wrong.
    """
    x = np.array([1.0, 2.0, 4.0, 8.0])
    fit = PowerLawOffCenter(x, 16.0 * x**-2.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit()
    assert fit.degenerate == []
    assert 0.999 < abs(_correlation(fit, "A", "x0")) < 0.99999

    with pytest.warns(FitDegeneracyWarning, match="A and x0 are degenerate"):
        fit.make_fit(degeneracy_threshold=0.999)


def test_degenerate_follows_the_class_threshold_after_the_fit():
    """``degenerate`` is recomputed from ``pcov`` with the current class threshold.

    ON FAILURE: the code is wrong.
    """

    class _Line(Line):
        degeneracy_threshold = 0.99999

    x = np.linspace(2, 3, 21)
    y = 3 * x + 2 + np.random.default_rng(1).normal(0, 0.1, x.size)
    fit = _Line(x, y, weights=np.full(x.size, 0.1))
    fit.make_fit()
    assert fit.degenerate == []

    # On x in [2, 3] slope and intercept correlate beyond 0.99.
    _Line.degeneracy_threshold = 0.99
    corr = _correlation(fit, "m", "b")
    assert fit.degenerate == [("m", "b", exact(corr))]


def test_degenerate_keeps_the_threshold_given_to_make_fit():
    """A ``degeneracy_threshold`` keyword outlasts a later class change.

    ON FAILURE: the code is wrong.
    """

    class _Line(Line):
        degeneracy_threshold = 0.99999

    x = np.linspace(2, 3, 21)
    y = 3 * x + 2 + np.random.default_rng(1).normal(0, 0.1, x.size)
    fit = _Line(x, y, weights=np.full(x.size, 0.1))
    with pytest.warns(FitDegeneracyWarning):
        fit.make_fit(degeneracy_threshold=0.99)
    _Line.degeneracy_threshold = 0.99999
    assert [pair[:2] for pair in fit.degenerate] == [("m", "b")]


def test_degeneracy_warning_names_exactly_the_degenerate_pairs():
    """The warning prints one sentence per pair ``degenerate`` lists, with its correlation.

    ``degeneracy_threshold=0`` flags every correlated pair of the Gaussian.

    ON FAILURE: the code is wrong.
    """
    fit, _ = _gaussian_plus_heavyside()
    with pytest.warns(FitDegeneracyWarning) as record:
        fit.make_fit(degeneracy_threshold=0)
    message = str(record[0].message)
    pairs = fit.degenerate
    assert len(pairs) > 1
    for a, b, c in pairs:
        assert f"{a} and {b} are degenerate (correlation {c:.6f})" in message
    assert message.count("are degenerate") == len(pairs)


def test_threshold_one_silences_correlations_but_not_non_finite_covariance():
    """At 1.0 an exact trade-off passes; an infinite covariance still warns.

    ON FAILURE: the code is wrong.
    """
    fit = _one_branch_hinge()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        fit.make_fit(degeneracy_threshold=1.0)
    assert fit.degenerate == []

    line = Line(np.array([0.0, 1.0]), np.array([2.0, 5.0]))
    with pytest.warns(FitDegeneracyWarning, match="non-finite covariance"):
        with pytest.warns(OptimizeWarning):
            line.make_fit(degeneracy_threshold=1.0)


@pytest.mark.parametrize("threshold", [-0.1, 1.5, np.nan])
def test_degeneracy_threshold_outside_zero_to_one_raises(threshold):
    """A threshold that is not a correlation from 0 to 1 raises ValueError.

    ON FAILURE: the code is wrong.
    """
    fit = _line_on(-0.5, seed=0)
    with pytest.raises(ValueError, match="degeneracy_threshold"):
        fit.make_fit(degeneracy_threshold=threshold)


def _gaussian_plus_heavyside():
    """A noise-free GaussianPlusHeavySide with its step between x = 2.0 and 2.1."""
    x = np.linspace(0, 10, 101)
    truth = {"y0": 1.0, "y1": 2.0, "mu": 5.0, "sigma": 1.0, "A": 4.0}
    y = (
        truth["A"] * np.exp(-0.5 * ((x - truth["mu"]) / truth["sigma"]) ** 2)
        + truth["y1"] * (x < 2.05)
        + truth["y0"]
    )
    return GaussianPlusHeavySide(x, y), truth


def test_composite_scan_accepts_the_threshold_keyword():
    """GaussianPlusHeavySide's x0 scan does not pass the threshold to SciPy.

    The scan picks the gap midpoint 2.05 between the samples 2.0 and 2.1
    that straddle the step.

    ON FAILURE: the code is wrong.
    """
    fit, truth = _gaussian_plus_heavyside()
    fit.make_fit(degeneracy_threshold=0.99999)
    assert fit.popt["x0"] == noise_free(2.05)
    assert {k: fit.popt[k] for k in truth} == noise_free(truth)


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(_one_branch_hinge, id="HingeSaturation"),
        pytest.param(lambda: _line_on(2, seed=1), id="Line"),
        pytest.param(lambda: _gaussian_plus_heavyside()[0], id="GaussianPlusHeavySide"),
    ],
)
def test_degeneracy_warning_points_at_the_caller(build):
    """The warning names this file, also when a subclass's make_fit calls the base's.

    ``degeneracy_threshold=0`` flags any correlated pair, so every fit warns.
    GaussianPlusHeavySide overrides ``make_fit`` and calls the base class's.

    ON FAILURE: the code is wrong.
    """
    fit = build()
    with pytest.warns(FitDegeneracyWarning) as record:
        fit.make_fit(degeneracy_threshold=0)
    assert [w.filename for w in record if w.category is FitDegeneracyWarning] == [
        __file__
    ]


def _trend_fit_with_degenerate_columns(skip=()):
    """A TrendFit of Gaussians: two good columns, two with three points, one empty.

    A Gaussian has three parameters, so a column with three finite points has
    no degree of freedom and an infinite covariance: degenerate on any
    platform. The empty column cannot be fitted at all. Columns in ``skip``
    are left out.
    """
    edges = np.linspace(-5, 5.25, 42)
    # TrendFit fits each column at its bin midpoints.
    x = 0.5 * (edges[1:] + edges[:-1])

    def gaussian(mu):
        return 3 * np.exp(-0.5 * ((x - mu) / 0.8) ** 2)

    def three_points(mu):
        y = np.full(x.size, np.nan)
        y[19:22] = gaussian(mu)[19:22]
        return y

    data = {
        pd.Interval(0, 1): gaussian(1.0),
        pd.Interval(1, 2): three_points(0.0),
        pd.Interval(2, 3): gaussian(2.0),
        pd.Interval(3, 4): three_points(0.5),
        pd.Interval(4, 5): np.full(x.size, np.nan),
    }
    index = pd.IntervalIndex.from_breaks(edges)
    data = {k: v for k, v in data.items() if k not in skip}
    tf = trend_fits.TrendFit(pd.DataFrame(data, index=index), Line)
    tf.make_ffunc1ds()
    return tf


GOOD = [pd.Interval(0, 1), pd.Interval(2, 3)]
DEGENERATE = [pd.Interval(1, 2), pd.Interval(3, 4)]
EMPTY = [pd.Interval(4, 5)]


def test_escalated_degeneracy_marks_trend_columns_as_failed_fits():
    """Escalated, both degenerate columns join ``bad_fits``; the good ones fit.

    ON FAILURE: the code is wrong.
    """
    tf = _trend_fit_with_degenerate_columns()
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        tf.make_1dfits()

    assert sorted(tf.bad_fits.index) == sorted(DEGENERATE + EMPTY)
    assert list(tf.ffuncs.index) == GOOD
    # The good columns recover the generating centres.
    assert [f.popt["mu"] for f in tf.ffuncs] == noise_free([1.0, 2.0])


def test_degenerate_trend_columns_stay_and_warn_by_default():
    """With default warning settings, degenerate columns stay in ``ffuncs``.

    ON FAILURE: the code is wrong.
    """
    tf = _trend_fit_with_degenerate_columns()
    with pytest.warns(FitDegeneracyWarning, match="non-finite covariance"):
        tf.make_1dfits()

    assert list(tf.bad_fits.index) == EMPTY
    assert list(tf.ffuncs.index) == sorted(GOOD + DEGENERATE)
    assert [bool(tf.ffuncs[k].degenerate) for k in DEGENERATE] == [True, True]


def test_escalated_degeneracy_is_raised_without_return_exception():
    """With ``return_exception=False`` the escalated warning is raised, as failures are.

    ON FAILURE: the code is wrong.
    """
    tf = _trend_fit_with_degenerate_columns(skip=EMPTY)
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        with pytest.raises(FitDegeneracyWarning, match="non-finite covariance"):
            tf.make_1dfits(return_exception=False)

    # Another failure still raises its own error.
    tf = _trend_fit_with_degenerate_columns(skip=DEGENERATE)
    with warnings.catch_warnings():
        warnings.simplefilter("error", FitDegeneracyWarning)
        with pytest.raises(InsufficientDataError):
            tf.make_1dfits(return_exception=False)
