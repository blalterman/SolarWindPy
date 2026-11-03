# Spent-When: MARKED(tests/plotting/test_binned_migration.py)
# Supersedes: none
"""The live plotting classes give exactly what the frozen legacy classes give.

``tests/plotting/_legacy/`` is a verbatim copy of the plotting modules at
master 4bc1c08e, before the binned-data migration. Every test here builds
the same plot from the same seeded case (``tests/plotting/_cases.py``) with
the live class and with its legacy copy, and asserts that what a caller can
read is identical: the stored data, the bins and bin assignments, every
aggregation and normalization, every selection method's output, and the
arrays handed to matplotlib. Comparisons are exact; there is no tolerance.

When both classes raise, the test asserts they raise the same exception type
with the same message.

Intended change a (Hist1D drops rows with NaN in x or y, as Hist2D does)
changes only the legacy side of every ``Hist1D`` comparison: the expected
``Hist1D`` is the legacy one built on the rows the live one keeps,
``LegacyHist1D(x[valid], y[valid])`` with the same settings, where ``valid``
means neither x nor y (aligned to x) is NaN (``hist1d_kept``). This covers
the ``Hist1D`` that legacy ``Hist2D.project_1d`` builds, whose y carries a NaN
placeholder for a y outside the y-bins (``_LegacyHist1DOnKeptRows``). The live
side is unchanged. ``test_hist1d_drops_exactly_the_legacy_nan_rows`` checks
that the rows the live ``Hist1D`` drops are exactly the legacy rows with a NaN
x or y. Every other comparison is unchanged.

The legacy copy is the oracle only until the migration is proven. This file
and ``tests/plotting/_legacy/`` are deleted together, in one commit, once all
three conditions hold:

1. these migration tests pass;
2. all 90 ``h2_set`` histograms match old vs new in the private icmes repo;
3. every edge case the migration caught has a permanent test with an
   independent source for its expected values.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.binned import BinnedData  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from tests.plotting._cases import (  # noqa: E402
    CASES,
    NBINS,
    SPIRAL_NBINS,
    nbins_spec,
    spiral_bins_spec,
)
from tests.plotting._legacy.beta_ani import (  # noqa: E402
    BetaRPlot as LegacyBetaRPlot,
)
from tests.plotting._legacy import hist2d as legacy_hist2d_module  # noqa: E402
from tests.plotting._legacy.hist1d import Hist1D as LegacyHist1D  # noqa: E402
from tests.plotting._legacy.hist2d import Hist2D as LegacyHist2D  # noqa: E402
from tests.plotting._legacy.scatter import Scatter as LegacyScatter  # noqa: E402
from tests.plotting._legacy.spiral import (  # noqa: E402
    SpiralPlot2D as LegacySpiralPlot2D,
)

#: Aggregation functions compared for every plot.
FCNS = (None, "count", "mean", "std")

#: Every ``axnorm`` each histogram accepts.
HIST1D_AXNORMS = (None, "d", "t")
HIST2D_AXNORMS = (None, "c", "r", "t", "d", "cd", "rd")

#: ``(lower, upper)`` count limits under which the selections are compared.
CLIMS = ((None, None), (3, None))

#: Cell-split threshold for ``SpiralPlot2D.initialize_mesh``.
MIN_PER_BIN = 40

CASE_IDS = tuple(CASES)


@pytest.fixture(autouse=True)
def _close_figures():
    """Close every figure a test opens."""
    yield
    plt.close("all")


def hist1d_kept(x, y):
    """``x`` and ``y`` on the rows a live ``Hist1D`` keeps (intended change a).

    ``y`` is aligned to ``x`` by label, as ``Hist1D`` aligns it, and a row is
    kept where neither is NaN; with ``y`` None, where ``x`` is not NaN. When
    every row is kept, ``x`` and ``y`` are returned as given, so the legacy
    side is built exactly as before.
    """
    if y is None:
        keep = x.notna().to_numpy()
    else:
        y_on_x = y.reindex(x.index)
        keep = (x.notna() & y_on_x.notna()).to_numpy()
    if keep.all():
        return x, y
    return x[keep], None if y is None else y_on_x[keep]


class _LegacyHist1DOnKeptRows(LegacyHist1D):
    """Legacy ``Hist1D`` built on ``hist1d_kept(x, y)``, otherwise unchanged."""

    def __init__(self, x, y=None, **kwargs):
        x, y = hist1d_kept(x, y)
        super().__init__(x, y=y, **kwargs)


@pytest.fixture(autouse=True)
def _legacy_projection_on_kept_rows(monkeypatch):
    """Legacy ``Hist2D.project_1d`` builds its ``Hist1D`` on the kept rows.

    Intended change a: the live projection no longer carries a NaN-y
    placeholder, so its expected side is the legacy ``Hist1D`` on the rows
    whose projected y is not NaN. Only ``project_1d`` reads this name.
    """
    monkeypatch.setattr(legacy_hist2d_module, "Hist1D", _LegacyHist1DOnKeptRows)


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Raised:
    """An exception a call raised, kept so two calls can be compared."""

    kind: str
    message: str


def attempt(fn, *args, **kwargs):
    """Return ``fn(*args, **kwargs)``, or a ``Raised`` if it raises."""
    try:
        return fn(*args, **kwargs)
    except Exception as err:  # noqa: BLE001 - the exception is the result
        return Raised(type(err).__name__, str(err))


def assert_same(live, legacy, where="value"):
    """Assert ``live`` equals ``legacy`` exactly, recursing into containers.

    pandas objects are compared with ``check_exact=True`` (index class, dtype,
    names, categories and values); numpy arrays element by element with
    matching dtype and shape, NaN equal to NaN; masked arrays by mask and
    data.
    """
    if isinstance(live, Raised) or isinstance(legacy, Raised):
        assert live == legacy, f"{where}: live {live!r} != legacy {legacy!r}"
    elif isinstance(legacy, pd.DataFrame):
        assert isinstance(live, pd.DataFrame), f"{where}: {type(live)}"
        pd.testing.assert_frame_equal(live, legacy, check_exact=True, obj=where)
    elif isinstance(legacy, pd.Series):
        assert isinstance(live, pd.Series), f"{where}: {type(live)}"
        pd.testing.assert_series_equal(live, legacy, check_exact=True, obj=where)
    elif isinstance(legacy, pd.Index):
        assert isinstance(live, pd.Index), f"{where}: {type(live)}"
        pd.testing.assert_index_equal(
            live, legacy, exact=True, check_exact=True, obj=where
        )
    elif isinstance(legacy, pd.Categorical):
        assert isinstance(live, pd.Categorical), f"{where}: {type(live)}"
        pd.testing.assert_series_equal(
            pd.Series(live), pd.Series(legacy), check_exact=True, obj=where
        )
    elif isinstance(legacy, np.ma.MaskedArray):
        assert isinstance(live, np.ma.MaskedArray), f"{where}: {type(live)}"
        np.testing.assert_array_equal(
            np.ma.getmaskarray(live),
            np.ma.getmaskarray(legacy),
            err_msg=f"{where} mask",
            strict=True,
        )
        np.testing.assert_array_equal(
            np.ma.getdata(live), np.ma.getdata(legacy), err_msg=where, strict=True
        )
    elif isinstance(legacy, np.ndarray):
        assert isinstance(live, np.ndarray), f"{where}: {type(live)}"
        np.testing.assert_array_equal(live, legacy, err_msg=where, strict=True)
    elif isinstance(legacy, dict):
        assert isinstance(live, dict), f"{where}: {type(live)}"
        assert list(live) == list(legacy), f"{where}: keys {list(live)}"
        for key in legacy:
            assert_same(live[key], legacy[key], f"{where}[{key!r}]")
    elif isinstance(legacy, (tuple, list)):
        assert isinstance(live, (tuple, list)), f"{where}: {type(live)}"
        assert len(live) == len(legacy), f"{where}: length {len(live)}"
        for i, (a, b) in enumerate(zip(live, legacy)):
            assert_same(a, b, f"{where}[{i}]")
    else:
        same = live == legacy or (pd.isna(live) and pd.isna(legacy))
        assert same, f"{where}: live {live!r} != legacy {legacy!r}"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def clip_kw(cls, clip):
    """The clip keyword argument for ``cls``.

    The live classes take ``clip`` and the legacy ones ``clip_data``: the
    rename is intended change e, so only the keyword's name differs.
    """
    legacy = cls.__module__.startswith("tests.plotting._legacy")
    return {"clip_data" if legacy else "clip": clip}


def _hist1d(cls, case, nbins, kept_rows=False):
    x, y, z = case.inputs()
    # Hist1D aggregates y in bins of x; the counts case has no value to average.
    y = None if z is None else y
    if kept_rows:
        x, y = hist1d_kept(x, y)
    return cls(x, y=y, logx=case.logx, nbins=nbins, **clip_kw(cls, case.clip_data))


def _hist2d(cls, case, nbins):
    x, y, z = case.inputs()
    return cls(
        x,
        y,
        z=z,
        logx=case.logx,
        logy=case.logy,
        nbins=nbins,
        **clip_kw(cls, case.clip_data),
    )


def _betar(cls, case, nbins):
    x, y, z = case.inputs()
    # BetaRPlot bins log10|beta| and log10|R| by default.
    return cls(x, y, "p", z=z, nbins=nbins, **clip_kw(cls, case.clip_data))


HIST2D_KINDS = {
    "Hist2D": (Hist2D, LegacyHist2D, _hist2d, False),
    "BetaRPlot": (BetaRPlot, LegacyBetaRPlot, _betar, True),
}


def _spec(name, case, axes, log):
    if name == "knuth":
        pytest.importorskip("astropy")
    return nbins_spec(name, case, axes, log)


def build_hist1d(case_name, spec_name):
    """Build the live and the legacy ``Hist1D`` for one case and ``nbins``."""
    case = CASES[case_name]
    log = {"x": case.logx}
    live = attempt(_hist1d, Hist1D, case, _spec(spec_name, case, ("x",), log))
    legacy = attempt(
        _hist1d,
        LegacyHist1D,
        case,
        _spec(spec_name, case, ("x",), log),
        kept_rows=True,
    )
    return live, legacy


def build_hist2d(kind, case_name, spec_name):
    """Build the live and the legacy 2-D histogram ``kind`` for one case."""
    live_cls, legacy_cls, factory, always_log = HIST2D_KINDS[kind]
    case = CASES[case_name]
    log = {"x": always_log or case.logx, "y": always_log or case.logy}
    axes = ("x", "y")
    live = attempt(factory, live_cls, case, _spec(spec_name, case, axes, log))
    legacy = attempt(factory, legacy_cls, case, _spec(spec_name, case, axes, log))
    return live, legacy


def built(live, legacy):
    """Return True when both built; when either raised, assert they raised alike."""
    if isinstance(live, Raised) or isinstance(legacy, Raised):
        assert_same(live, legacy, "construction")
        return False
    return True


# ---------------------------------------------------------------------------
# What a caller reads
# ---------------------------------------------------------------------------


def binning(h):
    """The stored data, the bins and the bin of every row."""
    return {
        "data": h.data,
        "cut": h.cut,
        "intervals": h.intervals,
        "edges": h.edges,
        "categoricals": h.categoricals,
        "log": tuple(h.log),
    }


def grid(h, agg):
    """``agg`` unstacked on x and reindexed to every (y, x) bin."""
    if isinstance(agg, Raised):
        return agg
    return agg.unstack("x").reindex(
        index=h.categoricals["y"], columns=h.categoricals["x"]
    )


def hist1d_aggs(h):
    out = {}
    for axnorm in HIST1D_AXNORMS:
        h.set_axnorm(axnorm)
        for fcn in FCNS:
            out[f"{axnorm}/{fcn}"] = attempt(h.agg, fcn=fcn)
    h.set_axnorm(None)
    return out


def hist2d_aggs(h):
    out = {}
    for axnorm in HIST2D_AXNORMS:
        h.set_axnorm(axnorm)
        for fcn in FCNS:
            out[f"{axnorm}/{fcn}"] = grid(h, attempt(h.agg, fcn=fcn))
    h.set_axnorm(None)
    return out


def _y_band(h):
    """Bottom and top of a y band around the middle half of the stored y."""
    y = h.data.loc[:, "y"]
    lo, hi = y.quantile([0.25, 0.75])
    return lo - 0.5, hi + 0.5


def hist1d_selections(h):
    out = {}
    for clim in CLIMS:
        h.set_clim(*clim)
        key = f"clim={clim}"
        out[f"{key}/plotted"] = attempt(h.get_plotted_data_boolean_series)
        out[f"{key}/above"] = attempt(h.get_subset_above_threshold, 3, fcn="count")
        for only_plotted in (True, False):
            out[f"{key}/cdf/{only_plotted}"] = attempt(
                h.construct_cdf, only_plotted=only_plotted
            )
        bottom, top = _y_band(h)
        ranges = pd.DataFrame({"bottom": bottom, "top": top}, index=h.agg().index)
        out[f"{key}/yrange"] = attempt(
            h.take_data_in_yrange_across_x,
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row: (row.bottom, row.top),
        )
    h.set_clim(None, None)
    return out


def projection(h1):
    """What a caller reads from a ``project_1d`` result."""
    out = binning(h1)
    out["agg"] = attempt(h1.agg)
    out["labels"] = tuple(str(label) for label in h1.labels)
    return out


def hist2d_selections(h):
    out = {}
    for clim in CLIMS:
        h.set_clim(*clim)
        key = f"clim={clim}"
        out[f"{key}/plotted"] = attempt(h.get_plotted_data_boolean_series)
        out[f"{key}/above"] = attempt(h.get_subset_above_threshold, 3, fcn="count")
        level = np.nanmedian(h.agg().to_numpy(dtype=float))
        out[f"{key}/contour"] = attempt(h.id_data_above_contour, level)
        bottom, top = _y_band(h)
        columns = h.agg().unstack("x").columns
        ranges = pd.DataFrame({"bottom": bottom, "top": top}, index=columns)
        out[f"{key}/yrange"] = attempt(
            h.take_data_in_yrange_across_x,
            ranges,
            lambda key, expected_logx=False: (key.left, key.right),
            lambda row, expected_logy=False: (row.bottom, row.top),
        )
        for axis in ("x", "y"):
            for only_plotted in (True, False):
                for project_counts in (True, False):
                    h1 = attempt(
                        h.project_1d,
                        axis,
                        only_plotted=only_plotted,
                        project_counts=project_counts,
                    )
                    name = f"{key}/project/{axis}/{only_plotted}/{project_counts}"
                    out[name] = h1 if isinstance(h1, Raised) else projection(h1)
    h.set_clim(None, None)
    return out


def hist1d_drawn(h):
    """Vertices of every line and error bar ``make_plot`` draws."""
    out = {}
    fcns = [None, "count"]
    if h.data.loc[:, "y"].nunique() > 1:
        fcns.append(("mean", "std"))
    for axnorm in (None, "t"):
        h.set_axnorm(axnorm)
        for fcn in fcns:
            fig, ax = plt.subplots()
            result = attempt(h.make_plot, ax=ax, fcn=fcn)
            key = f"{axnorm}/{fcn}"
            if isinstance(result, Raised):
                out[key] = result
            else:
                out[key] = {
                    "lines": [line.get_xydata() for line in ax.get_lines()],
                    "bars": [
                        [np.asarray(s) for s in c.get_segments()]
                        for c in ax.collections
                    ],
                }
            plt.close(fig)
    h.set_axnorm(None)
    return out


def hist2d_drawn(h):
    """The mesh and contour arrays ``make_plot`` and ``plot_contours`` hand over."""
    out = {}
    for axnorm in (None, "c", "d"):
        h.set_axnorm(axnorm)
        fig, ax = plt.subplots()
        result = attempt(h.make_plot, ax=ax, cbar=False)
        if isinstance(result, Raised):
            out[f"mesh/{axnorm}"] = result
        else:
            mesh = result[1]
            out[f"mesh/{axnorm}"] = {
                "array": mesh.get_array(),
                "coordinates": np.asarray(mesh.get_coordinates()),
            }
        plt.close(fig)
    for axnorm in (None, "t"):
        h.set_axnorm(axnorm)
        fig, ax = plt.subplots()
        result = attempt(h.plot_contours, ax=ax, cbar=False)
        if isinstance(result, Raised):
            out[f"contour/{axnorm}"] = result
        else:
            qset = result[2]
            out[f"contour/{axnorm}"] = {
                "levels": np.asarray(qset.levels),
                "allsegs": [[np.asarray(s) for s in level] for level in qset.allsegs],
            }
        plt.close(fig)
    h.set_axnorm(None)
    return out


# ---------------------------------------------------------------------------
# The comparator separates what it must
# ---------------------------------------------------------------------------


def test_the_comparator_tells_two_binnings_apart():
    """Legacy histograms of one case with 7 and with 8 bins compare unequal.

    The bins, the bin of every row and the aggregated grid all differ, so the
    comparator must reject each. Otherwise every migration test here could
    pass without comparing anything.

    ON FAILURE: the comparator no longer separates 7 bins from 8; fix the fixture.
    """
    case = CASES["clean"]
    seven = _hist2d(LegacyHist2D, case, 7)
    eight = _hist2d(LegacyHist2D, case, 8)
    with pytest.raises(AssertionError):
        assert_same(seven.intervals, eight.intervals)
    with pytest.raises(AssertionError):
        assert_same(seven.cut, eight.cut)
    with pytest.raises(AssertionError):
        assert_same(grid(seven, seven.agg()), grid(eight, eight.agg()))
    assert_same(seven.data, eight.data)


# ---------------------------------------------------------------------------
# Hist1D
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_drops_exactly_the_legacy_nan_rows(case):
    """The rows the live Hist1D drops are exactly the legacy rows with NaN x or y.

    Both are built on the case's full inputs. The legacy ``Hist1D`` keeps
    every row, so its own stored data says which rows hold a NaN x or y; the
    live ``Hist1D`` keeps the others, in the legacy order (intended change a).

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]
    live = _hist1d(Hist1D, c, 7)
    legacy = _hist1d(LegacyHist1D, c, 7)
    legacy_index = legacy.data.index
    nan_rows = legacy.data.isna().any(axis=1).to_numpy()
    assert_same(live.data.index, legacy_index[~nan_rows])
    dropped = legacy_index.difference(live.data.index, sort=False)
    assert_same(dropped, legacy_index[nan_rows])
    x, y, z = c.inputs()
    kept_x, _ = hist1d_kept(x, None if z is None else y)
    assert_same(live.data.index, kept_x.index)


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_binning_matches_legacy(case, spec):
    """Hist1D stores the legacy data, bins, intervals and edges.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist1d(case, spec)
    if built(live, legacy):
        assert_same(binning(live), binning(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_agg_matches_legacy(case, spec):
    """Hist1D aggregates to the legacy values for every fcn and axnorm.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist1d(case, spec)
    if built(live, legacy):
        assert_same(hist1d_aggs(live), hist1d_aggs(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_selections_match_legacy(case, spec):
    """Every Hist1D selection method returns the legacy result.

    Compared with and without a lower count limit: the plotted-data mask,
    the subset above a count threshold, both CDFs and the y-range selection.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist1d(case, spec)
    if built(live, legacy):
        assert_same(hist1d_selections(live), hist1d_selections(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_drawn_lines_match_legacy(case, spec):
    """Hist1D.make_plot hands matplotlib the legacy line and error-bar vertices.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist1d(case, spec)
    if built(live, legacy):
        assert_same(hist1d_drawn(live), hist1d_drawn(legacy))


# ---------------------------------------------------------------------------
# Hist2D and BetaRPlot
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
@pytest.mark.parametrize("kind", tuple(HIST2D_KINDS))
def test_hist2d_binning_matches_legacy(kind, case, spec):
    """Hist2D and BetaRPlot store the legacy data, bins, intervals and edges.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist2d(kind, case, spec)
    if built(live, legacy):
        assert_same(binning(live), binning(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
@pytest.mark.parametrize("kind", tuple(HIST2D_KINDS))
def test_hist2d_agg_matches_legacy(kind, case, spec):
    """The aggregated (y, x) grid equals the legacy one for every fcn and axnorm.

    Each aggregate is unstacked on x and reindexed to every bin, so a bin
    missing from one side and NaN on the other compares equal.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist2d(kind, case, spec)
    if built(live, legacy):
        assert_same(hist2d_aggs(live), hist2d_aggs(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
@pytest.mark.parametrize("kind", tuple(HIST2D_KINDS))
def test_hist2d_selections_match_legacy(kind, case, spec):
    """Every 2-D selection method and projection returns the legacy result.

    Compared with and without a lower count limit: the plotted-data mask,
    the subset above a count threshold, the data above the median level, the
    y-range selection, and each ``project_1d`` variant's data, bins and
    aggregate.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist2d(kind, case, spec)
    if built(live, legacy):
        assert_same(hist2d_selections(live), hist2d_selections(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
@pytest.mark.parametrize("kind", tuple(HIST2D_KINDS))
def test_hist2d_drawn_arrays_match_legacy(kind, case, spec):
    """The QuadMesh values and contour levels and segments equal the legacy ones.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_hist2d(kind, case, spec)
    if built(live, legacy):
        assert_same(hist2d_drawn(live), hist2d_drawn(legacy))


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------


def scatter_drawn(s):
    fig, ax = plt.subplots()
    result = attempt(s.make_plot, ax=ax, cbar=False)
    if isinstance(result, Raised):
        return result
    collection = ax.collections[0]
    array = collection.get_array()
    return {
        "offsets": np.asarray(collection.get_offsets()),
        "array": None if array is None else np.ma.asarray(array),
    }


@pytest.mark.parametrize("case", CASE_IDS)
def test_scatter_matches_legacy(case):
    """Scatter stores the legacy data and draws the legacy offsets and colours.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]

    def build(cls):
        x, y, z = c.inputs()
        return cls(x, y, z=z, **clip_kw(cls, c.clip_data))

    live, legacy = attempt(build, Scatter), attempt(build, LegacyScatter)
    if built(live, legacy):
        assert_same(live.data, legacy.data, "data")
        assert_same(scatter_drawn(live), scatter_drawn(legacy), "drawn")


# ---------------------------------------------------------------------------
# SpiralPlot2D
# ---------------------------------------------------------------------------


def build_spiral(case_name, spec_name):
    """Build the live and the legacy ``SpiralPlot2D`` and place every point."""
    case = CASES[case_name]
    log = {"x": case.logx, "y": case.logy}

    def build(cls):
        x, y, z = case.inputs()
        splot = cls(
            x,
            y,
            z=z,
            logx=case.logx,
            logy=case.logy,
            initial_bins=spiral_bins_spec(spec_name, case, log),
            **clip_kw(cls, case.clip_data),
        )
        splot.initialize_mesh(progress=False, min_per_bin=MIN_PER_BIN)
        return splot

    return attempt(build, SpiralPlot2D), attempt(build, LegacySpiralPlot2D)


def spiral_state(s):
    """The data, initial bins, mesh, cell of every point and aggregates."""
    mesh = s.mesh
    out = {
        "data": s.data,
        "initial_bins": s.initial_bins,
        "mesh": mesh.mesh,
        "bin_id": tuple(mesh.bin_id),
        "cat": mesh.cat,
        "cell_filter": mesh.cell_filter,
    }
    for fcn in FCNS:
        out[f"agg/{fcn}"] = attempt(s.agg, fcn=fcn)
    fig, ax = plt.subplots()
    result = attempt(s.make_plot, ax=ax, cbar=False)
    if isinstance(result, Raised):
        out["drawn"] = result
    else:
        out["drawn"] = np.ma.asarray(result[1].get_array())
    plt.close(fig)
    return out


@pytest.mark.parametrize("spec", SPIRAL_NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_spiral_matches_legacy(case, spec):
    """SpiralPlot2D builds the legacy mesh, places points alike and aggregates alike.

    Compared after ``initialize_mesh``: the stored data, initial bins, mesh
    cells, ``bin_id``, cell categories, cell filter, ``agg`` for every fcn,
    and the cell values handed to matplotlib.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    live, legacy = build_spiral(case, spec)
    if built(live, legacy):
        assert_same(spiral_state(live), spiral_state(legacy))


# ---------------------------------------------------------------------------
# A shared BinnedData through nbins, and a caller mask
# ---------------------------------------------------------------------------

#: Explicit bin specifications a ``BinnedData`` accepts.
SHARED_SPECS = ("edges", "intervals_left", "per_axis")

#: Seed of the mask drawn for a case that has none.
MASK_SEED = 20261103


def shared_spec(name, case, axes):
    """The legacy ``nbins`` and the equivalent ``BinnedData`` bins per axis.

    ``"edges"`` and ``"intervals_left"`` give every axis the same bins, as
    ``nbins_spec`` builds them. ``"per_axis"`` gives each axis its own edges
    (x) or left-closed intervals (y), legacy as one entry per axis.
    """
    log = {"x": case.logx, "y": case.logy}
    if name in ("edges", "intervals_left"):
        spec = nbins_spec(name, case, axes, log)
        return spec, {k: spec for k in axes}
    x_edges = nbins_spec("mixed", case, ("x",), log)[0]
    if axes == ("x",):
        return (x_edges,), {"x": x_edges}
    y_intervals = nbins_spec("mixed", case, axes, log)[1]
    return (x_edges, y_intervals), {"x": x_edges, "y": y_intervals}


def shared_binned_data(case, bins):
    """A ``BinnedData`` over the case's full, unmasked columns.

    The plot is given the case's inputs, which the case's mask may subset,
    so its rows are then taken from the ``BinnedData`` by label.
    """
    frame = pd.DataFrame({"x": case.x, "y": case.y})
    log = {"x": case.logx, "y": case.logy}
    return BinnedData(frame, bins, log={k: log[k] for k in bins})


def caller_mask(case):
    """The case's mask, or a seeded one, on the union of x's and y's labels."""
    if case.mask is not None:
        return case.mask
    index = pd.DataFrame({"x": case.x, "y": case.y}).index
    rng = np.random.default_rng(MASK_SEED)
    return pd.Series(rng.random(index.size) < 0.7, index=index)


def subset(series, mask):
    """``series`` on the labels ``mask`` keeps, as a caller subsets beforehand."""
    if series is None:
        return None
    return series.loc[mask.reindex(series.index).to_numpy(dtype=bool)]


def everything_2d(h):
    """Data, bins, cut, agg grids, selections and drawn arrays of a 2-D plot."""
    return {
        "binning": binning(h),
        "aggs": hist2d_aggs(h),
        "selections": hist2d_selections(h),
        "drawn": hist2d_drawn(h),
    }


def everything_1d(h):
    """Data, bins, cut, aggregates, selections and drawn lines of a Hist1D."""
    return {
        "binning": binning(h),
        "aggs": hist1d_aggs(h),
        "selections": hist1d_selections(h),
        "drawn": hist1d_drawn(h),
    }


@pytest.mark.parametrize("spec", SHARED_SPECS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist2d_from_shared_binned_data_matches_legacy_edges(case, spec):
    """Hist2D(nbins=BinnedData) equals legacy Hist2D(nbins=<the same bins>).

    The BinnedData bins the case's full columns; the plot is given the
    case's (possibly subset) inputs. Without clipping, data, cut, every agg
    grid, every selection and the matplotlib arrays are identical.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]
    legacy_spec, bins = shared_spec(spec, c, ("x", "y"))
    x, y, z = c.inputs()
    options = dict(z=z, logx=c.logx, logy=c.logy)
    live = attempt(
        Hist2D,
        x,
        y,
        nbins=shared_binned_data(c, bins),
        **options,
        **clip_kw(Hist2D, False),
    )
    legacy = attempt(
        LegacyHist2D,
        x,
        y,
        nbins=legacy_spec,
        **options,
        **clip_kw(LegacyHist2D, False),
    )
    if built(live, legacy):
        assert_same(everything_2d(live), everything_2d(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist2d_with_mask_matches_legacy_on_subset_inputs(case, spec):
    """Hist2D(x, y, z, mask=m) equals legacy Hist2D(x[m], y[m], z[m]).

    Data, cut, every agg grid, every selection and the matplotlib arrays
    are identical, so selections come back on the original labels.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]
    mask = caller_mask(c)
    nbins = _spec(spec, c, ("x", "y"), {"x": c.logx, "y": c.logy})
    options = dict(logx=c.logx, logy=c.logy, nbins=nbins)
    live = attempt(
        Hist2D,
        c.x,
        c.y,
        z=c.z,
        mask=mask,
        **options,
        **clip_kw(Hist2D, c.clip_data),
    )
    legacy = attempt(
        LegacyHist2D,
        subset(c.x, mask),
        subset(c.y, mask),
        z=subset(c.z, mask),
        **options,
        **clip_kw(LegacyHist2D, c.clip_data),
    )
    if built(live, legacy):
        assert_same(everything_2d(live), everything_2d(legacy))


@pytest.mark.parametrize("spec", SHARED_SPECS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_from_shared_binned_data_matches_legacy_edges(case, spec):
    """Hist1D(nbins=BinnedData) equals legacy Hist1D(nbins=<the same bins>).

    Without clipping, data, cut, every aggregate, every selection and the
    drawn lines are identical.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]
    legacy_spec, bins = shared_spec(spec, c, ("x",))
    x, y, z = c.inputs()
    options = dict(y=None if z is None else y, logx=c.logx)
    live = attempt(
        Hist1D,
        x,
        nbins=shared_binned_data(c, bins),
        **options,
        **clip_kw(Hist1D, False),
    )
    # Intended change a: the expected side is built on the kept rows.
    legacy_x, legacy_y = hist1d_kept(x, options.pop("y"))
    legacy = attempt(
        LegacyHist1D,
        legacy_x,
        y=legacy_y,
        nbins=legacy_spec,
        **options,
        **clip_kw(LegacyHist1D, False),
    )
    if built(live, legacy):
        assert_same(everything_1d(live), everything_1d(legacy))


@pytest.mark.parametrize("spec", NBINS)
@pytest.mark.parametrize("case", CASE_IDS)
def test_hist1d_with_mask_matches_legacy_on_subset_inputs(case, spec):
    """Hist1D(x, y, mask=m) equals legacy Hist1D(x[m], y[m]).

    Data, cut, every aggregate, every selection and the drawn lines are
    identical, so selections come back on the original labels.

    ON FAILURE: the code is wrong, unless the author lists this difference
    among the migration's intended behaviour changes.
    """
    c = CASES[case]
    mask = caller_mask(c)
    nbins = _spec(spec, c, ("x",), {"x": c.logx})
    y = None if c.z is None else c.y
    options = dict(logx=c.logx, nbins=nbins)
    live = attempt(
        Hist1D, c.x, y=y, mask=mask, **options, **clip_kw(Hist1D, c.clip_data)
    )
    # Intended change a: the expected side is built on the kept rows.
    legacy_x, legacy_y = hist1d_kept(subset(c.x, mask), subset(y, mask))
    legacy = attempt(
        LegacyHist1D,
        legacy_x,
        y=legacy_y,
        **options,
        **clip_kw(LegacyHist1D, c.clip_data),
    )
    if built(live, legacy):
        assert_same(everything_1d(live), everything_1d(legacy))
