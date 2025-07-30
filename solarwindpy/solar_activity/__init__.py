#!/usr/bin/env python
"""Solar activity indices.

This subpackage contains helpers for downloading sunspot numbers and
other LISIRD data sources, along with simple plotting routines.
"""

__all__ = ["sunspot_number", "ssn", "lisird", "plots"]

import pdb  # noqa: F401
import pandas as pd

from . import sunspot_number  # noqa: F401
from . import lisird  # noqa: F401
from . import plots  # noqa: F401

ssn = sunspot_number


def get_all_indices():
    r"""Convenience function to collect Lyman-alpha, CA-K, F10.7, and M13 SSN data."""
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
