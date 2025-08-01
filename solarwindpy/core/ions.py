#!/usr/bin/env python
r"""Contais Ion class.

Class inherets from :py:class:`~solarwindpy.core.base.Base` and contains :py:class:`~solarwindpy.core.vector.Vector` along with
:py:class:`~solarwindpy.core.tensor.Tensor` objects.
"""

import pdb  # noqa: F401

# import numpy as np
import pandas as pd

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
    from . import vector
    from . import tensor
except ImportError:
    import base
    import vector
    import tensor


class Ion(base.Base):
    r"""Ion class.

    Properties
    ----------
    species, velocity, thermal_speed, number_density, mass_density, anisotropy,
    temperature, pressure

    Methods
    -------
    set_species, set_data
    """

    def __init__(self, data, species):
        self.set_species(species)
        super(Ion, self).__init__(data)
        # self.set_data(data, species)

    def __eq__(self, other):
        # eq = super(Ion, self).__eq__(other)
        if id(self) == id(other):
            return True
        elif type(self) != type(other):
            return False
        elif self.species != other.species:
            return False
        else:
            try:
                pd.testing.assert_frame_equal(self.data, other.data)
            except AssertionError:
                return False
        #            try:
        #                # eq_data = self.data == other.data
        #                pd.testing.assert_frame_equal(self.data, other.data)
        #            except ValueError as e:
        #                # print(dir(e), flush=True)
        #                msg = "Can only compare identically-labeled DataFrame objects"
        #                if msg in str(e):
        #                    return False
        #                else:
        #                    raise e
        #
        #            while isinstance(eq_data, pd.core.generic.NDFrame):
        #                eq_data = eq_data.all()
        #            if eq_data:
        #                return True
        #
        return True

    def set_species(self, species):
        assert isinstance(species, str)
        if "+" in species:
            raise NotImplementedError
        self._species = species

    def set_data(self, data):
        #         assert isinstance(data, pd.DataFrame)
        super(Ion, self).set_data(data)

        species = self.species
        # TODO: Implement the following optional species xs if necessary
        #       based on ways ions are later created in Plasma.
        if data.columns.names == ["M", "C"]:
            pass
        elif data.columns.names == ["M", "C", "S"]:
            data = data.sort_index(axis=1)
            data = data.xs(species, axis=1, level="S")
        else:
            msg = "Unrecognized data column names: %s" % (data.columns.names)
            raise ValueError(msg)

        chk = [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
        ]
        assert pd.Index(chk).isin(data.columns).all()
        self._data = data

    @property
    def species(self):
        r"""Ion species.
        """
        return self._species

    @property
    def velocity(self):
        r"""Ion's velocity stored as a :py:class:`~solarwindpy.core.vector.Vector`.
        """
        return vector.Vector(self.data.loc[:, "v"])

    @property
    def v(self):
        r"""
        Shortcut to :py:meth:`velocity` property.
        """
        return self.velocity

    @property
    def thermal_speed(self):
        r"""Ion's thermal speed stored as :py:class:`~solarwindpy.core.tensor.Tensor`.
        """
        return tensor.Tensor(self.data.loc[:, "w"])

    @property
    def w(self):
        r"""Shortcut to :py:meth:`thermal_speed`.
        """
        return self.thermal_speed

    @property
    def number_density(self):
        r"""Number density returned from underlying :py:meth:`~solarwindpy.core.base.Base.data` as a `pd.Series`.
        """
        return self.data.loc[:, "n"]

    @property
    def n(self):
        r"""Shortcut to :py:meth:`number_density`.
        """
        return self.number_density

    @property
    def mass_density(self):
        r"""Ion's mass density.
        """
        out = self.n * self.constants.m_in_mp.loc[self.species]
        out.name = "rho"
        return out

    @property
    def rho(self):
        r"""
        Shortcut to :py:meth:`mass_density`.
        """
        return self.mass_density

    @property
    def anisotropy(self):
        r"""Temperature anisotropy :math:`R_T = p_\perp/p_\parallel`.
        """
        exp = pd.Series({"par": -1, "per": 1})
        pth = self.pth.drop("scalar", axis=1)
        assert pth.shape[1] == 2
        assert exp.index.equals(pth.columns)
        # TODO: test `skipna=False` to ensure NaNs propagate.
        ani = pth.pow(exp, axis=1, level="C").product(axis=1, skipna=False)
        ani.name = "RT"
        return ani

    @property
    def temperature(self):
        r""":math:`T = \frac{m}{2 k_B} w^2`.
        """
        m = self.constants.m.loc[self.species]
        # TODO: Make math operations work on ThermalSpeed
        w = self.w.data * self.units.w
        coeff = 0.5 * m / (self.constants.kb.J * self.units.temperature)
        temp = coeff * w.pow(2)
        temp.name = "T"
        return temp

    @property
    def pth(self):
        r"""Thermal pressure :math:`p_\mathrm{th} = \frac{1}{2}\rho w^2`.
        """
        rho = self.rho * self.units.rho
        # TODO: Make math operations work on ThermalSpeed
        w = self.w.multiply(self.units.w)
        pth = (0.5 / self.units.pth) * w.pow(2).multiply(rho, axis=0)
        pth.name = "pth"
        return pth

    @property
    def cs(self):
        r"""Species' sound speed.
        """
        pth = self.pth * self.units.pth
        rho = self.rho * self.units.rho
        gamma = self.constants.polytropic_index["scalar"]

        cs = pth.divide(rho).multiply(gamma).pow(0.5) / self.units.cs
        cs.name = "cs"
        return cs

    @property
    def specific_entropy(self):
        r"""Calculate the specific entropy following [1] as

            :math:`p_\mathrm{th} \rho^{-\gamma}`

        where :math:`gamma=5/3`, :math:`p_\mathrm{th}` is the thermal presure,
        and :math:`rho` is the mass density.

        References
        ----------
        [1] Siscoe, G. L. (1983). Solar System Magnetohydrodynamics (pp.
            11–100). https://doi.org/10.1007/978-94-009-7194-3_2
        """
        comp = "scalar"
        gamma = self.constants.polytropic_index.loc[comp]

        pth = self.pth.loc[:, comp] * self.units.pth
        rho = self.rho * self.units.rho
        out = pth.multiply(rho.pow(-gamma)) / self.units.specific_entropy

        out.name = "S"
        return out

    @property
    def S(self):
        r"""Shortuct to :py:meth:`~specific_entropy`.
        """
        return self.specific_entropy

    @property
    def kinetic_energy_flux(self):
        r"""Calcualte the kinetic energy flux as

            :math:`W_k = \frac{1}{2} \rho v^3`
        """
        rho = self.rho * self.units.rho
        v = self.v.mag * self.units.v
        w = rho.multiply(v.pow(3)).multiply(0.5)
        w /= self.units.kinetic_energy_flux

        w.name = "Wk"
        return w

    @property
    def Wk(self):
        r"""Shortcut to :py:meth:`~kinetic_energy_flux`.
        """
        return self.kinetic_energy_flux
