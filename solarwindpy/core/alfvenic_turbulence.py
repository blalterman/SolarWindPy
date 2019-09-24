#!/usr/bin/env python
"""Tools for calculating Alfvenic turbulence quantities derived from Elasser variables.

Bibliography
------------
[1] Bruno, R., & Carbone, V. (2013). The solar wind as a turbulence laboratory.
    Living Reviews in Solar Physics, 10(1), 1–208. https://doi.org/10.12942/lrsp-2013-2
[2] Telloni, D., & Bruno, R. (2016). Linking fluid and kinetic scales in solar
    wind turbulence. Monthly Notices of the Royal Astronomical Society: Letters,
    463(1), L79–L83. https://doi.org/10.1093/mnrasl/slw135
[3] Woodham, L. D., Wicks, R. T., Verscharen, D. & Owen, C. J. The Role of Proton-
    Cyclotron Resonance as a Dissipation Mechanism in Solar Wind Turbulence: A
    Statistical Study at Ion-Kinetic Scales. Astrophys. J. 856, 49 (2018).
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd

from collections import namedtuple

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
except ImportError:
    import base

AlvenicTurbAveraging = namedtuple("AlvenicTurbAveraging", "window,min_periods")


class AlfvenicTurbulence(base.Core):
    r"""Handle and calculate Alfvenic turbulence quantities using the Elsasser
    variables following Section B.3.1 in [1].

    Lloyd Woodham <https://orcid.org/0000-0003-2845-4250> helped me define these
    calculations at the 2018 AGU Fall Meeting and understand [1]. Please cite [3] if
    using this module.

    Parameters
    ----------
    velocity : pd.DataFrame, pd.Series (?)
        The velocity vector in the same basis as `bfield`.
        Can be a single species, a CoM species, or a differential flow. The
        differential flow case is an area of curiosity for me and I do not
        suggest passing it as an input.
        Expect [v] = km/s (i.e. default stored in `units_constants.Units`).
    bfield : pd.DataFrame, pd.Series (?)
        Magnetic field vector in the same basis as `velocity`.
        Expect [b] = nT (i.e. default stored in `units_contants.Units`).
    rho : pd.Series
        The total mass density of the plasma used to define velocity.
        Expect [rho] = m_p / cm^3 (i.e. default stored in
        `units_constants.Units`).
    species: str
        The species string. Can contain `+`. Can contain at most one `,`.

    Properties
    ----------
    data, velocity, v, bfield, b, species, z_plus, zp, z_minus, zm, e_plus, ep,
    e_minus, em, kinetic_energy, ev, magnetic_energy, eb, total_energy, etot,
    residual_energy, eres, normalized_residual_energy, eres_norm, sigma_r,
    cross_helicity, normalized_cross_helicity, sigma_c, alfven_ratio, rA,
    elsasser_ratio, rE

    Methods
    -------
    set_data

    Notes
    -----

    """

    def __init__(self, velocity, bfield, rho, species, **kwargs):
        r"""Initialize an :py:class:`AlfvenicTurbulence` object.

        Parameters
        ----------
        velocity: pd.DataFrame
            Vector velocity measurments.
        bfield: pd.DataFrame
            Vector mangetic field measurements.
        rho: pd.Series
            Mass density measurments, used to put `bfield` into Alfven units.
        kwargs:
            Passed to `rolling` method when mean-subtracing in `set_data`.
        """
        #         print("<Module>",
        #               "__init__",
        #               sep="\n",
        #               end="\n")

        super(AlfvenicTurbulence, self).__init__()
        self.set_data(velocity, bfield, rho, species, **kwargs)

    @property
    def data(self):
        r"""Mean-subtracted quantities used to calculated Elsasser variables.
        """
        return self._data

    @property
    def averaging_info(self):
        r"""Averaging window and minimum number of measurements / average used
        in calculating background component in :math:`\delta B` and :math:`\delta v`.
        """
        return self._averaging_info

    @property
    def measurements(self):
        r"""Measurements used to calcualte mean-subtracted `data`.
        """
        return self._measurements

    @property
    def velocity(self):
        r"""Velocity in Plasma's v-units.
        """
        return self.data.loc[:, "v"]

    @property
    def v(self):
        r"""Shortcut for `AlfvenicTurbulence.velocity`
        """
        return self.velocity

    @property
    def bfield(self):
        r"""Magnetic field in Alfven units, where velocity is stored in Plasma's
        v-units.
        """
        return self.data.loc[:, "b"]

    @property
    def b(self):
        r"""Shortcut for `AlfvenicTurbulence.bfield`.
        """
        return self.bfield

    @property
    def species(self):
        r"""Species used to create `AlfvenicTurbulence`. Defines mass density in Alfven
        units.
        """
        return self._species

    @property
    def z_plus(self):
        r"""Z+ Elsasser variable.
        """
        zp = self.v.add(self.b, axis=1)
        return zp

    @property
    def zp(self):
        r"""Shortcut for `AlfvenicTurbulence.z_plus`.
        """
        return self.z_plus

    @property
    def z_minus(self):
        r"""Z- Elsasser variable.
        """
        zm = self.v.subtract(self.b, axis=1)
        return zm

    @property
    def zm(self):
        r"""Shortcut for `AlfvenicTurbulence.z_minus`.
        """
        return self.z_minus

    @property
    def e_plus(self):
        # I took the averages before I created the +/-z quantities in my
        # previous test cases. Based on a more detailed read of Bruno and
        # Carbone, I calculate +/-z before I take averages. Note that because
        # I am adding v and b, the differene shouldn't matter.
        ep = 0.5 * self.zp.pow(2).sum(axis=1)
        return ep

    @property
    def ep(self):
        return self.e_plus

    @property
    def e_minus(self):
        em = 0.5 * self.zm.pow(2).sum(axis=1)
        return em

    @property
    def em(self):
        return self.e_minus

    @property
    def kinetic_energy(self):
        ev = 0.5 * self.v.pow(2).sum(axis=1)
        return ev

    @property
    def ev(self):
        return self.kinetic_energy

    @property
    def magnetic_energy(self):
        eb = 0.5 * self.b.pow(2).sum(axis=1)
        return eb

    @property
    def eb(self):
        return self.magnetic_energy

    @property
    def total_energy(self):
        return self.ev.add(self.eb, axis=0)

    @property
    def etot(self):
        return self.total_energy

    @property
    def residual_energy(self):
        return self.ev.subtract(self.eb, axis=0)

    @property
    def eres(self):
        return self.residual_energy

    @property
    def normalized_residual_energy(self):
        return self.eres.divide(self.etot, axis=0)

    @property
    def eres_norm(self):
        return self.normalized_residual_energy

    @property
    def sigma_r(self):
        return self.normalized_residual_energy

    @property
    def cross_helicity(self):
        v = self.v
        b = self.b
        c = 0.5 * v.multiply(b).sum(axis=1)
        return c

    @property
    def normalized_cross_helicity(self):
        ep = self.ep
        em = self.em
        num = ep.subtract(em)
        den = ep.add(em)
        out = num.divide(den)
        return out

    @property
    def sigma_c(self):
        return self.normalized_cross_helicity

    @property
    def alfven_ratio(self):
        return self.ev.divide(self.eb, axis=0)

    @property
    def rA(self):
        return self.alfven_ratio

    @property
    def elsasser_ratio(self):
        return self.em.divide(self.ep, axis=0)

    @property
    def rE(self):
        return self.elsasser_ratio

    def set_data(self, v_in, b_in, rho, species, **kwargs):
        r"""The `auto_reindex` kwarg can be set to False so that, if running a
        large batch of analysis on the same data, one can reindex once outside
        of this class and avoid many unnecessary reindexing cases within it.

        Be sure to carefully check your reindexing so as to not introduce lots
        of NaNs. I ran into that bug when first writing this class.
        """

        species = self._clean_species_for_setting(species)
        if not isinstance(v_in.index, pd.DatetimeIndex):
            raise TypeError
        if not isinstance(b_in.index, pd.DatetimeIndex):
            raise TypeError
        if not isinstance(rho.index, pd.DatetimeIndex):
            raise TypeError

        if not v_in.index.equals(b_in.index):
            self.logger.warn("v and b have unequal indices. Results may be unexpected.")
        if not v_in.index.equals(rho.index):
            self.logger.warn(
                """v and rho have unequal indices. Results may be
unexpected."""
            )
        # auto_reindex = bool(auto_reindex)

        # assert rho.ndim == 1

        # Based on my read of Bruno and Carbone's definition in B.3.1 (p.166),
        # we first define the magnetic field in Alfven units. Then we calculate
        # averages. Note that I took the other option in my test cases in
        # `TS-analysis` project. (20181120)
        coef = self.units.b / (  # Convert b -> Alfven units.
            np.sqrt(self.units.rho * self.constants.misc.mu0) * self.units.v
        )
        b_ca_units = b_in.divide(rho.pipe(np.sqrt), axis=0).multiply(coef)

        #        if auto_reindex:
        #            idx = v_in.index.union(b_in.index)
        #            i0 = idx.min()
        #            i1 = idx.max() + 1  # `stop` excludes `i1`, so use `i1 + 1`.
        #            idx = pd.RangeIndex(start=i0, stop=i1, step=1)
        #
        #            v = v_in.reindex(idx, axis=0)
        #            b = b_ca_units.reindex(idx, axis=0)
        #
        #        else:
        #            v = v_in
        #            b = b_ca_units

        #         print("<set_data>",
        #               "<species>: %s" % species,
        #               "<v_in>", type(v_in), v_in,
        #               "<v>", type(v), v,
        #               "<rho>", type(rho), rho,
        #               "<b_in>", type(b_in), b_in,
        #               "<coef>: %s" % coef,
        #               "<b>", type(b), b,
        #               sep="\n",
        #               end="\n\n")

        window = kwargs.pop("window", "15min")
        min_periods = kwargs.pop("min_periods", 5)

        data = pd.concat({"v": v_in, "b": b_ca_units}, axis=1, names=["M"])
        rolled = data.rolling(window, min_periods=min_periods, **kwargs)
        agged = rolled.agg("mean")
        deltas = data.subtract(agged, axis=1)

        data.name = "measurements"
        deltas.name = "deltas"

        self._measurements = data
        self._data = deltas
        self._species = species
        self._averaging_info = AlvenicTurbAveraging(window, min_periods)

    def _clean_species_for_setting(self, species):
        if not isinstance(species, str):
            msg = "%s.species must be a single species w/ an optional `+` or `,`"
            raise TypeError(msg % self.__class__.__name__)
        if species.count(",") > 1:
            msg = "%s.species can contain at most one `,`\nspecies: %s"
            raise ValueError(msg % (self.__class__.__name__, species))

        species = ",".join(
            ["+".join(tuple(sorted(s.split("+")))) for s in species.split(",")]
        )
        return species
