#!/usr/bin/env python
"""A Vector class and subclasses.

This module provides a Vector class and its subclass BField for handling vector
operations and magnetic field calculations.
"""

__all__ = [
    "Vector",
    "BField",
]

import numpy as np
import pandas as pd

from . import base


class Vector(base._ComponentFrame):
    """Three-dimensional vector container.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data with ``x``, ``y`` and ``z`` components.

    Examples
    --------
    A (3, 4, 0) vector has magnitude 5 and lies in the xy-plane, 90 degrees
    from +z; a (0, 0, 2) vector points along +z:

    >>> import pandas as pd
    >>> from solarwindpy.core.vector import Vector
    >>> t = pd.date_range("2020-01-01", periods=2, freq="min")
    >>> v = Vector(pd.DataFrame({"x": [3.0, 0.0], "y": [4.0, 0.0],
    ...                          "z": [0.0, 2.0]}, index=t))
    >>> v.mag.tolist()
    [5.0, 2.0]
    >>> v.colat.tolist()
    [90.0, 0.0]
    >>> v.uv.cartesian.loc[:, ["x", "y"]].iloc[0].tolist()
    [0.6, 0.8]

    A :class:`~solarwindpy.core.plasma.Plasma` holds each species' velocity
    as a vector:

    >>> import solarwindpy as swp
    >>> plasma = swp.examples.load_plasma()
    >>> plasma.p1.v.mag.round(2).tolist()
    [458.26, 700.0, 1044.03]
    """

    def __init__(self, data: pd.DataFrame, *, _time_checked: pd.Index | None = None):
        """Initialize a :class:`Vector` instance.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            The vector data with ``x``, ``y`` and ``z`` components.
        _time_checked : pandas.Index, optional
            Private; see :class:`~solarwindpy.core.base.Base`.
        """
        super().__init__(data, _time_checked=_time_checked)

    def set_data(self, new: pd.DataFrame):
        """Set new vector data.

        Parameters
        ----------
        new : :class:`pandas.DataFrame`
            New vector data. Rows out of time order are sorted with one
            warning, as :class:`~solarwindpy.core.plasma.Plasma` sorts its
            data.

        Raises
        ------
        ValueError
            If ``new`` does not contain the required columns, holds more than
            one species, or its time index holds missing timestamps (``NaT``).
        """
        new = self._put_in_time_order_unless_checked(new)
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
        mag = self._component_reduce(self.cartesian.pow(2)).pow(0.5)
        mag.name = "mag"
        return mag

    @property
    def rho(self) -> pd.Series:
        """Magnitude of the vector in the xy-plane.

        Returns
        -------
        pd.Series
            XY-plane magnitude.
        """
        rho = self._select(self.data, ["x", "y"], "C")
        rho = self._component_reduce(rho.pow(2)).pow(0.5)
        rho.name = "rho"
        return rho

    @property
    def colat(self) -> pd.Series:
        """Colatitude of the vector, the angle from the +z axis.

        Returns
        -------
        pd.Series
            Colatitude in degrees, in [0, 180]: 0 on +z, 90 in the xy-plane.

        Notes
        -----
        ``colat = arctan2(rho, z) = 90 - lat``.
        """
        colat = np.rad2deg(np.arctan2(self.rho, self("z")))
        colat.name = "colat"
        return colat

    @property
    def lat(self):
        """Latitude of the vector, the angle above the xy-plane.

        Returns
        -------
        pd.Series
            Latitude in degrees, in [-90, 90]: 90 on +z, 0 in the xy-plane.

        Notes
        -----
        ``lat = arctan2(z, rho) = 90 - colat``.
        """
        lat = np.rad2deg(np.arctan2(self("z"), self.rho))
        lat.name = "lat"
        return lat

    @property
    def lon(self) -> pd.Series:
        """Longitude of the vector.

        Returns
        -------
        pd.Series
            Longitude in degrees.
        """
        lon = np.rad2deg(np.arctan2(self("y"), self("x")))
        lon.name = "lon"
        return lon

    @property
    def cartesian(self) -> pd.DataFrame:
        """Cartesian coordinates of the vector.

        Returns
        -------
        pd.DataFrame
            Columns ``x``, ``y`` and ``z``.
        """
        return self._select(self.data, ["x", "y", "z"], "C")

    @property
    def uv(self) -> "Vector":
        """Cartesian unit vector.

        Returns
        -------
        Vector
            Normalised vector, derived row by row from this vector's
            already-checked data, so it skips the time checks.
        """
        uv = self.cartesian.divide(self.mag, axis=0)
        uv.name = "uv"
        return Vector(uv, _time_checked=self.data.index)

    def project(self, other: "Vector") -> pd.DataFrame:
        """Project self onto ``other``.

        Parameters
        ----------
        other : :class:`Vector`
            Vector to project onto; only its direction is used.

        Returns
        -------
        pd.DataFrame
            Parallel and perpendicular components of the projection, on the union
            of both indices; NaN on rows missing from either vector.

        Raises
        ------
        NotImplementedError
            If ``other`` is not a ``Vector``, including a bare ``DataFrame``.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            raise NotImplementedError(
                f"Project method not implemented for {type(other)}"
            )

        cart = self.cartesian
        par = self._component_reduce(cart.multiply(other, axis=1))
        per = self._component_reduce(
            cart.subtract(other.multiply(par, axis=0), axis=1).pow(2)
        ).pipe(np.sqrt)
        return pd.concat([par, per], axis=1, keys=("par", "per"), sort=True)

    def cos_theta(self, other: "Vector") -> pd.Series:
        """Cosine of the angle between this vector and ``other``.

        Parameters
        ----------
        other : :class:`Vector`
            Vector to calculate the angle with.

        Returns
        -------
        pd.Series
            Cosine of the angle, on the union of both indices; NaN on rows
            missing from either vector.

        Raises
        ------
        NotImplementedError
            If ``other`` is not a ``Vector``, including a bare ``DataFrame``.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            raise NotImplementedError(
                f"cos_theta method not implemented for {type(other)}"
            )

        cos_theta = self._component_reduce(self.uv.data.multiply(other, axis=1))
        cos_theta.name = "cos_theta"
        return cos_theta


class BField(Vector):
    """A class representing a magnetic field, inheriting from Vector."""

    @property
    def pb(self) -> pd.Series:
        r"""Calculate the magnetic pressure or energy density.

        Returns
        -------
        pd.Series
            Magnetic pressure.

        Notes
        -----
        The magnetic pressure is calculated using

        .. math::
           P_B = \frac{1}{2\mu_0} B^2
        """
        bsq = self.mag.pow(2.0)
        const = self.units.b**2.0 / (2.0 * self.constants.misc.mu0 * self.units.pth)
        pb = bsq * const
        pb.name = "pb"
        return pb
