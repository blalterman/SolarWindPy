#!/usr/bin/env python
"""Tests for the :class:`Ion` object."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from abc import ABC, abstractproperty
from unittest import TestCase

from scipy import constants
from scipy.constants import physical_constants

from . import _fixtures as fixtures

import solarwindpy as swp

from solarwindpy.core import vector
from solarwindpy.core import tensor
from solarwindpy.core import ions
from tests.tolerances import exact, printed


class IonTestBase(ABC):
    @classmethod
    def set_object_testing(cls):
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

    def test_mass_density(self):
        mmp = self.mass_in_mp
        rho = self.data.loc[:, pd.IndexSlice["n", ""]] * mmp
        rho.name = self.species
        if not isinstance(rho, pd.Series):
            assert rho.shape[1] == 1
            rho = rho.iloc[:, 0]
        rho.name = "rho"
        ot = self.object_testing
        pdt.assert_series_equal(rho, ot.rho)

    def test_v(self):
        v = vector.Vector(self.data.v)
        ot = self.object_testing
        self.assertEqual(v, ot.v)

    def test_w(self):
        w = tensor.Tensor(self.data.w)
        ot = self.object_testing
        self.assertEqual(w, ot.w)

    def test_anisotropy(self):
        w = self.data.w
        ani = (w.per / w.par).pow(2)
        ani.name = "R"
        ot = self.object_testing
        pdt.assert_series_equal(ani, ot.R)

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
        pdt.assert_frame_equal(t, self.object_testing.T)

    def test_cs(self):
        """Par, per and scalar sound speeds use the CGL indices 3, 2 and 5/3.

        cs_c = sqrt(gamma_c p_c / rho) per pressure component, with the
        double-adiabatic indices gamma_par = 3 and gamma_per = 2 of Chew,
        Goldberger & Low (1956), Proc. R. Soc. Lond. A 236, 112,
        doi:10.1098/rspa.1956.0116, and the isotropic gamma = 5/3 for the
        scalar. Recomputed from the raw n and w in SI, and, because
        p = rho w^2 / 2, also by hand: cs_par = sqrt(3/2) w_par,
        cs_per = w_per and cs = sqrt(5/6) w.

        ON FAILURE: the code is wrong, unless the author rejects the CGL
        indices for the par and per sound speeds.
        """
        rho = self.mass * self.data.n * 1e6  # [kg m^-3]
        w = self.data.w * 1e3  # [m s^-1]
        pth = w.pow(2).multiply(0.5 * rho, axis=0)  # [Pa]
        gamma = {"par": 3.0, "per": 2.0, "scalar": 5.0 / 3.0}
        cs = self.object_testing.cs
        for c, g in gamma.items():
            expected = (g * pth.loc[:, c] / rho).pow(0.5) / 1e3  # [km s^-1]
            assert cs.loc[:, c].to_numpy() == exact(expected.to_numpy())

        w_kms = self.data.w
        by_hand = {
            "par": np.sqrt(1.5) * w_kms.loc[:, "par"],
            "per": w_kms.loc[:, "per"],
            "scalar": np.sqrt(5.0 / 6.0) * w_kms.loc[:, "scalar"],
        }
        for c, expected in by_hand.items():
            assert cs.loc[:, c].to_numpy() == exact(expected.to_numpy())

    def test_kinetic_energy_flux(self):
        """W_k = rho |v|^3 / 2, in uW m^-2, recomputed from the raw n and v.

        ON FAILURE: the code is wrong.
        """
        rho = self.mass * self.data.n * 1e6  # [kg m^-3]
        v = self.data.v.loc[:, ["x", "y", "z"]].pow(2).sum(axis=1).pipe(np.sqrt) * 1e3
        wk = 0.5 * rho * v.pow(3) / 1e-6  # [uW m^-2]
        wk.name = "Wk"
        pdt.assert_series_equal(wk, self.object_testing.Wk)


class TestIonA(fixtures.AlphaTest, IonTestBase, fixtures.SWEData):
    pass


class TestIonP1(fixtures.P1Test, IonTestBase, fixtures.SWEData):
    pass


class TestIonP2(fixtures.P2Test, IonTestBase, fixtures.SWEData):
    pass


class TestIonSpecificsOptions(TestCase):
    """Ion construction and equality from the full (M, C, S) plasma frame."""

    species = ("a", "p1", "p2")

    @classmethod
    def setUpClass(cls):
        """Load the (M, C, S) plasma fixture; these tests build their own Ions."""
        cls.data = fixtures.SyntheticData().plasma_data

    def test_init_with_species(self):
        """An Ion built from one species' (M, C) slice keeps that slice and name.

        ON FAILURE: the code is wrong.
        """
        for species in self.species:
            with self.subTest(species=species):
                data = self.data.xs(species, axis=1, level="S")
                ion = ions.Ion(data, species)
                self.assertIsInstance(ion, ions.Ion)
                self.assertEqual(species, ion.species)
                pdt.assert_frame_equal(data, ion.data)

    def test_init_version_comparison(self):
        """An Ion built from (M, C, S) data equals one built from its (M, C) slice.

        ON FAILURE: the code is wrong.
        """
        for species in self.species:
            with self.subTest(species=species):
                with_s = self.data.xs(species, axis=1, level="S", drop_level=False)
                without_s = self.data.xs(species, axis=1, level="S")
                self.assertEqual(
                    ions.Ion(with_s, species), ions.Ion(without_s, species)
                )

    def test_eq(self):
        """Ions from the same frame are equal iff their species match.

        ON FAILURE: the code is wrong.
        """
        for s0 in self.species:
            for s1 in self.species:
                with self.subTest(s0=s0, s1=s1):
                    i0 = ions.Ion(self.data, s0)
                    i1 = ions.Ion(self.data, s1)
                    if s0 == s1:
                        self.assertEqual(i0, i1)
                    else:
                        self.assertNotEqual(i0, i1)

    def test_eq_across_frames(self):
        """Same-species Ions from different frames are equal iff the data match.

        A copy of the frame holds identical data, so its Ion is equal. A frame
        whose first density is doubled holds different data, so its Ion is not.

        ON FAILURE: the code is wrong.
        """
        for species in self.species:
            with self.subTest(species=species):
                original = ions.Ion(self.data, species)
                same = ions.Ion(self.data.copy(deep=True), species)
                changed_frame = self.data.copy(deep=True)
                changed_frame.loc[changed_frame.index[0], ("n", "", species)] *= 2.0
                changed = ions.Ion(changed_frame, species)
                self.assertEqual(original, same)
                self.assertNotEqual(original, changed)


def test_kinetic_energy_flux_of_a_hand_computed_proton_stream():
    """5 cm^-3 protons at 400 km/s carry rho v^3 / 2 = 267.6 uW m^-2.

    ON FAILURE: the code is wrong.
    """
    cols = pd.MultiIndex.from_tuples(
        [("n", ""), ("v", "x"), ("v", "y"), ("v", "z")]
        + [("w", c) for c in ("par", "per", "scalar")],
        names=["M", "C"],
    )
    data = pd.DataFrame([[5.0, 400.0, 0.0, 0.0, 50.0, 50.0, 50.0]], columns=cols)
    expected = 0.5 * (5e6 * constants.m_p) * (400e3) ** 3 / 1e-6  # [uW m^-2]
    assert ions.Ion(data, "p1").Wk.iloc[0] == exact(expected)
    # Guard the hand value in the docstring against the formula above.
    assert expected == printed(267.6, decimals=1)


@pytest.mark.parametrize(
    "names", [["M", "X"], ["M", "C", "X"]], ids=["two-levels", "three-levels"]
)
def test_ion_data_with_wrong_level_names_raises_value_error_naming_the_levels(names):
    r"""Ion columns must be levels named ("M", "C") or ("M", "C", "S"); others raise.

    The example protons' two-level slice and the full three-level plasma frame,
    each with its last level renamed "X", are refused with a ValueError naming
    the levels an Ion wants, as Plasma, its spacecraft and auxiliary data are.

    ON FAILURE: the code is wrong.
    """
    data = swp.examples.load_plasma().data
    if len(names) == 2:
        data = data.xs("p1", axis=1, level="S")
    with pytest.raises(ValueError, match="Ion data columns must have levels named"):
        ions.Ion(data.rename_axis(columns=names), "p1")


def test_an_ion_species_joined_by_plus_raises_value_error_naming_it():
    r"""An Ion species containing ``+`` raises ValueError naming it, as a Plasma's does.

    Combined species are formed in method calls, never stored; one check and
    one message refuse them for every object that stores a species.

    ON FAILURE: the code is wrong.
    """
    data = swp.examples.load_plasma().data
    with pytest.raises(ValueError, match=r"^Ion\.species can't contain '\+': p1\+a$"):
        ions.Ion(data, "p1+a")
