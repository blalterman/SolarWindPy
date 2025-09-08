#!/usr/bin/env python
r"""Gaussian-based fit functions.

The classes here implement standard Gaussian shapes and common
variations used throughout the package.  Each class inherits from
:class:`~solarwindpy.fitfunctions.core.FitFunction` and defines the
target function, initial parameter estimates, and LaTeX output helpers.
"""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Gaussian(FitFunction):
    """Standard Gaussian distribution for symmetric peak fitting.

    Fits data to the form: A * exp(-0.5 * ((x - mu) / sigma)^2)
    """

    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def gaussian(x, mu, sigma, A):
            arg = -0.5 * (((x - mu) / sigma) ** 2.0)
            return A * np.exp(arg)

        return gaussian

    @property
    def p0(self):
        r"""Return initial guesses ``[mu, sigma, A]`` for the fit."""
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if e.message.startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)

        p0 = [mean, std, peak]
        return p0

    @property
    def TeX_function(self):
        #         TeX = r"f(x)=\frac{1}{\sqrt{2 \pi} \sigma} A\cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2}"
        TeX = r"f(x)=A \cdot e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}"
        return TeX

    def make_fit(self, *args, **kwargs):
        super().make_fit(*args, **kwargs)
        try:
            self.TeX_info.set_TeX_argnames(mu=r"\mu", sigma=r"\sigma")
        except AttributeError:  # Fit failed
            pass


class GaussianNormalized(FitFunction):
    """Normalized Gaussian distribution where integral equals n.

    Fits data to the form: (n / (sqrt(2*pi) * sigma)) * exp(-0.5 * ((x - mu) / sigma)^2)
    """

    def __init__(self, xobs, yobs, **kwargs):
        """Initialize normalized Gaussian fit.

        Notes
        -----
        The normalization parameter n represents the total area under
        the Gaussian curve, useful for fitting probability distributions
        or particle count distributions.
        """
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def gaussian_normalized(x, mu, sigma, n):
            arg = -0.5 * (((x - mu) / sigma) ** 2.0)
            A = n / (np.sqrt(2 * np.pi) * sigma)
            return A * np.exp(arg)

        return gaussian_normalized

    @property
    def p0(self):
        r"""Return initial guesses ``[mu, sigma, n]`` for the fit."""
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if e.message.startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)

        n = peak * std * np.sqrt(2 * np.pi)
        p0 = [mean, std, n]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=\frac{n}{\sqrt{2 \pi} \sigma} e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}"
        #         TeX = r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2}"
        return TeX

    def make_fit(self, *args, **kwargs):
        super().make_fit(*args, **kwargs)
        try:
            self.TeX_info.set_TeX_argnames(mu=r"\mu", sigma=r"\sigma")
        except AttributeError:  # Fit failed
            pass


class GaussianLn(FitFunction):
    r"""Log-normal distribution for skewed data fitting.

    Fits a Gaussian in logarithmic space where :math:`\ln(x)` follows
    a normal distribution.

    References
    ----------
    .. [1] https://mathworld.wolfram.com/LogNormalDistribution.html
    """

    def __init__(self, xobs, yobs, **kwargs):
        """Initialize log-normal Gaussian fit.

        Notes
        -----
        xobs must be positive for log transformation.
        This distribution is commonly used for particle size distributions
        and velocity distributions in solar wind where values are
        positively skewed.
        """
        super().__init__(xobs, yobs, **kwargs)
        self.set_TeX_report_normal_parameters(False)

    @property
    def function(self):
        #         def gaussian_ln(x, m, s, A):
        #             x = np.log(x)
        #             coeff = (np.sqrt(2.0 * np.pi) * s) ** (-1.0)
        #             arg = -0.5 * (((x - m) / s) ** 2.0)
        #             return A * coeff * np.exp(arg)

        def gaussian_ln(x, m, s, A):
            lnx = np.log(x)

            coeff = A
            #             coeff *= (np.sqrt(2.0 * np.pi) * s * x) ** (-1.0)

            arg = -0.5 * (((lnx - m) / s) ** 2.0)

            return coeff * np.exp(arg)

        #         def gaussian_ln(x, m, s, A):
        #             arg = m + (s * x)
        #             return A * np.exp(arg)

        return gaussian_ln

    @property
    def p0(self):
        r"""Return initial guesses ``[ln(mu), ln(sigma), ln(A)]``."""
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y

        mean = (x * y).sum() / y.sum()
        std = ((x - mean) ** 2.0 * y).sum() / y.sum()

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if e.message.startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)

        p0 = [mean, std, peak]
        p0 = [np.log(x) for x in p0]
        return p0

    @property
    def TeX_function(self):
        TeX = (
            r"f(x) = A \cdot  "
            r"\mathrm{exp}\left[-\frac{1}{2}  "
            r"(\frac{\mathrm{ln}(x)-m}{s})^2\right]"
        )
        TeX = (
            r"f(x) ="
            r"A \cdot"
            #                r"\frac{1}{\sqrt{2\pi} s x}"
            r"\exp\left["
            r"\frac{\left(\ln x - m\right)^2}{2 s^2}"
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
            # psigma = self.psigma
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
