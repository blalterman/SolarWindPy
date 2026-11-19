"""HELIO4CAST ICMECAT - Interplanetary Coronal Mass Ejection Catalog.

This package provides the HELIO4CAST ICMECAT catalog for solar wind analysis
through :class:`~solarwindpy.solar_activity.icme.icmecat.ICMECAT`, whose
docstring carries a worked example.

Follow the ICMECAT rules of the road at the HELIO4CAST site
(https://helioforecast.space/icmecat) when publishing results that use the
catalog.
"""

from . import icmecat

__all__ = ["icmecat"]
