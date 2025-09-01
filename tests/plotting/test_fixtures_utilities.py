"""Test fixtures and utilities for plotting functionality.

Comprehensive test infrastructure, fixtures, and utility functions for the plotting test
suite.
"""

import pytest
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import warnings
from unittest.mock import patch, MagicMock
import pickle

# Configure matplotlib for testing
matplotlib.use("Agg")
plt.ioff()


# ============================================================================
# Core Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def matplotlib_backend():
    """Ensure consistent matplotlib backend for all tests."""
    original_backend = matplotlib.get_backend()
    matplotlib.use("Agg")
    yield "Agg"
    matplotlib.use(original_backend)


@pytest.fixture(scope="function")
def clean_matplotlib():
    """Clean matplotlib state before and after each test."""
    plt.close("all")
    plt.rcdefaults()  # Reset to default rc parameters
    yield
    plt.close("all")


@pytest.fixture(scope="function")
def suppress_warnings():
    """Suppress common matplotlib and numpy warnings during tests."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        warnings.simplefilter("ignore", RuntimeWarning)
        warnings.simplefilter("ignore", FutureWarning)
        yield


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def synthetic_time_series():
    """Generate synthetic time series data for testing."""
    dates = pd.date_range("2023-01-01", periods=1000, freq="1h")
    np.random.seed(42)

    # Solar wind parameters with realistic variations
    n = len(dates)
    time_index = np.arange(n)

    data = {
        "density": 10 + 2 * np.sin(time_index / 100) + np.random.normal(0, 0.5, n),
        "velocity": 400 + 50 * np.sin(time_index / 150) + np.random.normal(0, 10, n),
        "temperature": 1e5
        + 2e4 * np.sin(time_index / 80)
        + np.random.normal(0, 5e3, n),
        "b_field": 5 + np.sin(time_index / 120) + np.random.normal(0, 0.2, n),
        "pressure": 1.5 + 0.3 * np.sin(time_index / 90) + np.random.normal(0, 0.1, n),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture(scope="session")
def synthetic_plasma_data():
    """Generate synthetic plasma data for correlation analysis."""
    np.random.seed(42)
    n_points = 500

    # Correlated plasma parameters
    density = np.random.lognormal(mean=2.3, sigma=0.5, size=n_points)  # ~10 cm^-3
    velocity = (
        400 + 100 * (1 / density) + np.random.normal(0, 20, n_points)
    )  # Anti-corr with density
    temperature = 1e5 * (velocity / 400) ** 1.5 + np.random.normal(
        0, 2e4, n_points
    )  # Corr with velocity
    b_field = 5 * np.sqrt(density) + np.random.normal(
        0, 1, n_points
    )  # Corr with density

    return pd.DataFrame(
        {
            "density": density,
            "velocity": velocity,
            "temperature": temperature,
            "b_field": b_field,
        }
    )


@pytest.fixture(scope="function")
def small_dataset():
    """Small dataset for quick tests."""
    np.random.seed(42)
    x = np.linspace(0, 10, 50)
    y = np.sin(x) + 0.1 * np.random.randn(50)
    return x, y


@pytest.fixture(scope="function")
def medium_dataset():
    """Medium dataset for standard tests."""
    np.random.seed(42)
    x = np.linspace(0, 20, 1000)
    y = np.sin(x) * np.exp(-x / 10) + 0.1 * np.random.randn(1000)
    return x, y


@pytest.fixture(scope="function")
def large_dataset():
    """Large dataset for performance tests."""
    np.random.seed(42)
    x = np.linspace(0, 100, 100000)
    y = np.sin(x / 10) + 0.1 * np.random.randn(100000)
    return x, y


@pytest.fixture(scope="function")
def scatter_data():
    """Scatter plot data with color mapping."""
    np.random.seed(42)
    n = 200
    x = np.random.randn(n)
    y = np.random.randn(n)
    colors = np.random.rand(n)
    sizes = 20 + 50 * np.random.rand(n)
    return x, y, colors, sizes


@pytest.fixture(scope="function")
def histogram_data():
    """Data for histogram testing."""
    np.random.seed(42)
    return {
        "normal": np.random.normal(0, 1, 1000),
        "exponential": np.random.exponential(2, 1000),
        "uniform": np.random.uniform(-3, 3, 1000),
        "mixed": np.concatenate(
            [np.random.normal(-2, 0.5, 300), np.random.normal(2, 0.8, 700)]
        ),
    }


@pytest.fixture(scope="function")
def contour_data():
    """2D data for contour/surface plots."""
    x = np.linspace(-5, 5, 50)
    y = np.linspace(-5, 5, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2)) * np.exp(-0.1 * (X**2 + Y**2))
    return X, Y, Z


# ============================================================================
# Figure and Axes Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def single_axis(clean_matplotlib):
    """Single axis figure for basic plots."""
    fig, ax = plt.subplots(figsize=(8, 6))
    yield fig, ax
    plt.close(fig)


@pytest.fixture(scope="function")
def multi_axis(clean_matplotlib):
    """Multi-axis figure for subplot tests."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    yield fig, axes
    plt.close(fig)


@pytest.fixture(scope="function")
def time_series_axes(clean_matplotlib):
    """Specialized axes for time series plots."""
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    yield fig, axes
    plt.close(fig)


@pytest.fixture(scope="function")
def correlation_axes(clean_matplotlib):
    """Correlation plot axes configuration."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    yield fig, axes
    plt.close(fig)


# ============================================================================
# Temporary File Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def temp_dir():
    """Temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def temp_plot_file(temp_dir):
    """Temporary file for plot saving."""
    return temp_dir / "test_plot.png"


@pytest.fixture(scope="function")
def temp_data_file(temp_dir):
    """Temporary file for data saving."""
    return temp_dir / "test_data.csv"


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture(scope="function")
def mock_figure():
    """Mock matplotlib figure for unit testing."""
    with patch("matplotlib.pyplot.figure") as mock_fig:
        mock_instance = MagicMock()
        mock_fig.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_axes():
    """Mock matplotlib axes for unit testing."""
    mock_ax = MagicMock()
    mock_ax.plot.return_value = [MagicMock()]  # Line2D objects
    mock_ax.scatter.return_value = MagicMock()  # PathCollection
    mock_ax.hist.return_value = (
        np.array([1, 2, 3]),
        np.array([0, 1, 2, 3]),
        [MagicMock()],
    )
    return mock_ax


# ============================================================================
# Utility Classes and Functions
# ============================================================================


class PlotTestHelper:
    """Helper class for common plotting test operations."""

    @staticmethod
    def assert_plot_elements(
        ax,
        expected_lines=None,
        expected_collections=None,
        expected_patches=None,
        has_legend=None,
        has_grid=None,
    ):
        """Assert expected plot elements are present."""
        if expected_lines is not None:
            assert (
                len(ax.lines) == expected_lines
            ), f"Expected {expected_lines} lines, got {len(ax.lines)}"

        if expected_collections is not None:
            assert (
                len(ax.collections) == expected_collections
            ), f"Expected {expected_collections} collections, got {len(ax.collections)}"

        if expected_patches is not None:
            assert (
                len(ax.patches) == expected_patches
            ), f"Expected {expected_patches} patches, got {len(ax.patches)}"

        if has_legend is not None:
            legend_exists = ax.legend_ is not None
            assert (
                legend_exists == has_legend
            ), f"Legend existence mismatch: expected {has_legend}, got {legend_exists}"

        if has_grid is not None:
            # Check if grid is visible
            grid_on = (
                ax.xaxis.get_gridlines()[0].get_visible()
                if ax.xaxis.get_gridlines()
                else False
            )
            assert (
                grid_on == has_grid
            ), f"Grid visibility mismatch: expected {has_grid}, got {grid_on}"

    @staticmethod
    def assert_axes_labels(ax, xlabel=None, ylabel=None, title=None):
        """Assert axes labels are set correctly."""
        if xlabel is not None:
            assert (
                ax.get_xlabel() == xlabel
            ), f"X-label mismatch: expected '{xlabel}', got '{ax.get_xlabel()}'"

        if ylabel is not None:
            assert (
                ax.get_ylabel() == ylabel
            ), f"Y-label mismatch: expected '{ylabel}', got '{ax.get_ylabel()}'"

        if title is not None:
            assert (
                ax.get_title() == title
            ), f"Title mismatch: expected '{title}', got '{ax.get_title()}'"

    @staticmethod
    def assert_data_ranges(ax, xlim=None, ylim=None, tolerance=1e-10):
        """Assert data ranges are within expected limits."""
        if xlim is not None:
            actual_xlim = ax.get_xlim()
            assert (
                abs(actual_xlim[0] - xlim[0]) < tolerance
                and abs(actual_xlim[1] - xlim[1]) < tolerance
            ), f"X-limits mismatch: expected {xlim}, got {actual_xlim}"

        if ylim is not None:
            actual_ylim = ax.get_ylim()
            assert (
                abs(actual_ylim[0] - ylim[0]) < tolerance
                and abs(actual_ylim[1] - ylim[1]) < tolerance
            ), f"Y-limits mismatch: expected {ylim}, got {actual_ylim}"

    @staticmethod
    def save_and_verify_plot(fig, filepath, formats=["png"], dpi=100):
        """Save plot in multiple formats and verify files."""
        saved_files = []

        for fmt in formats:
            if isinstance(filepath, Path):
                file_path = filepath.with_suffix(f".{fmt}")
            else:
                file_path = Path(str(filepath)).with_suffix(f".{fmt}")

            fig.savefig(file_path, format=fmt, dpi=dpi, bbox_inches="tight")

            # Verify file was created and has content
            assert file_path.exists(), f"File {file_path} was not created"
            assert file_path.stat().st_size > 0, f"File {file_path} is empty"

            saved_files.append(file_path)

        return saved_files


@pytest.fixture(scope="function")
def plot_helper():
    """Provide PlotTestHelper instance."""
    return PlotTestHelper()


# ============================================================================
# Test Data Generators
# ============================================================================


def generate_solar_wind_event(duration_hours=24, cadence_minutes=1, event_type="shock"):
    """Generate synthetic solar wind event data."""
    n_points = int(duration_hours * 60 / cadence_minutes)
    times = pd.date_range("2023-01-01", periods=n_points, freq=f"{cadence_minutes}min")

    if event_type == "shock":
        # Sudden jump in parameters
        shock_time = n_points // 2

        density = np.ones(n_points) * 5
        density[shock_time:] = 20  # Density jump
        density += np.random.normal(0, 1, n_points)

        velocity = np.ones(n_points) * 350
        velocity[shock_time:] = 600  # Velocity jump
        velocity += np.random.normal(0, 15, n_points)

        temperature = np.ones(n_points) * 5e4
        temperature[shock_time:] = 2e5  # Temperature jump
        temperature += np.random.normal(0, 1e4, n_points)

    elif event_type == "cme":
        # Gradual rotation in magnetic field
        b_x = 5 * np.sin(np.linspace(0, 4 * np.pi, n_points))
        b_y = 5 * np.cos(np.linspace(0, 4 * np.pi, n_points))
        b_z = 2 * np.sin(np.linspace(0, 2 * np.pi, n_points))

        density = 15 + 5 * np.sin(np.linspace(0, 2 * np.pi, n_points))
        velocity = 450 + 100 * np.sin(np.linspace(0, np.pi, n_points))
        temperature = 1e5 + 5e4 * np.sin(np.linspace(0, np.pi, n_points))

        return pd.DataFrame(
            {
                "density": density + np.random.normal(0, 1, n_points),
                "velocity": velocity + np.random.normal(0, 20, n_points),
                "temperature": temperature + np.random.normal(0, 1e4, n_points),
                "b_x": b_x + np.random.normal(0, 0.5, n_points),
                "b_y": b_y + np.random.normal(0, 0.5, n_points),
                "b_z": b_z + np.random.normal(0, 0.5, n_points),
            },
            index=times,
        )

    return pd.DataFrame(
        {"density": density, "velocity": velocity, "temperature": temperature},
        index=times,
    )


@pytest.fixture(scope="function", params=["shock", "cme"])
def solar_wind_event(request):
    """Generate solar wind event data."""
    return generate_solar_wind_event(event_type=request.param)


# ============================================================================
# Performance Testing Utilities
# ============================================================================


class PerformanceTracker:
    """Track performance metrics for plotting operations."""

    def __init__(self):
        self.metrics = {}

    def time_operation(self, operation_name, func, *args, **kwargs):
        """Time a plotting operation and store metrics."""
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        elapsed = end_time - start_time

        if operation_name not in self.metrics:
            self.metrics[operation_name] = []
        self.metrics[operation_name].append(elapsed)

        return result, elapsed

    def get_average_time(self, operation_name):
        """Get average time for an operation."""
        if operation_name in self.metrics:
            return np.mean(self.metrics[operation_name])
        return None

    def assert_performance(self, operation_name, max_time):
        """Assert operation performance meets expectations."""
        avg_time = self.get_average_time(operation_name)
        if avg_time is not None:
            assert (
                avg_time < max_time
            ), f"{operation_name} took {avg_time:.3f}s (expected < {max_time}s)"


@pytest.fixture(scope="function")
def performance_tracker():
    """Provide PerformanceTracker instance."""
    return PerformanceTracker()


# ============================================================================
# Test Infrastructure Classes
# ============================================================================


class TestFixturesAndUtilities:
    """Test the test infrastructure itself."""

    def test_synthetic_time_series_fixture(self, synthetic_time_series):
        """Test synthetic time series data fixture."""
        assert isinstance(synthetic_time_series, pd.DataFrame)
        assert len(synthetic_time_series) == 1000
        assert synthetic_time_series.index.freq is not None

        expected_columns = ["density", "velocity", "temperature", "b_field", "pressure"]
        for col in expected_columns:
            assert col in synthetic_time_series.columns
            assert not synthetic_time_series[col].isna().any()

    def test_synthetic_plasma_data_fixture(self, synthetic_plasma_data):
        """Test synthetic plasma data fixture."""
        assert isinstance(synthetic_plasma_data, pd.DataFrame)
        assert len(synthetic_plasma_data) == 500

        # Check that correlations exist (anti-correlation between density and velocity)
        density_velocity_corr = synthetic_plasma_data["density"].corr(
            synthetic_plasma_data["velocity"]
        )
        assert (
            density_velocity_corr < 0
        ), "Expected anti-correlation between density and velocity"

    def test_plot_helper_functionality(self, plot_helper, single_axis):
        """Test PlotTestHelper functionality."""
        fig, ax = single_axis

        # Create a simple plot
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y, label="sin(x)")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Test Plot")
        ax.legend()
        ax.grid(True)

        # Test assertions
        plot_helper.assert_plot_elements(
            ax, expected_lines=1, has_legend=True, has_grid=True
        )
        plot_helper.assert_axes_labels(ax, xlabel="X", ylabel="Y", title="Test Plot")

    def test_temporary_file_fixtures(self, temp_dir, temp_plot_file, temp_data_file):
        """Test temporary file fixtures."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Test that parent directory of temp files exists
        assert temp_plot_file.parent.exists()
        assert temp_data_file.parent.exists()

        # Test file creation
        temp_plot_file.write_text("test plot data")
        temp_data_file.write_text("test,data\n1,2\n")

        assert temp_plot_file.exists()
        assert temp_data_file.exists()

    def test_dataset_fixtures(self, small_dataset, medium_dataset, large_dataset):
        """Test dataset fixtures have expected properties."""
        x_small, y_small = small_dataset
        x_medium, y_medium = medium_dataset
        x_large, y_large = large_dataset

        # Check sizes
        assert len(x_small) == 50
        assert len(x_medium) == 1000
        assert len(x_large) == 100000

        # Check data types
        for x, y in [(x_small, y_small), (x_medium, y_medium), (x_large, y_large)]:
            assert isinstance(x, np.ndarray)
            assert isinstance(y, np.ndarray)
            assert len(x) == len(y)

    def test_scatter_data_fixture(self, scatter_data):
        """Test scatter data fixture."""
        x, y, colors, sizes = scatter_data

        assert len(x) == len(y) == len(colors) == len(sizes) == 200
        assert 0 <= colors.min() and colors.max() <= 1  # Color values in [0,1]
        assert sizes.min() >= 20 and sizes.max() <= 70  # Size range

    def test_histogram_data_fixture(self, histogram_data):
        """Test histogram data fixture."""
        expected_types = ["normal", "exponential", "uniform", "mixed"]

        for data_type in expected_types:
            assert data_type in histogram_data
            data = histogram_data[data_type]
            assert len(data) == 1000 or (data_type == "mixed" and len(data) == 1000)

    def test_contour_data_fixture(self, contour_data):
        """Test contour data fixture."""
        X, Y, Z = contour_data

        assert X.shape == Y.shape == Z.shape == (50, 50)
        assert not np.isnan(Z).any()
        assert not np.isinf(Z).any()

    def test_performance_tracker(self, performance_tracker):
        """Test performance tracking functionality."""
        import time

        def slow_operation():
            time.sleep(0.1)
            return "result"

        def fast_operation():
            return "result"

        # Time operations
        result1, time1 = performance_tracker.time_operation("slow", slow_operation)
        result2, time2 = performance_tracker.time_operation("fast", fast_operation)

        assert result1 == "result"
        assert result2 == "result"
        assert time1 > time2
        assert time1 >= 0.1

        # Test performance assertions
        performance_tracker.assert_performance("fast", 0.1)

        with pytest.raises(AssertionError):
            performance_tracker.assert_performance("slow", 0.05)

    def test_solar_wind_event_generator(self, solar_wind_event):
        """Test solar wind event data generator."""
        assert isinstance(solar_wind_event, pd.DataFrame)
        assert "density" in solar_wind_event.columns
        assert "velocity" in solar_wind_event.columns
        assert "temperature" in solar_wind_event.columns

        # Check that data shows event characteristics
        density_std = solar_wind_event["density"].std()
        velocity_std = solar_wind_event["velocity"].std()

        # Events should show significant variation
        assert density_std > 1.0
        assert velocity_std > 10.0


class TestMockingUtilities:
    """Test mocking utilities for unit testing."""

    def test_mock_figure_fixture(self, mock_figure):
        """Test mock figure fixture."""
        assert mock_figure is not None

        # Test that mock can be called
        mock_figure.savefig("test.png")
        mock_figure.savefig.assert_called_with("test.png")

    def test_mock_axes_fixture(self, mock_axes):
        """Test mock axes fixture."""
        assert mock_axes is not None

        # Test plotting methods return expected types
        line = mock_axes.plot([1, 2, 3], [1, 2, 3])
        assert line is not None

        scatter = mock_axes.scatter([1, 2, 3], [1, 2, 3])
        assert scatter is not None

        hist_result = mock_axes.hist([1, 2, 3])
        assert len(hist_result) == 3  # n, bins, patches


class TestFixtureIntegration:
    """Test integration between different fixtures."""

    def test_plot_with_synthetic_data(
        self, single_axis, synthetic_time_series, plot_helper
    ):
        """Test plotting with synthetic data using fixtures."""
        fig, ax = single_axis

        # Plot first parameter
        param = "density"
        ax.plot(
            synthetic_time_series.index,
            synthetic_time_series[param],
            label=param,
            linewidth=1.5,
        )
        ax.set_xlabel("Time")
        ax.set_ylabel("Density (cm⁻³)")
        ax.set_title("Synthetic Time Series Test")
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Use helper to validate
        plot_helper.assert_plot_elements(
            ax, expected_lines=1, has_legend=True, has_grid=True
        )
        plot_helper.assert_axes_labels(
            ax,
            xlabel="Time",
            ylabel="Density (cm⁻³)",
            title="Synthetic Time Series Test",
        )

    def test_save_plot_with_temp_files(
        self, single_axis, small_dataset, temp_dir, plot_helper
    ):
        """Test saving plots using temporary file fixtures."""
        fig, ax = single_axis
        x, y = small_dataset

        ax.plot(x, y, "b-", linewidth=2)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Save Test Plot")

        # Save using helper
        plot_file = temp_dir / "integration_test"
        saved_files = plot_helper.save_and_verify_plot(
            fig, plot_file, formats=["png", "pdf"]
        )

        assert len(saved_files) == 2
        for file_path in saved_files:
            assert file_path.exists()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


# ============================================================================
# Utility Functions for External Use
# ============================================================================


def create_test_plot(plot_type="line", data_size="medium", **kwargs):
    """Create a test plot for external testing use."""
    if data_size == "small":
        n = 50
    elif data_size == "medium":
        n = 1000
    elif data_size == "large":
        n = 10000
    else:
        n = int(data_size)

    fig, ax = plt.subplots(figsize=kwargs.get("figsize", (8, 6)))

    if plot_type == "line":
        x = np.linspace(0, 10, n)
        y = np.sin(x) + 0.1 * np.random.randn(n)
        ax.plot(x, y, **kwargs)

    elif plot_type == "scatter":
        x = np.random.randn(n)
        y = np.random.randn(n)
        ax.scatter(x, y, **kwargs)

    elif plot_type == "histogram":
        data = np.random.normal(0, 1, n)
        ax.hist(data, bins=kwargs.get("bins", 30), **kwargs)

    return fig, ax


def validate_plot_output(ax, plot_type="line"):
    """Validate that plot output meets basic requirements."""
    if plot_type == "line":
        assert len(ax.lines) > 0, "No lines found in line plot"
    elif plot_type == "scatter":
        assert len(ax.collections) > 0, "No scatter collections found"
    elif plot_type == "histogram":
        assert len(ax.patches) > 0, "No histogram patches found"

    # General validations
    assert ax.get_xlabel() != "" or ax.get_ylabel() != "", "No axis labels set"
    return True
