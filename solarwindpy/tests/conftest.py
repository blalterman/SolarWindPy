import importlib.util
from pathlib import Path

import pandas as pd
import numpy as np
import pytest
from scipy import constants
from scipy.constants import physical_constants

_base_spec = importlib.util.spec_from_file_location(
    "test_base", Path(__file__).parent / "test_base.py"
)
test_base = importlib.util.module_from_spec(_base_spec)
assert _base_spec.loader is not None
_base_spec.loader.exec_module(test_base)
TestData = test_base.TestData

import sys

_turb_path = Path(__file__).resolve().parent.parent / "core" / "alfvenic_turbulence.py"
sys.path.insert(0, str(_turb_path.parent))
_turb_spec = importlib.util.spec_from_file_location("alfvenic_turbulence", _turb_path)
turb = importlib.util.module_from_spec(_turb_spec)
assert _turb_spec.loader is not None
_turb_spec.loader.exec_module(turb)

SPECIES_COMBINATIONS = [
    "a",
    "p1",
    "p2",
    "a+p1",
    "a+p2",
    "p1+p2",
    "a+p1+p2",
]


@pytest.fixture(scope="session")
def swe_data():
    """Return plasma test data."""
    return TestData().plasma_data.sort_index(axis=1)


@pytest.fixture(params=SPECIES_COMBINATIONS)
def species(request):
    """Parameterized species combinations."""
    return request.param


@pytest.fixture
def turbulence_data(species, swe_data):
    """Construct `AlfvenicTurbulence` and helper data for tests."""
    sp = species.split("+")
    data = (
        pd.concat(
            {s: swe_data.xs(s, axis=1, level="S") for s in sp}, axis=1, names=["S"]
        )
        .swaplevel(i="M", j="S", axis=1)
        .swaplevel(i="S", j="C", axis=1)
        .sort_index(axis=1)
    )

    tkb = ["x", "y", "z"]
    b = swe_data.xs("b", axis=1, level="M").xs("", axis=1, level="S").loc[:, tkb]

    tkv = pd.IndexSlice["v", ["x", "y", "z"], sp]
    v = swe_data.loc[:, tkv]

    n = swe_data.loc[:, "n"].loc[:, ""].loc[:, sp]

    trans = {
        "a": physical_constants["alpha particle-proton mass ratio"][0],
        "p": 1,
        "p1": 1,
        "p2": 1,
        "e": physical_constants["electron-proton mass ratio"][0],
    }
    m_mp = pd.Series({s: trans[s] for s in sp})
    r = n.multiply(m_mp)
    rtot = r.sum(axis=1)

    vcom = (
        v.multiply(r, axis=1, level="S")
        .T.groupby(level="C")
        .sum()
        .T.divide(rtot, axis=0)
    )

    coef = 1e-9 / (np.sqrt(constants.mu_0 * constants.m_p * 1e6) * 1e3)
    b_ca_units = coef * b.divide(np.sqrt(rtot), axis=0)

    window = "365d"
    periods = 1
    obj = turb.AlfvenicTurbulence(
        vcom, b, rtot, "+".join(sp), window=window, min_periods=periods
    )

    combined = pd.concat(
        {"v": vcom, "b": b_ca_units, "r": rtot.to_frame(name="+".join(sp))},
        axis=1,
        names=["M", "C"],
    ).sort_index(axis=1)
    rolled = combined.rolling(window=window, min_periods=periods).agg("mean")
    deltas = combined.subtract(rolled, axis=1)

    combined.name = "measurements"
    deltas.name = "deltas"

    return {
        "object": obj,
        "data": deltas,
        "unrolled": combined,
        "window": window,
        "periods": periods,
        "species": species,
    }
