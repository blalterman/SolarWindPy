r""":py:mod:`~solarwidpy.fitfunctions` classes."""

from . import core
from . import lines
from . import gaussians
from . import exponentials
from . import power_laws
from . import moyal

# from . import hinge
from . import trend_fits

FitFunction = core.FitFunction
Gaussian = gaussians.Gaussian
Exponential = exponentials.Exponential
Line = lines.Line
PowerLaw = power_laws.PowerLaw
Moyal = moyal.Moyal
# Hinge = hinge.Hinge
TrendFit = trend_fits.TrendFit

# Exception classes for better error handling
FitFunctionError = core.FitFunctionError
InsufficientDataError = core.InsufficientDataError
FitFailedError = core.FitFailedError
InvalidParameterError = core.InvalidParameterError
