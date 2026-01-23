r""":py:mod:`~solarwidpy.fitfunctions` classes."""

from . import core
from . import lines
from . import gaussians
from . import exponentials
from . import power_laws
from . import moyal

from . import hinge
from . import heaviside
from . import trend_fits
from . import composite

FitFunction = core.FitFunction
Gaussian = gaussians.Gaussian
Exponential = exponentials.Exponential
Line = lines.Line
PowerLaw = power_laws.PowerLaw
Moyal = moyal.Moyal
HingeSaturation = hinge.HingeSaturation
TwoLine = hinge.TwoLine
Saturation = hinge.Saturation
HingeMin = hinge.HingeMin
HingeMax = hinge.HingeMax
HingeAtPoint = hinge.HingeAtPoint
HeavySide = heaviside.HeavySide
TrendFit = trend_fits.TrendFit
GaussianPlusHeavySide = composite.GaussianPlusHeavySide
GaussianTimesHeavySide = composite.GaussianTimesHeavySide
GaussianTimesHeavySidePlusHeavySide = composite.GaussianTimesHeavySidePlusHeavySide

# Exception classes for better error handling
FitFunctionError = core.FitFunctionError
InsufficientDataError = core.InsufficientDataError
FitFailedError = core.FitFailedError
InvalidParameterError = core.InvalidParameterError
