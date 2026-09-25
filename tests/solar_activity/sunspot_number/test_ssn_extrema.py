#!/usr/bin/env python
"""Test SSNExtrema against the real shipped ``ssn_extrema.csv``.

Every test in this module reads the actual CSV that ships with the package,
``solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv``, whose own header
cites <http://sidc.oma.be/silso/DATA/Cycles/TableCyclesMiMa.txt> as its source.
Nothing here mocks :func:`pandas.read_csv`; the ``skiprows=45`` at
``sidc.py:552`` is the most fragile line in the module and it is executed by
every test below.

Expectations are derived from the file itself (parsed independently with the
standard library), from definitional properties of a solar cycle, or from
published cycle statistics -- never captured from a run of the code.

KNOWN GAP -- solar cycle 25 maximum
-----------------------------------
The shipped CSV records cycle 25's maximum as ``2030-12-01``, giving an
11.0-year rise time. Every closed cycle in the same file rises in 2.9 to 6.8
years. That value is a placeholder for a maximum the file was written before
observing, not a measurement, so no test here asserts it. Property tests that
depend on a cycle being closed run over cycles 1 through 24 via
:data:`LAST_CLOSED_CYCLE`. Deciding what cycle 25's maximum should be is the
author's call, not the test suite's.
"""

import pandas as pd
import pytest

from solarwindpy.solar_activity.base import IndicatorExtrema
from solarwindpy.solar_activity.sunspot_number import sidc
from solarwindpy.solar_activity.sunspot_number.sidc import SSNExtrema

# The canonical data file, located through the module that ships it rather
# than through a repository-relative path, so the test follows the package
# wherever it is installed.
SSN_EXTREMA_CSV = sidc.Path(sidc.__file__).parent / "ssn_extrema.csv"

# The header row of the data block. Everything above it is commentary.
HEADER_PREFIX = "Number,"

# Cycle 25 is still open in the shipped file (see KNOWN GAP above), so
# properties that require a completed rise and fall exclude it.
LAST_CLOSED_CYCLE = 24


# ---------------------------------------------------------------------------
# Independent parse of the CSV, using only the standard library.
# ---------------------------------------------------------------------------
def read_csv_with_stdlib(path):
    """Parse the extrema CSV without pandas.

    Returns
    -------
    tuple[int, list[str], list[list[str]]]
        The 0-based line index of the header row, the header fields, and the
        non-blank data rows below it, all as raw strings.
    """
    with open(path, "r") as f:
        lines = f.read().splitlines()

    header_index = next(
        i for i, line in enumerate(lines) if line.startswith(HEADER_PREFIX)
    )
    header = lines[header_index].split(",")
    first_data_line = header_index + 1
    rows = [line.split(",") for line in lines[first_data_line:] if line.strip()]
    return header_index, header, rows


@pytest.fixture(scope="module")
def raw_csv():
    """The shipped CSV as parsed by the standard library."""
    return read_csv_with_stdlib(SSN_EXTREMA_CSV)


@pytest.fixture
def extrema():
    """A real :class:`SSNExtrema`, built from the real shipped CSV."""
    return SSNExtrema()


@pytest.fixture
def closed_cycles(extrema):
    """Extrema rows for cycles whose maximum is a measurement, not a placeholder."""
    return extrema.data.loc[:LAST_CLOSED_CYCLE]


# ---------------------------------------------------------------------------
# The header offset: skiprows=45 at sidc.py:552.
# ---------------------------------------------------------------------------
#
# Measured (not guessed): the "Number,Min,Max" header line's raw 0-based line
# index in ssn_extrema.csv. sidc.py:552 uses skiprows=45, one less than this,
# because a blank line at index 45 precedes the header and pandas' default
# skip_blank_lines=True absorbs it during parsing -- confirmed below by
# actually parsing with skiprows=45 and checking the resulting columns.
#
# Measured consequence: skiprows=45 and skiprows=46 parse this file
# identically, because 45 lands on the blank line that pandas then drops and
# 46 lands on the header itself. Only 47 and beyond eat a data row. So there
# is no test here asserting that sidc.py's literal is 45 specifically -- such
# a test fails on a correct reimplementation that chose 46, which makes it a
# report of refactoring rather than of a defect. What is asserted instead is
# that the parse recovers every data row, which is what actually breaks.
EXPECTED_HEADER_LINE_INDEX = 46
SKIPROWS = 45


def test_header_line_index_matches_measurement(raw_csv):
    """The 'Number,' header line is where sidc.py:552's skiprows expects.

    skiprows=45 does not land directly on the header line (raw index 46); it
    lands on the blank line immediately before it, which pandas'
    skip_blank_lines default then absorbs. Both facts are measured here, not
    assumed.

    ON FAILURE: the CSV's comment header changed length. Update skiprows at
    sidc.py:552 to match, and update EXPECTED_HEADER_LINE_INDEX here.
    """
    header_index, _, _ = raw_csv
    assert header_index == EXPECTED_HEADER_LINE_INDEX

    df = pd.read_csv(SSN_EXTREMA_CSV, header=0, skiprows=SKIPROWS, index_col=0, nrows=1)
    assert list(df.columns) == ["Min", "Max"]


def test_loaded_rows_match_an_independent_parse(extrema, raw_csv):
    """SSNExtrema loads exactly the rows the stdlib finds below the header.

    This is the generalization of the offset check: it does not care what
    skiprows is, only that no data row is silently eaten and none invented.
    An off-by-one in skiprows consumes the first cycle, and that is precisely
    what mocking read_csv used to hide.

    ON FAILURE: the CSV parse is dropping or duplicating rows. The code is
    wrong.
    """
    _, header, rows = raw_csv

    assert header == ["Number", "Min", "Max"]
    assert len(extrema.data) == len(rows)

    expected = pd.DataFrame(
        [
            {
                "Number": int(number),
                "Min": pd.Timestamp(minimum.strip()),
                "Max": pd.Timestamp(maximum.strip()),
            }
            for number, minimum, maximum in rows
        ]
    ).set_index("Number")
    expected.columns.names = ["kind"]

    pd.testing.assert_frame_equal(
        extrema.data.sort_index(axis=1), expected.sort_index(axis=1)
    )


def test_extrema_are_datetimes(extrema):
    """Both columns are parsed to datetimes, not left as strings.

    ON FAILURE: to_datetime at sidc.py:553 is not being applied. The code is
    wrong.
    """
    for column in ("Min", "Max"):
        assert pd.api.types.is_datetime64_any_dtype(extrema.data.loc[:, column])


def test_columns_are_named_kind(extrema):
    """The column index is named 'kind', which stack/unstack downstream relies on.

    IndicatorExtrema.calculate_extrema_bands unstacks on level "kind", so the
    name is part of the contract, not cosmetics.

    ON FAILURE: sidc.py:554 stopped naming the columns. The code is wrong.
    """
    assert extrema.data.columns.names == ["kind"]
    assert set(extrema.data.columns) == {"Min", "Max"}


def test_is_an_indicator_extrema(extrema):
    """SSNExtrema is an IndicatorExtrema, so it carries the interval machinery.

    ON FAILURE: the class hierarchy changed and downstream code that accepts
    any IndicatorExtrema will no longer accept this. The code is wrong.
    """
    assert isinstance(extrema, IndicatorExtrema)


# ---------------------------------------------------------------------------
# Properties of the data. These hold for any correct extrema table, not just
# this one, so they survive the file being regenerated from SILSO.
# ---------------------------------------------------------------------------
def test_cycle_numbers_are_contiguous_from_one(extrema):
    """Cycles are numbered 1, 2, ... N with no gaps.

    Solar cycle numbering is conventionally continuous from cycle 1 (1755).
    Downstream code indexes ``extrema.loc[c + 1, "Min"]`` to find the falling
    edge, which is only meaningful if numbering is contiguous.

    ON FAILURE: a cycle is missing or numbered out of order. The data file is
    wrong.
    """
    index = extrema.data.index
    assert index.name == "Number"
    assert list(index) == list(range(1, len(index) + 1))


def test_minimum_precedes_maximum_within_each_cycle(closed_cycles):
    """A cycle rises before it falls: Min < Max.

    Definitional: a solar cycle begins at a minimum of the 13-month smoothed
    sunspot number and peaks at the following maximum.

    ON FAILURE: an extremum pair is transposed. The data file is wrong.
    """
    assert (closed_cycles.loc[:, "Min"] < closed_cycles.loc[:, "Max"]).all()


def test_maximum_precedes_the_next_cycles_minimum(extrema):
    """A cycle's maximum comes before the next cycle's minimum.

    Definitional: the falling edge runs Max(n) -> Min(n+1), so it must have
    positive duration or IndicatorExtrema.calculate_intervals builds an
    inverted pd.Interval.

    ON FAILURE: consecutive cycles overlap. The data file is wrong.
    """
    maxima = extrema.data.loc[:LAST_CLOSED_CYCLE, "Max"]
    next_minimum = extrema.data.loc[:, "Min"].shift(-1).loc[:LAST_CLOSED_CYCLE]
    assert (maxima < next_minimum).all()


def test_minima_are_strictly_increasing(extrema):
    """Cycle minima are monotonic in time.

    ON FAILURE: the table is out of chronological order, and every pd.cut
    downstream will raise or mis-bin. The data file is wrong.
    """
    assert extrema.data.loc[:, "Min"].is_monotonic_increasing


def test_extrema_fall_on_the_first_of_a_month(extrema):
    """Every extremum is a month start.

    The file's own header documents its construction: the dates are built as
    ``"{year}-{month}-01"`` from SILSO's year and month columns, because the
    13-month smoothed series has monthly resolution. A day other than 1 means
    a parse in the wrong date order.

    ON FAILURE: the dates were parsed with the wrong format, or the file is no
    longer built from year/month pairs. The data file is wrong.
    """
    stacked = extrema.data.stack()
    assert (stacked.dt.day == 1).all()


def test_cycle_lengths_are_physically_plausible(extrema):
    """Minimum-to-minimum cycle lengths sit inside the observed Schwabe range.

    The Schwabe cycle averages about 11 years, with individual cycles observed
    between roughly 9 and 14 years (Hathaway, D. H., "The Solar Cycle", Living
    Rev. Sol. Phys. 12, 4, 2015, DOI 10.12942/lrsp-2015-4, Sect. 2). The
    bounds below are deliberately wider than that observed range, so this
    catches a transcription error of years or a units mistake without
    asserting any particular cycle's length.

    ON FAILURE: a cycle length is unphysical -- most likely a mistyped year in
    the data file.
    """
    minima = extrema.data.loc[:, "Min"]
    lengths = minima.diff().dropna().dt.days / 365.25

    assert (lengths > 8.0).all()
    assert (lengths < 15.0).all()


def test_rise_is_shorter_than_the_full_cycle(closed_cycles, extrema):
    """Each cycle's rise is a proper part of the cycle.

    Definitional: Min -> Max is contained in Min -> next Min, so the rise must
    be strictly shorter. This holds regardless of the Waldmeier effect or any
    particular rise-time statistic.

    ON FAILURE: the maximum lies outside its own cycle. The data file is
    wrong.
    """
    rise = closed_cycles.loc[:, "Max"] - closed_cycles.loc[:, "Min"]
    full = extrema.data.loc[:, "Min"].diff().shift(-1).loc[:LAST_CLOSED_CYCLE]

    assert (rise > pd.Timedelta(0)).all()
    assert (rise < full).all()


# ---------------------------------------------------------------------------
# load_or_set_data argument contract.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "args,kwargs",
    [
        (("some_arg",), {}),
        ((), {"some_kwarg": "value"}),
        (("arg",), {"key": "value"}),
        (("arg1", "arg2"), {}),
        ((), {"key1": "value1", "key2": "value2"}),
    ],
)
def test_load_or_set_data_rejects_arguments(extrema, args, kwargs):
    """SSNExtrema reads a fixed shipped file, so it accepts no arguments.

    The error names the class so a caller of a sibling IndicatorExtrema can
    tell which one rejected them.

    ON FAILURE: the guard at sidc.py:546 is gone and a caller passing a path
    would be silently ignored. The code is wrong.
    """
    with pytest.raises(ValueError, match="SSNExtrema expects empty args and kwargs"):
        extrema.load_or_set_data(*args, **kwargs)


def test_reload_is_idempotent(extrema):
    """Calling load_or_set_data again reproduces the same table.

    A round trip through the real parser: loading twice must agree, which it
    will not if parsing depends on mutable state or on the previous result.

    ON FAILURE: loading has a side effect on its own input. The code is wrong.
    """
    before = extrema.data.copy()
    extrema.load_or_set_data()
    pd.testing.assert_frame_equal(extrema.data, before)


# ---------------------------------------------------------------------------
# Intervals derived from the extrema.
# ---------------------------------------------------------------------------
def test_intervals_are_derived_from_the_extrema(extrema):
    """Rise, Fall and Cycle intervals are built from the extrema they describe.

    Identity, computed from the parts: Rise = (Min(n), Max(n)),
    Fall = (Max(n), Min(n+1)), Cycle = (Min(n), Min(n+1)).

    ON FAILURE: calculate_intervals is not composing the intervals from the
    extrema table. The code is wrong.
    """
    data = extrema.data
    intervals = extrema.cycle_intervals

    for number in range(1, LAST_CLOSED_CYCLE + 1):
        rise = intervals.loc[number, "Rise"]
        fall = intervals.loc[number, "Fall"]
        cycle = intervals.loc[number, "Cycle"]

        assert rise.left == data.loc[number, "Min"]
        assert rise.right == data.loc[number, "Max"]
        assert fall.left == data.loc[number, "Max"]
        assert fall.right == data.loc[number + 1, "Min"]
        assert cycle.left == rise.left
        assert cycle.right == fall.right


def test_cycle_intervals_tile_time_without_gaps(extrema):
    """Consecutive Cycle intervals abut: cycle n ends where cycle n+1 begins.

    Every measurement between the first and last minimum therefore lands in
    exactly one cycle, which is what SIDCLoader.load_data's pd.cut assumes.

    ON FAILURE: cycle assignment will drop measurements into NaN. The code is
    wrong.
    """
    cycles = extrema.cycle_intervals.loc[:, "Cycle"]

    for number in range(1, LAST_CLOSED_CYCLE + 1):
        assert cycles.loc[number].right == cycles.loc[number + 1].left


def test_cut_spec_by_interval_round_trips_cycle_midpoints(extrema):
    """A point inside a cycle is binned back into that cycle's interval.

    Round trip: take the midpoint of each Cycle interval, cut it, and require
    the assigned interval to be the one it came from.

    ON FAILURE: cut_spec_by_interval mis-bins, and every cycle-resolved
    statistic downstream is attributed to the wrong cycle. The code is wrong.
    """
    cycles = extrema.cycle_intervals.loc[1:LAST_CLOSED_CYCLE, "Cycle"]
    midpoints = pd.DatetimeIndex(
        [interval.left + (interval.right - interval.left) / 2 for interval in cycles]
    )

    cut = extrema.cut_spec_by_interval(midpoints, kind="Cycle")

    assert list(cut.values) == list(cycles.values)


def test_cut_spec_by_interval_round_trips_rise_and_fall(extrema):
    """Points on the rising and falling edges bin into Rise and Fall respectively.

    Round trip over the "Edges" selector, which is the option most likely to
    be broken by a refactor because it is special-cased.

    ON FAILURE: edge classification is wrong. The code is wrong.
    """
    intervals = extrema.cycle_intervals
    number = LAST_CLOSED_CYCLE
    rise = intervals.loc[number, "Rise"]
    fall = intervals.loc[number, "Fall"]

    probes = pd.DatetimeIndex(
        [
            rise.left + (rise.right - rise.left) / 2,
            fall.left + (fall.right - fall.left) / 2,
        ]
    )
    cut = extrema.cut_spec_by_interval(probes, kind="Edges")

    assert list(cut.values) == [rise, fall]


@pytest.mark.parametrize("kind", ["Nonsense", ["Rise", "Nonsense"]])
def test_cut_spec_by_interval_rejects_unknown_kind(extrema, kind):
    """An unavailable interval kind is refused rather than silently ignored.

    ON FAILURE: a typo in a caller's `kind` would bin against the wrong
    intervals instead of raising. The code is wrong.
    """
    epoch = pd.DatetimeIndex(["2010-01-01"])
    with pytest.raises(ValueError, match="is unavailable"):
        extrema.cut_spec_by_interval(epoch, kind=kind)


def test_cut_spec_by_interval_honours_tk_cycles(extrema):
    """Restricting to a subset of cycles leaves points outside that subset unbinned.

    ON FAILURE: tk_cycles is not filtering, so a caller asking for cycle 24
    alone would silently receive neighbouring cycles too. The code is wrong.
    """
    cycles = extrema.cycle_intervals.loc[:, "Cycle"]
    inside = cycles.loc[LAST_CLOSED_CYCLE]
    outside = cycles.loc[LAST_CLOSED_CYCLE - 1]

    probes = pd.DatetimeIndex(
        [
            inside.left + (inside.right - inside.left) / 2,
            outside.left + (outside.right - outside.left) / 2,
        ]
    )
    cut = extrema.cut_spec_by_interval(
        probes, kind="Cycle", tk_cycles=[LAST_CLOSED_CYCLE]
    )

    assert cut.iloc[0] == inside
    assert pd.isna(cut.iloc[1])


# ---------------------------------------------------------------------------
# Bands about the extrema.
# ---------------------------------------------------------------------------
def test_extrema_bands_require_calculation_first(extrema):
    """Asking for bands before computing them says so, rather than raising bare.

    ON FAILURE: a caller gets an unhelpful AttributeError instead of the
    instruction to call calculate_extrema_bands. The code is wrong.
    """
    with pytest.raises(AttributeError, match="calculate_extrema_bands"):
        extrema.extrema_bands


@pytest.mark.parametrize("dt", ["365d", "180d", "2d"])
def test_extrema_bands_are_centred_on_the_extrema(extrema, dt):
    """Each band is [extremum - dt, extremum + dt].

    Identity, computed from the parts: the band's endpoints are the extremum
    displaced by dt, so its width is 2*dt and its centre is the extremum.

    ON FAILURE: calculate_extrema_bands is not symmetric about the extremum.
    The code is wrong.
    """
    delta = pd.to_timedelta(dt)
    bands = extrema.calculate_extrema_bands(dt=dt)

    for number, row in extrema.data.iterrows():
        for kind in ("Min", "Max"):
            band = bands.loc[number, kind]
            assert band.left == row.loc[kind] - delta
            assert band.right == row.loc[kind] + delta
            assert band.right - band.left == 2 * delta


def test_extrema_bands_accept_asymmetric_widths(extrema):
    """A two-element dt gives a left width and a right width independently.

    Identity: band = [extremum - dl, extremum + dr].

    ON FAILURE: the asymmetric branch of calculate_extrema_bands is swapping
    or ignoring one of its two widths. The code is wrong.
    """
    left_width = pd.Timedelta("30d")
    right_width = pd.Timedelta("400d")
    bands = extrema.calculate_extrema_bands(dt=[left_width, right_width])

    for number, row in extrema.data.iterrows():
        for kind in ("Min", "Max"):
            band = bands.loc[number, kind]
            assert band.left == row.loc[kind] - left_width
            assert band.right == row.loc[kind] + right_width


def test_extrema_bands_reject_more_than_two_widths(extrema):
    """Only one or two widths are meaningful for a band.

    ON FAILURE: extra widths are silently dropped. The code is wrong.
    """
    with pytest.raises(ValueError, match="1 or 2 dt options"):
        extrema.calculate_extrema_bands(dt=["1d", "2d", "3d"])


def test_cut_about_extrema_bands_round_trips_the_extrema(extrema):
    """Feeding the extrema dates back in recovers their own cycle and kind labels.

    Round trip: an extremum lies at the centre of its own band, so cutting the
    extrema themselves must label each one "{number}-{kind}". With dt=365d the
    bands are disjoint, because the shortest rise in the file is about 2.9
    years and the shortest cycle about 9 years.

    ON FAILURE: bands and labels have come out of correspondence, so extrema
    would be attributed to the wrong cycle. The code is wrong.
    """
    extrema.calculate_extrema_bands(dt="365d")

    stacked = extrema.data.stack()
    epoch = pd.DatetimeIndex(stacked.values)
    _, mapped = extrema.cut_about_extrema_bands(epoch)

    expected = [f"{number}-{kind}" for number, kind in stacked.index]
    assert list(mapped.values) == expected


def test_cut_about_extrema_bands_restricted_to_one_kind(extrema):
    """Restricting to Min bands leaves maxima unbinned.

    ON FAILURE: the kind selector is ignored, so a caller asking about minima
    also receives maxima. The code is wrong.
    """
    extrema.calculate_extrema_bands(dt="200d")

    minima = extrema.data.loc[:LAST_CLOSED_CYCLE, "Min"]
    maxima = extrema.data.loc[:LAST_CLOSED_CYCLE, "Max"]
    epoch = pd.DatetimeIndex(list(minima.values) + list(maxima.values))

    _, mapped = extrema.cut_about_extrema_bands(epoch, kind="Min")

    split = len(minima)
    assert list(mapped.iloc[:split]) == [f"{n}-Min" for n in minima.index]
    assert mapped.iloc[split:].isna().all()
