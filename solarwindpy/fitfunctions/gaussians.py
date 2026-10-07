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

from .core import FitFunction


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

    def make_fit(self, *args, **kwargs):
        r"""Run the fit, then label ``mu`` and ``sigma`` as Greek letters in the TeX info."""
        result = super().make_fit(*args, **kwargs)
        try:
            self.TeX_info.set_TeX_argnames(mu=r"\mu", sigma=r"\sigma")
        except AttributeError:  # Fit failed
            pass
        return result


class GaussianNormalized(FitFunction):
    """Normalized Gaussian distribution where integral equals n.

    Fits data to the form: (n / (sqrt(2*pi) * sigma)) * exp(-0.5 * ((x - mu) / sigma)^2)

    Notes
    -----
    The normalization parameter n represents the total area under
    the Gaussian curve, useful for fitting probability distributions
    or particle count distributions.
    """

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

    def make_fit(self, *args, **kwargs):
        r"""Run the fit, then label ``mu`` and ``sigma`` as Greek letters in the TeX info."""
        result = super().make_fit(*args, **kwargs)
        try:
            self.TeX_info.set_TeX_argnames(mu=r"\mu", sigma=r"\sigma")
        except AttributeError:  # Fit failed
            pass
        return result


class GaussianLn(FitFunction):
    r"""Log-normal distribution for skewed data fitting.

    Fits a Gaussian in logarithmic space where :math:`\ln(x)` follows
    a normal distribution.

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
        r"""The model as ``f(x, m, s, A)``."""

        def gaussian_ln(x, m, s, A):
            """Evaluate ``A * exp(-0.5 * ((ln(x) - m) / s)**2)``."""
            lnx = np.log(x)

            coeff = A

            arg = -0.5 * (((lnx - m) / s) ** 2.0)

            return coeff * np.exp(arg)

        return gaussian_ln

    @property
    def p0(self):
        r"""Return initial guesses ``[m, s, A]`` for the fit, or None.

        The model is a Gaussian in :math:`\ln x`, so the guess is estimated in
        :math:`\ln x`: ``m`` and ``s`` are the mean and standard deviation of
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
        m, var = moments

        p0 = [m, np.sqrt(var), y.max()]
        return p0

    @property
    def TeX_function(self):
        r"""LaTeX form of the model."""
        TeX = (
            r"f(x) ="
            r"A \cdot"
            r"\exp\left["
            r"-\frac{\left(\ln x - m\right)^2}{2 s^2}"
            r"\right]"
        )
        return TeX

    @property
    def normal_parameters(self):
        r"""Calculate the normal parameters from log-normal parameters.

        .. math::

            \mu = \exp[m + (s^2)/2]
            \sigma = \sqrt{\exp[s^2 + 2m] (\exp[s^2] - 1)}
        """
        m = self.popt["m"]
        s = self.popt["s"]

        mu = np.exp(m + ((s**2.0) / 2.0))
        sigma = np.exp(s**2.0 + 2.0 * m)
        sigma *= np.exp(s**2.0) - 1.0
        sigma = np.sqrt(sigma)

        return dict(mu=mu, sigma=sigma)

    @property
    def TeX_report_normal_parameters(self):
        r"""Report normal parameters, not log-normal parameters in the TeX info."""
        try:
            return self._use_normal_parameters
        except AttributeError:
            return False

    def set_TeX_report_normal_parameters(self, new):
        r"""Set :attr:`TeX_report_normal_parameters` to ``bool(new)``."""
        new = bool(new)
        self._use_normal_parameters = new

    @property
    def TeX_popt(self):
        r"""Create a dictionary with ``(k, v)`` pairs corresponding to parameter values.

        ``(self.argnames, :math:`p_{\mathrm{opt}} \pm \sigma_p`)`` with the
        appropriate uncertainty.

        See ``set_TeX_trans_argnames`` to translate the argnames for TeX.
        """
        TeX_popt = super(GaussianLn, self).TeX_popt

        if self.TeX_report_normal_parameters:
            popt = self.normal_parameters.items()
            # use -9999 to indicate fill value that hasn't been set.
            # I need to figure out how to calculate the transformation
            # of the uncertainty of log normal to normal.
            normal_popt = {k: self.val_uncert_2_string(v, np.nan) for k, v in popt}
            normal_popt = {k: v.split(r" \pm")[0] for k, v in normal_popt.items()}

            translate = dict(mu=r"\mu", sigma=r"\sigma")
            for k0, k1 in translate.items():
                normal_popt[k1] = normal_popt[k0]
                del normal_popt[k0]

            TeX_popt.update(normal_popt)

        return TeX_popt
