#!/usr/bin/env python
"""Alfvenic turbulence diagnostics using Elsasser variables.

Notes
-----
The implementation follows the formalism outlined in Bruno & Carbone [1].
Lloyd Woodham <https://orcid.org/0000-0003-2845-4250> helped me define these
calculations at the 2018 AGU Fall Meeting and understand [1]. Please cite [3]
if using this module.

References
----------
[1] Bruno, R., & Carbone, V. (2013). *Living Reviews in Solar Physics*,
10(1), 1–208. https://doi.org/10.12942/lrsp-2013-2

[2] Telloni, D., & Bruno, R. (2016). *Monthly Notices of the Royal
Astronomical Society: Letters*, 463(1), L79–L83.
https://doi.org/10.1093/mnrasl/slw135

[3] Woodham, L. D., Wicks, R. T., Verscharen, D., & Owen, C. J. (2018).
*Astrophys. J.*, 856, 49.
"""

__all__ = [
    "AlfvenicTurbAveraging",
    "AlfvenicTurbulence",
]

import numpy as np
import pandas as pd

from collections import namedtuple

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.

from . import base

AlfvenicTurbAveraging = namedtuple("AlfvenicTurbAveraging", "window,min_periods")


class AlfvenicTurbulence(base.Core):
    r"""Alfv\'enic turbulence diagnostics using Elsasser variables.

    Parameters
    ----------
    velocity : :class:`pandas.DataFrame`
        Plasma velocity in the same basis as ``bfield``.
    bfield : :class:`pandas.DataFrame`
        Magnetic field in the same basis as ``velocity``.
    rho : :class:`pandas.Series`
        Mass density used for normalising ``bfield``.
    species : str
        Species string used when converting to Alfv\'en units.

    Notes
    -----
    Implementation follows the formalism of Bruno & Carbone (2013).
    """

    def __init__(
        self,
        velocity,
        bfield,
        rho,
        species,
        raffaella_version=False,
        sc_vector=None,
        **kwargs,
    ):
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

        super(AlfvenicTurbulence, self).__init__()
        self.set_data(
            velocity,
            bfield,
            rho,
            species,
            raffaella_version=raffaella_version,
            sc_vector=sc_vector,
            **kwargs,
        )

    @property
    def data(self):
        r"""Mean-subtracted quantities used to calculated Elsasser variables."""
        return self._data

    @property
    def averaging_info(self):
        r"""Averaging window and minimum number of measurements / average used.

        In calculating background component in :math:`\delta B` and :math:`\delta v`.
        """
        return self._averaging_info

    @property
    def measurements(self):
        r"""Measurements used to calcualte mean-subtracted `data`."""
        return self._measurements

    @property
    def velocity(self):
        r"""Velocity fluctuations (:math:`\delta v`) in Plasma's v-units."""
        return self.data.loc[:, "v"]

    @property
    def v(self):
        r"""Shortcut for :py:attr:`velocity`"""
        return self.velocity

    @property
    def bfield(self):
        r"""B field fluctuations (:math:`\delta b`) in Alfven units."""
        b = self.data.loc[:, "b"]
        polarity = self.polarity
        if polarity is not None:
            self.logger.warning("Rectifying B")
            b = b.multiply(polarity, axis=0)
        return b

    @property
    def b(self):
        r"""Shortcut for :py:attr:`bfield`."""
        return self.bfield

    @property
    def polarity(self):
        r"""Magnetic field polarity."""
        return self._polarity

    @property
    def species(self):
        r"""Species used to create :class:`AlfvenicTurbulence`.

        Defines mass density in Alfven units.
        """
        return self._species

    @property
    def z_plus(self):
        r""":math:`z^+` Elsasser variable."""
        zp = self.v.add(self.b, axis=1)
        return zp

    @property
    def zp(self):
        r"""Shortcut for :py:attr:`z_plus`."""
        return self.z_plus

    @property
    def z_minus(self):
        r""":math:`z^-` Elsasser variable."""
        zm = self.v.subtract(self.b, axis=1)
        return zm

    @property
    def zm(self):
        r"""Shortcut for :py:attr:`z_minus`."""
        return self.z_minus

    @property
    def e_plus(self):
        r"""Energy contained in :math:`z^+`."""
        ep = 0.5 * self.zp.pow(2).sum(axis=1)
        return ep

    @property
    def ep(self):
        r"""Shortcut for :py:attr:`e_plus`."""
        return self.e_plus

    @property
    def e_minus(self):
        r"""Energy contained in :math:`z^-`."""
        em = 0.5 * self.zm.pow(2).sum(axis=1)
        return em

    @property
    def em(self):
        r"""Shortcut for :py:attr:`e_minus`."""
        return self.e_minus

    @property
    def kinetic_energy(self):
        r"""Energy contained in velocity fluctuations :math:`\frac{1}{2}v^2`."""
        ev = 0.5 * self.v.pow(2).sum(axis=1)
        return ev

    @property
    def ev(self):
        r"""Shortcut for :py:attr:`kinetic_energy`, :math:`E_v`."""
        return self.kinetic_energy

    @property
    def magnetic_energy(self):
        r"""Energy contained in magnetic field fluctuations

        :math:`E_b = \frac{1}{2}b^2`."""
        eb = 0.5 * self.b.pow(2).sum(axis=1)
        return eb

    @property
    def eb(self):
        r"""Shortcut for :py:attr:`magnetic_energy`."""
        return self.magnetic_energy

    @property
    def total_energy(self):
        r"""Total energy :math:`E_T = E_v + E_b`."""
        return self.ev.add(self.eb, axis=0)

    @property
    def etot(self):
        r"""Shortcut for :py:attr:`total_energy`."""
        return self.total_energy

    @property
    def residual_energy(self):
        r"""Residual energy :math:`E_R = E_v - E_b`."""
        return self.ev.subtract(self.eb, axis=0)

    @property
    def eres(self):
        r"""Shortcut for :py:attr:`residual_energy`."""
        return self.residual_energy

    @property
    def normalized_residual_energy(self):
        r"""Normalized residual energy, :math:`E_R/E_T`."""
        return self.eres.divide(self.etot, axis=0)

    @property
    def eres_norm(self):
        r"""Shortcut for :py:attr:`normalized_residual_energy`."""
        return self.normalized_residual_energy

    @property
    def sigma_r(self):
        r"""Shortcut for :py:attr:`normalized_residual_energy`."""
        return self.normalized_residual_energy

    @property
    def cross_helicity(self):
        r"""Cross helicity :math:`\frac{1}{2} \delta v \cdot \delta b`."""
        v = self.v
        b = self.b
        c = 0.5 * v.multiply(b).sum(axis=1)
        return c

    @property
    def normalized_cross_helicity(self):
        r"""Normalized cross helicity :math:`\frac{e^+ - e^-}{e^+ + e^-}`."""
        ep = self.ep
        em = self.em
        num = ep.subtract(em)
        den = ep.add(em)
        out = num.divide(den)
        return out

    @property
    def sigma_c(self):
        r"""Shortcut to :py:attr:`normalized_cross_helicity`."""
        return self.normalized_cross_helicity

    @property
    def alfven_ratio(self):
        r"""Alfv\'en ratio :math:`E_v/E_b`."""
        return self.ev.divide(self.eb, axis=0)

    @property
    def rA(self):
        r"""Shortcut to :py:attr:`alfven_ratio`."""
        return self.alfven_ratio

    @property
    def elsasser_ratio(self):
        r"""Elsasser ratio :math:`e^-/e^+`."""
        return self.em.divide(self.ep, axis=0)

    @property
    def rE(self):
        r"""Shortcut to :py:attr:`elsasser_ratio`."""
        return self.elsasser_ratio

    def set_data(
        self,
        v_in,
        b_in,
        rho,
        species,
        raffaella_version=False,
        sc_vector=None,
        **kwargs,
    ):
        r"""Set data for the class, performing routine formatting checks.

        The `auto_reindex` kwarg can be set to False for batch analysis. So
        that, if running a large batch of analysis on the same data, one can
        reindex once outside of this class and avoid many unnecessary reindexing
        cases within it. Be sure to carefully check your reindexing so as to not
        introduce lots of NaNs. I ran into that bug when first writing this
        class.
        """

        species = self._clean_species_for_setting(species)
        if not isinstance(v_in.index, pd.DatetimeIndex):
            raise TypeError
        if not isinstance(b_in.index, pd.DatetimeIndex):
            raise TypeError
        if not isinstance(rho.index, pd.DatetimeIndex):
            raise TypeError

        if not v_in.index.equals(b_in.index):
            self.logger.warning(
                "v and b have unequal indices. Results may be unexpected."
            )
        if not v_in.index.equals(rho.index):
            self.logger.warning("""v and rho have unequal indices. Results may be
unexpected.""")
        # Convert b -> Alfven units before averaging as in Bruno and Carbone
        # [2013], Section B.3.1.
        # Based on my read of Bruno and Carbone's definition in B.3.1 (p.166),
        # we first define the magnetic field in Alfven units. Then we calculate
        # averages. Note that I took the other option in my test cases in
        # `TS-analysis` project. (20181120)
        coef = self.units.b / (  # Convert b -> Alfven units.
            np.sqrt(self.units.rho * self.constants.misc.mu0) * self.units.v
        )
        b_ca_units = b_in.divide(rho.pipe(np.sqrt), axis=0).multiply(coef)

        data = (
            pd.concat({"v": v_in, "b": b_ca_units}, axis=1, names=["M"], sort=True)
            .sort_index(axis=1)
            .copy(deep=True)
        )

        polarity = None
        if raffaella_version:
            self.logger.warning("Running Raffaella's version")
            if sc_vector is None:
                raise ValueError(
                    "SC-Sun distance required to peform Raffaella's version."
                )

            # Convert GSE -> RTN
            data = data.multiply(
                pd.Series({"x": -1, "y": -1, "z": 1}), axis=1, level="C"
            )

            # Project along nominal Parker Spiral
            omega = 2.865e-6  # rad/s
            pos = sc_vector.data.pos.copy(deep=True)
            r_rtn = (
                pos.loc[:, ["x", "y", "z"]]
                .pow(2)
                .sum(axis=1, skipna=False)
                .pipe(np.sqrt)
            )
            rho_rtn = (
                pos.loc[:, ["x", "y"]].pow(2).sum(axis=1, skipna=False).pipe(np.sqrt)
            )
            cos_colat = rho_rtn.divide(r_rtn)

            r = sc_vector.distance2sun * sc_vector.units.distance2sun * 1e-3  # [km]

            correction = r.multiply(cos_colat, axis=0).multiply(
                omega
            )  # [arc length speed] = [km/s]
            vt = data.loc[:, ("v", "y")].subtract(correction)
            data.loc[:, ("v", "y")] = vt

            polarity = (
                data.loc[:, "v"]
                .multiply(data.loc[:, "b"], axis=1)
                .drop("z", axis=1)
                .sum(axis=1)
                .pipe(np.sign)
            )

        window = kwargs.pop("window", "15min")
        min_periods = kwargs.pop("min_periods", 5)

        rolled = data.rolling(window, min_periods=min_periods, **kwargs)
        agged = rolled.agg("mean")
        deltas = data.subtract(agged, axis=1)

        data.name = "measurements"
        deltas.name = "deltas"

        self._measurements = data
        self._data = deltas
        self._polarity = polarity
        self._species = species
        self._averaging_info = AlfvenicTurbAveraging(window, min_periods)

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
