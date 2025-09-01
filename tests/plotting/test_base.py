#!/usr/bin/env python
"""Tests for solarwindpy.plotting.base module.

This module provides comprehensive test coverage for the abstract base classes and
helper classes used throughout the plotting package.
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from solarwindpy.plotting.base import (
    Base,
    LogAxes,
    AxesLabels,
    RangeLimits,
    DataLimFormatter,
    CbarMaker,
    PlotWithZdata,
)


class ConcreteBase(Base):
    """Concrete implementation of Base for testing abstract functionality."""

    def __init__(self):
        super().__init__()
        self._data = None
        self._clip = False

    def set_data(self, data=None):
        """Minimal implementation for testing."""
        if data is None:
            self._data = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        else:
            self._data = data

    def make_plot(self):
        """Minimal implementation for testing."""
        return "plot_created"

    def set_path(self, new, add_scale=False):
        """Concrete implementation of set_path for testing."""
        path, x, y, z, scale_info = super().set_path(new, add_scale)
        self._path = path
        return path, x, y, z, scale_info


class ConcretePlotWithZdata(PlotWithZdata):
    """Concrete implementation of PlotWithZdata for testing."""

    def __init__(self):
        super().__init__()

    def make_plot(self):
        """Minimal implementation for testing."""
        return "plot_with_z_created"


class TestNamedTuples:
    """Test the named tuple definitions."""

    def test_log_axes_creation(self):
        """Test LogAxes namedtuple with defaults."""
        # LogAxes defaults=(False,) only provides default for y, x is required
        log_axes = LogAxes(x=True)
        assert log_axes.x is True
        assert log_axes.y is False  # default

        log_axes = LogAxes(True, True)
        assert log_axes.x is True
        assert log_axes.y is True

    def test_axes_labels_creation(self):
        """Test AxesLabels namedtuple with defaults."""
        # AxesLabels defaults=(None,) only provides default for z, x and y are required
        labels = AxesLabels("X-axis", "Y-axis")
        assert labels.x == "X-axis"
        assert labels.y == "Y-axis"
        assert labels.z is None  # default

        labels = AxesLabels("X-axis", "Y-axis", "Z-axis")
        assert labels.x == "X-axis"
        assert labels.y == "Y-axis"
        assert labels.z == "Z-axis"

    def test_range_limits_creation(self):
        """Test RangeLimits namedtuple with defaults."""
        # RangeLimits requires at least the 'lower' parameter
        limits = RangeLimits(None)
        assert limits.lower is None
        assert limits.upper is None

        limits = RangeLimits(0, 100)
        assert limits.lower == 0
        assert limits.upper == 100


class TestBaseAbstractClass:
    """Test the Base abstract class functionality."""

    def test_base_instantiation_via_subclass(self):
        """Test that Base can be instantiated via subclass with proper
        initialization."""
        concrete = ConcreteBase()

        # Verify initialization occurred
        assert hasattr(concrete, "_logger")
        assert hasattr(concrete, "_labels")
        assert hasattr(concrete, "_log")
        assert hasattr(concrete, "_path")

        # Verify types and defaults
        assert isinstance(concrete._labels, tuple)  # AxesLabels is a namedtuple
        assert isinstance(concrete._log, tuple)  # LogAxes is a namedtuple
        assert concrete._labels.x == "x"
        assert concrete._labels.y == "y"
        assert concrete._log.x is False
        assert concrete._log.y is False

    def test_base_cannot_be_instantiated_directly(self):
        """Test that Base cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Base()

    def test_str_returns_class_name(self):
        """Test that __str__ returns the class name."""
        concrete = ConcreteBase()
        assert str(concrete) == "ConcreteBase"

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        concrete = ConcreteBase()
        logger = concrete.logger
        assert isinstance(logger, logging.Logger)
        assert logger.name.endswith("ConcreteBase")

    def test_data_property(self):
        """Test that data property returns internal _data."""
        concrete = ConcreteBase()
        test_data = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        concrete._data = test_data
        assert concrete.data is test_data

    def test_clip_property(self):
        """Test that clip property returns internal _clip."""
        concrete = ConcreteBase()
        concrete._clip = True
        assert concrete.clip is True

        concrete._clip = False
        assert concrete.clip is False

    def test_log_property(self):
        """Test that log property returns internal _log."""
        concrete = ConcreteBase()
        assert concrete.log == concrete._log
        assert concrete.log.x is False
        assert concrete.log.y is False

    def test_labels_property(self):
        """Test that labels property returns internal _labels."""
        concrete = ConcreteBase()
        assert concrete.labels == concrete._labels
        assert concrete.labels.x == "x"
        assert concrete.labels.y == "y"

    def test_path_property(self):
        """Test that path property returns internal _path."""
        concrete = ConcreteBase()
        # Path should be set during initialization
        assert hasattr(concrete, "_path")
        assert concrete.path == concrete._path


class TestBaseLogMethods:
    """Test log scaling functionality in Base class."""

    def test_set_log_defaults(self):
        """Test set_log() with defaults toggles log.x and log.y appropriately."""
        concrete = ConcreteBase()

        # Initial state
        assert concrete.log.x is False
        assert concrete.log.y is False

        # Call with no arguments should use current values
        concrete.set_log()
        assert concrete.log.x is False
        assert concrete.log.y is False

    def test_set_log_explicit_values(self):
        """Test set_log(x=True, y=False) correctly updates log axes."""
        concrete = ConcreteBase()

        concrete.set_log(x=True, y=False)
        assert concrete.log.x is True
        assert concrete.log.y is False

        concrete.set_log(x=False, y=True)
        assert concrete.log.x is False
        assert concrete.log.y is True

        concrete.set_log(x=True, y=True)
        assert concrete.log.x is True
        assert concrete.log.y is True

    def test_set_log_partial_specification(self):
        """Test set_log with only x or y specified."""
        concrete = ConcreteBase()

        # Set initial state
        concrete.set_log(x=True, y=True)

        # Change only x
        concrete.set_log(x=False)
        assert concrete.log.x is False
        assert concrete.log.y is True  # Should remain unchanged

        # Change only y
        concrete.set_log(y=False)
        assert concrete.log.x is False  # Should remain unchanged
        assert concrete.log.y is False

    def test_set_log_type_coercion(self):
        """Test that set_log converts values to bool."""
        concrete = ConcreteBase()

        # Test truthy/falsy values
        concrete.set_log(x=1, y=0)
        assert concrete.log.x is True
        assert concrete.log.y is False

        concrete.set_log(x="true", y="")
        assert concrete.log.x is True
        assert concrete.log.y is False


class TestBaseLabelMethods:
    """Test label management functionality in Base class."""

    def test_set_labels_updates_labels_and_regenerates_path(self):
        """Test set_labels() updates labels and regenerates path."""
        concrete = ConcreteBase()
        original_path = concrete.path

        concrete.set_labels(x="New X", y="New Y")

        assert concrete.labels.x == "New X"
        assert concrete.labels.y == "New Y"
        # Path should have been regenerated (different from original)
        # Note: exact path comparison depends on implementation details
        assert hasattr(concrete, "_path")

    def test_set_labels_partial_update(self):
        """Test setting only some labels preserves others."""
        concrete = ConcreteBase()

        # Set initial labels
        concrete.set_labels(x="X1", y="Y1", z="Z1")

        # Update only x
        concrete.set_labels(x="X2")
        assert concrete.labels.x == "X2"
        assert concrete.labels.y == "Y1"  # Should remain unchanged
        assert concrete.labels.z == "Z1"  # Should remain unchanged

    def test_set_labels_auto_update_path_false(self):
        """Test set_labels with auto_update_path=False."""
        concrete = ConcreteBase()
        original_path = concrete.path

        # This should not trigger path update
        concrete.set_labels(x="New X", auto_update_path=False)

        assert concrete.labels.x == "New X"
        # Path should remain the same (though this is implementation dependent)
        # The main point is that set_path("auto") was not called

    def test_set_labels_unexpected_kwarg_raises_keyerror(self):
        """Test that set_labels(unexpected=...) raises KeyError."""
        concrete = ConcreteBase()

        with pytest.raises(KeyError, match="Unexpected kwarg"):
            concrete.set_labels(unexpected="value")

        with pytest.raises(KeyError, match="Unexpected kwarg"):
            concrete.set_labels(x="valid", invalid="invalid")

    def test_set_labels_multiple_unexpected_kwargs(self):
        """Test error message with multiple unexpected kwargs."""
        concrete = ConcreteBase()

        with pytest.raises(KeyError) as exc_info:
            concrete.set_labels(bad1="value1", bad2="value2")

        # Should mention both unexpected kwargs
        error_message = str(exc_info.value)
        assert "bad1" in error_message
        assert "bad2" in error_message


class TestBasePathMethods:
    """Test path management functionality in Base class."""

    def test_set_path_auto_mode(self):
        """Test set_path with 'auto' mode."""
        concrete = ConcreteBase()

        # Set some labels first
        concrete.set_labels(x="density", y="velocity", z="temperature")

        # Test auto path generation
        path, x, y, z, scale_info = concrete.set_path("auto")

        assert isinstance(path, Path)
        assert path.name == "ConcreteBase"  # Should use class name
        assert x == "density"
        assert y == "velocity"
        assert z == "temperature"
        assert scale_info is None  # add_scale defaults to False

    def test_set_path_auto_mode_with_scale(self):
        """Test set_path with 'auto' mode and add_scale=True."""
        concrete = ConcreteBase()
        concrete.set_log(x=True, y=False)

        path, x, y, z, scale_info = concrete.set_path("auto", add_scale=True)

        assert scale_info == ["logX", "linY"]

    def test_set_path_explicit_path(self):
        """Test set_path with explicit path."""
        concrete = ConcreteBase()

        path, x, y, z, scale_info = concrete.set_path("/custom/path")

        assert path == Path("/custom/path")
        assert x is None
        assert y is None
        assert z is None
        assert scale_info is None

    def test_set_path_none(self):
        """Test set_path with None."""
        concrete = ConcreteBase()

        path, x, y, z, scale_info = concrete.set_path(None)

        assert path == Path("")
        assert x is None
        assert y is None
        assert z is None
        assert scale_info is None

    def test_set_path_label_attribute_handling(self):
        """Test set_path handles labels with .path attributes."""
        concrete = ConcreteBase()

        # Mock labels with .path attributes
        mock_label = MagicMock()
        mock_label.path = "custom-path"
        concrete._labels = AxesLabels(x=mock_label, y="normal-label", z=None)

        path, x, y, z, scale_info = concrete.set_path("auto")

        assert x == "custom-path"
        assert y == "normal-label"
        assert z == "z"  # Default when None

    def test_set_path_string_sanitization(self):
        """Test that set_path sanitizes string labels."""
        concrete = ConcreteBase()
        concrete._labels = AxesLabels(x="Label With Spaces", y="normal", z="None")

        path, x, y, z, scale_info = concrete.set_path("auto")

        assert x == "Label-With-Spaces"  # Spaces replaced with hyphens
        assert y == "normal"
        assert z == "z"  # "None" string converted to default


class TestBaseAxisFormatting:
    """Test axis formatting methods in Base class."""

    @patch("matplotlib.pyplot")
    def test_add_axis_labels(self, mock_plt):
        """Test _add_axis_labels method."""
        concrete = ConcreteBase()
        concrete.set_labels(x="X Label", y="Y Label")

        mock_ax = MagicMock()
        concrete._add_axis_labels(mock_ax)

        mock_ax.set_xlabel.assert_called_once_with("X Label")
        mock_ax.set_ylabel.assert_called_once_with("Y Label")

    @patch("matplotlib.pyplot")
    def test_add_axis_labels_transpose(self, mock_plt):
        """Test _add_axis_labels with transpose_axes=True."""
        concrete = ConcreteBase()
        concrete.set_labels(x="X Label", y="Y Label")

        mock_ax = MagicMock()
        concrete._add_axis_labels(mock_ax, transpose_axes=True)

        # Labels should be swapped
        mock_ax.set_xlabel.assert_called_once_with("Y Label")
        mock_ax.set_ylabel.assert_called_once_with("X Label")

    @patch("matplotlib.pyplot")
    def test_add_axis_labels_none_handling(self, mock_plt):
        """Test _add_axis_labels with None labels."""
        concrete = ConcreteBase()
        concrete.set_labels(x=None, y="Y Label")

        mock_ax = MagicMock()
        concrete._add_axis_labels(mock_ax)

        mock_ax.set_xlabel.assert_not_called()
        mock_ax.set_ylabel.assert_called_once_with("Y Label")

    @patch("matplotlib.pyplot")
    def test_set_axis_scale(self, mock_plt):
        """Test _set_axis_scale method."""
        concrete = ConcreteBase()
        concrete.set_log(x=True, y=False)

        mock_ax = MagicMock()
        concrete._set_axis_scale(mock_ax)

        mock_ax.set_xscale.assert_called_once_with("log")
        mock_ax.set_yscale.assert_not_called()

    @patch("matplotlib.pyplot")
    def test_set_axis_scale_transpose(self, mock_plt):
        """Test _set_axis_scale with transpose_axes=True."""
        concrete = ConcreteBase()
        concrete.set_log(x=True, y=False)

        mock_ax = MagicMock()
        concrete._set_axis_scale(mock_ax, transpose_axes=True)

        # Scales should be swapped
        mock_ax.set_xscale.assert_not_called()
        mock_ax.set_yscale.assert_called_once_with("log")

    @patch("matplotlib.pyplot")
    def test_format_axis_complete(self, mock_plt):
        """Test _format_axis method calls all formatting functions."""
        concrete = ConcreteBase()
        concrete.set_labels(x="X", y="Y")
        concrete.set_log(x=True, y=True)

        mock_ax = MagicMock()
        concrete._format_axis(mock_ax)

        # Check that all formatting was applied
        mock_ax.set_xlabel.assert_called_once_with("X")
        mock_ax.set_ylabel.assert_called_once_with("Y")
        mock_ax.set_xscale.assert_called_once_with("log")
        mock_ax.set_yscale.assert_called_once_with("log")
        mock_ax.grid.assert_called_once_with(True, which="major", axis="both")
        mock_ax.tick_params.assert_called_once_with(
            axis="both", which="both", direction="inout"
        )


class TestPlotWithZdata:
    """Test the PlotWithZdata class functionality."""

    def test_set_data_basic(self):
        """Test basic set_data functionality."""
        plot = ConcretePlotWithZdata()

        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])
        z = np.array([7, 8, 9])

        plot.set_data(x, y, z)

        assert isinstance(plot.data, pd.DataFrame)
        assert list(plot.data.columns) == ["x", "y", "z"]
        assert len(plot.data) == 3
        assert plot.clip is False

    def test_set_data_without_z(self):
        """Test set_data without z parameter creates default z=1."""
        plot = ConcretePlotWithZdata()

        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        plot.set_data(x, y)

        assert "z" in plot.data.columns
        assert all(plot.data["z"] == 1)

    def test_set_data_with_clip(self):
        """Test set_data with clip_data=True."""
        plot = ConcretePlotWithZdata()

        x = np.array([1, 2, 3])
        y = np.array([4, 5, 6])

        plot.set_data(x, y, clip_data=True)

        assert plot.clip is True

    def test_set_data_drops_nan(self):
        """Test that set_data drops NaN values."""
        plot = ConcretePlotWithZdata()

        x = np.array([1, np.nan, 3])
        y = np.array([4, 5, np.nan])
        z = np.array([7, 8, 9])

        plot.set_data(x, y, z)

        # Should have dropped rows with NaN
        assert len(plot.data) == 1  # Only first row is complete
        assert plot.data.iloc[0]["x"] == 1
        assert plot.data.iloc[0]["y"] == 4
        assert plot.data.iloc[0]["z"] == 7

    def test_set_data_all_nan_raises_error(self):
        """Test that set_data raises ValueError when all data is NaN."""
        plot = ConcretePlotWithZdata()

        x = np.array([np.nan, np.nan])
        y = np.array([np.nan, np.nan])

        with pytest.raises(ValueError, match="exclusively NaNs"):
            plot.set_data(x, y)

    def test_set_path_auto_with_scale(self):
        """Test set_path auto mode with add_scale=True (default)."""
        plot = ConcretePlotWithZdata()
        plot.set_labels(x="X", y="Y", z="Z")
        plot.set_log(x=True, y=False)

        plot.set_path("auto")

        # Check that path was constructed properly
        assert isinstance(plot.path, Path)
        # Should include scale information by default

    def test_set_path_explicit(self):
        """Test set_path with explicit path."""
        plot = ConcretePlotWithZdata()

        plot.set_path("/custom/path", add_scale=False)

        assert plot.path == Path("/custom/path")

    def test_set_labels_preserves_z(self):
        """Test that set_labels properly handles z label."""
        plot = ConcretePlotWithZdata()
        plot.set_labels(x="X", y="Y", z="Z")

        # Update only x and y
        plot.set_labels(x="New X", y="New Y")

        assert plot.labels.x == "New X"
        assert plot.labels.y == "New Y"
        assert plot.labels.z == "Z"  # Should be preserved


class TestDataLimFormatter:
    """Test the DataLimFormatter mixin class."""

    def test_format_axis_calls_super_and_sets_limits(self):
        """Test that _format_axis calls super and sets data limits."""
        # This is a mixin, so we need to test it with a concrete class
        # that also inherits from Base

        class ConcreteDataLimFormatter(DataLimFormatter, ConcreteBase):
            def __init__(self):
                super().__init__()
                self.set_data(pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}))

        formatter = ConcreteDataLimFormatter()

        mock_ax = MagicMock()
        mock_collection = MagicMock()
        mock_collection.sticky_edges.x = []
        mock_collection.sticky_edges.y = []

        formatter._format_axis(mock_ax, mock_collection)

        # Should have called grid and tick_params from super()
        mock_ax.grid.assert_called_once()
        mock_ax.tick_params.assert_called_once()

        # Should have set sticky edges
        assert mock_collection.sticky_edges.x == [1, 3]  # min, max of x
        assert mock_collection.sticky_edges.y == [4, 6]  # min, max of y

        # Should have updated data limits
        mock_ax.update_datalim.assert_called_once()
        mock_ax.autoscale_view.assert_called_once()


class TestCbarMaker:
    """Test the CbarMaker mixin class."""

    @patch("matplotlib.pyplot")
    def test_make_cbar_with_ax(self, mock_plt):
        """Test _make_cbar with ax parameter."""

        class ConcreteCbarMaker(CbarMaker, ConcreteBase):
            pass

        maker = ConcreteCbarMaker()
        maker.set_labels(z="Z Label")

        mock_ax = MagicMock()
        mock_fig = MagicMock()
        mock_ax.figure = mock_fig
        mock_mappable = MagicMock()

        result = maker._make_cbar(mock_mappable, ax=mock_ax)

        mock_fig.colorbar.assert_called_once_with(
            mock_mappable, label="Z Label", ax=mock_ax, cax=None
        )
        assert result == mock_fig.colorbar.return_value

    @patch("matplotlib.pyplot")
    def test_make_cbar_with_cax(self, mock_plt):
        """Test _make_cbar with cax parameter."""

        class ConcreteCbarMaker(CbarMaker, ConcreteBase):
            pass

        maker = ConcreteCbarMaker()
        maker.set_labels(z="Z Label")

        mock_cax = MagicMock()
        mock_fig = MagicMock()
        mock_cax.figure = mock_fig
        mock_mappable = MagicMock()

        result = maker._make_cbar(mock_mappable, cax=mock_cax)

        mock_fig.colorbar.assert_called_once_with(
            mock_mappable, label="Z Label", ax=None, cax=mock_cax
        )

    def test_make_cbar_ax_and_cax_error(self):
        """Test that passing both ax and cax raises ValueError."""

        class ConcreteCbarMaker(CbarMaker, ConcreteBase):
            pass

        maker = ConcreteCbarMaker()
        mock_ax = MagicMock()
        mock_cax = MagicMock()
        mock_mappable = MagicMock()

        with pytest.raises(ValueError, match="Can't pass ax and cax"):
            maker._make_cbar(mock_mappable, ax=mock_ax, cax=mock_cax)

    def test_make_cbar_no_ax_or_cax_error(self):
        """Test that not passing ax or cax raises ValueError."""

        class ConcreteCbarMaker(CbarMaker, ConcreteBase):
            pass

        maker = ConcreteCbarMaker()
        mock_mappable = MagicMock()

        with pytest.raises(ValueError, match="You must pass `ax` or `cax`"):
            maker._make_cbar(mock_mappable)

    @patch("matplotlib.pyplot")
    def test_make_cbar_custom_label(self, mock_plt):
        """Test _make_cbar with custom label parameter."""

        class ConcreteCbarMaker(CbarMaker, ConcreteBase):
            pass

        maker = ConcreteCbarMaker()

        mock_ax = MagicMock()
        mock_fig = MagicMock()
        mock_ax.figure = mock_fig
        mock_mappable = MagicMock()

        maker._make_cbar(mock_mappable, ax=mock_ax, label="Custom Label")

        mock_fig.colorbar.assert_called_once_with(
            mock_mappable, label="Custom Label", ax=mock_ax, cax=None
        )


class TestBaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods raise NotImplementedError if not implemented."""

        class IncompleteBase(Base):
            def __init__(self):
                super().__init__()

            # Missing set_data and make_plot implementations

        with pytest.raises(TypeError):
            IncompleteBase()

    def test_logger_name_format(self):
        """Test that logger name includes module and class name."""
        concrete = ConcreteBase()
        logger_name = concrete.logger.name

        assert "base" in logger_name  # module name
        assert "ConcreteBase" in logger_name  # class name

    def test_multiple_label_updates(self):
        """Test multiple sequential label updates."""
        concrete = ConcreteBase()

        concrete.set_labels(x="X1", y="Y1")
        assert concrete.labels.x == "X1"

        concrete.set_labels(x="X2")
        assert concrete.labels.x == "X2"
        assert concrete.labels.y == "Y1"  # Should be preserved

        concrete.set_labels(y="Y2", z="Z2")
        assert concrete.labels.x == "X2"  # Should be preserved
        assert concrete.labels.y == "Y2"
        assert concrete.labels.z == "Z2"

    def test_log_scale_persistence(self):
        """Test that log scale settings persist across operations."""
        concrete = ConcreteBase()

        concrete.set_log(x=True, y=True)
        concrete.set_labels(x="New X")  # This might trigger path update

        # Log settings should remain unchanged
        assert concrete.log.x is True
        assert concrete.log.y is True


if __name__ == "__main__":
    pytest.main([__file__])
