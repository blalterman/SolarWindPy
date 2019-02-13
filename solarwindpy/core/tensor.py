#!/usr/bin/env python
"""
Name   : tensor.py
Author : Benjamin L. Alterman
e-mail : balterma@umich.edu

Description
-----------
-Contains Tensor class and subclasses.


Propodes Updates
----------------
-

Notes
-----
-

"""

import pdb  # noqa: F401

# import logging

# import re as re
# import numpy as np
import pandas as pd

# import warnings
# import itertools

# from numbers import Number
# from pandas import MultiIndex as MI

# from abc import ABC, abstractmethod, abstractproperty

# from scipy import constants


# from scipy.constants
# import physical_constants

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
except ImportError:
    import base


class Tensor(base.Base):
    def __init__(self, data):
        # print(type(self), data, sep="\n")
        super(Tensor, self).__init__(data)

    def __call__(self, component):
        assert isinstance(component, str)
        return self.__getattr__(component)

    def set_data(self, new):
        super(Tensor, self).set_data(new)
        chk = pd.Index(["per", "par", "scalar"])
        if not chk.isin(new.columns).all():
            msg = "\nTarget columns:\n%s\nAttempted:\n%s"
            msg = msg % (chk, new.columns)
            raise ValueError(msg)
        self._data = new
