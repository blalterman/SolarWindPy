"""Offline checks on the ICMECAT module constants.

Import paths are covered by ``tests/test_public_imports.py``; behavior by
``test_icmecat.py``. The opt-in drift suite (``tests/drift/test_drift_icmecat.py``)
checks these constants against the live catalog.
"""

from solarwindpy.solar_activity.icme.icmecat import ICMECAT_URL, SPACECRAFT_NAMES


class TestModuleConstants:
    """The pinned catalog source and its spacecraft spellings."""

    def test_url_constant_is_pinned_helio4cast_csv(self):
        """ICMECAT_URL is the HELIO4CAST ICMECAT CSV over https.

        ON FAILURE: the code is wrong, unless the author moved the pin to another
        host; update this test with it.
        """
        assert ICMECAT_URL.startswith("https://helioforecast.space/")
        assert "HELIO4CAST_ICMECAT_v" in ICMECAT_URL
        assert ICMECAT_URL.endswith(".csv")

    def test_spacecraft_names_use_catalog_spellings(self):
        """SPACECRAFT_NAMES spells names as the v23 catalog's sc_insitu column does.

        The catalog writes "ULYSSES" (all caps) and "SolarOrbiter" (no space),
        and has no ACE or Cassini events (see the comment above SPACECRAFT_NAMES
        and tests/drift/test_drift_icmecat.py).

        ON FAILURE: the code is wrong, unless the drift suite shows the catalog
        changed; then external fact drifted; update SPACECRAFT_NAMES.
        """
        assert {"ULYSSES", "SolarOrbiter", "Wind"} <= SPACECRAFT_NAMES
        assert not {"Ulysses", "Solar Orbiter", "ACE", "Cassini"} & SPACECRAFT_NAMES
