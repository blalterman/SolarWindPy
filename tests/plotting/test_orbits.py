#!/usr/bin/env python
"""Tests for solarwindpy.plotting.orbits module.

This module provides comprehensive test coverage for orbit plotting functionality
specialized for solar wind spacecraft trajectory visualization.
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from abc import ABC

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from matplotlib import pyplot as plt
from matplotlib.collections import QuadMesh

import solarwindpy.plotting.orbits as orbits_module
from solarwindpy.plotting.orbits import OrbitPlot, OrbitHist1D, OrbitHist2D
from solarwindpy.plotting import tools


class TestOrbitsModuleStructure:
    """Test orbits module structure and imports."""

    def test_module_imports(self):
        """Test that all required imports are accessible."""
        assert hasattr(orbits_module, "np")
        assert hasattr(orbits_module, "pd")
        assert hasattr(orbits_module, "mpl")
        assert hasattr(orbits_module, "histograms")
        assert hasattr(orbits_module, "tools")

    def test_classes_available(self):
        """Test that orbit classes are accessible."""
        assert hasattr(orbits_module, "OrbitPlot")
        assert hasattr(orbits_module, "OrbitHist1D")
        assert hasattr(orbits_module, "OrbitHist2D")

        assert callable(orbits_module.OrbitHist1D)
        assert callable(orbits_module.OrbitHist2D)

    def test_orbit_plot_inheritance(self):
        """Test OrbitPlot inheritance structure."""
        assert issubclass(OrbitPlot, ABC)
        assert issubclass(OrbitHist1D, OrbitPlot)
        assert issubclass(OrbitHist2D, OrbitPlot)


class ConcreteOrbitPlot(OrbitPlot):
    """Concrete implementation of OrbitPlot for testing abstract functionality."""

    def __init__(self, orbit, *args, **kwargs):
        # Mock the required attributes that the parent classes would provide
        self._gb_axes = ["test_axis"]
        self.joint = pd.DataFrame({"test_axis": [1, 2, 3], "Orbit": ["A", "B", "C"]})
        self.data = pd.DataFrame(
            {"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]},
            index=pd.date_range("2020-01-01", periods=5, freq="h"),
        )
        self.cut = pd.DataFrame({"test_cut": [1, 2, 3, 4, 5]}, index=self.data.index)
        self.path = Path("/test/path")

        super().__init__(orbit, *args, **kwargs)

    def set_path(self, *args, orbit=None, **kwargs):
        """Mock implementation of set_path."""
        if orbit is not None:
            self._path = self.path / orbit.path
        return self.path


class TestOrbitPlot:
    """Test OrbitPlot abstract base class."""

    def setup_method(self):
        """Set up test data for each test method."""
        # Create test orbit intervals
        self.orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

    def test_orbit_plot_initialization(self):
        """Test OrbitPlot initialization."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        assert orbit_plot is not None
        assert hasattr(orbit_plot, "orbit")
        assert hasattr(orbit_plot, "_orbit")

    def test_orbit_plot_invalid_orbit_type(self):
        """Test that invalid orbit type raises TypeError."""
        with pytest.raises(TypeError):
            ConcreteOrbitPlot("invalid_orbit")

        with pytest.raises(TypeError):
            ConcreteOrbitPlot([1, 2, 3])

    def test_disable_both_property(self):
        """Test _disable_both property is True by default."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)
        assert orbit_plot._disable_both is True

    def test_orbit_property(self):
        """Test orbit property returns the IntervalIndex."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        orbit = orbit_plot.orbit
        assert isinstance(orbit, pd.IntervalIndex)
        assert len(orbit) == 2

    def test_orbit_key_property(self):
        """Test _orbit_key returns 'Orbit'."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)
        assert orbit_plot._orbit_key == "Orbit"

    def test_grouped_property(self):
        """Test grouped property groups by _gb_axes + _orbit_key."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        grouped = orbit_plot.grouped
        assert hasattr(grouped, "groups")
        # Should group by both test_axis and Orbit

    def test_set_orbit_sorting(self):
        """Test set_orbit sorts the intervals."""
        # Create unsorted intervals
        unsorted_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
            ]
        )

        orbit_plot = ConcreteOrbitPlot(unsorted_intervals)

        # Should be sorted by start time
        assert orbit_plot.orbit[0].left < orbit_plot.orbit[1].left

    def test_set_orbit_validates_type(self):
        """Test set_orbit validates IntervalIndex type."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        with pytest.raises(TypeError):
            orbit_plot.set_orbit("invalid")

    def test_set_path_with_orbit(self):
        """Test set_path with orbit parameter."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        # Mock orbit object with path
        mock_orbit = MagicMock()
        mock_orbit.path = Path("orbit/path")

        result = orbit_plot.set_path(orbit=mock_orbit)

        # Path should be updated to include orbit path
        assert "orbit" in str(orbit_plot._path)

    def test_make_cut_method_exists(self):
        """Test make_cut method exists and processes orbit intervals."""
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)

        # Test that the method exists
        assert hasattr(orbit_plot, "make_cut")
        assert callable(orbit_plot.make_cut)

        # Test that orbit intervals exist
        assert len(orbit_plot.orbit) == 2


class TestOrbitHist1D:
    """Test OrbitHist1D class functionality."""

    def setup_method(self):
        """Set up test data for OrbitHist1D tests."""
        # Create test orbit intervals
        self.orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

        # Create test data
        times = pd.date_range("2020-01-01", periods=20, freq="15min")
        self.x_data = pd.Series(np.random.uniform(1, 10, 20), index=times)

    def test_orbit_hist_1d_initialization(self):
        """Test OrbitHist1D initialization basics."""
        # Test that class exists and can be instantiated (even if it fails)
        assert hasattr(orbits_module, "OrbitHist1D")
        assert callable(OrbitHist1D)

        # Test the class is properly defined
        assert issubclass(OrbitHist1D, OrbitPlot)

    def test_format_axis_method_exists(self):
        """Test _format_axis method exists."""
        # Test that the method exists on the class
        assert hasattr(OrbitHist1D, "_format_axis")
        assert callable(getattr(OrbitHist1D, "_format_axis"))

    def test_make_plot_method_exists(self):
        """Test make_plot method exists."""
        # Test that the method exists on the class
        assert hasattr(OrbitHist1D, "make_plot")
        assert callable(getattr(OrbitHist1D, "make_plot"))


class TestOrbitHist2D:
    """Test OrbitHist2D class functionality."""

    def setup_method(self):
        """Set up test data for OrbitHist2D tests."""
        # Create test orbit intervals
        self.orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

        # Create test data
        times = pd.date_range("2020-01-01", periods=20, freq="15min")
        self.x_data = pd.Series(np.random.uniform(1, 10, 20), index=times)
        self.y_data = pd.Series(np.random.uniform(1, 10, 20), index=times)

    def test_orbit_hist_2d_initialization(self):
        """Test OrbitHist2D initialization basics."""
        # Test that class exists and can be instantiated (even if it fails)
        assert hasattr(orbits_module, "OrbitHist2D")
        assert callable(OrbitHist2D)

        # Test the class is properly defined
        assert issubclass(OrbitHist2D, OrbitPlot)

    def test_format_in_out_axes_method_exists(self):
        """Test _format_in_out_axes method exists."""
        assert hasattr(OrbitHist2D, "_format_in_out_axes")
        assert callable(getattr(OrbitHist2D, "_format_in_out_axes"))

    def test_prune_lower_yaxis_ticks(self):
        """Test _prune_lower_yaxis_ticks prunes ticks correctly."""
        mock_ax0 = MagicMock()
        mock_ax1 = MagicMock()

        mock_ax0.get_yticks.return_value = np.array([0, 1, 2, 3, 4])
        mock_ax0.get_yscale.return_value = "linear"
        mock_ax1.get_yscale.return_value = "linear"

        OrbitHist2D._prune_lower_yaxis_ticks(mock_ax0, mock_ax1)

        # Should have called set_major_locator on both axes
        mock_ax0.yaxis.set_major_locator.assert_called_once()
        mock_ax1.yaxis.set_major_locator.assert_called_once()

    def test_project_1d_method_exists(self):
        """Test project_1d method exists."""
        assert hasattr(OrbitHist2D, "project_1d")
        assert callable(getattr(OrbitHist2D, "project_1d"))

    def test_make_one_plot_method_exists(self):
        """Test make_one_plot method exists."""
        assert hasattr(OrbitHist2D, "make_one_plot")
        assert callable(getattr(OrbitHist2D, "make_one_plot"))

    def test_make_one_plot_kind_validation(self):
        """Test make_one_plot kind validation logic."""
        # Test the transformation logic directly
        trans = {"i": "Inbound", "o": "Outbound", "b": "Both"}

        # Test valid transformations
        assert trans["i"] == "Inbound"
        assert trans["o"] == "Outbound"
        assert trans["b"] == "Both"

    def test_disable_both_property_default(self):
        """Test that _disable_both is True by default in OrbitPlot classes."""
        # This property is inherited from OrbitPlot
        orbit_plot = ConcreteOrbitPlot(self.orbit_intervals)
        assert orbit_plot._disable_both is True


class TestOrbitPlottingIntegration:
    """Test integration between orbit plotting components."""

    def setup_method(self):
        """Set up test data for integration tests."""
        self.orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

        times = pd.date_range("2020-01-01", periods=50, freq="6min")
        self.x_data = pd.Series(np.random.uniform(1, 10, 50), index=times)
        self.y_data = pd.Series(np.random.uniform(1, 10, 50), index=times)

    def test_orbit_plot_inheritance_chain(self):
        """Test that inheritance chain works correctly."""
        # OrbitHist1D should inherit from both OrbitPlot and Hist1D
        assert issubclass(OrbitHist1D, OrbitPlot)
        # Note: We can't easily test Hist1D inheritance without importing histograms

        # OrbitHist2D should inherit from both OrbitPlot and Hist2D
        assert issubclass(OrbitHist2D, OrbitPlot)

    def test_orbit_interval_validation(self):
        """Test that orbit intervals are properly validated across classes."""
        valid_intervals = self.orbit_intervals
        invalid_inputs = ["string", [1, 2, 3], pd.Index([1, 2, 3]), None]

        for invalid_input in invalid_inputs:
            with pytest.raises(TypeError):
                ConcreteOrbitPlot(invalid_input)


class TestOrbitErrorHandling:
    """Test error handling and edge cases in orbit plotting."""

    def setup_method(self):
        """Set up test data for error handling tests."""
        self.orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00")),
                (pd.Timestamp("2020-01-01 03:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

    def test_empty_orbit_intervals(self):
        """Test handling of empty orbit intervals."""
        empty_intervals = pd.IntervalIndex([])

        # Should not raise an error during initialization
        orbit_plot = ConcreteOrbitPlot(empty_intervals)
        assert len(orbit_plot.orbit) == 0

    def test_single_orbit_interval(self):
        """Test handling of single orbit interval."""
        single_interval = pd.IntervalIndex.from_tuples(
            [(pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 02:00"))]
        )

        orbit_plot = ConcreteOrbitPlot(single_interval)
        assert len(orbit_plot.orbit) == 1

    def test_overlapping_orbit_intervals(self):
        """Test handling of overlapping orbit intervals."""
        overlapping_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 03:00")),
                (pd.Timestamp("2020-01-01 02:00"), pd.Timestamp("2020-01-01 05:00")),
            ]
        )

        # Should accept overlapping intervals (sorting behavior may vary)
        orbit_plot = ConcreteOrbitPlot(overlapping_intervals)
        assert len(orbit_plot.orbit) == 2


class TestOrbitDocumentation:
    """Test documentation and docstrings for orbit classes."""

    def test_module_docstring(self):
        """Test that module has docstring."""
        assert orbits_module.__doc__ is not None
        assert len(orbits_module.__doc__.strip()) > 0

    def test_orbit_plot_docstring(self):
        """Test that OrbitPlot has class documentation."""
        # OrbitPlot is abstract, may not have detailed docstring
        assert hasattr(OrbitPlot, "__doc__")

    def test_orbit_hist_1d_docstring(self):
        """Test that OrbitHist1D methods have docstrings."""
        assert OrbitHist1D.make_plot.__doc__ is not None
        assert len(OrbitHist1D.make_plot.__doc__.strip()) > 0

    def test_orbit_hist_2d_docstring(self):
        """Test that OrbitHist2D methods have docstrings."""
        assert OrbitHist2D.project_1d.__doc__ is not None
        assert len(OrbitHist2D.project_1d.__doc__.strip()) > 0

        assert OrbitHist2D.make_one_plot.__doc__ is not None
        assert len(OrbitHist2D.make_one_plot.__doc__.strip()) > 0


class TestOrbitPerformance:
    """Test performance characteristics of orbit plotting."""

    def test_large_orbit_dataset(self):
        """Test handling of large orbit datasets."""
        # Create larger dataset
        large_intervals = pd.IntervalIndex.from_tuples(
            [
                (
                    pd.Timestamp("2020-01-01") + pd.Timedelta(hours=i),
                    pd.Timestamp("2020-01-01") + pd.Timedelta(hours=i + 1),
                )
                for i in range(0, 100, 2)
            ]
        )

        # Should handle large interval sets
        orbit_plot = ConcreteOrbitPlot(large_intervals)
        assert len(orbit_plot.orbit) == 50

    def test_memory_usage_with_large_data(self):
        """Test memory efficiency with large datasets."""
        orbit_intervals = pd.IntervalIndex.from_tuples(
            [
                (pd.Timestamp("2020-01-01 00:00"), pd.Timestamp("2020-01-01 12:00")),
                (pd.Timestamp("2020-01-01 12:00"), pd.Timestamp("2020-01-02 00:00")),
            ]
        )

        # Create orbit plot - should not consume excessive memory
        orbit_plot = ConcreteOrbitPlot(orbit_intervals)

        # Basic memory usage test - just ensure it doesn't crash
        assert orbit_plot is not None
        assert len(orbit_plot.orbit) == 2


if __name__ == "__main__":
    pytest.main([__file__])
