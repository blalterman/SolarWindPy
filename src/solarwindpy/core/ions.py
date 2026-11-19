#!/usr/bin/env python
"""Contains Ion class.

This module defines the Ion class, which inherits from the Base class and contains
Vector and Tensor objects.
"""

from __future__ import annotations

__all__ = [
    "Ion",
]
import pandas as pd

from . import base
from . import vector
from . import tensor


class Ion(base.Base):
    """Container for a single ion species.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Data for the ion in the form ``("M", "C")`` where ``M`` is the
        measurement type (``n``, ``v``, ``w``) and ``C`` is the component.
    species : str
        Species identifier, e.g. ``"p"`` for protons or ``"a"`` for alpha
        particles.

    Attributes
    ----------
    species : str
        The ion's species name.

    Examples
    --------
    Create a proton ion from the example plasma's measurement data:

    >>> import solarwindpy as swp
    >>> from solarwindpy.core.ions import Ion
    >>> plasma = swp.examples.load_plasma()
    >>> proton_data = plasma.data.xs('p1', level='S', axis=1)
    >>> proton = Ion(proton_data, 'p1')
    >>> proton.species
    'p1'
    >>> proton.n.tolist()
    [1.0, 2.0, 3.0]
    >>> proton.v.mag.round(2).tolist()
    [458.26, 700.0, 1044.03]

    It matches the proton ion the plasma builds itself:

    >>> proton == plasma.p1
    True
    """

    def __init__(
        self, data: pd.DataFrame, species: str, *, _time_checked: pd.Index | None = None
    ):
        """Initialize an Ion instance with plasma measurement data.

        Parameters
        ----------
        data : pandas.DataFrame
            Ion measurement data with MultiIndex columns formatted as
            ("M", "C") where M is measurement type (n, v, w, T) and
            C is component (x, y, z, par, per, etc.).
        species : str
            Ion species identifier following standard conventions:
            - 'p1' or 'p' for protons
            - 'a' for alpha particles (He2+)
            - 'o6' for O6+ ions
            - Other species as needed
        _time_checked : pandas.Index, optional
            Private; see :class:`~solarwindpy.core.base.Base`.

        Notes
        -----
        The Ion class provides access to fundamental plasma measurements:

        - n: Number density [cm^-3]
        - v: Velocity vector [km/s]
        - w: Thermal speed [km/s] (assumes mw² = 2kT)
        - T: Temperature [K] (derived from thermal speed)

        Physical constants and mass values are automatically assigned
        based on the species identifier using standard atomic masses.
        """
        self._set_species(species)
        super().__init__(data, _time_checked=_time_checked)

    def __eq__(self, other: object) -> bool:
        """Check equality between Ion objects.

        Parameters
        ----------
        other : object
            Object to compare with.

        Returns
        -------
        bool
            True if species and data are equal, False otherwise.
        """
        if not isinstance(other, Ion):
            return NotImplemented
        return self.species == other.species and self.data.equals(other.data)

    def _set_species(self, species: str) -> None:
        """Set the species of the ion.

        Parameters
        ----------
        species : str
            The species of the ion.

        Raises
        ------
        ValueError
            If the species contains a '+' character; a combined species is
            formed in method calls, never stored.
        """
        (self._species,) = self._clean_species_for_setting(species)

    def set_data(self, data: pd.DataFrame) -> None:
        """Set the data for the ion.

        Parameters
        ----------
        data : pd.DataFrame
            The data to set for the ion. Rows out of time order are sorted
            with one warning, as :class:`~solarwindpy.core.plasma.Plasma`
            sorts its data.

        Raises
        ------
        KeyError
            If the data hold no species :attr:`species`; the message names
            the species they hold.
        ValueError
            If the column levels are not named ``("M", "C", "S")``, or
            ``("M", "C")`` for data of one species, in that order; or the time
            index holds missing timestamps (``NaT``).
        """
        data = self._put_in_time_order_unless_checked(data)
        super().set_data(data)

        three = data.columns.nlevels == 3
        names = base._LEVEL_NAMES if three else base._LEVEL_NAMES[:2]
        self._require_level_names(data.columns, names, "Ion data")
        if three:
            data = data.sort_index(axis=1)
            try:
                data = data.xs(self.species, axis=1, level="S")
            except KeyError:
                available = self._level_labels(data.columns, "S").tolist()
                raise KeyError(
                    f"Unknown species {self.species!r}. Available: {available}"
                ) from None

        required_columns = [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
        ]
        if not pd.Index(required_columns).isin(data.columns).all():
            raise ValueError("Missing required columns in data")

        self._data = data

    @property
    def species(self) -> str:
        """Get the ion species."""
        return self._species

    @property
    def v(self) -> vector.Vector:
        """Get the ion's velocity as a Vector.

        Built from the ion's already-checked columns, so it skips the time
        checks.
        """
        return vector.Vector(self.data.loc[:, "v"], _time_checked=self.data.index)

    @property
    def w(self) -> tensor.Tensor:
        """Get the ion's thermal speed as a Tensor.

        Built from the ion's already-checked columns, so it skips the time
        checks.
        """
        return tensor.Tensor(self.data.loc[:, "w"], _time_checked=self.data.index)

    @property
    def n(self) -> pd.Series:
        """Get the number density of the ion."""
        return self.data.loc[:, "n"]

    @property
    def rho(self) -> pd.Series:
        """Calculate the ion's mass density."""
        out = self.n * self.constants.m_in_mp.loc[self.species]
        out.name = "rho"
        return out

    @property
    def R(self) -> pd.Series:
        """Calculate temperature anisotropy R_T = p_⟂/p_∥."""
        exp = pd.Series({"par": -1, "per": 1})
        pth = self.pth.loc[:, ["par", "per"]]
        ani = self._component_reduce(pth.pow(exp, axis=1, level="C"), "prod")
        ani.name = "R"
        return ani

    @property
    def T(self) -> pd.DataFrame:
        """Calculate temperature T = (m / (2 * k_B)) * w^2."""
        m = self.constants.m.loc[self.species]
        w = self.w.data * self.units.w
        coeff = 0.5 * m / (self.constants.kb.J * self.units.T)
        temp = coeff * w.pow(2)
        temp.name = "T"
        return temp

    @property
    def pth(self) -> pd.DataFrame:
        """Calculate thermal pressure p_th = 0.5 * ρ * w^2."""
        rho = self.rho * self.units.rho
        w = self.w.data.multiply(self.units.w)
        pth = (0.5 / self.units.pth) * w.pow(2).multiply(rho, axis=0)
        pth.name = "pth"
        return pth

    @property
    def cs(self) -> pd.DataFrame:
        r"""Calculate the species' sound speed per pressure component.

        :math:`c_{s,j} = \sqrt{\gamma_j p_j / \rho}` for each column ``j`` of
        :attr:`pth`, with the polytropic index of that column from
        :attr:`~solarwindpy.core.units_constants.Constants.polytropic_index`:
        the double-adiabatic (CGL) indices :math:`\gamma_\parallel = 3` and
        :math:`\gamma_\perp = 2` for ``par`` and ``per`` (Chew, Goldberger &
        Low 1956, Proc. R. Soc. Lond. A 236, 112, doi:10.1098/rspa.1956.0116),
        and :math:`\gamma = 5/3` for ``scalar``.
        """
        pth = self.pth * self.units.pth
        rho = self.rho * self.units.rho
        gamma = self.constants.polytropic_index.loc[pth.columns]
        return self._sound_speed(pth, rho, gamma)

    @property
    def Wk(self):
        r"""Calculate the kinetic energy flux, a pd.Series.

        The kinetic energy flux is calculated as:

        .. math::
            W_k = \frac{1}{2} \rho v^3
        """
        rho = self.rho * self.units.rho
        v = self.v.mag * self.units.v
        w = rho.multiply(v.pow(3)).multiply(0.5)
        w /= self.units.Wk

        w.name = "Wk"
        return w
