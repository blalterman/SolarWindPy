"""Reference elemental abundances from Asplund et al. (2009, 2021).

This module provides access to solar photospheric and CI chondrite
(meteoritic) abundances from the Asplund reference papers.

References
----------
Asplund, M., Amarsi, A. M., & Grevesse, N. (2021).
The chemical make-up of the Sun: A 2020 vision.
A&A, 653, A141. https://doi.org/10.1051/0004-6361/202140445

Asplund, M., Grevesse, N., Sauval, A. J., & Scott, P. (2009).
The Chemical Composition of the Sun.
Annu. Rev. Astron. Astrophys., 47, 481-522.
https://doi.org/10.1146/annurev.astro.46.060407.145222
"""

__all__ = ["ReferenceAbundances", "Abundance"]

import numpy as np
import pandas as pd
from collections import namedtuple
from pathlib import Path

Abundance = namedtuple("Abundance", "measurement,uncertainty")

# Alias mapping for backward compatibility
_KIND_ALIASES = {
    "Meteorites": "CI_chondrites",
}


class ReferenceAbundances:
    """Elemental abundances from Asplund et al. (2009, 2021).

    Provides photospheric and CI chondrite (meteoritic) abundances
    in the standard dex scale: log ε_X = log(N_X/N_H) + 12.

    Parameters
    ----------
    year : int, default 2021
        Reference year: 2009 or 2021. Default uses Asplund 2021.

    Attributes
    ----------
    data : pd.DataFrame
        MultiIndex DataFrame with abundances and uncertainties.
    year : int
        The reference year for the loaded data.

    References
    ----------
    Asplund, M., Amarsi, A. M., & Grevesse, N. (2021).
    The chemical make-up of the Sun: A 2020 vision.
    A&A, 653, A141. https://doi.org/10.1051/0004-6361/202140445

    Asplund, M., Grevesse, N., Sauval, A. J., & Scott, P. (2009).
    The Chemical Composition of the Sun.
    Annu. Rev. Astron. Astrophys., 47, 481-522.
    https://doi.org/10.1146/annurev.astro.46.060407.145222

    Examples
    --------
    >>> ref = ReferenceAbundances()  # Uses 2021 data
    >>> fe = ref.get_element("Fe")
    >>> print(f"Fe = {fe.Ab:.2f} ± {fe.Uncert:.2f}")
    Fe = 7.46 ± 0.04

    >>> ref_2009 = ReferenceAbundances(year=2009)
    >>> fe_2009 = ref_2009.get_element("Fe")
    >>> print(f"Fe (2009) = {fe_2009.Ab:.2f}")
    Fe (2009) = 7.50
    """

    _VALID_YEARS = (2009, 2021)

    def __init__(self, year=2021):
        if not isinstance(year, int):
            raise TypeError(f"year must be an integer, got {type(year).__name__}")
        if year not in self._VALID_YEARS:
            raise ValueError(
                f"year must be 2009 or 2021, got {year}"
            )
        self._year = year
        self._load_data()

    @property
    def year(self):
        """The reference year for the loaded data."""
        return self._year

    @property
    def data(self):
        r"""Elemental abundances in dex scale.

        The dex scale is defined as:
            log ε_X = log(N_X/N_H) + 12

        where N_X is the number density of species X.

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame with index (Z, Symbol) and columns
            (CI_chondrites, Photosphere) × (Ab, Uncert).
        """
        return self._data

    def _load_data(self):
        """Load Asplund data from package CSV based on year."""
        filename = f"asplund{self._year}.csv"
        path = Path(__file__).parent / "data" / filename

        data = pd.read_csv(
            path, skiprows=4, header=[0, 1], index_col=[0, 1]
        )

        # 2021 has Comment column, extract before float conversion
        # Column is ('Comment', 'Unnamed: X_level_1') due to pandas MultiIndex parsing
        comment_cols = [col for col in data.columns if col[0] == "Comment"]
        if comment_cols:
            comment_col = comment_cols[0]
            self._comments = data[comment_col].copy()
            data = data.drop(columns=[comment_col])
        else:
            self._comments = None

        # Convert remaining columns to float64
        self._data = data.astype(np.float64)

    def get_element(self, key, kind="Photosphere"):
        r"""Get measurements for element stored at `key`.

        Parameters
        ----------
        key : str or int
            Element symbol ('Fe') or atomic number (26).
        kind : str, default "Photosphere"
            Which abundance source: "Photosphere", "CI_chondrites",
            or "Meteorites" (alias for CI_chondrites).

        Returns
        -------
        pd.Series
            Series with 'Ab' (abundance in dex) and 'Uncert' (uncertainty).

        Raises
        ------
        ValueError
            If key is not a string or integer.
        KeyError
            If element not found or invalid kind.

        Examples
        --------
        >>> ref = ReferenceAbundances()
        >>> ref.get_element("Fe")
        Ab        7.46
        Uncert    0.04
        Name: (26, Fe), dtype: float64

        >>> ref.get_element(26)  # Same as above, using atomic number
        Ab        7.46
        Uncert    0.04
        Name: (26, Fe), dtype: float64
        """
        # Handle backward compatibility alias
        kind = _KIND_ALIASES.get(kind, kind)

        # Validate kind
        valid_kinds = ["Photosphere", "CI_chondrites"]
        if kind not in valid_kinds:
            raise KeyError(
                f"Invalid kind '{kind}'. Must be one of: {valid_kinds} "
                f"(or 'Meteorites' as alias for 'CI_chondrites')"
            )

        if isinstance(key, str):
            level = "Symbol"
        elif isinstance(key, int):
            level = "Z"
        else:
            raise ValueError(f"Unrecognized key type ({type(key)})")

        out = self.data.loc[:, kind].xs(key, axis=0, level=level)
        assert out.shape[0] == 1
        return out.iloc[0]

    def get_comment(self, key):
        """Get the source comment for an element (2021 data only).

        The comment indicates the source methodology for elements where
        the adopted abundance is not from photospheric spectroscopy:
        - 'definition': H abundance is defined as 12.00
        - 'helioseismology': Derived from helioseismology (He)
        - 'meteorites': Adopted from CI chondrite measurements
        - 'solar wind': Derived from solar wind measurements (Ne, Ar, Kr)
        - 'nuclear physics': Derived from nuclear physics (Xe)

        Parameters
        ----------
        key : str or int
            Element symbol ('Fe') or atomic number (26).

        Returns
        -------
        str or None
            The comment string, or None if no comment (spectroscopic
            measurement) or if using 2009 data.

        Examples
        --------
        >>> ref = ReferenceAbundances()
        >>> ref.get_comment("H")
        'definition'

        >>> ref.get_comment("Fe")  # Spectroscopic, no comment
        None
        """
        if self._comments is None:
            return None

        if isinstance(key, str):
            level = "Symbol"
        elif isinstance(key, int):
            level = "Z"
        else:
            raise ValueError(f"Unrecognized key type ({type(key)})")

        try:
            comment = self._comments.xs(key, axis=0, level=level)
            if len(comment) == 1:
                comment = comment.iloc[0]
            # Handle empty strings and NaN
            if pd.isna(comment) or comment == "":
                return None
            return comment
        except KeyError:
            return None

    @staticmethod
    def _convert_from_dex(case):
        """Convert from dex to linear abundance ratio relative to H.

        Parameters
        ----------
        case : pd.Series
            Series with 'Ab' and 'Uncert' in dex.

        Returns
        -------
        tuple
            (measurement, uncertainty) in linear units.
        """
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

        Notes
        -----
        Uncertainty is propagated assuming independent uncertainties:
            σ_ratio = ratio × ln(10) × √(σ_X² + σ_Y²)

        For denominator='H', uses the special conversion from dex
        since H is the reference element (log ε_H = 12 by definition).

        Examples
        --------
        >>> ref = ReferenceAbundances()
        >>> fe_o = ref.abundance_ratio("Fe", "O")
        >>> print(f"Fe/O = {fe_o.measurement:.4f} ± {fe_o.uncertainty:.4f}")
        Fe/O = 0.0589 ± 0.0038
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
