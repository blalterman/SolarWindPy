"""Tests for :class:`ElementalAbundance`."""

import logging
import pytest

from solarwindpy.plotting.labels.elemental_abundance import ElementalAbundance


@pytest.mark.parametrize(
    "species,reference",
    [
        ("Fe", "O"),
        ("X", "Fe"),  # 'X' allowed
    ],
)
def test_initialization_recognized_species(species, reference, caplog):
    """Test initialization with recognized species.

    Parameters
    ----------
    species, reference : str
        Input species and reference species.
    caplog : ``pytest`` fixture
        Logger capture fixture.
    """
    with caplog.at_level(logging.WARNING):
        obj = ElementalAbundance(species, reference)
    assert obj.species == species.title()
    assert obj.reference_species == reference.title()
    assert not caplog.records


@pytest.mark.parametrize(
    "species,reference",
    [
        ("foo", "bar"),
        ("Xx", "Yy"),
    ],
)
def test_initialization_unrecognized_species(species, reference, caplog):
    """Unrecognized species should log warnings and still be set."""
    with caplog.at_level(logging.WARNING):
        obj = ElementalAbundance(species, reference)
    assert obj.species == species.title()
    assert obj.reference_species == reference.title()
    warnings = [r.message for r in caplog.records]
    assert f"Species ({species.title()}) is not recognized" in warnings[0]
    assert f"Reference species ({reference.title()}) is not recognized" in warnings[1]


def test_units_and_photospheric_flag():
    """Check units and photospheric options."""
    obj_pct = ElementalAbundance("Fe", "O", pct_unit=True, photospheric=True)
    assert obj_pct.units == r"\%"
    assert obj_pct.pct_unit is True
    assert str(obj_pct.path).endswith("_photospheric-ratio")
    assert ":" in obj_pct.tex

    obj_dim = ElementalAbundance("Fe", "O", pct_unit=False, photospheric=False)
    assert obj_dim.units == r"\#"  # noqa: W605
    assert obj_dim.pct_unit is False
    assert str(obj_dim.path) == "Fe-OV-O"
    assert obj_dim.tex == r"\mathrm{\mathrm{Fe}}/\mathrm{\mathrm{O}}"
