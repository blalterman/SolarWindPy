r"""Binning strategies: how a binned plot assigns its rows to cells.

A :class:`Binning` places each row a plot keeps in one cell, or in none, and
describes the cells: their index, their measure, and the ``axnorm`` keys they
support. :class:`FixedGrid` bins on edges chosen before the rows are placed,
in one or two dimensions. The adaptive mesh of
:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` is
:class:`~solarwindpy.plotting.spiral.AdaptiveMesh`.
"""

__all__ = [
    "Binning",
    "FixedGrid",
]

import numpy as np
import pandas as pd

from abc import ABC, abstractmethod
from numbers import Integral

try:
    from astropy.stats import knuth_bin_width
except ModuleNotFoundError:
    pass

from . import binned


class Binning(ABC):
    r"""Places each row a plot keeps in one cell, and describes the cells.

    Cells are numbered from 0 in the order of ``cells``. ``codes`` gives the
    cell of each kept row, so a plot aggregates by grouping on it.
    """

    @property
    @abstractmethod
    def allowed_axnorm(self):
        r"""The ``axnorm`` keys these cells support, lowercase."""

    @property
    @abstractmethod
    def cells(self):
        r"""Every cell, a ``pd.Index`` in code order."""

    @abstractmethod
    def codes(self):
        r"""Cell code of each kept row, by position: an int array, -1 in no cell."""

    @abstractmethod
    def cell_measure(self):
        r"""Size of each cell on the binned scale, an array in code order.

        A width in 1-D, an area in 2-D. On a log axis the binned variable is
        ``log10`` of the data, so the size is measured in ``log10``.
        """

    def describe(self):
        r"""One line naming how many cells there are, for a plot's ``repr``."""
        return f"{len(self.cells)} cells"

    def postfilter(self, agg):
        r"""Drop cells of ``agg``, indexed by cell code, that fail a quality filter.

        Identity here; a strategy with a cell filter sets the cells it drops
        to NaN.
        """
        return agg

    def normalize(self, agg, axnorm, positions):
        r"""Normalize ``agg``, the occupied cells, by ``axnorm``.

        Parameters
        ----------
        agg : pd.Series
            Aggregated values of the occupied cells.
        axnorm : str or None
            A key of ``allowed_axnorm``, or None.
        positions : np.ndarray
            Cell code of each entry of ``agg``.

        Returns
        -------
        pd.Series
            ``"t"`` divides by the maximum, so the peak equals 1. ``"d"``
            divides by the total and by each cell's ``cell_measure``, so the
            values integrate to 1 over the binned scale.

        Raises
        ------
        ValueError
            For any other key.
        """
        if axnorm is None:
            return agg
        if axnorm == "t":
            return agg.divide(agg.max())
        if axnorm == "d":
            return agg.divide(self.cell_measure()[positions] * agg.sum())
        raise ValueError(f"{type(self).__name__} cannot normalize by {axnorm!r}.")


class FixedGrid(Binning):
    r"""Bins on edges fixed before the rows are placed, in one or two dimensions.

    The cells of a 1-D grid are its ``pd.IntervalIndex``; those of a 2-D grid
    are the product of the x and y intervals, x varying slowest. The bins come
    from a count, a rule, edges, an ``IntervalIndex``, or a shared
    :class:`~solarwindpy.plotting.binned.BinnedData`; see ``__init__``.
    """

    def __init__(
        self, source, nbins, *, axes, precision, names, index, log, clip, logger
    ):
        r"""Compute the bins of each axis and assign the source's rows to them.

        Parameters
        ----------
        source : solarwindpy.plotting.binned._PlotSource
            The plot's data.
        nbins : int, str, array-like, pd.IntervalIndex or BinnedData
            If a :class:`~solarwindpy.plotting.binned.BinnedData`, use its
            bins and bin codes for the columns named like the plot's inputs
            (e.g. ``x.name``).
            If an integer (a Python or numpy int), use
            :func:`numpy.histogram_bin_edges` to calculate that many bins.
            If str and nbins == "knuth", use `astropy.stats.knuth_bin_width`
            to calculate optimal bin widths.
            If str and nbins != "knuth", use
            `np.histogram_bin_edges(data, bins=nbins)` to calculate bins.
            If a :class:`pandas.IntervalIndex` of contiguous intervals closed
            on the left or right, use those bins and that side, e.g. another
            histogram's ``intervals``. Its edges are rounded only when
            ``precision`` is given.
            If array-like with one entry per binned axis, each entry is that
            axis's specification; any other array-like is the bin edges.
        axes : tuple of str
            The binned axes, ``("x",)`` or ``("x", "y")``.
        precision : int or None
            Decimal places to which bin edges are rounded. If None, 5, except
            that an ``IntervalIndex`` keeps its edges.
        names : dict of str to str
            Each axis's input name, e.g. ``{"x": x.name}``, read from a
            ``BinnedData``.
        index : pd.Index or None
            The index of the plot's x input, matched to a ``BinnedData``'s.
        log : ~solarwindpy.plotting.base.LogAxes
            The plot's log settings.
        clip : ~solarwindpy.plotting.base.ClipAxes
            The plot's clip settings.
        logger : logging.Logger
            Receives the warning of values outside memory-clipped bins.

        Raises
        ------
        ValueError
            If ``nbins`` is none of the above, e.g. a float, a bool or None.
        TypeError
            If a per-axis sequence holds a ``BinnedData``: one ``BinnedData``
            bins every axis.

        Notes
        -----
        Edges from an integer ``nbins`` follow :func:`numpy.histogram`: the
        outer edges are rounded outward so they enclose every sample, and each
        bin is closed on the left, the last bin also on the right. An
        ``IntervalIndex`` keeps its closure, and a left-closed one also closes
        its last bin on the right, so another histogram's intervals reproduce
        its bins. Other ``nbins`` give right-closed bins, ``(a, b]``.

        A bin rule that asks for more bins than fit in memory (e.g. ``"fd"`` on
        data with an extreme outlier) is retried on the data clipped to its
        0.05th and 99.95th percentiles. The values outside the resulting bins
        are not counted, and a warning gives their number.
        """
        self._source = source
        self._axes = tuple(axes)
        self._names = names
        self._index = index
        self._log = log
        self._clip = clip
        self._logger = logger
        self._calc_intervals(nbins, precision)
        self._assign()

    # ------------------------------------------------------------------
    # Settings a shared BinnedData fixes before the plot's data is stored
    # ------------------------------------------------------------------

    @staticmethod
    def _binned_columns(b, names):
        r"""Map each axis to the column of ``b`` named like its input.

        Raises
        ------
        KeyError
            If ``b`` has no column of that name.
        """
        columns = {}
        for k, col in names.items():
            if col not in b.columns:
                raise KeyError(
                    f"The BinnedData has no column {col!r}, the name of {k}; "
                    f"its columns are {b.columns!r}."
                )
            columns[k] = col
        return columns

    @classmethod
    def resolve(cls, nbins, names, log, clip, precision=None):
        r"""Resolve each binned axis's log and clip setting.

        Without a ``BinnedData``, None means False. With one, None means the
        setting ``nbins`` holds for the column named like that axis's input,
        and a setting given explicitly must equal it.

        Parameters
        ----------
        nbins : object
            The plot's ``nbins``. Only a ``BinnedData`` is read.
        names : dict of str to str
            Each binned axis's input name, e.g. ``{"x": x.name}``.
        log : dict of str to bool or None
            ``logx``, ``logy`` per axis, as given.
        clip : dict of str to bool, str or None
            Each axis's clip setting, as given (see ``Base._clip_by_axis``).
        precision : int or None
            The plot's ``bin_precision``.

        Returns
        -------
        log, clip : dict
            The resolved settings per axis.

        Raises
        ------
        KeyError
            If ``nbins`` is a ``BinnedData`` without a column named like an
            input.
        ValueError
            If ``nbins`` is a ``BinnedData`` and an explicit log or clip
            setting differs from its setting for that column, or
            ``precision`` is not None.
        """
        if not isinstance(nbins, binned.BinnedData):
            log = {k: False if v is None else bool(v) for k, v in log.items()}
            clip = {k: False if v is None else v for k, v in clip.items()}
            return log, clip

        b = nbins
        if precision is not None:
            raise ValueError(
                f"bin_precision={precision!r} cannot round a BinnedData's edges, "
                "which are fixed when it is built; pass precision to the "
                "BinnedData instead."
            )
        columns = cls._binned_columns(b, names)
        resolved_log = {}
        resolved_clip = {}
        for k, col in columns.items():
            held = b.log_of(col)
            given = log.get(k)
            if given is not None and bool(given) != held:
                raise ValueError(
                    f"log{k}={bool(given)} conflicts with the BinnedData, which "
                    f"bins {col!r} with log={held}. Leave log{k} as None to "
                    "inherit it."
                )
            resolved_log[k] = held

            held = b.clip_of(col)
            given = clip.get(k)
            if given is not None and (
                binned._clip_kind(given) != binned._clip_kind(held)
            ):
                raise ValueError(
                    f"clip={given!r} for {k} conflicts with the BinnedData, which "
                    f"bins {col!r} with clip={held!r}. Leave clip as None to "
                    "inherit it."
                )
            resolved_clip[k] = held
        return resolved_log, resolved_clip

    # ------------------------------------------------------------------
    # The bins
    # ------------------------------------------------------------------

    _edges_from_intervals = staticmethod(binned._edges_from_intervals)

    def _calc_intervals(self, nbins, precision):
        r"""Compute each axis's ``IntervalIndex`` from ``nbins``; see ``__init__``."""
        # Checked before `_nbins_by_axis`: a BinnedData is never a per-axis spec.
        if isinstance(nbins, binned.BinnedData):
            self._use_binned_data(nbins)
            return
        if isinstance(nbins, (tuple, list)) and any(
            isinstance(b, binned.BinnedData) for b in nbins
        ):
            raise TypeError(
                "A BinnedData bins every axis: pass it as nbins itself, not "
                "inside a per-axis sequence."
            )
        self._shared = None

        intervals = {}

        # An `IntervalIndex` keeps its edges unless the caller sets a precision.
        round_intervals = precision is not None
        if precision is None:
            precision = 5

        nbins = self._nbins_by_axis(nbins)
        finite = self._finite_by_axis(nbins)

        for k in self._axes:
            b = nbins[k]
            d = finite[k]

            if isinstance(b, str):
                b = b.lower()

            # Edges from an integer bin count follow `np.histogram`'s convention.
            from_count = isinstance(b, Integral) and not isinstance(b, bool)

            closed = "right"
            clipped_for_memory = False
            given_intervals = isinstance(b, pd.IntervalIndex)
            if given_intervals:
                b, closed = self._edges_from_intervals(b)

            elif isinstance(b, str) and b == "knuth":
                try:
                    assert knuth_bin_width
                except NameError:
                    raise NameError("Astropy is unavailable.")

                dx, b = knuth_bin_width(d, return_bins=True)

            else:
                try:
                    # Edges given (``d`` is None) are only validated.
                    b = np.histogram_bin_edges(np.empty(0) if d is None else d, b)
                except MemoryError:
                    # Clip the extremely large values and extremely small outliers.
                    lo, up = d.quantile([0.0005, 0.9995])
                    b = np.histogram_bin_edges(d.clip(lo, up), b)
                    clipped_for_memory = True

            assert np.unique(b).size == b.size
            try:
                assert not np.isnan(b).any()
            except TypeError:
                assert not b.isna().any()

            if from_count:
                # Round the outer edges outward so they enclose every sample.
                b = binned._round_edges(b, precision, enclose=d)
                closed = "left"
            elif round_intervals or not given_intervals:
                b = binned._round_edges(b, precision)

            if clipped_for_memory:
                self._warn_values_outside_bins(k, d, b)

            intervals[k] = pd.IntervalIndex.from_breaks(b, closed=closed)

        self._intervals = tuple(intervals.items())

    def _finite_by_axis(self, nbins):
        r"""Each binned axis's finite values, for computing its edges.

        Numpy and Astropy don't like NaNs when calculating bins. Infinities in
        bins (typically from log10(0)) also create problems. An axis whose
        specification is an ``IntervalIndex`` or edges gets None: its bins do
        not depend on the data, so values are taken only for a count or a
        rule.
        """
        given = {
            k: isinstance(nbins[k], pd.IntervalIndex) or np.ndim(nbins[k]) == 1
            for k in self._axes
        }
        if all(given.values()):
            return dict.fromkeys(self._axes)
        # The axes as the plot's ``data`` holds them, by position: edges need
        # no labels.
        source = self._source
        return {
            k: (
                None
                if given[k]
                else source.logged(k, labels=False)
                .replace([-np.inf, np.inf], np.nan)
                .dropna()
            )
            for k in self._axes
        }

    def _nbins_by_axis(self, nbins):
        r"""Map each binned axis to its bin specification.

        A count, a rule, an ``IntervalIndex``, or edges apply to every axis;
        a sequence with one entry per axis gives each axis its own.

        Raises
        ------
        ValueError
            If ``nbins`` is neither a specification nor a sequence of them.
        """
        axes = self._axes
        single = isinstance(nbins, (str, pd.IntervalIndex)) or (
            isinstance(nbins, Integral) and not isinstance(nbins, bool)
        )
        if single:
            return {k: nbins for k in axes}

        try:
            n_specs = len(nbins)
        except TypeError:
            raise ValueError(
                f"Unrecognized `nbins` {nbins!r} of type {type(nbins).__name__}: "
                "expected an int, a str, an IntervalIndex, bin edges, or one of "
                "these per axis."
            ) from None

        if n_specs == len(axes):
            return dict(zip(axes, nbins))
        return {k: nbins for k in axes}

    def _warn_values_outside_bins(self, axis, finite, edges):
        r"""Warn how many finite values of ``axis`` fall outside ``edges``.

        Called when a bin rule's edges were computed from clipped data, so the
        values beyond the clip lie outside every bin and go uncounted. Such
        bins are right-closed: an integer bin count that exhausts memory does
        so again on the clipped data, so only a rule reaches here. A value is
        counted as the rows are binned, after the axis's ``clip`` if set.
        """
        clip = getattr(self._clip, axis)
        if clip:
            finite = binned._clip_to_quantiles(finite, clip)
        inside = (finite > edges[0]) & (finite <= edges[-1])
        self._logger.warning(
            f"The bins for {axis!r} did not fit in memory, so they were computed "
            "from the data clipped to its 0.05th and 99.95th percentiles: "
            f"{int((~inside).sum())} of {finite.size} finite values lie outside "
            "the bins and are not counted."
        )

    def _use_binned_data(self, b):
        r"""Take the bins and bin codes of each axis from the ``BinnedData`` ``b``.

        Each axis reads the column named like the input given for it (e.g.
        ``x.name``), on the rows of ``x.index``. The plot's own rows (no NaN,
        within ``mask``) are unchanged; a row ``b`` places in no bin, or
        excludes by its own mask, is in no bin of the plot either.

        The plot resolved its log and clip from ``b`` before storing its data
        (``resolve``); they are checked again here, so the rows are never
        binned by settings the plot's data does not have.

        Raises
        ------
        KeyError
            If ``b`` has no column of that name.
        ValueError
            If ``x.index`` is not a subset of ``b.index``, or the plot's log or
            clip setting for an axis differs from ``b``'s for its column.
        """
        names = self._names
        columns = self._binned_columns(b, {k: names[k] for k in self._axes})

        index = self._index
        if index is None:
            index = self._source.index
        if not index.equals(b.index):
            if not b.index.is_unique:
                raise ValueError(
                    "The BinnedData's index repeats labels and differs from x's "
                    "index, so x's rows cannot be found in it by label."
                )
            if not index.isin(b.index).all():
                raise ValueError("x's index is not a subset of the BinnedData's index.")

        self.resolve(
            b,
            columns,
            {k: getattr(self._log, k) for k in columns},
            {k: getattr(self._clip, k) for k in columns},
        )

        self._shared = b
        self._intervals = tuple((k, b.intervals(col)) for k, col in columns.items())
        self._shared_columns = columns

    def _assign(self):
        r"""Assign the source's rows to the bins in ``intervals``.

        Without a shared ``BinnedData`` the rows are binned into a private
        one: the bins keep their closure and edges, and the source's log and
        each axis's clip apply. With one, its codes are used as they are.
        """
        b = self._shared
        if b is None:
            intervals = self.intervals
            self._binned = self._source.binned(
                {k: intervals[k] for k in self._axes},
                clip={k: getattr(self._clip, k) for k in self._axes},
            )
            self._columns = {k: k for k in self._axes}
        else:
            self._binned = b
            self._columns = dict(self._shared_columns)

    # ------------------------------------------------------------------
    # What the grid exposes
    # ------------------------------------------------------------------

    @property
    def axes(self):
        r"""The binned axes, ``("x",)`` or ``("x", "y")``."""
        return self._axes

    @property
    def allowed_axnorm(self):
        r"""``d`` and ``t`` in 1-D; also the row and column norms in 2-D."""
        if len(self._axes) == 1:
            return ("d", "t")
        return ("c", "r", "t", "d", "cd", "rd")

    @property
    def binned(self):
        r"""The ``BinnedData`` holding the rows' bin codes, private or shared."""
        return self._binned

    @property
    def shared(self):
        r"""The shared ``BinnedData`` passed as ``nbins``, or None."""
        return self._shared

    @property
    def columns(self):
        r"""Each axis's column in ``binned``."""
        return dict(self._columns)

    @property
    def intervals(self):
        r"""Bins per axis, a ``pd.IntervalIndex`` each."""
        return dict(self._intervals)

    @property
    def edges(self):
        r"""Bin edges per axis, a float ``pd.Index`` each."""
        columns = self._columns
        return {k: pd.Index(self._binned.edges(columns[k])) for k in self._axes}

    @property
    def cells(self):
        r"""Every bin: an ``IntervalIndex`` in 1-D, their product in 2-D."""
        intervals = [self.intervals[k].rename(k) for k in self._axes]
        if len(intervals) == 1:
            return intervals[0]
        return pd.MultiIndex.from_product(intervals, names=list(self._axes))

    def describe(self):
        r"""Bins per axis, e.g. ``"x: 4, y: 3"``, for a plot's ``repr``."""
        return ", ".join(f"{k}: {len(self.intervals[k])}" for k in self._axes)

    def cell_measure(self):
        r"""Each bin's width in 1-D, its area in 2-D, on the binned scale."""
        widths = [np.asarray(self.intervals[k].length) for k in self._axes]
        if len(widths) == 1:
            return widths[0]
        return np.outer(*widths).ravel()

    def _cut_on(self):
        r"""The rows taken from ``binned``, as its ``on`` argument."""
        rows = self._source.rows
        if self._shared is None:
            return rows
        index = self._source.index
        if index.equals(self._binned.index):
            return rows
        return index if rows is None else index[rows]

    def axis_codes(self):
        r"""Bin code of each kept row on each axis, -1 off the bins."""
        on = self._cut_on()
        columns = self._columns
        return {k: self._binned.codes(columns[k], on=on) for k in self._axes}

    def codes(self):
        r"""Position of each kept row's joint bin in ``cells``, -1 in none.

        The first axis varies slowest.
        """
        intervals = self.intervals
        flat = None
        inside = None
        for k, codes in self.axis_codes().items():
            codes = codes.astype(np.intp)
            if flat is None:
                flat = codes.copy()
                inside = codes >= 0
            else:
                flat = flat * len(intervals[k]) + codes
                inside &= codes >= 0
        flat[~inside] = -1
        return flat

    def cut(self):
        r"""Bin of each kept row: a DataFrame of categoricals, one column per axis."""
        on = self._cut_on()
        columns = self._columns
        return pd.DataFrame(
            {k: self._binned.categorical(columns[k], on=on) for k in self._axes},
            copy=False,
        )

    def normalize(self, agg, axnorm, positions):
        r"""Normalize ``agg`` by ``axnorm``, including the 2-D row and column norms.

        ===== =============================================================
         key                           description
        ===== =============================================================
         c     Column normalize: divide by each column's maximum
         r     Row normalize: divide by each row's maximum
         t     Divide by the maximum (peak equals 1)
         d     Density normalize over the binned scale
         cd    A PDF in each column
         rd    A PDF in each row
        ===== =============================================================

        On a log axis the densities ("d", "cd", "rd") are normalized over
        ``log10`` of that axis: the bins are log-space intervals, so cell
        areas on the log axes sum to 1.
        """
        if axnorm == "c":
            return agg.divide(agg.groupby(level="x").max(), level="x")
        if axnorm == "r":
            return agg.divide(agg.groupby(level="y").max(), level="y")
        if axnorm == "cd":
            N = agg.groupby(level="x").sum()
            dy = self._widths("y")
            # Divide by the total in each column and each row's width.
            return agg.divide(N, level="x").divide(dy, level="y")
        if axnorm == "rd":
            N = agg.groupby(level="y").sum()
            dx = self._widths("x")
            # Divide by the total in each row and each column's width.
            return agg.divide(N, level="y").divide(dx, level="x")
        return super().normalize(agg, axnorm, positions)

    def _widths(self, axis):
        r"""Width of each bin of ``axis``, a Series indexed by its intervals."""
        bins = self.intervals[axis]
        return pd.Series(bins.length, index=bins)
