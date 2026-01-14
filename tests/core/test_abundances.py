"""Tests for ReferenceAbundances class.

Tests verify:
1. Data structure matches expected CSV format
2. Values match published Asplund 2009 Table 1
3. Uncertainty propagation formula is correct
4. Edge cases (NaN, H denominator) handled properly

Run: pytest tests/core/test_abundances.py -v
"""

import numpy as np
import pandas as pd
import pytest

from solarwindpy.core.abundances import ReferenceAbundances, Abundance


class TestDataStructure:
    """Verify CSV loads with correct structure."""

    @pytest.fixture
    def ref(self):
        return ReferenceAbundances()

    def test_data_is_dataframe(self, ref):
        # NOT: assert ref.data is not None (trivial)
        # GOOD: Verify specific type
        assert isinstance(
            ref.data, pd.DataFrame
        ), f"Expected DataFrame, got {type(ref.data)}"

    def test_data_has_83_elements(self, ref):
        # Verify row count matches Asplund Table 1
        assert (
            ref.data.shape[0] == 83
        ), f"Expected 83 elements (Asplund Table 1), got {ref.data.shape[0]}"

    def test_index_is_multiindex_with_z_symbol(self, ref):
        assert isinstance(
            ref.data.index, pd.MultiIndex
        ), f"Expected MultiIndex, got {type(ref.data.index)}"
        assert list(ref.data.index.names) == [
            "Z",
            "Symbol",
        ], f"Expected index levels ['Z', 'Symbol'], got {ref.data.index.names}"

    def test_columns_have_photosphere_and_meteorites(self, ref):
        top_level = ref.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, "Missing 'Photosphere' column group"
        assert "Meteorites" in top_level, "Missing 'Meteorites' column group"

    def test_data_dtype_is_float64(self, ref):
        # All values should be float64 after .astype(np.float64)
        for col in ref.data.columns:
            assert (
                ref.data[col].dtype == np.float64
            ), f"Column {col} has dtype {ref.data[col].dtype}, expected float64"

    def test_h_has_nan_photosphere_uncertainty(self, ref):
        # H photosphere uncertainty is NaN (by definition, H is the reference)
        h = ref.get_element("H")
        assert np.isnan(h.Uncert), f"H uncertainty should be NaN, got {h.Uncert}"

    def test_arsenic_photosphere_is_nan(self, ref):
        # As (Z=33) has no photospheric measurement (only meteoritic)
        arsenic = ref.get_element("As", kind="Photosphere")
        assert np.isnan(
            arsenic.Ab
        ), f"As photosphere Ab should be NaN, got {arsenic.Ab}"


class TestGetElement:
    """Verify element lookup by symbol and Z."""

    @pytest.fixture
    def ref(self):
        return ReferenceAbundances()

    def test_get_element_by_symbol_returns_series(self, ref):
        fe = ref.get_element("Fe")
        assert isinstance(fe, pd.Series), f"Expected Series, got {type(fe)}"

    def test_iron_photosphere_matches_asplund(self, ref):
        # Asplund 2009 Table 1: Fe = 7.50 +/- 0.04
        fe = ref.get_element("Fe")
        assert np.isclose(
            fe.Ab, 7.50, atol=0.01
        ), f"Fe photosphere Ab: expected 7.50, got {fe.Ab}"
        assert np.isclose(
            fe.Uncert, 0.04, atol=0.01
        ), f"Fe photosphere Uncert: expected 0.04, got {fe.Uncert}"

    def test_get_element_by_z_matches_symbol(self, ref):
        # Z=26 is Fe, should return identical data values
        # Note: Series names differ (26 vs 'Fe') but values are identical
        by_symbol = ref.get_element("Fe")
        by_z = ref.get_element(26)
        pd.testing.assert_series_equal(by_symbol, by_z, check_names=False)

    def test_get_element_meteorites_differs_from_photosphere(self, ref):
        # Fe meteorites: 7.45 vs photosphere: 7.50
        photo = ref.get_element("Fe", kind="Photosphere")
        meteor = ref.get_element("Fe", kind="Meteorites")
        assert (
            photo.Ab != meteor.Ab
        ), "Photosphere and Meteorites should have different values"
        assert np.isclose(
            meteor.Ab, 7.45, atol=0.01
        ), f"Fe meteorites Ab: expected 7.45, got {meteor.Ab}"

    def test_invalid_key_type_raises_valueerror(self, ref):
        with pytest.raises(ValueError, match="Unrecognized key type"):
            ref.get_element(3.14)  # float is invalid

    def test_unknown_element_raises_keyerror(self, ref):
        with pytest.raises(KeyError, match="Xx"):
            ref.get_element("Xx")  # No element Xx

    def test_invalid_kind_raises_keyerror(self, ref):
        with pytest.raises(KeyError, match="Invalid"):
            ref.get_element("Fe", kind="Invalid")


class TestAbundanceRatio:
    """Verify ratio calculation with uncertainty propagation."""

    @pytest.fixture
    def ref(self):
        return ReferenceAbundances()

    def test_returns_abundance_namedtuple(self, ref):
        result = ref.abundance_ratio("Fe", "O")
        assert isinstance(
            result, Abundance
        ), f"Expected Abundance namedtuple, got {type(result)}"
        assert hasattr(result, "measurement"), "Missing 'measurement' attribute"
        assert hasattr(result, "uncertainty"), "Missing 'uncertainty' attribute"

    def test_fe_o_ratio_matches_computed_value(self, ref):
        # Fe/O = 10^(7.50 - 8.69) = 0.06457
        result = ref.abundance_ratio("Fe", "O")
        expected = 10.0 ** (7.50 - 8.69)
        assert np.isclose(
            result.measurement, expected, rtol=0.01
        ), f"Fe/O ratio: expected {expected:.5f}, got {result.measurement:.5f}"

    def test_fe_o_uncertainty_matches_formula(self, ref):
        # sigma = ratio * ln(10) * sqrt(sigma_Fe^2 + sigma_O^2)
        # sigma = 0.06457 * 2.303 * sqrt(0.04^2 + 0.05^2) = 0.00951
        result = ref.abundance_ratio("Fe", "O")
        expected_ratio = 10.0 ** (7.50 - 8.69)
        expected_uncert = expected_ratio * np.log(10) * np.sqrt(0.04**2 + 0.05**2)
        assert np.isclose(
            result.uncertainty, expected_uncert, rtol=0.01
        ), f"Fe/O uncertainty: expected {expected_uncert:.5f}, got {result.uncertainty:.5f}"

    def test_c_o_ratio_matches_computed_value(self, ref):
        # C/O = 10^(8.43 - 8.69) = 0.5495
        result = ref.abundance_ratio("C", "O")
        expected = 10.0 ** (8.43 - 8.69)
        assert np.isclose(
            result.measurement, expected, rtol=0.01
        ), f"C/O ratio: expected {expected:.4f}, got {result.measurement:.4f}"

    def test_ratio_destructuring_works(self, ref):
        # Verify namedtuple can be destructured
        measurement, uncertainty = ref.abundance_ratio("Fe", "O")
        assert isinstance(measurement, float), "measurement should be float"
        assert isinstance(uncertainty, float), "uncertainty should be float"


class TestHydrogenDenominator:
    """Verify special case when denominator is H."""

    @pytest.fixture
    def ref(self):
        return ReferenceAbundances()

    def test_fe_h_uses_convert_from_dex(self, ref):
        # Fe/H = 10^(7.50 - 12) = 3.162e-5
        result = ref.abundance_ratio("Fe", "H")
        expected = 10.0 ** (7.50 - 12.0)
        assert np.isclose(
            result.measurement, expected, rtol=0.01
        ), f"Fe/H ratio: expected {expected:.3e}, got {result.measurement:.3e}"

    def test_fe_h_uncertainty_from_numerator_only(self, ref):
        # H has no uncertainty, so sigma = Fe_linear * ln(10) * sigma_Fe
        result = ref.abundance_ratio("Fe", "H")
        fe_linear = 10.0 ** (7.50 - 12.0)
        expected_uncert = fe_linear * np.log(10) * 0.04
        assert np.isclose(
            result.uncertainty, expected_uncert, rtol=0.01
        ), f"Fe/H uncertainty: expected {expected_uncert:.3e}, got {result.uncertainty:.3e}"


class TestNaNHandling:
    """Verify NaN uncertainties are replaced with 0 in ratio calculations."""

    @pytest.fixture
    def ref(self):
        return ReferenceAbundances()

    def test_ratio_with_nan_uncertainty_uses_zero(self, ref):
        # H/O should use 0 for H's uncertainty
        # sigma = ratio * ln(10) * sqrt(0^2 + sigma_O^2) = ratio * ln(10) * sigma_O
        result = ref.abundance_ratio("H", "O")
        expected_ratio = 10.0 ** (12.00 - 8.69)
        expected_uncert = expected_ratio * np.log(10) * 0.05  # Only O contributes
        assert np.isclose(
            result.uncertainty, expected_uncert, rtol=0.01
        ), f"H/O uncertainty: expected {expected_uncert:.2f}, got {result.uncertainty:.2f}"
