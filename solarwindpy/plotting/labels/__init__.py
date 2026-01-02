#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels."""
__all__ = [
    "TeXlabel",
    "Vsw",
    "Count",
    "base",
    "special",
    "available_TeXlabel_measurements",
    "species_translation",
]

import pdb  # noqa: F401
from inspect import isclass
import pandas as pd

from . import base
from . import special
from . import composition
from . import elemental_abundance
from . import datetime  # noqa: F401
from . import chemistry  # noqa: F401

TeXlabel = base.TeXlabel
species_translation = base._run_species_substitution
Vsw = special.Vsw
Count = special.Count
Ion = composition.Ion
ChargeStateRatio = composition.ChargeStateRatio
ElementalAbundance = elemental_abundance.ElementalAbundance


def _clean_str_list_for_printing(data):
    """Format a list of strings as grouped, sorted text.

    Parameters
    ----------
    data : list of str
        Strings to format.

    Returns
    -------
    str
        Multiline string grouping entries by their first character.
    """

    upper = sorted([x for x in data if x[0].isupper()])
    [data.remove(u) for u in upper]

    gb = pd.DataFrame({"d": data, "g": pd.Series(data).str[0]}).groupby("g")
    agg = gb.apply(lambda x: ", ".join(sorted(x.d.values)))
    agg.loc["Upper"] = ", ".join(upper)
    agg.sort_index(inplace=True)
    agg = "\n".join(agg)
    return agg


def available_labels():
    """Print all available measurement, component and species labels."""

    m = sorted(list(base._trans_measurement.keys()) + list(base._templates.keys()))
    c = sorted(base._trans_component.keys())
    s = sorted(base._trans_species.keys())
    a = []
    for case in (special, composition, elemental_abundance, datetime):
        for x in dir(case):
            x = getattr(case, x)
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
