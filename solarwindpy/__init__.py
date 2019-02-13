r"""Package for solar wind data analysis."""

import pdb  # noqa: F401

# import logging
from pkg_resources import get_distribution, DistributionNotFound

from .core import units_constants, base, vector, tensor, ions, plasma
from . import plotting

pp = plotting

__all__ = [
    "plasma",
    "ions",
    "tensor",
    "vector",
    "base",
    "units_constants",
    "plotting",
    "pp",
]

__author__ = "B. L. Alterman <balterma@umich.edu>"

__name__ = "solarwindpy"

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"

# __version__ = "0.0.1.dev"
