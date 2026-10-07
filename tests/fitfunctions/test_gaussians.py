import inspect
import numpy as np
import pytest
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions.gaussians import (
    Gaussian,
    GaussianNormalized,
    GaussianLn,
)
from solarwindpy.fitfunctions.core import InsufficientDataError
from tests.tolerances import exact, noise_free


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
    """``function`` takes x then the parameters, and evaluates at the peak.

    The data are positive x only because GaussianLn refuses x <= 0.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.5, 2.5, 5)
    y = np.ones_like(x)
    obj = cls(x, y)
    sig = inspect.signature(obj.function)
    assert tuple(sig.parameters.keys()) == expected_params
    xval, *params = sample_args
    assert obj.function(xval, *params) == exact(expected_output)


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
        # Estimated in ln x: weighted mean and standard deviation of ln x, and
        # the peak y unlogged. Hand and recovery cases: test_p0_contract.py.
        m = (lnx * y).sum() / y.sum()
        s = np.sqrt(((lnx - m) ** 2 * y).sum() / y.sum())
        expected = [m, s, y.max()]
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
            # A exp[-(ln x - m)^2 / (2 s^2)]: the exponent of the log-normal
            # density on the class's reference,
            # https://mathworld.wolfram.com/LogNormalDistribution.html, with
            # the normalization replaced by A, as GaussianLn.function computes.
            (
                r"f(x) = A \cdot "
                r"\exp\left["
                r"-\frac{\left(\ln x - m\right)^2}{2 s^2}"
                r"\right]"
            ),
        ),
    ],
)
def test_TeX_function_strings(cls, expected):
    """``TeX_function`` is the class's LaTeX string.

    The data are positive x only because GaussianLn refuses x <= 0.

    ON FAILURE: the code is wrong, unless the author changed the string.
    """
    x = np.linspace(0.25, 1.25, 5)
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
    """A fit that fails on too few samples builds no ``TeX_info``.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.0, 1.0, 2)
    y = np.ones_like(x)
    obj = cls(x, y)
    obj.make_fit(return_exception=True)
    with pytest.raises(AttributeError):
        obj.TeX_info


class FailedFitReturnedNone(AssertionError):
    """make_fit(return_exception=True) returned None for a fit that failed."""


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized])
def test_make_fit_returns_exception_for_insufficient_data(cls):
    """Two points cannot fit three parameters, and the exception comes back.

    FitFunction.make_fit(return_exception=True) returns the exception instead
    of raising it; a subclass override must pass it on.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.0, 1.0, 2)
    obj = cls(x, np.ones_like(x))
    err = obj.make_fit(return_exception=True)
    if err is None:
        raise FailedFitReturnedNone(cls.__name__)
    assert isinstance(err, InsufficientDataError)


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

        ON FAILURE: the code is wrong.
        """
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        m = obj.popt["m"]
        s = obj.popt["s"]

        expected_mu = np.exp(m + (s**2) / 2)
        expected_sigma = np.sqrt(np.exp(s**2 + 2 * m) * (np.exp(s**2) - 1))

        normal = obj.normal_parameters
        assert normal["mu"] == exact(expected_mu)
        assert normal["sigma"] == exact(expected_sigma)

    def test_TeX_report_normal_parameters_default(self, lognormal_data):
        """Test that TeX_report_normal_parameters defaults to False."""
        x, y, _ = lognormal_data
        obj = GaussianLn(x, y)
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
        """GaussianLn fitted to noise-free log-normal data recovers m, |s|, A.

        ON FAILURE: the code is wrong.
        """
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        assert isinstance(obj.fit_result, OptimizeResult)
        assert "m" in obj.popt
        assert "s" in obj.popt
        assert "A" in obj.popt

        # s enters squared, so its fitted sign is arbitrary.
        assert obj.popt["m"] == noise_free(params["m"])
        assert np.abs(obj.popt["s"]) == noise_free(params["s"])
        assert obj.popt["A"] == noise_free(params["A"])


@pytest.mark.parametrize(
    "x",
    [
        pytest.param([0.0, 1.0, 2.0], id="zero"),
        pytest.param([-1.0, 1.0, 2.0], id="negative"),
    ],
)
def test_gaussian_ln_refuses_x_without_a_logarithm(x):
    """GaussianLn built on any used x <= 0 raises ValueError: ln x is undefined there.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(
        ValueError, match=r"every used x > 0: ln x is undefined at 1 of 3"
    ):
        GaussianLn(np.array(x), np.array([1.0, 2.0, 1.0]))


def test_gaussian_ln_accepts_x_excluded_from_the_fit():
    """An x <= 0 that ``xmin`` leaves out of the used data does not refuse the fit.

    ON FAILURE: the code is wrong.
    """
    x = np.array([-1.0, 0.0, 1.0, 2.0, 3.0])
    obj = GaussianLn(x, np.array([5.0, 5.0, 1.0, 2.0, 1.0]), xmin=0.5)
    assert obj.observations.used.x.tolist() == [1.0, 2.0, 3.0]


def test_gaussian_ln_set_fit_obs_refuses_x_without_a_logarithm():
    """Widening the used data to x <= 0 with ``set_fit_obs`` raises ValueError.

    The positive control narrows the same data to x > 0 and is accepted. A
    refused selection keeps the previous used data.

    ON FAILURE: the code is wrong.
    """
    x = np.array([-1.0, 0.0, 1.0, 2.0, 3.0])
    y = np.array([5.0, 5.0, 1.0, 2.0, 1.0])
    obj = GaussianLn(x, y, xmin=0.5)

    obj.set_fit_obs(x, y, None, xmin=1.5)
    assert obj.observations.used.x.tolist() == [2.0, 3.0]

    with pytest.raises(
        ValueError, match=r"every used x > 0: ln x is undefined at 2 of 5"
    ):
        obj.set_fit_obs(x, y, None)
    assert obj.observations.used.x.tolist() == [2.0, 3.0]
