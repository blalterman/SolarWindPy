#!/usr/bin/env python
"""Tests for Vector and Tensor objects."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from unittest import TestCase
from abc import ABC, abstractproperty
from scipy import constants

from . import test_base as base

from solarwindpy.core import vector
from solarwindpy.core import tensor
from solarwindpy.core import plasma

pd.set_option("mode.chained_assignment", "raise")

# Angles are O(1-180) degrees computed from exact inputs, so 1e-12 absolute is far below
# any formula error (the smallest wrong answer in these cases is off by >= 1 degree).
ANGLE_TOL = dict(rtol=1e-12, atol=1e-12)
# Projections and cosines are O(1) and computed from exact inputs; same reasoning.
VALUE_TOL = dict(rtol=1e-12, atol=1e-12)


def _hand_vector(rows, cls=vector.Vector):
    """Build a Vector from hand-chosen (x, y, z) rows on a DatetimeIndex."""
    index = pd.date_range("2000-01-01", periods=len(rows), freq="min")
    return cls(pd.DataFrame(rows, index=index, columns=["x", "y", "z"], dtype=float))


class QuantityTestBase(ABC):
    def test_data(self):
        """The object's data is the frame it was built from.

        ON FAILURE: the code is wrong.
        """
        data = self.data
        if isinstance(data, pd.Series):
            pdt.assert_series_equal(data, self.object_testing.data)
        else:
            pdt.assert_frame_equal(data, self.object_testing.data)

    def test_eq(self):
        """An object equals itself and a new object of its class built from its data.

        ON FAILURE: the code is wrong.
        """
        object_testing = self.object_testing
        self.assertEqual(object_testing, object_testing)
        new_object = object_testing.__class__(object_testing.data)
        self.assertEqual(object_testing, new_object)

    def test_neq(self):
        """An object differs from one with scaled data and from non-quantity containers.

        ON FAILURE: the code is wrong.
        """
        object_testing = self.object_testing
        self.assertNotEqual(
            object_testing, object_testing.__class__(object_testing.data * 4)
        )
        for other in (
            [],
            tuple(),
            np.array([]),
            pd.Series(dtype=np.float64),
            pd.DataFrame(dtype=np.float64),
        ):
            self.assertNotEqual(object_testing, other)

    def test_empty_data_catch(self):
        """Building an object from an empty frame raises ValueError.

        ON FAILURE: the code is wrong.
        """
        with self.assertRaisesRegex(
            ValueError, "You can't set an object with empty data."
        ):
            self.object_testing.__class__(pd.DataFrame())


#####
# Vectors
#####
class VectorTestBase(QuantityTestBase):
    def test_components(self):
        """The x, y and z components are the input columns.

        ON FAILURE: the code is wrong.
        """
        v = self.data
        ot = self.object_testing.data
        pdt.assert_series_equal(v.x, ot.x)
        pdt.assert_series_equal(v.y, ot.y)
        pdt.assert_series_equal(v.z, ot.z)

    def test_mag(self):
        """mag and magnitude are sqrt(x^2 + y^2 + z^2).

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        z = self.data.z
        mag = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        mag.name = "mag"
        pdt.assert_series_equal(mag, self.object_testing.mag)
        pdt.assert_series_equal(mag, self.object_testing.magnitude)

    def test_rho(self):
        """rho is the xy-plane magnitude sqrt(x^2 + y^2).

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        rho = np.sqrt(x.pow(2) + y.pow(2))
        rho.name = "rho"
        pdt.assert_series_equal(rho, self.object_testing.rho)

    def test_latitude_and_colatitude(self):
        """Latitude is arctan2(z, rho) and colatitude is arctan2(rho, z), in degrees.

        Latitude is measured from the xy-plane and colatitude from the +z axis, so
        latitude + colatitude = 90 for every row. The hand cases live in
        ``TestVectorAngleHandCases``.

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        z = self.data.z
        rho = np.sqrt(x.pow(2) + y.pow(2))
        lat = np.rad2deg(np.arctan2(z, rho))
        lat.name = "latitude"
        colat = np.rad2deg(np.arctan2(rho, z))
        colat.name = "colatitude"
        pdt.assert_series_equal(lat, self.object_testing.latitude)
        pdt.assert_series_equal(lat, self.object_testing.lat)
        pdt.assert_series_equal(colat, self.object_testing.colatitude)
        pdt.assert_series_equal(colat, self.object_testing.colat)
        np.testing.assert_allclose(
            self.object_testing.lat + self.object_testing.colat, 90.0, **ANGLE_TOL
        )

    def test_longitude(self):
        """lon and longitude are arctan2(y, x) in degrees.

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        lon = np.arctan2(y, x)
        lon = np.rad2deg(lon)
        lon.name = "longitude"
        pdt.assert_series_equal(lon, self.object_testing.lon)
        pdt.assert_series_equal(lon, self.object_testing.longitude)

    def test_r(self):
        """r is the magnitude sqrt(x^2 + y^2 + z^2), named "r".

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        z = self.data.z
        r = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        r.name = "r"
        pdt.assert_series_equal(r, self.object_testing.r)
        pdt.assert_series_equal(r, self.object_testing.mag, check_names=False)

    def test_cartesian(self):
        """cartesian returns the x, y and z columns.

        ON FAILURE: the code is wrong.
        """
        v = self.data.loc[:, ["x", "y", "z"]]
        pdt.assert_frame_equal(v, self.object_testing.cartesian)

    def test_unit_vector(self):
        """unit_vector and uv are the vector divided by its magnitude.

        ON FAILURE: the code is wrong.
        """
        v = self.data.loc[:, ["x", "y", "z"]]
        mag = v.pow(2).sum(axis=1).pipe(np.sqrt)
        uv = vector.Vector(v.divide(mag, axis=0))
        pdt.assert_frame_equal(uv.data, self.object_testing.unit_vector.data)
        pdt.assert_frame_equal(uv.data, self.object_testing.uv.data)
        self.assertEqual(uv, self.object_testing.unit_vector)
        self.assertEqual(uv, self.object_testing.uv)

    def test_project(self):
        """project splits the vector into components parallel and perpendicular to B.

        Re-derives par = v . b_hat and per = |v - par b_hat|; projecting a vector onto
        itself gives par = |v| and per = 0. The hand cases live in
        ``TestVectorProjectionHandCases``.

        ON FAILURE: the code is wrong.
        """
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

        per = pd.Series(0.0, index=per.index)
        projected = pd.concat([vmag, per], axis=1, keys=["par", "per"], sort=True)
        pdt.assert_frame_equal(
            projected, self.object_testing.project(self.object_testing)
        )

        with self.assertRaisesRegex(NotImplementedError, "DataFrame"):
            self.object_testing.project(b.data)

    def test_cos_theta(self):
        """cos_theta is the dot product of the two unit vectors.

        Re-derives v_hat . b_hat; a vector against itself, or its own unit vector,
        gives 1. The hand cases live in ``TestVectorProjectionHandCases``.

        ON FAILURE: the code is wrong.
        """
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

        v = vector.Vector(v)
        vuv = vector.Vector(vuv)
        par = pd.Series(1.0, index=vmag.index)
        pdt.assert_series_equal(par, self.object_testing.cos_theta(v))
        pdt.assert_series_equal(par, self.object_testing.cos_theta(vuv))

        with self.assertRaisesRegex(NotImplementedError, "DataFrame"):
            self.object_testing.cos_theta(b.data)


class TestBField(VectorTestBase, base.SWEData):
    @classmethod
    def set_object_testing(cls):
        data = cls.data.b.xs("", axis=1, level="S")
        b = vector.BField(data)
        cls.object_testing = b
        cls.data = data

    def test_pressure(self):
        """pressure and pb are B^2 / (2 mu_0), with B in nT and the result in pPa.

        ON FAILURE: the code is wrong.
        """
        bsq = self.data.loc[:, ["x", "y", "z"]].pow(2.0).sum(axis=1)
        const = 1e-18 / (2.0 * constants.mu_0 * 1e-12)  # ([b]**2 / 2.0 * \mu_0 * [p])
        pb = bsq * const
        pb.name = "pb"
        pdt.assert_series_equal(pb, self.object_testing.pressure)
        pdt.assert_series_equal(pb, self.object_testing.pb)


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


class TestVectorAngleHandCases:
    """Latitude and colatitude of hand-chosen directions.

    Latitude is the angle above the xy-plane, in [-90, 90]; colatitude is the angle
    from the +z axis, in [0, 180]. Each row's answer follows from its direction.
    """

    # (x, y, z), latitude, colatitude
    CASES = [
        ((0.0, 0.0, 1.0), 90.0, 0.0),  # +z axis: pole
        ((1.0, 0.0, 0.0), 0.0, 90.0),  # +x axis: in the xy-plane
        ((0.0, 0.0, -2.0), -90.0, 180.0),  # -z axis: opposite pole
        ((1.0, 1.0, np.sqrt(2.0)), 45.0, 45.0),  # rho = z = sqrt(2)
        ((0.0, -3.0, -np.sqrt(3.0)), -30.0, 120.0),  # z/rho = -1/sqrt(3)
    ]

    @pytest.fixture
    def v(self):
        return _hand_vector([c[0] for c in self.CASES])

    def test_latitude_of_hand_directions(self, v):
        """latitude and lat are 90 on +z, 0 on +x, -90 on -z, 45 and -30 off-axis.

        ON FAILURE: the code is wrong.
        """
        expected = [c[1] for c in self.CASES]
        np.testing.assert_allclose(v.latitude, expected, **ANGLE_TOL)
        np.testing.assert_allclose(v.lat, expected, **ANGLE_TOL)

    def test_colatitude_of_hand_directions(self, v):
        """colatitude and colat are 0 on +z, 90 on +x, 180 on -z, 45 and 120 off-axis.

        ON FAILURE: the code is wrong.
        """
        expected = [c[2] for c in self.CASES]
        np.testing.assert_allclose(v.colatitude, expected, **ANGLE_TOL)
        np.testing.assert_allclose(v.colat, expected, **ANGLE_TOL)


class TestVectorProjectionHandCases:
    """project and cos_theta on hand-chosen pairs.

    Rows (v; b):
    (3, 4, 0) on (2, 0, 0): par = 3, per = 4, cos = 3/5.
    (1, 1, 1) on (0, 0, 5): par = 1, per = sqrt(2), cos = 1/sqrt(3).
    (0, -2, 0) on (0, 3, 0): antiparallel, par = -2, per = 0, cos = -1.
    B is never unit length, so a missing normalisation changes every answer.
    """

    V = [(3.0, 4.0, 0.0), (1.0, 1.0, 1.0), (0.0, -2.0, 0.0)]
    B = [(2.0, 0.0, 0.0), (0.0, 0.0, 5.0), (0.0, 3.0, 0.0)]

    @pytest.fixture
    def v(self):
        return _hand_vector(self.V)

    @pytest.fixture
    def b(self):
        return _hand_vector(self.B, cls=vector.BField)

    def test_project_gives_hand_parallel_and_perpendicular(self, v, b):
        """project returns par = (3, 1, -2) and per = (4, sqrt(2), 0), in that column order.

        ON FAILURE: the code is wrong.
        """
        out = v.project(b)
        assert list(out.columns) == ["par", "per"]
        pdt.assert_index_equal(out.index, v.data.index)
        np.testing.assert_allclose(out["par"], [3.0, 1.0, -2.0], **VALUE_TOL)
        np.testing.assert_allclose(out["per"], [4.0, np.sqrt(2.0), 0.0], **VALUE_TOL)

    def test_cos_theta_gives_hand_cosines(self, v, b):
        """cos_theta returns (3/5, 1/sqrt(3), -1), and is symmetric in its arguments.

        ON FAILURE: the code is wrong.
        """
        expected = [0.6, 1.0 / np.sqrt(3.0), -1.0]
        np.testing.assert_allclose(v.cos_theta(b), expected, **VALUE_TOL)
        np.testing.assert_allclose(b.cos_theta(v), expected, **VALUE_TOL)

    @pytest.mark.parametrize("method", ["project", "cos_theta"])
    def test_non_vector_argument_raises_naming_its_type(self, v, method):
        """project and cos_theta reject a non-Vector with NotImplementedError naming its type.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(NotImplementedError, match=f"(?i){method} .*ndarray"):
            getattr(v, method)(np.ones((3, 3)))


#####
# Tensors
#####
class TensorTestBase(QuantityTestBase):
    def test_components(self):
        """The par, per and scalar components are the input columns.

        ON FAILURE: the code is wrong.
        """
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


class TestTensorMagnitude:
    """Tensor.magnitude is the thermal-speed scalar sqrt((par^2 + 2 per^2) / 3).

    Thermal speeds combine through the temperatures, T = (T_par + 2 T_per) / 3 with
    T proportional to w^2, so w = sqrt((w_par^2 + 2 w_per^2) / 3) (author decision).
    """

    def test_magnitude_of_hand_tensors(self):
        """magnitude is sqrt(3) for (par=3, per=0), sqrt(6) for (0, 3), w for par=per=w.

        The scalar column is deliberately inconsistent (-1) so a magnitude that reads
        it fails, and par != per in two rows so the trace form (par + 2 per) / 3
        (1, 2) and a swapped weighting (sqrt(3) <-> sqrt(6)) fail.

        ON FAILURE: the code is wrong.
        """
        cols = pd.Index(["par", "per", "scalar"], name="C")
        data = pd.DataFrame(
            [[3.0, 0.0, -1.0], [0.0, 3.0, -1.0], [4.0, 4.0, -1.0]], columns=cols
        )
        expected = [np.sqrt(3.0), np.sqrt(6.0), 4.0]
        # Exact inputs; 1e-12 relative covers the rounding of sqrt and /3 only.
        np.testing.assert_allclose(
            tensor.Tensor(data).magnitude, expected, rtol=1e-12, atol=0
        )

    def test_magnitude_of_plasma_thermal_speed(self):
        """A Plasma-built p1 thermal-speed Tensor's magnitude is its own scalar column.

        Plasma stores w_scalar = sqrt((w_par^2 + 2 w_per^2) / 3), the same thermal-speed
        identity, so magnitude must reproduce it row by row on the package's own
        Tensor layout (flat par/per/scalar columns from Ion.thermal_speed).

        ON FAILURE: the code is wrong.
        """
        p = plasma.Plasma(base.SyntheticData().plasma_data, "p1", "a")
        w = p.p1.w
        # Same formula evaluated in a different order; 1e-12 relative covers rounding.
        np.testing.assert_allclose(
            w.magnitude, w.data.loc[:, "scalar"], rtol=1e-12, atol=0
        )
        pdt.assert_index_equal(w.magnitude.index, w.data.index)


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
        """Two Vectors built from the same alpha velocity are equal.

        ON FAILURE: the code is wrong.
        """
        data = self.data.v.xs("a", axis=1, level="S")
        va0 = vector.Vector(data)
        va1 = vector.Vector(data)
        self.assertEqual(va0, va0)
        self.assertEqual(va0, va1)

    def test_b(self):
        """Two BFields built from the same field are equal.

        ON FAILURE: the code is wrong.
        """
        data = self.data.b.xs("", axis=1, level="S")
        b0 = vector.BField(data)
        b1 = vector.BField(data)
        self.assertEqual(b0, b0)
        self.assertEqual(b0, b1)

    def test_b_v(self):
        """A BField never equals a Vector holding a velocity.

        ON FAILURE: the code is wrong.
        """
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        v = vector.Vector(self.data.v.xs("p2", axis=1, level="S"))
        self.assertNotEqual(b, v)

    def test_b_w(self):
        """A BField never equals a Tensor.

        ON FAILURE: the code is wrong.
        """
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
        """Alpha and p1 velocity Vectors differ.

        ON FAILURE: the code is wrong.
        """
        va = vector.Vector(self.data.v.xs("a", axis=1, level="S"))
        vp1 = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        self.assertNotEqual(va, vp1)

    def test_v_w(self):
        """A Vector never equals a Tensor of the same species.

        ON FAILURE: the code is wrong.
        """
        v = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        w = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        self.assertNotEqual(v, w)

    def test_wp1_wp2(self):
        """p1 and p2 thermal-speed Tensors differ.

        ON FAILURE: the code is wrong.
        """
        wp1 = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        wp2 = tensor.Tensor(self.data.w.xs("p2", axis=1, level="S"))
        self.assertNotEqual(wp1, wp2)
