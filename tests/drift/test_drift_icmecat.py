# Spent-When: PERMANENT(SolarWindPy stops consuming the ICMECAT catalog)
# Supersedes: none
"""Drift assertions for the pinned HELIO4CAST ICMECAT catalog.

Restates every fact solarwindpy/solar_activity/icme/icmecat.py:11 depends on
as a local, evaluable assertion: the pinned URL still resolves, no successor
version has appeared, the columns the module indexes are still present, and
SPACECRAFT_NAMES still matches the catalog exactly.
"""

import pytest

from solarwindpy.solar_activity.icme.icmecat import ICMECAT_URL, SPACECRAFT_NAMES

from ._drift import (
    assert_columns_present,
    assert_head_ok,
    assert_set_equal,
    assert_status,
)

pytestmark = pytest.mark.drift

# The eight columns icmecat.py actually indexes (see _prepare_intervals and
# _filter_by_spacecraft in solarwindpy/solar_activity/icme/icmecat.py).
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

_LOCATION = "solarwindpy/solar_activity/icme/icmecat.py:11 (ICMECAT_URL)"


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
            "change the version in ICMECAT_URL; re-verify _DATETIME_COLUMNS "
            "(icmecat.py:32) and REQUIRED_COLUMNS against the new schema; "
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
        location="solarwindpy/solar_activity/icme/icmecat.py:14 (SPACECRAFT_NAMES)",
        remedy="refresh SPACECRAFT_NAMES from the new catalog's sc_insitu values",
    )
