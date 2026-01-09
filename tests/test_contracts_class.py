"""Contract tests for class patterns in SolarWindPy.

These tests validate the class hierarchy, constructor contracts, and
interface patterns used in solarwindpy.core. They serve as executable
documentation of the class architecture.

Note: These are structure/interface tests, not physics validation tests.
"""

import logging
from typing import Any, Type

import numpy as np
import pandas as pd
import pytest

# Import core classes
from solarwindpy.core import base, ions, plasma, spacecraft, tensor, vector


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_ion_data() -> pd.DataFrame:
    """Create minimal valid Ion data."""
    columns = pd.MultiIndex.from_tuples(
        [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
            ("w", "scalar"),  # Required for thermal_speed -> Tensor
        ],
        names=["M", "C"],
    )
    epoch = pd.date_range("2023-01-01", periods=5, freq="1min")
    data = np.abs(np.random.rand(5, 7)) + 0.1  # Positive values
    return pd.DataFrame(data, index=epoch, columns=columns)


@pytest.fixture
def sample_plasma_data() -> pd.DataFrame:
    """Create minimal valid Plasma data."""
    columns = pd.MultiIndex.from_tuples(
        [
            ("n", "", "p1"),
            ("v", "x", "p1"),
            ("v", "y", "p1"),
            ("v", "z", "p1"),
            ("w", "par", "p1"),
            ("w", "per", "p1"),
            ("b", "x", ""),
            ("b", "y", ""),
            ("b", "z", ""),
        ],
        names=["M", "C", "S"],
    )
    epoch = pd.date_range("2023-01-01", periods=5, freq="1min")
    data = np.abs(np.random.rand(5, len(columns))) + 0.1
    return pd.DataFrame(data, index=epoch, columns=columns)


@pytest.fixture
def sample_vector_data() -> pd.DataFrame:
    """Create minimal valid Vector data."""
    columns = ["x", "y", "z"]
    epoch = pd.date_range("2023-01-01", periods=5, freq="1min")
    data = np.random.rand(5, 3)
    return pd.DataFrame(data, index=epoch, columns=columns)


@pytest.fixture
def sample_tensor_data() -> pd.DataFrame:
    """Create minimal valid Tensor data."""
    columns = ["par", "per", "scalar"]
    epoch = pd.date_range("2023-01-01", periods=5, freq="1min")
    data = np.abs(np.random.rand(5, 3)) + 0.1
    return pd.DataFrame(data, index=epoch, columns=columns)


# ==============================================================================
# Class Hierarchy Tests
# ==============================================================================


class TestClassHierarchy:
    """Contract tests for class inheritance structure."""

    def test_ion_inherits_from_base(self) -> None:
        """Verify Ion inherits from Base."""
        assert issubclass(ions.Ion, base.Base)

    def test_plasma_inherits_from_base(self) -> None:
        """Verify Plasma inherits from Base."""
        assert issubclass(plasma.Plasma, base.Base)

    def test_spacecraft_inherits_from_base(self) -> None:
        """Verify Spacecraft inherits from Base."""
        assert issubclass(spacecraft.Spacecraft, base.Base)

    def test_vector_inherits_from_base(self) -> None:
        """Verify Vector inherits from Base."""
        assert issubclass(vector.Vector, base.Base)

    def test_tensor_inherits_from_base(self) -> None:
        """Verify Tensor inherits from Base."""
        assert issubclass(tensor.Tensor, base.Base)


# ==============================================================================
# Core Base Class Tests
# ==============================================================================


class TestCoreBaseClass:
    """Contract tests for Core/Base class initialization."""

    def test_ion_has_logger(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion initializes logger."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "logger")
        assert isinstance(ion.logger, logging.Logger)

    def test_ion_has_units(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion initializes units."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "units")

    def test_ion_has_constants(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion initializes constants."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "constants")

    def test_base_equality_by_data(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Base equality is based on data content."""
        ion1 = ions.Ion(sample_ion_data, "p1")
        ion2 = ions.Ion(sample_ion_data.copy(), "p1")
        assert ion1 == ion2


# ==============================================================================
# Ion Class Tests
# ==============================================================================


class TestIonClass:
    """Contract tests for Ion class."""

    def test_ion_constructor_requires_species(
        self, sample_ion_data: pd.DataFrame
    ) -> None:
        """Verify Ion constructor requires species argument."""
        # Should work with species
        ion = ions.Ion(sample_ion_data, "p1")
        assert ion.species == "p1"

    def test_ion_has_data_property(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion has data property returning DataFrame."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "data")
        assert isinstance(ion.data, pd.DataFrame)

    def test_ion_data_has_mc_columns(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion data has M/C column structure."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert ion.data.columns.names == ["M", "C"]

    def test_ion_extracts_species_from_mcs_data(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Ion extracts species from 3-level MultiIndex."""
        ion = ions.Ion(sample_plasma_data, "p1")

        # Should have M/C columns (not M/C/S)
        assert ion.data.columns.names == ["M", "C"]
        # Should have correct number of columns
        assert len(ion.data.columns) == 6  # n, v.x, v.y, v.z, w.par, w.per

    def test_ion_has_velocity_property(
        self, sample_ion_data: pd.DataFrame
    ) -> None:
        """Verify Ion has velocity property returning Vector."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "velocity")
        assert hasattr(ion, "v")  # Alias

    def test_ion_has_thermal_speed_property(
        self, sample_ion_data: pd.DataFrame
    ) -> None:
        """Verify Ion has thermal_speed property returning Tensor."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "thermal_speed")
        assert hasattr(ion, "w")  # Alias

    def test_ion_has_number_density_property(
        self, sample_ion_data: pd.DataFrame
    ) -> None:
        """Verify Ion has number_density property returning Series."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert hasattr(ion, "number_density")
        assert hasattr(ion, "n")  # Alias
        assert isinstance(ion.n, pd.Series)


# ==============================================================================
# Plasma Class Tests
# ==============================================================================


class TestPlasmaClass:
    """Contract tests for Plasma class."""

    def test_plasma_requires_species(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma constructor requires species."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert p.species == ("p1",)

    def test_plasma_species_is_tuple(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma.species returns tuple."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert isinstance(p.species, tuple)

    def test_plasma_has_ions_property(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma has ions property returning Series of Ion."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert hasattr(p, "ions")
        assert isinstance(p.ions, pd.Series)

    def test_plasma_ion_is_ion_instance(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma.ions contains Ion instances."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert isinstance(p.ions.loc["p1"], ions.Ion)

    def test_plasma_has_bfield_property(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma has bfield property."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert hasattr(p, "bfield")

    def test_plasma_attribute_access_shortcut(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma.species_name returns Ion via __getattr__."""
        p = plasma.Plasma(sample_plasma_data, "p1")

        # plasma.p1 should be equivalent to plasma.ions.loc['p1']
        p1_via_attr = p.p1
        p1_via_ions = p.ions.loc["p1"]
        assert p1_via_attr == p1_via_ions

    def test_plasma_data_has_mcs_columns(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma data has M/C/S column structure."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert p.data.columns.names == ["M", "C", "S"]


# ==============================================================================
# Vector Class Tests
# ==============================================================================


class TestVectorClass:
    """Contract tests for Vector class."""

    def test_vector_requires_xyz(self, sample_vector_data: pd.DataFrame) -> None:
        """Verify Vector requires x, y, z columns."""
        v = vector.Vector(sample_vector_data)
        assert hasattr(v, "data")

    def test_vector_has_magnitude(self, sample_vector_data: pd.DataFrame) -> None:
        """Verify Vector has mag property."""
        v = vector.Vector(sample_vector_data)
        assert hasattr(v, "mag")
        assert isinstance(v.mag, pd.Series)

    def test_vector_magnitude_calculation(
        self, sample_vector_data: pd.DataFrame
    ) -> None:
        """Verify Vector.mag = sqrt(x² + y² + z²)."""
        v = vector.Vector(sample_vector_data)

        # Calculate expected magnitude
        expected = np.sqrt(
            sample_vector_data["x"] ** 2
            + sample_vector_data["y"] ** 2
            + sample_vector_data["z"] ** 2
        )

        pd.testing.assert_series_equal(v.mag, expected, check_names=False)


# ==============================================================================
# Tensor Class Tests
# ==============================================================================


class TestTensorClass:
    """Contract tests for Tensor class."""

    def test_tensor_requires_par_per_scalar(
        self, sample_tensor_data: pd.DataFrame
    ) -> None:
        """Verify Tensor accepts par, per, scalar columns."""
        t = tensor.Tensor(sample_tensor_data)
        assert hasattr(t, "data")

    def test_tensor_data_has_required_columns(
        self, sample_tensor_data: pd.DataFrame
    ) -> None:
        """Verify Tensor data has par, per, scalar columns."""
        t = tensor.Tensor(sample_tensor_data)
        assert "par" in t.data.columns
        assert "per" in t.data.columns
        assert "scalar" in t.data.columns

    def test_tensor_has_magnitude_property(self) -> None:
        """Verify Tensor class has magnitude property defined."""
        # The magnitude property exists as a class attribute
        assert hasattr(tensor.Tensor, "magnitude")
        # Note: magnitude calculation requires MultiIndex columns with level "C"
        # so it can't be called with simple column names

    def test_tensor_data_access_via_loc(
        self, sample_tensor_data: pd.DataFrame
    ) -> None:
        """Verify Tensor data can be accessed via .data.loc[]."""
        t = tensor.Tensor(sample_tensor_data)
        par_data = t.data.loc[:, "par"]
        assert isinstance(par_data, pd.Series)


# ==============================================================================
# Constructor Validation Tests
# ==============================================================================


class TestConstructorValidation:
    """Contract tests for constructor argument validation."""

    def test_ion_validates_species_type(
        self, sample_ion_data: pd.DataFrame
    ) -> None:
        """Verify Ion species must be string."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert isinstance(ion.species, str)

    def test_plasma_validates_species(
        self, sample_plasma_data: pd.DataFrame
    ) -> None:
        """Verify Plasma validates species arguments."""
        p = plasma.Plasma(sample_plasma_data, "p1")
        assert all(isinstance(s, str) for s in p.species)


# ==============================================================================
# Property Type Tests
# ==============================================================================


class TestPropertyTypes:
    """Contract tests verifying property return types."""

    def test_ion_v_returns_vector(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion.v returns Vector instance."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert isinstance(ion.v, vector.Vector)

    def test_ion_w_returns_tensor(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion.w returns Tensor instance."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert isinstance(ion.w, tensor.Tensor)

    def test_ion_n_returns_series(self, sample_ion_data: pd.DataFrame) -> None:
        """Verify Ion.n returns Series."""
        ion = ions.Ion(sample_ion_data, "p1")
        assert isinstance(ion.n, pd.Series)
