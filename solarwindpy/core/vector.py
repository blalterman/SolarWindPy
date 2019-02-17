#!/usr/bin/env python
"""A Vector class and subclasses.

:py:class:`Vector` inherets :py:class:`~solarwindpy.core.Base`. The subclass
:py:class:`BField:` inheretes :py:class:`Vector`.
"""
import pdb  # noqa: F401
import numpy as np
import pandas as pd


# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
except ImportError:
    import base


class Vector(base.Base):
    def __init__(self, data):
        # print("Vector.__init__", data)
        super(Vector, self).__init__(data)

    def __call__(self, component):
        assert isinstance(component, str)
        return self.__getattr__(component)  # getattr(self, component)

    def set_data(self, new):
        # print("Vector.set_data", new)
        super(Vector, self).set_data(new)
        chk = pd.Index(["x", "y", "z"])
        assert not isinstance(new.columns, pd.MultiIndex)
        if not chk.isin(new.columns).all():
            msg = "\nTarget columns:\n%s\nAttempted:\n%s"
            msg = msg % (chk, new.columns)
            raise ValueError(msg)
        self._data = new

    @property
    def mag(self):
        mag = self.data.loc[:, ["x", "y", "z"]]
        assert mag.shape[1] == 3
        # TOOD: test for skipna behavior in mag propagation.
        #          Want to ensure we don't create valid data points when they don't exist.
        mag = mag.pow(2).sum(axis=1, skipna=False).pipe(np.sqrt)
        mag.name = "mag"
        return mag

    @property
    def magnitude(self):
        r"""
        Alias for `mag`.
        """
        return self.mag

    @property
    def rho(self):
        rho = self.data.loc[:, ["x", "y"]]
        assert rho.shape[1] == 2
        # TODO: test `skipna=False` behvior.
        rho = rho.pow(2).sum(axis=1, skipna=False).pipe(np.sqrt)
        rho.name = "rho"
        return rho

    @property
    def colat(self):
        colat = np.rad2deg(np.arctan2(self.data.z, self.rho))
        colat.name = "colat"
        return colat

    @property
    def longitude(self):
        lon = np.rad2deg(np.arctan2(self.data.y, self.data.x))
        lon.name = "longitude"
        return lon

    @property
    def lon(self):
        r"""
        Sortcut for `self.longitude`.
        """
        return self.longitude

    @property
    def r(self):
        r"""
        Shortcut to `mag` property.

        Useful when thinking in spherical coordinates, not
        magnitudes.
        """
        r = self.mag
        r.name = "r"
        return r

    @property
    def cartesian(self):
        r"""
        Cartesian coordinates: (x, y, z).
        """
        return self.data.loc[:, ["x", "y", "z"]]

    @property
    def unit_vector(self):
        r"""
        Cartesian unit vector.
        """
        v = self.cartesian
        m = self.mag
        uv = v.divide(m, axis=0)
        uv.name = "uv"
        return Vector(uv)

    @property
    def uv(self):
        r"""
        Shortcut to `unit_vector` property.
        """
        return self.unit_vector

    def project(self, other):
        r"""
        Project self onto `other`.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            msg = "`project` method needs algo development to use a `%s`."
            raise NotImplementedError(msg % type(other))

        cart = self.cartesian
        par = cart.multiply(other, axis=1).sum(axis=1)
        per = (
            cart.subtract(other.multiply(par, axis=0), axis=1)
            .pow(2)
            .sum(axis=1)
            .pipe(np.sqrt)
        )
        out = pd.concat([par, per], axis=1, keys=("par", "per")).sort_index(axis=1)

        # print("",
        #       "<Module>",
        #       "<uv>", type(other), other,
        #       "<cartesian>", type(cart), cart,
        #       "<projected>", type(out), out,
        #       "",
        #       sep="\n")

        return out

    def cos_theta(self, other):
        r"""
        Project self onto `other`.
        """
        if isinstance(other, Vector):
            other = other.uv.data
        else:
            msg = "`project` method needs algo development to use a `%s`."
            raise NotImplementedError(msg % type(other))

        uv = self.uv
        out = uv.multiply(other, axis=1).sum(axis=1)

        # print("",
        #       "<Module>",
        #       "<other>", type(other), other,
        #       "<uv>", type(uv), uv,
        #       "<out>", type(out), out,
        #       "",
        #       sep="\n")

        return out


class BField(Vector):
    @property
    def pressure(self):
        r"""Magnetic pressure or energy density in same units as thermal pressure.

            :math:`p_B = \frac{1}{2\mu_0} B^2`
        """
        bsq = self.mag.pow(2.0)
        const = self.units.b ** 2.0 / (2.0 * self.constants.misc.mu0 * self.units.pth)
        pb = bsq * const
        pb.name = "pb"
        return pb

    @property
    def pb(self):
        r"""
        Shortcut to :py:meth:`pressure`.
        """
        return self.pressure
