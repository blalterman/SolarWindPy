"""Tests for power law fit functions."""

import inspect
import numpy as np
import pytest

from solarwindpy.fitfunctions.power_laws import (
    PowerLaw,
    PowerLawPlusC,
    PowerLawOffCenter,
)
from solarwindpy.fitfunctions.core import InsufficientDataError


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, input_x",
    [
        (PowerLaw, ("x", "A", "b"), (2.0, 3.0, 1.5), 2.0),
        (PowerLawPlusC, ("x", "A", "b", "c"), (2.0, 3.0, 1.5, 1.0), 2.0),
        (PowerLawOffCenter, ("x", "A", "b", "x0"), (2.0, 3.0, 1.5, 0.5), 2.0),
    ],
)
def test_function_signature_and_output(cls, expected_params, sample_args, input_x):
    """Test function signatures and basic output for power law classes."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 4.0, 9.0])
    obj = cls(x, y)

    # Test function signature
    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    # Test function call with positive arguments
    result = obj.function(*sample_args)
    assert np.isfinite(result)
    assert result > 0  # Should be positive for positive inputs


@pytest.fixture
def power_law_data():
    """Generate synthetic power law data for testing."""
    np.random.seed(42)
    x = np.linspace(0.5, 5.0, 20)  # Avoid x=0 for power laws
    A, b = 2.0, -1.5
    noise = np.random.normal(0, 0.1, size=x.shape)
    y = A * x**b + noise
    # Ensure y stays positive for log stability
    y = np.maximum(y, 0.01)
    w = np.ones_like(x)
    return x, y, w


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_p0_zero_size_input(cls):
    """Test p0 behavior with zero-size input arrays."""
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


def test_power_law_p0_estimation(power_law_data):
    """Test initial parameter estimation for PowerLaw class."""
    x, y, w = power_law_data
    obj = PowerLaw(x, y)

    p0 = obj.p0
    assert len(p0) == 2
    assert isinstance(p0[0], (int, float))  # A
    assert isinstance(p0[1], (int, float))  # b


def test_power_law_plus_c_p0_estimation(power_law_data):
    """Test initial parameter estimation for PowerLawPlusC class."""
    x, y, w = power_law_data
    # Add constant offset
    y_offset = y + 0.5
    obj = PowerLawPlusC(x, y_offset)

    p0 = obj.p0
    assert len(p0) == 3
    assert isinstance(p0[0], (int, float))  # A
    assert isinstance(p0[1], (int, float))  # b
    assert isinstance(p0[2], (int, float))  # c


def test_power_law_off_center_p0_estimation(power_law_data):
    """Test initial parameter estimation for PowerLawOffCenter class."""
    x, y, w = power_law_data
    obj = PowerLawOffCenter(x, y)

    p0 = obj.p0
    assert len(p0) == 3
    assert isinstance(p0[0], (int, float))  # A
    assert isinstance(p0[1], (int, float))  # b
    assert isinstance(p0[2], (int, float))  # x0


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (PowerLaw, r"f(x)=A x^b"),
        (PowerLawPlusC, r"f(x)=A x^b + c"),
        (PowerLawOffCenter, r"f(x)=A (x-x_0)^b"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Test TeX function representation strings."""
    x = np.array([1.0, 2.0, 4.0])
    y = np.array([2.0, 1.0, 0.5])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_make_fit_success(cls, power_law_data):
    """Test successful fitting for power law classes."""
    x, y, w = power_law_data
    obj = cls(x, y)

    # Test fitting succeeds
    obj.make_fit()

    # Test fit results are available
    assert obj.popt is not None
    assert obj.pcov is not None
    assert obj.chisq_dof is not None

    # Test output shapes
    assert len(obj.popt) == len(obj.p0)


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
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


def test_power_law_perfect_fit():
    """Test PowerLaw with perfect power law data."""
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b = 16.0, -2.0
    y = A * x**b  # Perfect power law: 16, 4, 1, 0.25

    obj = PowerLaw(x, y)
    obj.make_fit()

    # Should recover true parameters accurately
    assert abs(obj.popt["A"] - A) < 1e-10  # A
    assert abs(obj.popt["b"] - b) < 1e-10  # b

    # Predicted values should match
    y_pred = obj(x)
    assert np.allclose(y_pred, y, rtol=1e-12)


def test_power_law_plus_c_perfect_fit():
    """Test PowerLawPlusC with perfect data."""
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b, c = 16.0, -2.0, 2.0
    y = A * x**b + c  # 18, 6, 3, 2.25

    obj = PowerLawPlusC(x, y)
    obj.make_fit()

    # Should recover parameters accurately
    assert abs(obj.popt["A"] - A) < 1e-10  # A
    assert abs(obj.popt["b"] - b) < 1e-10  # b
    assert abs(obj.popt["c"] - c) < 1e-10  # c

    y_pred = obj(x)
    assert np.allclose(y_pred, y, rtol=1e-12)


def test_power_law_off_center_perfect_fit():
    """Test PowerLawOffCenter with perfect data."""
    x = np.array([2.0, 3.0, 5.0, 9.0])
    A, b, x0 = 4.0, 2.0, 1.0
    y = A * (x - x0) ** b  # 4*1^2, 4*2^2, 4*4^2, 4*8^2 = 4, 16, 64, 256

    obj = PowerLawOffCenter(x, y)
    obj.make_fit()

    # Should recover parameters
    assert abs(obj.popt["A"] - A) < 1e-10  # A
    assert abs(obj.popt["b"] - b) < 1e-10  # b
    assert abs(obj.popt["x0"] - x0) < 1e-10  # x0

    y_pred = obj(x)
    assert np.allclose(y_pred, y, rtol=1e-12)


def test_power_law_numerical_stability():
    """Test power law functions handle extreme values."""
    x = np.array([0.1, 1.0, 10.0])
    y = np.array([10.0, 1.0, 0.1])

    obj = PowerLaw(x, y)

    # Test with extreme parameters
    result1 = obj.function(0.1, 1.0, -10.0)  # Very negative exponent
    assert np.isfinite(result1)
    assert result1 > 0

    result2 = obj.function(10.0, 1.0, 0.1)  # Very small exponent
    assert np.isfinite(result2)
    assert result2 > 0


def test_power_law_zero_handling():
    """Test power law behavior with zero and near-zero values."""
    x = np.array([0.01, 1.0, 100.0])  # Avoid exactly zero
    y = np.array([1.0, 1.0, 1.0])

    obj = PowerLaw(x, y)

    # Test function behavior near zero
    result = obj.function(0.01, 1.0, 1.0)
    assert np.isfinite(result)

    # Test with zero exponent (should give constant)
    result_zero_exp = obj.function(2.0, 5.0, 0.0)
    assert abs(result_zero_exp - 5.0) < 1e-10


def test_power_law_off_center_centering():
    """Test that PowerLawOffCenter properly handles centering."""
    x = np.array([2.0, 3.0, 4.0, 5.0])
    x0 = 1.5

    obj = PowerLawOffCenter(x, np.ones_like(x))

    # Test that centering works correctly
    result = obj.function(x, 2.0, 1.0, x0)
    expected = 2.0 * (x - x0) ** 1.0
    assert np.allclose(result, expected)


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_str_and_call_methods(cls, power_law_data):
    """Test string representation and callable interface."""
    x, y, w = power_law_data
    obj = cls(x, y)
    obj.make_fit()

    # Test string representation
    str_repr = str(obj)
    assert cls.__name__ in str_repr

    # Test callable interface
    x_test = np.array([1.0, 2.0, 3.0])
    y_pred = obj(x_test)
    assert y_pred.shape == x_test.shape
    assert np.all(np.isfinite(y_pred))
    assert np.all(y_pred > 0)  # Power laws should be positive


def test_power_law_with_weights(power_law_data):
    """Test power law fitting with observation weights."""
    x, y, w = power_law_data

    # Create varying weights
    w_varied = np.linspace(0.5, 2.0, len(x))

    obj = PowerLaw(x, y, weights=w_varied)
    obj.make_fit()

    # Should complete successfully
    assert obj.popt is not None
    assert len(obj.popt) == 2


def test_power_law_scaling_behavior():
    """Test that PowerLaw exhibits proper scaling behavior."""
    x = np.array([1.0, 2.0, 4.0, 8.0])
    A, b = 2.0, -1.0
    y = A * x**b

    obj = PowerLaw(x, y)
    obj.make_fit()

    # Test scaling: if x doubles, y should change by factor of 2^b
    x1, x2 = 2.0, 4.0
    y1, y2 = obj(x1), obj(x2)
    scaling_factor = y2 / y1
    expected_factor = (x2 / x1) ** b

    assert abs(scaling_factor - expected_factor) < 1e-8  # More realistic tolerance


@pytest.mark.parametrize("cls", [PowerLaw, PowerLawPlusC, PowerLawOffCenter])
def test_property_access_before_fit(cls):
    """Test accessing properties before fitting."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([2.0, 1.0, 0.5])
    obj = cls(x, y)

    # These should work before fitting
    assert obj.TeX_function is not None
    assert obj.p0 is not None

    # These should raise AttributeError before fitting
    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_power_law_negative_x_handling():
    """Test power law behavior with negative x values."""
    # Only test with even exponents to avoid complex numbers
    x = np.array([-2.0, -1.0, 1.0, 2.0])

    obj = PowerLaw(x, np.ones_like(x))

    # Test with even exponent
    result_even = obj.function(x, 1.0, 2.0)  # x^2
    assert np.all(np.isfinite(result_even))
    assert np.all(result_even > 0)

    # Test symmetry for even powers
    assert abs(result_even[0] - result_even[3]) < 1e-10  # (-2)^2 = 2^2
    assert abs(result_even[1] - result_even[2]) < 1e-10  # (-1)^2 = 1^2


def test_power_law_integer_vs_float_exponents():
    """Test that integer and float exponents give consistent results."""
    x = np.array([1.0, 2.0, 3.0])
    A = 2.0

    obj = PowerLaw(x, np.ones_like(x))

    # Test integer vs float exponent
    result_int = obj.function(x, A, 2)  # Integer exponent
    result_float = obj.function(x, A, 2.0)  # Float exponent

    assert np.allclose(result_int, result_float, rtol=1e-15)


def test_power_law_edge_case_exponents():
    """Test power laws with edge case exponent values."""
    x = np.array([1.0, 2.0, 4.0])
    obj = PowerLaw(x, np.ones_like(x))

    # Test with b = 1 (linear)
    result_linear = obj.function(x, 3.0, 1.0)
    expected_linear = 3.0 * x
    assert np.allclose(result_linear, expected_linear)

    # Test with b = 0 (constant)
    result_constant = obj.function(x, 5.0, 0.0)
    assert np.all(result_constant == 5.0)

    # Test with b = -1 (inverse)
    result_inverse = obj.function(x, 2.0, -1.0)
    expected_inverse = 2.0 / x
    assert np.allclose(result_inverse, expected_inverse)
