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


def _clip_kind(clip):
    r"""What a clip setting does: False, ``"l"``, ``"u"`` or True (both tails).

    Follows ``Base.clip_data``: a string starting with ``"l"`` or ``"u"``
    clips one tail, any other true value clips both.
    """
    if not clip:
        return False
    if isinstance(clip, str) and clip.lower()[0] in "lu":
        return clip.lower()[0]
    return True


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
        return {k: v.left.union(v.right) for k, v in self.intervals.items()}

    @property
    def categoricals(self):
        return dict(self._categoricals)

    @property
    def intervals(self):
        return {k: pd.IntervalIndex(v) for k, v in self.categoricals.items()}

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
        bins : array-like of pd.Interval
            The bins, e.g. an ``IntervalIndex`` or a categorical index of
            intervals.

        Returns
        -------
        pd.Series
            Each bin's width, indexed by ``bins``.
        """
        return pd.Series(pd.IntervalIndex(bins).length, index=bins)

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
            if given is not None and _clip_kind(given) != _clip_kind(held):
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

        data = self.data
        intervals = {}

        # An `IntervalIndex` keeps its edges unless the caller sets a precision.
        round_intervals = precision is not None
        if precision is None:
            precision = 5

        nbins = self._nbins_by_axis(nbins)

        for k in self._gb_axes:
            b = nbins[k]
            # Numpy and Astropy don't like NaNs when calculating bins.
            # Infinities in bins (typically from log10(0)) also create problems.
            d = data.loc[:, k].replace([-np.inf, np.inf], np.nan).dropna()

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
                    b = np.histogram_bin_edges(d, b)
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

            zipped = zip(b[:-1], b[1:])
            i = [pd.Interval(*b0b1, closed=closed) for b0b1 in zipped]

            intervals[k] = pd.CategoricalIndex(i)

        intervals = tuple(intervals.items())
        self._categoricals = intervals

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
        self._categoricals = tuple(
            (k, pd.CategoricalIndex(b.intervals(col))) for k, col in columns.items()
        )

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

    def _agg_reindexer(self, agg):
        # `self.grouped` uses `observed=True`: `observed=False` raised a TypeError
        # with mixed Categoricals and NaNs. (20200229)
        # Ensure all bins are represented in the data. (20190605)
        for k, v in self.categoricals.items():
            # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
            # Name the bins so a 1-D result keeps its axis name, e.g. "x".
            agg = agg.reindex(
                index=v.rename(k), level=k if agg.index.nlevels > 1 else None
            )

        return agg

    def agg(self, fcn=None, **kwargs):
        r"""Perform the aggregation along the agg axes.

        If either of the count limits specified in `clim` are not None, apply them.

        `fcn` allows you to specify a specific function for aggregation. Otherwise,
        automatically choose "count" or "mean" based on the uniqueness of the aggregated
        values.
        """
        cut = self.cut
        tko = self.agg_axes

        lbls = {k: str(v).replace("\n", " ") for k, v in self.labels._asdict().items()}
        self.logger.info(
            f"Starting {self.__class__.__name__!s} aggregation of ({tko}) in ({cut.columns.values})\n%s",
            "\n".join([f"""{k!s}: {v!s}""" for k, v in lbls.items()]),
        )

        gb = self.grouped

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
        cut = self.cut
        observed = []
        selected = []
        for k, v in cut.items():
            # Compare category codes: the Categoricals fail with some pandas numpy
            # ufuncs (20200611), and both sides are coded by the same categories.
            categories = v.cat.categories
            observed.append(v.cat.codes.to_numpy())
            selected.append(categories.get_indexer(kept.get_level_values(k)))

        observed = pd.MultiIndex.from_arrays(observed)
        selected = pd.MultiIndex.from_arrays(selected)
        return pd.Series(observed.isin(selected), index=cut.index)

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
        """
        agg = self.agg(fcn=fcn)
        tk = agg >= threshold
        tk = tk.loc[tk]

        tk_h2 = self._joint_bin_mask(tk.index)

        # Boolean selection returns a new frame; the stored data is untouched.
        subset = self.data.loc[tk_h2]
        for k, log in self.log._asdict().items():
            if log:
                subset.loc[:, k] = 10 ** subset.loc[:, k]

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
