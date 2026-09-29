# Spent-When: PERMANENT(the available() listing functions are removed from solarwindpy)
# Supersedes: none
"""Contract tests for the ``available()`` listing functions.

``solarwindpy.fitfunctions.available`` prints every fit function in the
package with its formula. These tests state what the listing promises, and
none of them names a particular fit function, so adding or removing a fit
function never requires editing this file.
"""

import importlib
import inspect
import pkgutil

import solarwindpy.fitfunctions as ff
from solarwindpy.fitfunctions.core import FitFunction


class _FitDefinedOutsideThePackage(FitFunction):
    """A concrete subclass that lives in this test module, not the package."""

    @property
    def function(self):
        return lambda x, a: a * x

    @property
    def p0(self):
        return [1.0]

    @property
    def TeX_function(self):
        return r"f(x)=a x"


def _fit_functions_found_by_scanning_modules():
    """Concrete FitFunction classes defined in the package's module files.

    This finds classes by importing every module under
    ``solarwindpy.fitfunctions`` and reading what each defines, a different
    route from the subclass-tree walk that ``available`` uses.
    """
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


def _printed_rows(capsys):
    """Run ``available`` and map each listed name to its printed row."""
    ff.available()
    lines = capsys.readouterr().out.splitlines()[2:]
    return {line.split()[0]: line for line in lines if line.strip()}


def test_available_lists_exactly_the_fit_functions_defined_in_the_package(capsys):
    """The listing and an independent scan of the module files agree.

    ON FAILURE: the code is wrong; available() missed or invented a fit
    function relative to the classes the modules define.
    """
    assert set(_printed_rows(capsys)) == set(_fit_functions_found_by_scanning_modules())


def test_each_row_shows_that_class_s_own_formula(capsys):
    """Every line of each class's LaTeX formula appears in that class's row.

    ON FAILURE: the code is wrong; a row lost or mixed up its formula.
    """
    rows = _printed_rows(capsys)
    for name, cls in _fit_functions_found_by_scanning_modules().items():
        for part in cls.TeX_function.fget(None).splitlines():
            assert part in rows[name], name


def test_every_fit_function_formula_reads_without_data(capsys):
    """No row shows the needs-a-fitted-instance note.

    ON FAILURE: a fit function's TeX_function now depends on fitted values;
    make that formula readable from the class, or accept the note and update
    this test.
    """
    assert not any(
        "needs a fitted instance" in row for row in _printed_rows(capsys).values()
    )


def test_available_ignores_subclasses_defined_elsewhere(capsys):
    """A FitFunction subclass defined outside the package is not listed.

    ON FAILURE: the code is wrong; discovery must stay inside
    solarwindpy.fitfunctions.
    """
    assert _FitDefinedOutsideThePackage.__name__ not in _printed_rows(capsys)


def test_labels_star_import_brings_available():
    """``from solarwindpy.plotting.labels import *`` succeeds and brings ``available``.

    Every name in a module's ``__all__`` must exist; a missing one makes the
    star import raise AttributeError.

    ON FAILURE: the code is wrong; labels.__all__ names something undefined.
    """
    namespace = {}
    exec("from solarwindpy.plotting.labels import *", namespace)
    assert callable(namespace["available"])
