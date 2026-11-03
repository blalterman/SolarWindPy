# Spent-When: PERMANENT(plot classes stop sourcing data through BinnedData)
# Supersedes: none
r"""The data a plot draws from, which of its rows it keeps, and their bins.

``_PlotSource`` holds the caller's columns without copying them and records,
once, which rows the plot uses (``rows``). ``BinnedData`` holds columns and
their bins, and assigns every row to a bin once. Everything else a plot shows
is derived from those on demand.

This module imports nothing from :mod:`solarwindpy.plotting`.
"""

__all__ = ["BinnedData"]

from collections.abc import Mapping
from numbers import Integral

import numpy as np
import pandas as pd


def _clip_to_quantiles(data, clip):
    r"""Clip data to its 0.01st and 99.99th percentiles.

    The one clipping rule every plot shares; ``Base.clip_data`` delegates here.

    Parameters
    ----------
    data : pd.Series or pd.DataFrame
        Data to clip. A DataFrame is clipped column by column.
    clip : bool or str
        A string starting with ``"l"`` or ``"u"`` selects the lower or upper
        tail only; any other value clips both tails.

    Returns
    -------
    pd.Series or pd.DataFrame
        The clipped data.

    Raises
    ------
    TypeError
        If ``data`` is neither a Series nor a DataFrame.
    """
    if isinstance(data, pd.Series):
        ax = 0
    elif isinstance(data, pd.DataFrame):
        ax = 1
    else:
        raise TypeError("Unexpected object %s" % type(data))

    q0 = 0.0001
    q1 = 0.9999
    pct = data.quantile([q0, q1])
    lo = pct.loc[q0]
    up = pct.loc[q1]

    if isinstance(clip, str) and clip.lower()[0] == "l":
        data = data.clip(lower=lo, axis=ax)
    elif isinstance(clip, str) and clip.lower()[0] == "u":
        data = data.clip(upper=up, axis=ax)
    else:
        data = data.clip(lo, up, axis=ax)
    return data


def _edges_from_intervals(intervals):
    """Return the edges of contiguous bins and the side they close on.

    The empty test comes first, and ``or`` short-circuits on it, so the
    contiguity test never sees empty intervals. That test alone would
    pass them: comparing ``intervals.left[1:]`` with
    ``intervals.right[:-1]`` gives an empty array, whose ``all()`` is
    True. Empty intervals would then reach ``intervals.right[-1]`` and
    raise :class:`IndexError` instead of the :class:`ValueError` below.

    Raises
    ------
    ValueError
        If the intervals are empty, not contiguous and increasing, or
        closed on neither or both sides.
    """
    if intervals.closed not in ("left", "right"):
        raise ValueError(
            f"Need intervals closed on the left or right, got {intervals.closed!r}."
        )
    if (
        intervals.empty
        or not intervals.is_monotonic_increasing
        or not (intervals.left[1:] == intervals.right[:-1]).all()
    ):
        raise ValueError(f"Need contiguous, increasing intervals, got {intervals}.")
    edges = np.append(intervals.left.to_numpy(), intervals.right[-1])
    return edges, intervals.closed


def _round_edges(edges, precision, enclose=None):
    r"""Round bin edges to ``precision`` decimal places.

    Parameters
    ----------
    edges : np.ndarray
        Increasing bin edges.
    precision : int
        Decimal places.
    enclose : pd.Series, optional
        The finite values the bins were computed from. If given, the outer
        edges are rounded outward so they enclose every value, as for edges
        from an integer bin count.

    Returns
    -------
    np.ndarray
        The rounded edges, a new array.
    """
    if enclose is None:
        return edges.round(precision)

    scale = 10.0**precision
    lo = np.floor(edges[0] * scale) / scale
    hi = np.ceil(edges[-1] * scale) / scale
    edges = edges.round(precision)
    edges[0] = lo if lo <= enclose.min() else lo - 1 / scale
    edges[-1] = hi if hi >= enclose.max() else hi + 1 / scale
    return edges


def _align(values, index, name):
    r"""Return ``values`` as a Series on ``index``, aligned by label.

    A Series is aligned by label, as assigning it to a DataFrame column does:
    labels of ``index`` missing from ``values`` get NaN. When the labels
    already match, the values are shared, not copied. Anything else is taken
    positionally.
    """
    if isinstance(values, pd.Series):
        if values.index.equals(index):
            values = values.set_axis(index)
        else:
            values = values.reindex(index)
        return values.rename(name)
    return pd.Series(values, index=index, name=name, copy=False)


def _has_one_distinct_value(values):
    r"""True if ``values`` hold exactly one distinct non-NaN value.

    Equals ``values.dropna().unique().size == 1``.
    """
    values = values.dropna()
    if values.empty:
        return False
    arr = values.to_numpy()
    if arr.dtype.kind in "biufcmM":
        return bool((arr == arr[0]).all())
    return values.unique().size == 1


class _PlotSource:
    r"""A plot's input columns and the rows it keeps.

    Parameters
    ----------
    coords : dict of str to pd.Series
        The binned or plotted coordinates, e.g. ``{"x": x, "y": y}``. They are
        combined with ``pd.DataFrame(coords, copy=False)``, so columns that
        share an index are held without copying.
    value_name : str
        Name of the column aggregated or coloured, e.g. ``"z"``.
    value : pd.Series, array-like, or None
        That column's values, aligned by label to the coordinates. None means
        every row has the value 1, which is generated on access, not stored.
    log : dict of str to bool, optional
        Columns that ``materialize`` returns as ``log10(abs())``.
    dropna : bool
        If True, keep only the rows where every column is non-NaN. If False,
        keep every row.
    owner : str
        Name of the plot class, used in the error message.
    mask : pd.Series of bool, optional
        The caller's selection, aligned by label to the coordinates' index:
        a row is kept only where it is True, in addition to ``dropna``.
    within : BinnedData, optional
        A shared ``BinnedData``: a row its own mask excludes is not kept
        either, so no kept row lacks a bin for that reason alone.

    Raises
    ------
    TypeError
        If ``mask`` is not a boolean ``pd.Series``.
    ValueError
        If ``dropna`` is True and no row is kept, or ``mask`` lacks a label
        of the index or holds NaN.

    Attributes
    ----------
    rows : np.ndarray of bool or None
        True for each kept row, in source order; None when every row is kept.
    counts : bool
        True when the value column has exactly one distinct non-NaN value on
        ``rows``: an aggregation without a function then counts, otherwise it
        averages. Decided once, here.
    """

    def __init__(
        self,
        coords,
        value_name,
        value=None,
        *,
        log=None,
        dropna,
        owner,
        mask=None,
        within=None,
    ):
        frame = pd.DataFrame(dict(coords), copy=False)
        index = frame.index
        if value is not None:
            value = _align(value, index, value_name)
        selected = _mask_rows(mask, index)
        if within is not None:
            shared = within._kept_on(index)
            if shared is not None:
                selected = shared if selected is None else selected & shared

        rows = selected
        if dropna:
            keep = frame.notna().all(axis=1).to_numpy()
            if value is not None:
                keep = keep & value.notna().to_numpy()
            if selected is not None:
                keep = keep & selected
            if not keep.any():
                raise ValueError(
                    "You can't build a %s with data that is exclusively NaNs" % owner
                )
            rows = None if keep.all() else keep

        self._frame = frame
        self._value_name = value_name
        self._value = value
        self._log = {k: bool(v) for k, v in (log or {}).items() if v}
        self._rows = rows

        if value is None:
            n_kept = index.size if rows is None else int(rows.sum())
            counts = n_kept > 0
        else:
            counts = _has_one_distinct_value(self.take(value_name))
        self._counts = counts

    @property
    def columns(self):
        r"""Column names: the coordinates, then the value column."""
        return tuple(self._frame.columns) + (self._value_name,)

    @property
    def index(self):
        r"""Labels of every row, kept or not."""
        return self._frame.index

    @property
    def rows(self):
        r"""Boolean ndarray of the kept rows, or None when all are kept."""
        return self._rows

    @property
    def counts(self):
        r"""True if aggregating without a function counts; False if it averages."""
        return self._counts

    def _frame_on_rows(self):
        frame = self._frame
        if self._rows is not None:
            frame = frame.loc[self._rows]
        return frame

    def _value_on(self, index):
        if self._value is None:
            return pd.Series(1, index=index, name=self._value_name)
        value = self._value
        if self._rows is not None:
            value = value.loc[self._rows]
        return value.set_axis(index)

    def take(self, col):
        r"""The source values of ``col`` on ``rows``, never logged.

        Parameters
        ----------
        col : str
            A name in ``columns``.

        Returns
        -------
        pd.Series
            Indexed by the kept rows' labels and named ``col``.
        """
        if col == self._value_name:
            if self._value is None:
                index = self._frame.index
                if self._rows is not None:
                    index = index[self._rows]
                return self._value_on(index)
            value = self._value
            if self._rows is not None:
                value = value.loc[self._rows]
            return value
        return self._frame_on_rows().loc[:, col]

    def binned(self, bins, *, clip=None):
        r"""A ``BinnedData`` over the coordinates, on ``rows``, logged as stored.

        Parameters
        ----------
        bins : dict of str to pd.IntervalIndex or array-like
            Bins per coordinate, as for ``BinnedData``.
        clip : dict of str to bool or str, optional
            Clipping per coordinate, as for ``BinnedData``.

        Returns
        -------
        BinnedData
            Rows outside ``rows`` have code -1.
        """
        frame = self._frame
        mask = None
        if self._rows is not None:
            mask = pd.Series(self._rows, index=frame.index, copy=False)
        log = {k: self._log.get(k, False) for k in bins}
        return BinnedData(frame, bins, log=log, clip=clip, mask=mask)

    def materialize(self):
        r"""Build the plot's ``data``: every column on ``rows``, logged where set.

        Returns
        -------
        pd.DataFrame
            A new frame on each call, columns in ``columns`` order.
        """
        frame = self._frame_on_rows()
        index = frame.index
        data = {}
        for k in frame.columns:
            v = frame.loc[:, k]
            if self._log.get(k, False):
                v = np.log10(np.abs(v))
            data[k] = v
        data[self._value_name] = self._value_on(index)
        return pd.DataFrame(data, index=index, copy=False)


_EXPLICIT_ONLY = (
    "BinnedData takes explicit bin edges or an IntervalIndex per column, got "
    "{spec!r} for {col!r}. An integer or string nbins depends on which rows are "
    "valid, so it stays per histogram: pass it to the plot's nbins instead."
)


def _per_column(setting, columns, name, default):
    r"""Map each column to its ``setting``, ``default`` where unset."""
    if setting is None:
        return {k: default for k in columns}
    if not isinstance(setting, Mapping):
        raise TypeError(
            f"{name} must be a mapping of column to value, got "
            f"{type(setting).__name__}."
        )
    unknown = [k for k in setting if k not in columns]
    if unknown:
        raise KeyError(f"{name} names columns that are not binned: {unknown!r}.")
    return {k: setting.get(k, default) for k in columns}


def _mask_rows(mask, index):
    r"""The positions ``mask`` keeps, as a boolean ndarray on ``index``.

    Returns None when ``mask`` is None or keeps every row.

    Raises
    ------
    TypeError
        If ``mask`` is not a boolean ``pd.Series``.
    ValueError
        If ``mask`` lacks a label of ``index``, holds NaN, or cannot be
        aligned because its labels repeat.
    """
    if mask is None:
        return None
    if not isinstance(mask, pd.Series):
        raise TypeError(
            "mask must be a boolean pd.Series aligned by label to the frame's "
            f"index, got {type(mask).__name__}."
        )
    if not mask.index.equals(index):
        if not mask.index.is_unique:
            raise ValueError(
                "mask's index differs from the frame's and repeats labels, so "
                "it cannot be aligned by label."
            )
        positions = mask.index.get_indexer(index)
        missing = positions == -1
        if missing.any():
            raise ValueError(
                f"mask lacks {int(missing.sum())} label(s) of the frame's index; "
                "a missing label is never treated as False."
            )
        mask = mask.iloc[positions]
    if mask.isna().any():
        raise ValueError(
            f"mask holds {int(mask.isna().sum())} NaN value(s); NaN is never "
            "treated as False."
        )
    if not pd.api.types.is_bool_dtype(mask.dtype) and not (
        mask.dtype == object and all(isinstance(v, (bool, np.bool_)) for v in mask)
    ):
        raise TypeError(f"mask must hold booleans, got dtype {mask.dtype}.")
    keep = mask.to_numpy(dtype=bool)
    if keep.all():
        return None
    return keep


def _code_dtype(nbins):
    r"""int8 for up to 127 bins, int16 above, wider beyond that."""
    for dtype in (np.int8, np.int16, np.int32):
        if nbins <= np.iinfo(dtype).max:
            return dtype
    return np.int64


def _read_only(arr):
    arr.flags.writeable = False
    return arr


class BinnedData:
    r"""Columns of a frame, their bins, and the bin of every row.

    The bin of each row is computed once, when the object is built, from the
    values the frame holds then.

    Parameters
    ----------
    frame : pd.DataFrame
        Holds the columns to bin. ``BinnedData`` keeps a copy-on-write view of
        those columns, ``frame.loc[:, list(bins)]``, never ``frame`` itself:
        editing ``frame`` in place afterwards changes neither the values held
        nor the bins assigned.
    bins : dict of str to pd.IntervalIndex or array-like
        Bins per column. An ``IntervalIndex`` of contiguous intervals closed on
        the left or right keeps its intervals and closure; edges give
        right-closed bins, ``(a, b]``. Integer or string bin rules are refused.
    log : dict of str to bool, optional
        Columns binned as ``log10(abs())``. Unlisted columns are linear.
    clip : dict of str to bool or str, optional
        Columns clipped to their 0.01st and 99.99th percentiles (over the rows
        ``mask`` keeps, after ``log``) before binning; ``"l"`` or ``"u"`` clips
        one tail only. Unlisted columns are not clipped.
    mask : pd.Series of bool, optional
        Rows to bin, aligned by label to ``frame.index``. Rows it excludes get
        code -1.
    precision : int, optional
        Decimal places to which edges are rounded. If None, 5 for edges, while
        an ``IntervalIndex`` keeps its edges.

    Raises
    ------
    TypeError
        If a column's bins are an integer or string bin rule, ``bins`` is not a
        mapping, or ``mask`` is not a boolean Series.
    KeyError
        If ``bins``, ``log`` or ``clip`` names a column ``frame`` lacks.
    ValueError
        If edges are not strictly increasing, intervals are not contiguous, or
        ``mask`` lacks a label or holds NaN.

    Notes
    -----
    A value is in a left-closed bin ``[a, b)``; as in :func:`numpy.histogram`,
    the last left-closed bin also holds its right edge. A right-closed bin is
    ``(a, b]``. NaN, +/-inf and values outside the edges get code -1.
    """

    def __init__(self, frame, bins, *, log=None, clip=None, mask=None, precision=None):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(
                f"frame must be a pd.DataFrame, got {type(frame).__name__}."
            )
        if not isinstance(bins, Mapping):
            raise TypeError(
                f"bins must be a mapping of column to bins, got {type(bins).__name__}."
            )
        columns = tuple(bins)
        unknown = [k for k in columns if k not in frame.columns]
        if unknown:
            raise KeyError(f"frame has no column(s) {unknown!r} to bin.")

        view = frame.loc[:, list(columns)]
        log = {k: bool(v) for k, v in _per_column(log, columns, "log", False).items()}
        clip = _per_column(clip, columns, "clip", False)
        clip = {k: False if v is None else v for k, v in clip.items()}
        keep = _mask_rows(mask, view.index)

        intervals = {}
        edges = {}
        codes = {}
        for k in columns:
            i, e = self._bins_of(k, bins[k], precision)
            intervals[k] = i
            edges[k] = _read_only(e)
            codes[k] = _read_only(
                self._assign(view.loc[:, k], e, i.closed, keep, log[k], clip[k])
            )

        self._frame = view
        self._keep = keep
        self._columns = columns
        self._log = log
        self._clip = clip
        self._intervals = intervals
        self._edges = edges
        self._codes = codes

    @staticmethod
    def _bins_of(col, spec, precision):
        r"""The ``IntervalIndex`` and numeric edges of one column's bins."""
        if isinstance(spec, pd.IntervalIndex):
            e, closed = _edges_from_intervals(spec)
            if precision is None:
                return spec, np.array(e)
            e = _round_edges(np.asarray(e), precision)
            return pd.IntervalIndex.from_breaks(e, closed=closed), e

        if isinstance(spec, (str, Integral, bool)) or np.ndim(spec) == 0:
            raise TypeError(_EXPLICIT_ONLY.format(spec=spec, col=col))

        e = np.asarray(spec)
        if e.ndim != 1 or e.size < 2:
            raise ValueError(
                f"Bin edges for {col!r} must be 1-D with at least 2 entries."
            )
        if not (np.diff(e) > 0).all():
            raise ValueError(f"Bin edges for {col!r} must increase strictly, got {e}.")
        e = _round_edges(e, 5 if precision is None else precision)
        if not (np.diff(e) > 0).all():
            raise ValueError(
                f"Bin edges for {col!r} are not distinct after rounding to "
                f"{precision} places: {e}."
            )
        return pd.IntervalIndex.from_breaks(e, closed="right"), e

    @staticmethod
    def _assign(values, edges, closed, keep, log, clip):
        r"""Bin code of every row of ``values``: -1 off the bins or the mask."""
        n_bins = edges.size - 1
        out = np.full(values.size, -1, dtype=_code_dtype(n_bins))
        if keep is not None:
            values = values.iloc[keep]
        if log:
            values = np.log10(np.abs(values))
        if clip:
            values = _clip_to_quantiles(values, clip)

        found = pd.cut(values, edges, right=(closed == "right"), labels=False)
        found = np.array(found, dtype=float)
        if closed == "left":
            # As in `np.histogram`, the last bin also holds its right edge.
            last = (values == edges[-1]).to_numpy(dtype=bool, na_value=False)
            found[last] = n_bins - 1
        inside = ~np.isnan(found)
        placed = np.full(found.size, -1, dtype=out.dtype)
        placed[inside] = found[inside]

        if keep is None:
            out[:] = placed
        else:
            out[keep] = placed
        return out

    def _kept_on(self, index):
        r"""Which labels of ``index`` this object's ``mask`` keeps.

        Returns a boolean ndarray on ``index``, or None when it keeps them
        all. A label absent from ``self.index`` counts as kept: whether the
        labels are a subset is the plot's check, not this one's. So is an
        index that differs from ``self.index`` while ``self.index`` repeats
        labels; that case returns None.
        """
        keep = self._keep
        if keep is None:
            return None
        own = self.index
        if index.equals(own):
            return keep
        if not own.is_unique:
            return None
        positions = own.get_indexer(index)
        found = positions != -1
        kept = np.ones(index.size, dtype=bool)
        kept[found] = keep[positions[found]]
        return None if kept.all() else kept

    def _check(self, col):
        if col not in self._codes:
            raise KeyError(f"{col!r} is not binned; binned columns: {self._columns!r}.")

    def _positions(self, on):
        r"""``on`` as a positional selector, or None for every row."""
        if on is None:
            return None
        index = self.index
        if isinstance(on, pd.Index):
            if on.equals(index):
                return None
            if not index.is_unique:
                raise ValueError(
                    "This BinnedData's index repeats labels, so rows cannot be "
                    "taken by label."
                )
            positions = index.get_indexer(on)
            if (positions == -1).any():
                raise ValueError("on is not a subset of this BinnedData's index.")
            return positions
        on = np.asarray(on)
        if on.dtype != bool or on.shape != (index.size,):
            raise ValueError(
                "on must be a pd.Index of labels or a boolean array with one "
                "entry per row."
            )
        return on

    @property
    def columns(self):
        r"""Names of the binned columns, in ``bins`` order."""
        return self._columns

    @property
    def index(self):
        r"""Row labels of the frame, all of them, including masked rows."""
        return self._frame.index

    def log_of(self, col):
        r"""True if ``col`` is binned as ``log10(abs())``."""
        self._check(col)
        return self._log[col]

    def clip_of(self, col):
        r"""The clip setting of ``col``: False, True, or a tail string."""
        self._check(col)
        return self._clip[col]

    def edges(self, col):
        r"""Bin edges of ``col``, a read-only ndarray."""
        self._check(col)
        return self._edges[col]

    def intervals(self, col):
        r"""Bins of ``col``, a ``pd.IntervalIndex``."""
        self._check(col)
        return self._intervals[col]

    def codes(self, col, on=None):
        r"""Bin of each row of ``col``, as positions in ``intervals(col)``.

        Parameters
        ----------
        col : str
            A binned column.
        on : pd.Index or boolean array, optional
            Rows to take, by label or by position. None takes every row.

        Returns
        -------
        np.ndarray
            Read-only, int8 up to 127 bins, int16 above. -1 marks NaN, +/-inf,
            a value outside the edges, or a row outside the mask.
        """
        self._check(col)
        codes = self._codes[col]
        positions = self._positions(on)
        if positions is None:
            return codes
        return _read_only(codes[positions])

    def categorical(self, col, on=None):
        r"""Bin of each row of ``col`` as a categorical of its interval.

        Equals ``pd.cut`` of the binned values by ``intervals(col)``, the
        last left-closed bin also holding its right edge.

        Parameters
        ----------
        col : str
            A binned column.
        on : pd.Index or boolean array, optional
            Rows to take, by label or by position. None takes every row.

        Returns
        -------
        pd.Series
            Categorical with ordered categories ``intervals(col)``, NaN where
            the code is -1, indexed by the rows' labels and named ``col``.
        """
        self._check(col)
        positions = self._positions(on)
        codes = self._codes[col]
        index = self.index
        if positions is not None:
            codes = codes[positions]
            index = index[positions]
        values = pd.Categorical.from_codes(
            codes, categories=self._intervals[col], ordered=True, validate=False
        )
        return pd.Series(values, index=index, name=col, copy=False)
