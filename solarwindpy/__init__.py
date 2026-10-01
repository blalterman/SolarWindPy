r"""Package for solar wind data analysis.

Primary focus is in situ solar wind measurements and the additional tools necessary for
context (e.g. solar activity indicies) and some simple plotting methods.
"""

from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _version

import pandas as _pd

from . import core, fitfunctions, instabilities, plotting, solar_activity, tools


def _configure_pandas() -> None:
    """Configure global pandas options used throughout SolarWindPy."""
    _pd.set_option("mode.chained_assignment", "raise")


_configure_pandas()

# ``pp`` is the one temporary nickname in the package: every other public
# object has exactly one import path, the module that defines it. It stays
# only until the author's analysis code migrates to ``solarwindpy.plotting``.
pp = plotting

__all__ = [
    "core",
    "fitfunctions",
    "instabilities",
    "plotting",
    "solar_activity",
    "tools",
]

__author__ = "B. L. Alterman <blaltermanphd@gmail.com>"

__name__ = "solarwindpy"

try:
    __version__ = _version(__name__)
except _PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
