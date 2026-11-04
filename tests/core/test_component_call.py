"""Calling a Vector or Tensor with a component label returns that component.

The expected values come from the plasma frame, not from the object under
test, so the tests do not compare the implementation against itself.
"""

import pandas.testing as pdt
import pytest

import solarwindpy as swp

B1_REASON = "B1: __call__ delegates to an undefined __getattr__"


@pytest.fixture(scope="module")
def plasma():
    return swp.examples.load_plasma()


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=B1_REASON)
@pytest.mark.parametrize("component", ["x", "y", "z"])
def test_bfield_call_returns_component(plasma, component):
    """``plasma.b(c)`` is the plasma frame's ``("b", c, "")`` column.

    ON FAILURE: the code is wrong.
    """
    expected = plasma.data.loc[:, ("b", component, "")]
    pdt.assert_series_equal(plasma.b(component), expected, check_names=False)


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=B1_REASON)
@pytest.mark.parametrize("component", ["x", "y", "z"])
def test_velocity_call_returns_component(plasma, component):
    """``ion.v(c)`` is the plasma frame's ``("v", c, species)`` column.

    ON FAILURE: the code is wrong.
    """
    expected = plasma.data.loc[:, ("v", component, "p1")]
    pdt.assert_series_equal(
        plasma.ions.loc["p1"].v(component), expected, check_names=False
    )


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=B1_REASON)
@pytest.mark.parametrize("component", ["par", "per", "scalar"])
def test_tensor_call_returns_component(plasma, component):
    """``ion.w(c)`` is the plasma frame's ``("w", c, species)`` column.

    ON FAILURE: the code is wrong.
    """
    expected = plasma.data.loc[:, ("w", component, "p1")]
    pdt.assert_series_equal(
        plasma.ions.loc["p1"].w(component), expected, check_names=False
    )


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=B1_REASON)
def test_vector_call_unknown_component_names_available(plasma):
    """An unknown component raises KeyError naming x, y and z.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(KeyError, match=r"x.*y.*z"):
        plasma.b("par")


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=B1_REASON)
def test_tensor_call_unknown_component_names_available(plasma):
    """An unknown component raises KeyError naming par, per and scalar.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(KeyError, match=r"par.*per.*scalar"):
        plasma.ions.loc["p1"].w("x")
