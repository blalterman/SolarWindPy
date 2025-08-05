__all__ = ["ElementalAbundance"]

import pdb  # noqa: F401
import logging
from pathlib import Path
from . import base

known_species = tuple(base._trans_species.keys()) + ("X",)


class ElementalAbundance(base.Base):
    """Ratio of elemental abundances."""

    def __init__(self, species, reference_species, pct_unit=False, photospheric=True):
        """Instantiate the abundance label."""
        self.set_species(species, reference_species)
        self._pct_unit = bool(pct_unit)
        self._photospheric = bool(photospheric)

    @property
    def species(self):
        return self._species

    @property
    def photospheric(self):
        return self._photospheric

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
        num = base._trans_species.get(self.species, self.species)
        den = base._trans_species.get(self.reference_species, self.reference_species)
        ratio = r"\mathrm{%s}/\mathrm{%s}" % (num, den)
        if self.photospheric:
            tex = f"{ratio}:{ratio}_" r"\mathrm{photo}"  # noqa: W605
        else:
            tex = ratio
        return tex

    @property
    def path(self):
        path = f"{self.species}-OV-{self.reference_species}"
        if self.photospheric:
            path += "_photospheric-ratio"
        return Path(path)

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
