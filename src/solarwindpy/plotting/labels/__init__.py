#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels."""

__all__ = [
    "available",
    "base",
    "chemistry",
    "composition",
    "datetime",
    "elemental_abundance",
    "special",
]

from inspect import isclass
import pandas as pd

from ...core import quantities as _quantities
from . import base
from . import chemistry
from . import composition
from . import datetime
from . import elemental_abundance
from . import special


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


def available():
    """Print all available measurement, component and species labels.

    The listing has four parts: the measurements and components
    :class:`~solarwindpy.plotting.labels.base.TeXlabel` translates, grouped
    by first letter; the species it translates; and the special label
    classes, the subclasses of
    :class:`~solarwindpy.plotting.labels.special.ArbitraryLabel` in this
    package. It is printed, not returned.

    Examples
    --------
    >>> import contextlib
    >>> import io
    >>> from solarwindpy.plotting import labels
    >>> printed = io.StringIO()
    >>> with contextlib.redirect_stdout(printed):
    ...     labels.available()
    >>> lines = printed.getvalue().splitlines()
    >>> lines[0]
    'TeXlabel knows'
    >>> [lines[i] for i in range(len(lines) - 1) if set(lines[i + 1]) == {"-"}]
    ['Measurements', 'Components', 'Species', 'Special']
    >>> special = lines[lines.index("Special") + 2].split(", ")
    >>> "ManualLabel" in special and "Epoch" in special
    True
    """

    m = sorted(_quantities.QUANTITIES)
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
""".format(m=m, c=c, s=s, a=a)
    )
