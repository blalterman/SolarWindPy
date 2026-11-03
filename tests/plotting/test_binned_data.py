# Spent-When: PERMANENT(BinnedData is removed from solarwindpy.plotting)
# Supersedes: none
"""Contract tests for ``solarwindpy.plotting.binned.BinnedData``.

Expected bins come from hand-placed values on a fixed grid, from
``pandas.cut`` with an ``IntervalIndex`` (which bins by the intervals
themselves, not by numeric edges), and from ``numpy.histogram``, whose last
bin also holds its right edge. Edges ``0, 1, 2, 3`` give three bins.

The plot classes' side of the contract is tested here too: a plot given a
``BinnedData`` as ``nbins`` takes its bins and codes by column name, and every
plot constructor checks its caller ``mask`` the way ``BinnedData`` does.
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.instabilities.beta_ani import BetaRPlot
from solarwindpy.plotting.binned import BinnedData
from solarwindpy.plotting.hist1d import Hist1D
from solarwindpy.plotting.hist2d import Hist2D
from solarwindpy.plotting.scatter import Scatter
from solarwindpy.plotting.spiral import SpiralPlot2D
from tests.tolerances import exact

EDGES = np.array([0.0, 1.0, 2.0, 3.0])

# Values on every edge, inside every bin, beyond both ends, +/-inf and NaN.
PROBE = np.array(
    [-np.inf, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, np.inf, np.nan]
)
# (a, b]: an edge belongs to the bin on its left; 0 is in no bin.
RIGHT_CODES = np.array([-1, -1, -1, 0, 0, 1, 1, 2, 2, -1, -1, -1])
# [a, b), the last bin [2, 3]: an edge belongs to the bin on its right.
LEFT_CODES = np.array([-1, -1, 0, 0, 1, 1, 2, 2, 2, -1, -1, -1])


def _frame(values, index=None):
    return pd.DataFrame({"x": values}, index=index)


class TestCodes:
    """Each row's code is the position of the bin holding its value."""

    @pytest.mark.parametrize(
        "bins, expected",
        [
            (EDGES, RIGHT_CODES),
            (pd.IntervalIndex.from_breaks(EDGES, closed="right"), RIGHT_CODES),
            (pd.IntervalIndex.from_breaks(EDGES, closed="left"), LEFT_CODES),
        ],
        ids=["edges", "right-closed", "left-closed"],
    )
    def test_codes_place_edges_infinities_and_nan_by_closure(self, bins, expected):
        """Values on edges, beyond the ends, at +/-inf and NaN get the hand codes.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(_frame(PROBE), {"x": bins})
        np.testing.assert_array_equal(b.codes("x"), expected)

    def test_right_closed_categorical_equals_pandas_cut(self):
        """Right-closed bins match ``pd.cut`` by the same intervals, index and name.

        ON FAILURE: the code is wrong.
        """
        intervals = pd.IntervalIndex.from_breaks(EDGES, closed="right")
        values = pd.Series(PROBE, index=pd.RangeIndex(10, 22), name="x")
        b = BinnedData(values.to_frame(), {"x": intervals})
        expected = pd.cut(values, intervals)
        pd.testing.assert_series_equal(b.categorical("x"), expected, check_exact=True)

    def test_left_closed_categorical_is_pandas_cut_with_the_last_edge_closed(self):
        """Left-closed bins match ``pd.cut`` except that 3 joins the last bin.

        ON FAILURE: the code is wrong.
        """
        intervals = pd.IntervalIndex.from_breaks(EDGES, closed="left")
        values = pd.Series(PROBE, name="x")
        b = BinnedData(values.to_frame(), {"x": intervals})
        expected = pd.cut(values, intervals)
        expected[values == 3.0] = intervals[-1]
        pd.testing.assert_series_equal(b.categorical("x"), expected, check_exact=True)
        assert b.categorical("x")[values == 3.0].tolist() == [intervals[-1]]

    def test_left_closed_counts_equal_numpy_histogram(self):
        """Counting codes per bin reproduces ``np.histogram`` on the finite values.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(20261102)
        # Integers on and between the edges, so many values sit on an edge.
        values = np.r_[rng.integers(-1, 5, 500).astype(float), PROBE]
        b = BinnedData(
            _frame(values), {"x": pd.IntervalIndex.from_breaks(EDGES, closed="left")}
        )
        codes = b.codes("x")
        expected, _ = np.histogram(values[np.isfinite(values)], bins=EDGES)
        got = np.bincount(codes[codes >= 0], minlength=EDGES.size - 1)
        np.testing.assert_array_equal(got, expected)

    def test_log_bins_log10_of_the_absolute_value(self):
        """With ``log``, -10, 100 and 0.5 are binned at 1, 2 and -0.30.

        ON FAILURE: the code is wrong.
        """
        frame = _frame([-10.0, 100.0, 0.5])
        b = BinnedData(frame, {"x": [-1.0, 0.0, 1.0, 2.0]}, log={"x": True})
        np.testing.assert_array_equal(b.codes("x"), [1, 2, 0])
        assert b.log_of("x") is True

    @pytest.mark.parametrize(
        "clip, expected", [(False, 2), (True, 1)], ids=["unclipped", "clipped"]
    )
    def test_clip_bins_an_outlier_at_its_quantile(self, clip, expected):
        """``clip`` bins 1000 at the 99.99th percentile, 999.009, in (5, 999.5].

        x = 0..9 and 1000; numpy's linear quantile at 0.9999 is
        9 + 0.999 * 991. The two parametrizations differ only in clipping.
        ON FAILURE: the code is wrong.
        """
        values = np.r_[np.arange(10.0), 1000.0]
        b = BinnedData(
            _frame(values), {"x": [-1.0, 5.0, 999.5, 1001.0]}, clip={"x": clip}
        )
        assert b.codes("x")[-1] == expected
        assert b.clip_of("x") is clip


class TestCodeType:
    """Codes take one byte per row up to 127 bins."""

    @pytest.mark.parametrize(
        "n_bins, dtype", [(127, np.int8), (128, np.int16)], ids=["127", "128"]
    )
    def test_code_dtype_widens_above_127_bins(self, n_bins, dtype):
        """127 bins give int8 codes; 128 give int16; the top bin's code survives.

        ON FAILURE: the code is wrong.
        """
        edges = np.arange(n_bins + 1.0)
        values = np.arange(n_bins) + 0.5
        b = BinnedData(_frame(values), {"x": edges})
        codes = b.codes("x")
        assert codes.dtype == dtype
        np.testing.assert_array_equal(codes, np.arange(n_bins))

    def test_writing_into_codes_raises(self):
        """Codes and edges are read-only, whole or taken on rows.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(_frame(PROBE), {"x": EDGES})
        on = np.isfinite(PROBE)
        for arr in (b.codes("x"), b.codes("x", on=on), b.edges("x")):
            with pytest.raises(ValueError, match="read-only"):
                arr[0] = 1


class TestErrors:
    """Bad bins, columns and masks raise."""

    @pytest.mark.parametrize("spec", [10, np.int64(10), "auto", "knuth"])
    def test_bin_rules_are_refused(self, spec):
        """An integer or string bin rule raises: only explicit bins are shared.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="explicit bin edges or an IntervalIndex"):
            BinnedData(_frame(PROBE), {"x": spec})

    def test_unknown_column_raises_key_error(self):
        """Binning, or asking for, a column that is not there raises KeyError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(KeyError, match="q"):
            BinnedData(_frame(PROBE), {"q": EDGES})
        b = BinnedData(_frame(PROBE), {"x": EDGES})
        for method in (b.codes, b.categorical, b.edges, b.intervals, b.log_of):
            with pytest.raises(KeyError, match="q"):
                method("q")


class TestSnapshot:
    """A BinnedData keeps the values it was built from."""

    def test_editing_the_source_in_place_changes_nothing(self):
        """After ``frame`` is edited in place, codes, bins and index are unchanged.

        Values and labels are both edited; the frame checks prove the edits
        landed.
        ON FAILURE: the code is wrong.
        """
        frame = pd.DataFrame({"x": PROBE.copy(), "y": np.arange(PROBE.size)})
        b = BinnedData(frame, {"x": EDGES})
        frame.loc[:, "x"] = 2.5
        frame.iloc[3, 0] = np.nan
        frame.index = pd.RangeIndex(100, 100 + PROBE.size)

        assert frame["x"].isna().sum() == 1
        assert frame.index[0] == 100
        np.testing.assert_array_equal(b.codes("x"), RIGHT_CODES)
        lefts = b.categorical("x").map(lambda iv: iv.left, na_action="ignore")
        expected = np.where(RIGHT_CODES >= 0, EDGES[RIGHT_CODES], np.nan)
        np.testing.assert_array_equal(lefts.astype(float).to_numpy(), expected)
        assert b.columns == ("x",)
        assert b.index.equals(pd.RangeIndex(PROBE.size))


class TestMask:
    """A mask is aligned by label; rows it excludes get code -1."""

    def test_rows_outside_the_mask_get_code_minus_one(self):
        """Masked-out rows are -1; kept rows keep their hand codes.

        The mask's index is the frame's, reversed, so it is aligned by label.
        ON FAILURE: the code is wrong.
        """
        index = pd.Index(list("abcdefghijkl"))
        keep = np.arange(PROBE.size) % 2 == 0
        mask = pd.Series(keep, index=index)[::-1]
        b = BinnedData(_frame(PROBE, index), {"x": EDGES}, mask=mask)
        np.testing.assert_array_equal(b.codes("x"), np.where(keep, RIGHT_CODES, -1))

    def test_rows_are_taken_by_label(self):
        """``on`` takes rows by label, in the order given.

        ON FAILURE: the code is wrong.
        """
        index = pd.Index(list("abcdefghijkl"))
        b = BinnedData(_frame(PROBE, index), {"x": EDGES})
        got = b.categorical("x", on=pd.Index(["h", "d"]))
        assert got.index.tolist() == ["h", "d"]
        assert got.tolist() == [pd.Interval(2.0, 3.0), pd.Interval(0.0, 1.0)]
        with pytest.raises(ValueError, match="subset"):
            b.codes("x", on=pd.Index(["z"]))

    def test_a_mask_missing_a_label_raises(self):
        """A missing label is never read as False.

        ON FAILURE: the code is wrong.
        """
        mask = pd.Series(True, index=pd.RangeIndex(PROBE.size - 1))
        with pytest.raises(ValueError, match="lacks 1 label"):
            BinnedData(_frame(PROBE), {"x": EDGES}, mask=mask)

    @pytest.mark.parametrize("dtype", [object, "boolean"])
    def test_a_mask_holding_nan_raises(self, dtype):
        """NaN in the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        values = [True] * (PROBE.size - 1) + [None]
        mask = pd.Series(values, dtype=dtype)
        with pytest.raises(ValueError, match="NaN"):
            BinnedData(_frame(PROBE), {"x": EDGES}, mask=mask)


# ---------------------------------------------------------------------------
# Through the plots: a shared BinnedData via nbins, and the caller mask
# ---------------------------------------------------------------------------

# Six labelled points on the grid 0, 1, 2, 3 per axis. Point "f" has no x,
# so no plot keeps it. Points "a" and "e" share the bin (0, 1] x (0, 1].
LABELS = list("abcdef")
POINTS = pd.DataFrame(
    {
        "vx": [0.5, 1.5, 2.5, 0.5, 0.5, np.nan],
        "vy": [0.5, 0.5, 1.5, 2.5, 0.5, 0.5],
    },
    index=LABELS,
)
# Drops "b": the plot keeps a, c, d and e.
MASK = pd.Series([True, False, True, True, True, True], index=LABELS)
KEPT = ["a", "c", "d", "e"]
GRID = {"vx": EDGES, "vy": EDGES}


def _interval(i):
    return pd.Interval(EDGES[i], EDGES[i + 1], closed="right")


class TestSharedBinnedData:
    """A plot given ``nbins=BinnedData`` takes its bins and codes from it."""

    def test_shared_codes_are_taken_by_name_on_the_plots_rows(self):
        """Hist2D(vx, vy, nbins=b, mask=m) counts the kept points in their bins.

        a and e fall in (0, 1] x (0, 1]; c in (2, 3] x (1, 2]; d in
        (0, 1] x (2, 3]. Cut and data hold exactly the kept labels.
        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        h = Hist2D(POINTS.vx, POINTS.vy, nbins=b, mask=MASK)
        assert h.data.index.tolist() == KEPT
        assert h.cut.index.tolist() == KEPT
        expected = pd.Series(
            [2, 1, 1],
            index=pd.MultiIndex.from_tuples(
                [
                    (_interval(0), _interval(0)),
                    (_interval(0), _interval(2)),
                    (_interval(2), _interval(1)),
                ],
                names=["x", "y"],
            ),
        )
        got = h.agg().dropna()
        assert got.index.tolist() == expected.index.tolist()
        assert got.to_numpy() == exact(expected.to_numpy(dtype=float))

    def test_rows_the_binned_data_excludes_are_in_no_bin_of_the_plot(self):
        """A row b's own mask drops is kept in data, but in no bin.

        b drops "c"; the plot keeps c (its x, y are finite) with NaN bins,
        exactly as a value outside the edges. That shows the plot uses b's
        codes, not bins of its own.
        ON FAILURE: the code is wrong.
        """
        b_mask = pd.Series([label != "c" for label in LABELS], index=LABELS)
        b = BinnedData(POINTS, GRID, mask=b_mask)
        h = Hist2D(POINTS.vx, POINTS.vy, nbins=b, mask=MASK)
        assert h.data.index.tolist() == KEPT
        assert h.cut.loc["c"].isna().all()
        assert h.cut.drop("c").notna().all().all()

    def test_a_subset_of_the_rows_is_taken_by_label(self):
        """x on labels e, a (a subset, reordered) gets the bins of e and a.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, {"vx": EDGES})
        x = POINTS.vx.loc[["e", "c"]]
        h = Hist1D(x, nbins=b)
        assert h.cut.index.tolist() == ["e", "c"]
        assert h.cut.loc[:, "x"].tolist() == [_interval(0), _interval(2)]

    def test_a_name_the_binned_data_lacks_raises_key_error(self):
        """y named "q" is not a column of b: KeyError naming it.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        with pytest.raises(KeyError, match="'q'"):
            Hist2D(POINTS.vx, POINTS.vy.rename("q"), nbins=b)

    def test_labels_outside_the_binned_data_raise_value_error(self):
        """x holding a label b lacks raises ValueError.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS.loc[["a", "b", "c"]], GRID)
        with pytest.raises(ValueError, match="not a subset"):
            Hist2D(POINTS.vx, POINTS.vy, nbins=b)

    @pytest.mark.parametrize("nbins", ["first", "second"])
    def test_a_binned_data_inside_a_per_axis_sequence_raises_type_error(self, nbins):
        """A BinnedData bins every axis, so (b, 5) or [5, b] is refused.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        spec = (b, 5) if nbins == "first" else [5, b]
        with pytest.raises(TypeError, match="per-axis"):
            Hist2D(POINTS.vx, POINTS.vy, nbins=spec)

    @pytest.mark.parametrize("initial_bins", ["alone", "in a pair"])
    def test_spiral_refuses_a_binned_data(self, initial_bins):
        """SpiralPlot2D adapts its mesh to its data and raises TypeError.

        ON FAILURE: the code is wrong.
        """
        b = BinnedData(POINTS, GRID)
        spec = b if initial_bins == "alone" else (b, 3)
        with pytest.raises(TypeError, match="cannot use a shared BinnedData"):
            SpiralPlot2D(POINTS.vx, POINTS.vy, initial_bins=spec)

    @pytest.mark.parametrize(
        "binned_with, plot_with, match",
        [
            ({"log": {"vx": True}}, {}, "logx=False conflicts"),
            ({}, {"logy": True}, "logy=True conflicts"),
            ({"clip": {"vy": True}}, {}, "clip_data=False conflicts"),
            ({"clip": {"vx": "u", "vy": "u"}}, {"clip_data": "l"}, "clip_data='l'"),
        ],
        ids=["log in b", "log in plot", "clip in b", "other tail"],
    )
    def test_log_or_clip_differing_from_the_binned_data_raises(
        self, binned_with, plot_with, match
    ):
        """The plot's logx, logy and clip_data must equal b's for its columns.

        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[KEPT]
        b = BinnedData(positive, GRID, **binned_with)
        with pytest.raises(ValueError, match=match):
            Hist2D(positive.vx, positive.vy, nbins=b, **plot_with)

    def test_betar_plot_takes_a_log_binned_data(self):
        """BetaRPlot bins log10 by default, so a log BinnedData is accepted.

        log10 of every kept value (0.5 to 2.5) lies in (-1, 1], so all four
        points are counted once BetaRPlot's default clim of 5 is cleared.
        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[KEPT]
        log_edges = [-1.0, 0.0, 1.0]
        b = BinnedData(
            positive,
            {"vx": log_edges, "vy": log_edges},
            log={"vx": True, "vy": True},
        )
        h = BetaRPlot(positive.vx, positive.vy, "p", nbins=b)
        h.set_clim(None, None)
        assert h.agg(fcn="count").sum() == exact(4)


#: Every plot class's constructor, given x and y and a mask.
MASKED_PLOTS = {
    "Hist1D": lambda x, y, mask: Hist1D(x, y, mask=mask),
    "Hist2D": lambda x, y, mask: Hist2D(x, y, mask=mask),
    "BetaRPlot": lambda x, y, mask: BetaRPlot(x, y, "p", mask=mask),
    "Scatter": lambda x, y, mask: Scatter(x, y, mask=mask),
    "SpiralPlot2D": lambda x, y, mask: SpiralPlot2D(x, y, mask=mask),
}


class TestCallerMask:
    """Every plot constructor takes a mask aligned by label, and checks it."""

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_the_mask_keeps_its_rows_under_their_labels(self, plot):
        """The mask is aligned by label: given reversed, it still drops "b".

        ON FAILURE: the code is wrong.
        """
        positive = POINTS.loc[["a", "b", "c", "d", "e"]]
        h = MASKED_PLOTS[plot](positive.vx, positive.vy, MASK[::-1])
        assert h.data.index.tolist() == KEPT

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_missing_a_label_raises(self, plot):
        """A label of x absent from the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="lacks 1 label"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, MASK.drop("c"))

    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_holding_nan_raises(self, plot):
        """NaN in the mask is never read as False.

        ON FAILURE: the code is wrong.
        """
        mask = MASK.astype("boolean")
        mask.loc["c"] = pd.NA
        with pytest.raises(ValueError, match="NaN"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, mask)

    @pytest.mark.parametrize(
        "mask",
        [MASK.astype(float), MASK.to_numpy()],
        ids=["float series", "ndarray"],
    )
    @pytest.mark.parametrize("plot", tuple(MASKED_PLOTS))
    def test_a_mask_that_is_not_a_boolean_series_raises_type_error(self, plot, mask):
        """A float Series or a bare array is refused, not converted.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="mask must"):
            MASKED_PLOTS[plot](POINTS.vx, POINTS.vy, mask)


@pytest.mark.parametrize(
    "cls", [Hist1D, Hist2D, BetaRPlot, Scatter, SpiralPlot2D], ids=lambda c: c.__name__
)
def test_no_plot_class_offers_set_data(cls):
    """Data is given only to the constructor: no class has a public set_data.

    To plot other data, build a new plot.
    ON FAILURE: the code is wrong.
    """
    assert not hasattr(cls, "set_data")
