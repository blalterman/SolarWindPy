# Spent-When: PERMANENT(solarwindpy.instabilities.verscharen2016 is removed from the package)
# Supersedes: none
"""Tests for :mod:`solarwindpy.instabilities.verscharen2016`.

Every expected threshold comes from the paper the module implements, transcribed
here independently of the module:

    Verscharen, D., Chandran, B. D. G., Klein, K. G., & Quataert, E. (2016),
    ApJ 831, 128. doi:10.3847/0004-637X/831/2/128 (arXiv:1605.07143v2).

- Eq. (5), Appendix A.1: R_p = 1 + a / (beta_par,p - c)**b.
- Table 1: fit parameters a, b, c for gamma_m / Omega_p = 1e-2, 1e-3, 1e-4.
- Section 1, first paragraph: R_p > 1 drives the A/IC and mirror-mode (MM)
  instabilities; R_p < 1 drives the FM/W and oblique firehose (OFI) instabilities.
"""

import io
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from matplotlib.colors import to_hex  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from solarwindpy.instabilities import verscharen2016 as v16  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# Verscharen et al. (2016), doi:10.3847/0004-637X/831/2/128, Table 1.
# Keys: log10(gamma_m / Omega_p). Values: (a, b, c) for use in Eq. (5).
TABLE_1 = {
    -2: {
        "AIC": (0.649, 0.400, 0.0),
        "MM": (1.040, 0.633, -0.012),
        "FMW": (-0.647, 0.583, 0.713),
        "OFI": (-1.447, 1.000, -0.148),
    },
    -3: {
        "AIC": (0.437, 0.428, -0.003),
        "MM": (0.801, 0.763, -0.063),
        "FMW": (-0.497, 0.566, 0.543),
        "OFI": (-1.390, 1.005, -0.111),
    },
    -4: {
        "AIC": (0.367, 0.364, 0.011),
        "MM": (0.702, 0.674, -0.009),
        "FMW": (-0.408, 0.529, 0.410),
        "OFI": (-1.454, 1.023, -0.178),
    },
}
GROWTH_RATES = sorted(TABLE_1)
INSTABILITIES = ["AIC", "FMW", "MM", "OFI"]
ROWS = [(g, k) for g in GROWTH_RATES for k in INSTABILITIES]

# Every fit is finite for beta_par > max(c) = 0.713 (Table 1, FMW at 1e-2).
FINITE_BETA = np.logspace(np.log10(0.75), 2, 40)
# Spans beta_par < c for the FM/W fits, where Eq. (5) is undefined (NaN).
WIDE_BETA = np.logspace(-1, 2, 40)


def eq5(beta, a, b, c):
    """Verscharen et al. (2016) Eq. (5), written from the paper."""
    with np.errstate(invalid="ignore"):
        return 1.0 + a / (np.asarray(beta, dtype=float) - c) ** b


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# Published fit parameters and Eq. (5)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "growth_rate,instability",
    ROWS,
    ids=[f"{g}-{k}" for g, k in ROWS],
)
@pytest.mark.parametrize("param", ["a", "b", "c"])
def test_fit_parameters_are_verscharen2016_table_1(growth_rate, instability, param):
    """insta_params holds Table 1 of doi:10.3847/0004-637X/831/2/128 verbatim.

    Published to 3 decimals, so a transcription error is at least 1e-3; exact
    comparison is correct.

    ON FAILURE: the code is wrong, unless the author rejects Verscharen et al.
    (2016) Table 1 as the source.
    """
    expected = dict(zip("abc", TABLE_1[growth_rate][instability]))[param]
    actual = v16.insta_params.loc[(instability, growth_rate), param]
    assert actual == exact(expected)


@pytest.mark.parametrize(
    "growth_rate,instability",
    ROWS,
    ids=[f"{g}-{k}" for g, k in ROWS],
)
def test_beta_ani_inst_is_equation_5(growth_rate, instability):
    """beta_ani_inst evaluates Eq. (5) of Verscharen et al. (2016), NaN where beta < c.

    ON FAILURE: the code is wrong.
    """
    a, b, c = TABLE_1[growth_rate][instability]
    with np.errstate(invalid="ignore"):
        actual = v16.beta_ani_inst(WIDE_BETA, a=a, b=b, c=c)
    assert actual == exact(eq5(WIDE_BETA, a, b, c), nan_ok=True)


def test_threshold_is_undefined_below_the_fit_offset():
    """Eq. (5) has no real value for beta_par < c (fractional power of a negative).

    FM/W at gamma_m = 1e-3 Omega_p has c = 0.543, b = 0.566 (Table 1).

    ON FAILURE: the code is wrong.
    """
    with np.errstate(invalid="ignore"):
        actual = v16.beta_ani_inst(np.array([0.1, 0.5]), a=-0.497, b=0.566, c=0.543)
    assert np.isnan(actual).all()


# Hand-computed: at beta_par = c + 1, Eq. (5) gives R_p = 1 + a for any b.
# Values from Table 1, gamma_m = 1e-2 Omega_p.
HAND_CASES = [
    ("AIC", 1.0, 1.649),  # c = 0      -> beta = 1,     R = 1 + 0.649
    ("MM", 0.988, 2.040),  # c = -0.012 -> beta = 0.988, R = 1 + 1.040
    ("FMW", 1.713, 0.353),  # c = 0.713  -> beta = 1.713, R = 1 - 0.647
    ("OFI", 0.852, -0.447),  # c = -0.148 -> beta = 0.852, R = 1 - 1.447
]


@pytest.mark.parametrize("instability,beta,expected", HAND_CASES)
def test_threshold_at_unit_offset_is_one_plus_a(instability, beta, expected):
    """StabilityCondition(-2) thresholds equal hand-computed 1 + a at beta = c + 1.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityCondition(-2, pd.Series([beta]), pd.Series([1.0]))
    actual = sc.instability_thresholds[instability].iloc[0]
    assert actual == exact(expected)


@pytest.mark.parametrize("growth_rate", GROWTH_RATES)
def test_stability_condition_thresholds_are_equation_5(growth_rate):
    """Each StabilityCondition threshold column is Eq. (5) with its Table 1 row.

    ON FAILURE: the code is wrong.
    """
    beta = pd.Series(FINITE_BETA)
    sc = v16.StabilityCondition(growth_rate, beta, pd.Series(np.ones_like(FINITE_BETA)))
    thresholds = sc.instability_thresholds
    assert sorted(thresholds.columns) == INSTABILITIES
    for instability in INSTABILITIES:
        assert thresholds[instability].to_numpy() == exact(
            eq5(FINITE_BETA, *TABLE_1[growth_rate][instability])
        )


# ---------------------------------------------------------------------------
# Classification by StabilityCondition
# ---------------------------------------------------------------------------

# (beta_par, R_p) points at gamma_m = 1e-3 Omega_p, with the instabilities each
# one exceeds, found by hand from Eq. (5) and Table 1:
#   beta = 1:  AIC 1.4364, MM 1.7645, FMW 0.2258, OFI -0.2505
#   beta = 10: AIC 1.1631, MM 1.1376, FMW 0.8607, OFI 0.8641
# AIC and MM are exceeded from above, FMW and OFI from below (Section 1).
CLASSIFICATION = [
    (1.0, 1.0, set(), "Stable"),
    (1.0, 1.6, {"AIC"}, "Between\nAIC &\nMM"),
    (1.0, 3.0, {"AIC", "MM"}, "MM"),
    (10.0, 1.15, {"MM"}, "MM"),
    (1.0, 0.1, {"FMW"}, "Between\nFMW &\nOFI"),
    (10.0, 0.5, {"FMW", "OFI"}, "OFI"),
    (10.0, 0.862, {"OFI"}, "OFI"),
]
CLASSIFICATION_IDS = [f"beta={b}-R={r}" for b, r, _, _ in CLASSIFICATION]
_EXCEEDS = {"AIC": np.greater, "MM": np.greater, "FMW": np.less, "OFI": np.less}


@pytest.mark.parametrize(
    "beta,anisotropy,unstable,label", CLASSIFICATION, ids=CLASSIFICATION_IDS
)
def test_classification_points_straddle_the_published_thresholds(
    beta, anisotropy, unstable, label
):
    """The hand-typed unstable sets agree with Eq. (5) and Table 1 at 1e-3.

    Guards the fixture: each point must sit on the stated side of every threshold,
    or the classification test below cannot tell the stability bins apart.

    ON FAILURE: the fixture no longer separates the stability bins; fix the fixture.
    """
    found = {
        k for k in INSTABILITIES if _EXCEEDS[k](anisotropy, eq5(beta, *TABLE_1[-3][k]))
    }
    assert found == unstable


@pytest.mark.parametrize(
    "beta,anisotropy,unstable,label", CLASSIFICATION, ids=CLASSIFICATION_IDS
)
def test_stability_condition_classifies_by_published_thresholds(
    beta, anisotropy, unstable, label
):
    """is_unstable flags exactly the exceeded thresholds; stability_bin names the region.

    The regions are the module's stability_map: MM wins over AIC and OFI over FM/W.

    ON FAILURE: the code is wrong, unless the author renamed the stability_map labels.
    """
    sc = v16.StabilityCondition(-3, pd.Series([beta]), pd.Series([anisotropy]))
    row = sc.is_unstable.iloc[0]
    assert {k for k in INSTABILITIES if bool(row[k])} == unstable
    assert sc.stability_map[sc.stability_bin.iloc[0]] == label


def test_stability_results_align_with_the_measurement_index():
    """Thresholds, flags and bins keep the index of the input measurements.

    ON FAILURE: the code is wrong.
    """
    index = pd.date_range("2020-01-01", periods=3, freq="min")
    beta = pd.Series([1.0, 1.0, 10.0], index=index)
    anisotropy = pd.Series([3.0, 1.0, 0.5], index=index)
    sc = v16.StabilityCondition(-3, beta, anisotropy)
    pd.testing.assert_index_equal(sc.instability_thresholds.index, index)
    pd.testing.assert_index_equal(sc.is_unstable.index, index)
    pd.testing.assert_index_equal(sc.stability_bin.index, index)
    # Hand-derived from CLASSIFICATION: MM, Stable, OFI.
    labels = [sc.stability_map[b] for b in sc.stability_bin]
    assert labels == ["MM", "Stable", "OFI"]


def test_isotropic_plasma_below_the_fmw_fit_domain_is_stable():
    """At beta_par = 0.1 < c_FMW = 0.543 (Table 1, 1e-3) an isotropic plasma is stable.

    The FM/W threshold is undefined there; R_p = 1 exceeds no other threshold.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityCondition(-3, pd.Series([0.1]), pd.Series([1.0]))
    assert sc.instability_thresholds["FMW"].isna().all()
    assert not sc.is_unstable.to_numpy().any()
    assert sc.stability_map[sc.stability_bin.iloc[0]] == "Stable"


def test_color_norm_centres_each_stability_bin():
    """norm maps bin k to the middle of the k-th of n equal colour intervals.

    Identity: with n bins on [kmin - 1/2, kmax + 1/2], norm(k) = (k - kmin + 1/2) / n,
    so each bin's tick sits at the centre of its colour interval.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityCondition(-3, pd.Series([1.0]), pd.Series([1.0]))
    keys = sorted(sc.stability_map)
    n = len(keys)
    for k in keys:
        expected = (k - keys[0] + 0.5) / n
        assert float(sc.norm(k)) == exact(expected)


@pytest.mark.filterwarnings("error::matplotlib.MatplotlibDeprecationWarning")
def test_colorbar_has_one_colour_and_one_labelled_tick_per_stability_bin():
    """cmap has one colour per bin; cbar_kwargs ticks each bin and labels it by name.

    Matplotlib deprecation warnings are raised as errors, so a colormap lookup
    through an API removed in a later matplotlib fails here before the removal.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityCondition(-3, pd.Series([1.0]), pd.Series([1.0]))
    keys = sorted(sc.stability_map)
    assert sc.cmap.N == len(keys)

    kwargs = sc.cbar_kwargs
    assert kwargs["cmap"].N == len(keys)
    assert list(kwargs["ticks"]) == keys
    assert [kwargs["format"](k, None) for k in keys] == [
        sc.stability_map[k] for k in keys
    ]


# ---------------------------------------------------------------------------
# StabilityContours
# ---------------------------------------------------------------------------


def _matching_growth_rates(instability, beta, ydata):
    """Return the growth rates whose Eq. (5) curve equals ``ydata``."""
    return [
        g
        for g in GROWTH_RATES
        if np.asarray(ydata, dtype=float)
        == exact(eq5(beta, *TABLE_1[g][instability]), nan_ok=True)
    ]


@pytest.mark.parametrize(
    "growth_rate,instability",
    ROWS,
    ids=[f"{g}-{k}" for g, k in ROWS],
)
def test_contours_are_equation_5_for_every_growth_rate(growth_rate, instability):
    """StabilityContours.contours holds Eq. (5) for each Table 1 row.

    ON FAILURE: the code is wrong.
    """
    with np.errstate(invalid="ignore"):
        sc = v16.StabilityContours(WIDE_BETA)
    assert np.asarray(sc.contours.loc[growth_rate, instability], dtype=float) == exact(
        eq5(WIDE_BETA, *TABLE_1[growth_rate][instability]), nan_ok=True
    )


def _plotted_curves(ax, beta):
    """Map each plotted line to (label, growth rate) by matching its data to Eq. (5)."""
    curves = []
    for line in ax.get_lines():
        np.testing.assert_array_equal(line.get_xdata(), beta)
        label = line.get_label()
        matches = _matching_growth_rates(label, beta, line.get_ydata())
        assert len(matches) == 1, (label, matches)
        curves.append((label, matches[0]))
    return curves


def test_plot_contours_draws_every_published_threshold_on_log_axes():
    """With no filter, all 12 Table 1 curves are drawn once, on log-log axes.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(ax)
    assert sorted(_plotted_curves(ax, FINITE_BETA)) == sorted((k, g) for g, k in ROWS)
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")


def test_plot_contours_returns_ax_lines_and_no_colorbar():
    """``plot_contours`` returns ``(ax, lines, None)``, the shared plot order.

    ``lines`` maps each drawn ``(growth_rate, instability)`` to its Line2D,
    every one of which is on the axes. The colorbar slot is None because
    the contours are lines, not a mappable.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    try:
        ret = sc.plot_contours(ax)
        assert isinstance(ret, tuple) and len(ret) == 3
        out_ax, lines, cbar = ret
        assert out_ax is ax
        assert cbar is None
        assert isinstance(lines, dict)
        assert sorted(lines) == sorted((g, k) for g, k in ROWS)
        for line in lines.values():
            assert isinstance(line, Line2D)
            assert any(line is drawn for drawn in ax.lines)
        assert len(lines) == len(ax.lines)
    finally:
        plt.close(fig)


def test_plot_contours_returns_only_the_curves_it_draws():
    """Filtering by growth rate and instability returns only the drawn curves.

    The table-legend placeholders for skipped curves are not returned.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    try:
        out_ax, lines, cbar = sc.plot_contours(
            ax, growth_rate=-3, tk_kind=["MM", "AIC"]
        )
        assert out_ax is ax
        assert cbar is None
        assert sorted(lines) == [(-3, "AIC"), (-3, "MM")]
        assert [line for line in ax.lines] == list(lines.values())
    finally:
        plt.close(fig)


def test_plot_contours_fix_scale_false_keeps_caller_scales():
    """fix_scale=False leaves the axes scales as the caller had them.

    The caller's scales are mixed (log x, linear y), so both a reset to linear
    and a forced log-log would fail.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    sc.plot_contours(ax, fix_scale=False)
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "linear")


@pytest.mark.parametrize("growth_rate", GROWTH_RATES)
def test_growth_rate_draws_only_its_curves(growth_rate):
    """growth_rate selects the four Table 1 curves of one growth rate.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(ax, growth_rate=growth_rate)
    assert sorted(_plotted_curves(ax, FINITE_BETA)) == [
        (k, growth_rate) for k in INSTABILITIES
    ]


@pytest.mark.parametrize(
    "tk_kind,growth_rate,expected",
    [
        ("mm", None, [("MM", g) for g in GROWTH_RATES]),
        (["aic", "OFI"], -3, [("AIC", -3), ("OFI", -3)]),
    ],
    ids=["one-kind-lowercase", "two-kinds-one-gamma"],
)
def test_tk_kind_selects_instabilities_case_insensitively(
    tk_kind, growth_rate, expected
):
    """tk_kind restricts the curves to the named instabilities, in any letter case.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(ax, tk_kind=tk_kind, growth_rate=growth_rate)
    assert sorted(_plotted_curves(ax, FINITE_BETA)) == sorted(expected)


def test_tk_kind_rejects_non_string_entries():
    """A non-string tk_kind entry raises TypeError.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    with pytest.raises(TypeError, match="Unexpected types for `tk_kind`"):
        sc.plot_contours(ax, tk_kind=["MM", 3])


def test_tk_kind_rejects_unknown_instability():
    """An instability name outside AIC, FMW, MM, OFI raises ValueError.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="Unexpected values for `tk_kind`"):
        sc.plot_contours(ax, tk_kind="XYZ")


class LegendTableMismatch(AssertionError):
    """A table-legend handle sits in a row or column that does not describe it."""


@pytest.mark.parametrize(
    "tk_kind, plotted",
    [
        (None, INSTABILITIES),
        ("mm", ["MM"]),
        (["aic", "OFI"], ["AIC", "OFI"]),
    ],
    ids=["all", "one-kind", "two-kinds"],
)
def test_table_legend_rows_and_columns_describe_their_curves(tk_kind, plotted):
    """Each legend handle sits in the row of its instability and column of its gamma.

    Rows and columns are read from where matplotlib draws them. A handle belongs
    to row X when it matches (colour, linestyle) of a plotted curve labelled X, and
    to column 10^g when that curve's data is Eq. (5) with Table 1 at 10^g. When
    ``tk_kind`` leaves instabilities out, their cells are blank and the table
    keeps its layout; matplotlib's warning about a handle it cannot draw is an
    error here.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        sc.plot_contours(ax, tk_kind=tk_kind)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legend = ax.get_legend()

    def centre(artist):
        box = artist.get_window_extent(renderer)
        return (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2

    rows, columns = {}, {}
    for text in legend.get_texts():
        s = text.get_text()
        names = [k for k in INSTABILITIES if k in s]
        gammas = [g for g in GROWTH_RATES if f"${g}$" == s]
        if names:
            rows[names[0]] = centre(text)[1]
        elif gammas:
            columns[gammas[0]] = centre(text)[0]
    assert sorted(rows) == INSTABILITIES and sorted(columns) == GROWTH_RATES

    curves = {}
    for line in ax.get_lines():
        key = (to_hex(line.get_color()), line.get_linestyle())
        label = line.get_label()
        g = _matching_growth_rates(label, FINITE_BETA, line.get_ydata())
        curves.setdefault(key, set()).update((label, gg) for gg in g)

    # Five label cells per column (header plus four rows), four columns.
    assert len(legend.legend_handles) == 20
    handles = [h for h in legend.legend_handles if isinstance(h, Line2D)]
    assert len(handles) == len(GROWTH_RATES) * len(plotted)
    mismatches = []
    for handle in handles:
        x, y = centre(handle)
        row = min(rows, key=lambda k: abs(rows[k] - y))
        column = min(columns, key=lambda g: abs(columns[g] - x))
        described = curves.get((to_hex(handle.get_color()), handle.get_linestyle()))
        if described is None or (row, column) not in described:
            mismatches.append(((row, column), sorted(described or [])))
    if mismatches:
        raise LegendTableMismatch(mismatches)


# ---------------------------------------------------------------------------
# Names, missing values, and contour styles
# ---------------------------------------------------------------------------


def test_user_visible_names_are_instability_growth_rate_and_stability():
    """``insta_params`` rows are named Instability and growth_rate; bins are "Stability".

    ON FAILURE: the code is wrong.
    """
    assert list(v16.insta_params.index.names) == ["Instability", "growth_rate"]
    sc = v16.StabilityCondition(-3, pd.Series([1.0]), pd.Series([1.0]))
    assert sc.stability_bin.name == "Stability"


def test_missing_beta_or_anisotropy_counts_as_stable():
    """A NaN beta or anisotropy is unstable to nothing and lands in the Stable bin.

    The class Notes say a missing value counts as stable.
    ON FAILURE: the code is wrong.
    """
    beta = pd.Series([np.nan, 1.0, np.nan])
    anisotropy = pd.Series([3.0, np.nan, np.nan])

    sc = v16.StabilityCondition(-3, beta, anisotropy)

    assert not sc.is_unstable.to_numpy().any()
    assert [sc.stability_map[b] for b in sc.stability_bin] == ["Stable"] * 3


def test_plot_contours_default_styles():
    """Each curve has its own colour, linestyle and marker, and the documented markers.

    The ``plot_contours`` docstring gives marker size 10, edge width 0.5,
    edge colour black, and a marker on every 10th point.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(ax)

    lines = ax.get_lines()
    assert len(lines) == len(ROWS)
    looks = {
        (to_hex(ln.get_color()), ln.get_linestyle(), ln.get_marker()) for ln in lines
    }
    assert len(looks) == len(ROWS)
    for line in lines:
        assert line.get_markersize() == 10
        assert line.get_markeredgewidth() == 0.5
        assert to_hex(line.get_markeredgecolor()) == to_hex("k")
        assert line.get_markevery() == 10
        assert line.get_label() in INSTABILITIES


def test_plot_contours_style_kwargs_override_every_default():
    """Passed styles, aliases included, replace the defaults on every curve.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(
        ax,
        growth_rate=-3,
        c="r",
        ls=":",
        marker="s",
        ms=4,
        mew=2.0,
        mec="b",
        markevery=5,
        label="mine",
    )

    lines = ax.get_lines()
    assert len(lines) == len(INSTABILITIES)
    for line in lines:
        assert (to_hex(line.get_color()), line.get_linestyle()) == (to_hex("r"), ":")
        assert (line.get_marker(), line.get_markersize()) == ("s", 4)
        assert line.get_markeredgewidth() == 2.0
        assert to_hex(line.get_markeredgecolor()) == to_hex("b")
        assert line.get_markevery() == 5
        assert line.get_label() == "mine"


def test_stability_contours_figure_renders_to_png():
    """All contours with their table legend render to an in-memory PNG.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityContours(FINITE_BETA)
    fig, ax = plt.subplots()
    sc.plot_contours(ax)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    assert buffer.getvalue().startswith(b"\x89PNG\r\n\x1a\n")  # PNG signature


@pytest.mark.parametrize(
    "anisotropy, expected, label",
    [
        (
            3.0,
            {"AIC": True, "FMW": False, "MM": False, "OFI": False},
            "Between\nAIC &\nMM",
        ),
        (5.0, {"AIC": True, "FMW": False, "MM": True, "OFI": False}, "MM"),
    ],
    ids=["R=3", "R=5"],
)
def test_undefined_threshold_is_stable_while_others_hold(anisotropy, expected, label):
    """With FMW undefined, the other instabilities still decide; FMW stays False.

    Table 1 at 1e-3 and beta = 0.1, by hand from Eq. (5): beta - c_FMW = 0.1 -
    0.543 < 0, so FMW is undefined; AIC 1 + 0.437 / 0.103**0.428 = 2.16; MM 1 +
    0.801 / 0.163**0.763 = 4.20; OFI 1 - 1.39 / 0.211**1.005 = -5.64. R = 3
    exceeds AIC only; R = 5 exceeds AIC and MM. Neither is below OFI.

    ON FAILURE: the code is wrong.
    """
    sc = v16.StabilityCondition(-3, pd.Series([0.1]), pd.Series([anisotropy]))

    assert sc.instability_thresholds["FMW"].isna().all()
    assert sc.is_unstable.iloc[0].to_dict() == expected
    assert sc.stability_map[sc.stability_bin.iloc[0]] == label


# ---------------------------------------------------------------------------
# Docstring examples
# ---------------------------------------------------------------------------


def _beta_ani_inst_example_call():
    """The ``(a, b, c)`` keywords of the beta_ani_inst call in its docstring."""
    import re

    match = re.search(
        r">>> beta_ani_inst\(beta, a=(\S+), b=(\S+), c=([^)\s]+)\)",
        v16.beta_ani_inst.__doc__,
    )
    assert match is not None, "beta_ani_inst's Examples no longer call it"
    return tuple(float(x) for x in match.groups())


def test_beta_ani_inst_example_uses_one_published_row():
    """The doctest's (a, b, c) is one row of Table 1, as insta_params holds it.

    Verscharen et al. (2016), doi:10.3847/0004-637X/831/2/128, Table 1. The
    coefficients of different rows (instabilities or growth rates) do not
    combine into a published threshold.

    ON FAILURE: the docstring is wrong.
    """
    call = _beta_ani_inst_example_call()
    rows = {tuple(row) for row in v16.insta_params.loc[:, ["a", "b", "c"]].values}
    assert call in rows


def test_beta_ani_inst_example_output_is_its_call():
    """The doctest's printed thresholds are what its call returns.

    The doctest runs only in the CI doctest workflow, so the default suite runs
    it here.

    ON FAILURE: the docstring is wrong.
    """
    import doctest

    finder = doctest.DocTestFinder()
    (test,) = finder.find(v16.beta_ani_inst, "beta_ani_inst", globs=vars(v16))
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    with np.errstate(invalid="ignore"):
        result = runner.run(test, out=lambda s: None)
    assert result.attempted > 0
    assert result.failed == 0


# ---------------------------------------------------------------------------
# Stability-bin dtype and coverage
# ---------------------------------------------------------------------------


def test_stability_bin_is_an_integer_label():
    """stability_bin has an integer dtype for stable, unstable and missing rows.

    Rows from the hand-derived MM, Stable and OFI cases at 1e-3, plus a NaN row.

    ON FAILURE: the code is wrong.
    """
    beta = pd.Series([1.0, 1.0, 10.0, np.nan])
    anisotropy = pd.Series([3.0, 1.0, 0.5, np.nan])
    sc = v16.StabilityCondition(-3, beta, anisotropy)
    assert pd.api.types.is_integer_dtype(sc.stability_bin)
    assert set(sc.stability_bin) <= set(sc.stability_map)


def _edge_inputs(growth_rate):
    """Beta and anisotropy at every edge of the classification.

    Missing and infinite values, beta at, just above and just below each fit
    offset ``c`` (where Eq. (5) is undefined), the anisotropy exactly on each
    threshold, and values far beyond every threshold.
    """
    params = v16.insta_params.xs(growth_rate, level="growth_rate")
    betas = [np.nan, 0.0, -1.0, np.inf, -np.inf, 1e-12, 1.0, 1e6]
    betas += list(params["c"]) + list(params["c"] + 1e-9) + list(params["c"] - 1e-9)
    beta, anisotropy = [], []
    for b in betas:
        with np.errstate(invalid="ignore", divide="ignore"):
            thresholds = [
                v16.beta_ani_inst(np.array([b]), **row)[0]
                for _, row in params.iterrows()
            ]
        for r in [np.nan, 0.0, -1.0, np.inf, -np.inf, 0.01, 1.0, 100.0] + [
            t for t in thresholds if np.isfinite(t)
        ]:
            beta.append(b)
            anisotropy.append(r)
    return pd.Series(beta), pd.Series(anisotropy)


@pytest.mark.parametrize("growth_rate", [-2, -3, -4])
def test_every_point_falls_in_exactly_one_stability_bin(growth_rate):
    """Every point gets a stability bin; none is left outside every bin.

    ``is_unstable`` is a boolean frame of the four instabilities with no
    missing values, so each row is one of 16 combinations. Stable is no
    instability; otherwise OFI, then FMW (between FMW and OFI), then MM, then
    AIC (between AIC and MM) sets the bin. Checked on edge inputs against that
    rule written independently.

    ON FAILURE: the code is wrong; a point may be left without a bin.
    """
    beta, anisotropy = _edge_inputs(growth_rate)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        sc = v16.StabilityCondition(growth_rate, beta, anisotropy)
    unstable = sc.is_unstable
    assert sorted(unstable.columns) == ["AIC", "FMW", "MM", "OFI"]
    assert all(pd.api.types.is_bool_dtype(d) for d in unstable.dtypes), unstable.dtypes
    code = sc.stability_map_inverse
    expected = np.select(
        [unstable.OFI, unstable.FMW, unstable.MM, unstable.AIC],
        [
            code["OFI"],
            code["Between\nFMW &\nOFI"],
            code["MM"],
            code["Between\nAIC &\nMM"],
        ],
        default=code["Stable"],
    )
    assert pd.api.types.is_integer_dtype(sc.stability_bin)
    assert sc.stability_bin.tolist() == expected.tolist()
    assert set(sc.stability_bin) <= set(sc.stability_map)
