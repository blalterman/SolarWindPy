#!/usr/bin/env python
"""Tests for the orbit-leg histograms in ``solarwindpy.plotting.orbits``.

An orbit is a pair of time intervals, the Inbound and Outbound legs. Every
expectation below is derived from ``ROWS``, a table the test chose by hand
(time, leg, x, y, z), by a pure-Python tally that shares no code with the
package: a right-closed binning rule, ``collections`` and ``statistics``. What
is asserted about a plot is the data handed to matplotlib (``QuadMesh`` values
and cell coordinates, line vertices), never its appearance.
"""

import bisect
import statistics
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402

from solarwindpy.plotting.orbits import OrbitHist1D, OrbitHist2D  # noqa: E402

# ---------------------------------------------------------------------------
# Chosen input. Leg boundaries sit half an hour off the sample times, so no
# sample lies on a boundary and the interval closure convention is never
# tested by accident. Hour 10 lies after both legs and belongs to neither.
# ---------------------------------------------------------------------------

T0 = pd.Timestamp("2020-01-01")


def _at(hours):
    return T0 + pd.Timedelta(hours=hours)


ORBIT = pd.IntervalIndex.from_tuples([(_at(-0.5), _at(4.5)), (_at(4.5), _at(9.5))])

# hour, leg, x, y, z
ROWS = [
    (0, "Inbound", 0.5, 10.5, 0.0),
    (1, "Inbound", 0.5, 10.5, 1.0),
    (2, "Inbound", 1.5, 10.5, 2.0),
    (3, "Inbound", 1.5, 12.0, 3.0),
    (4, "Inbound", 1.5, 12.0, 4.0),
    (5, "Outbound", 0.5, 12.0, 5.0),
    (6, "Outbound", 1.5, 12.0, 6.0),
    (7, "Outbound", 3.0, 10.5, 7.0),
    (8, "Outbound", 3.0, 10.5, 8.0),
    (9, "Outbound", 3.0, 12.0, 9.0),
    (10, None, 0.5, 10.5, 10.0),
]

# Widths (1, 1, 2) and (1, 2): non-uniform, so a missing or doubled bin-width
# factor changes the answer. 3 x-bins by 2 y-bins, so a transpose cannot pass.
XEDGES = (0.0, 1.0, 2.0, 4.0)
YEDGES = (10.0, 11.0, 13.0)
EDGES = {"x": XEDGES, "y": YEDGES}
COLUMN = {"x": 2, "y": 3, "z": 4}
LEGS = ("Inbound", "Outbound")

INDEX = pd.DatetimeIndex([_at(row[0]) for row in ROWS])
X = pd.Series([row[2] for row in ROWS], index=INDEX)
Y = pd.Series([row[3] for row in ROWS], index=INDEX)
Z = pd.Series([row[4] for row in ROWS], index=INDEX)

# Tolerance for means and normalisations: ratios and averages of a handful of
# exactly representable numbers, so only floating-point rounding separates the
# package from the tally.
REL = 1e-12


def _bin(value, edges):
    """Right-closed bin ``(edges[i], edges[i+1]]`` containing ``value``."""
    i = bisect.bisect_left(edges, value) - 1
    return (edges[i], edges[i + 1])


def _groups(*axes):
    """Rows of each leg grouped by their bin along ``axes``."""
    out = defaultdict(list)
    for row in ROWS:
        if row[1] is None:
            continue
        key = tuple(_bin(row[COLUMN[a]], EDGES[a]) for a in axes) + (row[1],)
        out[key].append(row)
    return dict(out)


def _counts(*axes):
    return {k: len(v) for k, v in _groups(*axes).items()}


def _means(column, *axes):
    return {
        k: statistics.fmean(r[COLUMN[column]] for r in v)
        for k, v in _groups(*axes).items()
    }


def _width(b):
    return b[1] - b[0]


def _table(agg):
    """``agg`` as ``{((left, right), ..., leg): value}``, empty bins dropped."""
    out = {}
    for key, value in agg.items():
        if pd.isna(value):
            continue
        *bins, leg = key
        out[tuple((iv.left, iv.right) for iv in bins) + (leg,)] = value
    return out


def _grid(values, leg):
    """(n_y, n_x) array of ``values`` for ``leg``, NaN where a cell is empty."""
    xbins = list(zip(XEDGES[:-1], XEDGES[1:]))
    ybins = list(zip(YEDGES[:-1], YEDGES[1:]))
    return np.array(
        [[values.get((xb, yb, leg), np.nan) for xb in xbins] for yb in ybins]
    )


def _mesh_values(ax):
    qm = ax.collections[0]
    return np.ma.filled(np.ma.asarray(qm.get_array(), dtype=float), np.nan).reshape(
        len(YEDGES) - 1, len(XEDGES) - 1
    )


def _expected_norm(kind):
    """Per-leg normalisation of the 2D counts, from the definitions.

    t: count / max in the leg.   c, r: count / max in the same column, row.
    d: count / (N_leg dx dy).    cd, rd: count / (N in column dy), (N in row dx).
    """
    counts = _counts("x", "y")
    out = {}
    for (xb, yb, leg), c in counts.items():
        leg_n = [v for (_, _, lg), v in counts.items() if lg == leg]
        col_n = [v for (x2, _, lg), v in counts.items() if lg == leg and x2 == xb]
        row_n = [v for (_, y2, lg), v in counts.items() if lg == leg and y2 == yb]
        out[(xb, yb, leg)] = {
            "t": c / max(leg_n),
            "c": c / max(col_n),
            "r": c / max(row_n),
            "d": c / (sum(leg_n) * _width(xb) * _width(yb)),
            "cd": c / (sum(col_n) * _width(yb)),
            "rd": c / (sum(row_n) * _width(xb)),
        }[kind]
    return out


# One cell per normalisation, worked by hand from ROWS, so that a definition
# wrong in both `_expected_norm` and the package still fails.
HAND_NORM = {
    # Inbound (1,2]x(10,11] holds 1; the Inbound maximum is 2.
    "t": (((1.0, 2.0), (10.0, 11.0), "Inbound"), 1 / 2),
    # Outbound column (2,4] holds 2 and 1.
    "c": (((2.0, 4.0), (11.0, 13.0), "Outbound"), 1 / 2),
    # Inbound row (10,11] holds 2 and 1.
    "r": (((1.0, 2.0), (10.0, 11.0), "Inbound"), 1 / 2),
    # 1 of the 5 Outbound samples, in a 2 x 2 cell.
    "d": (((2.0, 4.0), (11.0, 13.0), "Outbound"), 1 / (5 * 2 * 2)),
    # Inbound column (1,2] holds 3 samples; this cell has 2 of them, dy = 2.
    "cd": (((1.0, 2.0), (11.0, 13.0), "Inbound"), 2 / (3 * 2)),
    # Outbound row (11,13] holds 3 samples; this cell has 1 of them, dx = 2.
    "rd": (((2.0, 4.0), (11.0, 13.0), "Outbound"), 1 / (3 * 2)),
}


class LegNormalizationMismatch(AssertionError):
    """A per-leg normalisation disagrees with its definition."""


def _hist2d(**kwargs):
    return OrbitHist2D(ORBIT, X, Y, nbins=[list(XEDGES), list(YEDGES)], **kwargs)


def _hist1d(**kwargs):
    return OrbitHist1D(ORBIT, X, nbins=list(XEDGES), **kwargs)


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_fixture_separates_widths_orientation_and_legs():
    """ROWS exercises non-uniform widths, a non-square grid, and an off-orbit time.

    The hand tally also agrees with a count read directly off ROWS: Inbound
    hours 3 and 4 are the two samples at x=1.5, y=12.

    ON FAILURE: the fixture no longer separates uniform from non-uniform bins, x from y, or in-orbit from off-orbit samples; fix the fixture.
    """
    assert len(set(map(_width, zip(XEDGES[:-1], XEDGES[1:])))) > 1
    assert len(set(map(_width, zip(YEDGES[:-1], YEDGES[1:])))) > 1
    assert len(XEDGES) != len(YEDGES)
    assert any(row[1] is None for row in ROWS)
    assert set(row[1] for row in ROWS if row[1]) == set(LEGS)
    assert _counts("x", "y")[((1.0, 2.0), (11.0, 13.0), "Inbound")] == 2


class TestOrbitAssignment:
    """Each sample is assigned to the orbit leg whose interval contains it."""

    @pytest.mark.parametrize("reverse", [False, True], ids=["sorted", "reversed"])
    def test_each_time_is_assigned_to_the_leg_containing_it(self, reverse):
        """The earlier interval is Inbound, the later Outbound, in either input order.

        ON FAILURE: the code is wrong.
        """
        orbit = ORBIT[::-1] if reverse else ORBIT
        h = OrbitHist1D(orbit, X, nbins=list(XEDGES))
        assigned = h.cut["Orbit"].astype(object).where(h.cut["Orbit"].notna(), None)
        assert assigned.tolist() == [row[1] for row in ROWS]
        assert h.orbit.equals(ORBIT)

    @pytest.mark.parametrize(
        "orbit",
        ["2020-01-01", [0, 1], pd.Index([0, 1]), None],
        ids=["str", "list", "Index", "None"],
    )
    def test_non_interval_orbit_is_rejected(self, orbit):
        """An orbit that is not a ``pd.IntervalIndex`` raises TypeError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError):
            OrbitHist1D(orbit, X, nbins=list(XEDGES))

    def test_set_path_appends_the_orbit_path(self):
        """``set_path(..., orbit=o)`` appends ``o.path`` to the path built without it.

        ``orbit`` is duck-typed: any object with a ``path`` attribute.

        ON FAILURE: the code is wrong.
        """
        h = _hist1d()
        h.set_path("auto")
        base = h.path
        h.set_path("auto", orbit=SimpleNamespace(path=Path("E07")))
        assert h.path == base / "E07"


class TestOrbitHist1D:
    """OrbitHist1D bins x separately for each leg."""

    def test_counts_are_tallied_per_leg(self):
        """With no y, ``agg`` counts the samples of each leg in each x bin.

        The sample outside both legs is in no count.

        ON FAILURE: the code is wrong.
        """
        assert _table(_hist1d().agg()) == _counts("x")

    def test_y_is_averaged_per_leg(self):
        """With y given, ``agg`` returns the mean y of each leg in each x bin.

        ON FAILURE: the code is wrong.
        """
        h = OrbitHist1D(ORBIT, X, y=Z, nbins=list(XEDGES))
        assert _table(h.agg()) == pytest.approx(_means("z", "x"), rel=REL, abs=0)

    @pytest.mark.xfail(
        strict=True,
        raises=TypeError,
        reason=(
            "OrbitHist1D.agg (swp-defect:orbits-hist1d-agg-multiindex-norm) "
            "hands the (x, Orbit)-indexed "
            "aggregate to Hist1D._axis_normalizer, which builds "
            "pd.IntervalIndex from a MultiIndex; TypeError 'is not an "
            "interval'. Remove this marker when OrbitHist1D.agg normalises "
            "each leg separately, as OrbitHist2D.agg does."
        ),
    )
    def test_density_is_normalised_per_leg(self):
        """``axnorm="d"`` gives count / (N_leg dx) in each leg.

        Hand case: 3 of the 5 Outbound samples fall in (2, 4], width 2: 0.3.

        ON FAILURE: (unexpected pass) OrbitHist1D.agg now normalises per leg; drop the xfail marker.
        """
        expected = {
            (xb, leg): c
            / (sum(v for (_, lg), v in _counts("x").items() if lg == leg) * _width(xb))
            for (xb, leg), c in _counts("x").items()
        }
        assert expected[((2.0, 4.0), "Outbound")] == pytest.approx(0.3, rel=REL, abs=0)
        got = _table(_hist1d(axnorm="d").agg())
        assert got == pytest.approx(expected, rel=REL, abs=0)

    def test_make_plot_draws_one_line_per_leg(self):
        """``make_plot`` draws one line per leg at the bin centres, labelled by leg.

        Empty bins are NaN, so a leg's line breaks where it has no data.

        ON FAILURE: the code is wrong.
        """
        ax = _hist1d().make_plot()
        lines = {line.get_label(): line for line in ax.get_lines()}
        assert set(lines) == set(LEGS)

        centres = [(a + b) / 2 for a, b in zip(XEDGES[:-1], XEDGES[1:])]
        counts = _counts("x")
        for leg, line in lines.items():
            np.testing.assert_array_equal(line.get_xdata(), centres)
            expected = [
                counts.get((xb, leg), np.nan) for xb in zip(XEDGES[:-1], XEDGES[1:])
            ]
            np.testing.assert_array_equal(line.get_ydata(), expected)

        legend = sorted(t.get_text() for t in ax.get_legend().get_texts())
        assert legend == sorted(LEGS)

    def test_make_plot_on_log_x_places_lines_at_linear_bin_centres(self):
        """With ``logx``, bins are in log10(x) and the lines sit at 10**(bin centre).

        ON FAILURE: the code is wrong.
        """
        h = OrbitHist1D(ORBIT, 10.0**X, logx=True, nbins=list(XEDGES))
        ax = h.make_plot()
        centres = [10.0 ** ((a + b) / 2) for a, b in zip(XEDGES[:-1], XEDGES[1:])]
        assert {line.get_label() for line in ax.get_lines()} == set(LEGS)
        for line in ax.get_lines():
            # log10 then 10** is a round trip through floating point.
            assert line.get_xdata() == pytest.approx(centres, rel=1e-12, abs=0)

    @pytest.mark.parametrize(
        "kwargs, drawstyle",
        [({}, "steps-mid"), ({"drawstyle": "default"}, "default")],
        ids=["default", "override"],
    )
    def test_make_plot_drawstyle_defaults_to_steps_mid(self, kwargs, drawstyle):
        """Lines are drawn ``steps-mid`` unless the caller passes ``drawstyle``.

        ON FAILURE: the code is wrong, unless the author rejects the documented steps-mid default.
        """
        ax = _hist1d().make_plot(**kwargs)
        assert {line.get_drawstyle() for line in ax.get_lines()} == {drawstyle}


class TestOrbitHist2DAggregation:
    """OrbitHist2D bins (x, y) separately for each leg."""

    def test_counts_are_tallied_per_cell_and_leg(self):
        """With no z, ``agg`` counts each leg's samples in each (x, y) cell.

        ON FAILURE: the code is wrong.
        """
        assert _table(_hist2d().agg()) == _counts("x", "y")

    def test_z_is_averaged_per_cell_and_leg(self):
        """With z given, ``agg`` returns each leg's mean z in each (x, y) cell.

        ON FAILURE: the code is wrong.
        """
        h = OrbitHist2D(ORBIT, X, Y, z=Z, nbins=[list(XEDGES), list(YEDGES)])
        assert _table(h.agg()) == pytest.approx(_means("z", "x", "y"), rel=REL, abs=0)

    @pytest.mark.parametrize("axnorm", ["t", "c", "r"])
    def test_scale_free_normalisation_is_per_leg(self, axnorm):
        """Total, column, and row normalisation divide by maxima within each leg.

        ON FAILURE: the code is wrong.
        """
        expected = _expected_norm(axnorm)
        key, hand = HAND_NORM[axnorm]
        assert expected[key] == pytest.approx(hand, rel=REL, abs=0)
        got = _table(_hist2d(axnorm=axnorm).agg())
        assert got == pytest.approx(expected, rel=REL, abs=0)

    @pytest.mark.xfail(
        strict=True,
        raises=LegNormalizationMismatch,
        reason=(
            "OrbitHist2D.agg (swp-defect:orbits-hist2d-agg-double-norm) "
            "normalises twice: Hist2D.agg "
            "already applies _axis_normalizer across both legs, then the "
            "per-leg transform applies it again, dividing by the bin widths "
            "twice. Exact only for uniform bins; e.g. 'd' gives 0.5 where "
            "2/(5*1*1)=0.4. Remove this marker when OrbitHist2D.agg "
            "normalises the raw per-leg aggregate once."
        ),
    )
    @pytest.mark.parametrize("axnorm", ["d", "cd", "rd"])
    def test_density_normalisation_is_per_leg(self, axnorm):
        """Density, column-density, and row-density use each leg's own counts and widths.

        ON FAILURE: (unexpected pass) OrbitHist2D.agg now normalises once per leg; drop the xfail marker.
        """
        expected = _expected_norm(axnorm)
        key, hand = HAND_NORM[axnorm]
        assert expected[key] == pytest.approx(hand, rel=REL, abs=0)
        got = _table(_hist2d(axnorm=axnorm).agg())
        if got != pytest.approx(expected, rel=REL, abs=0):
            raise LegNormalizationMismatch(f"{axnorm}: got {got}, expected {expected}")


class TestOrbitHist2DPlots:
    """The orbit plots hand each leg's aggregate to ``pcolormesh``."""

    @pytest.mark.parametrize(
        "kind, leg",
        [
            ("Inbound", "Inbound"),
            ("inbound", "Inbound"),
            ("I", "Inbound"),
            ("i", "Inbound"),
            ("Outbound", "Outbound"),
            ("O", "Outbound"),
            ("o", "Outbound"),
        ],
    )
    def test_make_one_plot_meshes_the_requested_leg(self, kind, leg):
        """``make_one_plot(kind)`` meshes that leg's counts on the bin edges.

        Rows of the mesh are y bins and columns are x bins.

        ON FAILURE: the code is wrong.
        """
        ax, _ = _hist2d().make_one_plot(kind, cbar=False)
        np.testing.assert_array_equal(_mesh_values(ax), _grid(_counts("x", "y"), leg))

        xx, yy = np.meshgrid(XEDGES, YEDGES)
        coords = ax.collections[0].get_coordinates()
        np.testing.assert_array_equal(coords[..., 0], xx)
        np.testing.assert_array_equal(coords[..., 1], yy)

    def test_make_one_plot_on_log_axes_meshes_linear_edges(self):
        """With ``logx`` and ``logy``, mesh coordinates are 10**(log-space edges).

        ON FAILURE: the code is wrong.
        """
        h = OrbitHist2D(
            ORBIT,
            10.0**X,
            10.0**Y,
            logx=True,
            logy=True,
            nbins=[list(XEDGES), list(YEDGES)],
        )
        ax, _ = h.make_one_plot("o", cbar=False)
        xx, yy = np.meshgrid(10.0 ** np.array(XEDGES), 10.0 ** np.array(YEDGES))
        coords = np.asarray(ax.collections[0].get_coordinates())
        # log10 then 10** is a round trip through floating point.
        np.testing.assert_allclose(coords[..., 0], xx, rtol=1e-12, atol=0)
        np.testing.assert_allclose(coords[..., 1], yy, rtol=1e-12, atol=0)
        np.testing.assert_array_equal(
            _mesh_values(ax), _grid(_counts("x", "y"), "Outbound")
        )

    @pytest.mark.parametrize(
        "kind",
        [
            "z",
            "sideways",
            pytest.param(
                "",
                marks=pytest.mark.xfail(
                    strict=True,
                    raises=IndexError,
                    reason=(
                        "OrbitHist2D.make_one_plot "
                        "(swp-defect:orbits-make-one-plot-empty-kind) "
                        "indexes kind.lower()[0] "
                        "outside its try, so '' raises IndexError instead of "
                        "\"Unrecognized kind ''\". Remove this marker when the "
                        "empty string is rejected with ValueError."
                    ),
                ),
            ),
        ],
    )
    def test_unrecognised_kind_is_rejected(self, kind):
        """A kind that names no leg raises ValueError naming it.

        ON FAILURE: the code is wrong; for the '' case, an unexpected pass means empty kinds now raise ValueError, so drop that xfail marker.
        """
        with pytest.raises(ValueError, match=f"Unrecognized kind '{kind}'"):
            _hist2d().make_one_plot(kind, cbar=False)

    @pytest.mark.parametrize(
        "call",
        [
            lambda h: h.make_one_plot("Both", cbar=False),
            lambda h: h.make_one_plot("b", cbar=False),
            lambda h: h.make_in_out_both_plot(cbar=False),
        ],
        ids=["one-Both", "one-b", "in_out_both"],
    )
    def test_both_leg_is_disabled(self, call):
        """The combined "Both" leg is switched off and says so.

        ON FAILURE: the code is wrong, unless the author has re-enabled the Both leg; then replace this test with Both-leg tests.
        """
        with pytest.raises(NotImplementedError, match="Disabled"):
            call(_hist2d())

    @pytest.mark.xfail(
        strict=True,
        raises=TypeError,
        reason=(
            "OrbitHist2D._put_agg_on_ax "
            "(swp-defect:orbits-make-cbar-positional-ax) calls "
            "self._make_cbar(pc, ax, ...) but Hist2D._make_cbar takes ax only "
            "as a keyword; TypeError 'takes 2 positional arguments but 3 were "
            "given'. Remove this marker when the call passes ax=ax."
        ),
    )
    @pytest.mark.parametrize(
        "call",
        [
            lambda h: h.make_one_plot("i")[1],
            lambda h: h.make_in_out_plot()[1]["Outbound"],
        ],
        ids=["one", "in_out"],
    )
    def test_colorbar_is_drawn_by_default(self, call):
        """With the default ``cbar=True`` the plot returns a matplotlib Colorbar.

        ON FAILURE: (unexpected pass) _put_agg_on_ax now passes ax by keyword; drop the xfail marker.
        """
        assert isinstance(call(_hist2d()), Colorbar)

    @pytest.mark.parametrize("axnorm", ["c", "r"])
    def test_row_and_column_norms_fix_colour_scale_to_unit_interval(self, axnorm):
        """Row- and column-normalised values lie in (0, 1], so the colour scale is [0, 1].

        ON FAILURE: the code is wrong.
        """
        ax, _ = _hist2d(axnorm=axnorm).make_one_plot("i", cbar=False)
        norm = ax.collections[0].norm
        assert (norm.vmin, norm.vmax) == (0, 1)

    def test_make_in_out_plot_mirrors_inbound_about_a_shared_edge(self):
        """Inbound and Outbound sit side by side, Inbound's x-axis reversed.

        Both axes span the same x range, so the legs meet at one edge
        (perihelion), and each axis meshes its own leg.

        ON FAILURE: the code is wrong.
        """
        axes, _ = _hist2d().make_in_out_plot(cbar=False)
        assert axes.index.tolist() == list(LEGS)
        for leg in LEGS:
            np.testing.assert_array_equal(
                _mesh_values(axes[leg]), _grid(_counts("x", "y"), leg)
            )

        lo, hi = axes["Outbound"].get_xlim()
        assert lo < hi
        assert axes["Inbound"].get_xlim() == (hi, lo)
        assert lo <= XEDGES[0] and XEDGES[-1] <= hi


class TestOrbitHist2DProjection:
    """``project_1d`` turns an OrbitHist2D into the matching OrbitHist1D."""

    @pytest.mark.parametrize(
        "logx, logy",
        [(False, False), (False, True), (True, False)],
        ids=["lin", "logy", "logx"],
    )
    def test_projection_averages_the_other_axis_per_leg(self, logx, logy):
        """Projecting a count histogram onto x averages y in each leg's x bins.

        With ``logy`` the average is of the linear y values; with ``logx`` the
        projection keeps the parent's log-space x bins.

        ON FAILURE: the code is wrong.
        """
        x = 10.0**X if logx else X
        y = 10.0**Y if logy else Y
        h = OrbitHist2D(
            ORBIT, x, y, logx=logx, logy=logy, nbins=[list(XEDGES), list(YEDGES)]
        )
        h1 = h.project_1d("x")

        assert isinstance(h1, OrbitHist1D)
        assert h1.orbit.equals(ORBIT)
        np.testing.assert_array_equal(h1.edges["x"], h.edges["x"])

        if logy:
            expected = {
                k: statistics.fmean(10.0 ** r[COLUMN["y"]] for r in v)
                for k, v in _groups("x").items()
            }
        else:
            expected = _means("y", "x")
        # log10 then 10** is a round trip through floating point.
        assert _table(h1.agg()) == pytest.approx(expected, rel=1e-12, abs=0)

    def test_projection_of_counts_tallies_each_leg(self):
        """``project_counts=True`` gives the per-leg counts along the chosen axis.

        ON FAILURE: the code is wrong.
        """
        h1 = _hist2d().project_1d("y", project_counts=True)
        assert _table(h1.agg()) == _counts("y")

    @pytest.mark.xfail(
        strict=True,
        raises=KeyError,
        reason=(
            "OrbitHist2D.project_1d (swp-defect:orbits-project-1d-log-z) "
            "looks up "
            "self.log._asdict()['z'] when z is set, but LogAxes has only x and "
            "y; KeyError 'z'. Hist2D.project_1d guards this with "
            "`other == 'y'`. Remove this marker when OrbitHist2D.project_1d "
            "applies the same guard."
        ),
    )
    def test_projection_of_z_averages_z_per_leg(self):
        """Projecting a z-weighted histogram onto x averages z in each leg's x bins.

        ON FAILURE: (unexpected pass) OrbitHist2D.project_1d handles z; drop the xfail marker.
        """
        h = OrbitHist2D(ORBIT, X, Y, z=Z, nbins=[list(XEDGES), list(YEDGES)])
        got = _table(h.project_1d("x").agg())
        assert got == pytest.approx(_means("z", "x"), rel=REL, abs=0)
