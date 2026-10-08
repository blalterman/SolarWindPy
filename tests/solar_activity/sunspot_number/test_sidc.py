#!/usr/bin/env python
"""Test SIDC end to end against the real extrema table.

``SIDC.__init__`` runs an identifier, a loader, an extrema table, and two
labelling passes. The only genuine external boundary in that chain is the SIDC
download, and ``DataLoader`` only downloads when its on-disk cache is stale.
So these tests redirect ``Path.home`` at a temporary directory, seed today's
cache with a sunspot series of known shape, and then construct a real
``SIDC``: a real ``SIDC_ID``, a real ``SIDCLoader``, a real ``SSNExtrema``
reading the real shipped ``ssn_extrema.csv``, and the real labelling code.

Only boundaries are faked: ``Path.home`` (the ``fake_home`` fixture), the
socket layer (the autouse ``no_network`` fixture, which makes
``socket.getaddrinfo`` and ``socket.socket.connect`` raise ``NetworkRefused``),
and, in one test, ``SIDC_ID.url``, the SILSO download URL, redirected to a
local file in SILSO's layout (``silso_m13.csv``) so a stale cache downloads
offline.
Expectations are recomputed from the inputs -- the seeded series, the local SILSO
file's text and the extrema table -- or are analytic identities of the normalization
being applied.

Whether the live endpoint still serves SILSO's layout is a drift question, not
a unit-test question. ``test_sidc_loader.py`` covers ``download_data``'s
parsing of the other series keys.
"""

import inspect
import re
import socket

import matplotlib
import numpy as np
import pandas as pd
import pytest

from pathlib import Path

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.solar_activity.base import ActivityIndicator  # noqa: E402
from tests.tolerances import exact  # noqa: E402
from solarwindpy.solar_activity.sunspot_number.sidc import (  # noqa: E402
    SIDC,
    SIDC_ID,
    SIDCLoader,
    SSNExtrema,
)

# The seeded series spans cycles 23 and 24 in full: the shipped extrema table
# puts cycle 23's minimum at 1996-08-01, cycle 24's at 2008-12-01 and cycle
# 25's at 2019-12-01, so this window lies entirely inside two closed cycles.
SERIES_START = "1996-09-01"
SERIES_END = "2019-11-01"


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ``Path.home`` so the loader caches under ``tmp_path``.

    ``DataLoader.get_data_ctime`` recovers the cache date by matching eight
    consecutive digits anywhere in the absolute path and asserts it finds
    exactly one, so a tmp_path with its own eight-digit run would break the
    loader for reasons unrelated to the code under test.
    """
    if re.search(r"\d{8}", str(tmp_path)):
        pytest.skip(f"tmp_path contains an 8-digit run: {tmp_path}")

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


class NetworkRefused(AssertionError):
    """Raised by ``no_network`` when a test in this module opens a socket."""


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Refuse every socket, so no test in this module reaches SILSO.

    Every test here seeds today's cache and expects the loader to read it.
    ``maybe_update_stale_data`` recomputes "today" at load time, so a run that
    straddles local midnight between seeding and loading would judge the cache
    stale and run the real ``SIDCLoader.download_data``, whose
    ``pd.read_csv(self.url)`` opens a connection to the live SILSO endpoint.
    This guard sits on that network boundary rather than on any SolarWindPy
    name: ``socket.getaddrinfo`` (the DNS lookup) and ``socket.socket.connect``
    raise ``NetworkRefused``. It subclasses ``AssertionError``, not
    ``OSError``, so urllib does not wrap it and the failure names its cause.
    It is a guard, not a stand-in: a test that needs the network fails.
    """

    def refuse_lookup(host, *args, **kwargs):
        raise NetworkRefused(f"a test tried to open a network connection to {host}")

    def refuse_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        raise NetworkRefused(f"a test tried to open a network connection to {host}")

    monkeypatch.setattr(socket, "getaddrinfo", refuse_lookup)
    monkeypatch.setattr(socket.socket, "connect", refuse_connect)


def seed_cache(home, key, frame, date=None):
    """Write ``frame`` into the SIDC cache slot for ``key`` dated ``date``.

    ``date`` defaults to today, the slot the loader reads without downloading.
    """
    cache = home / "solarwindpy" / "data" / "sidc" / key
    cache.mkdir(parents=True, exist_ok=True)
    if date is None:
        date = pd.to_datetime("today")
    frame.to_csv(cache / f"{date.strftime('%Y%m%d')}.csv")
    return cache


def sinusoidal_ssn(index):
    """A smooth sunspot-like series: strictly positive, one broad peak per cycle."""
    phase = 2.0 * np.pi * np.arange(len(index)) / 132.0
    return 80.0 + 70.0 * np.sin(phase)


@pytest.fixture
def seeded_index():
    """Monthly epochs spanning solar cycles 23 and 24."""
    return pd.date_range(SERIES_START, SERIES_END, freq="MS")


@pytest.fixture
def sidc(fake_home, seeded_index):
    """A real ``SIDC`` built from a locally seeded cache."""
    frame = pd.DataFrame(
        {
            "ssn": sinusoidal_ssn(seeded_index),
            "std": 5.0,
            "n_obs": 25,
        },
        index=seeded_index,
    )
    seed_cache(fake_home, "m13", frame)
    return SIDC("m13")


@pytest.fixture
def extrema():
    """The real extrema table, built independently of the SIDC under test."""
    return SSNExtrema()


# ---------------------------------------------------------------------------
# The network guard.
# ---------------------------------------------------------------------------
def test_no_network_refuses_the_download_a_stale_cache_triggers(
    fake_home, seeded_index
):
    """A cache dated yesterday sends SIDC to the network, and the guard stops it.

    Seeding yesterday's slot instead of today's is the input chosen so the
    answer is known: ``maybe_update_stale_data`` must call the real
    ``download_data``, whose ``pd.read_csv`` on the SILSO URL is the only
    network access in the chain. Seeing ``NetworkRefused`` proves the guard
    sits on that path, so every other test's offline claim rests on it.

    ON FAILURE: the no_network fixture no longer separates a cached load from
    a live download; fix the fixture.
    """
    frame = pd.DataFrame(
        {"ssn": sinusoidal_ssn(seeded_index), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    yesterday = pd.to_datetime("today") - pd.Timedelta("1D")
    seed_cache(fake_home, "m13", frame, date=yesterday)

    with pytest.raises(NetworkRefused, match="tried to open a network connection"):
        SIDC("m13")


# ---------------------------------------------------------------------------
# The download, from a local file in SILSO's layout.
# ---------------------------------------------------------------------------
# ``silso_m13.csv`` holds six rows of the 13-month smoothed series in SILSO's
# layout (https://www.sidc.be/SILSO/infosnmstot): semicolon-separated,
# space-padded, no header; year, month, decimal year, smoothed sunspot number,
# standard deviation, observation count, definitive flag; -1 marks a missing
# value. The numbers are chosen for the test, not copied from SILSO.
SILSO_M13 = Path(__file__).parent / "silso_m13.csv"


def silso_rows():
    """The local file's rows, split by hand rather than by pandas."""
    return [line.split(";") for line in SILSO_M13.read_text().splitlines()]


def test_stale_cache_downloads_the_silso_series_and_loads_it(
    fake_home, seeded_index, extrema, monkeypatch
):
    """A stale cache downloads, parses, caches and labels the SILSO series.

    Yesterday's cache holds the sinusoidal series, so ``SIDC("m13")`` must
    download. The download URL is redirected to the local file, on the network
    boundary; ``no_network`` stays active, and reading a local path opens no
    socket. Every expectation comes from the file's text, split by hand: the
    index is each row's month start, the columns carry SILSO's values with -1
    as NaN (the last row is a month with no smoothed sunspot number yet, -1 in
    ``ssn``, ``std`` and ``n_obs``), the standard error is std / sqrt(n_obs),
    the flag is a bool, and the cycle is the extrema-table interval holding
    each time.

    ON FAILURE: the code is wrong, unless SILSO changed its published layout; then update ``silso_m13.csv`` and the column table in ``sidc.py``.
    """
    stale = pd.DataFrame(
        {"ssn": sinusoidal_ssn(seeded_index), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    yesterday = pd.to_datetime("today") - pd.Timedelta("1D")
    seed_cache(fake_home, "m13", stale, date=yesterday)
    monkeypatch.setattr(SIDC_ID, "url", property(lambda self: str(SILSO_M13)))

    data = SIDC("m13").data

    rows = silso_rows()
    year = [int(r[0]) for r in rows]
    month = [int(r[1]) for r in rows]
    ssn = np.array([float(r[3]) for r in rows])
    std = np.array([float(r[4]) for r in rows])
    n_obs = np.array([float(r[5]) for r in rows])
    # SILSO's missing-value marker, -1, is NaN after loading.
    for values in (ssn, std, n_obs):
        values[values == -1] = np.nan
    assert np.isnan(ssn[-1]), "the fixture's last row must carry the -1 marker"

    expected_index = pd.DatetimeIndex(
        [pd.Timestamp(year=y, month=m, day=1) for y, m in zip(year, month)]
    )
    pd.testing.assert_index_equal(data.index, expected_index, check_names=False)

    downloaded = {
        "definitive": np.dtype(bool),
        "month": np.dtype("int64"),
        "n_obs": np.dtype("float64"),
        "ssn": np.dtype("float64"),
        "std": np.dtype("float64"),
        "std_error": np.dtype("float64"),
        "year": np.dtype("int64"),
        "year_fraction": np.dtype("float64"),
    }
    assert set(data.columns) == set(downloaded) | {"cycle", "extremum", "edge"}
    assert data.loc[:, list(downloaded)].dtypes.to_dict() == downloaded

    assert data.loc[:, "year"].tolist() == year
    assert data.loc[:, "month"].tolist() == month
    assert data.loc[:, "year_fraction"].to_numpy() == exact([float(r[2]) for r in rows])
    assert data.loc[:, "ssn"].to_numpy() == exact(ssn, nan_ok=True)
    assert data.loc[:, "std"].to_numpy() == exact(std, nan_ok=True)
    assert data.loc[:, "n_obs"].to_numpy() == exact(n_obs, nan_ok=True)
    assert data.loc[:, "std_error"].to_numpy() == exact(
        std / np.sqrt(n_obs), nan_ok=True
    )
    assert data.loc[:, "definitive"].tolist() == [r[6] == "1" for r in rows]

    cycles = extrema.cycle_intervals.loc[:, "Cycle"]
    expected_cycles = [
        next(number for number, interval in cycles.items() if t in interval)
        for t in expected_index
    ]
    assert [int(c) for c in data.loc[:, "cycle"]] == expected_cycles


# ---------------------------------------------------------------------------
# Construction.
# ---------------------------------------------------------------------------
def test_sidc_constructs_from_a_local_cache(sidc, seeded_index):
    """A full SIDC construction produces the labelled table its callers expect.

    ON FAILURE: SIDC cannot be built at all, and every downstream consumer of
    sunspot number is broken. The code is wrong.
    """
    assert isinstance(sidc, ActivityIndicator)
    pd.testing.assert_index_equal(sidc.data.index, seeded_index, check_names=False)
    assert {"ssn", "cycle", "extremum", "edge"} <= set(sidc.data.columns)


def test_data_is_the_loaders_data(sidc):
    """``SIDC.data`` is the loader's table, not a copy of it.

    The labelling passes write straight into ``self.data``, so if this were a
    copy the labels would be computed and then discarded.

    ON FAILURE: extremum and edge labels would silently vanish. The code is
    wrong.
    """
    assert sidc.data is sidc.loader.data


def test_extrema_is_the_real_shipped_table(sidc, extrema):
    """``SIDC.extrema`` is an SSNExtrema holding the shipped CSV's contents.

    ON FAILURE: the cycle boundaries SIDC labels against are not the ones the
    package ships. The code is wrong.
    """
    assert isinstance(sidc.extrema, SSNExtrema)
    pd.testing.assert_frame_equal(sidc.extrema.data, extrema.data)


def test_id_is_a_real_sidc_id_for_the_requested_series(sidc):
    """The identifier carries the requested key and its SILSO URL.

    The expected URL is the documented base ``http://www.sidc.be/silso/INFO/``
    joined to the file the ``SIDC_ID`` docstring table lists for m13.

    ON FAILURE: SIDC would download a different series than it was asked for.
    The code is wrong.
    """
    assert isinstance(sidc.id, SIDC_ID)
    assert sidc.id.key == "m13"
    assert sidc.id.url == "http://www.sidc.be/silso/INFO/snmstotcsv.php"


def test_loader_is_a_real_sidc_loader_for_the_same_identifier(sidc):
    """The loader is built from the identifier, so key and URL cannot diverge.

    ON FAILURE: the series identified and the series loaded are different
    things. The code is wrong.
    """
    assert isinstance(sidc.loader, SIDCLoader)
    assert sidc.loader.key == sidc.id.key
    assert sidc.loader.url == sidc.id.url


def test_set_id_refuses_anything_that_is_not_an_id(sidc):
    """Only an ID may be installed as the identifier.

    ON FAILURE: a bare string could be installed and ``self.id.url`` would
    fail far from the cause. The code is wrong.
    """
    with pytest.raises(AssertionError):
        sidc.set_id("m13")


# ---------------------------------------------------------------------------
# Cycle assignment and labelling.
# ---------------------------------------------------------------------------
def test_every_measurement_lands_in_a_cycle(sidc, extrema):
    """Each epoch is assigned the cycle whose interval contains it.

    Recomputed from the extrema table rather than taken from SIDC's answer.

    ON FAILURE: measurements are attributed to the wrong solar cycle. The code
    is wrong.
    """
    cycles = extrema.cycle_intervals.loc[:, "Cycle"]

    expected = []
    for timestamp in sidc.data.index:
        containing = [
            number for number, interval in cycles.items() if timestamp in interval
        ]
        assert len(containing) == 1, f"{timestamp} is in {len(containing)} cycles"
        expected.append(containing[0])

    assert [int(value) for value in sidc.data.loc[:, "cycle"]] == expected
    assert set(expected) == {23, 24}


def test_edge_rises_to_the_cycle_maximum_and_falls_after(sidc, extrema):
    """An epoch is on the rising edge up to and including its cycle's maximum.

    Recomputed from the parts: the boundary is the cycle's maximum date in the
    extrema table, not anything SIDC derived from the sunspot values.

    ON FAILURE: rising and falling edges are mislabelled, and any analysis
    that separates them is wrong. The code is wrong.
    """
    expected = []
    for timestamp, cycle in sidc.data.loc[:, "cycle"].items():
        maximum = extrema.data.loc[int(cycle), "Max"]
        expected.append("Rise" if timestamp <= maximum else "Fall")

    assert list(sidc.data.loc[:, "edge"]) == expected
    assert set(expected) == {"Rise", "Fall"}


def test_extremum_kind_follows_the_half_max_rule(sidc, extrema):
    """Labels follow the documented rule, recomputed from the series itself.

    ``calculate_extrema_kind`` documents its rule: within a cycle, epochs at or
    above half that cycle's peak are Max epochs of that cycle; epochs below
    half-peak are Min epochs of the current cycle before the maximum date and
    of the next cycle after it. Here that rule is evaluated independently
    against the seeded series and the extrema table.

    ON FAILURE: the minimum and maximum populations are mixed, which shifts
    every statistic conditioned on solar activity level. The code is wrong.
    """
    data = sidc.data
    expected = {}

    for cycle, group in data.loc[:, ["cycle", "ssn"]].groupby("cycle", observed=True):
        ssn = group.loc[:, "ssn"]
        half_peak = 0.5 * ssn.max()
        maximum_date = extrema.data.loc[int(cycle), "Max"]

        for timestamp, value in ssn.items():
            if value >= half_peak:
                expected[timestamp] = f"{cycle}-Max"
            elif timestamp <= maximum_date:
                expected[timestamp] = f"{cycle}-Min"
            else:
                expected[timestamp] = f"{cycle + 1}-Min"

    actual = data.loc[:, "extremum"].to_dict()
    assert actual == expected

    kinds = set(expected.values())
    assert any(label.endswith("-Max") for label in kinds)
    assert any(label.endswith("-Min") for label in kinds)


def test_labels_are_stable_under_recalculation(sidc):
    """Running the labelling passes twice gives the same labels.

    Idempotence: the passes read ``cycle`` and ``ssn`` and write ``extremum``
    and ``edge``, so a second run that disagrees means one of them is reading
    its own output.

    ON FAILURE: labelling depends on prior state. The code is wrong.
    """
    first = sidc.data.loc[:, ["extremum", "edge"]].copy()

    sidc.calculate_extrema_kind()
    sidc.calculate_edge()

    pd.testing.assert_frame_equal(sidc.data.loc[:, ["extremum", "edge"]], first)


# ---------------------------------------------------------------------------
# Normalization. Each case asserts the analytic identity that defines it.
# ---------------------------------------------------------------------------
def normalized_by_cycle(sidc):
    """Group the normalized column by solar cycle."""
    return sidc.data.loc[:, "nssn"].groupby(sidc.data.loc[:, "cycle"], observed=True)


def test_normalization_by_max_gives_each_cycle_a_unit_maximum(sidc):
    """max normalization divides each cycle by its own peak, so every peak is 1.

    Analytic identity of g / max(g).

    ON FAILURE: cycles are not being normalized independently, so amplitudes
    from different cycles are not comparable. The code is wrong.
    """
    sidc.run_normalization(norm_by="max")

    for _, group in normalized_by_cycle(sidc):
        np.testing.assert_allclose(group.max(), 1.0)


def test_normalization_by_max_preserves_the_ratio_to_the_peak(sidc):
    """Each normalized value is its share of its own cycle's peak.

    Identity computed from the parts, point by point rather than only at the
    maximum.

    ON FAILURE: normalization is not a pure rescaling within the cycle. The
    code is wrong.
    """
    raw = sidc.data.loc[:, "ssn"].copy()
    cycle = sidc.data.loc[:, "cycle"]

    sidc.run_normalization(norm_by="max")

    expected = raw.groupby(cycle, observed=True).transform(lambda g: g / g.max())
    np.testing.assert_allclose(sidc.data.loc[:, "nssn"].values, expected.values)


def test_normalization_by_zscore_gives_each_cycle_zero_mean_unit_variance(sidc):
    """zscore normalization standardises each cycle.

    Analytic identity of (g - mean(g)) / std(g).

    ON FAILURE: the standardisation is not per cycle, or uses the wrong
    moments. The code is wrong.
    """
    sidc.run_normalization(norm_by="zscore")

    for _, group in normalized_by_cycle(sidc):
        assert group.mean() == exact(0.0, scale=1.0)  # mean of O(1) z-scores
        np.testing.assert_allclose(group.std(), 1.0)


def test_normalization_by_feature_scale_maps_each_cycle_onto_the_unit_interval(sidc):
    """feature-scale normalization sends each cycle's range to [0, 1].

    Analytic identity of (g - min(g)) / (max(g) - min(g)).

    ON FAILURE: the scaling is not using the cycle's own extremes. The code is
    wrong.
    """
    sidc.run_normalization(norm_by="feature-scale")

    for _, group in normalized_by_cycle(sidc):
        assert group.min() == exact(0.0)  # (min - min) / range
        np.testing.assert_allclose(group.max(), 1.0)


@pytest.mark.parametrize("factor", [2.0, 0.25, 1000.0])
def test_normalization_by_max_is_scale_invariant(fake_home, seeded_index, factor):
    """Rescaling the input sunspot number leaves the max normalization unchanged.

    Property over a region rather than a case: g / max(g) is invariant under
    g -> c*g for any positive c, so the normalized series must not move when
    the raw counts are multiplied.

    ON FAILURE: normalization has absorbed an absolute scale and the result
    depends on the units of the input. The code is wrong.
    """
    base = sinusoidal_ssn(seeded_index)

    results = []
    for scale in (1.0, factor):
        frame = pd.DataFrame(
            {"ssn": scale * base, "std": 5.0, "n_obs": 25}, index=seeded_index
        )
        seed_cache(fake_home, "m13", frame)
        indicator = SIDC("m13")
        results.append(indicator.run_normalization(norm_by="max"))

    np.testing.assert_allclose(results[0].values, results[1].values)


def test_normalization_by_zscore_is_affine_invariant(fake_home, seeded_index):
    """Shifting and rescaling the input leaves the z-score unchanged.

    Property: (g - mean) / std is invariant under g -> a*g + b for a > 0.

    ON FAILURE: the standardisation is not using the group's own moments. The
    code is wrong.
    """
    base = sinusoidal_ssn(seeded_index)

    results = []
    for scale, offset in ((1.0, 0.0), (3.0, 500.0)):
        frame = pd.DataFrame(
            {"ssn": scale * base + offset, "std": 5.0, "n_obs": 25},
            index=seeded_index,
        )
        seed_cache(fake_home, "m13", frame)
        indicator = SIDC("m13")
        results.append(indicator.run_normalization(norm_by="zscore"))

    np.testing.assert_allclose(results[0].values, results[1].values)


def test_run_normalization_rejects_an_unknown_method(sidc):
    """An unrecognised normalization is refused rather than silently skipped.

    ON FAILURE: a typo would leave the data unnormalized with no signal to the
    caller. The code is wrong.
    """
    with pytest.raises(AssertionError):
        sidc.run_normalization(norm_by="not_a_method")


def test_normalized_property_round_trips_the_stored_column(sidc):
    """``normalized`` returns what ``run_normalization`` stored.

    Round trip through the object's own state.

    ON FAILURE: the property and the computation disagree, so callers get a
    stale or recomputed answer. The code is wrong.
    """
    computed = sidc.run_normalization(norm_by="max")
    pd.testing.assert_series_equal(sidc.normalized, computed, check_names=False)


def test_normalized_property_computes_on_first_access(sidc):
    """Asking for ``normalized`` before normalizing performs the normalization.

    ON FAILURE: first access raises instead of computing. The code is wrong.
    """
    assert "nssn" not in sidc.data.columns

    result = sidc.normalized

    assert "nssn" in sidc.data.columns
    np.testing.assert_allclose(result.values, sidc.data.loc[:, "nssn"].values)


def test_norm_by_records_the_method_used(sidc):
    """The object remembers which normalization produced its current column.

    ON FAILURE: a caller cannot tell whether nssn is a max ratio or a z-score,
    which are not interchangeable. The code is wrong.
    """
    with pytest.raises(AttributeError, match="calculate normalized"):
        sidc.norm_by

    sidc.run_normalization(norm_by="feature-scale")
    assert sidc.norm_by == "feature-scale"


# ---------------------------------------------------------------------------
# Interpolation.
# ---------------------------------------------------------------------------
def test_interpolate_data_recovers_a_linear_ramp(fake_home, seeded_index):
    """Interpolating a straight line onto a finer grid returns that line.

    Parameter recovery: the source is exactly linear in elapsed time, so the
    interpolated value at any interior epoch is fixed by the slope and
    intercept alone, whatever interpolator is used. Note the ramp must be
    linear in time rather than in the month ordinal -- months have unequal
    lengths, so a series linear in the ordinal is not a straight line on the
    time axis the interpolator works on.

    ON FAILURE: interpolation is distorting the series it is handed. The code
    is wrong.
    """
    slope_per_day = 0.05
    intercept = 20.0

    def ramp(index):
        elapsed = (index - seeded_index[0]).total_seconds() / 86400.0
        return intercept + slope_per_day * np.asarray(elapsed)

    frame = pd.DataFrame(
        {"ssn": ramp(seeded_index), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    target = pd.date_range(seeded_index[10], seeded_index[-10], freq="10D")
    interpolated = indicator.interpolate_data(target, key="ssn")

    assert interpolated.loc[:, "ssn"].to_numpy() == exact(ramp(target))


def test_interpolate_data_does_not_extrapolate(fake_home, seeded_index):
    """Targets outside the measured span come back as NaN, not invented values.

    ON FAILURE: sunspot numbers would be fabricated for epochs the instrument
    never covered. The code is wrong.
    """
    frame = pd.DataFrame(
        {"ssn": sinusoidal_ssn(seeded_index), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    target = pd.date_range("1990-01-01", "2025-01-01", freq="MS")
    interpolated = indicator.interpolate_data(target, key="ssn")

    day = pd.Timedelta("1D")
    first, last = seeded_index[0], seeded_index[-1]

    ssn = interpolated.loc[:, "ssn"]
    before = ssn.loc[ssn.index < first - day]
    after = ssn.loc[ssn.index > last + day]
    inside = ssn.loc[(ssn.index >= first) & (ssn.index <= last)]

    assert len(before) and before.isna().all()
    assert len(after) and after.isna().all()
    assert inside.notna().all()


# ---------------------------------------------------------------------------
# Banding by sunspot number.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("dssn", [2.0, 5.0, 10.0])
def test_ssn_bands_contain_the_values_they_label(fake_home, seeded_index, dssn):
    """Banding is a partition: a value is labelled exactly when it is in range.

    Two properties, together, over the whole series. Every labelled value
    falls inside its own band, and every band is 2*dssn wide. And the
    converse, which is what stops the test passing vacuously on a series that
    was almost entirely dropped: a value goes unlabelled only when it lies
    outside the span the bands cover, which happens because the bands are laid
    out from the measured maximum while the values being cut come from the
    interpolation, whose spline can overshoot it.

    ON FAILURE: banding mislabels sunspot levels, so any spectrum sorted by
    activity level is sorted wrongly. The code is wrong.
    """
    frame = pd.DataFrame(
        {"ssn": sinusoidal_ssn(seeded_index), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    target = pd.date_range(seeded_index[5], seeded_index[-5], freq="20D")
    interpolated = indicator.interpolate_data(target, key="ssn")

    cut = indicator.cut_spec_by_ssn_band(key="ssn", dssn=dssn)

    assert cut.name == "ssn_band"
    for interval in indicator.ssn_band_intervals:
        np.testing.assert_allclose(interval.right - interval.left, 2.0 * dssn)

    values = interpolated.loc[:, "ssn"]
    intervals = indicator.ssn_band_intervals
    covered_low, covered_high = intervals[0].left, intervals[-1].right

    labelled = cut.dropna()
    assert len(labelled), "no value was banded at all"
    for timestamp, interval in labelled.items():
        assert values.loc[timestamp] in interval

    # The converse: nothing inside the covered span was silently dropped.
    for timestamp in cut.index[cut.isna()]:
        value = values.loc[timestamp]
        assert not (covered_low < value <= covered_high), (
            f"{value} at {timestamp} lies inside the banded span "
            f"({covered_low}, {covered_high}] but was left unlabelled"
        )


def test_ssn_bands_reject_a_width_that_spans_the_normalized_range(sidc):
    """Normalized sunspot number lives in [0, 1], so a band wider than 1 is refused.

    A half-width of 1 or more makes every band cover the entire normalized
    range, which is not a binning.

    ON FAILURE: a meaningless banding would be produced silently. The code is
    wrong.
    """
    sidc.run_normalization(norm_by="max")

    with pytest.raises(ValueError, match="Normalized SSN requires that dssn < 1"):
        sidc.cut_spec_by_ssn_band(key="nssn", dssn=1.5)


# ---------------------------------------------------------------------------
# Small hand-built series: a ramp across the cycle 23/24 boundary.
# ---------------------------------------------------------------------------
# Monthly epochs 2008-01-01 .. 2009-12-01 (700 days; 2008 is a leap year)
# straddle the shipped extrema table's cycle 23/24 boundary at 2008-12-01.
# SSN = 1 + 0.01 * (days since 2008-01-01) runs from 1.0 to 8.0 and is linear
# in time, so any interpolator returns the same line at an interior epoch.
RAMP_START = pd.Timestamp("2008-01-01")


def ramp_ssn(index):
    """SSN of the hand-built ramp at ``index``."""
    days = (index - RAMP_START).total_seconds().to_numpy() / 86400.0
    return 1.0 + 0.01 * days


@pytest.fixture
def ramp_index():
    """Monthly epochs of the hand-built ramp."""
    return pd.date_range(RAMP_START, "2009-12-01", freq="MS")


@pytest.fixture
def ramp_sidc(fake_home, ramp_index):
    """A real ``SIDC`` whose cached series is the hand-built ramp.

    ``std`` is constant, so interpolating it gives a different answer than
    interpolating ``ssn``.
    """
    frame = pd.DataFrame(
        {"ssn": ramp_ssn(ramp_index), "std": 5.0, "n_obs": 25}, index=ramp_index
    )
    seed_cache(fake_home, "m13", frame)
    return SIDC("m13")


def at_days(*days):
    """Epochs ``days`` after the ramp's start."""
    return pd.DatetimeIndex([RAMP_START + pd.Timedelta(days=d) for d in days])


def test_ramp_fixture_straddles_two_cycles(ramp_sidc, extrema):
    """The ramp's epochs fall in cycles 23 and 24 of the shipped table.

    ON FAILURE: the fixture no longer separates per-cycle from whole-series
    normalization; fix the fixture.
    """
    cycles = extrema.cycle_intervals.loc[:, "Cycle"]
    found = {
        number
        for timestamp in ramp_sidc.data.index
        for number, interval in cycles.items()
        if timestamp in interval
    }
    assert found == {23, 24}


def test_interpolate_data_defaults_to_the_ssn_column(ramp_sidc):
    """With no ``key``, ``interpolate_data`` interpolates ``ssn`` and stores it.

    At 50, 250 and 450 days the ramp reads 1.5, 3.5 and 5.5 (hand-computed);
    the constant ``std`` column would read 5 everywhere.

    ON FAILURE: the code is wrong.
    """
    target = at_days(50, 250, 450)
    interpolated = ramp_sidc.interpolate_data(target)

    assert list(interpolated.columns) == ["ssn"]
    assert interpolated.loc[:, "ssn"].to_numpy() == exact([1.5, 3.5, 5.5])
    assert ramp_sidc.interpolated is interpolated


def test_interpolate_data_skips_a_missing_month(fake_home, ramp_index):
    """A NaN month is dropped before interpolating, not propagated.

    The remaining months still lie on the ramp, so the value at the missing
    epoch is the ramp's own (hand-computed from its definition).

    ON FAILURE: the code is wrong.
    """
    ssn = ramp_ssn(ramp_index)
    ssn[10] = np.nan
    frame = pd.DataFrame({"ssn": ssn, "std": 5.0, "n_obs": 25}, index=ramp_index)
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    target = ramp_index[8:13]
    interpolated = indicator.interpolate_data(target, key="ssn")
    assert interpolated.loc[:, "ssn"].to_numpy() == exact(ramp_ssn(target))


def test_run_normalization_also_normalizes_the_interpolated_series(ramp_sidc, extrema):
    """After ``interpolate_data``, ``run_normalization`` adds ``nssn`` to the interpolation.

    Each interpolated value is divided by the largest interpolated value in
    its own cycle. Expected values come from the ramp's definition and the
    shipped cycle intervals, not from SIDC: the target grid crosses the
    cycle 23/24 boundary, so per-cycle and whole-series maxima differ.

    ON FAILURE: the code is wrong.
    """
    target = pd.date_range(RAMP_START, "2009-12-01", freq="10D")
    ramp_sidc.interpolate_data(target, key="ssn")
    ramp_sidc.run_normalization(norm_by="max")

    cycles = extrema.cycle_intervals.loc[:, "Cycle"]
    cycle_of = pd.Series(
        [next(n for n, interval in cycles.items() if t in interval) for t in target],
        index=target,
    )
    values = pd.Series(ramp_ssn(target), index=target)
    expected = values / values.groupby(cycle_of).transform("max")

    assert set(cycle_of) == {23, 24}
    nssn = ramp_sidc.interpolated.loc[:, "nssn"]
    assert nssn.to_numpy() == exact(expected.to_numpy())


def test_ssn_bands_default_to_half_width_two_centred_on_zero(ramp_sidc):
    """With no arguments the bands are (-2, 2], (2, 6], ... up to the series maximum.

    The defaults are key="ssn" and dssn=2.0: band centres run 0, 4, ... below
    the measured maximum of 8.0, i.e. centres 0 and 4. Hand-labelled:
    interpolated SSN 1.5 lands in (-2, 2], 3.5 and 5.5 in (2, 6], and 7.5 lies
    above the last band, so it is unlabelled.

    ON FAILURE: the code is wrong.
    """
    target = at_days(50, 250, 450, 650)
    ramp_sidc.interpolate_data(target)
    cut = ramp_sidc.cut_spec_by_ssn_band()

    intervals = ramp_sidc.ssn_band_intervals
    assert [(i.left, i.right) for i in intervals] == [(-2.0, 2.0), (2.0, 6.0)]
    assert intervals.name == "ssn_intervals"

    labelled = [None if pd.isna(v) else (v.left, v.right) for v in cut]
    assert labelled == [(-2.0, 2.0), (2.0, 6.0), (2.0, 6.0), None]
    assert ramp_sidc.spec_by_ssn_band is cut


def test_normalized_bands_accept_widths_below_one_only(ramp_sidc):
    """For ``nssn`` a half-width of exactly 1 is refused and 0.5 is accepted.

    The documented condition is dssn < 1, so the boundary value 1 itself
    must raise. With dssn = 0.5 and the per-cycle maximum of 1.0, the only
    band centre below the maximum is 0, so the band is (-0.5, 0.5].

    ON FAILURE: the code is wrong.
    """
    ramp_sidc.run_normalization(norm_by="max")
    with pytest.raises(ValueError, match="dssn < 1"):
        ramp_sidc.cut_spec_by_ssn_band(key="nssn", dssn=1.0)

    ramp_sidc.interpolate_data(at_days(50, 250), key="nssn")
    ramp_sidc.cut_spec_by_ssn_band(key="nssn", dssn=0.5)
    intervals = ramp_sidc.ssn_band_intervals
    assert [(i.left, i.right) for i in intervals] == [(-0.5, 0.5)]


def test_narrow_normalized_bands_touch_without_overlapping(ramp_sidc):
    """Half-width 0.05 on ``nssn`` gives ten touching bands, and pd.cut accepts them.

    Band centres run 0, 0.1, ..., 0.9 below the per-cycle maximum of 1.0, so
    the edges are -0.05, 0.05, ..., 0.95 and each band's right edge is the
    next band's left edge. Each interpolated value lies inside its label.

    ON FAILURE: the code is wrong.
    """
    ramp_sidc.run_normalization(norm_by="max")
    ramp_sidc.interpolate_data(at_days(50, 250, 450), key="nssn")
    cut = ramp_sidc.cut_spec_by_ssn_band(key="nssn", dssn=0.05)

    intervals = ramp_sidc.ssn_band_intervals
    assert len(intervals) == 10
    assert intervals.left.to_numpy() == exact(np.arange(10) / 10 - 0.05)
    assert intervals.right[-1] == exact(0.95)
    assert (intervals.right[:-1] == intervals.left[1:]).all()

    values = ramp_sidc.interpolated.loc[:, "nssn"]
    assert all(band.left < v <= band.right for v, band in zip(values, cut))


def test_ssn_bands_of_an_all_zero_series_are_empty(fake_home, ramp_index):
    """A series whose maximum is 0 has no band centres below it: every label is NaN.

    ON FAILURE: the code is wrong.
    """
    frame = pd.DataFrame({"ssn": 0.0, "std": 5.0, "n_obs": 25}, index=ramp_index)
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")
    indicator.interpolate_data(at_days(50, 250))

    assert indicator.cut_spec_by_ssn_band().isna().all()
    assert len(indicator.ssn_band_intervals) == 0


def test_ssn_bands_for_a_column_never_interpolated_raise_key_error(ramp_sidc):
    """Banding ``nssn`` when only ``ssn`` was interpolated raises KeyError naming it.

    The message names the missing column and that ``interpolated`` lacks it.

    ON FAILURE: the code is wrong.
    """
    ramp_sidc.run_normalization(norm_by="max")
    ramp_sidc.interpolate_data(at_days(50, 250), key="ssn")
    with pytest.raises(KeyError, match="`interpolated` has no column 'nssn'"):
        ramp_sidc.cut_spec_by_ssn_band(key="nssn", dssn=0.5)


# ---------------------------------------------------------------------------
# Plotting on a colour bar.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("vertical", [True, False])
def test_plot_on_colorbar_draws_the_requested_span(sidc, vertical):
    """The colour-bar overlay draws exactly the sunspot numbers in the window.

    Both lines (the white underlay and the dashed overlay) carry one point per
    monthly measurement between t0 and t1. The time axis is the epochs
    converted by matplotlib's date converter, and the value axis is checked as
    a property rather than against the scaling arithmetic: the plotted
    coordinates must be finite, must preserve the ordering of the sunspot
    numbers they represent, and must be an affine image of them, so equal
    sunspot numbers plot at equal positions and the overlay is readable
    against the colour bar's own scale.

    ON FAILURE: the sunspot overlay does not correspond to the interval it
    annotates. The code is wrong.
    """
    t0 = pd.Timestamp("2000-01-01")
    t1 = pd.Timestamp("2010-01-01")
    window = sidc.data.loc[t0:t1, "ssn"]

    figure, axes = plt.subplots()
    try:
        sidc.plot_on_colorbar(axes, t0, t1, vertical_cbar=vertical)

        assert len(axes.lines) == 2
        time_axis = 1 if vertical else 0
        value_axis = 1 - time_axis

        for line in axes.lines:
            np.testing.assert_allclose(
                line.get_data()[time_axis],
                matplotlib.dates.date2num(window.index),
            )

            values = np.asarray(line.get_data()[value_axis], dtype=float)
            assert np.isfinite(values).all()

            # Affine in the sunspot number: the residual of a straight-line
            # fit against ssn is zero, and the slope is positive.
            slope, intercept = np.polyfit(window.values, values, 1)
            assert slope > 0
            # Coordinates span the unit interval of the fresh axes.
            assert values == exact(slope * window.values + intercept, scale=1.0)
    finally:
        plt.close(figure)


def _value_axis_labels(axes):
    """Return the colour bar's major tick labels on the SSN (x) axis."""
    return [label.get_text() for label in axes.xaxis.get_ticklabels()]


def test_plot_on_colorbar_handles_a_low_activity_window(fake_home, seeded_index):
    """A window that never exceeds SSN 50 plots finite coordinates on a 0-100 scale.

    A plotted coordinate has to be finite to render at all. The scale top is
    the peak rounded up to the next 100 and never below 100, so a flat SSN of
    30 gives a top of 100 and ticks 0, 50, 100. On a fresh axes the x limits
    are (0, 1), so SSN 30 plots at 30 / 100 = 0.3.

    ON FAILURE: the code is wrong.
    """
    frame = pd.DataFrame(
        {"ssn": np.full(len(seeded_index), 30.0), "std": 5.0, "n_obs": 25},
        index=seeded_index,
    )
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    figure, axes = plt.subplots()
    try:
        indicator.plot_on_colorbar(
            axes, seeded_index[0], seeded_index[-1], vertical_cbar=True
        )
        for line in axes.lines:
            coords = np.asarray(line.get_data()[0], dtype=float)
            assert np.isfinite(coords).all()
            # Hand-computed: 30 / 100 of the fresh axes' unit span.
            assert coords == exact(0.3)
        # Hand-computed: top = 100, so ticks read 0, 100 / 2, 100.
        assert _value_axis_labels(axes) == ["0", "50", "100"]
    finally:
        plt.close(figure)


def test_plot_on_colorbar_rounds_a_peak_of_140_up_to_200(fake_home, seeded_index):
    """A peak of 140 gets a scale top of 200, so the line stays inside the scale.

    Rounding to the nearest 100 would give 100 and draw the peak beyond the
    colour bar. Rounded up, the top is 200 and the ticks read 0, 100, 200. On
    a fresh axes the x limits are (0, 1), so SSN 140 plots at 140 / 200 = 0.7
    and SSN 20 at 20 / 200 = 0.1, both inside [0, 1].

    ON FAILURE: the code is wrong.
    """
    ssn = np.full(len(seeded_index), 20.0)
    ssn[len(ssn) // 2] = 140.0
    frame = pd.DataFrame({"ssn": ssn, "std": 5.0, "n_obs": 25}, index=seeded_index)
    seed_cache(fake_home, "m13", frame)
    indicator = SIDC("m13")

    figure, axes = plt.subplots()
    try:
        indicator.plot_on_colorbar(
            axes, seeded_index[0], seeded_index[-1], vertical_cbar=True
        )
        for line in axes.lines:
            coords = np.asarray(line.get_data()[0], dtype=float)
            # Hand-computed: 140 / 200 and 20 / 200 of the unit span.
            assert coords.max() == exact(0.7)
            assert coords.min() == exact(0.1)
        assert _value_axis_labels(axes) == ["0", "100", "200"]
    finally:
        plt.close(figure)


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
