#!/usr/bin/env python
"""Tests for :mod:`solarwindpy.core.units_constants`.

Every expected value comes from outside the module under test:

- the exact defining constants of the 2019 SI, typed from the BIPM SI Brochure,
  9th edition (2019), Table 1;
- CODATA values looked up by name in ``scipy.constants.physical_constants``;
- IAU nominal values, each cited on its line;
- a dimensional identity built from ``scipy.constants`` SI prefixes, or a
  hand-computed case.

Species and ``Units`` fields are enumerated from the objects themselves, so a
new species or field without an expected value fails rather than going
untested.
"""

import dataclasses
import math

import pytest
from scipy import constants
from scipy.constants import physical_constants

from solarwindpy.core import units_constants as uc
from tests.tolerances import CODATA_JOINT_DECIMALS, exact, printed

# Defining constants of the 2019 SI, exact by definition (BIPM SI Brochure, 9th
# ed., 2019, Table 1).
SI_C = 299_792_458.0  # [m s^-1]
SI_H = 6.62607015e-34  # [J s]
SI_E = 1.602176634e-19  # [C]
SI_K = 1.380649e-23  # [J K^-1]
SI_NA = 6.02214076e23  # [mol^-1]

# IAU 2012 Resolution B2: the astronomical unit is exactly 149 597 870 700 m.
IAU_2012_AU = 149_597_870_700.0  # [m]

# IAU 2015 Resolution B3 nominal values, Prsa et al. (2016), AJ 152, 41,
# doi:10.3847/0004-6256/152/2/41.
IAU_2015_SOLAR_RADIUS = 695.7e6  # [m]
IAU_2015_EARTH_EQUATORIAL_RADIUS = 6.3781e6  # [m]


# Species label -> CODATA particle name. The label's first letter names the particle
# ("p1", "pm", "p_bimax" are protons; "a2", "a_bimax" are alpha particles).
PARTICLE = {"p": "proton", "a": "alpha particle", "e": "electron"}

# Charge number of each particle: proton +1, electron -1, alpha particle = He
# nucleus, Z = 2.
CHARGE_NUMBER = {"proton": 1.0, "electron": -1.0, "alpha particle": 2.0}

SPECIES = list(uc.Constants().m.index)


def particle(species):
    """Return the CODATA particle name for a SolarWindPy species label."""
    return PARTICLE[species[0]]


def codata(name):
    """Return the CODATA value named ``name``."""
    return physical_constants[name][0]


# Expected value of every entry in `Constants().misc`, with its source.
MISC_EXPECTED = {
    "e0": codata("vacuum electric permittivity"),  # CODATA
    "mu0": codata("vacuum mag. permeability"),  # CODATA
    "c": SI_C,  # SI defining constant
    "hbar": SI_H / (2 * math.pi),  # SI defining constant h over 2 pi
    "1AU [m]": IAU_2012_AU,  # IAU 2012 Resolution B2
    "Re [m]": IAU_2015_EARTH_EQUATORIAL_RADIUS,  # IAU 2015 Resolution B3
    "Rs [m]": IAU_2015_SOLAR_RADIUS,  # IAU 2015 Resolution B3
    "gas constant": SI_NA * SI_K,  # R = N_A k, exact in the 2019 SI
}

PROTON_MASS = codata("proton mass")

# SI value of one display unit for every `Units` field. Source: the `Units`
# docstring's stated unit, rebuilt from scipy.constants SI prefixes.
DISPLAY_UNIT_IN_SI = {
    "bfield": constants.nano,  # nT
    "b": constants.nano,  # nT, the magnetic field
    "v": constants.kilo,  # km s^-1
    "w": constants.kilo,  # km s^-1, thermal speed
    "dv": constants.kilo,  # km s^-1, differential flow
    "ca": constants.kilo,  # km s^-1, Alfven speed
    "cs": constants.kilo,  # km s^-1, sound speed
    "cfms": constants.kilo,  # km s^-1, fast magnetosonic speed
    "pth": constants.pico,  # pPa
    "temperature": 1e5,  # 10^5 K
    "n": constants.centi**-3,  # cm^-3
    "rho": PROTON_MASS * constants.centi**-3,  # m_p cm^-3
    "beta": 1.0,  # dimensionless
    "lnlambda": 1.0,  # dimensionless
    "nuc": 1e-7,  # 10^-7 Hz
    "nc": 1.0,  # dimensionless count
    "qpar": constants.micro,  # uW m^-2
    "kinetic_energy_flux": constants.micro,  # uW m^-2
    "distance2sun": 1.0,  # m
    # eV cm^2 m_p^-5/3
    "specific_entropy": codata("electron volt")
    * constants.centi**2
    * PROTON_MASS ** (-5.0 / 3.0),
}


# --- Constants: fundamental and astronomical ---------------------------------


@pytest.mark.parametrize("key", list(uc.Constants().misc.index))
def test_misc_constant_matches_its_published_value(key):
    """Each `Constants().misc` entry equals its SI, CODATA, or IAU value.

    Sources are listed in `MISC_EXPECTED`; a key missing there raises KeyError.

    ON FAILURE: the code is wrong, unless a new key lacks an entry in
    MISC_EXPECTED; add its published value with the source on the line.
    """
    assert uc.Constants().misc[key] == exact(MISC_EXPECTED[key])


def test_hbar_is_codata_reduced_planck_constant():
    """`hbar` equals the CODATA reduced Planck constant.

    ON FAILURE: the code is wrong.
    """
    assert uc.Constants().misc["hbar"] == exact(codata("reduced Planck constant"))


def test_permittivity_permeability_and_c_satisfy_e0_mu0_c2_equals_one():
    """Maxwell's identity epsilon_0 mu_0 c^2 = 1 holds for the stored constants.

    ON FAILURE: the code is wrong.
    """
    misc = uc.Constants().misc
    assert misc["e0"] * misc["mu0"] * misc["c"] ** 2 == printed(
        1.0, decimals=CODATA_JOINT_DECIMALS
    )


def test_boltzmann_constant_in_joules_is_the_si_defining_value():
    """`kb["J"]` is the exact SI Boltzmann constant.

    ON FAILURE: the code is wrong.
    """
    assert uc.Constants().kb["J"] == exact(SI_K)


def test_boltzmann_constant_in_ev_is_k_over_e():
    """`kb["eV"]` is k / e, and matches CODATA's Boltzmann constant in eV/K.

    ON FAILURE: the code is wrong.
    """
    kb_ev = uc.Constants().kb["eV"]
    assert kb_ev == exact(SI_K / SI_E)
    assert kb_ev == exact(codata("Boltzmann constant in eV/K"))


# --- Constants: per-species tables -------------------------------------------


def test_every_species_table_covers_the_same_species():
    """Masses, mass ratios, charges, and charge states name the same species.

    ON FAILURE: the code is wrong.
    """
    c = uc.Constants()
    expected = set(c.m.index)
    for table in (c.m_amu, c.m_in_mp, c.charges, c.charge_states):
        assert set(table.index) == expected


@pytest.mark.parametrize("species", SPECIES)
def test_species_mass_matches_codata(species):
    """`m[species]` is the CODATA mass of that species' particle, in kg.

    ON FAILURE: the code is wrong.
    """
    expected = codata(f"{particle(species)} mass")
    assert uc.Constants().m[species] == exact(expected)


@pytest.mark.parametrize("species", SPECIES)
def test_species_mass_in_u_matches_codata(species):
    """`m_amu[species]` is the CODATA mass of that particle in atomic mass units.

    ON FAILURE: the code is wrong.
    """
    expected = codata(f"{particle(species)} mass in u")
    assert uc.Constants().m_amu[species] == exact(expected)


@pytest.mark.parametrize("species", SPECIES)
def test_mass_in_u_times_atomic_mass_constant_is_mass_in_kg(species):
    """`m_amu * m_u` reproduces `m`, tying the two mass tables together.

    ON FAILURE: the code is wrong.
    """
    c = uc.Constants()
    m_u = codata("atomic mass constant")
    assert c.m_amu[species] * m_u / c.m[species] == printed(
        1.0, decimals=CODATA_JOINT_DECIMALS
    )


@pytest.mark.parametrize("species", SPECIES)
def test_mass_in_proton_masses_is_mass_over_proton_mass(species):
    """`m_in_mp` equals `m / m_p` and the CODATA mass ratio to the proton.

    ON FAILURE: the code is wrong.
    """
    c = uc.Constants()
    ratio = c.m_in_mp[species]
    assert ratio / (c.m[species] / PROTON_MASS) == printed(
        1.0, decimals=CODATA_JOINT_DECIMALS
    )
    name = particle(species)
    if name == "proton":
        # A proton is one proton mass by definition.
        assert ratio == 1.0
    else:
        assert ratio == exact(codata(f"{name}-proton mass ratio"))


@pytest.mark.parametrize("species", SPECIES)
def test_charge_state_is_the_particle_charge_number(species):
    """`charge_states[species]` is the particle's charge number (e -1, p +1, a +2).

    ON FAILURE: the code is wrong.
    """
    expected = CHARGE_NUMBER[particle(species)]
    assert uc.Constants().charge_states[species] == expected


@pytest.mark.parametrize("species", SPECIES)
def test_charge_is_charge_state_times_elementary_charge(species):
    """`charges[species]` is the charge number times the exact SI e, in C.

    ON FAILURE: the code is wrong.
    """
    expected = CHARGE_NUMBER[particle(species)] * SI_E
    assert uc.Constants().charges[species] == exact(expected)


def test_polytropic_indices_are_the_double_adiabatic_and_adiabatic_values():
    """Polytropic indices are gamma = (f + 2) / f for f degrees of freedom.

    f = 1 gives gamma_par = 3 and f = 2 gives gamma_perp = 2, the double-adiabatic
    (CGL) values of Chew, Goldberger & Low (1956), Proc. R. Soc. A 236, 112,
    doi:10.1098/rspa.1956.0116; f = 3 gives the isotropic 5/3.

    ON FAILURE: the code is wrong, unless the author rejects gamma = (f + 2) / f.
    """
    # Degrees of freedom per case; an unknown key raises KeyError.
    degrees_of_freedom = {"par": 1, "per": 2, "scalar": 3}
    gamma = uc.Constants().polytropic_index
    for key in gamma.index:
        f = degrees_of_freedom[key]
        assert gamma[key] == exact((f + 2) / f)


def test_constants_rejects_a_table_that_is_not_a_series():
    """`Constants` raises TypeError when a table is not a pandas Series.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="must be pandas Series"):
        uc.Constants(misc={"c": SI_C})


# --- Units: display units and dimensional identities -------------------------


@pytest.mark.parametrize("name", [f.name for f in dataclasses.fields(uc.Units)])
def test_units_field_is_one_display_unit_in_si(name):
    """Each `Units` field is the SI value of its documented display unit.

    Expected values are in `DISPLAY_UNIT_IN_SI`; a field missing there raises
    KeyError.

    ON FAILURE: the code is wrong, unless a new field lacks an entry in
    DISPLAY_UNIT_IN_SI; add its display unit built from scipy.constants.
    """
    assert getattr(uc.Units(), name) == exact(DISPLAY_UNIT_IN_SI[name])


def test_pressure_unit_is_consistent_with_n_k_t():
    """p = n k T: 1 cm^-3 at 10^5 K is 1e6 * 1.380649e-23 * 1e5 Pa = 1.380649 pPa.

    Hand-computed with the exact SI k.

    ON FAILURE: the code is wrong.
    """
    u = uc.Units()
    kb = uc.Constants().kb["J"]
    p = (1.0 * u.n) * kb * (1.0 * u.temperature) / u.pth
    assert p == exact(1.380649)


def test_temperature_unit_is_8_617_ev():
    """k * (10^5 K) = 8.617333262 eV (CODATA k in eV/K, published to 10 digits).

    ON FAILURE: the code is wrong.
    """
    kt = uc.Units().temperature * uc.Constants().kb["eV"]
    assert kt == printed(8.617333262, decimals=9)


def test_kinetic_energy_flux_of_5_per_cc_protons_at_400_km_s_is_267_6_uw_m2():
    """(1/2) rho v^3 for 5 cm^-3 protons at 400 km/s is 267.6 uW m^-2.

    Hand-computed: 0.5 * 5e6 m^-3 * 1.6726e-27 kg * (4e5 m/s)^3 = 2.676e-4 W m^-2.

    ON FAILURE: the code is wrong.
    """
    u = uc.Units()
    rho = 5.0 * u.rho
    v = 400.0 * u.v
    flux = 0.5 * rho * v**3 / u.kinetic_energy_flux
    assert flux == printed(267.6, decimals=1)


def test_specific_entropy_unit_is_p_over_rho_to_five_thirds():
    """1 cm^-3 protons at kT = 1 eV have p / rho^(5/3) = 1 eV cm^2 m_p^-5/3.

    p = 1 eV cm^-3 and rho = 1 m_p cm^-3, so p / rho^(5/3) is one display unit,
    computed here in SI from the `Units` density and mass-density units.

    ON FAILURE: the code is wrong.
    """
    u = uc.Units()
    p = u.n * codata("electron volt")  # 1 eV per cm^3, in Pa
    s = p / u.rho ** (5.0 / 3.0)
    assert s / u.specific_entropy == exact(1.0)
