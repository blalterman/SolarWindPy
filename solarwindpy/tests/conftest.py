import pytest
from solarwindpy.tests import test_base as base


@pytest.fixture(scope="module")
def swe_data_values():
    data = base.TestData()
    plasma = data.plasma_data.sort_index(axis=1)
    spacecraft = data.spacecraft_data
    return plasma, spacecraft


@pytest.fixture(scope="module")
def plasma_data(swe_data_values):
    return swe_data_values[0]


@pytest.fixture(scope="module")
def spacecraft_data(swe_data_values):
    return swe_data_values[1]


@pytest.fixture(scope="class")
def swe_data(request, plasma_data, spacecraft_data):
    cls = request.cls
    cls.data = plasma_data
    cls.spacecraft_data = spacecraft_data
    if hasattr(cls, "set_object_testing"):
        cls.set_object_testing()
    yield
