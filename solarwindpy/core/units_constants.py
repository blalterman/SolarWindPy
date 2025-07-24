#!/usr/bin/env python
"""Units and constants for transforming into and out of SI units.

All data is sourced from :py:mod:`scipy.constants` and :py:attr:`scipy.constants.physical_constants`. Every quantity stored in :py:class:`~solarwindpy.core.plasma.Plasma` and contained objects should have a entry in :py:class:`Constants`.
"""

import pandas as pd

from scipy import constants
from scipy.constants import physical_constants

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

_misc_constants = {
    "e0": constants.epsilon_0,
    "mu0": constants.mu_0,
    "c": constants.c,
    #     "gamma": 5.0 / 3.0,
    "hbar": physical_constants["Planck constant over 2 pi"][0],
    "1AU [m]": constants.au,
    "Re [m]": 6378.1e3,  # Earth Radius in meters
    "Rs [m]": 695.508e6,  # Sun Radius in meters
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


class Constants(object):
    def __init__(self):
        pass

    @property
    def misc(self):
        return pd.Series(_misc_constants)

    @property
    def kb(self):
        return pd.Series(_kBoltzmann)

    @property
    def m_in_mp(self):
        return pd.Series(_m_in_mp)

    @property
    def m(self):
        return pd.Series(_masses)

    @property
    def m_amu(self):
        r"""Masses in amu."""
        return pd.Series(_m_amu)

    @property
    def charges(self):
        return pd.Series(_charges)

    @property
    def charge_states(self):
        return pd.Series(_charge_states)

    @property
    def polytropic_index(self):
        r"""The polytropic index. Some example cases are [1, pg 27].

            ======= =========================== ==========
             gamma              use               alias
            ======= =========================== ==========
             3       Motion parallel to B        "par"
             2       Motion perpendicular to B   "per"
             5/3     Isotropic plasma            "scalar"
            ======= =========================== ==========

        References
        ----------
        [1] Siscoe, G. L. (1983). Solar System Magnetohydrodynamics (pp.
            11–100). https://doi.org/10.1007/978-94-009-7194-3_2
        """
        return pd.Series(_polytropic_index)


class Units(object):
    def __init__(self):
        pass

    @property
    def bfield(self):
        r""":math:`[\mathrm{nT}]`"""
        return 1e-9

    @property
    def b(self):
        r""":math:`[\mathrm{nT}]`"""
        return self.bfield

    @property
    def v(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return 1e3

    @property
    def w(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return self.v

    @property
    def dv(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return self.v

    @property
    def ca(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return self.v

    @property
    def cs(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return self.v

    @property
    def cfms(self):
        r""":math:`[\mathrm{km \, s^{-1}}]`"""
        return self.v

    @property
    def pth(self):
        r""":math:`[\mathrm{pPa}]`"""
        return 1e-12

    @property
    def temperature(self):
        r""":math:`[10^{5} \mathrm{K}]`"""
        return 1e5

    @property
    def n(self):
        r""":math:`[\mathrm{cm^{-3}}]`"""
        return 1e6

    @property
    def rho(self):
        r""":math:`[\mathrm{cm^{-3} \, m_p}]`"""
        return self.n * constants.m_p

    @property
    def beta(self):
        r""":math:`[\#]`"""
        return 1.0

    @property
    def lnlambda(self):
        r""":math:`[\#]`"""
        return 1.0

    @property
    def nuc(self):
        r""":math:`[10^{-7} \mathrm{Hz}]`"""
        return 1e-7

    @property
    def nc(self):
        r""":math:`[\#]`"""
        return 1.0

    @property
    def qpar(self):
        r""":math:`[\mathrm{mW \, cm^{-2}}]`"""
        return 1e-7

    @property
    def distance2sun(self):
        r""":math:`[m]`"""
        return 1.0

    @property
    def specific_entropy(self):
        r""":math:`[\mathrm{eV \, cm^2 \, m_p^{-5/3}}]`"""
        return 1e4 / constants.e
