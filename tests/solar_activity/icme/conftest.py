"""Shared fixtures for ICMECAT tests."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def mock_icmecat_csv_data():
    """Create mock ICMECAT CSV data matching real catalog structure.

    Returns DataFrame with realistic column names and data types
    matching HELIO4CAST ICMECAT v2.3 format.
    """
    np.random.seed(42)  # Reproducible
    n_events = 50
    base_date = pd.Timestamp("2000-01-01")

    data = {
        "icmecat_id": [f"ICME_{i:04d}" for i in range(n_events)],
        "sc_insitu": np.random.choice(
            ["Ulysses", "Wind", "STEREO-A", "STEREO-B", "ACE"],
            n_events
        ),
        "icme_start_time": [
            base_date + pd.Timedelta(days=i * 30 + np.random.randint(0, 10))
            for i in range(n_events)
        ],
        "mo_start_time": [
            base_date + pd.Timedelta(days=i * 30 + np.random.randint(10, 15))
            for i in range(n_events)
        ],
        "mo_end_time": [
            base_date + pd.Timedelta(days=i * 30 + np.random.randint(15, 25))
            if np.random.random() > 0.1 else pd.NaT  # 10% missing
            for i in range(n_events)
        ],
        "mo_sc_heliodistance": np.random.uniform(0.7, 5.4, n_events),
        "mo_sc_lat_heeq": np.random.uniform(-80, 80, n_events),
        "mo_sc_long_heeq": np.random.uniform(0, 360, n_events),
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_observation_times():
    """Create sample observation timestamps for containment testing."""
    return pd.Series(
        pd.date_range("2000-01-01", "2005-12-31", freq="4min"),
        name="time"
    )


@pytest.fixture
def simple_icme_intervals():
    """Simple, predictable ICME intervals for testing containment."""
    return pd.DataFrame({
        "icmecat_id": ["TEST_001", "TEST_002", "TEST_003"],
        "sc_insitu": ["Ulysses", "Ulysses", "Ulysses"],
        "icme_start_time": [
            pd.Timestamp("2000-01-10"),
            pd.Timestamp("2000-02-15"),
            pd.Timestamp("2000-03-20"),
        ],
        "mo_start_time": [
            pd.Timestamp("2000-01-11"),
            pd.Timestamp("2000-02-16"),
            pd.Timestamp("2000-03-21"),
        ],
        "mo_end_time": [
            pd.Timestamp("2000-01-15"),
            pd.Timestamp("2000-02-20"),
            pd.NaT,  # Missing - will use fallback
        ],
        "mo_sc_heliodistance": [1.0, 2.0, 3.0],
        "mo_sc_lat_heeq": [10.0, 20.0, 30.0],
        "mo_sc_long_heeq": [100.0, 200.0, 300.0],
    })
