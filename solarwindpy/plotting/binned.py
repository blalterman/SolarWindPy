# Spent-When: PERMANENT(plot classes stop sourcing data through BinnedData)
# Supersedes: none
r"""The data a plot draws from, and which of its rows the plot keeps.

``_PlotSource`` holds the caller's columns without copying them and records,
once, which rows the plot uses (``rows``). Everything else a plot shows is
derived from those two on demand.

This module imports nothing from :mod:`solarwindpy.plotting`.
"""

# Nothing is public yet: ``_PlotSource`` is private to the plot classes.
__all__ = []

import numpy as np
import pandas as pd


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

    Raises
    ------
    ValueError
        If ``dropna`` is True and no row is kept.

    Attributes
    ----------
    rows : np.ndarray of bool or None
        True for each kept row, in source order; None when every row is kept.
    counts : bool
        True when the value column has exactly one distinct non-NaN value on
        ``rows``: an aggregation without a function then counts, otherwise it
        averages. Decided once, here.
    """

    def __init__(self, coords, value_name, value=None, *, log=None, dropna, owner):
        frame = pd.DataFrame(dict(coords), copy=False)
        index = frame.index
        if value is not None:
            value = _align(value, index, value_name)

        rows = None
        if dropna:
            keep = frame.notna().all(axis=1).to_numpy()
            if value is not None:
                keep = keep & value.notna().to_numpy()
            if not keep.any():
                raise ValueError(
                    "You can't build a %s with data that is exclusively NaNs" % owner
                )
            if not keep.all():
                rows = keep

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
