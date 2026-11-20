#!/usr/bin/env python
"""Physical constants and unit conversions for SolarWindPy's calculations.

:class:`Constants` holds physical constants and per-species values (masses,
charges and charge states), taken from :mod:`scipy.constants`, and the
polytropic indices. :class:`Units` holds, for each quantity, the factor that
converts its display unit to SI, read from :mod:`solarwindpy.core.quantities`.
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

_misc_constants = {
    "e0": constants.epsilon_0,
    "mu0": constants.mu_0,
    "c": constants.c,
    "hbar": constants.hbar,
    "1AU [m]": constants.au,
    "gas constant": constants.R,
}

# Solar rotation rate [rad/s]: 2 pi over the 25.38 d sidereal period of the
# Carrington system, Thompson (2006), A&A 449, 791, sec. 2.2,
# doi:10.1051/0004-6361:20054262.
_SOLAR_ROTATION_RATE = 2.0 * constants.pi / (25.38 * constants.day)

_kBoltzmann = {
    "J": constants.k,
    "eV": physical_constants["Boltzmann constant in eV/K"][0],
}

# par and per are the double-adiabatic (CGL) indices, gamma_par = 3 and
# gamma_per = 2: Chew, Goldberger & Low (1956), Proc. R. Soc. Lond. A 236, 112,
# doi:10.1098/rspa.1956.0116. scalar is the isotropic monatomic gamma = 5/3.
_polytropic_index = dict(par=3.0, per=2.0, scalar=5.0 / 3.0)

# The particle each species label names. Every per-species constant below is
# read from this table and one value per particle.
_PARTICLE = {
    "e": "electron",
    "p": "proton",
    "p1": "proton",
    "p2": "proton",
    "pm": "proton",  # proton moment
    "p_bimax": "proton",
    "a": "alpha",
    "a1": "alpha",
    "a2": "alpha",
    "a_bimax": "alpha",
}


def _by_species(per_particle):
    """One value per species label, read from its particle's value."""
    return {s: per_particle[particle] for s, particle in _PARTICLE.items()}


_m_in_mp = _by_species(
    {
        "electron": physical_constants["electron-proton mass ratio"][0],
        "proton": 1.0,
        "alpha": physical_constants["alpha particle-proton mass ratio"][0],
    }
)

_charge_states = _by_species({"electron": -1.0, "proton": 1.0, "alpha": 2.0})

_charges = {s: q * constants.e for s, q in _charge_states.items()}

_masses = _by_species(
    {
        "electron": constants.m_e,
        "proton": constants.m_p,
        "alpha": physical_constants["alpha particle mass"][0],
    }
)

_m_amu = _by_species(
    {
        "electron": physical_constants["electron mass in u"][0],
        "proton": physical_constants["proton mass in u"][0],
        "alpha": physical_constants["alpha particle mass in u"][0],
    }
)


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
