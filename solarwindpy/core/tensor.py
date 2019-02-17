#!/usr/bin/env python
r"""Tensor class for storing quantities like thermal speed, pressure, and temperature.

:py:class:`Tensor` inherets :py:class:`~solarwindpy.core.Base`.
"""

import pdb  # noqa: F401
import pandas as pd

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
