import inspect
import warnings

import numpy as np
import pytest
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions.gaussians import (
    Gaussian,
    GaussianNormalized,
    GaussianLn,
)
from solarwindpy.fitfunctions.core import InsufficientDataError
from tests.tolerances import exact, noise_free, printed
from tests.fitfunctions._attempt import attempt_fit


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
        (GaussianLn, ("x", "mu", "sigma", "A"), (1.0, 0.0, 1.0, 1.0), 1.0),
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
        (GaussianLn, dict(mu=0.3, sigma=0.2, A=3.0)),
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
            np.exp(params["mu"] - 5 * params["sigma"]),
            np.exp(params["mu"] + 5 * params["sigma"]),
            100,
        )
        lnx = np.log(x)
        y = params["A"] * np.exp(-0.5 * ((lnx - params["mu"]) / params["sigma"]) ** 2)
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
            # A exp[-(ln x - mu)^2 / (2 sigma^2)]: the exponent of the log-normal
            # density on the class's reference,
            # https://mathworld.wolfram.com/LogNormalDistribution.html, with
            # the normalization replaced by A, as GaussianLn.function computes.
            (
                r"f(x) = A \cdot "
                r"\exp\left["
                r"-\frac{\left(\ln x - \mu\right)^2}{2 \sigma^2}"
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
    attempt_fit(obj)
    with pytest.raises(AttributeError):
        obj.TeX_info


class FailedFitReturnedNone(AssertionError):
    """A fit that failed recorded no error."""


@pytest.mark.parametrize("cls", [Gaussian, GaussianNormalized])
def test_make_fit_returns_exception_for_insufficient_data(cls):
    """Two points cannot fit three parameters, and the exception is recorded.

    FitFunction.make_fit records the exception as ``error`` before raising
    it; a subclass override must pass it on.

    ON FAILURE: the code is wrong.
    """
    x = np.linspace(0.0, 1.0, 2)
    obj = cls(x, np.ones_like(x))
    err = attempt_fit(obj)
    if err is None:
        raise FailedFitReturnedNone(cls.__name__)
    assert isinstance(err, InsufficientDataError)


#: TeX of the linear-space mean and std a GaussianLn annotation can report.
MEAN = r"\mathrm{mean}(x)"
STD = r"\mathrm{std}(x)"


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
        return x, y, dict(mu=m, sigma=s, A=A)

    def test_normal_parameters_calculation(self, lognormal_data):
        """Test that normal_parameters gives the linear-space mean and std.

        The conversion formulas, with mu and sigma fitted to ln x, are:
        - mean = exp(mu + sigma^2/2)
        - std = sqrt(exp(sigma^2 + 2 mu) * (exp(sigma^2) - 1))

        ON FAILURE: the code is wrong.
        """
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        m = obj.popt["mu"]
        s = obj.popt["sigma"]

        expected_mean = np.exp(m + (s**2) / 2)
        expected_std = np.sqrt(np.exp(s**2 + 2 * m) * (np.exp(s**2) - 1))

        normal = obj.normal_parameters
        assert normal == {"mean": exact(expected_mean), "std": exact(expected_std)}

    @staticmethod
    def _reported(info, name):
        """Value of the ``name = value`` line of a TeX annotation, or None."""
        for line in info.split("\n"):
            body = line.strip("$").strip()
            if body.startswith(f"{name} = "):
                text = body.split(" = ", 1)[1]
                text = text.replace(r" \times 10^{", "e").replace("}", "")
                assert r"\pm" not in text, line
                return float(text.replace(" ", ""))
        return None

    def test_tex_info_reports_normal_parameters_only_when_asked(self, lognormal_data):
        r"""The annotation lists the mean and std when the flag is on, and not when off.

        The data are noise-free with mu = 0.5 and sigma = 0.3, so the reported
        values are mean = exp(mu + sigma^2/2) = exp(0.545) = 1.7246 and
        std = sqrt(exp(sigma^2 + 2mu)(exp(sigma^2) - 1)) = sqrt(2.9743 * 0.094174)
        = 0.5292 (mathworld LogNormalDistribution, the class's reference),
        printed to four significant digits. Turning the flag on or off after
        the fit updates the annotation.

        ON FAILURE: the code is wrong.
        """
        x, y, params = lognormal_data
        m, s = params["mu"], params["sigma"]
        mu = np.exp(m + s**2 / 2)
        sigma = np.sqrt(np.exp(s**2 + 2 * m) * (np.exp(s**2) - 1))
        assert mu == printed(1.7246, decimals=4)
        assert sigma == printed(0.5292, decimals=4)

        obj = GaussianLn(x, y)
        assert obj.TeX_report_normal_parameters is False
        obj.make_fit()
        off = str(obj.TeX_info)
        assert self._reported(off, MEAN) is None
        assert self._reported(off, STD) is None

        obj.set_TeX_report_normal_parameters(True)
        assert obj.TeX_report_normal_parameters is True
        on = str(obj.TeX_info)
        assert self._reported(on, MEAN) == printed(mu, decimals=3)
        assert self._reported(on, STD) == printed(sigma, decimals=4)
        for name in (r"\mu", r"\sigma", "A"):
            assert f"$ {name} = " in on

        obj.set_TeX_report_normal_parameters(False)
        assert str(obj.TeX_info) == off

    def test_flag_set_before_the_fit_reaches_the_annotation(self, lognormal_data):
        """``set_TeX_report_normal_parameters(True)`` before ``make_fit`` holds.

        ON FAILURE: the code is wrong.
        """
        x, y, _ = lognormal_data
        obj = GaussianLn(x, y)
        obj.set_TeX_report_normal_parameters(True)
        obj.make_fit()
        assert self._reported(str(obj.TeX_info), MEAN) is not None

    @pytest.mark.xfail(strict=True, reason="except AttributeError swallows it")
    def test_a_bug_reading_TeX_info_is_not_taken_for_not_fitted(self, lognormal_data):
        """An AttributeError inside ``TeX_info`` propagates from the flag setter.

        Only NotFittedError means "not fitted yet"; any other AttributeError
        is a bug and must not be silenced.

        ON FAILURE: the code is wrong.
        """

        class Broken(GaussianLn):
            @property
            def TeX_info(self):
                raise AttributeError("boom")

        x, y, _ = lognormal_data
        with pytest.raises(AttributeError, match="boom"):
            Broken(x, y).set_TeX_report_normal_parameters(True)

    @pytest.mark.xfail(strict=True, reason="except AttributeError swallows it")
    def test_a_bug_computing_normal_parameters_is_not_taken_for_not_fitted(
        self, lognormal_data
    ):
        """An AttributeError inside ``normal_parameters`` reaches the TeX info.

        ON FAILURE: the code is wrong.
        """

        class Broken(GaussianLn):
            @property
            def normal_parameters(self):
                raise AttributeError("boom")

        x, y, _ = lognormal_data
        obj = Broken(x, y)
        obj.set_TeX_report_normal_parameters(True)
        with pytest.raises(AttributeError, match="boom"):
            obj._TeX_extra_params()

    def test_make_fit_success(self, lognormal_data):
        """GaussianLn fitted to noise-free log-normal data recovers mu, |sigma|, A.

        ON FAILURE: the code is wrong.
        """
        x, y, params = lognormal_data
        obj = GaussianLn(x, y)
        obj.make_fit()

        assert isinstance(obj.fit_result, OptimizeResult)
        assert "mu" in obj.popt
        assert "sigma" in obj.popt
        assert "A" in obj.popt

        # sigma enters squared, so its fitted sign is arbitrary.
        assert obj.popt["mu"] == noise_free(params["mu"])
        assert np.abs(obj.popt["sigma"]) == noise_free(params["sigma"])
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


def test_weights_summing_to_one_give_an_estimate():
    """y = [0.25, 0.5, 0.25] sums to 1 and still gives the weighted moments.

    x = [1, 2, 3] weighted by those y has mean 2 and variance 0.5; A is the
    peak, 0.5.

    ON FAILURE: the code is wrong.
    """
    p0 = Gaussian(np.array([1.0, 2, 3]), np.array([0.25, 0.5, 0.25])).p0
    assert p0 == exact([2.0, np.sqrt(0.5), 0.5])


def test_weights_summing_to_zero_give_no_estimate_without_a_numpy_warning():
    """y summing to zero gives ``p0`` None by check, not by dividing 0 by 0.

    numpy's invalid-value and divide warnings are errors here.

    ON FAILURE: the code is wrong.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        p0 = Gaussian(np.array([0.0, 1, 2, 3]), np.array([1.0, -1, 1, -1])).p0
    assert p0 is None


def test_an_overflowing_variance_alone_gives_no_estimate():
    """x = [-1e200, 0, 1e200] has mean 0 but a variance past the float maximum.

    One finite moment is not enough: ``p0`` is None.

    ON FAILURE: the code is wrong.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        p0 = Gaussian(np.array([-1e200, 0.0, 1e200]), np.ones(3)).p0
    assert p0 is None


def test_a_width_equal_to_half_the_spacing_of_two_distinct_x_is_resolved():
    """x = [1, 1, 3, 3] with equal weights: width 1 is half the spacing 2.

    Mean 2, variance 1 exactly. A width of exactly half the smallest spacing
    is resolved (the rule refuses only a narrower one), also when there are
    only two distinct x.

    ON FAILURE: the code is wrong.
    """
    p0 = Gaussian(np.array([1.0, 1, 3, 3]), np.ones(4)).p0
    assert p0 == exact([2.0, 1.0, 1.0])
