import pdb  # noqa: F401
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
    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        logger = logging.getLogger(
            name="{}.{}".format(__name__, self.__class__.__name__)
        )
        self._logger = logger

    def __str__(self):
        return self.__class__.__name__


class ID(Base):
    def __init__(self, key):
        self._init_logger()
        self.set_key(key)

    @abstractproperty
    def _url_base(self):
        pass

    @abstractproperty
    def _trans_url(self):
        pass

    @property
    def key(self):
        return self._key

    @property
    def url(self):
        r"""URL specifying location from which data was downloaded.
        """
        return self._url

    def set_key(self, key):
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
    def __init__(self, key, url):
        r"""
        key: str
            Unique data identifier, typically from something like `SIDCID`.
        url: str
        """
        self._init_logger()
        self.set_key(key)
        self.set_url(url)
        self.get_data_ctime()
        self.get_data_age()

    @abstractproperty
    def data_path(self):
        #        return Path(__file__).parent / "data"
        return Path.home() / "solarwindpy" / "data"

    @abstractstaticmethod
    def convert_nans(data):
        pass

    @abstractmethod
    def download_data(self):
        pass

    @abstractmethod
    def load_data(self):
        self.logger.info(f"""Loading {self.key!s} data""")

        self.maybe_update_stale_data()

        today = pd.to_datetime("today").strftime("%Y%m%d")
        fpath = (self.data_path / today).with_suffix(".csv")
        data = pd.read_csv(fpath, index_col=0, header=0)

        data.set_index(pd.DatetimeIndex(data.index), inplace=True)
        self._data = data

    @property
    def logger(self):
        return self._logger

    @property
    def data(self):
        return self._data

    @property
    def key(self):
        return self._key

    @property
    def url(self):
        return self._url

    @property
    def ctime(self):
        return self._ctime

    @property
    def age(self):
        return self._age

    def _init_logger(self):
        logger = logging.getLogger(
            name="{}.{}".format(__name__, self.__class__.__name__)
        )
        self._logger = logger

    def set_key(self, key):
        self._key = key

    def set_url(self, new):
        self._url = new

    def get_data_ctime(self):
        r"""Examine the path at which the local data was saved to determine the time at
        which it was created. Date format is (YYYYMMDD).
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
        #         if dates.size > 1:
        #             raise ValueError("Too many dates: %s" % ", ".join(dates.astype(str)))
        #         elif not dates.size:
        #             ctime = pd.to_datetime(0)
        #         else:
        #             ctime = pd.to_datetime(dates[0])

        assert dates.size == 1
        ctime = pd.to_datetime(dates[0])

        self.logger.info("Local data ctime %s", ctime)
        self._ctime = ctime

    def get_data_age(self):
        ctime = self.ctime
        today = pd.to_datetime("today")
        dt = today - ctime
        self._data_age = dt

    def maybe_update_stale_data(self):
        r"""Only the most recent data is retained to save space.
        """
        self.logger.info("Updating stale data")

        old_ctime = self.ctime
        new_ctime = pd.to_datetime("today")

        if new_ctime.date() > old_ctime.date():
            old_data_path = self.data_path / old_ctime.strftime("%Y%m%d")
            new_data_path = self.data_path / new_ctime.strftime("%Y%m%d")
            new_data_path.parent.mkdir(parents=True, exist_ok=True)

            self.download_data(new_data_path, old_data_path)


class ActivityIndicator(Base):
    @property
    def id(self):
        return self._id

    @property
    def loader(self):
        return self._loader

    @property
    def data(self):
        r"""Shortcut to `self.loader.data`.
        """
        return self.loader.data

    @property
    def interpolated(self):
        return self._interpolated

    def set_id(self, new):
        assert isinstance(new, ID)
        self._id = new

    # Need to store `interpolated` in subclass. Allows normalized ssn to be interpolated.
    @abstractmethod
    def interpolate_data(self, source_data, target_index):
        assert isinstance(target_index, pd.DatetimeIndex)
        assert isinstance(source_data.index, pd.DatetimeIndex)

        if isinstance(source_data, pd.Series):
            source_data = source_data.to_frame()

        nans = source_data.isna().any().any()
        if nans:
            raise NotImplementedError(
                """You must drop NaNs in the subclass's caller
            before calling parent method."""
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
        self._interpolated = interpolated
        return interpolated
