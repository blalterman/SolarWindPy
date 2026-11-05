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

#: The clip strings, in lower case, and the tail each one clips.
_CLIP_STRINGS = {"l": "l", "lower": "l", "u": "u", "upper": "u", "both": True}


def _clip_kind(clip):
    r"""What a clip setting clips: False, ``"l"``, ``"u"`` or True (both tails).

    A string must be ``"l"``, ``"lower"``, ``"u"``, ``"upper"`` or ``"both"``,
    in any case. Any other value is read by its truth: False (or None) clips
    nothing, True both tails.

    Raises
    ------
    ValueError
        If ``clip`` is any other string, the empty string included.
    """
    if isinstance(clip, str):
        try:
            return _CLIP_STRINGS[clip.lower()]
        except KeyError:
            raise ValueError(
                f"clip={clip!r} is not a clip setting: a clip string must be "
                "'l', 'lower', 'u', 'upper' or 'both' (any case)."
            ) from None
    return bool(clip)


def _clip_to_quantiles(data, clip):
    r"""Clip data to its 0.01st and 99.99th percentiles.

    The one clipping rule every plot shares; ``Base.clip_data`` delegates here.
    The percentiles are computed over the finite values only: NaN and +/-inf
    are left out, so an infinity cannot make a percentile infinite or NaN.
    The infinities are then clipped like any other value beyond a
    percentile: +inf to the upper one, -inf to the lower one, when that tail
    is clipped. NaN stays NaN. A column with no finite value is unchanged.

    Parameters
    ----------
    data : pd.Series or pd.DataFrame
        Data to clip. A DataFrame is clipped column by column.
    clip : bool or str
        ``"l"`` or ``"lower"`` clips the lower tail only, ``"u"`` or
        ``"upper"`` the upper tail only, in any case; ``"both"`` and any
        value that is not a string clip both tails.

    Returns
    -------
    pd.Series or pd.DataFrame
        The clipped data.

    Raises
    ------
    TypeError
        If ``data`` is neither a Series nor a DataFrame.
    ValueError
        If ``clip`` is any other string.
    """
    kind = _clip_kind(clip)
    if isinstance(data, pd.Series):
        ax = 0
    elif isinstance(data, pd.DataFrame):
        ax = 1
    else:
        raise TypeError("Unexpected object %s" % type(data))

    q0 = 0.0001
    q1 = 0.9999
    pct = data.replace([-np.inf, np.inf], np.nan).quantile([q0, q1])
    lo = pct.loc[q0]
    up = pct.loc[q1]

    if kind == "l":
        data = data.clip(lower=lo, axis=ax)
    elif kind == "u":
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
        from an integer bin count. Where ``10**-precision`` is below the
        float spacing of the data, no step of it moves an edge, and an outer
        edge is then the data's own extreme.

    Returns
    -------
    np.ndarray
        The rounded edges, a new array.
    """
    if enclose is None:
        return edges.round(precision)

    scale = 10.0**precision
    vmin = enclose.min()
    vmax = enclose.max()
    lo = np.floor(edges[0] * scale) / scale
    hi = np.ceil(edges[-1] * scale) / scale
    edges = edges.round(precision)
    edges[0] = min(lo if lo <= vmin else lo - 1 / scale, vmin)
    edges[-1] = max(hi if hi >= vmax else hi + 1 / scale, vmax)
    return edges


def _ambiguous_alignment(names):
    r"""The ValueError for columns that repeat labels and must be aligned."""
    return ValueError(
        f"{list(names)!r} repeat index labels and the indexes of the plot's "
        "columns differ, so aligning them by label is ambiguous. Give every "
        "column the same index, or drop the repeated labels."
    )


def _align(values, index, name):
    r"""Return ``values`` as a Series on ``index``, aligned by label.

    A Series is aligned by label, as assigning it to a DataFrame column does:
    labels of ``index`` missing from ``values`` get NaN. When the labels
    already match, the values are shared, not copied. Anything else is taken
    positionally.

    Raises
    ------
    ValueError
        If ``values`` is a Series whose index differs from ``index`` and
        repeats a label: which of its rows a label of ``index`` takes is
        ambiguous.
    """
    if isinstance(values, pd.Series):
        if values.index.equals(index):
            values = values.set_axis(index)
        elif not values.index.is_unique:
            raise _ambiguous_alignment([name])
        else:
            values = values.reindex(index)
        return values.rename(name)
    return pd.Series(values, index=index, name=name, copy=False)


def _combine(coords):
    r"""``pd.DataFrame(coords, copy=False)``, the columns aligned by label.

    Raises
    ------
    ValueError
        If the indexes differ and a column that pandas has to align repeats
        a label, naming every coordinate that repeats one.
    """
    try:
        return pd.DataFrame(coords, copy=False)
    except ValueError as err:
        series = {k: v for k, v in coords.items() if isinstance(v, pd.Series)}
        indexes = [v.index for v in series.values()]
        differ = any(not i.equals(indexes[0]) for i in indexes[1:])
        repeated = [k for k, v in series.items() if not v.index.is_unique]
        if not (differ and repeated):
            raise
        raise _ambiguous_alignment(repeated) from err


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


def _numeric_if_object(values):
    r"""An object-dtype Series of numbers as the numeric Series it holds.

    ``infer_objects`` gives the dtype the values share; a numeric one
    (integer, float or bool) is returned, so NaN, +/-inf, ``log10`` and
    binning treat the column as they treat a numeric one. Any other value,
    and an object column whose values are not all numbers (strings,
    timestamps, a mix), is returned unchanged.
    """
    if not (isinstance(values, pd.Series) and values.dtype == object):
        return values
    inferred = values.infer_objects()
    if inferred.dtype.kind in "iufb":
        return inferred
    return values


def _usable(values, log):
    r"""True where a value is neither NaN nor +/-inf, as the plot holds it.

    On a logged column the plot holds ``log10(abs(v))``, which is -inf where
    ``v`` is 0 and finite for every other finite ``v``, so 0 is not usable
    there either. A column whose dtype is neither float nor integer is only
    tested for NaN; ``_PlotSource`` first turns an object column of numbers
    into the numeric column it holds (``_numeric_if_object``).

    Parameters
    ----------
    values : pd.Series
        One column.
    log : bool
        True if the column is held as ``log10(abs())``.

    Returns
    -------
    np.ndarray of bool
        A new array, one entry per value.
    """
    kind = values.dtype.kind
    if kind == "f":
        arr = values.to_numpy(dtype=np.float64, na_value=np.nan)
        keep = np.isfinite(arr)
    elif kind in "iub":
        arr = values.to_numpy()
        keep = np.ones(arr.size, dtype=bool)
    else:
        return values.notna().to_numpy()
    if log:
        keep &= arr != 0
    return keep


class _PlotSource:
    r"""A plot's input columns and the rows it keeps.

    A row is kept only where no coordinate and not the value is NaN or
    +/-inf (how="any"), each logged coordinate is finite after
    ``log10(abs())`` (so not 0), ``mask`` keeps it, and ``within`` keeps it.

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
    owner : str
        Name of the plot class, used in the error message.
    mask : pd.Series of bool, optional
        The caller's selection, aligned by label to the coordinates' index:
        a row is kept only where it is True.
    within : BinnedData, optional
        A shared ``BinnedData``: a row its own mask excludes is not kept
        either, so no kept row lacks a bin for that reason alone.

    Raises
    ------
    TypeError
        If ``mask`` is not a boolean ``pd.Series``.
    ValueError
        If no row is kept, or ``mask`` lacks a label of the index or holds
        NaN.

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
        owner,
        mask=None,
        within=None,
    ):
        frame = _combine({k: _numeric_if_object(v) for k, v in dict(coords).items()})
        index = frame.index
        if value is not None:
            value = _numeric_if_object(_align(value, index, value_name))
        selected = _mask_rows(mask, index)
        if within is not None:
            shared = within._kept_on(index)
            if shared is not None:
                selected = shared if selected is None else selected & shared

        log = {k: bool(v) for k, v in (log or {}).items()}
        # A row is kept only if no column is NaN or +/-inf as the plot holds
        # it, after log10 on a logged coordinate (how="any").
        keep = np.ones(index.size, dtype=bool)
        for k in frame.columns:
            keep &= _usable(frame.loc[:, k], log.get(k, False))
        if value is not None:
            keep &= _usable(value, False)
        if selected is not None:
            keep = keep & selected
        if not keep.any():
            raise ValueError(
                "You can't build a %s with data that is exclusively NaNs or "
                "infinite values" % owner
            )
        rows = None if keep.all() else keep

        self._frame = frame
        self._value_name = value_name
        self._value = value
        # The coordinates whose log setting, True or False, the rows, the
        # data and any bins were built on.
        self._log_columns = tuple(log)
        self._log = {k: v for k, v in log.items() if v}
        self._rows = rows

        self._n_kept = index.size if rows is None else int(rows.sum())

        if value is None:
            counts = self._n_kept > 0
        else:
            counts = _has_one_distinct_value(self.take(value_name, labels=False))
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
    def n_kept(self):
        r"""Number of rows the plot keeps."""
        return self._n_kept

    @property
    def has_value(self):
        r"""True if the caller gave the aggregated column; False for a count."""
        return self._value is not None

    def is_logged(self, col):
        r"""True if ``col`` is held as ``log10(abs())``."""
        return bool(self._log.get(col, False))

    @property
    def log_columns(self):
        r"""Coordinates given a log setting, True or False, when built.

        Their kept rows and values, and so the bins of a plot on them,
        depend on that setting.
        """
        return self._log_columns

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

    def take(self, col, *, labels=True):
        r"""The source values of ``col`` on ``rows``, never logged.

        Parameters
        ----------
        col : str
            A name in ``columns``.
        labels : bool, optional
            If False, the values are indexed by position (a ``RangeIndex``)
            instead of by the kept rows' labels, which are then not copied.
            For callers that use the values by position only.

        Returns
        -------
        pd.Series
            Indexed by the kept rows' labels, or by position if ``labels`` is
            False, and named ``col``.
        """
        rows = self._rows
        if col == self._value_name and self._value is None:
            if labels:
                index = self._frame.index
                if rows is not None:
                    index = index[rows]
            else:
                index = pd.RangeIndex(self._n_kept)
            return self._value_on(index)
        if col == self._value_name:
            values = self._value
        else:
            values = self._frame.loc[:, col]
        if labels:
            return values if rows is None else values.loc[rows]
        if rows is None:
            return values.set_axis(pd.RangeIndex(values.size))
        return pd.Series(values.array[rows], name=values.name, copy=False)

    def logged(self, col, *, labels=True):
        r"""A coordinate on ``rows`` as ``materialize`` returns it.

        Parameters
        ----------
        col : str
            A coordinate name.
        labels : bool, optional
            As for ``take``.

        Returns
        -------
        pd.Series
            ``take(col, labels=labels)``, as ``log10(abs())`` where ``log``
            sets it. When every row is kept, ``col`` is not logged and
            ``labels`` is True, it shares the source's values and index.
        """
        values = self.take(col, labels=labels)
        if self.is_logged(col):
            values = np.log10(np.abs(values))
        return values

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


def _guess_and_check_codes(arr, edges, closed):
    r"""``searchsorted(edges, arr) - 1`` for floats, -1 outside the edges or NaN.

    Each value's bin is guessed by linear interpolation between the outer
    edges, then checked against that bin's own two edges with the comparison
    ``searchsorted`` makes; only values whose guess fails are searched. The
    result is therefore exactly ``searchsorted``'s, and as fast as the guess
    is good: for even edges, nearly every guess holds.

    Parameters
    ----------
    arr : np.ndarray of float
        Values to bin.
    edges : np.ndarray of float
        Strictly increasing, finite bin edges.
    closed : {"left", "right"}
        The side each bin is closed on.

    Returns
    -------
    np.ndarray of np.int64
        A new array: the bin of each value, or -1.
    """
    n_bins = edges.size - 1
    lo, hi = edges[0], edges[-1]
    if closed == "right":
        side = "left"
        inside = (arr > lo) & (arr <= hi)
    else:
        side = "right"
        inside = (arr >= lo) & (arr < hi)

    guess = arr - lo
    guess *= n_bins / (hi - lo)
    np.clip(guess, 0, n_bins - 1, out=guess)
    np.copyto(guess, 0, where=~inside)
    out = guess.astype(np.int64)

    below, above = edges[out], edges[out + 1]
    if closed == "right":
        wrong = (arr <= below) | (arr > above)
    else:
        wrong = (arr < below) | (arr >= above)
    wrong &= inside
    if wrong.any():
        out[wrong] = np.searchsorted(edges, arr[wrong], side=side) - 1
    out[~inside] = -1
    return out


def _cut_codes(values, edges, closed):
    r"""Position of each value's bin in ``edges``, -1 where it has none.

    Equals ``pd.cut(values, edges, right=(closed == "right"), labels=False)``
    with NaN as -1, except that, as in :func:`numpy.histogram`, the last
    left-closed bin also holds its right edge, and that +/-inf is -1 even
    where an edge is infinite. A float or signed-integer
    column is searched directly, as ``pd.cut`` searches it; any other dtype
    goes through ``pd.cut``.

    Parameters
    ----------
    values : pd.Series
        Values to bin.
    edges : np.ndarray
        Strictly increasing bin edges.
    closed : {"left", "right"}
        The side each bin is closed on.

    Returns
    -------
    np.ndarray of np.int64
        A new array, one code per value.
    """
    n_bins = edges.size - 1
    arr = values.to_numpy() if isinstance(values, pd.Series) else np.asarray(values)
    if arr.dtype.kind == "f" and edges.dtype.kind == "f" and np.isfinite(edges).all():
        out = _guess_and_check_codes(arr, edges, closed)
        last = arr == edges[-1]
    elif arr.dtype.kind in "fi":
        # `pd.cut`'s own rule: `searchsorted` on the edges, then no bin at
        # either end or for NaN.
        side = "left" if closed == "right" else "right"
        ids = np.searchsorted(edges, arr, side=side)
        out = ids - 1
        off = (ids == 0) | (ids == edges.size)
        if arr.dtype.kind == "f":
            off |= np.isnan(arr)
        out[off] = -1
        last = arr == edges[-1]
    else:
        values = pd.Series(values, copy=False)
        found = pd.cut(values, edges, right=(closed == "right"), labels=False)
        found = np.array(found, dtype=float)
        out = np.full(found.size, -1, dtype=np.int64)
        inside = ~np.isnan(found)
        out[inside] = found[inside]
        last = (values == edges[-1]).to_numpy(dtype=bool, na_value=False)
    if closed == "left":
        # As in `np.histogram`, the last bin also holds its right edge.
        out[last] = n_bins - 1
    if arr.dtype.kind == "f":
        # +/-inf is in no bin, even where an edge is infinite.
        out[np.isinf(arr)] = -1
    return out


def _read_only(arr):
    arr.flags.writeable = False
    return arr


class BinnedData:
    r"""Columns of a frame, their bins, and the bin of every row.

    The bin of each row is computed once, when the object is built, from the
    values the frame holds then, and cached as int8 codes (int16 above 127
    bins). Pass one ``BinnedData`` as the ``nbins`` of several ``Hist1D``,
    ``Hist2D`` or ``BetaRPlot`` objects and they share its bins and codes
    instead of each binning, and copying, the same columns. A plot finds its
    columns by the names of its inputs (``x.name``, ``y.name``) and takes the
    rows of ``x.index``, which must be a subset of ``index``. Its ``logx``,
    ``logy`` and ``clip`` default to the settings held here for those
    columns. ``SpiralPlot2D`` refuses a ``BinnedData``: its adaptive mesh is
    built from its own data.

    Only explicit bins are accepted: edges or a ``pd.IntervalIndex`` per
    column. Edges from an integer or string rule (``nbins=101``, ``"auto"``,
    ``"knuth"``) depend on which rows a plot keeps, so they stay per plot:
    pass those to the plot's ``nbins`` instead.

    The object is read-only once built. Its API is ``columns``, ``index``,
    ``log_of(col)``, ``clip_of(col)``, ``edges(col)``, ``intervals(col)``,
    ``codes(col, on=None)`` and ``categorical(col, on=None)``; the arrays it
    returns are read-only.

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
        Columns clipped to their 0.01st and 99.99th percentiles (over the
        finite values of the rows ``mask`` keeps, after ``log``) before
        binning; ``"l"`` or ``"u"`` clips one tail only. Unlisted columns are
        not clipped. Clipping never places +/-inf in a bin.
    mask : pd.Series of bool, optional
        Rows to bin, aligned by label to ``frame.index``. Rows it excludes get
        code -1, and a plot sharing this object does not keep them. A label of
        ``frame.index`` missing from ``mask``, or a NaN in it, raises; neither
        is ever treated as False.
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
        If edges are not strictly increasing, intervals are not contiguous,
        ``mask`` lacks a label or holds NaN, or a ``clip`` string is not one
        ``Base.clip_data`` accepts.

    Notes
    -----
    A value is in a left-closed bin ``[a, b)``; as in :func:`numpy.histogram`,
    the last left-closed bin also holds its right edge. A right-closed bin is
    ``(a, b]``. NaN, +/-inf (also after ``log``, so a logged 0, and also
    where an edge is infinite) and values outside the edges get code -1,
    clipped or not.

    A ``BinnedData`` is a snapshot. It holds a copy-on-write view of the
    binned columns, so a pandas edit to ``frame`` after it is built (for
    example ``frame.loc[i, col] = v``) changes neither its values nor its
    codes; build a new ``BinnedData`` to bin the edited data. One case is not
    guarded: a column that wraps a NumPy array without a copy
    (``pd.Series(arr, copy=False)``, or a frame built from one with
    ``copy=False``) shares that array, and writing into ``arr`` after
    building changes the values held, and the ``data`` of plots built on
    them, though not the codes already assigned.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from solarwindpy.plotting.binned import BinnedData
    >>> from solarwindpy.plotting.hist2d import Hist2D
    >>> rng = np.random.default_rng(0)
    >>> frame = pd.DataFrame(
    ...     {
    ...         "a": rng.normal(size=1000),
    ...         "b": rng.normal(size=1000),
    ...         "c": rng.uniform(size=1000),
    ...     }
    ... )
    >>> edges = {"a": np.linspace(-4, 4, 9), "b": np.linspace(-4, 4, 5)}
    >>> b = BinnedData(frame, edges)
    >>> b.columns, b.codes("a").dtype
    (('a', 'b'), dtype('int8'))
    >>> b.intervals("b")
    IntervalIndex([(-4.0, -2.0], (-2.0, 0.0], (0.0, 2.0], (2.0, 4.0]],
                  dtype='interval[float64, right]')

    Two histograms share its bins and codes; the second keeps only the rows
    its ``mask`` selects.

    >>> h = Hist2D(frame["a"], frame["b"], nbins=b)
    >>> low_c = Hist2D(frame["a"], frame["b"], nbins=b, mask=frame["c"] < 0.5)
    >>> h.agg().shape, low_c.agg().shape  # every (a, b) bin, NaN where empty
    ((32,), (32,))
    >>> int(h.agg().count()), int(low_c.agg().count())
    (24, 22)
    >>> int(h.agg().sum()), int(low_c.agg().sum()), int((frame["c"] < 0.5).sum())
    (1000, 519, 519)

    Editing ``frame`` afterwards changes neither the codes nor the plots.

    >>> before = b.codes("a").copy()
    >>> frame.loc[0, "a"] = 100.0
    >>> bool((b.codes("a") == before).all()), bool(h.data.loc[0, "x"] < 100)
    (True, True)
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
        for k in columns:
            if view[k].dtype == object:
                view[k] = _numeric_if_object(view[k])
        log = {k: bool(v) for k, v in _per_column(log, columns, "log", False).items()}
        clip = _per_column(clip, columns, "clip", False)
        clip = {k: False if v is None else v for k, v in clip.items()}
        for v in clip.values():
            _clip_kind(v)
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
        r"""Bin code of every row of ``values``: -1 off the bins or the mask.

        A linear, unclipped column is binned whole and the mask applied after,
        since a row's bin does not depend on the other rows. Otherwise the
        kept rows are taken first: clip quantiles are computed over them, and
        ``log10`` would warn on a zero in a row that is not kept. A value
        that is +/-inf, given or after ``log10``, is set to NaN before
        clipping, so clipping cannot move it into a bin: its code is -1.
        """
        dtype = _code_dtype(edges.size - 1)
        if not (log or clip):
            out = _cut_codes(values, edges, closed)
            if keep is not None:
                out[~keep] = -1
            return out.astype(dtype)

        out = np.full(values.size, -1, dtype=dtype)
        if keep is not None:
            values = values.iloc[keep]
        if log:
            values = np.log10(np.abs(values))
        if clip:
            values = values.replace([-np.inf, np.inf], np.nan)
            values = _clip_to_quantiles(values, clip)
        placed = _cut_codes(values, edges, closed)
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
        r"""True if ``col`` is binned as ``log10(abs())``.

        Parameters
        ----------
        col : str
            A binned column.

        Returns
        -------
        bool
            Whether ``col`` is binned on its ``log10(abs())`` scale.

        Raises
        ------
        KeyError
            If ``col`` is not binned.
        """
        self._check(col)
        return self._log[col]

    def clip_of(self, col):
        r"""The clip setting of ``col``: False, True, or a tail string.

        Parameters
        ----------
        col : str
            A binned column.

        Returns
        -------
        bool or str
            The clip setting ``col`` was binned with.

        Raises
        ------
        KeyError
            If ``col`` is not binned.
        """
        self._check(col)
        return self._clip[col]

    def edges(self, col):
        r"""Bin edges of ``col``, a read-only ndarray.

        Parameters
        ----------
        col : str
            A binned column.

        Returns
        -------
        np.ndarray
            Read-only edges of the bins of ``col``, on its binned scale.

        Raises
        ------
        KeyError
            If ``col`` is not binned.
        """
        self._check(col)
        return self._edges[col]

    def intervals(self, col):
        r"""Bins of ``col``, a ``pd.IntervalIndex``.

        Parameters
        ----------
        col : str
            A binned column.

        Returns
        -------
        pd.IntervalIndex
            The bins of ``col``, on its binned scale.

        Raises
        ------
        KeyError
            If ``col`` is not binned.
        """
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
