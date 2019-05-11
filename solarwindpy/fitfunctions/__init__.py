r""":py:mod:`~solarwidpy.fitfunctions` classes.
"""

from . import core
from . import lines
from . import gaussians
from . import exponentials

FitFunction = core.FitFunction
Gaussian = gaussians.Gaussian
Exponential = exponentials.Exponential
Line = lines.Line