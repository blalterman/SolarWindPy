#!/usr/bin/env python
r"""Plotting utilities for :py:mod:`solarwindpy`."""

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
