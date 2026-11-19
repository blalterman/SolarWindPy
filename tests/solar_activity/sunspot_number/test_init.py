"""The ``solarwindpy.solar_activity.sunspot_number`` package entry point."""

import pytest

import solarwindpy.solar_activity.sunspot_number as sunspot_number


@pytest.mark.parametrize("name", sunspot_number.__all__)
def test_every_exported_name_resolves(name):
    """Every name in ``__all__`` is an attribute of the package.

    ON FAILURE: the code is wrong.
    """
    assert getattr(sunspot_number, name) is not None
