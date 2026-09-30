# Spent-When: PERMANENT(solarwindpy stops promising public import paths)
# Supersedes: none
"""Every promised public name imports.

Two independent routes say which names are public. The first is the code:
``solarwindpy.__all__`` and the ``__all__`` of each public subpackage, found by
walking the package. The second is the documentation: the autosummary entries
in ``docs/source/api_reference.rst``. Neither list is typed here, so adding or
removing a public name never requires editing this file.
"""

import importlib
import inspect
import pkgutil
import re
from pathlib import Path

import pytest

import solarwindpy

API_REFERENCE = (
    Path(__file__).resolve().parents[1] / "docs" / "source" / "api_reference.rst"
)


def _public_packages():
    """Names of solarwindpy and every subpackage without a leading underscore."""
    found = [solarwindpy.__name__]
    for info in pkgutil.walk_packages(solarwindpy.__path__, "solarwindpy."):
        parts = info.name.split(".")
        if info.ispkg and not any(part.startswith("_") for part in parts):
            found.append(info.name)
    return found


def _promised_pairs():
    """(package, name) for each name in each public package's ``__all__``."""
    pairs = []
    for package in _public_packages():
        module = importlib.import_module(package)
        pairs.extend((package, name) for name in getattr(module, "__all__", ()))
    return pairs


def _documented_names():
    """Dotted names listed under every autosummary directive in the API page."""
    names = []
    in_block = False
    for line in API_REFERENCE.read_text().splitlines():
        if line.startswith(".. autosummary::"):
            in_block = True
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if line and not line[0].isspace():
            in_block = False
        elif stripped and not stripped.startswith(":"):
            names.append(stripped.lstrip("~"))
    return names


def _import_statement(dotted):
    """``from <parent> import <leaf>`` for a dotted name."""
    parent, _, leaf = dotted.rpartition(".")
    return f"from {parent} import {leaf}"


PROMISED = _promised_pairs()
DOCUMENTED = _documented_names()


@pytest.mark.parametrize(
    ("module", "name"), PROMISED, ids=[f"{m}:{n}" for m, n in PROMISED]
)
def test_every_name_in_a_public_all_imports(module, name):
    """``from <module> import <name>`` works for every ``__all__`` entry.

    ON FAILURE: the code is wrong; <module>.__all__ promises a name the
    package does not provide.
    """
    namespace = {}
    exec(f"from {module} import {name}", namespace)
    assert name in namespace


def test_discovery_reaches_every_subpackage_the_top_level_exports():
    """The walk finds each subpackage in ``solarwindpy.__all__`` and some names.

    Guards the parametrized test above against passing vacuously.

    ON FAILURE: the discovery no longer reaches the package; fix the test.
    """
    exported_packages = {
        obj.__name__
        for obj in (getattr(solarwindpy, n) for n in solarwindpy.__all__)
        if inspect.ismodule(obj) and hasattr(obj, "__path__")
    }
    assert exported_packages
    assert exported_packages <= set(_public_packages())
    assert len(PROMISED) > 0


@pytest.mark.parametrize("dotted", DOCUMENTED)
def test_every_documented_api_name_imports(dotted):
    """Each autosummary entry in ``api_reference.rst`` imports.

    ON FAILURE: the code or the docs are wrong; api_reference.rst documents
    a name the package does not provide.
    """
    namespace = {}
    exec(_import_statement(dotted), namespace)
    assert dotted.rpartition(".")[2] in namespace


def test_docs_parse_finds_the_documented_api():
    """The rst parse yields entries, each under the solarwindpy namespace.

    Guards the documented-name test above against passing vacuously.

    ON FAILURE: the api_reference.rst layout changed; fix _documented_names.
    """
    assert DOCUMENTED
    assert all(re.fullmatch(r"solarwindpy(\.\w+)+", d) for d in DOCUMENTED)
