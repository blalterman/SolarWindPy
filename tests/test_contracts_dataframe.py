"""Contract tests for DataFrame patterns in SolarWindPy.

These tests validate the MultiIndex DataFrame structure and access patterns
used throughout the codebase. They serve as executable documentation of
the M/C/S (Measurement/Component/Species) column architecture.
"""

import numpy as np
import pandas as pd
import pytest


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sample_plasma_df() -> pd.DataFrame:
    """Create sample plasma DataFrame with canonical M/C/S structure."""
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
    epoch = pd.date_range("2023-01-01", periods=10, freq="1min")
    data = np.random.rand(10, len(columns))
    return pd.DataFrame(data, index=epoch, columns=columns)


@pytest.fixture
def sample_ion_df() -> pd.DataFrame:
    """Create sample Ion DataFrame with M/C structure (no species level)."""
    columns = pd.MultiIndex.from_tuples(
        [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
        ],
        names=["M", "C"],
    )
    epoch = pd.date_range("2023-01-01", periods=5, freq="1min")
    data = np.random.rand(5, len(columns))
    return pd.DataFrame(data, index=epoch, columns=columns)


@pytest.fixture
def multi_species_df() -> pd.DataFrame:
    """Create DataFrame with multiple species for aggregation tests."""
    columns = pd.MultiIndex.from_tuples(
        [
            ("w", "par", "p1"),
            ("w", "per", "p1"),
            ("w", "par", "a"),
            ("w", "per", "a"),
        ],
        names=["M", "C", "S"],
    )
    return pd.DataFrame([[1, 2, 3, 4], [5, 6, 7, 8]], columns=columns)


# ==============================================================================
# MultiIndex Structure Tests
# ==============================================================================


class TestMultiIndexStructure:
    """Contract tests for MultiIndex DataFrame structure."""

    def test_multiindex_level_names(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify MultiIndex has correct level names."""
        assert sample_plasma_df.columns.names == ["M", "C", "S"], (
            "Column MultiIndex must have names ['M', 'C', 'S']"
        )

    def test_multiindex_level_count(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify MultiIndex has exactly 3 levels."""
        assert sample_plasma_df.columns.nlevels == 3, (
            "Column MultiIndex must have exactly 3 levels"
        )

    def test_datetime_index(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify row index is DatetimeIndex."""
        assert isinstance(sample_plasma_df.index, pd.DatetimeIndex), (
            "Row index must be DatetimeIndex"
        )

    def test_monotonic_increasing_index(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify datetime index is monotonically increasing."""
        assert sample_plasma_df.index.is_monotonic_increasing, (
            "DatetimeIndex must be monotonically increasing"
        )

    def test_no_duplicate_columns(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify no duplicate columns exist."""
        assert not sample_plasma_df.columns.duplicated().any(), (
            "DataFrame must not have duplicate columns"
        )

    def test_bfield_empty_species(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify magnetic field uses empty string for species."""
        b_columns = sample_plasma_df.xs("b", axis=1, level="M").columns
        species_values = b_columns.get_level_values("S")
        assert all(s == "" for s in species_values), (
            "Magnetic field species level must be empty string"
        )

    def test_density_empty_component(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify scalar quantities use empty string for component."""
        n_columns = sample_plasma_df.xs("n", axis=1, level="M").columns
        component_values = n_columns.get_level_values("C")
        assert all(c == "" for c in component_values), (
            "Density component level must be empty string"
        )


# ==============================================================================
# Ion Structure Tests
# ==============================================================================


class TestIonDataStructure:
    """Contract tests for Ion class data requirements."""

    def test_ion_mc_column_names(self, sample_ion_df: pd.DataFrame) -> None:
        """Verify Ion data uses ['M', 'C'] column names."""
        assert sample_ion_df.columns.names == ["M", "C"], (
            "Ion data must have column names ['M', 'C']"
        )

    def test_required_columns_present(self, sample_ion_df: pd.DataFrame) -> None:
        """Verify required columns for Ion class."""
        required = [
            ("n", ""),
            ("v", "x"),
            ("v", "y"),
            ("v", "z"),
            ("w", "par"),
            ("w", "per"),
        ]
        assert pd.Index(required).isin(sample_ion_df.columns).all(), (
            "Ion data must have all required columns"
        )

    def test_ion_extraction_from_mcs_data(
        self, sample_plasma_df: pd.DataFrame
    ) -> None:
        """Verify Ion correctly extracts species from ['M', 'C', 'S'] data."""
        # Should extract 'p1' data via xs()
        p1_data = sample_plasma_df.xs("p1", axis=1, level="S")

        assert p1_data.columns.names == ["M", "C"]
        assert len(p1_data.columns) >= 5  # n, v.x, v.y, v.z, w.par, w.per


# ==============================================================================
# Cross-Section Pattern Tests
# ==============================================================================


class TestCrossSectionPatterns:
    """Contract tests for .xs() usage patterns."""

    def test_xs_extracts_single_species(
        self, sample_plasma_df: pd.DataFrame
    ) -> None:
        """Verify .xs() extracts single species correctly."""
        p1_data = sample_plasma_df.xs("p1", axis=1, level="S")

        # Should reduce from 3 levels to 2 levels
        assert p1_data.columns.nlevels == 2
        assert p1_data.columns.names == ["M", "C"]

    def test_xs_extracts_measurement_type(
        self, sample_plasma_df: pd.DataFrame
    ) -> None:
        """Verify .xs() extracts measurement type correctly."""
        v_data = sample_plasma_df.xs("v", axis=1, level="M")

        # Should have velocity components
        assert len(v_data.columns) >= 3  # x, y, z for p1

    def test_xs_with_tuple_full_path(
        self, sample_plasma_df: pd.DataFrame
    ) -> None:
        """Verify .xs() with tuple for full path selection."""
        # Select density for p1
        n_p1 = sample_plasma_df.xs(("n", "", "p1"), axis=1)

        # Should return a Series
        assert isinstance(n_p1, pd.Series)

    def test_xs_preserves_index(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify .xs() preserves the row index."""
        p1_data = sample_plasma_df.xs("p1", axis=1, level="S")

        pd.testing.assert_index_equal(p1_data.index, sample_plasma_df.index)


# ==============================================================================
# Reorder Levels Pattern Tests
# ==============================================================================


class TestReorderLevelsBehavior:
    """Contract tests for reorder_levels + sort_index pattern."""

    def test_reorder_levels_restores_canonical_order(self) -> None:
        """Verify reorder_levels produces ['M', 'C', 'S'] order."""
        # Create DataFrame with non-canonical column order
        columns = pd.MultiIndex.from_tuples(
            [
                ("p1", "x", "v"),
                ("p1", "", "n"),  # Wrong order: S, C, M
            ],
            names=["S", "C", "M"],
        )
        shuffled = pd.DataFrame([[1, 2]], columns=columns)

        reordered = shuffled.reorder_levels(["M", "C", "S"], axis=1)
        assert reordered.columns.names == ["M", "C", "S"]

    def test_sort_index_after_reorder(self) -> None:
        """Verify sort_index produces deterministic column order."""
        columns = pd.MultiIndex.from_tuples(
            [
                ("p1", "x", "v"),
                ("p1", "", "n"),
            ],
            names=["S", "C", "M"],
        )
        shuffled = pd.DataFrame([[1, 2]], columns=columns)

        reordered = shuffled.reorder_levels(["M", "C", "S"], axis=1).sort_index(
            axis=1
        )

        expected = pd.MultiIndex.from_tuples(
            [("n", "", "p1"), ("v", "x", "p1")], names=["M", "C", "S"]
        )
        assert reordered.columns.equals(expected)


# ==============================================================================
# Groupby Transpose Pattern Tests
# ==============================================================================


class TestGroupbyTransposePattern:
    """Contract tests for .T.groupby().agg().T pattern."""

    def test_groupby_transpose_sum_by_species(
        self, multi_species_df: pd.DataFrame
    ) -> None:
        """Verify transpose-groupby-transpose sums by species correctly."""
        result = multi_species_df.T.groupby(level="S").sum().T

        # Should have 2 columns: 'a' and 'p1'
        assert len(result.columns) == 2
        assert set(result.columns) == {"a", "p1"}

        # p1 values: [1+2=3, 5+6=11], a values: [3+4=7, 7+8=15]
        assert result.loc[0, "p1"] == 3
        assert result.loc[0, "a"] == 7

    def test_groupby_transpose_sum_by_component(
        self, multi_species_df: pd.DataFrame
    ) -> None:
        """Verify transpose-groupby-transpose sums by component correctly."""
        result = multi_species_df.T.groupby(level="C").sum().T

        assert len(result.columns) == 2
        assert set(result.columns) == {"par", "per"}

    def test_groupby_transpose_preserves_row_index(
        self, multi_species_df: pd.DataFrame
    ) -> None:
        """Verify transpose pattern preserves row index."""
        result = multi_species_df.T.groupby(level="S").sum().T

        pd.testing.assert_index_equal(result.index, multi_species_df.index)


# ==============================================================================
# Column Duplication Prevention Tests
# ==============================================================================


class TestColumnDuplicationPrevention:
    """Contract tests for column duplication prevention."""

    def test_isin_detects_duplicates(self) -> None:
        """Verify .isin() correctly detects column overlap."""
        cols1 = pd.MultiIndex.from_tuples(
            [("n", "", "p1"), ("v", "x", "p1")], names=["M", "C", "S"]
        )
        cols2 = pd.MultiIndex.from_tuples(
            [("n", "", "p1"), ("w", "par", "p1")],  # n overlaps
            names=["M", "C", "S"],
        )

        df1 = pd.DataFrame([[1, 2]], columns=cols1)
        df2 = pd.DataFrame([[3, 4]], columns=cols2)

        assert df2.columns.isin(df1.columns).any(), (
            "Should detect overlapping column ('n', '', 'p1')"
        )

    def test_duplicated_filters_duplicates(self) -> None:
        """Verify .duplicated() can filter duplicate columns."""
        cols = pd.MultiIndex.from_tuples(
            [("n", "", "p1"), ("v", "x", "p1"), ("n", "", "p1")],  # duplicate
            names=["M", "C", "S"],
        )
        df = pd.DataFrame([[1, 2, 3]], columns=cols)

        clean = df.loc[:, ~df.columns.duplicated()]
        assert len(clean.columns) == 2
        assert not clean.columns.duplicated().any()


# ==============================================================================
# Level-Specific Operation Tests
# ==============================================================================


class TestLevelSpecificOperations:
    """Contract tests for level-specific DataFrame operations."""

    def test_multiply_with_level_broadcasts(
        self, multi_species_df: pd.DataFrame
    ) -> None:
        """Verify multiply with level= broadcasts correctly."""
        coeffs = pd.Series({"par": 2.0, "per": 0.5})
        result = multi_species_df.multiply(coeffs, axis=1, level="C")

        # par columns should be doubled, per halved
        # Original: [[1, 2, 3, 4], [5, 6, 7, 8]] with (par, per) for (p1, a)
        assert result.loc[0, ("w", "par", "p1")] == 2  # 1 * 2
        assert result.loc[0, ("w", "per", "p1")] == 1  # 2 * 0.5
        assert result.loc[0, ("w", "par", "a")] == 6  # 3 * 2
        assert result.loc[0, ("w", "per", "a")] == 2  # 4 * 0.5

    def test_drop_with_level(self, sample_plasma_df: pd.DataFrame) -> None:
        """Verify drop with level= removes specified values."""
        # Drop proton data
        result = sample_plasma_df.drop("p1", axis=1, level="S")

        # Should only have magnetic field columns (species='')
        remaining_species = result.columns.get_level_values("S").unique()
        assert "p1" not in remaining_species
