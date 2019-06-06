#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels.
"""
import pdb  # noqa: F401
from inspect import isclass

from . import base
from . import special

TeXlabel = base.TeXlabel
Vsw = special.Vsw
Count = special.Count


def available_TeXlabel_measurements():
    m = sorted(list(base._trans_measurement.keys()) + list(base._templates.keys()))
    c = sorted(base._trans_component.keys())
    s = sorted(base._trans_species.keys())
    arbitrary = []
    for x in dir(special):
        x = getattr(special, x)
        if (
            isclass(x)
            and issubclass(x, special.ArbitraryLabel)
            and x != special.ArbitraryLabel
        ):
            arbitrary.append(x.__name__)

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
            m=", ".join(m), c=", ".join(c), s=", ".join(s), a=", ".join(arbitrary)
        )
    )
