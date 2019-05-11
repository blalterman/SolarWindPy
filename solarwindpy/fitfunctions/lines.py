#!/usr/bin/env python
r""":py:mod:`Line` and similar `FitFunction` sublcasses.
"""
import pdb  # noqa: F401
import numpy as np

from .core import FitFunction


class Line(FitFunction):
    def __init__(self, xobs, yobs, **kwargs):
        super(Line, self).__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        def line(x, m, b):
            return (m * x) + b

        return line

    @property
    def p0(self):
        r"""Calculate the initial guess for the line parameters.

        Return
        ------
        p0 : list
            The initial guesses as [m, b].
        """
        assert self.sufficient_data

        dy, dx = np.ediff1d(self.yobs), np.ediff1d(self.xobs)
        assert np.all(np.isfinite(dx)), "dx = 0 -> m = infty"

        m = dy / dx
        m = np.median(m)
        assert np.all(np.isfinite(m))

        b = (m * self.xobs) - self.yobs
        b = np.median(b)

        p0 = [m, b]
        return p0

    @property
    def TeX_function(self):
        TeX = r"f(x)=m \cdot x + b"
        return TeX
