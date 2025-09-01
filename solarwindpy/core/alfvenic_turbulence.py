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
[2] Telloni, D., & Bruno, R. (2016). *Monthly Notices of the Royal Astronomical
    Society: Letters*, 463(1), L79–L83. https://doi.org/10.1093/mnrasl/slw135
[3] Woodham, L. D., Wicks, R. T., Verscharen, D., & Owen, C. J. (2018).
    *Astrophys. J.*, 856, 49.
"""


import numpy as np
import pandas as pd

from collections import namedtuple

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.

from . import base

AlvenicTurbAveraging = namedtuple("AlvenicTurbAveraging", "window,min_periods")


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
        #         return self.data.loc[:, "b"]
        b = self.data.loc[:, "b"]
        polarity = self.polarity
        if polarity is not None:
            self.logger.warning("Rectifying B")
            b = b.multiply(polarity, axis=0)
        #             b = b.copy(deep=True)
        #             b.loc[:, ["x", "y"]] = b.loc[:, ["x", "y"]].multiply(polarity, axis=0)
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
        r"""Shortcut for :py:attr:`E_v = kinetic_energy`."""
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
        r"""Normalized residual energy :py:attr:`E_R/E_T`."""
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
            self.logger.warn("v and b have unequal indices. Results may be unexpected.")
        if not v_in.index.equals(rho.index):
            self.logger.warn(
                """v and rho have unequal indices. Results may be
unexpected."""
            )
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

        polarity = None
        if raffaella_version:
            self.logger.warning("Running Raffaella's version")
            if sc_vector is None:
                raise ValueError(
                    "SC-Sun distance required to peform Raffaella's version."
                )

            #             # Drop normal component
            #             data = data.drop("z", axis=1, level="C").copy(deep=True)

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
            #             cos_colat = 1

            r = sc_vector.distance2sun * sc_vector.units.distance2sun * 1e-3  # [km]

            correction = r.multiply(cos_colat, axis=0).multiply(
                omega
            )  # [arc length speed] = [km/s]
            vt = data.loc[:, ("v", "y")].subtract(correction)
            data.loc[:, ("v", "y")] = vt
            #             vy = data.loc[:, ("v", "y")].add(correction)
            #             data.loc[:, ("v", "y")] = vy

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


# lass AlfvenicTurbulenceDAmicis(base.Core):
#     r"""Handle and calculate Alfvenic turbulence quantities using the Elsasser
#     variables following R D'Amicis' email (20240214).
#
#     Parameters
#     ----------
#     velocity : pd.DataFrame, pd.Series (?)
#         The velocity vector in the same basis as `bfield`.
#         Can be a single species, a CoM species, or a differential flow. The
#         differential flow case is an area of curiosity for me and I do not
#         suggest passing it as an input.
#         Expect [v] = km/s (i.e. default stored in `units_constants.Units`).
#     bfield : pd.DataFrame, pd.Series (?)
#         Magnetic field vector in the same basis as `velocity`.
#         Expect [b] = nT (i.e. default stored in `units_contants.Units`).
#     rho : pd.Series
#         The total mass density of the plasma used to define velocity.
#         Expect [rho] = m_p / cm^3 (i.e. default stored in
#         `units_constants.Units`).
#     species: str
#         The species string. Can contain `+`. Can contain at most one `,`.
#
#     Attributes
#     ----------
#     data, species, z_plus, zp, z_minus, zm, e_plus, ep,
#     e_minus, em, total_energy, etot,
#     residual_energy, eres, normalized_residual_energy, eres_norm, sigma_r,
#     cross_helicity, normalized_cross_helicity, sigma_c, alfven_ratio, rA,
#     elsasser_ratio, rE
#
#     Methods
#     -------
#     set_data
#
#     Notes
#     -----
#
#     """
#
#     def __init__(self, velocity, bfield, rho, species, sc_vector, **kwargs):
#         r"""Initialize an :py:class:`AlfvenicTurbulence` object.
#
#         Parameters
#         ----------
#         velocity: pd.DataFrame
#             Vector velocity measurments.
#         bfield: pd.DataFrame
#             Vector mangetic field measurements.
#         rho: pd.Series
#             Mass density measurments, used to put `bfield` into Alfven units.
#         kwargs:
#             Passed to `rolling` method when mean-subtracing in `set_data`.
#         """
#         #         print("<Module>",
#         #               "__init__",
#         #               sep="\n",
#         #               end="\n")
#
#         super(AlfvenicTurbulenceDAmicis, self).__init__()
#         self.set_data(velocity, bfield, rho, species, sc_vector, **kwargs)
#
#     @property
#     def data(self):
#         r"""Mean-subtracted quantities used to calculated Elsasser variables.
#         """
#         return self._data
#
#     @property
#     def averaging_info(self):
#         r"""Averaging window and minimum number of measurements / average used
#         in calculating background component in :math:`\delta B` and :math:`\delta v`.
#         """
#         return self._averaging_info
#
#     @property
#     def measurements(self):
#         r"""Measurements used to calcualte mean-subtracted `data`.
#         """
#         return self._measurements
#
#     @property
#     def polarity(self):
#         r"""Magnetic field polarity.
#         """
#         return self._polarity
#
#     @property
#     def species(self):
#         r"""Species used to create `AlfvenicTurbulence`. Defines mass density in Alfven
#         units.
#         """
#         return self._species
#
#     @property
#     def z_plus(self):
#         r"""Z+ Elsasser variable.
#         """
#         zp = self.data.loc[:, "zp"]
#         return zp
#
#     @property
#     def zp(self):
#         r"""Shortcut for `AlfvenicTurbulence.z_plus`.
#         """
#         return self.z_plus
#
#     @property
#     def z_minus(self):
#         r"""Z- Elsasser variable.
#         """
#         zm = self.data.loc[:, "zm"]
#         return zm
#
#     @property
#     def zm(self):
#         r"""Shortcut for `AlfvenicTurbulence.z_minus`.
#         """
#         return self.z_minus
#
#     @property
#     def e_plus(self):
#         # I took the averages before I created the +/-z quantities in my
#         # previous test cases. Based on a more detailed read of Bruno and
#         # Carbone, I calculate +/-z before I take averages. Note that because
#         # I am adding v and b, the differene shouldn't matter.
#         ep = 0.5 * self.zp.pow(2).sum(axis=1)
#         return ep
#
#     @property
#     def ep(self):
#         return self.e_plus
#
#     @property
#     def e_minus(self):
#         em = 0.5 * self.zm.pow(2).sum(axis=1)
#         return em
#
#     @property
#     def em(self):
#         return self.e_minus
#
#     #     @property
#     #     def kinetic_energy(self):
#     #         ev = 0.5 * self.v.pow(2).sum(axis=1)
#     #         return ev
#
#     #     @property
#     #     def ev(self):
#     #         return self.kinetic_energy
#
#     #     @property
#     #     def magnetic_energy(self):
#     #         eb = 0.5 * self.b.pow(2).sum(axis=1)
#     #         return eb
#
#     #     @property
#     #     def eb(self):
#     #         return self.magnetic_energy
#
#     #     @property
#     #     def total_energy(self):
#     #         return self.ev.add(self.eb, axis=0)
#
#     #     @property
#     #     def etot(self):
#     #         return self.total_energy
#
#     #     @property
#     #     def residual_energy(self):
#     #         return self.ev.subtract(self.eb, axis=0)
#
#     #     @property
#     #     def eres(self):
#     #         return self.residual_energy
#
#     #     @property
#     #     def normalized_residual_energy(self):
#     #         return self.eres.divide(self.etot, axis=0)
#
#     #     @property
#     #     def eres_norm(self):
#     #         return self.normalized_residual_energy
#
#     #     @property
#     #     def sigma_r(self):
#     #         return self.normalized_residual_energy
#
#     #     @property
#     #     def cross_helicity(self):
#     #         v = self.v
#     #         b = self.b
#     #         c = 0.5 * v.multiply(b).sum(axis=1)
#     #         return c
#
#     @property
#     def normalized_cross_helicity(self):
#         ep = self.ep
#         em = self.em
#         num = ep.subtract(em)
#         den = ep.add(em)
#         out = num.divide(den)
#         return out
#
#     @property
#     def sigma_c(self):
#         """Normalized cross helicity.
#
#         Returns
#         -------
#         pd.Series
#             Sigma_c parameter.
#         """
#         return self.normalized_cross_helicity
#
#     #     @property
#     #     def alfven_ratio(self):
#     #         return self.ev.divide(self.eb, axis=0)
#
#     #     @property
#     #     def rA(self):
#     #         return self.alfven_ratio
#
#     @property
#     def elsasser_ratio(self):
#         return self.em.divide(self.ep, axis=0)
#
#     @property
#     def rE(self):
#         """Elsasser ratio.
#
#         Returns
#         -------
#         pd.Series
#             Elsasser ratio parameter.
#         """
#         return self.elsasser_ratio
#
#     def set_data(self, v_in, b_in, rho, species, sc_vector, **kwargs):
#         r"""The `auto_reindex` kwarg can be set to False so that, if running a
#         large batch of analysis on the same data, one can reindex once outside
#         of this class and avoid many unnecessary reindexing cases within it.
#
#         Be sure to carefully check your reindexing so as to not introduce lots
#         of NaNs. I ran into that bug when first writing this class.
#         """
#
#         species = self._clean_species_for_setting(species)
#         if not isinstance(v_in.index, pd.DatetimeIndex):
#             raise TypeError
#         if not isinstance(b_in.index, pd.DatetimeIndex):
#             raise TypeError
#         if not isinstance(rho.index, pd.DatetimeIndex):
#             raise TypeError
#
#         if not v_in.index.equals(b_in.index):
#             self.logger.warn("v and b have unequal indices. Results may be unexpected.")
#         if not v_in.index.equals(rho.index):
#             self.logger.warn(
#                 """v and rho have unequal indices. Results may be
# unexpected."""
#             )
#         # auto_reindex = bool(auto_reindex)
#
#         data = (
#             pd.concat({"v": v_in, "b": b_in}, axis=1, names=["M"], sort=True)
#             .sort_index(axis=1)
#             .copy(deep=True)
#         )
#
#         #         print("1", data.head().round(3), sep="\n", end="\n\n")
#
#         # Convert GSE -> RTN
#         data = data.multiply(pd.Series({"x": -1, "y": -1, "z": 1}), axis=1, level="C")
#
#         #         print("2", data.head().round(3), sep="\n", end="\n\n")
#
#         # Project along nominal Parker Spiral
#         omega = 2.865e-6  # rad/s
#         pos = sc_vector.data.pos.copy(deep=True)
#         r_rtn = (
#             pos.loc[:, ["x", "y", "z"]].pow(2).sum(axis=1, skipna=False).pipe(np.sqrt)
#         )
#         rho_rtn = pos.loc[:, ["x", "y"]].pow(2).sum(axis=1, skipna=False).pipe(np.sqrt)
#         cos_colat = rho_rtn.divide(r_rtn)
#
#         r = sc_vector.distance2sun * sc_vector.units.distance2sun * 1e-3  # [km]
#
#         correction = r.multiply(cos_colat, axis=0).multiply(
#             omega
#         )  # [arc length speed] = [km/s]
#         vt = data.loc[:, ("v", "y")].subtract(correction)
#         data.loc[:, ("v", "y")] = vt
#
#         # #         print("3", data.head().round(3), sep="\n", end="\n\n")
#
#         polarity = (
#             data.loc[:, "v"]
#             .multiply(data.loc[:, "b"], axis=1)
#             #                     .drop(["x", "y"], axis=1)
#             .drop("z", axis=1)
#             .sum(axis=1)
#             .pipe(np.sign)
#         )
#
#         coef = self.units.b / (  # Convert b -> Alfven units.
#             np.sqrt(self.units.rho * self.constants.misc.mu0) * self.units.v
#         )
#         coef = rho.pow(-0.5).multiply(coef)
#         polarity_coef = polarity.multiply(coef)
#
#         #         print("Coef", polarity_coef.head(), sep="\n", end="\n\n")
#
#         b_calc = data.loc[:, "b"].multiply(polarity_coef, axis=0)
#         #         b_calc = data.loc[:, "b"].multiply(coef, axis=0)
#         v_calc = data.loc[:, "v"]
#
#         #         print("4", v_calc.head().round(3), b_calc.head().round(3),sep="\n",  end="\n\n")
#
#         zp = v_calc.add(b_calc)
#         zm = v_calc.subtract(b_calc)
#         z_raw = pd.concat({"zp": zp, "zm": zm}, axis=1).sort_index(axis=1)
#
#         #         print("5", z_raw.head().round(3), sep="\n", end="\n\n")
#
#         window = kwargs.pop("window", "15min")
#         min_periods = kwargs.pop("min_periods", 5)
#
#         rolled = z_raw.rolling(window, min_periods=min_periods, **kwargs)
#         agged = rolled.agg("mean")
#         deltas = z_raw.subtract(agged, axis=1)
#
#         #         print("6", agged.head().round(3), sep="\n", end="\n\n")
#         #         print("y", deltas.head().round(3), sep="\n", end="\n\n")
#
#         data.name = "measurements"
#         deltas.name = "deltas"
#
#         self._measurements = data
#         self._data = deltas
#         self._polarity = polarity
#         self._species = species
#         self._averaging_info = AlvenicTurbAveraging(window, min_periods)
#
#     def _clean_species_for_setting(self, species):
#         if not isinstance(species, str):
#             msg = "%s.species must be a single species w/ an optional `+` or `,`"
#             raise TypeError(msg % self.__class__.__name__)
#         if species.count(",") > 1:
#             msg = "%s.species can contain at most one `,`\nspecies: %s"
#             raise ValueError(msg % (self.__class__.__name__, species))
#
#         species = ",".join(
#             ["+".join(tuple(sorted(s.split("+")))) for s in species.split(",")]
#         )
#         return species
