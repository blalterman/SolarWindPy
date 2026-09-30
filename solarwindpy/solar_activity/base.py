"""Base classes for solar activity indicators."""

import logging
import re
import urllib

import numpy as np
import pandas as pd

from pathlib import Path
from abc import ABC, abstractmethod, abstractproperty, abstractstaticmethod
from collections import namedtuple

from scipy.interpolate import InterpolatedUnivariateSpline

_Loader_Dtypes_Columns = namedtuple("LoaderNamedTuple", ["dtypes", "columns"])
_data_date_pattern = re.compile(r"\d{4}\d{2}\d{2}")

pd.set_option("mode.chained_assignment", "raise")


class Base(ABC):
    """Abstract base class providing a logger interface."""

    @property
    def logger(self):
        """``logging.Logger`` attached to the instance."""
        return self._logger

    def _init_logger(self):
        r"""Attach a logger named after the module and class."""
        logger = logging.getLogger(
            name="{}.{}".format(__name__, self.__class__.__name__)
        )
        self._logger = logger

    def __str__(self):
        r"""Return the class name."""
        return self.__class__.__name__


class ID(Base):
    """Container for identifying a particular data product."""

    def __init__(self, key: str) -> None:
        """Instantiate the identifier and set the corresponding URL.

        Parameters
        ----------
        key : str
            Key that maps to a URL fragment in the subclass's ``_trans_url``.
        """
        self._init_logger()
        self.set_key(key)

    @abstractproperty
    def _url_base(self):
        r"""Base URL that each key's URL fragment is joined to."""
        pass

    @abstractproperty
    def _trans_url(self):
        r"""Map from key to URL fragment."""
        pass

    @property
    def key(self):
        r"""Key identifying the data product."""
        return self._key

    @property
    def url(self):
        r"""URL specifying location from which data was downloaded."""
        return self._url

    def set_key(self, key):
        """Set the identifier key and construct the download URL.

        Raises
        ------
        NotImplementedError
            If ``key`` is not in ``_trans_url``.
        """

        try:
            url_end = self._trans_url[key]
        except KeyError:
            msg = "{} key unavailable".format(key)
            self.logger.exception(msg)
            raise NotImplementedError(msg)

        url = urllib.parse.urljoin(self._url_base, url_end)

        self.logger.info("Setting key\nkey : %s\nurl : %s", key, url)

        self._key = key
        self._url = url


class DataLoader(Base):
    r"""Download, cache, and load a solar activity data set.

    Data are cached under :attr:`data_path` in a file named for the date of
    download, and downloaded again when that date is before today.
    """

    def __init__(self, key, url):
        r"""Initialize a data loader.

        Parameters
        ----------
        key : str
            Unique data identifier, typically from something like
            :class:`~solarwindpy.solar_activity.sunspot_number.sidc.SIDC_ID`.
        url : str
            Full download URL for the data source.
        """
        self._init_logger()
        self.set_key(key)
        self.set_url(url)
        self.get_data_ctime()
        self.get_data_age()

    @abstractproperty
    def data_path(self):
        r"""Root of the local data cache, ``~/solarwindpy/data``.

        Subclasses extend this path with their source and key.
        """
        return Path.home() / "solarwindpy" / "data"

    @abstractstaticmethod
    def convert_nans(data):
        r"""Replace the source's missing-value sentinel with NaN."""
        pass

    @abstractmethod
    def download_data(self):
        r"""Download the data and write them to the cache."""
        pass

    @abstractmethod
    def load_data(self):
        r"""Load today's cached data into :attr:`data`, downloading if stale.

        Subclasses call this and may add to the loaded data.
        """
        self.logger.info(f"""Loading {self.key!s} data""")

        self.maybe_update_stale_data()

        today = pd.to_datetime("today").strftime("%Y%m%d")
        fpath = (self.data_path / today).with_suffix(".csv")
        data = pd.read_csv(fpath, index_col=0, header=0)

        data.set_index(pd.DatetimeIndex(data.index), inplace=True)
        self._data = data

    @property
    def logger(self):
        r"""``logging.Logger`` attached to the instance."""
        return self._logger

    @property
    def data(self):
        r"""Loaded data, :class:`pandas.DataFrame` indexed by time."""
        return self._data

    @property
    def key(self):
        r"""Data identifier."""
        return self._key

    @property
    def url(self):
        r"""Download URL."""
        return self._url

    @property
    def ctime(self):
        r"""Date of the cached data, from its file name."""
        return self._ctime

    @property
    def age(self):
        r"""Time since :attr:`ctime`."""
        return self._age

    def _init_logger(self):
        r"""Attach a logger named after the module and class."""
        logger = logging.getLogger(
            name="{}.{}".format(__name__, self.__class__.__name__)
        )
        self._logger = logger

    def set_key(self, key):
        r"""Set :attr:`key`."""
        self._key = key

    def set_url(self, new):
        r"""Set :attr:`url`."""
        self._url = new

    def get_data_ctime(self):
        r"""Determine when the current data set was created.

        Returns
        -------
        pandas.Timestamp
            Creation time inferred from the file name, or ``1970-01-01`` if no
            prior data are found.
        """
        path = self.data_path
        files = [str(x) for x in path.rglob("*.csv")]
        dates = [re.findall(_data_date_pattern, f) for f in files]

        if not len(dates):
            # This will automatically return a date in 1970, so we
            # will clear and download new data.
            self._ctime = pd.to_datetime(0)
            return

        dates = np.concatenate(dates)
        dates = [x.strip("/") for x in dates]
        dates = np.unique(dates)

        # BUG: This fails if there are more than two dated data directories.
        assert dates.size == 1
        ctime = pd.to_datetime(dates[0])

        self.logger.info("Local data ctime %s", ctime)
        self._ctime = ctime

    def get_data_age(self):
        r"""Compute the time elapsed since :attr:`ctime`."""
        ctime = self.ctime
        today = pd.to_datetime("today")
        dt = today - ctime
        self._data_age = dt

    def maybe_update_stale_data(self):
        r"""Download new data if the existing cache is stale."""
        self.logger.info("Updating stale data")

        old_ctime = self.ctime
        new_ctime = pd.to_datetime("today")

        if new_ctime.date() > old_ctime.date():
            old_data_path = self.data_path / old_ctime.strftime("%Y%m%d")
            new_data_path = self.data_path / new_ctime.strftime("%Y%m%d")
            new_data_path.parent.mkdir(parents=True, exist_ok=True)

            self.download_data(new_data_path, old_data_path)


class ActivityIndicator(Base):
    r"""Abstract solar activity indicator: data, their extrema, and normalization."""

    @property
    def id(self):
        r"""The :class:`~solarwindpy.solar_activity.base.ID` identifying the data product."""
        return self._id

    @property
    def loader(self):
        r"""The :class:`~solarwindpy.solar_activity.base.DataLoader` holding the data."""
        return self._loader

    @property
    def data(self):
        r"""Shortcut to `self.loader.data`."""
        return self.loader.data

    @property
    def extrema(self):
        r"""The :class:`~solarwindpy.solar_activity.base.IndicatorExtrema` of the indicator."""
        return self._extrema

    @property
    def norm_by(self):
        r"""Normalization last applied by :meth:`run_normalization`.

        Raises
        ------
        AttributeError
            If no normalization has been run.
        """
        try:
            return self._norm_by
        except AttributeError:
            raise AttributeError("Please calculate normalized quantity")

    @property
    def interpolated(self):
        r"""Result of the last :meth:`interpolate_data` call."""
        return self._interpolated

    def set_id(self, new):
        r"""Set :attr:`id`, which must be an :class:`~solarwindpy.solar_activity.base.ID`."""
        assert isinstance(new, ID)
        self._id = new

    # Need to store `interpolated` in subclass. Allows normalized ssn to be interpolated.
    @abstractmethod
    def interpolate_data(self, source_data, target_index):
        """Interpolate ``source_data`` onto ``target_index``.

        Parameters
        ----------
        source_data : pandas.Series or pandas.DataFrame
            Data with a :class:`~pandas.DatetimeIndex` to interpolate.
        target_index : pandas.DatetimeIndex
            Target time axis for the interpolation.

        Returns
        -------
        pandas.DataFrame
            Data interpolated onto ``target_index``.
        """
        assert isinstance(target_index, pd.DatetimeIndex)
        assert isinstance(source_data.index, pd.DatetimeIndex)

        if isinstance(source_data, pd.Series):
            source_data = source_data.to_frame()

        nans = source_data.isna().any().any()
        if nans:
            raise NotImplementedError(
                "You must drop NaNs in the subclass's caller before "
                "calling parent method."
            )

        x_target = target_index.asi8
        x_source = source_data.index.asi8

        interpolated = {}
        for k, y_source in source_data.items():
            interpolator = InterpolatedUnivariateSpline(
                x_source, y_source, check_finite=True
            )
            interped = interpolator(x_target)
            interpolated[k] = interped

        interpolated = pd.DataFrame(interpolated, index=target_index)

        # Remove extrapolated data
        tk = pd.Series(True, target_index)

        t1 = target_index[-1]
        s1 = source_data.index[-1]
        if s1 < t1:
            tk = tk & (target_index <= s1)

        t0 = target_index[0]
        s0 = source_data.index[0]
        if t0 < s0:
            tk = tk & (s0 <= target_index)

        if not tk.all():
            interpolated.where(tk, inplace=True, axis=0)

        self._interpolated = interpolated
        return interpolated

    @abstractproperty
    def normalized(self):
        r"""The indicator normalized within each solar cycle."""
        pass

    @abstractmethod
    def set_extrema(self):
        r"""Set :attr:`extrema`."""
        pass

    @abstractmethod
    def run_normalization(self):
        r"""Normalize the indicator within each solar cycle.

        Parameters
        ----------
        norm_by : {"max", "zscore", "feature-scale"}
            Normalization algorithm to apply.

        Returns
        -------
        pandas.Series
            Normalized values indexed by time.
        """
        pass

    def _run_normalization(self, indicator, norm_fcn):
        r"""Apply ``norm_fcn`` to ``indicator`` separately within each cycle."""
        cut = self.extrema.cut_spec_by_interval(indicator.index, kind="Cycle")
        joint = pd.concat(
            [indicator, cut], axis=1, keys=["indicator", "cycle"]
        ).sort_index(axis=1)
        grouped = joint.groupby("cycle")

        normed = {}
        for k, g in grouped:
            g = g.loc[:, "indicator"]
            normed[k] = norm_fcn(g)
        normed = pd.concat(normed.values(), axis=0).sort_index()
        return normed


class IndicatorExtrema(Base):
    """Base class for objects describing indicator extrema."""

    def __init__(self, *args, **kwargs):
        r"""Load the extrema and compute the cycle intervals.

        Arguments are passed to :meth:`load_or_set_data`.
        """
        self._init_logger()
        self.load_or_set_data(*args, **kwargs)
        self.calculate_intervals()

    @property
    def data(self):
        r"""``Min`` and ``Max`` dates of each cycle, :class:`pandas.DataFrame`."""
        return self._data

    @property
    def cycle_intervals(self):
        r""":class:`pandas.Interval` for rising and falling edges and full cycle."""
        return self._cycle_intervals

    @property
    def extrema_bands(self):
        r"""Bands of time (:math:`\Delta t`) about indicator extrema.

        Set by :meth:`calculate_extrema_bands`.

        Raises
        ------
        AttributeError
            If :meth:`calculate_extrema_bands` has not been called.
        """
        try:
            return self._extrema_bands
        except AttributeError:
            raise AttributeError("Have you called `extrema.calculate_extrema_bands`?")

    @abstractmethod
    def load_or_set_data(self):
        r"""Set :attr:`data`, the ``Min`` and ``Max`` dates of each cycle."""
        pass

    #######################################################################
    # Tools for grouping data by Cycle and Cycle Edge (Rising or Falling) #
    #######################################################################
    def calculate_intervals(self):
        r"""Compute rising, falling, and full-cycle time intervals.

        Notes
        -----
        The rising edge comes before the falling edge in time, i.e. it's
        Min ``N`` followed by Max ``N``. Also calculate intervals for a full
        SSN cycle.
        """
        extrema = self.data
        intervals = pd.DataFrame(
            index=extrema.index,
            columns=pd.Index(["Rise", "Fall", "Cycle"], name="kind"),
        )

        # Make `today` only keep the date.
        today = pd.to_datetime(pd.to_datetime("today").date())
        for c, r in extrema.iterrows():
            t0 = r.loc["Min"]
            t1 = r.loc["Max"]

            if pd.isna(t1):
                # No maximum yet, then use Today for maximum
                t1 = today

            try:
                # Get next cycle's Minimum to calculate Falling edge
                t2 = extrema.loc[c + 1, "Min"]
            except KeyError:
                if t1 < today:
                    # We haven't reached next Min yet, but have current cycle Max
                    # so use today.
                    t2 = today
                else:
                    # This cycle does not have a falling edge.
                    t2 = t1 + pd.to_timedelta(6 * 365, unit="D")

            rise_ = pd.Interval(t0, t1)
            fall_ = pd.Interval(t1, t2)
            all_ = pd.Interval(t0, t2)

            if t1 == t2:
                # Then no falling edge
                fall_ = pd.NaT

            intervals.loc[c] = pd.Series({"Rise": rise_, "Fall": fall_, "Cycle": all_})

        intervals = intervals.sort_index(axis=1)
        self._cycle_intervals = intervals
        return intervals

    def cut_spec_by_interval(self, epoch, kind=None, tk_cycles=None):
        r"""Assign epochs to solar-cycle intervals.

        Parameters
        ----------
        epoch : pandas.Series or pandas.DatetimeIndex
            Data to cut.
        kind : str, optional
            If provided, restricts the cut to a subset of interval types.

            ========= ===============================
               Key              Description
            ========= ===============================
             None      Cut by all available options.
             "Cycle"   Cut by solar cycle
             "Rise"    Cut by rising edge
             "Fall"    Cut by falling edge
             "Edges"   Cut by `["Fall", "Rise"]`.
                       Exclusive option.
            ========= ===============================

            Note that ``"Edges"`` is exclusive and will specify
            ``["Fall", "Rise"]`` alone.
        tk_cycles : list or slice, optional
            If not ``None``, a selector used to choose target solar cycles.

        Returns
        -------
        pandas.Series
            Series of :class:`pandas.Interval` objects labeling each epoch.
        """
        if isinstance(epoch, pd.DatetimeIndex):
            epoch = epoch.to_series()

        intervals = self.cycle_intervals

        available_kind = intervals.columns.get_level_values("kind")
        if kind is None:
            kind = available_kind
        elif isinstance(kind, str):
            if kind == "Edges":
                intervals = intervals.loc[:, ["Fall", "Rise"]]
            else:
                if kind not in available_kind:
                    raise ValueError(f"""Interval `{kind!s}` is unavailable""")
                intervals = intervals.loc[:, [kind]]
        elif hasattr(kind, "__iter__"):
            if not np.all([k in available_kind for k in kind]):
                raise ValueError(f"""Interval `{kind!s}` is unavailable""")
            intervals = intervals.loc[:, kind]
        else:
            raise ValueError(f"""Interval `{kind!s}` is unavailable""")

        if tk_cycles is not None:
            intervals = intervals.loc[tk_cycles]

        ii = pd.IntervalIndex(intervals.stack()).sort_values()
        if not (ii.is_unique and ii.is_monotonic_increasing):
            raise ValueError

        cut = pd.cut(epoch, ii)
        cut.name = "Cycle_Interval"

        return cut

    ############################################################
    # Tools for selecting data within some dt of cycle extrema #
    ############################################################
    def calculate_extrema_bands(self, dt="365d"):
        r"""Return time windows around indicator extrema.

        Parameters
        ----------
        dt : str or pandas.Timedelta, optional
            Half-width of the window around each extremum. Defaults to ``"365d"``.

        Returns
        -------
        pandas.DataFrame
            ``Min`` and ``Max`` intervals for each cycle.
        """
        dt = pd.to_timedelta(dt)
        extrema = self.data.stack()

        dt = pd.to_timedelta(dt)
        dt = np.atleast_1d(dt)
        if dt.size == 2:
            dl, dr = dt
        elif dt.size == 1:
            dl = dr = dt[0]
        else:
            raise ValueError("Only know how to handle 1 or 2 dt options.")

        left = extrema.subtract(dl)
        right = extrema.add(dr)
        lr = pd.DataFrame({"left": left, "right": right})

        def make_interval(x):
            return pd.Interval(x.loc["left"], x.loc["right"])

        bands = lr.apply(make_interval, axis=1).unstack(level="kind")
        self._extrema_bands = bands
        return bands

    def cut_about_extrema_bands(self, epoch, tk_cycles=None, kind=None):
        r"""Bin epochs relative to extrema bands.

        Computed with :py:meth:`calculate_extrema_bands`.

        Parameters
        ----------
        epoch : pandas.DatetimeIndex
            Times to classify.
        tk_cycles : slice, optional
            Subset of cycles to use when cutting.
        kind : {"Min", "Max"}, optional
            Restrict the classification to minima or maxima.

        Returns
        -------
        tuple[pandas.Series, pandas.Series]
            A series of intervals and a mapped series of the form ``"N-Min"`` or
            ``"N-Max"``.
        """
        bands = self.extrema_bands
        if tk_cycles is not None:
            bands = bands.loc[tk_cycles]

        if kind is None:
            kind = ["Min", "Max"]

        elif isinstance(kind, str):
            kind = [kind]

        bands = bands.loc[:, kind]
        bands = bands.stack()

        # TODO: verify bands shape
        intervals = pd.IntervalIndex(bands.values).sort_values()
        cut = pd.cut(epoch, intervals)
        cut = pd.Series(cut, index=epoch, name="spec_by_extrema_band")

        mapper = bands.reset_index(name="Intervals").set_index("Intervals")
        mapper = mapper.loc[:, "Number"].astype(str) + "-" + mapper.loc[:, "kind"]
        mapped = cut.map(mapper)

        return cut, mapped
