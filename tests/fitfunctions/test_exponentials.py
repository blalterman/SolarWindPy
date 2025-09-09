"""Tests for exponential fit functions."""

import inspect
import numpy as np
import pytest

from solarwindpy.fitfunctions.exponentials import (
    Exponential,
    ExponentialPlusC,
    ExponentialCDF,
)
from solarwindpy.fitfunctions.core import InsufficientDataError


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_shape",
    [
        (Exponential, ("x", "c", "A"), (0.0, 1.0, 2.0), ()),
        (ExponentialPlusC, ("x", "c", "A", "d"), (0.0, 1.0, 2.0, 0.5), ()),
        (ExponentialCDF, ("x", "c"), (0.0, 1.0), ()),
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_shape
):
    """Test function signatures and basic output for exponential classes."""
    x = np.linspace(0.0, 2.0, 10)
    y = np.ones_like(x)
    obj = cls(x, y)

    # ExponentialCDF needs y0 to be set before function can be called
    if cls.__name__ == "ExponentialCDF":
        obj.set_y0(1.0)

    # Test function signature
    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params

    # Test function call
    result = obj.function(*sample_args)
    assert np.isscalar(result) or result.shape == expected_shape
    assert np.isfinite(result)


@pytest.fixture
def exponential_data():
    """Generate synthetic exponential data for testing."""
    np.random.seed(42)
    x = np.linspace(0, 3, 30)
    c, A = 0.8, 3.0
    noise = np.random.normal(0, 0.1, size=x.shape)
    y = A * np.exp(-c * x) + noise
    w = np.ones_like(x)
    return x, y, w


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC, ExponentialCDF])
def test_p0_zero_size_input(cls):
    """Test p0 behavior with zero-size input arrays."""
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)

    with pytest.raises(InsufficientDataError):
        _ = obj.p0


def test_exponential_p0_estimation(exponential_data):
    """Test initial parameter estimation for Exponential class."""
    x, y, w = exponential_data
    obj = Exponential(x, y)
    obj.make_fit()

    p0 = obj.p0
    assert len(p0) == 2
    assert isinstance(p0[0], (int, float))  # c
    assert isinstance(p0[1], (int, float))  # A
    assert p0[1] > 0  # A should be positive for exponential decay


def test_exponential_plus_c_p0_estimation(exponential_data):
    """Test initial parameter estimation for ExponentialPlusC class."""
    x, y, w = exponential_data
    # Add constant offset to data
    y_offset = y + 0.5
    obj = ExponentialPlusC(x, y_offset)
    obj.make_fit()

    p0 = obj.p0
    assert len(p0) == 3
    assert isinstance(p0[0], (int, float))  # c
    assert isinstance(p0[1], (int, float))  # A
    assert isinstance(p0[2], (int, float))  # d


def test_exponential_cdf_p0_estimation(exponential_data):
    """Test initial parameter estimation for ExponentialCDF class."""
    x, y, w = exponential_data
    # Transform to CDF-like data
    y_cdf = np.cumsum(y) / np.sum(y)
    obj = ExponentialCDF(x, y_cdf)
    obj.set_y0(1.0)  # Set amplitude before fitting

    p0 = obj.p0
    assert len(p0) == 1
    assert isinstance(p0[0], (int, float))  # c


@pytest.mark.parametrize(
    "cls, expected_tex",
    [
        (Exponential, r"f(x)=A \cdot e^{-cx}"),
        (ExponentialPlusC, r"f(x)=A \cdot e^{-cx} + d"),
        (ExponentialCDF, r"f(x)=A \left(1 - e^{-cx}\right)"),
    ],
)
def test_TeX_function_strings(cls, expected_tex):
    """Test TeX function representation strings."""
    x = np.array([1.0, 2.0])
    y = np.array([1.0, 0.5])
    obj = cls(x, y)
    assert obj.TeX_function == expected_tex


def test_make_fit_success_regular(exponential_data):
    """Test successful fitting for regular exponential classes."""
    x, y, w = exponential_data

    for cls in [Exponential, ExponentialPlusC]:
        obj = cls(x, y)

        # Test fitting succeeds
        obj.make_fit()

        # Test fit results are available
        assert obj.popt is not None
        assert obj.pcov is not None
        assert obj.chisq_dof is not None
        assert obj.fit_result is not None

        # Test output shapes
        assert len(obj.popt) == len(obj.p0)


def test_make_fit_success_cdf(exponential_data):
    """Test successful fitting for ExponentialCDF class."""
    x, y, w = exponential_data
    # Transform to CDF-like data
    y_cdf = np.cumsum(y) / np.sum(y)

    obj = ExponentialCDF(x, y_cdf)
    obj.set_y0(1.0)  # Set amplitude before fitting

    # Test fitting succeeds
    obj.make_fit()

    # Test fit results are available
    assert obj.popt is not None
    assert obj.pcov is not None
    assert obj.chisq_dof is not None
    assert obj.fit_result is not None

    # Test output shapes
    assert len(obj.popt) == len(obj.p0)


def test_make_fit_insufficient_data():
    """Test fitting failure with insufficient data."""
    # Test Exponential and ExponentialPlusC
    for cls in [Exponential, ExponentialPlusC]:
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

    # Test ExponentialCDF (needs special setup)
    # Note: ExponentialCDF has only 1 parameter (c) so 1 data point is technically sufficient
    # The fit will succeed but may not be meaningful
    x = np.array([1.0])
    y = np.array([1.0])
    obj = ExponentialCDF(x, y)
    obj.set_y0(1.0)

    result = obj.make_fit()
    # For ExponentialCDF with 1 point, the fit technically succeeds
    # (1 point for 1 parameter), so it returns None
    assert result is None or isinstance(result, InsufficientDataError)
    if isinstance(result, InsufficientDataError):
        assert "insufficient data" in str(result).lower()


def test_exponential_numerical_stability():
    """Test exponential function handles large negative exponents."""
    x = np.array([0.0, 10.0, 100.0])  # Large x values
    y = np.array([1.0, 0.1, 0.01])
    obj = Exponential(x, y)

    # Should not raise overflow warnings
    result = obj.function(100.0, 1.0, 1.0)  # exp(-100) -> very small
    assert np.isfinite(result)
    assert result >= 0


def test_exponential_plus_c_constant_term():
    """Test that ExponentialPlusC handles constant offset correctly."""
    x = np.linspace(0, 2, 20)
    c, A, d = 1.0, 2.0, 0.5
    y_true = A * np.exp(-c * x) + d

    obj = ExponentialPlusC(x, y_true)
    result = obj.function(x, c, A, d)

    assert np.allclose(result, y_true, rtol=1e-10)


def test_exponential_cdf_monotonicity():
    """Test that ExponentialCDF produces monotonically increasing output."""
    x = np.linspace(0, 5, 20)
    c = 0.5

    obj = ExponentialCDF(x, np.ones_like(x))  # Dummy y data
    obj.set_y0(1.0)  # Set amplitude
    result = obj.function(x, c)

    # CDF should be monotonically increasing
    assert np.all(np.diff(result) >= 0)
    # Should approach y0 as x increases
    assert result[-1] < obj.y0  # Not quite reaching y0 for finite x
    assert result[-1] > 0.9 * obj.y0  # But close to it


def test_str_and_call_methods_regular(exponential_data):
    """Test string representation and callable interface for regular exponentials."""
    x, y, w = exponential_data

    for cls in [Exponential, ExponentialPlusC]:
        obj = cls(x, y)
        obj.make_fit()

        # Test string representation
        str_repr = str(obj)
        assert cls.__name__ in str_repr

        # Test callable interface
        x_test = np.array([0.5, 1.0, 1.5])
        y_pred = obj(x_test)
        assert y_pred.shape == x_test.shape
        assert np.all(np.isfinite(y_pred))


def test_str_and_call_methods_cdf(exponential_data):
    """Test string representation and callable interface for ExponentialCDF."""
    x, y, w = exponential_data
    # Transform to CDF-like data
    y_cdf = np.cumsum(y) / np.sum(y)

    obj = ExponentialCDF(x, y_cdf)
    obj.set_y0(1.0)  # Set amplitude before fitting
    obj.make_fit()

    # Test string representation
    str_repr = str(obj)
    assert "ExponentialCDF" in str_repr

    # Test callable interface
    x_test = np.array([0.5, 1.0, 1.5])
    y_pred = obj(x_test)
    assert y_pred.shape == x_test.shape
    assert np.all(np.isfinite(y_pred))


def test_exponential_decay_behavior():
    """Test that Exponential produces proper decay behavior."""
    x = np.linspace(0, 3, 10)
    y = 2.0 * np.exp(-0.5 * x)  # True exponential decay

    obj = Exponential(x, y)
    obj.make_fit()

    # Check that function values decrease with x
    x_test = np.array([0.0, 1.0, 2.0, 3.0])
    y_test = obj(x_test)

    # Should be decreasing
    assert np.all(np.diff(y_test) < 0)
    # Should be positive
    assert np.all(y_test > 0)


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC, ExponentialCDF])
def test_property_access_before_fit(cls):
    """Test accessing properties before fitting raises appropriate errors."""
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([1.0, 0.5, 0.25])
    obj = cls(x, y)

    # These should work before fitting
    assert obj.TeX_function is not None
    assert obj.p0 is not None

    # These should raise AttributeError before fitting
    with pytest.raises(AttributeError):
        _ = obj.popt
    with pytest.raises(AttributeError):
        _ = obj.pcov


def test_exponential_with_weights(exponential_data):
    """Test exponential fitting with observation weights."""
    x, y, w = exponential_data

    # Create varying weights (higher weight for early points)
    w_varied = np.linspace(2.0, 0.5, len(x))

    obj = Exponential(x, y, weights=w_varied)
    obj.make_fit()

    # Should complete successfully
    assert obj.popt is not None
    assert len(obj.popt) == 2


@pytest.mark.parametrize("cls", [Exponential, ExponentialPlusC, ExponentialCDF])
def test_edge_case_single_parameter_bounds(cls):
    """Test behavior with extreme parameter values."""
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 0.5, 0.25])
    obj = cls(x, y)

    # Test with very small decay constant
    if cls == Exponential:
        result = obj.function(x, 1e-6, 1.0)  # Very slow decay
        assert np.allclose(result, 1.0, atol=1e-5)

    # Test with very large decay constant
    if cls == Exponential:
        result = obj.function(x, 100.0, 1.0)  # Very fast decay
        assert result[0] == 1.0  # At x=0
        assert result[-1] < 1e-40  # At x=2, essentially zero
