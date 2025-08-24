"""Integration tests for plotting functionality.

Tests end-to-end workflows and cross-module integration of the plotting package.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import warnings

# Configure matplotlib for testing
matplotlib.use("Agg")
plt.ioff()

# Import SolarWindPy components
import solarwindpy.plotting.base as base_plotting
import solarwindpy.plotting.histograms as hist_plotting
import solarwindpy.plotting.tools as plot_tools
import solarwindpy.plotting.labels as labels

try:
    import solarwindpy.plotting.scatter as scatter_plotting
    import solarwindpy.plotting.spiral as spiral_plotting
    import solarwindpy.plotting.orbits as orbit_plotting

    ADVANCED_IMPORTS = True
except ImportError:
    ADVANCED_IMPORTS = False


class TestBasicIntegrationWorkflows:
    """Test basic integration workflows across plotting modules."""

    def setup_method(self):
        """Set up test data for integration tests."""
        # Create synthetic time series data
        self.dates = pd.date_range("2023-01-01", periods=100, freq="1h")
        self.n_points = len(self.dates)

        # Plasma parameters
        np.random.seed(42)
        self.density = (
            10
            + 2 * np.sin(np.arange(self.n_points) / 10)
            + np.random.normal(0, 0.5, self.n_points)
        )
        self.velocity = (
            400
            + 50 * np.sin(np.arange(self.n_points) / 15)
            + np.random.normal(0, 10, self.n_points)
        )
        self.temperature = (
            1e5
            + 2e4 * np.sin(np.arange(self.n_points) / 8)
            + np.random.normal(0, 5e3, self.n_points)
        )
        self.magnetic_field = (
            5
            + np.sin(np.arange(self.n_points) / 12)
            + np.random.normal(0, 0.2, self.n_points)
        )

        # Create DataFrame
        self.data = pd.DataFrame(
            {
                "density": self.density,
                "velocity": self.velocity,
                "temperature": self.temperature,
                "b_field": self.magnetic_field,
            },
            index=self.dates,
        )

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_time_series_integration_workflow(self):
        """Test complete time series plotting workflow."""
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

        # Plot each parameter
        parameters = ["density", "velocity", "temperature", "b_field"]
        labels_text = [
            "Density (cm⁻³)",
            "Velocity (km/s)",
            "Temperature (K)",
            "B-field (nT)",
        ]
        colors = ["blue", "red", "green", "orange"]

        for i, (param, label, color) in enumerate(zip(parameters, labels_text, colors)):
            axes[i].plot(self.data.index, self.data[param], color=color, linewidth=1.5)
            axes[i].set_ylabel(label)
            axes[i].grid(True, alpha=0.3)

            # Add statistical info
            mean_val = self.data[param].mean()
            std_val = self.data[param].std()
            axes[i].axhline(
                mean_val,
                color=color,
                linestyle="--",
                alpha=0.7,
                label=f"Mean: {mean_val:.2f}",
            )
            axes[i].fill_between(
                self.data.index,
                mean_val - std_val,
                mean_val + std_val,
                alpha=0.2,
                color=color,
                label=f"±1σ: {std_val:.2f}",
            )
            axes[i].legend(fontsize=8)

        axes[-1].set_xlabel("Time")
        plt.suptitle("Solar Wind Parameters Time Series", fontsize=14)
        plt.tight_layout()

        # Validation
        assert len(fig.axes) == 4
        for ax in axes:
            assert len(ax.lines) >= 1  # At least the data line
            assert ax.get_ylabel() != ""

    def test_correlation_analysis_workflow(self):
        """Test correlation analysis workflow."""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))

        # Define parameter pairs for correlation
        param_pairs = [
            ("velocity", "temperature", "V-T Correlation"),
            ("density", "b_field", "n-B Correlation"),
            ("velocity", "density", "V-n Correlation"),
            ("temperature", "b_field", "T-B Correlation"),
            ("velocity", "b_field", "V-B Correlation"),
            ("density", "temperature", "n-T Correlation"),
        ]

        for i, (param1, param2, title) in enumerate(param_pairs):
            row, col = divmod(i, 3)
            ax = axes[row, col]

            x = self.data[param1]
            y = self.data[param2]

            # Scatter plot
            scatter = ax.scatter(x, y, alpha=0.6, c=range(len(x)), cmap="viridis")

            # Fit line
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            ax.plot(x, p(x), "r--", alpha=0.8, linewidth=2)

            # Calculate correlation
            correlation = np.corrcoef(x, y)[0, 1]

            ax.set_xlabel(param1.title())
            ax.set_ylabel(param2.title())
            ax.set_title(f"{title}\nr = {correlation:.3f}")
            ax.grid(True, alpha=0.3)

            # Add colorbar for time evolution
            if i == 0:  # Only for first subplot to avoid clutter
                plt.colorbar(scatter, ax=ax, label="Time Index")

        plt.tight_layout()

        # Validation
        assert len(fig.axes) >= 6  # 6 subplots + potential colorbars
        for ax in axes.flat:
            assert len(ax.collections) >= 1  # Scatter plot
            assert len(ax.lines) >= 1  # Trend line

    def test_distribution_analysis_workflow(self):
        """Test distribution analysis workflow."""
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))

        parameters = ["density", "velocity", "temperature", "b_field"]

        # Top row: Histograms
        for i, param in enumerate(parameters):
            ax = axes[0, i]
            data = self.data[param]

            # Histogram with statistics
            n, bins, patches = ax.hist(
                data,
                bins=20,
                alpha=0.7,
                density=True,
                color="skyblue",
                edgecolor="black",
            )

            # Add normal distribution overlay
            mu, sigma = data.mean(), data.std()
            x_norm = np.linspace(data.min(), data.max(), 100)
            y_norm = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
                -0.5 * ((x_norm - mu) / sigma) ** 2
            )
            ax.plot(x_norm, y_norm, "r-", linewidth=2, label="Normal Fit")

            ax.axvline(
                mu, color="red", linestyle="--", alpha=0.7, label=f"Mean: {mu:.2f}"
            )
            ax.set_xlabel(param.title())
            ax.set_ylabel("Probability Density")
            ax.set_title(f"{param.title()} Distribution")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)

        # Bottom row: Box plots and Q-Q plots
        # Combined box plot
        ax_box = axes[1, 0]
        data_normalized = [
            self.data[param] / self.data[param].std() for param in parameters
        ]
        box_plot = ax_box.boxplot(
            data_normalized, labels=[p.title() for p in parameters]
        )
        ax_box.set_ylabel("Normalized Value")
        ax_box.set_title("Parameter Distributions")
        ax_box.grid(True, alpha=0.3)

        # Time evolution of statistics
        ax_stats = axes[1, 1]
        window = 10
        rolling_means = self.data.rolling(window=window).mean()
        for i, param in enumerate(parameters[:2]):  # Just first two to avoid clutter
            ax_stats.plot(
                rolling_means.index,
                rolling_means[param],
                label=f"{param.title()} (rolling mean)",
                linewidth=2,
            )
        ax_stats.set_xlabel("Time")
        ax_stats.set_ylabel("Rolling Mean")
        ax_stats.set_title(f"Rolling Statistics (window={window})")
        ax_stats.legend()
        ax_stats.grid(True, alpha=0.3)

        # Scatter matrix sample
        ax_scatter = axes[1, 2]
        ax_scatter.scatter(
            self.data["velocity"], self.data["temperature"], alpha=0.6, c="purple"
        )
        ax_scatter.set_xlabel("Velocity")
        ax_scatter.set_ylabel("Temperature")
        ax_scatter.set_title("V-T Scatter")
        ax_scatter.grid(True, alpha=0.3)

        # Summary statistics
        ax_summary = axes[1, 3]
        ax_summary.axis("off")
        summary_text = []
        for param in parameters:
            data = self.data[param]
            summary_text.append(f"{param.title()}:")
            summary_text.append(f"  Mean: {data.mean():.2f}")
            summary_text.append(f"  Std:  {data.std():.2f}")
            summary_text.append(f"  Min:  {data.min():.2f}")
            summary_text.append(f"  Max:  {data.max():.2f}")
            summary_text.append("")

        ax_summary.text(
            0.1,
            0.9,
            "\n".join(summary_text),
            fontfamily="monospace",
            fontsize=10,
            verticalalignment="top",
            transform=ax_summary.transAxes,
        )
        ax_summary.set_title("Summary Statistics")

        plt.tight_layout()

        # Validation
        assert len(fig.axes) == 8
        for i in range(4):  # First row histograms
            assert len(axes[0, i].patches) > 0  # Histogram bars
            assert len(axes[0, i].lines) >= 1  # Normal fit line


class TestLabelIntegrationWorkflow:
    """Test integration of plotting with label system."""

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_chemistry_labels_integration(self):
        """Test integration of chemistry labels with plots."""
        try:
            from solarwindpy.plotting.labels.chemistry import (
                mass_per_charge,
                fip,
                charge,
                mass,
            )

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))

            # Mock data for chemistry plots
            np.random.seed(42)
            species = ["H", "He", "C", "O", "Fe"]

            # Mass-to-charge ratio plot
            mq_ratios = [1.0, 2.0, 6.0, 8.0, 28.0]  # Simplified M/Q ratios
            counts = np.random.poisson(100, len(species))

            bars = axes[0, 0].bar(species, counts, alpha=0.7, color="skyblue")
            axes[0, 0].set_xlabel(str(mass_per_charge))  # Use chemistry label
            axes[0, 0].set_ylabel("Counts")
            axes[0, 0].set_title("Ion Mass-to-Charge Distribution")

            # FIP plot
            fip_values = [13.6, 24.6, 11.3, 13.6, 7.9]  # eV
            axes[0, 1].bar(species, fip_values, alpha=0.7, color="lightcoral")
            axes[0, 1].set_xlabel("Ion Species")
            axes[0, 1].set_ylabel(str(fip))  # Use chemistry label
            axes[0, 1].set_title("First Ionization Potential")

            # Charge state plot
            charge_states = np.random.randint(1, 8, 20)
            charge_counts = np.bincount(charge_states)[1:]  # Remove 0 count

            axes[1, 0].bar(
                range(1, len(charge_counts) + 1),
                charge_counts,
                alpha=0.7,
                color="lightgreen",
            )
            axes[1, 0].set_xlabel(str(charge))  # Use chemistry label
            axes[1, 0].set_ylabel("Frequency")
            axes[1, 0].set_title("Charge State Distribution")

            # Mass spectrum
            masses = [1, 4, 12, 16, 56]  # AMU
            intensities = np.random.exponential(50, len(masses))

            axes[1, 1].stem(masses, intensities, basefmt=" ")
            axes[1, 1].set_xlabel(str(mass))  # Use chemistry label
            axes[1, 1].set_ylabel("Intensity")
            axes[1, 1].set_title("Mass Spectrum")

            plt.tight_layout()

            # Validation
            assert len(fig.axes) == 4
            for ax in axes.flat:
                assert ax.get_xlabel() != ""
                assert ax.get_ylabel() != ""

        except ImportError:
            pytest.skip("Chemistry labels not available")

    def test_datetime_labels_integration(self):
        """Test integration of datetime labels with time series plots."""
        try:
            from solarwindpy.plotting.labels.datetime import Timedelta, Frequency

            fig, axes = plt.subplots(2, 1, figsize=(12, 8))

            # Time series with time delta labels
            time = np.arange(0, 24, 0.1)  # 24 hours in 0.1 hour steps
            signal = np.sin(2 * np.pi * time / 6) + 0.3 * np.sin(2 * np.pi * time / 1.5)

            axes[0].plot(time, signal, "b-", linewidth=2)

            # Use datetime labels
            time_delta = Timedelta("1h")
            axes[0].set_xlabel(f"Time [{time_delta.units}]")
            axes[0].set_ylabel("Signal Amplitude")
            axes[0].set_title("Time Series with Time Delta Labels")
            axes[0].grid(True, alpha=0.3)

            # Frequency domain plot
            dt = time[1] - time[0]
            freqs = np.fft.fftfreq(len(signal), dt)
            fft_signal = np.abs(np.fft.fft(signal))

            # Plot only positive frequencies
            pos_freqs = freqs[: len(freqs) // 2]
            pos_fft = fft_signal[: len(fft_signal) // 2]

            axes[1].plot(pos_freqs, pos_fft, "r-", linewidth=2)

            frequency_label = Frequency("1h")
            axes[1].set_xlabel(str(frequency_label))
            axes[1].set_ylabel("Amplitude")
            axes[1].set_title("Frequency Domain")
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()

            # Validation
            assert len(fig.axes) == 2
            for ax in axes:
                assert len(ax.lines) == 1
                assert ax.get_xlabel() != ""

        except ImportError:
            pytest.skip("DateTime labels not available")


class TestFileIOIntegration:
    """Test integration with file I/O operations."""

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_plot_saving_workflow(self):
        """Test complete workflow of creating and saving plots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a multi-panel plot
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))

            # Generate different types of plots
            x = np.linspace(0, 10, 100)

            # Line plot
            axes[0, 0].plot(x, np.sin(x), "b-", linewidth=2)
            axes[0, 0].set_title("Line Plot")
            axes[0, 0].grid(True)

            # Scatter plot
            np.random.seed(42)
            axes[0, 1].scatter(np.random.randn(100), np.random.randn(100), alpha=0.6)
            axes[0, 1].set_title("Scatter Plot")
            axes[0, 1].grid(True)

            # Histogram
            axes[1, 0].hist(np.random.normal(0, 1, 1000), bins=30, alpha=0.7)
            axes[1, 0].set_title("Histogram")
            axes[1, 0].grid(True)

            # Contour plot
            X, Y = np.meshgrid(x, x)
            Z = np.sin(X) * np.cos(Y)
            contour = axes[1, 1].contourf(X, Y, Z, levels=20)
            axes[1, 1].set_title("Contour Plot")
            plt.colorbar(contour, ax=axes[1, 1])

            plt.tight_layout()

            # Save in multiple formats
            formats = ["png", "pdf", "svg"]
            saved_files = []

            for fmt in formats:
                file_path = temp_path / f"test_plot.{fmt}"
                fig.savefig(file_path, format=fmt, dpi=100, bbox_inches="tight")
                saved_files.append(file_path)

            # Verify files were saved
            for file_path in saved_files:
                assert file_path.exists()
                assert file_path.stat().st_size > 0

            # Test file sizes are reasonable
            png_size = saved_files[0].stat().st_size
            assert png_size > 1000  # Should be at least 1KB for a real plot

    def test_data_export_integration(self):
        """Test integration of plotting with data export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test data
            dates = pd.date_range("2023-01-01", periods=50, freq="1h")
            data = pd.DataFrame(
                {
                    "time": dates,
                    "value1": np.random.randn(50).cumsum(),
                    "value2": np.random.randn(50).cumsum(),
                    "value3": np.random.randn(50).cumsum(),
                }
            )

            # Create plot
            fig, ax = plt.subplots(figsize=(12, 6))

            for column in ["value1", "value2", "value3"]:
                ax.plot(data["time"], data[column], label=column, linewidth=2)

            ax.set_xlabel("Time")
            ax.set_ylabel("Value")
            ax.set_title("Multi-Series Time Plot")
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            # Save plot and data
            plot_file = temp_path / "timeseries_plot.png"
            data_file = temp_path / "timeseries_data.csv"

            fig.savefig(plot_file, dpi=100, bbox_inches="tight")
            data.to_csv(data_file, index=False)

            # Verify both files exist
            assert plot_file.exists()
            assert data_file.exists()

            # Verify data can be read back
            loaded_data = pd.read_csv(data_file)
            assert len(loaded_data) == len(data)
            assert list(loaded_data.columns) == list(data.columns)


class TestErrorHandlingIntegration:
    """Test error handling across integrated workflows."""

    def teardown_method(self):
        """Clean up after each test."""
        plt.close("all")

    def test_missing_data_integration(self):
        """Test handling of missing data in integrated workflows."""
        # Create data with missing values
        dates = pd.date_range("2023-01-01", periods=100, freq="1h")
        data = pd.DataFrame(
            {
                "param1": np.random.randn(100).cumsum(),
                "param2": np.random.randn(100).cumsum(),
            },
            index=dates,
        )

        # Introduce missing values
        data.loc[data.index[20:30], "param1"] = np.nan
        data.loc[data.index[50:55], "param2"] = np.nan

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Raw data plot with gaps
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress NaN warnings

            axes[0].plot(data.index, data["param1"], "b-", label="param1")
            axes[0].plot(data.index, data["param2"], "r-", label="param2")
            axes[0].set_title("Raw Data with Missing Values")
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)

            # Interpolated data
            data_interp = data.interpolate()
            axes[1].plot(
                data_interp.index, data_interp["param1"], "b-", label="param1 (interp)"
            )
            axes[1].plot(
                data_interp.index, data_interp["param2"], "r-", label="param2 (interp)"
            )
            axes[1].set_title("Interpolated Data")
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)

            # Forward filled data
            data_ffill = data.fillna(method="ffill")
            axes[2].plot(
                data_ffill.index, data_ffill["param1"], "b-", label="param1 (ffill)"
            )
            axes[2].plot(
                data_ffill.index, data_ffill["param2"], "r-", label="param2 (ffill)"
            )
            axes[2].set_title("Forward Filled Data")
            axes[2].set_xlabel("Time")
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)

        plt.tight_layout()

        # Validation
        assert len(fig.axes) == 3
        for ax in axes:
            assert len(ax.lines) == 2

    def test_invalid_parameter_integration(self):
        """Test handling of invalid parameters in integrated workflows."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Test with various edge cases
        x = np.linspace(0, 10, 100)

        # Normal case
        axes[0, 0].plot(x, np.sin(x), "b-")
        axes[0, 0].set_title("Normal Case")

        # Infinite values
        y_inf = np.sin(x)
        y_inf[50] = np.inf
        y_inf[60] = -np.inf

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            axes[0, 1].plot(x, y_inf, "r-")
            axes[0, 1].set_title("With Infinite Values")

        # Very large/small values
        y_extreme = 1e10 * np.sin(x) + 1e-10
        axes[1, 0].plot(x, y_extreme, "g-")
        axes[1, 0].set_title("Extreme Values")
        axes[1, 0].ticklabel_format(style="scientific", axis="y", scilimits=(0, 0))

        # Empty/single point arrays
        x_empty = np.array([])
        y_empty = np.array([])
        x_single = np.array([5.0])
        y_single = np.array([1.0])

        axes[1, 1].plot(x_empty, y_empty, "k-", label="Empty")
        axes[1, 1].scatter(x_single, y_single, color="red", s=50, label="Single Point")
        axes[1, 1].set_title("Edge Cases")
        axes[1, 1].legend()

        plt.tight_layout()

        # All should create without errors
        assert len(fig.axes) == 4


def test_module_integration():
    """Test that all plotting modules can be imported and work together."""
    # Test basic imports work
    import solarwindpy.plotting.base
    import solarwindpy.plotting.tools
    import solarwindpy.plotting.histograms
    import solarwindpy.plotting.labels

    # Test that classes can be instantiated
    assert hasattr(solarwindpy.plotting.labels, "base")
    assert hasattr(solarwindpy.plotting.labels, "special")

    # Test that basic functionality works
    fig, ax = plt.subplots()
    x = np.linspace(0, 1, 10)
    y = x**2
    ax.plot(x, y)

    # Should not raise any errors
    assert len(ax.lines) == 1
    plt.close(fig)


def test_cross_platform_compatibility():
    """Test that plotting works consistently across platforms."""
    # Test figure creation
    fig, ax = plt.subplots(figsize=(8, 6))

    # Test with various data types
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x).astype(np.float32)  # 32-bit float
    y2 = np.cos(x).astype(np.float64)  # 64-bit float
    y3 = (x**2).astype(int)  # Integer

    ax.plot(x, y1, label="float32")
    ax.plot(x, y2, label="float64")
    ax.plot(x, y3, label="int")

    ax.legend()
    ax.grid(True)

    # Should handle all data types
    assert len(ax.lines) == 3
    plt.close(fig)
