#!/usr/bin/env python
"""Tests for Alfvenic turbulence calculations."""

import numpy as np
import pandas as pd
import logging
import warnings
import pytest

import pandas.testing as pdt

from abc import ABC, abstractproperty

from scipy import constants
from scipy.constants import physical_constants

from . import test_base as base

from solarwindpy.core import alfvenic_turbulence as turb
from solarwindpy.core.spacecraft import Spacecraft
from tests.tolerances import exact

pd.set_option("mode.chained_assignment", "raise")


class AlfvenicTrubulenceTestBase(ABC):
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
            .T.divide(rtot, axis=0)
        )

        coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
        b_ca_units = coef * b.divide(np.sqrt(rtot), axis=0)

        # Have **kwargs pass to rolling(**kwargs) with window, min_periods, and
        # center taken from kwargs.pop("window", 2), etc.
        test_window = "365D"
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
        rolled = data.rolling(window=test_window, min_periods=test_periods).agg("mean")
        deltas = data.subtract(rolled, axis=1)

        data.name = "measurements"
        deltas.name = "deltas"

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
        expected = turb.AlfvenicTurbAveraging(self.test_window, self.test_periods)
        self.assertEqual(expected, avg)

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


#####
# Tests
#####
class TestPlasmaAlpha(base.AlphaTest, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


class TestAlfvenicTrubulenceP1(base.P1Test, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


class TestAlfvenicTrubulenceP2(base.P2Test, AlfvenicTrubulenceTestBase, base.SWEData):
    pass


class TestAlfvenicTrubulenceAlphaP1(
    base.AlphaP1Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


class TestAlfvenicTrubulenceAlphaP2(
    base.AlphaP2Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


class TestAlfvenicTrubulenceP1P2(
    base.P1P2Test, AlfvenicTrubulenceTestBase, base.SWEData
):
    pass


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


@pytest.mark.parametrize("shifted", ["b", "rho"])
def test_set_data_warns_on_mismatched_index(shifted, caplog):
    """Mismatched indices log a warning through ``Logger.warning``.

    The deprecated ``Logger.warn`` alias also logs, but raises a
    DeprecationWarning, which this test makes an error.

    ON FAILURE: the code is wrong.
    """

    v_idx = pd.date_range("2020-01-01", periods=3, freq="h")
    shifted_idx = pd.date_range("2020-01-02", periods=3, freq="h")
    b_idx = shifted_idx if shifted == "b" else v_idx
    rho_idx = shifted_idx if shifted == "rho" else v_idx
    v = pd.DataFrame(np.arange(9).reshape(3, 3), index=v_idx, columns=["x", "y", "z"])
    b = pd.DataFrame(
        np.arange(9).reshape(3, 3) / 10.0, index=b_idx, columns=["x", "y", "z"]
    )
    rho = pd.Series(np.arange(3), index=rho_idx)

    with caplog.at_level(logging.WARNING), warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        turb.AlfvenicTurbulence(v, b, rho, "p1")
    assert f"v and {shifted} have unequal indices" in caplog.text


def _small_turbulence(species):
    """An ``AlfvenicTurbulence`` on three hourly samples, for ``species``."""
    idx = pd.date_range("2020-01-01", periods=3, freq="h")
    v = pd.DataFrame(np.arange(9.0).reshape(3, 3), index=idx, columns=["x", "y", "z"])
    b = pd.DataFrame(
        np.arange(9.0).reshape(3, 3) / 10.0, index=idx, columns=["x", "y", "z"]
    )
    rho = pd.Series([1.0, 2.0, 3.0], index=idx)
    return turb.AlfvenicTurbulence(v, b, rho, species)


@pytest.mark.parametrize(
    "species",
    [
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
    ],
)
def test_species_with_at_most_one_comma_is_kept(species):
    """A species string with at most one ``,`` is stored as given.

    ON FAILURE: the code is wrong.
    """
    assert _small_turbulence(species).species == species


def test_species_with_two_commas_raises_value_error():
    """More than one ``,`` in the species raises ``ValueError``.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match="at most one `,`"):
        _small_turbulence("a,p1,p2")


def test_species_that_is_not_a_string_raises_type_error():
    """A species given as a tuple rather than one string raises ``TypeError``.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="must be a single species"):
        _small_turbulence(("a", "p1", "p2"))


@pytest.mark.parametrize(
    "given, stored",
    [("p2+a", "a+p2"), ("p2+p1+a", "a+p1+p2"), ("p1,p2+a", "p1,a+p2")],
)
def test_species_joined_by_plus_are_sorted_on_each_side_of_the_comma(given, stored):
    """``+``-joined species are sorted; the order across the ``,`` is kept.

    Chosen input: unsorted ``+`` lists, so a species string stored as given
    fails. The comma separates the velocity species from the density
    species, so the two sides never swap.

    ON FAILURE: the code is wrong.
    """
    assert _small_turbulence(given).species == stored


def test_equal_indexes_log_no_mismatch_warning(caplog):
    """v, b and rho on one index log no "unequal indices" warning.

    ON FAILURE: the code is wrong.
    """
    with caplog.at_level(logging.WARNING):
        _small_turbulence("p1")
    assert "unequal indices" not in caplog.text


def test_unequal_v_and_b_indexes_are_put_in_time_order():
    """v and b on interleaved times give measurements on the sorted union.

    Chosen input: v at 00, 02, 04 h and b at 01, 03, 05 h, so a union kept
    in order of appearance (v's times, then b's) is out of time order.

    ON FAILURE: the code is wrong.
    """
    t = pd.date_range("2020-01-01", periods=6, freq="h")
    cols = pd.Index(["x", "y", "z"], name="C")
    v = pd.DataFrame(np.ones((3, 3)), index=t[::2], columns=cols)
    b = pd.DataFrame(np.ones((3, 3)), index=t[1::2], columns=cols)
    rho = pd.Series(1.0, index=t)

    ot = turb.AlfvenicTurbulence(v, b, rho, "p1", window="2h", min_periods=1)
    assert ot.measurements.index.equals(t)
    assert ot.data.index.equals(t)


def test_min_periods_and_rolling_kwargs_reach_the_background_average():
    """``min_periods`` and other rolling keywords change the background.

    Chosen input: v = 0, 1, ..., 5 km/s along x, hourly. With
    ``min_periods=3`` the first two rows have no background (NaN); with
    ``center=True`` the 3 h window at row 2 holds rows 1, 2, 3 (mean 2),
    so the fluctuation there is 0.

    ON FAILURE: the code is wrong.
    """
    t = pd.date_range("2020-01-01", periods=6, freq="h")
    cols = pd.Index(["x", "y", "z"], name="C")
    vx = np.arange(6.0)
    v = pd.DataFrame({"x": vx, "y": 0.0, "z": 0.0}, index=t)
    v.columns = cols
    b = pd.DataFrame(1.0, index=t, columns=cols)
    rho = pd.Series(1.0, index=t)

    trailing = turb.AlfvenicTurbulence(v, b, rho, "p1", window="3h", min_periods=3)
    dvx = trailing.v.loc[:, "x"].to_numpy()
    assert np.isnan(dvx[:2]).all()
    # Rows 2..5 trail rows i-2..i, mean i-1, so each fluctuation is 1.
    assert dvx[2:] == exact([1.0, 1.0, 1.0, 1.0])
    assert trailing.averaging_info == turb.AlfvenicTurbAveraging("3h", 3)

    centered = turb.AlfvenicTurbulence(
        v, b, rho, "p1", window="3h", min_periods=1, center=True
    )
    assert centered.v.loc[t[2], "x"] == exact(0.0)


def test_measurements_and_fluctuations_carry_their_names():
    """``measurements`` is named "measurements" and ``data`` "deltas".

    ON FAILURE: the code is wrong.
    """
    ot = _small_turbulence("p1")
    assert ot.measurements.name == "measurements"
    assert ot.data.name == "deltas"


def test_set_data_called_directly_replaces_the_data():
    """``set_data`` with its defaults rebuilds the object from new inputs.

    Chosen input: the same frames with v doubled, so the fluctuations
    double.

    ON FAILURE: the code is wrong.
    """
    ot = _small_turbulence("p1")
    before = ot.v.copy()
    idx = before.index
    v = pd.DataFrame(
        2 * np.arange(9.0).reshape(3, 3), index=idx, columns=["x", "y", "z"]
    )
    b = pd.DataFrame(
        np.arange(9.0).reshape(3, 3) / 10.0, index=idx, columns=["x", "y", "z"]
    )
    ot.set_data(v, b, pd.Series([1.0, 2.0, 3.0], index=idx), "p1")
    assert ot.v.to_numpy() == exact(2 * before.to_numpy(), nan_ok=True)


# ---------------------------------------------------------------------------
# raffaella_version: GSE input converted to RTN
# ---------------------------------------------------------------------------

#: Hand-computed solar-rotation speed subtracted from v_T, km/s. The
#: spacecraft sits at GSE (3, 0, 4) Re, so cos(latitude) = 3/5. Its distance
#: to the Sun is |(AU - 3 Re, 0, 4 Re)| with AU = 149 597 870 700 m (IAU 2012
#: B2) and Re = 6378.1 km (the package's Earth radius, IAU 2015 B3):
#: sqrt(149 578 736 400^2 + 25 512 400^2) m = 149 578 738.5757 km. Then
#: 2.865e-6 rad/s * 149 578 738.5757 km * 0.6 = 257.1258516 km/s.
ROTATION_SPEED_KM_S = 257.12585161166068


def _gse_inputs():
    """Five hourly GSE samples and a Wind spacecraft at GSE (3, 0, 4) Re.

    Rows, as (v [km/s]; b [nT]) in GSE, chosen so each polarity rule shows:

    0. v = (-400, 0, 0), b = (-1, 0, 0): v_R b_R > 0, polarity +1.
    1. v = (-400, 0, 0), b = (+1, 0, 0): v_R b_R < 0, polarity -1.
    2. v = (-100, 0, 0), b = (-1, -5, 0): v_R b_R = 100 k but
       v_T b_T = -257.1 * 5 k, so polarity -1 only with the rotation
       correction and the T term.
    3. v = (-400, 0, 1000), b = (-1, 0, -1): the N term (-1000 k) would
       flip the sign; it is excluded, so polarity +1.
    4. v = (-400, 0, 0), b = (0, 0, 0), spacecraft z unknown (NaN).

    k > 0 is the Alfven-unit scale of 1 nT at rho = 1.
    """
    t = pd.date_range("2020-01-01", periods=5, freq="h")
    cols = pd.Index(["x", "y", "z"], name="C")
    v = pd.DataFrame(
        [
            [-400.0, 0.0, 0.0],
            [-400.0, 0.0, 0.0],
            [-100.0, 0.0, 0.0],
            [-400.0, 0.0, 1000.0],
            [-400.0, 0.0, 0.0],
        ],
        index=t,
        columns=cols,
    )
    b = pd.DataFrame(
        [
            [-1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [-1.0, -5.0, 0.0],
            [-1.0, 0.0, -1.0],
            [0.0, 0.0, 0.0],
        ],
        index=t,
        columns=cols,
    )
    rho = pd.Series(1.0, index=t)
    pos = pd.DataFrame({"x": 3.0, "y": 0.0, "z": 4.0}, index=t)
    pos.iloc[4, 2] = np.nan
    pos.columns = pd.MultiIndex.from_product(
        [["pos"], ["x", "y", "z"]], names=["M", "C"]
    )
    sc = Spacecraft(pos, "wind", "gse")
    return v, b, rho, sc


def test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values():
    """GSE input becomes RTN, v_T loses the solar-rotation speed, b is rectified.

    Expected values come from the documented transformation applied by hand
    to ``_gse_inputs``: (R, T, N) = (-X, -Y, Z); v_T minus
    ``ROTATION_SPEED_KM_S``, NaN where the spacecraft position is unknown;
    polarity = sign(v_R b_R + v_T b_T) = +1, -1, -1, +1 for rows 0-3; and
    ``bfield`` is the field fluctuation times that polarity. The inputs are
    left unchanged.

    ON FAILURE: the code is wrong, unless the author rejects the documented
    GSE-to-RTN steps in the ``AlfvenicTurbulence`` docstring.
    """
    v, b, rho, sc = _gse_inputs()
    v_before, b_before = v.copy(), b.copy()
    kwargs = dict(window="10h", min_periods=1, center=True)

    ot = turb.AlfvenicTurbulence(
        v, b, rho, "p1", raffaella_version=True, sc_vector=sc, **kwargs
    )
    plain = turb.AlfvenicTurbulence(v, b, rho, "p1", **kwargs)

    mv = ot.measurements.loc[:, "v"]
    assert mv.loc[:, "x"].to_numpy() == exact([400.0, 400.0, 100.0, 400.0, 400.0])
    assert mv.loc[:, "z"].to_numpy() == exact([0.0, 0.0, 0.0, 1000.0, 0.0])
    vt = mv.loc[:, "y"].to_numpy()
    assert vt[:4] == exact([-ROTATION_SPEED_KM_S] * 4)
    assert np.isnan(vt[4])

    flip = pd.Series({"x": -1.0, "y": -1.0, "z": 1.0})
    expected_b = plain.measurements.loc[:, "b"].multiply(flip, axis=1)
    assert ot.measurements.loc[:, "b"].to_numpy() == exact(expected_b.to_numpy())

    polarity = np.array([1.0, -1.0, -1.0, 1.0])
    raw_db = ot.data.loc[:, "b"].to_numpy()[:4]
    assert ot.bfield.to_numpy()[:4] == exact(raw_db * polarity[:, None])

    pdt.assert_frame_equal(v, v_before)
    pdt.assert_frame_equal(b, b_before)


def test_raffaella_version_without_a_spacecraft_raises_value_error():
    """The GSE-to-RTN aid needs the spacecraft position, and says so.

    ON FAILURE: the code is wrong.
    """
    v, b, rho, _ = _gse_inputs()
    with pytest.raises(ValueError, match="SC-Sun distance required"):
        turb.AlfvenicTurbulence(v, b, rho, "p1", raffaella_version=True)
