# Spent-When: PERMANENT(the available() listing functions are removed from solarwindpy)
# Supersedes: none
"""Contract tests for the ``available()`` listing functions.

``solarwindpy.plotting.labels.available`` prints the label vocabulary and
``solarwindpy.fitfunctions.available`` prints every fit function with its
formula. Both discover what they list from the code, so neither needs a
hand-kept list inside the package.
"""

import pytest

import solarwindpy.fitfunctions as ff
import solarwindpy.plotting.labels as labels
from solarwindpy.fitfunctions.core import FitFunction

# Every concrete FitFunction subclass defined in solarwindpy/fitfunctions,
# read from the class statements in those modules.
EXPECTED_FIT_FUNCTIONS = {
    "Exponential",
    "ExponentialCDF",
    "ExponentialPlusC",
    "Gaussian",
    "GaussianLn",
    "GaussianNormalized",
    "GaussianPlusHeavySide",
    "GaussianTimesHeavySide",
    "GaussianTimesHeavySidePlusHeavySide",
    "HeavySide",
    "HingeAtPoint",
    "HingeMax",
    "HingeMin",
    "HingeSaturation",
    "Line",
    "LineXintercept",
    "Moyal",
    "PowerLaw",
    "PowerLawOffCenter",
    "PowerLawPlusC",
    "Saturation",
    "TwoLine",
}


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


def _listed_names(printed):
    """Return the first column of each table row printed by ``available``."""
    rows = printed.splitlines()[2:]
    return {row.split()[0] for row in rows if row.strip()}


def test_fitfunctions_available_lists_every_fit_function(capsys):
    """``available()`` lists exactly the concrete fit functions in the package.

    ON FAILURE: a fit function was added or removed; update
    EXPECTED_FIT_FUNCTIONS if that was intended, else the discovery is wrong.
    """
    ff.available()
    assert _listed_names(capsys.readouterr().out) == EXPECTED_FIT_FUNCTIONS


@pytest.mark.parametrize(
    "name, formula",
    [
        ("PowerLaw", r"f(x)=A x^b"),
        ("Line", r"f(x)=m \cdot x + b"),
        ("Exponential", r"f(x)=A \cdot e^{-cx}"),
    ],
)
def test_fitfunctions_available_shows_each_formula(capsys, name, formula):
    """Each row carries the fit function's LaTeX formula.

    Expected formulas are the textbook forms: A x^b, m x + b and A e^{-cx}.

    ON FAILURE: the code is wrong, unless the author changed that formula.
    """
    ff.available()
    row = next(
        line
        for line in capsys.readouterr().out.splitlines()
        if line.split() and line.split()[0] == name
    )
    assert formula in row


def test_every_fit_function_formula_reads_without_data(capsys):
    """Every listed fit function shows its formula, not the needs-an-instance note.

    ON FAILURE: a fit function's TeX_function now depends on fitted values;
    make that formula readable from the class, or accept the note and update
    this test.
    """
    ff.available()
    assert "needs a fitted instance" not in capsys.readouterr().out


def test_fitfunctions_available_ignores_subclasses_defined_elsewhere(capsys):
    """A FitFunction subclass defined outside the package is not listed.

    ON FAILURE: the code is wrong; discovery must stay inside
    solarwindpy.fitfunctions.
    """
    ff.available()
    listed = _listed_names(capsys.readouterr().out)
    assert _FitDefinedOutsideThePackage.__name__ not in listed


def test_labels_available_is_exported():
    """``from solarwindpy.plotting.labels import *`` succeeds and brings ``available``.

    Before this change ``__all__`` named ``available_TeXlabel_measurements``,
    which does not exist, so the star import raised AttributeError.

    ON FAILURE: the code is wrong.
    """
    namespace = {}
    exec("from solarwindpy.plotting.labels import *", namespace)
    assert callable(namespace["available"])


def test_labels_available_prints_every_section(capsys):
    """``available()`` prints the label vocabulary under each section heading.

    ON FAILURE: the code is wrong.
    """
    labels.available()
    printed = capsys.readouterr().out
    for section in ("Measurements", "Components", "Species", "Special"):
        assert section in printed


def test_available_labels_is_a_deprecated_alias(capsys):
    """The old name still prints the same text and warns that it is deprecated.

    ON FAILURE: the code is wrong; remove this test only when the
    deprecated alias is deleted.
    """
    labels.available()
    new_output = capsys.readouterr().out
    with pytest.warns(DeprecationWarning, match="use available"):
        labels.available_labels()
    assert capsys.readouterr().out == new_output
