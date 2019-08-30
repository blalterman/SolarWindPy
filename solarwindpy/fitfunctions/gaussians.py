#!/usr/bin/env python
r""":py:mod:`Gaussian` and related `FitFunction` sublcasses.
"""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Gaussian(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        super(Gaussian, self).__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def gaussian(x, mu, sigma, A):
            arg = -0.5 * (((x - mu) / sigma) ** 2.0)
            return A * np.exp(arg)

        return gaussian

    @property
    def p0(self):
        r"""Calculate the initial guess for the Gaussian parameters.

        Return
        ------
        p0 : list
            The initial guesses as [mu, sigma, A].
        """
        assert self.sufficient_data

        x, y = self.xobs, self.yobs
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
        TeX = r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2}"
        return TeX


class GaussianLn(FitFunction):
    r"""Gaussian where taking `$ln(x)$`.
    """

    def __init__(self, xobs, yobs, **kwargs):
        super(GaussianLn, self).__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def gaussian_ln(x, m, s, A):
            x = np.log(x)
            coeff = (np.sqrt(2.0 * np.pi) * s) ** (-1.0)
            arg = -0.5 * (((x - m) / s) ** 2.0)
            return A * coeff * np.exp(arg)

    @property
    def p0(self):
        r"""
        Calculate the initial guess for the log normal parameters.

        Return
        ------
        p0 : list
            The initial guesses as [mean, std, peak].
        """
        assert self.sufficient_data

        x, y = self.xobs, self.yobs

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
            r"\mathrm{exp}[-\frac{1}{2}  "
            r"(\frac{\mathrm{ln}(x)-m}{s})^2]"
        )
        return TeX

    @property
    def normal_parameters(self):
        r"""Calculate the normal parameters from log-normal parameters.

            $\mu = \exp[m + (s^2)/2]$
            $\sigma = \sqrt{ \exp[s^2 + 2m] (\exp[s^2] - 1)}$
        """
        m = self.popt["m"]
        s = self.popt["s"]

        mu = np.exp(m + ((s ** 2.0) / 2.0))
        sigma = np.exp(s ** 2.0 + 2.0 * m)
        sigma *= np.exp(s ** 2.0) - 1.0
        sigma = np.sqrt(sigma)

        return dict(mu=mu, sigma=sigma)

    @property
    def TeX_report_normal_parameters(self):
        r"""Report normal parameters, not log-normal parameters in the TeX info.
        """
        try:
            return self._use_normal_parameters
        except AttributeError:
            return False

    def set_TeX_report_normal_parameters(self, new):
        new = bool(new)
        self._use_normal_parameters = new

    @property
    def TeX_popt(self):
        r"""
        Create a dictionary with (k, v) pairs corresponding to
        (self.argnames, popt \pm psigma) with the appropriate uncertainty.

        See self.set_TeX_trans_argnames to translate the argnames for TeX.
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
