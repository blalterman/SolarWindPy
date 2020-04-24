#!/usr/bin/env python
r"""Plotting utilities for :py:mod:`solarwindpy`.
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
]

from . import labels, histograms, scatter, spiral, orbits, tools

subplots = tools.subplots

subplots = tools.subplots
save = tools.save
