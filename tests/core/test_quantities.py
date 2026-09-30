#!/usr/bin/env python
"""Tests for Vector and Tensor objects."""

import numpy as np
import pandas as pd
import pandas.testing as pdt

from unittest import TestCase
from abc import ABC, abstractproperty
from scipy import constants

from . import test_base as base

from solarwindpy import vector
from solarwindpy import tensor

pd.set_option("mode.chained_assignment", "raise")


class QuantityTestBase(ABC):
    def test_data(self):
        data = self.data
        if isinstance(data, pd.Series):
            pdt.assert_series_equal(data, self.object_testing.data)
        else:
            pdt.assert_frame_equal(data, self.object_testing.data)

    def test_eq(self):
        print_inline_debug = False
        object_testing = self.object_testing
        # ID should be equal.
        self.assertEqual(object_testing, object_testing)
        # Data and type should be equal.
        new_object = object_testing.__class__(object_testing.data)

        if print_inline_debug:
            print(
                "<Test>",
                "<object_testing>",
                type(object_testing),
                object_testing,
                object_testing.data,
                "<new_object>",
                type(new_object),
                new_object,
                new_object.data,
                "",
                sep="\n",
            )

        self.assertEqual(object_testing, new_object)

    def test_neq(self):
        object_testing = self.object_testing
        # Data isn't equal

        self.assertNotEqual(
            object_testing, object_testing.__class__(object_testing.data * 4)
        )
        # Type isn't equal
        for other in (
            [],
            tuple(),
            np.array([]),
            pd.Series(dtype=np.float64),
            pd.DataFrame(dtype=np.float64),
        ):
            self.assertNotEqual(object_testing, other)

    def test_empty_data_catch(self):
        with self.assertRaisesRegex(
            ValueError, "You can't set an object with empty data."
        ):
            self.object_testing.__class__(pd.DataFrame())


#####
# Vectors
#####
class VectorTestBase(QuantityTestBase):
    def test_components(self):

        v = self.data
        ot = self.object_testing.data
        pdt.assert_series_equal(v.x, ot.x)
        pdt.assert_series_equal(v.y, ot.y)
        pdt.assert_series_equal(v.z, ot.z)

    def test_mag(self):
        x = self.data.x
        y = self.data.y
        z = self.data.z
        mag = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        mag.name = "mag"
        pdt.assert_series_equal(mag, self.object_testing.mag)
        pdt.assert_series_equal(mag, self.object_testing.magnitude)
        pdt.assert_series_equal(self.object_testing.mag, self.object_testing.magnitude)

    def test_rho(self):
        x = self.data.x
        y = self.data.y
        rho = np.sqrt(x.pow(2) + y.pow(2))
        rho.name = "rho"
        pdt.assert_series_equal(rho, self.object_testing.rho)

    def test_colat(self):
        x = self.data.x
        y = self.data.y
        z = self.data.z
        colat = np.arctan2(z, np.sqrt(x.pow(2) + y.pow(2)))
        colat = np.rad2deg(colat)
        colat.name = "colatitude"
        pdt.assert_series_equal(colat, self.object_testing.colat)

    def test_longitude(self):
        x = self.data.x
        y = self.data.y
        lon = np.arctan2(y, x)
        lon = np.rad2deg(lon)
        lon.name = "longitude"
        pdt.assert_series_equal(lon, self.object_testing.lon)
        pdt.assert_series_equal(lon, self.object_testing.longitude)
        pdt.assert_series_equal(self.object_testing.lon, self.object_testing.longitude)

    def test_r(self):
        x = self.data.x
        y = self.data.y
        z = self.data.z
        r = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        r.name = "r"
        pdt.assert_series_equal(r, self.object_testing.r)
        pdt.assert_series_equal(r, self.object_testing.mag, check_names=False)
        pdt.assert_series_equal(
            self.object_testing.r, self.object_testing.mag, check_names=False
        )

    def test_cartesian(self):
        v = self.data.loc[:, ["x", "y", "z"]]
        pdt.assert_frame_equal(v, self.object_testing.cartesian)

    def test_unit_vector(self):
        v = self.data.loc[:, ["x", "y", "z"]]
        mag = v.pow(2).sum(axis=1).pipe(np.sqrt)
        uv = v.divide(mag, axis=0)
        uv.name = "uv"
        uv = vector.Vector(uv)
        pdt.assert_frame_equal(uv.data, self.object_testing.unit_vector.data)
        pdt.assert_frame_equal(uv.data, self.object_testing.uv.data)
        pdt.assert_frame_equal(
            self.object_testing.uv.data, self.object_testing.unit_vector.data
        )
        self.assertEqual(uv, self.object_testing.unit_vector)
        self.assertEqual(uv, self.object_testing.uv)
        self.assertEqual(self.object_testing.unit_vector, self.object_testing.uv)

    def test_project(self):
        b = (
            base.SyntheticData()
            .plasma_data.xs("b", axis=1, level="M")
            .xs("", axis=1, level="S")
            .loc[:, ["x", "y", "z"]]
        )
        bmag = b.pow(2).sum(axis=1).pipe(np.sqrt)
        buv = b.divide(bmag, axis=0)

        v = self.data.loc[:, ["x", "y", "z"]]
        vmag = v.pow(2).sum(axis=1).pipe(np.sqrt)

        par = v.multiply(buv, axis=1).sum(axis=1)
        per = (
            v.subtract(buv.multiply(par, axis=0), axis=1)
            .pow(2)
            .sum(axis=1)
            .pipe(np.sqrt)
        )
        projected = pd.concat([par, per], axis=1, keys=["par", "per"], sort=True)

        b = vector.Vector(b)
        pdt.assert_frame_equal(projected, self.object_testing.project(b))

        # Projecting a thing onto itself should return 1 for parallel
        # and 0 for perp.
        per = pd.Series(0.0, index=per.index)
        projected = pd.concat([vmag, per], axis=1, keys=["par", "per"], sort=True)
        pdt.assert_frame_equal(
            projected, self.object_testing.project(self.object_testing)
        )

        msg = "method not implemented"
        with self.assertRaisesRegex(NotImplementedError, msg):
            self.object_testing.project(b.data)

    def test_cos_theta(self):
        b = (
            base.SyntheticData()
            .plasma_data.xs("b", axis=1, level="M")
            .xs("", axis=1, level="S")
            .loc[:, ["x", "y", "z"]]
        )
        bmag = b.pow(2).sum(axis=1).pipe(np.sqrt)
        buv = b.divide(bmag, axis=0)

        v = self.data.loc[:, ["x", "y", "z"]]
        vmag = v.pow(2).sum(axis=1).pipe(np.sqrt)
        vuv = v.divide(vmag, axis=0)

        cos_theta = vuv.multiply(buv, axis=1).sum(axis=1)

        b = vector.BField(b)
        pdt.assert_series_equal(cos_theta, self.object_testing.cos_theta(b))

        # Projecting a thing onto itself should return 1 for parallel
        # and 0 for perp.
        v = vector.Vector(v)
        vuv = vector.Vector(vuv)
        par = pd.Series(1.0, index=vmag.index)
        pdt.assert_series_equal(par, self.object_testing.cos_theta(v))
        pdt.assert_series_equal(par, self.object_testing.cos_theta(vuv))

        msg = "method not implemented"
        with self.assertRaisesRegex(NotImplementedError, msg):
            self.object_testing.project(b.data)


class TestBField(VectorTestBase, base.SWEData):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.b.xs("", axis=1, level="S")
        b = vector.BField(data)
        cls.object_testing = b
        cls.data = data

    def test_pressure(self):
        print_inline_debug = False
        bsq = self.data.loc[:, ["x", "y", "z"]].pow(2.0).sum(axis=1)
        const = 1e-18 / (2.0 * constants.mu_0 * 1e-12)  # ([b]**2 / 2.0 * \mu_0 * [p])
        pb = bsq * const
        pb.name = "pb"

        if print_inline_debug:
            print(
                "",
                "<Test>",
                "<bsq>",
                type(bsq),
                bsq,
                "<const>: %s" % const,
                "<pb>",
                type(pb),
                pb,
                sep="\n",
                end="\n\n",
            )
            print(
                "<Module>",
                "<object testing>",
                type(self.object_testing),
                self.object_testing,
                "<dir(ot)>",
                *dir(self.object_testing),
                sep="\n",
                end="\n\n",
            )

        pdt.assert_series_equal(pb, self.object_testing.pressure)
        pdt.assert_series_equal(pb, self.object_testing.pb)
        pdt.assert_series_equal(self.object_testing.pressure, self.object_testing.pb)


class VelocityTestBase(VectorTestBase):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.v.xs(cls().species, axis=1, level="S")
        v = vector.Vector(data)
        cls.object_testing = v
        cls.data = data

    @abstractproperty
    def species(self):
        pass


class TestVelocityAlpha(base.AlphaTest, VelocityTestBase, base.SWEData):
    pass


class TestVelocityP1(base.P1Test, VelocityTestBase, base.SWEData):
    pass


class TestVelocityP2(base.P2Test, VelocityTestBase, base.SWEData):
    pass


#####
# Tensors
#####
class TensorTestBase(QuantityTestBase):
    def test_components(self):
        t = self.data
        ot = self.object_testing.data
        pdt.assert_series_equal(t.par, ot.par)
        pdt.assert_series_equal(t.per, ot.per)
        pdt.assert_series_equal(t.scalar, ot.scalar)


class ThermalSpeedTestBase(TensorTestBase):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.w.xs(cls().species, axis=1, level="S")
        coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
        scalar = (
            data.pow(2).multiply(coeff, axis=1, level="C").sum(axis=1).pipe(np.sqrt)
        )
        scalar.name = "scalar"
        data = pd.concat([data, scalar], axis=1).sort_index(axis=1)
        w = tensor.Tensor(data)
        cls.object_testing = w
        cls.data = data

    @abstractproperty
    def species(self):
        pass


class TestThermalSpeedAlpha(base.AlphaTest, ThermalSpeedTestBase, base.SWEData):
    pass


class TestThermalSpeedP1(base.P1Test, ThermalSpeedTestBase, base.SWEData):
    pass


class TestThermalSpeedP2(base.P2Test, ThermalSpeedTestBase, base.SWEData):
    pass


class TestQuantitySubclassEquality(TestCase):
    @classmethod
    def setUpClass(cls):
        r"""Override `setUpClass` so that it doesn't call `set_object_testing`."""
        fixture = base.SyntheticData()
        data = fixture.plasma_data
        cls.gse = fixture.spacecraft_data.gse
        coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
        scalar = data.w.pow(2).multiply(coeff, axis=1, level="C")

        scalar = scalar.T.groupby(level="S").sum().T.pow(0.5)

        cols = pd.MultiIndex.from_tuples(
            scalar.columns.to_series().apply(lambda x: ("w", "scalar", x)),
            names=data.columns.names,
        )
        scalar.columns = cols
        scalar.name = "scalar"
        data = pd.concat([data, scalar], axis=1).sort_index(axis=1)
        cls.data = data

    def test_v(self):
        data = self.data.v.xs("a", axis=1, level="S")
        va0 = vector.Vector(data)
        va1 = vector.Vector(data)
        self.assertEqual(va0, va0)
        self.assertEqual(va0, va1)

    def test_b(self):
        data = self.data.b.xs("", axis=1, level="S")
        b0 = vector.BField(data)
        b1 = vector.BField(data)
        self.assertEqual(b0, b0)
        self.assertEqual(b0, b1)

    def test_b_v(self):
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        v = vector.Vector(self.data.v.xs("p2", axis=1, level="S"))
        self.assertNotEqual(b, v)

    def test_b_w(self):
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        w = tensor.Tensor(self.data.w.xs("a", axis=1, level="S"))
        self.assertNotEqual(b, w)

    def test_gse(self):
        """Vectors from one GSE position are equal; a shifted one is not.

        The shifted position is displaced by 1.0 along GSE x.

        ON FAILURE: the code is wrong.
        """
        gse0 = vector.Vector(self.gse)
        gse1 = vector.Vector(self.gse)
        shifted = self.gse.copy()
        shifted["x"] = shifted["x"] + 1.0
        gse2 = vector.Vector(shifted)
        self.assertEqual(gse0, gse0)
        self.assertEqual(gse0, gse1)
        self.assertNotEqual(gse0, gse2)

    def test_b_gse(self):
        """A BField never equals a Vector, here the GSE position.

        ON FAILURE: the code is wrong.
        """
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        gse = vector.Vector(self.gse)
        self.assertNotEqual(b, gse)

    def test_gse_v(self):
        """Vectors holding different data (GSE position, p2 velocity) differ.

        ON FAILURE: the code is wrong.
        """
        gse = vector.Vector(self.gse)
        v = vector.Vector(self.data.v.xs("p2", axis=1, level="S"))
        self.assertNotEqual(gse, v)

    def test_gse_w(self):
        """A Vector (GSE position) never equals a Tensor (alpha thermal speed).

        ON FAILURE: the code is wrong.
        """
        gse = vector.Vector(self.gse)
        w = tensor.Tensor(self.data.w.xs("a", axis=1, level="S"))
        self.assertNotEqual(gse, w)

    def test_va_vp1(self):
        va = vector.Vector(self.data.v.xs("a", axis=1, level="S"))
        vp1 = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        self.assertNotEqual(va, vp1)

    def test_v_w(self):
        v = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        w = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        self.assertNotEqual(v, w)

    def test_wp1_wp2(self):
        wp1 = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        wp2 = tensor.Tensor(self.data.w.xs("p2", axis=1, level="S"))
        self.assertNotEqual(wp1, wp2)
