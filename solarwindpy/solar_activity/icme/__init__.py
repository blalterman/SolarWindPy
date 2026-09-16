"""HELIO4CAST ICMECAT - Interplanetary Coronal Mass Ejection Catalog.

This module provides access to the HELIO4CAST ICMECAT catalog for solar wind
analysis. See https://helioforecast.space/icmecat for the most up-to-date
rules of the road.
"""

from .icmecat import (
    ICMECAT,
    ICMECAT_URL,
    ICMECATDownloadError,
    SPACECRAFT_NAMES,
    RULES_OF_THE_ROAD,
)

__doc__ = f"""{__doc__}
Rules of the Road (as of January 2026)
--------------------------------------
{RULES_OF_THE_ROAD}

Example
-------
>>> from solarwindpy.solar_activity.icme import ICMECAT  # doctest: +SKIP
>>> cat = ICMECAT(spacecraft="Ulysses")  # doctest: +SKIP
>>> print(f"Found {{len(cat)}} Ulysses ICMEs")  # doctest: +SKIP
>>> in_icme = cat.contains(observations.index)  # doctest: +SKIP
"""

__all__ = [
    "ICMECAT",
    "ICMECAT_URL",
    "ICMECATDownloadError",
    "SPACECRAFT_NAMES",
]
