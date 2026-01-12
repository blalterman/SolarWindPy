#!/usr/bin/env python
r"""High level plotting API for :mod:`solarwindpy`.

This subpackage exposes a collection of plotters and helper functions that simplify
producing publication quality figures.
"""

from pathlib import Path
from matplotlib import pyplot as plt

# Apply solarwindpy style on import
_STYLE_PATH = Path(__file__).parent / "solarwindpy.mplstyle"
plt.style.use(_STYLE_PATH)

__all__ = [
    "labels",
    "histograms",
    "scatter",
    "spiral",
    "orbits",
    "tools",
    "subplots",
    "save",
    "nan_gaussian_filter",
    "select_data_from_figure",
]

from . import (
    labels,
    histograms,
    scatter,
    spiral,
    orbits,
    tools,
    select_data_from_figure,
)

subplots = tools.subplots
save = tools.save
nan_gaussian_filter = tools.nan_gaussian_filter
