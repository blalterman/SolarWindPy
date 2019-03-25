#!/usr/bin/env python
"""Object for calculating Alfvenic turbulence.

Description
-----------
-Contains a class to analyze Alfvenic turbulence.
-Primarily follows [1].

Bibliography
------------
[1] Bruno, R., & Carbone, V. (2013). The solar wind as a turbulence laboratory.
    Living Reviews in Solar Physics, 10(1), 1–208. https://doi.org/10.12942/lrsp-2013-2
[2] Telloni, D., & Bruno, R. (2016). Linking fluid and kinetic scales in solar
    wind turbulence. Monthly Notices of the Royal Astronomical Society: Letters,
    463(1), L79–L83. https://doi.org/10.1093/mnrasl/slw135
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import pdb  # noqa: F401

import numpy as np
import pandas as pd

from types import FunctionType


# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")


try:
    from . import base
#     from . import units_constants as uc
except ImportError:
    import base
#     import units_constants as uc


class AlfvenicTurbulence(base.Core):
    def __init__(self, velocity, bfield, rho, species, auto_reindex=True):
        #         self._init_units()
        #         self._init_constants()

        #         print("<Module>",
        #               "__init__",
        #               sep="\n",
        #               end="\n")

        super(AlfvenicTurbulence, self).__init__()
        self.set_data(velocity, bfield, rho, species, auto_reindex=auto_reindex)
        self.update_rolling()
        self.set_agg("mean")

    #     @property
    #     def units(self):
    #         return self._units
    #     @property
    #     def constants(self):
    #         return self._constants
    @property
    def data(self):
        return self._data

    @property
    def velocity(self):
        r"""Velocity in Plasma's v-units.
        """
        return self.data.loc[:, "v"]  # self._velocity

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
        #         return self._bfield
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
        ep = 0.5 * self.zp.pow(2).sum(axis=1).rolling(
            self.rolling_window, **self.rolling_kwargs
        ).agg(self.agg)
        return ep

    @property
    def ep(self):
        return self.e_plus

    @property
    def e_minus(self):
        em = 0.5 * self.zm.pow(2).sum(axis=1).rolling(
            self.rolling_window, **self.rolling_kwargs
        ).agg(self.agg)
        return em

    @property
    def em(self):
        return self.e_minus

    @property
    def kinetic_energy(self):
        ev = 0.5 * self.v.pow(2).sum(axis=1).rolling(
            self.rolling_window, **self.rolling_kwargs
        ).agg(self.agg)
        return ev

    @property
    def ev(self):
        return self.kinetic_energy

    @property
    def magnetic_energy(self):
        eb = 0.5 * self.b.pow(2).sum(axis=1).rolling(
            self.rolling_window, **self.rolling_kwargs
        ).agg(self.agg)
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
        # -1 so outward propagation is positive. [2]
        c = -0.5 * v.multiply(b, axis=1).sum(axis=1).rolling(
            self.rolling_window, **self.rolling_kwargs
        ).agg(self.agg)

        return c

    @property
    def normalized_cross_helicity(self):
        ep = self.ep
        em = self.em

        num = ep.subtract(em)
        den = ep.add(em)
        # -1 so outward propagation is positive. [2]
        out = -1.0 * num.divide(den)

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

    @property
    def agg(self):
        return self._agg

    def set_agg(self, new):
        if isinstance(new, str):
            new = (new,)
        assert hasattr(new, "__iter__")
        if not np.all([isinstance(x, (str, FunctionType)) for x in new]):
            msg = "All aggregators must be strings or functions."
            raise TypeError(msg)

        new = tuple(sorted(new))
        self._agg = new

    @property
    def rolling_window(self):
        return self._rolling_window

    @property
    def rolling_kwargs(self):
        return dict(self._rolling_kwargs)

    def update_rolling(self, **new_kwargs):
        r"""We treat `window` as a kwarg to simplify use of all `pd.<>.rolling`
        inputs.
        """
        try:
            kwargs = self.rolling_kwargs
        except AttributeError:
            kwargs = dict(window=5, min_periods=3, center=True)

        kwargs.update(new_kwargs)

        window = kwargs.pop("window")
        kwargs = tuple(sorted(kwargs.items()))
        self._rolling_window = window
        self._rolling_kwargs = kwargs

    def set_data(self, v_in, b_in, rho, species, auto_reindex=True):

        species = self._clean_species_for_setting(species)
        auto_reindex = bool(auto_reindex)

        # Based on my read of Bruno and Carbone's definition in B.3.1 (p.166),
        # we first define the magnetic field in Alfven units. Then we calculate
        # averages. Note that I took the other option in my test cases in
        # `TS-analysis` project. (20181120)
        coef = self.units.b / (  # Convert b -> Alfven units.
            np.sqrt(self.units.rho * self.constants.misc.mu0) * self.units.v
        )
        b_ca_units = b_in.divide(rho.pipe(np.sqrt), axis=0).multiply(coef)

        if auto_reindex:
            idx = v_in.index.union(b_in.index)
            i0 = idx.min()
            i1 = idx.max() + 1  # `stop` excludes `i1`, so use `i1 + 1`.
            idx = pd.RangeIndex(start=i0, stop=i1, step=1)

            v = v_in.reindex(idx, axis=0)
            b = b_ca_units.reindex(idx, axis=0)

        else:
            v = v_in
            b = b_ca_units

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

        data = pd.concat({"v": v, "b": b}, axis=1)
        self._data = data
        self._species = species

    def _clean_species_for_setting(self, species):
        if not isinstance(species, str):
            msg = "%s.species must be a single species w/ an optional `+`"
            raise TypeError(msg % self.__class__.__name__)
        if species.count(",") > 1:
            msg = "%s.species can contain at most one `,`\nspecies: %s"
            raise ValueError(msg % (self.__class__.__name__, species))

        species = ",".join(
            ["+".join(tuple(sorted(s.split("+")))) for s in species.split(",")]
        )
        return species
