import inspect
import numpy as np
import pytest

from solarwindpy.fitfunctions.gaussians import (
    Gaussian,
    GaussianNormalized,
    GaussianLn,
)
from solarwindpy.fitfunctions.core import InsufficientDataError


@pytest.mark.parametrize(
    "cls, expected_params, sample_args, expected_output",
    [
        (Gaussian, ("x", "mu", "sigma", "A"), (0.0, 0.0, 1.0, 1.0), 1.0),
        (
            GaussianNormalized,
            ("x", "mu", "sigma", "n"),
            (0.0, 0.0, 1.0, 1.0),
            1.0 / (np.sqrt(2 * np.pi)),
        ),
        (GaussianLn, ("x", "m", "s", "A"), (1.0, 0.0, 1.0, 1.0), 1.0),
    ],
)
def test_function_signature_and_output(
    cls, expected_params, sample_args, expected_output
):
    x = np.linspace(-1.0, 1.0, 5)
    y = np.ones_like(x)
    obj = cls(x, y)
    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params
    xval, *params = sample_args
    assert np.allclose(obj.function(xval, *params), expected_output)


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized, GaussianLn])
def test_p0_zero_size_input(cls):
    x = np.array([])
    y = np.array([])
    obj = cls(x, y)
    with pytest.raises(InsufficientDataError):
        _ = obj.p0


@pytest.mark.parametrize(
    "cls, params",
    [
        (Gaussian, dict(mu=1.0, sigma=0.5, amp=2.0)),
        (GaussianNormalized, dict(mu=1.0, sigma=0.5, n=5.0)),
        (GaussianLn, dict(m=0.3, s=0.2, A=3.0)),
    ],
)
def test_p0_estimation(cls, params):
    if cls is Gaussian:
        x = np.linspace(
            params["mu"] - 5 * params["sigma"], params["mu"] + 5 * params["sigma"], 100
        )
        y = params["amp"] * np.exp(-0.5 * ((x - params["mu"]) / params["sigma"]) ** 2)
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2 * y).sum() / y.sum())
        peak = y.max()
        expected = [mean, std, peak]
    elif cls is GaussianNormalized:
        x = np.linspace(
            params["mu"] - 5 * params["sigma"], params["mu"] + 5 * params["sigma"], 100
        )
        A = params["n"] / (np.sqrt(2 * np.pi) * params["sigma"])
        y = A * np.exp(-0.5 * ((x - params["mu"]) / params["sigma"]) ** 2)
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2 * y).sum() / y.sum())
        peak = y.max()
        n_est = peak * std * np.sqrt(2 * np.pi)
        expected = [mean, std, n_est]
    else:  # GaussianLn
        x = np.linspace(
            np.exp(params["m"] - 5 * params["s"]),
            np.exp(params["m"] + 5 * params["s"]),
            100,
        )
        lnx = np.log(x)
        y = params["A"] * np.exp(-0.5 * ((lnx - params["m"]) / params["s"]) ** 2)
        mean = (x * y).sum() / y.sum()
        std = ((x - mean) ** 2 * y).sum() / y.sum()
        peak = y.max()
        expected = [np.log(mean), np.log(std), np.log(peak)]
    obj = cls(x, y)
    assert np.allclose(obj.p0, expected)


@pytest.mark.parametrize(
    "cls, expected",
    [
        (
            Gaussian,
            r"f(x)=A \cdot e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}",
        ),
        (
            GaussianNormalized,
            r"f(x)=\frac{n}{\sqrt{2 \pi} \sigma} e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}",
        ),
        (
            GaussianLn,
            (
                r"f(x) =A \cdot"
                r"\exp\left["
                r"\frac{\left(\ln x - m\right)^2}{2 s^2}"
                r"\right]"
            ),
        ),
    ],
)
def test_TeX_function_strings(cls, expected):
    x = np.linspace(0.0, 1.0, 5)
    y = np.ones_like(x)
    obj = cls(x, y)
    assert obj.TeX_function == expected


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized])
def test_make_fit_TeX_argnames_success(cls):
    mu, sigma = 0.0, 0.5
    x = np.linspace(mu - sigma, mu + sigma, 5)
    if cls is Gaussian:
        A = 1.0
        y = A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
    else:
        n = 1.0
        A = n / (np.sqrt(2 * np.pi) * sigma)
        y = A * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
    obj = cls(x, y)
    obj.make_fit()
    assert obj.TeX_info.TeX_argnames == {"mu": r"\mu", "sigma": r"\sigma"}


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized])
def test_make_fit_TeX_argnames_failure(cls):
    x = np.linspace(0.0, 1.0, 2)
    y = np.ones_like(x)
    obj = cls(x, y)
    obj.make_fit(return_exception=True)
    assert not hasattr(obj, "_TeX_info")


class TestGaussianLn:
    """Tests for GaussianLn log-normal distribution fitting.

    This class tests GaussianLn-specific functionality including
    normal parameter conversion, TeX formatting with normal parameters,
    and proper fit behavior.
    """

    @pytest.fixture
    def lognormal_data(self):
        """Generate synthetic log-normal distribution data.

        Returns
        -------
        tuple
            ``(x, y, params)`` where x is positive, y follows a log-normal
            distribution, and params contains the log-normal parameters.
        """
        m = 0.5  # log mean
        s = 0.3  # log std
        A = 2.0  # amplitude
        x = np.linspace(0.5, 5.0, 100)
        lnx = np.log(x)
        y = A * np.exp(-0.5 * ((lnx - m) / s) ** 2)
        return x, y, dict(m=m, s=s, A=A)

    def test_normal_parameters_calculation(self, lognormal_data):
        """Test that normal_parameters correctly converts log-normal to normal.

        The conversion formulas are:
        - mu = exp(m + s^2/2)
        - sigma = sqrt(exp(s^2 + 2m) * (exp(s^2) - 1))
        """
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        m = obj.popt["m"]
        s = obj.popt["s"]

        expected_mu = np.exp(m + (s**2) / 2)
        expected_sigma = np.sqrt(np.exp(s**2 + 2 * m) * (np.exp(s**2) - 1))

        normal = obj.normal_parameters
        assert np.isclose(normal["mu"], expected_mu, rtol=1e-10)
        assert np.isclose(normal["sigma"], expected_sigma, rtol=1e-10)

    def test_TeX_report_normal_parameters_default(self, lognormal_data):
        """Test that TeX_report_normal_parameters defaults to False."""
        x, y, _ = lognormal_data
        obj = GaussianLn(x, y)
        assert obj.TeX_report_normal_parameters is False

    def test_TeX_report_normal_parameters_attribute_error(self):
        """Test TeX_report_normal_parameters returns False when attribute missing.

        This tests the AttributeError catch in the property getter.
        """
        x = np.linspace(0.5, 5.0, 10)
        y = np.ones_like(x)
        obj = GaussianLn(x, y)
        # Delete the attribute to trigger AttributeError path
        if hasattr(obj, "_use_normal_parameters"):
            del obj._use_normal_parameters
        assert obj.TeX_report_normal_parameters is False

    def test_set_TeX_report_normal_parameters(self, lognormal_data):
        """Test setting TeX_report_normal_parameters."""
        x, y, _ = lognormal_data
        obj = GaussianLn(x, y)
        obj.set_TeX_report_normal_parameters(True)
        assert obj.TeX_report_normal_parameters is True
        obj.set_TeX_report_normal_parameters(False)
        assert obj.TeX_report_normal_parameters is False

    def test_TeX_info_TeX_popt_without_normal_parameters(self, lognormal_data):
        """Test TeX_info.TeX_popt returns log-normal params."""
        x, y, _ = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        # Access via TeX_info, not direct property (GaussianLn.TeX_popt is broken)
        tex_popt = obj.TeX_info.TeX_popt
        assert "m" in tex_popt
        assert "s" in tex_popt
        assert "A" in tex_popt

    def test_make_fit_success(self, lognormal_data):
        """Test successful fit of GaussianLn to log-normal data."""
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        assert hasattr(obj, "_fit_result")
        assert "m" in obj.popt
        assert "s" in obj.popt
        assert "A" in obj.popt

        # Verify fitted parameters are close to true values
        # Note: s can be negative in fitted result (same shape, different sign)
        assert np.isclose(obj.popt["m"], params["m"], rtol=0.1)
        assert np.isclose(np.abs(obj.popt["s"]), params["s"], rtol=0.1)
        assert np.isclose(obj.popt["A"], params["A"], rtol=0.1)
