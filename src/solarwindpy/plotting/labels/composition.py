r"""Labels for heavy ion charge states and charge-state ratios."""

__all__ = ["Ion", "ChargeStateRatio"]

from pathlib import Path
from . import base

known_species = ("C", "Fe", "He", "Mg", "Ne", "N", "O", "Si", "S")


class Ion(base.Base):
    """Represent a single ion."""

    def __init__(self, species, charge, description=None):
        """Instantiate the ion.

        Parameters
        ----------
        species : str
            The element symbol, e.g. ``"He"``, ``"O"``, ``"Fe"``.
        charge : int or str
            The ion charge state, e.g. ``6``, ``"7"``, ``"i"``.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_species_charge(species, charge)
        self.set_description(description)

    @property
    def species(self):
        r"""Element symbol, title-cased."""
        return self._species

    @property
    def charge(self):
        r"""Charge state as passed, e.g. ``6`` or ``"i"``."""
        return self._charge

    @property
    def tex(self):
        r"""TeX of the ion, ``{species}^{charge}``."""
        return "{%s}^{%s}" % (self.species, self.charge)

    @property
    def units(self):
        r"""TeX of the count units."""
        return r"\#"  # noqa: W605

    @property
    def path(self):
        r"""Save path ``<species>_<charge>``, with ``+`` as ``p`` and ``-`` as ``m``."""
        return Path(
            f"""{self.species}_{str(self.charge).replace("+", "p").replace("-", "m")}"""
        )

    def set_species_charge(self, species, charge):
        r"""Store the species and charge.

        An unrecognized species logs a warning.

        Raises
        ------
        ValueError
            If ``charge`` is neither an integer nor ``"i"`` or ``"j"``.
        """
        species = species.title()
        if species not in known_species:
            self.logger.warning(f"Unknown species ({species})")

        invalid_charge = False
        try:
            isinstance(int(charge), int)
        except ValueError:
            invalid_charge = True

        if invalid_charge and charge not in ("i", "j"):
            raise ValueError(f"Invalid charge ({charge})")

        self._species = species
        self._charge = charge


class ChargeStateRatio(base.Base):
    """Ratio of two ion abundances."""

    def __init__(self, ionA, ionB, description=None):
        """Instantiate the charge-state ratio.

        Parameters
        ----------
        ionA : Ion or tuple
            The numerator ion. If tuple, passed to Ion constructor.
        ionB : Ion or tuple
            The denominator ion. If tuple, passed to Ion constructor.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_ions(ionA, ionB)
        self.set_description(description)

    @property
    def ionA(self):
        r"""Numerator ``Ion``."""
        return self._ionA

    @property
    def ionB(self):
        r"""Denominator ``Ion``."""
        return self._ionB

    @property
    def path(self):
        r"""Save path ``<ionA path>-OV-<ionB path>``."""
        return Path(f"{str(self.ionA.path)}-OV-{str(self.ionB.path)}")

    @property
    def tex(self):
        r"""TeX of the ratio."""
        return f"{self.ionA.tex}/{self.ionB.tex}"

    @property
    def units(self):
        r"""Count units when both ions share units, otherwise their ratio."""
        uA = self.ionA.units
        uB = self.ionB.units

        units = r"\#"
        if uA != uB:
            units = f"{uA}/{uB}"

        return units

    def set_ions(self, ionA, ionB):
        r"""Store both ions, building an ``Ion`` from each tuple."""
        if not isinstance(ionA, Ion):
            ionA = Ion(*ionA)
        if not isinstance(ionB, Ion):
            ionB = Ion(*ionB)

        self._ionA = ionA
        self._ionB = ionB
