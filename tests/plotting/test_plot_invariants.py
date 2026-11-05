# Spent-When: PERMANENT(the plotting classes stop offering row selections)
# Supersedes: none
"""Invariants every plot class keeps, and every row selection it offers.

A plot keeps some of the rows its caller passes and can hand them back, by
their original labels, through its selection methods. Whatever a selection
returns, these hold, for every ``solarwindpy`` plot class (found by walking
``BinnedPlot`` and ``ColorPlot`` subclasses), every seeded case in
``tests.plotting._cases`` and every way the plot gets its bins (each ``nbins``
rule on the private path, explicit bins in a shared ``BinnedData``):

- I1: every selected label is a label of ``h.data``.
- I2: no selected label has NaN or +/-inf in the caller's x, y or z, nor 0
  on an axis the caller asked to be logged (``log10(0)`` is -inf), and the
  caller's mask keeps it.
- I3: the caller's values at those labels, as ``log10(abs())`` on the axes
  the caller asked to be logged, equal ``h.data`` there. Values a selection
  returns equal the caller's, in absolute value on a logged axis: a logged
  axis bins ``log10|v|``, so its sign is not part of what the plot carries.
- I4: counting the rows ``get_plotted_data_boolean_series`` keeps, bin by
  bin through ``h.cut``, gives ``agg(fcn="count")`` on the plotted bins.
- I5: the counts of ``project_1d`` equal the parent's counts summed over the
  other axis.

The expected values come from the caller's own inputs (I2, I3), from the
documented definitions of the plotted rows and bins counted here in plain
Python (I4), and from the identity that a projection's counts are the
marginal sums of the 2-D counts (I5).

Which public attributes are selections lives here, not in the library:
``SELECTIONS`` says how to call each one and ``EXEMPT`` why every other one is
not a selection. A guard fails on any public attribute of a plot class that
is in neither, so a new method is classified before it ships.
"""

import importlib
import pkgutil
from collections import Counter, namedtuple

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import solarwindpy  # noqa: E402
from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.base import BinnedPlot, ColorPlot  # noqa: E402
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
from tests.tolerances import exact  # noqa: E402


class InvariantViolation(AssertionError):
    """A selection broke I1 to I5."""


class UnclassifiedAttribute(AssertionError):
    """A public attribute of a plot class is in neither SELECTIONS nor EXEMPT."""


class StaleClassification(AssertionError):
    """SELECTIONS or EXEMPT names an attribute no plot class has."""


class VacuousFixture(AssertionError):
    """A fixture no longer lets an invariant fail."""


#: Cell-split threshold of ``SpiralPlot2D``'s mesh. Every case has
#: far fewer identical (x, y) points than this, so no cell splits forever.
MIN_PER_BIN = 40

# ---------------------------------------------------------------------------
# The plot classes
# ---------------------------------------------------------------------------


def _import_every_module():
    """Import every ``solarwindpy`` module, so the walk sees every plot class."""
    for info in pkgutil.walk_packages(solarwindpy.__path__, "solarwindpy."):
        importlib.import_module(info.name)


def _walk_plot_classes():
    """Every ``solarwindpy`` subclass of ``BinnedPlot`` or ``ColorPlot``."""
    _import_every_module()
    found, stack = set(), [BinnedPlot, ColorPlot]
    while stack:
        for sub in stack.pop().__subclasses__():
            if sub not in found:
                found.add(sub)
                stack.append(sub)
    return {cls for cls in found if cls.__module__.startswith("solarwindpy.")}


PLOT_CLASSES = _walk_plot_classes()


def _public_attributes(cls):
    """Public names of ``cls``: methods, properties and static methods."""
    return {name for name in dir(cls) if not name.startswith("_")}


# ---------------------------------------------------------------------------
# Building a plot from a case
# ---------------------------------------------------------------------------

#: A built plot with what the caller passed it: ``inputs`` maps each column of
#: ``h.data`` to the caller's series (None: the plot fills it with 1), ``log``
#: maps it to whether the caller asked for ``log10(abs())``, ``mask`` is the
#: caller's mask or None.
Build = namedtuple("Build", "h inputs log mask")


def _shared(case, axes, log, spec):
    """A ``BinnedData`` over the case's columns, its mask and clip, with explicit bins."""
    bins = nbins_spec(spec, case, axes, log)
    frame = pd.DataFrame({k: getattr(case, k) for k in axes})
    return BinnedData(
        frame,
        {k: bins for k in axes},
        log={k: log[k] for k in axes},
        clip={k: case.clip_data for k in axes},
        mask=case.mask,
    )


def _nbins(case, variant, axes, log):
    """``nbins`` and the private-path keywords for ``variant``."""
    path, spec = variant.split(":")
    if path == "shared":
        return _shared(case, axes, log, spec), {}
    return nbins_spec(spec, case, axes, log), {
        "clip": case.clip_data,
        "mask": case.mask,
    }


def _build_hist1d(case, variant):
    log = {"x": case.logx}
    nbins, kw = _nbins(case, variant, ("x",), log)
    if variant.startswith("private"):
        kw["logx"] = case.logx
    # Hist1D aggregates y in bins of x; the counts case has nothing to average.
    y = None if case.z is None else case.y
    h = Hist1D(case.x, y=y, nbins=nbins, **kw)
    # Hist1D stores y in linear units (its take_data_in_yrange_across_x docstring).
    return Build(h, {"x": case.x, "y": y}, {"x": case.logx, "y": False}, case.mask)


def _build_hist2d(case, variant):
    log = {"x": case.logx, "y": case.logy}
    nbins, kw = _nbins(case, variant, ("x", "y"), log)
    if variant.startswith("private"):
        kw.update(logx=case.logx, logy=case.logy)
    h = Hist2D(case.x, case.y, z=case.z, nbins=nbins, **kw)
    inputs = {"x": case.x, "y": case.y, "z": case.z}
    return Build(h, inputs, {**log, "z": False}, case.mask)


def _build_betar(case, variant):
    # BetaRPlot bins log10|beta| and log10|R| unless told otherwise.
    log = {"x": True, "y": True}
    nbins, kw = _nbins(case, variant, ("x", "y"), log)
    h = BetaRPlot(case.x, case.y, "p", z=case.z, nbins=nbins, **kw)
    inputs = {"x": case.x, "y": case.y, "z": case.z}
    return Build(h, inputs, {**log, "z": False}, case.mask)


def _build_scatter(case, variant):
    h = Scatter(case.x, case.y, z=case.z, clip=case.clip_data, mask=case.mask)
    inputs = {"x": case.x, "y": case.y, "z": case.z}
    return Build(h, inputs, {"x": False, "y": False, "z": False}, case.mask)


def _build_spiral(case, variant):
    _, spec = variant.split(":")
    log = {"x": case.logx, "y": case.logy}
    h = SpiralPlot2D(
        case.x,
        case.y,
        z=case.z,
        logx=case.logx,
        logy=case.logy,
        initial_bins=spiral_bins_spec(spec, case, log),
        clip=case.clip_data,
        mask=case.mask,
        min_per_bin=MIN_PER_BIN,
    )
    inputs = {"x": case.x, "y": case.y, "z": case.z}
    return Build(h, inputs, {**log, "z": False}, case.mask)


_HIST_VARIANTS = tuple(f"private:{s}" for s in NBINS) + (
    "shared:edges",
    "shared:intervals_left",
)

#: How to build each plot class, and the ways it gets its bins. Scatter has no
#: bins; SpiralPlot2D refuses a shared BinnedData (decision S).
BUILDERS = {
    Hist1D: (_build_hist1d, _HIST_VARIANTS),
    Hist2D: (_build_hist2d, _HIST_VARIANTS),
    BetaRPlot: (_build_betar, _HIST_VARIANTS),
    Scatter: (_build_scatter, ("private:none",)),
    SpiralPlot2D: (_build_spiral, tuple(f"private:{s}" for s in SPIRAL_NBINS)),
}


def build(cls, case, variant):
    """Build ``cls`` from ``case`` and check it logs the axes the caller asked for."""
    b = BUILDERS[cls][0](case, variant)
    for axis in ("x", "y"):
        if axis in b.h.data.columns and not isinstance(b.h, Hist1D):
            if b.h.log._asdict()[axis] != b.log[axis]:
                raise VacuousFixture(
                    f"{cls.__name__} log.{axis} is {b.h.log._asdict()[axis]}, "
                    f"the caller asked for {b.log[axis]}"
                )
    return b


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# Selections
# ---------------------------------------------------------------------------

#: What one call of a selection gives back. ``labels``: the selected rows.
#: ``values``: values it returns, in linear units, one column per column of
#: ``h.data`` they come from, or None. ``by_label``: True when ``values`` is
#: indexed by ``labels``; False when it holds the caller's values at
#: ``labels`` in ascending order, without labels.
Selection = namedtuple("Selection", "labels values by_label")


def _where(flags):
    """Labels of a boolean Series where it is True."""
    return flags.index[flags.to_numpy(dtype=bool)]


def _as_labels(taken, index):
    """An array of labels as an index of the same kind as ``index``."""
    if isinstance(index, pd.MultiIndex):
        if len(taken) == 0:
            return index[:0]
        return pd.MultiIndex.from_tuples(list(taken), names=index.names)
    return pd.Index(taken)


def _select_data(b):
    return [Selection(b.h.data.index, None, True)]


def _select_cut(b):
    return [Selection(b.h.cut.index, None, True)]


def _select_plotted(b):
    return [Selection(_where(b.h.get_plotted_data_boolean_series()), None, True)]


def _select_plotted_data(b):
    rows = b.h.get_plotted_data()
    return [Selection(rows.index, rows, True)]


def _select_above_threshold(b):
    # The median bin count: some bins reach it, some do not.
    threshold = b.h.agg(fcn="count").dropna().median()
    subset, kept = b.h.get_subset_above_threshold(threshold)
    labels = _where(kept)
    if not subset.index.sort_values().equals(labels.sort_values()):
        raise InvariantViolation(
            "get_subset_above_threshold returned a subset whose labels are not "
            "the rows its boolean series keeps"
        )
    return [Selection(labels, subset, True)]


def _select_above_contour(b):
    # The median aggregate: some bins reach it, some do not.
    level = b.h.agg().dropna().median()
    above = b.h.id_data_above_contour(level)
    return [Selection(above.index[above.notna().to_numpy()], None, True)]


def _select_in_yrange(b):
    h = b.h
    data = h.data
    y = data.y.to_numpy(dtype=float)
    y = y[np.isfinite(y)]
    # The middle 60% of the stored y; widened when y is constant (counts).
    bottom, top = np.percentile(y, [20.0, 80.0])
    if not bottom < top:
        bottom, top = bottom - 0.5, top + 0.5

    def x_bounds(interval, expected_logx):
        # The bins are on the stored scale, log10|x| when expected_logx.
        return interval.left, interval.right

    if isinstance(h, Hist2D):
        available = h.agg().unstack("x").columns

        def y_bounds(at_x, expected_logy):
            return at_x.bottom, at_x.top

    else:
        available = h.agg().index

        def y_bounds(at_x):
            return at_x.bottom, at_x.top

    ranges = pd.DataFrame({"bottom": bottom, "top": top}, index=available)
    taken = h.take_data_in_yrange_across_x(ranges, x_bounds, y_bounds)
    return [Selection(_as_labels(taken, data.index), None, True)]


def _select_cdf(b):
    h = b.h
    out = []
    for only_plotted in (True, False):
        cdf = h.construct_cdf(only_plotted=only_plotted)
        # The rows the docstring says the CDF is built from.
        keep = h.cut.loc[:, "x"].notna()
        if only_plotted:
            keep = keep & h.get_plotted_data_boolean_series()
        values = pd.DataFrame({"x": cdf.loc[:, "x"].to_numpy(dtype=float)})
        out.append(Selection(_where(keep), values, False))
    return out


def _select_projection(b):
    h = b.h
    out = []
    for axis in ("x", "y"):
        h1 = h.project_1d(axis)
        # The projection averages z, or the other axis when the caller gave no z.
        other = "z" if b.inputs["z"] is not None else ({"x", "y"} - {axis}).pop()
        d = h1.data
        x = d.loc[:, "x"]
        if h1.log.x:
            x = 10.0**x
        values = pd.DataFrame({axis: x, other: d.loc[:, "y"]})
        out.append(Selection(d.index, values, True))
    return out


#: Every public attribute that returns rows of the plot, and how to call it.
SELECTIONS = {
    "data": _select_data,
    "cut": _select_cut,
    "get_plotted_data_boolean_series": _select_plotted,
    "get_plotted_data": _select_plotted_data,
    "get_subset_above_threshold": _select_above_threshold,
    "id_data_above_contour": _select_above_contour,
    "take_data_in_yrange_across_x": _select_in_yrange,
    "construct_cdf": _select_cdf,
    "project_1d": _select_projection,
}

#: Every other public attribute of a plot class, and why it selects no rows.
EXEMPT = {
    "agg": "aggregates per bin or cell, not per row; I4 and I5 check its counts",
    "agg_axes": "name of the aggregated column",
    "alim": "aggregate limits, a setting",
    "alim_kind": "kind of the aggregate limits, a setting",
    "axnorm": "normalization key, a setting",
    "binning": "the cells rows are placed in, not rows",
    "clim": "count limits, a setting",
    "clip": "clip settings per axis",
    "clip_data": "static helper inherited from Base that clips the values it is "
    "given; it holds no plot rows",
    "edges": "the bin edges per axis, not rows",
    "get_border": "the top and bottom bins of each x column, not rows",
    "grouped": "groupby over bins or cells, not a selection of rows",
    "initial_bins": "the initial spiral edges, not rows",
    "intervals": "the bins per axis, not rows",
    "joint": "aggregated values indexed by bin, not by row label",
    "labels": "axis labels",
    "log": "log settings per axis",
    "logger": "the plot's logger",
    "make_joint_h2_h1_plot": "draws a figure",
    "make_plot": "draws a figure",
    "mesh": "the spiral mesh, cells not rows",
    "path": "output path",
    "plot_contours": "draws a figure",
    "plot_edges": "draws a figure",
    "plot_hist_with_contours": "draws a figure",
    "set_alim": "setter",
    "set_axnorm": "setter",
    "set_clim": "setter",
    "set_labels": "setter",
    "set_log": "setter",
}


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


def _caller(b, col, labels):
    """The caller's values of ``col`` at ``labels``, as floats; 1 where it gave none."""
    series = b.inputs[col]
    if series is None:
        return np.ones(len(labels))
    return series.reindex(labels).to_numpy(dtype=float)


def _assert_i1(b, sel, where):
    outside = sel.labels.difference(b.h.data.index)
    if outside.size:
        raise InvariantViolation(
            f"I1 {where}: {outside.size} selected labels are not in h.data, "
            f"e.g. {list(outside[:3])}"
        )


def _assert_i2(b, sel, where):
    for col in b.h.data.columns:
        if b.inputs.get(col) is None:
            continue
        values = _caller(b, col, sel.labels)
        bad = ~np.isfinite(values)
        if b.log[col]:
            bad |= values == 0
        if bad.any():
            raise InvariantViolation(
                f"I2 {where}: {bad.sum()} selected labels have NaN or inf in "
                f"the caller's {col}, after log10 where logged, e.g. "
                f"{list(sel.labels[bad][:3])}"
            )
    if b.mask is not None:
        kept = b.mask.reindex(sel.labels).eq(True).to_numpy()
        if not kept.all():
            raise InvariantViolation(
                f"I2 {where}: {(~kept).sum()} selected labels are excluded by "
                f"the caller's mask, e.g. {list(sel.labels[~kept][:3])}"
            )


def _assert_i3(b, sel, where):
    data = b.h.data.loc[sel.labels]
    for col in data.columns:
        expected = _caller(b, col, sel.labels)
        if b.log[col]:
            with np.errstate(divide="ignore"):
                expected = np.log10(np.abs(expected))
        actual = data.loc[:, col].to_numpy(dtype=float)
        assert actual == exact(expected), f"I3 {where}: h.data.{col}"


def _assert_returned_values(b, sel, where):
    for col in sel.values.columns:
        expected = _caller(b, col, sel.labels)
        if sel.by_label:
            actual = sel.values.loc[sel.labels, col].to_numpy(dtype=float)
        else:
            actual = sel.values.loc[:, col].to_numpy(dtype=float)
        if b.log[col]:
            expected, actual = np.abs(expected), np.abs(actual)
        if not sel.by_label:
            expected = np.sort(expected)
        assert actual == exact(expected), f"I3 {where}: returned {col}"


def _bin_key(key):
    """A bin label as a tuple with one interval per binned axis."""
    return key if isinstance(key, tuple) else (key,)


def _counts_by_bin(series):
    """Non-NaN, non-zero values of a Series indexed by bins, keyed by ``_bin_key``."""
    out = {}
    for key, value in zip(series.index, series.to_numpy(dtype=float)):
        if np.isfinite(value) and value != 0:
            out[_bin_key(key)] = value
    return out


def _sorted_keys(keys):
    return sorted(keys, key=lambda t: tuple((i.left, i.right) for i in t))


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------


def _params(classes, methods=None):
    out = []
    for cls in sorted(classes, key=lambda c: c.__name__):
        variants = BUILDERS[cls][1]
        names = (
            [None] if methods is None else sorted(m for m in methods if hasattr(cls, m))
        )
        for method in names:
            for case_name in CASES:
                for variant in variants:
                    values = (cls, case_name, variant)
                    ident = [cls.__name__, case_name, variant]
                    if methods is not None:
                        values = (cls, method, case_name, variant)
                        ident.insert(1, method)
                    out.append(pytest.param(*values, id="-".join(ident)))
    return out


SELECTION_PARAMS = _params(BUILDERS, SELECTIONS)
AGG_CLASSES = {cls for cls in BUILDERS if hasattr(cls, "cut")}
PROJECTING_CLASSES = {cls for cls in BUILDERS if hasattr(cls, "project_1d")}


# ---------------------------------------------------------------------------
# Completeness guards
# ---------------------------------------------------------------------------


def test_every_plot_class_has_a_builder():
    """The walk finds exactly the plot classes ``BUILDERS`` knows how to build.

    Guards the parametrized invariants against passing vacuously, and puts a
    new plot class under them.

    ON FAILURE: a plot class has no builder, or one no longer subclasses BinnedPlot or ColorPlot; add the builder, or restore the parent.
    """
    five = {Hist1D, Hist2D, BetaRPlot, Scatter, SpiralPlot2D}
    if not PLOT_CLASSES == set(BUILDERS) == five:
        raise UnclassifiedAttribute(
            f"walked {sorted(c.__qualname__ for c in PLOT_CLASSES)}, "
            f"builders {sorted(c.__qualname__ for c in BUILDERS)}"
        )


def test_every_public_attribute_of_every_plot_class_is_classified():
    """Each public attribute of each plot class is in ``SELECTIONS`` or ``EXEMPT``.

    ON FAILURE: a public attribute is unclassified; add it to SELECTIONS with how to call it, or to EXEMPT with why it selects no rows.
    """
    missing = sorted(
        f"{cls.__qualname__}.{name}"
        for cls in PLOT_CLASSES
        for name in _public_attributes(cls)
        if name not in SELECTIONS and name not in EXEMPT
    )
    if missing:
        raise UnclassifiedAttribute(f"unclassified: {missing}")


def test_no_classification_is_stale_or_doubled():
    """Every ``SELECTIONS`` and ``EXEMPT`` key is on a plot class, and in one of them.

    ON FAILURE: an attribute was removed or renamed; drop or rename its entry.
    """
    every = set().union(*(_public_attributes(cls) for cls in PLOT_CLASSES))
    stale = sorted((set(SELECTIONS) | set(EXEMPT)) - every)
    doubled = sorted(set(SELECTIONS) & set(EXEMPT))
    if stale or doubled:
        raise StaleClassification(f"stale: {stale}; in both: {doubled}")


@pytest.mark.parametrize(
    "cls, method",
    [
        pytest.param(cls, m, id=f"{cls.__name__}-{m}")
        for cls in sorted(BUILDERS, key=lambda c: c.__name__)
        for m in sorted(SELECTIONS)
        if hasattr(cls, m)
    ],
)
def test_each_selection_picks_some_rows_and_skips_the_nan_ones(cls, method):
    """On the ``nan_x`` case each selection returns rows, and none of the NaN ones.

    The caller's x is NaN on 40 of 400 rows, so a selection that let those
    rows through would break I2; a selection returning no rows would pass
    every invariant vacuously.

    ON FAILURE: the fixture no longer separates kept rows from NaN rows; fix the fixture.
    """
    case = CASES["nan_x"]
    variant = BUILDERS[cls][1][0]
    b = build(cls, case, variant)
    nan_labels = case.x.index[case.x.isna().to_numpy()]
    if nan_labels.size == 0:
        raise VacuousFixture("nan_x has no NaN in x")
    for sel in SELECTIONS[method](b):
        if sel.labels.size == 0:
            raise VacuousFixture(f"{method} selected no rows")
        if sel.labels.intersection(nan_labels).size:
            raise InvariantViolation(f"{method} selected rows whose x is NaN")


# ---------------------------------------------------------------------------
# I1 to I3: every selection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls, method, case_name, variant", SELECTION_PARAMS)
def test_selected_rows_are_kept_valid_and_hold_the_callers_values(
    cls, method, case_name, variant
):
    """Every selection obeys I1, I2 and I3 (see the module docstring).

    The expected values are the caller's own inputs at the selected labels.

    ON FAILURE: the code is wrong.
    """
    b = build(cls, CASES[case_name], variant)
    for n, sel in enumerate(SELECTIONS[method](b)):
        where = f"{cls.__name__}.{method} call {n}"
        _assert_i1(b, sel, where)
        _assert_i2(b, sel, where)
        _assert_i3(b, sel, where)
        if sel.values is not None:
            _assert_returned_values(b, sel, where)


# ---------------------------------------------------------------------------
# I4: plotted rows counted per bin
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls, case_name, variant", _params(AGG_CLASSES))
def test_plotted_rows_counted_per_bin_equal_the_count_aggregate(
    cls, case_name, variant
):
    """Counting the plotted rows bin by bin through ``cut`` gives ``agg("count")``.

    The plotted bins are the ones ``agg()`` leaves non-NaN, as
    ``get_plotted_data_boolean_series`` documents; the rows in each are
    counted here with ``collections.Counter`` over ``h.cut``.

    ON FAILURE: the code is wrong.
    """
    h = build(cls, CASES[case_name], variant).h
    plotted = _where(h.get_plotted_data_boolean_series())
    cut = h.cut.loc[plotted]
    counted = Counter(zip(*(cut.loc[:, k].tolist() for k in cut.columns)))

    plotted_bins = {_bin_key(k) for k in h.agg().dropna().index}
    counts = _counts_by_bin(h.agg(fcn="count"))
    expected = {k: v for k, v in counts.items() if k in plotted_bins}

    if set(counted) != set(expected):
        raise InvariantViolation(
            f"I4: plotted rows fall in {len(counted)} bins, agg plots "
            f"{len(expected)}; differing: "
            f"{_sorted_keys(set(counted) ^ set(expected))[:3]}"
        )
    keys = _sorted_keys(expected)
    assert [counted[k] for k in keys] == exact([expected[k] for k in keys])


# ---------------------------------------------------------------------------
# I5: a projection's counts are the parent's marginal counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cls, case_name, variant",
    _params(PROJECTING_CLASSES),
)
def test_projected_counts_equal_the_parents_counts_summed_over_the_other_axis(
    cls, case_name, variant
):
    """``project_1d(axis, project_counts=True)`` counts the parent's marginal.

    Identity: projecting the plotted rows onto one axis, each bin holds the
    sum of the parent's counts over the other axis. The sums are taken here
    in plain Python over ``agg(fcn="count")``.

    ON FAILURE: the code is wrong.
    """
    h = build(cls, CASES[case_name], variant).h
    parent = _counts_by_bin(h.agg(fcn="count"))
    for position, axis in enumerate(("x", "y")):
        expected = {}
        for key, value in parent.items():
            expected[(key[position],)] = expected.get((key[position],), 0) + value
        h1 = h.project_1d(axis, project_counts=True)
        got = _counts_by_bin(h1.agg(fcn="count"))
        if set(got) != set(expected):
            raise InvariantViolation(
                f"I5 {axis}: projection has {len(got)} non-empty bins, the "
                f"parent's marginal {len(expected)}; differing: "
                f"{_sorted_keys(set(got) ^ set(expected))[:3]}"
            )
        keys = _sorted_keys(expected)
        assert [got[k] for k in keys] == exact([expected[k] for k in keys]), axis


# ---------------------------------------------------------------------------
# SpiralPlot2D: every kept row is placed in the mesh
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls, case_name, variant", _params({SpiralPlot2D}))
def test_spiral_mesh_places_every_kept_row(cls, case_name, variant):
    """The constructor's mesh has one ``mesh.cat`` entry per row of ``data``.

    ON FAILURE: the code is wrong.
    """
    h = build(cls, CASES[case_name], variant).h
    if h.mesh.cat.size != len(h.data):
        raise InvariantViolation(
            f"mesh.cat has {h.mesh.cat.size} entries, data {len(h.data)} rows"
        )
