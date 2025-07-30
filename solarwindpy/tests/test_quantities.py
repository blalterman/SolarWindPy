#!/usr/bin/env python
"""
Tests for Vector and Tensor objects.
"""
import numpy as np
import pytest
import pandas as pd
import pandas.testing as pdt

from abc import ABC
from scipy import constants

# import test_base as base
from solarwindpy.tests import test_base as base

from solarwindpy import vector
from solarwindpy import tensor

pd.set_option("mode.chained_assignment", "raise")


@pytest.fixture(scope="module")
def quantity_subclass_data():
    data = base.TestData().plasma_data
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
    return data


@pytest.fixture(scope="class")
def species(request):
    return request.param


@pytest.fixture(scope="class")
def velocity_setup(request, species):
    data = base.TestData().plasma_data.sort_index(axis=1)
    vdata = data.v.xs(species, axis=1, level="S")
    request.cls.object_testing = vector.Vector(vdata)
    request.cls.data = vdata


@pytest.fixture(scope="class")
def thermal_setup(request, species):
    data = base.TestData().plasma_data.sort_index(axis=1)
    tdata = data.w.xs(species, axis=1, level="S")
    coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
    scalar = tdata.pow(2).multiply(coeff, axis=1, level="C").sum(axis=1).pipe(np.sqrt)
    scalar.name = "scalar"
    tdata = pd.concat([tdata, scalar], axis=1).sort_index(axis=1)
    request.cls.object_testing = tensor.Tensor(tdata)
    request.cls.data = tdata


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
        assert object_testing == object_testing
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

        assert object_testing == new_object

    def test_neq(self):
        object_testing = self.object_testing
        # Data isn't equal

        assert object_testing != object_testing.__class__(object_testing.data * 4)
        # Type isn't equal
        for other in (
            [],
            tuple(),
            np.array([]),
            pd.Series(dtype=np.float64),
            pd.DataFrame(dtype=np.float64),
        ):
            assert object_testing != other

    def test_empty_data_catch(self):
        with pytest.raises(
            ValueError, match="You can't set an object with empty data."
        ):
            self.object_testing.__class__(pd.DataFrame())


#####
# Vectors
#####
class VectorTestBase(QuantityTestBase):
    def test_components(self):
        # print("test_components")
        # print(self.data.iloc[:, :7], flush=True)

        v = self.data
        ot = self.object_testing.data
        # print(v, file=sys.stdout)
        pdt.assert_series_equal(v.x, ot.x)
        pdt.assert_series_equal(v.y, ot.y)
        pdt.assert_series_equal(v.z, ot.z)

    def test_mag(self):
        # print("test_mag")
        # print(self.data.iloc[:, :7], flush=True)
        x = self.data.x
        y = self.data.y
        z = self.data.z
        # print(v, file=sys.stdout)
        mag = np.sqrt(x.pow(2) + y.pow(2) + z.pow(2))
        # mag = self.data.loc[:, ["x", "y", "z"]].pow(2).sum(axis=1).pipe(np.sqrt)
        mag.name = "mag"
        # print("", self.data, mag, self.object_testing.mag, sep="\n")
        pdt.assert_series_equal(mag, self.object_testing.mag)
        pdt.assert_series_equal(mag, self.object_testing.magnitude)
        pdt.assert_series_equal(self.object_testing.mag, self.object_testing.magnitude)

    def test_rho(self):
        # print("test_rho")
        x = self.data.x
        y = self.data.y
        rho = np.sqrt(x.pow(2) + y.pow(2))
        rho.name = "rho"
        pdt.assert_series_equal(rho, self.object_testing.rho)

    def test_colat(self):
        # print("test_colat")
        x = self.data.x
        y = self.data.y
        z = self.data.z
        colat = np.arctan2(z, np.sqrt(x.pow(2) + y.pow(2)))
        colat = np.rad2deg(colat)
        colat.name = "colat"
        pdt.assert_series_equal(colat, self.object_testing.colat)

    def test_longitude(self):
        # print("test_longitude")
        x = self.data.x
        y = self.data.y
        lon = np.arctan2(y, x)
        lon = np.rad2deg(lon)
        lon.name = "longitude"
        pdt.assert_series_equal(lon, self.object_testing.lon)
        pdt.assert_series_equal(lon, self.object_testing.longitude)
        pdt.assert_series_equal(self.object_testing.lon, self.object_testing.longitude)

    def test_r(self):
        # print("test_r")
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
        assert uv == self.object_testing.unit_vector
        assert uv == self.object_testing.uv
        assert self.object_testing.unit_vector == self.object_testing.uv

    def test_project(self):
        b = (
            base.TestData()
            .plasma_data.xs("b", axis=1, level="M")
            .xs("", axis=1, level="S")
            .loc[:, ["x", "y", "z"]]
        )
        #         b.setUpClass()
        #         b = (
        #             b.data.b.loc[:, ["x", "y", "z"]]
        #             .xs("", axis=1, level="S")
        #             .xs("", axis=1, level="N")
        #         )
        bmag = b.pow(2).sum(axis=1).pipe(np.sqrt)
        buv = b.divide(bmag, axis=0)

        v = self.data.loc[:, ["x", "y", "z"]]
        vmag = v.pow(2).sum(axis=1).pipe(np.sqrt)
        #         vuv = v.divide(vmag, axis=0)

        par = v.multiply(buv, axis=1).sum(axis=1)
        per = (
            v.subtract(buv.multiply(par, axis=0), axis=1)
            .pow(2)
            .sum(axis=1)
            .pipe(np.sqrt)
        )
        projected = pd.concat([par, per], axis=1, keys=["par", "per"], sort=True)

        # print("",
        #       "<Test>",
        #       "<buv>", type(buv), buv,
        #       "<v>", type(v), v,
        #       "<vmag>", type(vmag), vmag,
        #       "<vuv>", type(vuv), vuv,
        #       "<projected>", type(projected), projected,
        #       "",
        #       sep="\n")

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
        with pytest.raises(NotImplementedError, match=msg):
            self.object_testing.project(b.data)

    def test_cos_theta(self):
        #         b = base.TestData()
        #         b.setUpClass()
        #         b = (
        #             b.data.b.loc[:, ["x", "y", "z"]]
        #             .xs("", axis=1, level="S")
        #             .xs("", axis=1, level="N")
        #         )
        b = (
            base.TestData()
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

        # print("",
        #       "<Test>",
        #       "<buv>", type(buv), buv,
        #       "<v>", type(v), v,
        #       "<vmag>", type(vmag), vmag,
        #       "<vuv>", type(vuv), vuv,
        #       "<cos_theta>", type(cos_theta), cos_theta,
        #       "",
        #       sep="\n")

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
        with pytest.raises(NotImplementedError, match=msg):
            self.object_testing.project(b.data)


# class TestGSE(VectorTestBase, base.SWEData):
#     @classmethod
#     def set_object_testing(cls):
#         # print("TestGSE.set_object_testing", flush=True)
#         data = cls.data.gse.xs("", axis=1, level="S")
#         gse = vector.Vector(data)
#         cls.object_testing = gse
#         cls.data = data
#         # print("Done with TestGSE.set_object_testing", flush=True)


class TestBField(VectorTestBase, base.SWEData):
    @classmethod
    def set_object_testing(cls):
        # print("BField.set_object_testing", flush=True)
        data = cls.data.b.xs("", axis=1, level="S")
        # b = vector.Vector(data)
        b = vector.BField(data)
        cls.object_testing = b
        cls.data = data
        # print("Done with BField.set_object_testing", flush=True)

    def test_pressure(self):
        print_inline_debug = False
        bsq = self.data.loc[:, ["x", "y", "z"]].pow(2.0).sum(axis=1)
        const = 1e-18 / (2.0 * constants.mu_0 * 1e-12)  # ([b]**2 / 2.0 * \mu_0 * [p])
        pb = bsq * const
        pb.name = "pb"

        # ot = self.object_testing
        # pdb.set_trace()

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
                end="\n\n"
            )

        pdt.assert_series_equal(pb, self.object_testing.pressure)
        pdt.assert_series_equal(pb, self.object_testing.pb)
        pdt.assert_series_equal(self.object_testing.pressure, self.object_testing.pb)


class VelocityTestBase(VectorTestBase):
    pass


@pytest.mark.parametrize("species", ["a", "p1", "p2"], indirect=True)
@pytest.mark.usefixtures("velocity_setup")
class TestVelocity(VelocityTestBase):
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
    pass


@pytest.mark.parametrize("species", ["a", "p1", "p2"], indirect=True)
@pytest.mark.usefixtures("thermal_setup")
class TestThermalSpeed(ThermalSpeedTestBase):
    pass


# @unittest.skip
def test_quantity_subclass_v(quantity_subclass_data):
    data = quantity_subclass_data.v.xs("a", axis=1, level="S")
    va0 = vector.Vector(data)
    va1 = vector.Vector(data)
    assert va0 == va0
    assert va0 == va1


def test_quantity_subclass_b(quantity_subclass_data):
    data = quantity_subclass_data.b.xs("", axis=1, level="S")
    b0 = vector.BField(data)
    b1 = vector.BField(data)
    assert b0 == b0
    assert b0 == b1


def test_quantity_subclass_b_v(quantity_subclass_data):
    b = vector.BField(quantity_subclass_data.b.xs("", axis=1, level="S"))
    v = vector.Vector(quantity_subclass_data.v.xs("p2", axis=1, level="S"))
    assert b != v


def test_quantity_subclass_b_w(quantity_subclass_data):
    b = vector.BField(quantity_subclass_data.b.xs("", axis=1, level="S"))
    w = tensor.Tensor(quantity_subclass_data.w.xs("a", axis=1, level="S"))
    assert b != w


@pytest.mark.skip(reason="Need to update with new `spacecraft` position vectors")
def test_quantity_subclass_gse(quantity_subclass_data):
    data = quantity_subclass_data.gse.xs("", axis=1, level="S")
    gse0 = vector.Vector(data)
    gse1 = vector.Vector(data)
    assert gse0 == gse0
    assert gse0 == gse1


@pytest.mark.skip(reason="Need to update with new `spacecraft` position vectors")
def test_quantity_subclass_b_gse(quantity_subclass_data):
    b = vector.BField(quantity_subclass_data.b.xs("", axis=1, level="S"))
    gse = vector.Vector(quantity_subclass_data.gse.xs("", axis=1, level="S"))
    assert b != gse


@pytest.mark.skip(reason="Need to update with new `spacecraft` position vectors")
def test_quantity_subclass_gse_v(quantity_subclass_data):
    gse = vector.Vector(quantity_subclass_data.gse.xs("", axis=1, level="S"))
    v = vector.Vector(quantity_subclass_data.v.xs("p2", axis=1, level="S"))
    assert gse != v


@pytest.mark.skip(reason="Need to update with new `spacecraft` position vectors")
def test_quantity_subclass_gse_w(quantity_subclass_data):
    gse = vector.Vector(quantity_subclass_data.gse.xs("", axis=1, level="S"))
    w = tensor.Tensor(quantity_subclass_data.w.xs("a", axis=1, level="S"))
    assert gse != w


def test_quantity_subclass_va_vp1(quantity_subclass_data):
    va = vector.Vector(quantity_subclass_data.v.xs("a", axis=1, level="S"))
    vp1 = vector.Vector(quantity_subclass_data.v.xs("p1", axis=1, level="S"))
    assert va != vp1


def test_quantity_subclass_v_w(quantity_subclass_data):
    v = vector.Vector(quantity_subclass_data.v.xs("p1", axis=1, level="S"))
    w = tensor.Tensor(quantity_subclass_data.w.xs("p1", axis=1, level="S"))
    assert v != w


def test_quantity_subclass_wp1_wp2(quantity_subclass_data):
    wp1 = tensor.Tensor(quantity_subclass_data.w.xs("p1", axis=1, level="S"))
    wp2 = tensor.Tensor(quantity_subclass_data.w.xs("p2", axis=1, level="S"))
    assert wp1 != wp2
