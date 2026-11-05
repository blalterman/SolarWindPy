#!/usr/bin/env python
"""Tests for the adaptive (spiral) mesh in ``solarwindpy.plotting.spiral``.

A spiral mesh starts from a rectangular grid and splits every cell holding more
than ``min_per_bin`` samples into four quadrants at its midpoint, repeating until
no cell is over-full. Cells are half-open, ``[x0, x1) x [y0, y1)``.

Every expectation is derived from ``ROWS``, a table chosen by hand, either by a
worked example written next to it or by ``_refine`` and ``_tally``, a
plain-Python quadtree and counter that share no code with the package. The grid
is 2 x-bins by 3 y-bins with unequal widths, so a transpose or a width error
changes the answer, and one cell splits twice, so a single refinement step is
not enough. What is asserted about a plot is the data handed to matplotlib
(rectangle coordinates, collection arrays, face alphas, contour segments).
"""

import io
import logging
import re
import warnings

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402
from matplotlib.tri import Triangulation  # noqa: E402
from scipy.stats import multivariate_normal  # noqa: E402

from solarwindpy.plotting.base import ClipAxes  # noqa: E402
from solarwindpy.plotting.labels.special import Count  # noqa: E402
from solarwindpy.plotting.spiral import (  # noqa: E402
    SpiralMesh,
    SpiralPlot2D,
)
from tests.tolerances import exact  # noqa: E402

# ---------------------------------------------------------------------------
# Chosen input. No sample lies on a cell edge (the edge convention has its own
# test), and no two samples coincide (coincident samples never stop splitting).
# ---------------------------------------------------------------------------

XEDGES = (0.0, 2.0, 6.0)  # widths 2, 4
YEDGES = (0.0, 1.0, 2.0, 4.0)  # widths 1, 1, 2

# x, y, z
ROWS = [
    (1.0, 0.5, 1.0),  # p0: [0,2)x[0,1)
    (5.0, 1.5, 3.0),  # p1: [2,6)x[1,2)
    (2.5, 2.2, 2.0),  # p2: [2,6)x[2,4) -> [2,4)x[2,3) -> [2,3)x[2,2.5)
    (3.5, 2.7, 5.0),  # p3: [2,6)x[2,4) -> [2,4)x[2,3) -> [3,4)x[2.5,3)
    (5.0, 3.5, 9.0),  # p4: [2,6)x[2,4) -> [4,6)x[3,4)
    (0.5, 3.0, 4.0),  # p5: [0,2)x[2,4)
]
X = pd.Series([r[0] for r in ROWS])
Y = pd.Series([r[1] for r in ROWS])
Z = pd.Series([r[2] for r in ROWS])

# The initial cells, x-major: row i * ny + j is x-bin i, y-bin j.
INITIAL = [
    (0.0, 2.0, 0.0, 1.0),
    (0.0, 2.0, 1.0, 2.0),
    (0.0, 2.0, 2.0, 4.0),
    (2.0, 6.0, 0.0, 1.0),
    (2.0, 6.0, 1.0, 2.0),
    (2.0, 6.0, 2.0, 4.0),
]

# Worked by hand for min_per_bin=1. [2,6)x[2,4) holds p2, p3, p4 and splits at
# (4, 3); its quadrant [2,4)x[2,3) holds p2, p3 and splits at (3, 2.5).
MESH_MIN1 = {
    (0.0, 2.0, 0.0, 1.0),
    (0.0, 2.0, 1.0, 2.0),
    (0.0, 2.0, 2.0, 4.0),
    (2.0, 6.0, 0.0, 1.0),
    (2.0, 6.0, 1.0, 2.0),
    (4.0, 6.0, 2.0, 3.0),
    (4.0, 6.0, 3.0, 4.0),
    (2.0, 4.0, 3.0, 4.0),
    (2.0, 3.0, 2.0, 2.5),
    (3.0, 4.0, 2.0, 2.5),
    (3.0, 4.0, 2.5, 3.0),
    (2.0, 3.0, 2.5, 3.0),
}

# Worked by hand for min_per_bin=2: only [2,6)x[2,4) (3 samples) splits, and
# [2,4)x[2,3) keeps p2 and p3 together (2 is not more than 2).
MESH_MIN2 = set(INITIAL[:5]) | {
    (2.0, 4.0, 2.0, 3.0),
    (4.0, 6.0, 2.0, 3.0),
    (4.0, 6.0, 3.0, 4.0),
    (2.0, 4.0, 3.0, 4.0),
}

FILL = -9999  # the documented out-of-mesh bin number


def _inside(cell, x, y):
    x0, x1, y0, y1 = cell
    return x0 <= x < x1 and y0 <= y < y1


def _grid_cells(xedges, yedges):
    return [
        (xedges[i], xedges[i + 1], yedges[j], yedges[j + 1])
        for i in range(len(xedges) - 1)
        for j in range(len(yedges) - 1)
    ]


def _refine(xedges, yedges, points, min_per_bin):
    """Leaves of a quadtree that splits any cell holding > min_per_bin points."""
    leaves = set()
    todo = _grid_cells(xedges, yedges)
    while todo:
        cell = todo.pop()
        if sum(_inside(cell, x, y) for x, y in points) > min_per_bin:
            x0, x1, y0, y1 = cell
            xh, yh = (x0 + x1) / 2, (y0 + y1) / 2
            todo += [
                (x0, xh, y0, yh),
                (xh, x1, y0, yh),
                (xh, x1, yh, y1),
                (x0, xh, yh, y1),
            ]
        else:
            leaves.add(cell)
    return leaves


def _tally(cells, rows):
    """z values of ``rows`` inside each of ``cells``, in the order of ``cells``."""
    return [[z for x, y, z in rows if _inside(tuple(c), x, y)] for c in cells]


def _cells(mesh):
    return [tuple(float(v) for v in row) for row in mesh]


def _points(rows=ROWS):
    return [(x, y) for x, y, _ in rows]


def _plot(min_per_bin, z=Z, log=False, rows=None):
    """SpiralPlot2D on ROWS with the chosen edges; ``log`` stores 10**x, 10**y.

    SpiralPlot2D raises the top edges (6 -> 6.06, 4 -> 4.04), so the cells
    that reach a top edge, and their split points, shift slightly. No sample
    lies near a split point, so which samples share a cell is unchanged, and
    cells below are named by the hand-worked edges they came from.
    """
    if rows is None:
        x, y = X, Y
    else:
        x = pd.Series([r[0] for r in rows])
        y = pd.Series([r[1] for r in rows])
        z = None if z is None else pd.Series([r[2] for r in rows])
    if log:
        x, y = 10.0**x, 10.0**y
    splot = SpiralPlot2D(
        x,
        y,
        z,
        logx=log,
        logy=log,
        initial_bins=(np.array(XEDGES), np.array(YEDGES)),
        min_per_bin=min_per_bin,
    )
    return splot


def _expected_agg(splot, fcn, rows=ROWS):
    """``fcn`` of the z values in each mesh cell of ``splot``, NaN if empty."""
    return np.array(
        [fcn(zs) if zs else np.nan for zs in _tally(splot.mesh.mesh, rows)],
        dtype=float,
    )


def _rectangles(collection):
    out = []
    for path in collection.get_paths():
        v = path.vertices
        out.append((v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max()))
    return np.array(out)


def _occupied_centers(splot, fcn=np.mean, rows=ROWS):
    """Centres and values of the occupied cells, in linear data space."""
    values = _expected_agg(splot, fcn, rows)
    mesh = splot.mesh.mesh
    x = 0.5 * (mesh[:, 0] + mesh[:, 1])
    y = 0.5 * (mesh[:, 2] + mesh[:, 3])
    if splot.log.x:
        x = 10.0**x
    if splot.log.y:
        y = 10.0**y
    ok = np.isfinite(values)
    return x[ok], y[ok], values[ok]


def _drawn_triangulation(splot, x, y):
    """The occupied centres ``x``, ``y`` triangulated as the contours need.

    Delaunay in plot coordinates (log10 on a log axis), each axis divided by
    its span so neither axis's units dominate the distances; the triangles
    are then placed at ``x``, ``y`` in data units for drawing.
    """
    px = np.log10(x) if splot.log.x else x
    py = np.log10(y) if splot.log.y else y
    triangles = Triangulation(px / np.ptp(px), py / np.ptp(py)).triangles
    return Triangulation(x, y, triangles=triangles)


def _assert_same_segments(qset, ref):
    assert len(qset.allsegs) == len(ref.allsegs)
    for got, want in zip(qset.allsegs, ref.allsegs):
        assert len(got) == len(want)
        for g, w in zip(got, want):
            # Same arrays through the same scipy and matplotlib routines.
            assert np.asarray(g) == exact(w)


def _segments_differ(a, b):
    try:
        _assert_same_segments(a, b)
    except AssertionError:
        return True
    return False


@pytest.fixture(autouse=True)
def _quiet_and_close():
    logging.disable(logging.WARNING)
    yield
    logging.disable(logging.NOTSET)
    plt.close("all")


def test_fixture_separates_orientation_widths_and_depth():
    """ROWS exercises a non-square grid, unequal widths, and a two-level split.

    The quadtree reference also reproduces both hand-worked meshes, so a
    reference wrong in the same way as the package still fails.

    ON FAILURE: the fixture no longer separates x from y, uniform from non-uniform widths, or one refinement step from two; fix the fixture.
    """
    assert len(XEDGES) != len(YEDGES)
    assert len({b - a for a, b in zip(XEDGES, XEDGES[1:])}) > 1
    assert len({b - a for a, b in zip(YEDGES, YEDGES[1:])}) > 1
    assert _grid_cells(XEDGES, YEDGES) == INITIAL
    assert _refine(XEDGES, YEDGES, _points(), 1) == MESH_MIN1
    assert _refine(XEDGES, YEDGES, _points(), 2) == MESH_MIN2
    assert MESH_MIN1 != MESH_MIN2
    # p2 and p3 share a cell at min_per_bin=2 but not at 1.
    shared = [c for c in MESH_MIN2 if _inside(c, 2.5, 2.2) and _inside(c, 3.5, 2.7)]
    assert shared == [(2.0, 4.0, 2.0, 3.0)]


def _unsplit_bin_ids(x, y):
    """``bin_id`` of a ``SpiralMesh`` on the initial grid, with no cell split.

    ``min_per_bin`` is the number of samples, so no cell can hold more and
    the mesh stays the initial grid, row ``i`` being ``INITIAL[i]``.
    """
    mesh = SpiralMesh(
        pd.Series(x),
        pd.Series(y),
        np.array(XEDGES),
        np.array(YEDGES),
        min_per_bin=len(x),
    )
    bin_id = mesh.place_spectra_in_mesh()
    assert [tuple(c) for c in mesh.mesh] == INITIAL  # the fixture: no split
    return bin_id


def _counts(bin_id):
    """Samples per initial cell, from the cell index of each in-mesh sample."""
    ids = np.asarray(bin_id.id)
    return np.bincount(ids[ids != bin_id.fill], minlength=len(INITIAL)).tolist()


class TestCountsAndBinNumbers:
    """Samples are counted and located in half-open cells."""

    def test_counts_per_bin_match_a_hand_count(self):
        """ROWS fall 1, 0, 1, 0, 1, 3 to the six initial cells.

        ON FAILURE: the code is wrong.
        """
        bin_id = _unsplit_bin_ids(X.values, Y.values)
        assert _counts(bin_id) == [1, 0, 1, 0, 1, 3]
        assert _counts(bin_id) == [len(z) for z in _tally(INITIAL, ROWS)]

    def test_cells_are_closed_below_and_open_above(self):
        """A sample on a shared edge belongs to the cell above or right of it.

        (2, 1) sits on the corner shared by four cells and belongs to
        [2,6)x[1,2); (6, 4) sits on the outer top-right corner and belongs to
        no cell.

        ON FAILURE: the code is wrong.
        """
        bin_id = _unsplit_bin_ids(np.array([2.0, 6.0, 0.0]), np.array([1.0, 4.0, 2.0]))
        assert _counts(bin_id) == [0, 0, 1, 0, 1, 0]
        assert np.asarray(bin_id.id).tolist() == [4, bin_id.fill, 2]

    def test_a_sample_on_a_right_edge_does_not_split_the_cell_left_of_it(self):
        """An edge sample counts only in the cell to its right when splitting.

        With ``min_per_bin=1``, [0,2)x[1,2) holds (1, 1.5) and [2,6)x[1,2)
        holds (2, 1.5), on their shared edge. Each cell holds one sample, which
        is not more than 1, so the mesh stays the initial grid; counting the
        edge sample in both cells would split [0,2)x[1,2).

        ON FAILURE: the code is wrong.
        """
        mesh = SpiralMesh(
            pd.Series([1.0, 2.0]),
            pd.Series([1.5, 1.5]),
            np.array(XEDGES),
            np.array(YEDGES),
            min_per_bin=1,
        )
        mesh.generate_mesh()
        assert [tuple(c) for c in mesh.mesh] == INITIAL

    def test_bin_number_is_the_index_of_the_containing_cell(self):
        """Each sample gets the row of the mesh cell containing it; others get -9999.

        Samples outside the grid and NaN samples get the fill value, and every
        cell is visited exactly once.

        ON FAILURE: the code is wrong.
        """
        x = np.append(X.values, [-1.0, 7.0, np.nan])
        y = np.append(Y.values, [0.5, 0.5, 0.5])
        bin_id = _unsplit_bin_ids(x, y)
        assert bin_id.fill == FILL
        assert np.asarray(bin_id.id).tolist() == [0, 4, 5, 5, 5, 2, FILL, FILL, FILL]
        assert np.asarray(bin_id.visited).tolist() == [1] * len(INITIAL)


class TestSpiralMesh:
    """Refinement of the initial grid into the adaptive mesh."""

    def _mesh(self, min_per_bin, rows=ROWS):
        x = pd.Series([r[0] for r in rows])
        y = pd.Series([r[1] for r in rows])
        return SpiralMesh(
            x, y, np.array(XEDGES), np.array(YEDGES), min_per_bin=min_per_bin
        )

    def test_initial_cells_are_ordered_x_major(self):
        """Row ``i * ny + j`` of the initial mesh is x-bin i and y-bin j.

        On this 2 x 3 grid row 1 is [0,2)x[1,2); a y-major layout would give
        [2,6)x[0,1).

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        assert _cells(mesh.initialize_bins()) == INITIAL
        assert _cells(mesh.initial_mesh) == INITIAL

    def test_one_step_splits_overfull_cells_into_quadrants(self):
        """One step replaces each cell over ``min_per_bin`` by its four quadrants.

        At min_per_bin=1 only [2,6)x[2,4) (3 samples) splits, at its midpoint
        (4, 3); its row in the input becomes NaN and the others are untouched.

        ON FAILURE: the code is wrong.
        """
        bins = np.array(INITIAL)
        new, n = SpiralMesh.process_one_spiral_step(bins, X.values, Y.values, 1)
        assert n == 1
        assert set(_cells(new)) == {
            (2.0, 4.0, 2.0, 3.0),
            (4.0, 6.0, 2.0, 3.0),
            (4.0, 6.0, 3.0, 4.0),
            (2.0, 4.0, 3.0, 4.0),
        }
        assert np.isnan(bins[5]).all()
        assert _cells(bins[:5]) == INITIAL[:5]

    def test_a_cell_at_exactly_min_per_bin_is_not_split(self):
        """A cell splits only when it holds strictly more than ``min_per_bin``.

        [2,6)x[2,4) holds 3 samples, so min_per_bin=3 splits nothing.

        ON FAILURE: the code is wrong.
        """
        bins = np.array(INITIAL)
        new, n = SpiralMesh.process_one_spiral_step(bins, X.values, Y.values, 3)
        assert new is None and n == 0
        assert _cells(bins) == INITIAL

    @pytest.mark.parametrize(
        "min_per_bin, hand", [(1, MESH_MIN1), (2, MESH_MIN2), (3, set(INITIAL))]
    )
    def test_generated_mesh_matches_the_hand_worked_mesh(self, min_per_bin, hand):
        """``generate_mesh`` yields the hand-worked leaves, each exactly once.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(min_per_bin)
        mesh.generate_mesh()
        cells = _cells(mesh.mesh)
        assert len(cells) == len(set(cells))
        assert set(cells) == hand

    @pytest.mark.parametrize("min_per_bin", [1, 2])
    def test_generated_mesh_tiles_the_grid_without_overfull_cells(self, min_per_bin):
        """The leaves cover the initial grid's area and none holds > min_per_bin.

        Identity: the areas sum to (6 - 0) * (4 - 0) = 24.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(min_per_bin)
        mesh.generate_mesh()
        m = mesh.mesh
        area = ((m[:, 1] - m[:, 0]) * (m[:, 3] - m[:, 2])).sum()
        assert area == exact(24.0)
        assert max(len(z) for z in _tally(m, ROWS)) <= min_per_bin

    def test_samples_outside_the_grid_do_not_drive_refinement(self):
        """Samples outside the initial grid leave the mesh unchanged.

        Three extra samples at x=10 would split any cell they entered.

        ON FAILURE: the code is wrong.
        """
        outside = [(10.0, 1.5, 0.0), (10.5, 1.5, 0.0), (11.0, 1.5, 0.0)]
        mesh = self._mesh(1, ROWS + outside)
        mesh.generate_mesh()
        assert set(_cells(mesh.mesh)) == MESH_MIN1

    def test_bin_ids_locate_every_sample_in_its_leaf(self):
        """``place_spectra_in_mesh`` numbers each sample by the leaf containing it.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        bin_id = mesh.place_spectra_in_mesh()
        assert bin_id is mesh.bin_id
        assert bin_id.fill == FILL
        for (x, y, _), i in zip(ROWS, bin_id.id):
            assert _inside(tuple(mesh.mesh[i]), x, y)
        assert len(set(bin_id.id)) == len(ROWS)  # min_per_bin=1: one per leaf

    def test_categorical_holds_one_category_per_occupied_leaf(self):
        """``cat`` equals the bin ids, with the occupied leaves as categories.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(2)
        mesh.place_spectra_in_mesh()
        mesh.build_cat()
        assert list(mesh.cat) == list(mesh.bin_id.id)
        assert set(mesh.cat.categories) == set(mesh.bin_id.id)
        assert len(mesh.cat.categories) == 5  # p2, p3 share a leaf

    def test_default_cell_filter_keeps_every_cell(self):
        """With no thresholds set, ``cell_filter`` selects every cell.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        mesh.place_spectra_in_mesh()
        assert mesh.cell_filter.tolist() == [True] * len(MESH_MIN1)

    @pytest.mark.parametrize(
        "thresholds, kept",
        [
            # 12 areas: 0.5 x4, 2 x5, 4 x3. The 0.9 quantile is 4, and only
            # cells strictly below it are kept: the three area-4 cells go.
            ({"size": 0.9}, lambda c, n: (c[1] - c[0]) * (c[3] - c[2]) < 4),
            # Densities: 0 x6, 0.25 x2, 0.5 x2, 2 x2. The 0.5 quantile is 0,
            # so exactly the occupied cells are kept.
            ({"density": 0.5}, lambda c, n: n > 0),
            # The 0.75 quantile is 0.5: only the two occupied 0.5-area cells.
            ({"density": 0.75}, lambda c, n: n > 0 and (c[1] - c[0]) == 1),
            # Both filters must pass.
            (
                {"density": 0.5, "size": 0.9},
                lambda c, n: n > 0 and (c[1] - c[0]) * (c[3] - c[2]) < 4,
            ),
        ],
        ids=["size", "density-median", "density-upper", "both"],
    )
    def test_cell_filter_selects_by_area_and_density_quantiles(self, thresholds, kept):
        """``size`` keeps cells below an area quantile, ``density`` above a density one.

        Worked by hand for the min_per_bin=1 mesh; see the parameter comments.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        mesh.place_spectra_in_mesh()
        mesh.set_cell_filter_thresholds(**thresholds)
        counts = [len(z) for z in _tally(mesh.mesh, ROWS)]
        expected = [kept(c, n) for c, n in zip(_cells(mesh.mesh), counts)]
        assert mesh.cell_filter.tolist() == expected
        assert 0 < sum(expected) < len(expected)

    def test_unknown_filter_threshold_is_rejected(self):
        r"""``set_cell_filter_thresholds`` rejects names other than density and size.

        The error names the rejected keyword and its value. ``KeyError``
        reprs its message, so the newline appears as a literal ``\n``.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        with pytest.raises(KeyError, match="Unexpected kwarg\\\\narea: 0.5"):
            mesh.set_cell_filter_thresholds(area=0.5)


class TestInitialBins:
    """SpiralPlot2D's data transform and initial edges."""

    def test_integer_bins_are_quantile_edges(self):
        """An integer n gives the n + 1 quantiles of the data as edges.

        Data 0..8 with n=4 have quantiles 0, 2, 4, 6, 8; the top edge is then
        raised above 8 so the largest sample lies inside a cell.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series(np.arange(9.0))
        splot = SpiralPlot2D(x, x[::-1].reset_index(drop=True), initial_bins=4)
        for axis in ("x", "y"):
            edges = splot.initial_bins[axis]
            assert edges[:-1].tolist() == [0.0, 2.0, 4.0, 6.0]
            assert edges[-1] > 8.0

    def test_bins_may_differ_per_axis(self):
        """A pair of integers sets the number of bins along x and y separately.

        ON FAILURE: the code is wrong.
        """
        splot = SpiralPlot2D(X, Y, initial_bins=(4, 2))
        assert len(splot.initial_bins["x"]) == 5
        assert len(splot.initial_bins["y"]) == 3

    def test_infinite_samples_do_not_move_quantile_edges(self):
        """Infinite samples are left out when the quantile edges are computed.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series(np.append(np.arange(9.0), np.inf))
        y = pd.Series(np.append(np.arange(9.0), -np.inf))
        splot = SpiralPlot2D(x, y, initial_bins=4)
        assert splot.initial_bins["x"][:-1].tolist() == [0.0, 2.0, 4.0, 6.0]
        assert splot.initial_bins["y"][:-1].tolist() == [0.0, 2.0, 4.0, 6.0]

    def test_explicit_edges_keep_interior_edges_and_contain_every_sample(self):
        """Given edges are used as-is except the top one, which exceeds every sample.

        ON FAILURE: the code is wrong.
        """
        rows = ROWS + [(6.0, 4.0, 0.0)]  # on the given top-right corner
        splot = _plot(1, rows=rows)
        xe, ye = splot.initial_bins["x"], splot.initial_bins["y"]
        assert xe[:-1].tolist() == list(XEDGES[:-1])
        assert ye[:-1].tolist() == list(YEDGES[:-1])
        assert xe[-1] > 6.0 and ye[-1] > 4.0
        # ... so the corner sample is counted.
        assert np.nansum(_expected_agg(splot, len, rows)) == len(rows)

    @pytest.mark.parametrize(
        "bins, error, match",
        [
            # The message names the problem and the type that was passed.
            ((3, 3, 3), ValueError, r"Unrecognized `nbins`\ntype: <class 'tuple'>"),
            (
                [list(XEDGES), list(YEDGES)],
                TypeError,
                "integer or np.ndarrays for initial edges",
            ),
        ],
        ids=["three-axes", "list-edges"],
    )
    def test_malformed_bins_are_rejected(self, bins, error, match):
        """Bins other than an int, or one int or ndarray per axis, raise and say why.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(error, match=match):
            SpiralPlot2D(X, Y, initial_bins=bins)

    def test_log_axes_store_log10_of_the_magnitude(self):
        """With ``logx``/``logy`` the stored coordinates are log10(|value|).

        -100, 10, 1000 become 2, 1, 3.

        ON FAILURE: the code is wrong.
        """
        v = pd.Series([-100.0, 10.0, 1000.0])
        splot = SpiralPlot2D(v, v, logx=True, logy=True, initial_bins=1)
        for axis in ("x", "y"):
            assert splot.data[axis].tolist() == exact([2.0, 1.0, 3.0])

    def test_all_nan_data_is_rejected(self):
        """A plot whose every sample has a NaN raises ValueError.

        ON FAILURE: the code is wrong.
        """
        nan = pd.Series([np.nan, np.nan])
        with pytest.raises(ValueError, match="exclusively NaNs"):
            SpiralPlot2D(nan, nan)


class TestAggregation:
    """``SpiralPlot2D.agg`` reduces z per mesh cell."""

    def test_plot_mesh_is_the_refinement_of_its_initial_bins(self):
        """The plot's mesh is the quadtree refinement of its (extended) edges.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        b = splot.initial_bins
        cells = _cells(splot.mesh.mesh)
        assert len(cells) == len(set(cells))
        assert set(cells) == _refine(b["x"], b["y"], _points(), 1)

    def test_without_z_each_cell_holds_its_sample_count(self):
        """With no z, ``agg`` counts samples per cell, NaN for empty cells.

        At min_per_bin=2 the occupied cells hold 1, 1, 1, 1 and 2 samples.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2, z=None)
        agg = splot.agg()
        assert agg.index.tolist() == list(range(splot.mesh.mesh.shape[0]))
        np.testing.assert_array_equal(agg.values, _expected_agg(splot, len))
        assert sorted(agg.dropna().tolist()) == [1, 1, 1, 1, 2]

    def test_with_z_each_cell_holds_the_mean(self):
        """With varying z, ``agg`` averages z per cell.

        At min_per_bin=3 nothing splits and the top-right cell holds z = 2, 5, 9:
        mean 16/3, which a median (5) would not give.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(3)
        agg = splot.agg()
        assert np.asarray(agg.values) == exact(
            _expected_agg(splot, np.mean), nan_ok=True
        )
        assert agg.tolist() == exact(
            [1.0, np.nan, 4.0, np.nan, 3.0, 16 / 3], nan_ok=True
        )

    def test_explicit_function_is_applied(self):
        """``agg(fcn)`` applies ``fcn`` per cell: the shared cell's max is 5.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        np.testing.assert_array_equal(
            splot.agg("max").values, _expected_agg(splot, max)
        )
        assert 5.0 in splot.agg("max").tolist()

    @pytest.mark.parametrize(
        "lower, upper, keep",
        [(2, None, lambda n: n >= 2), (None, 1, lambda n: n <= 1)],
        ids=["lower", "upper"],
    )
    def test_clim_masks_cells_by_sample_count(self, lower, upper, keep):
        """``set_clim`` limits cells by their number of samples, not their z.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        splot.set_clim(lower, upper)
        counts = [len(z) for z in _tally(splot.mesh.mesh, ROWS)]
        means = _expected_agg(splot, np.mean)
        expected = [m if n and keep(n) else np.nan for m, n in zip(means, counts)]
        assert np.asarray(splot.agg().values) == exact(expected, nan_ok=True)

    def test_cell_filter_masks_aggregated_cells(self):
        """Cells rejected by the mesh's ``cell_filter`` aggregate to NaN.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        splot.mesh.set_cell_filter_thresholds(density=0.75)
        keep = splot.mesh.cell_filter
        means = _expected_agg(splot, np.mean)
        assert 0 < keep.sum() < np.isfinite(means).sum()
        expected = np.where(keep, means, np.nan)
        assert np.asarray(splot.agg().values) == exact(expected, nan_ok=True)

    def test_alim_masks_cells_whose_value_is_outside_the_range(self):
        """After ``set_alim(3, 4)`` a cell keeps its mean iff 3 <= mean <= 4.

        At min_per_bin=2 the occupied cells hold means 1, 4, 3, 3.5 and 9
        (p0; p5; p1; p2 and p3; p4), so 3, 3.5 and 4 survive: both bounds are
        inclusive and both sides mask something.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        splot.set_alim(3.0, 4.0)
        means = _expected_agg(splot, np.mean)
        expected = np.where((means >= 3.0) & (means <= 4.0), means, np.nan)
        assert np.asarray(splot.agg().values) == exact(expected, nan_ok=True)
        assert sorted(splot.agg().dropna().tolist()) == [3.0, 3.5, 4.0]
        assert splot.alim == (3.0, 4.0)

    def test_quantile_alim_masks_cells_outside_the_quantiles_of_the_means(self):
        """``set_alim(0.25, 0.75, kind="quantile")`` keeps means from 3 to 4.

        The occupied cells' means sorted are 1, 3, 3.5, 4, 9 (worked in
        ``test_alim_masks_cells_whose_value_is_outside_the_range``); empty
        cells are NaN and excluded. The 25% and 75% quantiles fall at
        positions 1 and 3: 3 and 4.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        means = _expected_agg(splot, np.mean)
        lo, hi = np.nanquantile(means, [0.25, 0.75])
        assert (lo, hi) == exact((3.0, 4.0))  # hand-computed

        splot.set_alim(0.25, 0.75, kind="quantile")
        expected = np.where((means >= lo) & (means <= hi), means, np.nan)
        assert np.asarray(splot.agg().values) == exact(expected, nan_ok=True)
        assert splot.alim_kind == "quantile"


class TestMakePlot:
    """``make_plot`` draws one rectangle per mesh cell coloured by ``agg``."""

    @pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
    def test_rectangles_are_the_mesh_cells_coloured_by_agg(self, log):
        """Each patch spans its cell (10**edges on log axes) and carries its value.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2, log=log)
        _, ax = plt.subplots()
        ax, coll, _ = splot.make_plot(ax=ax, cbar=False)
        assert isinstance(coll, PolyCollection)
        expected = 10.0**splot.mesh.mesh if log else splot.mesh.mesh
        assert np.asarray(_rectangles(coll)) == exact(expected)
        values = np.ma.filled(np.ma.asarray(coll.get_array(), dtype=float), np.nan)
        assert np.asarray(values) == exact(_expected_agg(splot, np.mean), nan_ok=True)
        scale = "log" if log else "linear"
        assert (ax.get_xscale(), ax.get_yscale()) == (scale, scale)

    def test_log_rectangles_include_a_hand_worked_cell(self):
        """On log axes cell [0,2)x[0,1) is drawn from (1, 1) to (100, 10).

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2, log=True)
        _, coll, _ = splot.make_plot(cbar=False)
        rects = _rectangles(coll).tolist()
        assert any(r == exact([1.0, 100.0, 1.0, 10.0]) for r in rects)

    def test_colorbar_is_returned_for_the_collection(self):
        """With ``cbar=True`` the second return is a Colorbar of the collection.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        _, ax = plt.subplots()
        _, _, cbar = splot.make_plot(ax=ax)
        assert isinstance(cbar, Colorbar)
        assert isinstance(cbar.mappable, PolyCollection)
        assert cbar.mappable in ax.collections

    def test_unexpected_keyword_is_rejected(self):
        """Keywords other than cmap and norm raise ValueError.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        with pytest.raises(ValueError, match="Unexpected kwargs"):
            splot.make_plot(cbar=False, linewidth=2)

    def test_quantile_alim_limits_the_drawn_cells_to_the_bulk(self):
        """With 1%/99% quantile ``alim``, the extreme cells are not coloured.

        With min_per_bin=2 the occupied cells hold p0 (1), p5 (4), p1 (3), p2
        and p3 (mean 3.5), and p4 (9); empty cells are NaN. Sorted: 1, 3,
        3.5, 4, 9. Linear interpolation puts the 1% quantile at position 0.04,
        1 + 0.04 * (3 - 1) = 1.08, and the 99% quantile at 3.96,
        4 + 0.96 * (9 - 4) = 8.8, so the cells holding 1 and 9 are masked.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        means = _expected_agg(splot, np.mean)
        lo, hi = np.nanquantile(means, [0.01, 0.99])
        assert (lo, hi) == exact((1.08, 8.8))  # hand-computed

        splot.set_alim(0.01, 0.99, kind="quantile")
        _, coll, _ = splot.make_plot(cbar=False)
        values = np.ma.filled(np.ma.asarray(coll.get_array(), dtype=float), np.nan)
        expected = np.where((means >= lo) & (means <= hi), means, np.nan)
        assert np.asarray(values) == exact(expected, nan_ok=True)
        assert sorted(values[np.isfinite(values)]) == [3.0, 3.5, 4.0]
        plt.close("all")

    def test_alpha_fcn_makes_small_values_opaque(self):
        """``alpha_fcn`` sets face alpha to (1 - scaled value)**0.25, 0 when empty.

        Per-cell maxima are 1, 3, 4, 5, 9 (source of 0.25: the exponent
        ``make_plot`` logs as "Scaling alpha filter as alpha**0.25"). The cell
        with 5, midway between 1 and 9, gets 0.5**0.25; the cell with 1 is
        opaque; the cell with 9 and the empty cells are transparent.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        _, coll, _ = splot.make_plot(cbar=False, alpha_fcn="max")
        vmax = _expected_agg(splot, max)
        scaled = (vmax - np.nanmin(vmax)) / (np.nanmax(vmax) - np.nanmin(vmax))
        expected = np.nan_to_num((1 - scaled) ** 0.25, nan=0.0)
        alpha = coll.get_facecolors()[:, 3]
        assert alpha == exact(expected)
        by_value = dict(zip(vmax.tolist(), alpha.tolist()))
        assert by_value[5.0] == exact(0.5**0.25)
        assert by_value[1.0] == exact(1.0)
        assert by_value[9.0] == 0.0


class TestPlotContours:
    """``plot_contours`` contours the occupied cells' values at their centres."""

    LEVELS = [2.0, 4.0, 6.0]

    def _contour(self, splot, **kwargs):
        _, ax = plt.subplots()
        kwargs.setdefault("cbar", False)
        return splot.plot_contours(ax=ax, levels=self.LEVELS, **kwargs)

    def test_centres_include_a_hand_worked_cell(self):
        """Cell [0,2)x[0,1) enters the contour input at (1, 0.5) with z = 1.

        ON FAILURE: the fixture no longer places p0 alone in [0,2)x[0,1); fix the fixture.
        """
        x, y, z = _occupied_centers(_plot(1))
        assert (1.0, 0.5, 1.0) in zip(x.tolist(), y.tolist(), z.tolist())
        assert len(z) == len(ROWS)

    @pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
    def test_tricontour_triangulates_the_occupied_centres(self, log):
        """The contours triangulate the occupied cells' centres in plot coordinates.

        Empty cells are excluded; on log axes centres are 10**(mid-edge).
        The triangles are Delaunay's in plot coordinates (log10 on a log
        axis) with each axis scaled to its span, drawn in data units. On log
        axes ROWS' centres triangulate differently in data units, so the
        reference is shown to separate the two; on linear axes they agree.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1, log=log)
        _, qset, _ = self._contour(splot)
        x, y, z = _occupied_centers(splot)
        _, ax = plt.subplots()
        ref = ax.tricontour(_drawn_triangulation(splot, x, y), z, self.LEVELS)
        _assert_same_segments(qset, ref)
        assert list(qset.levels) == self.LEVELS
        if log:
            _, ax = plt.subplots()
            assert _segments_differ(ref, ax.tricontour(x, y, z, self.LEVELS))

    def test_use_contourf_fills_the_same_field(self):
        """``use_contourf=True`` draws filled contours of the same field.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, qset, _ = self._contour(splot, use_contourf=True)
        assert qset.filled
        x, y, z = _occupied_centers(splot)
        _, ax = plt.subplots()
        tri = _drawn_triangulation(splot, x, y)
        _assert_same_segments(qset, ax.tricontourf(tri, z, self.LEVELS))

    def test_colorbar_and_contour_set_are_returned(self):
        """``cbar=True`` returns a Colorbar of the contour set; ``cbar=False`` None.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        ax, qset, cbar = self._contour(splot, cbar=True)
        assert isinstance(cbar, Colorbar) and cbar.mappable is qset
        _, qset, cbar = self._contour(splot, cbar=False)
        assert cbar is None

    @pytest.mark.parametrize(
        "keyword", ["label_levels", "clabel_kwargs", "skip_max_clbl"]
    )
    def test_removed_labelling_keywords_are_rejected(self, keyword):
        """A removed labelling keyword fails loudly instead of being ignored.

        Unknown keywords are forwarded to matplotlib's contour call, whose
        ``Artist.set`` raises ``AttributeError`` naming the keyword.

        ON FAILURE: the code is wrong -- ``plot_contours`` accepts a labelling
        keyword again, or swallows unknown keywords silently.
        """
        with pytest.raises(AttributeError, match=keyword):
            self._contour(_plot(1), **{keyword: True})

    def test_filled_contours_draw_no_labels_and_no_deprecation(self):
        """Filled contours draw no text and emit no ``MatplotlibDeprecationWarning``.

        Matplotlib deprecated ``clabel`` on filled contours in 3.11; the old
        default ``label_levels=True`` labelled ``contourf`` output and warned.

        ON FAILURE: the code is wrong -- something labels the filled contours
        again, or calls another deprecated matplotlib API.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("error", matplotlib.MatplotlibDeprecationWarning)
            ax, qset, _ = self._contour(_plot(1), use_contourf=True)
        assert qset.filled
        assert len(ax.texts) == 0

    @pytest.mark.parametrize(
        "keyword, value",
        [
            ("method", "rbf"),
            ("rbf_neighbors", 50),
            ("rbf_smoothing", 1.0),
            ("rbf_kernel", "cubic"),
            ("grid_resolution", 100),
            ("gaussian_filter_std", 1.5),
            ("interpolation", "cubic"),
            ("nan_aware_filter", True),
        ],
    )
    def test_removed_smoothing_keywords_are_rejected(self, keyword, value):
        """A removed smoothing keyword fails loudly instead of being ignored.

        The adaptive mesh is the smoothing, so the rbf and grid methods and
        their parameters are gone. Unknown keywords are forwarded to
        matplotlib's contour call, whose ``Artist.set`` raises
        ``AttributeError`` naming the keyword.

        ON FAILURE: the code is wrong -- ``plot_contours`` accepts a removed
        smoothing keyword again, or swallows unknown keywords silently.
        """
        _, ax = plt.subplots()
        with pytest.raises(AttributeError, match=keyword):
            _plot(1).plot_contours(
                ax=ax, levels=self.LEVELS, cbar=False, **{keyword: value}
            )


def _unsplit(rows, yedges=YEDGES):
    """SpiralPlot2D on ``rows`` over x-bins [0,2), [2,4), [4,6); no cell splits."""
    x, y, z = (pd.Series(c) for c in zip(*rows))
    return SpiralPlot2D(
        x,
        y,
        z,
        initial_bins=(np.array([0.0, 2.0, 4.0, 6.0]), np.array(yedges)),
        min_per_bin=len(rows),
    )


@pytest.mark.parametrize(
    "rows, yedges, match",
    [
        pytest.param(
            [(1.0, 0.5, 1.0), (5.0, 1.5, 2.0)],
            YEDGES,
            r"at least 3 occupied cells.*got 2",
            id="two-cells",
        ),
        pytest.param(
            [(1.0, 0.5, 1.0), (1.0, 1.5, 2.0), (1.0, 3.0, 3.0)],
            YEDGES,
            r"occupied cells' centers all lie on one line",
            id="vertical-line",
        ),
        pytest.param(
            [(1.0, 0.5, 1.0), (3.0, 0.5, 2.0), (5.0, 0.5, 3.0)],
            YEDGES,
            r"occupied cells' centers all lie on one line",
            id="horizontal-line",
        ),
        pytest.param(
            [(1.0, 0.5, 1.0), (3.0, 1.5, 2.0), (5.0, 2.5, 3.0)],
            (0.0, 1.0, 2.0, 3.0),
            r"occupied cells' centers all lie on one line",
            id="diagonal-line",
        ),
    ],
)
def test_contours_of_cells_that_cannot_be_triangulated_raise_clearly(
    rows, yedges, match
):
    """Too few occupied cells, or centres all on one line, raise ValueError.

    Chosen input: samples in two cells; three cells of the x-bin [0,2) whose
    centres share x = 1; three cells of the y-bin [0,1), across x-bins
    [0,2), [2,4) and [4,6), whose centres share y = 0.5; and three cells on
    the diagonal of unit y-bins, centres (1, 0.5), (3, 1.5), (5, 2.5). No
    triangle can be drawn between them, and the message names why.

    ON FAILURE: the code is wrong.
    """
    splot = _unsplit(rows, yedges)
    with pytest.raises(ValueError, match=match):
        splot.plot_contours(levels=[1.5, 2.5], cbar=False)


def test_contours_of_three_cells_off_one_line_draw_their_triangle():
    """Three occupied cells whose centres are not on one line are contoured.

    Chosen input: cells centred at (1, 0.5), (3, 0.5) and (1, 1.5) holding
    1, 2 and 3. Their one triangle interpolates linearly, so the level 1.5
    crosses the edge from 1 to 2 halfway, at (2, 0.5), and the edge from 1
    to 3 a quarter of the way, at (1, 0.75).

    ON FAILURE: the code is wrong.
    """
    splot = _unsplit([(1.0, 0.5, 1.0), (3.0, 0.5, 2.0), (1.0, 1.5, 3.0)])
    _, qset, _ = splot.plot_contours(levels=[1.5], cbar=False)
    (segments,) = qset.allsegs
    (segment,) = segments
    ends = np.asarray(sorted(map(tuple, segment)))
    assert ends == exact(np.array([[1.0, 0.75], [2.0, 0.5]]))


# ---------------------------------------------------------------------------
# Samples outside the mesh, and integer initial edges.
# ---------------------------------------------------------------------------


class TopEdgeNotAboveData(AssertionError):
    """The top initial edge does not lie above the largest sample."""


@pytest.mark.parametrize(
    "outside, log",
    [((-1.0, 0.5, 100.0), False), ((-np.inf, 0.5, 100.0), True)],
    ids=["left-of-grid", "log-of-zero"],
)
def test_samples_outside_the_mesh_are_excluded_from_the_aggregation(outside, log):
    """A sample outside the mesh is dropped from ``agg``, not an error.

    Source of the contract: ``calculate_bin_number`` logs that out-of-mesh
    samples "will be replaced by NaNs and excluded from the aggregation." In
    the log case the sample's x is 0, whose log10 is -inf: like NaN, it is
    not kept as a row (author ruling #3), so it never reaches the mesh.

    ON FAILURE: the code is wrong.
    """
    splot = _plot(1, z=None, log=log, rows=ROWS + [outside])
    if log:
        assert len(splot.data) == len(ROWS)  # the zero is not a row
    np.testing.assert_array_equal(splot.agg().values, _expected_agg(splot, len))
    assert np.nansum(splot.agg().values) == len(ROWS)


def test_density_filter_ignores_samples_outside_the_mesh():
    """The density filter counts only samples inside the mesh.

    With one extra sample outside the grid, density=0.5 still keeps exactly the
    occupied cells (hand-worked in TestSpiralMesh).

    ON FAILURE: the code is wrong.
    """
    rows = ROWS + [(-1.0, 0.5, 0.0)]
    x = pd.Series([r[0] for r in rows])
    y = pd.Series([r[1] for r in rows])
    mesh = SpiralMesh(x, y, np.array(XEDGES), np.array(YEDGES), min_per_bin=1)
    mesh.place_spectra_in_mesh()
    mesh.set_cell_filter_thresholds(density=0.5)
    occupied = [len(z) > 0 for z in _tally(mesh.mesh, ROWS)]
    assert mesh.cell_filter.tolist() == occupied


def test_integer_edges_are_raised_above_the_largest_sample():
    """Integer edge arrays get a top edge above the data, as float edges do.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([1.0, 10.0])
    splot = SpiralPlot2D(x, x, initial_bins=(np.array([0, 5, 10]), np.array([0, 10])))
    for axis in ("x", "y"):
        if not splot.initial_bins[axis][-1] > 10.0:
            raise TopEdgeNotAboveData(f"{axis}: {splot.initial_bins[axis]}")


# ---------------------------------------------------------------------------
# Progress output of mesh building.
# ---------------------------------------------------------------------------

HEADER = [
    "",
    " Step      N      Elapsed Time",
    "======  =======  ==============",
]
ELAPSED = re.compile(r"\d+:\d{2}:\d{2}(\.\d{6})?")  # str(datetime.timedelta)


def _mesh_on_rows(min_per_bin, rows=ROWS):
    x = pd.Series([r[0] for r in rows])
    y = pd.Series([r[1] for r in rows])
    return SpiralMesh(x, y, np.array(XEDGES), np.array(YEDGES), min_per_bin=min_per_bin)


def _step_rows(lines):
    """(step, number split) of each table row, checking the column layout.

    Columns: step right-aligned in 6, two spaces, number split right-aligned
    in 7, two spaces, the step's elapsed time.
    """
    start = lines.index(HEADER[-1]) + 1
    stop = lines.index("", start)
    rows = []
    for line in lines[start:stop]:
        assert line[6:8] == "  " and line[15:17] == "  ", line
        assert ELAPSED.fullmatch(line[17:]), line
        rows.append((int(line[:6]), int(line[8:15])))
    return rows


def _own_or_warning_records(caplog):
    """Records at WARNING or above, or from ``__main__`` or SolarWindPy, at any level.

    Numba logs DEBUG records of its own whenever it compiles a function, which
    depends on its cache, so those are left out.
    """
    return [
        r
        for r in caplog.records
        if r.levelno >= logging.WARNING
        or r.name == "__main__"
        or r.name.startswith("solarwindpy")
    ]


class TestProgressOutput:
    """Mesh building reports its progress on stderr unless told not to."""

    def test_progress_table_is_written_to_stderr(self, capsys):
        """By default ``generate_mesh`` writes the header, steps and summary to stderr.

        Hand-worked for min_per_bin=1 (see ``MESH_MIN1``): step 0 splits
        [2,6)x[2,4), step 1 splits [2,4)x[2,3), step 2 splits nothing. The
        result is 12 cells for the 6 samples, 6 / 12 = 0.500 per cell.
        Nothing goes to stdout.

        ON FAILURE: the code is wrong.
        """
        _mesh_on_rows(1).generate_mesh()
        out, err = capsys.readouterr()
        assert out == ""
        lines = err.split("\n")
        assert lines[0].startswith("Generating SpiralMesh at ")
        assert lines[1:4] == HEADER
        assert _step_rows(lines) == [(0, 1), (1, 1), (2, 0)]
        after_steps = lines.index("", 4) + 1
        summary = lines[after_steps:]
        assert summary[0].startswith("Completed SpiralMesh at ")
        assert re.fullmatch(r"Elapsed time " + ELAPSED.pattern, summary[1])
        assert summary[2:] == [
            "Split bin threshold 1",
            "Generated 12 bins for 6 spectra (~0.500 spectra per bin)",
            "",
            "",
        ]

    def test_a_mesh_needing_no_split_reports_no_steps(self, capsys):
        """When no cell is over-full, the table has a header and no step rows.

        At min_per_bin=3 the fullest initial cell holds 3 samples.

        ON FAILURE: the code is wrong.
        """
        _mesh_on_rows(3).generate_mesh()
        lines = capsys.readouterr().err.split("\n")
        assert _step_rows(lines) == []
        assert "Generated 6 bins for 6 spectra (~1.000 spectra per bin)" in lines

    def test_progress_false_writes_nothing_and_logs_nothing(self, capfd, caplog):
        """``progress=False`` writes nothing to either stream and logs nothing.

        Logging is re-enabled here, so a WARNING record on any logger would
        reach ``caplog`` and Python's last-resort handler on stderr.

        ON FAILURE: the code is wrong.
        """
        logging.disable(logging.NOTSET)
        with caplog.at_level(logging.DEBUG):
            _mesh_on_rows(1).generate_mesh(progress=False)
        assert capfd.readouterr() == ("", "")
        assert _own_or_warning_records(caplog) == []

    def test_progress_is_not_logged(self, capsys, caplog):
        """With progress on, the table goes to stderr only, not to a logger.

        ON FAILURE: the code is wrong.
        """
        logging.disable(logging.NOTSET)
        with caplog.at_level(logging.DEBUG):
            _mesh_on_rows(1).generate_mesh()
        assert "Elapsed Time" in capsys.readouterr().err
        assert _own_or_warning_records(caplog) == []

    def test_constructor_builds_the_mesh_without_the_progress_table(self, capsys):
        """``SpiralPlot2D`` refines its mesh in the constructor, writing no table.

        ON FAILURE: the code is wrong.
        """
        splot = SpiralPlot2D(
            X, Y, Z, initial_bins=(np.array(XEDGES), np.array(YEDGES)), min_per_bin=1
        )
        err = capsys.readouterr().err
        assert "Elapsed Time" not in err
        assert set(_cells(splot.mesh.mesh)) == _refine(
            splot.initial_bins["x"], splot.initial_bins["y"], _points(), 1
        )

    def test_constructing_and_drawing_log_no_warning(self, caplog):
        """Building a ``SpiralPlot2D`` and drawing it log nothing at WARNING.

        Timing and bin statistics report normal operation, so they are DEBUG
        records. Every point here lies inside the mesh, so nothing is dropped.

        ON FAILURE: the code is wrong.
        """
        logging.disable(logging.NOTSET)
        with caplog.at_level(logging.DEBUG):
            splot = SpiralPlot2D(
                X,
                Y,
                Z,
                initial_bins=(np.array(XEDGES), np.array(YEDGES)),
                min_per_bin=1,
            )
            splot.make_plot()
        plt.close("all")
        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []
        assert any(
            r.name.startswith("solarwindpy") and r.levelno == logging.DEBUG
            for r in caplog.records
        )


# ---------------------------------------------------------------------------
# The top initial edge.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "values, top",
    [
        ([2.0, 10.0], 10.1),  # 10 + 1% of 10
        ([-20.0, -5.0], -4.95),  # -5 + 1% of |-5|: above -5, not 1% below it
        ([-3.0, 0.0], 0.01),  # zero: the 0.01 floor
    ],
    ids=["positive", "negative", "zero"],
)
def test_top_edge_is_the_largest_value_plus_one_percent_of_its_size(values, top):
    """The top initial edge is max + 0.01 * |max|, or 0.01 when max is zero.

    With one quantile bin the edges are the minimum and maximum; only the top
    one moves.

    ON FAILURE: the code is wrong.
    """
    v = pd.Series(values)
    splot = SpiralPlot2D(v, v, initial_bins=1)
    for axis in ("x", "y"):
        assert splot.initial_bins[axis].tolist() == exact([values[0], top])


# ---------------------------------------------------------------------------
# Clipping the data before meshing.
# ---------------------------------------------------------------------------

# 101 samples: one just inside [0,2), 99 at 3, one just inside [4,6). With
# pandas' linear quantiles the 0.01% quantile sits at position
# q * (n - 1) = 0.0001 * 100 = 0.01, between the two smallest samples:
# 1.99 + 0.01 * (3 - 1.99) = 2.0001. The 99.99% quantile sits at 99.99:
# 3 + 0.99 * (4.01 - 3) = 3.9999. Both fall in [2,4), so clipping moves each
# tail sample into the middle cell.
CLIP_X = pd.Series([1.99] + [3.0] * 99 + [4.01])
CLIP_Y = pd.Series([0.5] * 101)  # constant, so clipping leaves y alone
CLIP_EDGES = (np.array([0.0, 2.0, 4.0, 6.0]), np.array([0.0, 1.0]))


@pytest.mark.parametrize(
    "clip, counts",
    [
        (False, [1, 99, 1]),
        (True, [np.nan, 101, np.nan]),
        ("l", [np.nan, 100, 1]),
        ("u", [1, 100, np.nan]),
    ],
    ids=["none", "both", "lower", "upper"],
)
def test_clip_data_moves_the_clipped_tails_into_the_cells_of_the_quantiles(
    clip, counts
):
    """``clip`` clips x and y to their 0.01%/99.99% quantiles before meshing.

    True clips both tails, "l" and "u" one each (worked next to ``CLIP_X``).
    ``min_per_bin=101`` keeps the three initial cells unsplit.

    ON FAILURE: the code is wrong.
    """
    splot = SpiralPlot2D(
        CLIP_X, CLIP_Y, initial_bins=CLIP_EDGES, clip=clip, min_per_bin=101
    )
    assert splot.clip == ClipAxes(x=clip, y=clip, z=False)
    assert splot.agg().tolist() == exact(counts, nan_ok=True)


def test_data_are_not_clipped_by_default():
    """Without ``clip`` the tail samples stay in their own cells.

    ON FAILURE: the code is wrong.
    """
    splot = SpiralPlot2D(CLIP_X, CLIP_Y, initial_bins=CLIP_EDGES, min_per_bin=101)
    assert splot.agg().tolist() == [1, 99, 1]


# ---------------------------------------------------------------------------
# plot_contours: no-argument calls, documented defaults, all options.
# ---------------------------------------------------------------------------


class TestPlotContoursCalls:
    """Calls with no arguments, with every option, and with one level."""

    def test_call_without_arguments_uses_the_documented_defaults(self):
        """With no arguments ``plot_contours`` draws its documented default.

        It makes its own axes and draws line contours of the mean per cell,
        triangulated between the occupied centres at matplotlib's levels,
        with a colorbar.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        ax, qset, cbar = splot.plot_contours()
        assert isinstance(cbar, Colorbar) and cbar.mappable is qset
        assert qset.axes is ax and not qset.filled
        x, y, z = _occupied_centers(splot)
        _, ref_ax = plt.subplots()
        _assert_same_segments(
            qset, ref_ax.tricontour(_drawn_triangulation(splot, x, y), z)
        )

    def test_every_option_reaches_the_drawing(self):
        """Each option changes the drawing as documented.

        ``fcn="max"`` contours the maxima (5 where p2 and p3 share a cell at
        min_per_bin=2); ``levels``, ``cmap``, ``norm`` and ``linestyles``
        reach the contour set; the colorbar is drawn with ``cbar_kwargs`` on
        the given axes.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        levels = [2.0, 4.0, 6.0]
        norm = matplotlib.colors.Normalize(0.0, 10.0)
        linestyles = ["--", ":", "-."]
        _, ax = plt.subplots()
        got_ax, qset, cbar = splot.plot_contours(
            ax=ax,
            fcn="max",
            levels=levels,
            cmap="magma",
            norm=norm,
            linestyles=linestyles,
            cbar_kwargs={"label": "chosen"},
        )
        assert got_ax is ax and qset.axes is ax
        assert list(qset.levels) == levels
        assert qset.get_cmap().name == "magma" and qset.norm is norm
        assert list(qset.linestyles) == linestyles
        assert cbar.mappable is qset and cbar.ax.get_ylabel() == "chosen"

        x, y, z = _occupied_centers(splot, fcn=max)
        assert 5.0 in z.tolist()
        _, ref_ax = plt.subplots()
        tri = _drawn_triangulation(splot, x, y)
        _assert_same_segments(qset, ref_ax.tricontour(tri, z, levels))

    def test_one_level_with_a_colorbar_is_a_clear_error(self):
        """A single contour level with ``cbar=True`` raises a ValueError saying why.

        Without the colorbar the single level is drawn.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        with pytest.raises(ValueError, match="at least 2 contour levels"):
            splot.plot_contours(levels=[3.0])
        _, qset, cbar = splot.plot_contours(levels=[3.0], cbar=False)
        assert cbar is None and list(qset.levels) == [3.0]


# ---------------------------------------------------------------------------
# Contour accuracy against a known density.
# ---------------------------------------------------------------------------

#: Two bivariate normals in (v [km/s], log10 n [cm^-3]), slow and fast wind:
#: weight, mean v, mean log10 n, sd v, sd log10 n, correlation.
_WIND = (
    (0.75, 380.0, np.log10(8.0), 40.0, 0.15, -0.3),
    (0.25, 650.0, np.log10(3.0), 50.0, 0.12, 0.0),
)
#: Each case's evaluation grid in v and in plot y (log10 n, or n).
_WIND_GRID = {
    True: (np.linspace(250.0, 800.0, 120), np.linspace(-0.2, 1.5, 120)),
    False: (np.linspace(250.0, 800.0, 120), np.linspace(0.6, 30.0, 120)),
}


def _wind_laws():
    for w, mv, mu, sv, su, rho in _WIND:
        cov = [[sv**2, rho * sv * su], [rho * sv * su, su**2]]
        yield w, multivariate_normal([mv, mu], cov)


def _wind_sample(size, seed=20261104):
    """``size`` draws of (v, n) from ``_WIND``."""
    rng = np.random.default_rng(seed)
    laws = list(_wind_laws())
    counts = rng.multinomial(size, [w for w, _ in laws])
    draws = np.concatenate(
        [law.rvs(size=k, random_state=rng) for (_, law), k in zip(laws, counts)]
    )
    return draws[:, 0], 10.0 ** draws[:, 1]


def _wind_density(v, n, log):
    """The true density SpiralPlot2D's ``axnorm="d"`` estimates.

    Per (km/s dex) on a log n axis; per (km/s cm^-3) on a linear one, the
    log density times d(log10 n)/dn = 1 / (n ln 10).
    """
    vu = np.stack([v, np.log10(n)], axis=-1)
    pdf = sum(w * law.pdf(vu) for w, law in _wind_laws())
    return pdf if log else pdf / (n * np.log(10.0))


def _misclassified(qset, points, truth):
    """Fraction of ``points`` whose inclusion in the filled ``qset`` != ``truth``."""
    inside = np.zeros(len(points), dtype=bool)
    for path in qset.get_paths():
        if len(path.vertices):
            inside |= path.contains_points(points)
    return np.mean(inside != truth)


@pytest.mark.parametrize("log", [True, False], ids=["log n", "linear n"])
def test_density_contours_misclassify_less_than_data_unit_triangles(log):
    """Contours of a known density are closer to the truth than data-unit ones.

    20,000 (v, n) draws from ``_WIND``, contoured as a density. For the
    levels enclosing 99% and 90% of the draws under the true density, each
    filled region above the level is compared on a 120 x 120 grid in plot
    coordinates with where the true density lies above it. Delaunay
    triangles in data units, as plot_contours drew before (v spans hundreds
    of km/s, n tens of cm^-3), are slivers; scaled plot coordinates must
    misclassify at most 0.9 of their area at each level. At this seed the
    ratio is 0.81 (99%) and 0.47 (90%) on log n, 0.60 and 0.34 on linear n;
    the bound leaves room for Qhull and matplotlib versions. At the 50%
    level the two are within sampling noise at this size on log n, so it
    is not asserted.

    ON FAILURE: the code is wrong -- plot_contours triangulates in data
    units again, or without scaling each axis to its span.
    """
    v, n = _wind_sample(20_000)
    splot = SpiralPlot2D(
        pd.Series(v), pd.Series(n), logy=log, axnorm="d", min_per_bin=50
    )
    agg = splot.agg().to_numpy()
    occupied = np.isfinite(agg)
    cells = splot.mesh.mesh[occupied]
    cx = cells[:, :2].mean(axis=1)
    cy = cells[:, 2:].mean(axis=1)
    if log:
        cy = 10.0**cy

    gv, gy = np.meshgrid(*_WIND_GRID[log])
    gn = 10.0**gy if log else gy
    points = np.column_stack([gv.ravel(), gn.ravel()])
    true_on_grid = _wind_density(points[:, 0], points[:, 1], log)
    # 1.0 lies far above any density here (the peak is below 0.03).
    for level in np.quantile(_wind_density(v, n, log), [0.01, 0.10]):
        truth = true_on_grid > level
        _, ax = plt.subplots()
        _, drawn, _ = splot.plot_contours(
            ax=ax, levels=[level, 1.0], use_contourf=True, cbar=False
        )
        _, ref_ax = plt.subplots()
        data_units = ref_ax.tricontourf(cx, cy, agg[occupied], [level, 1.0])
        got = _misclassified(drawn, points, truth)
        before = _misclassified(data_units, points, truth)
        assert got <= 0.9 * before, (level, got, before)
        plt.close("all")


# ---------------------------------------------------------------------------
# Refinement at the grid's lower edges, the categorical, labels, options.
# ---------------------------------------------------------------------------


def test_samples_on_the_lower_outer_edges_drive_refinement():
    """Samples in the first column and row, and on the grid's lower corner, count.

    [0,2)x[0,1) holds (0, 0) on the outer corner, (0.5, 0.25) and
    (1.5, 0.75): 3 > 2, so it splits at (1, 0.5) into four quadrants, none
    over-full. Without the corner sample it would hold 2 and not split.

    ON FAILURE: the code is wrong.
    """
    rows = [(0.0, 0.0, 0.0), (0.5, 0.25, 0.0), (1.5, 0.75, 0.0)]
    mesh = _mesh_on_rows(2, rows)
    mesh.generate_mesh(progress=False)
    hand = set(INITIAL[1:]) | {
        (0.0, 1.0, 0.0, 0.5),
        (1.0, 2.0, 0.0, 0.5),
        (1.0, 2.0, 0.5, 1.0),
        (0.0, 1.0, 0.5, 1.0),
    }
    assert _refine(XEDGES, YEDGES, _points(rows), 2) == hand
    assert set(_cells(mesh.mesh)) == hand


def test_categorical_leaves_out_samples_outside_the_mesh():
    """``cat`` has no fill-value category; an out-of-mesh sample is NaN in it.

    ON FAILURE: the code is wrong.
    """
    mesh = _mesh_on_rows(2, ROWS + [(-1.0, 0.5, 0.0)])
    mesh.place_spectra_in_mesh(progress=False)
    mesh.build_cat()
    assert FILL not in mesh.cat.categories
    assert pd.isna(mesh.cat[-1])
    assert list(mesh.cat[:-1]) == list(mesh.bin_id.id[:-1])


def test_default_labels_name_the_axes_and_count_without_z():
    """Labels default to "x" and "y"; z is a Count label without z, "z" with it.

    ON FAILURE: the code is wrong.
    """
    counted = SpiralPlot2D(X, Y)
    valued = SpiralPlot2D(X, Y, Z)
    assert (counted.labels.x, counted.labels.y) == ("x", "y")
    assert isinstance(counted.labels.z, Count)
    assert (valued.labels.x, valued.labels.y, valued.labels.z) == ("x", "y", "z")


def test_other_data_is_plotted_by_a_new_plot_whose_mesh_holds_only_it():
    """A plot's data cannot be replaced; a new plot on p0-p4 groups only them.

    The mesh and the z values grouped by it then always come from the same
    samples: 5 points with z summing to 1 + 3 + 2 + 5 + 9 = 20 (ROWS).

    ON FAILURE: the code is wrong.
    """
    splot = _plot(1, rows=ROWS[:5])
    assert splot.grouped.size().sum() == 5
    assert splot.grouped.sum().sum() == exact(20.0)


class TestMakePlotOptions:
    """``make_plot`` passes its options to the drawn collection."""

    def test_fcn_selects_the_aggregation_drawn(self):
        """``make_plot(fcn="max")`` colours each cell by its maximum.

        At min_per_bin=2, p2 and p3 share a cell: max 5, mean 3.5.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        _, coll, _ = splot.make_plot(cbar=False, fcn="max")
        values = np.ma.filled(np.ma.asarray(coll.get_array(), dtype=float), np.nan)
        assert np.asarray(values) == exact(_expected_agg(splot, max), nan_ok=True)
        assert 5.0 in values.tolist() and 3.5 not in values.tolist()

    def test_cmap_and_norm_reach_the_collection(self):
        """``cmap`` and ``norm`` are the collection's colormap and normalisation.

        ON FAILURE: the code is wrong.
        """
        norm = matplotlib.colors.Normalize(0.0, 20.0)
        _, coll, _ = _plot(2).make_plot(cbar=False, cmap="magma", norm=norm)
        assert coll.get_cmap().name == "magma"
        assert coll.norm is norm

    @pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
    def test_axes_limits_span_the_mesh(self, log):
        """The axes show exactly the mesh: x from 0 to 6.06, y from 0 to 4.04.

        6.06 and 4.04 are the raised top edges (6 + 1%, 4 + 1%); on log axes
        the limits are 10 to those powers.

        ON FAILURE: the code is wrong.
        """
        ax, _, _ = _plot(2, log=log).make_plot(cbar=False)
        expected = np.array([[0.0, 6.06], [0.0, 4.04]])
        if log:
            expected = 10.0**expected
        assert np.array([ax.get_xlim(), ax.get_ylim()]) == exact(expected)

    def test_figure_draws_to_an_agg_buffer(self):
        """A SpiralPlot2D figure with a colorbar renders to an in-memory Agg buffer.

        Inside three cells, away from grid lines, the rendered pixel is the
        colour of the cell's mean: p4 alone (9), p0 alone (1), p1 alone (3),
        each mapped through the collection's colormap and norm and rounded to
        8 bits. The figure also saves as PNG.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        _, _, cbar = _plot(2).make_plot(ax=ax)
        fig.canvas.draw()
        rgba = np.asarray(fig.canvas.buffer_rgba())
        coll = cbar.mappable
        height = rgba.shape[0]
        for point, mean in [((4.7, 3.3), 9.0), ((1.3, 0.3), 1.0), ((4.7, 1.3), 3.0)]:
            px, py = ax.transData.transform(point)
            pixel = rgba[int(round(height - py)), int(round(px))]
            colour = np.round(np.array(coll.cmap(coll.norm(mean))) * 255)
            assert pixel.tolist() == colour.astype(int).tolist(), point
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        assert buf.getvalue().startswith(b"\x89PNG\r\n\x1a\n")


# ---------------------------------------------------------------------------
# The mesh, every point's cell and the per-cell counts against a brute-force
# quadtree, on both routes generate_mesh can take: descent (each point moved
# down the tree) and per-cell counting, its fallback for edges descent cannot
# handle. Expected values come from `_ordered_leaves` and `_brute_bin_ids`:
# point-in-rectangle tests with the half-open [x0, x1) x [y0, y1) rule.
# ---------------------------------------------------------------------------

# On the interior edges x=2, y=1, y=2; on the lower outer edges; on the upper
# outer edges x=6, y=4 (outside, cells being half-open); outside; non-finite;
# and on the midpoints (4, 3) of [2,6)x[2,4) and (3, 2.5) of [2,4)x[2,3),
# which the cluster below splits.
EDGE_POINTS = [
    (2.0, 0.5),
    (1.0, 1.0),
    (1.0, 2.0),
    (2.0, 2.0),
    (0.0, 0.5),
    (1.0, 0.0),
    (0.0, 0.0),
    (6.0, 1.0),
    (1.0, 4.0),
    (-1.0, 1.0),
    (3.0, 5.0),
    (np.nan, 1.0),
    (1.0, np.inf),
    (4.0, 3.0),
    (4.0, 2.5),
    (3.0, 2.5),
    (3.0, 2.2),
    (2.5, 3.0),
    (5.0, 3.0),
]


def _descent_points(seed=2026):
    """EDGE_POINTS, a seeded cluster in [2,4)x[2,3), and seeded points on the grid."""
    rng = np.random.default_rng(seed)
    cluster = np.column_stack([rng.uniform(2.0, 4.0, 40), rng.uniform(2.0, 3.0, 40)])
    spread = np.column_stack([rng.uniform(0.0, 6.0, 80), rng.uniform(0.0, 4.0, 80)])
    pts = np.vstack([np.array(EDGE_POINTS), cluster, spread])
    return pd.Series(pts[:, 0]), pd.Series(pts[:, 1])


def _ordered_leaves(xedges, yedges, points, min_per_bin):
    """Brute-force leaves in mesh order.

    The documented split order: the initial cells x-major, then each step's
    unsplit cells in order, a split cell's quarters being lower left, lower
    right, upper right, upper left, at the midpoint.
    """
    cells = _grid_cells(xedges, yedges)
    leaves = []
    while cells:
        split = []
        for cell in cells:
            if sum(_inside(cell, x, y) for x, y in points) > min_per_bin:
                x0, x1, y0, y1 = cell
                xh, yh = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                split += [
                    (x0, xh, y0, yh),
                    (xh, x1, y0, yh),
                    (xh, x1, yh, y1),
                    (x0, xh, yh, y1),
                ]
            else:
                leaves.append(cell)
        cells = split
    return np.array(leaves)


def _brute_bin_ids(leaves, points):
    """Row of the one leaf holding each point, FILL for none."""
    ids = []
    for x, y in points:
        holding = [i for i, c in enumerate(leaves) if _inside(tuple(c), x, y)]
        assert len(holding) <= 1  # leaves are disjoint
        ids.append(holding[0] if holding else FILL)
    return np.array(ids)


# Initial edges that give the same cells as XEDGES on both routes: finite
# float edges take descent; a trailing +inf edge (its column of cells is
# empty, so unsplit and dropped as non-finite) and object-dtype edges take
# the counting fallback.
ROUTES = {
    "descent": np.array(XEDGES),
    "counting-inf-edge": np.append(XEDGES, np.inf),
    "counting-object-edges": np.array(XEDGES, dtype=object),
}


def _route_mesh(route, min_per_bin, x=None, y=None):
    if x is None:
        x, y = _descent_points()
    mesh = SpiralMesh(x, y, ROUTES[route], np.array(YEDGES), min_per_bin=min_per_bin)
    mesh.place_spectra_in_mesh(progress=False)
    return mesh


def test_route_fixture_separates_descent_from_counting():
    """The ROUTES edges select descent and counting, and the points probe edges.

    Uses the private ``SpiralMesh._descent_edges``: which route
    ``generate_mesh`` takes is not public, and only the fixture's validity
    depends on it. The points include one on a split midpoint at both
    refinement depths, and the cluster makes [2,4)x[2,3) split.

    ON FAILURE: the fixture no longer separates descent from per-cell counting, or no longer puts points on split edges; fix the fixture.
    """
    x, y = _descent_points()
    for route, xedges in ROUTES.items():
        mesh = SpiralMesh(x, y, xedges, np.array(YEDGES), min_per_bin=3)
        found, _ = mesh._descent_edges(x.values, y.values)
        assert (found is not None) == (route == "descent"), route
    leaves = {tuple(c) for c in _ordered_leaves(XEDGES, YEDGES, _points_of(x, y), 3)}
    # A leaf's lower-left corner at each midpoint: (4, 3) depth 1, (3, 2.5) depth 2.
    assert any(c[0] == 4.0 and c[2] == 3.0 for c in leaves)
    assert any(c[0] == 3.0 and c[2] == 2.5 for c in leaves)
    assert not any(c[1] == np.inf for c in leaves)


def _points_of(x, y):
    return list(zip(x.tolist(), y.tolist()))


@pytest.mark.parametrize("min_per_bin", [1, 3, 10])
@pytest.mark.parametrize("route", list(ROUTES))
class TestMeshEqualsBruteForce:
    """Mesh rows, ``bin_id`` and counts equal a point-in-rectangle brute force."""

    def test_mesh_rows_are_the_brute_force_leaves_in_split_order(
        self, route, min_per_bin
    ):
        """``mesh`` equals the brute-force leaves, row for row.

        ON FAILURE: the code is wrong.
        """
        mesh = _route_mesh(route, min_per_bin)
        x, y = _descent_points()
        expected = _ordered_leaves(XEDGES, YEDGES, _points_of(x, y), min_per_bin)
        np.testing.assert_array_equal(mesh.mesh, expected)

    def test_bin_id_is_the_row_of_the_leaf_holding_each_point(self, route, min_per_bin):
        """``bin_id.id`` is each point's leaf row, -9999 off the mesh or non-finite.

        ON FAILURE: the code is wrong.
        """
        mesh = _route_mesh(route, min_per_bin)
        x, y = _descent_points()
        pts = _points_of(x, y)
        expected = _brute_bin_ids(
            _ordered_leaves(XEDGES, YEDGES, pts, min_per_bin), pts
        )
        np.testing.assert_array_equal(mesh.bin_id.id, expected)
        assert mesh.bin_id.fill == FILL

    def test_counts_per_cell_are_the_brute_force_counts(self, route, min_per_bin):
        """Points per mesh cell equal a brute-force count and none exceeds the limit.

        ON FAILURE: the code is wrong.
        """
        mesh = _route_mesh(route, min_per_bin)
        x, y = _descent_points()
        pts = _points_of(x, y)
        leaves = _ordered_leaves(XEDGES, YEDGES, pts, min_per_bin)
        expected = [sum(_inside(tuple(c), px, py) for px, py in pts) for c in leaves]
        ids = mesh.bin_id.id
        counts = np.bincount(ids[ids != FILL], minlength=mesh.mesh.shape[0])
        np.testing.assert_array_equal(counts, expected)
        assert max(expected) <= min_per_bin


@pytest.mark.parametrize("seed", [3, 4])
@pytest.mark.parametrize("min_per_bin", [2, 5])
def test_descent_and_counting_give_identical_meshes_and_bin_ids(seed, min_per_bin):
    """On the same points, descent and the counting fallback agree exactly.

    Identity: both routes refine the same initial cells by the same rule.

    ON FAILURE: the code is wrong.
    """
    x, y = _descent_points(seed)
    descent = _route_mesh("descent", min_per_bin, x, y)
    for route in ("counting-inf-edge", "counting-object-edges"):
        counting = _route_mesh(route, min_per_bin, x, y)
        np.testing.assert_array_equal(counting.mesh, descent.mesh)
        np.testing.assert_array_equal(counting.bin_id.id, descent.bin_id.id)


def test_a_new_mesh_on_the_same_object_places_the_points_again():
    """After ``set_data``, ``bin_id`` holds the new points' leaves.

    The placement found while splitting belongs to the data it was found
    for; new data and a new mesh give the brute-force ids of the new data.

    ON FAILURE: the code is wrong.
    """
    mesh = _route_mesh("descent", 3)
    x, y = _descent_points(7)
    mesh.set_data(x, y)
    mesh.place_spectra_in_mesh(progress=False)
    pts = _points_of(x, y)
    expected = _brute_bin_ids(_ordered_leaves(XEDGES, YEDGES, pts, 3), pts)
    np.testing.assert_array_equal(mesh.bin_id.id, expected)


def test_spiral_plot_bin_ids_equal_brute_force_on_its_edges():
    """SpiralPlot2D's mesh and ``bin_id`` are the brute force on its own edges.

    The plot raises the top edges by 1% and drops NaN rows; the brute force
    uses its ``initial_bins`` and the rows of ``data``.

    ON FAILURE: the code is wrong.
    """
    x, y = _descent_points()
    splot = SpiralPlot2D(
        x, y, initial_bins=(np.array(XEDGES), np.array(YEDGES)), min_per_bin=3
    )
    xe, ye = splot.initial_bins["x"], splot.initial_bins["y"]
    pts = _points_of(splot.data.x, splot.data.y)
    leaves = _ordered_leaves(tuple(xe), tuple(ye), pts, 3)
    np.testing.assert_array_equal(splot.mesh.mesh, leaves)
    np.testing.assert_array_equal(splot.mesh.bin_id.id, _brute_bin_ids(leaves, pts))


@pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
def test_drawn_polygons_are_the_mesh_cells_corner_by_corner(log):
    """One closed polygon per mesh cell: (x0,y0), (x1,y0), (x1,y1), (x0,y1).

    Expected: the corners of each row of ``mesh.mesh`` (10**edges on log
    axes), in mesh order, counter-clockwise from the lower left.

    ON FAILURE: the code is wrong.
    """
    x, y = _descent_points()
    if log:
        x, y = 10.0**x, 10.0**y
    splot = SpiralPlot2D(
        x,
        y,
        logx=log,
        logy=log,
        initial_bins=(np.array(XEDGES), np.array(YEDGES)),
        min_per_bin=3,
    )
    _, coll, _ = splot.make_plot(cbar=False)
    assert isinstance(coll, PolyCollection)
    m = 10.0**splot.mesh.mesh if log else splot.mesh.mesh
    paths = coll.get_paths()
    assert len(paths) == m.shape[0]  # one polygon per mesh cell
    for path, (x0, x1, y0, y1) in zip(paths, m):
        v = path.vertices
        np.testing.assert_array_equal(v[:4], [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        np.testing.assert_array_equal(v[-1], v[0])  # closed
    assert coll.get_array().size == m.shape[0]  # one value per polygon
