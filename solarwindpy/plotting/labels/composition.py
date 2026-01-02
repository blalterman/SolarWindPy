__all__ = ["Ion", "ChargeStateRatio"]

import pdb  # noqa: F401
from pathlib import Path
from . import base

known_species = ("C", "Fe", "He", "Mg", "Ne", "N", "O", "Si", "S")


class Ion(base.Base):
    """Represent a single ion."""

    def __init__(self, species, charge):
        """Instantiate the ion."""
        super().__init__()
        self.set_species_charge(species, charge)

    @property
    def species(self):
        return self._species

    @property
    def charge(self):
        return self._charge

    @property
    def tex(self):
        return "{%s}^{%s}" % (self.species, self.charge)

    @property
    def units(self):
        return r"\#"  # noqa: W605

    @property
    def path(self):
        return Path(
            f"""{self.species}_{self.charge.replace("+", "p").replace("-", "m")}"""
        )

    def set_species_charge(self, species, charge):
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

    def __init__(self, ionA, ionB):
        """Instantiate the charge-state ratio."""
        super().__init__()
        self.set_ions(ionA, ionB)

    @property
    def ionA(self):
        return self._ionA

    @property
    def ionB(self):
        return self._ionB

    @property
    def path(self):
        return Path(f"{str(self.ionA.path)}-OV-{str(self.ionB.path)}")

    @property
    def tex(self):
        return f"{self.ionA.tex}/{self.ionB.tex}"

    @property
    def units(self):
        uA = self.ionA.units
        uB = self.ionB.units

        units = r"\#"
        if uA != uB:
            units = f"{uA}/{uB}"

        return units

    def set_ions(self, ionA, ionB):
        if not isinstance(ionA, Ion):
            ionA = Ion(*ionA)
        if not isinstance(ionB, Ion):
            ionB = Ion(*ionB)

        self._ionA = ionA
        self._ionB = ionB
