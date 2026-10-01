# Spent-When: PERMANENT(solarwindpy stops promising one import path per public object)
# Supersedes: none
"""Every public object has exactly one import path: the module that defines it.

An object is public when its name is in exactly one module's ``__all__`` and
that module defines it. A package's ``__all__`` lists its submodules and the
objects the package file itself defines; it re-exports nothing. The one
exception is the ``solarwindpy.pp`` nickname for ``solarwindpy.plotting``.

Expectations come from scanning, never from a typed list: the modules from
walking the package, the public names from each ``__all__``, and the
documented names from the autosummary entries in
``docs/source/api_reference.rst``.
"""

import ast
import importlib
import inspect
import pkgutil
import re
from pathlib import Path

import pytest

import solarwindpy

DOCS_SOURCE = Path(__file__).resolve().parents[1] / "docs" / "source"
API_REFERENCE = DOCS_SOURCE / "api_reference.rst"

# The one temporary nickname the ruling allows, pending migration of the
# author's analysis code to ``solarwindpy.plotting``.
NICKNAMES = {"pp": "solarwindpy.plotting"}


def _module_names():
    """``solarwindpy`` and every module and package below it."""
    walked = pkgutil.walk_packages(solarwindpy.__path__, solarwindpy.__name__ + ".")
    return [solarwindpy.__name__] + [info.name for info in walked]


def _is_package(module):
    """``module`` is a package (it has a ``__path__``)."""
    return hasattr(module, "__path__")


def _assigned_names(module):
    """Names bound by a top-level assignment in ``module``'s source."""
    names = set()
    for node in ast.parse(inspect.getsource(module)).body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
        names.update(t.id for t in targets if isinstance(t, ast.Name))
    return names


def _is_defined_in(obj, name, module):
    """``obj``, bound to ``name`` on ``module``, was defined by ``module``."""
    if inspect.isclass(obj) or inspect.isroutine(obj):
        return obj.__module__ == module.__name__ and obj.__name__ == name
    # A constant or an instance carries no reliable __module__ of its own;
    # its definition is the top-level assignment that binds it.
    return name in _assigned_names(module)


def _is_own_submodule(obj, name, module):
    """``obj`` is the submodule ``<module>.<name>`` of package ``module``."""
    return (
        inspect.ismodule(obj)
        and _is_package(module)
        and obj.__name__ == f"{module.__name__}.{name}"
    )


def _autosummary_entries():
    """``(dotted name, recursive)`` for each autosummary entry in the API page."""
    entries = []
    in_block = recursive = False
    for line in API_REFERENCE.read_text().splitlines():
        if line.startswith(".. autosummary::"):
            in_block, recursive = True, False
            continue
        if not in_block:
            continue
        stripped = line.strip()
        if line and not line[0].isspace():
            in_block = False
        elif stripped == ":recursive:":
            recursive = True
        elif stripped and not stripped.startswith(":"):
            entries.append((stripped.lstrip("~"), recursive))
    return entries


def _documented_names():
    """Dotted names listed under every autosummary directive in the API page."""
    return [name for name, _ in _autosummary_entries()]


def _sphinx_lists(module, name):
    """Autosummary's module template lists ``<module>.<name>`` on its page.

    Mirrors ``sphinx.ext.autosummary.generate`` under this repo's conf.py:
    classes, functions and exceptions are listed when the module defines them
    and the name is not private; any other attribute only when Sphinx finds a
    doc comment for it (``#:`` before the assignment, or a string after it).
    """
    from sphinx.pycode import ModuleAnalyzer

    if name.startswith("_"):
        return False
    obj = getattr(module, name)
    if inspect.isclass(obj) or inspect.isroutine(obj):
        return obj.__module__ == module.__name__
    attr_docs = ModuleAnalyzer.for_module(module.__name__).find_attr_docs()
    return ("", name) in attr_docs


MODULES = _module_names()
PACKAGES = [m for m in MODULES if _is_package(importlib.import_module(m))]
PUBLIC = [
    (module, name)
    for module in MODULES
    for name in getattr(importlib.import_module(module), "__all__", ())
]
DOCUMENTED = _documented_names()


def test_the_scan_reaches_every_subpackage_and_finds_public_objects():
    """The walk finds every subpackage, and the ``__all__`` lists name objects.

    Guards every test below against passing vacuously.

    ON FAILURE: the discovery no longer reaches the package; fix the test.
    """
    assert {f"solarwindpy.{n}" for n in solarwindpy.__all__} <= set(PACKAGES)
    objects = [
        getattr(importlib.import_module(m), n)
        for m, n in PUBLIC
        if not inspect.ismodule(getattr(importlib.import_module(m), n))
    ]
    assert len(objects) > len(MODULES)
    assert any(inspect.isclass(obj) for obj in objects)
    assert any(inspect.isfunction(obj) for obj in objects)


@pytest.mark.parametrize("module", MODULES)
def test_every_module_declares_all(module):
    """Each module states its public names in ``__all__``.

    ON FAILURE: the code is wrong; give <module> an ``__all__`` listing the
    objects it defines and intends public.
    """
    assert hasattr(importlib.import_module(module), "__all__")


@pytest.mark.parametrize(
    ("module", "name"), PUBLIC, ids=[f"{m}:{n}" for m, n in PUBLIC]
)
def test_every_public_name_is_defined_where_it_is_listed(module, name):
    """``from <module> import <name>`` works and <module> defines <name>.

    A package may also list its own submodules.

    ON FAILURE: the code is wrong; <module>.__all__ lists a name defined
    elsewhere (a re-export) or not at all. Import it from its defining module.
    """
    namespace = {}
    exec(f"from {module} import {name}", namespace)
    obj = namespace[name]
    mod = importlib.import_module(module)
    assert _is_own_submodule(obj, name, mod) or _is_defined_in(obj, name, mod)


def test_no_public_object_is_listed_twice():
    """No object, compared by identity, is in two ``__all__`` entries.

    Plain strings and numbers are skipped: the interpreter may share one
    object between unrelated equal constants.

    ON FAILURE: the code is wrong; an object is public at two paths. Remove
    every listing except the one in its defining module.
    """
    seen = {}
    duplicates = []
    for module, name in PUBLIC:
        obj = getattr(importlib.import_module(module), name)
        if isinstance(obj, (str, bytes, int, float)):
            continue
        path = f"{module}.{name}"
        if id(obj) in seen:
            duplicates.append((seen[id(obj)], path))
        seen.setdefault(id(obj), path)
    assert not duplicates, duplicates


@pytest.mark.parametrize("package", PACKAGES)
def test_no_package_binds_a_solarwindpy_object_it_does_not_define(package):
    """A package namespace holds its own submodules and objects, nothing else.

    Catches a re-export even when it is left out of ``__all__``: every public
    attribute that comes from solarwindpy is the package's own submodule
    under its real name, or an object the package file defines. The
    ``solarwindpy.pp`` nickname is the one exception.

    ON FAILURE: the code is wrong; <package> re-exports or renames an object.
    Import it from its defining module instead.
    """
    mod = importlib.import_module(package)
    offenders = []
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        if inspect.ismodule(obj):
            if not obj.__name__.startswith("solarwindpy"):
                continue
            if package == "solarwindpy" and NICKNAMES.get(name) == obj.__name__:
                continue
            if not _is_own_submodule(obj, name, mod):
                offenders.append(name)
        elif str(getattr(obj, "__module__", "")).startswith("solarwindpy"):
            if not _is_defined_in(obj, name, mod):
                offenders.append(name)
    assert not offenders, offenders


def test_top_level_exposes_only_subpackages_and_the_pp_nickname():
    """``solarwindpy`` exposes its subpackages, ``pp``, and dunder metadata.

    ON FAILURE: the code is wrong; solarwindpy/__init__.py exposes another
    public name. Give helper imports a leading underscore and import objects
    from their defining modules.
    """
    public = {n for n in vars(solarwindpy) if not n.startswith("_")}
    subpackages = {
        n
        for n in public
        if _is_own_submodule(getattr(solarwindpy, n), n, solarwindpy)
        and _is_package(getattr(solarwindpy, n))
    }
    assert public - subpackages == set(NICKNAMES)
    assert set(solarwindpy.__all__) == subpackages
    for nickname, target in NICKNAMES.items():
        assert getattr(solarwindpy, nickname).__name__ == target


@pytest.mark.parametrize("dotted", DOCUMENTED)
def test_every_documented_name_is_documented_at_its_one_path(dotted):
    """Each autosummary entry imports, at the path that defines it.

    ON FAILURE: the docs or the code are wrong; api_reference.rst documents
    a name the package does not provide, or documents it at a path other
    than its defining module.
    """
    parent, _, leaf = dotted.rpartition(".")
    namespace = {}
    exec(f"from {parent} import {leaf}", namespace)
    obj = namespace[leaf]
    parent_mod = importlib.import_module(parent)
    if inspect.ismodule(obj):
        assert _is_own_submodule(obj, leaf, parent_mod)
    else:
        assert leaf in parent_mod.__all__
        assert _is_defined_in(obj, leaf, parent_mod)


def test_every_public_object_is_documented_on_the_api_reference():
    """Every name in any ``__all__`` is on a page the docs build generates.

    The documented set is derived without building Sphinx. Each top-level
    subpackage has a ``:recursive:`` autosummary entry on the API page;
    recursion reaches every module whose path below that entry has no
    private component; and the module template lists the object (see
    ``_sphinx_lists``). conf.py must not change what autosummary generates:
    no event hooks (``setup``), no mocked imports, no ``exclude_patterns``.

    ON FAILURE: the docs or the code are wrong; add the subpackage's
    recursive entry to api_reference.rst, give the attribute a ``#:`` doc
    comment, or make the module path public. If conf.py gained a setting
    named in the assertion, extend this test to model it.
    """
    conf = set()
    for node in ast.parse((DOCS_SOURCE / "conf.py").read_text()).body:
        if isinstance(node, ast.FunctionDef):
            conf.add(node.name)
        elif isinstance(node, ast.Assign):
            conf.update(t.id for t in node.targets if isinstance(t, ast.Name))
    unmodeled = {
        "setup",
        "autodoc_mock_imports",
        "autosummary_mock_imports",
        "exclude_patterns",
        "autosummary_ignore_module_all",
    }
    assert not conf & unmodeled, conf & unmodeled

    roots = {name for name, recursive in _autosummary_entries() if recursive}
    subpackages = {f"solarwindpy.{n}" for n in solarwindpy.__all__}
    assert subpackages, "no subpackages found; the scan is broken"
    assert subpackages <= roots, sorted(subpackages - roots)

    def reachable(module):
        for root in roots:
            if module == root or module.startswith(root + "."):
                below = module.removeprefix(root).split(".")[1:]
                return not any(part.startswith("_") for part in below)
        return False

    checked = []
    missing = []
    for module, name in PUBLIC:
        mod = importlib.import_module(module)
        if inspect.ismodule(getattr(mod, name)):
            continue
        checked.append(f"{module}.{name}")
        if not (reachable(module) and _sphinx_lists(mod, name)):
            missing.append(f"{module}.{name}")
    assert len(checked) > len(MODULES), "too few public objects checked"
    assert not missing, missing


def test_docs_parse_finds_the_documented_api():
    """The rst parse yields entries, each under the solarwindpy namespace.

    Guards the documented-name test above against passing vacuously.

    ON FAILURE: the api_reference.rst layout changed; fix _documented_names.
    """
    assert DOCUMENTED
    assert all(re.fullmatch(r"solarwindpy(\.\w+)+", d) for d in DOCUMENTED)
