"""Performance benchmarks for plotting functionality.

Tests performance characteristics and scalability of plotting operations with large
datasets typical in space physics applications.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import time
import gc
import psutil
import os
import warnings

# Optional import for memory profiling
try:
    from memory_profiler import profile

    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False

    def profile(func):
        return func


# Configure matplotlib for testing
matplotlib.use("Agg")
plt.ioff()


class TestBasicPerformance:
    """Test basic performance characteristics of plotting operations."""

    def setup_method(self):
        """Set up performance test environment."""
        # Force garbage collection before tests
        gc.collect()
        self.process = psutil.Process(os.getpid())

    def teardown_method(self):
        """Clean up after performance tests."""
        plt.close("all")
        gc.collect()

    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def test_line_plot_performance(self):
        """Test line plot performance with various data sizes."""
        data_sizes = [1000, 10000, 100000, 500000]
        times = []

        for size in data_sizes:
            x = np.linspace(0, 10, size)
            y = np.sin(x) + 0.1 * np.random.randn(size)

            start_time = time.time()

            fig, ax = plt.subplots()
            ax.plot(x, y)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Line Plot - {size:,} points")

            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)

            plt.close(fig)

            # Performance assertions
            if size <= 10000:
                assert (
                    elapsed < 1.0
                ), f"Plot with {size} points took {elapsed:.3f}s (expected < 1.0s)"
            elif size <= 100000:
                assert (
                    elapsed < 5.0
                ), f"Plot with {size} points took {elapsed:.3f}s (expected < 5.0s)"
            else:
                assert (
                    elapsed < 15.0
                ), f"Plot with {size} points took {elapsed:.3f}s (expected < 15.0s)"

        # Test that performance scales reasonably
        assert len(times) == len(data_sizes)
        print(f"Line plot timing: {list(zip(data_sizes, times))}")

    def test_scatter_plot_performance(self):
        """Test scatter plot performance with various data sizes."""
        data_sizes = [1000, 5000, 25000, 50000]  # Smaller sizes for scatter
        times = []

        for size in data_sizes:
            np.random.seed(42)
            x = np.random.randn(size)
            y = np.random.randn(size)
            colors = np.random.rand(size)

            start_time = time.time()

            fig, ax = plt.subplots()
            scatter = ax.scatter(x, y, c=colors, alpha=0.6, cmap="viridis")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Scatter Plot - {size:,} points")
            plt.colorbar(scatter, ax=ax)

            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)

            plt.close(fig)

            # Performance assertions (scatter plots are slower)
            if size <= 5000:
                assert (
                    elapsed < 2.0
                ), f"Scatter with {size} points took {elapsed:.3f}s (expected < 2.0s)"
            elif size <= 25000:
                assert (
                    elapsed < 10.0
                ), f"Scatter with {size} points took {elapsed:.3f}s (expected < 10.0s)"
            else:
                assert (
                    elapsed < 30.0
                ), f"Scatter with {size} points took {elapsed:.3f}s (expected < 30.0s)"

        print(f"Scatter plot timing: {list(zip(data_sizes, times))}")

    def test_histogram_performance(self):
        """Test histogram performance with large datasets."""
        data_sizes = [10000, 100000, 1000000]
        bin_counts = [50, 100, 200]

        for size in data_sizes:
            for bins in bin_counts:
                np.random.seed(42)
                data = np.random.normal(0, 1, size)

                start_time = time.time()

                fig, ax = plt.subplots()
                n, bins_out, patches = ax.hist(data, bins=bins, alpha=0.7, density=True)
                ax.set_xlabel("Value")
                ax.set_ylabel("Density")
                ax.set_title(f"Histogram - {size:,} points, {bins} bins")

                end_time = time.time()
                elapsed = end_time - start_time

                plt.close(fig)

                # Histograms should be fast even for large data
                assert (
                    elapsed < 5.0
                ), f"Histogram with {size} points, {bins} bins took {elapsed:.3f}s"

                # Validate histogram output
                assert len(n) == bins
                assert len(patches) == bins
                assert len(bins_out) == bins + 1

    def test_memory_usage_scalability(self):
        """Test memory usage scaling with data size."""
        initial_memory = self.get_memory_usage()

        data_sizes = [10000, 50000, 100000]
        memory_usages = []

        for size in data_sizes:
            # Clear memory before test
            gc.collect()
            mem_before = self.get_memory_usage()

            # Create large dataset
            x = np.linspace(0, 100, size)
            y = np.sin(x) + 0.1 * np.random.randn(size)

            fig, ax = plt.subplots(figsize=(12, 8))
            ax.plot(x, y, linewidth=1)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Memory Test - {size:,} points")
            ax.grid(True)

            mem_after = self.get_memory_usage()
            memory_increase = mem_after - mem_before
            memory_usages.append(memory_increase)

            plt.close(fig)

            # Memory usage should be reasonable
            assert (
                memory_increase < 100
            ), f"Memory usage increased by {memory_increase:.1f}MB for {size} points"

        print(f"Memory usage increases: {list(zip(data_sizes, memory_usages))}")


class TestAdvancedPerformance:
    """Test performance of advanced plotting features."""

    def teardown_method(self):
        """Clean up after performance tests."""
        plt.close("all")
        gc.collect()

    def test_contour_plot_performance(self):
        """Test contour plot performance with 2D data."""
        grid_sizes = [50, 100, 200]
        contour_levels = [10, 20, 50]

        for grid_size in grid_sizes:
            for levels in contour_levels:
                x = np.linspace(0, 10, grid_size)
                y = np.linspace(0, 10, grid_size)
                X, Y = np.meshgrid(x, y)
                Z = np.sin(X) * np.cos(Y) + 0.1 * np.random.randn(grid_size, grid_size)

                start_time = time.time()

                fig, ax = plt.subplots()
                contour = ax.contourf(X, Y, Z, levels=levels, cmap="viridis")
                plt.colorbar(contour, ax=ax)
                ax.set_xlabel("X")
                ax.set_ylabel("Y")
                ax.set_title(f"Contour - {grid_size}x{grid_size} grid, {levels} levels")

                end_time = time.time()
                elapsed = end_time - start_time

                plt.close(fig)

                # Contour plots scale with grid size and levels
                expected_time = (
                    (grid_size / 50) * (levels / 10) * 2.0
                )  # Base expectation
                assert (
                    elapsed < expected_time
                ), f"Contour plot took {elapsed:.3f}s (expected < {expected_time:.3f}s)"

    def test_subplot_performance(self):
        """Test performance of multi-subplot layouts."""
        subplot_counts = [4, 9, 16, 25]  # 2x2, 3x3, 4x4, 5x5

        for n_subplots in subplot_counts:
            grid_size = int(np.sqrt(n_subplots))

            start_time = time.time()

            fig, axes = plt.subplots(grid_size, grid_size, figsize=(12, 12))
            axes_flat = axes.flatten() if hasattr(axes, "flatten") else [axes]

            for i, ax in enumerate(axes_flat):
                x = np.linspace(0, 10, 1000)
                y = np.sin(x + i * np.pi / 4)
                ax.plot(x, y)
                ax.set_title(f"Subplot {i+1}")
                ax.grid(True, alpha=0.3)

            plt.tight_layout()

            end_time = time.time()
            elapsed = end_time - start_time

            plt.close(fig)

            # Subplot creation should scale linearly
            expected_time = n_subplots * 0.1  # 0.1s per subplot
            assert (
                elapsed < expected_time + 2.0
            ), f"{n_subplots} subplots took {elapsed:.3f}s"

    def test_repeated_plot_performance(self):
        """Test performance of repeated plot creation/destruction."""
        n_iterations = 50
        data_size = 10000

        times = []

        for i in range(n_iterations):
            x = np.linspace(0, 10, data_size)
            y = np.sin(x) + 0.1 * np.random.randn(data_size)

            start_time = time.time()

            fig, ax = plt.subplots()
            ax.plot(x, y)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Iteration {i+1}")

            plt.close(fig)

            end_time = time.time()
            elapsed = end_time - start_time
            times.append(elapsed)

        # Check for performance degradation over time
        early_times = np.mean(times[:10])
        late_times = np.mean(times[-10:])

        # Late times shouldn't be significantly slower (indicating memory leaks)
        degradation_ratio = late_times / early_times
        assert (
            degradation_ratio < 2.0
        ), f"Performance degraded by {degradation_ratio:.2f}x over {n_iterations} iterations"

        # Average time per iteration should be reasonable
        avg_time = np.mean(times)
        assert (
            avg_time < 1.0
        ), f"Average time per plot: {avg_time:.3f}s (expected < 1.0s)"


class TestDataTypePerformance:
    """Test performance with different data types and structures."""

    def teardown_method(self):
        """Clean up after performance tests."""
        plt.close("all")
        gc.collect()

    def test_pandas_integration_performance(self):
        """Test performance when plotting with pandas DataFrames."""
        sizes = [1000, 10000, 50000]

        for size in sizes:
            # Create pandas DataFrame
            dates = pd.date_range("2023-01-01", periods=size, freq="1min")
            data = pd.DataFrame(
                {
                    "param1": np.random.randn(size).cumsum(),
                    "param2": np.random.randn(size).cumsum(),
                    "param3": np.random.randn(size).cumsum(),
                },
                index=dates,
            )

            start_time = time.time()

            fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

            for i, column in enumerate(data.columns):
                axes[i].plot(data.index, data[column], label=column)
                axes[i].set_ylabel(column)
                axes[i].legend()
                axes[i].grid(True, alpha=0.3)

            axes[-1].set_xlabel("Time")
            plt.tight_layout()

            end_time = time.time()
            elapsed = end_time - start_time

            plt.close(fig)

            # Pandas plotting should be reasonably fast
            expected_time = size / 10000 * 2.0  # Scale with data size
            assert (
                elapsed < expected_time
            ), f"Pandas plot with {size} points took {elapsed:.3f}s"

    def test_different_data_types_performance(self):
        """Test performance with different numpy data types."""
        size = 50000
        data_types = [np.float32, np.float64, np.int32, np.int64]

        x = np.linspace(0, 10, size)

        for dtype in data_types:
            y = (np.sin(x) * 1000).astype(dtype)

            start_time = time.time()

            fig, ax = plt.subplots()
            ax.plot(x, y)
            ax.set_xlabel("X")
            ax.set_ylabel(f"Y ({dtype.__name__})")
            ax.set_title(f"Performance Test - {dtype.__name__}")

            end_time = time.time()
            elapsed = end_time - start_time

            plt.close(fig)

            # All data types should have similar performance
            assert elapsed < 5.0, f"Plot with {dtype.__name__} took {elapsed:.3f}s"

    def test_sparse_data_performance(self):
        """Test performance with sparse/irregular data."""
        # Test with data that has irregular spacing
        n_points = 10000

        # Regular spacing
        x_regular = np.linspace(0, 100, n_points)
        y_regular = np.sin(x_regular)

        start_time = time.time()
        fig, ax = plt.subplots()
        ax.plot(x_regular, y_regular)
        ax.set_title("Regular Spacing")
        end_time = time.time()
        regular_time = end_time - start_time
        plt.close(fig)

        # Irregular spacing (clustered points)
        x_irregular = np.sort(np.random.exponential(0.1, n_points))
        y_irregular = np.sin(x_irregular)

        start_time = time.time()
        fig, ax = plt.subplots()
        ax.plot(x_irregular, y_irregular)
        ax.set_title("Irregular Spacing")
        end_time = time.time()
        irregular_time = end_time - start_time
        plt.close(fig)

        # Irregular data shouldn't be significantly slower
        time_ratio = irregular_time / regular_time
        assert time_ratio < 2.0, f"Irregular data {time_ratio:.2f}x slower than regular"


class TestMemoryEfficiency:
    """Test memory efficiency of plotting operations."""

    def setup_method(self):
        """Set up memory efficiency tests."""
        gc.collect()
        self.process = psutil.Process(os.getpid())

    def teardown_method(self):
        """Clean up after memory tests."""
        plt.close("all")
        gc.collect()

    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def test_memory_cleanup(self):
        """Test that memory is properly released after plots are closed."""
        initial_memory = self.get_memory_usage()

        # Create and close many plots
        for i in range(20):
            x = np.linspace(0, 10, 10000)
            y = np.sin(x) + 0.1 * np.random.randn(10000)

            fig, ax = plt.subplots(figsize=(12, 8))
            ax.plot(x, y)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Memory Test {i+1}")
            ax.grid(True)

            plt.close(fig)

            # Force garbage collection every few iterations
            if i % 5 == 0:
                gc.collect()

        # Final cleanup
        gc.collect()
        final_memory = self.get_memory_usage()

        # Memory increase should be minimal
        memory_increase = final_memory - initial_memory
        assert (
            memory_increase < 50
        ), f"Memory increased by {memory_increase:.1f}MB after 20 plots"

    def test_large_figure_memory(self):
        """Test memory usage with large figure sizes."""
        sizes = [(8, 6), (16, 12), (24, 18), (32, 24)]
        memory_usages = []

        for width, height in sizes:
            gc.collect()
            mem_before = self.get_memory_usage()

            fig, ax = plt.subplots(figsize=(width, height), dpi=100)
            x = np.linspace(0, 10, 50000)
            y = np.sin(x)
            ax.plot(x, y)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Large Figure {width}x{height}")

            mem_after = self.get_memory_usage()
            memory_increase = mem_after - mem_before
            memory_usages.append(memory_increase)

            plt.close(fig)

            # Memory should scale reasonably with figure size
            area = width * height
            memory_per_area = memory_increase / area
            assert (
                memory_per_area < 2.0
            ), f"Memory per area: {memory_per_area:.3f} MB per unit²"

        print(f"Figure size memory usage: {list(zip(sizes, memory_usages))}")


@pytest.mark.slow
class TestLargeDatasetPerformance:
    """Test performance with datasets typical of space physics applications."""

    def teardown_method(self):
        """Clean up after large dataset tests."""
        plt.close("all")
        gc.collect()

    def test_space_physics_timeseries_performance(self):
        """Test performance with typical space physics time series."""
        # Simulate 1 year of 1-minute cadence data
        n_points = 365 * 24 * 60  # ~525,600 points

        print(f"Testing with {n_points:,} data points (1 year of 1-min data)")

        # Create realistic space physics data
        times = pd.date_range("2023-01-01", periods=n_points, freq="1min")

        # Solar wind parameters with realistic variations
        np.random.seed(42)
        density = 10 * (
            1
            + 0.5 * np.sin(np.arange(n_points) / (24 * 60))  # Daily variation
            + 0.2 * np.sin(np.arange(n_points) / (27 * 24 * 60))  # Solar rotation
            + 0.1 * np.random.randn(n_points)
        )  # Random noise

        velocity = 400 * (
            1
            + 0.3 * np.sin(np.arange(n_points) / (27 * 24 * 60))
            + 0.1 * np.random.randn(n_points)
        )

        temperature = 1e5 * (
            1
            + 0.4 * np.sin(np.arange(n_points) / (24 * 60))
            + 0.2 * np.random.randn(n_points)
        )

        data = pd.DataFrame(
            {"density": density, "velocity": velocity, "temperature": temperature},
            index=times,
        )

        start_time = time.time()

        # Create multi-panel time series plot
        fig, axes = plt.subplots(3, 1, figsize=(15, 12), sharex=True)

        parameters = ["density", "velocity", "temperature"]
        labels = ["Density (cm⁻³)", "Velocity (km/s)", "Temperature (K)"]
        colors = ["blue", "red", "green"]

        for ax, param, label, color in zip(axes, parameters, labels, colors):
            ax.plot(data.index, data[param], color=color, linewidth=0.5, alpha=0.8)
            ax.set_ylabel(label)
            ax.grid(True, alpha=0.3)

            # Add rolling mean for trend
            rolling_mean = data[param].rolling(window=60 * 24).mean()  # Daily average
            ax.plot(data.index, rolling_mean, color="black", linewidth=2, alpha=0.7)

        axes[-1].set_xlabel("Time")
        plt.suptitle("Space Physics Time Series - 1 Year of Data", fontsize=14)
        plt.tight_layout()

        end_time = time.time()
        elapsed = end_time - start_time

        plt.close(fig)

        # Should handle large datasets in reasonable time
        assert (
            elapsed < 30.0
        ), f"Large dataset plot took {elapsed:.3f}s (expected < 30s)"
        print(f"Large dataset plot completed in {elapsed:.3f}s")

    def test_high_resolution_contour_performance(self):
        """Test performance with high-resolution 2D data."""
        # High-resolution grid typical of simulation data
        nx, ny = 500, 500
        print(f"Testing contour plot with {nx}x{ny} = {nx*ny:,} grid points")

        x = np.linspace(0, 10, nx)
        y = np.linspace(0, 10, ny)
        X, Y = np.meshgrid(x, y)

        # Complex 2D function with multiple scales
        Z = (
            np.sin(X) * np.cos(Y)
            + 0.5 * np.sin(5 * X) * np.cos(5 * Y)
            + 0.1 * np.sin(20 * X) * np.cos(20 * Y)
            + 0.05 * np.random.randn(nx, ny)
        )

        start_time = time.time()

        fig, axes = plt.subplots(2, 2, figsize=(12, 12))

        # Filled contour
        contourf = axes[0, 0].contourf(X, Y, Z, levels=50, cmap="viridis")
        axes[0, 0].set_title("Filled Contour")
        plt.colorbar(contourf, ax=axes[0, 0])

        # Line contour
        contour = axes[0, 1].contour(X, Y, Z, levels=20, colors="black")
        axes[0, 1].set_title("Line Contour")
        axes[0, 1].clabel(contour, inline=True, fontsize=8)

        # Image plot
        im = axes[1, 0].imshow(Z, extent=[0, 10, 0, 10], cmap="plasma", aspect="auto")
        axes[1, 0].set_title("Image Plot")
        plt.colorbar(im, ax=axes[1, 0])

        # Pcolormesh
        pcm = axes[1, 1].pcolormesh(X, Y, Z, cmap="coolwarm")
        axes[1, 1].set_title("Pcolormesh")
        plt.colorbar(pcm, ax=axes[1, 1])

        plt.tight_layout()

        end_time = time.time()
        elapsed = end_time - start_time

        plt.close(fig)

        # High-resolution 2D plots are computationally intensive
        assert (
            elapsed < 60.0
        ), f"High-res contour plot took {elapsed:.3f}s (expected < 60s)"
        print(f"High-resolution contour plot completed in {elapsed:.3f}s")


def test_performance_regression():
    """Test for performance regressions in basic operations."""
    # This test establishes baseline performance expectations
    # Values should be updated if significant performance improvements are made

    # Basic line plot performance
    x = np.linspace(0, 10, 100000)
    y = np.sin(x)

    start_time = time.time()
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Performance Regression Test")
    end_time = time.time()

    elapsed = end_time - start_time
    plt.close(fig)

    # Baseline expectation: 100k points should plot in under 2 seconds
    assert elapsed < 2.0, f"Basic plot regression: {elapsed:.3f}s > 2.0s"


def test_memory_leak_detection():
    """Test for memory leaks in plotting operations."""
    gc.collect()
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024

    # Create and destroy many plots
    for i in range(100):
        fig, ax = plt.subplots()
        x = np.random.randn(1000)
        y = np.random.randn(1000)
        ax.scatter(x, y, alpha=0.6)
        plt.close(fig)

        # Periodic cleanup
        if i % 20 == 0:
            gc.collect()

    gc.collect()
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    # Memory increase should be minimal after 100 plot cycles
    assert (
        memory_increase < 20
    ), f"Potential memory leak: {memory_increase:.1f}MB increase"


if __name__ == "__main__":
    # Run basic performance tests when script is executed directly
    print("Running basic performance tests...")

    test = TestBasicPerformance()
    test.setup_method()
    test.test_line_plot_performance()
    test.test_scatter_plot_performance()
    test.teardown_method()

    print("Performance tests completed successfully!")
