"""Integration tests for ICMECAT class.

These tests require network access and download real data.
Mark with pytest.mark.integration to skip in CI without network.
"""

import pytest
import pandas as pd


@pytest.mark.integration
@pytest.mark.slow
class TestLiveDownload:
    """Integration tests that download real ICMECAT data."""

    def test_instantiate_downloads_data(self):
        """ICMECAT() downloads real data."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT()

        assert len(cat) > 100, "Should have >100 ICME events"

    def test_ulysses_events_exist(self):
        """Real catalog contains Ulysses events."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT(spacecraft="Ulysses")

        assert len(cat) > 0, "Should have Ulysses events"
        # Ulysses mission: 1990-2009
        min_year = cat.data["icme_start_time"].min().year
        max_year = cat.data["icme_start_time"].max().year
        assert min_year >= 1990
        assert max_year <= 2010

    def test_data_types_correct(self):
        """Real data has correct dtypes."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT()

        assert pd.api.types.is_datetime64_any_dtype(cat.data["icme_start_time"])
        assert pd.api.types.is_datetime64_any_dtype(cat.data["mo_end_time"])
        assert cat.data["icmecat_id"].dtype == object

    def test_filter_then_contains(self):
        """End-to-end: filter to Ulysses, check containment."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT(spacecraft="Ulysses")

        # Get first strict interval
        strict = cat.strict_intervals
        if len(strict) > 0:
            first = strict.iloc[0]
            mid_time = first["icme_start_time"] + (
                first["mo_end_time"] - first["icme_start_time"]
            ) / 2

            times = pd.Series([mid_time])
            result = cat.contains(times)

            assert result.iloc[0] == True, "Mid-point should be in interval"

    def test_summary_on_real_data(self):
        """summary() works on real data."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT(spacecraft="Ulysses")

        result = cat.summary()

        assert result["n_events"].iloc[0] > 0
        assert result["duration_median_hours"].iloc[0] > 0


@pytest.mark.integration
class TestMultipleSpacecraft:
    """Test filtering to different spacecraft."""

    @pytest.mark.parametrize("spacecraft", ["Ulysses", "Wind", "ACE", "STEREO-A"])
    def test_filter_to_spacecraft(self, spacecraft):
        """Can filter to various spacecraft."""
        from solarwindpy.solar_activity.icme import ICMECAT
        cat = ICMECAT()
        filtered = cat.filter(spacecraft)

        # Some spacecraft may have no events, that's OK
        if len(filtered) > 0:
            # Case-insensitive comparison (catalog uses ULYSSES, user may pass Ulysses)
            assert all(filtered.data["sc_insitu"].str.lower() == spacecraft.lower())
