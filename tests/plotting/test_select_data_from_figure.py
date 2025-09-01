#!/usr/bin/env python
"""Tests for solarwindpy.plotting.select_data_from_figure module.

This module provides comprehensive test coverage for the SelectFromPlot2D class used for
interactive data selection from plotted figures.
"""

import pytest
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call, Mock
from collections import namedtuple

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from matplotlib import pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle
from matplotlib.text import Text

import solarwindpy.plotting.select_data_from_figure as select_module
from solarwindpy.plotting.select_data_from_figure import SelectFromPlot2D, DateAxes


class TestSelectDataFromFigureModuleStructure:
    """Test select_data_from_figure module structure and imports."""

    def test_module_imports(self):
        """Test that all required imports are accessible."""
        # Test basic imports
        assert hasattr(select_module, "logging")
        assert hasattr(select_module, "np")
        assert hasattr(select_module, "pd")
        assert hasattr(select_module, "mpl")
        assert hasattr(select_module, "namedtuple")

    def test_module_all_export(self):
        """Test that __all__ exports are correct."""
        assert hasattr(select_module, "__all__")
        assert "SelectFromPlot2D" in select_module.__all__
        assert len(select_module.__all__) == 1

    def test_date_axes_namedtuple(self):
        """Test DateAxes namedtuple structure."""
        assert hasattr(select_module, "DateAxes")
        assert DateAxes._fields == ("x", "y")

        # Test creation
        date_axes = DateAxes(True, False)
        assert date_axes.x is True
        assert date_axes.y is False

    def test_select_from_plot_2d_class_available(self):
        """Test that SelectFromPlot2D class is accessible from module."""
        assert hasattr(select_module, "SelectFromPlot2D")
        assert callable(select_module.SelectFromPlot2D)


class TestSelectFromPlot2DInitialization:
    """Test SelectFromPlot2D class initialization and basic properties."""

    @pytest.fixture
    def mock_plotter(self):
        """Create a mock plotter object."""
        plotter = Mock()
        plotter.data = pd.DataFrame(
            {
                "x": np.random.randn(100),
                "y": np.random.randn(100),
                "z": np.random.randn(100),
            }
        )
        plotter.log = Mock()
        plotter.log.x = False
        plotter.log.y = False
        return plotter

    @pytest.fixture
    def mock_ax(self):
        """Create a mock axes object."""
        ax = Mock()
        ax.figure = Mock()
        ax.figure.axes = [ax]  # Single panel by default
        ax.patches = []
        ax.transAxes = Mock()
        ax.text = Mock(return_value=Mock())
        ax.xaxis = Mock()
        ax.xaxis.get_label = Mock()
        ax.xaxis.get_label.return_value = Mock()
        ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
        ax.yaxis = Mock()
        ax.yaxis.get_label = Mock()
        ax.yaxis.get_label.return_value = Mock()
        ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
        ax.figure.canvas = Mock()
        ax.figure.canvas.draw_idle = Mock()
        ax.add_patch = Mock()
        ax.scatter = Mock()
        ax.get_xlim = Mock(return_value=(0, 1))
        ax.get_ylim = Mock(return_value=(0, 1))
        ax.set_xlim = Mock()
        ax.set_ylim = Mock()
        return ax

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_init_basic(self, mock_rect_selector, mock_plotter, mock_ax):
        """Test basic initialization."""
        mock_selector = Mock()
        mock_rect_selector.return_value = mock_selector

        selector = SelectFromPlot2D(mock_plotter, mock_ax)

        # Test basic attributes
        assert selector._plotter is mock_plotter
        assert selector._ax is mock_ax
        assert selector._corners == tuple()
        assert hasattr(selector, "_date_axes")
        assert hasattr(selector, "_text")
        assert hasattr(selector, "_selector")

        # Test initialization calls
        mock_rect_selector.assert_called_once()
        mock_ax.text.assert_called_once()

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_init_with_colorbar(self, mock_rect_selector, mock_plotter, mock_ax):
        """Test initialization with colorbar consideration."""
        # Mock multi-panel with colorbar
        mock_ax.figure.axes = [mock_ax, Mock(), Mock()]  # 3 axes (2 + colorbar)
        mock_selector = Mock()
        mock_rect_selector.return_value = mock_selector

        selector = SelectFromPlot2D(mock_plotter, mock_ax, has_colorbar=True)

        # With colorbar=True and 3 axes: (3 - 1) = 2 > 1, so is_multipanel=True
        assert selector.is_multipanel is True

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_init_date_axes(self, mock_rect_selector, mock_plotter, mock_ax):
        """Test initialization with date axes."""
        mock_selector = Mock()
        mock_rect_selector.return_value = mock_selector

        selector = SelectFromPlot2D(mock_plotter, mock_ax, xdate=True, ydate=False)

        assert selector.date_axes.x is True
        assert selector.date_axes.y is False

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_init_text_kwargs(self, mock_rect_selector, mock_plotter, mock_ax):
        """Test initialization with custom text kwargs."""
        mock_selector = Mock()
        mock_rect_selector.return_value = mock_selector
        text_kwargs = {"fontsize": 12, "color": "red"}

        selector = SelectFromPlot2D(mock_plotter, mock_ax, text_kwargs=text_kwargs)

        # Should initialize without error
        assert hasattr(selector, "_text")

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_invalid_plotter_type(self, mock_rect_selector, mock_ax):
        """Test that invalid plotter type raises AttributeError when accessing plotter
        attributes."""
        mock_selector = Mock()
        mock_rect_selector.return_value = mock_selector

        # Initialization should work (plotter attributes not accessed yet)
        selector = SelectFromPlot2D("invalid_plotter", mock_ax)

        # But accessing plotter.data should fail
        with pytest.raises(AttributeError):
            selector._add_corners((0, 1, 0, 1))
            selector.sample_data(n=3)


class TestSelectFromPlot2DProperties:
    """Test SelectFromPlot2D properties."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    def test_ax_property(self, selector_setup):
        """Test ax property."""
        selector, plotter, ax = selector_setup
        assert selector.ax is ax

    def test_corners_property(self, selector_setup):
        """Test corners property."""
        selector, plotter, ax = selector_setup
        assert selector.corners == tuple()

        # Test after adding corners
        selector._add_corners((0, 1, 0, 1))
        assert len(selector.corners) == 1
        assert selector.corners[0] == (0, 1, 0, 1)

    def test_date_axes_property(self, selector_setup):
        """Test date_axes property."""
        selector, plotter, ax = selector_setup
        assert hasattr(selector.date_axes, "x")
        assert hasattr(selector.date_axes, "y")

    def test_is_multipanel_property(self, selector_setup):
        """Test is_multipanel property."""
        selector, plotter, ax = selector_setup
        assert selector.is_multipanel is False  # Single panel by default

    def test_plotter_property(self, selector_setup):
        """Test plotter property."""
        selector, plotter, ax = selector_setup
        assert selector.plotter is plotter

    def test_selector_property(self, selector_setup):
        """Test selector property."""
        selector, plotter, ax = selector_setup
        assert hasattr(selector, "selector")
        assert selector.selector is not None

    def test_text_property(self, selector_setup):
        """Test text property."""
        selector, plotter, ax = selector_setup
        assert hasattr(selector, "text")
        assert selector.text is not None

    def test_num_initial_patches_property(self, selector_setup):
        """Test num_initial_patches property."""
        selector, plotter, ax = selector_setup
        assert hasattr(selector, "num_initial_patches")
        assert isinstance(selector.num_initial_patches, int)

    def test_num_selection_patches_property(self, selector_setup):
        """Test num_selection_patches property."""
        selector, plotter, ax = selector_setup
        # Initially should be 0
        assert selector.num_selection_patches == 0

    def test_logger_property(self, selector_setup):
        """Test logger property."""
        selector, plotter, ax = selector_setup
        logger = selector.logger
        assert isinstance(logger, logging.Logger)
        assert "analysis" in logger.name


class TestSelectFromPlot2DCornerManagement:
    """Test corner management methods."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    def test_init_corners(self, selector_setup):
        """Test _init_corners method."""
        selector, plotter, ax = selector_setup

        # Corners should be initialized as empty tuple
        assert selector.corners == tuple()

    def test_add_corners(self, selector_setup):
        """Test _add_corners method."""
        selector, plotter, ax = selector_setup

        # Add first corner
        corner1 = (0, 1, 0, 1)
        selector._add_corners(corner1)
        assert len(selector.corners) == 1
        assert selector.corners[0] == corner1

        # Add second corner
        corner2 = (2, 3, 2, 3)
        selector._add_corners(corner2)
        assert len(selector.corners) == 2
        assert selector.corners[0] == corner1
        assert selector.corners[1] == corner2


class TestSelectFromPlot2DTextManagement:
    """Test text management methods."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            # Mock required attributes for text methods
            selector._sampled_indices = pd.Index([1, 2, 3])
            selector._failed_samples = []
            selector._sampled_per_patch = 3

            return selector, plotter, ax

    def test_finalize_text_single_panel(self, selector_setup):
        """Test _finalize_text method for single panel."""
        selector, plotter, ax = selector_setup
        selector._is_multipanel = False

        # Mock the text object
        mock_text = Mock()
        selector._text = mock_text

        selector._finalize_text()

        # Should call set_text with formatted string
        mock_text.set_text.assert_called_once()
        call_args = mock_text.set_text.call_args[0][0]
        assert "Patches" in call_args
        assert "Spectra" in call_args
        assert "  -  " in call_args  # Single panel format

    def test_finalize_text_multi_panel(self, selector_setup):
        """Test _finalize_text method for multi panel."""
        selector, plotter, ax = selector_setup
        selector._is_multipanel = True

        # Mock the text object
        mock_text = Mock()
        selector._text = mock_text

        selector._finalize_text()

        # Should call set_text with formatted string
        mock_text.set_text.assert_called_once()
        call_args = mock_text.set_text.call_args[0][0]
        assert "Patches" in call_args
        assert "Spectra" in call_args
        assert "\n" in call_args  # Multi panel format

    def test_update_text_no_dates(self, selector_setup):
        """Test _update_text method without date axes."""
        selector, plotter, ax = selector_setup

        # Mock selector with extents
        mock_selector = Mock()
        mock_selector.extents = (0.1, 0.9, 0.2, 0.8)
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        selector._update_text()

        mock_text.set_text.assert_called_once()
        call_args = mock_text.set_text.call_args[0][0]
        assert "Patch" in call_args
        assert "Lower Left" in call_args
        assert "Upper Right" in call_args

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.dates.num2date")
    def test_update_text_with_dates(self, mock_num2date, selector_setup):
        """Test _update_text method with date axes."""
        selector, plotter, ax = selector_setup

        # Set date axes
        selector._date_axes = DateAxes(True, True)

        # Mock date conversion
        mock_date = Mock()
        mock_date.strftime = Mock(return_value="2020-01-01 12:00:00")
        mock_num2date.return_value = [mock_date, mock_date]

        # Mock selector with extents
        mock_selector = Mock()
        mock_selector.extents = (737425.5, 737426.5, 737425.5, 737426.5)  # date numbers
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        selector._update_text()

        mock_text.set_text.assert_called_once()
        mock_num2date.assert_called()


class TestSelectFromPlot2DSelection:
    """Test selection-related methods."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()
            ax.add_patch = Mock()
            ax.scatter = Mock()
            ax.get_xlim = Mock(return_value=(0, 1))
            ax.get_ylim = Mock(return_value=(0, 1))
            ax.set_xlim = Mock()
            ax.set_ylim = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.patches.Rectangle")
    def test_onselect(self, mock_rectangle, selector_setup):
        """Test onselect method."""
        selector, plotter, ax = selector_setup

        # Mock selector rect_bbox
        mock_selector = Mock()
        mock_selector._rect_bbox = [0, 0, 1, 1]  # x, y, w, h
        mock_selector.extents = (0, 1, 0, 1)
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        # Mock rectangle patch
        mock_rect = Mock()
        mock_rectangle.return_value = mock_rect

        selector.onselect("press", "release")

        # Should create rectangle and add to axis
        mock_rectangle.assert_called_once()
        ax.add_patch.assert_called_once_with(mock_rect)

        # Should update corners and text
        assert len(selector.corners) == 1
        mock_text.set_text.assert_called()
        ax.figure.canvas.draw_idle.assert_called()

    def test_set_ax(self, selector_setup):
        """Test set_ax method."""
        selector, plotter, ax = selector_setup

        # Test single panel
        new_ax = Mock()
        new_ax.figure = Mock()
        new_ax.figure.axes = [new_ax]

        selector.set_ax(new_ax, has_colorbar=False)

        assert selector._ax is new_ax
        assert selector._is_multipanel is False

        # Test multi panel with colorbar
        new_ax.figure.axes = [new_ax, Mock(), Mock()]  # 3 axes
        selector.set_ax(new_ax, has_colorbar=True)
        assert selector._is_multipanel is True

    def test_start_text_single_panel(self, selector_setup):
        """Test start_text method for single panel."""
        selector, plotter, ax = selector_setup
        selector._is_multipanel = False

        # Mock text creation
        mock_text = Mock()
        ax.text = Mock(return_value=mock_text)

        selector.start_text()

        # Should call ax.text with appropriate parameters
        ax.text.assert_called()
        call_kwargs = ax.text.call_args[1]
        assert call_kwargs["va"] == "bottom"  # Single panel

        assert selector._text is mock_text

    def test_start_text_multi_panel(self, selector_setup):
        """Test start_text method for multi panel."""
        selector, plotter, ax = selector_setup
        selector._is_multipanel = True

        # Mock text creation
        mock_text = Mock()
        ax.text = Mock(return_value=mock_text)

        selector.start_text()

        # Should call ax.text with appropriate parameters
        ax.text.assert_called()
        call_kwargs = ax.text.call_args[1]
        assert call_kwargs["va"] == "top"  # Multi panel

        assert selector._text is mock_text

    def test_start_text_custom_kwargs(self, selector_setup):
        """Test start_text method with custom kwargs."""
        selector, plotter, ax = selector_setup

        # Mock text creation
        mock_text = Mock()
        ax.text = Mock(return_value=mock_text)

        custom_kwargs = {"fontsize": 14, "color": "blue"}
        selector.start_text(**custom_kwargs)

        ax.text.assert_called()
        assert selector._text is mock_text

    def test_start_selector(self, selector_setup):
        """Test start_selector method."""
        selector, plotter, ax = selector_setup

        # Should have initialized selector and tracked initial patches
        assert hasattr(selector, "_selector")
        assert hasattr(selector, "_num_initial_patches")
        assert isinstance(selector._num_initial_patches, int)


class TestSelectFromPlot2DSampleData:
    """Test data sampling methods."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            # Create realistic test data
            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "x": np.random.uniform(0, 10, 100),
                    "y": np.random.uniform(0, 10, 100),
                    "z": np.random.uniform(0, 1, 100),
                },
                index=pd.RangeIndex(100),
            )

            plotter = Mock()
            plotter.data = data
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()
            ax.add_patch = Mock()
            ax.scatter = Mock()
            ax.get_xlim = Mock(return_value=(0, 1))
            ax.get_ylim = Mock(return_value=(0, 1))
            ax.set_xlim = Mock()
            ax.set_ylim = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    def test_sample_data_basic(self, selector_setup):
        """Test basic sample_data functionality."""
        selector, plotter, ax = selector_setup

        # Add a corner that should contain some data
        selector._add_corners((2, 8, 2, 8))

        selector.sample_data(n=3, random_state=42)

        # Should have sampled indices
        assert hasattr(selector, "_sampled_indices")
        assert hasattr(selector, "_failed_samples")
        assert hasattr(selector, "_sampled_per_patch")
        assert selector._sampled_per_patch == 3
        assert isinstance(selector._sampled_indices, pd.Index)
        assert len(selector._failed_samples) >= 0

    def test_sample_data_frac_not_implemented(self, selector_setup):
        """Test that sample_data with frac raises NotImplementedError."""
        selector, plotter, ax = selector_setup

        with pytest.raises(NotImplementedError, match="Please use the `n` kwarg"):
            selector.sample_data(frac=0.1)

    def test_sample_data_with_log_axes(self, selector_setup):
        """Test sample_data with logarithmic axes."""
        selector, plotter, ax = selector_setup

        # Set log axes
        plotter.log.x = True
        plotter.log.y = True

        # Add corner
        selector._add_corners((1, 10, 1, 10))  # Will be log10 transformed

        selector.sample_data(n=2, random_state=42)

        # Should complete without error
        assert hasattr(selector, "_sampled_indices")

    def test_sample_data_empty_region(self, selector_setup):
        """Test sample_data with region containing no data."""
        selector, plotter, ax = selector_setup

        # Add corner outside data range
        selector._add_corners((100, 110, 100, 110))

        selector.sample_data(n=3, random_state=42)

        # Should have failed samples
        assert len(selector._failed_samples) == 1
        assert selector._failed_samples[0] == (100, 110, 100, 110)

    def test_sample_data_with_other_selector(self, selector_setup):
        """Test sample_data with other_SelectFromPlot2D."""
        selector, plotter, ax = selector_setup

        # Create another selector with already sampled indices
        other_selector = Mock()
        other_selector.sampled_indices = pd.Index([0, 1, 2])

        # Add corner
        selector._add_corners((0, 10, 0, 10))

        selector.sample_data(
            n=3, random_state=42, other_SelectFromPlot2D=other_selector
        )

        # Should complete without error
        assert hasattr(selector, "_sampled_indices")

    def test_sample_data_with_other_selector_list(self, selector_setup):
        """Test sample_data with list of other selectors."""
        selector, plotter, ax = selector_setup

        # Create other selectors
        other1 = Mock()
        other1.sampled_indices = pd.Index([0, 1])
        other2 = Mock()
        other2.sampled_indices = pd.Index([2, 3])

        # Add corner
        selector._add_corners((0, 10, 0, 10))

        selector.sample_data(
            n=3, random_state=42, other_SelectFromPlot2D=[other1, other2]
        )

        # Should complete without error
        assert hasattr(selector, "_sampled_indices")

    def test_sample_data_insufficient_samples(self, selector_setup):
        """Test sample_data when not enough samples available without replacement."""
        selector, plotter, ax = selector_setup

        # Create data with only 2 points in range but request 5
        selector._plotter.data = pd.DataFrame(
            {"x": [5.0, 5.1], "y": [5.0, 5.1], "z": [0.5, 0.6]}, index=[0, 1]
        )

        # Add corner that contains both points
        selector._add_corners((4.9, 5.2, 4.9, 5.2))

        # Mock logger module to capture warning
        with patch(
            "solarwindpy.plotting.select_data_from_figure.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            selector.sample_data(n=5, random_state=42)

            # Should log warning about sampling with replacement
            mock_logger.warning.assert_called()
            assert "Sample failed without replacement" in str(
                mock_logger.warning.call_args
            )


class TestSelectFromPlot2DDisconnectAndPlotting:
    """Test disconnect and plotting methods."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            # Create realistic test data
            np.random.seed(42)
            data = pd.DataFrame(
                {
                    "x": np.random.uniform(0, 10, 100),
                    "y": np.random.uniform(0, 10, 100),
                    "z": np.random.uniform(0, 1, 100),
                },
                index=pd.RangeIndex(100),
            )

            plotter = Mock()
            plotter.data = data
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()
            ax.add_patch = Mock()
            ax.scatter = Mock()
            ax.get_xlim = Mock(return_value=(0, 10))
            ax.get_ylim = Mock(return_value=(0, 10))
            ax.set_xlim = Mock()
            ax.set_ylim = Mock()

            selector = SelectFromPlot2D(plotter, ax)

            # Set up some sampled data
            selector._add_corners((2, 8, 2, 8))
            selector.sample_data(n=3, random_state=42)

            return selector, plotter, ax

    def test_disconnect(self, selector_setup):
        """Test disconnect method."""
        selector, plotter, ax = selector_setup

        # Mock selector disconnect
        mock_selector = Mock()
        mock_selector.disconnect_events = Mock()
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        selector.disconnect()

        # Should call all required methods
        mock_selector.disconnect_events.assert_called_once()
        mock_text.set_text.assert_called()

    def test_disconnect_with_other_selector(self, selector_setup):
        """Test disconnect with other SelectFromPlot2D."""
        selector, plotter, ax = selector_setup

        # Create other selector
        other_selector = Mock()
        other_selector.sampled_indices = pd.Index([10, 11, 12])

        # Mock selector disconnect
        mock_selector = Mock()
        mock_selector.disconnect_events = Mock()
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        selector.disconnect(other_SelectFromPlot2D=other_selector)

        # Should call disconnect_events
        mock_selector.disconnect_events.assert_called_once()

    def test_disconnect_with_scatter_kwargs(self, selector_setup):
        """Test disconnect with custom scatter kwargs."""
        selector, plotter, ax = selector_setup

        # Mock selector disconnect
        mock_selector = Mock()
        mock_selector.disconnect_events = Mock()
        selector._selector = mock_selector

        # Mock text object
        mock_text = Mock()
        selector._text = mock_text

        scatter_kwargs = {"color": "red", "s": 50}
        selector.disconnect(scatter_kwargs=scatter_kwargs)

        # Should call disconnect_events
        mock_selector.disconnect_events.assert_called_once()

    def test_scatter_sample(self, selector_setup):
        """Test scatter_sample method."""
        selector, plotter, ax = selector_setup

        selector.scatter_sample()

        # Should call ax.scatter
        ax.scatter.assert_called_once()

        # Should preserve axis limits
        ax.set_xlim.assert_called_once_with(0, 10)
        ax.set_ylim.assert_called_once_with(0, 10)

    def test_scatter_sample_with_log_axes(self, selector_setup):
        """Test scatter_sample with logarithmic axes."""
        selector, plotter, ax = selector_setup

        # Set log axes
        plotter.log.x = True
        plotter.log.y = True

        selector.scatter_sample()

        # Should call ax.scatter (data will be transformed)
        ax.scatter.assert_called_once()

    def test_scatter_sample_custom_kwargs(self, selector_setup):
        """Test scatter_sample with custom kwargs."""
        selector, plotter, ax = selector_setup

        custom_kwargs = {"c": "blue", "s": 100, "marker": "x"}
        selector.scatter_sample(**custom_kwargs)

        # Should call ax.scatter
        ax.scatter.assert_called_once()
        call_kwargs = ax.scatter.call_args[1]
        assert call_kwargs["c"] == "blue"
        assert call_kwargs["s"] == 100
        assert call_kwargs["marker"] == "x"

    def test_plot_failed_samples(self, selector_setup):
        """Test plot_failed_samples method."""
        selector, plotter, ax = selector_setup

        # Add some failed samples
        selector._failed_samples = [(100, 110, 100, 110), (120, 130, 120, 130)]

        selector.plot_failed_samples()

        # Should add patches for failed samples
        assert ax.add_patch.call_count == 2
        ax.figure.canvas.draw_idle.assert_called_once()

    def test_plot_failed_samples_empty(self, selector_setup):
        """Test plot_failed_samples with no failed samples."""
        selector, plotter, ax = selector_setup

        # No failed samples
        selector._failed_samples = []

        selector.plot_failed_samples()

        # Should still call draw_idle but no patches added
        ax.figure.canvas.draw_idle.assert_called_once()
        # ax.add_patch should not be called
        ax.add_patch.assert_not_called()


class TestSelectFromPlot2DDateAxes:
    """Test date axes functionality."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    def test_set_date_axes(self, selector_setup):
        """Test set_date_axes method."""
        selector, plotter, ax = selector_setup

        selector.set_date_axes(True, False)

        assert selector.date_axes.x is True
        assert selector.date_axes.y is False

        selector.set_date_axes(False, True)

        assert selector.date_axes.x is False
        assert selector.date_axes.y is True


class TestSelectFromPlot2DEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def selector_setup(self):
        """Set up a SelectFromPlot2D instance for testing."""
        with patch(
            "solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector"
        ):
            plotter = Mock()
            plotter.data = pd.DataFrame(
                {
                    "x": np.random.randn(100),
                    "y": np.random.randn(100),
                    "z": np.random.randn(100),
                }
            )
            plotter.log = Mock()
            plotter.log.x = False
            plotter.log.y = False

            ax = Mock()
            ax.figure = Mock()
            ax.figure.axes = [ax]
            ax.patches = []
            ax.transAxes = Mock()
            ax.text = Mock(return_value=Mock())
            ax.xaxis = Mock()
            ax.xaxis.get_label = Mock()
            ax.xaxis.get_label.return_value = Mock()
            ax.xaxis.get_label.return_value.get_text = Mock(return_value="x-axis")
            ax.yaxis = Mock()
            ax.yaxis.get_label = Mock()
            ax.yaxis.get_label.return_value = Mock()
            ax.yaxis.get_label.return_value.get_text = Mock(return_value="y-axis")
            ax.figure.canvas = Mock()
            ax.figure.canvas.draw_idle = Mock()

            selector = SelectFromPlot2D(plotter, ax)
            return selector, plotter, ax

    def test_sample_data_value_error_reraise(self, selector_setup):
        """Test that ValueError other than sample size is re-raised."""
        selector, plotter, ax = selector_setup

        # Mock pandas Series.sample to raise different ValueError
        with patch("pandas.Series.sample") as mock_sample:
            mock_sample.side_effect = ValueError("Different error message")

            selector._add_corners((0, 10, 0, 10))

            with pytest.raises(ValueError, match="Different error message"):
                selector.sample_data(n=3, random_state=42)

    def test_sample_data_missing_already_selected(self, selector_setup):
        """Test sample_data when already_selected indices are missing."""
        selector, plotter, ax = selector_setup

        # Create other selector with indices not in current data
        other_selector = Mock()
        other_selector.sampled_indices = pd.Index(
            [200, 201, 202]
        )  # Outside current data range

        # Add corner
        selector._add_corners((0, 10, 0, 10))

        # Mock logger module to capture warning
        with patch(
            "solarwindpy.plotting.select_data_from_figure.logging.getLogger"
        ) as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            selector.sample_data(
                n=3, random_state=42, other_SelectFromPlot2D=other_selector
            )

            # Should log warning about missing indices
            mock_logger.warning.assert_called()
            assert "None of `already_selected` found" in str(
                mock_logger.warning.call_args
            )

    def test_sample_data_other_selector_no_sampled_indices(self, selector_setup):
        """Test sample_data with other selector that has no sampled_indices
        attribute."""
        selector, plotter, ax = selector_setup

        # Create other selector without sampled_indices
        other_selector = Mock()
        del other_selector.sampled_indices  # Remove attribute

        # Add corner
        selector._add_corners((0, 10, 0, 10))

        # Should handle gracefully
        selector.sample_data(
            n=3, random_state=42, other_SelectFromPlot2D=other_selector
        )

        # Should complete without error
        assert hasattr(selector, "_sampled_indices")


class TestSelectFromPlot2DIntegration:
    """Integration tests for SelectFromPlot2D."""

    @patch("solarwindpy.plotting.select_data_from_figure.mpl.widgets.RectangleSelector")
    def test_full_workflow(self, mock_rect_selector):
        """Test complete selection workflow."""
        # Set up realistic scenario
        np.random.seed(42)
        data = pd.DataFrame(
            {
                "x": np.random.uniform(0, 10, 50),
                "y": np.random.uniform(0, 10, 50),
                "z": np.random.uniform(0, 1, 50),
            },
            index=pd.RangeIndex(50),
        )

        plotter = Mock()
        plotter.data = data
        plotter.log = Mock()
        plotter.log.x = False
        plotter.log.y = False

        # Create figure and axis
        fig, ax = plt.subplots()

        # Mock selector
        mock_selector = Mock()
        mock_selector.extents = (2, 8, 2, 8)
        mock_selector._rect_bbox = [2, 2, 6, 6]
        mock_selector.disconnect_events = Mock()
        mock_rect_selector.return_value = mock_selector

        # Create selector
        selector = SelectFromPlot2D(plotter, ax)

        # Simulate selection
        selector.onselect("press", "release")

        # Should have added corner
        assert len(selector.corners) == 1

        # Sample data
        selector.sample_data(n=3, random_state=42)

        # Should have sampled indices
        assert hasattr(selector, "_sampled_indices")
        assert len(selector._sampled_indices) > 0

        # Disconnect
        selector.disconnect()

        # Should have called disconnect_events
        mock_selector.disconnect_events.assert_called_once()

        plt.close(fig)
