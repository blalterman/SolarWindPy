import numpy as np
import pandas.testing as pdt
import pytest
from scipy import constants

SPECIES_COMBINATIONS = ["a", "p1", "p2", "a+p1", "a+p2", "p1+p2", "a+p1+p2"]


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_str(species, turbulence_data):
    ot = turbulence_data["object"]
    assert ot.__class__.__name__ == "AlfvenicTurbulence"
    assert turbulence_data["species"] == species


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_clean_species_for_setting(species, turbulence_data):
    ot = turbulence_data["object"]
    test_fcn = ot._clean_species_for_setting
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
        assert test_fcn(stest) == stest

    with pytest.raises(ValueError):
        test_fcn("a,p1,p2")
    with pytest.raises(TypeError):
        test_fcn("a", "p1", "p2")


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_data(species, turbulence_data):
    data = turbulence_data["data"].drop("r", axis=1, level="M")
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(data, ot.data)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_measurements(species, turbulence_data):
    measurements = turbulence_data["unrolled"].drop("r", axis=1, level="M")
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(measurements, ot.measurements)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_bfield(species, turbulence_data):
    b = turbulence_data["data"].loc[:, "b"]
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(b, ot.bfield)
    pdt.assert_frame_equal(ot.bfield, ot.b)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_velocity(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(v, ot.velocity)
    pdt.assert_frame_equal(ot.v, ot.velocity)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_z_plus(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    zp = v.add(b, axis=1)
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(zp, ot.z_plus)
    pdt.assert_frame_equal(ot.zp, ot.z_plus)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_z_minus(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    zm = v.subtract(b, axis=1)
    ot = turbulence_data["object"]
    pdt.assert_frame_equal(zm, ot.z_minus)
    pdt.assert_frame_equal(ot.zm, ot.z_minus)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_e_plus(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    zp = v.add(b, axis=1)
    ep = 0.5 * zp.pow(2).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(ep, ot.e_plus)
    pdt.assert_series_equal(ot.ep, ot.e_plus)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_e_minus(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    zm = v.subtract(b, axis=1)
    em = 0.5 * zm.pow(2).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(em, ot.e_minus)
    pdt.assert_series_equal(ot.em, ot.e_minus)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_kinetic_energy(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    ev = 0.5 * v.pow(2).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(ev, ot.kinetic_energy)
    pdt.assert_series_equal(ot.kinetic_energy, ot.ev)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_magnetic_energy(species, turbulence_data):
    b = turbulence_data["data"].loc[:, "b"]
    eb = 0.5 * b.pow(2).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(eb, ot.magnetic_energy)
    pdt.assert_series_equal(ot.magnetic_energy, ot.eb)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_total_energy(species, turbulence_data):
    tk = ["v", "b"]
    etot = 0.5 * turbulence_data["data"].loc[:, tk].pow(2).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(etot, ot.total_energy)
    pdt.assert_series_equal(ot.total_energy, ot.etot)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_residual_energy(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    ev = 0.5 * v.pow(2).sum(axis=1)
    b = turbulence_data["data"].loc[:, "b"]
    eb = 0.5 * b.pow(2).sum(axis=1)
    eres = ev.subtract(eb, axis=0)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(eres, ot.residual_energy)
    pdt.assert_series_equal(ot.residual_energy, ot.eres)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_normalized_residual_energy(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    ev = 0.5 * v.pow(2).sum(axis=1)
    b = turbulence_data["data"].loc[:, "b"]
    eb = 0.5 * b.pow(2).sum(axis=1)
    etot = ev.add(eb, axis=0)
    eres = ev.subtract(eb, axis=0)
    eres_norm = eres.divide(etot, axis=0)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(eres_norm, ot.normalized_residual_energy)
    pdt.assert_series_equal(ot.normalized_residual_energy, ot.eres_norm)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_cross_helicity(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    ch = 0.5 * v.multiply(b, axis=1).sum(axis=1)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(ch, ot.cross_helicity)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_normalized_cross_helicity(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    ch = 0.5 * v.multiply(b, axis=1).sum(axis=1)
    ev = 0.5 * v.pow(2).sum(axis=1)
    eb = 0.5 * b.pow(2).sum(axis=1)
    etot = ev.add(eb, axis=0)
    normalized_cross_helicity = 2.0 * ch.divide(etot, axis=0)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(normalized_cross_helicity, ot.normalized_cross_helicity)
    pdt.assert_series_equal(ot.sigma_c, ot.normalized_cross_helicity)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_alfven_ratio(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    ev = 0.5 * v.pow(2).sum(axis=1)
    eb = 0.5 * b.pow(2).sum(axis=1)
    rA = ev.divide(eb, axis=0)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(rA, ot.alfven_ratio)
    pdt.assert_series_equal(ot.alfven_ratio, ot.rA)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_elsasser_ratio(species, turbulence_data):
    v = turbulence_data["data"].loc[:, "v"]
    b = turbulence_data["data"].loc[:, "b"]
    zp = v.add(b, axis=1)
    zm = v.subtract(b, axis=1)
    ep = 0.5 * zp.pow(2).sum(axis=1)
    em = 0.5 * zm.pow(2).sum(axis=1)
    rE = em.divide(ep, axis=0)
    ot = turbulence_data["object"]
    pdt.assert_series_equal(rE, ot.elsasser_ratio)
    pdt.assert_series_equal(ot.elsasser_ratio, ot.rE)


@pytest.mark.parametrize("species", SPECIES_COMBINATIONS)
def test_eq(species, turbulence_data):
    ot = turbulence_data["object"]
    assert ot == ot
    data = turbulence_data["unrolled"]
    v = data.loc[:, "v"]
    r = data.loc[:, ("r", species)]
    b = data.loc[:, "b"]
    coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
    b_nT = b.multiply(np.sqrt(r), axis=0) / coef
    new_obj = ot.__class__(
        v,
        b_nT,
        r,
        ot.species,
        window=turbulence_data["window"],
        min_periods=turbulence_data["periods"],
    )
    assert ot.species == new_obj.species
    pdt.assert_frame_equal(ot.data, new_obj.data)
    try:
        assert ot == new_obj
    except AssertionError as e0:
        try:
            pdt.assert_frame_equal(ot.data.round(15), new_obj.data.round(15))
        except AssertionError:
            raise e0
