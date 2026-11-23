"""Tests for :mod:`solarwindpy.core.vector`: ``Vector`` and ``BField``."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from abc import abstractproperty
from scipy import constants

from . import _fixtures as fixtures

from solarwindpy.core import vector
from tests.tolerances import exact

# Hand inputs are of order 1, so a component that cancels to 0 carries rounding of
# order 1e-16 times this scale.
UNIT_SCALE = 1.0


def _hand_vector(rows, cls=vector.Vector):
    """Build a Vector from hand-chosen (x, y, z) rows on a DatetimeIndex."""
    index = pd.date_range("2000-01-01", periods=len(rows), freq="min")
    return cls(pd.DataFrame(rows, index=index, columns=["x", "y", "z"], dtype=float))


#####
# Vectors
#####
class VectorTestBase(fixtures.QuantityTestBase):
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
        lat.name = "lat"
        colat = np.rad2deg(np.arctan2(rho, z))
        colat.name = "colat"
        pdt.assert_series_equal(lat, self.object_testing.lat)
        pdt.assert_series_equal(colat, self.object_testing.colat)
        assert (
            self.object_testing.lat + self.object_testing.colat
        ).to_numpy() == exact(90.0)

    def test_longitude(self):
        """lon and longitude are arctan2(y, x) in degrees.

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        lon = np.arctan2(y, x)
        lon = np.rad2deg(lon)
        lon.name = "lon"
        pdt.assert_series_equal(lon, self.object_testing.lon)

    def test_r(self):
        """mag is the magnitude sqrt(x^2 + y^2 + z^2), named "mag".

        ON FAILURE: the code is wrong.
        """
        x = self.data.x
        y = self.data.y
        z = self.data.z
        r = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        r.name = "mag"
        pdt.assert_series_equal(r, self.object_testing.mag)
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
        pdt.assert_frame_equal(uv.data, self.object_testing.uv.data)
        self.assertEqual(uv, self.object_testing.uv)

    def test_project(self):
        """project splits the vector into components parallel and perpendicular to B.

        Re-derives par = v . b_hat and per = |v - par b_hat|; projecting a vector onto
        itself gives par = |v| and per = 0. The hand cases live in
        ``TestVectorProjectionHandCases``.

        ON FAILURE: the code is wrong.
        """
        b = (
            fixtures.SyntheticData()
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
            fixtures.SyntheticData()
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
        pdt.assert_series_equal(
            cos_theta.rename("cos_theta"), self.object_testing.cos_theta(b)
        )

        v = vector.Vector(v)
        vuv = vector.Vector(vuv)
        par = pd.Series(1.0, index=vmag.index, name="cos_theta")
        pdt.assert_series_equal(par, self.object_testing.cos_theta(v))
        pdt.assert_series_equal(par, self.object_testing.cos_theta(vuv))

        with self.assertRaisesRegex(NotImplementedError, "DataFrame"):
            self.object_testing.cos_theta(b.data)


class TestBField(VectorTestBase, fixtures.SWEData):
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


class TestVelocityAlpha(fixtures.AlphaTest, VelocityTestBase, fixtures.SWEData):
    pass


class TestVelocityP1(fixtures.P1Test, VelocityTestBase, fixtures.SWEData):
    pass


class TestVelocityP2(fixtures.P2Test, VelocityTestBase, fixtures.SWEData):
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
        assert np.asarray(v.lat) == exact(expected, scale=UNIT_SCALE)

    def test_colatitude_of_hand_directions(self, v):
        """colatitude and colat are 0 on +z, 90 on +x, 180 on -z, 45 and 120 off-axis.

        ON FAILURE: the code is wrong.
        """
        expected = [c[2] for c in self.CASES]
        assert np.asarray(v.colat) == exact(expected, scale=UNIT_SCALE)


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
        assert out["par"].to_numpy() == exact([3.0, 1.0, -2.0], scale=UNIT_SCALE)
        assert out["per"].to_numpy() == exact(
            [4.0, np.sqrt(2.0), 0.0], scale=UNIT_SCALE
        )

    def test_cos_theta_gives_hand_cosines(self, v, b):
        """cos_theta returns (3/5, 1/sqrt(3), -1), and is symmetric in its arguments.

        ON FAILURE: the code is wrong.
        """
        expected = [0.6, 1.0 / np.sqrt(3.0), -1.0]
        assert np.asarray(v.cos_theta(b)) == exact(expected, scale=UNIT_SCALE)
        assert np.asarray(b.cos_theta(v)) == exact(expected, scale=UNIT_SCALE)

    def test_rows_in_only_one_vector_are_nan(self):
        """project and cos_theta are NaN on rows present in only one of the two vectors.

        v covers minutes 0-2 and b covers minutes 1-3, so the result spans minutes 0-3:
        minute 0 has no b and minute 3 has no v, and both must be NaN rather than 0
        (0 would claim a perpendicular field). Minutes 1 and 2 reuse the hand rows
        (1, 1, 1) on (0, 0, 5) and (0, -2, 0) on (0, 3, 0).

        ON FAILURE: the code is wrong.
        """
        minutes = pd.date_range("2000-01-01", periods=4, freq="min")
        v = vector.Vector(
            pd.DataFrame(self.V, index=minutes[:3], columns=["x", "y", "z"])
        )
        b = vector.BField(
            pd.DataFrame(
                [self.B[1], self.B[2], self.B[0]],
                index=minutes[1:],
                columns=["x", "y", "z"],
            )
        )
        nan = np.nan
        out = v.project(b)
        pdt.assert_index_equal(out.index, minutes)
        # nan_ok matches NaN only to NaN, so a 0 fails.
        assert out["par"].to_numpy() == exact(
            [nan, 1.0, -2.0, nan], scale=UNIT_SCALE, nan_ok=True
        )
        assert out["per"].to_numpy() == exact(
            [nan, np.sqrt(2.0), 0.0, nan], scale=UNIT_SCALE, nan_ok=True
        )
        cos = v.cos_theta(b)
        pdt.assert_index_equal(cos.index, minutes)
        assert cos.to_numpy() == exact(
            [nan, 1.0 / np.sqrt(3.0), -1.0, nan], scale=UNIT_SCALE, nan_ok=True
        )

    @pytest.mark.parametrize("method", ["project", "cos_theta"])
    def test_non_vector_argument_raises_naming_its_type(self, v, method):
        """project and cos_theta reject a non-Vector with NotImplementedError naming its type.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(NotImplementedError, match=f"(?i){method} .*ndarray"):
            getattr(v, method)(np.ones((3, 3)))
