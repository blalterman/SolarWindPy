import pandas as pd
import numpy as np
import pytest

from solarwindpy import plasma
from solarwindpy.tests import test_base as base


@pytest.fixture(scope="session")
def plasma_data():
    return base.TestData().plasma_data.sort_index(axis=1)


@pytest.fixture(scope="session")
def spacecraft_data():
    return base.TestData().spacecraft_data


@pytest.fixture
def prepared_plasma(request, plasma_data):
    species = request.param
    plas = plasma.Plasma(plasma_data, *species.split("+"))
    par = plasma_data.w.par.pow(2)
    per = plasma_data.w.per.pow(2)
    scalar = ((2.0 * per) + par).multiply(1 / 3.0).pipe(np.sqrt)
    cols = scalar.columns.to_series().apply(lambda x: ("w", "scalar", x))
    scalar.columns = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
    data = pd.concat([plasma_data, scalar], axis=1, sort=True)
    return plas, data


@pytest.fixture(autouse=True)
def plasma_setup(request, plasma_data):
    """Automatically prepare Plasma objects for test classes."""
    cls = getattr(request, "cls", None)
    if cls is None or not hasattr(cls, "species"):
        return
    species_attr = getattr(cls, "species")
    if isinstance(species_attr, property):
        species = species_attr.fget(cls())
    else:
        species = species_attr
    plas = plasma.Plasma(plasma_data, *species.split("+"))
    par = plasma_data.w.par.pow(2)
    per = plasma_data.w.per.pow(2)
    scalar = ((2.0 * per) + par).multiply(1 / 3.0).pipe(np.sqrt)
    cols = scalar.columns.to_series().apply(lambda x: ("w", "scalar", x))
    scalar.columns = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
    data = pd.concat([plasma_data, scalar], axis=1, sort=True)
    cls.object_testing = plas
    cls.data = data
