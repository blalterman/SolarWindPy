#!/usr/bin/env python
"""
Name                :   test_alfvenic_turbulence.py
Common Alias        :
Version             :   0.1.00
Updated             :   20181121
Author              :   B. L. Alterman
e-mail              :   balterma@umich.edu

Description
-----------
-Tests `alfvenic_turbulence.py` modeule.

Bibliography
------------
[1]

Dependencies beyond standard distribution
-----------------------------------------
-

Revision History
----------------
-Started module. (20181121)

Propodes Updates
----------------
-

Notes
-----
-

"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import pdb

import numpy as np
import pandas as pd
import unittest

import pandas.util.testing as pdt

from abc import ABC, abstractproperty

from scipy import constants
from scipy.constants import physical_constants


import test_base as base

from solarwindpy import alfvenic_turbulence as turb

pd.set_option("mode.chained_assignment", "raise")


class AlfvenicTrubulenceTestBase(ABC):
    def setUp(self):
        self.object_testing.set_agg("mean")
        self.object_testing.update_rolling(window=2, min_periods=1, center=True)

    @classmethod
    def set_object_testing(cls):
        species = cls().species.split("+")

        data = (
            pd.concat(
                {s: cls().data.xs(s, axis=1, level="S") for s in species},
                axis=1,
                names=["S"],
            )
            .swaplevel(i="M", j="S", axis=1)
            .swaplevel(i="S", j="C", axis=1)
        )

        tkb = ["x", "y", "z"]
        b = cls().data.xs("b", axis=1, level="M").xs("", axis=1, level="S").loc[:, tkb]

        tkv = pd.IndexSlice["v", ["x", "y", "z"], species]
        v = cls().data.loc[:, tkv]

        # Do the following so `n` only has one level in MultiIndex.
        n = cls().data.loc[:, "n"].loc[:, ""].loc[:, species]

        m = cls().mass_in_mp
        r = n.multiply(m)
        rtot = r.sum(axis=1)

        vcom = (
            v.multiply(r, axis=1, level="S").sum(axis=1, level="C").divide(rtot, axis=0)
        )

        coef = 1e-9 / (np.sqrt(constants.mu_0 * 1e6 * constants.m_p) * 1e3)
        b_ca_units = coef * b.divide(np.sqrt(rtot), axis=0)

        data = pd.concat(
            {
                "v": vcom,
                "b": b_ca_units,
                "r": rtot.to_frame(name="+".join(species)),
                #                           "b_in_ca": b_ca_units
            },
            axis=1,
        ).sort_index(axis=1)

        #         print("",
        #               "<Test>",
        #               "<species>: %s" % species,
        #               "<m>: %s" % m,
        #               "<n>", type(n), n,
        #               "<r>", type(r), r,
        #               "<rtot>", type(rtot), rtot,
        #               "<v>", type(v), v,
        #               "<vcom>", type(vcom), vcom,
        #               "<b>", type(b), b,
        #               "<coeff>: %s" % coef,
        #               "<b_ca_units>", type(b_ca_units), b_ca_units,
        #               "<data>", type(data), data,
        #               sep="\n",
        #               end="\n\n")

        module = turb.AlfvenicTurbulence(
            vcom, b, rtot, "+".join(species), auto_reindex=False
        )
        module.update_rolling(window=2, min_periods=1, center=True)

        cls.object_testing = module
        cls.data = data

    @abstractproperty
    def species(self):
        pass

    @property
    def mass(self):
        trans = {
            "a": "alpha particle",
            "p": "proton",
            "p1": "proton",
            "p2": "proton",
            "e": "electron",
        }
        m = {
            s: physical_constants["%s mass" % trans[s]][0]
            for s in self.species.split("+")
        }
        return pd.Series(m)

    @property
    def mass_in_mp(self):
        trans = {
            "a": physical_constants["alpha particle-proton mass ratio"][0],
            "p": 1,
            "p1": 1,
            "p2": 1,
            "e": physical_constants["electron-proton mass ratio"][0],
        }
        return pd.Series({s: trans[s] for s in self.species.split("+")})

    def test_str(self):
        self.assertEqual("AlfvenicTurbulence", self.object_testing.__class__.__name__)

    def test_species(self):
        self.assertEqual(self.species, self.object_testing.species)

    def test__clean_species_for_setting(self):
        test_fcn = self.object_testing._clean_species_for_setting
        for stest in (
            "a",
            "p1",
            "p2",
            "a,p1",
            "a,p2",
            "p2,p1",
            "p1,p2",
            "a,p1+p2",
            "p2,a+p2",
            "p1,a+p2",
            "a,a+p1+p2",
            "p1,a+p1+p2",
            "p2,a+p1+p2",
        ):
            self.assertEqual(stest, test_fcn(stest))

        with self.assertRaises(ValueError):
            test_fcn("a,p1,p2")
        with self.assertRaises(TypeError):
            test_fcn("a", "p1", "p2")

    def test_auto_reindex(self):

        v = self.data.loc[:, "v"].drop(1, axis=0)
        b = self.data.loc[:, "b"].drop(1, axis=0)
        r = self.data.loc[:, ("r", self.species)].drop(1, axis=0)

        idx_with_skip = pd.Int64Index([0, 2])
        pdt.assert_index_equal(idx_with_skip, v.index)
        pdt.assert_index_equal(idx_with_skip, b.index)
        pdt.assert_index_equal(idx_with_skip, r.index)
        pdt.assert_index_equal(v.index, b.index)
        pdt.assert_index_equal(v.index, r.index)

        coef = 1e9 * (np.sqrt(constants.mu_0 * 1e6 * constants.m_p) * 1e3)
        b_nT = coef * b.multiply(np.sqrt(r), axis=0)

        chk = turb.AlfvenicTurbulence(v, b_nT, r, self.species, auto_reindex=True)
        chk.update_rolling(window=2, min_periods=1)

        idx = pd.RangeIndex(start=v.index.min(), stop=v.index.max() + 1, step=1)
        pdt.assert_index_equal(idx, chk.v.index)
        pdt.assert_index_equal(idx, chk.b.index)
        pdt.assert_index_equal(chk.v.index, chk.b.index)

        nans = pd.DataFrame(
            {
                "x": pd.Series([False, True, False]),
                "y": pd.Series([False, True, False]),
                "z": pd.Series([False, True, False]),
            }
        )
        nans.columns.names = ["C"]

        v = v.reindex(idx, axis=0)
        b = b.reindex(idx, axis=0)

        pdt.assert_frame_equal(nans, chk.v.isna())
        pdt.assert_frame_equal(nans, chk.b.isna())
        pdt.assert_frame_equal(v, chk.v)
        pdt.assert_frame_equal(b, chk.b)

    def test_rolling_kwarg_update(self):
        ot = self.object_testing
        new_window = ot.rolling_window + 1
        new_kwargs = {
            k: not v if isinstance(v, bool) else v + 1
            for k, v in ot.rolling_kwargs.items()
        }

        ot.update_rolling(window=new_window, **new_kwargs)
        self.assertEqual(new_window, ot.rolling_window)
        self.assertDictEqual(new_kwargs, ot.rolling_kwargs)

    def test_rolling_agg_fcns(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]

        agg = tuple(sorted(["mean", "std"]))
        zp = v.add(b, axis=1)
        zm = v.subtract(b, axis=1)

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        ep = 0.5 * zp.pow(2).sum(axis=1).rolling(window, **kwargs).agg(agg)
        em = 0.5 * zm.pow(2).sum(axis=1).rolling(window, **kwargs).agg(agg)

        ot.set_agg(agg)
        self.assertEqual(agg, ot.agg)
        pdt.assert_frame_equal(ep, ot.ep)
        pdt.assert_frame_equal(em, ot.em)

    def test_bfield(self):
        # Test in Alfven units
        b = self.data.loc[:, "b"]
        pdt.assert_frame_equal(b, self.object_testing.bfield)
        pdt.assert_frame_equal(self.object_testing.bfield, self.object_testing.b)

    def test_velocity(self):
        v = self.data.loc[:, "v"]
        pdt.assert_frame_equal(v, self.object_testing.velocity)
        pdt.assert_frame_equal(self.object_testing.v, self.object_testing.velocity)

    def test_z_plus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)
        pdt.assert_frame_equal(zp, self.object_testing.z_plus)
        pdt.assert_frame_equal(self.object_testing.zp, self.object_testing.z_plus)

    def test_z_minus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zm = v.subtract(b, axis=1)
        pdt.assert_frame_equal(zm, self.object_testing.z_minus)
        pdt.assert_frame_equal(self.object_testing.zm, self.object_testing.z_minus)

    def test_e_plus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        ep = 0.5 * zp.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])

        pdt.assert_frame_equal(ep, ot.e_plus)
        pdt.assert_frame_equal(ot.ep, ot.e_plus)

    def test_e_minus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zm = v.subtract(b, axis=1)

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        em = 0.5 * zm.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])

        pdt.assert_frame_equal(em, ot.e_minus)
        pdt.assert_frame_equal(ot.em, ot.e_minus)

    def test_kinetic_energy(self):
        v = self.data.loc[:, "v"]

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        ev = 0.5 * v.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])

        pdt.assert_frame_equal(ev, ot.kinetic_energy)
        pdt.assert_frame_equal(ot.kinetic_energy, ot.ev)

    def test_magnetic_energy(self):
        b = self.data.loc[:, "b"]

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        eb = 0.5 * b.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])

        pdt.assert_frame_equal(eb, ot.magnetic_energy)
        pdt.assert_frame_equal(ot.magnetic_energy, ot.eb)

    def test_total_energy(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        tk = ["v", "b"]
        etot = 0.5 * self.data.loc[:, tk].pow(2).sum(axis=1).rolling(
            window, **kwargs
        ).agg(["mean"])

        pdt.assert_frame_equal(etot, ot.total_energy)
        pdt.assert_frame_equal(ot.total_energy, ot.etot)

    def test_residual_energy(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        eres = ev.subtract(eb, axis=0)

        pdt.assert_frame_equal(eres, ot.residual_energy)
        pdt.assert_frame_equal(ot.residual_energy, ot.eres)

    def test_normalized_residual_energy(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        etot = ev.add(eb, axis=0)
        eres = ev.subtract(eb, axis=0)
        eres_norm = eres.divide(etot, axis=0)

        pdt.assert_frame_equal(eres_norm, ot.normalized_residual_energy)
        pdt.assert_frame_equal(ot.normalized_residual_energy, ot.eres_norm)

    def test_cross_helicity(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]

        # -1 normalization by references in `alfvenic_turbulence.py`.
        ch = -0.5 * v.multiply(b, axis=1).sum(axis=1).rolling(window, **kwargs).agg(
            ["mean"]
        )

        pdt.assert_frame_equal(ch, ot.cross_helicity)

    def test_normalized_cross_helicity(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]

        # -1 normalization by references in `alfvenic_turbulence.py`.
        ch = -0.5 * v.multiply(b, axis=1).sum(axis=1).rolling(window, **kwargs).agg(
            ["mean"]
        )
        ev = 0.5 * v.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        eb = 0.5 * b.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        etot = ev.add(eb, axis=1)
        normalized_cross_helicity = 2.0 * ch.divide(etot, axis=0)

        pdt.assert_frame_equal(normalized_cross_helicity, ot.normalized_cross_helicity)
        pdt.assert_frame_equal(ot.sigma_c, ot.normalized_cross_helicity)

    def test_alfven_ratio(self):
        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs

        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        rA = ev.divide(eb, axis=1)

        pdt.assert_frame_equal(rA, ot.alfven_ratio)
        pdt.assert_frame_equal(ot.alfven_ratio, ot.rA)

    def test_elsasser_ratio(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)
        zm = v.subtract(b, axis=1)

        ot = self.object_testing
        window = ot.rolling_window
        kwargs = ot.rolling_kwargs
        ep = 0.5 * zp.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        em = 0.5 * zm.pow(2).sum(axis=1).rolling(window, **kwargs).agg(["mean"])
        rE = em.divide(ep, axis=1)

        pdt.assert_frame_equal(rE, ot.elsasser_ratio)
        pdt.assert_frame_equal(ot.elsasser_ratio, ot.rE)

    def test_eq(self):
        print_inline_debug = False
        ot = self.object_testing
        # ID should be equal.
        self.assertEqual(ot, ot)
        # Data and type should be equal.

        v = self.data.loc[:, "v"]
        r = self.data.loc[:, ("r", self.species)]
        b = self.data.loc[:, "b"]
        coef = 1e9 * (np.sqrt(constants.mu_0 * 1e6 * constants.m_p) * 1e3)
        b_nT = coef * b.multiply(np.sqrt(r), axis=0)

        new_object = ot.__class__(v, b_nT, r, ot.species, auto_reindex=True)

        if print_inline_debug:
            print(
                "<Test>",
                "<object_testing>",
                type(ot),
                ot,
                id(ot),
                ot.species,
                ot.data,
                "<new_object>",
                type(new_object),
                id(new_object),
                new_object,
                new_object.species,
                new_object.data,
                "",
                sep="\n",
                end="\n\n",
            )

        self.assertEqual(ot.species, new_object.species)
        pdt.assert_frame_equal(ot.data, new_object.data)
        try:
            self.assertEqual(ot, new_object)
        except AssertionError as e0:
            try:
                pdt.assert_frame_equal(ot.data.round(15), new_object.data.round(15))
            except AssertionError as e1:  # noqa: F841
                raise (e0)


#     def test_neq(self):
#         object_testing = self.object_testing
#         # Data isn't equal
#         self.assertNotEqual(object_testing,
#                             object_testing.__class__(object_testing.data * 4))
#          # Type isn't equal
#         for other in ([], tuple(), np.array([]), pd.Series(), pd.DataFrame()):
#             self.assertNotEqual(object_testing, other)

#####
# Tests
#####
# @unittest.skip
class TestPlasmaAlpha(base.AlphaTest, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceP1(base.P1Test, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceP2(base.P2Test, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceAlphaP1(
    base.AlphaP1Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceAlphaP2(
    base.AlphaP2Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceP1P2(
    base.P1P2Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


# @unittest.skip
class TestAlfvenicTrubulenceAlphaP1P2(
    base.AlphaP1P2Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


if __name__ == "__main__":
    import sys

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    #     sys.setrecursionlimit(sys.getrecursionlimit() // 10)
    sys.setrecursionlimit(100)

    try:
        run_this_test = "TestAlfvenicTrubulenceAlphaP1P2"
        run_this_test = None
        unittest.main(verbosity=2, defaultTest=run_this_test)

    except (  # noqa: F841
        AssertionError,
        AttributeError,
        ValueError,
        TypeError,
        IndexError,
    ) as e:
        import sys
        import traceback as tb

        exc_info = sys.exc_info()
        tb.print_exception(*exc_info)
        pdb.post_mortem(exc_info[-1])
