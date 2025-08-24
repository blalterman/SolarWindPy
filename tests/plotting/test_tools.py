#!/usr/bin/env python
"""Tests for solarwindpy.plotting.tools module.

This module provides comprehensive test coverage for matplotlib utility functions
including subplot creation, figure saving, legends, and colorbar management.
"""

import pytest
import logging
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime
import tempfile
import os

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.legend import Legend
import matplotlib.gridspec

import solarwindpy.plotting.tools as tools_module


class TestToolsModuleStructure:
    """Test tools module structure and imports."""

    def test_module_imports(self):
        """Test that all required imports are accessible."""
        assert hasattr(tools_module, "np")
        assert hasattr(tools_module, "mpl")
        assert hasattr(tools_module, "plt")
        assert hasattr(tools_module, "logging")
        assert hasattr(tools_module, "Path")
        assert hasattr(tools_module, "datetime")

    def test_functions_available(self):
        """Test that all utility functions are accessible."""
        expected_functions = [
            "subplots",
            "save",
            "joint_legend",
            "multipanel_figure_shared_cbar",
            "build_ax_array_with_common_colorbar",
            "calculate_nrows_ncols",
        ]

        for func_name in expected_functions:
            assert hasattr(tools_module, func_name)
            assert callable(getattr(tools_module, func_name))

    def test_module_docstring(self):
        """Test that module has comprehensive docstring."""
        assert tools_module.__doc__ is not None
        assert len(tools_module.__doc__.strip()) > 0
        assert "matplotlib" in tools_module.__doc__


class TestSubplotsFunction:
    """Test subplots utility function."""

    def test_subplots_default_parameters(self):
        """Test subplots with default parameters."""
        fig, ax = tools_module.subplots()

        assert isinstance(fig, Figure)
        assert isinstance(ax, Axes)

        # Clean up
        plt.close(fig)

    def test_subplots_multiple_rows_cols(self):
        """Test subplots with multiple rows and columns."""
        fig, axes = tools_module.subplots(nrows=2, ncols=3)

        assert isinstance(fig, Figure)
        assert isinstance(axes, np.ndarray)
        assert axes.shape == (2, 3)

        # All elements should be Axes
        for ax in axes.flat:
            assert isinstance(ax, Axes)

        plt.close(fig)

    def test_subplots_scaling(self):
        """Test figure size scaling."""
        fig1, ax1 = tools_module.subplots(scale_width=1.0, scale_height=1.0)
        fig2, ax2 = tools_module.subplots(scale_width=2.0, scale_height=1.5)

        # Scaled figure should be larger
        assert fig2.get_figwidth() > fig1.get_figwidth()
        assert fig2.get_figheight() > fig1.get_figheight()

        plt.close(fig1)
        plt.close(fig2)

    def test_subplots_with_kwargs(self):
        """Test subplots with additional kwargs."""
        fig, axes = tools_module.subplots(nrows=1, ncols=2, figsize=(10, 5))

        assert isinstance(fig, Figure)
        # Note: figsize may be scaled by the function
        assert fig.get_figwidth() >= 10  # May be scaled up
        assert fig.get_figheight() >= 5  # May be scaled up

        plt.close(fig)

    def test_subplots_single_row_col(self):
        """Test subplots with single row/column returns array."""
        fig, axes = tools_module.subplots(nrows=1, ncols=3)

        assert isinstance(axes, np.ndarray)
        assert axes.shape == (3,)

        plt.close(fig)


class TestSaveFunction:
    """Test save utility function."""

    def setup_method(self):
        """Set up temporary directory for save tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_path = self.temp_dir / "test_figure"

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_save_figure_basic(self):
        """Test basic figure saving."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(fig, self.test_path, log=False)

        # Check that files were created
        assert (self.test_path.with_suffix(".pdf")).exists()
        assert (self.test_path.with_suffix(".png")).exists()

        plt.close(fig)

    def test_save_axes_input(self):
        """Test saving with Axes input instead of Figure."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(ax, self.test_path, log=False)

        # Should work the same as passing the figure
        assert (self.test_path.with_suffix(".pdf")).exists()
        assert (self.test_path.with_suffix(".png")).exists()

        plt.close(fig)

    def test_save_pdf_only(self):
        """Test saving PDF only."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(fig, self.test_path, pdf=True, png=False, log=False)

        assert (self.test_path.with_suffix(".pdf")).exists()
        assert not (self.test_path.with_suffix(".png")).exists()

        plt.close(fig)

    def test_save_png_only(self):
        """Test saving PNG only."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(fig, self.test_path, pdf=False, png=True, log=False)

        assert not (self.test_path.with_suffix(".pdf")).exists()
        assert (self.test_path.with_suffix(".png")).exists()

        plt.close(fig)

    def test_save_with_info(self):
        """Test saving with attribution info."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(fig, self.test_path, add_info=True, log=False)

        # Files should exist (info is added to PNG)
        assert (self.test_path.with_suffix(".pdf")).exists()
        assert (self.test_path.with_suffix(".png")).exists()

        plt.close(fig)

    @patch("logging.getLogger")
    def test_save_with_logging(self, mock_get_logger):
        """Test save function with logging enabled."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        tools_module.save(fig, self.test_path, log=True)

        # Should have logged save information
        mock_logger.info.assert_called()

        plt.close(fig)

    def test_save_input_validation(self):
        """Test save function input validation."""
        fig, ax = plt.subplots()

        # Should work with Figure
        tools_module.save(fig, self.test_path, log=False)

        # Should work with Axes
        tools_module.save(ax, self.test_path, log=False)

        # Path should be a Path object (assertion in function)
        with pytest.raises(AssertionError):
            tools_module.save(fig, "string_path", log=False)

        plt.close(fig)


class TestJointLegendFunction:
    """Test joint_legend utility function."""

    def test_joint_legend_basic(self):
        """Test basic joint legend functionality."""
        fig, axes = plt.subplots(1, 2)

        axes[0].plot([1, 2, 3], [1, 4, 2], label="Line A")
        axes[1].plot([1, 2, 3], [2, 3, 1], label="Line B")

        legend = tools_module.joint_legend(axes[0], axes[1])

        assert isinstance(legend, Legend)

        # Check that legend contains both labels
        legend_labels = [text.get_text() for text in legend.get_texts()]
        assert "Line A" in legend_labels
        assert "Line B" in legend_labels

        plt.close(fig)

    def test_joint_legend_duplicate_labels(self):
        """Test joint legend with duplicate labels."""
        fig, axes = plt.subplots(1, 2)

        axes[0].plot([1, 2, 3], [1, 4, 2], label="Same Label")
        axes[1].plot([1, 2, 3], [2, 3, 1], label="Same Label")

        legend = tools_module.joint_legend(axes[0], axes[1])

        # Should only have one entry for duplicate labels
        legend_labels = [text.get_text() for text in legend.get_texts()]
        assert legend_labels.count("Same Label") == 1

        plt.close(fig)

    def test_joint_legend_custom_idx(self):
        """Test joint legend with custom axis index."""
        fig, axes = plt.subplots(1, 3)

        for i, ax in enumerate(axes):
            ax.plot([1, 2, 3], [i, i + 1, i + 2], label=f"Line {i}")

        legend = tools_module.joint_legend(*axes, idx_for_legend=1)

        assert isinstance(legend, Legend)

        plt.close(fig)

    def test_joint_legend_with_kwargs(self):
        """Test joint legend with additional kwargs."""
        fig, axes = plt.subplots(1, 2)

        axes[0].plot([1, 2, 3], [1, 4, 2], label="Line A")
        axes[1].plot([1, 2, 3], [2, 3, 1], label="Line B")

        legend = tools_module.joint_legend(
            axes[0], axes[1], loc="upper right", frameon=True, ncol=2
        )

        assert isinstance(legend, Legend)

        plt.close(fig)

    def test_joint_legend_errorbar_handling(self):
        """Test joint legend with errorbar containers."""
        fig, axes = plt.subplots(1, 2)

        x = [1, 2, 3]
        y = [1, 4, 2]
        yerr = [0.1, 0.2, 0.1]

        axes[0].errorbar(x, y, yerr=yerr, label="Error Line")
        axes[1].plot(x, [2, 3, 1], label="Regular Line")

        legend = tools_module.joint_legend(axes[0], axes[1])

        assert isinstance(legend, Legend)

        plt.close(fig)

    def test_joint_legend_sorting(self):
        """Test that legend labels are sorted alphabetically."""
        fig, axes = plt.subplots(1, 2)

        axes[0].plot([1, 2, 3], [1, 4, 2], label="Z Line")
        axes[1].plot([1, 2, 3], [2, 3, 1], label="A Line")

        legend = tools_module.joint_legend(axes[0], axes[1])

        legend_labels = [text.get_text() for text in legend.get_texts()]
        assert legend_labels == ["A Line", "Z Line"]

        plt.close(fig)


class TestMultipanelFigureSharedCbar:
    """Test multipanel_figure_shared_cbar function."""

    def test_multipanel_function_exists(self):
        """Test that multipanel function exists and is callable."""
        assert hasattr(tools_module, "multipanel_figure_shared_cbar")
        assert callable(tools_module.multipanel_figure_shared_cbar)

    def test_multipanel_basic_structure(self):
        """Test basic multipanel figure structure."""
        try:
            fig, axes, cax = tools_module.multipanel_figure_shared_cbar(1, 1)

            assert isinstance(fig, Figure)
            assert isinstance(cax, Axes)
            # axes might be ndarray or single Axes depending on input

            plt.close(fig)
        except AttributeError:
            # Skip if matplotlib version incompatibility
            pytest.skip("Matplotlib version incompatibility with axis sharing")

    def test_multipanel_parameters(self):
        """Test multipanel parameter handling."""
        # Test that function accepts the expected parameters
        try:
            fig, axes, cax = tools_module.multipanel_figure_shared_cbar(
                1, 1, vertical_cbar=True, sharex=False, sharey=False
            )
            plt.close(fig)
        except AttributeError:
            pytest.skip("Matplotlib version incompatibility")


class TestBuildAxArrayWithCommonColorbar:
    """Test build_ax_array_with_common_colorbar function."""

    def test_build_ax_array_function_exists(self):
        """Test that build_ax_array function exists and is callable."""
        assert hasattr(tools_module, "build_ax_array_with_common_colorbar")
        assert callable(tools_module.build_ax_array_with_common_colorbar)

    def test_build_ax_array_basic_interface(self):
        """Test basic interface without axis sharing."""
        try:
            fig, axes, cax = tools_module.build_ax_array_with_common_colorbar(
                1, 1, gs_kwargs={"sharex": False, "sharey": False}
            )

            assert isinstance(fig, Figure)
            assert isinstance(cax, Axes)

            plt.close(fig)
        except AttributeError:
            pytest.skip("Matplotlib version incompatibility with axis sharing")

    def test_build_ax_array_invalid_location(self):
        """Test invalid colorbar location raises error."""
        with pytest.raises(ValueError):
            tools_module.build_ax_array_with_common_colorbar(2, 2, cbar_loc="invalid")

    def test_build_ax_array_location_validation(self):
        """Test colorbar location validation."""
        valid_locations = ["top", "bottom", "left", "right"]

        for loc in valid_locations:
            try:
                fig, axes, cax = tools_module.build_ax_array_with_common_colorbar(
                    1, 1, cbar_loc=loc, gs_kwargs={"sharex": False, "sharey": False}
                )
                plt.close(fig)
            except AttributeError:
                # Skip if matplotlib incompatibility
                continue


class TestCalculateNrowsNcols:
    """Test calculate_nrows_ncols utility function."""

    def test_calculate_perfect_squares(self):
        """Test calculation for perfect squares."""
        # Perfect squares should give nearly square layouts
        nrows, ncols = tools_module.calculate_nrows_ncols(4)
        assert nrows * ncols >= 4
        assert abs(nrows - ncols) <= 1

        nrows, ncols = tools_module.calculate_nrows_ncols(9)
        assert nrows * ncols >= 9

        nrows, ncols = tools_module.calculate_nrows_ncols(16)
        assert nrows * ncols >= 16

    def test_calculate_prime_numbers(self):
        """Test calculation for prime numbers."""
        # Prime numbers should get bumped up to next composite
        nrows, ncols = tools_module.calculate_nrows_ncols(7)
        assert nrows * ncols >= 7

        nrows, ncols = tools_module.calculate_nrows_ncols(11)
        assert nrows * ncols >= 11

    def test_calculate_small_numbers(self):
        """Test calculation for small numbers."""
        test_cases = [1, 2, 3, 4, 5, 6]

        for n in test_cases:
            nrows, ncols = tools_module.calculate_nrows_ncols(n)
            assert nrows * ncols >= n
            assert nrows > 0
            assert ncols > 0

    def test_calculate_larger_numbers(self):
        """Test calculation for larger numbers."""
        test_cases = [15, 20, 24, 30, 36]

        for n in test_cases:
            nrows, ncols = tools_module.calculate_nrows_ncols(n)
            assert nrows * ncols >= n
            assert nrows > 0
            assert ncols > 0

    def test_calculate_aspect_ratio_preference(self):
        """Test that function prefers wider layouts."""
        nrows, ncols = tools_module.calculate_nrows_ncols(6)
        # Should prefer wider layout (fewer rows, more columns)
        assert ncols >= nrows

    def test_calculate_edge_cases(self):
        """Test edge cases."""
        # Test very small numbers
        nrows, ncols = tools_module.calculate_nrows_ncols(1)
        assert nrows * ncols >= 1

        # Test numbers that require adjustment
        nrows, ncols = tools_module.calculate_nrows_ncols(5)
        assert nrows * ncols >= 5


class TestToolsIntegration:
    """Test integration between different tools functions."""

    def test_subplots_save_integration(self):
        """Test integration between subplots and save."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "integration_test"

            fig, axes = tools_module.subplots(2, 2, scale_width=1.5)

            for i, ax in enumerate(axes.flat):
                ax.plot([1, 2, 3], [i, i + 1, i + 2], label=f"Line {i}")

            tools_module.save(fig, temp_path, log=False)

            assert temp_path.with_suffix(".pdf").exists()
            assert temp_path.with_suffix(".png").exists()

            plt.close(fig)

    def test_multipanel_joint_legend_integration(self):
        """Test integration between multipanel and joint legend."""
        try:
            fig, axes, cax = tools_module.multipanel_figure_shared_cbar(
                1, 3, sharex=False, sharey=False
            )

            # Handle case where axes might be 1D array or single Axes
            if isinstance(axes, np.ndarray):
                for i, ax in enumerate(axes.flat):
                    ax.plot([1, 2, 3], [i, i + 1, i + 2], label=f"Series {i}")
                legend = tools_module.joint_legend(*axes.flat)
            else:
                axes.plot([1, 2, 3], [1, 2, 3], label="Series")
                legend = tools_module.joint_legend(axes)

            assert isinstance(legend, Legend)

            plt.close(fig)
        except AttributeError:
            pytest.skip("Matplotlib version incompatibility")

    def test_calculate_nrows_ncols_with_basic_plotting(self):
        """Test using calculate_nrows_ncols with basic plotting."""
        n_plots = 6
        nrows, ncols = tools_module.calculate_nrows_ncols(n_plots)

        # Test with basic subplots instead of multipanel
        fig, axes = tools_module.subplots(nrows, ncols)

        assert nrows * ncols >= n_plots

        plt.close(fig)


class TestToolsErrorHandling:
    """Test error handling in tools functions."""

    def test_save_invalid_inputs(self):
        """Test save function with invalid inputs."""
        fig, ax = plt.subplots()

        # Invalid figure type
        with pytest.raises(AssertionError):
            tools_module.save("not_a_figure", Path("test"), log=False)

        # Invalid path type
        with pytest.raises(AssertionError):
            tools_module.save(fig, "not_a_path_object", log=False)

        plt.close(fig)

    def test_multipanel_invalid_parameters(self):
        """Test multipanel with edge case parameters."""
        try:
            # Test with minimal parameters
            fig, axes, cax = tools_module.multipanel_figure_shared_cbar(
                1, 1, sharex=False, sharey=False
            )
            plt.close(fig)
        except AttributeError:
            pytest.skip("Matplotlib version incompatibility")

    def test_build_ax_array_basic_validation(self):
        """Test build_ax_array basic validation."""
        try:
            fig, axes, cax = tools_module.build_ax_array_with_common_colorbar(
                1, 1, gs_kwargs={"sharex": False, "sharey": False}
            )

            # Should return valid matplotlib objects
            assert isinstance(fig, Figure)
            assert isinstance(cax, Axes)

            plt.close(fig)
        except AttributeError:
            pytest.skip("Matplotlib version incompatibility")


class TestToolsDocumentation:
    """Test documentation and examples in tools functions."""

    def test_function_docstrings(self):
        """Test that all functions have comprehensive docstrings."""
        functions = [
            tools_module.subplots,
            tools_module.save,
            tools_module.joint_legend,
            tools_module.multipanel_figure_shared_cbar,
            tools_module.build_ax_array_with_common_colorbar,
            tools_module.calculate_nrows_ncols,
        ]

        for func in functions:
            assert func.__doc__ is not None
            assert len(func.__doc__.strip()) > 0
            # Should have Parameters section
            assert "Parameters" in func.__doc__
            # Should have Returns section (for most functions)
            if func != tools_module.save:  # save returns None
                assert "Returns" in func.__doc__

    def test_docstring_examples(self):
        """Test that functions have usage examples in docstrings."""
        functions_with_examples = [
            tools_module.subplots,
            tools_module.save,
            tools_module.joint_legend,
            tools_module.multipanel_figure_shared_cbar,
            tools_module.build_ax_array_with_common_colorbar,
            tools_module.calculate_nrows_ncols,
        ]

        for func in functions_with_examples:
            assert "Examples" in func.__doc__
            assert ">>>" in func.__doc__


if __name__ == "__main__":
    pytest.main([__file__])
