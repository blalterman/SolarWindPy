#!/usr/bin/env python
"""Helper functions and shortcuts for solar activity data.

This package consolidates the different solar activity indicators available in
:mod:`solarwindpy` and exposes convenience utilities for working with them.
"""

__all__ = ["sunspot_number", "ssn", "lisird", "plots"]

import pdb  # noqa: F401
import pandas as pd

from . import sunspot_number  # noqa: F401
from . import lisird  # noqa: F401
from . import plots  # noqa: F401

ssn = sunspot_number


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
    #     f107 = lisird.lisird.LISIRD("f107-penticton")
    MgII = lisird.lisird.LISIRD("MgII")
    sidc = ssn.sidc.SIDC("m13")

    mgII = MgII.data.mg_index
    mgII.index = pd.DatetimeIndex(MgII.data.index.date)

    sa = pd.concat(
        {
            "Lalpha": Lalpha.data.loc[:, "irradiance"],
            #             "F107": f107.data.loc[:, "adjusted_flux"],
            "ssn": sidc.data.loc[:, "ssn"],
            "MgII": mgII,
            "CaK": CaK.data.drop("milliseconds", axis=1),
        },
        axis=1,
    ).sort_index(
        axis=1
    )  # .dropna()
    #     sa.loc[:, "JD"] = sa.index.to_julian_date()

    return sa
