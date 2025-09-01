#!/usr/bin/env python
"""Tests for Alfvenic turbulence calculations."""


import numpy as np
import pandas as pd
import logging
import pytest

import pandas.testing as pdt

from abc import ABC, abstractproperty

from scipy import constants
from scipy.constants import physical_constants

# import test_base as base
from . import test_base as base

from solarwindpy import alfvenic_turbulence as turb

pd.set_option("mode.chained_assignment", "raise")


class AlfvenicTrubulenceTestBase(ABC):
    #    def setUp(self):
    #        self.object_testing.set_agg("mean")
    #        self.object_testing.update_rolling(window=2,
    #                                           min_periods=1,
    #                                           center=True)
    #
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
            .sort_index(axis=1)
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
            v.multiply(r, axis=1, level="S")
            .T.groupby(level="C")
            .sum()
            .T
            # sum(axis=1, level="C")
            .divide(rtot, axis=0)
        )

        coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
        b_ca_units = coef * b.divide(np.sqrt(rtot), axis=0)

        # Have **kwargs pass to rolling(**kwargs) with window, min_periods, and
        # center taken from kwargs.pop("window", 2), etc.
        test_window = "365d"
        test_periods = 1
        module = turb.AlfvenicTurbulence(
            vcom,
            b,
            rtot,
            "+".join(species),
            window=test_window,
            min_periods=test_periods,
        )

        data = pd.concat(
            {"v": vcom, "b": b_ca_units, "r": rtot.to_frame(name="+".join(species))},
            axis=1,
            names=["M", "C"],
        ).sort_index(axis=1)
        # rolled = data.rolling(window=2, min_periods=1, center=True).agg("mean")
        rolled = data.rolling(window=test_window, min_periods=test_periods).agg("mean")
        deltas = data.subtract(rolled, axis=1)

        data.name = "measurements"
        deltas.name = "deltas"

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

        # pdb.set_trace()
        cls.object_testing = module
        cls.data = deltas
        cls.unrolled_data = data
        cls.test_window = test_window
        cls.test_periods = test_periods

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

    def test_data(self):
        data = self.data.drop("r", axis=1, level="M")
        ot = self.object_testing

        pdt.assert_frame_equal(data, ot.data)

    def test_meaurements(self):
        measurements = self.unrolled_data.drop("r", axis=1, level="M")
        ot = self.object_testing
        pdt.assert_frame_equal(measurements, ot.measurements)

    def test_averaging_info(self):
        ot = self.object_testing
        avg = ot.averaging_info
        expected = turb.AlvenicTurbAveraging(self.test_window, self.test_periods)
        self.assertEqual(expected, avg)

    #    def test_auto_reindex(self):
    #
    #        v = self.unrolled_data.loc[:, "v"].drop(1, axis=0)
    #        b = self.unrolled_data.loc[:, "b"].drop(1, axis=0)
    #        r = self.unrolled_data.loc[:, ("r", self.species)].drop(1, axis=0)
    #
    #        idx_with_skip = pd.Int64Index([0, 2])
    #        pdt.assert_index_equal(idx_with_skip, v.index)
    #        pdt.assert_index_equal(idx_with_skip, b.index)
    #        pdt.assert_index_equal(idx_with_skip, r.index)
    #        pdt.assert_index_equal(v.index, b.index)
    #        pdt.assert_index_equal(v.index, r.index)
    #
    #        # `unrolled_data` stores [b] = km/s. Need to get back to nT.
    #        coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
    #        b_nT = b.multiply(np.sqrt(r), axis=0) / coef
    #
    #        chk = turb.AlfvenicTurbulence(
    #            v,
    #            b_nT,
    #            r,
    #            self.species,
    #            auto_reindex=True,
    #            window=2,
    #            min_periods=1,
    #            center=True,
    #        )
    #
    #        idx = pd.RangeIndex(start=v.index.min(), stop=v.index.max() + 1, step=1)
    #        pdt.assert_index_equal(idx, chk.v.index)
    #        pdt.assert_index_equal(idx, chk.b.index)
    #        pdt.assert_index_equal(chk.v.index, chk.b.index)
    #
    #        nans = pd.DataFrame(
    #            {
    #                "x": pd.Series([False, True, False]),
    #                "y": pd.Series([False, True, False]),
    #                "z": pd.Series([False, True, False]),
    #            }
    #        )
    #        nans.columns.names = ["C"]
    #
    #        v = v.reindex(idx, axis=0)
    #        b = b.reindex(idx, axis=0)
    #
    #        pdt.assert_frame_equal(nans, chk.v.isna())
    #        pdt.assert_frame_equal(nans, chk.b.isna())
    #
    #        # TODO: I don't think I want to test values here, so I've removed this
    #        #       code. All this function tests is if things automatically
    #        #       reindex correctly.
    #        # Rolled values will average with NaN -> zero.
    #        # v = v.mask(~nans, 0.0)
    #        # b = b.mask(~nans, 0.0)
    #
    #    #        pdb.set_trace()
    #    #
    #    #        pdt.assert_frame_equal(v, chk.v)
    #    #        pdt.assert_frame_equal(b, chk.b)

    def test_bfield(self):
        # Test in Alfven units
        b = self.data.loc[:, "b"]

        ot = self.object_testing
        pdt.assert_frame_equal(b, ot.bfield)
        pdt.assert_frame_equal(ot.bfield, ot.b)

    def test_velocity(self):
        v = self.data.loc[:, "v"]

        ot = self.object_testing
        pdt.assert_frame_equal(v, ot.velocity)
        pdt.assert_frame_equal(ot.v, ot.velocity)

    def test_z_plus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)

        ot = self.object_testing
        pdt.assert_frame_equal(zp, ot.z_plus)
        pdt.assert_frame_equal(ot.zp, ot.z_plus)

    def test_z_minus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zm = v.subtract(b, axis=1)

        ot = self.object_testing
        pdt.assert_frame_equal(zm, ot.z_minus)
        pdt.assert_frame_equal(ot.zm, ot.z_minus)

    def test_e_plus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)
        ep = 0.5 * zp.pow(2).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(ep, ot.e_plus)
        pdt.assert_series_equal(ot.ep, ot.e_plus)

    def test_e_minus(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zm = v.subtract(b, axis=1)
        em = 0.5 * zm.pow(2).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(em, ot.e_minus)
        pdt.assert_series_equal(ot.em, ot.e_minus)

    def test_kinetic_energy(self):
        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(ev, ot.kinetic_energy)
        pdt.assert_series_equal(ot.kinetic_energy, ot.ev)

    def test_magnetic_energy(self):
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(eb, ot.magnetic_energy)
        pdt.assert_series_equal(ot.magnetic_energy, ot.eb)

    def test_total_energy(self):
        tk = ["v", "b"]
        etot = 0.5 * self.data.loc[:, tk].pow(2).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(etot, ot.total_energy)
        pdt.assert_series_equal(ot.total_energy, ot.etot)

    def test_residual_energy(self):
        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1)
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1)
        eres = ev.subtract(eb, axis=0)

        ot = self.object_testing
        pdt.assert_series_equal(eres, ot.residual_energy)
        pdt.assert_series_equal(ot.residual_energy, ot.eres)

    def test_normalized_residual_energy(self):
        v = self.data.loc[:, "v"]
        ev = 0.5 * v.pow(2).sum(axis=1)
        b = self.data.loc[:, "b"]
        eb = 0.5 * b.pow(2).sum(axis=1)
        etot = ev.add(eb, axis=0)
        eres = ev.subtract(eb, axis=0)
        eres_norm = eres.divide(etot, axis=0)

        ot = self.object_testing
        pdt.assert_series_equal(eres_norm, ot.normalized_residual_energy)
        pdt.assert_series_equal(ot.normalized_residual_energy, ot.eres_norm)

    def test_sigma_r(self):
        ot = self.object_testing
        pdt.assert_series_equal(ot.sigma_r, ot.normalized_residual_energy)

    def test_cross_helicity(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        ch = 0.5 * v.multiply(b, axis=1).sum(axis=1)

        ot = self.object_testing
        pdt.assert_series_equal(ch, ot.cross_helicity)

    def test_normalized_cross_helicity(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        ch = 0.5 * v.multiply(b, axis=1).sum(axis=1)
        ev = 0.5 * v.pow(2).sum(axis=1)
        eb = 0.5 * b.pow(2).sum(axis=1)
        etot = ev.add(eb, axis=0)
        normalized_cross_helicity = 2.0 * ch.divide(etot, axis=0)

        ot = self.object_testing
        pdt.assert_series_equal(normalized_cross_helicity, ot.normalized_cross_helicity)
        pdt.assert_series_equal(ot.sigma_c, ot.normalized_cross_helicity)

    def test_alfven_ratio(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        ev = 0.5 * v.pow(2).sum(axis=1)
        eb = 0.5 * b.pow(2).sum(axis=1)
        rA = ev.divide(eb, axis=0)

        ot = self.object_testing
        pdt.assert_series_equal(rA, ot.alfven_ratio)
        pdt.assert_series_equal(ot.alfven_ratio, ot.rA)

    def test_elsasser_ratio(self):
        v = self.data.loc[:, "v"]
        b = self.data.loc[:, "b"]
        zp = v.add(b, axis=1)
        zm = v.subtract(b, axis=1)
        ep = 0.5 * zp.pow(2).sum(axis=1)
        em = 0.5 * zm.pow(2).sum(axis=1)
        rE = em.divide(ep, axis=0)

        ot = self.object_testing
        pdt.assert_series_equal(rE, ot.elsasser_ratio)
        pdt.assert_series_equal(ot.elsasser_ratio, ot.rE)

    def test_eq(self):
        ot = self.object_testing
        # ID should be equal.
        self.assertEqual(ot, ot)
        # Data and type should be equal.

        data = self.unrolled_data
        v = data.loc[:, "v"]
        r = data.loc[:, ("r", self.species)]
        b = data.loc[:, "b"]
        coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
        # `unrolled_data` stores [b] = km/s. Need to get back to nT.
        b_nT = b.multiply(np.sqrt(r), axis=0) / coef
        new_object = ot.__class__(
            v,
            b_nT,
            r,
            ot.species,
            window=self.test_window,
            min_periods=self.test_periods,
        )

        print_inline_debug = False
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


def test_set_data_requires_datetimeindex():
    """``set_data`` raises ``TypeError`` for non-``DatetimeIndex`` inputs."""

    idx = pd.RangeIndex(3)
    v = pd.DataFrame(np.arange(9).reshape(3, 3), index=idx, columns=["x", "y", "z"])
    b = pd.DataFrame(
        np.arange(9).reshape(3, 3) / 10.0, index=idx, columns=["x", "y", "z"]
    )
    rho = pd.Series(np.arange(3), index=idx)

    with pytest.raises(TypeError):
        turb.AlfvenicTurbulence(v, b, rho, "p1")


def test_set_data_warns_on_mismatched_index(caplog):
    """Mismatched indices trigger a warning."""

    v_idx = pd.date_range("2020-01-01", periods=3, freq="H")
    b_idx = pd.date_range("2020-01-02", periods=3, freq="H")
    v = pd.DataFrame(np.arange(9).reshape(3, 3), index=v_idx, columns=["x", "y", "z"])
    b = pd.DataFrame(
        np.arange(9).reshape(3, 3) / 10.0, index=b_idx, columns=["x", "y", "z"]
    )
    rho = pd.Series(np.arange(3), index=v_idx)

    with caplog.at_level(logging.WARNING):
        turb.AlfvenicTurbulence(v, b, rho, "p1")
    assert "v and b have unequal indices" in caplog.text
