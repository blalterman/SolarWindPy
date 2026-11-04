# Spent-When: PERMANENT(the hinge fit functions stop sharing one guess_h keyword)
# Supersedes: none
"""Contract tests for the one hinge guess shared by every hinge class.

Every hinge class takes ``guess_h=None``: the x of the hinge its estimate
splits the data at. None means the split is estimated from the data, so no
class carries a hardcoded solar-wind default. A full start goes through
``make_fit(p0=...)``, as in every family.
"""

import numpy as np
import pytest

from solarwindpy.fitfunctions import hinge
from tests.tolerances import noise_free


HINGES = [
    hinge.HingeSaturation,
    hinge.TwoLine,
    hinge.Saturation,
    hinge.HingeMin,
    hinge.HingeMax,
    hinge.HingeAtPoint,
]

# Two lines meeting at the hinge (5, 10): slope 2, then slope -1.
X = np.linspace(0.0, 15.0, 100)
MIN_LINES = np.minimum(2.0 * X, -(X - 15.0))
# A V opening upward, for HingeMax: slopes -2 then 2, meeting at (5, -10).
MAX_LINES = np.maximum(-2.0 * X, 2.0 * (X - 10.0))


@pytest.mark.parametrize("cls", HINGES, ids=lambda c: c.__name__)
def test_every_hinge_takes_guess_h_and_defaults_it_to_none(cls):
    """``guess_h`` is the one guess keyword; None is its default.

    ON FAILURE: the code is wrong.
    """
    assert cls(X, MIN_LINES).guess_h is None
    assert cls(X, MIN_LINES, guess_h=5.0).guess_h == 5.0


@pytest.mark.parametrize("cls", HINGES, ids=lambda c: c.__name__)
def test_the_old_guess_keywords_are_refused(cls):
    """``guess_xs``, ``guess_xh`` and ``guess_yh`` are gone: one name per concept.

    ON FAILURE: the code is wrong.
    """
    for old in ("guess_xs", "guess_xh", "guess_yh"):
        with pytest.raises(TypeError, match=old):
            cls(X, MIN_LINES, **{old: 5.0})
    fit = cls(X, MIN_LINES, guess_h=5.0)
    for gone in ("guess_xs", "guess_xh", "saturation_guess"):
        assert gone not in dir(fit)


@pytest.mark.parametrize("cls", HINGES, ids=lambda c: c.__name__)
def test_no_guess_splits_the_data_at_its_median_x(cls):
    """With ``guess_h=None`` the estimate splits at the median used x.

    ON FAILURE: the code is wrong.
    """
    y = MAX_LINES if cls is hinge.HingeMax else MIN_LINES
    estimated = cls(X, y).p0
    explicit = cls(X, y, guess_h=float(np.median(X))).p0
    np.testing.assert_array_equal(estimated, explicit)


@pytest.mark.parametrize(
    "cls, y, hinge_x",
    [
        (hinge.HingeSaturation, MIN_LINES, lambda f: f.popt["h"]),
        (hinge.TwoLine, MIN_LINES, lambda f: f.h),
        (hinge.Saturation, MIN_LINES, lambda f: f.popt["h"]),
        (hinge.HingeMin, MIN_LINES, lambda f: f.popt["h"]),
        (hinge.HingeMax, MAX_LINES, lambda f: f.popt["h"]),
        (hinge.HingeAtPoint, MIN_LINES, lambda f: f.popt["h"]),
    ],
    ids=lambda v: getattr(v, "__name__", ""),
)
def test_a_hinge_with_no_guess_is_recovered(cls, y, hinge_x):
    """Without a guess, each class recovers the hinge at x = 5 from noise-free lines.

    ON FAILURE: the code is wrong.
    """
    fit = cls(X, y)
    fit.make_fit()
    assert hinge_x(fit) == noise_free(5.0)  # where the two lines meet


def test_hinge_saturation_estimates_yh_at_the_split():
    """HingeSaturation's start takes ``yh`` from the observation nearest the split.

    ON FAILURE: the code is wrong.
    """
    fit = hinge.HingeSaturation(X, MIN_LINES, guess_h=5.0)
    h, yh = fit.p0[:2]
    assert h == 5.0
    assert yh == MIN_LINES[np.argmin(np.abs(X - 5.0))]
