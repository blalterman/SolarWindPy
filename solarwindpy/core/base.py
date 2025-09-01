#!/usr/bin/env python
"""Contains in situ data Base and Core classes.

This module provides abstract base classes for handling in situ data in solar wind
physics applications.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Any, Tuple

import numpy as np
import pandas as pd
from pandas import MultiIndex as MI

from . import units_constants as uc


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
            Class name.
        """
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
    def units(self) -> uc.Units:
        """Units conversion factors.

        Returns
        -------
        uc.Units
            Units conversion instance.
        """
        return self._units

    @property
    def constants(self) -> uc.Constants:
        """Physical constants.

        Returns
        -------
        uc.Constants
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
        self._units = uc.Units()

    def _init_constants(self) -> None:
        self._constants = uc.Constants()

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

    def _verify_datetimeindex(self, data: pd.DataFrame) -> None:
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning(
                "A non-DatetimeIndex will prevent some DatetimeIndex-dependent functionality from working."
            )

        if not data.index.is_monotonic_increasing:
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
    :class:`DataFrame` structure.
    """

    def __init__(self, data: pd.DataFrame) -> None:
        super().__init__()
        self.set_data(data)

    @staticmethod
    def mi_tuples(x: Tuple[Tuple[str, ...], ...]) -> MI:
        """Create a MultiIndex from tuples with appropriate names.

        Parameters
        ----------
        x : Tuple[Tuple[str, ...], ...]
            Tuples to create MultiIndex from.

        Returns
        -------
        MI
            MultiIndex created from tuples.
        """
        names = ["M", "C", "S"]
        return MI.from_tuples(x, names=names)

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
