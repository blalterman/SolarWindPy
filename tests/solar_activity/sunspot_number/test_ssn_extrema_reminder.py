# Spent-When: PERMANENT(ssn_extrema.csv stops being hand-copied from SILSO)
# Supersedes: none
"""A reminder, in the default suite, to refresh ssn_extrema.csv from SILSO.

``ssn_extrema.csv`` is a hand copy of SILSO's solar-cycle extrema. Six years
after its latest extremum a new minimum or maximum has likely occurred, so
from that due date on the reminder test warns, naming the due date. It never
fails: the warning appears in pytest's warnings summary. Adding a new
extremum row moves the due date, so the reminder resets itself.

The clock is a parameter, so both sides of the due date are tested without
freezing real time.
"""

import warnings

import pandas as pd
import pytest

from solarwindpy.solar_activity.sunspot_number import sidc

SSN_EXTREMA_CSV = sidc.Path(sidc.__file__).parent / "ssn_extrema.csv"

#: Years after the latest extremum at which the reminder falls due.
REMINDER_YEARS = 6


class ExtremaReminderWarning(UserWarning):
    """ssn_extrema.csv is due to be checked against SILSO."""


def read_extrema(path):
    """The CSV's extrema table, parsed independently of ``SSNExtrema``."""
    return pd.read_csv(
        path, comment="#", index_col="Number", parse_dates=["Min", "Max"]
    )


def reminder_due(path=SSN_EXTREMA_CSV):
    """Due date: the later of the last row's Min and Max, plus six years."""
    latest = read_extrema(path).iloc[-1].loc[["Min", "Max"]].max()  # skips NaT
    return latest + pd.DateOffset(years=REMINDER_YEARS)


def remind_if_due(today, path=SSN_EXTREMA_CSV):
    """Warn ``ExtremaReminderWarning`` if ``today`` is on or after the due date.

    Returns the due date.
    """
    due = reminder_due(path)
    if pd.Timestamp(today) >= due:
        warnings.warn(
            f"ssn_extrema.csv was due for a check on {due:%Y-%m-%d}: look for a "
            "new cycle minimum or maximum in SILSO's "
            "https://www.sidc.be/SILSO/DATA/Cycles/TableCyclesMiMa.txt and the "
            "13-month smoothed series "
            "https://www.sidc.be/SILSO/DATA/SN_ms_tot_V2.0.txt, update "
            f"{path}, and optionally run the opt-in drift test "
            "tests/drift/test_drift_silso.py (pytest --run-drift).",
            ExtremaReminderWarning,
            stacklevel=2,
        )
    return due


def test_ssn_extrema_csv_is_not_due_for_a_silso_check():
    """Warns, never fails, once ssn_extrema.csv is due for a check against SILSO.

    ON FAILURE: the code is wrong; the reminder itself only ever warns.
    """
    remind_if_due(pd.Timestamp.today())


def test_the_due_date_is_six_years_after_the_latest_extremum():
    """The due date is the later of the last row's Min and Max plus six years.

    Identity, computed from the parts read off the CSV with the standard
    library; for cycle 25 (Max 2024-10-01) it is 2030-10-01.

    ON FAILURE: the code is wrong.
    """
    lines = [
        line
        for line in SSN_EXTREMA_CSV.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    _, minimum, maximum = lines[-1].split(",")
    latest = max(pd.Timestamp(minimum), pd.Timestamp(maximum))
    expected = latest.replace(year=latest.year + REMINDER_YEARS)
    assert reminder_due() == expected


def test_no_reminder_before_the_due_date():
    """The day before the due date passes silently.

    ON FAILURE: the code is wrong.
    """
    due = reminder_due()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        remind_if_due(due - pd.Timedelta(days=1))


@pytest.mark.parametrize("after", ["0D", "400D"])
def test_a_reminder_on_and_after_the_due_date(after):
    """On and after the due date, a warning names it and SILSO.

    ON FAILURE: the code is wrong.
    """
    due = reminder_due()
    with pytest.warns(ExtremaReminderWarning) as record:
        remind_if_due(due + pd.Timedelta(after))
    message = str(record[0].message)
    assert f"{due:%Y-%m-%d}" in message
    assert "TableCyclesMiMa.txt" in message
    assert "SN_ms_tot_V2.0" in message


def test_a_new_extremum_row_moves_the_due_date(tmp_path):
    """Appending cycle 26's minimum moves the due date six years past it.

    Chosen input: the shipped CSV plus a row for cycle 26 with Min 2031-01-01
    and no Max yet, so the due date becomes 2037-01-01 and a date that was
    overdue against the shipped CSV is quiet again.

    ON FAILURE: the code is wrong.
    """
    updated = tmp_path / "ssn_extrema.csv"
    updated.write_text(SSN_EXTREMA_CSV.read_text().rstrip("\n") + "\n26,2031-01-01,\n")

    assert reminder_due(updated) == pd.Timestamp("2037-01-01")
    overdue = reminder_due() + pd.Timedelta(days=1)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        remind_if_due(overdue, updated)
