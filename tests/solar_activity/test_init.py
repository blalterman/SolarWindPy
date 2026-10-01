"""The ``solarwindpy.solar_activity`` package entry point."""

import pytest

import solarwindpy.solar_activity as sa


@pytest.mark.parametrize("name", sa.__all__)
def test_every_exported_name_resolves(name):
    """Every name in ``__all__`` is an attribute of the package.

    ON FAILURE: the code is wrong.
    """
    assert getattr(sa, name) is not None
