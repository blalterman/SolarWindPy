#!/usr/bin/env python
"""Tests for the :class:`Ion` object."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from scipy import constants
from scipy.constants import physical_constants

from solarwindpy import ions, tensor, vector

pd.set_option("mode.chained_assignment", "raise")

DATA_PATH = Path(__file__).with_suffix("").parent / "data"


def _load_plasma_data() -> pd.DataFrame:
    """Return the sample plasma data used for testing."""
    epoch = pd.read_csv(DATA_PATH / "epoch.csv")["epoch"].map(pd.to_datetime)
    epoch.name = "epoch"
    plasma = pd.read_csv(DATA_PATH / "plasma.csv")
    plasma.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split("|")) for c in plasma.columns]
    )
    plasma = plasma.astype(float)
    plasma.columns.names = ["M", "C", "S"]
    plasma.index = epoch
    plasma = plasma.sort_index(axis=1)
    return plasma


def _ion_data(plasma: pd.DataFrame, species: str) -> pd.DataFrame:
    """Return the data for a single ion species."""
    data = plasma.xs(species, axis=1, level="S")
    coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
    scalar = data.w.pow(2).multiply(coeff, axis=1, level="C").sum(axis=1)
    scalar = scalar.pipe(np.sqrt)
    scalar.name = ("w", "scalar")
    out = pd.concat([data, scalar], axis=1, sort=True)
    out.columns = pd.MultiIndex.from_tuples(out.columns, names=["M", "C"])
    return out


def _mass(species: str) -> float:
    """Return the mass for ``species`` in kilograms."""
    mapping = {
        "a": "alpha particle",
        "p": "proton",
        "p1": "proton",
        "p2": "proton",
        "e": "electron",
    }
    return physical_constants[f"{mapping[species]} mass"][0]


def _mass_in_mp(species: str) -> float:
    """Return the mass ratio ``m / m_p`` for ``species``."""
    mapping = {
        "a": physical_constants["alpha particle-proton mass ratio"][0],
        "p": 1.0,
        "p1": 1.0,
        "p2": 1.0,
        "e": physical_constants["electron-proton mass ratio"][0],
    }
    return mapping[species]


@pytest.fixture(scope="module")
def plasma_data() -> pd.DataFrame:
    """Provide the full plasma data set."""
    return _load_plasma_data()


@pytest.fixture(params=["a", "p1", "p2"])
def ion_fixture(plasma_data: pd.DataFrame, request: pytest.FixtureRequest):
    """Return an ``Ion`` and its underlying data for several species."""
    species = request.param
    data = _ion_data(plasma_data, species)
    ion = ions.Ion(data, species)
    return species, ion, data


def test_species(ion_fixture):
    species, ion, _ = ion_fixture
    assert species == ion.species


def test_n(ion_fixture):
    species, ion, data = ion_fixture
    n = data.loc[:, ("n", "")]
    if not isinstance(n, pd.Series):
        assert n.shape[1] == 1
        n = n.iloc[:, 0]
    n.name = "n"
    pdt.assert_series_equal(n, ion.n)
    pdt.assert_series_equal(n, ion.number_density)
    pdt.assert_series_equal(ion.number_density, ion.n)


def test_mass_density(ion_fixture):
    species, ion, data = ion_fixture
    mmp = _mass_in_mp(species)
    rho = data.loc[:, pd.IndexSlice["n", ""]] * mmp
    rho.name = species
    if not isinstance(rho, pd.Series):
        assert rho.shape[1] == 1
        rho = rho.iloc[:, 0]
    rho.name = "rho"
    pdt.assert_series_equal(ion.rho, ion.mass_density)
    pdt.assert_series_equal(rho, ion.rho)
    pdt.assert_series_equal(rho, ion.mass_density)


def test_v(ion_fixture):
    _, ion, data = ion_fixture
    v = vector.Vector(data.v)
    assert v == ion.velocity
    assert v == ion.v
    assert ion.velocity == ion.v


def test_w(ion_fixture):
    _, ion, data = ion_fixture
    w = tensor.Tensor(data.w)
    assert w == ion.thermal_speed
    assert w == ion.w
    assert ion.w == ion.thermal_speed


def test_anisotropy(ion_fixture):
    _, ion, data = ion_fixture
    w = data.w
    ani = (w.per / w.par).pow(2)
    ani.name = "RT"
    pdt.assert_series_equal(ani, ion.anisotropy)


def test_pth(ion_fixture):
    species, ion, data = ion_fixture
    n = data.n * 1e6
    w = data.w * 1e3
    m = _mass(species)
    p = w.pow(2).multiply(0.5 * n * m, axis=0) / 1e-12
    pdt.assert_frame_equal(p, ion.pth)


def test_temperature(ion_fixture):
    species, ion, data = ion_fixture
    m = _mass(species)
    w = data.w * 1e3
    kb = physical_constants["Boltzmann constant"][0]
    t = (0.5 * m / kb) * w.pow(2) / 1e5
    pdt.assert_frame_equal(t, ion.temperature)


def test_specific_entropy(ion_fixture):
    species, ion, data = ion_fixture
    rho = _mass(species) * data.n * 1e6
    w = data.w.xs("scalar", axis=1) * 1e3
    pth = w.pow(2).multiply(0.5 * rho, axis=0)
    gamma = 5.0 / 3.0
    units = 1e4 / constants.e
    S = pth.multiply(rho.pow(-gamma)) / units
    S.name = "S"
    pdt.assert_series_equal(S, ion.specific_entropy)
    pdt.assert_series_equal(S, ion.S)
    pdt.assert_series_equal(ion.S, ion.specific_entropy)


@pytest.mark.parametrize("species", ["a", "p1", "p2"])
def test_init_with_species(plasma_data: pd.DataFrame, species: str):
    data = plasma_data.xs(species, axis=1, level="S")
    ion = ions.Ion(data, species)
    assert isinstance(ion, ions.Ion)
    assert ion.species == species
    pdt.assert_frame_equal(data, ion.data)


@pytest.mark.parametrize("species", ["a", "p1", "p2"])
def test_init_version_comparison(plasma_data: pd.DataFrame, species: str):
    data_with_species = plasma_data.xs(species, axis=1, level="S", drop_level=False)
    data_without_species = plasma_data.xs(species, axis=1, level="S")
    ion_with_species = ions.Ion(data_with_species, species)
    ion_without_species = ions.Ion(data_without_species, species)
    assert ion_with_species == ion_without_species


@pytest.mark.parametrize(
    "s0,s1,expected",
    [
        ("a", "a", True),
        ("p1", "p1", True),
        ("p2", "p2", True),
        ("a", "p1", False),
        ("p1", "a", False),
        ("a", "p2", False),
        ("p2", "p1", False),
    ],
)
def test_eq(plasma_data: pd.DataFrame, s0: str, s1: str, expected: bool):
    i0 = ions.Ion(plasma_data, s0)
    i1 = ions.Ion(plasma_data, s1)
    if expected:
        assert i0 == i1
    else:
        assert i0 != i1
