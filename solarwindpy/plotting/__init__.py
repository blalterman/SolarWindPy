#!/usr/bin/env python
"""Plotting utilities for :mod:`solarwindpy`.

The subpackage provides histogram and scatter plot helpers as well as
orbit and spiral plotting functions.
"""

__all__ = [
    "labels",
    "histograms",
    "scatter",
    "spiral",
    "orbits",
    "tools",
    "subplots",
    "save",
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

subplots = tools.subplots
save = tools.save
