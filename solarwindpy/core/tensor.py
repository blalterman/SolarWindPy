#!/usr/bin/env python
"""Tensor utilities for thermal speed, pressure, and temperature.

The :class:`Tensor` class provides convenient methods for handling
tensor quantities used throughout the package.
"""

import pandas as pd
from typing import Union

try:
    from . import base
except ImportError:
    import base


class Tensor(base.Base):
    """A class for storing and manipulating tensor data.

    Inherits from solarwindpy.core.Base.

    Attributes:
        _data (pd.DataFrame): The underlying tensor data.
    """

    def __init__(self, data: pd.DataFrame):
        """Initialize the Tensor object.

        Args:
            data (pd.DataFrame): The tensor data to be stored.
        """
        super().__init__(data)
        self._validate_data(data)
        self._data = data

    def __call__(self, component: str) -> Union[pd.Series, pd.DataFrame]:
        """Access a specific component of the tensor.

        Args:
            component (str): The name of the component to access.

        Returns:
            Union[pd.Series, pd.DataFrame]: The requested component data.

        Raises:
            AttributeError: If the component does not exist.
        """
        return self.__getattr__(component)

    def set_data(self, new: pd.DataFrame):
        """Set new data for the tensor.

        Args:
            new (pd.DataFrame): The new tensor data.

        Raises:
            ValueError: If the new data does not contain the required columns.
        """
        super().set_data(new)
        self._validate_data(new)

    @staticmethod
    def _validate_data(data: pd.DataFrame):
        """Validate the tensor data structure.

        Args:
            data (pd.DataFrame): The tensor data to validate.

        Raises:
            ValueError: If the data does not contain the required columns.
        """
        required_columns = pd.Index(["per", "par", "scalar"])
        if not required_columns.isin(data.columns).all():
            missing_columns = required_columns[~required_columns.isin(data.columns)]
            raise ValueError(f"Missing required columns: {missing_columns.tolist()}")

    # @property
    # def per(self) -> Union[pd.Series, pd.DataFrame]:
    #     """Access the 'per' component of the tensor."""
    #     return self.data.loc[:, 'per']

    # @property
    # def par(self) -> Union[pd.Series, pd.DataFrame]:
    #     """Access the 'par' component of the tensor."""
    #     return self.data.loc[:, 'par']

    # @property
    # def scalar(self) -> Union[pd.Series, pd.DataFrame]:
    #     """Access the 'scalar' component of the tensor."""
    #     return self.data.loc[:, 'scalar']

    @property
    def magnitude(self) -> Union[pd.Series, pd.DataFrame]:
        """Calculate and return the magnitude of the tensor."""
        return self.data.multiply({"par": 1 / 3, "per": 2 / 3}, axis=1, level="C").sum(
            axis=1
        )
