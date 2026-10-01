# Spent-When: PERMANENT(solarwindpy.fitfunctions stops declaring each fit function public in its module)
# Supersedes: none
"""Contract tests for the public names of ``solarwindpy.fitfunctions``.

Every fit function a user can build has one import path, the module that
defines it, and is declared in that module's ``__all__``. The package itself
re-exports none of them. No test here names a particular fit function, so
adding one needs no test edit.
"""

import importlib
import inspect
import pkgutil

import solarwindpy.fitfunctions as ff
from solarwindpy.fitfunctions.core import FitFunction


def _fit_functions_found_by_scanning_modules():
    """Concrete FitFunction classes defined in the package's module files."""
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


def test_scan_finds_fit_functions():
    """The module scan finds at least one fit function.

    Guards the tests below against passing vacuously.

    ON FAILURE: the scan no longer reaches the fit functions; fix the test.
    """
    assert _fit_functions_found_by_scanning_modules()


def test_every_fit_function_is_declared_public_in_its_module():
    """Each fit function is listed in its defining module's ``__all__``.

    ON FAILURE: the code is wrong; add the new fit function to the
    ``__all__`` of the module that defines it.
    """
    missing = [
        f"{cls.__module__}.{name}"
        for name, cls in _fit_functions_found_by_scanning_modules().items()
        if name not in importlib.import_module(cls.__module__).__all__
    ]
    assert not missing, missing


def test_no_fit_function_is_reexported_by_the_package():
    """``solarwindpy.fitfunctions`` binds no fit function at package level.

    ON FAILURE: the code is wrong; import the fit function from its module
    instead of re-exporting it in solarwindpy/fitfunctions/__init__.py.
    """
    reexported = [
        name for name in _fit_functions_found_by_scanning_modules() if hasattr(ff, name)
    ]
    assert not reexported, reexported
