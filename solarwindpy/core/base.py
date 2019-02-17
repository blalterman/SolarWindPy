#!/usr/bin/env python
r"""Contains in situ data :py:class:`Base` and :py:class:`Core` classes.

:py:class:`Base` inherets :py:class:`Core`.
"""

import pdb  # noqa: F401
import logging

# import re as re
import numpy as np
import pandas as pd

# import warnings
# import itertools

# from numbers import Number
from pandas import MultiIndex as MI

from abc import ABC, abstractmethod  # , abstractproperty

# from scipy import constants
# from scipy.constants import physical_constants

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import units_constants as uc
except ImportError:
    import units_constants as uc


class Core(ABC):
    r"""Initializes methods and properties common to inhereting classes.

    1. Initialized properties include logger, units, and constants.
    2. Contains checks for species passed to methods inhereting classes.
    3. Partially implenets total ordering, including disabling some comparisons.
    """

    def __init__(self):
        self._init_logger()
        self._init_units()
        self._init_constants()

    def __str__(self):
        return self.__class__.__name__

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        elif type(self) != type(other):
            return False
        else:
            try:
                eq_data = self.data == other.data
            except ValueError as e:
                # print(dir(e), flush=True)
                msg = "Can only compare identically-labeled DataFrame objects"
                if msg in str(e):
                    return False
                else:
                    raise e

            while isinstance(eq_data, pd.core.generic.NDFrame):
                # TODO: remove while loop
                #       Something like a list comprehension might avoid
                #       run conditions upon inheritence and overriding.
                #       E.g:
                #           eq_data = [v.all() if v.ndim()>= 1 else v for v in a]
                #           np.all(eq_data)
                #       Contact Eshed Magali to figure out the details. (BLA 20180217)
                eq_data = eq_data.all()

            #             if not eq_data:
            #                 # Check if it's a machie precision issue.
            #                 eq_data = (self.data.round(15), other.data.round(15))
            #                 while isinstance(eq_data, pd.core.generic.NDFrame):
            #                     eq_data = eq_data.all()

            if eq_data and (type(self) == type(other)):
                return True

        return False

    # TODO: Write tests for these then ensure they pass.
    def __neq__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        raise NotImplementedError

    def __gt__(self, other):
        raise NotImplementedError

    def __le__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        raise NotImplementedError

    @property
    def logger(self):
        return self._logger

    @property
    def units(self):
        return self._units

    @property
    def constants(self):
        return self._constants

    @property
    def data(self):
        return self._data

    def _init_logger(self):
        r"""
        Init a logger with a StreamHandler at INFO level.
        """
        logger = logging.getLogger(name="analysis.%s" % self.__class__.__name__)
        self._logger = logger

    def _init_units(self):
        self._units = uc.Units()

    def _init_constants(self):
        self._constants = uc.Constants()

    @staticmethod
    def _conform_species(*species):
        r"""
        Conform the species inputs to a standard form.

        Primarily called from within :py:meth:`~solarwindpy.core.plasma.Plasma._chk_species`.
        """
        #        print("",
        #              "<_conform_species>",
        #              "<species>: {}".format(species),
        #              sep="\n",
        #              end="\n\n")
        if not np.all([isinstance(s, str) for s in species]):
            raise TypeError("Invalid species: {}".format(species))
        if not np.all(["," not in s for s in species]):
            raise ValueError("Invalid species: {}".format(species))
        if np.any(["+" in s for s in species]) and len(species) > 1:
            # Either need len(species) == 1 and "+" can be in species[0] or
            # len(species) > 1 and "+" not in species.
            msg = (
                "Invalid species: {}\n\nA multi-species list for which "
                "one species includes '+' may not be uniformly "
                "implementable across methods.".format(species)
            )
            #            print("",
            #                  "<_conform_species>",
            #                  "<species>: {}".format(species),
            #                  sep="\n",
            #                  end="\n\n")
            raise ValueError(msg)
        slist = species
        if len(species) == 1:
            slist = species[0].split("+")
        return tuple(sorted(slist))

    @abstractmethod
    def _clean_species_for_setting(self, *species):
        if not len(species):
            msg = "You must specify a species to instantiate a %s."
            raise ValueError(msg % self.__class__.__name__)
        return species


class Base(Core):
    r"""Inherets Core and adds data property.

    Has methods for validating species when setting data. Data is stored as a pandas DataFrame. Method and properties fall back to this DataFrame when not found.
    """

    def __init__(self, data):
        super(Base, self).__init__()
        self.set_data(data)

    def __getattr__(self, attr):
        r"""
        When __getattr__ access fails, go to the underlying DataFrame.
        This will allow access to the columns via DataFrame.__getattr__.
        """
        # print("Base __getattr__: %s" % attr)
        # if isinstance(self, BField) and attr in ("pb", "pressure"):
        #    pdb.set_trace()

        out = self.data.__getattr__(attr)
        if isinstance(out, pd.core.generic.NDFrame) and not out.size:
            msg = "`%s` attr returns an empty NDFrame" % attr
            raise ValueError(msg)
        # print("attr: %s" % out)
        return out

    #     def __eq__(self, other):
    #         if id(self) == id(other):
    #             return True
    #         elif type(self) != type(other):
    #             return False
    #         else:
    #             try:
    #                 eq_data = (self.data == other.data)
    #             except ValueError as e:
    #                 #print(dir(e), flush=True)
    #                 msg = "Can only compare identically-labeled DataFrame objects"
    #                 if msg in str(e):
    #                     return False
    #                 else:
    #                     raise e
    #
    #             while isinstance(eq_data, pd.core.generic.NDFrame):
    #                 # TODO: remove while loop
    #                 #       Something like a list comprehension might avoid
    #                 #       run conditions upon inheritence and overriding.
    #                 #       E.g:
    #                 #           eq_data = [v.all() if v.ndim()>= 1 else v for v in a]
    #                 #           np.all(eq_data)
    #                 #       Contact Eshed Magali to figure out the details. (BLA 20180217)
    #                 eq_data = eq_data.all()
    #             if eq_data and (type(self) == type(other)):
    #                 return True
    #         return False
    #
    #     # TODO: Write tests for these then ensure they pass.
    #     def __neq__(self, other):
    #         return not self.__eq__(other)
    #     def __lt__(self, other):
    #         raise NotImplementedError
    #     def __gt__(self, other):
    #         raise NotImplementedError
    #     def __le__(self, other):
    #         raise NotImplementedError
    #     def __ge__(self, other):
    #         raise NotImplementedError

    @staticmethod
    def mi_tuples(x):
        names = ["M", "C", "S"]  # , "N"]
        return MI.from_tuples(x, names=names)

    @abstractmethod
    def set_data(self, new):
        data_exists = new.any()
        while isinstance(data_exists, pd.core.generic.NDFrame):
            data_exists = data_exists.any()
        if not data_exists:
            msg = "You can't set an object with empty data."
            raise ValueError(msg)

    def _clean_species_for_setting(self, *species):
        species = super(Base, self)._clean_species_for_setting(*species)
        assert np.all(
            ["+" not in s for s in species]
        ), "%s.species can't contain '+'." % (self.__class__.__name__)
        species = tuple(sorted(species))
        return species
