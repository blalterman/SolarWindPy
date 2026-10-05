#!/usr/bin/env python
"""Tensor class for storing quantities like thermal speed, pressure, and temperature."""

__all__ = [
    "Tensor",
]

import pandas as pd

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

    def __call__(self, component: str) -> pd.Series | pd.DataFrame:
        """Access a specific component of the tensor.

        Parameters
        ----------
        component : str
            The name of the component to access.

        Returns
        -------
        pd.Series | pd.DataFrame
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
    def magnitude(self) -> pd.Series:
        r"""Scalar magnitude of a thermal-speed tensor.

        Returns
        -------
        pd.Series
            Scalar thermal speed, in the units of the stored components.

        Notes
        -----
        Thermal speeds combine through the temperatures. With
        :math:`T = (T_\parallel + 2 T_\perp) / 3` and :math:`T \propto w^2`,

        .. math::
           w = \sqrt{\frac{w_\parallel^2 + 2 w_\perp^2}{3}}

        This is the combination ``Plasma`` uses for the stored ``scalar`` thermal
        speed; the ``scalar`` column itself is not read.
        """
        par = self.data.loc[:, "par"]
        per = self.data.loc[:, "per"]
        return par.pow(2).add(per.pow(2).multiply(2.0)).divide(3.0).pow(0.5)
