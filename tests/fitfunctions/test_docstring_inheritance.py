# Spent-When: PERMANENT(solarwindpy stops inheriting fit-function docstrings from FitFunction)
# Supersedes: none
"""Contract tests for docstring inheritance in the fit functions.

A fit function that does not document a method itself shows its parent's
help text at runtime, because ``solarwindpy`` switches on docstring-inheritance
before importing its subpackages.
"""

import os
import subprocess
import sys

from solarwindpy.fitfunctions.core import FitFunction
from solarwindpy.fitfunctions.heaviside import HeavySide


def test_undocumented_method_shows_parent_help_text():
    """``HeavySide.__init__`` documents nothing itself and shows FitFunction's text.

    ON FAILURE: ``help()`` on a fit function's method loses its description;
    check that ``solarwindpy/__init__.py`` switches docstring-inheritance on
    before importing ``fitfunctions``.
    """
    parent_summary = FitFunction.__init__.__doc__.strip().splitlines()[0]
    assert HeavySide.__init__.__doc__ is not None
    assert parent_summary in HeavySide.__init__.__doc__


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
