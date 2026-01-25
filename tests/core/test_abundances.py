"""Tests for ReferenceAbundances class.

Tests verify:
1. Data structure matches expected CSV format (both 2009 and 2021)
2. Values match published Asplund tables
3. Uncertainty propagation formula is correct
4. Edge cases (NaN, H denominator, missing photosphere) handled properly
5. Backward compatibility (Meteorites alias, year=2009)
6. Comments column (2021 only)

References
----------
Asplund, M., Amarsi, A. M., & Grevesse, N. (2021).
The chemical make-up of the Sun: A 2020 vision.
A&A, 653, A141. https://doi.org/10.1051/0004-6361/202140445

Asplund, M., Grevesse, N., Sauval, A. J., & Scott, P. (2009).
The Chemical Composition of the Sun.
Annu. Rev. Astron. Astrophys., 47, 481-522.
https://doi.org/10.1146/annurev.astro.46.060407.145222

Run: pytest tests/core/test_abundances.py -v
"""

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd
import pytest

from solarwindpy.core.abundances import ReferenceAbundances, Abundance


# =============================================================================
# Test Data Specifications
# =============================================================================


@dataclass(frozen=True)
class ElementData:
    """Expected values for a single element from published tables.

    Parameters
    ----------
    symbol : str
        Element symbol (e.g., 'Fe').
    z : int
        Atomic number.
    photosphere_ab : float or None
        Photospheric abundance in dex (None if no measurement).
    photosphere_uncert : float or None
        Photospheric uncertainty.
    ci_chondrites_ab : float
        CI chondrite abundance in dex.
    ci_chondrites_uncert : float
        CI chondrite uncertainty.
    comment : str or None
        Source comment (2021 only): 'definition', 'helioseismology', etc.
    """

    symbol: str
    z: int
    photosphere_ab: Optional[float]
    photosphere_uncert: Optional[float]
    ci_chondrites_ab: float
    ci_chondrites_uncert: float
    comment: Optional[str] = None


# Reference data keyed by year - values from published Asplund tables
ASPLUND_DATA: Dict[int, Dict[str, ElementData]] = {
    2009: {
        "H": ElementData("H", 1, 12.00, None, 8.22, 0.04),
        "He": ElementData("He", 2, 10.93, 0.01, 1.29, None),
        "Li": ElementData("Li", 3, 1.05, 0.10, 3.26, 0.05),
        "C": ElementData("C", 6, 8.43, 0.05, 7.39, 0.04),
        "N": ElementData("N", 7, 7.83, 0.05, 6.26, 0.06),
        "O": ElementData("O", 8, 8.69, 0.05, 8.40, 0.04),
        "Ne": ElementData("Ne", 10, 7.93, 0.10, None, None),
        "Fe": ElementData("Fe", 26, 7.50, 0.04, 7.45, 0.01),
        "Si": ElementData("Si", 14, 7.51, 0.03, 7.51, 0.01),
        "As": ElementData("As", 33, None, None, 2.30, 0.04),
    },
    2021: {
        "H": ElementData("H", 1, 12.00, 0.00, 8.22, 0.04, "definition"),
        "He": ElementData("He", 2, 10.914, 0.013, 1.29, 0.18, "helioseismology"),
        "Li": ElementData("Li", 3, 0.96, 0.06, 3.25, 0.04, "meteorites"),
        "C": ElementData("C", 6, 8.46, 0.04, 7.39, 0.04, None),
        "N": ElementData("N", 7, 7.83, 0.07, 6.26, 0.06, None),
        "O": ElementData("O", 8, 8.69, 0.04, 8.39, 0.04, None),
        "Ne": ElementData("Ne", 10, 8.06, 0.05, None, None, "solar wind"),
        "Fe": ElementData("Fe", 26, 7.46, 0.04, 7.46, 0.02, None),
        "Si": ElementData("Si", 14, 7.51, 0.03, 7.51, 0.01, None),
        "As": ElementData("As", 33, None, None, 2.30, 0.04, "meteorites"),
        "Xe": ElementData("Xe", 54, 2.22, 0.05, None, None, "nuclear physics"),
    },
}

# Elements with no photospheric data in BOTH years
# Note: Ir and Pt have photospheric data in 2009 but not 2021
ELEMENTS_WITHOUT_PHOTOSPHERE = [
    "As",
    "Se",
    "Br",
    "Cd",
    "Sb",
    "Te",
    "I",
    "Cs",
    "Ta",
    "Re",
    # "Ir",  # Has data in 2009, not 2021
    # "Pt",  # Has data in 2009, not 2021
    "Hg",
    "Bi",
    "U",
]

# Expected abundance ratios computed from published values
# Format: (expected_ratio, sigma_numerator, sigma_denominator)
EXPECTED_RATIOS: Dict[int, Dict[tuple, tuple]] = {
    2009: {
        ("Fe", "O"): (10.0 ** (7.50 - 8.69), 0.04, 0.05),
        ("C", "O"): (10.0 ** (8.43 - 8.69), 0.05, 0.05),
        ("Fe", "H"): (10.0 ** (7.50 - 12.0), 0.04, 0.0),
    },
    2021: {
        ("Fe", "O"): (10.0 ** (7.46 - 8.69), 0.04, 0.04),
        ("C", "O"): (10.0 ** (8.46 - 8.69), 0.04, 0.04),
        ("Fe", "H"): (10.0 ** (7.46 - 12.0), 0.04, 0.0),
    },
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(params=[2009, 2021], ids=["asplund2009", "asplund2021"])
def ref_any_year(request):
    """ReferenceAbundances instance for both years (structural tests)."""
    return ReferenceAbundances(year=request.param)


@pytest.fixture
def ref_2021():
    """ReferenceAbundances with 2021 data (default)."""
    return ReferenceAbundances()


@pytest.fixture
def ref_2009():
    """ReferenceAbundances with 2009 data."""
    return ReferenceAbundances(year=2009)


@pytest.fixture(params=[2009, 2021], ids=["asplund2009", "asplund2021"])
def ref_with_year(request):
    """Tuple of (ReferenceAbundances, year) for value-parameterized tests."""
    year = request.param
    return ReferenceAbundances(year=year), year


# =============================================================================
# Smoke Tests: Data Loading
# =============================================================================


class TestDataLoading:
    """Smoke tests: verify data files load without errors."""

    def test_default_loads_2021_data(self):
        """Default initialization loads 2021 data."""
        ref = ReferenceAbundances()
        assert isinstance(ref.data, pd.DataFrame), (
            f"Expected pd.DataFrame, got {type(ref.data).__name__}"
        )
        assert ref.year == 2021, f"Expected default year=2021, got {ref.year}"

    def test_explicit_2021_loads(self):
        """year=2021 loads 2021 data explicitly."""
        ref = ReferenceAbundances(year=2021)
        assert isinstance(ref.data, pd.DataFrame), (
            f"Expected pd.DataFrame, got {type(ref.data).__name__}"
        )
        assert ref.year == 2021, f"Expected year=2021, got {ref.year}"

    def test_explicit_2009_loads(self):
        """year=2009 loads 2009 data for backward compatibility."""
        ref = ReferenceAbundances(year=2009)
        assert isinstance(ref.data, pd.DataFrame), (
            f"Expected pd.DataFrame, got {type(ref.data).__name__}"
        )
        assert ref.year == 2009, f"Expected year=2009, got {ref.year}"

    def test_invalid_year_raises_valueerror(self):
        """Invalid year raises ValueError with helpful message."""
        with pytest.raises(ValueError, match=r"year must be 2009 or 2021"):
            ReferenceAbundances(year=2000)

    def test_invalid_year_type_raises_typeerror(self):
        """Non-integer year raises TypeError."""
        with pytest.raises(TypeError, match=r"year must be an integer"):
            ReferenceAbundances(year="2021")


# =============================================================================
# Unit Tests: Data Structure
# =============================================================================


class TestDataStructure:
    """Unit tests for DataFrame structure: shape, dtype, index."""

    def test_data_is_dataframe(self, ref_any_year):
        """Data property returns pandas DataFrame."""
        assert isinstance(ref_any_year.data, pd.DataFrame), (
            f"Expected pd.DataFrame, got {type(ref_any_year.data).__name__}"
        )

    def test_data_has_83_elements(self, ref_any_year):
        """Both Asplund 2009 and 2021 have 83 elements."""
        assert ref_any_year.data.shape[0] == 83, (
            f"Expected 83 elements, got {ref_any_year.data.shape[0]}"
        )

    def test_index_is_multiindex_with_z_symbol(self, ref_any_year):
        """Index is MultiIndex with levels ['Z', 'Symbol']."""
        idx = ref_any_year.data.index
        assert isinstance(idx, pd.MultiIndex), (
            f"Expected MultiIndex, got {type(idx).__name__}"
        )
        assert list(idx.names) == ["Z", "Symbol"], (
            f"Expected index names ['Z', 'Symbol'], got {list(idx.names)}"
        )

    def test_columns_have_photosphere_and_ci_chondrites(self, ref_any_year):
        """Top-level columns include Photosphere and CI_chondrites."""
        top_level = ref_any_year.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, "Missing 'Photosphere' column group"
        assert "CI_chondrites" in top_level, "Missing 'CI_chondrites' column group"

    def test_columns_are_multiindex(self, ref_any_year):
        """Columns are MultiIndex with at least 2 levels."""
        assert isinstance(ref_any_year.data.columns, pd.MultiIndex), (
            f"Expected MultiIndex columns, got {type(ref_any_year.data.columns).__name__}"
        )
        assert ref_any_year.data.columns.nlevels >= 2, (
            f"Expected at least 2 column levels, got {ref_any_year.data.columns.nlevels}"
        )

    def test_abundance_values_are_float64(self, ref_any_year):
        """All Ab and Uncert columns are float64."""
        for col in ref_any_year.data.columns:
            # Check columns that contain abundance data
            if len(col) >= 2 and col[1] in ["Ab", "Uncert"]:
                dtype = ref_any_year.data[col].dtype
                assert dtype == np.float64, (
                    f"Column {col} has dtype {dtype}, expected float64"
                )

    @pytest.mark.parametrize("z", [1, 26, 92])
    def test_key_z_values_present(self, ref_any_year, z):
        """Key atomic numbers (H=1, Fe=26, U=92) are present in index."""
        z_values = ref_any_year.data.index.get_level_values("Z").tolist()
        assert z in z_values, f"Z={z} not found in index"

    @pytest.mark.parametrize("symbol", ["H", "He", "C", "O", "Fe", "Si"])
    def test_key_symbols_present(self, ref_any_year, symbol):
        """Key element symbols are present in index."""
        symbols = ref_any_year.data.index.get_level_values("Symbol").tolist()
        assert symbol in symbols, f"Symbol '{symbol}' not found in index"

    def test_z_values_are_integers(self, ref_any_year):
        """Z values in index are integers."""
        z_values = ref_any_year.data.index.get_level_values("Z")
        # Check that Z values can be used as integers
        assert all(isinstance(z, (int, np.integer)) for z in z_values), (
            "Z values should be integers"
        )

    def test_z_range_is_1_to_92(self, ref_any_year):
        """Z values range from 1 (H) to 92 (U)."""
        z_values = ref_any_year.data.index.get_level_values("Z")
        assert min(z_values) == 1, f"Expected min Z=1, got {min(z_values)}"
        assert max(z_values) == 92, f"Expected max Z=92, got {max(z_values)}"


# =============================================================================
# Unit Tests: Year Parameter
# =============================================================================


class TestYearParameter:
    """Unit tests for year parameter behavior."""

    def test_year_attribute_stored_2009(self, ref_2009):
        """Year is stored as instance attribute for 2009."""
        assert ref_2009.year == 2009, f"Expected year=2009, got {ref_2009.year}"

    def test_year_attribute_stored_2021(self, ref_2021):
        """Year is stored as instance attribute for 2021."""
        assert ref_2021.year == 2021, f"Expected year=2021, got {ref_2021.year}"

    def test_2009_fe_differs_from_2021(self):
        """Fe photosphere differs: 7.50 (2009) vs 7.46 (2021)."""
        ref_2009 = ReferenceAbundances(year=2009)
        ref_2021 = ReferenceAbundances(year=2021)

        fe_2009 = ref_2009.get_element("Fe")
        fe_2021 = ref_2021.get_element("Fe")

        # 2009: Fe = 7.50, 2021: Fe = 7.46
        assert not np.isclose(fe_2009.Ab, fe_2021.Ab, atol=0.01), (
            f"Fe should differ between years: 2009={fe_2009.Ab}, 2021={fe_2021.Ab}"
        )
        assert np.isclose(fe_2009.Ab, 7.50, atol=0.01), (
            f"2009 Fe should be 7.50, got {fe_2009.Ab}"
        )
        assert np.isclose(fe_2021.Ab, 7.46, atol=0.01), (
            f"2021 Fe should be 7.46, got {fe_2021.Ab}"
        )


# =============================================================================
# Unit Tests: Column Naming
# =============================================================================


class TestColumnNaming:
    """Unit tests for CI_chondrites column with Meteorites alias."""

    def test_ci_chondrites_in_columns(self, ref_any_year):
        """'CI_chondrites' is a top-level column."""
        top_level = ref_any_year.data.columns.get_level_values(0).unique().tolist()
        assert "CI_chondrites" in top_level, (
            f"'CI_chondrites' not in columns: {top_level}"
        )

    def test_photosphere_in_columns(self, ref_any_year):
        """'Photosphere' is a top-level column."""
        top_level = ref_any_year.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, f"'Photosphere' not in columns: {top_level}"

    def test_meteorites_alias_returns_ci_chondrites_data(self, ref_any_year):
        """kind='Meteorites' returns same data as kind='CI_chondrites'."""
        fe_meteorites = ref_any_year.get_element("Fe", kind="Meteorites")
        fe_ci_chondrites = ref_any_year.get_element("Fe", kind="CI_chondrites")

        pd.testing.assert_series_equal(
            fe_meteorites,
            fe_ci_chondrites,
            check_names=False,
            obj="Fe via kind='Meteorites' vs kind='CI_chondrites'",
        )

    def test_meteorites_alias_works_for_multiple_elements(self, ref_any_year):
        """Meteorites alias works consistently for multiple elements."""
        for symbol in ["H", "C", "O", "Si"]:
            via_alias = ref_any_year.get_element(symbol, kind="Meteorites")
            via_canonical = ref_any_year.get_element(symbol, kind="CI_chondrites")
            pd.testing.assert_series_equal(
                via_alias,
                via_canonical,
                check_names=False,
                obj=f"{symbol} via Meteorites vs CI_chondrites",
            )

    def test_invalid_kind_raises_keyerror(self, ref_any_year):
        """Invalid kind raises KeyError."""
        with pytest.raises(KeyError, match=r"Invalid|not found|unknown"):
            ref_any_year.get_element("Fe", kind="InvalidKind")


# =============================================================================
# Unit Tests: Comments Column (2021 only)
# =============================================================================


class TestCommentsColumn:
    """Unit tests for Comments metadata column (2021 only)."""

    def test_2021_has_get_comment_method(self, ref_2021):
        """2021 instance has get_comment method."""
        assert hasattr(ref_2021, "get_comment"), (
            "ReferenceAbundances should have get_comment method"
        )

    @pytest.mark.parametrize(
        "symbol,expected_comment",
        [
            ("H", "definition"),
            ("He", "helioseismology"),
            ("As", "meteorites"),
            ("Ne", "solar wind"),
            ("Xe", "nuclear physics"),
            ("Li", "meteorites"),
        ],
    )
    def test_comment_values_match_asplund_2021(self, ref_2021, symbol, expected_comment):
        """Comment values match Asplund 2021 Table 2."""
        comment = ref_2021.get_comment(symbol)
        assert comment == expected_comment, (
            f"{symbol} comment: expected '{expected_comment}', got '{comment}'"
        )

    @pytest.mark.parametrize("symbol", ["C", "O", "Fe", "Si", "N"])
    def test_spectroscopic_elements_have_no_comment(self, ref_2021, symbol):
        """Elements with spectroscopic measurements have empty/None comment."""
        comment = ref_2021.get_comment(symbol)
        assert comment is None or comment == "" or pd.isna(comment), (
            f"{symbol} should have no comment (spectroscopic), got '{comment}'"
        )

    def test_2009_get_comment_returns_none(self, ref_2009):
        """2009 data get_comment returns None (no comments in 2009)."""
        comment = ref_2009.get_comment("H")
        assert comment is None, (
            f"2009 get_comment should return None, got '{comment}'"
        )


# =============================================================================
# Unit Tests: Get Element
# =============================================================================


class TestGetElement:
    """Unit tests for element lookup by symbol and Z."""

    def test_get_by_symbol_returns_series(self, ref_any_year):
        """get_element('Fe') returns pd.Series."""
        fe = ref_any_year.get_element("Fe")
        assert isinstance(fe, pd.Series), (
            f"Expected pd.Series, got {type(fe).__name__}"
        )

    def test_get_by_symbol_series_has_correct_shape(self, ref_any_year):
        """get_element returns Series with shape (2,) for [Ab, Uncert]."""
        fe = ref_any_year.get_element("Fe")
        assert fe.shape == (2,), (
            f"Expected shape (2,) for [Ab, Uncert], got {fe.shape}"
        )

    def test_get_by_symbol_series_has_correct_index(self, ref_any_year):
        """get_element returns Series with index ['Ab', 'Uncert']."""
        fe = ref_any_year.get_element("Fe")
        assert list(fe.index) == ["Ab", "Uncert"], (
            f"Expected index ['Ab', 'Uncert'], got {list(fe.index)}"
        )

    def test_get_by_symbol_series_dtype_is_float64(self, ref_any_year):
        """get_element returns Series with float64 dtype."""
        fe = ref_any_year.get_element("Fe")
        assert fe.dtype == np.float64, (
            f"Expected dtype float64, got {fe.dtype}"
        )

    def test_get_by_z_returns_series(self, ref_any_year):
        """get_element(26) returns pd.Series."""
        fe = ref_any_year.get_element(26)
        assert isinstance(fe, pd.Series), (
            f"Expected pd.Series, got {type(fe).__name__}"
        )

    def test_symbol_and_z_return_equal_values(self, ref_any_year):
        """get_element('Fe') equals get_element(26) in values."""
        by_symbol = ref_any_year.get_element("Fe")
        by_z = ref_any_year.get_element(26)
        pd.testing.assert_series_equal(
            by_symbol, by_z, check_names=False, obj="Fe by symbol vs by Z"
        )

    def test_default_kind_is_photosphere(self, ref_any_year):
        """Default kind is 'Photosphere'."""
        default = ref_any_year.get_element("Fe")
        explicit = ref_any_year.get_element("Fe", kind="Photosphere")
        pd.testing.assert_series_equal(
            default, explicit, check_names=False, obj="Default kind vs explicit Photosphere"
        )

    def test_invalid_key_type_raises_valueerror(self, ref_any_year):
        """Float key raises ValueError."""
        with pytest.raises(ValueError, match=r"Unrecognized key type"):
            ref_any_year.get_element(3.14)

    def test_unknown_element_raises_keyerror(self, ref_any_year):
        """Unknown element raises KeyError."""
        with pytest.raises(KeyError):
            ref_any_year.get_element("Xx")

    def test_unknown_z_raises_keyerror(self, ref_any_year):
        """Unknown atomic number raises KeyError."""
        with pytest.raises(KeyError):
            ref_any_year.get_element(999)


# =============================================================================
# Unit Tests: Missing Photosphere Data
# =============================================================================


class TestMissingPhotosphereData:
    """Unit tests for elements without photospheric measurements."""

    @pytest.mark.parametrize("symbol", ELEMENTS_WITHOUT_PHOTOSPHERE)
    def test_missing_photosphere_ab_is_nan(self, ref_any_year, symbol):
        """Elements without photospheric data have NaN for Ab."""
        element = ref_any_year.get_element(symbol, kind="Photosphere")
        assert np.isnan(element.Ab), (
            f"{symbol} photosphere Ab should be NaN, got {element.Ab}"
        )

    @pytest.mark.parametrize("symbol", ELEMENTS_WITHOUT_PHOTOSPHERE[:5])
    def test_missing_photosphere_has_ci_chondrites(self, ref_any_year, symbol):
        """Elements without photosphere DO have CI chondrite values."""
        element = ref_any_year.get_element(symbol, kind="CI_chondrites")
        assert not np.isnan(element.Ab), (
            f"{symbol} CI chondrites Ab should NOT be NaN, got {element.Ab}"
        )

    def test_h_photosphere_ab_is_12(self, ref_any_year):
        """H photosphere Ab is 12.00 (by definition)."""
        h = ref_any_year.get_element("H", kind="Photosphere")
        assert np.isclose(h.Ab, 12.00, atol=0.001), (
            f"H photosphere Ab should be 12.00, got {h.Ab}"
        )

    def test_h_2009_uncertainty_is_nan(self, ref_2009):
        """H uncertainty is NaN in 2009 (undefined)."""
        h = ref_2009.get_element("H", kind="Photosphere")
        assert np.isnan(h.Uncert), (
            f"H (2009) uncertainty should be NaN, got {h.Uncert}"
        )

    def test_h_2021_uncertainty_is_zero(self, ref_2021):
        """H uncertainty is 0.00 in 2021 (by definition)."""
        h = ref_2021.get_element("H", kind="Photosphere")
        assert np.isclose(h.Uncert, 0.00, atol=0.001), (
            f"H (2021) uncertainty should be 0.00, got {h.Uncert}"
        )


# =============================================================================
# Integration Tests: Value Validation
# =============================================================================


class TestValueValidation:
    """Integration tests verifying values match published Asplund tables."""

    @pytest.mark.parametrize(
        "year,symbol",
        [
            (2009, "Fe"),
            (2009, "C"),
            (2009, "O"),
            (2009, "Si"),
            (2021, "Fe"),
            (2021, "C"),
            (2021, "O"),
            (2021, "He"),
            (2021, "Si"),
        ],
    )
    def test_photosphere_values_match_published(self, year, symbol):
        """Photospheric abundances match Asplund Table values."""
        ref = ReferenceAbundances(year=year)
        expected = ASPLUND_DATA[year][symbol]

        element = ref.get_element(symbol, kind="Photosphere")

        # Type and shape
        assert isinstance(element, pd.Series), (
            f"Expected pd.Series, got {type(element).__name__}"
        )
        assert element.shape == (2,), f"Expected shape (2,), got {element.shape}"

        # Content from published table
        if expected.photosphere_ab is not None:
            assert np.isclose(element.Ab, expected.photosphere_ab, atol=0.005), (
                f"Asplund {year} {symbol} photosphere Ab: "
                f"expected {expected.photosphere_ab}, got {element.Ab}"
            )
        if expected.photosphere_uncert is not None:
            assert np.isclose(element.Uncert, expected.photosphere_uncert, atol=0.005), (
                f"Asplund {year} {symbol} photosphere Uncert: "
                f"expected {expected.photosphere_uncert}, got {element.Uncert}"
            )

    @pytest.mark.parametrize(
        "year,symbol",
        [
            (2009, "Fe"),
            (2009, "H"),
            (2009, "Si"),
            (2021, "Fe"),
            (2021, "H"),
            (2021, "Si"),
        ],
    )
    def test_ci_chondrites_values_match_published(self, year, symbol):
        """CI chondrite abundances match Asplund Table values."""
        ref = ReferenceAbundances(year=year)
        expected = ASPLUND_DATA[year][symbol]

        element = ref.get_element(symbol, kind="CI_chondrites")

        assert np.isclose(element.Ab, expected.ci_chondrites_ab, atol=0.005), (
            f"Asplund {year} {symbol} CI chondrites Ab: "
            f"expected {expected.ci_chondrites_ab}, got {element.Ab}"
        )
        if expected.ci_chondrites_uncert is not None:
            assert np.isclose(
                element.Uncert, expected.ci_chondrites_uncert, atol=0.005
            ), (
                f"Asplund {year} {symbol} CI chondrites Uncert: "
                f"expected {expected.ci_chondrites_uncert}, got {element.Uncert}"
            )


# =============================================================================
# Integration Tests: Abundance Ratio
# =============================================================================


class TestAbundanceRatio:
    """Integration tests for abundance ratio calculations."""

    def test_returns_abundance_namedtuple(self, ref_any_year):
        """abundance_ratio returns Abundance namedtuple."""
        result = ref_any_year.abundance_ratio("Fe", "O")
        assert isinstance(result, Abundance), (
            f"Expected Abundance namedtuple, got {type(result).__name__}"
        )

    def test_abundance_has_measurement_and_uncertainty(self, ref_any_year):
        """Abundance namedtuple has measurement and uncertainty attributes."""
        result = ref_any_year.abundance_ratio("Fe", "O")
        assert hasattr(result, "measurement"), "Missing 'measurement' attribute"
        assert hasattr(result, "uncertainty"), "Missing 'uncertainty' attribute"

    def test_measurement_is_float(self, ref_any_year):
        """measurement attribute is float."""
        result = ref_any_year.abundance_ratio("Fe", "O")
        assert isinstance(result.measurement, (float, np.floating)), (
            f"measurement should be float, got {type(result.measurement).__name__}"
        )

    def test_uncertainty_is_float(self, ref_any_year):
        """uncertainty attribute is float."""
        result = ref_any_year.abundance_ratio("Fe", "O")
        assert isinstance(result.uncertainty, (float, np.floating)), (
            f"uncertainty should be float, got {type(result.uncertainty).__name__}"
        )

    def test_ratio_can_be_destructured(self, ref_any_year):
        """Abundance namedtuple can be destructured."""
        measurement, uncertainty = ref_any_year.abundance_ratio("Fe", "O")
        assert isinstance(measurement, (float, np.floating))
        assert isinstance(uncertainty, (float, np.floating))

    @pytest.mark.parametrize(
        "year,numerator,denominator",
        [
            (2009, "Fe", "O"),
            (2009, "C", "O"),
            (2021, "Fe", "O"),
            (2021, "C", "O"),
        ],
    )
    def test_ratio_calculation_matches_expected(self, year, numerator, denominator):
        """Abundance ratios match calculated values from published data."""
        ref = ReferenceAbundances(year=year)
        result = ref.abundance_ratio(numerator, denominator)

        expected_ratio, sigma_num, sigma_den = EXPECTED_RATIOS[year][
            (numerator, denominator)
        ]
        expected_uncert = (
            expected_ratio * np.log(10) * np.sqrt(sigma_num**2 + sigma_den**2)
        )

        assert np.isclose(result.measurement, expected_ratio, rtol=0.02), (
            f"Asplund {year} {numerator}/{denominator} ratio: "
            f"expected {expected_ratio:.5f}, got {result.measurement:.5f}"
        )
        assert np.isclose(result.uncertainty, expected_uncert, rtol=0.02), (
            f"Asplund {year} {numerator}/{denominator} uncertainty: "
            f"expected {expected_uncert:.5f}, got {result.uncertainty:.5f}"
        )

    @pytest.mark.parametrize("year", [2009, 2021])
    def test_fe_h_ratio_uses_hydrogen_denominator_path(self, year):
        """Fe/H ratio uses special hydrogen denominator logic."""
        ref = ReferenceAbundances(year=year)
        result = ref.abundance_ratio("Fe", "H")

        expected_ratio, sigma_fe, _ = EXPECTED_RATIOS[year][("Fe", "H")]
        # For H denominator, uncertainty comes only from numerator
        expected_uncert = expected_ratio * np.log(10) * sigma_fe

        assert np.isclose(result.measurement, expected_ratio, rtol=0.02), (
            f"Asplund {year} Fe/H ratio: "
            f"expected {expected_ratio:.3e}, got {result.measurement:.3e}"
        )
        assert np.isclose(result.uncertainty, expected_uncert, rtol=0.02), (
            f"Asplund {year} Fe/H uncertainty: "
            f"expected {expected_uncert:.3e}, got {result.uncertainty:.3e}"
        )


# =============================================================================
# Integration Tests: Backward Compatibility
# =============================================================================


class TestBackwardCompatibility:
    """Integration tests ensuring backward compatibility with existing code."""

    def test_2009_iron_matches_original_tests(self):
        """year=2009 Fe matches original test values (7.50±0.04)."""
        ref = ReferenceAbundances(year=2009)
        fe = ref.get_element("Fe")
        assert np.isclose(fe.Ab, 7.50, atol=0.01), (
            f"2009 Fe photosphere should be 7.50, got {fe.Ab}"
        )
        assert np.isclose(fe.Uncert, 0.04, atol=0.01), (
            f"2009 Fe uncertainty should be 0.04, got {fe.Uncert}"
        )

    def test_2009_c_o_ratio_matches_original_calculation(self):
        """year=2009 C/O ratio matches original expected value."""
        ref = ReferenceAbundances(year=2009)
        result = ref.abundance_ratio("C", "O")
        # Original: 10^(8.43 - 8.69) = 0.5495
        expected = 10.0 ** (8.43 - 8.69)
        assert np.isclose(result.measurement, expected, rtol=0.01), (
            f"2009 C/O ratio: expected {expected:.4f}, got {result.measurement:.4f}"
        )

    def test_abundance_ratio_method_exists(self, ref_any_year):
        """abundance_ratio method exists and is callable."""
        assert hasattr(ref_any_year, "abundance_ratio"), (
            "Missing abundance_ratio method"
        )
        assert callable(ref_any_year.abundance_ratio), (
            "abundance_ratio should be callable"
        )

    def test_data_property_returns_dataframe(self, ref_any_year):
        """data property returns DataFrame as in original API."""
        assert isinstance(ref_any_year.data, pd.DataFrame), (
            f"data property should return DataFrame, got {type(ref_any_year.data)}"
        )

    def test_get_element_method_exists(self, ref_any_year):
        """get_element method exists and is callable."""
        assert hasattr(ref_any_year, "get_element"), "Missing get_element method"
        assert callable(ref_any_year.get_element), "get_element should be callable"


# =============================================================================
# Module-Level Tests
# =============================================================================


def test_module_exports_referenceabundances():
    """Module __all__ includes ReferenceAbundances."""
    from solarwindpy.core import abundances

    assert hasattr(abundances, "__all__"), "Module missing __all__"
    assert "ReferenceAbundances" in abundances.__all__, (
        "ReferenceAbundances not in __all__"
    )


def test_module_exports_abundance_namedtuple():
    """Module __all__ includes Abundance namedtuple."""
    from solarwindpy.core import abundances

    assert "Abundance" in abundances.__all__, "Abundance not in __all__"


def test_abundance_namedtuple_structure():
    """Abundance namedtuple has correct fields."""
    assert hasattr(Abundance, "_fields"), "Abundance should be a namedtuple"
    assert Abundance._fields == ("measurement", "uncertainty"), (
        f"Expected fields ('measurement', 'uncertainty'), got {Abundance._fields}"
    )


def test_can_import_from_core():
    """Can import ReferenceAbundances from solarwindpy.core."""
    from solarwindpy.core import ReferenceAbundances as RA

    assert RA is ReferenceAbundances, "Import should resolve to same class"
