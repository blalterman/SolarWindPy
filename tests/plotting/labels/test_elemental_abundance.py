"""Test suite for elemental abundance label functionality."""

import pytest
import warnings
from pathlib import Path
from unittest.mock import patch

from solarwindpy.plotting.labels.elemental_abundance import ElementalAbundance


class TestElementalAbundanceInitialization:
    """Test ElementalAbundance class initialization."""

    def test_basic_initialization(self):
        """Test basic ElementalAbundance initialization."""
        abundance = ElementalAbundance("He", "H")
        assert abundance.species == "He"
        assert abundance.reference_species == "H"
        assert not abundance.pct_unit
        assert abundance.photospheric

    def test_initialization_with_options(self):
        """Test initialization with all options."""
        abundance = ElementalAbundance("Fe", "H", pct_unit=True, photospheric=False)
        assert abundance.species == "Fe"
        assert abundance.reference_species == "H"
        assert abundance.pct_unit
        assert not abundance.photospheric

    def test_species_case_conversion(self):
        """Test species names are converted to title case."""
        abundance = ElementalAbundance("he", "h")
        assert abundance.species == "He"
        assert abundance.reference_species == "H"

    def test_initialization_boolean_conversion(self):
        """Test boolean parameters are properly converted."""
        abundance = ElementalAbundance("C", "H", pct_unit="true", photospheric=0)
        assert abundance.pct_unit is True
        assert abundance.photospheric is False


class TestElementalAbundanceProperties:
    """Test ElementalAbundance property access."""

    def test_species_property(self):
        """Test species property returns correct value."""
        abundance = ElementalAbundance("Fe", "O")
        assert abundance.species == "Fe"

    def test_reference_species_property(self):
        """Test reference_species property returns correct value."""
        abundance = ElementalAbundance("Fe", "O")
        assert abundance.reference_species == "O"

    def test_photospheric_property(self):
        """Test photospheric property returns correct value."""
        abundance1 = ElementalAbundance("C", "H", photospheric=True)
        abundance2 = ElementalAbundance("C", "H", photospheric=False)
        assert abundance1.photospheric is True
        assert abundance2.photospheric is False

    def test_pct_unit_property(self):
        """Test pct_unit property returns correct value."""
        abundance1 = ElementalAbundance("C", "H", pct_unit=True)
        abundance2 = ElementalAbundance("C", "H", pct_unit=False)
        assert abundance1.pct_unit is True
        assert abundance2.pct_unit is False


class TestElementalAbundanceUnits:
    """Test ElementalAbundance units property."""

    def test_units_dimensionless(self):
        """Test units property with dimensionless numbers."""
        abundance = ElementalAbundance("He", "H", pct_unit=False)
        assert abundance.units == r"\#"

    def test_units_percentage(self):
        """Test units property with percentage."""
        abundance = ElementalAbundance("He", "H", pct_unit=True)
        assert abundance.units == r"\%"


class TestElementalAbundanceTeX:
    """Test ElementalAbundance TeX formatting."""

    def test_tex_basic_ratio(self):
        """Test basic ratio TeX formatting."""
        abundance = ElementalAbundance("He", "H", photospheric=False)
        tex = abundance.tex
        assert r"\mathrm{He}" in tex
        assert r"\mathrm{H}" in tex
        assert "/" in tex

    def test_tex_photospheric_ratio(self):
        """Test photospheric ratio TeX formatting."""
        abundance = ElementalAbundance("He", "H", photospheric=True)
        tex = abundance.tex
        assert r"\mathrm{He}" in tex
        assert r"\mathrm{H}" in tex
        assert r"\mathrm{photo}" in tex
        assert ":" in tex

    def test_tex_with_known_species(self):
        """Test TeX formatting with known species translations."""
        abundance = ElementalAbundance("He", "H")
        tex = abundance.tex
        # Should translate to LaTeX representations
        assert "He" in tex
        assert "H" in tex

    def test_tex_with_unknown_species(self):
        """Test TeX formatting with unknown species."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abundance = ElementalAbundance("Xx", "Yy")
        tex = abundance.tex
        # Should use species names directly when not in translation dict
        assert "Xx" in tex or "Yy" in tex


class TestElementalAbundancePath:
    """Test ElementalAbundance path generation."""

    def test_path_basic_ratio(self):
        """Test path generation for basic ratio."""
        abundance = ElementalAbundance("He", "H", photospheric=False)
        path = abundance.path
        assert isinstance(path, Path)
        assert "He-OV-H" in str(path)

    def test_path_photospheric_ratio(self):
        """Test path generation for photospheric ratio."""
        abundance = ElementalAbundance("He", "H", photospheric=True)
        path = abundance.path
        assert isinstance(path, Path)
        assert "He-OV-H" in str(path)
        assert "photospheric-ratio" in str(path)

    def test_path_special_characters(self):
        """Test path generation handles special characters."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abundance = ElementalAbundance("C/N", "H", photospheric=False)
        path = abundance.path
        # Path should contain separator
        assert "C/N-OV-H" in str(path)


class TestElementalAbundanceSetMethods:
    """Test ElementalAbundance setter methods."""

    def test_set_species_basic(self):
        """Test set_species method with valid species."""
        abundance = ElementalAbundance("He", "H")
        abundance.set_species("Fe", "O")
        assert abundance.species == "Fe"
        assert abundance.reference_species == "O"

    def test_set_species_case_conversion(self):
        """Test set_species converts to title case."""
        abundance = ElementalAbundance("He", "H")
        abundance.set_species("fe", "o")
        assert abundance.species == "Fe"
        assert abundance.reference_species == "O"

    def test_set_species_unknown_warning(self):
        """Test set_species warns for unknown species."""
        abundance = ElementalAbundance("He", "H")
        with patch("logging.getLogger") as mock_logger:
            mock_log = mock_logger.return_value
            abundance.set_species("Unknown", "H")
            mock_log.warning.assert_called()

    def test_set_species_unknown_reference_warning(self):
        """Test set_species warns for unknown reference species."""
        abundance = ElementalAbundance("He", "H")
        with patch("logging.getLogger") as mock_logger:
            mock_log = mock_logger.return_value
            abundance.set_species("He", "Unknown")
            mock_log.warning.assert_called()


class TestElementalAbundanceInheritance:
    """Test ElementalAbundance inheritance from Base."""

    def test_inheritance_from_base(self):
        """Test ElementalAbundance inherits from Base."""
        from solarwindpy.plotting.labels.base import Base

        abundance = ElementalAbundance("He", "H")
        assert isinstance(abundance, Base)

    def test_string_representation(self):
        """Test string representation uses with_units property."""
        abundance = ElementalAbundance("He", "H")
        str_repr = str(abundance)
        assert "$" in str_repr  # LaTeX formatting
        assert r"\left[" in str_repr  # Units formatting

    def test_comparison_operators(self):
        """Test comparison operators work correctly."""
        abundance1 = ElementalAbundance("He", "H")
        abundance2 = ElementalAbundance("He", "H")
        abundance3 = ElementalAbundance("Fe", "H")

        assert abundance1 == abundance2
        assert abundance1 != abundance3

    def test_hash_functionality(self):
        """Test ElementalAbundance objects are hashable."""
        abundance = ElementalAbundance("He", "H")
        hash_value = hash(abundance)
        assert isinstance(hash_value, int)


class TestElementalAbundanceKnownSpecies:
    """Test known species functionality."""

    def test_known_species_import(self):
        """Test known_species is properly imported."""
        from solarwindpy.plotting.labels.elemental_abundance import known_species

        assert isinstance(known_species, tuple)
        assert "H" in known_species
        assert "He" in known_species
        assert "X" in known_species  # Special case

    def test_known_species_validation(self):
        """Test validation against known species."""
        # Should not warn for known species
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            ElementalAbundance("He", "H")
            # Filter out unrelated warnings
            relevant_warnings = [
                warning for warning in w if "not recognized" in str(warning.message)
            ]
            assert len(relevant_warnings) == 0

    def test_unknown_species_validation(self):
        """Test validation warns for unknown species."""
        import logging

        with patch("logging.getLogger") as mock_logger:
            mock_log = mock_logger.return_value
            ElementalAbundance("Unknown", "H")
            # Should have warning for unknown species
            mock_log.warning.assert_called()


class TestElementalAbundanceIntegration:
    """Test ElementalAbundance integration scenarios."""

    def test_common_abundance_ratios(self):
        """Test common abundance ratios used in solar wind."""
        # He/H ratio
        he_h = ElementalAbundance("He", "H")
        assert "He" in he_h.tex
        assert "H" in he_h.tex

        # Fe/O ratio
        fe_o = ElementalAbundance("Fe", "O")
        assert "Fe" in fe_o.tex
        assert "O" in fe_o.tex

    def test_photospheric_vs_solar_wind(self):
        """Test photospheric vs solar wind abundance comparison."""
        photospheric = ElementalAbundance("He", "H", photospheric=True)
        solar_wind = ElementalAbundance("He", "H", photospheric=False)

        assert r"\mathrm{photo}" in photospheric.tex
        assert r"\mathrm{photo}" not in solar_wind.tex
        assert "photospheric-ratio" in str(photospheric.path)
        assert "photospheric-ratio" not in str(solar_wind.path)

    def test_percentage_vs_ratio_units(self):
        """Test percentage vs ratio unit formatting."""
        percentage = ElementalAbundance("He", "H", pct_unit=True)
        ratio = ElementalAbundance("He", "H", pct_unit=False)

        assert percentage.units == r"\%"
        assert ratio.units == r"\#"

    def test_multiple_abundance_uniqueness(self):
        """Test multiple abundance objects maintain uniqueness."""
        he_h = ElementalAbundance("He", "H")
        fe_h = ElementalAbundance("Fe", "H")
        c_o = ElementalAbundance("C", "O")

        # All should have different paths
        paths = [str(ab.path) for ab in [he_h, fe_h, c_o]]
        assert len(set(paths)) == 3

        # All should have different tex representations
        tex_reprs = [ab.tex for ab in [he_h, fe_h, c_o]]
        assert len(set(tex_reprs)) == 3

    def test_scientific_accuracy(self):
        """Test scientific accuracy of abundance representations."""
        # Standard solar wind abundance ratio
        he_h = ElementalAbundance("He", "H", photospheric=True)

        # Should show ratio format for abundance comparison
        assert ":" in he_h.tex  # Comparison format
        assert "/" in he_h.tex  # Ratio format

        # Units should be dimensionless for abundance ratios
        ratio_abundance = ElementalAbundance("He", "H", pct_unit=False)
        assert ratio_abundance.units == r"\#"


class TestElementalAbundanceEdgeCases:
    """Test ElementalAbundance edge cases and error handling."""

    def test_same_species_ratio(self):
        """Test abundance ratio of same species."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abundance = ElementalAbundance("H", "H")

        assert abundance.species == "H"
        assert abundance.reference_species == "H"
        # Should still generate valid TeX
        assert r"\mathrm{H}" in abundance.tex

    def test_empty_string_species(self):
        """Test handling of empty string species."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abundance = ElementalAbundance("", "H")

        assert abundance.species == ""
        assert abundance.reference_species == "H"

    def test_numeric_species_names(self):
        """Test handling of numeric species names."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            abundance = ElementalAbundance("3He", "4He")

        assert abundance.species == "3He"
        assert abundance.reference_species == "4He"
        # Should handle isotope notation (3He becomes ^{3}\mathrm{He})
        tex = abundance.tex
        assert "He" in tex  # Base element should be present
        assert "3" in tex  # Mass number should be present
        assert "4" in tex  # Mass number should be present


def test_module_all_attribute():
    """Test module __all__ attribute is correctly defined."""
    from solarwindpy.plotting.labels import elemental_abundance

    assert hasattr(elemental_abundance, "__all__")
    assert "ElementalAbundance" in elemental_abundance.__all__


def test_module_imports():
    """Test module can be imported correctly."""
    from solarwindpy.plotting.labels.elemental_abundance import ElementalAbundance
    from solarwindpy.plotting.labels.elemental_abundance import known_species

    assert ElementalAbundance is not None
    assert known_species is not None
