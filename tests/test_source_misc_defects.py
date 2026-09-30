# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Defects found in the source-misc slice.

The slice is ``instabilities``, ``solar_activity``, ``tools``, ``scripts`` and
the package root. A fixed defect's test failed against the code before its
fix. A defect whose fix is blocked is a strict xfail naming what retires it.
"""

import functools
import inspect

import numpy as np
import pandas as pd
import pytest

from solarwindpy.solar_activity.base import ActivityIndicator
from solarwindpy.solar_activity.lisird.extrema_calculator import ExtremaCalculator
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC

# An 11-year sinusoid about 2.0, sampled daily. It starts on a rising crossing
# of its midline and spans exactly three periods, so every stretch between
# midline crossings holds one whole half-cycle and one extremum.
_PERIOD = pd.Timedelta(days=11 * 365.25)
_T0 = pd.Timestamp("1980-01-01")
_EPOCH = pd.date_range(_T0, _T0 + 3 * _PERIOD, freq="D")
_PHASE = 2 * np.pi * ((_EPOCH - _T0) / _PERIOD)
_INDEX = pd.Series(2.0 + np.sin(_PHASE), index=_EPOCH)

# ExtremaCalculator.set_threshold calls a threshold only if it is a
# types.FunctionType. numpy functions (np.nanmedian, the documented default)
# and functools.partial are callables that are not, so they are stored
# uncalled and find_threshold_crossings raises TypeError comparing floats to
# them. The fix, testing callable(threshold), is blocked:
# tests/solar_activity/lisird/test_extrema_calculator.py asserts the stored
# callable in test_set_threshold_callable and test_set_threshold_automatic, and
# that file is the author's to change.
_THRESHOLD_NOT_CALLED = pytest.mark.xfail(
    strict=True,
    raises=TypeError,
    reason=(
        "extrema_calculator.py set_threshold tests isinstance(threshold, "
        "FunctionType), so a numpy or partial callable is stored uncalled; "
        "expected TypeError \"'>' not supported between instances of 'float' "
        'and ..."; remove this marker when set_threshold tests '
        "callable(threshold) and test_extrema_calculator.py stops asserting "
        "the stored callable"
    ),
)


@_THRESHOLD_NOT_CALLED
def test_default_threshold_is_the_median_of_an_unlisted_index():
    """An index absent from the built-in table is thresholded at its median.

    ``ExtremaCalculator`` documents that ``threshold=None`` falls back to
    ``numpy.nanmedian`` of the series. With ``window=None`` the series is not
    smoothed, so the median of the input is the expected threshold.

    ON FAILURE: (unexpected pass) set_threshold now calls any callable;
    drop the xfail marker.
    """
    calc = ExtremaCalculator("unlisted_index", _INDEX, window=None)
    expected = np.nanmedian(_INDEX.to_numpy())  # identity: documented default
    # Exact: both sides are the same numpy reduction over the same values.
    assert calc.threshold.to_numpy() == pytest.approx(
        np.full(_INDEX.size, expected), rel=1e-12, abs=0
    )


@_THRESHOLD_NOT_CALLED
def test_a_callable_threshold_that_is_not_a_python_function_is_called():
    """Any callable threshold is evaluated on the series, not stored as is.

    ``functools.partial`` objects and numpy functions are callables that are not
    ``types.FunctionType``; the documented contract is "if a callable, it is
    invoked".

    ON FAILURE: (unexpected pass) set_threshold now calls any callable;
    drop the xfail marker.
    """
    q25 = functools.partial(np.nanpercentile, q=25)
    calc = ExtremaCalculator("unlisted_index", _INDEX, threshold=q25, window=None)
    expected = np.nanpercentile(_INDEX.to_numpy(), 25)  # the callable, called
    # Exact: both sides are the same numpy reduction over the same values.
    assert calc.threshold.to_numpy() == pytest.approx(
        np.full(_INDEX.size, expected), rel=1e-12, abs=0
    )


@_THRESHOLD_NOT_CALLED
def test_default_threshold_recovers_the_extrema_of_a_sinusoid():
    """With the default threshold, the extrema are the sinusoid's peaks and troughs.

    Maxima of ``2 + sin(2 pi t / P)`` fall at ``t = P/4 + nP`` and minima at
    ``t = 3P/4 + nP``. Daily sampling places each within one day of the
    analytic time.

    ON FAILURE: (unexpected pass) set_threshold now calls any callable;
    drop the xfail marker.
    """
    calc = ExtremaCalculator("unlisted_index", _INDEX, window=None)
    extrema = calc.extrema

    n = np.arange(3)
    expected_max = _T0 + (0.25 + n) * _PERIOD  # analytic peak times
    expected_min = _T0 + (0.75 + n) * _PERIOD  # analytic trough times

    found_max = extrema.index[extrema == "Max"]
    found_min = extrema.index[extrema == "Min"]
    assert found_max.size == expected_max.size
    assert found_min.size == expected_min.size
    # One day: the sampling interval of the input.
    assert (abs(found_max - expected_max) <= pd.Timedelta(days=1)).all()
    assert (abs(found_min - expected_min) <= pd.Timedelta(days=1)).all()


def test_sidc_run_normalization_documents_itself_with_the_base_docstring():
    """``help(SIDC.run_normalization)`` shows the documented contract.

    ``SIDC.run_normalization`` reuses ``ActivityIndicator.run_normalization``'s
    docstring. It must reuse the text, not the function object, or
    ``inspect.getdoc`` finds no docstring at all.

    ON FAILURE: the code is wrong.
    """
    expected = inspect.getdoc(ActivityIndicator.run_normalization)
    assert isinstance(expected, str)  # the fixture: the base is documented
    assert inspect.getdoc(SIDC.run_normalization) == expected
