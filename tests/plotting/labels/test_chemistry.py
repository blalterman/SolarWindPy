"""Tests for :mod:`solarwindpy.plotting.labels.chemistry` constants."""

from pathlib import Path

import pytest

from solarwindpy.plotting.labels import chemistry
from solarwindpy.plotting.labels.special import ManualLabel


@pytest.mark.parametrize(
    "label, expected_tex, expected_unit, expected_path",
    [
        (
            chemistry.mass_per_charge,
            r"\mathrm{M/Q}",
            r"\mathrm{AMU \, e^{-1}}",
            Path("M-OV-Q"),
        ),
        (
            chemistry.fip,
            r"\mathrm{FIP}",
            r"\mathrm{eV}",
            Path("FIP"),
        ),
        (
            chemistry.charge,
            r"\mathrm{Q}",
            r"\mathrm{e}",
            Path("IonCharge"),
        ),
        (
            chemistry.mass,
            r"\mathrm{M}",
            r"\mathrm{AMU}",
            Path("IonMass"),
        ),
    ],
)
def test_manual_label_attributes(label, expected_tex, expected_unit, expected_path):
    """Ensure each ``ManualLabel`` exposes the correct values."""

    assert label.tex == expected_tex
    assert label.unit == expected_unit
    assert label.path == expected_path


class TestChemistryLabels:
    """Test chemistry label constants comprehensively."""

    def test_all_labels_are_manual_labels(self):
        """Test that all chemistry labels are ManualLabel instances."""
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        for label in labels:
            assert isinstance(label, ManualLabel)

    def test_mass_per_charge_properties(self):
        """Test mass per charge label properties."""
        label = chemistry.mass_per_charge
        assert "M/Q" in label.tex
        assert "AMU" in label.unit
        assert "e^{-1}" in label.unit
        assert str(label.path) == "M-OV-Q"

    def test_fip_properties(self):
        """Test First Ionization Potential label properties."""
        label = chemistry.fip
        assert "FIP" in label.tex
        assert "eV" in label.unit
        assert str(label.path) == "FIP"

    def test_charge_properties(self):
        """Test ion charge label properties."""
        label = chemistry.charge
        assert "Q" in label.tex
        assert "e" in label.unit
        assert str(label.path) == "IonCharge"

    def test_mass_properties(self):
        """Test ion mass label properties."""
        label = chemistry.mass
        assert "M" in label.tex
        assert "AMU" in label.unit
        assert str(label.path) == "IonMass"

    def test_string_representation(self):
        """Test string representations of chemistry labels."""
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        for label in labels:
            str_repr = str(label)
            assert str_repr.startswith("$")
            assert str_repr.endswith("$")
            assert "[" in str_repr  # Units are included
            assert "]" in str_repr

    def test_label_uniqueness(self):
        """Test that all labels have unique tex, units, and paths."""
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        # Test unique tex
        tex_values = [label.tex for label in labels]
        assert len(tex_values) == len(set(tex_values))

        # Test unique units
        unit_values = [label.unit for label in labels]
        assert len(unit_values) == len(set(unit_values))

        # Test unique paths
        path_values = [str(label.path) for label in labels]
        assert len(path_values) == len(set(path_values))

    def test_label_inheritance(self):
        """Test that labels inherit from base classes correctly."""
        from solarwindpy.plotting.labels.base import Base

        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        for label in labels:
            assert isinstance(label, Base)  # Should inherit from Base
            assert hasattr(label, "logger")  # Should have logger from Base

    def test_tex_formatting(self):
        """Test TeX formatting is correct."""
        # Test that math mode indicators are properly stripped from tex
        assert chemistry.mass_per_charge.tex == r"\mathrm{M/Q}"
        assert chemistry.fip.tex == r"\mathrm{FIP}"
        assert chemistry.charge.tex == r"\mathrm{Q}"
        assert chemistry.mass.tex == r"\mathrm{M}"

    def test_unit_formatting(self):
        """Test unit formatting is correct."""
        # Test specific unit formatting
        assert chemistry.mass_per_charge.unit == r"\mathrm{AMU \, e^{-1}}"
        assert chemistry.fip.unit == r"\mathrm{eV}"
        assert chemistry.charge.unit == r"\mathrm{e}"
        assert chemistry.mass.unit == r"\mathrm{AMU}"

    def test_path_types(self):
        """Test that all paths are Path objects."""
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        for label in labels:
            assert isinstance(label.path, Path)

    def test_label_comparison(self):
        """Test label comparison based on string representation."""
        # Labels should be comparable
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        # Test equality (should be equal to themselves)
        for label in labels:
            assert label == label

        # Test inequality (different labels should not be equal)
        for i, label1 in enumerate(labels):
            for j, label2 in enumerate(labels):
                if i != j:
                    assert label1 != label2

    def test_label_hashing(self):
        """Test that labels can be hashed."""
        labels = [
            chemistry.mass_per_charge,
            chemistry.fip,
            chemistry.charge,
            chemistry.mass,
        ]

        # Should be able to create a set (requires hashing)
        label_set = set(labels)
        assert len(label_set) == len(labels)

        # Should be able to use as dictionary keys
        label_dict = {label: str(label) for label in labels}
        assert len(label_dict) == len(labels)

    def test_module_attributes(self):
        """Test that the chemistry module has all expected attributes."""
        expected_attrs = ["mass_per_charge", "fip", "charge", "mass"]

        for attr in expected_attrs:
            assert hasattr(chemistry, attr)
            label = getattr(chemistry, attr)
            assert isinstance(label, ManualLabel)

    def test_label_immutability(self):
        """Test that label properties are effectively immutable."""
        original_tex = chemistry.mass.tex
        original_unit = chemistry.mass.unit
        original_path = chemistry.mass.path

        # These properties should be read-only
        # (We can't directly test immutability, but we can test they return consistent values)
        assert chemistry.mass.tex == original_tex
        assert chemistry.mass.unit == original_unit
        assert chemistry.mass.path == original_path

    def test_scientific_accuracy(self):
        """Test that labels represent scientifically accurate concepts."""
        # Mass per charge should use atomic mass units per elementary charge
        assert "AMU" in chemistry.mass_per_charge.unit
        assert "e^{-1}" in chemistry.mass_per_charge.unit

        # FIP should use electron volts
        assert "eV" in chemistry.fip.unit

        # Charge should use elementary charge units
        assert "e" in chemistry.charge.unit

        # Mass should use atomic mass units
        assert "AMU" in chemistry.mass.unit
