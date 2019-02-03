r"""Package for solar wind data analysis."""

import pdb
import logging
from pkg_resources import get_distribution, DistributionNotFound

from . import units_constants, base, vector, tensor, ions, plasma

__all__ = ["plasma", "ions", "tensor", "vector", "base", "units_constants"]

__author__ = "B. L. Alterman <balterma@umich.edu>"

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "unknown"
    
# __version__ = "0.0.1.dev"
