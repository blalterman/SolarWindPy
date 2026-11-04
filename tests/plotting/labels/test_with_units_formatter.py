# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
r"""The label-with-units form ``$tex <sep> [units]$`` has one home (F130).

Every label class builds its ``with_units`` string through
:func:`solarwindpy.plotting.labels.base.format_with_units`. Which bracket form a
class uses (plain ``[ ]`` or sized ``\left[ \right]``) is left as it was: the
author decides whether to unify it.
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
        # Chosen inputs; each form is the one the label classes render today.
        ({"sized": False}, r"$n_{p} \; [\mathrm{cm}^{-3}]$"),
        ({"sized": True}, r"$n_{p} \; \left[\mathrm{cm}^{-3}\right]$"),
        (
            {"sized": True, "new_line": True},
            "$n_{p} $\n$ " + r"\left[\mathrm{cm}^{-3}\right]$",
        ),
        ({"sized": False, "new_line": True}, "$n_{p} $\n$ " + r"[\mathrm{cm}^{-3}]$"),
    ],
)
def test_format_with_units_writes_tex_separator_and_bracketed_units(kwargs, expected):
    r"""The formatter joins TeX and units with ``\;`` or a line break, in brackets.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels.base import format_with_units

    assert format_with_units(r"n_{p}", r"\mathrm{cm}^{-3}", **kwargs) == expected
