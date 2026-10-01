# Spent-When: PERMANENT(solarwindpy stops handing label objects to matplotlib)
# Supersedes: none
"""Integration contract between solarwindpy labels and matplotlib.

Every plot class hands its label objects to ``Axes.set_xlabel`` and
``Axes.set_ylabel`` (``_add_axis_labels`` in ``solarwindpy/plotting/base.py``),
and matplotlib typesets ``str(label)`` with its mathtext engine: the package
style, ``solarwindpy/plotting/solarwindpy.mplstyle``, leaves ``text.usetex``
off. A label mathtext cannot parse raises at draw time, inside the user's
``savefig``; a label with unbalanced dollar signs is drawn as literal TeX
source instead of math.

The oracle here is matplotlib itself: each label is drawn on a real Agg canvas.
The inputs are enumerated from ``solarwindpy.plotting.labels.available()``, the
public listing of what ``TeXlabel`` knows, so a vocabulary entry added later is
checked without editing this file. Label wording is not asserted;
``tests/plotting/labels`` covers it.
"""

import itertools
import re

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402
from matplotlib import cbook  # noqa: E402

from solarwindpy.plotting import labels  # noqa: E402
from solarwindpy.plotting.labels import (  # noqa: E402
    chemistry,
    composition,
    elemental_abundance,
    special,
)
from solarwindpy.plotting.labels import datetime as dt_labels  # noqa: E402
from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402


def _listing_sections():
    """Parse ``labels.available()`` output into ``{heading: [names]}``.

    ``available()`` prints each heading, a dashed underline, then one or more
    comma-separated lines until a blank line.
    """
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        labels.available()
    text = buffer.getvalue()

    sections = {}
    pattern = re.compile(r"^(\w+)\n-+\n(.*?)(?:\n\s*\n|\Z)", re.M | re.S)
    for heading, body in pattern.findall(text):
        names = [n.strip() for line in body.splitlines() for n in line.split(",")]
        sections[heading] = sorted({n for n in names if n})
    return sections


_LISTING = _listing_sections()


def _listed(heading):
    """Names under ``heading``, or none, so an unparsed listing fails one test.

    A missing heading would otherwise raise ``KeyError`` while pytest collects
    the module; with an empty list the parametrized sweeps collect no cases and
    ``test_available_lists_...`` reports the parser failure.
    """
    return _LISTING.get(heading, [])


def _assert_renders_as_math_axis_label(label):
    """Draw ``label`` as an x-axis label the way ``base.py`` sets it.

    matplotlib typesets a string as mathtext only when
    ``matplotlib.cbook.is_math_text`` says so (an even, nonzero count of
    unescaped ``$``; ``matplotlib.text.Text`` asks it); otherwise it draws the
    characters literally. The draw raises ``ValueError`` when mathtext cannot
    parse the math.
    """
    text = str(label)
    assert cbook.is_math_text(text), f"not typeset as math: {text!r}"

    fig, ax = plt.subplots()
    try:
        ax.set_xlabel(label)
        fig.canvas.draw()
    finally:
        plt.close(fig)


def test_available_lists_measurements_components_species_and_special_labels():
    """The parser finds each ``available()`` section and its documented names.

    ``n``, ``x`` and ``p1`` are the measurement, component and species examples
    of the ``M``/``C``/``S`` data model in the repository's CLAUDE.md, and
    ``Count`` is the histogram label every ``Hist1D``/``Hist2D`` uses. Without
    this check a parser that found nothing would let the sweeps below pass
    with no cases.

    ON FAILURE: the fixture no longer separates the listing into sections;
    fix ``_listing_sections`` for the current ``available()`` layout.
    """
    assert "n" in _listed("Measurements")
    assert "x" in _listed("Components")
    assert "p1" in _listed("Species")
    assert "Count" in _listed("Special")


@pytest.mark.parametrize("measurement", _listed("Measurements"))
def test_every_listed_measurement_renders_as_a_math_axis_label(measurement):
    """``TeXlabel((m, "", ""))`` draws as math for each listed measurement.

    ON FAILURE: the code is wrong; the measurement's TeX or units string is not
    valid mathtext, unless the installed matplotlib dropped a mathtext command
    the label uses.
    """
    _assert_renders_as_math_axis_label(TeXlabel((measurement, "", "")))


@pytest.mark.parametrize("component", _listed("Components"))
def test_every_listed_component_renders_as_a_math_axis_label(component):
    """``TeXlabel(("v", c, "p1"))`` draws as math for each listed component.

    ON FAILURE: the code is wrong; the component's TeX is not valid mathtext
    inside a subscript, unless the installed matplotlib dropped a mathtext
    command the label uses.
    """
    _assert_renders_as_math_axis_label(TeXlabel(("v", component, "p1")))


@pytest.mark.parametrize("species", _listed("Species"))
def test_every_listed_species_renders_as_a_math_axis_label(species):
    """``TeXlabel(("n", "", s))`` draws as math for each listed species.

    ON FAILURE: the code is wrong; the species' TeX is not valid mathtext
    inside a subscript, unless the installed matplotlib dropped a mathtext
    command the label uses.
    """
    _assert_renders_as_math_axis_label(TeXlabel(("n", "", species)))


_N_P1 = ("n", "", "p1")
_N_A = ("n", "", "a")
_V_X_A = ("v", "x", "a")

# Labels whose strings are assembled from more than one table entry, or whose
# class the listing names but ``TeXlabel`` does not build. Each factory is
# called inside the test so a constructor error is reported against its case.
_STRUCTURED_LABELS = {
    "TeXlabel-ratio": lambda: TeXlabel(_N_A, _N_P1),
    "TeXlabel-new-line-for-units": lambda: TeXlabel(_N_P1, new_line_for_units=True),
    "TeXlabel-description": lambda: TeXlabel(_N_P1, description="Protons"),
    **{
        f"TeXlabel-axnorm-{norm}": (lambda norm=norm: TeXlabel(_N_P1, axnorm=norm))
        for norm in ("c", "r", "t", "d")
    },
    **{
        f"Count-{norm}": (lambda norm=norm: special.Count(norm))
        for norm in (None, "c", "r", "t", "d", "rd", "cd")
    },
    "Vsw": lambda: special.Vsw(),
    "CarringtonRotation-short": lambda: special.CarringtonRotation(True),
    "CarringtonRotation-long": lambda: special.CarringtonRotation(False),
    "Power": lambda: special.Power(),
    "Probability": lambda: special.Probability(TeXlabel(_N_P1), "> 5"),
    "CountOther": lambda: special.CountOther(TeXlabel(_N_P1), "> 5"),
    "CountOther-new-line": lambda: special.CountOther(
        TeXlabel(_N_P1), "> 5", new_line_for_units=True
    ),
    "MathFcn": lambda: special.MathFcn("log10", TeXlabel(_N_P1)),
    "MathFcn-dimensional-new-line": lambda: special.MathFcn(
        "log10", TeXlabel(_N_P1), dimensionless=False, new_line_for_units=True
    ),
    "AbsoluteValue": lambda: special.AbsoluteValue(TeXlabel(_V_X_A)),
    "AbsoluteValue-new-line": lambda: special.AbsoluteValue(
        TeXlabel(_V_X_A), new_line_for_units=True
    ),
    **{
        f"Distance2Sun-{units}": (lambda units=units: special.Distance2Sun(units))
        for units in ("rs", "re", "au", "m", "km")
    },
    **{
        f"SSN-{key}": (lambda key=key: special.SSN(key))
        for key in ("M", "M13", "D", "Y", "NM", "NM13", "ND", "NY")
    },
    "ComparisonLabel": lambda: special.ComparisonLabel(
        TeXlabel(_N_A), TeXlabel(_N_P1), "subtract"
    ),
    "Xcorr": lambda: special.Xcorr(TeXlabel(_N_P1), TeXlabel(_V_X_A), "pearson"),
    "Xcorr-short": lambda: special.Xcorr(
        TeXlabel(_N_P1), TeXlabel(_V_X_A), "pearson", short_tex=True
    ),
    "ManualLabel": lambda: chemistry.mass_per_charge,
    "Ion": lambda: composition.Ion("O", "6"),
    "ChargeStateRatio": lambda: composition.ChargeStateRatio(("O", "7"), ("O", "6")),
    "ElementalAbundance": lambda: elemental_abundance.ElementalAbundance("Fe", "O"),
    "ElementalAbundance-pct": lambda: elemental_abundance.ElementalAbundance(
        "Fe", "O", pct_unit=True, photospheric=False
    ),
    "Timedelta": lambda: dt_labels.Timedelta("30min"),
    "Frequency": lambda: dt_labels.Frequency("1h"),
    "DateTime": lambda: dt_labels.DateTime("year"),
    "Epoch": lambda: dt_labels.Epoch("hour", "day"),
    "January1st": lambda: dt_labels.January1st(),
}


@pytest.mark.parametrize("case", sorted(_STRUCTURED_LABELS))
def test_every_structured_label_renders_as_a_math_axis_label(case):
    """Each composite or special label draws as math.

    ON FAILURE: the code is wrong; the class assembles a string that is not
    valid mathtext or has unbalanced dollar signs, unless the installed
    matplotlib dropped a mathtext command the label uses.
    """
    _assert_renders_as_math_axis_label(_STRUCTURED_LABELS[case]())


def test_every_special_label_class_available_lists_has_a_rendering_case():
    """Each class ``available()`` lists under Special is built above.

    ON FAILURE: a label class was added to the listing without a case; add an
    instance of it to ``_STRUCTURED_LABELS``.
    """
    built = {type(factory()).__name__ for factory in _STRUCTURED_LABELS.values()}
    assert set(_listed("Special")) - built == set()


# Each pair of M/C/S axes crossed in full, the third axis held at the data
# model's example (n, x, p1 in CLAUDE.md; "v" for C x S, since "n" is a
# scalar): the single-axis sweeps above miss strings assembled from two
# listed entries, such as a component and a species sharing one subscript.
_PAIRS = {
    "measurement-x-component": lambda: [
        (m, c, "p1")
        for m, c in itertools.product(_listed("Measurements"), _listed("Components"))
    ],
    "measurement-x-species": lambda: [
        (m, "x", sp)
        for m, sp in itertools.product(_listed("Measurements"), _listed("Species"))
    ],
    "component-x-species": lambda: [
        ("v", c, sp)
        for c, sp in itertools.product(_listed("Components"), _listed("Species"))
    ],
}


@pytest.mark.parametrize("pair", sorted(_PAIRS))
def test_every_pair_of_listed_axes_renders_as_math(pair):
    """Every ``TeXlabel`` from a full cross of two listed axes is typeset as math.

    Each distinct label string is laid out once on a shared Agg figure (the
    layout runs mathtext and raises ``ValueError`` on invalid math); all
    failures are collected so one run names every bad combination.

    ON FAILURE: the code is wrong; the listed combinations are not valid
    mathtext, unless the installed matplotlib dropped a mathtext command the
    labels use.
    """
    texts = {str(TeXlabel(mcs)): mcs for mcs in _PAIRS[pair]()}
    assert texts, "the listing parser found no names; see test_available_lists_..."

    fig, ax = plt.subplots()
    renderer = fig.canvas.get_renderer()
    failures = []
    try:
        for text, mcs in texts.items():
            if not cbook.is_math_text(text):
                failures.append((mcs, "not typeset as math", text))
                continue
            ax.set_xlabel(text)
            try:
                ax.xaxis.label.get_window_extent(renderer)
            except ValueError as err:
                failures.append((mcs, str(err).splitlines()[0], text))
    finally:
        plt.close(fig)
    assert failures == []
