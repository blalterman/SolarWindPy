#!/usr/bin/env python
"""Tests for the :class:`Ion` object."""
import numpy as np
import pandas as pd

# import sys
# import itertools

# from numbers import Number
# from pandas import MultiIndex as MI

# import numpy.testing as npt
import pandas.testing as pdt

from abc import ABC, abstractproperty

# from abc import abstractmethod, abstractstaticmethod, abstractclassmethod
# from unittest import TestCase

from scipy import constants
from scipy.constants import physical_constants

# try:
#     import test_base as base
# except ImportError:
#     from . import test_base as base
from . import test_base as base

from solarwindpy import vector
from solarwindpy import tensor
from solarwindpy import ions

pd.set_option("mode.chained_assignment", "raise")


class IonTestBase(ABC):
    @classmethod
    def set_object_testing(cls):
        # print(cls.__class__, "set_object_testing", flush=True)
        # print("Data", cls.data, sep="\n")
        data = cls.data.xs(cls().species, axis=1, level="S")

        w = data.w
        coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
        kwargs = dict(axis=1, level="C")
        scalar = w.pow(2).multiply(coeff, **kwargs).sum(axis=1).pipe(np.sqrt)
        scalar.name = ("w", "scalar")
        data = pd.concat([data, scalar], axis=1, sort=True)
        data.columns = pd.MultiIndex.from_tuples(data.columns, names=["M", "C"])

        ion = ions.Ion(data, cls().species)
        cls.object_testing = ion
        cls.data = data
        # print("Done with", cls.__class__, flush=True)

    @abstractproperty
    def species(self):
        pass

    @classmethod
    def ion(cls):
        return cls._ion

    @property
    def mass(self):
        trans = {
            "a": "alpha particle",
            "p": "proton",
            "p1": "proton",
            "p2": "proton",
            "e": "electron",
        }
        m = physical_constants["%s mass" % trans[self.species]][0]
        return m

    @property
    def mass_in_mp(self):
        trans = {
            "a": physical_constants["alpha particle-proton mass ratio"][0],
            "p": 1,
            "p1": 1,
            "p2": 1,
            "e": physical_constants["electron-proton mass ratio"][0],
        }
        return trans[self.species]

    def test_species(self):
        self.assertEqual(self.species, self.object_testing.species)

    def test_n(self):
        n = self.data.loc[:, ("n", "")]
        if not isinstance(n, pd.Series):
            assert n.shape[1] == 1
            n = n.iloc[:, 0]
        n.name = "n"
        ot = self.object_testing
        pdt.assert_series_equal(n, ot.n)
        pdt.assert_series_equal(n, ot.number_density)
        pdt.assert_series_equal(ot.number_density, ot.n)

    def test_mass_density(self):
        mmp = self.mass_in_mp
        rho = self.data.loc[:, pd.IndexSlice["n", ""]] * mmp
        rho.name = self.species
        if not isinstance(rho, pd.Series):
            assert rho.shape[1] == 1
            rho = rho.iloc[:, 0]
        rho.name = "rho"
        ot = self.object_testing
        pdt.assert_series_equal(ot.rho, ot.mass_density)
        pdt.assert_series_equal(rho, ot.rho)
        pdt.assert_series_equal(rho, ot.mass_density)

    def test_v(self):
        v = vector.Vector(self.data.v)
        ot = self.object_testing
        self.assertEqual(v, ot.velocity)
        self.assertEqual(v, ot.v)
        self.assertEqual(ot.velocity, ot.v)

    def test_w(self):
        w = tensor.Tensor(self.data.w)
        ot = self.object_testing
        self.assertEqual(w, ot.thermal_speed)
        self.assertEqual(w, ot.w)
        self.assertEqual(ot.w, ot.thermal_speed)

    def test_anisotropy(self):
        w = self.data.w
        ani = (w.per / w.par).pow(2)
        ani.name = "RT"
        ot = self.object_testing
        pdt.assert_series_equal(ani, ot.anisotropy)

    def test_pth(self):
        # pth = nkT = 0.5 * n * m * w^2
        n = self.data.n * 1e6
        w = self.data.w * 1e3
        m = self.mass
        p = w.pow(2).multiply(0.5 * n * m, axis=0) / 1e-12
        pdt.assert_frame_equal(p, self.object_testing.pth)

    def test_temperature(self):
        # 0.5 mw^2 = kT
        # T = 0.5 mw^2 / k
        m = self.mass
        w = self.data.w * 1e3
        kb = physical_constants["Boltzmann constant"][0]
        t = (0.5 * m / kb) * w.pow(2) / 1e5
        pdt.assert_frame_equal(t, self.object_testing.temperature)

    def test_specific_entropy(self):
        rho = self.mass * self.data.n * 1e6
        w = self.data.w.xs("scalar", axis=1) * 1e3
        pth = w.pow(2).multiply(0.5 * rho, axis=0)

        #         ln_pth = np.log(pth)
        #         ln_rho = np.log(rho)
        #
        gamma = 5.0 / 3.0
        units = 1e4 / constants.e
        S = pth.multiply(rho.pow(-gamma)) / units
        S.name = "S"
        #         print(
        #             "<specific_entropy>",
        #             "<s>",
        #             self.species,
        #             "<test>",
        #             "<ln_pth>",
        #             ln_pth,
        #             "<ln_rho>",
        #             ln_rho,
        #             "<lnS>",
        #             lnS,
        #             sep="\n",
        #         )

        ot = self.object_testing
        pdt.assert_series_equal(S, ot.specific_entropy)
        pdt.assert_series_equal(S, ot.S)
        pdt.assert_series_equal(ot.S, ot.specific_entropy)

    def test_cs(self):
        m = self.mass
        n = self.data.n * 1e6
        w = self.data.w * 1e3
        rho = n * m
        pth = w.pow(2).multiply(0.5 * rho, axis=0)
        gamma = 5.0 / 3.0
        cs = (pth.divide(rho, axis=0) * gamma).pow(0.5) / 1e3
        cs.name = "cs"
        pdt.assert_frame_equal(cs, self.object_testing.cs)


class TestIonA(base.AlphaTest, IonTestBase, base.SWEData):
    pass


class TestIonP1(base.P1Test, IonTestBase, base.SWEData):
    pass


class TestIonP2(base.P2Test, IonTestBase, base.SWEData):
    pass


class TestIonSpecificsOptions(base.TestData):
    @classmethod
    def setUpClass(cls):
        r"""Override `setUpClass` because this set of tests doesn't rely on
        `object_testing`."""
        # print("SWEData.setUpClass", flush=True)
        super(TestIonSpecificsOptions, cls).setUpClass()
        # print(cls.data.iloc[:, :7])
        # print(cls.data.columns.values)
        cls.data = cls.data.xs("", axis=1, level="N")

    #     def test_init_with_species(self):
    #         species = "a"
    #         data = self.data.xs(species, axis=1, level="S", drop_level=False)
    #         ion = ions.Ion(data, species)
    #         self.assertIsInstance(ion, ions.Ion)
    #         self.assertEqual(species, ion.species)
    #         pdt.assert_frame_equal(data, ion.data)
    #
    #         species = "p1"
    #         data = self.data.xs(species, axis=1, level="S", drop_level=False)
    #         ion = ions.Ion(data, species)
    #         self.assertIsInstance(ion, ions.Ion)
    #         self.assertEqual(species, ion.species)
    #         pdt.assert_frame_equal(data, ion.data)
    #
    #         species = "p1"
    #         data = self.data.xs(species, axis=1, level="S", drop_level=False)
    #         ion = ions.Ion(data, species)
    #         self.assertIsInstance(ion, ions.Ion)
    #         self.assertEqual(species, ion.species)
    #         pdt.assert_frame_equal(data, ion.data)

    def test_init_with_species(self):
        species = "a"
        data = self.data.xs(species, axis=1, level="S")
        ion = ions.Ion(data, species)
        self.assertIsInstance(ion, ions.Ion)
        self.assertEqual(species, ion.species)
        pdt.assert_frame_equal(data, ion.data)

        species = "p1"
        data = self.data.xs(species, axis=1, level="S")
        ion = ions.Ion(data, species)
        self.assertIsInstance(ion, ions.Ion)
        self.assertEqual(species, ion.species)
        pdt.assert_frame_equal(data, ion.data)

        species = "p2"
        data = self.data.xs(species, axis=1, level="S")
        ion = ions.Ion(data, species)
        self.assertIsInstance(ion, ions.Ion)
        self.assertEqual(species, ion.species)
        pdt.assert_frame_equal(data, ion.data)

    def test_init_version_comparison(self):
        species = "a"
        data_with_species = self.data.xs(species, axis=1, level="S", drop_level=False)
        data_without_species = self.data.xs(species, axis=1, level="S")
        ion_with_species = ions.Ion(data_with_species, species)
        ion_without_species = ions.Ion(data_without_species, species)
        self.assertEqual(ion_with_species, ion_without_species)

        species = "p1"
        data_with_species = self.data.xs(species, axis=1, level="S", drop_level=False)
        data_without_species = self.data.xs(species, axis=1, level="S")
        ion_with_species = ions.Ion(data_with_species, species)
        ion_without_species = ions.Ion(data_without_species, species)
        self.assertEqual(ion_with_species, ion_without_species)

        species = "p2"
        data_with_species = self.data.xs(species, axis=1, level="S", drop_level=False)
        data_without_species = self.data.xs(species, axis=1, level="S")
        ion_with_species = ions.Ion(data_with_species, species)
        ion_without_species = ions.Ion(data_without_species, species)
        self.assertEqual(ion_with_species, ion_without_species)

    def test_eq(self):
        s0 = "a"
        s1 = "a"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertEqual(i0, i1)

        s0 = "p1"
        s1 = "p1"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertEqual(i0, i1)

        s0 = "p2"
        s1 = "p2"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertEqual(i0, i1)

        s0 = "a"
        s1 = "p1"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertNotEqual(i0, i1)

        s0 = "p1"
        s1 = "a"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertNotEqual(i0, i1)

        s0 = "a"
        s1 = "p2"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertNotEqual(i0, i1)

        s0 = "p2"
        s1 = "p1"
        i0 = ions.Ion(self.data, s0)
        i1 = ions.Ion(self.data, s1)
        self.assertNotEqual(i0, i1)
