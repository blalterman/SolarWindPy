#!/usr/bin/env python
"""Contains in situ data Base and Core classes.

This module provides abstract base classes for handling in situ data
in solar wind physics applications.
"""

from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from typing import Any, Tuple, Union

import numpy as np
import pandas as pd
from pandas import MultiIndex as MI
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import units_constants as uc
except ImportError:
    import units_constants as uc


class Core(ABC):
    """
    Abstract base class for initializing common methods and properties.

    Attributes
    ----------
    logger : logging.Logger
        Logger instance for the class.
    units : uc.Units
        Units used in the class.
    constants : uc.Constants
        Physical constants used in the class.
    data : pd.DataFrame
        Data stored in the class.

    Methods
    -------
    __init__()
        Initialize the Core class.
    __str__()
        Return the class name as a string.
    __eq__(other)
        Check equality with another object.
    _init_logger()
        Initialize the logger.
    _init_units()
        Initialize the units.
    _init_constants()
        Initialize the constants.
    _conform_species(*species)
        Conform the species inputs to a standard form.
    _clean_species_for_setting(*species)
        Clean and validate species for setting.
    _verify_datetimeindex(data)
        Verify if the index is a DatetimeIndex and monotonic.
    """

    def __init__(self) -> None:
        self._init_logger()
        self._init_units()
        self._init_constants()

    def __str__(self) -> str:
        return self.__class__.__name__

    def __eq__(self, other: Any) -> bool:
        if id(self) == id(other):
            return True
        if not isinstance(other, type(self)):
            return False
        try:
            # eq_data = self.data.equals() == other.data
            # return eq_data.all().all()
            eq_data = self.data.equals(other.data)
            return eq_data
        
        except ValueError as e:
            if "Can only compare identically-labeled DataFrame objects" in str(e):
                return False
            raise

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def units(self) -> uc.Units:
        return self._units

    @property
    def constants(self) -> uc.Constants:
        return self._constants

    @property
    def data(self) -> pd.DataFrame:
        return self._data

    def _init_logger(self) -> None:
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _init_units(self) -> None:
        self._units = uc.Units()

    def _init_constants(self) -> None:
        self._constants = uc.Constants()

    @staticmethod
    def _conform_species(*species: str) -> Tuple[str, ...]:
        """
        Conform the species inputs to a standard form.

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
            raise ValueError(f"You must specify a species to instantiate a {self.__class__.__name__}.")
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
    """
    Base class for handling in situ data.

    This class inherits from Core and adds data handling capabilities.

    Attributes
    ----------
    data : pd.DataFrame
        Data stored in the class.

    Methods
    -------
    __init__(data)
        Initialize the Base class with data.
    __getattr__(attr)
        Get attribute from the underlying DataFrame if not found in the class.
    set_data(new)
        Set new data for the class.
    mi_tuples(x)
        Create a MultiIndex from tuples.
    """

    def __init__(self, data: pd.DataFrame) -> None:
        super().__init__()
        # self._cache = {}
        self.set_data(data)

    # def __getattr__(self, attr: str) -> Any:
    #     if attr in self._cache:
    #         return self._cache[attr]       

    #     if hasattr(self._data, attr):
    #         value = getattr(self._data, attr)
    #         if callable(value):
    #             def wrapped_method(*args, **kwargs):
    #                 return value(*args, **kwargs)
    #             self._cache[attr] = wrapped_method
    #         else:
    #             self._cache[attr] = value
    #         return self._cache[attr]

    #     raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")
     
        # try:
        #     out = getattr(self.data, attr)
        #     if isinstance(out, pd.core.generic.NDFrame) and out.empty:
        #         raise ValueError(f"`{attr}` attr returns an empty NDFrame")
        #     return out
        # except AttributeError:
        #     raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    # # Implement common DataFrame properties
    # @property
    # def index(self):
    #     return self._data.index
    
    # # Implement common DataFrame methods
    # def loc(self, *args, **kwargs):
    #     return self._data.loc(*args, **kwargs)

    # def iloc(self, *args, **kwargs):
    #     return self._data.iloc(*args, **kwargs)

    # def xs(self, *args, **kwargs):
    #     return self._data.xs(*args, **kwargs)

    @staticmethod
    def mi_tuples(x: Tuple[Tuple[str, ...], ...]) -> MI:
        """
        Create a MultiIndex from tuples with appropriate names.

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
        """
        Set new data for the class.

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
