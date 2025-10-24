import logging
import pytest
from pathlib import Path

from solarwindpy.plotting.labels import composition
from solarwindpy.plotting.labels.base import Base


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
    """``ChargeStateRatio`` has ``#`` units when ion units match."""
    cs = composition.ChargeStateRatio(("O", "2"), ("Fe", "3"))
    assert cs.units == r"\#"


def test_charge_state_units_different():
    """``ChargeStateRatio`` units combine when ion units differ."""
    ion_a = IonWithUnits("O", "2", "cm-3")
    ion_b = IonWithUnits("Fe", "3", "km/s")
    cs = composition.ChargeStateRatio(ion_a, ion_b)
    assert cs.units == "cm-3/km/s"


class TestIon:
    """Test Ion class functionality."""

    def test_ion_initialization(self):
        """Test basic Ion initialization."""
        ion = composition.Ion("Fe", "2")
        assert ion.species == "Fe"
        assert ion.charge == "2"

    def test_ion_inheritance(self):
        """Test that Ion inherits from Base."""
        ion = composition.Ion("O", "6")
        assert isinstance(ion, Base)
        assert hasattr(ion, "logger")

    def test_species_title_case(self):
        """Test that species is converted to title case."""
        ion = composition.Ion("fe", "2")
        assert ion.species == "Fe"

        ion2 = composition.Ion("FE", "3")
        assert ion2.species == "Fe"

    def test_tex_property(self):
        """Test TeX representation of ion."""
        ion = composition.Ion("Fe", "2")
        assert ion.tex == "{Fe}^{2}"

        # Test with different charge formats
        ion_plus = composition.Ion("O", "6")
        assert ion_plus.tex == "{O}^{6}"

    def test_units_property(self):
        """Test ion units property."""
        ion = composition.Ion("Ne", "8")
        assert ion.units == "\\#"

    def test_path_property(self):
        """Test path generation for ions."""
        ion = composition.Ion("Si", "4")
        assert isinstance(ion.path, Path)
        assert str(ion.path) == "Si_4"

    def test_path_with_valid_charges(self):
        """Test path generation with various valid charges."""
        # Test basic numeric charges
        ion1 = composition.Ion("Fe", "2")
        assert str(ion1.path) == "Fe_2"

        # Test special charges
        ion_i = composition.Ion("Fe", "i")
        expected_path = "Fe_i"
        assert str(ion_i.path) == expected_path

        ion_j = composition.Ion("O", "j")
        expected_path = "O_j"
        assert str(ion_j.path) == expected_path

    def test_known_species_list(self):
        """Test the known species list."""
        expected_species = ("C", "Fe", "He", "Mg", "Ne", "N", "O", "Si", "S")
        assert composition.known_species == expected_species

    def test_all_known_species_no_warning(self, caplog):
        """Test that all known species don't trigger warnings."""
        with caplog.at_level(logging.WARNING):
            for species in composition.known_species:
                composition.Ion(species, "2")
        assert "Unknown species" not in caplog.text

    def test_valid_charges(self):
        """Test various valid charge formats."""
        valid_charges = ["1", "2", "3", "10", "i", "j"]

        for charge in valid_charges:
            ion = composition.Ion("O", charge)
            assert ion.charge == charge

    def test_invalid_charges(self):
        """Test invalid charge formats raise ValueError."""
        invalid_charges = ["a", "x", "1.5", "+", "-", ""]

        for charge in invalid_charges:
            with pytest.raises(ValueError, match="Invalid charge"):
                composition.Ion("O", charge)

    def test_string_representation(self):
        """Test string representations through base class."""
        ion = composition.Ion("Fe", "2")
        # Ion inherits from Base, so it should have with_units property
        str_repr = str(ion)
        assert isinstance(str_repr, str)

    def test_ion_comparison(self):
        """Test ion comparison functionality."""
        ion1 = composition.Ion("Fe", "2")
        ion2 = composition.Ion("Fe", "2")
        ion3 = composition.Ion("O", "6")

        # Same ions should be equal
        assert ion1 == ion2

        # Different ions should not be equal
        assert ion1 != ion3

    def test_ion_hashing(self):
        """Test that ions can be hashed."""
        ion1 = composition.Ion("Fe", "2")
        ion2 = composition.Ion("O", "6")

        # Should be able to create a set
        ion_set = {ion1, ion2}
        assert len(ion_set) == 2

        # Should be able to use as dictionary keys
        ion_dict = {ion1: "iron", ion2: "oxygen"}
        assert len(ion_dict) == 2


class TestChargeState:
    """Test ChargeStateRatio class functionality."""

    def test_charge_state_initialization_with_tuples(self):
        """Test ChargeStateRatio initialization with tuples."""
        cs = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        assert cs.ionA.species == "O"
        assert cs.ionA.charge == "6"
        assert cs.ionB.species == "O"
        assert cs.ionB.charge == "7"

    def test_charge_state_initialization_with_ions(self):
        """Test ChargeState initialization with Ion objects."""
        ion_a = composition.Ion("Fe", "10")
        ion_b = composition.Ion("Fe", "11")
        cs = composition.ChargeStateRatio(ion_a, ion_b)
        assert cs.ionA == ion_a
        assert cs.ionB == ion_b

    def test_charge_state_inheritance(self):
        """Test that ChargeState inherits from Base."""
        cs = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        assert isinstance(cs, Base)
        assert hasattr(cs, "logger")

    def test_charge_state_tex(self):
        """Test TeX representation of charge state."""
        cs = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        assert cs.tex == "{O}^{6}/{O}^{7}"

    def test_charge_state_path(self):
        """Test path generation for charge state."""
        cs = composition.ChargeStateRatio(("Fe", "10"), ("Fe", "11"))
        assert isinstance(cs.path, Path)
        expected_path = "Fe_10-OV-Fe_11"
        assert str(cs.path) == expected_path

    def test_charge_state_same_units(self):
        """Test charge state units when both ions have same units."""
        # Default Ion units are "\#"
        cs = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        assert cs.units == r"\#"

    def test_charge_state_different_units(self):
        """Test charge state units when ions have different units."""
        ion_a = IonWithUnits("O", "6", "cm^-3")
        ion_b = IonWithUnits("O", "7", "km/s")
        cs = composition.ChargeStateRatio(ion_a, ion_b)
        assert cs.units == "cm^-3/km/s"

    def test_charge_state_mixed_initialization(self):
        """Test ChargeState with mix of Ion and tuple."""
        ion_a = composition.Ion("Fe", "2")
        cs = composition.ChargeStateRatio(ion_a, ("O", "6"))
        assert cs.ionA == ion_a
        assert cs.ionB.species == "O"
        assert cs.ionB.charge == "6"

    def test_charge_state_comparison(self):
        """Test charge state comparison functionality."""
        cs1 = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        cs2 = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        cs3 = composition.ChargeStateRatio(("Fe", "10"), ("Fe", "11"))

        # Same charge states should be equal
        assert cs1 == cs2

        # Different charge states should not be equal
        assert cs1 != cs3

    def test_charge_state_hashing(self):
        """Test that charge states can be hashed."""
        cs1 = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        cs2 = composition.ChargeStateRatio(("Fe", "10"), ("Fe", "11"))

        # Should be able to create a set
        cs_set = {cs1, cs2}
        assert len(cs_set) == 2

        # Should be able to use as dictionary keys
        cs_dict = {cs1: "oxygen", cs2: "iron"}
        assert len(cs_dict) == 2

    def test_charge_state_string_representation(self):
        """Test string representation of charge state."""
        cs = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        str_repr = str(cs)
        assert isinstance(str_repr, str)


class TestCompositionModule:
    """Test module-level functionality."""

    def test_module_all(self):
        """Test module __all__ exports."""
        assert composition.__all__ == ["Ion", "ChargeStateRatio"]

    def test_module_attributes(self):
        """Test module has expected attributes."""
        assert hasattr(composition, "Ion")
        assert hasattr(composition, "ChargeStateRatio")
        assert hasattr(composition, "known_species")

    def test_known_species_completeness(self):
        """Test that known_species covers common solar wind ions."""
        expected_common_ions = ["C", "Fe", "He", "Mg", "Ne", "N", "O", "Si", "S"]
        for ion in expected_common_ions:
            assert ion in composition.known_species

    def test_scientific_accuracy(self):
        """Test that composition labels represent scientifically accurate concepts."""
        # Test common solar wind charge states
        o6_o7 = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        assert "O" in o6_o7.tex
        assert "6" in o6_o7.tex
        assert "7" in o6_o7.tex

        # Test iron charge states
        fe10_fe11 = composition.ChargeStateRatio(("Fe", "10"), ("Fe", "11"))
        assert "Fe" in fe10_fe11.tex
        assert "10" in fe10_fe11.tex
        assert "11" in fe10_fe11.tex


class TestCompositionIntegration:
    """Test integration between Ion and ChargeState classes."""

    def test_ion_in_charge_state_roundtrip(self):
        """Test creating ions and using them in charge states."""
        # Create ions
        o6 = composition.Ion("O", "6")
        o7 = composition.Ion("O", "7")

        # Use in charge state
        cs = composition.ChargeStateRatio(o6, o7)

        # Verify roundtrip
        assert cs.ionA.species == "O"
        assert cs.ionA.charge == "6"
        assert cs.ionB.species == "O"
        assert cs.ionB.charge == "7"

    def test_complex_charge_state_ratios(self):
        """Test complex charge state ratios with different species."""
        # O6+ / Fe10+ ratio
        cs = composition.ChargeStateRatio(("O", "6"), ("Fe", "10"))
        assert "O" in cs.tex
        assert "Fe" in cs.tex
        assert "{O}^{6}/{Fe}^{10}" == cs.tex

    def test_charge_state_path_uniqueness(self):
        """Test that different charge states have unique paths."""
        cs1 = composition.ChargeStateRatio(("O", "6"), ("O", "7"))
        cs2 = composition.ChargeStateRatio(("Fe", "10"), ("Fe", "11"))
        cs3 = composition.ChargeStateRatio(("O", "7"), ("O", "6"))  # Reversed

        paths = [str(cs1.path), str(cs2.path), str(cs3.path)]
        assert len(paths) == len(set(paths))  # All unique
