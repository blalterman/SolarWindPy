"""Integration tests for ICMECAT against the live HELIO4CAST catalog.

These download real data and are opt-in (``integration`` marker; see
``tests/conftest.py``). The ``_no_network`` fixture in this directory's
``conftest.py`` leaves ``ICMECAT_URL`` alone for them.
"""

import pandas as pd
import pytest

from solarwindpy.solar_activity.icme.icmecat import ICMECAT


@pytest.mark.integration
@pytest.mark.slow
class TestLiveDownload:
    """Integration tests that download real ICMECAT data."""

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


@pytest.mark.integration
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
