#!/usr/bin/env python
"""Units and constants for transforming into and out of SI units.

All data is sourced from :py:mod:`scipy.constants` and :py:attr:`scipy.constants.physical_constants`. Every quantity stored in :py:class:`~solarwindpy.core.plasma.Plasma` and contained objects should have a entry in :py:class:`Constants`.
"""

import pdb  # noqa: F401
import pandas as pd

from scipy import constants
from scipy.constants import physical_constants

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")


class Constants(object):
    def __init__(self):
        pass

    @property
    def misc(self):
        return pd.Series(
            {
                "e0": constants.epsilon_0,
                "mu0": constants.mu_0,
                "c": constants.c,
                "gamma": 5.0 / 3.0,
                "hbar": physical_constants["Planck constant over 2 pi"][0],
                "1AU [m]": constants.au,
                "Re [m]": 6378.1e3,  # Earth Radius in meters
                "Rs [m]": 695.508e6,  # Sun Radius in meters
            }
        )

    @property
    def kb(self):
        ev = "Boltzmann constant in eV/K"
        return pd.Series({"J": constants.k, "eV": physical_constants[ev][0]})

    @property
    def m_in_mp(self):
        mamp = physical_constants["alpha particle-proton mass ratio"][0]
        memp = physical_constants["electron-proton mass ratio"][0]
        return pd.Series(
            {
                "p": 1.0,
                "p1": 1.0,
                "p2": 1.0,
                "pm": 1.0,
                "p_bimax": 1.0,
                "a": mamp,
                "a1": mamp,
                "a2": mamp,
                "e": memp,
            }
        )

    @property
    def m(self):
        ma = physical_constants["alpha particle mass"][0]
        out = {
            "e": constants.m_e,
            "p": constants.m_p,
            "p1": constants.m_p,
            "p2": constants.m_p,
            "pm": constants.m_p,  # proton moment
            "p_bimax": constants.m_p,
            "a": ma,
            "a1": ma,
            "a2": ma,
        }
        return pd.Series(out)

    @property
    def m_amu(self):
        r"""
        Masses in amu.
        """
        a = physical_constants["alpha particle mass in u"][0]
        p = physical_constants["proton mass in u"][0]
        e = physical_constants["electron mass in u"][0]
        out = {
            "a": a,
            "a1": a,
            "a2": a,
            "p": p,
            "p1": p,
            "p2": p,
            "pm": p,
            "e": e,
            "p_bimax": p,
        }
        return pd.Series(out)

    @property
    def charges(self):
        a = 2.0 * constants.e
        p = constants.e
        e = -constants.e
        out = {
            "e": e,
            "p": p,
            "p1": p,
            "p2": p,
            "pm": p,
            "a": a,
            "a1": a,
            "a2": a,
            "p_bimax": p,
        }
        return pd.Series(out)

    @property
    def charge_states(self):
        out = {
            "e": -1.0,
            "p": 1.0,
            "p1": 1.0,
            "p2": 1.0,
            "pm": 1.0,
            "p_bimax": 1.0,
            "a": 2.0,
            "a1": 2.0,
            "a2": 2.0,
        }
        return pd.Series(out)


class Units(object):
    def __init__(self):
        pass

    @property
    def bfield(self):
        return 1e-9

    @property
    def b(self):
        return self.bfield

    @property
    def v(self):
        return 1e3

    @property
    def w(self):
        return self.v

    @property
    def dv(self):
        return self.v

    @property
    def ca(self):
        return self.v

    @property
    def cs(self):
        return self.v

    @property
    def cfms(self):
        return self.v

    @property
    def pth(self):
        return 1e-12

    @property
    def temperature(self):
        return 1e5

    @property
    def n(self):
        return 1e6

    @property
    def rho(self):
        return self.n * constants.m_p

    @property
    def beta(self):
        return 1.0

    @property
    def lnlambda(self):
        return 1.0

    @property
    def nuc(self):
        return 1e-7

    @property
    def nc(self):
        return 1.0

    @property
    def qpar(self):
        return 1e-4

    @property
    def distance2sun(self):
        return 1.0  # unit stored in [m]
