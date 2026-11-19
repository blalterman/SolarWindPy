"""Plotting a solar activity indicator: ``solar_activity.plots``.

The indicator is a real ``SIDC`` monthly-smoothed sunspot series. Only the
network is faked: SILSO's URL base is pointed at a local directory holding a
file in SILSO's ``;``-separated format, and the download cache is kept under
``tmp_path``: ``tests/solar_activity/conftest.py`` has every test here use the
root ``isolated_cache`` fixture (``tests/conftest.py``) through an autouse
wrapper. The series is chosen so each value is known by hand: the SSN of
month ``i`` after January 2000 is ``50 + i``.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from solarwindpy.plotting import labels  # noqa: E402
from solarwindpy.plotting.base import Guides  # noqa: E402
from solarwindpy.solar_activity import plots  # noqa: E402
from solarwindpy.solar_activity.plots import IndicatorPlot, SSNPlot  # noqa: E402
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC, SIDC_ID  # noqa: E402
from tests.tolerances import exact  # noqa: E402

MONTHS = pd.date_range("2000-01-01", "2009-12-01", freq="MS")
SSN = 50.0 + np.arange(MONTHS.size)  # month i after 2000-01 has SSN 50 + i
STD = 2.0


def silso_m13(ssn=SSN):
    """``ssn`` as SILSO writes it (year; month; frac; ssn; std; n; def)."""
    return "".join(
        f"{t.year};{t.month:02d};{t.year + (t.month - 0.5) / 12:.3f};"
        f"{s:6.1f};{STD:5.1f};  100;1\n"
        for t, s in zip(MONTHS, ssn)
    )


@pytest.fixture
def sidc(tmp_path, monkeypatch):
    """A real ``SIDC("m13")`` downloaded from a local SILSO file of ``SSN``."""
    return sidc_from_silso(tmp_path, monkeypatch, SSN)


def sidc_from_silso(tmp_path, monkeypatch, ssn):
    """A real ``SIDC("m13")`` downloaded from a local SILSO file of ``ssn``.

    Build one per test: a second ``SIDC("m13")`` under the same cache reads
    the fresh cached copy instead of the new file.
    """
    remote = tmp_path / "remote"
    remote.mkdir()
    (remote / "snmstotcsv.php").write_text(silso_m13(ssn), encoding="utf-8")

    base = remote.as_uri() + "/"
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

    assert ax.get_xlabel() == str(labels.epochs.DateTime("Year"))
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


def test_ssn_axis_of_a_peak_between_100_and_200_spans_zero_to_200(sidc):
    """A series peaking between 100 and 200 gets an SSN range of 0-200.

    Chosen input: the series peaks at SSN 169, which rounds up to 200.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    SSNPlot(sidc).make_plot(ax)
    assert ax.get_ylim() == (0.0, 200.0)


# An active series peaking above 200 (cycle 19 peaked near 285) and a quiet
# one peaking below 100. A peak between 100 and 200 cannot tell a fixed 0-200
# range from the round-up rule.
ACTIVE_SSN = 2.0 * SSN
QUIET_SSN = SSN / 4.0


def test_the_rule_fixtures_bracket_the_old_fixed_range():
    """The active series peaks above 200 and the quiet one below 100.

    ON FAILURE: the fixtures no longer separate the round-up rule from a
    fixed 0-200 range; fix the fixtures.
    """
    assert ACTIVE_SSN.max() > 200
    assert QUIET_SSN.max() < 100


def test_ssn_axis_tops_an_active_series_at_its_peak_rounded_up_to_100(
    tmp_path, monkeypatch
):
    """An SSN plot's y range starts at 0 and tops the peak at the next 100.

    The top is a multiple of 100, at or above the plotted peak, and less
    than 100 above it, so no part of a strong cycle is clipped.

    ON FAILURE: the code is wrong.
    """
    indicator = sidc_from_silso(tmp_path, monkeypatch, ACTIVE_SSN)
    plot = SSNPlot(indicator)
    fig, ax = plt.subplots()
    plot.make_plot(ax)

    bottom, top = ax.get_ylim()
    peak = plot.plot_data.max()
    assert bottom == 0
    assert top % 100 == 0
    assert peak <= top < peak + 100


def test_ssn_axis_of_a_quiet_series_tops_at_100(tmp_path, monkeypatch):
    """A series peaking below 100 gets the rule's floor, 0 to 100.

    ON FAILURE: the code is wrong.
    """
    indicator = sidc_from_silso(tmp_path, monkeypatch, QUIET_SSN)
    fig, ax = plt.subplots()
    SSNPlot(indicator).make_plot(ax)

    assert ax.get_ylim() == (0.0, 100.0)


@pytest.mark.parametrize("ssn", [ACTIVE_SSN, QUIET_SSN], ids=["active", "quiet"])
def test_ssn_axis_top_matches_the_colour_bar_scale(tmp_path, monkeypatch, ssn):
    """SSNPlot and ``plot_on_colorbar`` scale the same series to one top.

    ``plot_on_colorbar`` labels its scale top as the last major tick.

    ON FAILURE: the two SSN scales have diverged. The code is wrong.
    """
    indicator = sidc_from_silso(tmp_path, monkeypatch, ssn)
    fig, ax = plt.subplots()
    SSNPlot(indicator).make_plot(ax)

    cbar_fig, cax = plt.subplots()
    index = indicator.data.index
    plots.plot_on_colorbar(indicator, cax, index[0], index[-1], vertical_cbar=True)
    cbar_top = float(cax.xaxis.get_ticklabels()[-1].get_text())

    assert ax.get_ylim()[1] == cbar_top


@pytest.mark.parametrize(
    "ssn, top",
    [
        ([0.0, 30.0, 15.0], 100),  # ceil(30 / 100) * 100 = 100
        ([0.0, 100.0, 50.0], 100),  # a peak on a multiple of 100 is the top
        ([0.0, 140.0, 70.0], 200),  # ceil(140 / 100) * 100 = 200
        ([0.0, 285.0, 140.0], 300),  # cycle 19's peak: ceil(2.85) * 100 = 300
        ([0.0, 0.0], 100),  # the floor: never a zero-height scale
        ([], 100),  # an empty series has no peak; the floor holds
    ],
    ids=["quiet", "on-a-hundred", "moderate", "active", "all-zero", "empty"],
)
def test_ssn_scale_top_rounds_the_peak_up_to_the_next_100(ssn, top):
    """``ssn_scale_top`` is the peak rounded up to a multiple of 100, at least 100.

    Each expected top is computed by hand from the series' peak.

    ON FAILURE: the code is wrong.
    """
    assert plots.ssn_scale_top(pd.Series(ssn, dtype=float)) == top


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
    assert plot.path == expected.with_name("linX-logY")


# ---------------------------------------------------------------------------
# The sunspot number along a colour bar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("vertical", [True, False])
def test_plot_on_colorbar_draws_the_requested_span(sidc, vertical):
    """Both lines carry the window's sunspot numbers, scaled onto the bar.

    Chosen input: the window 2002-01 to 2008-01 holds months 24 to 96, so
    SSN 74 to 146 and a scale top of 200. On a fresh axes the value axis
    spans (0, 1), so each SSN plots at SSN / 200. The time coordinates are
    the months in days since 1970, recomputed from the dates. A vertical bar
    puts time on y and SSN on x; a horizontal bar swaps them.

    ON FAILURE: the code is wrong.
    """
    window = slice(24, 97)
    fig, cax = plt.subplots()
    plots.plot_on_colorbar(sidc, cax, MONTHS[24], MONTHS[96], vertical_cbar=vertical)

    assert len(cax.lines) == 2
    for line in cax.lines:
        ssn_coords, time_coords = line.get_data()
        if not vertical:
            ssn_coords, time_coords = time_coords, ssn_coords
        assert np.asarray(time_coords) == exact(days_since_1970(MONTHS[window]))
        assert np.asarray(ssn_coords) == exact(SSN[window] / 200.0)


@pytest.mark.parametrize("vertical", [True, False])
def test_plot_on_colorbar_returns_cax_both_lines_and_no_colorbar(sidc, vertical):
    """``plot_on_colorbar`` returns ``(cax, underlay, overlay, guides)``.

    The underlay is the solid white line and the overlay the dashed black
    line drawn over it, both on ``cax``. Every field of ``guides`` is None
    because the function receives only the colour bar's axes.

    ON FAILURE: the code is wrong.
    """
    fig, axes = plt.subplots()
    ret = plots.plot_on_colorbar(
        sidc, axes, MONTHS[24], MONTHS[96], vertical_cbar=vertical
    )

    assert isinstance(ret, tuple) and len(ret) == 4
    cax, underlay, overlay, guides = ret
    assert cax is axes
    assert guides == Guides()
    assert isinstance(underlay, matplotlib.lines.Line2D)
    assert isinstance(overlay, matplotlib.lines.Line2D)
    assert list(axes.lines) == [underlay, overlay]
    assert underlay.get_linestyle() == "-"
    assert matplotlib.colors.to_hex(underlay.get_color()) == "#ffffff"
    assert matplotlib.colors.to_hex(overlay.get_color()) == "#000000"


def _value_axis_labels(axes):
    """The colour bar's major tick labels on the SSN (x) axis of a vertical bar."""
    return [label.get_text() for label in axes.xaxis.get_ticklabels()]


def test_plot_on_colorbar_handles_a_low_activity_window(tmp_path, monkeypatch):
    """A window that never exceeds SSN 50 plots on a 0-100 scale.

    Chosen input: a flat SSN of 30. The scale top is the peak rounded up to
    the next 100 and never below 100, so the top is 100 and the ticks read
    0, 50, 100. On a fresh axes the x limits are (0, 1), so SSN 30 plots at
    30 / 100 = 0.3.

    ON FAILURE: the code is wrong.
    """
    indicator = sidc_from_silso(tmp_path, monkeypatch, np.full(MONTHS.size, 30.0))
    fig, cax = plt.subplots()
    plots.plot_on_colorbar(indicator, cax, MONTHS[0], MONTHS[-1], vertical_cbar=True)

    for line in cax.lines:
        assert np.asarray(line.get_data()[0], dtype=float) == exact(0.3)
    assert _value_axis_labels(cax) == ["0", "50", "100"]


def test_plot_on_colorbar_rounds_a_peak_of_140_up_to_200(tmp_path, monkeypatch):
    """A peak of 140 gets a scale top of 200, so the line stays inside the scale.

    Rounding to the nearest 100 would give 100 and draw the peak beyond the
    colour bar. Rounded up, the top is 200 and the ticks read 0, 100, 200. On
    a fresh axes the x limits are (0, 1), so SSN 140 plots at 140 / 200 = 0.7
    and SSN 20 at 20 / 200 = 0.1, both inside [0, 1].

    ON FAILURE: the code is wrong.
    """
    ssn = np.full(MONTHS.size, 20.0)
    ssn[MONTHS.size // 2] = 140.0
    indicator = sidc_from_silso(tmp_path, monkeypatch, ssn)
    fig, cax = plt.subplots()
    plots.plot_on_colorbar(indicator, cax, MONTHS[0], MONTHS[-1], vertical_cbar=True)

    for line in cax.lines:
        coords = np.asarray(line.get_data()[0], dtype=float)
        assert coords.max() == exact(0.7)  # hand-computed: 140 / 200
        assert coords.min() == exact(0.1)  # hand-computed: 20 / 200
    assert _value_axis_labels(cax) == ["0", "100", "200"]
