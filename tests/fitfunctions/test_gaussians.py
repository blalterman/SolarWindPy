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
