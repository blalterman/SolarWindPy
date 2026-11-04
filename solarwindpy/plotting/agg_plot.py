#!/usr/bin/env python
r"""Abstract helpers for aggregated plotting.

These classes calculate bin edges, perform data aggregation, and provide
common functionality used by :mod:`solarwindpy` histogram plots.
"""

__all__ = [
    "AggPlot",
]

import numpy as np
import pandas as pd

from numbers import Integral, Number
from abc import abstractproperty, abstractmethod

try:
    from astropy.stats import knuth_bin_width
except ModuleNotFoundError:
    pass

from . import base
from . import binned


class AggPlot(base.Base):
    r"""ABC for aggregating data in 1D and 2D.

    Attributes
    ----------
    logger, data, bins, clip, cut, logx, labels.x, labels.y, clim, agg_axes
    path, _gb_axes (abstract)

    Methods
    -------
    set_<>:
        Set property <>.

    calc_bins, make_cut, agg, clip_data, make_plot
    __init__, set_labels.y, set_path, _set_data, _format_axis, make_plot (abstract)
    """

    @property
    def edges(self):
        r"""Bin edges per axis, a float ``pd.Index`` each.

        The edges the rows were binned by, as the plot's ``BinnedData`` stores
        them.
        """
        columns = self._bin_columns
        return {k: pd.Index(self._binned.edges(columns[k])) for k in self._gb_axes}

    @property
    def intervals(self):
        r"""Bins per axis, a ``pd.IntervalIndex`` each."""
        return dict(self._intervals)

    @property
    def categoricals(self):
        r"""Alias of ``intervals``: the bins per axis, a ``pd.IntervalIndex`` each."""
        return self.intervals

    @property
    def cut(self):
        r"""Bin of each row the plot keeps: a DataFrame of categoricals.

        One column per binned axis, indexed by the kept rows' labels. Built on
        each access from the bin codes.
        """
        on = self._cut_on()
        columns = self._bin_columns
        return pd.DataFrame(
            {k: self._binned.categorical(columns[k], on=on) for k in self._gb_axes},
            copy=False,
        )

    @property
    def clim(self):
        return self._clim

    @property
    def agg_axes(self):
        r"""The axis to aggregate into, e.g. the z variable in an (x, y, z) heatmap."""
        tko = [c for c in self._source.columns if c not in self._gb_axes]
        assert len(tko) == 1
        tko = tko[0]
        return tko

    @property
    def joint(self):
        r"""Combines the categorical and continuous data for `Groupby`."""
        cut = self.cut
        target = self._source.take(self.agg_axes)

        mi = pd.MultiIndex.from_frame(cut)
        return target.set_axis(mi)

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes."""

        target = self.joint
        gb_axes = list(self._gb_axes)
        gb = target.groupby(gb_axes, observed=True)

        return gb

    @property
    def axnorm(self):
        r"""Data normalization in plot.

        Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
        `make_plot`.
        """
        return self._axnorm

    @staticmethod
    def _bin_widths(bins):
        r"""Width of each bin in the binned variable.

        On a log axis the binned variable is ``log10`` of the data, so the
        widths are log10 widths and a density normalised by them integrates
        to 1 over the log axis.

        Parameters
        ----------
        bins : pd.IntervalIndex
            The bins.

        Returns
        -------
        pd.Series
            Each bin's width, indexed by ``bins``.
        """
        return pd.Series(bins.length, index=bins)

    @staticmethod
    def _divide_by_max(agg):
        r"""Divide ``agg`` by its maximum, so the peak equals 1.

        This is the ``"t"`` axis normalization shared by the histograms.

        Parameters
        ----------
        agg : pd.Series
            Aggregated values, one per bin.

        Returns
        -------
        pd.Series
            ``agg / agg.max()``.
        """
        return agg.divide(agg.max())

    def set_clim(self, lower=None, upper=None):
        """Set the minimum (lower) and maximum (upper) allowed number of.

        counts per bin to return after calling :py:meth:`agg`.
        """
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._clim = (lower, upper)

    _edges_from_intervals = staticmethod(binned._edges_from_intervals)

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

    def _inherit(self, nbins, names, log, clip, precision=None):
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
            Each axis's clip setting, as given (see ``_clip_by_axis``).
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
        columns = self._binned_columns(b, names)
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

    def calc_bins_intervals(self, nbins=101, precision=None):
        r"""Calculate histogram bins.

        nbins: int, str, array-like, BinnedData
            If a :class:`~solarwindpy.plotting.binned.BinnedData`, use its bins
            and bin codes for the columns named like the plot's inputs (e.g.
            ``x.name``); see ``_use_binned_data``.
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

        precision: int or None
            Decimal places to which bin edges are rounded. If None, 5, except
            that an ``IntervalIndex`` keeps its edges.

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
        self._shared_binned = None

        intervals = {}

        # An `IntervalIndex` keeps its edges unless the caller sets a precision.
        round_intervals = precision is not None
        if precision is None:
            precision = 5

        nbins = self._nbins_by_axis(nbins)
        finite = self._finite_by_axis(nbins)

        for k in self._gb_axes:
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
        r"""Each binned axis's finite values in ``data``, for computing its edges.

        Numpy and Astropy don't like NaNs when calculating bins. Infinities in
        bins (typically from log10(0)) also create problems. An axis whose
        specification is an ``IntervalIndex`` or edges gets None: its bins do
        not depend on the data, so values are taken only for a count or a
        rule.
        """
        given = {
            k: isinstance(nbins[k], pd.IntervalIndex) or np.ndim(nbins[k]) == 1
            for k in self._gb_axes
        }
        if all(given.values()):
            return dict.fromkeys(self._gb_axes)
        # The axes as ``data`` holds them, by position: edges need no labels.
        source = self._source
        return {
            k: (
                None
                if given[k]
                else source.logged(k, labels=False)
                .replace([-np.inf, np.inf], np.nan)
                .dropna()
            )
            for k in self._gb_axes
        }

    def _use_binned_data(self, b):
        r"""Take the bins and bin codes of each axis from the ``BinnedData`` ``b``.

        Each axis reads the column named like the input given for it (e.g.
        ``x.name``), on the rows of ``x.index``. The plot's own rows (no NaN,
        within ``mask``) are unchanged; a row ``b`` places in no bin, or
        excludes by its own mask, is in no bin of the plot either.

        The constructor already resolved the plot's log and clip from ``b``
        (``_inherit``); they are checked again here, so a later
        ``calc_bins_intervals(nbins=b)`` cannot bin by settings the plot's
        data does not have.

        Raises
        ------
        KeyError
            If ``b`` has no column of that name.
        ValueError
            If ``x.index`` is not a subset of ``b.index``, or the plot's log or
            clip setting for an axis differs from ``b``'s for its column.
        """
        names = self._bin_names
        columns = self._binned_columns(b, {k: names[k] for k in self._gb_axes})

        index = self._bin_index
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

        self._inherit(
            b,
            columns,
            {k: getattr(self.log, k) for k in columns},
            {k: getattr(self.clip, k) for k in columns},
        )

        self._shared_binned = b
        self._shared_columns = columns
        self._intervals = tuple((k, b.intervals(col)) for k, col in columns.items())

    def _bin_source(self):
        r"""Bin the plot's source by ``intervals`` into a private ``BinnedData``.

        The bins keep their closure and edges; the source's log and each
        axis's field of the plot's ``clip`` apply to that axis.
        """
        intervals = self.intervals
        clip = self.clip
        self._binned = self._source.binned(
            {k: intervals[k] for k in self._gb_axes},
            clip={k: getattr(clip, k) for k in self._gb_axes},
        )
        self._bin_columns = {k: k for k in self._gb_axes}

    def _cut_on(self):
        r"""The rows ``cut`` takes from ``self._binned``, as its ``on`` argument."""
        rows = self._source.rows
        if self._shared_binned is None:
            return rows
        index = self._source.index
        if index.equals(self._binned.index):
            return rows
        return index if rows is None else index[rows]

    def _nbins_by_axis(self, nbins):
        r"""Map each binned axis to its bin specification.

        A count, a rule, an ``IntervalIndex``, or edges apply to every axis;
        a sequence with one entry per axis gives each axis its own.

        Raises
        ------
        ValueError
            If ``nbins`` is neither a specification nor a sequence of them.
        """
        gb_axes = self._gb_axes
        single = isinstance(nbins, (str, pd.IntervalIndex)) or (
            isinstance(nbins, Integral) and not isinstance(nbins, bool)
        )
        if single:
            return {k: nbins for k in gb_axes}

        try:
            n_specs = len(nbins)
        except TypeError:
            raise ValueError(
                f"Unrecognized `nbins` {nbins!r} of type {type(nbins).__name__}: "
                "expected an int, a str, an IntervalIndex, bin edges, or one of "
                "these per axis."
            ) from None

        if n_specs == len(gb_axes):
            return dict(zip(gb_axes, nbins))
        return {k: nbins for k in gb_axes}

    def _warn_values_outside_bins(self, axis, finite, edges):
        r"""Warn how many finite values of ``axis`` fall outside ``edges``.

        Called when a bin rule's edges were computed from clipped data, so the
        values beyond the clip lie outside every bin and go uncounted. Such
        bins are right-closed: an integer bin count that exhausts memory does
        so again on the clipped data, so only a rule reaches here. A value is
        counted as ``make_cut`` bins it, after the axis's ``clip`` if set.
        """
        clip = getattr(self.clip, axis)
        if clip:
            finite = self.clip_data(finite, clip)
        inside = (finite > edges[0]) & (finite <= edges[-1])
        self.logger.warning(
            f"The bins for {axis!r} did not fit in memory, so they were computed "
            "from the data clipped to its 0.05th and 99.95th percentiles: "
            f"{int((~inside).sum())} of {finite.size} finite values lie outside "
            "the bins and are not counted."
        )

    def make_cut(self):
        r"""Assign the plot's rows to the bins in ``intervals``.

        ``cut`` then gives those rows' bins. With a shared ``BinnedData`` the
        rows were assigned when it was built, and its codes are used as they
        are.
        """
        b = self._shared_binned
        if b is None:
            self._bin_source()
        else:
            self._binned = b
            self._bin_columns = dict(self._shared_columns)

    def _kept_index(self):
        r"""Labels of the rows the plot keeps, the index of ``cut``."""
        rows = self._source.rows
        index = self._source.index
        return index if rows is None else index[rows]

    def _bin_codes(self):
        r"""Bin code of each kept row on each binned axis, -1 off the bins."""
        on = self._cut_on()
        columns = self._bin_columns
        return {k: self._binned.codes(columns[k], on=on) for k in self._gb_axes}

    def _grouped_by_bin(self):
        r"""The aggregated column on the binned rows, grouped by joint bin.

        The group keys are positions in the full bin grid of ``_bin_grid``:
        the joint bin's codes, the first axis's varying slowest.
        """
        intervals = self.intervals
        flat = None
        inside = None
        for k, codes in self._bin_codes().items():
            codes = codes.astype(np.intp)
            if flat is None:
                flat = codes
                inside = codes >= 0
            else:
                flat = flat * len(intervals[k]) + codes
                inside &= codes >= 0
        # By position: the groups are keyed by `flat`, never by row label.
        target = self._source.take(self.agg_axes, labels=False)
        if not inside.all():
            target = pd.Series(target.array[inside], name=target.name, copy=False)
            flat = flat[inside]
        return target.groupby(flat)

    def _bin_grid(self):
        r"""Every bin: an ``IntervalIndex`` in 1-D, their product in 2-D."""
        intervals = [self.intervals[k].rename(k) for k in self._gb_axes]
        if len(intervals) == 1:
            return intervals[0]
        return pd.MultiIndex.from_product(intervals, names=list(self._gb_axes))

    def agg(self, fcn=None, **kwargs):
        r"""Perform the aggregation along the agg axes.

        If either of the count limits specified in `clim` are not None, apply them.

        `fcn` allows you to specify a specific function for aggregation. Otherwise,
        automatically choose "count" or "mean" based on the uniqueness of the aggregated
        values.

        The occupied bins are normalized by ``_axis_normalizer``. Every bin is
        then in the result, indexed by its interval on each axis
        (``intervals``); a bin no row falls in is NaN.
        """
        tko = self.agg_axes

        lbls = {k: str(v).replace("\n", " ") for k, v in self.labels._asdict().items()}
        self.logger.info(
            f"Starting {self.__class__.__name__!s} aggregation of ({tko}) in ({list(self._gb_axes)})\n%s",
            "\n".join([f"""{k!s}: {v!s}""" for k, v in lbls.items()]),
        )

        gb = self._grouped_by_bin()

        if fcn is None:
            fcn = "count" if self._source.counts else "mean"

        agg = gb.agg(fcn, **kwargs)  # .loc[:, tko]

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
            cnt = gb.agg("count")  # .loc[:, tko]
            tk = pd.Series(True, index=agg.index)
            if c0 is not None:
                tk = tk & (cnt >= c0)
            if c1 is not None:
                tk = tk & (cnt <= c1)

            agg = agg.where(tk)

        # Normalize the occupied bins only, so sums over bins never see the
        # NaN of an empty one; then fill the grid.
        grid = self._bin_grid()
        agg = agg.set_axis(grid[agg.index.to_numpy()])
        agg = self._axis_normalizer(agg)
        return agg.reindex(grid)

    def _axis_normalizer(self, agg):
        r"""Normalize ``agg``, the occupied bins, by ``axnorm``; identity here."""
        return agg

    def _joint_bin_mask(self, kept):
        r"""Boolean ``pd.Series`` marking each observation whose joint bin is kept.

        Parameters
        ----------
        kept : pd.Index or pd.MultiIndex
            Aggregated bins to keep, with one named level per column of ``cut``.

        Returns
        -------
        pd.Series
            True where the observation's bin across every column of ``cut``
            (e.g. the joint (x, y) bin in 2-D) is in ``kept``.
        """
        intervals = self.intervals
        observed = []
        selected = []
        # Compare bin codes: both sides are positions in `intervals`.
        for k, codes in self._bin_codes().items():
            observed.append(codes)
            selected.append(intervals[k].get_indexer(kept.get_level_values(k)))

        observed = pd.MultiIndex.from_arrays(observed)
        selected = pd.MultiIndex.from_arrays(selected)
        return pd.Series(observed.isin(selected), index=self._kept_index())

    def get_plotted_data_boolean_series(self):
        """Return a boolean ``pd.Series`` identifying each plotted measurement.

        A measurement is plotted when its joint bin (e.g. its (x, y) bin in 2-D)
        survives aggregation. The series shares the same index as the stored
        data. To align with a different index you may need to adjust the
        returned series.
        """
        agg = self.agg().dropna()
        tk = self._joint_bin_mask(agg.index)

        self.logger.info(
            f"Taking {tk.sum()!s} ({100 * tk.mean():.1f}%) {self.__class__.__name__} spectra"
        )

        return tk

    def get_subset_above_threshold(self, threshold, fcn="count"):
        r"""Get the subset of data above a given threshold using `fcn` to.

        aggregate. If `axnorm` set, this is used. A row is kept when its joint
        bin (e.g. its (x, y) bin in 2-D) meets `threshold`.

        Returns
        -------
        subset : pd.DataFrame
            The kept rows, one column per column of ``data``, holding the
            values the caller passed: never logged, sign included, whatever
            ``log`` says.
        tk : pd.Series of bool
            True for each kept row, on the index of ``data``.
        """
        agg = self.agg(fcn=fcn)
        tk = agg >= threshold
        tk = tk.loc[tk]

        tk_h2 = self._joint_bin_mask(tk.index)

        # The source's values on the kept rows: no 10** round trip, so only
        # what was stored logged differs from `data`, and it is not inverted.
        source = self._source
        subset = pd.DataFrame(
            {k: source.take(k) for k in source.columns},
            index=self._kept_index(),
            copy=False,
        )
        subset = subset.loc[tk_h2.to_numpy(dtype=bool)]

        return subset, tk_h2

    @abstractproperty
    def _gb_axes(self):
        r"""The axes or columns over which the `groupby` aggregation takes place.

        1D cases aggregate over `x`. 2D cases aggregate over `x` and `y`.
        """
        pass

    @abstractmethod
    def set_axnorm(self, new):
        r"""The method by which the gridded data is normalized."""
        pass

    @staticmethod
    def _validate_axnorm(new, allowed):
        r"""Check an ``axnorm`` key and return it in its normalized form.

        Parameters
        ----------
        new : str or None
            The requested key. Matching is case-insensitive and exact.
        allowed : tuple of str
            The lowercase keys the calling class supports.

        Returns
        -------
        str or None
            ``None`` unchanged, otherwise the lowercase key.

        Raises
        ------
        TypeError
            If `new` is neither a string nor None.
        ValueError
            If `new` is not one of `allowed`.
        """
        if new is None:
            return None
        if not isinstance(new, str):
            raise TypeError(
                f"axnorm must be a string or None; got {type(new).__name__}"
            )
        key = new.lower()
        if key not in allowed:
            raise ValueError(
                f"Unrecognized axnorm '{new}'; expected one of: {', '.join(allowed)}"
            )
        return key
