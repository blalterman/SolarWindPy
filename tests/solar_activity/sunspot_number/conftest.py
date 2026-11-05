# Spent-When: PERMANENT(the sunspot-number tests stop seeding the download cache)
# Supersedes: none
"""Fixtures that seed the download cache with SILSO sunspot series.

The cache holds what SILSO serves: semicolon-separated, headerless rows. A
13-month smoothed row is year; month; decimal year; sunspot number; standard
deviation; observation count; definitive flag, with -1 marking a missing value
(https://www.sidc.be/SILSO/infosnmstot).
"""

import numpy as np
import pytest

from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID


def silso_m13(frame):
    """``frame`` (monthly index; ``ssn``, ``std``, ``n_obs``) in SILSO's m13 layout.

    Floats are written with ``repr``, which round-trips exactly, and NaN as
    SILSO's -1. The decimal year is the month's middle, as SILSO gives it.
    """

    def field(value):
        return "-1" if np.isnan(value) else repr(float(value))

    def count(value):
        return "-1" if np.isnan(value) else str(int(value))

    return "".join(
        f"{t.year};{t.month:02d};{t.year + (t.month - 0.5) / 12:.3f};"
        f"{field(ssn)};{field(std)};{count(n)};1\n"
        for t, ssn, std, n in zip(
            frame.index, frame["ssn"], frame["std"], frame["n_obs"].astype(float)
        )
    )


@pytest.fixture
def seed_m13(seed_cache):
    """Return ``seed(frame, age_days=0, url=None)``: cache ``frame`` as an m13 download.

    ``url`` defaults to the URL ``SIDC("m13")`` downloads from, read when the
    seed is called, so a test that redirects that URL seeds the redirected one.
    """

    def _seed(frame, age_days=0.0, url=None):
        url = SIDC_ID("m13").url if url is None else url
        return seed_cache(url, silso_m13(frame), age_days)

    return _seed
