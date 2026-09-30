r"""Fit parametric models to observations with robust least squares.

Each fit function is a subclass of
:class:`~solarwindpy.fitfunctions.core.FitFunction` and is importable as
``solarwindpy.fitfunctions.<Name>``. :func:`available` prints every one with
its module and LaTeX formula.

Using a fit function
--------------------
Construct it from the observations, then call ``make_fit``:

>>> import numpy as np
>>> from solarwindpy.fitfunctions import Line
>>> x = np.arange(10.0)
>>> fit = Line(x, 2.0 * x + 1.0)
>>> fit.make_fit()
>>> print(f"m={fit.popt['m']:.2f}, b={fit.popt['b']:.2f}")
m=2.00, b=1.00

Every subclass takes ``(xobs, yobs, **kwargs)``. The keyword arguments of
:class:`~solarwindpy.fitfunctions.core.FitFunction` select which observations
enter the fit (``xmin``, ``xmax``, ``xoutside``, ``ymin``, ``ymax``,
``youtside``, ``wmin``, ``wmax``) and supply 1-sigma ``weights``. A few
subclasses add their own, such as the ``guess_x0`` initial step position of
:class:`~solarwindpy.fitfunctions.composite.GaussianTimesHeavySide`.

How a fit runs
--------------
:meth:`~solarwindpy.fitfunctions.core.FitFunction.make_fit` is a template
method shared by every subclass. It checks that there are at least as many
observations as parameters, runs :func:`scipy.optimize.least_squares`,
computes the optimized parameters, their covariance and
:math:`\chi^2_\nu`, then builds the LaTeX annotation
(:class:`~solarwindpy.fitfunctions.tex_info.TeXinfo`) and the plotter
(:class:`~solarwindpy.fitfunctions.plots.FFPlot`).

- The default loss is ``"huber"`` with ``f_scale=0.1``, method ``"trf"``;
  ``loss``, ``f_scale``, ``method``, ``bounds``, ``p0`` and other
  :func:`~scipy.optimize.least_squares` keywords pass through ``make_fit``.
- ``weights`` are treated as :func:`scipy.optimize.curve_fit` treats
  ``sigma``: a 1-D array holds per-point uncertainties, a 2-D array a
  covariance matrix. ``absolute_sigma=True`` raises ``NotImplementedError``.
- The covariance is the pseudo-inverse of :math:`J^T J` from the final
  Jacobian, scaled by the robust :math:`\chi^2_\nu`; ``psigma`` is the square
  root of its diagonal.
- With ``return_exception=True``, a failed fit returns the exception instead
  of raising it, for loops over many fits.

Failures are reported with
:class:`~solarwindpy.fitfunctions.core.FitFunctionError` and its subclasses
:class:`~solarwindpy.fitfunctions.core.InsufficientDataError`,
:class:`~solarwindpy.fitfunctions.core.FitFailedError` and
:class:`~solarwindpy.fitfunctions.core.InvalidParameterError`.

Writing a fit function
----------------------
A subclass implements three abstract properties: ``function`` (the model,
whose arguments after ``x`` are the fit parameters, in order), ``p0`` (the
initial guess, in the same order) and ``TeX_function`` (the model in LaTeX).
The metaclass :class:`~solarwindpy.fitfunctions.core.FitFunctionMeta` combines
:class:`abc.ABCMeta` with NumPy-style docstring inheritance, so a subclass
method without a docstring, or with only some sections, inherits the missing
sections from :class:`~solarwindpy.fitfunctions.core.FitFunction`.
:class:`~solarwindpy.fitfunctions.trend_fits.TrendFit` fits one fit function
in each bin of 2-D aggregated data and a second to the trend of the results.
"""

__all__ = [
    "FitFunction",
    "TrendFit",
    "available",
    # Fit functions
    "Exponential",
    "ExponentialCDF",
    "ExponentialPlusC",
    "Gaussian",
    "GaussianLn",
    "GaussianNormalized",
    "GaussianPlusHeavySide",
    "GaussianTimesHeavySide",
    "GaussianTimesHeavySidePlusHeavySide",
    "HeavySide",
    "HingeAtPoint",
    "HingeMax",
    "HingeMin",
    "HingeSaturation",
    "Line",
    "LineXintercept",
    "PowerLaw",
    "PowerLawOffCenter",
    "PowerLawPlusC",
    "Saturation",
    "TwoLine",
    # Exceptions
    "FitFunctionError",
    "InsufficientDataError",
    "FitFailedError",
    "InvalidParameterError",
]

from inspect import isabstract

from . import core
from . import lines
from . import gaussians
from . import exponentials
from . import power_laws

from . import hinge
from . import heaviside
from . import trend_fits
from . import composite

FitFunction = core.FitFunction
TrendFit = trend_fits.TrendFit

Exponential = exponentials.Exponential
ExponentialCDF = exponentials.ExponentialCDF
ExponentialPlusC = exponentials.ExponentialPlusC
Gaussian = gaussians.Gaussian
GaussianLn = gaussians.GaussianLn
GaussianNormalized = gaussians.GaussianNormalized
GaussianPlusHeavySide = composite.GaussianPlusHeavySide
GaussianTimesHeavySide = composite.GaussianTimesHeavySide
GaussianTimesHeavySidePlusHeavySide = composite.GaussianTimesHeavySidePlusHeavySide
HeavySide = heaviside.HeavySide
HingeAtPoint = hinge.HingeAtPoint
HingeMax = hinge.HingeMax
HingeMin = hinge.HingeMin
HingeSaturation = hinge.HingeSaturation
Line = lines.Line
LineXintercept = lines.LineXintercept
PowerLaw = power_laws.PowerLaw
PowerLawOffCenter = power_laws.PowerLawOffCenter
PowerLawPlusC = power_laws.PowerLawPlusC
Saturation = hinge.Saturation
TwoLine = hinge.TwoLine

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
