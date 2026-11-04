# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Contracts every concrete fit function keeps, checked class by class.

The classes are found by importing every module of
``solarwindpy.fitfunctions`` and reading what each defines, so a new fit
function falls under these tests; ``test_every_class_has_a_case`` fails until
it has the constructor case it needs.
"""

import importlib
import importlib.util
import inspect
import pkgutil

import numpy as np
import pytest

import solarwindpy.fitfunctions as ff
from solarwindpy.fitfunctions.core import FitFunction
from solarwindpy.fitfunctions.hinge import HingeMax
from tests.fitfunctions._attempt import attempt_fit


def _concrete_fit_functions():
    found = {}
    for info in pkgutil.walk_packages(ff.__path__, ff.__name__ + "."):
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and obj.__module__ == info.name
                and issubclass(obj, FitFunction)
                and not inspect.isabstract(obj)
            ):
                found[name] = obj
    return found


CLASSES = _concrete_fit_functions()

# x from 2 keeps every model defined: GaussianLn needs x > 0, and
# PowerLawOffCenter bounds x0 below the smallest x, which the all-ones start
# (x0 = 1) then satisfies.
X = np.linspace(2.0, 10.0, 33)
Y = 3.0 * np.exp(-0.5 * ((X - 5.0) / 1.5) ** 2) + 1.0


def _build(name, **kwargs):
    return CLASSES[name](X, Y, **kwargs)


def test_every_class_has_a_case():
    """The module scan finds exactly the package's fit functions, and each constructs.

    ``CLASSES`` comes from importing every module and reading what it defines.
    ``fitfunctions._fit_function_classes`` walks the ``FitFunction`` subclass
    tree instead. The two discoveries must agree and find at least one class,
    so every fit function the package lists is checked by these tests.

    ON FAILURE: the code is wrong if the two discoveries differ; otherwise a
    fit function needs a constructor keyword or set-up before a fit; give
    ``_build`` a case for it.
    """
    by_subclass_tree = {cls.__name__ for cls in ff._fit_function_classes()}
    assert CLASSES, "the module scan found no fit function"
    assert set(CLASSES) == by_subclass_tree
    for name in CLASSES:
        _build(name)


def test_the_heaviside_step_models_and_exponential_cdf_are_removed():
    """The step-function modules and ``ExponentialCDF`` no longer exist.

    The author removed ``heaviside`` (``HeavySide``), ``composite`` (the three
    Gaussian-with-step models) and ``exponentials.ExponentialCDF``.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.fitfunctions import exponentials

    for module in ("heaviside", "composite"):
        assert importlib.util.find_spec(f"{ff.__name__}.{module}") is None, module
    assert not hasattr(exponentials, "ExponentialCDF")


@pytest.mark.parametrize("name", ff.__all__)
def test_every_name_in_the_package_all_resolves(name):
    """Each name in ``fitfunctions.__all__`` is a submodule or a package object.

    ON FAILURE: the code is wrong; ``fitfunctions.__all__`` names something
    the package no longer defines.
    """
    if not hasattr(ff, name):
        importlib.import_module(f"{ff.__name__}.{name}")
    assert hasattr(ff, name), name


def _generic_start(name, n):
    """The feasible start scipy's ``curve_fit`` picks for the class's bounds.

    Ones for an unbounded parameter, and ``ub - 1`` for one bounded only
    above (scipy.optimize._minpack_py._initialize_feasible). Only
    PowerLawOffCenter bounds a parameter here: ``x0`` lies below the smallest
    used x, the largest float below 2.
    """
    start = np.ones(n)
    if name == "PowerLawOffCenter":
        start[CLASSES[name](X, Y).argnames.index("x0")] = (
            np.nextafter(X.min(), -np.inf) - 1.0
        )
    return start


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_explicit_p0_none_fits_from_the_generic_start(name):
    """``make_fit(p0=None)`` ends exactly as a fit from the generic start.

    The author decided an explicit ``p0=None`` means the generic start,
    whatever the class's own guess. Same start and same solver give the same
    exception or the same popt.

    ON FAILURE: the code is wrong.
    """
    explicit_none = _build(name)
    generic = _build(name)
    n = len(generic.argnames)

    got = attempt_fit(explicit_none, p0=None)
    expected = attempt_fit(generic, p0=_generic_start(name, n))
    assert type(got) is type(expected), (got, expected)
    assert str(got) == str(expected), (got, expected)
    if got is None:
        assert explicit_none.popt == generic.popt


def test_explicit_p0_none_does_not_read_the_class_guess():
    """HingeMax, whose guess raises on these data, fits from ``p0=None``.

    A flat plateau gives no estimate, so HingeMax's ``p0`` raises
    NotImplementedError; the generic start must not consult it.

    ON FAILURE: the code is wrong.
    """
    x = np.array([0.0, 1, 2, 3, 4, 5])
    fit = HingeMax(x, np.array([0.0, 1, 2, 2, 2, 2]), guess_xh=2.5)
    with pytest.raises(NotImplementedError):
        fit.p0
    got = attempt_fit(fit, p0=None)
    assert not isinstance(got, NotImplementedError), got


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_base_class_keywords_reach_the_observation_selection(name):
    """Every class passes ``xmin`` and ``xmax`` on to the base class.

    The used x are exactly the raw x in [3, 8], from the chosen grid.

    ON FAILURE: the code is wrong.
    """
    fit = _build(name, xmin=3.0, xmax=8.0)
    np.testing.assert_array_equal(fit.observations.used.x, X[(X >= 3.0) & (X <= 8.0)])
