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
        try:
            eq_data = self.data.equals(other.data)
            return eq_data

        except ValueError as e:
            if "Can only compare identically-labeled DataFrame objects" in str(e):
                return False
            raise

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
    def _time_disorder(index: pd.Index):
        r"""Count the missing times in ``index`` and locate the rows out of order.

        The one place that decides whether a time index is in order, for
        :meth:`_time_order` and :meth:`_verify_datetimeindex` alike.

        Parameters
        ----------
        index : pd.Index
            The time index to check.

        Returns
        -------
        missing : int
            How many entries of ``index`` are missing (``NaT`` or NaN).
        behind : np.ndarray
            Positions of rows earlier than the row before them; empty when
            ``missing`` is nonzero, since a missing time has no place in order.
        """
        missing = int(index.isna().sum())
        if missing:
            return missing, np.array([], dtype=int)
        values = index.to_numpy()
        return 0, np.flatnonzero(values[1:] < values[:-1]) + 1

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
        missing, behind = Core._time_disorder(index)
        if missing:
            raise ValueError(
                f"{what} time index has {missing} of {len(index)} "
                "timestamps missing (NaT); drop those rows first"
            )
        order = np.argsort(index.to_numpy(), kind="stable") if len(behind) else None
        return behind, order

    def _put_in_time_order(
        self, data: pd.DataFrame, what: str, refusal: str | None = None
    ) -> pd.DataFrame:
        r"""Return ``data`` in time order, warning per call about rows out of order.

        Missing timestamps (``NaT``) raise. Rows earlier than the row before
        them are counted and located in one warning per call, then sorted with a stable
        sort, so rows sharing a timestamp keep their order.

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
        r"""Warn about an index that is not a DatetimeIndex or not in order.

        Order is decided by :meth:`_time_disorder`, as for
        :meth:`_put_in_time_order`. Missing times count as out of order here
        and are not refused: :class:`~solarwindpy.core.plasma.Plasma` and
        :class:`~solarwindpy.core.spacecraft.Spacecraft` refuse them, and sort
        their data, before this runs, so they never reach the order warning.

        Parameters
        ----------
        data : pd.DataFrame
            Data indexed by time.
        """
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning(
                "A non-DatetimeIndex will prevent some DatetimeIndex-dependent functionality from working."
            )

        missing, behind = self._time_disorder(data.index)
        if missing or len(behind):
            self.logger.warning(
                "An Index that is not monotonically increasing typically indicates the presence of bad data. This will impact performance, especially if it is a DatetimeIndex."
            )


class Base(Core):
    """Base class for objects backed by a :class:`pandas.DataFrame`.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data used to initialise the object.

    Notes
    -----
    Subclasses override :meth:`set_data` to validate the underlying
    :class:`pandas.DataFrame` structure.
    """

    def __init__(self, data: pd.DataFrame) -> None:
        super().__init__()
        self.set_data(data)

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
            If the new data is empty.
        """
        if new.empty:
            raise ValueError("You can't set an object with empty data.")

        self._verify_datetimeindex(new)

    def _clean_species_for_setting(self, *species):
        species = super(Base, self)._clean_species_for_setting(*species)
        assert np.all(
            ["+" not in s for s in species]
        ), "%s.species can't contain '+'." % (self.__class__.__name__)
        species = tuple(sorted(species))
        return species

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
