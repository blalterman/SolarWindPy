import importlib

from solarwindpy import instabilities


def test_instabilities_all():
    expected = {"verscharen2016", "beta_ani"}
    assert set(instabilities.__all__) == expected
    # ensure modules import correctly via __all__
    for name in expected:
        assert isinstance(
            importlib.import_module(f"solarwindpy.instabilities.{name}"), object
        )
