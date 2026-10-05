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
from importlib import resources
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
    "Hg",
    "Bi",
    "U",
]

# CI chondrite (Ab, Uncert) for the first five ELEMENTS_WITHOUT_PHOTOSPHERE,
# identical in Asplund+2009 Table 1 (doi:10.1146/annurev.astro.46.060407.145222)
# and Asplund+2021 Table 2 (doi:10.1051/0004-6361/202140445).
PUBLISHED_CI_WITHOUT_PHOTOSPHERE = {
    "As": (2.30, 0.04),
    "Se": (3.34, 0.03),
    "Br": (2.54, 0.06),
    "Cd": (1.71, 0.03),
    "Sb": (1.01, 0.06),
}


class SeriesNameMismatch(AssertionError):
    """``get_element`` names a Series differently for symbol and Z lookups."""


class PublishedTableMismatch(AssertionError):
    """A shipped abundance disagrees with the published Asplund table."""


def exact(x):
    """``pytest.approx`` for a value shipped verbatim or computed from verbatim inputs.

    Tolerance rel=1e-12, abs=0: the CSVs carry the tables' decimals unchanged,
    so only float parsing or rounding may differ.
    """
    return pytest.approx(x, rel=1e-12, abs=0)


# Fe (CI Ab, CI Uncert, Photosphere Ab, Photosphere Uncert) by year.
PUBLISHED_FE = {
    2009: (
        7.45,
        0.01,
        7.50,
        0.04,
    ),  # Asplund+2009 Table 1, doi:10.1146/annurev.astro.46.060407.145222
    2021: (
        7.46,
        0.02,
        7.46,
        0.04,
    ),  # Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445
}

# O photosphere (Ab, Uncert) by year.
PUBLISHED_O_PHOTOSPHERE = {
    2009: (
        8.69,
        0.05,
    ),  # Asplund+2009 Table 1, doi:10.1146/annurev.astro.46.060407.145222
    2021: (8.69, 0.04),  # Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445
}

# Fe/O photosphere (ratio, uncertainty) by hand, to 5 significant digits:
# 10**(Fe-O) and ratio x ln10 x hypot(sigma_Fe, sigma_O).
HAND_FE_O = {
    2009: (0.064565, 0.0095194),  # 10**-1.19; hypot(.04, .05)
    2021: (0.058884, 0.0076699),  # 10**-1.23; hypot(.04, .04)
}


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
        assert isinstance(
            ref.data, pd.DataFrame
        ), f"Expected pd.DataFrame, got {type(ref.data).__name__}"
        assert ref.year == 2021, f"Expected default year=2021, got {ref.year}"

    def test_explicit_2021_loads(self):
        """year=2021 loads 2021 data explicitly."""
        ref = ReferenceAbundances(year=2021)
        assert isinstance(
            ref.data, pd.DataFrame
        ), f"Expected pd.DataFrame, got {type(ref.data).__name__}"
        assert ref.year == 2021, f"Expected year=2021, got {ref.year}"

    def test_explicit_2009_loads(self):
        """year=2009 loads 2009 data for backward compatibility."""
        ref = ReferenceAbundances(year=2009)
        assert isinstance(
            ref.data, pd.DataFrame
        ), f"Expected pd.DataFrame, got {type(ref.data).__name__}"
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

    def test_data_fe_row_matches_published_table(self, ref_with_year):
        """``data`` holds the published Fe row (PUBLISHED_FE), addressed by (Z, Symbol).

        Tolerance is ``exact``, not the significant-digit rule, which would
        accept 7.50 for 7.46.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ref, year = ref_with_year
        ci_ab, ci_uncert, ph_ab, ph_uncert = PUBLISHED_FE[year]
        row = ref.data.loc[(26, "Fe")]
        assert row[("CI_chondrites", "Ab")] == exact(ci_ab)
        assert row[("CI_chondrites", "Uncert")] == exact(ci_uncert)
        assert row[("Photosphere", "Ab")] == exact(ph_ab)
        assert row[("Photosphere", "Uncert")] == exact(ph_uncert)

    def test_data_has_83_elements(self, ref_any_year):
        """Both Asplund 2009 and 2021 have 83 elements."""
        assert (
            ref_any_year.data.shape[0] == 83
        ), f"Expected 83 elements, got {ref_any_year.data.shape[0]}"

    def test_index_is_multiindex_with_z_symbol(self, ref_any_year):
        """Index is MultiIndex with levels ['Z', 'Symbol']."""
        idx = ref_any_year.data.index
        assert isinstance(
            idx, pd.MultiIndex
        ), f"Expected MultiIndex, got {type(idx).__name__}"
        assert list(idx.names) == [
            "Z",
            "Symbol",
        ], f"Expected index names ['Z', 'Symbol'], got {list(idx.names)}"

    def test_columns_have_photosphere_and_ci_chondrites(self, ref_any_year):
        """Top-level columns include Photosphere and CI_chondrites."""
        top_level = ref_any_year.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, "Missing 'Photosphere' column group"
        assert "CI_chondrites" in top_level, "Missing 'CI_chondrites' column group"

    def test_columns_are_multiindex(self, ref_any_year):
        """Columns are MultiIndex with at least 2 levels."""
        assert isinstance(
            ref_any_year.data.columns, pd.MultiIndex
        ), f"Expected MultiIndex columns, got {type(ref_any_year.data.columns).__name__}"
        assert (
            ref_any_year.data.columns.nlevels >= 2
        ), f"Expected at least 2 column levels, got {ref_any_year.data.columns.nlevels}"

    def test_abundance_values_are_float64(self, ref_any_year):
        """``data`` columns are exactly (CI_chondrites, Photosphere) x (Ab, Uncert), all float64.

        The column set is the one the ``data`` docstring promises. Naming it
        exactly means the dtype check cannot pass over an empty selection, as
        a filter on ``col[1] in ("Ab", "Uncert")`` did when no column matched.

        ON FAILURE: the code is wrong.
        """
        data = ref_any_year.data
        expected = [
            ("CI_chondrites", "Ab"),
            ("CI_chondrites", "Uncert"),
            ("Photosphere", "Ab"),
            ("Photosphere", "Uncert"),
        ]
        assert sorted(data.columns.tolist()) == expected
        assert data.dtypes.to_dict() == {col: np.dtype(np.float64) for col in expected}

    @pytest.mark.parametrize("z", [1, 26, 92])
    def test_key_z_values_present(self, ref_any_year, z):
        """Key atomic numbers (H=1, Fe=26, U=92) are present in index."""
        z_values = ref_any_year.data.index.get_level_values("Z").tolist()
        assert z in z_values, f"Z={z} missing from index"

    @pytest.mark.parametrize("symbol", ["H", "He", "C", "O", "Fe", "Si"])
    def test_key_symbols_present(self, ref_any_year, symbol):
        """Key element symbols are present in index."""
        symbols = ref_any_year.data.index.get_level_values("Symbol").tolist()
        assert symbol in symbols, f"Symbol '{symbol}' missing from index"

    def test_z_values_are_integers(self, ref_any_year):
        """Z values in index are integers."""
        z_values = ref_any_year.data.index.get_level_values("Z")
        # Check that Z values can be used as integers
        assert all(
            isinstance(z, (int, np.integer)) for z in z_values
        ), "Z values should be integers"

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
        assert not np.isclose(
            fe_2009.Ab, fe_2021.Ab, atol=0.01
        ), f"Fe should differ between years: 2009={fe_2009.Ab}, 2021={fe_2021.Ab}"
        assert np.isclose(
            fe_2009.Ab, 7.50, atol=0.01
        ), f"2009 Fe should be 7.50, got {fe_2009.Ab}"
        assert np.isclose(
            fe_2021.Ab, 7.46, atol=0.01
        ), f"2021 Fe should be 7.46, got {fe_2021.Ab}"


# =============================================================================
# Unit Tests: Column Naming
# =============================================================================


class TestColumnNaming:
    """Unit tests for CI_chondrites column with Meteorites alias."""

    def test_ci_chondrites_in_columns(self, ref_any_year):
        """'CI_chondrites' is a top-level column."""
        top_level = ref_any_year.data.columns.get_level_values(0).unique().tolist()
        assert (
            "CI_chondrites" in top_level
        ), f"'CI_chondrites' not in columns: {top_level}"

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
    def test_comment_values_match_asplund_2021(
        self, ref_2021, symbol, expected_comment
    ):
        """Comment values match Asplund 2021 Table 2."""
        comment = ref_2021.get_comment(symbol)
        assert (
            comment == expected_comment
        ), f"{symbol} comment: expected '{expected_comment}', got '{comment}'"

    # Comments column blank for these in Asplund+2021 Table 2,
    # doi:10.1051/0004-6361/202140445
    @pytest.mark.parametrize("symbol", ["C", "O", "Fe", "Si", "N"])
    def test_spectroscopic_elements_have_no_comment(self, ref_2021, symbol):
        """``get_comment`` returns None where Table 2 has no comment.

        The ``get_comment`` docstring promises None for a spectroscopic
        measurement; an empty string or NaN is not None.

        ON FAILURE: the code is wrong.
        """
        comment = ref_2021.get_comment(symbol)
        assert comment is None, f"{symbol}: expected None, got {comment!r}"

    def test_2009_get_comment_returns_none(self, ref_2009):
        """2009 data get_comment returns None (no comments in 2009)."""
        comment = ref_2009.get_comment("H")
        assert comment is None, f"2009 get_comment should return None, got '{comment}'"


# =============================================================================
# Unit Tests: Get Element
# =============================================================================


class TestGetElement:
    """Unit tests for element lookup by symbol and Z."""

    @pytest.mark.parametrize("key", ["Fe", 26], ids=["symbol", "z"])
    def test_get_element_returns_published_fe_photosphere(self, ref_with_year, key):
        """``get_element`` by symbol or by Z is the published Fe photosphere Series.

        Expected values: PUBLISHED_FE.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ref, year = ref_with_year
        _, _, ab, uncert = PUBLISHED_FE[year]
        fe = ref.get_element(key)
        assert isinstance(fe, pd.Series)
        assert fe.index.tolist() == ["Ab", "Uncert"]
        assert fe["Ab"] == exact(ab)
        assert fe["Uncert"] == exact(uncert)

    @pytest.mark.xfail(
        strict=True,
        raises=SeriesNameMismatch,
        reason=(
            "ReferenceAbundances.get_element (solarwindpy/core/abundances.py) "
            "names its Series by the level it did not search: get_element('Fe') "
            "is named 26, get_element(26) is named 'Fe', although its docstring "
            "calls the Z lookup 'Same result'; expected message: 'get_element "
            "Series names differ'; remove this marker when get_element returns "
            "the same Series name for a symbol and its atomic number"
        ),
    )
    def test_symbol_and_z_lookups_return_same_series_name(self, ref_2021):
        """``get_element('Fe')`` and ``get_element(26)`` carry the same name.

        The ``get_element`` docstring shows ``Name: 26`` for the symbol lookup
        and calls the atomic-number lookup the "Same result".

        ON FAILURE: (unexpected pass) a fix making the names agree has
        landed; drop the xfail marker.
        """
        by_symbol = ref_2021.get_element("Fe")
        by_z = ref_2021.get_element(26)
        if by_symbol.name != by_z.name:
            raise SeriesNameMismatch(
                f"get_element Series names differ: {by_symbol.name!r} != {by_z.name!r}"
            )

    def test_get_by_symbol_series_has_correct_shape(self, ref_any_year):
        """get_element returns Series with shape (2,) for [Ab, Uncert]."""
        fe = ref_any_year.get_element("Fe")
        assert fe.shape == (2,), f"Expected shape (2,) for [Ab, Uncert], got {fe.shape}"

    def test_get_by_symbol_series_has_correct_index(self, ref_any_year):
        """get_element returns Series with index ['Ab', 'Uncert']."""
        fe = ref_any_year.get_element("Fe")
        assert list(fe.index) == [
            "Ab",
            "Uncert",
        ], f"Expected index ['Ab', 'Uncert'], got {list(fe.index)}"

    def test_get_by_symbol_series_dtype_is_float64(self, ref_any_year):
        """get_element returns Series with float64 dtype."""
        fe = ref_any_year.get_element("Fe")
        assert fe.dtype == np.float64, f"Expected dtype float64, got {fe.dtype}"

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
            default,
            explicit,
            check_names=False,
            obj="Default kind vs explicit Photosphere",
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
        assert np.isnan(
            element.Ab
        ), f"{symbol} photosphere Ab should be NaN, got {element.Ab}"

    @pytest.mark.parametrize("symbol", ELEMENTS_WITHOUT_PHOTOSPHERE[:5])
    def test_missing_photosphere_has_ci_chondrites(self, ref_any_year, symbol):
        """Elements without a photospheric value carry the published CI value.

        Expected values: PUBLISHED_CI_WITHOUT_PHOTOSPHERE (Asplund 2009
        Table 1 and 2021 Table 2, same in both).

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ab, uncert = PUBLISHED_CI_WITHOUT_PHOTOSPHERE[symbol]
        element = ref_any_year.get_element(symbol, kind="CI_chondrites")
        assert element.Ab == exact(ab)
        assert element.Uncert == exact(uncert)

    def test_h_photosphere_ab_is_12(self, ref_any_year):
        """H photosphere Ab is 12.00 (by definition)."""
        h = ref_any_year.get_element("H", kind="Photosphere")
        assert np.isclose(
            h.Ab, 12.00, atol=0.001
        ), f"H photosphere Ab should be 12.00, got {h.Ab}"

    def test_h_2009_uncertainty_is_nan(self, ref_2009):
        """H uncertainty is NaN in 2009 (undefined)."""
        h = ref_2009.get_element("H", kind="Photosphere")
        assert np.isnan(h.Uncert), f"H (2009) uncertainty should be NaN, got {h.Uncert}"

    def test_h_2021_uncertainty_is_zero(self, ref_2021):
        """H uncertainty is 0.00 in 2021 (by definition)."""
        h = ref_2021.get_element("H", kind="Photosphere")
        assert np.isclose(
            h.Uncert, 0.00, atol=0.001
        ), f"H (2021) uncertainty should be 0.00, got {h.Uncert}"


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
        assert isinstance(
            element, pd.Series
        ), f"Expected pd.Series, got {type(element).__name__}"
        assert element.shape == (2,), f"Expected shape (2,), got {element.shape}"

        # Content from published table
        if expected.photosphere_ab is not None:
            assert np.isclose(element.Ab, expected.photosphere_ab, atol=0.005), (
                f"Asplund {year} {symbol} photosphere Ab: "
                f"expected {expected.photosphere_ab}, got {element.Ab}"
            )
        if expected.photosphere_uncert is not None:
            assert np.isclose(
                element.Uncert, expected.photosphere_uncert, atol=0.005
            ), (
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

    @pytest.mark.xfail(
        strict=True,
        raises=PublishedTableMismatch,
        reason=(
            "solarwindpy/core/data/asplund2009.csv gives Ar CI_chondrites Ab "
            "-0.05; Asplund+2009 Table 1 prints -0.50; expected message: "
            "'Ar CI_chondrites Ab'; remove this marker when the 2009 CSV "
            "carries -0.50 for Ar"
        ),
    )
    def test_2009_argon_ci_chondrites_matches_table_1(self, ref_2009):
        """2009 Ar CI chondrite abundance is the Table 1 value, -0.50.

        Source: Asplund+2009 Table 1, doi:10.1146/annurev.astro.46.060407.145222.

        ON FAILURE: (unexpected pass) the 2009 CSV now carries -0.50 for Ar;
        drop the xfail marker.
        """
        ab = ref_2009.get_element("Ar", kind="CI_chondrites").Ab
        if ab != exact(-0.50):
            raise PublishedTableMismatch(
                f"Ar CI_chondrites Ab: expected -0.50, got {ab}"
            )

    @pytest.mark.xfail(
        strict=True,
        raises=PublishedTableMismatch,
        reason=(
            "solarwindpy/core/data/asplund2021.csv leaves CI_chondrites Ab "
            "blank (NaN) for Ne, Ar, Kr, Xe while keeping their 0.18 "
            "uncertainty; Asplund+2021 Table 2 prints -1.12, -0.50, -2.27, "
            "-1.95; expected message: 'CI_chondrites Ab'; remove this marker "
            "when the 2021 CSV carries those values"
        ),
    )
    @pytest.mark.parametrize(
        "symbol,ab",
        [
            # Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445
            ("Ne", -1.12),
            ("Ar", -0.50),
            ("Kr", -2.27),
            ("Xe", -1.95),
        ],
    )
    def test_2021_noble_gas_ci_chondrites_match_table_2(self, ref_2021, symbol, ab):
        """2021 noble-gas CI chondrite abundances are the Table 2 values.

        Source: Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445.

        ON FAILURE: (unexpected pass) the 2021 CSV now carries the noble-gas
        CI values; drop the xfail marker.
        """
        got = ref_2021.get_element(symbol, kind="CI_chondrites").Ab
        if got != exact(ab):
            raise PublishedTableMismatch(
                f"{symbol} CI_chondrites Ab: expected {ab}, got {got}"
            )


# =============================================================================
# Integration Tests: Abundance Ratio
# =============================================================================


class TestAbundanceRatio:
    """Integration tests for abundance ratio calculations."""

    def test_fe_o_ratio_is_abundance_of_published_values(self, ref_with_year):
        """``abundance_ratio('Fe', 'O')`` is Abundance(10**(Fe-O), ratio ln10 sqrt(sFe^2+sO^2)).

        Unpacking yields (measurement, uncertainty) in that order. Expected
        values follow the propagation stated in the ``abundance_ratio``
        docstring Notes, from the published dex values (PUBLISHED_FE,
        PUBLISHED_O_PHOTOSPHERE), plus the independent hand-computed HAND_FE_O
        so a formula wrong in both places still fails.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table values or the stated error propagation.
        """
        ref, year = ref_with_year
        _, _, fe, sigma_fe = PUBLISHED_FE[year]
        o, sigma_o = PUBLISHED_O_PHOTOSPHERE[year]
        hand_ratio, hand_uncert = HAND_FE_O[year]

        result = ref.abundance_ratio("Fe", "O")
        assert isinstance(result, Abundance)
        measurement, uncertainty = result
        assert (measurement, uncertainty) == (result.measurement, result.uncertainty)

        ratio = 10.0 ** (fe - o)
        uncert = ratio * np.log(10) * np.hypot(sigma_fe, sigma_o)
        assert measurement == exact(ratio)
        assert uncertainty == exact(uncert)
        # Hand values written to 5 significant digits.
        assert measurement == pytest.approx(hand_ratio, rel=1e-4, abs=0)
        assert uncertainty == pytest.approx(hand_uncert, rel=1e-4, abs=0)

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
        assert np.isclose(
            fe.Ab, 7.50, atol=0.01
        ), f"2009 Fe photosphere should be 7.50, got {fe.Ab}"
        assert np.isclose(
            fe.Uncert, 0.04, atol=0.01
        ), f"2009 Fe uncertainty should be 0.04, got {fe.Uncert}"

    def test_2009_c_o_ratio_matches_original_calculation(self):
        """year=2009 C/O ratio matches original expected value."""
        ref = ReferenceAbundances(year=2009)
        result = ref.abundance_ratio("C", "O")
        # Original: 10^(8.43 - 8.69) = 0.5495
        expected = 10.0 ** (8.43 - 8.69)
        assert np.isclose(
            result.measurement, expected, rtol=0.01
        ), f"2009 C/O ratio: expected {expected:.4f}, got {result.measurement:.4f}"


# =============================================================================
# Module-Level Tests
# =============================================================================


def test_module_exports_referenceabundances():
    """Module __all__ includes ReferenceAbundances."""
    from solarwindpy.core import abundances

    assert hasattr(abundances, "__all__"), "Module missing __all__"
    assert (
        "ReferenceAbundances" in abundances.__all__
    ), "ReferenceAbundances not in __all__"


def test_module_exports_abundance_namedtuple():
    """Module __all__ includes Abundance namedtuple."""
    from solarwindpy.core import abundances

    assert "Abundance" in abundances.__all__, "Abundance not in __all__"


def test_abundance_namedtuple_structure():
    """Abundance namedtuple has correct fields."""
    assert Abundance._fields == (
        "measurement",
        "uncertainty",
    ), f"Expected fields ('measurement', 'uncertainty'), got {Abundance._fields}"


def test_can_import_from_core():
    """Can import ReferenceAbundances from solarwindpy.core."""
    from solarwindpy.core.abundances import ReferenceAbundances as RA

    assert RA is ReferenceAbundances, "Import should resolve to same class"


# =============================================================================
# Consistency: shipped CSVs vs. the years ReferenceAbundances accepts
# =============================================================================


def shipped_asplund_years(data_dir):
    """Years present as ``asplund<year>.csv`` in ``data_dir``.

    Parameters
    ----------
    data_dir : Path
        Directory to scan for ``asplund*.csv`` files.

    Returns
    -------
    set of int
    """
    years = set()
    for path in data_dir.glob("asplund*.csv"):
        digits = "".join(c for c in path.stem if c.isdigit())
        if digits:
            years.add(int(digits))
    return years


def test_shipped_asplund_csvs_are_exactly_the_accepted_years():
    """``ReferenceAbundances(year)`` builds for exactly the shipped CSV years.

    Every year from 1980 to 2050 is tried: an unsupported year raises
    ``ValueError``; a supported one must load its CSV (an accepted year with no
    CSV raises ``FileNotFoundError`` and errors the test). The set that builds
    must equal the ``asplund<year>.csv`` files shipped. This is an internal
    consistency fact (not a claim about whether a successor Asplund
    compilation exists -- that judgment stays with the author).

    ON FAILURE: the code is wrong; the accepted years and the shipped CSVs
    disagree.
    """
    data_dir = resources.files("solarwindpy.core") / "data"
    with resources.as_file(data_dir) as data_path:
        shipped = shipped_asplund_years(data_path)
    assert shipped  # the fixture: the package ships at least one compilation

    accepted = set()
    for year in range(1980, 2051):
        try:
            ref = ReferenceAbundances(year=year)
        except ValueError:
            continue
        assert ref.year == year
        accepted.add(year)

    assert accepted == shipped
