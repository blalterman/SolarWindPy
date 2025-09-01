#!/usr/bin/env python
r""":py:mod:`Gaussian` and related `FitFunction` sublcasses."""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Moyal(FitFunction):
    def __init__(self, sigma, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    #         self._sigma = float(sigma)

    @property
    def function(self):
        def moyal(x, mu, sigma, A):
            center = x - mu
            #             sigma = self.sigma
            ms_sq = (center / sigma) ** 2
            arg0 = 0.5 * (ms_sq - np.exp(ms_sq))
            arg1 = np.exp(arg0)
            out = A * (np.exp(arg1) - 1)
            return out

        return moyal

    @property
    def sigma(self):
        r"""Initial guess for mean value."""
        return self._sigma

    @property
    def p0(self):
        r"""Calculate the initial guess for the Gaussian parameters.

        Return
        ------
        p0 : list
            The initial guesses as [mu, sigma, A].
        """
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())
        #         std = self.sigma

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
        TeX = r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2 - e^{\frac{x-\mu}{\sigma}}^2}"
        TeX = "lala"
        return TeX
