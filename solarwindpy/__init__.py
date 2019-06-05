r"""Package for solar wind data analysis.

Primary focus is in situ solar wind measurements and the additional tools
necessary for context (e.g. solar activity indicies) and some simple plotting
methods.
"""

import pdb  # noqa: F401

from pkg_resources import get_distribution, DistributionNotFound

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

pd.set_option("mode.chained_assignment", "raise")
pd.set_option("mode.use_inf_as_na", True)

Plasma = core.plasma.Plasma
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
]

__author__ = "B. L. Alterman <balterma@umich.edu>"

__name__ = "solarwindpy"

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

# __version__ = "0.0.1.dev"
