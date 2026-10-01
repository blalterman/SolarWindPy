#!/usr/bin/env python
"""Helper functions for solar activity data.

This package consolidates the different solar activity indicators available in
:mod:`solarwindpy` and provides :func:`get_all_indices` to combine them.
"""

__all__ = [
    "base",
    "get_all_indices",
    "icme",
    "lisird",
    "plots",
    "sunspot_number",
]

import pandas as pd

from . import base
from . import icme
from . import lisird
from . import plots
from . import sunspot_number


def get_all_indices():
    """Return a table of common solar activity indicators.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing Lyman-alpha, Calcium K line, monthly smoothed
        sunspot number, the Bremen MgII index, and other indices where
        available. The index is daily and missing data are preserved.
    """
    Lalpha = lisird.lisird.LISIRD("Lalpha")
    CaK = lisird.lisird.LISIRD("CaK")
    MgII = lisird.lisird.LISIRD("MgII")
    sidc = sunspot_number.sidc.SIDC("m13")

    mgII = MgII.data.mg_index
    mgII.index = pd.DatetimeIndex(MgII.data.index.date)

    sa = pd.concat(
        {
            "Lalpha": Lalpha.data.loc[:, "irradiance"],
            "ssn": sidc.data.loc[:, "ssn"],
            "MgII": mgII,
            "CaK": CaK.data.drop("milliseconds", axis=1),
        },
        axis=1,
        # The sources sample on different dates (SSN is monthly), so the
        # union of their indices must be sorted to stay chronological.
        sort=True,
    ).sort_index(axis=1)

    return sa
