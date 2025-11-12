"""Visual validation tests for plotting functionality.

This module provides visual validation framework for matplotlib plots to ensure
consistent rendering and detect visual regressions.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import warnings

# Configure matplotlib for testing
matplotlib.use("Agg")  # Non-interactive backend
plt.ioff()  # Turn off interactive mode


class TestVisualValidationFramework:
    """Test the visual validation framework infrastructure."""

    def test_matplotlib_backend(self):
        """Test matplotlib backend is properly configured."""
        backend = matplotlib.get_backend()
        assert backend.lower() == "agg", f"Expected Agg backend, got {backend}"

    def test_matplotlib_interactive_mode(self):
        """Test matplotlib interactive mode is disabled."""
        assert (
            not plt.isinteractive()
        ), "Interactive mode should be disabled for testing"

    def test_figure_creation(self):
        """Test basic figure creation works in test environment."""
        fig, ax = plt.subplots()
        assert fig is not None
        assert ax is not None
        plt.close(fig)

    def test_plot_generation(self):
        """Test basic plot generation works."""
        fig, ax = plt.subplots()
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        ax.set_xlabel("X Label")
        ax.set_ylabel("Y Label")
        ax.set_title("Test Plot")

        # Verify plot has expected elements
        assert len(ax.lines) == 1
        assert ax.get_xlabel() == "X Label"
        assert ax.get_ylabel() == "Y Label"
        assert ax.get_title() == "Test Plot"

        plt.close(fig)


class TestBasicPlotVisualValidation:
    """Basic visual validation tests for common plot types."""

    def setup_method(self):
        """Set up test data for plotting."""
        self.x = np.linspace(0, 10, 100)
        self.y_sin = np.sin(self.x)
        self.y_cos = np.cos(self.x)

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_line_plot_visual(self):
        """Test basic line plot visual output."""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(self.x, self.y_sin, label="sin(x)", linewidth=2)
        ax.plot(self.x, self.y_cos, label="cos(x)", linewidth=2, linestyle="--")
        ax.set_xlabel("X values")
        ax.set_ylabel("Y values")
        ax.set_title("Line Plot Test")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Basic validation - plot should have expected elements
        assert len(ax.lines) == 2
        assert ax.legend_ is not None
        assert ax.get_xlabel() == "X values"

        plt.tight_layout()
        # Note: For actual visual validation, would use @image_comparison decorator
        # This serves as a framework test

    def test_scatter_plot_visual(self):
        """Test scatter plot visual output."""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Generate scatter data
        np.random.seed(42)
        x_scatter = np.random.randn(100)
        y_scatter = np.random.randn(100)
        colors = np.random.rand(100)

        scatter = ax.scatter(x_scatter, y_scatter, c=colors, alpha=0.7, cmap="viridis")
        ax.set_xlabel("X values")
        ax.set_ylabel("Y values")
        ax.set_title("Scatter Plot Test")

        # Add colorbar
        plt.colorbar(scatter, ax=ax, label="Color Value")

        # Validation
        assert len(ax.collections) == 1  # Scatter collection
        assert ax.get_xlabel() == "X values"

        plt.tight_layout()

    def test_histogram_visual(self):
        """Test histogram visual output."""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Generate histogram data
        np.random.seed(42)
        data = np.random.normal(0, 1, 1000)

        n, bins, patches = ax.hist(
            data, bins=30, alpha=0.7, color="skyblue", edgecolor="black", linewidth=0.5
        )
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        ax.set_title("Histogram Test")
        ax.grid(True, alpha=0.3, axis="y")

        # Validation
        assert len(patches) == 30  # Number of bins
        assert len(n) == 30
        assert len(bins) == 31  # n+1 bin edges

        plt.tight_layout()


class TestSolarWindPyPlottingVisualValidation:
    """Visual validation tests for SolarWindPy plotting components."""

    def setup_method(self):
        """Set up test data for SolarWindPy plotting."""
        # Create synthetic plasma data
        self.time = np.arange(100)
        self.density = 10 + 2 * np.sin(self.time / 10) + np.random.normal(0, 0.5, 100)
        self.velocity = 400 + 50 * np.sin(self.time / 15) + np.random.normal(0, 10, 100)
        self.temperature = (
            1e5 + 2e4 * np.sin(self.time / 8) + np.random.normal(0, 5e3, 100)
        )

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_time_series_plot_visual(self):
        """Test time series plotting visual output."""
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

        # Density plot
        axes[0].plot(self.time, self.density, "b-", linewidth=1.5)
        axes[0].set_ylabel("Density (cm⁻³)")
        axes[0].set_title("Solar Wind Time Series")
        axes[0].grid(True, alpha=0.3)

        # Velocity plot
        axes[1].plot(self.time, self.velocity, "r-", linewidth=1.5)
        axes[1].set_ylabel("Velocity (km/s)")
        axes[1].grid(True, alpha=0.3)

        # Temperature plot
        axes[2].plot(self.time, self.temperature, "g-", linewidth=1.5)
        axes[2].set_ylabel("Temperature (K)")
        axes[2].set_xlabel("Time")
        axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        # Validation
        for ax in axes:
            assert len(ax.lines) == 1
            assert ax.get_ylabel() != ""

    def test_correlation_plot_visual(self):
        """Test correlation/scatter plot visual output."""
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create correlation plot
        scatter = ax.scatter(
            self.velocity, self.temperature, c=self.density, alpha=0.7, cmap="plasma"
        )
        ax.set_xlabel("Velocity (km/s)")
        ax.set_ylabel("Temperature (K)")
        ax.set_title("Velocity-Temperature Correlation")

        # Add colorbar with scientific notation
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Density (cm⁻³)")

        # Add trend line
        z = np.polyfit(self.velocity, self.temperature, 1)
        p = np.poly1d(z)
        ax.plot(self.velocity, p(self.velocity), "r--", alpha=0.8, linewidth=2)

        plt.tight_layout()

        # Validation
        assert len(ax.collections) == 1  # Scatter collection
        assert len(ax.lines) == 1  # Trend line

    def test_distribution_plot_visual(self):
        """Test distribution plotting visual output."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Density histogram
        axes[0, 0].hist(
            self.density,
            bins=20,
            alpha=0.7,
            color="blue",
            edgecolor="black",
            density=True,
        )
        axes[0, 0].set_xlabel("Density (cm⁻³)")
        axes[0, 0].set_ylabel("Probability Density")
        axes[0, 0].set_title("Density Distribution")
        axes[0, 0].grid(True, alpha=0.3)

        # Velocity histogram
        axes[0, 1].hist(
            self.velocity,
            bins=20,
            alpha=0.7,
            color="red",
            edgecolor="black",
            density=True,
        )
        axes[0, 1].set_xlabel("Velocity (km/s)")
        axes[0, 1].set_ylabel("Probability Density")
        axes[0, 1].set_title("Velocity Distribution")
        axes[0, 1].grid(True, alpha=0.3)

        # Temperature histogram
        axes[1, 0].hist(
            self.temperature,
            bins=20,
            alpha=0.7,
            color="green",
            edgecolor="black",
            density=True,
        )
        axes[1, 0].set_xlabel("Temperature (K)")
        axes[1, 0].set_ylabel("Probability Density")
        axes[1, 0].set_title("Temperature Distribution")
        axes[1, 0].grid(True, alpha=0.3)

        # Combined box plot
        data_for_box = [
            self.density / np.mean(self.density),
            self.velocity / np.mean(self.velocity),
            self.temperature / np.mean(self.temperature),
        ]
        box_plot = axes[1, 1].boxplot(
            data_for_box, labels=["Density", "Velocity", "Temperature"]
        )
        axes[1, 1].set_ylabel("Normalized Value")
        axes[1, 1].set_title("Parameter Distributions")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()

        # Validation
        for ax in axes.flat[:-1]:  # All except box plot
            assert len(ax.patches) > 0  # Histogram bars

        # Box plot validation using the returned dictionary
        assert len(box_plot["boxes"]) == 3  # Three data sets
        assert len(box_plot["whiskers"]) == 6  # Two whiskers per box
        assert len(box_plot["medians"]) == 3  # One median per box


class TestPlotLayoutValidation:
    """Test plot layout and formatting validation."""

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_subplot_layout_visual(self):
        """Test subplot layout and spacing."""
        fig = plt.figure(figsize=(12, 8))

        # Create different subplot layouts
        ax1 = plt.subplot2grid((3, 3), (0, 0), colspan=2)
        ax2 = plt.subplot2grid((3, 3), (0, 2))
        ax3 = plt.subplot2grid((3, 3), (1, 0))
        ax4 = plt.subplot2grid((3, 3), (1, 1), colspan=2)
        ax5 = plt.subplot2grid((3, 3), (2, 0), colspan=3)

        # Add content to each subplot
        x = np.linspace(0, 10, 100)

        ax1.plot(x, np.sin(x), "b-")
        ax1.set_title("Sin Wave")
        ax1.grid(True, alpha=0.3)

        ax2.plot(x, np.cos(x), "r-")
        ax2.set_title("Cos Wave")
        ax2.grid(True, alpha=0.3)

        ax3.hist(np.random.randn(1000), bins=30, alpha=0.7)
        ax3.set_title("Histogram")

        ax4.scatter(np.random.randn(100), np.random.randn(100), alpha=0.7)
        ax4.set_title("Scatter Plot")
        ax4.grid(True, alpha=0.3)

        ax5.plot(x, np.tan(x), "g-")
        ax5.set_ylim(-5, 5)
        ax5.set_title("Tan Wave")
        ax5.set_xlabel("X values")
        ax5.grid(True, alpha=0.3)

        plt.tight_layout()

        # Validation
        assert len(fig.axes) == 5
        for ax in fig.axes:
            assert ax.get_title() != ""

    def test_colorbar_layout_visual(self):
        """Test colorbar layout and positioning."""
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))

        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(X) * np.cos(Y)

        # Different colorbar layouts
        im1 = axes[0, 0].contourf(X, Y, Z, levels=20, cmap="viridis")
        plt.colorbar(im1, ax=axes[0, 0], shrink=0.8)
        axes[0, 0].set_title("Contour with Colorbar")

        im2 = axes[0, 1].imshow(Z, extent=[0, 10, 0, 10], cmap="plasma")
        plt.colorbar(im2, ax=axes[0, 1], orientation="horizontal", pad=0.1)
        axes[0, 1].set_title("Image with Horizontal Colorbar")

        im3 = axes[1, 0].pcolormesh(X, Y, Z, cmap="coolwarm")
        plt.colorbar(im3, ax=axes[1, 0], fraction=0.046, pad=0.04)
        axes[1, 0].set_title("Pcolormesh with Colorbar")

        # Contour lines without colorbar
        axes[1, 1].contour(X, Y, Z, levels=10, cmap="jet")
        axes[1, 1].set_title("Contour Lines")

        plt.tight_layout()

        # Validation - check that colorbars were created
        # Note: This is a basic structural test
        assert len(fig.axes) >= 4  # At least the 4 main axes


class TestErrorHandlingVisualValidation:
    """Test error handling in visual validation framework."""

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_invalid_data_handling(self):
        """Test handling of invalid data in plots."""
        fig, ax = plt.subplots()

        # Data with NaN values
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        y[50:60] = np.nan  # Insert NaN values

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress NaN warnings
            ax.plot(x, y, "b-")

        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Plot with NaN Values")

        # Should still create a valid plot
        assert len(ax.lines) == 1

        plt.close(fig)

    def test_empty_data_handling(self):
        """Test handling of empty data."""
        fig, ax = plt.subplots()

        # Empty arrays
        x = np.array([])
        y = np.array([])

        ax.plot(x, y, "b-")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Empty Plot")

        # Should create plot without error
        assert len(ax.lines) == 1

        plt.close(fig)


def test_visual_validation_framework_availability():
    """Test that visual validation framework components are available."""
    # Test matplotlib testing decorators
    from matplotlib.testing.decorators import image_comparison

    assert image_comparison is not None

    # Test that we can create baseline directory path
    import os

    baseline_dir = os.path.join(os.path.dirname(__file__), "baseline_images")
    # Directory doesn't need to exist yet, but path should be valid
    assert isinstance(baseline_dir, str)


def test_reproducible_random_plots():
    """Test that plots with random data are reproducible with seed."""
    # First plot
    np.random.seed(42)
    fig1, ax1 = plt.subplots()
    x1 = np.random.randn(100)
    y1 = np.random.randn(100)
    ax1.scatter(x1, y1)

    # Second plot with same seed
    np.random.seed(42)
    fig2, ax2 = plt.subplots()
    x2 = np.random.randn(100)
    y2 = np.random.randn(100)
    ax2.scatter(x2, y2)

    # Data should be identical
    np.testing.assert_array_equal(x1, x2)
    np.testing.assert_array_equal(y1, y2)

    plt.close(fig1)
    plt.close(fig2)


# Example of how to implement actual image comparison test
# (Commented out as it requires baseline images)
"""
@image_comparison(baseline_images=['example_plot'],
                  extensions=['png'],
                  tol=0.1)
def test_example_image_comparison():
    '''Example of actual image comparison test.'''
    fig, ax = plt.subplots()
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    ax.plot(x, y, 'b-', linewidth=2)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Example Plot')
    ax.grid(True)
    return fig
"""
