"""HELIO4CAST ICMECAT - Interplanetary Coronal Mass Ejection Catalog.

This module provides access to the HELIO4CAST ICMECAT catalog for solar wind
analysis. See https://helioforecast.space/icmecat for the most up-to-date
rules of the road.
"""

from . import icmecat

__doc__ = f"""{__doc__}
Rules of the Road (as of January 2026)
--------------------------------------
{icmecat.RULES_OF_THE_ROAD}

Example
-------
In normal use ``ICMECAT(spacecraft="Ulysses")`` downloads the catalog from
``icmecat.ICMECAT_URL``. This example stays offline by pointing that URL at a
small local catalog in the same CSV layout.

>>> import tempfile
>>> from pathlib import Path
>>> import pandas as pd
>>> from solarwindpy.solar_activity.icme.icmecat import ICMECAT
>>> catalog = pd.DataFrame({{
...     "icmecat_id": ["ICME_ULYSSES_1", "ICME_Wind_1"],
...     "sc_insitu": ["ULYSSES", "Wind"],
...     "icme_start_time": ["1998-01-01 00:00", "1998-03-01 00:00"],
...     "mo_start_time": ["1998-01-01 06:00", "1998-03-01 06:00"],
...     "mo_end_time": ["1998-01-02 00:00", "1998-03-02 00:00"],
... }})
>>> with tempfile.TemporaryDirectory() as d:
...     local = Path(d) / "icmecat.csv"
...     catalog.to_csv(local, index=False)
...     original_url = icmecat.ICMECAT_URL
...     icmecat.ICMECAT_URL = str(local)
...     try:
...         cat = ICMECAT(spacecraft="Ulysses")
...     finally:
...         icmecat.ICMECAT_URL = original_url
>>> print(f"Found {{len(cat)}} Ulysses ICMEs")
Found 1 Ulysses ICMEs
>>> observations = pd.DatetimeIndex(["1998-01-01 12:00", "1998-03-01 12:00"])
>>> cat.contains(observations).tolist()
[True, False]
"""

__all__ = ["icmecat"]
