#!/usr/bin/env python
r"""Moyal distribution fit function for asymmetric peak fitting.

The Moyal distribution is commonly used in particle physics and solar wind
analysis for modeling energy loss distributions and asymmetric velocity
distributions.
"""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Moyal(FitFunction):
    """Moyal distribution for fitting asymmetric peaks.

    The Moyal distribution is the convolution of a Landau distribution
    with a Gaussian, commonly used in particle physics for energy loss
    distributions.
    """

    def __init__(self, xobs, yobs, **kwargs):
        # Docstring inherited from FitFunction
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

    # Note: sigma property removed as it was not properly initialized
    # The sigma parameter is now handled entirely through the fitting process

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
        """LaTeX representation of the Moyal function.

        Returns
        -------
        str
            LaTeX string for the Moyal distribution formula.
        """
        # Moyal distribution approximation used in this implementation
        TeX = r"f(x) = A \cdot \exp\left[\frac{1}{2}\left(\left(\frac{x-\mu}{\sigma}\right)^2 - \exp\left(\left(\frac{x-\mu}{\sigma}\right)^2\right)\right)\right]"
        return TeX
