# Spent-When: PERMANENT(solarwindpy stops following PyHC standard 8 on docstrings)
# Supersedes: none
"""Public docstrings meet PyHC standard 8: purpose, inputs, outputs, examples.

PyHC standard 8 says docstrings "must describe the code's purpose, describe all
inputs and outputs, and provide examples". The checks run on the docstrings
Python reports at runtime (``inspect.getdoc``), so a docstring that
``docstring-inheritance`` merges in from a parent counts.

Public objects come from walking the package: every module whose dotted name
has no part starting with an underscore, every class and function it defines
whose name has no leading underscore, and every such class's own methods and
properties. Examples are required only of the entry points a user calls
directly, listed in ``ENTRY_POINTS``.
"""

import ast
import importlib
import inspect
import pkgutil
import re

import pytest

import solarwindpy

# The public classes and functions a user calls directly; each shows its use
# in an ``Examples`` section run by ``pytest --doctest-modules src/solarwindpy``.
ENTRY_POINTS = [
    "solarwindpy.core.abundances.ReferenceAbundances",
    "solarwindpy.core.alfvenic_turbulence.AlfvenicTurbulence",
    "solarwindpy.core.ions.Ion",
    "solarwindpy.core.plasma.Plasma",
    "solarwindpy.core.spacecraft.Spacecraft",
    "solarwindpy.core.tensor.Tensor",
    "solarwindpy.core.vector.Vector",
    "solarwindpy.examples.load_plasma",
    "solarwindpy.fitfunctions.available",
    "solarwindpy.fitfunctions.exponentials.Exponential",
    "solarwindpy.fitfunctions.gaussians.Gaussian",
    "solarwindpy.fitfunctions.hinge.HingeSaturation",
    "solarwindpy.fitfunctions.lines.Line",
    "solarwindpy.fitfunctions.power_laws.PowerLaw",
    "solarwindpy.fitfunctions.trend_fits.TrendFit",
    "solarwindpy.instabilities.beta_ani.BetaRPlot",
    "solarwindpy.instabilities.verscharen2016.beta_ani_inst",
    "solarwindpy.instabilities.verscharen2016.StabilityCondition",
    "solarwindpy.instabilities.verscharen2016.StabilityContours",
    "solarwindpy.plotting.binned.BinnedData",
    "solarwindpy.plotting.hist1d.Hist1D",
    "solarwindpy.plotting.hist2d.Hist2D",
    "solarwindpy.plotting.labels.available",
    "solarwindpy.plotting.labels.base.TeXlabel",
    "solarwindpy.plotting.scatter.Scatter",
    "solarwindpy.plotting.spiral.SpiralPlot2D",
    "solarwindpy.solar_activity.icme.icmecat.ICMECAT",
    "solarwindpy.solar_activity.sunspot_number.sidc.SIDCLoader",
    "solarwindpy.solar_activity.sunspot_number.sidc.SSNExtrema",
    "solarwindpy.tools.normal_parameters",
    "solarwindpy.tools.swap_protons",
]

_SECTION = r"^{}\s*\n-{{3,}}\s*$"
_PARAMETERS = re.compile(_SECTION.format("Parameters"), re.M)
_RETURNS = re.compile(_SECTION.format("(Returns|Yields)"), re.M)
_EXAMPLES = re.compile(_SECTION.format("Examples"), re.M)
_ANY_SECTION = re.compile(r"^\S[^\n]*\n-{3,}\s*$", re.M)
# A Parameters entry: ``name : type`` or ``x, y : type``, or a bare ``name``.
_ENTRY = re.compile(r"^(\*{0,2}\w+(?:\s*,\s*\*{0,2}\w+)*)\s*(?::|$)")


def _public_modules():
    """Every module of the package with no underscore-led part in its name."""
    walked = pkgutil.walk_packages(solarwindpy.__path__, "solarwindpy.")
    names = ["solarwindpy"] + [info.name for info in walked]
    return [
        importlib.import_module(name)
        for name in names
        if not any(part.startswith("_") for part in name.split("."))
    ]


def _public_objects():
    """``(qualified name, object, callable or None)`` for every public object.

    The callable is the function whose signature and source the checks read;
    it is None for classes and properties.
    """
    seen = set()
    for module in _public_modules():
        for name, obj in vars(module).items():
            if name.startswith("_") or id(obj) in seen:
                continue
            if getattr(obj, "__module__", None) != module.__name__:
                continue
            seen.add(id(obj))
            qualname = f"{module.__name__}.{name}"
            if inspect.isfunction(obj):
                yield qualname, obj, obj
            elif inspect.isclass(obj):
                yield qualname, obj, None
                for attr, raw in vars(obj).items():
                    if attr.startswith("_"):
                        continue
                    if isinstance(raw, property):
                        yield f"{qualname}.{attr}", raw, None
                    elif inspect.isfunction(raw) or isinstance(
                        raw, (staticmethod, classmethod)
                    ):
                        method = getattr(obj, attr)
                        yield f"{qualname}.{attr}", method, method


def _arguments(func):
    """The names ``func`` takes, other than ``self`` and ``cls``."""
    return [
        name
        for name in inspect.signature(func).parameters
        if name not in ("self", "cls")
    ]


def _section(doc, header):
    """The body of the numpydoc section ``header`` matches, or None."""
    match = header.search(doc)
    if match is None:
        return None
    rest = doc[match.end() :]
    following = _ANY_SECTION.search(rest)
    return rest if following is None else rest[: following.start()]


def _documented_parameters(body):
    """The argument names a Parameters section body lists."""
    names = set()
    for line in body.splitlines():
        if not line or line[0].isspace():
            continue
        entry = _ENTRY.match(line)
        if entry:
            names.update(n.strip().lstrip("*") for n in entry.group(1).split(","))
    return names


def _function_node(func):
    """The AST node of ``func``'s definition in its source file."""
    func = inspect.unwrap(func)
    tree = ast.parse(inspect.getsource(inspect.getmodule(func)))
    first = func.__code__.co_firstlineno
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = (
                node.decorator_list[0].lineno if node.decorator_list else node.lineno
            )
            if start == first:
                return node
    raise LookupError(f"no definition of {func.__qualname__} at line {first}")


def _returns_a_value(func):
    """``func``'s own body has a ``return`` of something other than None, or a yield."""
    root = _function_node(func)
    found = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            if node is root:
                self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, node):
            pass

        def visit_Return(self, node):
            value = node.value
            if value is not None and not (
                isinstance(value, ast.Constant) and value.value is None
            ):
                found.append(node)

        def visit_Yield(self, node):
            found.append(node)

        visit_YieldFrom = visit_Yield

    Visitor().visit(root)
    return bool(found)


def test_public_objects_are_found():
    """The walk finds public classes, methods, properties and functions.

    ON FAILURE: the fixture no longer finds the public objects; fix the fixture
    (``_public_objects``).
    """
    names = {name for name, _, _ in _public_objects()}
    assert "solarwindpy.core.plasma.Plasma" in names
    assert "solarwindpy.core.plasma.Plasma.set_data" in names
    assert "solarwindpy.core.plasma.Plasma.species" in names
    assert "solarwindpy.examples.load_plasma" in names


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="14 public methods and properties have no docstring; remove this marker when the docstring work lands",
)
def test_every_public_object_has_a_docstring():
    """Every public class, method, property and function has a docstring.

    ON FAILURE: the code is wrong; write a docstring for each listed object.
    """
    missing = [name for name, obj, _ in _public_objects() if not inspect.getdoc(obj)]
    assert not missing, missing


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="about 100 public methods do not name every argument under Parameters; remove this marker when the docstring work lands",
)
def test_every_public_argument_is_in_a_parameters_section():
    """Every argument of a public method or function is named under Parameters.

    ``self`` and ``cls`` are exempt; ``*args`` and ``**kwargs`` are named
    with or without their stars.

    ON FAILURE: the code is wrong; document each listed argument.
    """
    missing = []
    for name, obj, func in _public_objects():
        if func is None:
            continue
        arguments = _arguments(func)
        if not arguments:
            continue
        body = _section(inspect.getdoc(obj) or "", _PARAMETERS)
        documented = set() if body is None else _documented_parameters(body)
        undocumented = [a for a in arguments if a not in documented]
        if undocumented:
            missing.append((name, undocumented))
    assert not missing, missing


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="31 public methods return a value without a Returns section; remove this marker when the docstring work lands",
)
def test_every_public_function_returning_a_value_has_a_returns_section():
    """A public method or function whose body returns a value has Returns.

    A body returns a value when it holds a ``return`` of something other
    than None, or a ``yield``.

    ON FAILURE: the code is wrong; add a Returns section to each listed object.
    """
    missing = [
        name
        for name, obj, func in _public_objects()
        if func is not None
        and _returns_a_value(func)
        and not _RETURNS.search(inspect.getdoc(obj) or "")
    ]
    assert not missing, missing


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="entry points in ENTRY_POINTS lack an Examples section; remove this marker when the docstring work lands",
)
def test_every_entry_point_has_an_examples_section():
    """Every class and function in ENTRY_POINTS has an Examples section.

    ON FAILURE: the code is wrong; add an Examples section to each listed
    entry point, unless the author removes it from ENTRY_POINTS.
    """
    missing = []
    for qualname in ENTRY_POINTS:
        module_name, name = qualname.rsplit(".", 1)
        obj = getattr(importlib.import_module(module_name), name)
        if not _EXAMPLES.search(inspect.getdoc(obj) or ""):
            missing.append(qualname)
    assert not missing, missing
