# Spent-When: PERMANENT(plot classes stop sourcing data through BinnedData)
# Supersedes: none
"""Contract tests for four rulings on the plot data path.

- ``clip`` accepts True/False and the strings ``"l"``, ``"lower"``, ``"u"``,
  ``"upper"`` and ``"both"`` in any case. Any other string raises
  ``ValueError`` naming them, when the plot or ``BinnedData`` is built and
  from ``Base.clip_data``.
- x, y and z are aligned by label. When their indexes differ and a column
  that has to be aligned repeats labels, alignment is ambiguous: the plot
  raises ``ValueError`` naming the column. Identical indexes, repeated labels
  included, and a column with unique labels aligned onto repeated ones keep
  working.
- Edges from an integer ``nbins`` enclose every sample, also where the data
  are so large that ``10**precision`` is below their float spacing.
- An object-dtype column of numbers is treated as the numbers it holds, so a
  +/-inf in it drops the row exactly as in a float column.

Every input is placed by hand. Expected counts and means are worked out from
those inputs in each test's comments.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.base import Base, ClipAxes  # noqa: E402
from solarwindpy.plotting.binned import BinnedData  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.tolerances import exact  # noqa: E402

# 1..10: the 0.01st and 99.99th percentiles are 1.0009 and 9.9991.
SERIES = pd.Series(np.arange(1.0, 11.0), name="x")
LOWER = np.r_[1.0009, np.arange(2.0, 11.0)]
UPPER = np.r_[np.arange(1.0, 10.0), 9.9991]
BOTH = np.r_[1.0009, np.arange(2.0, 10.0), 9.9991]

ACCEPTED_FORMS = [
    ("l", LOWER),
    ("L", LOWER),
    ("lower", LOWER),
    ("Lower", LOWER),
    ("LOWER", LOWER),
    ("u", UPPER),
    ("U", UPPER),
    ("upper", UPPER),
    ("Upper", UPPER),
    ("both", BOTH),
    ("Both", BOTH),
    (True, BOTH),
]
REJECTED_FORMS = ["", "foo", "lo", "lower ", "uppr", "b"]
ACCEPTED_MESSAGE = "'l', 'lower', 'u', 'upper' or 'both'"


class TestClipSetting:
    @pytest.mark.parametrize(
        "clip, expected", ACCEPTED_FORMS, ids=[repr(c) for c, _ in ACCEPTED_FORMS]
    )
    def test_clip_data_accepts_each_documented_form(self, clip, expected):
        """Each documented form clips the tail(s) it names, in any case.

        ON FAILURE: the code is wrong.
        """
        result = Base.clip_data(SERIES, clip)
        assert result.to_numpy() == exact(expected)

    @pytest.mark.parametrize("clip", REJECTED_FORMS)
    def test_clip_data_rejects_any_other_string(self, clip):
        """An empty or unknown string raises ValueError naming the accepted ones.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=ACCEPTED_MESSAGE):
            Base.clip_data(SERIES, clip)

    @pytest.mark.parametrize("clip", ["", "foo"])
    @pytest.mark.parametrize(
        "build",
        [
            lambda c: Hist1D(SERIES, clip=c, nbins=3),
            lambda c: Hist2D(SERIES, SERIES.rename("y"), clip=c, nbins=3),
            lambda c: Hist2D(SERIES, SERIES.rename("y"), clip={"y": c}, nbins=3),
            lambda c: Scatter(SERIES, SERIES.rename("y"), clip={"z": c}),
            lambda c: SpiralPlot2D(SERIES, SERIES.rename("y"), clip=c),
            lambda c: BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": c}),
        ],
        ids=["Hist1D", "Hist2D", "Hist2D-mapping", "Scatter-z", "Spiral", "BinnedData"],
    )
    def test_constructors_reject_an_unknown_clip_string(self, build, clip):
        """A plot or BinnedData given an unknown clip string raises when built.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=ACCEPTED_MESSAGE):
            build(clip)

    def test_constructors_keep_the_accepted_forms(self):
        """Accepted forms build, and ``clip`` reads back what was passed.

        ON FAILURE: the code is wrong.
        """
        y = SERIES.rename("y")
        assert Hist2D(SERIES, y, clip="Lower", nbins=3).clip == ClipAxes(
            "Lower", "Lower", False
        )
        assert Scatter(SERIES, y, clip={"z": "both"}).clip == ClipAxes(
            False, False, "both"
        )
        b = BinnedData(SERIES.to_frame(), {"x": [0, 5, 11]}, clip={"x": "UPPER"})
        assert b.clip_of("x") == "UPPER"


# Rows on four timestamps, the second one repeated.
REPEATED = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03"])
UNIQUE = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])


class TestAlignmentWithRepeatedLabels:
    def test_identical_repeated_indexes_keep_working(self):
        """x, y and z on one index that repeats a label are taken row by row.

        x = y = 1, 2, 3, 4 and z = 5, 6, 7, 8. nbins=2 splits 1..4 at 2.5,
        so bin (0, 0) holds rows 0 and 1 (mean z 5.5) and bin (1, 1) rows 2
        and 3 (mean z 7.5).

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        z = pd.Series([5.0, 6, 7, 8], index=REPEATED, name="z")
        agg = Hist2D(x, x.rename("y"), z=z, nbins=2).agg()
        assert agg.to_numpy() == exact([5.5, np.nan, np.nan, 7.5], nan_ok=True)

    def test_unique_labels_align_onto_repeated_ones(self):
        """z with unique labels gives each repeat of a label the same value.

        x = y = 1, 2, 3, 4 on REPEATED; z = 5, 6, 7 on UNIQUE, so rows 1 and
        2 (both 2020-01-02) get z = 6. Bin (0, 0) holds rows 0, 1: mean 5.5;
        bin (1, 1) holds rows 2, 3: z 6 and 7, mean 6.5.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        z = pd.Series([5.0, 6, 7], index=UNIQUE, name="z")
        agg = Hist2D(x, x.rename("y"), z=z, nbins=2).agg()
        assert agg.to_numpy() == exact([5.5, np.nan, np.nan, 6.5], nan_ok=True)

    def test_z_with_repeated_labels_on_another_index_raises(self):
        """z repeats a label and its index differs from x's: ValueError names z.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3], index=UNIQUE, name="x")
        z = pd.Series([5.0, 6, 7, 8], index=REPEATED, name="z")
        with pytest.raises(ValueError, match=r"\['z'\] repeat.*ambiguous"):
            Hist2D(x, x.rename("y"), z=z, nbins=2)

    @pytest.mark.parametrize(
        "build",
        [
            lambda x, y: Hist2D(x, y, nbins=2),
            lambda x, y: Hist1D(x, y=y, nbins=2),
            lambda x, y: Scatter(x, y),
        ],
        ids=["Hist2D", "Hist1D", "Scatter"],
    )
    def test_coordinates_with_repeated_labels_on_different_indexes_raise(self, build):
        """x and y both repeat labels on different indexes: ValueError names them.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 2, 3, 4], index=REPEATED, name="x")
        other = pd.to_datetime(
            ["2020-01-01", "2020-01-02", "2020-01-02", "2020-01-03", "2020-01-05"]
        )
        y = pd.Series([1.0, 2, 3, 4, 5], index=other, name="y")
        with pytest.raises(ValueError, match=r"repeat.*ambiguous"):
            build(x, y)


class TestEdgesFromACountEncloseLargeData:
    # Each pair was found by a seeded search for data whose rounded outer edge
    # lands one float spacing inside the data: at ~4e11 and ~1e12 the spacing
    # (6e-5, 1.2e-4) exceeds 10**-5, the default precision.
    @pytest.mark.parametrize(
        "lo, hi",
        [
            (440651515598.04877, 440655054132.1329),
            (988667622348.9438, 1045034220770.2701),
        ],
        ids=["lower-edge", "upper-edge"],
    )
    def test_hist1d_counts_every_sample(self, lo, hi):
        """Three samples and nbins=2: the edges enclose them and all 3 count.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([lo, (lo + hi) / 2, hi], name="x")
        h = Hist1D(x, nbins=2)
        edges = h.edges["x"]
        assert edges[0] <= lo
        assert edges[-1] >= hi
        assert h.agg().sum() == 3


# 1, 2, inf, 4 held as Python floats in an object column.
OBJECT_WITH_INF = pd.Series([1.0, 2.0, np.inf, 4.0], dtype=object)
FLOATS = pd.Series([1.0, 2.0, 3.0, 4.0])


class TestObjectDtypeColumns:
    def test_object_z_with_inf_drops_that_row(self):
        """z = 1, 2, inf, 4 as objects: the inf row is dropped, as for floats.

        x = y = 1..4 and nbins=2 (split at 2.5): bin (0, 0) holds rows 0, 1,
        mean 1.5; bin (1, 1) holds row 3 only, z = 4.

        ON FAILURE: the code is wrong.
        """
        z = OBJECT_WITH_INF.rename("z")
        h = Hist2D(FLOATS.rename("x"), FLOATS.rename("y"), z=z, nbins=2)
        assert h.agg().to_numpy() == exact([1.5, np.nan, np.nan, 4.0], nan_ok=True)
        assert list(h.data.index) == [0, 1, 3]

    def test_object_x_with_inf_bins_by_count(self):
        """x = 1, 2, inf, 4 as objects, nbins=2: edges 1, 2.5, 4; counts 2 and 1.

        ON FAILURE: the code is wrong.
        """
        agg = Hist1D(OBJECT_WITH_INF.rename("x"), nbins=2).agg()
        assert agg.to_numpy() == exact([2, 1])

    def test_object_x_takes_log(self):
        """x = 1, 10, inf, 100 as objects with logx: log10 0, 1, 2; counts 1, 2.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series([1.0, 10.0, np.inf, 100.0], dtype=object, name="x")
        agg = Hist1D(x, logx=True, nbins=2).agg()
        assert agg.to_numpy() == exact([1, 2])

    def test_scatter_data_holds_no_inf_from_an_object_column(self):
        """Scatter keeps rows 0, 1, 3 of an object x holding inf at row 2.

        ON FAILURE: the code is wrong.
        """
        data = Scatter(OBJECT_WITH_INF.rename("x"), FLOATS.rename("y")).data
        assert list(data.index) == [0, 1, 3]
        assert data.loc[:, "x"].to_numpy() == exact([1.0, 2.0, 4.0])

    def test_binned_data_logs_an_object_column(self):
        """BinnedData logs objects 1, 10, inf: log10 0, 1 in (-1, 0.5], (0.5, 2].

        inf gets code -1.

        ON FAILURE: the code is wrong.
        """
        frame = pd.DataFrame({"x": pd.Series([1.0, 10.0, np.inf], dtype=object)})
        b = BinnedData(frame, {"x": [-1, 0.5, 2]}, log={"x": True})
        assert b.codes("x").tolist() == [0, 1, -1]

    def test_non_numeric_object_column_is_left_as_given(self):
        """Strings are not numbers: Scatter keeps them as given.

        ON FAILURE: the code is wrong.
        """
        x = pd.Series(["a", "b"], dtype=object, name="x")
        data = Scatter(x, pd.Series([1.0, 2.0], name="y")).data
        assert data.loc[:, "x"].tolist() == ["a", "b"]
