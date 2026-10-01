#!/usr/bin/env python
"""Solar activity indicators and event catalogs.

The SIDC sunspot number, with each observation labeled by its solar cycle and
normalized within that cycle, and the HELIO4CAST ICME catalog.
"""

__all__ = [
    "base",
    "icme",
    "plots",
    "sunspot_number",
]

from . import base
from . import icme
from . import plots
from . import sunspot_number
