#!/usr/bin/env python
"""A Vector class and subclasses.

This module provides a Vector class and its subclass BField for handling
vector operations and magnetic field calculations.
"""

from typing import Union
import numpy as np
import pandas as pd

pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
except ImportError:
    import base


class Vector(base.Base):
    """A class representing a 3D vector.

    This class provides methods for vector operations and coordinate transformations.

    Attributes:
        data (pd.DataFrame): The vector data with 'x', 'y', and 'z' components.
    """

    def __init__(self, data: pd.DataFrame):
        """Initialize a Vector object.

        Args:
            data (pd.DataFrame): The vector data with 'x', 'y', and 'z' components.
        """
        super().__init__(data)

    def __call__(self, component: str) -> pd.Series:
        """Return the specified component of the vector.

        Args:
            component (str): The component to return ('x', 'y', or 'z').

        Returns:
            pd.Series: The specified component of the vector.
        """
        return self.__getattr__(component)

    def set_data(self, new: pd.DataFrame):
        """Set new data for the vector.

        Args:
            new (pd.DataFrame): The new vector data.

        Raises:
            ValueError: If the new data doesn't have the required columns.
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

        Returns:
            pd.Series: The magnitude of the vector.
        """
        mag = self.data.loc[:, ["x", "y", "z"]]
        mag = mag.pow(2).sum(axis=1, skipna=False).pow(0.5)
        mag.name = "mag"
        return mag

    @property
    def magnitude(self) -> pd.Series:
        """Alias for `mag`.

        Returns:
            pd.Series: The magnitude of the vector.
        """
        return self.mag

    @property
    def rho(self) -> pd.Series:
        """Calculate the magnitude of the vector in the xy-plane.

        Returns:
            pd.Series: The magnitude of the vector in the xy-plane.
        """
        rho = self.data.loc[:, ["x", "y"]]
        rho = rho.pow(2).sum(axis=1, skipna=False).pow(0.5)
        rho.name = "rho"
        return rho

    @property
    def colat(self) -> pd.Series:
        """Calculate the colatitude of the vector.

        Returns:
            pd.Series: The colatitude of the vector in degrees.
        """
        colat = np.rad2deg(np.arctan2(self.data.z, self.rho))
        colat.name = "colat"
        return colat

    @property
    def longitude(self) -> pd.Series:
        """Calculate the longitude of the vector.

        Returns:
            pd.Series: The longitude of the vector in degrees.
        """
        lon = np.rad2deg(np.arctan2(self.data.y, self.data.x))
        lon.name = "longitude"
        return lon

    @property
    def lon(self) -> pd.Series:
        """Shortcut for `longitude`.

        Returns:
            pd.Series: The longitude of the vector in degrees.
        """
        return self.longitude

    @property
    def r(self) -> pd.Series:
        """Shortcut to `mag` property.

        Useful when thinking in spherical coordinates, not magnitudes.

        Returns:
            pd.Series: The magnitude of the vector.
        """
        r = self.mag
        r.name = "r"
        return r

    @property
    def cartesian(self) -> pd.DataFrame:
        """Return the Cartesian coordinates of the vector.

        Returns:
            pd.DataFrame: The Cartesian coordinates (x, y, z) of the vector.
        """
        return self.data.loc[:, ["x", "y", "z"]]

    @property
    def unit_vector(self) -> "Vector":
        """Calculate the Cartesian unit vector.

        Returns:
            Vector: The unit vector.
        """
        uv = self.cartesian.divide(self.mag, axis=0)
        uv.name = "uv"
        return Vector(uv)

    @property
    def uv(self) -> "Vector":
        """Shortcut to `unit_vector` property.

        Returns:
            Vector: The unit vector.
        """
        return self.unit_vector

    def project(self, other: Union["Vector", pd.DataFrame]) -> pd.DataFrame:
        """Project self onto `other`.

        Args:
            other (Union[Vector, pd.DataFrame]): The vector to project onto.

        Returns:
            pd.DataFrame: The parallel and perpendicular components of the projection.

        Raises:
            NotImplementedError: If `other` is not a Vector or DataFrame.
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

    def cos_theta(self, other: Union["Vector", pd.DataFrame]) -> pd.Series:
        """Calculate the cosine of the angle between self and `other`.

        Args:
            other (Union[Vector, pd.DataFrame]): The vector to calculate the angle with.

        Returns:
            pd.Series: The cosine of the angle between the vectors.

        Raises:
            NotImplementedError: If `other` is not a Vector or DataFrame.
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
            The magnetic pressure.
        Notes
        -----
        The magnetic pressure is calculated using the equation:

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
        """Shortcut to `pressure` property.

        Returns:
            pd.Series: The magnetic pressure.
        """
        return self.pressure
