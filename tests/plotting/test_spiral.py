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

import logging
import warnings

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PatchCollection  # noqa: E402
from matplotlib.colorbar import Colorbar  # noqa: E402
from scipy.interpolate import RBFInterpolator, griddata  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

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
    )
    splot.initialize_mesh(min_per_bin=min_per_bin)
    splot.build_grouped()
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


def _occupied_centers(splot, fcn=np.mean):
    """Centres and values of the occupied cells, in linear data space."""
    values = _expected_agg(splot, fcn)
    mesh = splot.mesh.mesh
    x = 0.5 * (mesh[:, 0] + mesh[:, 1])
    y = 0.5 * (mesh[:, 2] + mesh[:, 3])
    if splot.log.x:
        x = 10.0**x
    if splot.log.y:
        y = 10.0**y
    ok = np.isfinite(values)
    return x[ok], y[ok], values[ok]


def _regular_grid(x, y, resolution):
    return np.meshgrid(
        np.linspace(x.min(), x.max(), resolution),
        np.linspace(y.min(), y.max(), resolution),
    )


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
        """``set_cell_filter_thresholds`` rejects names other than density and size.

        ON FAILURE: the code is wrong.
        """
        mesh = self._mesh(1)
        with pytest.raises(KeyError, match="Unexpected kwarg"):
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
        "bins, error",
        [((3, 3, 3), ValueError), ([list(XEDGES), list(YEDGES)], TypeError)],
        ids=["three-axes", "list-edges"],
    )
    def test_malformed_bins_are_rejected(self, bins, error):
        """Bins other than an int, or one int or ndarray per axis, raise.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(error):
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
        ax, coll = splot.make_plot(ax=ax, cbar=False)
        assert isinstance(coll, PatchCollection)
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
        _, coll = splot.make_plot(cbar=False)
        rects = _rectangles(coll).tolist()
        assert any(r == exact([1.0, 100.0, 1.0, 10.0]) for r in rects)

    def test_colorbar_is_returned_for_the_collection(self):
        """With ``cbar=True`` the second return is a Colorbar of the collection.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(2)
        _, ax = plt.subplots()
        _, cbar = splot.make_plot(ax=ax)
        assert isinstance(cbar, Colorbar)
        assert isinstance(cbar.mappable, PatchCollection)
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
        _, coll = splot.make_plot(cbar=False)
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
        _, coll = splot.make_plot(cbar=False, alpha_fcn="max")
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
    RES = 20

    def _contour(self, splot, **kwargs):
        _, ax = plt.subplots()
        kwargs.setdefault("cbar", False)
        kwargs.setdefault("grid_resolution", self.RES)
        return splot.plot_contours(ax=ax, levels=self.LEVELS, **kwargs)

    def _reference(self, XX, YY, ZZ, filled=False):
        _, ax = plt.subplots()
        fcn = ax.contourf if filled else ax.contour
        return fcn(XX, YY, np.ma.masked_invalid(ZZ), self.LEVELS)

    def test_centres_include_a_hand_worked_cell(self):
        """Cell [0,2)x[0,1) enters the contour input at (1, 0.5) with z = 1.

        ON FAILURE: the fixture no longer places p0 alone in [0,2)x[0,1); fix the fixture.
        """
        x, y, z = _occupied_centers(_plot(1))
        assert (1.0, 0.5, 1.0) in zip(x.tolist(), y.tolist(), z.tolist())
        assert len(z) == len(ROWS)

    @pytest.mark.parametrize("log", [False, True], ids=["linear", "log"])
    def test_tricontour_triangulates_the_occupied_centres(self, log):
        """``method="tricontour"`` contours exactly the occupied cells' centres.

        Empty cells are excluded; on log axes centres are 10**(mid-edge).

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1, log=log)
        _, _, qset = self._contour(splot, method="tricontour")
        x, y, z = _occupied_centers(splot)
        _, ax = plt.subplots()
        _assert_same_segments(qset, ax.tricontour(x, y, z, self.LEVELS))
        assert list(qset.levels) == self.LEVELS

    def test_grid_without_smoothing_is_griddata_on_the_centres(self):
        """``method="grid"`` with no smoothing contours ``griddata`` of the centres.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, _, qset = self._contour(
            splot, method="grid", interpolation="linear", gaussian_filter_std=0
        )
        x, y, z = _occupied_centers(splot)
        XX, YY = _regular_grid(x, y, self.RES)
        ZZ = griddata((x, y), z, (XX, YY), method="linear")
        _assert_same_segments(qset, self._reference(XX, YY, ZZ))

    def test_grid_smoothing_without_nan_awareness_zero_fills(self):
        """``nan_aware_filter=False`` smooths ``griddata`` with NaNs set to 0.

        The reference with another sigma differs, so sigma is shown to reach
        the filter.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, _, qset = self._contour(
            splot,
            method="grid",
            interpolation="linear",
            gaussian_filter_std=1.5,
            nan_aware_filter=False,
        )
        x, y, z = _occupied_centers(splot)
        XX, YY = _regular_grid(x, y, self.RES)
        ZZ = np.nan_to_num(griddata((x, y), z, (XX, YY), method="linear"), nan=0)
        _assert_same_segments(qset, self._reference(XX, YY, gaussian_filter(ZZ, 1.5)))
        assert _segments_differ(qset, self._reference(XX, YY, gaussian_filter(ZZ, 3)))

    def test_nan_aware_smoothing_of_a_complete_grid_is_a_gaussian_filter(self):
        """With no NaNs, the NaN-aware filter is a plain Gaussian filter.

        Nearest-neighbour interpolation leaves no NaN, so normalised
        convolution reduces to ``scipy.ndimage.gaussian_filter``.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, _, qset = self._contour(
            splot,
            method="grid",
            interpolation="nearest",
            gaussian_filter_std=1.5,
            nan_aware_filter=True,
        )
        x, y, z = _occupied_centers(splot)
        XX, YY = _regular_grid(x, y, self.RES)
        ZZ = griddata((x, y), z, (XX, YY), method="nearest")
        _assert_same_segments(qset, self._reference(XX, YY, gaussian_filter(ZZ, 1.5)))

    def test_rbf_uses_the_given_interpolator_parameters(self):
        """``method="rbf"`` contours an RBFInterpolator built with the caller's settings.

        The reference with another smoothing differs, so the parameters are
        shown to reach the interpolator.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        params = {"neighbors": 5, "smoothing": 0.5, "kernel": "cubic"}
        _, _, qset = self._contour(
            splot,
            method="rbf",
            rbf_neighbors=params["neighbors"],
            rbf_smoothing=params["smoothing"],
            rbf_kernel=params["kernel"],
        )
        x, y, z = _occupied_centers(splot)
        XX, YY = _regular_grid(x, y, self.RES)
        pts = np.column_stack([XX.ravel(), YY.ravel()])

        def ref(**kw):
            rbf = RBFInterpolator(np.column_stack([x, y]), z, **kw)
            return self._reference(XX, YY, rbf(pts).reshape(XX.shape))

        _assert_same_segments(qset, ref(**params))
        assert _segments_differ(qset, ref(**{**params, "smoothing": 5.0}))

    def test_default_method_is_rbf(self):
        """With no ``method``, the contours are the default RBF interpolation.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, _, default = self._contour(splot)
        _, _, rbf = self._contour(splot, method="rbf")
        _, _, grid = self._contour(splot, method="grid")
        _assert_same_segments(default, rbf)
        assert _segments_differ(default, grid)

    def test_use_contourf_fills_the_same_field(self):
        """``use_contourf=True`` draws filled contours of the same field.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        _, _, qset = self._contour(
            splot,
            method="grid",
            interpolation="linear",
            gaussian_filter_std=0,
            use_contourf=True,
        )
        assert qset.filled
        x, y, z = _occupied_centers(splot)
        XX, YY = _regular_grid(x, y, self.RES)
        ZZ = griddata((x, y), z, (XX, YY), method="linear")
        _assert_same_segments(qset, self._reference(XX, YY, ZZ, filled=True))

    def test_colorbar_and_contour_set_are_returned(self):
        """``cbar=True`` returns a Colorbar of the contour set; ``cbar=False`` the set.

        ON FAILURE: the code is wrong.
        """
        splot = _plot(1)
        ax, cbar, qset = self._contour(splot, cbar=True)
        assert isinstance(cbar, Colorbar) and cbar.mappable is qset
        _, mappable, qset = self._contour(splot, cbar=False)
        assert mappable is qset

    @pytest.mark.parametrize("method", ["tricontour", "grid"])
    @pytest.mark.parametrize(
        "keyword", ["label_levels", "clabel_kwargs", "skip_max_clbl"]
    )
    def test_removed_labelling_keywords_are_rejected(self, method, keyword):
        """A removed labelling keyword fails loudly instead of being ignored.

        Unknown keywords are forwarded to matplotlib's contour call, whose
        ``Artist.set`` raises ``AttributeError`` naming the keyword.

        ON FAILURE: the code is wrong -- ``plot_contours`` accepts a labelling
        keyword again, or swallows unknown keywords silently.
        """
        with pytest.raises(AttributeError, match=keyword):
            self._contour(_plot(1), method=method, **{keyword: True})

    @pytest.mark.parametrize("method", ["tricontour", "grid"])
    def test_filled_contours_draw_no_labels_and_no_deprecation(self, method):
        """Filled contours draw no text and emit no ``MatplotlibDeprecationWarning``.

        Matplotlib deprecated ``clabel`` on filled contours in 3.11; the old
        default ``label_levels=True`` labelled ``contourf`` output and warned.

        ON FAILURE: the code is wrong -- something labels the filled contours
        again, or calls another deprecated matplotlib API.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("error", matplotlib.MatplotlibDeprecationWarning)
            ax, _, qset = self._contour(_plot(1), method=method, use_contourf=True)
        assert qset.filled
        assert len(ax.texts) == 0

    def test_unknown_method_is_rejected(self):
        """A method other than rbf, grid or tricontour raises ValueError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="Invalid method"):
            self._contour(_plot(1), method="spline")


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
    the log case the sample's x is 0, whose log10 is -inf.

    ON FAILURE: the code is wrong.
    """
    splot = _plot(1, z=None, log=log, rows=ROWS + [outside])
    if log:
        assert splot.data["x"].min() == -np.inf  # the zero reached the mesh
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
