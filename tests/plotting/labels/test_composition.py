import logging
import pytest

from solarwindpy.plotting.labels import composition


class IonWithUnits(composition.Ion):
    """Ion subclass that allows overriding units."""

    def __init__(self, species, charge, units):
        super().__init__(species, charge)
        self._units_override = units

    @property
    def units(self):
        return self._units_override


def test_set_species_charge_known_species(caplog):
    """Check that a known species does not trigger a warning.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Logging capture fixture.
    """
    with caplog.at_level(logging.WARNING):
        ion = composition.Ion("Fe", "2")
    assert ion.species == "Fe"
    assert ion.charge == "2"
    assert "Unknown species" not in caplog.text


def test_set_species_charge_unknown_species(caplog):
    """Check that an unknown species logs a warning.

    Parameters
    ----------
    caplog : pytest.LogCaptureFixture
        Logging capture fixture.
    """
    with caplog.at_level(logging.WARNING):
        composition.Ion("Xe", "2")
    assert "Unknown species (Xe)" in caplog.text


def test_set_species_charge_invalid_charge():
    """Ensure invalid charge raises ``ValueError``."""
    with pytest.raises(ValueError):
        composition.Ion("Fe", "a")


def test_charge_state_units_equal():
    """``ChargeState`` has ``#`` units when ion units match."""
    cs = composition.ChargeState(("O", "2"), ("Fe", "3"))
    assert cs.units == r"\#"


def test_charge_state_units_different():
    """``ChargeState`` units combine when ion units differ."""
    ion_a = IonWithUnits("O", "2", "cm-3")
    ion_b = IonWithUnits("Fe", "3", "km/s")
    cs = composition.ChargeState(ion_a, ion_b)
    assert cs.units == "cm-3/km/s"
