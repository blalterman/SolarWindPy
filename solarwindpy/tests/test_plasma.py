#!/usr/bin/env python
r"""Test :py:class:`~solarwindpy.core.plasma.Plasma`.

Includes tests for making contained instances of :py:class:`~solarwindpy.core.vector.Vector`
and :py:class:`~solarwindpy.core.tensor.Tensor`.


Propodes Updates
----------------
-Different test cases to catch longitudinal diffusion rates
 that don't equal 1. (Priority: High)
"""
import pdb

# import re as re
import numpy as np
import pandas as pd
import unittest
import sys
import itertools
import pandas.util.testing as pdt

from abc import ABC, abstractproperty, abstractmethod

from scipy import constants
from scipy.constants import physical_constants

# import test_base as base
from solarwindpy.tests import test_base as base

from solarwindpy import vector
from solarwindpy import ions
from solarwindpy import plasma
from solarwindpy import spacecraft
from solarwindpy import alfvenic_turbulence

pd.set_option("mode.chained_assignment", "raise")


class PlasmaTestBase(ABC):
    @classmethod
    def set_object_testing(cls):
        # print(cls.__class__, "set_object_testing", flush=True)
        # print("Data", cls.data, sep="\n")
        data = cls.data
        plas = plasma.Plasma(data, *cls().species.split("+"))

        par = data.w.par.pow(2)
        per = data.w.per.pow(2)
        scalar = ((2.0 * per) + par).multiply(1.0 / 3.0).pipe(np.sqrt)
        cols = scalar.columns.to_series().apply(lambda x: ("w", "scalar", x))
        scalar.columns = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
        data = pd.concat([data, scalar], axis=1).sort_index(axis=1)

        cls.object_testing = plas
        cls.data = data
        # print("Done with", cls.__class__, flush=True)

    @abstractproperty
    def species(self):
        pass

    @property
    def stuple(self):
        return tuple(self.species.split("+"))

    @property
    def species_combinations(self):
        r"""
        The various combinations of the species for use in testing
        Plasma methods.
        """
        from itertools import combinations, chain

        stuple = self.stuple
        ncombinations = np.arange(start=1, stop=len(stuple) + 1)
        if ncombinations.any():
            combos = chain(*[combinations(stuple, n) for n in ncombinations])
            return combos
        else:
            return None

    @property
    def mass(self):
        trans = {
            "a": "alpha particle",
            "p": "p,roton",
            "p1": "proton",
            "p2": "proton",
            "e": "electron",
        }
        m = {s: physical_constants["%s mass" % trans[s]][0] for s in self.stuple}
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
        return pd.Series({s: trans[s] for s in self.stuple})

    @property
    def m_amu(self):
        r"""
        Masses in amu.
        """
        a = physical_constants["alpha particle mass in u"][0]
        p = physical_constants["proton mass in u"][0]
        e = physical_constants["electron mass in u"][0]
        out = {"a": a, "p": p, "p1": p, "p2": p, "e": e}
        return pd.Series({s: out[s] for s in self.stuple})

    @property
    def charges(self):
        out = {
            "e": -constants.e,
            "p": constants.e,
            "p1": constants.e,
            "p2": constants.e,
            "a": 2 * constants.e,
        }
        return pd.Series({s: out[s] for s in self.stuple})

    @property
    def charge_states(self):
        out = {"e": -1.0, "p": 1.0, "p1": 1.0, "p2": 1.0, "a": 2.0}
        return pd.Series({s: out[s] for s in self.stuple})

    def test_ions(self):
        ions_ = pd.Series({s: ions.Ion(self.data, s) for s in self.stuple})
        pdt.assert_index_equal(ions_.index, self.object_testing.ions.index)
        for k, i in ions_.iteritems():
            pdt.assert_frame_equal(
                i.data,
                self.object_testing.ions.loc[k].data,
                "Unequal data for ion: %s" % k,
            )

    def test_conform_species(self):
        r"""
        Just test that the species is a valid input.
        """
        slist = (
            "a",
            "e",
            "p1",
            "p2",
            "a+p1",
            "p1+p2",
            "a+p2",
            "a+p1+p2",
            "a+p1+e",
            "p1+p2+e",
            "a+p2+e",
            "a+p1+p2+e",
        )
        # Check that the exception isn't raised.
        for s in slist:
            self.assertEqual(
                self.object_testing._conform_species(s), tuple(sorted(s.split("+")))
            )

        slist = (
            "a,p1",
            "p1,p2",
            "a,p2",
            "a,p1,p2",
            "a,p1,e",
            "p1,p2,e",
            "a,p2,e",
            "a,p1,p2,e",
            "a,p1+p2",
            "a,p1+e",
            "a+e,p1,p2",
        )
        for s in slist:
            with self.assertRaisesRegex(ValueError, "Invalid species"):
                self.object_testing._conform_species(s)

            if "+" in s:
                # A species list for which one species contains "+" is not
                # uniformly parsable.
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    self.object_testing._conform_species(*s.split(","))

    def test_chk_species_success(self):
        # print(self.slist)
        self.assertEqual(self.stuple, self.object_testing._chk_species(*self.stuple))

        # Ensure exception isn't raised for plasma's individual species.
        for s in self.stuple:
            # Automatically passes if no exception raised.
            self.object_testing._chk_species(s)

        # Check that any subset of the species and "s0+s1+..." pass,
        # but "s0,s1" don't.
        # combo_sizes = np.arange(start=2, stop=len(self.stuple) + 1)
        bad_species_msg = "Invalid species:"
        # if combo_sizes.any():
        #     for size in combo_sizes:
        #         combos = itertools.combinations(stuple, size)
        for combo in self.species_combinations:
            # print(combo, s, sep="\n")
            self.object_testing._chk_species(*combo)
            self.object_testing._chk_species("+".join(combo))
            bad_species = ",".join(combo)
            if "," in bad_species:
                with self.assertRaisesRegex(ValueError, bad_species_msg):
                    self.object_testing._chk_species(bad_species)

    @abstractmethod
    def test_chk_species_fail(self):
        r"""
        This method must be subclassed to test for species that fail the
        `_chk_species` tests.

        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        pass

    def test_species(self):
        self.assertEqual(self.object_testing.species, self.stuple)

    def test__set_species(self):
        with self.assertRaisesRegex(
            ValueError, "You must specify a species to instantiate a Plasma."
        ):
            plasma.Plasma(self.object_testing.data)

    def test_bfield(self):
        b = self.data.b.xs("", axis=1, level="S").loc[:, ["x", "y", "z"]]
        self.assertEqual(vector.BField(b), self.object_testing.bfield)
        self.assertEqual(vector.BField(b), self.object_testing.b)
        self.assertEqual(self.object_testing.b, self.object_testing.bfield)

    def test_number_density(self):
        ot = self.object_testing

        # print_inline_debug_info = False
        ions_ = pd.concat(
            {s: ot.ions[s].number_density for s in self.stuple}, axis=1, names=["S"]
        )
        total_ions = ions_.sum(axis=1)
        total_ions.name = "+".join(self.stuple)
        sum_species = self.species

        pdt.assert_series_equal(total_ions, ot.number_density(sum_species))
        pdt.assert_series_equal(total_ions, ot.n(sum_species))
        pdt.assert_series_equal(ot.n(sum_species), ot.number_density(sum_species))

        # print("", *self.species_combinations, sep="\n")
        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            this_ion = ions_.loc[:, s[0] if len(s) == 1 else s]

            # if print_inline_debug_info:
            #     print(s)
            #     print("<Ion>", type(this_ion))
            #     print(this_ion)
            #     print("<Plasma>", type(ot.number_density(*s)))
            #     print(ot.number_density(*s))

            if isinstance(this_ion, pd.Series):
                fcn = pdt.assert_series_equal
            else:
                fcn = pdt.assert_frame_equal

            fcn(this_ion, ot.number_density(*s))
            fcn(this_ion, ot.n(*s))
            fcn(ot.n(*s), ot.number_density(*s))

            if len(s) > 1:
                this_ion = this_ion.sum(axis=1)
                this_ion.name = "+".join(sorted(s))
                pdt.assert_series_equal(this_ion, ot.number_density("+".join(s)))
                pdt.assert_series_equal(this_ion, ot.n("+".join(s)))
                pdt.assert_series_equal(
                    ot.number_density("+".join(s)), ot.n("+".join(s))
                )

    def test_mass_density(self):
        ot = self.object_testing

        # print_inline_debug_info = False
        ions_ = pd.concat(
            {s: ot.ions[s].mass_density for s in self.stuple}, axis=1, names=["S"]
        )
        total_ions = ions_.sum(axis=1)
        total_ions.name = "+".join(self.stuple)
        sum_species = self.species

        pdt.assert_series_equal(total_ions, ot.mass_density(sum_species))
        pdt.assert_series_equal(total_ions, ot.rho(sum_species))
        pdt.assert_series_equal(ot.rho(sum_species), ot.mass_density(sum_species))

        # print("", *self.species_combinations, sep="\n")
        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            this_ion = ions_.loc[:, s[0] if len(s) == 1 else s]

            # if print_inline_debug_info:
            #     print(s)
            #     print("<Ion>", type(this_ion))
            #     print(this_ion)
            #     print("<Plasma>", type(ot.mass_density(*s)))
            #     print(ot.mass_density(*s))

            if isinstance(this_ion, pd.Series):
                fcn = pdt.assert_series_equal
            else:
                fcn = pdt.assert_frame_equal

            fcn(this_ion, ot.mass_density(*s))
            fcn(this_ion, ot.rho(*s))
            fcn(ot.rho(*s), ot.mass_density(*s))

            if len(s) > 1:
                this_ion = this_ion.sum(axis=1)
                this_ion.name = "+".join(sorted(s))
                pdt.assert_series_equal(this_ion, ot.mass_density("+".join(s)))
                pdt.assert_series_equal(this_ion, ot.rho("+".join(s)))
                pdt.assert_series_equal(
                    ot.mass_density("+".join(s)), ot.rho("+".join(s))
                )

    def test_thermal_speed(self):
        ot = self.object_testing
        ions_ = {s: ot.ions.loc[s].thermal_speed.data for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"]).sort_index(axis=1)
        ions_ = ions_.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        for s in self.species_combinations:
            if len(s) == 1:
                this_ion = ions_.xs(s[0], axis=1, level="S")
                pdt.assert_frame_equal(this_ion, ot.thermal_speed(*s))
                pdt.assert_frame_equal(ot.thermal_speed(*s), ot.w(*s))
                pdt.assert_frame_equal(ot.thermal_speed(s[0]), ot.w(*s))

                # Test that the scalar thermal speed is as expected in plasma.
                scalar = this_ion.loc[:, "scalar"].pow(2)
                par = this_ion.loc[:, "par"].pow(2)
                per = this_ion.loc[:, "per"].pow(2)
                chk = per.multiply(2).add(par).multiply(1.0 / 3.0)
                pdt.assert_series_equal(scalar, chk, check_names=False)

            else:
                these_ions = ions_.loc[:, pd.IndexSlice[:, s]]
                pdt.assert_frame_equal(these_ions, ot.thermal_speed(*s))
                pdt.assert_frame_equal(these_ions, ot.w(*s))
                pdt.assert_frame_equal(ot.thermal_speed(*s), ot.w(*s))

                msg = "The result of a total species thermal speed is physically ambiguous"
                with self.assertRaisesRegex(NotImplementedError, msg):
                    ot.thermal_speed("+".join(s))
                with self.assertRaisesRegex(NotImplementedError, msg):
                    ot.w("+".join(s))
                with self.assertRaises(ValueError):
                    ot.thermal_speed(",".join(s))

    def test_pth(self):
        # print_inline_debug_info = False
        # Test that Plasma returns each Ion plasma independently.
        ions_ = {s: self.object_testing.ions[s].pth for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"]).sort_index(axis=1)
        ions_ = ions_.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        # print("<Ions>", ions, sep="\n")

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            # if print_inline_debug_info:
            #     print(s)
            #     print("<Ion>", type(this_ion))
            #     print(this_ion)
            #     print("<Plasma>", type(self.object_testing.pth(*s)))
            #     print(self.object_testing.pth(*s))

            pdt.assert_frame_equal(this_ion, self.object_testing.pth(*s))

            if len(s) > 1:
                this_ion = this_ion.sum(axis=1, level="C")
                # if print_inline_debug_info:
                #     print("<Summed Ion>", this_ion,
                #           "<Plasma sum>", self.object_testing.pth("+".join(s)),
                #           sep="\n")
                pdt.assert_frame_equal(this_ion, self.object_testing.pth("+".join(s)))

    def test_temperature(self):
        # print_inline_debug_info = False
        # Test that Plasma returns each Ion plasma independently.
        ions_ = {s: self.object_testing.ions[s].temperature for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"]).sort_index(axis=1)
        ions_ = ions_.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        # print("<Ions>", ions, sep="\n")

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            # if print_inline_debug_info:
            #     print(s)
            #     print("<Ion>", type(this_ion))
            #     print(this_ion)
            #     print("<Plasma>", type(self.object_testing.temperature(*s)))
            #     print(self.object_testing.temperature(*s))

            pdt.assert_frame_equal(this_ion, self.object_testing.temperature(*s))

            if len(s) > 1:
                this_ion = this_ion.sum(axis=1, level="C")
                # if print_inline_debug_info:
                #     print("<Summed Ion>", this_ion,
                #           "<Plasma sum>",
                #           self.object_testing.temperature("+".join(s)),
                #           sep="\n")
                pdt.assert_frame_equal(
                    this_ion, self.object_testing.temperature("+".join(s))
                )

    def test_beta(self):
        pth = {s: self.object_testing.ions[s].pth for s in self.stuple}
        pth = pd.concat(pth, axis=1, names=["S"]).sort_index(axis=1)
        pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        bsq = self.data.loc[:, pd.IndexSlice["b", ["x", "y", "z"], ""]]
        bsq = bsq.pow(2).sum(axis=1)

        ions_ = pth.divide(bsq, axis=0)

        coeff = 2.0 * constants.mu_0 * 1e-12 / (1e-9 ** 2.0)
        ions_ *= coeff

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            # print_inline_debug_info = False
            # if print_inline_debug_info:
            #     print("",
            #           "<Test>",
            #           s,
            #           "<pth>",
            #           pth.loc[:, tk_species],
            #           "<bsq>", bsq,
            #           "<Ion>",
            #           type(this_ion),
            #           this_ion,
            #           "<Plasma>",
            #           type(self.object_testing.beta(*s)),
            #           self.object_testing.beta(*s),
            #           sep="\n")

            pdt.assert_frame_equal(this_ion, self.object_testing.beta(*s))

            if len(s) > 1:
                this_ion = this_ion.sum(axis=1, level="C")
                # if print_inline_debug_info:
                #     print("<Summed Ion>", this_ion,
                #           "<Plasma sum>",
                #           self.object_testing.beta("+".join(s)),
                #           sep="\n")
                pdt.assert_frame_equal(this_ion, self.object_testing.beta("+".join(s)))

    def test_anisotropy(self):

        # Test individual components. Should return RT values.
        for s in self.stuple:
            w = self.data.w.xs(s, axis=1, level="S")
            ani = (w.per / w.par).pow(2)
            ani.name = s
            # print("", ani, sep="\n")
            right = self.object_testing.anisotropy(s)
            pdt.assert_series_equal(ani, right)
            # print("", "<ani>", ani, sep="\n")

        # Test list of and sums of sums of species.
        for s in self.species_combinations:
            if len(s) == 1:
                continue
                # w = self.data.w.xs(s[0], axis=1, level="S")
                # ani = (w.per / w.par).pow(2)
                # ani.name = s
                # right = self.object_testing.anisotropy(s)
                # pdt.assert_series_equal(ani, right)
            else:
                # Test list of and sums of sums of species.
                pth = {sprime: self.object_testing.ions.loc[sprime].pth for sprime in s}
                pth = pd.concat(pth, axis=1, names=["S"])
                pth = pth.drop("scalar", axis=1, level="C")

                coeff = pd.Series({"par": -1, "per": 1})
                ani_s = pth.pow(coeff, axis=1, level="C").product(axis=1, level="S")
                ani_sum = (
                    pth.sum(axis=1, level="C")
                    .pow(coeff, axis=1, level="C")
                    .product(axis=1)
                )
                ani_sum.name = "+".join(sorted(s))

                # print_inline_debug_info = False
                # if print_inline_debug_info:
                #     print("<By species>",
                #           ani_s,
                #           "<Total ani>",
                #           ani_s,
                #           "<Plasma>",
                #           "<by species>",
                #           self.object_testing.anisotropy(*s),
                #           "<summed>",
                #           self.object_testing.anisotropy("+".join(s)),
                #           sep="\n")
                pdt.assert_frame_equal(ani_s, self.object_testing.anisotropy(*s))
                pdt.assert_series_equal(
                    ani_sum, self.object_testing.anisotropy("+".join(s))
                )

    def test_velocity(self):
        for s in self.species_combinations:
            if len(s) == 1:
                self.assertEqual(
                    self.object_testing.ions.loc[s[0]].velocity,
                    self.object_testing.velocity(*s),
                )
                self.assertEqual(
                    self.object_testing.ions.loc[s[0]].velocity,
                    self.object_testing.v(*s),
                )
                self.assertEqual(
                    self.object_testing.velocity(*s), self.object_testing.v(*s)
                )
            else:
                # Test species = (s0, s1, ..., sn)
                ot = self.object_testing
                ions_ = self.object_testing.ions.loc[list(s)].apply(lambda x: x.v)

                pdt.assert_series_equal(ions_, ot.velocity(*s))
                pdt.assert_series_equal(ions_, ot.v(*s))
                pdt.assert_series_equal(self.object_testing.velocity(*s), ot.v(*s))

                # Test species = "s0+s1+...+sn"
                rhos = ot.rho(*s)
                ions_ = pd.concat(
                    ions_.apply(lambda x: x.cartesian).to_dict(), axis=1, names=["S"]
                )
                # print("", "<Ions>", ions, "<rhos>", rhos, sep="\n")
                ions_ = ions_.multiply(rhos, axis=1, level="S")
                ions_ = ions_.sum(axis=1, level="C").divide(rhos.sum(axis=1), axis=0)
                # print("<vcom>", ions, sep="\n")
                ions_ = vector.Vector(ions_)

                self.assertEqual(ions_, ot.v("+".join(s)))
                self.assertEqual(ions_, ot.velocity("+".join(s)))

    def test_dv(self):
        # print_inline_debug_info = False

        msg = "identically zero"
        for s in self.stuple:
            with self.assertRaisesRegex(NotImplementedError, msg):
                self.object_testing.dv(s, s)
        with self.assertRaisesRegex(NotImplementedError, msg):
            s = "+".join(self.stuple)
            self.object_testing.dv(s, s)

        if len(self.stuple) == 1:
            # A multi-species plasma is necessary to calculate a dv.
            return None

        combos2 = [x for x in self.species_combinations if len(x) == 2]
        # print(*combos2)

        ot = self.object_testing
        for combo in combos2:
            # Calculate individual species dv.
            sb, sc = combo
            v0 = self.data.v.xs(sb, axis=1, level="S")
            v1 = self.data.v.xs(sc, axis=1, level="S")
            dv = v0.subtract(v1, axis=1)
            vector_dv = vector.Vector(dv)
            pdt.assert_frame_equal(dv, ot.dv(sb, sc).data)
            self.assertEqual(vector_dv, ot.dv(sb, sc))

            # Calculate dv for v_s - v_com.
            ssum = "+".join(combo)
            for s in combo:
                tk = pd.IndexSlice[["x", "y", "z"], list(combo)]
                vs = self.data.v.loc[:, tk]
                ns = self.data.n.loc[:, ""].loc[:, list(combo)]
                m = self.mass_in_mp.loc[list(combo)]
                rhos = ns.multiply(m, axis=1, level="S")
                rho_total = rhos.sum(axis=1)
                vcom = (
                    vs.multiply(rhos, axis=1, level="S")
                    .sum(axis=1, level="C")
                    .divide(rho_total, axis=0)
                )

                v = self.data.v.xs(s, axis=1, level="S")
                dv = v.subtract(vcom, axis=1, level="C")

                # if print_inline_debug_info:
                #     print(
                #           "<Test>",
                #           "<species>: %s, %s" % (combo, ssum),
                #           "<vs>", type(vs), vs,
                #           "<ns>", type(ns), ns,
                #           "<rhos>", type(rhos), rhos,
                #           "<sum(rhos)>", type(rho_total), rho_total,
                #           "<vcom>", type(vcom), vcom,
                #           "",
                #           sep="\n")

                pdt.assert_frame_equal(dv, ot.dv(s, ssum).data)
                self.assertEqual(vector.Vector(dv), ot.dv(s, ssum))

        if len(self.stuple) > 2:
            # Calculate dv for v_si - v_com for each s in stuple.
            ssum = "+".join(self.stuple)

            tk = pd.IndexSlice[["x", "y", "z"], list(self.stuple)]
            vs = self.data.v.loc[:, tk]
            ns = self.data.n.loc[:, ""].loc[:, list(self.stuple)]
            m = self.mass_in_mp.loc[list(self.stuple)]
            rhos = ns.multiply(m, axis=1, level="S")
            rho_total = rhos.sum(axis=1)
            vcom = (
                vs.multiply(rhos, axis=1, level="S")
                .sum(axis=1, level="C")
                .divide(rho_total, axis=0)
            )

            # if print_inline_debug_info:
            #     print(
            #           "",
            #           "<Test>",
            #           "<ssum>: %s" % ssum,
            #           "<vs>", type(vs), vs,
            #           "<ns>", type(ns), ns,
            #           "<rhos>", type(rhos), rhos,
            #           "<sum(rhos)>", type(rho_total), rho_total,
            #           "<vcom>", type(vcom), vcom,
            #           "",
            #           sep="\n")

            for s in self.stuple:
                # Calculate dv for v_si - v_com for each s in stuple.
                v = self.data.v.xs(s, axis=1, level="S")
                dv = v.subtract(vcom, axis=1, level="C")

                # if print_inline_debug_info:
                #     print(
                #           "",
                #           "<species>: %s" % s,
                #           "<v>", type(v), v,
                #           "<dv>", type(dv), dv,
                #           "",
                #           sep="\n")

                pdt.assert_frame_equal(dv, ot.dv(s, ssum).data)
                self.assertEqual(vector.Vector(dv), ot.dv(s, ssum))

            for combo in combos2:
                # Calculate dv for v_{s0+s1} - v_com for each s in stuple.
                tk = pd.IndexSlice[["x", "y", "z"], list(combo)]
                v_s0s1 = self.data.v.loc[:, tk]
                n_s0s1 = self.data.n.loc[:, ""].loc[:, list(combo)]
                m_s0s1 = self.mass_in_mp.loc[list(combo)]

                rho_s0s1 = n_s0s1.multiply(m_s0s1, axis=1, level="S")
                rho_total_s0s1 = rho_s0s1.sum(axis=1)
                rv_s0s1 = v_s0s1.multiply(rho_s0s1, axis=1, level="S").sum(
                    axis=1, level="C"
                )
                vcom_s0s1 = rv_s0s1.divide(rho_total_s0s1, axis=0)

                dv_s0s1 = vcom_s0s1.subtract(vcom, axis=1, level="C")

                # if print_inline_debug_info:
                #     print(
                #           "",
                #           "<species s0s1>: %s, %s" % (combo, "+".join(combo)),
                #           "<v s0s1>", type(v_s0s1), v_s0s1,
                #           "<ns s0s1>", type(n_s0s1), n_s0s1,
                #           "<rho s0s1>", type(rho_s0s1), rho_s0s1,
                #           "<sum(rho_s0s1)>",
                #               type(rho_total_s0s1), rho_total_s0s1,
                #           "<rv_s0s1>", type(rv_s0s1), rv_s0s1,
                #           "<vcom_s0s1>", type(vcom_s0s1), vcom_s0s1,
                #           "",
                #           "<dv_s0s1_com>", type(dv_s0s1), dv_s0s1,
                #           sep="\n")

                right = self.object_testing.dv("+".join(combo), ssum)
                pdt.assert_frame_equal(dv_s0s1, right.data)
                self.assertEqual(vector.Vector(dv_s0s1), right)

    def test_ca(self):
        tk = ["x", "y", "z"]
        b = self.data.b.loc[:, tk].pow(2).sum(axis=1).pipe(np.sqrt) * 1e-9
        n = self.data.n.loc[:, ""].loc[:, self.stuple] * 1e6
        m = self.mass
        rho = n * m

        combos = [x for x in self.species_combinations if len(x) > 1]
        total_masses = pd.DataFrame(
            {"+".join(s): rho.loc[:, s].sum(axis=1) for s in combos}
        )
        rho = pd.concat([rho, total_masses], axis=1).sort_index(axis=1)

        ions_ = (constants.mu_0 * rho).pow(-0.5).multiply(b, axis=0) / 1e3
        ions_.columns.names = ["S"]
        # print_inline_debug_info = False
        # if print_inline_debug_info:
        #     print("",
        #             "<Test>",
        #             "<species>", self.stuple,
        #             "<b>", type(b), b,
        #             "<n>", type(n), n,
        #             "<m>", type(m), m,
        #             "<rho>", type(rho), rho,
        #             "<Ions>", type(ions), ions,
        #             "<Species combinations>",
        #             [x for x in self.species_combinations],
        #             sep="\n")

        for s in self.species_combinations:
            if len(s) == 1:
                pdt.assert_series_equal(
                    ions_.xs(*s, axis=1), self.object_testing.ca(*s)
                )
            else:
                # Check individual species.
                pdt.assert_frame_equal(ions_.loc[:, s], self.object_testing.ca(*s))
                # Check total plasma.
                pdt.assert_series_equal(
                    ions_.loc[:, "+".join(s)], self.object_testing.ca("+".join(s))
                )

    def test_afsq(self):
        #        print_inline_debug_info = True

        slist = list(self.stuple)
        tk = pd.IndexSlice[["par", "per"], slist]
        w = self.data.w.loc[:, tk].drop("scalar", axis=1, level="C") * 1e3
        n = self.data.n.loc[:, ""].loc[:, slist] * 1e6
        m = self.mass.loc[slist]
        rho = n.multiply(m, axis=1, level="S")
        pth = 0.5 * w.pow(2.0).multiply(rho, axis=1, level="S")

        tk = pd.IndexSlice[["x", "y", "z"], ""]
        bsq = (self.data.b.loc[:, tk] * 1e-9).pow(2.0).sum(axis=1)

        # NOTE: Factor of 2 to get proper betas would go here.
        beta = pth.divide(bsq, axis=0) * constants.mu_0  # * 2.0
        dbeta = beta.per - beta.par
        ions_ = dbeta + 1.0

        #        if print_inline_debug_info:
        #            print("",
        #                  "<Test>",
        #                  "<species>: {}".format(list(self.species_combinations)),
        #                  "<tk>: {}".format(tk),
        #                  "<w>", type(w), w,
        #                  "<n>", type(n), n,
        #                  "<m>", type(m), m,
        #                  "<rho>", type(rho), rho,
        #                  "<pth>", type(pth), pth,
        #                  "<bsq>", type(bsq), bsq,
        #                  "<''beta''>", type(beta), beta,
        #                  "<''dbeta''>", type(dbeta), dbeta,
        #                  "<Ions>", type(ions), ions,
        #                  "",
        #                  sep="\n")

        msg = (
            "Youngest beams analysis shows that dynamic pressure is "
            "probably not useful."
        )
        # for s in self.stuple:
        #     pdt.assert_series_equal(ions.loc[:, s],
        #                            self.object_testing.afsq(s, pdynamic=False))
        #     with self.assertRaisesRegex(NotImplementedError, msg):
        #         self.object_testing.afsq(s, pdynamic=True)

        for combo in self.species_combinations:
            with self.assertRaisesRegex(NotImplementedError, msg):
                self.object_testing.afsq(*combo, pdynamic=True)
            if len(combo) == 1:
                #                print("<Series>")
                pdt.assert_series_equal(
                    ions_.loc[:, combo[0]],
                    self.object_testing.afsq(*combo, pdynamic=False),
                )
            else:
                #                if print_inline_debug_info:
                #                    print("<Frame>", ions.loc[:, combo], "", sep="\n")
                pdt.assert_frame_equal(
                    ions_.loc[:, combo], self.object_testing.afsq(*combo)
                )

                # So that we don't overcount the $1 +$ in AFSQ, we
                # do the following before taking the sum.
                left = 1 + (ions_.loc[:, combo] - 1).sum(axis=1)
                left.name = "+".join(combo)
                pdt.assert_series_equal(left, self.object_testing.afsq("+".join(combo)))

    def test_caani(self):
        # print_inline_debug_info = False

        combos = [x for x in self.species_combinations]
        masses = self.mass
        n = self.data.n.xs("", axis=1, level="C") * 1e6
        rhos = {
            "+".join(x): n.loc[:, list(x)].multiply(masses.loc[list(x)]).sum(axis=1)
            for x in combos
        }
        rhos = pd.concat(rhos, axis=1, names=["S"])

        tk = pd.IndexSlice[["x", "y", "z"], ""]
        b = (self.data.b.loc[:, tk]).pow(2).sum(axis=1).pipe(np.sqrt) * 1e-9

        ca = (rhos * constants.mu_0).pow(-0.5).multiply(b, axis=0) / 1e3

        slist = list(self.stuple)
        tk = pd.IndexSlice[["par", "per"], slist]
        w = self.data.w.loc[:, tk].drop("scalar", axis=1, level="C") * 1e3
        n = self.data.n.loc[:, ""].loc[:, slist] * 1e6
        m = self.mass.loc[slist]
        rho = n.multiply(m, axis=1, level="S")
        pth = 0.5 * w.pow(2.0).multiply(rho, axis=1, level="S")
        dp = pth.per - pth.par

        beta_ish = dp.multiply(constants.mu_0 * b.pow(-2.0), axis=0)

        # if print_inline_debug_info:
        #     print("",
        #           "<Test>",
        #           "<combos>: {}".format(combos),
        #           "<masses>", type(masses), masses,
        #           "<n>", type(n), n,
        #           "<rho>", type(rhos), rhos,
        #           "<b>", type(b), b,
        #           "<ca>", type(ca), ca,
        #           "<p>", type(pth), pth,
        #           "<dp>", type(dp), dp,
        #           "<beta*>", type(beta_ish), beta_ish,
        #           sep="\n")

        regex_msg = (
            "Youngest beams analysis shows that "
            "dynamic pressure is probably not useful."
        )
        for combo in combos:
            this_ca = ca.loc[:, "+".join(combo)]
            afsq = 1.0 + beta_ish.loc[:, list(combo)].sum(axis=1)
            this_caani = this_ca.multiply(afsq.pow(0.5), axis=0)
            this_caani.name = "+".join(combo)

            # if print_inline_debug_info:
            #     print(
            #           "<species>: {}".format(combo),
            #           "<afsq>", type(afsq), afsq,
            #           "<caani>", type(this_caani), this_caani,
            #           sep="\n")

            pdt.assert_series_equal(this_caani, self.object_testing.caani(*combo))
            pdt.assert_series_equal(
                this_caani, self.object_testing.caani("+".join(combo))
            )
            pdt.assert_series_equal(
                self.object_testing.caani(*combo),
                self.object_testing.caani("+".join(combo)),
            )
            with self.assertRaisesRegex(NotImplementedError, regex_msg):
                self.object_testing.caani(*combo, pdynamic=True)
            with self.assertRaisesRegex(NotImplementedError, regex_msg):
                self.object_testing.caani("+".join(combo), pdynamic=True)

    def test_lnlambda(self):
        # print_inline_debug_info = False

        #        if len(self.stuple) == 1:
        #            # We only test plasmas w/ > 1 species.
        #            return None

        kb_J = constants.physical_constants["Boltzmann constant"]
        kb_eV = constants.physical_constants["Boltzmann constant in eV/K"]

        amu = self.m_amu
        charge_states = self.charge_states
        n = self.data.n.xs("", axis=1, level="C").loc[:, self.stuple] * 1e6
        m = self.mass
        # rho = n.multiply(m, axis=1, level="S")
        w = self.data.w.scalar.loc[:, self.stuple] * 1e3

        Tkelvin = 0.5 * w.pow(2.0).multiply(m, axis=1, level="S") / kb_J[0]
        TeV = Tkelvin * kb_eV[0]

        nZsqOTeV = n.multiply(charge_states.pow(2), axis=1, level="S").divide(
            TeV, axis=1, level="S"
        )

        # if print_inline_debug_info:
        #     print("",
        #           "<Test>",
        #           "<species>: {}".format(self.stuple),
        #           "<amu>", type(amu), amu,
        #           "<charge_states>", type(charge_states), charge_states,
        #           "<n>", type(n), n,
        #           "<mass>", type(m), m,
        #           # "<rho>", type(rho), rho,
        #           "<w>", type(w), w,
        #           "<kb_J>", kb_J,
        #           "<kb_eV>", kb_eV,
        #           "<T [K]>", type(Tkelvin), Tkelvin,
        #           "<T [eV]>", type(TeV), TeV,
        #           "<n Z^2 / T [eV]>", type(nZsqOTeV), nZsqOTeV,
        #           "",
        #           sep="\n")

        regex_msg = (
            "`lnlambda` can only calculate with individual s0 " "and s1 species."
        )
        invalid = "Invalid species"
        combos2 = [x for x in self.species_combinations if len(x) == 2]
        for combo in combos2:
            si, sj = combo
            ai = amu.loc[si]
            aj = amu.loc[sj]
            zi = charge_states.loc[si]
            zj = charge_states.loc[sj]
            ti = TeV.loc[:, si]
            tj = TeV.loc[:, sj]

            left = (zi * zj * (ai + aj)) / ((ai * tj) + (aj * ti))
            right = nZsqOTeV.loc[:, list(combo)].sum(axis=1).pipe(np.sqrt)
            ln = np.log(left * right)
            lnlambda = 29.9 - ln
            lnlambda.name = ",".join(sorted(combo))
            # ln = None
            # lnlambda = None

            # if print_inline_debug_info:
            #     print(
            #           "<combo>: {}".format(combo),
            #           "<sqrt( sum(n_i Z_i^s / T_i [eV]) )>",
            #               type(right), right,
            #           "<left>", type(left), left,
            #           "<ln>", type(ln), ln,
            #           "<lnlambda>", type(lnlambda), lnlambda,
            #           "",
            #           sep="\n")

            pdt.assert_series_equal(
                lnlambda, self.object_testing.lnlambda(combo[0], combo[1])
            )
            pdt.assert_series_equal(
                lnlambda,
                self.object_testing.lnlambda(combo[1], combo[0]),
                check_names=False,
            )

            # NOTE: The following various Invalid Species tests are excessive
            #       and should be reduced.
            s0s1 = "+".join(combo)  # ("+".join(combo), combo):
            with self.assertRaisesRegex(ValueError, regex_msg):
                self.object_testing.lnlambda(combo[0], s0s1)
            with self.assertRaisesRegex(ValueError, regex_msg):
                self.object_testing.lnlambda(s0s1, combo[0])
            with self.assertRaisesRegex(ValueError, regex_msg):
                self.object_testing.lnlambda(combo[1], s0s1)
            with self.assertRaisesRegex(ValueError, regex_msg):
                self.object_testing.lnlambda(s0s1, combo[1])
            with self.assertRaisesRegex(ValueError, regex_msg):
                self.object_testing.lnlambda(s0s1, s0s1)

            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda("+".join(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(list(combo), "+".join(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(",".join(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(list(combo), ",".join(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(list(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(list(combo), combo[0])
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(list(combo), combo[1])
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(combo[0], list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                self.object_testing.lnlambda(combo[1], list(combo))

    @unittest.skip("in progress")
    def test_nuc_ii(self):
        pass

    @unittest.skip("in progress")
    def test_nc_ii(self):
        pass

    def test_nuc_ij(self):
        r"""
        We calculate the two-species collision frequency for differential
        flow following Hernandez & Marsch (JGR 1985,
        doi:10.1029/JA090iA11p11062) Eq. (18).
        """
        from scipy.special import erf
        from scipy import constants

        # print_inline_debug_info = False

        if len(self.stuple) == 1:
            # We only test plasmas w/ > 1 species.
            return None

        slist = list(self.stuple)
        coeff = 4.0 * np.pi * constants.epsilon_0 ** 2.0
        qsq = self.charges ** 2.0
        m = self.mass
        w = self.data.w.par.loc[:, slist] * 1e3
        wsq = w.pow(2.0)
        n = self.data.n.xs("", axis=1, level="C").loc[:, slist] * 1e6
        rho = n.multiply(m, axis=1)
        tk = pd.IndexSlice[["x", "y", "z"], slist]
        v = self.data.v.loc[:, tk] * 1e3

        combos2 = [x for x in self.species_combinations if len(x) == 2]

        # if print_inline_debug_info:
        #     print("",
        #           "<Test>",
        #           "<species>: {}".format(self.stuple),
        #           "<coeff>: %s" % coeff,
        #           "<qsq>", type(qsq), qsq,
        #           "<m>", type(m), m,
        #           "<w>", type(w), w,
        #           "<wsq>", type(wsq), wsq,
        #           "<n>", type(n), n,
        #           "<rho>", type(rho), rho,
        #           "<v>", type(v), v,
        #           "<combos len 2>", combos2,
        #           "",
        #           sep="\n")

        for combo in combos2:
            sa, sb = combo

            ma = m.loc[sa]
            mb = m.loc[sb]
            mu = (ma * mb) / (ma + mb)
            qabsq = qsq.loc[[sa, sb]].product()
            all_coeff = qabsq / (coeff * mu * ma)

            nb = n.loc[:, sb]
            wab = wsq.loc[:, [sa, sb]].sum(axis=1).pipe(np.sqrt)

            lnlambda = self.object_testing.lnlambda(sa, sb)

            va = v.xs(sa, axis=1, level="S")
            vb = v.xs(sb, axis=1, level="S")
            dvvec = va - vb
            dv = dvvec.pow(2).sum(axis=1).pipe(np.sqrt)
            dvw = dv.divide(wab, axis=0)

            gauss_coeff = dvw.multiply(2.0 / np.sqrt(np.pi))
            # ldr = longitudinal diffusion rate $\hat{\nu}_L$.
            erf_dvw = erf(dvw)
            gaussian_term = gauss_coeff * np.exp(-(dvw ** 2.0))
            ldr = dvw.pow(-3.0) * (erf_dvw - gaussian_term)

            nuab = all_coeff * (nb * lnlambda / wab.pow(3.0)) * ldr / 1e-7

            exp = pd.Series({sa: 1.0, sb: -1.0})
            rho_ratio = rho.loc[:, [sa, sb]].pow(exp, axis=1, level="S").product(axis=1)
            nuba = nuab.multiply(rho_ratio, axis=0)
            nuc = nuab.add(nuba, axis=0)

            nuab.name = "%s-%s" % (sa, sb)
            nuba.name = "%s-%s" % (sb, sa)
            nuc.name = "%s+%s" % (sa, sb)

            # if print_inline_debug_info:
            #     print("",
            #           "<combo>: {}".format(combo),
            #           "<ma>", type(ma), ma,
            #           "<mu>", type(mu), mu,
            #           "<qab^2>", type(qabsq), qabsq,
            #           "<qa^2 qb^2 / 4 pi e0^2 ma mu>", type(all_coeff), all_coeff,
            #           "<nb>", type(nb), nb,
            #           "<wab>", type(wab), wab,
            #           "<lnlambda>", type(lnlambda), lnlambda,
            #           "<dv vec>", type(dvvec), dvvec,
            #           "<dv>", type(dv), dv,
            #           "<dv/wab>", type(dvw), dvw,
            #           "<erf(dv/wab)>", type(erf_dvw), erf_dvw,
            #           "<(dv/wab) * 2/sqrt(pi) * exp(-(dv/wab)^2)>", type(gaussian_term), gaussian_term,
            #           "<transverse diffusion rate>", type(ldr), ldr,
            #           "<nuab>", type(nuab), nuab,
            #           "<rho_a/rho_b>", type(rho_ratio), rho_ratio,
            #           "<nuba>", type(nuba), nuba,
            #           "<nuc>", type(nuc), nuc,
            #           "",
            #           sep="\n")

            pdt.assert_series_equal(
                nuab, self.object_testing.nuc_ij(sa, sb, both_species=False)
            )
            pdt.assert_series_equal(
                nuba, self.object_testing.nuc_ij(sb, sa, both_species=False)
            )
            pdt.assert_series_equal(nuc, self.object_testing.nuc_ij(sa, sb))

            nuc.name = "%s+%s" % (sb, sa)
            pdt.assert_series_equal(nuc, self.object_testing.nuc_ij(sb, sa))

            pdt.assert_series_equal(
                self.object_testing.nuc_ij(sa, sb),
                self.object_testing.nuc_ij(sb, sa),
                check_names=False,
            )

    def test_spacecraft_in_plasma(self):
        sc_data = base.TestData().spacecraft_data

        Wind = pd.concat(
            {"pos": sc_data.xs("gse", axis=1, level="M")}, axis=1, names=["M"]
        )
        Wind = spacecraft.Spacecraft(Wind, "Wind", "GSE")

        PSP = pd.concat(
            {
                "pos": sc_data.xs("pos_HCI", axis=1, level="M"),
                "v": sc_data.xs("v_HCI", axis=1, level="M"),
                "carr": sc_data.xs("Carr", axis=1, level="M"),
            },
            axis=1,
            names=["M"],
        )
        PSP = spacecraft.Spacecraft(PSP, "PSP", "HCI")

        ot = self.object_testing
        ot.set_spacecraft(None)
        self.assertIsNone(ot.spacecraft)

        ot.set_spacecraft(Wind)
        self.assertEqual(ot.spacecraft, Wind)
        self.assertEqual(ot.spacecraft, ot.sc)

        ot.set_spacecraft(PSP)
        self.assertEqual(ot.spacecraft, PSP)
        self.assertEqual(ot.spacecraft, ot.sc)

        self.assertNotEqual(ot.spacecraft, Wind)
        self.assertNotEqual(ot.sc, Wind)

        ot.set_spacecraft(None)

    def test_nc_ij_without_spacecraft(self):
        #         if len(self.stuple) == 1:
        #             # We only test Nc for plasmas with more than 1 species.
        #             return None

        ot = self.object_testing
        ot.set_spacecraft(None)
        combos2 = [x for x in self.species_combinations if len(x) == 2]
        for combo in combos2:
            sa, sb = combo
            # Assert failure to calculate Nc when no spacecraft set.
            with self.assertRaises(ValueError):
                ot.nc_ij(sa, sb)

    def test_nc_ij_with_spacecraft(self):

        if len(self.stuple) == 1:
            # We only test plasmas w/ > 1 species.
            return None

        slist = list(self.stuple)

        v = self.data.v
        v = pd.concat(
            {s: v.xs(s, axis=1, level="S") for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)

        # Neither `n` nor `rho` units b/c Vcom divides out
        # the [rho].
        m = self.mass
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)
        rho = n.multiply(m, axis=1, level="S")

        vcom = (
            v.multiply(rho, axis=1, level="S")
            .sum(axis=1, level="C")
            .divide(rho.sum(axis=1), axis=0)
        )
        vsw = vcom.pow(2.0).sum(axis=1).pipe(np.sqrt) * 1e3

        sc_data = base.TestData().spacecraft_data

        Wind = pd.concat(
            {"pos": sc_data.xs("gse", axis=1, level="M")}, axis=1, names=["M"]
        )
        Wind = spacecraft.Spacecraft(Wind, "Wind", "GSE")
        tau_exp_Wind = Wind.distance2sun.multiply(vsw.pow(-1.0), axis=0)

        PSP = pd.concat(
            {
                "pos": sc_data.xs("pos_HCI", axis=1, level="M"),
                "v": sc_data.xs("v_HCI", axis=1, level="M"),
                "carr": sc_data.xs("Carr", axis=1, level="M"),
            },
            axis=1,
            names=["M"],
        )
        PSP = spacecraft.Spacecraft(PSP, "PSP", "HCI")
        #         Rs = 695.508e6 # [m]
        #         r_Re = constants.au - (self.data.gse.x * Rs)
        tau_exp_PSP = PSP.distance2sun.multiply(vsw.pow(-1.0), axis=0)

        # print("",
        #       "<Test>",
        #       "<species>: {}".format(self.stuple),
        #       "<v>", type(v), v,
        #       "<m>", type(m), m,
        #       "<n>", type(n), n,
        #       "<rho>", type(rho), rho,
        #       "<vcom>", type(vcom), vcom,
        #       "<vsw>", type(vsw), vsw,
        #       "<r>", type(r), r,
        #       "<tau_exp>", type(tau_exp), tau_exp,
        #       sep="\n")

        individual_msg = (
            "`nc` can only calculate with individual" " `sa` and `sb` species."
        )
        invalid_msg = "Invalid species"

        combos2 = [x for x in self.species_combinations if len(x) == 2]
        ot = self.object_testing
        for combo in combos2:
            sa, sb = combo

            for sc, tau_exp in zip((Wind, PSP), (tau_exp_Wind, tau_exp_PSP)):

                ot.set_spacecraft(sc)

                nuab = ot.nuc_ij(sa, sb, both_species=False)
                nuba = ot.nuc_ij(sb, sa, both_species=False)
                nuc = ot.nuc_ij(sa, sb, both_species=True)

                ncab = nuab.multiply(tau_exp, axis=0) * 1e-7
                ncab.name = "%s-%s" % (sa, sb)

                ncba = nuba.multiply(tau_exp, axis=0) * 1e-7
                ncba.name = "%s-%s" % (sb, sa)

                nc = nuc.multiply(tau_exp, axis=0) * 1e-7
                nc.name = "%s+%s" % combo

                # print("",
                #       "<nuab>", type(nuab), nuab,
                #       "<ncab>", type(ncab), ncab,
                #       "<nuba>", type(nuba), nuba,
                #       "<ncba>", type(ncba), ncba,
                #       "<nuc>", type(nuc), nuc,
                #       "<nc>", type(nc), nc,
                #       "",
                #       sep="\n")

                pdt.assert_series_equal(ncab, ot.nc_ij(sa, sb, both_species=False))
                pdt.assert_series_equal(ncba, ot.nc_ij(sb, sa, both_species=False))
                pdt.assert_series_equal(nc, ot.nc_ij(sa, sb, both_species=True))
                pdt.assert_series_equal(
                    nc, ot.nc_ij(sb, sa, both_species=True), check_names=False
                )
                pdt.assert_series_equal(
                    ot.nc_ij(sa, sb, both_species=True),
                    ot.nc_ij(sb, sa, both_species=True),
                    check_names=False,
                )

        # Ensure spacecraft is None
        ot.set_spacecraft(None)

        with self.assertRaisesRegex(ValueError, individual_msg):
            ot.nc_ij("+".join(combo), sa)
        with self.assertRaisesRegex(ValueError, individual_msg):
            ot.nc_ij(sa, "+".join(combo))

        with self.assertRaisesRegex(ValueError, invalid_msg):
            ot.nc_ij(",".join(combo), sa)
        with self.assertRaisesRegex(ValueError, invalid_msg):
            ot.nc_ij(sa, ",".join(combo))

        with self.assertRaisesRegex(TypeError, invalid_msg):
            ot.nc_ij(combo, sa)
        with self.assertRaisesRegex(TypeError, invalid_msg):
            ot.nc_ij(sa, combo)

    def test_estimate_electrons(self):
        #        print_inline_debug_info = True

        stuple = self.stuple

        if "p" not in self.stuple and "p1" not in self.stuple:
            with self.assertRaisesRegex(
                ValueError,
                # Match this sentence at start of string.
                "^Plasma must contain \(core\) protons to estimate electrons.",  # noqa: W605
            ):
                self.object_testing.estimate_electrons()

        else:

            qi = self.charge_states
            ni = self.data.n.xs("", axis=1, level="C").loc[:, list(stuple)]
            niqi = ni.multiply(qi, axis=1, level="S")
            vi = self.data.v.loc[:, pd.IndexSlice[:, list(stuple)]]
            niqivi = vi.multiply(niqi, axis=1, level="S")
            nqv = niqivi.sum(axis=1, level="C")
            # Signs in -1 * niqi / qe cancel to give positive definite ne.
            ne = niqi.sum(axis=1)
            # Signs in -1 * niqivi / neqe cancel. The charge state of e- is -1.
            ve = nqv.divide(ne, axis=0)

            if "p" in self.stuple:
                tkw = pd.IndexSlice["scalar", "p"]
                tkn = "p"
                exp = pd.Series({"p": 1.0, "e": -1.0})
            else:
                tkw = pd.IndexSlice["scalar", "p1"]
                tkn = "p1"
                exp = pd.Series({"p1": 1.0, "e": -1.0})

            wp = self.data.w.loc[:, tkw]
            npne = self.data.n.xs("", axis=1, level="C").loc[:, tkn]
            npne = pd.concat([npne, ne], axis=1, keys=[tkn, "e"])
            nrat = npne.pow(exp, axis=1, level="S").product(axis=1)
            mpme = physical_constants["electron-proton mass ratio"][0] ** -1.0
            we = (nrat * mpme).multiply(wp.pow(2), axis=0).pipe(np.sqrt)

            tmp = pd.concat([we, we], axis=1, keys=["par", "per"])
            ne.name = ""
            electrons = pd.concat(
                [ne, ve, tmp], axis=1, keys=["n", "v", "w"], names=["M", "C"]
            )

            electrons = ions.Ion(electrons, "e")

            #            if print_inline_debug_info:
            #                print("<Test>",
            #                      "<species>: {}".format(stuple),
            #                      "<charges>", type(qi), qi,
            #                      "<n>", type(ni), ni,
            #                      "<niqi>", type(niqi), niqi,
            #                      "<ne>", type(ne), ne,
            #                      "<vi>", type(vi), vi,
            #                      "<niqivi>", type(niqivi), niqivi,
            #                      "<nqv>", type(nqv), nqv,
            #                      "<ve>", type(ve), ve,
            #                      "<w proton>", type(wp), wp,
            #                      "<npne>", type(npne), npne,
            #                      "<nrat>", type(nrat), nrat,
            #                      "<mpme>: %s" % mpme,
            #                      "<we>", type(we), we,
            #                      "<electrons>", type(electrons), electrons, electrons.data,
            #                      "", sep="\n")

            # Check electrons are properly calculated.
            ot = self.object_testing
            pdt.assert_frame_equal(electrons.data, ot.estimate_electrons().data)
            self.assertEqual(electrons, ot.estimate_electrons())

            # Check that electrons aren't stored in plasma.
            self.assertFalse("e" in ot.species)
            comp_data = (
                pd.concat({"e": electrons.data}, axis=1, names=["S", "M", "C"])
                .reorder_levels(["M", "C", "S"], axis=1)
                .sort_index(axis=1)
            )

            self.assertFalse(
                comp_data.isin(ot.data).any().any(),
                "There should not be e- data in plasma data.",
            )

            # # Check that electrons are still returned when `inplace=True`.
            # self.assertEqual(electrons,
            #                  self.object_testing.estimate_electrons(inplace=True))
            # # Check that electrons are in plasma after inplace calculation.
            # self.assertTrue("e" in object_testing.species)
            # self.assertTrue(electrons.data.isin(plasma.data).all().all(),
            #                 "There should be e- data in plasma data.")
            # self.assertEqual(electrons, self.object_testing.ions["e"])
            # # Check that electrons aren't duplicately stored after inplace calculation.
            # self.assertFalse(self.object_testing.data.columns.duplicated().any(),
            #         "There should not be duplicated columns after inplace e- calculation.")
            # self.object_testing.estimate_electrons(inplace=True)
            # self.assertFalse(self.object_testing.data.columns.duplicated().any(),
            #         "There should not be duplicated columns after inplace e- calculation.")
            #
            # # TODO: Do I need to drop the electrons and create a new plasma as tear down for this test?
            # self.object_testing.data.drop(electrons.data.columns, axis=1, inplace=True)
            # species = list(self.object_testing.species)
            # species.remove("e")
            # self.object_testing._Plasma__set_species(*species)
            # self.object_testing._Plasma__set_ions()

    def test_pdynamic(self):
        print_inline_debug_info = False

        slist = list(self.stuple)

        if len(slist) == 1:
            msg = "Must have >1 species to calculate dynamic pressure."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.pdynamic(*slist)
            return None  # Exit test.

        v = self.data.v
        v = pd.concat(
            {s: v.xs(s, axis=1, level="S") for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)

        # Neither `n` nor `rho` units b/c Vcom divides out
        # the [rho].
        m = self.mass_in_mp
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)
        rho = n.multiply(m, axis=1, level="S")

        if print_inline_debug_info:
            print(
                "",
                "<Test>",
                "<species>: {}".format(self.stuple),
                "<v>",
                type(v),
                v,
                "<m>",
                type(m),
                m,
                "<n>",
                type(n),
                n,
                "<rho>",
                type(rho),
                rho,
                sep="\n",
            )

        for combo in self.species_combinations:

            if len(combo) == 1:
                msg = "Must have >1 species to calculate dynamic pressure."
                with self.assertRaisesRegex(ValueError, msg):
                    self.object_testing.pdynamic(*combo)
                continue  # Skip this test case.

            scom = "+".join(combo)

            rho_i = rho.loc[:, list(combo)]
            rho_t = rho_i.sum(axis=1)
            v_i = v.loc[:, list(combo)]
            vcom = (
                v_i.multiply(rho_i, axis=1, level="S")
                .sum(axis=1, level="C")
                .divide(rho_t, axis=0)
            )
            dv_i = v_i.subtract(vcom, axis=1, level="C")
            dvsq_i = dv_i.pow(2.0).sum(axis=1, level="S")
            dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
            dvsq_rho = dvsq_rho_i.sum(axis=1)

            const = (
                0.5 * constants.m_p * 1e6 * 1e6 / 1e-12
            )  # [m_p] * [n] * [dv]**2 / [p]
            pdv = dvsq_rho.multiply(const)

            if print_inline_debug_info:
                print(
                    "",
                    "<combo>: {}".format(combo),
                    "<scom>: %s" % scom,
                    "<rho_i>",
                    type(rho_i),
                    rho_i,
                    "<rho_t>",
                    type(rho_t),
                    rho_t,
                    "<v_i>",
                    type(v_i),
                    v_i,
                    "<vcom>",
                    type(vcom),
                    vcom,
                    "<dv_i>",
                    type(dv_i),
                    dv_i,
                    "<dvsq_i>",
                    type(dvsq_i),
                    dvsq_i,
                    "<dvsq_rho_i>",
                    type(dvsq_rho_i),
                    dvsq_rho_i,
                    "<dvsq_rho>",
                    type(dvsq_rho),
                    dvsq_rho,
                    "<const> %s" % const,
                    "<pdv>",
                    type(pdv),
                    pdv,
                    sep="\n",
                    end="\n\n",
                )

            pdv.name = "pdynamic"
            pdt.assert_series_equal(pdv, self.object_testing.pdynamic(*combo))
            pdt.assert_series_equal(pdv, self.object_testing.pdv(*combo))
            pdt.assert_series_equal(
                self.object_testing.pdynamic(*combo), self.object_testing.pdv(*combo)
            )
            pdt.assert_series_equal(
                self.object_testing.pdv(*combo), self.object_testing.pdynamic(*combo)
            )
            pdt.assert_series_equal(self.object_testing.pdynamic(*combo), pdv)
            pdt.assert_series_equal(
                self.object_testing.pdynamic(*combo),
                self.object_testing.pdynamic(*combo),
            )
            pdt.assert_series_equal(
                self.object_testing.pdynamic(*combo),
                self.object_testing.pdynamic(*combo[::-1]),
            )

            invalid_msg = "Invalid species"
            # dynamic pressure shouldn't work with a comma separated list or sub-list.
            with self.assertRaisesRegex(ValueError, invalid_msg):
                self.object_testing.pdynamic(",".join(combo))
            with self.assertRaisesRegex(ValueError, invalid_msg):
                self.object_testing.pdynamic(",".join(combo), combo[0])
            with self.assertRaisesRegex(ValueError, invalid_msg):
                self.object_testing.pdynamic(combo[0], ",".join(combo))

            # dynamic pressure should work with sum of species, but ot a sub-list
            # that includes a sum.
            pdt.assert_series_equal(pdv, self.object_testing.pdynamic(scom))

            #            print("<combo[0], scom>: {}, {}".format(combo[0], scom), end="\n\n")
            with self.assertRaisesRegex(ValueError, invalid_msg):
                self.object_testing.pdynamic(combo[0], scom)
            with self.assertRaisesRegex(ValueError, invalid_msg):
                self.object_testing.pdynamic(scom, combo[0])

    def test_heatflux(self):
        print_inline_debug_info = False

        # q = rho (v^3 + (3/2) v w^2)
        slist = list(self.stuple)

        if len(slist) == 1:
            msg = "Must have >1 species to calculate dynamic pressure."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.pdynamic(*slist)
            return None  # Exit test.

        m = self.mass_in_mp
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)
        rho = n.multiply(m, axis=1, level="S")
        rho.columns.names = ["S"]

        w = self.data.w.par.loc[:, slist]

        b = self.data.b.xs("", axis=1, level="S").loc[:, ["x", "y", "z"]]
        bhat = b.divide(b.pow(2).sum(axis=1).pipe(np.sqrt), axis=0)

        v = self.data.v
        v = pd.concat(
            {s: v.xs(s, axis=1, level="S") for s in slist}, axis=1, names=["S"]
        ).sort_index(axis=1)
        vpar = v.multiply(bhat, axis=0).sum(axis=1, level="S")
        qa = vpar.pow(3)
        qb = vpar.multiply(w.pow(2), axis=1, level="S")
        qc = rho.multiply(
            qa.add((3.0 / 2.0) * qb, axis=1, level="S"), axis=1, level="S"
        )

        coeff = constants.m_p * 1e6 * 1e9 / 1e-4  # [m_p] [n] [v]^3 / [q]
        q = qc.multiply(coeff)

        if print_inline_debug_info:
            print(
                "",
                "<Test>",
                "<species>: {}".format(self.stuple),
                "<m>",
                type(m),
                m,
                "<n>",
                type(n),
                n,
                "<rho>",
                type(rho),
                rho,
                "<b>",
                type(b),
                b,
                "<bhat>",
                type(bhat),
                bhat,
                "<v>",
                type(v),
                v,
                "<vpar>",
                type(vpar),
                vpar,
                "<qa>",
                type(qa),
                qa,
                "<qb>",
                type(qb),
                qb,
                "<qc>",
                type(qc),
                qc,
                "<q>",
                type(q),
                q,
                sep="\n",
            )

        for s in self.species_combinations:
            if len(s) == 1:
                # Only single species case.
                qi = q.loc[:, s[0]]
                qi.name = s[0]
            else:
                qi = q.loc[:, list(s)]

                if print_inline_debug_info:
                    print("<qi>", type(qi), qi, sep="\n")

                # Check the list input case first.
                pdt.assert_frame_equal(qi, self.object_testing.heat_flux(*s))
                pdt.assert_frame_equal(qi, self.object_testing.qpar(*s))
                pdt.assert_frame_equal(
                    self.object_testing.heat_flux(*s), self.object_testing.qpar(*s)
                )
                # Then sum `qi` to check the sum case.
                qi = qi.sum(axis=1)
                qi.name = "+".join(sorted(list(s)))

            if print_inline_debug_info:
                print("<qi>", type(qi), qi, sep="\n")

            # Check the sum case.
            pdt.assert_series_equal(qi, self.object_testing.heat_flux("+".join(s)))
            pdt.assert_series_equal(qi, self.object_testing.qpar("+".join(s)))
            pdt.assert_series_equal(
                self.object_testing.heat_flux("+".join(s)),
                self.object_testing.qpar("+".join(s)),
            )

    def test_set_auxiliary_data(self):
        ot = self.object_testing
        data = base.TestData().combined_data
        drop = data.columns.isin(ot.data.columns)
        aux = data.loc[:, ~drop]
        ot.set_auxiliary_data(aux)
        pdt.assert_frame_equal(aux, ot.auxiliary_data)
        pdt.assert_frame_equal(ot.auxiliary_data, ot.aux)

        ot.set_auxiliary_data(None)
        self.assertIsNone(ot.auxiliary_data)
        self.assertIsNone(ot.aux)

        with self.assertRaises(ValueError):
            ot.set_auxiliary_data(ot.data)

    def test_epoch(self):
        epoch = self.data.index
        self.assertIsInstance(epoch, pd.DatetimeIndex)

        ot = self.object_testing
        pdt.assert_index_equal(epoch, ot.data.index)
        pdt.assert_index_equal(epoch, ot.index)
        pdt.assert_index_equal(epoch, ot.epoch)
        pdt.assert_index_equal(ot.epoch, ot.data.index)

    # @unittest.skip("Code under dev. Not ready to test.")
    def test_build_alfvenic_turbulence(self):
        species = self.species
        slist = species.split("+")
        ns = len(slist)
        data = self.data

        tkc = ["x", "y", "z"]
        v = data.loc[:, "v"].loc[:, pd.IndexSlice[tkc, slist]]
        b = data.loc[:, "b"].xs("", axis=1, level="S").loc[:, tkc]
        n = data.loc[:, "n"].xs("", axis=1, level="C").loc[:, slist]
        r = n.multiply(self.mass_in_mp.loc[slist], axis=1)
        rtot = r.sum(axis=1)

        bat = self.object_testing.build_alfvenic_turbulence
        AlfvenicTurbulence = alfvenic_turbulence.AlfvenicTurbulence

        test_window = "365d"
        test_periods = 1
        if ns == 1:
            v = v.xs(species, axis=1, level="S")
            alf_turb = AlfvenicTurbulence(
                v, b, rtot, species, window=test_window, min_periods=test_periods
            )
            built = bat(species, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

        elif ns == 2:

            # Check CoM velocity case.
            vcom = (
                v.multiply(r, axis=1, level="S")
                .sum(axis=1, level="C")
                .divide(rtot, axis=0)
            )
            alf_turb = AlfvenicTurbulence(
                vcom, b, rtot, species, window=test_window, min_periods=test_periods
            )
            built = bat(species, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            s0, s1 = species.split("+")
            v0 = v.xs(s0, axis=1, level="S")
            v1 = v.xs(s1, axis=1, level="S")

            # Check dv s0,s1 case.
            dv = v0.subtract(v1, axis=1, level="C")
            s0s1 = ",".join([s0, s1])
            r1 = r.xs(s1, axis=1)
            alf_turb = AlfvenicTurbulence(
                dv, b, r1, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s1,s0 case.
            dv = v1.subtract(v0, axis=1, level="C")
            s0s1 = ",".join([s1, s0])
            r0 = r.xs(s0, axis=1)
            alf_turb = AlfvenicTurbulence(
                dv, b, r0, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s0,s0+s1 case.
            dv = v0.subtract(vcom, axis=1)
            s0s1 = ",".join([s0, species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s1,s0+s1 case.
            dv = v1.subtract(vcom, axis=1)
            s0s1 = ",".join([s1, species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

        elif ns == 3:

            # Check CoM velocity case.
            vcom = (
                v.multiply(r, axis=1, level="S")
                .sum(axis=1, level="C")
                .divide(rtot, axis=0)
            )
            alf_turb = AlfvenicTurbulence(
                vcom, b, rtot, species, window=test_window, min_periods=test_periods
            )
            built = bat(species, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            s0, s1, s2 = species.split("+")
            v0 = v.xs(s0, axis=1, level="S")
            v1 = v.xs(s1, axis=1, level="S")
            v2 = v.xs(s2, axis=1, level="S")

            # Check dv s0,stot case.
            dv = v0.subtract(vcom, axis=1)
            s0s1 = ",".join([s0, species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s1,stot case.
            dv = v1.subtract(vcom, axis=1)
            s0s1 = ",".join([s1, species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s2,stot case.
            dv = v2.subtract(vcom, axis=1)
            s0s1 = ",".join([s2, species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s0+s1,stot case.
            tks = [s0, s1]
            r0r1 = r.loc[:, tks]
            v0v1 = (
                v.loc[:, pd.IndexSlice[tkc, tks]]
                .multiply(r0r1, axis=1)
                .sum(axis=1, level="C")
                .divide(r0r1.sum(axis=1), axis=0)
            )
            dv = v0v1.subtract(vcom, axis=1)
            s0s1 = ",".join(["{}+{}".format(*tks), species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s1+s2,stot case.
            tks = [s1, s2]
            r0r1 = r.loc[:, tks]
            v0v1 = (
                v.loc[:, pd.IndexSlice[tkc, tks]]
                .multiply(r0r1, axis=1)
                .sum(axis=1, level="C")
                .divide(r0r1.sum(axis=1), axis=0)
            )
            dv = v0v1.subtract(vcom, axis=1)
            s0s1 = ",".join(["{}+{}".format(*tks), species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check dv s0+s2,stot case.
            tks = [s0, s2]
            r0r1 = r.loc[:, tks]
            v0v1 = (
                v.loc[:, pd.IndexSlice[tkc, tks]]
                .multiply(r0r1, axis=1)
                .sum(axis=1, level="C")
                .divide(r0r1.sum(axis=1), axis=0)
            )
            dv = v0v1.subtract(vcom, axis=1)
            s0s1 = ",".join(["{}+{}".format(*tks), species])
            alf_turb = AlfvenicTurbulence(
                dv, b, rtot, s0s1, window=test_window, min_periods=test_periods
            )
            built = bat(s0s1, window=test_window, min_periods=test_periods)
            self.assertEqual(alf_turb, built)

            # Check bad species
            for bad_species in ("a,p1,p2", "a+p1,p1+p2,a+p2"):
                with self.assertRaises(ValueError):
                    bat(bad_species)
        else:
            msg = "Unexpected number of species in test case\nslist: %s"
            raise NotImplementedError(msg % (slist))

    @unittest.skip("Not yet implemented")
    def test_drop_species(self):
        print_inline_debug_info = True  # noqa: F841

        slist = list(self.stuple)
        if len(slist) == 1:
            msg = "Must have >1 species. Can't have empty plasma."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.drop_species(*slist)
            return None  # Exit test.

        combos = []
        for i in np.arange(1, len(slist) + 1):
            combos += list(itertools.combinations(slist, i))
        combos.sort(key=len)

        data = self.data  # noqa: F841
        for c in combos:
            raise NotImplementedError


#####
# Tests
#####
class TestPlasmaAlpha(base.AlphaTest, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            "a+p1",
            "p1",
            "p2",
            ("a", "p1"),
            ("a", "p1", "p2"),
            ("p1", "p2"),
            "a+p1+p2",
            "p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaP1(base.P1Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            "a+p1",
            "a",
            "p2",
            ("a", "p1"),
            ("a", "p1", "p2"),
            ("p1", "p2"),
            "a+p1+p2",
            "p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaP2(base.P2Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            "a+p1",
            "a",
            "p1",
            ("a", "p2"),
            ("a", "p1", "p2"),
            ("p1", "p2"),
            "a+p1+p2",
            "p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaAlphaP1(base.AlphaP1Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            ("a", "p2"),
            ("a", "e"),
            ("p2", "e"),
            ("a", "p1", "p2"),
            ("p1", "p2"),
            "a+p1+p2",
            "p1+p2",
            "a+e+p1+p2",
            "e+p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaAlphaP2(base.AlphaP2Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            ("a", "p1"),
            ("a", "e"),
            ("p2", "e"),
            ("a", "p1", "p2"),
            ("p1", "p2"),
            "a+p1+p2",
            "p1+p2",
            "a+e+p1+p2",
            "e+p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaP1P2(base.P1P2Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            "a",
            ("a", "p2"),
            ("a", "e"),
            ("p2", "e"),
            ("a", "p1", "p2"),
            "a+p1+p2",
            "a+e+p1+p2",
            "e+p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


class TestPlasmaAlphaP1P2(base.AlphaP1P2Test, PlasmaTestBase, base.SWEData):
    def test_chk_species_fail(self):
        r"""
        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        bad_species = [
            "a+e",
            "a+e",
            "e",
            ("e", "p1"),
            ("a", "p1", "p2", "e"),
            ("p1", "p2", "e"),
            "a+e+p1+p2",
            "e+p1+p2",
        ]
        for s in bad_species:
            with self.assertRaisesRegex(ValueError, "Requested species unavailable."):
                if isinstance(s, str):
                    s = [s]
                self.object_testing._chk_species(*s)


if __name__ == "__main__":

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

    try:
        run_this_test = "TestPlasmaP1P2"
        run_this_test = None
        unittest.main(verbosity=2, defaultTest=run_this_test)
        # unittest.main()

    except (  # noqa: F841
        AssertionError,
        AttributeError,
        ValueError,
        TypeError,
        IndexError,
    ) as e:
        import traceback as tb

        exc_info = sys.exc_info()
        tb.print_exception(*exc_info)
        pdb.post_mortem(exc_info[-1])
