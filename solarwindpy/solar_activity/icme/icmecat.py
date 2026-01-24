"""ICMECAT class for accessing the HELIO4CAST ICME catalog."""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


ICMECAT_URL = "https://helioforecast.space/static/sync/icmecat/HELIO4CAST_ICMECAT_v23.csv"

SPACECRAFT_NAMES = frozenset([
    "Ulysses", "Wind", "STEREO-A", "STEREO-B", "ACE",
    "Solar Orbiter", "PSP", "BepiColombo", "Juno", "MESSENGER",
    "VEX", "MAVEN", "Cassini",
])

_DATETIME_COLUMNS = ["icme_start_time", "mo_start_time", "mo_end_time"]


class ICMECAT:
    """Access the HELIO4CAST Interplanetary Coronal Mass Ejection Catalog.

    See https://helioforecast.space/icmecat for the most up-to-date rules of
    the road. As of January 2026, they are:

        If this catalog is used for results that are published in peer-reviewed
        international journals, please contact chris.moestl@outlook.com for
        possible co-authorship.

        Cite the catalog with: Möstl et al. (2020)
        DOI: 10.6084/m9.figshare.6356420

    Parameters
    ----------
    spacecraft : str, optional
        If provided, filter catalog to this spacecraft on load.
        Valid names: Ulysses, Wind, ACE, STEREO-A, STEREO-B, etc.
    cache_dir : Path, optional
        Directory for caching downloaded data. If None, no caching.

    Attributes
    ----------
    data : pd.DataFrame
        Raw catalog data (filtered if spacecraft was specified).
    intervals : pd.DataFrame
        Prepared intervals with computed interval_end column.
    strict_intervals : pd.DataFrame
        Intervals with valid mo_end_time only (no fallbacks used).
    spacecraft : str or None
        Spacecraft filter applied (None if full catalog).

    Example
    -------
    >>> cat = ICMECAT(spacecraft="Ulysses")  # doctest: +SKIP
    >>> print(f"Found {len(cat)} Ulysses ICMEs")  # doctest: +SKIP
    >>> intervals = cat.intervals  # doctest: +SKIP
    >>> print(intervals[["icme_start_time", "mo_end_time", "interval_end"]])  # doctest: +SKIP
    >>>
    >>> # Check which observations fall within ICME intervals
    >>> in_icme = cat.contains(observations.index)  # doctest: +SKIP
    """

    def __init__(
        self,
        spacecraft: Optional[str] = None,
        cache_dir: Optional[Path] = None,
    ):
        self._init_logger()
        self._spacecraft = spacecraft
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._data: Optional[pd.DataFrame] = None
        self._intervals: Optional[pd.DataFrame] = None

        self._load_data()

        if spacecraft is not None:
            self._filter_by_spacecraft(spacecraft)

        self._prepare_intervals()

    def _init_logger(self):
        """Initialize logger for this instance."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def logger(self) -> logging.Logger:
        """Logger instance."""
        return self._logger

    @property
    def spacecraft(self) -> Optional[str]:
        """Spacecraft filter applied, or None if full catalog."""
        return self._spacecraft

    @property
    def data(self) -> pd.DataFrame:
        """Raw ICMECAT data (filtered if spacecraft specified)."""
        return self._data

    @property
    def intervals(self) -> pd.DataFrame:
        """Prepared intervals with computed interval_end.

        The interval_end column uses fallbacks:
        1. mo_end_time if available
        2. mo_start_time + 24h if mo_end_time is NaT
        3. icme_start_time + 24h if both are NaT
        """
        return self._intervals

    @property
    def strict_intervals(self) -> pd.DataFrame:
        """Intervals with valid mo_end_time only (no fallbacks)."""
        return self._intervals[self._intervals["mo_end_time"].notna()].copy()

    def __len__(self) -> int:
        """Number of ICME events."""
        return len(self._data) if self._data is not None else 0

    def __repr__(self) -> str:
        sc_str = f"spacecraft={self._spacecraft!r}" if self._spacecraft else "all spacecraft"
        return f"ICMECAT({sc_str}, n_events={len(self)})"

    # -------------------------------------------------------------------------
    # Data Loading
    # -------------------------------------------------------------------------

    def _load_data(self) -> None:
        """Load ICMECAT data from URL or cache."""
        cached = self._try_load_cache()
        if cached is not None:
            self._data = cached
            self.logger.info("Loaded from cache: %d events", len(self._data))
            return

        self._download()

    def _try_load_cache(self) -> Optional[pd.DataFrame]:
        """Try to load from cache. Returns None if no cache or stale."""
        if self._cache_dir is None:
            return None

        cache_path = self._cache_dir / "icmecat.parquet"
        if not cache_path.exists():
            return None

        # Check age - re-download if > 30 days old
        import time
        age_days = (time.time() - cache_path.stat().st_mtime) / 86400
        if age_days > 30:
            self.logger.info("Cache stale (%.0f days), re-downloading", age_days)
            return None

        return pd.read_parquet(cache_path)

    def _download(self) -> None:
        """Download ICMECAT from helioforecast.space."""
        self.logger.info("Downloading ICMECAT from %s", ICMECAT_URL)

        self._data = pd.read_csv(ICMECAT_URL, parse_dates=_DATETIME_COLUMNS)

        self.logger.info("Downloaded %d ICME events", len(self._data))

        # Save to cache if configured
        if self._cache_dir is not None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = self._cache_dir / "icmecat.parquet"
            self._data.to_parquet(cache_path, index=False)
            self.logger.info("Cached to %s", cache_path)

    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------

    def _filter_by_spacecraft(self, spacecraft: str) -> None:
        """Filter data to specified spacecraft (case-insensitive)."""
        # Build case-insensitive mapping
        available = self._data["sc_insitu"].unique()
        name_map = {name.lower(): name for name in available}

        # Find matching spacecraft name (case-insensitive)
        spacecraft_lower = spacecraft.lower()
        if spacecraft_lower in name_map:
            actual_name = name_map[spacecraft_lower]
        else:
            self.logger.warning(
                "Spacecraft '%s' not found. Available: %s",
                spacecraft, sorted(available)
            )
            actual_name = spacecraft  # Will result in empty filter

        self._data = self._data[self._data["sc_insitu"] == actual_name].copy()
        self._spacecraft = spacecraft  # Keep user's original spelling for display
        self.logger.info("Filtered to %s: %d events", actual_name, len(self._data))

    def filter(self, spacecraft: str) -> "ICMECAT":
        """Return new ICMECAT instance filtered to spacecraft.

        Parameters
        ----------
        spacecraft : str
            Spacecraft name (e.g., "Ulysses", "Wind"). Case-insensitive.

        Returns
        -------
        ICMECAT
            New instance with filtered data (does not re-download).
        """
        # Build case-insensitive mapping
        available = self._data["sc_insitu"].unique()
        name_map = {name.lower(): name for name in available}

        # Find matching spacecraft name (case-insensitive)
        spacecraft_lower = spacecraft.lower()
        actual_name = name_map.get(spacecraft_lower, spacecraft)

        # Create new instance without re-downloading
        new = object.__new__(ICMECAT)
        new._init_logger()
        new._spacecraft = spacecraft  # Keep user's original spelling for display
        new._cache_dir = self._cache_dir
        new._data = self._data[self._data["sc_insitu"] == actual_name].copy()
        new._intervals = None
        new._prepare_intervals()
        return new

    # -------------------------------------------------------------------------
    # Interval Preparation
    # -------------------------------------------------------------------------

    def _prepare_intervals(self) -> None:
        """Prepare interval DataFrame with computed interval_end."""
        columns = [
            "icmecat_id",
            "icme_start_time",
            "mo_start_time",
            "mo_end_time",
            "mo_sc_heliodistance",
            "mo_sc_lat_heeq",
            "mo_sc_long_heeq",
        ]

        # Select available columns
        available = [c for c in columns if c in self._data.columns]
        result = self._data[available].copy()

        if len(result) == 0:
            result["interval_end"] = pd.Series(dtype="datetime64[ns]")
            self._intervals = result
            return

        # Compute interval_end with fallbacks
        interval_end = result["mo_end_time"].copy()

        # Fallback 1: mo_start_time + 24h
        mask_missing = interval_end.isna()
        if "mo_start_time" in result.columns:
            fallback = result.loc[mask_missing, "mo_start_time"] + pd.Timedelta(hours=24)
            interval_end.loc[mask_missing] = fallback

        # Fallback 2: icme_start_time + 24h
        mask_still_missing = interval_end.isna()
        fallback = result.loc[mask_still_missing, "icme_start_time"] + pd.Timedelta(hours=24)
        interval_end.loc[mask_still_missing] = fallback

        result["interval_end"] = interval_end
        self._intervals = result

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_events_in_range(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Get ICME events that overlap with a time range.

        Parameters
        ----------
        start, end : pd.Timestamp
            Time range to query.

        Returns
        -------
        pd.DataFrame
            Events where icme_start_time <= end AND interval_end >= start.
        """
        mask = (
            (self._intervals["icme_start_time"] <= end) &
            (self._intervals["interval_end"] >= start)
        )
        return self._intervals[mask].copy()

    def contains(self, times: pd.DatetimeIndex | pd.Series) -> pd.Series:
        """Check which timestamps fall within any ICME interval.

        Uses only strict intervals (events with valid mo_end_time) to ensure
        accurate containment checking.

        Parameters
        ----------
        times : pd.DatetimeIndex or pd.Series
            Timestamps to check.

        Returns
        -------
        pd.Series
            Boolean mask, True if timestamp is within any ICME interval.
            Index matches input times.
        """
        if isinstance(times, pd.DatetimeIndex):
            times = times.to_series()

        if len(times) == 0:
            return pd.Series([], dtype=bool)

        if len(self._intervals) == 0:
            return pd.Series(False, index=times.index)

        # Use strict intervals (valid mo_end_time only)
        intervals = self.strict_intervals
        if len(intervals) == 0:
            return pd.Series(False, index=times.index)

        starts = intervals["icme_start_time"].values
        ends = intervals["mo_end_time"].values
        obs = times.values

        # Sort intervals by start time for efficient search
        sort_idx = np.argsort(starts)
        sorted_starts = starts[sort_idx]
        sorted_ends = ends[sort_idx]

        # Vectorized containment check
        mask = np.zeros(len(obs), dtype=bool)
        for i, t in enumerate(obs):
            # Find intervals that start before or at this time
            idx = np.searchsorted(sorted_starts, t, side="right")
            # Check if any of those intervals end at or after this time
            if idx > 0 and np.any(sorted_ends[:idx] >= t):
                mask[i] = True

        return pd.Series(mask, index=times.index)

    # -------------------------------------------------------------------------
    # Summary Statistics
    # -------------------------------------------------------------------------

    def summary(self) -> pd.DataFrame:
        """Summary statistics of ICME events.

        Returns
        -------
        pd.DataFrame
            Single-row DataFrame with statistics including:
            - n_events: Total number of events
            - n_strict: Events with valid mo_end_time
            - date_range_start/end: Temporal coverage
            - duration_*: Duration statistics in hours
            - spacecraft: If filtered (optional)
        """
        intervals = self._intervals

        if len(intervals) == 0:
            stats = {
                "n_events": 0,
                "n_strict": 0,
                "date_range_start": pd.NaT,
                "date_range_end": pd.NaT,
                "duration_median_hours": np.nan,
                "duration_mean_hours": np.nan,
                "duration_min_hours": np.nan,
                "duration_max_hours": np.nan,
            }
        else:
            # Duration statistics
            durations = intervals["interval_end"] - intervals["icme_start_time"]
            duration_hours = durations.dt.total_seconds() / 3600

            stats = {
                "n_events": len(intervals),
                "n_strict": len(self.strict_intervals),
                "date_range_start": intervals["icme_start_time"].min(),
                "date_range_end": intervals["interval_end"].max(),
                "duration_median_hours": duration_hours.median(),
                "duration_mean_hours": duration_hours.mean(),
                "duration_min_hours": duration_hours.min(),
                "duration_max_hours": duration_hours.max(),
            }

        if self._spacecraft:
            stats["spacecraft"] = self._spacecraft

        return pd.DataFrame([stats])
