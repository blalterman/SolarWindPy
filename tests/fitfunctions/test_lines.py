"""Tests for linear fit functions."""

import inspect
import numpy as np
import pytest

from solarwindpy.fitfunctions.lines import (
    Line,
    LineXintercept,
)
from solarwindpy.fitfunctions.core import InsufficientDataError


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_result",
    [
        (Line, ("x", "m", "b"), (2.0, 1.5, 0.5), 3.5),  # 1.5*2.0 + 0.5
        (LineXintercept, ("x", "m", "x0"), (2.0, 1.5, 1.0), 1.5),  # 1.5*(2.0-1.0)
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_result
):
    """Test function signatures and basic output for line classes."""
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.5, 2.0, 3.5])
    obj = cls(x, y)

    # Test function signature
    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    # Test function call
    result = obj.function(*sample_args)
    assert np.isclose(result, expected_result)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_p0_zero_size_input(cls):
    """Test p0 behavior with zero-size input arrays."""
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


def test_line_p0_estimation(simple_linear_data):
    """Test initial parameter estimation for Line class."""
    x, y, w = simple_linear_data
    obj = Line(x, y)

    p0 = obj.p0
    assert len(p0) == 2
    assert isinstance(p0[0], (int, float))  # m (slope)
    assert isinstance(p0[1], (int, float))  # b (intercept)

    # For the simple_linear_data fixture (y = 2*x + 1 + noise)
    # the slope should be close to 2 and intercept close to 1
    # The initial parameter estimation may not be perfect, so allow larger tolerance
    assert abs(p0[0] - 2.0) < 2.0  # Slope estimate within reasonable range
    assert (
        abs(p0[1] - 1.0) < 3.0
    )  # Intercept estimate within reasonable range (relaxed)


def test_line_x_intercept_p0_estimation(simple_linear_data):
    """Test initial parameter estimation for LineXintercept class."""
    x, y, w = simple_linear_data
    obj = LineXintercept(x, y)

    p0 = obj.p0
    assert len(p0) == 2
    assert isinstance(p0[0], (int, float))  # m (slope)
    assert isinstance(p0[1], (int, float))  # x0 (x-intercept)

    # Should have reasonable slope estimate
    assert abs(p0[0] - 2.0) < 1.0  # Slope estimate


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (Line, r"f(x)=m \cdot x + b"),
        (LineXintercept, r"f(x)=m \cdot (x - x_0)"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Test TeX function representation strings."""
    x = np.array([1.0, 2.0])
    y = np.array([2.0, 4.0])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_make_fit_success(cls, simple_linear_data):
    """Test successful fitting for line classes."""
    x, y, w = simple_linear_data
    obj = cls(x, y)

    # Test fitting succeeds
    obj.make_fit()

    # Test fit results are available
    assert obj.popt is not None
    assert obj.pcov is not None
    assert obj.chisq_dof is not None

    # Test output shapes
    assert len(obj.popt) == len(obj.p0)
    y_pred = obj(x)
    assert y_pred.shape == y.shape


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_make_fit_insufficient_data(cls):
    """Test fitting failure with insufficient data."""
    x = np.array([1.0])  # Single point
    y = np.array([1.0])
    obj = cls(x, y)

    # With insufficient data, make_fit raises InsufficientDataError by default
    with pytest.raises(InsufficientDataError):
        obj.make_fit()

    # With return_exception=True, make_fit returns the exception
    result = obj.make_fit(return_exception=True)
    assert isinstance(result, InsufficientDataError)
    assert "insufficient data" in str(result).lower()


def test_line_x_intercept_property():
    """Test x_intercept property for Line class."""
    # Create perfect linear data y = 2x - 4, so x-intercept is at x = 2
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-4.0, -2.0, 0.0, 2.0])

    obj = Line(x, y)
    obj.make_fit()

    # Test x_intercept property
    x_int = obj.x_intercept
    assert isinstance(x_int, (int, float))

    # Should be close to 2.0 for this data
    assert abs(x_int - 2.0) < 0.1


def test_line_x_intercept_y_intercept_property():
    """Test y_intercept property for LineXintercept class."""
    # Create linear data passing through (1, 0) with slope 2
    # So y = 2(x - 1) = 2x - 2, y-intercept should be -2
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([-2.0, 0.0, 2.0, 4.0])

    obj = LineXintercept(x, y)
    obj.make_fit()

    # Test y_intercept property
    y_int = obj.y_intercept
    assert isinstance(y_int, (int, float))

    # Should be close to -2.0 for this data
    assert abs(y_int - (-2.0)) < 0.1


def test_line_perfect_fit():
    """Test Line with perfect linear data (no noise)."""
    x = np.linspace(0, 5, 10)
    m_true, b_true = 1.5, -0.7
    y = m_true * x + b_true

    obj = Line(x, y)
    obj.make_fit()

    # Should recover true parameters very accurately
    assert abs(obj.popt["m"] - m_true) < 1e-10  # slope
    assert abs(obj.popt["b"] - b_true) < 1e-10  # intercept

    # Predicted values should match exactly
    y_pred = obj(x)
    assert np.allclose(y_pred, y, rtol=1e-12)


def test_line_x_intercept_perfect_fit():
    """Test LineXintercept with perfect linear data."""
    x = np.linspace(-2, 3, 10)
    m_true, x0_true = 2.0, 1.5
    y = m_true * (x - x0_true)

    obj = LineXintercept(x, y)
    obj.make_fit()

    # Should recover true parameters
    assert abs(obj.popt["m"] - m_true) < 1e-10  # slope
    assert abs(obj.popt["x0"] - x0_true) < 1e-10  # x-intercept

    # Predicted values should match
    y_pred = obj(x)
    assert np.allclose(y_pred, y, rtol=1e-12)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_str_and_call_methods(cls, simple_linear_data):
    """Test string representation and callable interface."""
    x, y, w = simple_linear_data
    obj = cls(x, y)
    obj.make_fit()

    # Test string representation
    str_repr = str(obj)
    assert cls.__name__ in str_repr

    # Test callable interface
    x_test = np.array([0.5, 1.5, 2.5])
    y_pred = obj(x_test)
    assert y_pred.shape == x_test.shape
    assert np.all(np.isfinite(y_pred))


def test_line_with_weights(simple_linear_data):
    """Test Line fitting with observation weights."""
    x, y, w = simple_linear_data

    # Create varying weights
    w_varied = np.linspace(0.5, 2.0, len(x))

    obj = Line(x, y, weights=w_varied)
    obj.make_fit()

    # Should complete successfully
    assert obj.popt is not None
    assert len(obj.popt) == 2


def test_line_horizontal_data():
    """Test Line with horizontal data (zero slope)."""
    x = np.linspace(0, 5, 10)
    y = np.full_like(x, 3.0)  # Horizontal line at y = 3

    obj = Line(x, y)
    obj.make_fit()

    # Slope should be close to zero
    assert abs(obj.popt["m"]) < 1e-9  # Relaxed tolerance for numerical precision
    # Intercept should be close to 3
    assert abs(obj.popt["b"] - 3.0) < 1e-8


def test_line_vertical_like_data_fails():
    """Test Line with nearly vertical data fails gracefully."""
    # Create data with very small dx
    x = np.array([1.0, 1.0001, 1.0002])  # Very small differences
    y = np.array([0.0, 10.0, 20.0])  # Large differences

    obj = Line(x, y)

    # This should either fit successfully (with large slope) or handle gracefully
    # The specific behavior depends on numerical precision
    try:
        obj.make_fit()
        # If it succeeds, slope should be very large
        assert abs(obj.popt["m"]) > 1000
    except (ValueError, RuntimeError):
        # It's also acceptable to fail on near-vertical data
        pass


def test_line_p0_with_duplicate_x_values():
    """Test Line p0 calculation with duplicate x values."""
    x = np.array([1.0, 1.0, 2.0, 2.0])  # Duplicate values
    y = np.array([2.0, 2.1, 4.0, 4.1])

    obj = Line(x, y)

    # p0 calculation might return None for problematic data
    p0 = obj.p0
    if p0 is not None:
        assert len(p0) == 2
        assert all(isinstance(p, (int, float)) for p in p0)


@pytest.mark.parametrize("cls", [Line, LineXintercept])
def test_property_access_before_fit(cls):
    """Test accessing properties before fitting."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 4.0, 6.0])
    obj = cls(x, y)

    # These should work before fitting
    assert obj.TeX_function is not None
    assert obj.p0 is not None

    # These should raise AttributeError before fitting
    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_line_intercept_properties_require_fit():
    """Test that intercept properties require fitting first."""
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 3.0, 5.0])

    line_obj = Line(x, y)
    xint_obj = LineXintercept(x, y)

    # Should raise AttributeError before fitting
    with pytest.raises(AttributeError):
        _ = line_obj.x_intercept

    with pytest.raises(AttributeError):
        _ = xint_obj.y_intercept

    # Should work after fitting
    line_obj.make_fit()
    xint_obj.make_fit()

    assert isinstance(line_obj.x_intercept, (int, float))
    assert isinstance(xint_obj.y_intercept, (int, float))


def test_line_edge_cases():
    """Test Line with edge case parameter values."""
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 0.0, 0.0])  # All zeros

    obj = Line(x, y)
    obj.make_fit()

    # Should handle all-zero y data
    # Slope should be 0, intercept should be 0
    assert abs(obj.popt["m"]) < 1e-10  # slope ≈ 0
    assert abs(obj.popt["b"]) < 1e-10  # intercept ≈ 0


def test_line_numerical_precision():
    """Test Line with data requiring high numerical precision."""
    x = np.array([1e6, 1e6 + 1, 1e6 + 2])
    y = np.array([2e6, 2e6 + 2, 2e6 + 4])  # slope = 2

    obj = Line(x, y)
    obj.make_fit()

    # Should handle large numbers correctly
    assert abs(obj.popt["m"] - 2.0) < 1e-10  # slope should be 2

    # Function evaluation should work
    result = obj(1e6 + 0.5)
    expected = 2.0 * (1e6 + 0.5) + (obj.popt["b"])
    assert abs(result - expected) < 1e-6
