"""``solarwindpy.plotting.labels.available`` prints what ``TeXlabel`` knows."""

import re

from solarwindpy.plotting import labels


def _measurement_lines(capsys):
    """The comma-separated lines of the Measurements section of ``available()``."""
    labels.available()
    text = capsys.readouterr().out
    block = re.search(r"^Measurements\n-+\n(.*?)\n\s*\n", text, re.M | re.S)
    assert block, "available() printed no Measurements section"
    return [line.split(", ") for line in block.group(1).splitlines()]


def test_available_output(capsys):
    """``available()`` prints the heading and all four sections.

    ON FAILURE: the code is wrong.
    """
    labels.available()
    captured = capsys.readouterr().out
    for section in (
        "TeXlabel knows",
        "Measurements",
        "Components",
        "Species",
        "Special",
    ):
        assert section in captured


def test_measurements_are_grouped_by_first_character(capsys):
    """Measurements print sorted, capitalised names first, then one line per letter.

    The first line holds every name starting with an upper-case letter. Each
    later line holds the lower-case names sharing one first character, and
    the lines run in order of that character. Names are sorted within a line.

    ON FAILURE: the code is wrong.
    """
    lines = _measurement_lines(capsys)
    upper, rest = lines[0], lines[1:]
    assert all(name[0].isupper() for name in upper)
    assert rest, "the fixture: some measurement starts with a lower-case letter"
    firsts = []
    for line in [upper] + rest:
        assert line == sorted(line)
    for line in rest:
        assert len({name[0] for name in line}) == 1
        assert not line[0][0].isupper()
        firsts.append(line[0][0])
    assert firsts == sorted(set(firsts))
