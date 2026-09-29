r""":py:mod:`~solarwidpy.fitfunctions` classes."""

from inspect import isabstract

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


def _fit_function_classes():
    """Return every concrete FitFunction subclass defined in this package.

    Classes are found by walking the subclass tree, so a new fit function is
    listed as soon as its module is imported above. Subclasses defined outside
    ``solarwindpy.fitfunctions`` (for example in tests) are excluded.
    """
    found, stack = set(), [core.FitFunction]
    while stack:
        for sub in stack.pop().__subclasses__():
            if sub not in found:
                found.add(sub)
                stack.append(sub)
    return sorted(
        (
            cls
            for cls in found
            if cls.__module__.startswith(__name__ + ".") and not isabstract(cls)
        ),
        key=lambda cls: cls.__name__,
    )


_NEEDS_INSTANCE = "(formula needs a fitted instance)"


def _class_formula(cls):
    """Return ``cls``'s LaTeX formula without fitting data.

    ``TeX_function`` is usually a property whose value does not depend on the
    instance. A formula that does, or one that is not a string, is reported as
    ``_NEEDS_INSTANCE`` so a single class cannot break the whole listing.
    """
    tex = cls.TeX_function
    try:
        tex = tex.fget(None) if isinstance(tex, property) else tex
    except (AttributeError, TypeError):
        return _NEEDS_INSTANCE
    if not isinstance(tex, str):
        return _NEEDS_INSTANCE
    return "; ".join(tex.splitlines())


def available():
    """Print every available fit function, its module and its LaTeX formula.

    The formula is read from each class's ``TeX_function`` without fitting any
    data. Formulas that span several lines are joined with ``"; "``.
    """
    rows = [
        (cls.__name__, cls.__module__.rsplit(".", 1)[-1], _class_formula(cls))
        for cls in _fit_function_classes()
    ]
    header = ("Fit function", "Module", "LaTeX")
    widths = [max(len(r[i]) for r in rows + [header]) for i in range(2)]

    def fmt(row):
        return f"{row[0]:<{widths[0]}}  {row[1]:<{widths[1]}}  {row[2]}"

    lines = [fmt(header), fmt(("-" * widths[0], "-" * widths[1], "-" * 5))]
    print("\n".join(lines + [fmt(r) for r in rows]))
