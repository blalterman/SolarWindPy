"""Tests for ReferenceAbundances class.

Tests verify:
1. Data structure matches expected CSV format
2. Values match the published Asplund et al. (2021) Table 2
3. Uncertainty propagation formula is correct
4. Edge cases (NaN, H denominator, missing photosphere) handled properly
5. Backward compatibility (Meteorites alias)
6. Comments column

References
----------
Asplund, M., Amarsi, A. M., & Grevesse, N. (2021).
The chemical make-up of the Sun: A 2020 vision.
A&A, 653, A141. https://doi.org/10.1051/0004-6361/202140445

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
    """Expected values for a single element from the published table.

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
        Source comment: 'definition', 'helioseismology', etc.
    """

    symbol: str
    z: int
    photosphere_ab: Optional[float]
    photosphere_uncert: Optional[float]
    ci_chondrites_ab: float
    ci_chondrites_uncert: float
    comment: Optional[str] = None


# Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445
ASPLUND_DATA: Dict[str, ElementData] = {
    "H": ElementData("H", 1, 12.00, 0.00, 8.22, 0.04, "definition"),
    "He": ElementData("He", 2, 10.914, 0.013, 1.29, 0.18, "helioseismology"),
    "Li": ElementData("Li", 3, 0.96, 0.06, 3.25, 0.04, "meteorites"),
    "C": ElementData("C", 6, 8.46, 0.04, 7.39, 0.04, None),
    "N": ElementData("N", 7, 7.83, 0.07, 6.26, 0.06, None),
    "O": ElementData("O", 8, 8.69, 0.04, 8.39, 0.04, None),
    "Ne": ElementData("Ne", 10, 8.06, 0.05, -1.12, 0.18, "solar wind"),
    "Fe": ElementData("Fe", 26, 7.46, 0.04, 7.46, 0.02, None),
    "Si": ElementData("Si", 14, 7.51, 0.03, 7.51, 0.01, None),
    "As": ElementData("As", 33, None, None, 2.30, 0.04, "meteorites"),
    "Xe": ElementData("Xe", 54, 2.22, 0.05, -1.95, 0.18, "nuclear physics"),
}

# The 15 elements whose Photosphere cells Asplund+2021 Table 2 leaves blank
# (unavailable), doi:10.1051/0004-6361/202140445.
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
    "Ir",
    "Pt",
    "Hg",
    "Bi",
    "U",
]

# CI chondrite (Ab, Uncert) for the first five ELEMENTS_WITHOUT_PHOTOSPHERE,
# Asplund+2021 Table 2 (doi:10.1051/0004-6361/202140445).
PUBLISHED_CI_WITHOUT_PHOTOSPHERE = {
    "As": (2.30, 0.04),
    "Se": (3.34, 0.03),
    "Br": (2.54, 0.06),
    "Cd": (1.71, 0.03),
    "Sb": (1.01, 0.06),
}

# Noble-gas CI chondrite (Ab, Uncert), Asplund+2021 Table 2
# (doi:10.1051/0004-6361/202140445).
PUBLISHED_NOBLE_GAS_CI = {
    "Ne": (-1.12, 0.18),
    "Ar": (-0.50, 0.18),
    "Kr": (-2.27, 0.18),
    "Xe": (-1.95, 0.18),
}


def exact(x):
    """``pytest.approx`` for a value shipped verbatim or computed from verbatim inputs.

    Tolerance rel=1e-12, abs=0: the CSV carries the table's decimals unchanged,
    so only float parsing or rounding may differ.
    """
    return pytest.approx(x, rel=1e-12, abs=0)


# Fe (CI Ab, CI Uncert, Photosphere Ab, Photosphere Uncert),
# Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445.
PUBLISHED_FE = (7.46, 0.02, 7.46, 0.04)

# O photosphere (Ab, Uncert), Asplund+2021 Table 2, doi:10.1051/0004-6361/202140445.
PUBLISHED_O_PHOTOSPHERE = (8.69, 0.04)

# Fe/O photosphere (ratio, uncertainty) by hand, to 5 significant digits:
# 10**(Fe-O) and ratio x ln10 x hypot(sigma_Fe, sigma_O).
HAND_FE_O = (0.058884, 0.0076699)  # 10**-1.23; hypot(.04, .04)


# Expected abundance ratios computed from published values
# Format: (expected_ratio, sigma_numerator, sigma_denominator)
EXPECTED_RATIOS: Dict[tuple, tuple] = {
    ("Fe", "O"): (10.0 ** (7.46 - 8.69), 0.04, 0.04),
    ("C", "O"): (10.0 ** (8.46 - 8.69), 0.04, 0.04),
    ("Fe", "H"): (10.0 ** (7.46 - 12.0), 0.04, 0.0),
}


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def ref():
    """ReferenceAbundances, which always loads Asplund+2021 Table 2."""
    return ReferenceAbundances()


# =============================================================================
# Smoke Tests: Data Loading
# =============================================================================


class TestDataLoading:
    """Smoke tests: verify data files load without errors."""

    def test_default_loads_a_dataframe(self):
        """``ReferenceAbundances()`` builds and exposes ``data`` as a DataFrame.

        ON FAILURE: the code is wrong.
        """
        ref = ReferenceAbundances()
        assert isinstance(
            ref.data, pd.DataFrame
        ), f"Expected pd.DataFrame, got {type(ref.data).__name__}"


# =============================================================================
# Unit Tests: Data Structure
# =============================================================================


class TestDataStructure:
    """Unit tests for DataFrame structure: shape, dtype, index."""

    def test_data_fe_row_matches_published_table(self, ref):
        """``data`` holds the published Fe row (PUBLISHED_FE), addressed by (Z, Symbol).

        Tolerance is ``exact``, not the significant-digit rule, which would
        accept 7.50 for 7.46.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ci_ab, ci_uncert, ph_ab, ph_uncert = PUBLISHED_FE
        row = ref.data.loc[(26, "Fe")]
        assert row[("CI_chondrites", "Ab")] == exact(ci_ab)
        assert row[("CI_chondrites", "Uncert")] == exact(ci_uncert)
        assert row[("Photosphere", "Ab")] == exact(ph_ab)
        assert row[("Photosphere", "Uncert")] == exact(ph_uncert)

    def test_data_has_83_elements(self, ref):
        """Asplund+2021 Table 2 lists 83 elements.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table's row count.
        """
        assert ref.data.shape[0] == 83, f"Expected 83 elements, got {ref.data.shape[0]}"

    def test_index_is_multiindex_with_z_symbol(self, ref):
        """Index is MultiIndex with levels ['Z', 'Symbol'].

        ON FAILURE: the code is wrong.
        """
        idx = ref.data.index
        assert isinstance(
            idx, pd.MultiIndex
        ), f"Expected MultiIndex, got {type(idx).__name__}"
        assert list(idx.names) == [
            "Z",
            "Symbol",
        ], f"Expected index names ['Z', 'Symbol'], got {list(idx.names)}"

    def test_columns_have_photosphere_and_ci_chondrites(self, ref):
        """Top-level columns include Photosphere and CI_chondrites.

        ON FAILURE: the code is wrong.
        """
        top_level = ref.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, "Missing 'Photosphere' column group"
        assert "CI_chondrites" in top_level, "Missing 'CI_chondrites' column group"

    def test_columns_are_multiindex(self, ref):
        """Columns are MultiIndex with at least 2 levels.

        ON FAILURE: the code is wrong.
        """
        assert isinstance(
            ref.data.columns, pd.MultiIndex
        ), f"Expected MultiIndex columns, got {type(ref.data.columns).__name__}"
        assert (
            ref.data.columns.nlevels >= 2
        ), f"Expected at least 2 column levels, got {ref.data.columns.nlevels}"

    def test_abundance_values_are_float64(self, ref):
        """``data`` columns are exactly (CI_chondrites, Photosphere) x (Ab, Uncert), all float64.

        The column set is the one the ``data`` docstring promises. Naming it
        exactly means the dtype check cannot pass over an empty selection, as
        a filter on ``col[1] in ("Ab", "Uncert")`` did when no column matched.

        ON FAILURE: the code is wrong.
        """
        data = ref.data
        expected = [
            ("CI_chondrites", "Ab"),
            ("CI_chondrites", "Uncert"),
            ("Photosphere", "Ab"),
            ("Photosphere", "Uncert"),
        ]
        assert sorted(data.columns.tolist()) == expected
        assert data.dtypes.to_dict() == {col: np.dtype(np.float64) for col in expected}

    @pytest.mark.parametrize("z", [1, 26, 92])
    def test_key_z_values_present(self, ref, z):
        """Key atomic numbers (H=1, Fe=26, U=92) are present in index.

        ON FAILURE: the code is wrong.
        """
        z_values = ref.data.index.get_level_values("Z").tolist()
        assert z in z_values, f"Z={z} missing from index"

    @pytest.mark.parametrize("symbol", ["H", "He", "C", "O", "Fe", "Si"])
    def test_key_symbols_present(self, ref, symbol):
        """Key element symbols are present in index.

        ON FAILURE: the code is wrong.
        """
        symbols = ref.data.index.get_level_values("Symbol").tolist()
        assert symbol in symbols, f"Symbol '{symbol}' missing from index"

    def test_z_values_are_integers(self, ref):
        """Z values in index are integers.

        ON FAILURE: the code is wrong.
        """
        z_values = ref.data.index.get_level_values("Z")
        assert all(
            isinstance(z, (int, np.integer)) for z in z_values
        ), "Z values should be integers"

    def test_z_range_is_1_to_92(self, ref):
        """Z values range from 1 (H) to 92 (U).

        ON FAILURE: the code is wrong.
        """
        z_values = ref.data.index.get_level_values("Z")
        assert min(z_values) == 1, f"Expected min Z=1, got {min(z_values)}"
        assert max(z_values) == 92, f"Expected max Z=92, got {max(z_values)}"


# =============================================================================
# Unit Tests: Column Naming
# =============================================================================


class TestColumnNaming:
    """Unit tests for CI_chondrites column with Meteorites alias."""

    def test_ci_chondrites_in_columns(self, ref):
        """'CI_chondrites' is a top-level column.

        ON FAILURE: the code is wrong.
        """
        top_level = ref.data.columns.get_level_values(0).unique().tolist()
        assert (
            "CI_chondrites" in top_level
        ), f"'CI_chondrites' not in columns: {top_level}"

    def test_photosphere_in_columns(self, ref):
        """'Photosphere' is a top-level column.

        ON FAILURE: the code is wrong.
        """
        top_level = ref.data.columns.get_level_values(0).unique().tolist()
        assert "Photosphere" in top_level, f"'Photosphere' not in columns: {top_level}"

    def test_meteorites_alias_returns_ci_chondrites_data(self, ref):
        """kind='Meteorites' returns the same Series as kind='CI_chondrites'.

        ON FAILURE: the code is wrong.
        """
        fe_meteorites = ref.get_element("Fe", kind="Meteorites")
        fe_ci_chondrites = ref.get_element("Fe", kind="CI_chondrites")

        pd.testing.assert_series_equal(
            fe_meteorites,
            fe_ci_chondrites,
            obj="Fe via kind='Meteorites' vs kind='CI_chondrites'",
        )

    def test_meteorites_alias_works_for_multiple_elements(self, ref):
        """Meteorites alias matches CI_chondrites for H, C, O and Si.

        ON FAILURE: the code is wrong.
        """
        for symbol in ["H", "C", "O", "Si"]:
            via_alias = ref.get_element(symbol, kind="Meteorites")
            via_canonical = ref.get_element(symbol, kind="CI_chondrites")
            pd.testing.assert_series_equal(
                via_alias,
                via_canonical,
                obj=f"{symbol} via Meteorites vs CI_chondrites",
            )

    def test_invalid_kind_raises_keyerror(self, ref):
        """Invalid kind raises KeyError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(KeyError, match=r"Invalid|not found|unknown"):
            ref.get_element("Fe", kind="InvalidKind")


# =============================================================================
# Unit Tests: Comments Column
# =============================================================================


class TestCommentsColumn:
    """Unit tests for Comments metadata column."""

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
    def test_comment_values_match_asplund_2021(self, ref, symbol, expected_comment):
        """Comment values match Asplund+2021 Table 2.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table comment.
        """
        comment = ref.get_comment(symbol)
        assert (
            comment == expected_comment
        ), f"{symbol} comment: expected '{expected_comment}', got '{comment}'"

    # Comments column blank for these in Asplund+2021 Table 2,
    # doi:10.1051/0004-6361/202140445
    @pytest.mark.parametrize("symbol", ["C", "O", "Fe", "Si", "N"])
    def test_spectroscopic_elements_have_no_comment(self, ref, symbol):
        """``get_comment`` returns None where Table 2 has no comment.

        The ``get_comment`` docstring promises None for a spectroscopic
        measurement; an empty string or NaN is not None.

        ON FAILURE: the code is wrong.
        """
        comment = ref.get_comment(symbol)
        assert comment is None, f"{symbol}: expected None, got {comment!r}"


# =============================================================================
# Unit Tests: Get Element
# =============================================================================


class TestGetElement:
    """Unit tests for element lookup by symbol and Z."""

    @pytest.mark.parametrize("key", ["Fe", 26], ids=["symbol", "z"])
    def test_get_element_returns_published_fe_photosphere(self, ref, key):
        """``get_element`` by symbol or by Z is the published Fe photosphere Series.

        Expected values: PUBLISHED_FE.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        _, _, ab, uncert = PUBLISHED_FE
        fe = ref.get_element(key)
        assert isinstance(fe, pd.Series)
        assert fe.index.tolist() == ["Ab", "Uncert"]
        assert fe["Ab"] == exact(ab)
        assert fe["Uncert"] == exact(uncert)

    @pytest.mark.parametrize("key", ["Fe", 26], ids=["symbol", "z"])
    def test_get_element_series_is_named_by_atomic_number(self, ref, key):
        """``get_element('Fe')`` and ``get_element(26)`` are both named 26.

        The ``get_element`` docstring promises a Series named by the atomic
        number Z for either key, and shows ``Name: 26`` for both lookups.

        ON FAILURE: the code is wrong.
        """
        assert ref.get_element(key).name == 26

    def test_get_by_symbol_series_has_correct_shape(self, ref):
        """get_element returns Series with shape (2,) for [Ab, Uncert].

        ON FAILURE: the code is wrong.
        """
        fe = ref.get_element("Fe")
        assert fe.shape == (2,), f"Expected shape (2,) for [Ab, Uncert], got {fe.shape}"

    def test_get_by_symbol_series_has_correct_index(self, ref):
        """get_element returns Series with index ['Ab', 'Uncert'].

        ON FAILURE: the code is wrong.
        """
        fe = ref.get_element("Fe")
        assert list(fe.index) == [
            "Ab",
            "Uncert",
        ], f"Expected index ['Ab', 'Uncert'], got {list(fe.index)}"

    def test_get_by_symbol_series_dtype_is_float64(self, ref):
        """get_element returns Series with float64 dtype.

        ON FAILURE: the code is wrong.
        """
        fe = ref.get_element("Fe")
        assert fe.dtype == np.float64, f"Expected dtype float64, got {fe.dtype}"

    def test_symbol_and_z_return_equal_series(self, ref):
        """get_element('Fe') equals get_element(26), values and name.

        ON FAILURE: the code is wrong.
        """
        by_symbol = ref.get_element("Fe")
        by_z = ref.get_element(26)
        pd.testing.assert_series_equal(by_symbol, by_z, obj="Fe by symbol vs by Z")

    def test_default_kind_is_photosphere(self, ref):
        """Default kind is 'Photosphere'.

        ON FAILURE: the code is wrong.
        """
        default = ref.get_element("Fe")
        explicit = ref.get_element("Fe", kind="Photosphere")
        pd.testing.assert_series_equal(
            default,
            explicit,
            obj="Default kind vs explicit Photosphere",
        )

    def test_invalid_key_type_raises_valueerror(self, ref):
        """Float key raises ValueError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match=r"Unrecognized key type"):
            ref.get_element(3.14)

    def test_unknown_element_raises_keyerror(self, ref):
        """Unknown element raises KeyError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(KeyError):
            ref.get_element("Xx")

    def test_unknown_z_raises_keyerror(self, ref):
        """Unknown atomic number raises KeyError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(KeyError):
            ref.get_element(999)


# =============================================================================
# Unit Tests: Missing Photosphere Data
# =============================================================================


class TestMissingPhotosphereData:
    """Unit tests for elements without photospheric measurements."""

    def test_photosphere_blank_exactly_where_table_2_is_blank(self, ref):
        """Photosphere Ab and Uncert are NaN for exactly the 15 Table 2 blanks.

        Asplund+2021 Table 2 leaves the photospheric value unavailable for
        ELEMENTS_WITHOUT_PHOTOSPHERE and gives one for every other element,
        so the NaN set must equal that list: filling a blank cell or blanking
        a measured one both fail.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table's blank cells.
        """
        photosphere = ref.data.loc[:, "Photosphere"]
        symbols = photosphere.index.get_level_values("Symbol")
        expected = set(ELEMENTS_WITHOUT_PHOTOSPHERE)
        assert len(expected) == 15
        assert set(symbols[photosphere["Ab"].isna()]) == expected
        assert set(symbols[photosphere["Uncert"].isna()]) == expected

    @pytest.mark.parametrize("symbol", ELEMENTS_WITHOUT_PHOTOSPHERE)
    def test_missing_photosphere_ab_is_nan(self, ref, symbol):
        """Elements without photospheric data have NaN for Ab via ``get_element``.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table's blank cell.
        """
        element = ref.get_element(symbol, kind="Photosphere")
        assert np.isnan(
            element.Ab
        ), f"{symbol} photosphere Ab should be NaN, got {element.Ab}"

    @pytest.mark.parametrize("symbol", ELEMENTS_WITHOUT_PHOTOSPHERE[:5])
    def test_missing_photosphere_has_ci_chondrites(self, ref, symbol):
        """Elements without a photospheric value carry the published CI value.

        Expected values: PUBLISHED_CI_WITHOUT_PHOTOSPHERE (Asplund+2021 Table 2).

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ab, uncert = PUBLISHED_CI_WITHOUT_PHOTOSPHERE[symbol]
        element = ref.get_element(symbol, kind="CI_chondrites")
        assert element.Ab == exact(ab)
        assert element.Uncert == exact(uncert)

    def test_h_photosphere_ab_is_12(self, ref):
        """H photosphere Ab is 12.00 (by definition).

        ON FAILURE: the code is wrong.
        """
        h = ref.get_element("H", kind="Photosphere")
        assert h.Ab == exact(12.00)

    def test_h_uncertainty_is_zero(self, ref):
        """H photosphere uncertainty is 0.00 (by definition, Table 2).

        ON FAILURE: the code is wrong.
        """
        h = ref.get_element("H", kind="Photosphere")
        assert h.Uncert == 0.0, f"H uncertainty should be 0.00, got {h.Uncert}"


# =============================================================================
# Integration Tests: Value Validation
# =============================================================================


class TestValueValidation:
    """Integration tests verifying values match the published Asplund table."""

    @pytest.mark.parametrize("symbol", ["Fe", "C", "O", "He", "Si"])
    def test_photosphere_values_match_published(self, ref, symbol):
        """Photospheric abundances match Asplund+2021 Table 2 (ASPLUND_DATA).

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        expected = ASPLUND_DATA[symbol]
        element = ref.get_element(symbol, kind="Photosphere")

        assert isinstance(
            element, pd.Series
        ), f"Expected pd.Series, got {type(element).__name__}"
        assert element.shape == (2,), f"Expected shape (2,), got {element.shape}"
        assert element.Ab == exact(expected.photosphere_ab)
        assert element.Uncert == exact(expected.photosphere_uncert)

    @pytest.mark.parametrize("symbol", ["Fe", "H", "Si"])
    def test_ci_chondrites_values_match_published(self, ref, symbol):
        """CI chondrite abundances match Asplund+2021 Table 2 (ASPLUND_DATA).

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        expected = ASPLUND_DATA[symbol]
        element = ref.get_element(symbol, kind="CI_chondrites")
        assert element.Ab == exact(expected.ci_chondrites_ab)
        assert element.Uncert == exact(expected.ci_chondrites_uncert)

    @pytest.mark.parametrize("symbol", sorted(PUBLISHED_NOBLE_GAS_CI))
    def test_noble_gas_ci_chondrites_match_table_2(self, ref, symbol):
        """Noble-gas CI chondrite abundances are the Table 2 values.

        Source: PUBLISHED_NOBLE_GAS_CI, Asplund+2021 Table 2,
        doi:10.1051/0004-6361/202140445.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value.
        """
        ab, uncert = PUBLISHED_NOBLE_GAS_CI[symbol]
        element = ref.get_element(symbol, kind="CI_chondrites")
        assert element.Ab == exact(ab)
        assert element.Uncert == exact(uncert)


# =============================================================================
# Integration Tests: Abundance Ratio
# =============================================================================


class TestAbundanceRatio:
    """Integration tests for abundance ratio calculations."""

    def test_fe_o_ratio_is_abundance_of_published_values(self, ref):
        """``abundance_ratio('Fe', 'O')`` is Abundance(10**(Fe-O), ratio ln10 sqrt(sFe^2+sO^2)).

        Unpacking yields (measurement, uncertainty) in that order. Expected
        values follow the propagation stated in the ``abundance_ratio``
        docstring Notes, from the published dex values (PUBLISHED_FE,
        PUBLISHED_O_PHOTOSPHERE), plus the independent hand-computed HAND_FE_O
        so a formula wrong in both places still fails.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table values or the stated error propagation.
        """
        _, _, fe, sigma_fe = PUBLISHED_FE
        o, sigma_o = PUBLISHED_O_PHOTOSPHERE
        hand_ratio, hand_uncert = HAND_FE_O

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

    @pytest.mark.parametrize("numerator,denominator", [("Fe", "O"), ("C", "O")])
    def test_ratio_calculation_matches_expected(self, ref, numerator, denominator):
        """Abundance ratios match values calculated from published data.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table values or the stated error propagation.
        """
        result = ref.abundance_ratio(numerator, denominator)

        expected_ratio, sigma_num, sigma_den = EXPECTED_RATIOS[(numerator, denominator)]
        expected_uncert = (
            expected_ratio * np.log(10) * np.sqrt(sigma_num**2 + sigma_den**2)
        )

        # Both sides are computed from the same verbatim table decimals.
        assert result.measurement == exact(expected_ratio)
        assert result.uncertainty == exact(expected_uncert)

    def test_fe_h_ratio_uses_hydrogen_denominator_path(self, ref):
        """Fe/H is 10**(Fe-12) with uncertainty from Fe alone.

        ON FAILURE: the code is wrong, unless the author rejects the cited
        table value or the stated error propagation.
        """
        result = ref.abundance_ratio("Fe", "H")

        expected_ratio, sigma_fe, _ = EXPECTED_RATIOS[("Fe", "H")]
        # For H denominator, uncertainty comes only from numerator
        expected_uncert = expected_ratio * np.log(10) * sigma_fe

        # Both sides are computed from the same verbatim table decimals.
        assert result.measurement == exact(expected_ratio)
        assert result.uncertainty == exact(expected_uncert)


# =============================================================================
# Module-Level Tests
# =============================================================================


def test_module_exports_referenceabundances():
    """Module __all__ includes ReferenceAbundances.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import abundances

    assert (
        "ReferenceAbundances" in abundances.__all__
    ), "ReferenceAbundances not in __all__"


def test_module_exports_abundance_namedtuple():
    """Module __all__ includes Abundance namedtuple.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import abundances

    assert "Abundance" in abundances.__all__, "Abundance not in __all__"


def test_abundance_namedtuple_structure():
    """Abundance namedtuple has fields (measurement, uncertainty).

    ON FAILURE: the code is wrong.
    """
    assert Abundance._fields == (
        "measurement",
        "uncertainty",
    ), f"Expected fields ('measurement', 'uncertainty'), got {Abundance._fields}"


def test_can_import_from_core():
    """Can import ReferenceAbundances from solarwindpy.core.abundances.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core.abundances import ReferenceAbundances as RA

    assert RA is ReferenceAbundances, "Import should resolve to same class"
