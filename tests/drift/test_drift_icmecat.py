# Spent-When: PERMANENT(SolarWindPy stops consuming the ICMECAT catalog)
# Supersedes: none
"""Drift assertions for the pinned HELIO4CAST ICMECAT catalog.

Restates every fact icmecat.ICMECAT_URL depends on
as a local, evaluable assertion: the pinned URL still resolves, no successor
version has appeared, the columns the module indexes are still present, and
SPACECRAFT_NAMES still matches the catalog exactly. ``TestLiveDownload`` and
``TestMultipleSpacecraft`` run ``ICMECAT`` itself on the live catalog.
"""

import pandas as pd
import pytest

from solarwindpy.solar_activity.icme.icmecat import (
    ICMECAT,
    ICMECAT_URL,
    SPACECRAFT_NAMES,
)

from ._drift import (
    assert_columns_present,
    assert_head_ok,
    assert_set_equal,
    assert_status,
)

pytestmark = pytest.mark.drift

# The eight columns icmecat.py actually indexes (see _prepare_intervals and
# _filter_by_spacecraft in src/solarwindpy/solar_activity/icme/icmecat.py).
REQUIRED_COLUMNS = [
    "icmecat_id",
    "icme_start_time",
    "mo_start_time",
    "mo_end_time",
    "mo_sc_heliodistance",
    "mo_sc_lat_heeq",
    "mo_sc_long_heeq",
    "sc_insitu",
]

_LOCATION = "src/solarwindpy/solar_activity/icme/icmecat.py::ICMECAT_URL"


def test_pinned_url_head_ok(head_status):
    """The pinned ICMECAT URL HEADs 200 with a plausible CSV payload."""
    info = head_status(ICMECAT_URL)
    assert_head_ok(
        info,
        min_content_length=100_000,
        content_type_substr="csv",
        fact="HELIO4CAST still serves the pinned ICMECAT version",
        location=_LOCATION,
        remedy="verify ICMECAT_URL against https://helioforecast.space/icmecat",
    )


def test_successor_url_not_yet_published(head_status):
    """The mechanically-derived v24 URL still 404s.

    One candidate derived from the pin. If this starts returning 200, a new
    catalog version exists and is invisible to the pinned URL.
    """
    successor_url = ICMECAT_URL.replace("_v23.csv", "_v24.csv")
    info = head_status(successor_url)
    assert_status(
        info,
        404,
        fact="HELIO4CAST published ICMECAT v24",
        location=_LOCATION,
        remedy=(
            "change the version in ICMECAT_URL; re-verify "
            "icmecat._DATETIME_COLUMNS and REQUIRED_COLUMNS against the new schema; "
            "refresh SPACECRAFT_NAMES from the new catalog's sc_insitu values."
        ),
    )


def test_required_columns_present(live_catalog):
    """The columns icmecat.py indexes are still present in the catalog."""
    assert_columns_present(
        live_catalog,
        REQUIRED_COLUMNS,
        fact="ICMECAT still carries the columns icmecat.py indexes",
        location=_LOCATION,
        remedy="re-verify REQUIRED_COLUMNS against the new schema",
    )


def test_spacecraft_names_match_catalog(live_catalog):
    """SPACECRAFT_NAMES equals the catalog's sc_insitu values exactly."""
    assert_set_equal(
        SPACECRAFT_NAMES,
        live_catalog["sc_insitu"].unique(),
        fact="SPACECRAFT_NAMES matches the catalog's sc_insitu values",
        location="src/solarwindpy/solar_activity/icme/icmecat.py::SPACECRAFT_NAMES",
        remedy="refresh SPACECRAFT_NAMES from the new catalog's sc_insitu values",
    )


# Each live test downloads into its own empty cache (tests/conftest.py), so
# it reaches the host and leaves the user's ~/.cache/solarwindpy untouched.
@pytest.mark.usefixtures("isolated_cache")
@pytest.mark.slow
class TestLiveDownload:
    """Checks that download the live ICMECAT catalog."""

    def test_instantiate_downloads_data(self):
        """ICMECAT() downloads the live catalog, which has more than 100 events.

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        cat = ICMECAT()
        assert len(cat) > 100, "Should have >100 ICME events"

    def test_ulysses_events_exist(self):
        """Live Ulysses events fall within the mission, 1990 to 2009.

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        cat = ICMECAT(spacecraft="Ulysses")
        assert len(cat) > 0, "Should have Ulysses events"
        assert cat.data["icme_start_time"].min().year >= 1990
        assert cat.data["icme_start_time"].max().year <= 2010

    def test_data_types_correct(self):
        """Live time columns parse to datetime64 and ids to strings.

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        cat = ICMECAT()
        assert pd.api.types.is_datetime64_any_dtype(cat.data["icme_start_time"])
        assert pd.api.types.is_datetime64_any_dtype(cat.data["mo_end_time"])
        # pandas 3 gives str, not object: do not revert to `== object`.
        assert pd.api.types.is_string_dtype(cat.data["icmecat_id"])

    def test_filter_then_contains(self):
        """The midpoint of the first live Ulysses strict interval is contained.

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        cat = ICMECAT(spacecraft="Ulysses")
        strict = cat.strict_intervals
        assert len(strict) > 0, "live catalog has no Ulysses strict intervals"
        first = strict.iloc[0]
        mid_time = (
            first["icme_start_time"]
            + (first["mo_end_time"] - first["icme_start_time"]) / 2
        )
        result = cat.contains(pd.Series([mid_time]))
        assert result.iloc[0], "Mid-point should be in interval"

    def test_summary_on_real_data(self):
        """summary() on live Ulysses data reports events and positive durations.

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        result = ICMECAT(spacecraft="Ulysses").summary()
        assert result["n_events"].iloc[0] > 0
        assert result["duration_median_hours"].iloc[0] > 0


@pytest.mark.usefixtures("isolated_cache")
class TestMultipleSpacecraft:
    """Test filtering to different spacecraft."""

    @pytest.mark.parametrize("spacecraft", ["Ulysses", "Wind", "STEREO-A"])
    def test_filter_to_spacecraft(self, spacecraft):
        """filter() on the live catalog keeps only the named spacecraft.

        Case-insensitive: the catalog spells Ulysses "ULYSSES".

        ON FAILURE: nothing is wrong with the package if helioforecast.space is
        unreachable; otherwise the code is wrong.
        """
        filtered = ICMECAT().filter(spacecraft)
        assert len(filtered) > 0
        assert all(filtered.data["sc_insitu"].str.lower() == spacecraft.lower())
