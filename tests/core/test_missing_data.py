# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The missing-data rule (docs/source/missing_data.rst) across core/.

A quantity computed from a fixed set of inputs (a magnitude, a component sum,
a par and per product) needs every input. Only additive totals over species or
time may be partial, and an empty reduction is NaN.

The example plasma has no missing values, so each case masks values in a copy
of its data before building the object, letting ``Plasma.set_data`` mask the
species as it would for real data.
"""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

import solarwindpy as swp
from solarwindpy.core import alfvenic_turbulence as turb
from solarwindpy.core.plasma import Plasma
from solarwindpy.core.spacecraft import Spacecraft
from tests.tolerances import exact

XFAIL_ANISOTROPY = pytest.mark.xfail(
    strict=True, reason="M1: Plasma.anisotropy skips missing par or per"
)
XFAIL_DISTANCE = pytest.mark.xfail(
    strict=True, reason="M1: Spacecraft.distance2sun skips missing components"
)
XFAIL_TURBULENCE = pytest.mark.xfail(
    strict=True, reason="M1: AlfvenicTurbulence sums skip missing components"
)


def _species_masked_plasma():
    r"""Example plasma with p1 missing at row 0, a at row 1, and both at row 2."""
    base = swp.examples.load_plasma()
    data = base.data.copy()
    t = data.index
    data.loc[t[0], ("w", "par", "p1")] = np.nan
    data.loc[t[1], ("w", "per", "a")] = np.nan
    data.loc[t[2], ("w", "par", "p1")] = np.nan
    data.loc[t[2], ("w", "per", "a")] = np.nan
    return Plasma(data, *base.species, spacecraft=base.spacecraft)


def _position_masked_plasma():
    r"""Example plasma whose spacecraft position x is missing at row 0."""
    base = swp.examples.load_plasma()
    sc = base.spacecraft.data.copy()
    sc.loc[sc.index[0], ("pos", "x")] = np.nan
    spacecraft = Spacecraft(sc, base.spacecraft.name, base.spacecraft.frame)
    return Plasma(base.data, *base.species, spacecraft=spacecraft)


@XFAIL_ANISOTROPY
def test_one_species_anisotropy_matches_the_ion_and_is_nan_where_masked():
    r"""``anisotropy("p1")`` equals ``p1.anisotropy``, NaN where p1 is masked.

    ON FAILURE: the code is wrong.
    """
    plasma = _species_masked_plasma()
    ani = plasma.anisotropy("p1")
    assert np.isnan(ani.iloc[[0, 2]]).all()
    pdt.assert_series_equal(ani, plasma.p1.anisotropy, check_names=False)


@XFAIL_ANISOTROPY
def test_several_species_anisotropy_matches_each_ion():
    r"""Column s of ``anisotropy("a", "p1")`` equals ``plasma.s.anisotropy``.

    ON FAILURE: the code is wrong.
    """
    plasma = _species_masked_plasma()
    ani = plasma.anisotropy("a", "p1")
    for s in ("a", "p1"):
        expected = plasma.ions.loc[s].anisotropy
        pdt.assert_series_equal(ani.loc[:, s], expected, check_names=False)


@XFAIL_ANISOTROPY
def test_total_anisotropy_is_nan_where_no_species_is_present():
    r"""``anisotropy("a+p1")`` is NaN, not the empty product 1, with no species.

    ON FAILURE: the code is wrong.
    """
    assert np.isnan(_species_masked_plasma().anisotropy("a+p1").iloc[2])


def test_total_anisotropy_stays_partial_over_species():
    r"""``anisotropy("a+p1")`` uses the species present at each time.

    Where p1 is masked the total is the alpha value, and where a is masked it
    is the proton value.

    ON FAILURE: the code is wrong.
    """
    plasma = _species_masked_plasma()
    ani = plasma.anisotropy("a+p1")
    assert ani.iloc[0] == exact(plasma.a.anisotropy.iloc[0])
    assert ani.iloc[1] == exact(plasma.p1.anisotropy.iloc[1])


@XFAIL_DISTANCE
def test_distance_to_the_sun_is_the_position_magnitude():
    r"""``distance2sun`` is NaN exactly where ``position.mag`` is.

    In HCI it equals ``position.mag`` times the solar radius over the
    distance unit, at every row.

    ON FAILURE: the code is wrong.
    """
    sc = _position_masked_plasma().spacecraft
    assert sc.frame == "HCI"
    mag = sc.position.mag
    assert mag.isna().tolist() == [True, False, False]
    expected = mag * sc.constants.misc.loc["Rs [m]"] / sc.units.distance2sun
    pdt.assert_series_equal(sc.distance2sun, expected, check_names=False)


@XFAIL_DISTANCE
def test_coulomb_number_is_nan_where_the_position_is_missing():
    r"""``Plasma.nc`` is NaN where a position component is missing.

    ON FAILURE: the code is wrong.
    """
    nc = _position_masked_plasma().nc("a", "p1")
    assert nc.isna().tolist() == [True, False, False]


def _turbulence():
    r"""Four hourly samples with v_x missing at row 1 and b_z at row 2."""
    t = pd.date_range("2020-01-01", periods=4, freq="h")
    cols = pd.Index(["x", "y", "z"], name="C")
    v = pd.DataFrame(
        [[100.0, 200, 300], [400, 500, 600], [700, 800, 900], [300, 100, 200]],
        index=t,
        columns=cols,
        dtype=float,
    )
    b = pd.DataFrame(
        [[1.0, -2, 3], [2, 1, 0], [0, 3, 1], [1, 1, 1]],
        index=t,
        columns=cols,
        dtype=float,
    )
    v.iloc[1, 0] = np.nan
    b.iloc[2, 2] = np.nan
    rho = pd.Series(1.0, index=t)
    return turb.AlfvenicTurbulence(
        v, b, rho, "p1", window="10h", min_periods=1, center=True
    )


@XFAIL_TURBULENCE
@pytest.mark.parametrize(
    "energy, vector, missing",
    [
        ("e_plus", "zp", [1, 2]),
        ("e_minus", "zm", [1, 2]),
        ("kinetic_energy", "v", [1]),
        ("magnetic_energy", "b", [2]),
    ],
)
def test_each_energy_is_half_the_squared_magnitude_of_its_vector(
    energy, vector, missing
):
    r"""An energy is NaN where a component of its vector is missing.

    Elsewhere it is finite and equals half that vector's squared magnitude.

    ON FAILURE: the code is wrong.
    """
    ot = _turbulence()
    e = getattr(ot, energy)
    assert e.isna().to_numpy().nonzero()[0].tolist() == missing
    expected = 0.5 * getattr(ot, vector).pow(2).sum(axis=1, skipna=False)
    pdt.assert_series_equal(e, expected, check_names=False)


@XFAIL_TURBULENCE
def test_cross_helicity_is_nan_where_a_component_is_missing():
    r"""``cross_helicity`` is NaN where a component of v or b is missing.

    ON FAILURE: the code is wrong.
    """
    ot = _turbulence()
    c = ot.cross_helicity
    assert c.isna().tolist() == [False, True, True, False]
    expected = 0.5 * ot.v.multiply(ot.b).sum(axis=1, skipna=False)
    pdt.assert_series_equal(c, expected, check_names=False)


@XFAIL_TURBULENCE
def test_raffaella_polarity_and_field_are_nan_where_a_component_is_missing():
    r"""The polarity and ``bfield`` are NaN where v_T is missing.

    The spacecraft position z is missing at the last row, so the rotation
    correction, and with it v_T, is NaN there. Rows 0 to 3 keep the polarity
    +1, -1, -1, +1.

    ON FAILURE: the code is wrong.
    """
    t = pd.date_range("2020-01-01", periods=5, freq="h")
    cols = pd.Index(["x", "y", "z"], name="C")
    v = pd.DataFrame(
        [[-400.0, 0, 0], [-400, 0, 0], [-100, 0, 0], [-400, 0, 1000], [-400, 0, 0]],
        index=t,
        columns=cols,
        dtype=float,
    )
    b = pd.DataFrame(
        [[-1.0, 0, 0], [1, 0, 0], [-1, -5, 0], [-1, 0, -1], [0, 0, 0]],
        index=t,
        columns=cols,
        dtype=float,
    )
    rho = pd.Series(1.0, index=t)
    pos = pd.DataFrame({"x": 3.0, "y": 0.0, "z": 4.0}, index=t)
    pos.iloc[4, 2] = np.nan
    pos.columns = pd.MultiIndex.from_product(
        [["pos"], ["x", "y", "z"]], names=["M", "C"]
    )
    sc = Spacecraft(pos, "wind", "gse")

    ot = turb.AlfvenicTurbulence(
        v,
        b,
        rho,
        "p1",
        raffaella_version=True,
        sc_vector=sc,
        window="10h",
        min_periods=1,
        center=True,
    )
    assert ot.polarity.iloc[:4].tolist() == [1.0, -1.0, -1.0, 1.0]
    assert np.isnan(ot.polarity.iloc[4])
    assert ot.bfield.iloc[4].isna().all()
    assert ot.bfield.iloc[:4].notna().all().all()
