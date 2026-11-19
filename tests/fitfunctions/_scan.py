# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The test suite's own discovery of the concrete fit functions.

``fit_functions_found_by_scanning_modules`` imports every module under
``solarwindpy.fitfunctions`` and reads what each defines. The package's
``_fit_function_classes`` walks the ``FitFunction`` subclass tree instead;
the tests keep the two routes separate so each checks the other.
"""

import importlib
import inspect
import pkgutil

import solarwindpy.fitfunctions as ff
from solarwindpy.fitfunctions.core import FitFunction


def fit_functions_found_by_scanning_modules():
    """Map the name of each concrete FitFunction a package module defines to its class."""
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
