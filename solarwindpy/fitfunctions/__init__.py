"""Curve-fitting utilities.

This subpackage exposes :class:`FitFunction` along with common
fit implementations such as :class:`Gaussian` and :class:`Exponential`.
"""

from . import core
from . import lines
from . import gaussians
from . import exponentials
from . import power_laws

# from . import hinge
from . import trend_fits

FitFunction = core.FitFunction
Gaussian = gaussians.Gaussian
Exponential = exponentials.Exponential
Line = lines.Line
PowerLaw = power_laws.PowerLaw
# Hinge = hinge.Hinge
TrendFit = trend_fits.TrendFit
