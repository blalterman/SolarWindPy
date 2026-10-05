"""Plotting a solar activity indicator: ``solar_activity.plots``.

The indicator is a real ``SIDC`` monthly-smoothed sunspot series. Only the
network is faked: SILSO's URL base is pointed at a local directory holding a
file in SILSO's ``;``-separated format, and the cache home is moved under
``tmp_path``. The series is chosen so each value is known by hand: the SSN
of month ``i`` after January 2000 is ``50 + i``.
"""

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from solarwindpy.plotting import labels  # noqa: E402
from solarwindpy.solar_activity.plots import IndicatorPlot, SSNPlot  # noqa: E402
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC, SIDC_ID  # noqa: E402
from tests.tolerances import exact  # noqa: E402

MONTHS = pd.date_range("2000-01-01", "2009-12-01", freq="MS")
SSN = 50.0 + np.arange(MONTHS.size)  # month i after 2000-01 has SSN 50 + i
STD = 2.0


def silso_m13():
    """The chosen series as SILSO writes it (year; month; frac; ssn; std; n; def)."""
    return "".join(
        f"{t.year};{t.month:02d};{t.year + (t.month - 0.5) / 12:.3f};"
        f"{s:6.1f};{STD:5.1f};  100;1\n"
        for t, s in zip(MONTHS, SSN)
    )


@pytest.fixture
def sidc(tmp_path, monkeypatch):
    """A real ``SIDC("m13")`` downloaded from a local SILSO file.

    ``DataLoader`` reads the cache date from an 8-digit run anywhere in the
    cache's absolute path, so a ``tmp_path`` that holds one would be misread.
    """
    if re.search(r"\d{8}", str(tmp_path)):
        pytest.skip(f"tmp_path contains an 8-digit run: {tmp_path}")
    home = tmp_path / "home"
    home.mkdir()
    remote = tmp_path / "remote"
    remote.mkdir()
    (remote / "snmstotcsv.php").write_text(silso_m13())

    base = remote.as_uri() + "/"
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(SIDC_ID, "_url_base", property(lambda self: base))
    return SIDC("m13")


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


class StdPlot(IndicatorPlot):
    """The generic plotter, on the ``std`` column, with the base axis format."""

    def _format_axis(self, ax):
        return super()._format_axis(ax)


def days_since_1970(index):
    """Matplotlib's default date number: days since 1970-01-01 (mpl >= 3.3)."""
    return ((index - pd.Timestamp("1970-01-01")) / pd.Timedelta(days=1)).to_numpy()


# ---------------------------------------------------------------------------
# What is plotted
# ---------------------------------------------------------------------------


def test_the_fixture_series_is_the_one_chosen(sidc):
    """The SIDC built from the local file carries exactly the chosen SSN.

    ON FAILURE: the fixture no longer separates one month's SSN from the
    next; fix the fixture.
    """
    ssn = sidc.data["ssn"]
    assert ssn.index.equals(MONTHS.as_unit(ssn.index.unit))
    assert ssn.to_numpy() == exact(SSN)  # through a CSV round trip


def test_ssn_plot_shows_the_whole_ssn_series(sidc):
    """With no plasma index, an SSN plot shows every month of ``ssn``.

    ON FAILURE: the code is wrong.
    """
    plot = SSNPlot(sidc)
    assert plot.ykey == "ssn"
    assert plot.indicator is sidc
    assert plot.plasma_index is None
    assert plot.plot_data.to_numpy() == exact(SSN)  # through a CSV round trip


def test_plasma_index_trims_to_data_from_its_earliest_time(sidc):
    """A plasma index keeps the indicator from its earliest epoch onward.

    Chosen input: an unsorted index whose earliest time, 2005-01-15, is not
    its first element. The first month on or after it is 2005-02-01, month
    61, so SSN 111, and 59 months remain.

    ON FAILURE: the code is wrong.
    """
    plasma = pd.DatetimeIndex(["2007-03-01", "2005-01-15", "2008-06-01"])
    data = SSNPlot(sidc, plasma_index=plasma).plot_data

    assert data.index[0] == pd.Timestamp("2005-02-01")
    assert data.iloc[0] == 111.0
    assert data.size == MONTHS.size - 61


def test_plasma_index_after_the_series_leaves_nothing_to_plot(sidc):
    """A plasma index that starts after the last month selects no data.

    ON FAILURE: the code is wrong.
    """
    plasma = pd.DatetimeIndex(["2015-01-01"])
    assert SSNPlot(sidc, plasma_index=plasma).plot_data.empty


def test_an_absent_column_is_reported_by_name(sidc):
    """Plotting a column the indicator lacks raises a KeyError naming it.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(KeyError, match="no_such_column"):
        StdPlot(sidc, "no_such_column").plot_data


def test_make_plot_draws_the_series_against_date_numbers(sidc):
    """``make_plot`` draws one line: x in days since 1970, y the column.

    Independent route: the x vertices are recomputed from the month dates,
    not from matplotlib's converter.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    StdPlot(sidc, "ssn").make_plot(ax)

    assert len(ax.lines) == 1
    x, y = ax.lines[0].get_data()
    assert np.asarray(x) == exact(days_since_1970(MONTHS))
    assert np.asarray(y) == exact(SSN)


def test_make_plot_without_axes_draws_on_a_new_figure(sidc):
    """With no axes given, ``make_plot`` draws on a figure of its own.

    ON FAILURE: the code is wrong.
    """
    plt.close("all")
    SSNPlot(sidc).make_plot()

    assert len(plt.get_fignums()) == 1
    (ax,) = plt.gcf().axes
    assert len(ax.lines) == 1


# ---------------------------------------------------------------------------
# Axis formatting
# ---------------------------------------------------------------------------


def test_axes_are_labelled_with_time_and_the_indicator(sidc):
    """The x label is the year label and the y label is this series' SSN label.

    The expected strings come from the label objects themselves, so this
    checks which label is used, not its wording.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    SSNPlot(sidc).make_plot(ax)

    assert ax.get_xlabel() == str(labels.datetime.DateTime("Year"))
    assert ax.get_ylabel() == str(labels.special.SSN("m13"))


def test_date_ticks_are_labelled_by_year(sidc):
    """Major x ticks name the year of the date they mark.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    SSNPlot(sidc).make_plot(ax)

    formatter = ax.xaxis.get_major_formatter()
    june_2005 = days_since_1970(pd.DatetimeIndex(["2005-06-01"]))[0]
    assert formatter(june_2005) == "2005"


def test_ssn_axis_spans_zero_to_two_hundred(sidc):
    """The SSN plot fixes its y range to 0-200 whatever the data span.

    Chosen input: the series peaks at SSN 169, below the upper limit.

    ON FAILURE: the code is wrong, unless the author changed the SSN range.
    """
    fig, ax = plt.subplots()
    SSNPlot(sidc).make_plot(ax)
    assert ax.get_ylim() == (0.0, 200.0)


@pytest.mark.parametrize("logx, logy", [(True, False), (False, True)])
def test_log_flags_set_the_matching_axis_scale(sidc, logx, logy):
    """``set_log`` puts exactly the flagged axes on a log scale.

    ON FAILURE: the code is wrong.
    """
    plot = StdPlot(sidc, "std")
    plot.set_log(x=logx, y=logy)
    fig, ax = plt.subplots()
    plot.make_plot(ax)

    assert ax.get_xscale() == ("log" if logx else "linear")
    assert ax.get_yscale() == ("log" if logy else "linear")


# ---------------------------------------------------------------------------
# Save path
# ---------------------------------------------------------------------------


def test_auto_path_is_built_from_class_labels_and_scales(sidc):
    """The automatic path is class / x label / y label / axis scales.

    The label components come from the label objects' own ``path``.

    ON FAILURE: the code is wrong.
    """
    plot = SSNPlot(sidc)
    expected = Path("SSNPlot", plot.labels.x.path, plot.labels.y.path, "linX-linY")
    assert plot.path == expected

    plot.set_log(y=True)
    plot.set_path("auto")
    assert plot.path == expected.with_name("linX-logY")


def test_explicit_path_is_used_with_or_without_scales(sidc):
    """An explicit path is kept, with the scale suffix only when asked.

    ON FAILURE: the code is wrong.
    """
    plot = SSNPlot(sidc)
    plot.set_path("figures/ssn")
    assert plot.path == Path("figures", "ssn", "linX-linY")

    plot.set_path("figures/ssn", add_scale=False)
    assert plot.path == Path("figures", "ssn")
