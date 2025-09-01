#!/usr/bin/env python
"""Tests for solarwindpy.plotting.scatter module.

This module provides comprehensive test coverage for the Scatter class used for creating
scatter plots with optional color mapping functionality.
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from matplotlib import pyplot as plt
from matplotlib.collections import PathCollection

import solarwindpy.plotting.scatter as scatter_module
from solarwindpy.plotting.scatter import Scatter
from solarwindpy.plotting.base import PlotWithZdata, CbarMaker, AxesLabels, LogAxes


class TestScatterModuleStructure:
    """Test scatter module structure and imports."""

    def test_module_imports(self):
        """Test that all required imports are accessible."""
        # Test basic imports
        assert hasattr(scatter_module, "base")
        assert hasattr(scatter_module, "plt")
        assert hasattr(scatter_module, "Scatter")

    def test_scatter_class_available(self):
        """Test that Scatter class is accessible from module."""
        assert hasattr(scatter_module, "Scatter")
        assert callable(scatter_module.Scatter)

    def test_scatter_inheritance(self):
        """Test that Scatter inherits from correct base classes."""
        assert issubclass(Scatter, PlotWithZdata)
        assert issubclass(Scatter, CbarMaker)

        # Test MRO (Method Resolution Order)
        mro = Scatter.__mro__
        assert PlotWithZdata in mro
        assert CbarMaker in mro


class TestScatterInitialization:
    """Test Scatter class initialization."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    def test_basic_initialization(self):
        """Test basic initialization with x, y data only."""
        scatter = Scatter(self.x_data, self.y_data)

        assert scatter is not None
        assert hasattr(scatter, "data")
        assert hasattr(scatter, "_labels")
        assert hasattr(scatter, "_log")
        assert hasattr(scatter, "clip")

    def test_initialization_with_z_data(self):
        """Test initialization with z data for color mapping."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        assert scatter is not None
        assert "z" in scatter.data.columns
        assert scatter._labels.z == "z"

    def test_initialization_with_clip_data_true(self):
        """Test initialization with clip_data=True."""
        scatter = Scatter(self.x_data, self.y_data, clip_data=True)

        assert scatter.clip is True

    def test_initialization_with_clip_data_false(self):
        """Test initialization with clip_data=False."""
        scatter = Scatter(self.x_data, self.y_data, clip_data=False)

        assert scatter.clip is False

    def test_labels_initialization(self):
        """Test that labels are properly initialized."""
        # Without z data
        scatter = Scatter(self.x_data, self.y_data)
        assert scatter._labels.x == "x"
        assert scatter._labels.y == "y"
        assert scatter._labels.z is None

        # With z data
        scatter_z = Scatter(self.x_data, self.y_data, self.z_data)
        assert scatter_z._labels.x == "x"
        assert scatter_z._labels.y == "y"
        assert scatter_z._labels.z == "z"

    def test_log_initialization(self):
        """Test that log axes are properly initialized."""
        scatter = Scatter(self.x_data, self.y_data)

        assert hasattr(scatter, "_log")
        assert scatter._log.x is False
        assert scatter._log.y is False

    def test_path_initialization(self):
        """Test that path is initialized to None."""
        scatter = Scatter(self.x_data, self.y_data)

        assert hasattr(scatter, "_path")

    def test_invalid_input_types(self):
        """Test behavior with non-pandas Series inputs."""
        # Lists are actually converted to Series internally
        scatter = Scatter([1, 2, 3], self.y_data[:3])
        assert len(scatter.data) == 3

        # Both as lists
        scatter2 = Scatter([1, 2, 3], [4, 5, 6])
        assert len(scatter2.data) == 3

    def test_empty_data_handling(self):
        """Test behavior with empty pandas Series."""
        empty_x = pd.Series([], dtype=float)
        empty_y = pd.Series([], dtype=float)

        with pytest.raises(ValueError, match="exclusively NaNs"):
            Scatter(empty_x, empty_y)

    def test_mismatched_data_lengths(self):
        """Test error handling for different length x, y, z."""
        short_data = pd.Series([1, 2])

        # This should work - pandas will align indices
        scatter = Scatter(short_data, self.y_data)
        assert len(scatter.data) == 2  # Should keep only aligned data

    def test_nan_data_handling(self):
        """Test handling of NaN values in data."""
        x_with_nan = pd.Series([1, 2, np.nan, 4, 5])
        y_with_nan = pd.Series([2, np.nan, 6, 8, 10])

        scatter = Scatter(x_with_nan, y_with_nan)

        # NaN rows should be dropped
        assert not scatter.data.isnull().any().any()
        assert len(scatter.data) < 5


class TestScatterDataManagement:
    """Test data management methods and properties."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    def test_set_data_method(self):
        """Test the set_data method."""
        scatter = Scatter(self.x_data, self.y_data)

        # Test basic data assignment
        assert "x" in scatter.data.columns
        assert "y" in scatter.data.columns
        assert "z" in scatter.data.columns  # Should be filled with 1s

    def test_set_data_with_z(self):
        """Test set_data with z data."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        assert "z" in scatter.data.columns
        assert not (scatter.data["z"] == 1).all()  # Should not be all 1s

    def test_data_property_access(self):
        """Test access to stored data via properties."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        data = scatter.data
        assert isinstance(data, pd.DataFrame)
        assert "x" in data.columns
        assert "y" in data.columns
        assert "z" in data.columns

    def test_data_integrity(self):
        """Test that data remains unchanged after storage."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # Check that original values are preserved
        np.testing.assert_array_equal(scatter.data["x"].values, self.x_data.values)
        np.testing.assert_array_equal(scatter.data["y"].values, self.y_data.values)
        np.testing.assert_array_equal(scatter.data["z"].values, self.z_data.values)

    def test_clip_property(self):
        """Test the clip property."""
        scatter_no_clip = Scatter(self.x_data, self.y_data, clip_data=False)
        scatter_with_clip = Scatter(self.x_data, self.y_data, clip_data=True)

        assert scatter_no_clip.clip is False
        assert scatter_with_clip.clip is True


class TestScatterLabelsAndAxes:
    """Test label and axis configuration."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    def test_default_labels(self):
        """Test that default labels are set correctly."""
        scatter = Scatter(self.x_data, self.y_data)

        assert scatter._labels.x == "x"
        assert scatter._labels.y == "y"
        assert scatter._labels.z is None

    def test_labels_with_z_data(self):
        """Test labels when z data is provided."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        assert scatter._labels.x == "x"
        assert scatter._labels.y == "y"
        assert scatter._labels.z == "z"

    def test_label_customization(self):
        """Test updating axis labels via namedtuple replacement."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # AxesLabels is a namedtuple, so we need to replace it entirely
        original_labels = scatter._labels
        new_labels = scatter._labels._replace(x="Custom X", y="Custom Y", z="Custom Z")
        scatter._labels = new_labels

        assert scatter._labels.x == "Custom X"
        assert scatter._labels.y == "Custom Y"
        assert scatter._labels.z == "Custom Z"

    def test_label_persistence(self):
        """Test that labels maintain values across operations."""
        scatter = Scatter(self.x_data, self.y_data)

        original_x = scatter._labels.x
        original_y = scatter._labels.y

        # Perform some operation (access data)
        _ = scatter.data

        # Labels should persist
        assert scatter._labels.x == original_x
        assert scatter._labels.y == original_y

    def test_log_scale_defaults(self):
        """Test default log scale settings."""
        scatter = Scatter(self.x_data, self.y_data)

        assert scatter._log.x is False
        assert scatter._log.y is False

    def test_log_scale_configuration(self):
        """Test setting logarithmic scales via namedtuple replacement."""
        scatter = Scatter(self.x_data, self.y_data)

        # LogAxes is a namedtuple, so we need to replace it entirely
        new_log = scatter._log._replace(x=True, y=True)
        scatter._log = new_log

        assert scatter._log.x is True
        assert scatter._log.y is True


class TestScatterPlotGeneration:
    """Test plot generation and matplotlib integration."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    @patch("matplotlib.pyplot.subplots")
    def test_make_plot_basic(self, mock_subplots):
        """Test basic scatter plot generation."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data)
        ax, cbar = scatter.make_plot()

        # Verify scatter plot was called
        mock_ax.scatter.assert_called_once()
        assert ax == mock_ax
        assert cbar is None  # No colorbar for 2D plot

    @patch("matplotlib.pyplot.subplots")
    def test_make_plot_with_z_data(self, mock_subplots):
        """Test scatter plot generation with z data."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # Mock the _make_cbar method
        with patch.object(scatter, "_make_cbar") as mock_make_cbar:
            mock_cbar = MagicMock()
            mock_make_cbar.return_value = mock_cbar

            ax, cbar = scatter.make_plot()

            # Verify scatter plot was called
            mock_ax.scatter.assert_called_once()
            # Verify colorbar was created
            mock_make_cbar.assert_called_once()
            assert ax == mock_ax
            assert cbar == mock_cbar

    @patch("matplotlib.pyplot.subplots")
    def test_make_plot_with_provided_ax(self, mock_subplots):
        """Test plot generation with provided axes."""
        # Setup mock
        provided_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        provided_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data)
        ax, cbar = scatter.make_plot(ax=provided_ax)

        # Should not create new subplot
        mock_subplots.assert_not_called()
        # Should use provided axes
        provided_ax.scatter.assert_called_once()
        assert ax == provided_ax

    @patch("matplotlib.pyplot.subplots")
    def test_make_plot_no_colorbar(self, mock_subplots):
        """Test plot generation with colorbar disabled."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.z_data)
        ax, cbar = scatter.make_plot(cbar=False)

        assert cbar is None

    @patch("matplotlib.pyplot.subplots")
    def test_make_plot_kwargs_passed(self, mock_subplots):
        """Test that kwargs are passed to ax.scatter."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data)
        scatter.make_plot(s=50, alpha=0.7, marker="s")

        # Check that kwargs were passed
        call_args = mock_ax.scatter.call_args
        assert "s" in call_args.kwargs
        assert "alpha" in call_args.kwargs
        assert "marker" in call_args.kwargs
        assert call_args.kwargs["s"] == 50
        assert call_args.kwargs["alpha"] == 0.7
        assert call_args.kwargs["marker"] == "s"

    def test_format_axis_method(self):
        """Test the _format_axis method."""
        scatter = Scatter(self.x_data, self.y_data)

        # Setup mock axes and collection
        mock_ax = MagicMock()
        mock_collection = MagicMock()
        mock_collection.sticky_edges.x = [0, 0]
        mock_collection.sticky_edges.y = [0, 0]

        # Test the method
        scatter._format_axis(mock_ax, mock_collection)

        # Verify axes methods were called
        mock_ax.update_datalim.assert_called_once()
        mock_ax.autoscale_view.assert_called_once()

        # Verify sticky edges were set
        assert mock_collection.sticky_edges.x[0] == self.x_data.min()
        assert mock_collection.sticky_edges.x[1] == self.x_data.max()
        assert mock_collection.sticky_edges.y[0] == self.y_data.min()
        assert mock_collection.sticky_edges.y[1] == self.y_data.max()


class TestScatterColorMapping:
    """Test color mapping and colorbar functionality."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")
        self.uniform_z = pd.Series([5, 5, 5, 5, 5], name="uniform_z")

    @patch("matplotlib.pyplot.subplots")
    def test_colorbar_creation_with_z_data(self, mock_subplots):
        """Test colorbar creation when z data is provided."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        with patch.object(scatter, "_make_cbar") as mock_make_cbar:
            mock_cbar = MagicMock()
            mock_make_cbar.return_value = mock_cbar

            ax, cbar = scatter.make_plot(cbar=True)

            mock_make_cbar.assert_called_once()
            assert cbar == mock_cbar

    @patch("matplotlib.pyplot.subplots")
    def test_no_colorbar_with_uniform_z(self, mock_subplots):
        """Test no colorbar when z data is uniform."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.uniform_z)
        ax, cbar = scatter.make_plot()

        # No colorbar should be created for uniform z data
        assert cbar is None

    @patch("matplotlib.pyplot.subplots")
    def test_colorbar_kwargs_passed(self, mock_subplots):
        """Test that colorbar kwargs are passed correctly."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        cbar_kwargs = {"orientation": "horizontal", "shrink": 0.8}

        with patch.object(scatter, "_make_cbar") as mock_make_cbar:
            mock_cbar = MagicMock()
            mock_make_cbar.return_value = mock_cbar

            scatter.make_plot(cbar_kwargs=cbar_kwargs)

            # Check that kwargs were passed
            call_args = mock_make_cbar.call_args
            assert "orientation" in call_args.kwargs
            assert "shrink" in call_args.kwargs


class TestScatterInheritance:
    """Test integration with base classes."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    def test_plot_with_z_data_inheritance(self):
        """Test inheritance from PlotWithZdata."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # Should have PlotWithZdata methods and properties
        assert hasattr(scatter, "data")
        assert hasattr(scatter, "clip")
        assert hasattr(scatter, "set_data")

        # Test inherited functionality
        assert isinstance(scatter.data, pd.DataFrame)
        assert isinstance(scatter.clip, bool)

    def test_cbar_maker_inheritance(self):
        """Test inheritance from CbarMaker."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # Should have CbarMaker methods
        assert hasattr(scatter, "_make_cbar")

        # Test that _make_cbar is callable
        assert callable(scatter._make_cbar)

    def test_base_class_properties_accessible(self):
        """Test that base class properties are accessible."""
        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        # Should have Base class properties
        assert hasattr(scatter, "labels")
        assert hasattr(scatter, "log")

        # Test property access
        labels = scatter.labels
        log_settings = scatter.log
        assert labels is not None
        assert log_settings is not None


class TestScatterErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    def test_invalid_data_types(self):
        """Test handling of non-pandas Series data types."""
        # Lists are actually converted to Series internally
        scatter1 = Scatter([1, 2, 3], self.y_data[:3])
        assert len(scatter1.data) == 3

        scatter2 = Scatter(self.x_data[:3], [4, 5, 6])
        assert len(scatter2.data) == 3

        scatter3 = Scatter(self.x_data, self.y_data, [7, 8, 9, 10, 11])
        assert len(scatter3.data) == 5

    def test_nan_inf_handling(self):
        """Test handling of NaN and infinite values."""
        x_with_inf = pd.Series([1, 2, np.inf, 4, 5])
        y_with_nan = pd.Series([2, np.nan, 6, 8, 10])

        # NaN rows are dropped, but inf values may remain
        scatter = Scatter(x_with_inf, y_with_nan)

        # Check that NaN values are removed
        assert not scatter.data.isnull().any().any()

        # Inf values might remain in the data (this is the actual behavior)
        assert len(scatter.data) == 4  # Row with NaN is dropped

    def test_missing_data(self):
        """Test behavior with incomplete data."""
        # Test with missing indices
        x_missing = pd.Series([1, 3, 5], index=[0, 2, 4])
        y_missing = pd.Series([2, 6, 10], index=[0, 2, 4])

        scatter = Scatter(x_missing, y_missing)

        # Should handle missing indices correctly
        assert len(scatter.data) == 3
        assert list(scatter.data.index) == [0, 2, 4]

    def test_single_point_data(self):
        """Test handling of single data point."""
        single_x = pd.Series([1])
        single_y = pd.Series([2])

        scatter = Scatter(single_x, single_y)

        assert len(scatter.data) == 1
        assert scatter.data.iloc[0]["x"] == 1
        assert scatter.data.iloc[0]["y"] == 2

    def test_negative_values_with_log(self):
        """Test behavior with negative values when log scale is set."""
        negative_x = pd.Series([-1, -2, -3])
        positive_y = pd.Series([1, 2, 3])

        scatter = Scatter(negative_x, positive_y)
        # Set log scale using namedtuple replacement
        new_log = scatter._log._replace(x=True)
        scatter._log = new_log

        # This should not raise an error during initialization
        # The error would occur during plotting, which matplotlib handles
        assert scatter._log.x is True

    def test_empty_data_after_processing(self):
        """Test handling when data becomes empty after processing."""
        # Create data that becomes empty after NaN removal
        all_nan_x = pd.Series([np.nan, np.nan, np.nan])
        all_nan_y = pd.Series([np.nan, np.nan, np.nan])

        with pytest.raises(ValueError, match="exclusively NaNs"):
            Scatter(all_nan_x, all_nan_y)


class TestScatterPerformanceAndMemory:
    """Test performance and memory usage."""

    def test_large_datasets(self):
        """Test performance with large datasets."""
        # Create large dataset
        n_points = 10000
        large_x = pd.Series(np.random.randn(n_points))
        large_y = pd.Series(np.random.randn(n_points))
        large_z = pd.Series(np.random.randn(n_points))

        # Should handle large datasets without issues
        scatter = Scatter(large_x, large_y, large_z)

        assert len(scatter.data) == n_points
        assert "x" in scatter.data.columns
        assert "y" in scatter.data.columns
        assert "z" in scatter.data.columns

    def test_memory_usage(self):
        """Test efficient memory usage."""
        scatter = Scatter(self.x_data, self.y_data)

        # Data should be stored efficiently
        data_memory = scatter.data.memory_usage(deep=True).sum()
        assert data_memory > 0  # Should use some memory

        # Should not create excessive copies
        original_data = scatter.data
        accessed_data = scatter.data
        assert original_data is accessed_data  # Should be same object

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")


class TestScatterDocumentation:
    """Test documentation and examples."""

    def test_class_docstring_exists(self):
        """Test that class has docstring."""
        assert Scatter.__doc__ is not None
        assert len(Scatter.__doc__.strip()) > 0

    def test_init_docstring_exists(self):
        """Test that __init__ method has docstring."""
        assert Scatter.__init__.__doc__ is not None
        assert len(Scatter.__init__.__doc__.strip()) > 0

    def test_make_plot_docstring_exists(self):
        """Test that make_plot method has docstring."""
        assert Scatter.make_plot.__doc__ is not None
        assert len(Scatter.make_plot.__doc__.strip()) > 0

    def test_docstring_parameter_documentation(self):
        """Test that parameters are documented in docstrings."""
        init_doc = Scatter.__init__.__doc__

        # Check that key parameters are documented
        assert "x" in init_doc
        assert "y" in init_doc
        assert "z" in init_doc
        assert "clip_data" in init_doc

        make_plot_doc = Scatter.make_plot.__doc__
        assert "ax" in make_plot_doc
        assert "cbar" in make_plot_doc


class TestScatterIntegration:
    """Integration tests for full scatter plot workflow."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.x_data = pd.Series([1, 2, 3, 4, 5], name="x_values")
        self.y_data = pd.Series([2, 4, 6, 8, 10], name="y_values")
        self.z_data = pd.Series([10, 20, 30, 40, 50], name="z_values")

    @patch("matplotlib.pyplot.subplots")
    def test_full_workflow_2d(self, mock_subplots):
        """Test complete workflow for 2D scatter plot."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        # Create scatter plot
        scatter = Scatter(self.x_data, self.y_data)

        # Customize labels using namedtuple replacement
        new_labels = scatter._labels._replace(x="X Values", y="Y Values")
        scatter._labels = new_labels

        # Generate plot
        ax, cbar = scatter.make_plot()

        # Verify workflow
        assert ax is not None
        assert cbar is None
        mock_ax.scatter.assert_called_once()

    @patch("matplotlib.pyplot.subplots")
    def test_full_workflow_3d_with_colorbar(self, mock_subplots):
        """Test complete workflow for 3D scatter plot with colorbar."""
        # Setup mock
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_collection = MagicMock(spec=PathCollection)
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_ax.scatter.return_value = mock_collection

        scatter = Scatter(self.x_data, self.y_data, self.z_data)

        with patch.object(scatter, "_make_cbar") as mock_make_cbar:
            mock_cbar = MagicMock()
            mock_make_cbar.return_value = mock_cbar

            # Customize labels using namedtuple replacement
            new_labels = scatter._labels._replace(
                x="X Values", y="Y Values", z="Color Values"
            )
            scatter._labels = new_labels

            # Generate plot with colorbar
            ax, cbar = scatter.make_plot(cbar=True)

            # Verify workflow
            assert ax is not None
            assert cbar is not None
            mock_ax.scatter.assert_called_once()
            mock_make_cbar.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
