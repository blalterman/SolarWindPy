# Spent-When: PERMANENT(solarwindpy stops inheriting fit-function docstrings from FitFunction)
# Supersedes: none
"""Contract tests for docstring inheritance in the fit functions.

A fit function shows its parent's help text for every section it does not
write itself, at runtime, because ``solarwindpy`` switches on
docstring-inheritance before importing its subpackages. Constructor parameters
are documented in the class docstring, so a fit function's class help lists
every argument its constructor takes.
"""

import inspect
import os
import re
import subprocess
import sys

import pytest

from solarwindpy.fitfunctions import _fit_function_classes
from solarwindpy.fitfunctions.lines import Line

_PARAMETERS_HEADER = re.compile(r"^Parameters\n-{10}$", re.M)
# docstring-inheritance writes this text for an argument no docstring documents.
_MISSING = "The description is missing."


def test_class_help_shows_parent_parameters():
    """``Line`` writes no Parameters section and shows FitFunction's entries.

    ON FAILURE: ``help()`` on a fit function loses its inherited text; check
    that ``solarwindpy/__init__.py`` switches docstring-inheritance on before
    importing ``fitfunctions``.
    """
    assert "xmin : float, optional" in inspect.getdoc(Line)


@pytest.mark.parametrize("cls", _fit_function_classes(), ids=lambda c: c.__name__)
def test_class_help_documents_every_constructor_argument(cls):
    """The merged class docstring has a Parameters section and no stub entries.

    docstring-inheritance checks a class docstring's Parameters against the
    constructor's signature and writes ``The description is missing.`` for an
    argument that nothing documents, so no stub means every argument is
    described.

    ON FAILURE: ``help(cls)`` lists no constructor arguments, or names one
    without describing it. Check that ``FitFunctionMeta`` uses
    ``NumpyDocstringInheritanceInitMeta`` (the plain metaclass deletes a class
    docstring's Parameters section), and that the class docstring documents
    each argument its own ``__init__`` adds, ``**kwargs`` included.
    """
    doc = inspect.getdoc(cls)
    assert _PARAMETERS_HEADER.search(doc), doc
    assert _MISSING not in doc, doc


def test_import_order_that_disables_inheritance_warns():
    """Importing docstring_inheritance first, with its switch unset, draws a warning.

    ON FAILURE: a researcher whose program loads docstring_inheritance before
    solarwindpy gets fit functions without inherited help text and no notice.
    """
    env = {k: v for k, v in os.environ.items() if k != "DOCSTRING_INHERITANCE_ENABLE"}
    code = (
        "import warnings; warnings.simplefilter('always'); "
        "import docstring_inheritance; import solarwindpy"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "docstring inheritance is off" in result.stderr
