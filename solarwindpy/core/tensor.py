#!/usr/bin/env python
"""Tensor class for storing quantities like thermal speed, pressure, and temperature."""

import pandas as pd
from typing import Union

from . import base


class Tensor(base.Base):
    """Container for tensor-valued quantities.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Tensor data with components ``par``, ``per`` and ``scalar``.
    """

    def __init__(self, data: pd.DataFrame):
        """Initialize the Tensor object.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            Tensor data to be stored.
        """
        super().__init__(data)
        self._validate_data(data)
        self._data = data

    def __getattr__(self, attr: str) -> Union[pd.Series, pd.DataFrame]:
        """Return a component column if present.

        Parameters
        ----------
        attr : str
            Component name to return.

        Returns
        -------
        Union[pd.Series, pandas.DataFrame]
            Column data corresponding to ``attr``.

        Raises
        ------
        AttributeError
            If ``attr`` is not a valid component.
        """
        if attr in self.data.columns:
            return self.data[attr]
        return super().__getattr__(attr)

    def __call__(self, component: str) -> Union[pd.Series, pd.DataFrame]:
        """Access a specific component of the tensor.

        Parameters
        ----------
        component : str
            The name of the component to access.

        Returns
        -------
        Union[pd.Series, pandas.DataFrame]
            The requested component data.

        Raises
        ------
        AttributeError
            If the component does not exist.
        """
        return self.__getattr__(component)

    def set_data(self, new: pd.DataFrame):
        """Set new tensor data.

        Parameters
        ----------
        new : :class:`pandas.DataFrame`
            The new tensor data.

        Raises
        ------
        ValueError
            If ``new`` does not contain the required columns.
        """
        super().set_data(new)
        self._validate_data(new)

    @staticmethod
    def _validate_data(data: pd.DataFrame):
        """Validate the tensor data structure.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            Tensor data to validate.

        Raises
        ------
        ValueError
            If the data does not contain the required columns.
        """
        required_columns = pd.Index(["per", "par", "scalar"])
        if not required_columns.isin(data.columns).all():
            missing_columns = required_columns[~required_columns.isin(data.columns)]
            raise ValueError(f"Missing required columns: {missing_columns.tolist()}")

    @property
    def magnitude(self) -> Union[pd.Series, pd.DataFrame]:
        """Calculate and return the magnitude of the tensor.

        The magnitude is defined as :math:`(p_\\parallel + 2 p_\\perp) / 3`.
        It is computed using only the ``par`` and ``per`` components so that
        it works regardless of the column index name.
        """

        coeff = pd.Series({"par": 1 / 3, "per": 2 / 3})
        cols = coeff.index.intersection(self.data.columns)
        mag = self.data[cols].multiply(coeff[cols], axis=1).sum(axis=1)
        mag.name = "magnitude"
        return mag
