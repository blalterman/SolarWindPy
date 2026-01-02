#!/usr/bin/env python
"""Contains Ion class.

This module defines the Ion class, which inherits from the Base class and contains
Vector and Tensor objects.
"""

from __future__ import annotations
import pandas as pd

from . import base
from . import vector
from . import tensor


class Ion(base.Base):
    """Container for a single ion species.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data for the ion in the form ``("M", "C")`` where ``M`` is the
        measurement type (``n``, ``v``, ``w``) and ``C`` is the component.
    species : str
        Species identifier, e.g. ``"p"`` for protons or ``"a"`` for alpha
        particles.

    Attributes
    ----------
    species : str
        The ion's species name.
    """

    def __init__(self, data: pd.DataFrame, species: str):
        """Initialize an Ion instance with plasma measurement data.

        Parameters
        ----------
        data : pandas.DataFrame
            Ion measurement data with MultiIndex columns formatted as
            ("M", "C") where M is measurement type (n, v, w, T) and
            C is component (x, y, z, par, per, etc.).
        species : str
            Ion species identifier following standard conventions:
            - 'p1' or 'p' for protons
            - 'a' for alpha particles (He2+)
            - 'o6' for O6+ ions
            - Other species as needed

        Notes
        -----
        The Ion class provides access to fundamental plasma measurements:

        - n: Number density [cm^-3]
        - v: Velocity vector [km/s]
        - w: Thermal speed [km/s] (assumes mw² = 2kT)
        - T: Temperature [K] (derived from thermal speed)

        Physical constants and mass values are automatically assigned
        based on the species identifier using standard atomic masses.

        Examples
        --------
        Create a proton ion from measurement data:

        >>> import pandas as pd
        >>> import numpy as np
        >>> columns = pd.MultiIndex.from_tuples([
        ...     ('n', '', 'p1'),
        ...     ('v', 'x', 'p1'), ('v', 'y', 'p1'), ('v', 'z', 'p1'),
        ...     ('w', 'par', 'p1'), ('w', 'per', 'p1')
        ... ], names=['M', 'C', 'S'])
        >>> df = pd.DataFrame(np.random.rand(2, 6), columns=columns)
        >>> proton_data = df.xs('p1', level='S', axis=1)
        >>> proton = Ion(proton_data, 'p1')
        >>> proton.species
        'p1'
        """
        self.set_species(species)
        super().__init__(data)

    def __eq__(self, other: object) -> bool:
        """Check equality between Ion objects.

        Parameters
        ----------
        other : object
            Object to compare with.

        Returns
        -------
        bool
            True if species and data are equal, False otherwise.
        """
        if not isinstance(other, Ion):
            return NotImplemented
        return self.species == other.species and self.data.equals(other.data)

    def set_species(self, species: str) -> None:
        """Set the species of the ion.

        Parameters
        ----------
        species : str
            The species of the ion.

        Raises
        ------
        ValueError
            If the species contains a '+' character.
        """
        if "+" in species:
            raise ValueError("Species with '+' are not supported")
        self._species = species

    def set_data(self, data: pd.DataFrame) -> None:
        """Set the data for the ion.

        Parameters
        ----------
        data : pd.DataFrame
            The data to set for the ion.

        Raises
        ------
        ValueError
            If the data column names are unrecognized.
        """
        super().set_data(data)

        if data.columns.names == ["M", "C", "S"]:
            data = data.sort_index(axis=1)
            data = data.xs(self.species, axis=1, level="S")
        elif data.columns.names != ["M", "C"]:
            raise ValueError(f"Unrecognized data column names: {data.columns.names}")

        required_columns = [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
        ]
        if not pd.Index(required_columns).isin(data.columns).all():
            raise ValueError("Missing required columns in data")

        self._data = data

    @property
    def species(self) -> str:
        """Get the ion species."""
        return self._species

    @property
    def velocity(self) -> vector.Vector:
        """Get the ion's velocity as a Vector."""
        return vector.Vector(self.data.loc[:, "v"])

    @property
    def v(self) -> vector.Vector:
        """Alias for velocity property."""
        return self.velocity

    @property
    def thermal_speed(self) -> tensor.Tensor:
        """Get the ion's thermal speed as a Tensor."""
        return tensor.Tensor(self.data.loc[:, "w"])

    @property
    def w(self) -> tensor.Tensor:
        """Alias for thermal_speed property."""
        return self.thermal_speed

    @property
    def number_density(self) -> pd.Series:
        """Get the number density of the ion."""
        return self.data.loc[:, "n"]

    @property
    def n(self) -> pd.Series:
        """Alias for number_density property."""
        return self.number_density

    @property
    def mass_density(self) -> pd.Series:
        """Calculate the ion's mass density."""
        out = self.n * self.constants.m_in_mp.loc[self.species]
        out.name = "rho"
        return out

    @property
    def rho(self) -> pd.Series:
        """Alias for mass_density property."""
        return self.mass_density

    @property
    def anisotropy(self) -> pd.Series:
        """Calculate temperature anisotropy R_T = p_⟂/p_∥.

        Returns
        -------
        pd.Series
            Temperature anisotropy.
        """
        exp = pd.Series({"par": -1, "per": 1})
        pth = self.pth.drop("scalar", axis=1)
        ani = pth.pow(exp, axis=1, level="C").product(axis=1, skipna=False)
        ani.name = "RT"
        return ani

    @property
    def temperature(self) -> pd.DataFrame:
        """Calculate temperature T = (m / (2 * k_B)) * w^2.

        Returns
        -------
        pd.DataFrame
            Temperature of the ion.
        """
        m = self.constants.m.loc[self.species]
        w = self.w.data * self.units.w
        coeff = 0.5 * m / (self.constants.kb.J * self.units.temperature)
        temp = coeff * w.pow(2)
        temp.name = "T"
        return temp

    @property
    def pth(self) -> pd.DataFrame:
        """Calculate thermal pressure p_th = 0.5 * ρ * w^2.

        Returns
        -------
        pd.DataFrame
            Thermal pressure.
        """
        rho = self.rho * self.units.rho
        w = self.w.data.multiply(self.units.w)
        pth = (0.5 / self.units.pth) * w.pow(2).multiply(rho, axis=0)
        pth.name = "pth"
        return pth

    @property
    def cs(self) -> pd.DataFrame:
        """Calculate the species' sound speed.

        Returns
        -------
        pd.DataFrame
            Sound speed of the ion species.
        """
        pth = self.pth * self.units.pth
        rho = self.rho * self.units.rho
        gamma = self.constants.polytropic_index["scalar"]
        cs = pth.divide(rho, axis=0).multiply(gamma).pow(0.5) / self.units.cs
        cs.name = "cs"
        return cs

    @property
    def specific_entropy(self) -> pd.Series:
        """Calculate the specific entropy S = p_th * ρ^(-γ).

        Returns
        -------
        pd.Series
            Specific entropy of the ion.

        References
        ----------
        Siscoe, G. L. (1983). Solar System Magnetohydrodynamics (pp. 11-100).
        https://doi.org/10.1007/978-94-009-7194-3_2
        """
        comp = "scalar"
        gamma = self.constants.polytropic_index.loc[comp]
        pth = self.pth.loc[:, comp] * self.units.pth
        rho = self.rho * self.units.rho
        out = pth.multiply(rho.pow(-gamma)) / self.units.specific_entropy
        out.name = "S"
        return out

    @property
    def S(self) -> pd.Series:
        """Alias for specific_entropy property."""
        return self.specific_entropy

    @property
    def kinetic_energy_flux(self):
        r"""Calculate the kinetic energy flux.

        The kinetic energy flux is calculated as:

        .. math::
            W_k = \frac{1}{2} \rho v^3

        Returns
        -------
        pd.Series
            Kinetic energy flux.
        """
        rho = self.rho * self.units.rho
        v = self.v.mag * self.units.v
        w = rho.multiply(v.pow(3)).multiply(0.5)
        w /= self.units.kinetic_energy_flux

        w.name = "Wk"
        return w

    @property
    def Wk(self):
        r"""Shortcut to :py:attr:`~kinetic_energy_flux`."""
        return self.kinetic_energy_flux
