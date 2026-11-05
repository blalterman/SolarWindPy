#!/usr/bin/env python
r"""Gaussian-based fit functions.

The classes here implement standard Gaussian shapes and common
variations used throughout the package.  Each class inherits from
:class:`~solarwindpy.fitfunctions.core.FitFunction` and defines the
target function, initial parameter estimates, and LaTeX output helpers.
"""

__all__ = [
    "Gaussian",
    "GaussianNormalized",
    "GaussianLn",
]

import numpy as np

from .core import FitFunction, NotFittedError


def _weighted_moments(fitfunction, x, y):
    r"""Mean and variance of ``x`` weighted by ``y``, or None.

    The mean is :math:`\sum x y / \sum y` and the variance
    :math:`\sum (x - \mathrm{mean})^2 y / \sum y`. Both are undefined when
    ``x`` is empty or ``y`` sums to zero, they are not finite when a sum
    overflows (finite data near the float maximum), and a negative variance
    (possible when some weights are negative) has no square root. A width
    (the square root of the variance) under half the smallest spacing between
    distinct ``x``, including any width when there is only one distinct
    ``x``, is narrower than the samples can resolve, as when all the weight
    sits at one ``x``. In those cases, the reason is logged and None
    returned, so the caller's ``p0`` can return None.

    Parameters
    ----------
    fitfunction : FitFunction
        Whose logger records why no estimate was made.
    x, y : numpy.ndarray
        Positions and their weights.

    Returns
    -------
    tuple of float or None
        ``(mean, variance)``, or None.
    """
    total = y.sum()
    if x.size == 0 or total == 0 or not np.isfinite(total):
        fitfunction.logger.warning(
            f"No weighted mean: {x.size} points with weights summing to {total}."
            "\nReturning None."
        )
        return None

    mean = (x * y).sum() / total
    var = ((x - mean) ** 2.0 * y).sum() / total
    if not (np.isfinite(mean) and np.isfinite(var)):
        fitfunction.logger.warning(
            f"Weighted mean {mean} or variance {var} is not finite (overflow)."
            "\nReturning None."
        )
        return None
    if var < 0:
        fitfunction.logger.warning(
            f"Weighted variance {var} is negative, so no width.\nReturning None."
        )
        return None

    distinct = np.unique(x)
    half_spacing = 0.5 * np.diff(distinct).min() if distinct.size > 1 else np.inf
    if np.sqrt(var) < half_spacing:
        fitfunction.logger.warning(
            f"Width {np.sqrt(var)} is under half the smallest x spacing "
            f"({half_spacing}), so the samples cannot resolve it.\nReturning None."
        )
        return None

    return mean, var


class Gaussian(FitFunction):
    """Standard Gaussian distribution for symmetric peak fitting.

    Fits data to the form: A * exp(-0.5 * ((x - mu) / sigma)^2)
    """

    _TeX_argnames = {"mu": r"\mu", "sigma": r"\sigma"}

    @property
    def function(self):
        r"""The model as ``f(x, mu, sigma, A)``."""

        def gaussian(x, mu, sigma, A):
            """Evaluate ``A * exp(-0.5 * ((x - mu) / sigma)**2)``."""
            arg = -0.5 * (((x - mu) / sigma) ** 2.0)
            return A * np.exp(arg)

        return gaussian

    @property
    def p0(self):
        r"""Return initial guesses ``[mu, sigma, A]`` for the fit, or None.

        ``mu`` and ``sigma`` are the mean and standard deviation of ``x``
        weighted by ``y``, and ``A`` is the largest ``y``. When ``y`` sums to
        zero, the weighted variance is negative, or the width ``sigma`` is
        under half the smallest spacing between distinct ``x`` (narrower than
        the samples resolve, as when all the weight sits at one ``x``), there
        is no estimate and ``p0`` is None.
        """
        self._require_sufficient_data()

        x, y = self.observations.used.x, self.observations.used.y
        moments = _weighted_moments(self, x, y)
        if moments is None:
            return None
        mean, var = moments
        std = np.sqrt(var)

        peak = y.max()

        p0 = [mean, std, peak]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=A \cdot e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}"
        return TeX


class GaussianNormalized(FitFunction):
    """Normalized Gaussian distribution where integral equals n.

    Fits data to the form: (n / (sqrt(2*pi) * sigma)) * exp(-0.5 * ((x - mu) / sigma)^2)

    Notes
    -----
    The normalization parameter n represents the total area under
    the Gaussian curve, useful for fitting probability distributions
    or particle count distributions.
    """

    _TeX_argnames = {"mu": r"\mu", "sigma": r"\sigma"}

    @property
    def function(self):
        r"""The model as ``f(x, mu, sigma, n)``."""

        def gaussian_normalized(x, mu, sigma, n):
            """Evaluate a Gaussian of area ``n``, mean ``mu``, width ``sigma``."""
            arg = -0.5 * (((x - mu) / sigma) ** 2.0)
            A = n / (np.sqrt(2 * np.pi) * sigma)
            return A * np.exp(arg)

        return gaussian_normalized

    @property
    def p0(self):
        r"""Return initial guesses ``[mu, sigma, n]`` for the fit, or None.

        Estimated as in :attr:`Gaussian.p0`, with ``n`` the area of a
        Gaussian of that width and peak. None under the same conditions.
        """
        self._require_sufficient_data()

        x, y = self.observations.used.x, self.observations.used.y
        moments = _weighted_moments(self, x, y)
        if moments is None:
            return None
        mean, var = moments
        std = np.sqrt(var)

        peak = y.max()

        n = peak * std * np.sqrt(2 * np.pi)
        p0 = [mean, std, n]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = r"f(x)=\frac{n}{\sqrt{2 \pi} \sigma} e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}"
        return TeX


class GaussianLn(FitFunction):
    r"""Log-normal distribution for skewed data fitting.

    Fits a Gaussian in logarithmic space where :math:`\ln(x)` follows
    a normal distribution with mean ``mu`` and standard deviation ``sigma``,
    the usual parameters of a log-normal.

    Parameters
    ----------
    **kwargs
        Additional arguments passed to
        :class:`~solarwindpy.fitfunctions.core.FitFunction`.

    Raises
    ------
    ValueError
        If any used x is not positive, where :math:`\ln x` is undefined, at
        construction or when
        :meth:`~solarwindpy.fitfunctions.core.FitFunction.set_fit_obs` selects
        new observations.

    Notes
    -----
    This distribution is commonly used for particle size distributions
    and velocity distributions in solar wind where values are
    positively skewed.

    References
    ----------
    .. [1] https://mathworld.wolfram.com/LogNormalDistribution.html
    """

    _TeX_argnames = {"mu": r"\mu", "sigma": r"\sigma"}

    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)
        self.set_TeX_report_normal_parameters(False)

    def _check_used_obs(self, used):
        r"""Raise ``ValueError`` if any used x is not positive: ln x is undefined."""
        x = used.x
        if np.any(x <= 0):
            raise ValueError(
                f"GaussianLn needs every used x > 0: ln x is undefined at "
                f"{np.sum(x <= 0)} of {x.size}."
            )

    @property
    def function(self):
        r"""The model as ``f(x, mu, sigma, A)``."""

        def gaussian_ln(x, mu, sigma, A):
            """Evaluate ``A * exp(-0.5 * ((ln(x) - mu) / sigma)**2)``."""
            lnx = np.log(x)

            coeff = A

            arg = -0.5 * (((lnx - mu) / sigma) ** 2.0)

            return coeff * np.exp(arg)

        return gaussian_ln

    @property
    def p0(self):
        r"""Return initial guesses ``[mu, sigma, A]`` for the fit, or None.

        The model is a Gaussian in :math:`\ln x`, so the guess is estimated in
        :math:`\ln x`: ``mu`` and ``sigma`` are the mean and standard deviation of
        :math:`\ln x` weighted by ``y``, and ``A`` is the largest ``y`` (``A``
        multiplies the model directly and is not logged). ``p0`` is None when
        the weighted moments of :math:`\ln x` give no estimate, under the same
        rules as :attr:`Gaussian.p0` applied to :math:`\ln x`.
        """
        self._require_sufficient_data()

        x, y = self.observations.used.x, self.observations.used.y

        moments = _weighted_moments(self, np.log(x), y)
        if moments is None:
            return None
        mu, var = moments

        p0 = [mu, np.sqrt(var), y.max()]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = (
            r"f(x) = "
            r"A \cdot "
            r"\exp\left["
            r"-\frac{\left(\ln x - \mu\right)^2}{2 \sigma^2}"
            r"\right]"
        )
        return TeX

    @property
    def normal_parameters(self):
        r"""Linear-space mean and standard deviation of the log-normal variable.

        The fit models :math:`\ln X \sim \mathcal{N}(\mu, \sigma^2)`, with
        the natural logarithm. This returns the mean and the standard
        deviation of :math:`X` itself, not of :math:`\ln X`:

        .. math::

            \mathrm{mean}(X) = \exp[\mu + \sigma^2/2]

            \mathrm{std}(X) = \sqrt{\exp[2\mu + \sigma^2] (\exp[\sigma^2] - 1)}

        Returns
        -------
        dict
            ``mean`` and ``std``, from the fitted ``mu`` and ``sigma``. They
            are not named ``mu`` and ``sigma``, which are the fitted
            parameters of :math:`\ln X`.
        """
        mu = self.popt["mu"]
        sigma = self.popt["sigma"]

        mean = np.exp(mu + ((sigma**2.0) / 2.0))
        std = np.exp(sigma**2.0 + 2.0 * mu)
        std *= np.exp(sigma**2.0) - 1.0
        std = np.sqrt(std)

        return dict(mean=mean, std=std)

    @property
    def TeX_report_normal_parameters(self):
        r"""Whether the TeX info also reports the linear-space mean and std.

        When True, the annotation lists :attr:`normal_parameters` after the
        fitted ``mu``, ``sigma`` and ``A``, without an uncertainty: the
        propagation of the log-normal uncertainties is not implemented.
        """
        try:
            return self._use_normal_parameters
        except AttributeError:
            return False

    def set_TeX_report_normal_parameters(self, new):
        r"""Set :attr:`TeX_report_normal_parameters` to ``bool(new)``.

        A TeX info already built by a fit is updated to match.
        """
        new = bool(new)
        self._use_normal_parameters = new
        try:
            tex_info = self.TeX_info
        except NotFittedError:
            return
        tex_info.set_extra_params(self._TeX_extra_params())

    def _TeX_extra_params(self):
        r"""The linear-space mean and std by their TeX, or None.

        None unless :attr:`TeX_report_normal_parameters` and a fit has set
        ``popt``.
        """
        if not self.TeX_report_normal_parameters:
            return None
        try:
            normal = self.normal_parameters
        except NotFittedError:
            return None
        return {
            r"\mathrm{mean}(x)": normal["mean"],
            r"\mathrm{std}(x)": normal["std"],
        }
