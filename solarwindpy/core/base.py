#!/usr/bin/env python
"""Contains in situ data Base and Core classes.

This module provides abstract base classes for handling in situ data in solar wind
physics applications.
"""

from __future__ import annotations

__all__ = [
    "Core",
    "Base",
]
import logging
from abc import ABC, abstractmethod
from typing import Any, Tuple

import numpy as np
import pandas as pd

from . import units_constants

# What each column level holds, for messages that name a level.
_LEVEL_WORDS = {"M": "measurement", "C": "component", "S": "species"}


class Core(ABC):
    """Base class for all :mod:`solarwindpy` objects.

    The class sets up logging, unit definitions, and physical constants. It
    provides a common interface that all other core objects inherit from.

    Attributes
    ----------
    logger : :class:`logging.Logger`
        Logger instance associated with the object.
    units : :class:`~solarwindpy.core.units_constants.Units`
        Conversion factors used throughout the package.
    constants : :class:`~solarwindpy.core.units_constants.Constants`
        Collection of physical constants.
    data : :class:`pandas.DataFrame`
        Container for the underlying data.
    """

    def __init__(self) -> None:
        self._init_logger()
        self._init_units()
        self._init_constants()

    def __str__(self) -> str:
        """Return string representation of the object.

        Returns
        -------
        str
            Class name or class name(species) if the class has a species.
        """
        try:
            return f"{self.__class__.__name__}({self.species})"
        except AttributeError:
            return self.__class__.__name__

    def __eq__(self, other: Any) -> bool:
        """Check equality between Base objects.

        Parameters
        ----------
        other : Any
            Object to compare with.

        Returns
        -------
        bool
            True if objects are equal, False otherwise.
        """
        if id(self) == id(other):
            return True
        if not isinstance(other, type(self)):
            return False
        return self.data.equals(other.data)

    @property
    def logger(self) -> logging.Logger:
        """Logger instance for this object.

        Returns
        -------
        logging.Logger
            Logger instance.
        """
        return self._logger

    @property
    def units(self) -> units_constants.Units:
        """Units conversion factors.

        Returns
        -------
        units_constants.Units
            Units conversion instance.
        """
        return self._units

    @property
    def constants(self) -> units_constants.Constants:
        """Physical constants.

        Returns
        -------
        units_constants.Constants
            Physical constants instance.
        """
        return self._constants

    @property
    def data(self) -> pd.DataFrame:
        """Underlying DataFrame containing the data.

        Returns
        -------
        pd.DataFrame
            Data with MultiIndex columns.
        """
        return self._data

    def _init_logger(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _init_units(self) -> None:
        self._units = units_constants.Units()

    def _init_constants(self) -> None:
        self._constants = units_constants.Constants()

    # --- Column access and reduction by level name -------------------------
    #
    # Columns are a MultiIndex with levels "M" (measurement), "C" (component)
    # and "S" (species), or one of those levels alone as a flat Index, as in a
    # Vector's x, y and z. Every component and species selection, and every
    # reduction over columns, in `core` goes through the methods below, which
    # name the level they act on and never assume its position. Changing how
    # columns are stored means rewriting these methods only.

    @staticmethod
    def _level_labels(columns: pd.Index, level: str) -> pd.Index:
        r"""The labels ``columns`` holds on ``level``.

        A flat Index is one level: its name, when set, must be ``level``.

        Raises
        ------
        ValueError
            If ``columns`` has no level ``level``.
        """
        if columns.nlevels == 1:
            if columns.name not in (None, level):
                raise ValueError(
                    f"Expected level {level!r}; these flat columns are level "
                    f"{columns.name!r}"
                )
            return columns
        if level not in columns.names:
            raise ValueError(
                f"Expected level {level!r}; these columns have levels "
                f"{list(columns.names)}"
            )
        return columns.unique(level=level)

    @classmethod
    def _select(cls, frame: pd.DataFrame, key, level: str):
        r"""Columns of ``frame`` labelled ``key`` on the column level named ``level``.

        The one accessor for component (``level="C"``) and species
        (``level="S"``) selection in :mod:`solarwindpy.core`.

        Parameters
        ----------
        frame : pd.DataFrame
            Columns with a level named ``level``, or a flat Index named
            ``level`` or unnamed.
        key : str or list of str
            One label, or a list of labels.
        level : str
            The level's name: ``"M"``, ``"C"`` or ``"S"``.

        Returns
        -------
        pd.Series or pd.DataFrame
            For one label, ``frame.xs(key, level=level)``: the level is
            dropped and the result shares ``frame``'s data rather than
            copying it. For a list, exactly those labels in the order given,
            every other level kept, as ``.loc`` with a list selects them.

        Raises
        ------
        KeyError
            If a label is absent, naming the labels the level holds.
        ValueError
            If ``frame`` has no level ``level``.
        """
        columns = frame.columns
        labels = cls._level_labels(columns, level)
        many = isinstance(key, (list, tuple, pd.Index, np.ndarray))
        keys = list(key) if many else [key]
        absent = [k for k in keys if k not in labels]
        if absent:
            word = _LEVEL_WORDS.get(level, f"level {level!r} label")
            raise KeyError(
                f"Unknown {word} {absent[0]!r}. Available: {labels.tolist()}"
            )
        flat = columns.nlevels == 1
        if many:
            return (
                frame.loc[:, keys] if flat else frame.reindex(columns=keys, level=level)
            )
        return frame.xs(key, axis=1) if flat else frame.xs(key, axis=1, level=level)

    @classmethod
    def _reduce_level(cls, frame: pd.DataFrame, level: str, how: str, **kwargs):
        r"""Reduce ``frame`` over the column level named ``level``.

        Every other level is kept: a flat ``frame`` reduces to a Series, and
        a MultiIndex reduces to one column per combination of the remaining
        levels. Callers use :meth:`_component_reduce` or
        :meth:`_species_total`, which fix the missing-data rule by level.

        Parameters
        ----------
        frame : pd.DataFrame
            Columns with a level named ``level``.
        level : str
            The level reduced over.
        how : str
            The reduction: ``"sum"``, ``"prod"`` or ``"all"``.
        **kwargs
            Passed to the reduction.
        """
        columns = frame.columns
        cls._level_labels(columns, level)
        if columns.nlevels == 1:
            return getattr(frame, how)(axis=1, **kwargs)
        keep = [name for name in columns.names if name != level]
        by = keep[0] if len(keep) == 1 else keep
        return getattr(frame.T.groupby(level=by), how)(**kwargs).T

    @classmethod
    def _component_reduce(cls, frame: pd.DataFrame, how: str = "sum"):
        r"""Reduce over components (level ``"C"``), NaN where any is missing.

        A magnitude, dot product or par-per product needs every component it
        is built from (docs page :doc:`/missing_data`, Within a species).

        Parameters
        ----------
        frame : pd.DataFrame
            Columns with a component level.
        how : str, default "sum"
            ``"sum"``, ``"prod"`` or ``"all"``.
        """
        return cls._reduce_level(frame, "C", how, skipna=False)

    @classmethod
    def _species_total(cls, frame: pd.DataFrame):
        r"""Sum over species (level ``"S"``) present, NaN where none is.

        A total over species uses the species present at each time (docs
        page :doc:`/missing_data`, Across species).

        Parameters
        ----------
        frame : pd.DataFrame
            Columns with a species level.
        """
        return cls._reduce_level(frame, "S", "sum", min_count=1)

    @staticmethod
    def _conform_species(*species: str) -> Tuple[str, ...]:
        """Conform the species inputs to a standard form.

        Parameters
        ----------
        *species : str
            Species to be conformed.

        Returns
        -------
        Tuple[str, ...]
            Conformed species.

        Raises
        ------
        TypeError
            If any species is not a string.
        ValueError
            If species contain invalid characters or combinations.
        """
        if not all(isinstance(s, str) for s in species):
            raise TypeError(f"Invalid species: {species}")
        if any("," in s for s in species):
            raise ValueError(f"Invalid species: {species}")
        if any("+" in s for s in species) and len(species) > 1:
            raise ValueError(
                f"Invalid species: {species}\n\nA multi-species list for which "
                "one species includes '+' may not be uniformly "
                "implementable across methods."
            )

        slist = species[0].split("+") if len(species) == 1 else species
        return tuple(sorted(slist))

    @abstractmethod
    def _clean_species_for_setting(self, *species: str) -> Tuple[str, ...]:
        if not species:
            raise ValueError(
                f"You must specify a species to instantiate a {self.__class__.__name__}."
            )
        return species

    @staticmethod
    def _time_disorder(index: pd.Index, what: str):
        r"""Locate the rows of ``index`` out of time order, refusing missing times.

        The one place that decides whether a time index is complete and in
        order, for :meth:`_time_order` and :meth:`_verify_datetimeindex` alike.

        Parameters
        ----------
        index : pd.Index
            The time index to check.
        what : str
            Names the checked frame in the error message.

        Returns
        -------
        behind : np.ndarray
            Positions of rows earlier than the row before them.

        Raises
        ------
        ValueError
            If ``index`` holds any missing time (``NaT`` or NaN), naming how
            many; a missing time has no place in time order.
        """
        missing = int(index.isna().sum())
        if missing:
            raise ValueError(
                f"{what} time index has {missing} of {len(index)} "
                "timestamps missing (NaT); drop those rows first"
            )
        values = index.to_numpy()
        return np.flatnonzero(values[1:] < values[:-1]) + 1

    @staticmethod
    def _time_order(index: pd.Index, what: str):
        r"""Locate the rows of ``index`` out of time order, refusing ``NaT``.

        Parameters
        ----------
        index : pd.Index
            The time index to check.
        what : str
            Names the checked frame in the error message.

        Returns
        -------
        behind : np.ndarray
            Positions of rows earlier than the row before them.
        order : np.ndarray or None
            The stable sort putting ``index`` in time order, so rows sharing a
            timestamp keep their order; None when ``index`` is in order.

        Raises
        ------
        ValueError
            If ``index`` holds any ``NaT``, naming how many.
        """
        behind = Core._time_disorder(index, what)
        order = np.argsort(index.to_numpy(), kind="stable") if len(behind) else None
        return behind, order

    @staticmethod
    def _require_dataframe(data: Any, what: str) -> None:
        r"""Raise :class:`TypeError` unless ``data`` is a :class:`pandas.DataFrame`.

        Run before anything reads ``data``'s index or columns, so the error
        names the expected type rather than a missing attribute.

        Parameters
        ----------
        data : object
            The data to check.
        what : str
            Names the checked data in the error message.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                f"{what} must be a pandas DataFrame, not {type(data).__name__}"
            )

    def _put_in_time_order(
        self, data: pd.DataFrame, what: str, refusal: str | None = None
    ) -> pd.DataFrame:
        r"""Return ``data`` in time order, warning per call about rows out of order.

        Missing timestamps (``NaT``) raise. Rows earlier than the row before
        them are counted and located in one warning per call, then sorted
        with a stable sort, so rows sharing a timestamp keep their order.

        Parameters
        ----------
        data : pd.DataFrame
            Data indexed by time.
        what : str
            Names the checked frame in messages.
        refusal : str, optional
            When given, out-of-order rows raise :class:`ValueError` ending with
            this reason instead of being sorted.

        Returns
        -------
        pd.DataFrame
            ``data`` in time order; the input itself when already in order.

        Raises
        ------
        ValueError
            If ``data``'s index holds ``NaT``, or is out of order and
            ``refusal`` is given.
        """
        index = data.index
        behind, order = self._time_order(index, what)
        if order is None:
            return data
        if refusal is not None:
            raise ValueError(
                f"{len(behind)} of {len(index)} {what} rows are earlier than "
                f"the row before them; {refusal}"
            )
        self.logger.warning(
            "%d of %d rows are earlier than the row before them, first at "
            "rows %s (times %s); sorting the data by time",
            len(behind),
            len(index),
            behind[:5].tolist(),
            [str(t) for t in index[behind[:5]]],
        )
        return data.iloc[order]

    def _verify_datetimeindex(self, data: pd.DataFrame) -> None:
        r"""Refuse missing times; warn about an index not a DatetimeIndex or not in order.

        Completeness and order are decided by :meth:`_time_disorder`, as for
        :meth:`_put_in_time_order`.
        :class:`~solarwindpy.core.plasma.Plasma` and
        :class:`~solarwindpy.core.spacecraft.Spacecraft` sort their data
        before this runs, so they never reach the order warning. An index whose
        values cannot be compared, such as ``[1, "a", 2.0]``, has no order: it
        gets the order warning, as pandas' ``is_monotonic_increasing`` is False
        for it, and the data are kept.

        Parameters
        ----------
        data : pd.DataFrame
            Data indexed by time.

        Raises
        ------
        ValueError
            If the index holds missing times (``NaT``), naming how many.
        """
        what = f"{self.__class__.__name__} data"
        try:
            in_order = not len(self._time_disorder(data.index, what))
        except TypeError:
            # Values that cannot be compared have no order.
            in_order = False
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning(
                "A non-DatetimeIndex will prevent some DatetimeIndex-dependent functionality from working."
            )

        if not in_order:
            self.logger.warning(
                "An Index that is not monotonically increasing typically indicates the presence of bad data. This will impact performance, especially if it is a DatetimeIndex."
            )


class Base(Core):
    """Base class for objects backed by a :class:`pandas.DataFrame`.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data used to initialise the object.
    _time_checked : :class:`pandas.Index`, optional
        Private, keyword only. Not for users: objects built directly leave it
        unset and run every time check. See Notes.

    Notes
    -----
    Subclasses override :meth:`set_data` to validate the underlying
    :class:`pandas.DataFrame` structure.

    ``_time_checked`` is the switch that skips the missing-time (``NaT``) and
    time-order checks at construction. It exists for children built from data
    their parent already checked, such as the ions a
    :class:`~solarwindpy.core.plasma.Plasma` builds or the unit vector of a
    :class:`~solarwindpy.core.vector.Vector`, so one problem in the parent's
    times is reported once rather than again by every child. The builder
    passes the parent's own time index; the checks are skipped only when
    ``data``'s index equals it, so a child whose times differ from its
    parent's is checked like any other object. A child built from its
    parent's columns shares the parent's index, and the comparison then
    returns without reading a single timestamp. Later calls to
    :meth:`set_data` always check.
    """

    def __init__(
        self, data: pd.DataFrame, *, _time_checked: pd.Index | None = None
    ) -> None:
        super().__init__()
        self._time_checked = _time_checked
        try:
            self.set_data(data)
        finally:
            self._time_checked = None

    @staticmethod
    def mi_tuples(x: Tuple[Tuple[str, ...], ...]) -> pd.MultiIndex:
        """Create a MultiIndex from tuples with appropriate names.

        Parameters
        ----------
        x : Tuple[Tuple[str, ...], ...]
            Tuples to create MultiIndex from.

        Returns
        -------
        pd.MultiIndex
            MultiIndex created from tuples.
        """
        names = ["M", "C", "S"]
        return pd.MultiIndex.from_tuples(x, names=names)

    @abstractmethod
    def set_data(self, new: pd.DataFrame) -> None:
        """Set new data for the class.

        Parameters
        ----------
        new : pd.DataFrame
            New data to set.

        Raises
        ------
        ValueError
            If the new data is empty, or their time index holds ``NaT``.
        """
        if new.empty:
            raise ValueError("You can't set an object with empty data.")

        if not self._times_already_checked(new.index):
            self._verify_datetimeindex(new)

    def _times_already_checked(self, index: pd.Index) -> bool:
        r"""Whether ``index`` is the parent's already-checked time index.

        True only while :meth:`__init__` runs with ``_time_checked`` set and
        ``index`` equals it; see the class Notes.
        """
        checked = self._time_checked
        return checked is not None and index.equals(checked)

    def _put_in_time_order_unless_checked(self, new: pd.DataFrame) -> pd.DataFrame:
        r"""Return ``new`` in time order, warning once, unless already checked.

        For classes that sort their data on setting, as
        :class:`~solarwindpy.core.vector.Vector` and
        :class:`~solarwindpy.core.tensor.Tensor` do. Missing timestamps
        (``NaT``) raise :class:`ValueError`; see :meth:`_put_in_time_order`.
        An index whose values cannot be compared has no order, so ``new`` is
        returned as given and :meth:`_verify_datetimeindex` warns about it.
        """
        if self._times_already_checked(new.index):
            return new
        what = f"{self.__class__.__name__} data"
        try:
            # Only the comparison of index values is guarded: it raises
            # TypeError for values that cannot be compared.
            self._time_disorder(new.index, what)
        except TypeError:
            return new
        return self._put_in_time_order(new, what)

    def _clean_species_for_setting(self, *species):
        species = super(Base, self)._clean_species_for_setting(*species)
        combined = [s for s in species if "+" in s]
        if combined:
            raise ValueError(
                f"{self.__class__.__name__}.species can't contain '+': "
                f"{', '.join(combined)}"
            )
        return tuple(sorted(species))

    def head(self):
        """Return the first few rows of the data.

        Returns
        -------
        pd.DataFrame
            First few rows of the data.
        """
        return self.data.head()

    def tail(self):
        """Return the last few rows of the data.

        Returns
        -------
        pd.DataFrame
            Last few rows of the data.
        """
        return self.data.tail()


class _ComponentFrame(Base):
    r"""One species' components: the common base of Vector and Tensor.

    Holds what :class:`~solarwindpy.core.vector.Vector` and
    :class:`~solarwindpy.core.tensor.Tensor` share, so neither copies it:
    calling the object with a component label.
    """

    def __call__(self, component: str) -> pd.Series:
        r"""Return one component.

        Parameters
        ----------
        component : str
            The component's label, such as ``'x'`` for a Vector or ``'par'``
            for a Tensor.

        Returns
        -------
        pd.Series
            The requested component, which shares data with :attr:`data`.

        Raises
        ------
        KeyError
            If ``component`` is not a component of :attr:`data`; the message
            names the available components.
        """
        return self._select(self.data, component, "C")
