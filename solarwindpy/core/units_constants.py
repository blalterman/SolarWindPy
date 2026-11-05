#!/usr/bin/env python
"""Definitions of common units and physical constants.

The values are derived from :mod:`scipy.constants`. All quantities stored in
the :class:`~solarwindpy.core.plasma.Plasma` object have a corresponding entry
in :class:`Constants` and can be converted using :class:`Units`, which reads
its factors from :mod:`solarwindpy.core.quantities`.
"""

__all__ = [
    "Constants",
    "Units",
]

from dataclasses import dataclass, field, make_dataclass

import pandas as pd

from scipy import constants
from scipy.constants import physical_constants

from . import quantities

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.

_misc_constants = {
    "e0": constants.epsilon_0,
    "mu0": constants.mu_0,
    "c": constants.c,
    "hbar": constants.hbar,
    "1AU [m]": constants.au,
    "gas constant": constants.R,
}

_kBoltzmann = {
    "J": constants.k,
    "eV": physical_constants["Boltzmann constant in eV/K"][0],
}

_polytropic_index = dict(par=3.0, per=2.0, scalar=5.0 / 3.0)

_m_in_mp = {
    "p": 1.0,
    "p1": 1.0,
    "p2": 1.0,
    "pm": 1.0,
    "p_bimax": 1.0,
    "a": physical_constants["alpha particle-proton mass ratio"][0],
    "a1": physical_constants["alpha particle-proton mass ratio"][0],
    "a2": physical_constants["alpha particle-proton mass ratio"][0],
    "a_bimax": physical_constants["alpha particle-proton mass ratio"][0],
    "e": physical_constants["electron-proton mass ratio"][0],
}

_charges = {
    "e": -constants.e,
    "p": constants.e,
    "p1": constants.e,
    "p2": constants.e,
    "pm": constants.e,
    "p_bimax": constants.e,
    "a": 2.0 * constants.e,
    "a1": 2.0 * constants.e,
    "a2": 2.0 * constants.e,
    "a_bimax": 2.0 * constants.e,
}

_charge_states = {
    "e": -1.0,
    "p": 1.0,
    "p1": 1.0,
    "p2": 1.0,
    "pm": 1.0,
    "p_bimax": 1.0,
    "a": 2.0,
    "a1": 2.0,
    "a2": 2.0,
    "a_bimax": 2.0,
}

_masses = {
    "e": constants.m_e,
    "p": constants.m_p,
    "p1": constants.m_p,
    "p2": constants.m_p,
    "pm": constants.m_p,  # proton moment
    "p_bimax": constants.m_p,
    "a_bimax": physical_constants["alpha particle mass"][0],
    "a": physical_constants["alpha particle mass"][0],
    "a1": physical_constants["alpha particle mass"][0],
    "a2": physical_constants["alpha particle mass"][0],
}

_m_amu = {
    "a": physical_constants["alpha particle mass in u"][0],
    "a1": physical_constants["alpha particle mass in u"][0],
    "a2": physical_constants["alpha particle mass in u"][0],
    "a_bimax": physical_constants["alpha particle mass in u"][0],
    "p": physical_constants["proton mass in u"][0],
    "p1": physical_constants["proton mass in u"][0],
    "p2": physical_constants["proton mass in u"][0],
    "pm": physical_constants["proton mass in u"][0],
    "p_bimax": physical_constants["proton mass in u"][0],
    "e": physical_constants["electron mass in u"][0],
}


@dataclass
class Constants:
    """Physical constants useful for solar wind calculations."""

    misc: pd.Series = field(default_factory=lambda: pd.Series(_misc_constants))
    kb: pd.Series = field(default_factory=lambda: pd.Series(_kBoltzmann))
    m_in_mp: pd.Series = field(default_factory=lambda: pd.Series(_m_in_mp))
    m: pd.Series = field(default_factory=lambda: pd.Series(_masses))
    m_amu: pd.Series = field(
        default_factory=lambda: pd.Series(_m_amu),
        metadata={"doc": "Masses in amu."},
    )
    charges: pd.Series = field(default_factory=lambda: pd.Series(_charges))
    charge_states: pd.Series = field(default_factory=lambda: pd.Series(_charge_states))
    polytropic_index: pd.Series = field(
        default_factory=lambda: pd.Series(_polytropic_index),
        metadata={"doc": "Polytropic index for various cases."},
    )

    def __post_init__(self) -> None:
        """Validate the shapes of series."""
        for s in (
            self.misc,
            self.kb,
            self.m_in_mp,
            self.m,
            self.m_amu,
            self.charges,
            self.charge_states,
            self.polytropic_index,
        ):
            if not isinstance(s, pd.Series):
                raise TypeError("Constant values must be pandas Series")


def _build_units():
    """Make ``Units``: one field per registry quantity that has an SI factor."""
    fields_ = [
        (key, float, field(default=q.si))
        for key, q in quantities.QUANTITIES.items()
        if q.si is not None
    ]
    doc = r"""SI value of one display unit for each quantity ``core`` converts.

    Multiply a stored value by its field to convert it to SI. The fields and
    their values come from :data:`~solarwindpy.core.quantities.QUANTITIES`, keyed
    by canonical name; the TeX of each display unit is the entry's ``units``.
    """
    return make_dataclass(
        "Units", fields_, namespace={"__doc__": doc, "__module__": __name__}
    )


Units = _build_units()
