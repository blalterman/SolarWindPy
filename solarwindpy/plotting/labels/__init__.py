#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels.
"""
__all__ = [
    "TeXlabel",
    "Vsw",
    "Count",
    "base",
    "special",
    "available_TeXlabel_measurements",
]

import pdb  # noqa: F401
from inspect import isclass
import pandas as pd

from . import base
from . import special

TeXlabel = base.TeXlabel
Vsw = special.Vsw
Count = special.Count


def _clean_str_list_for_printing(data):
    # Clean and sort the measurements.
    upper = sorted([x for x in data if x[0].isupper()])
    [data.remove(u) for u in upper]

    gb = pd.DataFrame({"d": data, "g": pd.Series(data).str[0]}).groupby("g")
    agg = gb.apply(lambda x: ", ".join(sorted(x.d.values)))
    agg.loc["Upper"] = ", ".join(upper)
    agg.sort_index(inplace=True)
    agg = "\n".join(agg)
    return agg


def available_labels():
    m = sorted(list(base._trans_measurement.keys()) + list(base._templates.keys()))
    c = sorted(base._trans_component.keys())
    s = sorted(base._trans_species.keys())
    a = []
    for x in dir(special):
        x = getattr(special, x)
        if (
            isclass(x)
            and issubclass(x, special.ArbitraryLabel)
            and x != special.ArbitraryLabel
        ):
            a.append(x.__name__)

    m = _clean_str_list_for_printing(m)
    c = _clean_str_list_for_printing(c)
    #     s = _clean_str_list_for_printing(s)
    s = ", ".join(s)

    a = sorted(a)
    a = ", ".join(a)

    print(
        r"""TeXlabel knows

Measurements
------------
{m}

Components
----------
{c}

Species
-------
{s}

Special
-------
{a}
""".format(
            m=m, c=c, s=s, a=a
        )
    )
