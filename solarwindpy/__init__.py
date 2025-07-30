"""Top-level package for SolarWindPy.

SolarWindPy provides utilities for analysing in situ solar wind
measurements.  The package is organised into several submodules:

``core``
    Fundamental classes such as :class:`~solarwindpy.core.Plasma` and
    :class:`~solarwindpy.core.Vector`.
``plotting``
    Convenience routines for visualising data.
``tools``
    Miscellaneous helper functions for data manipulation.
``solar_activity``
    Functions for retrieving solar activity indices.
``fitfunctions``
    Generic curve-fitting utilities.
``instabilities``
    Tools for evaluating plasma instabilities.
"""

import pdb  # noqa: F401

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:  # pragma: no cover - Python <3.8
    from importlib_metadata import PackageNotFoundError, version

import pandas as pd

from .core import (
    units_constants,
    base,
    vector,
    tensor,
    ions,
    plasma,
    spacecraft,
    alfvenic_turbulence,
)
from . import core, plotting, solar_activity, tools, fitfunctions
from . import instabilities  # noqa: F401


def _configure_pandas() -> None:
    """Configure global pandas options used throughout SolarWindPy."""

    pd.set_option("mode.chained_assignment", "raise")


_configure_pandas()

Plasma = core.plasma.Plasma
at = alfvenic_turbulence
sc = spacecraft
pp = plotting
sa = solar_activity
Hist1D = plotting.histograms.Hist1D
Hist2D = plotting.histograms.Hist2D
TeXlabel = plotting.labels.TeXlabel

__all__ = [
    "core",
    "plasma",
    "ions",
    "tensor",
    "vector",
    "spacecraft",
    "sc",
    "alfvenic_turbulence",
    "at",
    "base",
    "units_constants",
    "plotting",
    "pp",
    "solar_activity",
    "sa",
    "tools",
    "fitfunctions",
    "instabilities",
]

__author__ = "B. L. Alterman <balterma@umich.edu>"

__name__ = "solarwindpy"

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"

# __version__ = "0.0.1.dev"
