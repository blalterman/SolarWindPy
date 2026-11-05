"""ICMECAT class for accessing the HELIO4CAST ICME catalog."""

__all__ = [
    "ICMECAT_URL",
    "SPACECRAFT_NAMES",
    "ICMECATDownloadError",
    "ICMECATWarning",
    "ICMECATVersionWarning",
    "ICMECATNotHostedWarning",
    "ICMECATSpacecraftWarning",
    "ICMECAT",
]

import logging
import re
import warnings
import pandas as pd
import numpy as np
from typing import Optional

from .. import cache

#: Download URL of the pinned HELIO4CAST ICMECAT release, v23.
ICMECAT_URL = (
    "https://helioforecast.space/static/sync/icmecat/HELIO4CAST_ICMECAT_v23.csv"
)

_PINNED_VERSION = "v23"
# HELIO4CAST hosts one ICMECAT version at a time, so when the pinned one is
# gone (HTTP 404) this many later versions are tried in turn.
_N_PROBED_VERSIONS = 5
_ICMECAT_PAGE = "https://helioforecast.space/icmecat"
_VERSION_IN_URL = re.compile(r"_v(\d+)\.csv$")
# Freshness window: a cached catalog younger than this is used without
# downloading (see solarwindpy.solar_activity.cache).
_MAX_AGE = pd.Timedelta(days=30)
# Warnings name the user's ICMECAT() call. ICMECAT's own warnings are raised in
# methods _load_data calls, and __init__ calls _load_data directly, so they use
# stacklevel=4 (method, _load_data, __init__, user); cache.fall_back sits one
# frame deeper, under _after_failed_download. Moving _load_data changes both.
_FALL_BACK_STACKLEVEL = 5

# The eleven `sc_insitu` values actually present in HELIO4CAST ICMECAT v23.
# ACE and Cassini were previously (and wrongly) included: both have zero
# events in the catalog. "SolarOrbiter" (no space) and "ULYSSES" (all caps)
# are the catalog's actual spellings; the old "Solar Orbiter" spelling broke
# `_filter_by_spacecraft`, which lowercases before comparing.
#: The ``sc_insitu`` spacecraft names present in HELIO4CAST ICMECAT v23.
SPACECRAFT_NAMES = frozenset(
    [
        "BepiColombo",
        "Juno",
        "MAVEN",
        "MESSENGER",
        "PSP",
        "STEREO-A",
        "STEREO-B",
        "SolarOrbiter",
        "ULYSSES",
        "VEX",
        "Wind",
    ]
)

_DATETIME_COLUMNS = ["icme_start_time", "mo_start_time", "mo_end_time"]


RULES_OF_THE_ROAD = """\
See https://helioforecast.space/icmecat for the most up-to-date rules of
the road. As of January 2026, they are:

    If this catalog is used for results that are published in peer-reviewed
    international journals, please contact chris.moestl@outlook.com for
    possible co-authorship.

    Cite the catalog with: Möstl et al. (2020)
    DOI: 10.6084/m9.figshare.6356420
"""


class ICMECATDownloadError(cache.DownloadError):
    """Raised when the ICMECAT catalog cannot be downloaded and none is cached."""


class ICMECATWarning(UserWarning):
    """Base class of the warnings ICMECAT issues about the catalog it loaded."""


class ICMECATVersionWarning(ICMECATWarning):
    """Warns that the pinned ICMECAT version is gone and a later one was loaded."""


class ICMECATNotHostedWarning(ICMECATWarning):
    """Warns that neither the pinned ICMECAT version nor any probed successor is hosted."""


class ICMECATSpacecraftWarning(ICMECATWarning):
    """Warns that the catalog names spacecraft outside ``SPACECRAFT_NAMES``."""


def _version_of(url):
    """The ``vNN`` version token in an ICMECAT URL, or None if it has none."""
    match = _VERSION_IN_URL.search(url)
    return None if match is None else f"v{match.group(1)}"


def _successor_urls(url):
    """The URLs of the ``_N_PROBED_VERSIONS`` versions after the one in ``url``.

    Empty when ``url`` names no version, e.g. a local file.
    """
    match = _VERSION_IN_URL.search(url)
    if match is None:
        return []
    pinned = int(match.group(1))
    head = url[: match.start()]
    return [
        f"{head}_v{version}.csv"
        for version in range(pinned + 1, pinned + 1 + _N_PROBED_VERSIONS)
    ]


class ICMECAT:
    """Access the HELIO4CAST Interplanetary Coronal Mass Ejection Catalog.

    See the module-level ``RULES_OF_THE_ROAD`` constant for the catalog's
    citation and co-authorship terms.

    The downloaded catalog is kept in SolarWindPy's download cache
    (:mod:`solarwindpy.solar_activity.cache`, by default
    ``~/.cache/solarwindpy``) and downloaded again once it is more than 30
    days old. If that download fails, the cached catalog is used with a
    :class:`~solarwindpy.solar_activity.cache.StaleCacheWarning`.

    HELIO4CAST hosts one catalog version at a time. If the pinned version,
    v23, answers HTTP 404, the next five versions (v24 to v28) are tried in
    turn and the first one hosted is loaded with an
    :class:`ICMECATVersionWarning`: its layout may differ from v23's, and
    ``ICMECAT_URL`` should be updated. If none is hosted, an
    :class:`ICMECATNotHostedWarning` is issued and the cached v23 is used, or
    :class:`ICMECATDownloadError` raised when there is none. Any other
    failure (no connection, a timeout, a server error) never starts or
    continues that probe; it falls back to the cache as above.

    Parameters
    ----------
    spacecraft : str, optional
        If provided, filter catalog to this spacecraft on load.
        Valid names are the ``SPACECRAFT_NAMES`` values, matched
        case-insensitively: BepiColombo, Juno, MAVEN, MESSENGER, PSP,
        SolarOrbiter, STEREO-A, STEREO-B, ULYSSES, VEX, Wind.

    Attributes
    ----------
    data : pd.DataFrame
        Raw catalog data (filtered if spacecraft was specified).
    strict_intervals : pd.DataFrame
        Events with a recorded ``mo_end_time``, the intervals that
        :meth:`contains` and :meth:`get_events_in_range` use.
    estimated_intervals : pd.DataFrame
        Every event, with an ``interval_end`` estimated where
        ``mo_end_time`` is missing.
    spacecraft : str or None
        Spacecraft filter applied (None if full catalog).
    version : str or None
        Catalog version loaded, e.g. ``"v23"``; None if the catalog was read
        from a URL or path that names no version.

    Examples
    --------
    In normal use ``ICMECAT(spacecraft="Ulysses")`` downloads the catalog
    from ``ICMECAT_URL``. This example stays offline by pointing
    ``ICMECAT_URL`` at a small local catalog in the same CSV layout.

    >>> import tempfile
    >>> from pathlib import Path
    >>> from solarwindpy.solar_activity.icme import icmecat
    >>> catalog = pd.DataFrame({
    ...     "icmecat_id": ["ICME_ULYSSES_1", "ICME_ULYSSES_2", "ICME_Wind_1"],
    ...     "sc_insitu": ["ULYSSES", "ULYSSES", "Wind"],
    ...     "icme_start_time": ["1998-01-01 00:00", "1998-02-01 00:00",
    ...                         "1998-03-01 00:00"],
    ...     "mo_start_time": ["1998-01-01 06:00", "1998-02-01 06:00",
    ...                       "1998-03-01 06:00"],
    ...     "mo_end_time": ["1998-01-02 00:00", "", "1998-03-02 00:00"],
    ... })
    >>> with tempfile.TemporaryDirectory() as d:
    ...     local = Path(d) / "icmecat.csv"
    ...     catalog.to_csv(local, index=False)
    ...     original_url = icmecat.ICMECAT_URL
    ...     icmecat.ICMECAT_URL = str(local)
    ...     try:
    ...         cat = ICMECAT(spacecraft="Ulysses")
    ...     finally:
    ...         icmecat.ICMECAT_URL = original_url
    >>> cat
    ICMECAT(spacecraft='Ulysses', n_events=2)

    The second event has no ``mo_end_time``, so its estimated
    ``interval_end`` falls back to ``mo_start_time`` + 24 h:

    >>> ends = cat.estimated_intervals["interval_end"]
    >>> ends.dt.strftime("%Y-%m-%d %H:%M").tolist()
    ['1998-01-02 00:00', '1998-02-02 06:00']

    Check which observations fall within ICME intervals. Only events with a
    recorded ``mo_end_time`` count, so the second observation is outside:

    >>> observations = pd.DatetimeIndex(["1998-01-01 12:00", "1998-02-01 12:00"])
    >>> cat.contains(observations).tolist()
    [True, False]
    """

    def __init__(self, spacecraft: Optional[str] = None):
        self._init_logger()
        self._spacecraft = spacecraft
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
    def version(self) -> Optional[str]:
        """Catalog version loaded, e.g. ``"v23"``, or None if its URL names none."""
        return self._version

    @property
    def data(self) -> pd.DataFrame:
        """Raw ICMECAT data (filtered if spacecraft specified)."""
        return self._data

    @property
    def estimated_intervals(self) -> pd.DataFrame:
        """Every event, with an ``interval_end`` estimated where none is recorded.

        The ``interval_end`` column is:

        1. ``mo_end_time`` if recorded,
        2. else ``mo_start_time`` + 24 h,
        3. else ``icme_start_time`` + 24 h.

        The spacecraft's heliocentric distance and HEEQ latitude and
        longitude (``mo_sc_heliodistance``, ``mo_sc_lat_heeq``,
        ``mo_sc_long_heeq``) are carried along where the catalog has them.
        :meth:`contains` and :meth:`get_events_in_range` do not use the
        estimates; they use :attr:`strict_intervals`.
        """
        return self._intervals

    @property
    def strict_intervals(self) -> pd.DataFrame:
        """Events with a recorded ``mo_end_time`` only, no estimated ends."""
        return self._intervals[self._intervals["mo_end_time"].notna()].copy()

    def __len__(self) -> int:
        """Number of ICME events."""
        return len(self._data)

    def __repr__(self) -> str:
        sc_str = (
            f"spacecraft={self._spacecraft!r}" if self._spacecraft else "all spacecraft"
        )
        return f"ICMECAT({sc_str}, n_events={len(self)})"

    # -------------------------------------------------------------------------
    # Data Loading
    # -------------------------------------------------------------------------

    def _load_data(self) -> None:
        """Load ICMECAT through the download cache, probing later versions on a 404.

        A cached catalog younger than ``_MAX_AGE`` is used directly;
        otherwise it is downloaded again. A 404 on ``ICMECAT_URL`` starts the
        probe described in the class docstring. Any other failure uses the
        cached copy with a warning naming its age (see
        :func:`solarwindpy.solar_activity.cache.fall_back`). With nothing
        cached, a failed download raises :class:`ICMECATDownloadError`.
        """
        url = ICMECAT_URL
        try:
            try:
                path = cache.fetch(url, _MAX_AGE, fallback=False)
            except cache.DownloadError as exc:
                path, url = self._after_failed_download(url, exc)
        except cache.DownloadError as exc:
            raise ICMECATDownloadError(
                f"Failed to download ICMECAT {_PINNED_VERSION} from {ICMECAT_URL}. "
                f"Edit solarwindpy.solar_activity.icme.icmecat.ICMECAT_URL "
                f"to point at a working catalog version, see "
                f"{_ICMECAT_PAGE} for the current URL. "
                f"Underlying error: {exc!r}",
                status=exc.status,
            ) from exc

        self._version = _version_of(url)
        self._data = pd.read_csv(path, parse_dates=_DATETIME_COLUMNS)
        self.logger.info("Loaded %d ICME events from %s", len(self._data), path)
        self._warn_unknown_spacecraft()

    def _after_failed_download(self, url, error):
        """Return ``(path, url)`` of the catalog to read after ``url`` failed.

        Probes the successor versions only when ``error`` is an HTTP 404;
        a probe that meets anything but a 404 stops there. Otherwise falls
        back to the cached ``url``.
        """
        if error.status != 404:
            return cache.fall_back(url, error, stacklevel=_FALL_BACK_STACKLEVEL), url

        for successor in _successor_urls(url):
            try:
                path = cache.fetch(successor, _MAX_AGE, fallback=False)
            except cache.DownloadError as exc:
                if exc.status == 404:
                    continue
                return cache.fall_back(url, exc, stacklevel=_FALL_BACK_STACKLEVEL), url
            found = _version_of(successor)
            warnings.warn(
                f"ICMECAT {_version_of(url)} is no longer hosted at {url}; "
                f"loaded {found} from {successor} instead. SolarWindPy expects "
                f"{_PINNED_VERSION}, and the {found} catalog layout may differ: "
                f"update solarwindpy.solar_activity.icme.icmecat.ICMECAT_URL "
                f"and SPACECRAFT_NAMES to {found}.",
                ICMECATVersionWarning,
                stacklevel=4,
            )
            return path, successor

        successors = _successor_urls(url)
        if successors:
            warnings.warn(
                f"No ICMECAT from {_version_of(url)} to "
                f"{_version_of(successors[-1])} is hosted at "
                f"{url.rsplit('/', 1)[0]}/; see {_ICMECAT_PAGE} for the current "
                f"catalog and update "
                f"solarwindpy.solar_activity.icme.icmecat.ICMECAT_URL.",
                ICMECATNotHostedWarning,
                stacklevel=4,
            )
        return cache.fall_back(url, error, stacklevel=_FALL_BACK_STACKLEVEL), url

    def _warn_unknown_spacecraft(self) -> None:
        """Warn if the catalog names spacecraft outside ``SPACECRAFT_NAMES``."""
        unknown = sorted(set(self._data["sc_insitu"].dropna()) - SPACECRAFT_NAMES)
        if unknown:
            warnings.warn(
                f"ICMECAT {self._version or ''} names spacecraft that "
                f"SPACECRAFT_NAMES, written for {_PINNED_VERSION}, does not list: "
                f"{unknown}. They load and filter normally; update "
                f"solarwindpy.solar_activity.icme.icmecat.SPACECRAFT_NAMES.",
                ICMECATSpacecraftWarning,
                stacklevel=4,
            )

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
                spacecraft,
                sorted(available),
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
        new._version = self._version
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
            fallback = result.loc[mask_missing, "mo_start_time"] + pd.Timedelta(
                hours=24
            )
            interval_end.loc[mask_missing] = fallback

        # Fallback 2: icme_start_time + 24h
        mask_still_missing = interval_end.isna()
        fallback = result.loc[mask_still_missing, "icme_start_time"] + pd.Timedelta(
            hours=24
        )
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

        Uses only :attr:`strict_intervals` (events with a recorded
        ``mo_end_time``), as :meth:`contains` does.

        Parameters
        ----------
        start, end : pd.Timestamp
            Time range to query.

        Returns
        -------
        pd.DataFrame
            Events where ``icme_start_time <= end`` and
            ``mo_end_time >= start``.
        """
        intervals = self.strict_intervals
        mask = (intervals["icme_start_time"] <= end) & (
            intervals["mo_end_time"] >= start
        )
        return intervals[mask]

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
