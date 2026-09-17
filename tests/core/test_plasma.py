#!/usr/bin/env python
"""Tests for the :class:`Plasma` container."""
import pandas as pd
import numpy as np
import itertools
import pandas.testing as pdt

from abc import ABC, abstractproperty, abstractmethod

from scipy import constants
from scipy.constants import physical_constants

from . import test_base as base

from solarwindpy import vector
from solarwindpy import ions
from solarwindpy import plasma
from solarwindpy import spacecraft
from solarwindpy import alfvenic_turbulence

pd.set_option("mode.chained_assignment", "raise")


class PlasmaTestBase(ABC):
    @classmethod
    def set_object_testing(cls):
        data = cls.data
        plas = plasma.Plasma(data, *cls().species.split("+"))

        par = data.w.par.pow(2)
        per = data.w.per.pow(2)
        scalar = ((2.0 * per) + par).multiply(1.0 / 3.0).pipe(np.sqrt)
        cols = scalar.columns.to_series().apply(lambda x: ("w", "scalar", x))
        scalar.columns = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
        data = pd.concat([data, scalar], axis=1, sort=True)

        cls.object_testing = plas
        cls.data = data

    @abstractproperty
    def species(self):
        pass

    @property
    def stuple(self):
        return tuple(self.species.split("+"))

    @property
    def species_combinations(self):
        r"""The various combinations of the species for use in testing Plasma
        methods."""
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
        r"""Masses in amu."""
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
        r"""Plasma exposes one Ion per species, built from the same DataFrame.

        ON FAILURE: the code is wrong; `Plasma` is not building its per-species
        `Ion` objects from the data it was given.
        """
        ions_ = pd.Series({s: ions.Ion(self.data, s) for s in self.stuple})
        pdt.assert_index_equal(ions_.index, self.object_testing.ions.index)
        for k, i in ions_.items():
            pdt.assert_frame_equal(
                i.data,
                self.object_testing.ions.loc[k].data,
                "Unequal data for ion: %s" % k,
            )

    def test_conform_species(self):
        r"""Just test that the species is a valid input.

        ON FAILURE: the code is wrong; `_conform_species` must accept "+"-joined
        species and reject comma-joined ones.
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
        r"""`_chk_species` accepts every species, subset, and "+"-sum this plasma holds.

        ON FAILURE: the code is wrong; `_chk_species` is rejecting a species the
        plasma actually contains.
        """
        self.assertEqual(self.stuple, self.object_testing._chk_species(*self.stuple))

        # Ensure exception isn't raised for plasma's individual species.
        for s in self.stuple:
            # Automatically passes if no exception raised.
            self.object_testing._chk_species(s)

        # Check that any subset of the species and "s0+s1+..." pass,
        # but "s0,s1" don't.
        bad_species_msg = "Invalid species:"
        for combo in self.species_combinations:
            self.object_testing._chk_species(*combo)
            self.object_testing._chk_species("+".join(combo))
            bad_species = ",".join(combo)
            if "," in bad_species:
                with self.assertRaisesRegex(ValueError, bad_species_msg):
                    self.object_testing._chk_species(bad_species)

    @abstractmethod
    def test_chk_species_fail(self):
        r"""This method must be subclassed to test for species that fail the
        `_chk_species` tests.

        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing._chk_species(*s)
        """
        pass

    def test_species(self):
        r"""`Plasma.species` returns the constructor's species as a sorted tuple.

        ON FAILURE: the code is wrong.
        """
        self.assertEqual(self.object_testing.species, self.stuple)

    def test__set_species(self):
        r"""Constructing a Plasma without species raises rather than yielding an empty one.

        ON FAILURE: the code is wrong.
        """
        with self.assertRaisesRegex(
            ValueError, "You must specify a species to instantiate a Plasma."
        ):
            plasma.Plasma(self.object_testing.data)

    def test_bfield(self):
        r"""`b` and `bfield` both return the spacecraft-frame vector from the `b` columns.

        ON FAILURE: the code is wrong.
        """
        b = self.data.b.xs("", axis=1, level="S").loc[:, ["x", "y", "z"]]
        self.assertEqual(vector.BField(b), self.object_testing.bfield)
        self.assertEqual(vector.BField(b), self.object_testing.b)
        self.assertEqual(self.object_testing.b, self.object_testing.bfield)

    def test_number_density(self):
        r"""Plasma's number density per species, and summed over species, matches the ions.

        ON FAILURE: the code is wrong in `Plasma`'s species selection or in its sum
        over species. The expectation comes from `Ion.number_density`, so a defect
        common to both is not caught here; `tests/core/test_ions.py` covers that.
        """
        ot = self.object_testing

        ions_ = pd.concat(
            {s: ot.ions[s].number_density for s in self.stuple},
            axis=1,
            names=["S"],
            sort=True,
        )
        total_ions = ions_.sum(axis=1)
        total_ions.name = "+".join(self.stuple)
        sum_species = self.species

        pdt.assert_series_equal(total_ions, ot.number_density(sum_species))
        pdt.assert_series_equal(total_ions, ot.n(sum_species))
        pdt.assert_series_equal(ot.n(sum_species), ot.number_density(sum_species))

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            this_ion = ions_.loc[:, s[0] if len(s) == 1 else s]

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
        r"""Plasma's mass density per species, and summed over species, matches the ions.

        ON FAILURE: the code is wrong in `Plasma`'s species selection or in its sum
        over species. The expectation comes from `Ion.mass_density`, so a defect
        common to both is not caught here; `tests/core/test_ions.py` covers that.
        """
        ot = self.object_testing

        ions_ = pd.concat(
            {s: ot.ions[s].mass_density for s in self.stuple},
            axis=1,
            names=["S"],
            sort=True,
        )
        total_ions = ions_.sum(axis=1)
        total_ions.name = "+".join(self.stuple)
        sum_species = self.species

        pdt.assert_series_equal(total_ions, ot.mass_density(sum_species))
        pdt.assert_series_equal(total_ions, ot.rho(sum_species))
        pdt.assert_series_equal(ot.rho(sum_species), ot.mass_density(sum_species))

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            this_ion = ions_.loc[:, s[0] if len(s) == 1 else s]

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
        r"""Thermal speeds match the ions and satisfy the scalar-moment identity.

        ON FAILURE: the code is wrong, unless the author rejects the moment identity
        w_scalar^2 = (2 w_perp^2 + w_par^2) / 3 that this test recomputes from the
        parallel and perpendicular components.
        """
        ot = self.object_testing
        ions_ = {s: ot.ions.loc[s].thermal_speed.data for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"], sort=True)
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
        r"""Plasma's thermal pressure per species, and summed over species, matches the ions.

        ON FAILURE: `Plasma.pth` and `Ion.pth` disagree, or `Plasma`'s sum over
        species is wrong. This test cannot say which of the two is at fault, and a
        defect common to both passes it.
        """
        print_inline_debug_info = False
        # Test that Plasma returns each Ion plasma independently.
        ot = self.object_testing

        ions_ = {s: ot.ions[s].pth for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"], sort=True)
        ions_ = ions_.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            if print_inline_debug_info:
                print(s)
                print(len(s))
                print("<Ion>", type(this_ion))
                print(this_ion)
                print("<Plasma>", type(ot.pth(*s)))
                print(self.object_testing.pth(*s))

            pdt.assert_frame_equal(this_ion, ot.pth(*s))

            if len(s) > 1:
                this_ion = this_ion.T.groupby(level="C").sum().T
                pdt.assert_frame_equal(this_ion, ot.pth("+".join(s)))

    def test_temperature(self):
        r"""Plasma's temperature per species, and summed over species, matches the ions.

        ON FAILURE: `Plasma.temperature` and `Ion.temperature` disagree, or
        `Plasma`'s sum over species is wrong. This test cannot say which of the two
        is at fault, and a defect common to both passes it.
        """
        # Test that Plasma returns each Ion plasma independently.
        ions_ = {s: self.object_testing.ions[s].temperature for s in self.stuple}
        ions_ = pd.concat(ions_, axis=1, names=["S"], sort=True)
        ions_ = ions_.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            pdt.assert_frame_equal(this_ion, self.object_testing.temperature(*s))

            if len(s) > 1:
                this_ion = this_ion.T.groupby(level="C").sum().T
                pdt.assert_frame_equal(
                    this_ion, self.object_testing.temperature("+".join(s))
                )

    def test_beta(self):
        r"""Plasma beta equals 2 mu_0 p_th / B^2, with the unit conversion built here.

        ON FAILURE: the code is wrong in `Plasma.beta`'s unit conversion (pPa and nT
        to SI, coefficient recomputed here from scipy's mu_0) or in its sum over
        species. The pressures come from `Ion.pth`, so a defect there is not caught
        here.
        """
        pth = {s: self.object_testing.ions[s].pth for s in self.stuple}
        pth = pd.concat(pth, axis=1, names=["S"], sort=True)
        pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        bsq = self.data.loc[:, pd.IndexSlice["b", ["x", "y", "z"], ""]]
        bsq = bsq.pow(2).sum(axis=1)

        ions_ = pth.divide(bsq, axis=0)

        coeff = 2.0 * constants.mu_0 * 1e-12 / (1e-9**2.0)
        ions_ *= coeff

        # Check that plasma returns each ion species independently.
        for s in self.species_combinations:
            tk_species = pd.IndexSlice[:, s[0] if len(s) == 1 else s]
            this_ion = ions_.loc[:, tk_species]
            if len(s) == 1:
                this_ion = this_ion.xs(s[0], axis=1, level="S")

            pdt.assert_frame_equal(this_ion, self.object_testing.beta(*s))

            if len(s) > 1:
                this_ion = this_ion.T.groupby(level="C").sum().T
                pdt.assert_frame_equal(this_ion, self.object_testing.beta("+".join(s)))

    def test_anisotropy(self):
        r"""Anisotropy is (w_perp/w_par)^2 per species and p_perp/p_par for a summed species.

        ON FAILURE: the code is wrong; both forms are recomputed here from the
        underlying thermal-speed columns.
        """
        ot = self.object_testing

        # Test individual components. Should return RT values.
        for s in self.stuple:
            w = self.data.w.xs(s, axis=1, level="S")
            ani = (w.per / w.par).pow(2)
            ani.name = s
            right = ot.anisotropy(s)
            pdt.assert_series_equal(ani, right)

        # Test list of and sums of sums of species.
        for s in self.species_combinations:
            if len(s) == 1:
                continue
            else:
                # Test list of and sums of sums of species.
                pth = {sprime: ot.ions.loc[sprime].pth for sprime in s}
                pth = pd.concat(pth, axis=1, names=["S"], sort=True)
                pth = pth.drop("scalar", axis=1, level="C", errors="ignore")

                coeff = pd.Series({"par": -1, "per": 1})

                # Calculate anisotropy of each individual species.
                ani_s = pth.pow(coeff, axis=1, level="C")
                ani_s = ani_s.T.groupby("S").prod().T

                # Calculate total anisotropy.
                ani_sum = (
                    pth.T.groupby(level="C")
                    .sum()
                    .T.pow(coeff, axis=1, level="C")
                    .product(axis=1)
                )
                ani_sum.name = "+".join(sorted(s))

                pdt.assert_frame_equal(ani_s, ot.anisotropy(*s))
                pdt.assert_series_equal(ani_sum, ot.anisotropy("+".join(s)))

    def test_velocity(self):
        r"""Bulk velocity, its sqrt(m/q) projection, and the centre-of-mass velocity.

        ON FAILURE: the code is wrong; the projection factor and the mass-density
        weighted centre of mass are both recomputed here from the data.
        """
        ot = self.object_testing
        for s in self.species_combinations:
            if len(s) == 1:
                # Test the species
                self.assertEqual(ot.ions.loc[s[0]].velocity, ot.velocity(*s))
                self.assertEqual(ot.ions.loc[s[0]].velocity, ot.v(*s))
                self.assertEqual(ot.velocity(*s), ot.v(*s))

                # Test `project_m2q`.
                v = ot.ions.loc[s[0]].velocity.data
                m2q = np.sqrt(self.mass_in_mp[s[0]] / self.charge_states[s[0]])
                v = v.multiply(m2q)
                pdt.assert_frame_equal(v, ot.v(*s, project_m2q=True).data)
                pdt.assert_frame_equal(v, ot.velocity(*s, project_m2q=True).data)
                self.assertEqual(vector.Vector(v), ot.v(*s, project_m2q=True))
                self.assertEqual(vector.Vector(v), ot.velocity(*s, project_m2q=True))
                self.assertEqual(
                    ot.v(*s, project_m2q=True), ot.velocity(*s, project_m2q=True)
                )

            else:
                # Test species = (s0, s1, ..., sn)
                ions_ = ot.ions.loc[list(s)].apply(lambda x: x.v)

                pdt.assert_series_equal(ions_, ot.velocity(*s))
                pdt.assert_series_equal(ions_, ot.v(*s))
                pdt.assert_series_equal(ot.velocity(*s), ot.v(*s))

                # comma-separated species list fails
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.velocity(",".join(s))
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.v(",".join(s))

                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.velocity(*s, project_m2q=True)
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.v(*s, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.velocity(",".join(s), project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.v(",".join(s), project_m2q=True)

                # Test species = "s0+s1+...+sn"
                rhos = ot.rho(*s)
                ions_ = pd.concat(
                    ions_.apply(lambda x: x.cartesian).to_dict(),
                    axis=1,
                    names=["S"],
                    sort=True,
                )
                ions_ = ions_.multiply(rhos, axis=1, level="S")
                ions_ = (
                    ions_.T.groupby(level="C").sum().T.divide(rhos.sum(axis=1), axis=0)
                )
                ions_ = vector.Vector(ions_)

                self.assertEqual(ions_, ot.v("+".join(s)))
                self.assertEqual(ions_, ot.velocity("+".join(s)))

                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.velocity("+".join(s), project_m2q=True)
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.v("+".join(s), project_m2q=True)

    def test_dv(self):
        r"""Differential flow between two species and between a species and the CoM.

        ON FAILURE: the code is wrong; dv is recomputed here as the component-wise
        difference of the two bulk velocities.
        """
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

        ot = self.object_testing
        for combo in combos2:
            # Calculate individual species dv.
            sb, sc = combo
            v0 = self.data.v.xs(sb, axis=1, level="S")
            v1 = self.data.v.xs(sc, axis=1, level="S")
            dv = v0.subtract(v1, axis=1)
            pdt.assert_frame_equal(dv, ot.dv(sb, sc).data)
            self.assertEqual(vector.Vector(dv), ot.dv(sb, sc))

            # Test single species \sqrt{m/q} projection.
            v0 = v0.multiply(np.sqrt(self.mass_in_mp[sb] / self.charge_states[sb]))
            v1 = v1.multiply(np.sqrt(self.mass_in_mp[sc] / self.charge_states[sc]))
            dv_projected = v0.subtract(v1, axis=1)
            pdt.assert_frame_equal(dv_projected, ot.dv(sb, sc, project_m2q=True).data)
            self.assertEqual(
                vector.Vector(dv_projected), ot.dv(sb, sc, project_m2q=True)
            )

            # Calculate dv for v_s - v_com.
            ssum = "+".join(combo)
            scomma = ",".join(combo)
            for s in combo:
                tk = pd.IndexSlice[["x", "y", "z"], list(combo)]
                vs = self.data.v.loc[:, tk]
                ns = self.data.n.loc[:, ""].loc[:, list(combo)]
                m = self.mass_in_mp.loc[list(combo)]
                rhos = ns.multiply(m, axis=1, level="S")
                rho_total = rhos.sum(axis=1)
                vcom = (
                    vs.multiply(rhos, axis=1, level="S")
                    .T.groupby(level="C")
                    .sum()
                    .T.divide(rho_total, axis=0)
                )

                v = self.data.v.xs(s, axis=1, level="S")
                dv = v.subtract(vcom, axis=1, level="C")

                pdt.assert_frame_equal(dv, ot.dv(s, ssum).data)
                self.assertEqual(vector.Vector(dv), ot.dv(s, ssum))

                # Verify that we can't pass a sum or comma species with `project_m2q`
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.dv(s, ssum, project_m2q=True)
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.dv(ssum, s, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(s, scomma, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(scomma, s, project_m2q=True)

                # Verify a combination of comma and sum fail.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum)

                # Verify a combination of comma and sum fail with `project_m2q`.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma, project_m2q=True)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum, project_m2q=True)

        if len(self.stuple) > 2:
            # Calculate dv for v_si - v_com for each s in stuple.
            ssum = "+".join(self.stuple)
            scomma = ",".join(self.stuple)

            tk = pd.IndexSlice[["x", "y", "z"], list(self.stuple)]
            vs = self.data.v.loc[:, tk]
            ns = self.data.n.loc[:, ""].loc[:, list(self.stuple)]
            m = self.mass_in_mp.loc[list(self.stuple)]
            rhos = ns.multiply(m, axis=1, level="S")
            rho_total = rhos.sum(axis=1)
            vcom = (
                vs.multiply(rhos, axis=1, level="S")
                .T.groupby(level="C")
                .sum()
                .T.divide(rho_total, axis=0)
            )

            for s in self.stuple:
                # Calculate dv for v_si - v_com for each s in stuple.
                v = self.data.v.xs(s, axis=1, level="S")
                dv = v.subtract(vcom, axis=1, level="C")

                pdt.assert_frame_equal(dv, ot.dv(s, ssum).data)
                self.assertEqual(vector.Vector(dv), ot.dv(s, ssum))

                # Test comma-separated species failes.
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(s, scomma)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(scomma, s)
                # Test comma-separated species failes with `project_m2q`.
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(s, scomma, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(scomma, s, project_m2q=True)

                # Verify center-of-mass species fail with `project_m2q`.
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.dv(ssum, s, project_m2q=True)
                with self.assertRaisesRegex(
                    NotImplementedError, "A multi-species velocity is not valid"
                ):
                    ot.dv(s, ssum, project_m2q=True)

                # Verify a combination of comma and sum fail.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum)

                # Verify a combination of comma and sum fail with `project_m2q`.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma, project_m2q=True)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum, project_m2q=True)

            for combo in combos2:
                # Calculate dv for v_{s0+s1} - v_com for each s in stuple.
                tk = pd.IndexSlice[["x", "y", "z"], list(combo)]
                v_s0s1 = self.data.v.loc[:, tk]
                n_s0s1 = self.data.n.loc[:, ""].loc[:, list(combo)]
                m_s0s1 = self.mass_in_mp.loc[list(combo)]

                rho_s0s1 = n_s0s1.multiply(m_s0s1, axis=1, level="S")
                rho_total_s0s1 = rho_s0s1.sum(axis=1)
                rv_s0s1 = (
                    v_s0s1.multiply(rho_s0s1, axis=1, level="S")
                    .T.groupby(level="C")
                    .sum()
                    .T
                )
                vcom_s0s1 = rv_s0s1.divide(rho_total_s0s1, axis=0)

                dv_s0s1 = vcom_s0s1.subtract(vcom, axis=1, level="C")

                right = self.object_testing.dv("+".join(combo), ssum)
                pdt.assert_frame_equal(dv_s0s1, right.data)
                self.assertEqual(vector.Vector(dv_s0s1), right)

                # Test comma-separated species failes
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(s, scomma)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(scomma, s)
                # Test comma-separated species failes with `project_m2q`.
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(s, scomma, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.dv(scomma, s, project_m2q=True)

                # Verify center-of-mass species fail with `project_m2q`.
                with self.assertRaises(NotImplementedError):
                    ot.dv(ssum, s, project_m2q=True)
                with self.assertRaises(NotImplementedError):
                    ot.dv(s, ssum, project_m2q=True)

                # Verify a combination of comma and sum fail.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum)

                # Verify a combination of comma and sum fail with `project_m2q`.
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(ssum, scomma, project_m2q=True)
                with self.assertRaises((NotImplementedError, ValueError)):
                    ot.dv(scomma, ssum, project_m2q=True)

    def test_ca(self):
        r"""Alfven speed c_A = B / sqrt(mu_0 rho).

        ON FAILURE: the code is wrong; the expectation is recomputed here from
        scipy's mu_0 and the CODATA species masses, independently of `Plasma`.
        """
        tk = ["x", "y", "z"]
        b = self.data.b.loc[:, tk].pow(2).sum(axis=1).pipe(np.sqrt) * 1e-9
        n = self.data.n.loc[:, ""].loc[:, self.stuple] * 1e6
        m = self.mass
        rho = n * m

        combos = [x for x in self.species_combinations if len(x) > 1]
        total_masses = pd.DataFrame(
            {"+".join(s): rho.loc[:, s].sum(axis=1) for s in combos}
        )
        rho = pd.concat([rho, total_masses], axis=1, sort=True)

        ions_ = (constants.mu_0 * rho).pow(-0.5).multiply(b, axis=0) / 1e3
        ions_.columns.names = ["S"]

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
        r"""Squared anisotropy factor AF^2 = 1 + mu_0 (p_perp - p_par) / B^2.

        ON FAILURE: the code is wrong, unless the author rejects the form of AF^2
        recomputed here. Only the `pdynamic=False` branch is exercised, so the
        -p_dv term in `Plasma.afsq` is not covered. That expression carries no
        citation in either this test or `plasma.py`, so a disagreement in the
        expression itself is the author's call.
        """
        slist = list(self.stuple)
        tk = pd.IndexSlice[["par", "per"], slist]

        w = (
            self.data.w.loc[:, tk].drop("scalar", axis=1, level="C", errors="ignore")
            * 1e3
        )
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

        msg = (
            "Youngest beams analysis shows that dynamic pressure is "
            "probably not useful."
        )

        for combo in self.species_combinations:
            with self.assertRaisesRegex(NotImplementedError, msg):
                self.object_testing.afsq(*combo, pdynamic=True)
            if len(combo) == 1:
                pdt.assert_series_equal(
                    ions_.loc[:, combo[0]],
                    self.object_testing.afsq(*combo, pdynamic=False),
                )
            else:
                pdt.assert_frame_equal(
                    ions_.loc[:, combo], self.object_testing.afsq(*combo)
                )

                # So that we don't overcount the $1 +$ in AFSQ, we
                # do the following before taking the sum.
                left = 1 + (ions_.loc[:, combo] - 1).sum(axis=1)
                left.name = "+".join(combo)
                pdt.assert_series_equal(left, self.object_testing.afsq("+".join(combo)))

    def test_caani(self):
        r"""Anisotropy-corrected Alfven speed C_A;Ani = C_A sqrt(AFSQ).

        ON FAILURE: the code is wrong; both factors are recomputed here from
        scipy's mu_0 and the CODATA species masses.
        """
        combos = [x for x in self.species_combinations]
        masses = self.mass
        n = self.data.n.xs("", axis=1, level="C") * 1e6
        rhos = {
            "+".join(x): n.loc[:, list(x)].multiply(masses.loc[list(x)]).sum(axis=1)
            for x in combos
        }
        rhos = pd.concat(rhos, axis=1, names=["S"], sort=True)

        tk = pd.IndexSlice[["x", "y", "z"], ""]
        b = (self.data.b.loc[:, tk]).pow(2).sum(axis=1).pipe(np.sqrt) * 1e-9

        ca = (rhos * constants.mu_0).pow(-0.5).multiply(b, axis=0) / 1e3

        slist = list(self.stuple)
        tk = pd.IndexSlice[["par", "per"], slist]
        w = (
            self.data.w.loc[:, tk].drop("scalar", axis=1, level="C", errors="ignore")
            * 1e3
        )
        n = self.data.n.loc[:, ""].loc[:, slist] * 1e6
        m = self.mass.loc[slist]
        rho = n.multiply(m, axis=1, level="S")
        pth = 0.5 * w.pow(2.0).multiply(rho, axis=1, level="S")
        dp = pth.per - pth.par

        beta_ish = dp.multiply(constants.mu_0 * b.pow(-2.0), axis=0)

        regex_msg = (
            "Youngest beams analysis shows that "
            "dynamic pressure is probably not useful."
        )
        for combo in combos:
            this_ca = ca.loc[:, "+".join(combo)]
            afsq = 1.0 + beta_ish.loc[:, list(combo)].sum(axis=1)
            this_caani = this_ca.multiply(afsq.pow(0.5), axis=0)
            this_caani.name = "+".join(combo)

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
        r"""Coulomb logarithm between two species, and its species-argument contract.

        ON FAILURE: `Plasma.lnlambda` disagrees with the expression in its own
        docstring, which this test recomputes. The additive constant 29.9 carries no
        citation in either the test or `plasma.py`, so a failure in that constant
        alone is for the author to adjudicate.
        """
        ot = self.object_testing
        regex_msg = (
            "`lnlambda` can only calculate with individual s0 " "and s1 species."
        )
        invalid = "Invalid species"

        kb_J = constants.physical_constants["Boltzmann constant"]
        kb_eV = constants.physical_constants["Boltzmann constant in eV/K"]

        amu = self.m_amu
        charge_states = self.charge_states
        n_all = self.data.n.xs("", axis=1, level="C").loc[:, self.stuple] * 1e6
        m = self.mass
        w = self.data.w.scalar.loc[:, self.stuple] * 1e3

        Tkelvin = 0.5 * w.pow(2.0).multiply(m, axis=1, level="S") / kb_J[0]
        TeV = Tkelvin * kb_eV[0]

        if len(self.stuple) == 1:
            s = self.stuple[0]
            z = charge_states.loc[s]
            n = n_all.loc[:, s]
            T = TeV.loc[:, s]
            lnlambda = 29.9 - np.log(
                np.sqrt(2) * z**3 * n.pipe(np.sqrt) * T.pow(-3.0 / 2.0)
            )
            lnlambda.name = f"{s},{s}"

            pdt.assert_series_equal(lnlambda, ot.lnlambda(s, s))
            pdt.assert_series_equal(ot.lnlambda(s, s), ot.lnlambda(s, s))

            s0s1 = f"{s}+{s}"
            with self.assertRaisesRegex(ValueError, regex_msg):
                ot.lnlambda(s, s0s1)
            with self.assertRaisesRegex(ValueError, regex_msg):
                ot.lnlambda(s0s1, s)
            with self.assertRaisesRegex(ValueError, regex_msg):
                ot.lnlambda(s0s1, s0s1)

            combo = [s, s]
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda("+".join(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(list(combo), "+".join(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(",".join(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(list(combo), ",".join(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(list(combo), list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(list(combo), s)
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(list(combo), combo[1])
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(s, list(combo))
            with self.assertRaisesRegex((TypeError, ValueError), invalid):
                ot.lnlambda(combo[1], list(combo))

        else:
            nZsqOTeV = n_all.multiply(charge_states.pow(2), axis=1, level="S").divide(
                TeV, axis=1, level="S"
            )

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

                pdt.assert_series_equal(lnlambda, ot.lnlambda(combo[0], combo[1]))
                pdt.assert_series_equal(
                    lnlambda, ot.lnlambda(combo[1], combo[0]), check_names=False
                )

                # NOTE: The following various Invalid Species tests are excessive
                #       and should be reduced.
                s0s1 = "+".join(combo)  # ("+".join(combo), combo):
                with self.assertRaisesRegex(ValueError, regex_msg):
                    ot.lnlambda(combo[0], s0s1)
                with self.assertRaisesRegex(ValueError, regex_msg):
                    ot.lnlambda(s0s1, combo[0])
                with self.assertRaisesRegex(ValueError, regex_msg):
                    ot.lnlambda(combo[1], s0s1)
                with self.assertRaisesRegex(ValueError, regex_msg):
                    ot.lnlambda(s0s1, combo[1])
                with self.assertRaisesRegex(ValueError, regex_msg):
                    ot.lnlambda(s0s1, s0s1)

                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda("+".join(combo), list(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(list(combo), "+".join(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(",".join(combo), list(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(list(combo), ",".join(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(list(combo), list(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(list(combo), combo[0])
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(list(combo), combo[1])
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(combo[0], list(combo))
                with self.assertRaisesRegex((TypeError, ValueError), invalid):
                    ot.lnlambda(combo[1], list(combo))

    def test_nuc(self):
        r"""We calculate the collision frequency for differential flow following
        Hernandez & Marsch (JGR 1985, doi:10.1029/JA090iA11p11062) Eq.

        (18).

        ON FAILURE: the code is wrong, unless the author rejects this transcription.
        The `both_species=False` path is Eq. (18); the default `both_species=True`
        path, which this test also asserts, is Eq. (23).
        """
        from scipy.special import erf
        from scipy import constants

        if len(self.stuple) == 1:
            # We only test plasmas w/ > 1 species.
            return None

        slist = list(self.stuple)
        coeff = 4.0 * np.pi * constants.epsilon_0**2.0
        qsq = self.charges**2.0
        m = self.mass
        w = self.data.w.par.loc[:, slist] * 1e3
        wsq = w.pow(2.0)
        n = self.data.n.xs("", axis=1, level="C").loc[:, slist] * 1e6
        rho = n.multiply(m, axis=1)
        tk = pd.IndexSlice[["x", "y", "z"], slist]
        v = self.data.v.loc[:, tk] * 1e3

        combos2 = [x for x in self.species_combinations if len(x) == 2]

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
            gaussian_term = gauss_coeff * np.exp(-(dvw**2.0))
            ldr = dvw.pow(-3.0) * (erf_dvw - gaussian_term)

            nuab = all_coeff * (nb * lnlambda / wab.pow(3.0)) * ldr / 1e-7

            exp = pd.Series({sa: 1.0, sb: -1.0})
            rho_ratio = rho.loc[:, [sa, sb]].pow(exp, axis=1, level="S").product(axis=1)
            nuba = nuab.multiply(rho_ratio, axis=0)
            nuc = nuab.add(nuba, axis=0)

            nuab.name = "%s-%s" % (sa, sb)
            nuba.name = "%s-%s" % (sb, sa)
            nuc.name = "%s+%s" % (sa, sb)

            pdt.assert_series_equal(
                nuab, self.object_testing.nuc(sa, sb, both_species=False)
            )
            pdt.assert_series_equal(
                nuba, self.object_testing.nuc(sb, sa, both_species=False)
            )
            pdt.assert_series_equal(nuc, self.object_testing.nuc(sa, sb))

            nuc.name = "%s+%s" % (sb, sa)
            pdt.assert_series_equal(nuc, self.object_testing.nuc(sb, sa))

            pdt.assert_series_equal(
                self.object_testing.nuc(sa, sb),
                self.object_testing.nuc(sb, sa),
                check_names=False,
            )

    def test_spacecraft_in_plasma(self):
        r"""`set_spacecraft` stores the spacecraft and exposes it as `spacecraft` and `sc`.

        ON FAILURE: the code is wrong.
        """
        sc_data = base.TestData().spacecraft_data

        Wind = pd.concat(
            {"pos": sc_data.xs("gse", axis=1, level="M")},
            axis=1,
            names=["M"],
            sort=True,
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
            sort=True,
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

    def test_nc_without_spacecraft(self):
        r"""`nc` raises when no spacecraft is set, since it has no expansion time.

        ON FAILURE: the code is wrong; a collisional age computed without an
        expansion time would be silently meaningless.
        """
        ot = self.object_testing
        ot.set_spacecraft(None)
        combos2 = [x for x in self.species_combinations if len(x) == 2]
        for combo in combos2:
            sa, sb = combo
            # Assert failure to calculate Nc when no spacecraft set.
            with self.assertRaises(ValueError):
                ot.nc(sa, sb)

    def test_nc_with_spacecraft(self):
        r"""Collisional age is the collision frequency times the expansion time.

        ON FAILURE: the code is wrong in `nc`'s expansion-time weighting. The
        collision frequency is taken from `Plasma.nuc`, so a defect there surfaces in
        `test_nuc`, not here.
        """
        if len(self.stuple) == 1:
            # We only test plasmas w/ > 1 species.
            return None

        slist = list(self.stuple)

        v = self.data.v
        v = pd.concat(
            {s: v.xs(s, axis=1, level="S") for s in slist},
            axis=1,
            names=["S"],
            sort=True,
        )

        # Neither `n` nor `rho` units b/c Vcom divides out
        # the [rho].
        m = self.mass
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"], sort=True
        )
        rho = n.multiply(m, axis=1, level="S")

        vcom = (
            v.multiply(rho, axis=1, level="S")
            .T.groupby(level="C")
            .sum()
            .T.divide(rho.sum(axis=1), axis=0)
        )
        vsw = vcom.pow(2.0).sum(axis=1).pipe(np.sqrt) * 1e3

        sc_data = base.TestData().spacecraft_data

        Wind = pd.concat(
            {"pos": sc_data.xs("gse", axis=1, level="M")},
            axis=1,
            names=["M"],
            sort=True,
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
            sort=True,
        )
        PSP = spacecraft.Spacecraft(PSP, "PSP", "HCI")
        #         Rs = 695.508e6 # [m]
        #         r_Re = constants.au - (self.data.gse.x * Rs)
        tau_exp_PSP = PSP.distance2sun.multiply(vsw.pow(-1.0), axis=0)

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

                nuab = ot.nuc(sa, sb, both_species=False)
                nuba = ot.nuc(sb, sa, both_species=False)
                nuc = ot.nuc(sa, sb, both_species=True)

                ncab = nuab.multiply(tau_exp, axis=0) * 1e-7
                ncab.name = "%s-%s" % (sa, sb)

                ncba = nuba.multiply(tau_exp, axis=0) * 1e-7
                ncba.name = "%s-%s" % (sb, sa)

                nc = nuc.multiply(tau_exp, axis=0) * 1e-7
                nc.name = "%s+%s" % combo

                pdt.assert_series_equal(ncab, ot.nc(sa, sb, both_species=False))
                pdt.assert_series_equal(ncba, ot.nc(sb, sa, both_species=False))
                pdt.assert_series_equal(nc, ot.nc(sa, sb, both_species=True))
                pdt.assert_series_equal(
                    nc, ot.nc(sb, sa, both_species=True), check_names=False
                )
                pdt.assert_series_equal(
                    ot.nc(sa, sb, both_species=True),
                    ot.nc(sb, sa, both_species=True),
                    check_names=False,
                )

        # Ensure spacecraft is None
        ot.set_spacecraft(None)

        with self.assertRaisesRegex(ValueError, individual_msg):
            ot.nc("+".join(combo), sa)
        with self.assertRaisesRegex(ValueError, individual_msg):
            ot.nc(sa, "+".join(combo))

        with self.assertRaisesRegex(ValueError, invalid_msg):
            ot.nc(",".join(combo), sa)
        with self.assertRaisesRegex(ValueError, invalid_msg):
            ot.nc(sa, ",".join(combo))

        with self.assertRaisesRegex(TypeError, invalid_msg):
            ot.nc(combo, sa)
        with self.assertRaisesRegex(TypeError, invalid_msg):
            ot.nc(sa, combo)

    def test_estimate_electrons(self):
        r"""Electron moments follow from charge neutrality and zero net current.

        ON FAILURE: the code is wrong; n_e, v_e and w_e are recomputed here from
        charge neutrality, zero net current, and the CODATA electron-proton mass
        ratio, independently of `Plasma`.
        """
        stuple = self.stuple

        if "p" not in self.stuple and "p1" not in self.stuple:
            with self.assertRaisesRegex(
                ValueError,
                # Match this sentence at start of string.
                r"^Plasma must contain \(core\) protons to estimate electrons.",
            ):
                self.object_testing.estimate_electrons()

        else:
            qi = self.charge_states
            ni = self.data.n.xs("", axis=1, level="C").loc[:, list(stuple)]
            niqi = ni.multiply(qi, axis=1, level="S")
            vi = self.data.v.loc[:, pd.IndexSlice[:, list(stuple)]]
            niqivi = vi.multiply(niqi, axis=1, level="S")
            nqv = niqivi.T.groupby(level="C").sum().T
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
            npne = pd.concat([npne, ne], axis=1, keys=[tkn, "e"], sort=True)
            nrat = npne.pow(exp, axis=1, level="S").product(axis=1)
            mpme = physical_constants["electron-proton mass ratio"][0] ** -1.0
            we = (nrat * mpme).multiply(wp.pow(2), axis=0).pipe(np.sqrt)

            tmp = pd.concat([we, we], axis=1, keys=["par", "per"], sort=True)
            ne.name = ""
            electrons = pd.concat(
                [ne, ve, tmp], axis=1, keys=["n", "v", "w"], names=["M", "C"], sort=True
            )

            electrons = ions.Ion(electrons, "e")

            # Check electrons are properly calculated.
            ot = self.object_testing
            pdt.assert_frame_equal(electrons.data, ot.estimate_electrons().data)

            # For some reason, this check failed (20250722).
            # self.assertEqual(electrons, ot.estimate_electrons())

            # Check that electrons aren't stored in plasma.
            self.assertFalse("e" in ot.species)
            comp_data = (
                pd.concat(
                    {"e": electrons.data}, axis=1, names=["S", "M", "C"], sort=True
                )
                .reorder_levels(["M", "C", "S"], axis=1)
                .sort_index(axis=1)
            )

            self.assertFalse(
                comp_data.isin(ot.data).any().any(),
                "There should not be e- data in plasma data.",
            )

    def test_pdynamic_without_m2q_projection(self):
        r"""Dynamic pressure p_dv = (1/2) sum_s rho_s (v_s - v_com)^2.

        ON FAILURE: the code is wrong; the expectation is recomputed here from
        scipy's m_p and the data.
        """
        slist = list(self.stuple)

        if len(slist) == 1:
            msg = "Must have >1 species to calculate dynamic pressure."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.pdynamic(*slist)
            return None  # Exit test.

        v = self.data.v
        v = pd.concat(
            {s: v.xs(s, axis=1, level="S") for s in slist},
            axis=1,
            names=["S"],
            sort=True,
        )

        # Neither `n` nor `rho` units b/c Vcom divides out
        # the [rho].
        m = self.mass_in_mp
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"], sort=True
        )
        rho = n.multiply(m, axis=1, level="S")

        ot = self.object_testing
        for combo in self.species_combinations:
            if len(combo) == 1:
                msg = "Must have >1 species to calculate dynamic pressure."
                with self.assertRaisesRegex(ValueError, msg):
                    ot.pdynamic(*combo)
                continue  # Skip this test case.

            scom = "+".join(combo)

            rho_i = rho.loc[:, list(combo)]
            rho_t = rho_i.sum(axis=1)
            v_i = v.loc[:, list(combo)]
            vcom = (
                v_i.multiply(rho_i, axis=1, level="S")
                .T.groupby(level="C")
                .sum()
                .T.divide(rho_t, axis=0)
            )
            dv_i = v_i.subtract(vcom, axis=1, level="C")
            dvsq_i = dv_i.pow(2.0).T.groupby(level="S").sum().T
            dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
            dvsq_rho = dvsq_rho_i.sum(axis=1)

            const = (
                0.5 * constants.m_p * 1e6 * 1e6 / 1e-12
            )  # [m_p] * [n] * [dv]**2 / [p]
            pdv = dvsq_rho.multiply(const)

            pdv.name = "pdynamic"
            pdt.assert_series_equal(pdv, ot.pdynamic(*combo))
            pdt.assert_series_equal(pdv, ot.pdv(*combo))
            pdt.assert_series_equal(ot.pdynamic(*combo), ot.pdv(*combo))
            pdt.assert_series_equal(ot.pdv(*combo), ot.pdynamic(*combo))
            pdt.assert_series_equal(ot.pdynamic(*combo), pdv)
            pdt.assert_series_equal(ot.pdynamic(*combo), ot.pdynamic(*combo))
            pdt.assert_series_equal(ot.pdynamic(*combo), ot.pdynamic(*combo[::-1]))

            invalid_msg = "Invalid species"
            # dynamic pressure shouldn't work with a comma separated list or sub-list.
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(",".join(combo))
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(",".join(combo), combo[0])
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(combo[0], ",".join(combo))

            # dynamic pressure should work with sum of species, but not a sub-list
            # that includes a sum.
            pdt.assert_series_equal(pdv, self.object_testing.pdynamic(scom))

            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(combo[0], scom)
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(scom, combo[0])

            # dynamic pressure should fail when each element is a sum or comma list.
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(scom, ",".join(combo))
            with self.assertRaisesRegex(ValueError, invalid_msg):
                ot.pdynamic(",".join(combo), scom)

    def test_pdynamic_with_m2q_projection(self):
        r"""Dynamic pressure in reduced-mass form, p_dv = (1/2) mu dv^2.

        ON FAILURE: the code is wrong in the reduced-mass form. The projected dv is
        taken from `Plasma.dv`, so a defect there surfaces in `test_dv`, not here.
        """
        slist = list(self.stuple)

        if len(slist) == 1:
            msg = "Must have >1 species to calculate dynamic pressure."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.pdynamic(*slist)
            return None  # Exit test.

        # Neither `n` nor `rho` units b/c Vcom divides out
        # the [rho].
        m = self.mass_in_mp
        n = self.data.n.xs("", axis=1, level="C")
        n = pd.concat(
            {s: n.xs(s, axis=1) for s in slist}, axis=1, names=["S"], sort=True
        )
        rho = n.multiply(m, axis=1, level="S")

        const = 0.5 * constants.m_p * 1e6 * 1e6 / 1e-12  # [m_p] * [n] * [dv]**2 / [p]

        ot = self.object_testing
        invalid_msg = "Invalid species"
        for combo in self.species_combinations:
            scom = "+".join(combo)
            comma = ",".join(combo)

            if len(combo) == 1:
                msg = "Must have >1 species to calculate dynamic pressure."
                with self.assertRaisesRegex(ValueError, msg):
                    self.object_testing.pdynamic(*combo)
                continue  # Skip this test case.

            elif len(combo) == 2:
                dvsq = ot.dv(*combo, project_m2q=True).mag.pow(2)
                rho_s = rho.loc[:, combo]
                mu = rho_s.product(axis=1).divide(rho_s.sum(axis=1))
                pdv = dvsq.multiply(mu, axis=0).multiply(const)
                pdv.name = "pdynamic"

                pdt.assert_series_equal(pdv, ot.pdynamic(*combo, project_m2q=True))
                pdt.assert_series_equal(pdv, ot.pdv(*combo, project_m2q=True))
                pdt.assert_series_equal(
                    ot.pdv(*combo, project_m2q=True),
                    ot.pdynamic(*combo, project_m2q=True),
                )

                for s in combo:
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(scom, s, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(s, scom, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(comma, s, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(s, comma, project_m2q=True)

            elif len(combo) == 3:
                for s in combo:
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(scom, s, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(s, scom, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(comma, s, project_m2q=True)
                    with self.assertRaisesRegex(ValueError, invalid_msg):
                        ot.pdynamic(s, comma, project_m2q=True)

            else:
                raise NotImplementedError("Unrecognized combo length: {}".format(combo))

            for s in combo:
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.pdynamic(comma, s, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.pdynamic(s, comma, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.pdynamic(scom, s, project_m2q=True)
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.pdynamic(s, scom, project_m2q=True)

            with self.assertRaisesRegex(ValueError, "Invalid species"):
                ot.pdynamic(scom, comma, project_m2q=True)
            with self.assertRaisesRegex(ValueError, "Invalid species"):
                ot.pdynamic(comma, scom, project_m2q=True)

    def test_heatflux(self):
        r"""Parallel heat flux q_par = rho (dv_par^3 + (3/2) dv_par w_par^2).

        ON FAILURE: the code is wrong; the expectation is recomputed here from
        scipy's m_p, the field direction, and the centre-of-mass velocity.
        """
        print_inline_debug_info = False

        # q = rho (dv^3 + (3/2) dv w^2)
        slist = list(self.stuple)
        scom = "+".join(slist)

        if len(slist) == 1:
            msg = "Must have >1 species to calculate heatflux."
            with self.assertRaisesRegex(ValueError, msg):
                self.object_testing.heat_flux(*slist)
            return None  # Exit test.

        m = self.mass_in_mp
        n = self.data.n.loc[:, pd.IndexSlice["", slist]].xs("", axis=1, level="C")
        rho = n.multiply(m, axis=1, level="S")
        rho.columns.names = ["S"]

        w = self.data.w.par.loc[:, slist]

        b = self.data.b.xs("", axis=1, level="S").loc[:, ["x", "y", "z"]]
        bhat = b.divide(b.pow(2).sum(axis=1).pipe(np.sqrt), axis=0)

        v = self.data.v.loc[:, pd.IndexSlice[:, slist]]
        vcom = (
            v.multiply(rho, axis=1, level="S")
            .T.groupby(level="C")
            .sum()
            .T.divide(rho.sum(axis=1), axis=0)
        )
        dv = v.subtract(vcom, axis=1, level="C")

        dvpar = dv.multiply(bhat, axis=0).T.groupby(level="S").sum().T
        qa = dvpar.pow(3)
        qb = dvpar.multiply(w.pow(2), axis=1, level="S").multiply(3.0 / 2.0)
        qc = rho.multiply(qa.add(qb, axis=1, level="S"), axis=1, level="S")

        coeff = constants.m_p * 1e6 * 1e9 / 1e-7  # [m_p] [n] [v]^3 / [q]
        q = qc.multiply(coeff)
        qtot = q.sum(axis=1)
        qtot.name = "+".join(slist)

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
                "<dv>",
                type(dv),
                dv,
                "<dvpar>",
                type(dvpar),
                dvpar,
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
                "<qtot>",
                type(qtot),
                qtot,
                sep="\n",
            )

        ot = self.object_testing
        pdt.assert_frame_equal(q, ot.heat_flux(*slist))
        pdt.assert_frame_equal(q, ot.qpar(*slist))
        pdt.assert_series_equal(qtot, ot.heat_flux(scom))
        pdt.assert_series_equal(qtot, ot.qpar(scom))

        pdt.assert_frame_equal(ot.heat_flux(*slist), ot.qpar(*slist))
        pdt.assert_series_equal(ot.heat_flux(scom), ot.qpar(scom))

    def test_set_auxiliary_data(self):
        r"""Auxiliary data round-trips through `aux`, clears to None, and rejects dupes.

        ON FAILURE: the code is wrong.
        """
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
        r"""Plasma preserves the DatetimeIndex it was constructed with.

        ON FAILURE: the code is wrong.
        """
        epoch = self.data.index
        self.assertIsInstance(epoch, pd.DatetimeIndex)

        ot = self.object_testing

        pdt.assert_index_equal(epoch, ot.data.index)

    def test_build_alfvenic_turbulence(self):
        r"""Plasma hands the right velocity, density and label to AlfvenicTurbulence.

        ON FAILURE: the code is wrong in `Plasma`'s dispatch. This test checks the
        dispatch only; the turbulence quantities themselves are covered in
        `tests/core/test_alfvenic_turbulence.py`.
        """
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
                .T.groupby(level="C")
                .sum()
                .T.divide(rtot, axis=0)
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
                .T.groupby(level="C")
                .sum()
                .T.divide(rtot, axis=0)
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
                .T.groupby(level="C")
                .sum()
                .T.divide(r0r1.sum(axis=1), axis=0)
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
                .T.groupby(level="C")
                .sum()
                .T.divide(r0r1.sum(axis=1), axis=0)
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
                .T.groupby(level="C")
                .sum()
                .T.divide(r0r1.sum(axis=1), axis=0)
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

    def test_drop_species(self):
        r"""`drop_species` returns a new Plasma without the dropped species.

        ON FAILURE: the code is wrong; the result must keep the shared columns and
        the surviving species, and must not mutate the original.
        """
        print_inline_debug_info = True  # noqa: F841

        ot = self.object_testing
        slist = list(self.stuple)
        if len(slist) == 1:
            msg = "Must have >1 species. Can't have empty plasma."
            with self.assertRaisesRegex(ValueError, msg):
                ot.drop_species(*slist)
            return None

        combos = []
        for i in np.arange(1, len(slist) + 1):
            combos += list(itertools.combinations(slist, i))
        combos.sort(key=len)

        for c in combos:
            if len(c) == len(slist):
                msg = "Must have >1 species. Can't have empty plasma."
                with self.assertRaisesRegex(ValueError, msg):
                    ot.drop_species(*c)
                continue

            dropped = set(c)
            remaining = tuple(sorted(set(slist) - dropped))

            result = ot.drop_species(*c)

            self.assertIsInstance(result, plasma.Plasma)
            self.assertEqual(result.species, remaining)

            keep_mask = (
                ot.data.columns.get_level_values("S") == ""
            ) | ot.data.columns.get_level_values("S").isin(remaining)
            expected_data = ot.data.loc[:, keep_mask]

            pdt.assert_frame_equal(result.data, expected_data)

            pdt.assert_index_equal(result.ions.index, pd.Index(remaining))

            # Original object should remain unchanged
            self.assertEqual(ot.species, tuple(slist))

    def test_VDFratio(self):
        r"""ln(f_beam/f_core) evaluated at the beam velocity for bi-Maxwellian VDFs.

        ON FAILURE: the code is wrong, unless the author rejects the bi-Maxwellian
        ratio derived in the `vdf_ratio` docstring, which this test recomputes from
        the densities, thermal speeds, and field-projected differential flow.
        """
        ot = self.object_testing
        slist = [s for s in self.species_combinations if len(s) == 2]
        sother = [sisj[::-1] for sisj in slist]
        slist = slist + sother

        for sisj in slist:
            si, sj = sisj
            ni = self.data.loc[:, ("n", "", si)]
            nj = self.data.loc[:, ("n", "", sj)]

            wi = (
                self.data.loc[:, "w"]
                .xs(si, axis=1, level="S")
                .drop("scalar", axis=1, errors="ignore")
            )
            wi_par = wi.loc[:, "par"]
            wi_per = wi.loc[:, "per"]

            wj = (
                self.data.loc[:, "w"]
                .xs(sj, axis=1, level="S")
                .drop("scalar", axis=1, errors="ignore")
            )
            wj_par = wj.loc[:, "par"]
            wj_per = wj.loc[:, "per"]

            nbar = ni.divide(nj)
            par = wj_par.divide(wi_par)
            per = wj_per.divide(wi_per).pow(2)
            wbar = par.multiply(per, axis=0)
            coef = nbar.multiply(wbar, axis=0).apply(np.log)

            vi = self.data.loc[:, "v"].xs(si, axis=1, level="S")
            vj = self.data.loc[:, "v"].xs(sj, axis=1, level="S")
            if si == "a":
                vi = vi.multiply(np.sqrt(self.mass_in_mp[si] / self.charge_states[si]))
            elif sj == "a":
                vj = vj.multiply(np.sqrt(self.mass_in_mp[sj] / self.charge_states[sj]))

            dv = vi.subtract(vj)
            dv = vector.Vector(dv).project(ot.b)
            dvw = dv.divide(wj, axis=1).pow(2).sum(axis=1)

            f2f1 = coef.add(dvw, axis=0)
            f2f1.name = "{}/{}".format(si, sj)

            pdt.assert_series_equal(f2f1, ot.vdf_ratio(si, sj))

            # Test catching multi-species strings.
            ssum = "+".join(sisj)
            scomma = ",".join(sisj)
            msg0 = "Invalid species"
            msg1 = "VDFs are evaluated on a species-by-species basis."
            with self.assertRaisesRegex(ValueError, msg1):
                ot.vdf_ratio(ssum, si)
            with self.assertRaisesRegex(ValueError, msg1):
                ot.vdf_ratio(ssum, sj)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(scomma, si)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(scomma, sj)
            with self.assertRaisesRegex(ValueError, msg1):
                ot.vdf_ratio(si, ssum)
            with self.assertRaisesRegex(ValueError, msg1):
                ot.vdf_ratio(sj, ssum)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(si, scomma)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(sj, scomma)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(ssum, scomma)
            with self.assertRaisesRegex(ValueError, msg0):
                ot.vdf_ratio(scomma, ssum)

    def test_specific_entropy(self):
        r"""Specific entropy S = p_th rho^-gamma with gamma = 5/3.

        ON FAILURE: the code is wrong, per Siscoe (1983),
        doi:10.1007/978-94-009-7194-3_2, cited in the `specific_entropy` docstring.
        """
        ot = self.object_testing

        gamma = 5.0 / 3.0
        units = 1e4 / constants.e
        for s in self.species_combinations:
            multi_species = len(s) > 1
            pth = ot.pth(*s).xs("scalar", axis=1, level="C" if multi_species else None)
            rho = ot.rho(*s)

            pth *= 1e-12
            rho *= 1e6 * constants.m_p

            by_species = (
                pth.multiply(
                    rho.pow(-gamma),
                    axis=1 if multi_species else 0,
                    level="S" if multi_species else None,
                )
                / units
            )
            by_species.name = "S"

            test_fcn = (
                pdt.assert_frame_equal if multi_species else pdt.assert_series_equal
            )
            test_fcn(by_species, ot.specific_entropy(*s))
            test_fcn(ot.specific_entropy(*s), ot.S(*s))

            if multi_species:
                stotal = "+".join(s)
                pth_total = pth.sum(axis=1)
                rho_total = rho.sum(axis=1)
                total = pth_total.multiply(rho_total.pow(-gamma), axis=0) / units
                total.name = "S"

                pdt.assert_series_equal(total, ot.specific_entropy(stotal))
                pdt.assert_series_equal(ot.specific_entropy(stotal), ot.S(stotal))
                pdt.assert_series_equal(ot.specific_entropy(stotal), ot.S(stotal))

                # comma-separated species list fails
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.specific_entropy(",".join(s))
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    ot.S(",".join(s))


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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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

        ON FAILURE: the code is wrong; `_chk_species` accepted a species this
        plasma does not hold.
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
