#!/usr/bin/env python
"""A Vector class and subclasses.

This module provides a Vector class and its subclass BField for handling vector
operations and magnetic field calculations.
"""

import numpy as np
import pandas as pd

from . import base


class Vector(base.Base):
    """Three-dimensional vector container.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data with ``x``, ``y`` and ``z`` components.
    """

    def __init__(self, data: pd.DataFrame):
        """Initialize a :class:`Vector` instance.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            The vector data with ``x``, ``y`` and ``z`` components.
        """
        super().__init__(data)

    def __call__(self, component: str) -> pd.Series:
        """Return a vector component.

        Parameters
        ----------
        component : str
            Component to return (``'x'``, ``'y'`` or ``'z'``).

        Returns
        -------
        pd.Series
            The requested component.
        """
        return self.__getattr__(component)

    def set_data(self, new: pd.DataFrame):
        """Set new vector data.

        Parameters
        ----------
        new : :class:`pandas.DataFrame`
            New vector data.

        Raises
        ------
        ValueError
            If ``new`` does not contain the required columns.
        """
        super().set_data(new)
        required_columns = pd.Index(["x", "y", "z"])
        if (
            not isinstance(new.columns, pd.MultiIndex)
            and not required_columns.isin(new.columns).all()
        ):
            raise ValueError(
                f"Required columns: {required_columns}\nProvided: {new.columns}"
            )
        self._data = new

    @property
    def mag(self) -> pd.Series:
        """Calculate the magnitude of the vector.

        Returns
        -------
        pd.Series
            Vector magnitude.
        """
        mag = self.data.loc[:, ["x", "y", "z"]]
        mag = mag.pow(2).sum(axis=1, skipna=False).pow(0.5)
        mag.name = "mag"
        return mag

    @property
    def magnitude(self) -> pd.Series:
        """Alias for :py:attr:`mag`.

        Returns
        -------
        pd.Series
            Vector magnitude.
        """
        return self.mag

    @property
    def rho(self) -> pd.Series:
        """Magnitude of the vector in the xy-plane.

        Returns
        -------
        pd.Series
            XY-plane magnitude.
        """
        rho = self.data.loc[:, ["x", "y"]]
        rho = rho.pow(2).sum(axis=1, skipna=False).pow(0.5)
        rho.name = "rho"
        return rho

    @property
    def colat(self):
        """Shortcut to colatitude property.

        Returns
        -------
        pd.Series
            Colatitude in degrees.
        """
        return self.colatitude

    @property
    def colatitude(self) -> pd.Series:
        """Colatitude of the vector.

        Returns
        -------
        pd.Series
            Colatitude in degrees.
        """
        colat = np.rad2deg(np.arctan2(self.data.z, self.rho))
        colat.name = "colatitude"
        return colat

    @property
    def lat(self):
        """Shortcut to latitude property.

        Returns
        -------
        pd.Series
            Latitude in degrees.
        """
        return self.latitude

    @property
    def latitude(self):
        """Latitude of the vector.

        Returns
        -------
        pd.Series
            Latitude in degrees.
        """
        lat = np.rad2deg(np.arctan2(self.rho, self.data.z))
        lat.name = "latitude"
        return lat

    @property
    def longitude(self) -> pd.Series:
        """Longitude of the vector.

        Returns
        -------
        pd.Series
            Longitude in degrees.
        """
        lon = np.rad2deg(np.arctan2(self.data.y, self.data.x))
        lon.name = "longitude"
        return lon

    @property
    def lon(self) -> pd.Series:
        """Shortcut for :py:attr:`longitude`.

        Returns
        -------
        pd.Series
            Longitude in degrees.
        """
        return self.longitude

    @property
    def r(self) -> pd.Series:
        """Shortcut to :py:attr:`mag` when using spherical coordinates.

        Returns
        -------
        pd.Series
            Vector magnitude.
        """
        r = self.mag
        r.name = "r"
        return r

    @property
    def cartesian(self) -> pd.DataFrame:
        """Cartesian coordinates of the vector.

        Returns
        -------
        pd.DataFrame
            Columns ``x``, ``y`` and ``z``.
        """
        return self.data.loc[:, ["x", "y", "z"]]

    @property
    def unit_vector(self) -> "Vector":
        """Cartesian unit vector.

        Returns
        -------
        Vector
            Normalised vector.
        """
        uv = self.cartesian.divide(self.mag, axis=0)
        uv.name = "uv"
        return Vector(uv)

    @property
    def uv(self) -> "Vector":
        """Shortcut for :py:attr:`unit_vector`.

        Returns
        -------
        Vector
            Normalised vector.
        """
        return self.unit_vector

    def project(self, other: "Vector | pd.DataFrame") -> pd.DataFrame:
        """Project self onto ``other``.

        Parameters
        ----------
        other : :class:`Vector` or :class:`pandas.DataFrame`
            Vector to project onto.

        Returns
        -------
        pd.DataFrame
            Parallel and perpendicular components of the projection.

        Raises
        ------
        NotImplementedError
            If ``other`` is not a ``Vector`` or ``DataFrame``.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            raise NotImplementedError(
                f"Project method not implemented for {type(other)}"
            )

        cart = self.cartesian
        par = cart.multiply(other, axis=1).sum(axis=1)
        per = (
            cart.subtract(other.multiply(par, axis=0), axis=1)
            .pow(2)
            .sum(axis=1)
            .pipe(np.sqrt)
        )
        return pd.concat([par, per], axis=1, keys=("par", "per"), sort=True)

    def cos_theta(self, other: "Vector | pd.DataFrame") -> pd.Series:
        """Cosine of the angle between this vector and ``other``.

        Parameters
        ----------
        other : :class:`Vector` or :class:`pandas.DataFrame`
            Vector to calculate the angle with.

        Returns
        -------
        pd.Series
            Cosine of the angle.

        Raises
        ------
        NotImplementedError
            If ``other`` is not a ``Vector`` or ``DataFrame``.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            raise NotImplementedError(
                f"cos_theta method not implemented for {type(other)}"
            )

        return self.uv.data.multiply(other, axis=1).sum(axis=1)


class BField(Vector):
    """A class representing a magnetic field, inheriting from Vector."""

    @property
    def pressure(self) -> pd.Series:
        r"""Calculate the magnetic pressure or energy density.

        Returns
        -------
        pd.Series
            Magnetic pressure.

        Notes
        -----
        The magnetic pressure is calculated using

        .. math::
           p_B = \frac{1}{2\mu_0} B^2
        """
        bsq = self.mag.pow(2.0)
        const = self.units.b**2.0 / (2.0 * self.constants.misc.mu0 * self.units.pth)
        pb = bsq * const
        pb.name = "pb"
        return pb

    @property
    def pb(self) -> pd.Series:
        """Shortcut for :py:attr:`pressure`.

        Returns
        -------
        pd.Series
            Magnetic pressure.
        """
        return self.pressure
