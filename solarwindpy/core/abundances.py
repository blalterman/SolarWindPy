__all__ = ["ReferenceAbundances"]

import numpy as np
import pandas as pd
from collections import namedtuple
from pathlib import Path

Abundance = namedtuple("Abundance", "measurement,uncertainty")


class ReferenceAbundances:
    """Elemental abundances from Asplund et al. (2009).

    Provides both photospheric and meteoritic abundances.

    References
    ----------
    Asplund, M., Grevesse, N., Sauval, A. J., & Scott, P. (2009).
    The Chemical Composition of the Sun.
    Annual Review of Astronomy and Astrophysics, 47(1), 481–522.
    https://doi.org/10.1146/annurev.astro.46.060407.145222
    """

    def __init__(self):
        self.load_data()

    @property
    def data(self):
        r"""Elemental abundances in dex scale:

        log ε_X = log(N_X/N_H) + 12

        where N_X is the number density of species X.
        """
        return self._data

    def load_data(self):
        """Load Asplund 2009 data from package CSV."""
        path = Path(__file__).parent / "data" / "asplund2009.csv"
        data = pd.read_csv(path, skiprows=4, header=[0, 1], index_col=[0, 1]).astype(
            np.float64
        )
        self._data = data

    def get_element(self, key, kind="Photosphere"):
        r"""Get measurements for element stored at `key`.

        Parameters
        ----------
        key : str or int
            Element symbol ('Fe') or atomic number (26).
        kind : str, default "Photosphere"
            Which abundance source: "Photosphere" or "Meteorites".
        """
        if isinstance(key, str):
            level = "Symbol"
        elif isinstance(key, int):
            level = "Z"
        else:
            raise ValueError(f"Unrecognized key type ({type(key)})")

        out = self.data.loc[:, kind].xs(key, axis=0, level=level)
        assert out.shape[0] == 1
        return out.iloc[0]

    @staticmethod
    def _convert_from_dex(case):
        m = case.loc["Ab"]
        u = case.loc["Uncert"]
        mm = 10.0 ** (m - 12.0)
        uu = mm * np.log(10) * u
        return mm, uu

    def abundance_ratio(self, numerator, denominator):
        r"""Calculate abundance ratio N_X/N_Y with uncertainty.

        Parameters
        ----------
        numerator, denominator : str or int
            Element symbols ('Fe', 'O') or atomic numbers.

        Returns
        -------
        Abundance
            namedtuple with (measurement, uncertainty).
        """
        top = self.get_element(numerator)
        tu = top.Uncert
        if np.isnan(tu):
            tu = 0

        if denominator != "H":
            bottom = self.get_element(denominator)
            bu = bottom.Uncert
            if np.isnan(bu):
                bu = 0

            rat = 10.0 ** (top.Ab - bottom.Ab)
            uncert = rat * np.log(10) * np.sqrt((tu**2) + (bu**2))
        else:
            rat, uncert = self._convert_from_dex(top)

        return Abundance(rat, uncert)
