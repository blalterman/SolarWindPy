#!/usr/bin/env python
r"""Convenience accessors for histogram style plotters.

This module re-exports :class:`~solarwindpy.plotting.agg_plot.AggPlot`,
:class:`~solarwindpy.plotting.hist1d.Hist1D`, and
:class:`~solarwindpy.plotting.hist2d.Hist2D` so they can be imported directly from
:mod:`solarwindpy.plotting.histograms`.
"""

from . import agg_plot
from . import hist1d
from . import hist2d

AggPlot = agg_plot.AggPlot
Hist1D = hist1d.Hist1D
Hist2D = hist2d.Hist2D
