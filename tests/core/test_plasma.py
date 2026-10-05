#!/usr/bin/env python
"""Tests for the :class:`Plasma` container."""

import pandas as pd
import numpy as np
import itertools
import pandas.testing as pdt
import pytest

from abc import ABC, abstractproperty, abstractmethod

from scipy import constants
from scipy.constants import physical_constants
from scipy.special import erf

from . import test_base as base

from solarwindpy.core import vector
from solarwindpy.core import ions
from solarwindpy.core import plasma
from solarwindpy.core import spacecraft
from solarwindpy.core import alfvenic_turbulence

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
        r"""Every combination of this plasma's species, for testing methods."""
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

    def test_comma_joined_species_are_rejected_as_invalid(self):
        r"""A comma inside a species string raises "Invalid species".

        Species are passed as separate arguments or summed with "+"; "a,p1" is
        neither, whether or not the plasma holds the species named.

        ON FAILURE: the code is wrong; `Plasma` accepted a comma-joined species.
        """
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
                self.object_testing.number_density(s)

            if "+" in s:
                # A species list for which one species contains "+" is not
                # uniformly parsable.
                with self.assertRaisesRegex(ValueError, "Invalid species"):
                    self.object_testing.number_density(*s.split(","))

    def test_held_species_are_accepted_in_any_order_and_sum(self):
        r"""Every held species, subset, and "+"-sum is accepted; sum order is irrelevant.

        The total of a "+"-sum is the same whichever order its terms are
        written in (identity: addition commutes).

        ON FAILURE: the code is wrong; `Plasma` is rejecting a species it holds
        or treating "+"-sums as ordered.
        """
        ot = self.object_testing
        for s in self.stuple:
            self.assertEqual(ot.number_density(s).name, s)
        for combo in self.species_combinations:
            ot.number_density(*combo)
            forward = ot.number_density("+".join(combo))
            backward = ot.number_density("+".join(reversed(combo)))
            pdt.assert_series_equal(forward, backward, check_names=False)

    @abstractmethod
    def test_unheld_species_are_unavailable(self):
        r"""Subclass this to test species the plasma does not hold.

        The code will look something like:
            for s in bad_species:
                with self.assertRaisesRegex(ValueError,
                                            "Requested species unavailable."):
                    self.object_testing.number_density(*s)
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

    def test_kinetic_energy_flux(self):
        """Plasma's kinetic energy flux is each ion's, and their sum for "a+b".

        ON FAILURE: `Plasma.kinetic_energy_flux` does not reproduce or sum the
        per-ion values; `Ion.kinetic_energy_flux` itself is tested in test_ions.
        """
        ot = self.object_testing
        by_ion = {s: ot.ions.loc[s].kinetic_energy_flux for s in self.stuple}
        for s, wk in by_ion.items():
            pdt.assert_series_equal(ot.kinetic_energy_flux(s), wk, check_names=False)
        if len(self.stuple) > 1:
            total = sum(by_ion.values())
            scom = "+".join(self.stuple)
            pdt.assert_series_equal(
                ot.kinetic_energy_flux(scom), total, check_names=False
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
        r"""The collision frequency for differential flow follows the paper.

        Hernandez & Marsch (JGR 1985, doi:10.1029/JA090iA11p11062), Eq. (18).

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
        sc_data = base.SyntheticData().spacecraft_data

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

        sc_data = base.SyntheticData().spacecraft_data

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

            # Ion equality is exact (DataFrame.equals); for three species the two
            # summation orders differ by ~1e-16 relative, so compare with tolerance.

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

        # [m_p] [n] [v]^3 / [q], with [q] = 1 uW m^-2 = 1e-6 W m^-2.
        coeff = constants.m_p * 1e6 * 1e9 / 1e-6
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
        data = base.SyntheticData().combined_data
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

        test_window = "365D"
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
        # [S] = eV cm^2 m_p^-5/3 in SI: e [J/eV] * 1e-4 [m^2/cm^2] * m_p^-5/3.
        units = constants.e * 1e-4 * constants.m_p ** (-5.0 / 3.0)
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
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaP1(base.P1Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaP2(base.P2Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaAlphaP1(base.AlphaP1Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaAlphaP2(base.AlphaP2Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaP1P2(base.P1P2Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


class TestPlasmaAlphaP1P2(base.AlphaP1P2Test, PlasmaTestBase, base.SWEData):
    def test_unheld_species_are_unavailable(self):
        r"""Species this plasma does not hold raise "Requested species unavailable".

        ON FAILURE: the code is wrong; `Plasma` accepted a species it does not
        hold.
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
                self.object_testing.number_density(*s)


# ---------------------------------------------------------------------------
# Hand-worked physics cases.
#
# Each Plasma below is built from round-number inputs in the package's storage
# units (`solarwindpy.core.units_constants.Units`): n [cm^-3], v and w [km/s],
# b [nT]. Thermal speeds follow m w^2 = 2 k T (`Plasma.__init__` Notes;
# `Ion.temperature` and `Ion.pth` = rho w^2 / 2 in solarwindpy/core/ions.py),
# the convention Hernandez & Marsch (1985) state after their Eq. 5. Outputs are
# in `Units`: rho [m_p cm^-3], nuc [1e-7 Hz], qpar and Wk [uW m^-2], cs [km/s],
# specific_entropy [eV cm^2 m_p^-5/3]. Expected values are computed here in SI
# from the named source and converted to those units.
# ---------------------------------------------------------------------------

M_P = constants.m_p
M_ALPHA = physical_constants["alpha particle mass"][0]
GAMMA = 5.0 / 3.0  # adiabatic index of a monatomic ideal gas
PER_CC = 1e6  # m^-3 per cm^-3
KM = 1e3  # m s^-1 per km s^-1
MICRO = 1e-6  # W m^-2 per uW m^-2
# rel=1e-9 wherever an alpha mass density enters: the package forms it from the
# CODATA alpha/proton mass ratio times m_p, these tests from the CODATA alpha
# mass; the two agree to 1e-11.
REL_ALPHA = 1e-9


class MissingFieldGaveNumber(AssertionError):
    """A quantity that needs the field direction returned a number where b is missing."""


def _hand_plasma(rows, *species, b=None):
    """Build a `Plasma` from hand-chosen rows.

    rows: list of {species: (n, (vx, vy, vz), w_par, w_per)}, one dict per time.
    b: list of (bx, by, bz) per time; defaults to 5 nT along x.
    """
    if b is None:
        b = [(5.0, 0.0, 0.0)] * len(rows)
    records = []
    for sp, bb in zip(rows, b):
        d = {("b", c, ""): x for c, x in zip("xyz", bb)}
        for s, (n, v, wpar, wper) in sp.items():
            d[("n", "", s)] = n
            d.update({("v", c, s): x for c, x in zip("xyz", v)})
            d[("w", "par", s)] = wpar
            d[("w", "per", s)] = wper
        records.append(d)
    data = pd.DataFrame.from_records(records)
    data.columns = pd.MultiIndex.from_tuples(data.columns, names=["M", "C", "S"])
    data.index = pd.date_range("2020-01-01", periods=len(rows), freq="min")
    data.index.name = "Epoch"
    return plasma.Plasma(data, *species)


def _hm_rate_function(x):
    """Drift dependence of the H&M momentum exchange rate.

    (erf(x) - x erf'(x)) / x^3 with erf'(x) = (2/sqrt(pi)) exp(-x^2):
    Hernandez & Marsch (1985), doi:10.1029/JA090iA11p11062, Eqs. 26-27, where it
    appears as phi_1(x) / tau_0 with tau_0 = (3 sqrt(pi)/4) tau. It tends to
    4/(3 sqrt(pi)) = 0.7523 as x -> 0 (phi_1(0) = 1).
    """
    return (erf(x) - x * (2.0 / np.sqrt(np.pi)) * np.exp(-(x**2))) / x**3


# Alphas (test species a) drifting through protons (field species b = p1).
# Isotropic w_a = 40 and w_p1 = 30 km/s, so W_ab = sqrt(40^2 + 30^2) = 50 km/s
# (H&M Eq. 10). Row 0 drifts 50 km/s (x = 1), row 1 drifts 25 km/s (x = 0.5).
# At x = 1 the Gaussian term (2/sqrt(pi)) x exp(-x^2) = 0.4151 is 49% of
# erf(1) = 0.8427, so the rate depends on it; the SWE fixture has x >= 8.6,
# where that term is below 1e-30 of erf(x). Isotropic inputs also make the
# rate independent of which thermal-speed component `nuc` reads (it reads
# w_par): H&M treat isotropic Maxwellians.
NUC_ROWS = [
    {
        "a": (0.2, (450.0, 0.0, 0.0), 40.0, 40.0),
        "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0),
    },
    {
        "a": (0.2, (425.0, 0.0, 0.0), 40.0, 40.0),
        "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0),
    },
]


def test_nuc_test_particle_rate_is_hernandez_marsch_at_low_drift():
    r"""`nuc(a, p1, both_species=False)` is the H&M alpha-proton rate at x = 1 and 0.5.

    nu_ab = q_a^2 q_b^2 n_b lnL / (4 pi eps0^2 m_a mu_ab W_ab^3) * G(x), with
    mu_ab = m_a m_b / (m_a + m_b): Hernandez & Marsch (1985),
    doi:10.1029/JA090iA11p11062, Eq. 14 (tau_ab^-1, Gaussian units converted to SI
    by e^2 -> e^2 / (4 pi eps0)) and Eq. 18 with the rate function of Eqs. 26-27.
    lnL is an input taken from `Plasma.lnlambda`, which `test_lnlambda` checks.

    ON FAILURE: the code is wrong, unless the author rejects Hernandez & Marsch
    (1985) Eqs. 14, 18 and 26-27 as the definition of `nuc`.
    """
    p = _hand_plasma(NUC_ROWS, "a", "p1")
    q_a, q_b = 2.0 * constants.e, constants.e
    mu_ab = M_ALPHA * M_P / (M_ALPHA + M_P)  # reduced mass, Eq. 14
    n_b = 5.0 * PER_CC  # proton density, chosen input
    w_ab = 50.0 * KM  # sqrt(40^2 + 30^2) km/s, Eq. 10
    x = np.array([50.0, 25.0]) / 50.0  # drift / W_ab, Eq. 10
    lnlambda = p.lnlambda("a", "p1").to_numpy()
    tau_inv = (
        q_a**2
        * q_b**2
        * n_b
        * lnlambda
        / (4.0 * np.pi * constants.epsilon_0**2 * M_ALPHA * mu_ab * w_ab**3)
    )  # Eq. 14 in SI
    expected = tau_inv * _hm_rate_function(x) / 1e-7  # Units.nuc = 1e-7 Hz

    nu = p.nuc("a", "p1", both_species=False)
    assert nu.name == "a-p1"
    assert nu.to_numpy() == pytest.approx(expected, rel=REL_ALPHA, abs=0)


def test_nuc_drift_dependence_is_the_hernandez_marsch_rate_function():
    r"""Halving the drift from x = 1 to x = 0.5 scales `nuc` by G(1)/G(0.5) = 0.65898.

    Both rows share n, T and W_ab, so lnL and the Eq. 14 prefactor cancel and the
    ratio is the H&M (1985) rate function alone (Eqs. 18, 26-27), worked by hand:
    G(1) = erf(1) - 2 e^-1 / sqrt(pi) = 0.8427007929 - 0.4151074974 = 0.4275932955;
    G(0.5) = (erf(0.5) - e^-0.25 / sqrt(pi)) / 0.125
           = (0.5204998778 - 0.4393912895) / 0.125 = 0.6488687068.
    Writing 3 for the Gaussian coefficient 2 turns the ratio to -0.198.

    ON FAILURE: the code is wrong, unless the author rejects Hernandez & Marsch
    (1985) Eqs. 18 and 26-27 as the drift dependence of `nuc`.
    """
    p = _hand_plasma(NUC_ROWS, "a", "p1")
    g1 = 0.8427007929 - 0.4151074974  # G(1), hand-worked above
    g05 = (0.5204998778 - 0.4393912895) / 0.125  # G(0.5), hand-worked above

    for both in (False, True):
        nu = p.nuc("a", "p1", both_species=both)
        # rel=1e-9: the hand values carry 10 significant digits.
        assert nu.iloc[0] / nu.iloc[1] == pytest.approx(g1 / g05, rel=1e-9, abs=0)


def test_nuc_both_species_adds_the_reverse_rate_eq23():
    r"""`nuc(..., both_species=True)` is nu_ab + nu_ba = nu_ab (1 + rho_a / rho_b).

    Hernandez & Marsch (1985) Eq. 23: 1/tau = 1/tau_ab + 1/tau_ba, and momentum
    conservation (rho_a nu_ab = rho_b nu_ba, F_ab = -F_ba below their Eq. 14) gives
    nu_ba = nu_ab rho_a / rho_b. Here rho_a / rho_b = 0.2 m_alpha / (5 m_p).

    ON FAILURE: the code is wrong, unless the author rejects Hernandez & Marsch
    (1985) Eq. 23 as the definition of the two-species rate.
    """
    p = _hand_plasma(NUC_ROWS, "a", "p1")
    single = p.nuc("a", "p1", both_species=False)
    both = p.nuc("a", "p1", both_species=True)
    expected_ratio = 1.0 + (0.2 * M_ALPHA) / (5.0 * M_P)  # Eq. 23, chosen inputs

    assert both.name == "a+p1"
    assert (both / single).to_numpy() == pytest.approx(
        [expected_ratio] * 2, rel=REL_ALPHA, abs=0
    )


def test_sound_speed_of_one_species_is_sqrt_gamma_p_over_rho():
    r"""Protons at w = 30 km/s have c_s = sqrt(gamma p / rho) = 30 sqrt(5/6) km/s.

    With p = rho w^2 / 2 (m w^2 = 2 k T) and gamma = 5/3, c_s = w sqrt(gamma / 2)
    = 30 * 0.9128709292 = 27.38612788 km/s, independent of the density.

    ON FAILURE: the code is wrong, unless the author rejects c_s = sqrt(gamma p / rho)
    with gamma = 5/3.
    """
    p = _hand_plasma([{"p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0)}], "p1")
    # rel=1e-9: the hand value carries 10 significant digits.
    assert p.sound_speed("p1").iloc[0] == pytest.approx(27.38612788, rel=1e-9, abs=0)
    assert p.cs("p1").iloc[0] == pytest.approx(27.38612788, rel=1e-9, abs=0)


def test_sound_speed_per_species_and_species_sum():
    r"""`cs` per species and for "a+p1" equal sqrt(gamma p / rho) of those species.

    Scalar pressure p_s = rho_s w_s^2 / 2 with w_s^2 = (w_par^2 + 2 w_per^2) / 3
    (the trace of the pressure tensor); the species sum uses sum(p) / sum(rho).
    Species are requested in the order ("p1", "a") so a swapped column fails.

    ON FAILURE: the code is wrong, unless the author rejects c_s = sqrt(gamma p / rho)
    with total pressure over total mass density for a species sum.
    """
    rows = [
        {
            "a": (0.2, (450.0, 0.0, 0.0), 50.0, 40.0),
            "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0),
        }
    ]
    p = _hand_plasma(rows, "a", "p1")
    rho = {"a": 0.2 * PER_CC * M_ALPHA, "p1": 5.0 * PER_CC * M_P}
    wsq = {
        "a": (50.0**2 + 2 * 40.0**2) / 3 * KM**2,  # trace of the pressure tensor
        "p1": 30.0**2 * KM**2,
    }
    pth = {s: 0.5 * rho[s] * wsq[s] for s in rho}  # p = rho w^2 / 2

    each = p.cs("p1", "a")
    for s in ("a", "p1"):
        expected = np.sqrt(GAMMA * pth[s] / rho[s]) / KM
        assert each.loc[:, s].iloc[0] == pytest.approx(expected, rel=REL_ALPHA, abs=0)

    expected_sum = np.sqrt(GAMMA * sum(pth.values()) / sum(rho.values())) / KM
    total = p.sound_speed("a+p1")
    assert total.name == "a+p1"
    assert total.iloc[0] == pytest.approx(expected_sum, rel=REL_ALPHA, abs=0)


def test_Wk_of_one_species_is_half_rho_v_cubed():
    r"""5 cm^-3 protons at 400 km/s carry W_K = rho v^3 / 2 = 267.62 uW m^-2.

    W_K,s = rho_s v_s^3 / 2 with v_s the species speed (author's definition).
    The velocity (240, 320, 0) km/s has speed 400 km/s, so a component used in
    place of the speed fails. By hand: 0.5 * 5e6 * 1.67262e-27 * (4e5)^3
    = 2.6762e-4 W m^-2.

    ON FAILURE: the code is wrong.
    """
    p = _hand_plasma([{"p1": (5.0, (240.0, 320.0, 0.0), 30.0, 30.0)}], "p1")
    expected = 0.5 * 5.0 * PER_CC * M_P * (400.0 * KM) ** 3 / MICRO
    for wk in (p.Wk("p1"), p.kinetic_energy_flux("p1")):
        # rel=1e-12: same IEEE-754 arithmetic as the code, in a different order.
        assert wk.iloc[0] == pytest.approx(expected, rel=1e-12, abs=0)
        # rel=1e-4: the hand value carries 5 significant digits.
        assert wk.iloc[0] == pytest.approx(267.62, rel=1e-4, abs=0)


def test_Wk_species_sum_is_a_partial_sum_over_species():
    r"""`Wk("a+p1")` adds rho_s v_s^3 / 2 over species; a NaN species drops out.

    Row 0 holds both species; row 1 has no alpha data. Per the author, a species
    sum is a partial sum: row 1 of the sum is the proton term alone, while the
    per-species frame keeps the alpha NaN.

    ON FAILURE: the code is wrong.
    """
    alpha = (0.2, (450.0, 0.0, 0.0), 40.0, 40.0)
    proton = (5.0, (400.0, 0.0, 0.0), 30.0, 30.0)
    missing = (np.nan, (np.nan, np.nan, np.nan), np.nan, np.nan)
    p = _hand_plasma(
        [{"a": alpha, "p1": proton}, {"a": missing, "p1": proton}], "a", "p1"
    )
    wk_a = 0.5 * 0.2 * PER_CC * M_ALPHA * (450.0 * KM) ** 3 / MICRO
    wk_p = 0.5 * 5.0 * PER_CC * M_P * (400.0 * KM) ** 3 / MICRO

    each = p.Wk("a", "p1")
    assert each.loc[:, "a"].iloc[0] == pytest.approx(wk_a, rel=REL_ALPHA, abs=0)
    assert np.isnan(each.loc[:, "a"].iloc[1])
    # rel=1e-12: same IEEE-754 arithmetic as the code, in a different order.
    assert each.loc[:, "p1"].to_numpy() == pytest.approx([wk_p] * 2, rel=1e-12, abs=0)

    total = p.Wk("a+p1")
    assert total.name == "a+p1"
    assert total.to_numpy() == pytest.approx([wk_a + wk_p, wk_p], rel=REL_ALPHA, abs=0)


def test_heat_flux_matches_its_docstring_formula():
    r"""`heat_flux` is Q_s = rho_s (v_s^3 + 3/2 v_s w_par,s^2), v_s along b in the CM frame.

    Two proton populations of 5 cm^-3 move along b = (3, 4, 0) nT at 400 and
    500 km/s, so the centre of mass moves at 450 km/s and v = -50, +50 km/s along
    b; w_par = 30 and 40 km/s (w_per is set to other values and must not enter).
    By hand, in m_p cm^-3 km^3 s^-3 (1 unit = 1.67262e-6 uW m^-2):
    p1: 5 (-125000 - 67500) = -962500 -> -1.609898604 uW m^-2
    p2: 5 ( 125000 + 120000) = 1225000 ->  2.048961859 uW m^-2
    sum: 262500 -> 0.4390632556 uW m^-2.

    ON FAILURE: the code is wrong, unless the author revises the `heat_flux`
    docstring formula.
    """
    uv = np.array([0.6, 0.8, 0.0])  # unit vector along b = (3, 4, 0)
    rows = [
        {
            "p1": (5.0, tuple(400.0 * uv), 30.0, 20.0),
            "p2": (5.0, tuple(500.0 * uv), 40.0, 25.0),
        }
    ]
    p = _hand_plasma(rows, "p1", "p2", b=[(3.0, 4.0, 0.0)])
    rho = 5.0 * PER_CC * M_P
    expected = {}
    for s, v, w in (("p1", -50.0, 30.0), ("p2", 50.0, 40.0)):
        v, w = v * KM, w * KM
        expected[s] = rho * (v**3 + 1.5 * v * w**2) / MICRO  # docstring formula

    each = p.heat_flux("p1", "p2")
    total = p.qpar("p1+p2")
    # rel=1e-10: the code projects onto b / |b|, which is inexact in binary.
    for s in ("p1", "p2"):
        assert each.loc[:, s].iloc[0] == pytest.approx(expected[s], rel=1e-10, abs=0)
    assert total.name == "p1+p2"
    assert total.iloc[0] == pytest.approx(sum(expected.values()), rel=1e-10, abs=0)
    # rel=1e-9: the hand values carry 10 significant digits.
    assert each.loc[:, "p1"].iloc[0] == pytest.approx(-1.609898604, rel=1e-9, abs=0)
    assert each.loc[:, "p2"].iloc[0] == pytest.approx(2.048961859, rel=1e-9, abs=0)
    assert total.iloc[0] == pytest.approx(0.4390632556, rel=1e-9, abs=0)


def _missing_b_plasma(*species):
    """Two identical rows, the second without b: a/p1 from NUC_ROWS, or p1/p2."""
    if species == ("p1", "p2"):
        sp = {
            "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 20.0),
            "p2": (0.5, (500.0, 0.0, 0.0), 60.0, 40.0),
        }
    else:
        sp = NUC_ROWS[0]
    return _hand_plasma(
        [sp, sp], *species, b=[(5.0, 0.0, 0.0), (np.nan, np.nan, np.nan)]
    )


def test_heat_flux_per_species_is_nan_where_b_is_missing():
    r"""Without b there is no parallel direction, so each species' Q_par is NaN.

    `Vector.project` returns NaN on rows missing from either vector (author
    decision); row 0, with b, stays finite.

    ON FAILURE: the code is wrong.
    """
    q = _missing_b_plasma("a", "p1").heat_flux("a", "p1")
    assert np.isfinite(q.iloc[0]).all()
    assert q.iloc[1].isna().all()


@pytest.mark.xfail(
    strict=True,
    raises=MissingFieldGaveNumber,
    reason="Plasma.heat_flux sums species with DataFrame.sum(axis=1), whose skipna "
    "turns a row where every species is NaN into 0.0 (solarwindpy/core/plasma.py, "
    "heat_flux); expected message 'heat_flux(\"a+p1\") is 0.0 where b is missing'; "
    "remove this marker when heat_flux sums species with min_count=1",
)
def test_heat_flux_species_sum_is_nan_where_b_is_missing():
    r"""Without b, no species contributes to Q_par, so the species sum is NaN, not 0.

    A partial sum keeps the species that are present; where none is, a zero heat
    flux would be invented data.

    ON FAILURE: (unexpected pass) heat_flux sums with min_count=1; drop the xfail
    marker.
    """
    q = _missing_b_plasma("a", "p1").heat_flux("a+p1")
    assert np.isfinite(q.iloc[0])
    if not np.isnan(q.iloc[1]):
        raise MissingFieldGaveNumber(
            f'heat_flux("a+p1") is {q.iloc[1]} where b is missing'
        )


@pytest.mark.xfail(
    strict=True,
    raises=MissingFieldGaveNumber,
    reason="Plasma.vdf_ratio sums (dv/w)^2 over par and per with "
    "DataFrame.sum(axis=1), whose skipna turns the NaN projection into 0 and "
    "returns ln(n2 w1^3 / n1 w2^3) (solarwindpy/core/plasma.py, vdf_ratio); "
    "expected message 'vdf_ratio is -4.38... where b is missing'; remove this "
    "marker when vdf_ratio sums with skipna=False",
)
def test_vdf_ratio_is_nan_where_b_is_missing():
    r"""Without b the beam drift has no par/per split, so ln(f2/f1) is NaN.

    `Vector.project` returns NaN on rows missing from either vector (author
    decision); row 0, with b, stays finite.

    ON FAILURE: (unexpected pass) vdf_ratio sums with skipna=False; drop the xfail
    marker.
    """
    f2f1 = _missing_b_plasma("p1", "p2").vdf_ratio()
    assert np.isfinite(f2f1.iloc[0])
    if not np.isnan(f2f1.iloc[1]):
        raise MissingFieldGaveNumber(f"vdf_ratio is {f2f1.iloc[1]} where b is missing")


def test_specific_entropy_per_species_and_species_sum():
    r"""S = p rho^-gamma per species, and sum(p) sum(rho)^-gamma for "a+p1".

    Siscoe (1983), doi:10.1007/978-94-009-7194-3_2, as cited by
    `specific_entropy`, in eV cm^2 m_p^-5/3. Hand case for protons alone:
    S = k T n^(-2/3) with k T = m_p (30 km/s)^2 / 2 = 4.697858218 eV and
    n = 5 cm^-3, so S = 4.697858218 / 5^(2/3) = 1.606644911. Species are requested
    as ("p1", "a") so a swapped column fails.

    ON FAILURE: the code is wrong, unless the author rejects the Siscoe (1983)
    definition or its species sum.
    """
    rows = [
        {
            "a": (0.2, (450.0, 0.0, 0.0), 50.0, 40.0),
            "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0),
        }
    ]
    p = _hand_plasma(rows, "a", "p1")
    rho = {"a": 0.2 * PER_CC * M_ALPHA, "p1": 5.0 * PER_CC * M_P}
    wsq = {"a": (50.0**2 + 2 * 40.0**2) / 3 * KM**2, "p1": 30.0**2 * KM**2}
    pth = {s: 0.5 * rho[s] * wsq[s] for s in rho}  # p = rho w^2 / 2
    unit = constants.e * 1e-4 * M_P ** (-GAMMA)  # eV cm^2 m_p^-5/3 in SI

    each = p.S("p1", "a")
    for s in ("a", "p1"):
        expected = pth[s] * rho[s] ** (-GAMMA) / unit
        assert each.loc[:, s].iloc[0] == pytest.approx(expected, rel=REL_ALPHA, abs=0)
    # rel=1e-9: the hand value carries 10 significant digits.
    assert each.loc[:, "p1"].iloc[0] == pytest.approx(1.606644911, rel=1e-9, abs=0)

    expected_sum = sum(pth.values()) * sum(rho.values()) ** (-GAMMA) / unit
    total = p.specific_entropy("a+p1")
    assert total.iloc[0] == pytest.approx(expected_sum, rel=REL_ALPHA, abs=0)


def test_estimate_electrons_weights_each_species_by_its_own_charge():
    r"""n_e = sum z_s n_s and n_e v_e = sum z_s n_s v_s, with z_a = 2 on the alphas.

    Quasi-neutrality and zero net current. With 5 cm^-3 protons at (400, 0, 0)
    and 0.2 cm^-3 alphas at (450, 30, 0) km/s: n_e = 5 + 2 * 0.2 = 5.4 cm^-3
    (a swapped charge gives 10.2) and v_e = (2180, 12, 0) / 5.4
    = (403.7037, 2.2222, 0) km/s.

    ON FAILURE: the code is wrong.
    """
    rows = [
        {
            "a": (0.2, (450.0, 30.0, 0.0), 40.0, 40.0),
            "p1": (5.0, (400.0, 0.0, 0.0), 30.0, 30.0),
        }
    ]
    e = _hand_plasma(rows, "p1", "a").estimate_electrons()
    # rel=1e-12: exact sums of chosen inputs.
    assert e.n.iloc[0] == pytest.approx(5.4, rel=1e-12, abs=0)
    v = e.v.cartesian.iloc[0]
    assert v.loc["x"] == pytest.approx(2180.0 / 5.4, rel=1e-12, abs=0)
    assert v.loc["y"] == pytest.approx(12.0 / 5.4, rel=1e-12, abs=0)
    assert v.loc["z"] == 0.0
