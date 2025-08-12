"""Tests for :mod:`solarwindpy.plotting.labels.chemistry` constants."""

from pathlib import Path

import pytest

from solarwindpy.plotting.labels import chemistry


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
