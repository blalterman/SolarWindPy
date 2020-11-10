__all__ = ["ElementalAbundance"]

import pdb  # noqa: F401
import logging
from pathlib import Path
from . import base

known_species = ("C", "Fe", "He", "H", "Mg", "Ne", "N", "O", "Si", "S")


class ElementalAbundance(base.Base):
    def __init__(self, species, reference_species, pct_unit=False):
        self.set_species(species, reference_species)
        self._pct_unit = bool(pct_unit)

    @property
    def species(self):
        return self._species

    @property
    def reference_species(self):
        return self._reference_species

    @property
    def units(self):
        if self.pct_unit:
            return r"\%"
        else:
            return r"\#"  # noqa: W605

    @property
    def tex(self):
        ratio = r"\mathrm{%s}/\mathrm{%s}" % (self.species, self.reference_species)
        tex = f"{ratio}:{ratio}_" r"\mathrm{photo}"  # noqa: W605
        return tex

    @property
    def path(self):
        return Path(f"{self.species}-OV-{self.reference_species}_photospheric-ratio")

    @property
    def pct_unit(self):
        return self._pct_unit

    def set_species(self, species, reference_species):
        species = species.title()
        reference_species = reference_species.title()

        if species not in known_species:
            logging.getLogger().warning(f"Species ({species}) is not recognized")
        if reference_species not in known_species:
            logging.getLogger().warning(
                f"Reference species ({reference_species}) is not recognized"
            )

        self._species = species
        self._reference_species = reference_species
