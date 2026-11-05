# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
r"""The label-with-units form ``$tex <sep> \left[units\right]$`` has one home (F130).

Every label class builds its ``with_units`` string through
:func:`solarwindpy.plotting.labels.base.format_with_units`. The author ruled one
bracket form, sized ``\left[ \right]``, for every class.
"""

import re
from pathlib import Path

import pytest

import solarwindpy.plotting.labels as labels


#: The closing of a label-with-units literal: a bracket, then ``$``, then the
#: end of the string.
_CLOSING = re.compile(r"\]\$(?:\"|')")


def test_no_label_module_writes_the_closing_bracket_itself():
    """No module in ``plotting/labels`` spells out ``...]$`` in a string literal.

    ON FAILURE: the code is wrong; route the label through ``format_with_units``.
    """
    root = Path(labels.__file__).parent
    hits = [
        f"{path.name}:{n}"
        for path in sorted(root.glob("*.py"))
        for n, line in enumerate(path.read_text().splitlines(), start=1)
        if _CLOSING.search(line)
    ]
    assert hits == []


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        # Chosen inputs.
        ({}, r"$n_{p} \; \left[\mathrm{cm}^{-3}\right]$"),
        ({"new_line": True}, "$n_{p} $\n$ " + r"\left[\mathrm{cm}^{-3}\right]$"),
    ],
)
def test_format_with_units_writes_tex_separator_and_bracketed_units(kwargs, expected):
    r"""The formatter joins TeX and units with ``\;`` or a line break, in brackets.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels.base import format_with_units

    assert format_with_units(r"n_{p}", r"\mathrm{cm}^{-3}", **kwargs) == expected


# --- one bracket form (the author's F130 ruling) ------------------------------


def test_format_with_units_always_sizes_the_brackets():
    r"""Units sit in ``\left[ \right]``, which grow with fractional units.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels.base import format_with_units

    assert format_with_units(r"n_{p}", r"\mathrm{cm}^{-3}") == (
        r"$n_{p} \; \left[\mathrm{cm}^{-3}\right]$"
    )


def _n_p1():
    from solarwindpy.plotting.labels.base import TeXlabel

    return TeXlabel(("n", "", "p1"))


def _v_xa():
    from solarwindpy.plotting.labels.base import TeXlabel

    return TeXlabel(("v", "x", "a"))


_PLAIN_BEFORE_F130 = {
    "Timedelta": lambda s, d: d.Timedelta("2h"),
    "ManualLabel": lambda s, d: s.ManualLabel("Test Label", "b"),
    "CarringtonRotation": lambda s, d: s.CarringtonRotation(),
    "Count": lambda s, d: s.Count(),
    "Power": lambda s, d: s.Power(),
    "Probability": lambda s, d: s.Probability(_n_p1(), "> 5"),
    "CountOther": lambda s, d: s.CountOther(_n_p1(), "> 5"),
    "Distance2Sun": lambda s, d: s.Distance2Sun("m"),
    "SSN": lambda s, d: s.SSN("M13"),
    "ComparisonLabel": lambda s, d: s.ComparisonLabel(_n_p1(), _n_p1(), "add"),
    "Xcorr": lambda s, d: s.Xcorr(_n_p1(), _v_xa(), "pearson"),
}


@pytest.mark.parametrize(
    "make", list(_PLAIN_BEFORE_F130.values()), ids=list(_PLAIN_BEFORE_F130)
)
def test_every_label_class_sizes_its_unit_brackets(make):
    r"""Each label class that bracketed units plainly before F130 now sizes them.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels import datetime, special

    label = str(make(special, datetime))
    assert r" \; \left[" in label
    assert label.endswith(r"\right]$")
