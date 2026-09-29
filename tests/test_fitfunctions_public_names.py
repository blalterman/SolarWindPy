# Spent-When: PERMANENT(solarwindpy.fitfunctions stops offering its fit functions at package level)
# Supersedes: none
"""Contract tests for the public names of ``solarwindpy.fitfunctions``.

Every fit function a user can build is reachable as
``solarwindpy.fitfunctions.<Name>`` and declared in the package's
``__all__``. The modules that define them are implementation. No test here
names a particular fit function, so adding one needs no test edit.
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


def test_every_fit_function_is_reachable_at_package_level():
    """Each fit function the modules define is ``ff.<Name>``, the same class.

    ON FAILURE: the code is wrong; a fit function is missing from, or
    shadowed in, solarwindpy/fitfunctions/__init__.py.
    """
    for name, cls in _fit_functions_found_by_scanning_modules().items():
        assert getattr(ff, name, None) is cls, name


def test_every_fit_function_is_declared_public():
    """Each fit function the modules define is listed in ``ff.__all__``.

    ON FAILURE: the code is wrong; add the new fit function to
    solarwindpy.fitfunctions.__all__.
    """
    missing = set(_fit_functions_found_by_scanning_modules()) - set(ff.__all__)
    assert not missing, sorted(missing)


def test_every_public_name_exists():
    """``from solarwindpy.fitfunctions import *`` succeeds and binds every name.

    ON FAILURE: the code is wrong; __all__ names something undefined.
    """
    namespace = {}
    exec("from solarwindpy.fitfunctions import *", namespace)
    assert set(ff.__all__) <= set(namespace)


def test_public_names_are_listed_once():
    """No name appears twice in ``ff.__all__``.

    ON FAILURE: the code is wrong; remove the duplicate entry.
    """
    assert len(ff.__all__) == len(set(ff.__all__))
