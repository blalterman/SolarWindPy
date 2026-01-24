"""HELIO4CAST ICMECAT - Interplanetary Coronal Mass Ejection Catalog.

This module provides access to the HELIO4CAST ICMECAT catalog for solar wind
analysis. See https://helioforecast.space/icmecat for the most up-to-date
rules of the road.

Rules of the Road (as of January 2026)
--------------------------------------
    If this catalog is used for results that are published in peer-reviewed
    international journals, please contact chris.moestl@outlook.com for
    possible co-authorship.

    Cite the catalog with: Möstl et al. (2020)
    DOI: 10.6084/m9.figshare.6356420

Example
-------
>>> from solarwindpy.solar_activity.icme import ICMECAT  # doctest: +SKIP
>>> cat = ICMECAT(spacecraft="Ulysses")  # doctest: +SKIP
>>> print(f"Found {len(cat)} Ulysses ICMEs")  # doctest: +SKIP
>>> in_icme = cat.contains(observations.index)  # doctest: +SKIP
"""

from .icmecat import (
    ICMECAT,
    ICMECAT_URL,
    SPACECRAFT_NAMES,
)

__all__ = [
    "ICMECAT",
    "ICMECAT_URL",
    "SPACECRAFT_NAMES",
]
