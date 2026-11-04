# Spent-When: PERMANENT(ssn_extrema.csv stops being hand-copied from SILSO)
# Supersedes: none
"""Drift assertion for the solar-cycle extrema copied into ssn_extrema.csv.

``SSNExtrema`` reads ``ssn_extrema.csv``, a hand copy of SILSO's cycle table.
Every minimum and maximum SILSO lists must appear in the CSV with the same
year and month. The CSV may hold an extremum SILSO has not listed yet: cycle
25's maximum (2024-10) comes from the 13-month smoothed series.
"""

import urllib.request

import pytest

from solarwindpy.solar_activity.sunspot_number.sidc import SSNExtrema

from ._drift import assert_extrema_listed

pytestmark = pytest.mark.drift

TABLE_URL = "https://www.sidc.be/SILSO/DATA/Cycles/TableCyclesMiMa.txt"


def parse_cycle_table(text):
    """Map ``(cycle, kind)`` to ``"YYYY-MM"`` for every extremum in SILSO's table.

    Data rows start with the cycle number, then the minimum's year, month and
    smoothed sunspot number, then the same three for the maximum. An open
    cycle's row stops after its minimum.
    """
    extrema = {}
    for line in text.splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        cycle = int(fields[0])
        for kind, year_month in (("Min", fields[1:3]), ("Max", fields[4:6])):
            if len(year_month) == 2:
                year, month = year_month
                extrema[(cycle, kind)] = f"{int(year):04d}-{int(month):02d}"
    return extrema


def test_parse_cycle_table_reads_open_and_closed_cycles():
    """A closed cycle gives both extrema; an open one only its minimum.

    Chosen input: SILSO's layout, two header lines, a blank, a closed cycle 24
    and an open cycle 25.

    ON FAILURE: the code is wrong.
    """
    text = (
        "Cycle Minimum         Maximum         Duration in\n"
        "Nb    Year Month SN   Year Month SN   Years + Months\n"
        "\n"
        "24    2008 12    2.2  2014 04  116.4   11 00\n"
        "25    2019 12    1.8\n"
    )
    assert parse_cycle_table(text) == {
        (24, "Min"): "2008-12",
        (24, "Max"): "2014-04",
        (25, "Min"): "2019-12",
    }


def test_silso_extrema_are_in_ssn_extrema_csv():
    """Every extremum SILSO lists is in ssn_extrema.csv with the same year-month.

    ON FAILURE: external fact drifted; update
    src/solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv.
    """
    with urllib.request.urlopen(TABLE_URL, timeout=30) as response:
        observed = parse_cycle_table(response.read().decode())

    data = SSNExtrema().data
    pinned = {
        (int(cycle), kind): date.strftime("%Y-%m")
        for (cycle, kind), date in data.stack().items()
    }

    assert_extrema_listed(
        pinned,
        observed,
        fact="SILSO lists an extremum that ssn_extrema.csv lacks or differs on",
        location="src/solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv",
        remedy=f"copy the new or changed extrema from {TABLE_URL}",
    )
