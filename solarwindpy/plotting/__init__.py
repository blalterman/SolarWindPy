#!/usr/bin/env python
r"""High level plotting API for :mod:`solarwindpy`.

This subpackage exposes a collection of plotters and helper functions that simplify
producing publication quality figures.
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
