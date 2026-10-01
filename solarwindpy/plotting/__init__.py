#!/usr/bin/env python
r"""High level plotting API for :mod:`solarwindpy`.

This subpackage holds plotters and helper functions that simplify producing
publication quality figures. Each object is imported from the module that
defines it, for example :class:`solarwindpy.plotting.hist2d.Hist2D` and
:func:`solarwindpy.plotting.tools.subplots`.
"""

from pathlib import Path
from matplotlib import pyplot as plt

# Apply solarwindpy style on import
_STYLE_PATH = Path(__file__).parent / "solarwindpy.mplstyle"
plt.style.use(_STYLE_PATH)

__all__ = [
    "agg_plot",
    "base",
    "hist1d",
    "hist2d",
    "labels",
    "scatter",
    "spiral",
    "tools",
]

from . import (  # noqa: E402 - imports after style application is intentional
    agg_plot,
    base,
    hist1d,
    hist2d,
    labels,
    scatter,
    spiral,
    tools,
)
