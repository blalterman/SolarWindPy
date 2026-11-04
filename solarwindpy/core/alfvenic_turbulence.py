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
        Species string used when converting to Alfv\'en units. At most one
        ``,``; the ``+``-joined species on either side are sorted.
    raffaella_version : bool, optional
        If True, ``velocity`` and ``bfield`` must be GSE vectors, which are
        converted to RTN and corrected for solar rotation; see Notes.
    sc_vector : :class:`~solarwindpy.core.spacecraft.Spacecraft`, optional
        Spacecraft in the GSE frame, at the times of ``velocity``. Required
        when ``raffaella_version`` is True.
    **kwargs
        Passed to :meth:`pandas.DataFrame.rolling` when subtracting the
        background. ``window`` defaults to ``"15min"`` and ``min_periods``
        to 5.

    Raises
    ------
    ValueError
        If ``raffaella_version`` is True and ``sc_vector`` is None.

    Notes
    -----
    Implementation follows the formalism of Bruno & Carbone (2013).

    ``raffaella_version`` is a verification aid that expects GSE input and
    converts it to RTN before the background is subtracted:

    1. Every vector, velocity and field alike, becomes
       :math:`(R, T, N) = (-X, -Y, Z)`.
    2. The speed of solar rotation at the spacecraft,
       :math:`\Omega r \cos\lambda`, is subtracted from :math:`v_T`. Here
       :math:`\Omega = 2.865 \times 10^{-6}` rad/s is the Sun's sidereal
       rotation rate (:math:`2\pi` per 25.38 days), :math:`r` is the
       spacecraft's distance to the Sun in km, and :math:`\cos\lambda` is
       :math:`\sqrt{x^2 + y^2} / \sqrt{x^2 + y^2 + z^2}` of its GSE position.
    3. The polarity of each measurement is the sign of
       :math:`v_R b_R + v_T b_T`, and :attr:`b` returns the field
       fluctuations multiplied by it.
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

        The parameters are described in the class docstring.
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
    def v(self):
        r"""Velocity fluctuations (:math:`\delta v`) in Plasma's v-units."""
        return self.data.loc[:, "v"]

    @property
    def b(self):
        r"""B field fluctuations (:math:`\delta b`) in Alfven units."""
        b = self.data.loc[:, "b"]
        polarity = self.polarity
        if polarity is not None:
            self.logger.warning("Rectifying B")
            b = b.multiply(polarity, axis=0)
        return b

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
    def zp(self):
        r""":math:`z^+` Elsasser variable."""
        zp = self.v.add(self.b, axis=1)
        return zp

    @property
    def zm(self):
        r""":math:`z^-` Elsasser variable."""
        zm = self.v.subtract(self.b, axis=1)
        return zm

    @property
    def ep(self):
        r"""Energy contained in :math:`z^+`."""
        ep = 0.5 * self._component_reduce(self.zp.pow(2))
        ep.name = "ep"
        return ep

    @property
    def em(self):
        r"""Energy contained in :math:`z^-`."""
        em = 0.5 * self._component_reduce(self.zm.pow(2))
        em.name = "em"
        return em

    @property
    def ev(self):
        r"""Energy contained in velocity fluctuations :math:`\frac{1}{2}v^2`."""
        ev = 0.5 * self._component_reduce(self.v.pow(2))
        ev.name = "ev"
        return ev

    @property
    def eb(self):
        r"""Energy contained in magnetic field fluctuations

        :math:`E_b = \frac{1}{2}b^2`."""
        eb = 0.5 * self._component_reduce(self.b.pow(2))
        eb.name = "eb"
        return eb

    @property
    def etot(self):
        r"""Total energy :math:`E_T = E_v + E_b`."""
        etot = self.ev.add(self.eb, axis=0)
        etot.name = "etot"
        return etot

    @property
    def eres(self):
        r"""Residual energy :math:`E_R = E_v - E_b`."""
        eres = self.ev.subtract(self.eb, axis=0)
        eres.name = "eres"
        return eres

    @property
    def sigma_r(self):
        r"""Normalized residual energy, :math:`E_R/E_T`."""
        sigma_r = self.eres.divide(self.etot, axis=0)
        sigma_r.name = "sigma_r"
        return sigma_r

    @property
    def cross_helicity(self):
        r"""Cross helicity :math:`\frac{1}{2} \delta v \cdot \delta b`."""
        v = self.v
        b = self.b
        c = 0.5 * self._component_reduce(v.multiply(b))
        c.name = "cross_helicity"
        return c

    @property
    def sigma_c(self):
        r"""Normalized cross helicity :math:`\frac{e^+ - e^-}{e^+ + e^-}`."""
        ep = self.ep
        em = self.em
        num = ep.subtract(em)
        den = ep.add(em)
        out = num.divide(den)
        out.name = "sigma_c"
        return out

    @property
    def rA(self):
        r"""Alfv\'en ratio :math:`E_v/E_b`."""
        rA = self.ev.divide(self.eb, axis=0)
        rA.name = "rA"
        return rA

    @property
    def rE(self):
        r"""Elsasser ratio :math:`e^-/e^+`."""
        rE = self.em.divide(self.ep, axis=0)
        rE.name = "rE"
        return rE

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

        # `sort=True` puts the union of unequal v and b indexes in time order,
        # which `rolling` requires.
        data = pd.concat(
            {"v": v_in, "b": b_ca_units}, axis=1, names=["M"], sort=True
        ).sort_index(axis=1)

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
            pos = sc_vector.data.xs("pos", axis=1, level="M")
            r_rtn = self._component_reduce(
                self._select(pos, ["x", "y", "z"], "C").pow(2)
            ).pipe(np.sqrt)
            rho_rtn = self._component_reduce(
                self._select(pos, ["x", "y"], "C").pow(2)
            ).pipe(np.sqrt)
            cos_colat = rho_rtn.divide(r_rtn)

            r = sc_vector.distance2sun * sc_vector.units.distance2sun * 1e-3  # [km]

            correction = r.multiply(cos_colat, axis=0).multiply(
                omega
            )  # [arc length speed] = [km/s]
            vt = data.loc[:, ("v", "y")].subtract(correction)
            data.loc[:, ("v", "y")] = vt

            vb = data.loc[:, "v"].multiply(data.loc[:, "b"], axis=1)
            polarity = self._component_reduce(self._select(vb, ["x", "y"], "C")).pipe(
                np.sign
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
        parts = species.split(",")
        if len(parts) > 2:
            msg = "%s.species can contain at most one `,`\nspecies: %s"
            raise ValueError(msg % (self.__class__.__name__, species))

        return ",".join("+".join(self._conform_species(s)) for s in parts)
