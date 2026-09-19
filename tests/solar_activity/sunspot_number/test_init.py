#!/usr/bin/env python
"""Test the sunspot_number package's import surface.

``solarwindpy/solar_activity/sunspot_number/__init__.py`` does one thing:
``from . import sidc``. That makes the package's contract small and checkable
-- the module is importable, ``sidc`` is bound on it, the SIDC classes are
reachable through it, and nothing else is exported.

REMOVED, deliberately
---------------------
Earlier versions of this module asserted that importing the package took less
than 1.0 second, added fewer than 20 entries to ``sys.modules``, and left
fewer than 20 names on the package. Those bounds had no derivation and no
citation: they measure the machine and the import cache, not the package, and
the first two are order-dependent because a prior test may already have
imported everything. One further test consisted of ``assert True`` under the
name ``test_import_style``, which could not fail. All four are gone rather
than re-pinned to numbers captured from a run.
"""

import importlib
import types

import pytest

import solarwindpy.solar_activity
import solarwindpy.solar_activity.sunspot_number as sunspot_number
from solarwindpy.solar_activity.sunspot_number import sidc

# The classes __init__.py exists to make reachable.
SIDC_CLASS_NAMES = ("SIDC", "SIDC_ID", "SIDCLoader", "SSNExtrema")


def test_package_is_a_package():
    """sunspot_number is an importable package, not a bare module.

    ON FAILURE: the directory lost its __init__.py and the submodule is no
    longer importable by path. The packaging is wrong.
    """
    assert isinstance(sunspot_number, types.ModuleType)
    assert sunspot_number.__name__ == "solarwindpy.solar_activity.sunspot_number"
    assert sunspot_number.__file__.endswith("__init__.py")
    assert str(sunspot_number.__path__[0]).endswith("sunspot_number")


def test_sidc_is_bound_by_the_package_import():
    """Importing the package binds ``sidc`` on it, which is its whole purpose.

    ON FAILURE: ``from . import sidc`` was dropped, and callers relying on
    ``sunspot_number.sidc`` break. The code is wrong.
    """
    assert isinstance(sunspot_number.sidc, types.ModuleType)
    assert sunspot_number.sidc is sidc


@pytest.mark.parametrize("name", SIDC_CLASS_NAMES)
def test_sidc_classes_are_reachable_through_the_package(name):
    """Each SIDC class is reachable through the package, and is a class.

    ON FAILURE: a public class was renamed or removed without a deprecation.
    The code is wrong.
    """
    attribute = getattr(sunspot_number.sidc, name)
    assert isinstance(attribute, type)


def test_public_surface_holds_only_submodules_of_this_package():
    """Nothing public on the package except its own submodules.

    ``__init__.py`` binds ``sidc``; anything else public would be a leaked
    import that becomes API the moment someone depends on it.

    The assertion is deliberately not ``== {"sidc"}``. Python binds every
    imported submodule as an attribute of its parent package, process-wide, so
    an exact-set assertion starts failing the day a second module is added
    under ``sunspot_number/`` and some other test imports it first -- an
    order-dependent failure reported against an untouched ``__init__.py``.
    What is checked instead holds regardless of import order: every public
    name is a module belonging to this package.

    ON FAILURE: a non-module object, or a module from elsewhere, is exposed on
    the package namespace. The code is wrong.
    """
    public = {name for name in dir(sunspot_number) if not name.startswith("_")}

    assert "sidc" in public
    for name in public:
        attribute = getattr(sunspot_number, name)
        assert isinstance(attribute, types.ModuleType), f"{name} is not a module"
        assert attribute.__name__.startswith(f"{sunspot_number.__name__}.")


def test_package_is_reachable_from_its_parent():
    """solar_activity exposes sunspot_number as the same module object.

    ON FAILURE: the documented import path
    ``solarwindpy.solar_activity.sunspot_number`` no longer resolves to the
    package. The code is wrong.
    """
    assert solarwindpy.solar_activity.sunspot_number is sunspot_number


def test_package_docstring_describes_sunspot_numbers():
    """The package carries a docstring that names what it is for.

    ON FAILURE: help() and the generated API docs show an unlabelled package.
    The code is wrong.
    """
    assert sunspot_number.__doc__
    assert "sunspot" in sunspot_number.__doc__.lower()


def test_repeated_import_returns_the_cached_module():
    """Importing twice yields one module object, so module state is shared.

    sidc.py calls ``pd.set_option("mode.chained_assignment", "raise")`` at
    import time; a second, distinct copy of the module would mean two copies
    of every class and failing isinstance checks across them.

    ON FAILURE: the package is being imported under two names. The packaging
    is wrong.
    """
    first = importlib.import_module("solarwindpy.solar_activity.sunspot_number")
    second = importlib.import_module("solarwindpy.solar_activity.sunspot_number")

    assert first is second is sunspot_number


def test_reload_rebinds_the_same_submodule():
    """Reloading the package leaves ``sidc`` bound to the same module.

    Round trip through importlib: a reload that raised or rebound ``sidc`` to
    a fresh copy would break isinstance checks against classes held by
    already-imported callers.

    ON FAILURE: the package cannot be reloaded, which breaks interactive
    workflows and doctest collection. The code is wrong.
    """
    reloaded = importlib.reload(sunspot_number)

    assert reloaded is sunspot_number
    assert reloaded.sidc is sidc


def test_sidc_id_is_usable_through_the_package():
    """The package-level path reaches a working class, not just a name.

    Constructs a real SIDC_ID through the package to show the import chain
    yields something usable rather than a stub.

    ON FAILURE: the re-export is broken in a way a hasattr check would miss.
    The code is wrong.
    """
    identifier = sunspot_number.sidc.SIDC_ID("m")
    assert identifier.key == "m"
    assert identifier.url.endswith("snmtotcsv.php")
