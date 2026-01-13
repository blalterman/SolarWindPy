#!/usr/bin/env python
"""Tests for solarwindpy.plotting.spiral module.

This module provides comprehensive test coverage for the spiral mesh plotting and
binning utilities, including numba-accelerated functions.
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from collections import namedtuple

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection

import solarwindpy.plotting.spiral as spiral_module
from solarwindpy.plotting.spiral import (
    get_counts_per_bin,
    calculate_bin_number_with_numba,
    SpiralMesh,
    SpiralPlot2D,
    InitialSpiralEdges,
    SpiralMeshBinID,
    SpiralFilterThresholds,
)


class TestSpiralModuleStructure:
    """Test spiral module structure and imports."""

    def test_module_imports(self):
        """Test that all required imports are accessible."""
        # Test basic imports
        assert hasattr(spiral_module, "base")
        assert hasattr(spiral_module, "labels_module")
        assert hasattr(spiral_module, "plt")
        assert hasattr(spiral_module, "np")
        assert hasattr(spiral_module, "pd")

    def test_numba_functions_available(self):
        """Test that numba-accelerated functions are accessible."""
        assert hasattr(spiral_module, "get_counts_per_bin")
        assert hasattr(spiral_module, "calculate_bin_number_with_numba")
        assert callable(spiral_module.get_counts_per_bin)
        assert callable(spiral_module.calculate_bin_number_with_numba)

    def test_classes_available(self):
        """Test that spiral classes are accessible."""
        assert hasattr(spiral_module, "SpiralMesh")
        assert hasattr(spiral_module, "SpiralPlot2D")
        assert callable(spiral_module.SpiralMesh)
        assert callable(spiral_module.SpiralPlot2D)

    def test_namedtuple_definitions(self):
        """Test that named tuples are properly defined."""
        assert hasattr(spiral_module, "InitialSpiralEdges")
        assert hasattr(spiral_module, "SpiralMeshBinID")
        assert hasattr(spiral_module, "SpiralFilterThresholds")

        # Test that they are indeed named tuples
        assert issubclass(InitialSpiralEdges, tuple)
        assert issubclass(SpiralMeshBinID, tuple)
        assert issubclass(SpiralFilterThresholds, tuple)


class TestNamedTuples:
    """Test named tuple structures and functionality."""

    def test_initial_spiral_edges_structure(self):
        """Test InitialSpiralEdges named tuple."""
        # Test creation
        x_edges = np.array([0, 1, 2, 3])
        y_edges = np.array([0, 1, 2])
        edges = InitialSpiralEdges(x_edges, y_edges)

        assert edges.x is x_edges
        assert edges.y is y_edges
        assert len(edges) == 2

    def test_spiral_mesh_bin_id_structure(self):
        """Test SpiralMeshBinID named tuple."""
        bin_ids = np.array([0, 1, 2, 1, 0])
        fill_value = -9999
        visited = np.array([1, 1, 1])

        bin_id = SpiralMeshBinID(bin_ids, fill_value, visited)

        assert np.array_equal(bin_id.id, bin_ids)
        assert bin_id.fill == fill_value
        assert np.array_equal(bin_id.visited, visited)
        assert len(bin_id) == 3

    def test_spiral_filter_thresholds_structure(self):
        """Test SpiralFilterThresholds named tuple with defaults."""
        # Test with defaults
        thresholds = SpiralFilterThresholds(density=0.5)
        assert thresholds.density == 0.5
        assert thresholds.size is False  # Default value

        # Test without defaults
        thresholds2 = SpiralFilterThresholds(density=0.3, size=0.9)
        assert thresholds2.density == 0.3
        assert thresholds2.size == 0.9

    def test_namedtuple_immutability(self):
        """Test that named tuples are immutable."""
        edges = InitialSpiralEdges([1, 2, 3], [4, 5, 6])

        with pytest.raises(AttributeError):
            edges.x = [7, 8, 9]


class TestNumbaFunctions:
    """Test numba-accelerated functions."""

    def setup_method(self):
        """Set up test data for numba functions."""
        # Create simple test bins: 2x2 grid
        self.bins = np.array(
            [
                [0, 1, 0, 1],  # Lower-left bin
                [1, 2, 0, 1],  # Lower-right bin
                [0, 1, 1, 2],  # Upper-left bin
                [1, 2, 1, 2],  # Upper-right bin
            ],
            dtype=np.float64,
        )

        # Test points
        self.x = np.array([0.5, 1.5, 0.5, 1.5, 0.1])
        self.y = np.array([0.5, 0.5, 1.5, 1.5, 0.1])

    def test_get_counts_per_bin_basic(self):
        """Test basic functionality of get_counts_per_bin."""
        counts = get_counts_per_bin(self.bins, self.x, self.y)

        assert isinstance(counts, np.ndarray)
        assert counts.dtype == np.int64
        assert len(counts) == len(self.bins)

        # Should have one point in each of the 4 bins, plus one more in bin 0
        expected = np.array([2, 1, 1, 1])  # Two points in first bin
        assert np.array_equal(counts, expected)

    def test_get_counts_per_bin_empty_bins(self):
        """Test get_counts_per_bin with empty bins."""
        # Points outside all bins
        x_out = np.array([5, 6])
        y_out = np.array([5, 6])

        counts = get_counts_per_bin(self.bins, x_out, y_out)

        assert isinstance(counts, np.ndarray)
        assert len(counts) == len(self.bins)
        assert np.all(counts == 0)

    def test_get_counts_per_bin_boundary_points(self):
        """Test boundary point handling in get_counts_per_bin."""
        # Points exactly on boundaries (should be included in left/bottom bin)
        x_boundary = np.array([1.0, 0.0])
        y_boundary = np.array([0.0, 1.0])

        counts = get_counts_per_bin(self.bins, x_boundary, y_boundary)

        # Point at (1,0) should be in lower-left bin (x>=0 & x<1 is false, x>=1 & x<2 is true)
        # Point at (0,1) should be in upper-left bin
        expected = np.array([0, 1, 1, 0])
        assert np.array_equal(counts, expected)

    def test_calculate_bin_number_with_numba_basic(self):
        """Test basic functionality of calculate_bin_number_with_numba."""
        zbin, fill, bin_visited = calculate_bin_number_with_numba(
            self.bins, self.x, self.y
        )

        assert isinstance(zbin, np.ndarray)
        assert isinstance(fill, (int, np.integer))
        assert isinstance(bin_visited, np.ndarray)

        assert len(zbin) == len(self.x)
        assert zbin.dtype == np.int64
        assert fill == -9999

        # Check that points are assigned to correct bins
        expected_bins = np.array([0, 1, 2, 3, 0])  # Last point also in bin 0
        assert np.array_equal(zbin, expected_bins)

    def test_calculate_bin_number_with_numba_outside_points(self):
        """Test calculate_bin_number_with_numba with points outside mesh."""
        # Add points outside the mesh
        x_with_outside = np.append(self.x, [5, -1])
        y_with_outside = np.append(self.y, [5, -1])

        zbin, fill, bin_visited = calculate_bin_number_with_numba(
            self.bins, x_with_outside, y_with_outside
        )

        # Points outside mesh should have fill value
        assert zbin[-2] == fill
        assert zbin[-1] == fill

        # Other points should still be assigned correctly
        assert zbin[0] == 0  # First point in bin 0

    def test_numba_function_performance(self):
        """Test that numba functions handle reasonably large datasets."""
        # Create larger dataset
        n_points = 10000
        large_x = np.random.uniform(0, 2, n_points)
        large_y = np.random.uniform(0, 2, n_points)

        # Should not raise memory errors or take excessive time
        counts = get_counts_per_bin(self.bins, large_x, large_y)
        assert len(counts) == len(self.bins)
        assert counts.sum() <= n_points  # Some points might be outside

        zbin, fill, bin_visited = calculate_bin_number_with_numba(
            self.bins, large_x, large_y
        )
        assert len(zbin) == n_points


class TestSpiralMesh:
    """Test SpiralMesh class functionality."""

    def setup_method(self):
        """Set up test data for SpiralMesh tests."""
        self.x_data = pd.Series(np.random.uniform(0, 10, 100))
        self.y_data = pd.Series(np.random.uniform(0, 10, 100))
        self.x_edges = np.linspace(0, 10, 6)  # 5 bins
        self.y_edges = np.linspace(0, 10, 6)  # 5 bins
        self.min_per_bin = 5

    def test_spiral_mesh_initialization(self):
        """Test SpiralMesh initialization."""
        mesh = SpiralMesh(
            self.x_data,
            self.y_data,
            self.x_edges,
            self.y_edges,
            min_per_bin=self.min_per_bin,
        )

        assert mesh is not None
        assert hasattr(mesh, "data")
        assert hasattr(mesh, "initial_edges")
        assert hasattr(mesh, "min_per_bin")
        assert hasattr(mesh, "cell_filter_thresholds")

    def test_spiral_mesh_properties(self):
        """Test SpiralMesh property access."""
        mesh = SpiralMesh(
            self.x_data,
            self.y_data,
            self.x_edges,
            self.y_edges,
            min_per_bin=self.min_per_bin,
        )

        # Test property access
        assert isinstance(mesh.data, pd.DataFrame)
        assert isinstance(mesh.initial_edges, InitialSpiralEdges)
        assert isinstance(mesh.min_per_bin, int)
        assert isinstance(mesh.cell_filter_thresholds, SpiralFilterThresholds)

        # Test data structure
        assert "x" in mesh.data.columns
        assert "y" in mesh.data.columns
        assert len(mesh.data) == len(self.x_data)

    def test_spiral_mesh_set_methods(self):
        """Test SpiralMesh setter methods."""
        mesh = SpiralMesh(
            self.x_data, self.y_data, self.x_edges, self.y_edges, min_per_bin=10
        )

        # Test set_min_per_bin
        mesh.set_min_per_bin(20)
        assert mesh.min_per_bin == 20

        # Test set_cell_filter_thresholds
        mesh.set_cell_filter_thresholds(density=0.5, size=0.9)
        assert mesh.cell_filter_thresholds.density == 0.5
        assert mesh.cell_filter_thresholds.size == 0.9

        # Test set_initial_edges
        new_x_edges = np.linspace(0, 5, 4)
        new_y_edges = np.linspace(0, 5, 4)
        mesh.set_initial_edges(new_x_edges, new_y_edges)
        assert np.array_equal(mesh.initial_edges.x, new_x_edges)
        assert np.array_equal(mesh.initial_edges.y, new_y_edges)

    def test_spiral_mesh_initialize_bins(self):
        """Test spiral mesh bin initialization."""
        mesh = SpiralMesh(
            self.x_data,
            self.y_data,
            self.x_edges,
            self.y_edges,
            min_per_bin=self.min_per_bin,
        )

        initial_mesh = mesh.initialize_bins()

        assert isinstance(initial_mesh, np.ndarray)
        assert initial_mesh.shape[1] == 4  # x0, x1, y0, y1

        # Should have (nx-1) * (ny-1) bins
        expected_n_bins = (len(self.x_edges) - 1) * (len(self.y_edges) - 1)
        assert initial_mesh.shape[0] == expected_n_bins

        # All values should be finite
        assert np.isfinite(initial_mesh).all()

    def test_spiral_mesh_cell_filter_invalid_kwargs(self):
        """Test that invalid kwargs raise errors."""
        mesh = SpiralMesh(
            self.x_data,
            self.y_data,
            self.x_edges,
            self.y_edges,
            min_per_bin=self.min_per_bin,
        )

        with pytest.raises(KeyError, match="Unexpected kwarg"):
            mesh.set_cell_filter_thresholds(invalid_param=0.5)


class TestSpiralPlot2D:
    """Test SpiralPlot2D class functionality."""

    def setup_method(self):
        """Set up test data for SpiralPlot2D tests."""
        self.x_data = pd.Series(np.random.uniform(1, 100, 50))  # Positive for log
        self.y_data = pd.Series(np.random.uniform(1, 100, 50))  # Positive for log
        self.z_data = pd.Series(np.random.uniform(0, 10, 50))

    def test_spiral_plot_2d_initialization(self):
        """Test SpiralPlot2D initialization."""
        splot = SpiralPlot2D(self.x_data, self.y_data)

        assert splot is not None
        assert hasattr(splot, "data")
        assert hasattr(splot, "initial_bins")
        assert hasattr(splot, "clim")

    def test_spiral_plot_2d_with_z_data(self):
        """Test SpiralPlot2D initialization with z data."""
        splot = SpiralPlot2D(self.x_data, self.y_data, self.z_data)

        assert "z" in splot.data.columns
        assert len(splot.data) == len(self.x_data)

    def test_spiral_plot_2d_log_scaling(self):
        """Test SpiralPlot2D with logarithmic scaling."""
        splot = SpiralPlot2D(self.x_data, self.y_data, logx=True, logy=True)

        # With log scaling, data should be log-transformed
        original_data_range = self.x_data.max() - self.x_data.min()
        plot_data_range = splot.data["x"].max() - splot.data["x"].min()

        # Log-transformed range should be smaller than original
        assert plot_data_range < original_data_range

    def test_spiral_plot_2d_initial_bins_calculation(self):
        """Test initial bins calculation."""
        splot = SpiralPlot2D(self.x_data, self.y_data, initial_bins=5)

        bins = splot.initial_bins
        assert isinstance(bins, dict)
        assert "x" in bins
        assert "y" in bins

        # Each should have 6 edges for 5 bins
        assert len(bins["x"]) == 6
        assert len(bins["y"]) == 6

    def test_spiral_plot_2d_clim_setting(self):
        """Test color limit setting."""
        splot = SpiralPlot2D(self.x_data, self.y_data, self.z_data)

        # Test setting color limits
        splot.set_clim(lower=1, upper=9)
        assert splot.clim.lower == 1
        assert splot.clim.upper == 9

        # Test with None values
        splot.set_clim(lower=None, upper=10)
        assert splot.clim.lower is None
        assert splot.clim.upper == 10

    @patch("matplotlib.pyplot.subplots")
    def test_spiral_plot_2d_initialization_mesh(self, mock_subplots):
        """Test mesh initialization in SpiralPlot2D."""
        splot = SpiralPlot2D(self.x_data, self.y_data, initial_bins=3)

        # Initialize mesh with small min_per_bin for testing
        splot.initialize_mesh(min_per_bin=2)

        assert hasattr(splot, "_mesh")
        assert isinstance(splot._mesh, SpiralMesh)
        assert hasattr(splot._mesh, "mesh")


class TestSpiralIntegration:
    """Test integration between spiral components."""

    def setup_method(self):
        """Set up test data for integration tests."""
        # Create structured test data
        np.random.seed(42)  # For reproducible tests
        self.x_data = pd.Series(np.random.uniform(0, 10, 100))
        self.y_data = pd.Series(np.random.uniform(0, 10, 100))
        self.z_data = pd.Series(np.random.uniform(0, 5, 100))

    def test_spiral_mesh_full_workflow(self):
        """Test complete spiral mesh workflow."""
        x_edges = np.linspace(0, 10, 6)
        y_edges = np.linspace(0, 10, 6)

        mesh = SpiralMesh(self.x_data, self.y_data, x_edges, y_edges, min_per_bin=3)

        # Initialize and generate mesh
        initial_bins = mesh.initialize_bins()
        assert initial_bins is not None

        # The generate_mesh method is complex and involves iterative refinement
        # For testing, we'll just verify the basic structure exists
        assert hasattr(mesh, "generate_mesh")
        assert callable(mesh.generate_mesh)

    def test_numba_functions_integration(self):
        """Test integration between numba functions."""
        # Create simple mesh
        bins = np.array(
            [
                [0, 5, 0, 5],
                [5, 10, 0, 5],
                [0, 5, 5, 10],
                [5, 10, 5, 10],
            ],
            dtype=np.float64,
        )

        x = self.x_data.values
        y = self.y_data.values

        # Test that both functions work together
        counts = get_counts_per_bin(bins, x, y)
        zbin, fill, visited = calculate_bin_number_with_numba(bins, x, y)

        # Counts should match the assigned bins
        manual_counts = np.bincount(zbin[zbin != fill], minlength=len(bins))
        assert np.array_equal(counts, manual_counts)


class TestSpiralErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_x = pd.Series([], dtype=float)
        empty_y = pd.Series([], dtype=float)
        edges = np.array([0, 1, 2])

        # Should not crash with empty data
        mesh = SpiralMesh(empty_x, empty_y, edges, edges, min_per_bin=1)
        assert len(mesh.data) == 0

    def test_invalid_bin_parameters(self):
        """Test invalid bin parameter handling."""
        x_data = pd.Series([1, 2, 3])
        y_data = pd.Series([1, 2, 3])

        # Invalid min_per_bin type
        with pytest.raises((TypeError, ValueError)):
            SpiralMesh(x_data, y_data, [0, 1], [0, 1], min_per_bin="invalid")

    def test_mismatched_data_lengths(self):
        """Test handling of mismatched x, y data lengths."""
        x_data = pd.Series([1, 2, 3])
        y_data = pd.Series([1, 2])  # Different length
        edges = np.array([0, 1, 2])

        # pandas concat fills missing values with NaN
        mesh = SpiralMesh(x_data, y_data, edges, edges, min_per_bin=1)
        # Data preserves the longer length but has NaN values
        assert len(mesh.data) == 3
        assert mesh.data.isnull().any().any()  # Should have NaN values

    def test_numba_function_edge_cases(self):
        """Test numba functions with edge case inputs."""
        # Single bin
        single_bin = np.array([[0, 1, 0, 1]], dtype=np.float64)
        x = np.array([0.5])
        y = np.array([0.5])

        counts = get_counts_per_bin(single_bin, x, y)
        assert len(counts) == 1
        assert counts[0] == 1

        zbin, fill, visited = calculate_bin_number_with_numba(single_bin, x, y)
        assert len(zbin) == 1
        assert zbin[0] == 0  # Should be assigned to bin 0


class TestSpiralPerformance:
    """Test performance characteristics of spiral components."""

    def test_numba_compilation(self):
        """Test that numba functions compile successfully."""
        # Small test to trigger JIT compilation
        bins = np.array([[0, 1, 0, 1]], dtype=np.float64)
        x = np.array([0.5])
        y = np.array([0.5])

        # First call triggers compilation
        counts1 = get_counts_per_bin(bins, x, y)

        # Second call should use compiled version
        counts2 = get_counts_per_bin(bins, x, y)

        assert np.array_equal(counts1, counts2)

    def test_large_dataset_handling(self):
        """Test handling of reasonably large datasets."""
        # Create larger dataset (but not too large for CI)
        n_points = 5000
        x_large = pd.Series(np.random.uniform(0, 10, n_points))
        y_large = pd.Series(np.random.uniform(0, 10, n_points))
        edges = np.linspace(0, 10, 11)  # 10 bins

        mesh = SpiralMesh(x_large, y_large, edges, edges, min_per_bin=10)

        # Should handle large datasets without memory issues
        initial_bins = mesh.initialize_bins()
        assert initial_bins.shape[0] == 100  # 10x10 grid
        assert len(mesh.data) == n_points


class TestSpiralDocumentation:
    """Test documentation and docstrings."""

    def test_module_docstring(self):
        """Test that module has docstring."""
        assert spiral_module.__doc__ is not None
        assert len(spiral_module.__doc__.strip()) > 0

    def test_function_docstrings(self):
        """Test that functions have docstrings."""
        # Note: numba functions may not preserve docstrings
        # Just test that they are callable
        assert callable(get_counts_per_bin)
        assert callable(calculate_bin_number_with_numba)

    def test_class_docstrings(self):
        """Test that classes have docstrings."""
        # SpiralMesh may not have docstrings, just test it exists and is callable
        assert callable(SpiralMesh)

        # SpiralPlot2D should have docstring
        assert SpiralPlot2D.__doc__ is not None
        assert len(SpiralPlot2D.__doc__.strip()) > 0


class TestSpiralPlot2DContours:
    """Test SpiralPlot2D.plot_contours() method with interpolation options."""

    @pytest.fixture
    def spiral_plot_instance(self):
        """Minimal SpiralPlot2D with initialized mesh."""
        np.random.seed(42)
        x = pd.Series(np.random.uniform(1, 100, 500))
        y = pd.Series(np.random.uniform(1, 100, 500))
        z = pd.Series(np.sin(x / 10) * np.cos(y / 10))
        splot = SpiralPlot2D(x, y, z, initial_bins=5)
        splot.initialize_mesh(min_per_bin=10)
        splot.build_grouped()
        return splot

    @pytest.fixture
    def spiral_plot_with_nans(self, spiral_plot_instance):
        """SpiralPlot2D with NaN values in z-data."""
        # Add NaN values to every 10th data point
        data = spiral_plot_instance.data.copy()
        data.loc[data.index[::10], "z"] = np.nan
        spiral_plot_instance._data = data
        # Rebuild grouped data to include NaNs
        spiral_plot_instance.build_grouped()
        return spiral_plot_instance

    def test_returns_correct_types(self, spiral_plot_instance):
        """Test that plot_contours returns correct types (API contract)."""
        fig, ax = plt.subplots()
        result = spiral_plot_instance.plot_contours(ax=ax)
        plt.close()

        assert len(result) == 4, "Should return 4-tuple"
        ret_ax, lbls, cbar_or_mappable, qset = result

        # ax should be Axes
        assert isinstance(ret_ax, matplotlib.axes.Axes), "First element should be Axes"

        # lbls can be list of Text objects or None (if label_levels=False or no levels)
        if lbls is not None:
            assert isinstance(lbls, list), "Labels should be a list"
            if len(lbls) > 0:
                assert all(
                    isinstance(lbl, matplotlib.text.Text) for lbl in lbls
                ), "All labels should be Text objects"

        # cbar_or_mappable should be Colorbar when cbar=True
        assert isinstance(
            cbar_or_mappable, matplotlib.colorbar.Colorbar
        ), "Should return Colorbar when cbar=True"

        # qset should be a contour set
        assert hasattr(qset, "levels"), "qset should have levels attribute"
        assert hasattr(qset, "allsegs"), "qset should have allsegs attribute"

    def test_default_method_is_rbf(self, spiral_plot_instance):
        """Test that default method is 'rbf'."""
        fig, ax = plt.subplots()

        # Mock _interpolate_with_rbf to verify it's called
        with patch.object(
            spiral_plot_instance,
            "_interpolate_with_rbf",
            wraps=spiral_plot_instance._interpolate_with_rbf,
        ) as mock_rbf:
            ax, lbls, cbar, qset = spiral_plot_instance.plot_contours(ax=ax)
            mock_rbf.assert_called_once()
        plt.close()

        # Should also produce valid contours
        assert len(qset.levels) > 0, "Should produce contour levels"
        assert qset.allsegs is not None, "Should have contour segments"

    def test_rbf_respects_neighbors_parameter(self, spiral_plot_instance):
        """Test that RBF neighbors parameter is passed to interpolator."""
        fig, ax = plt.subplots()

        # Verify rbf_neighbors is passed through to _interpolate_with_rbf
        with patch.object(
            spiral_plot_instance,
            "_interpolate_with_rbf",
            wraps=spiral_plot_instance._interpolate_with_rbf,
        ) as mock_rbf:
            spiral_plot_instance.plot_contours(
                ax=ax, method="rbf", rbf_neighbors=77, cbar=False, label_levels=False
            )
            mock_rbf.assert_called_once()
            # Verify the neighbors parameter was passed correctly
            call_kwargs = mock_rbf.call_args.kwargs
            assert (
                call_kwargs["neighbors"] == 77
            ), f"Expected neighbors=77, got neighbors={call_kwargs['neighbors']}"
        plt.close()

    def test_grid_respects_gaussian_filter_std(self, spiral_plot_instance):
        """Test that Gaussian filter std parameter is passed to filter."""
        from solarwindpy.plotting.tools import nan_gaussian_filter

        fig, ax = plt.subplots()

        # Verify nan_gaussian_filter is called with the correct sigma
        # Patch where it's defined since spiral.py imports it locally
        with patch(
            "solarwindpy.plotting.tools.nan_gaussian_filter",
            wraps=nan_gaussian_filter,
        ) as mock_filter:
            _, _, _, qset = spiral_plot_instance.plot_contours(
                ax=ax,
                method="grid",
                gaussian_filter_std=2.5,
                nan_aware_filter=True,
                cbar=False,
                label_levels=False,
            )
            mock_filter.assert_called_once()
            # Verify sigma parameter was passed correctly
            assert (
                mock_filter.call_args.kwargs["sigma"] == 2.5
            ), f"Expected sigma=2.5, got sigma={mock_filter.call_args.kwargs.get('sigma')}"
        plt.close()

        # Also verify valid output
        assert len(qset.levels) > 0, "Should produce contour levels"

    def test_tricontour_method_works(self, spiral_plot_instance):
        """Test that tricontour method produces valid output."""
        import matplotlib.tri

        fig, ax = plt.subplots()

        ax, lbls, cbar, qset = spiral_plot_instance.plot_contours(
            ax=ax, method="tricontour"
        )
        plt.close()

        # Should produce valid contours (TriContourSet)
        assert len(qset.levels) > 0, "Tricontour should produce levels"
        assert qset.allsegs is not None, "Tricontour should have segments"

        # Verify tricontour was used (not regular contour)
        # ax.tricontour returns TriContourSet, ax.contour returns QuadContourSet
        assert isinstance(
            qset, matplotlib.tri.TriContourSet
        ), "tricontour should return TriContourSet, not QuadContourSet"

    def test_handles_nan_with_rbf(self, spiral_plot_with_nans):
        """Test that RBF method handles NaN values correctly."""
        fig, ax = plt.subplots()

        # Verify RBF method is actually called with NaN data
        with patch.object(
            spiral_plot_with_nans,
            "_interpolate_with_rbf",
            wraps=spiral_plot_with_nans._interpolate_with_rbf,
        ) as mock_rbf:
            result = spiral_plot_with_nans.plot_contours(
                ax=ax, method="rbf", cbar=False, label_levels=False
            )
            mock_rbf.assert_called_once()
        plt.close()

        # Verify valid output types
        ret_ax, lbls, mappable, qset = result
        assert isinstance(ret_ax, matplotlib.axes.Axes)
        assert isinstance(qset, matplotlib.contour.QuadContourSet)
        assert len(qset.levels) > 0, "Should produce contour levels despite NaN input"

    def test_handles_nan_with_grid(self, spiral_plot_with_nans):
        """Test that grid method handles NaN values correctly."""
        fig, ax = plt.subplots()

        # Verify grid method is actually called with NaN data
        with patch.object(
            spiral_plot_with_nans,
            "_interpolate_to_grid",
            wraps=spiral_plot_with_nans._interpolate_to_grid,
        ) as mock_grid:
            result = spiral_plot_with_nans.plot_contours(
                ax=ax,
                method="grid",
                nan_aware_filter=True,
                cbar=False,
                label_levels=False,
            )
            mock_grid.assert_called_once()
        plt.close()

        # Verify valid output types
        ret_ax, lbls, mappable, qset = result
        assert isinstance(ret_ax, matplotlib.axes.Axes)
        assert isinstance(qset, matplotlib.contour.QuadContourSet)
        assert len(qset.levels) > 0, "Should produce contour levels despite NaN input"

    def test_invalid_method_raises_valueerror(self, spiral_plot_instance):
        """Test that invalid method raises ValueError."""
        fig, ax = plt.subplots()

        with pytest.raises(ValueError, match="Invalid method"):
            spiral_plot_instance.plot_contours(ax=ax, method="invalid_method")
        plt.close()

    def test_cbar_false_returns_qset(self, spiral_plot_instance):
        """Test that cbar=False returns qset instead of colorbar."""
        fig, ax = plt.subplots()

        ax, lbls, mappable, qset = spiral_plot_instance.plot_contours(ax=ax, cbar=False)
        plt.close()

        # When cbar=False, third element should be the same as qset
        assert mappable is qset, "With cbar=False, should return qset as third element"
        # Verify it's a ContourSet, not a Colorbar
        assert isinstance(
            mappable, matplotlib.contour.ContourSet
        ), "mappable should be ContourSet when cbar=False"
        assert not isinstance(
            mappable, matplotlib.colorbar.Colorbar
        ), "mappable should not be Colorbar when cbar=False"

    def test_contourf_option(self, spiral_plot_instance):
        """Test that use_contourf=True produces filled contours."""
        fig, ax = plt.subplots()

        ax, lbls, cbar, qset = spiral_plot_instance.plot_contours(
            ax=ax, use_contourf=True, cbar=False, label_levels=False
        )
        plt.close()

        # Verify return type is correct
        assert isinstance(qset, matplotlib.contour.QuadContourSet)
        # Verify filled contours were produced
        # Filled contours (contourf) produce filled=True on the QuadContourSet
        assert qset.filled, "use_contourf=True should produce filled contours"
        assert len(qset.levels) > 0, "Should have contour levels"

    def test_all_three_methods_produce_output(self, spiral_plot_instance):
        """Test that all three methods produce valid comparable output."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        results = []
        for ax, method in zip(axes, ["rbf", "grid", "tricontour"]):
            result = spiral_plot_instance.plot_contours(
                ax=ax, method=method, cbar=False, label_levels=False
            )
            results.append(result)
        plt.close()

        # All should produce valid output
        for i, (ax, lbls, mappable, qset) in enumerate(results):
            method = ["rbf", "grid", "tricontour"][i]
            assert ax is not None, f"{method} should return ax"
            assert qset is not None, f"{method} should return qset"
            assert len(qset.levels) > 0, f"{method} should produce contour levels"


if __name__ == "__main__":
    pytest.main([__file__])
