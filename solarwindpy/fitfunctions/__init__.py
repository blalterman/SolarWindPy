r""":py:mod:`~solarwidpy.fitfunctions` classes.
"""

from . import core
from . import lines
from . import gaussians
from . import exponentials
from . import power_laws
from . import trend_fits

FitFunction = core.FitFunction
Gaussian = gaussians.Gaussian
Exponential = exponentials.Exponential
Line = lines.Line
PowerLaw = power_laws.PowerLaw
TrendFit = trend_fits.TrendFit
