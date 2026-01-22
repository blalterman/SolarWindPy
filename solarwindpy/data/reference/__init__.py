"""Reference photospheric abundances from Asplund et al. (2009).

Reference:
    Asplund, M., Grevesse, N., Sauval, A. J., & Scott, P. (2009).
    The Chemical Composition of the Sun.
    Annual Review of Astronomy and Astrophysics, 47(1), 481-522.
    https://doi.org/10.1146/annurev.astro.46.060407.145222
"""

__all__ = ["ReferenceAbundances", "Abundance"]

import numpy as np
import pandas as pd
from collections import namedtuple
from importlib import resources

Abundance = namedtuple("Abundance", "measurement,uncertainty")


class ReferenceAbundances:
    """Photospheric elemental abundances from Asplund et al. (2009).

    Abundances are stored in 'dex' units:
        log(epsilon_X) = log(N_X/N_H) + 12

    where N_X is the number density of element X and N_H is hydrogen.

    Example
    -------
    >>> ref = ReferenceAbundances()
    >>> fe_o = ref.photospheric_abundance("Fe", "O")
    >>> print(f"Fe/O = {fe_o.measurement:.4f} +/- {fe_o.uncertainty:.4f}")
    Fe/O = 0.0646 +/- 0.0060
    """

    def __init__(self):
        self._load_data()

    @property
    def data(self):
        """Elemental abundances in dex units."""
        return self._data

    def _load_data(self):
        """Load Asplund 2009 data from package resources."""
        with resources.files(__package__).joinpath("asplund.csv").open() as f:
            data = pd.read_csv(
                f, skiprows=4, header=[0, 1], index_col=[0, 1]
            ).astype(np.float64)
        self._data = data

    def get_element(self, key, kind="Photosphere"):
        """Get abundance measurements for an element.

        Parameters
        ----------
        key : str or int
            Element symbol (e.g., "Fe") or atomic number (e.g., 26)
        kind : str, optional
            "Photosphere" or "Meteorites" (default: "Photosphere")

        Returns
        -------
        pd.Series
            Series with 'Ab' (abundance in dex) and 'Uncert' (uncertainty)
        """
        if isinstance(key, str):
            level = "Symbol"
        elif isinstance(key, int):
            level = "Z"
        else:
            raise ValueError(f"Unrecognized key type ({type(key)})")

        out = self.data.loc[:, kind].xs(key, axis=0, level=level)
        assert out.shape[0] == 1, f"Expected 1 row for {key}, got {out.shape[0]}"

        return out.iloc[0]

    @staticmethod
    def _convert_from_dex(case):
        """Convert from dex to linear abundance ratio."""
        m = case.loc["Ab"]
        u = case.loc["Uncert"]

        mm = 10.0 ** (m - 12.0)
        uu = mm * np.log(10) * u
        return mm, uu

    def photospheric_abundance(self, top, bottom):
        """Compute photospheric abundance ratio of two elements.

        Parameters
        ----------
        top : str or int
            Numerator element (symbol or Z)
        bottom : str or int
            Denominator element (symbol or Z), or "H" for hydrogen

        Returns
        -------
        Abundance
            Named tuple with (measurement, uncertainty) for the ratio N_top/N_bottom

        Example
        -------
        >>> ref = ReferenceAbundances()
        >>> ref.photospheric_abundance("Fe", "O")
        Abundance(measurement=0.0646, uncertainty=0.0060)
        """
        top_data = self.get_element(top)
        tu = top_data.Uncert
        if np.isnan(tu):
            tu = 0

        if bottom != "H":
            bottom_data = self.get_element(bottom)
            bu = bottom_data.Uncert
            if np.isnan(bu):
                bu = 0

            rat = 10.0 ** (top_data.Ab - bottom_data.Ab)
            uncert = rat * np.log(10) * np.sqrt((tu ** 2) + (bu ** 2))
        else:
            rat, uncert = self._convert_from_dex(top_data)

        return Abundance(rat, uncert)
