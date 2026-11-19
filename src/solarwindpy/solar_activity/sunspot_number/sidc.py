#!/usr/bin/env python
"""Access sunspot-number data from the SIDC."""

__all__ = [
    "SIDC_ID",
    "SIDCLoader",
    "SIDC",
    "SSNExtrema",
]

import numpy as np
import pandas as pd

from pathlib import Path
from collections import namedtuple

from ..base import (
    ActivityIndicator,
    DataLoader,
    ID,
    IndicatorExtrema,
    _Loader_Dtypes_Columns,
)

_d_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: int, 3: float, 4: float, 5: float, 6: int, 7: bool},
    ["year", "month", "day", "year_fraction", "ssn", "std", "n_obs", "definitive"],
)

# year_fraction: the middle of the period, in years (a month's is ~ day 15).
_m_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
    ["year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"],
)

_y_dtypes_columns = _Loader_Dtypes_Columns(
    {0: float, 1: float, 2: float, 3: int, 4: bool},
    ["year", "ssn", "std", "n_obs", "definitive"],
)

_hm_dtypes_columns = _Loader_Dtypes_Columns(
    {
        0: int,
        1: int,
        2: float,
        3: float,
        4: float,
        5: float,
        6: float,
        7: float,
        8: float,
        9: int,
        10: int,
        11: int,
        12: bool,
    },
    (
        "year",
        "month",
        "year_fraction",
        "total_ssn",
        "north_ssn",
        "south_ssn",
        "total_std",
        "north_std",
        "south_std",
        "n_total",
        "n_north",
        "n_south",
        "definitive",
    ),
)

_hd_dtypes_columns = _Loader_Dtypes_Columns(
    {
        0: int,
        1: int,
        2: int,
        3: float,
        4: float,
        5: float,
        6: float,
        7: float,
        8: float,
        9: float,
        10: int,
        11: int,
        12: int,
        13: bool,
    },
    (
        "year",
        "month",
        "day",
        "year_fraction",
        "total_ssn",
        "north_ssn",
        "south_ssn",
        "total_std",
        "north_std",
        "south_std",
        "n_total",
        "n_north",
        "n_south",
        "definitive",
    ),
)


# One row per SILSO series: its file under ``SIDC_ID._url_base``, its column
# layout, and the date resolution ``SIDCLoader.read_data`` builds the time
# index from. Each 13-month smoothed series is laid out as its monthly one.
_Series = namedtuple("_Series", ["url", "layout", "dates"])

_SERIES = {
    "d": _Series("sndtotcsv.php", _d_dtypes_columns, "day"),
    "m": _Series("snmtotcsv.php", _m_dtypes_columns, "month"),
    "m13": _Series("snmstotcsv.php", _m_dtypes_columns, "month"),
    "y": _Series("snytotcsv.php", _y_dtypes_columns, "decimal year"),
    "hd": _Series("sndhemcsv.php", _hd_dtypes_columns, "day"),
    "hm": _Series("snmhemcsv.php", _hm_dtypes_columns, "month"),
    "hm13": _Series("snmshemcsv.php", _hm_dtypes_columns, "month"),
}


class SIDC_ID(ID):
    r"""Identifier mapping a SIDC sunspot-number series to its download URL."""

    def __init__(self, key):
        r"""Key identifies the SSN used.

        ====== =================== ================
        Key          Type                URL
        ====== =================== ================
        d      Daily total         sndtotcsv.php
        m      Monthly total       snmtotcsv.php
        m13    13-month smoothed   snmstotcsv.php
        y      Yearly total        snytotcsv.php
        hd     Hemispheric Daily   sndhemcsv.php
        hm     Hemispheric Monthly snmhemcsv.php
        hm13   13-Month Smoothed   snmshemcsv.php
               Hemispheric
        ====== =================== ================

        URLs replace the wild card in ``http://www.sidc.be/silso/INFO/*``.
        """
        super(SIDC_ID, self).__init__(key)

    @property
    def _url_base(self):
        r"""Base URL of the SILSO data service."""
        return r"http://www.sidc.be/silso/INFO/"

    @property
    def _trans_url(self):
        r"""Map from series key to file name under :attr:`_url_base`."""
        return {key: series.url for key, series in _SERIES.items()}


class SIDCLoader(DataLoader):
    r"""Download, cache, and load one SIDC sunspot-number series.

    Parameters
    ----------
    key : str
        Series key, as in :class:`SIDC_ID` (e.g. ``"m"`` for the monthly
        total).
    url : str
        Download URL of the series, or a local path to a file in SILSO's
        layout, which is read as is and never cached.

    Examples
    --------
    In normal use the URL comes from :class:`SIDC_ID`. This example stays
    offline by reading a small local file in SILSO's monthly layout
    (year; month; year fraction; SSN; standard deviation; number of
    observations; definitive flag), where ``-1`` marks a missing value:

    >>> import tempfile
    >>> from pathlib import Path
    >>> rows = (
    ...     "2019;12;2019.958;1.5;0.4;500;1\n"
    ...     "2020;01;2020.042;6.2;1.1;400;1\n"
    ...     "2020;02;2020.124;-1;-1;0;0\n"
    ... )
    >>> with tempfile.TemporaryDirectory() as d:
    ...     path = Path(d) / "monthly.csv"
    ...     _ = path.write_text(rows, encoding="utf-8")
    ...     loader = SIDCLoader("m", str(path))
    ...     loader.load_data()
    >>> loader.data.index.strftime("%Y-%m").tolist()
    ['2019-12', '2020-01', '2020-02']
    >>> loader.data["ssn"].tolist()
    [1.5, 6.2, nan]

    Each month is labelled with the solar cycle, from :class:`SSNExtrema`,
    that contains it:

    >>> loader.data["cycle"].tolist()
    [24, 25, 25]
    """

    @property
    def max_age(self):
        r"""One day: SILSO updates its series daily."""
        return pd.Timedelta(days=1)

    def convert_nans(self, data):
        r"""Replace SILSO's missing-value sentinel, -1, with NaN in place.

        Parameters
        ----------
        data : pandas.DataFrame
            Series read from SILSO; modified in place.
        """
        data.replace(-1, np.nan, inplace=True)

    def read_data(self, path):
        r"""Parse a series downloaded from SILSO.

        Parameters
        ----------
        path : str or pathlib.Path
            File in SILSO's semicolon-separated, headerless layout.

        Returns
        -------
        pandas.DataFrame
            The series indexed by time, with -1 replaced by NaN and a standard
            error, std / sqrt(n), added for each standard deviation.
        """
        self.logger.info("Reading SIDC sunspot number\npath: %s", path)

        key = self.key
        series = _SERIES.get(key)
        if series is None:
            raise NotImplementedError(
                f"""You have not yet used the SSN specified by your key ({key}). Please verify the column labels before continuing."""
            )

        csv = pd.read_csv(path, sep=";", header=None, dtype=series.layout.dtypes)
        csv.columns = series.layout.columns

        if series.dates == "month":
            ts = pd.to_datetime(csv.loc[:, ["year", "month"]].assign(day=1))

        elif series.dates == "day":
            ts = pd.to_datetime(csv.loc[:, ["year", "month", "day"]])

        else:  # "decimal year"
            import astropy.time

            dt = astropy.time.Time(csv.loc[:, "year"], format="decimalyear")
            ts = pd.DatetimeIndex(dt.datetime)

        if key.startswith("h"):
            std = csv.loc[:, ["total_std", "north_std", "south_std"]]
            cnt = csv.loc[:, ["n_total", "n_north", "n_south"]]

            std.columns = (
                std.columns.to_series().str.split("_").apply(lambda x: x[0]).values
            )
            cnt.columns = cnt.columns.to_series().str.split("_").apply(lambda x: x[1])
            std_error = std.divide(cnt.apply(np.sqrt), axis=1)

            std_error.columns = (std_error.columns.to_series() + "_std_error").values

            csv = pd.concat([csv, std_error], axis=1, sort=True)

        else:
            std_error = csv.loc[:, "std"].divide(
                csv.loc[:, "n_obs"].apply(np.sqrt), axis=0
            )
            csv.loc[:, "std_error"] = std_error
            csv = csv.sort_index(axis=1)

        csv = csv.set_index(ts)
        self.convert_nans(csv)
        return csv

    def load_data(self):
        r"""Load the cached series and label each row with its cycle.

        Downloads the series first if the cache is stale. Adds a ``cycle``
        column holding the number of the solar cycle, from
        :class:`SSNExtrema`, that contains each time. The table is kept, and
        :meth:`SIDC.set_extrema` reads it, so the labels and
        :attr:`SIDC.extrema` come from one table.
        """
        super().load_data()

        extrema = SSNExtrema()
        self._extrema = extrema
        # The cycle to which each measurement belongs.
        data = self.data
        cut = pd.cut(data.index, pd.IntervalIndex(extrema.cycle_intervals.Cycle.values))
        cut = pd.Series(cut, index=data.index, name="cycle")
        cut = cut.map(
            extrema.cycle_intervals.Cycle.reset_index().set_index("Cycle").Number
        )

        data = pd.concat([data, cut], axis=1, sort=True)
        self._data = data

        self.logger.info("Load complete")


class SIDC(ActivityIndicator):
    """Solar sunspot number data from the SIDC.

    Parameters
    ----------
    key : str
        Passed to :class:`SIDC_ID` to select the data series.
    """

    def __init__(self, key):
        self.set_id(SIDC_ID(key))
        self.load_data()
        self.set_extrema()
        self.calculate_extrema_kind()
        self.calculate_edge()

    def load_data(self):
        r"""Load the series through a :class:`SIDCLoader`."""
        loader = SIDCLoader(self.id.key, self.id.url)
        loader.load_data()
        self._loader = loader

    def set_extrema(self):
        r"""Set :attr:`extrema` to the :class:`SSNExtrema` the loader labelled the cycles with."""
        self._extrema = self.loader._extrema

    def interpolate_data(self, target_index, key="ssn"):
        r"""Interpolate one column onto ``target_index``.

        Parameters
        ----------
        target_index : pandas.DatetimeIndex
            Times to interpolate onto.
        key : str, optional
            Column of :attr:`data` to interpolate.

        Returns
        -------
        pandas.DataFrame
            Interpolated values; NaN outside the data's time range.
        """
        return self._interpolate(
            self.data.loc[:, key].dropna(how="any", axis=0), target_index
        )

    def _cycles(self):
        r"""Yield ``(k, ssn, before_max, after_max)`` for each cycle ``k`` in :attr:`data`.

        ``ssn`` holds the cycle's sunspot numbers; ``before_max`` and
        ``after_max`` are boolean masks over them, split at the cycle's
        maximum in :attr:`extrema`.
        """
        extrema = self.extrema.data
        for k, g in self.data.loc[:, ["cycle", "ssn"]].groupby("cycle"):
            ssn = g.loc[:, "ssn"]
            max_date = extrema.loc[k, "Max"]
            yield k, ssn, ssn.index <= max_date, ssn.index > max_date

    def calculate_extrema_kind(self):
        r"""Determine whether an SSN observation belongs to a cycle Minimum or Maximum.

            Min: ssn < cycle mean
            Max: ssn >= cycle mean

        Labels for the extremum kind include indicators for which cycle the extremum
        belongs to. These can be easily stripped with string manipulations, but are
        difficult to calculate after the fact.
        """
        kind = pd.Series(np.nan, index=self.data.index, dtype=str)
        for k, g, before_max, after_max in self._cycles():
            mid = 0.5 * g.max()

            case = pd.Series(index=g.index, dtype=str)
            case.loc[g >= mid] = f"{k}-Max"
            case.loc[(g < mid) & before_max] = f"{k}-Min"
            case.loc[(g < mid) & after_max] = f"{k + 1}-Min"

            kind.update(case)

        self.data.loc[:, "extremum"] = kind

    def calculate_edge(self):
        r"""Determine whether an SSN observation belongs to a rising or falling edge."""
        kind = pd.Series(np.nan, index=self.data.index, dtype=str)
        for k, g, before_max, after_max in self._cycles():
            case = pd.Series(index=g.index, dtype=str)
            case.loc[before_max] = "Rise"
            case.loc[after_max] = "Fall"

            kind.update(case)

        self.data.loc[:, "edge"] = kind

    #################
    # Normalize SSN #
    #################
    @property
    def normalized(self):
        r"""SSN normalized within each cycle, computed by :meth:`run_normalization` if absent."""
        try:
            return self.data.loc[:, "nssn"]
        except KeyError:
            return self.run_normalization()

    def run_normalization(self, norm_by="max"):
        # Note: "max" and "feature-scale" are the same if the min(SSN) = 0.
        assert norm_by in ("max", "zscore", "feature-scale")
        self.logger.info("Normalizing SSN by %s", norm_by)
        self._norm_by = norm_by

        if norm_by == "max":

            def norm_fcn(g):
                return g.divide(g.max())

        elif norm_by == "zscore":

            def norm_fcn(g):
                return g.subtract(g.mean()).divide(g.std())

        elif norm_by == "feature-scale":

            def norm_fcn(g):
                return g.subtract(g.min()).divide(g.max() - g.min())

        ssn = self.data.loc[:, "ssn"]
        normed = self._run_normalization(ssn, norm_fcn)

        self.data.loc[:, "nssn"] = normed
        # The loader holds the frame; sorting returns a new one (pandas deprecates
        # inplace=True), which replaces it.
        self.loader._data = self.data.sort_index(axis=1)

        try:
            interpolated = self.interpolated.loc[:, "ssn"]
            normed_interpolated = self._run_normalization(interpolated, norm_fcn)
            self.interpolated.loc[:, "nssn"] = normed_interpolated

        except AttributeError:
            pass

        return normed

    run_normalization.__doc__ = ActivityIndicator.run_normalization.__doc__

    @staticmethod
    def ssn_scale_top(ssn):
        r"""Top of an SSN scale that starts at 0 and holds all of ``ssn``.

        The peak of ``ssn`` rounded up to the next multiple of 100, and never
        less than 100, so the series always stays inside the scale and a
        quiet or empty series cannot give a zero-height scale.

        Parameters
        ----------
        ssn : pandas.Series
            Sunspot numbers to fit on the scale.

        Returns
        -------
        int
            The scale top.
        """
        # Python's max keeps 100 when the peak is NaN (an empty series).
        return int(max(100, np.ceil(ssn.max() / 100.0) * 100))


class SSNExtrema(IndicatorExtrema):
    r"""Solar-cycle sunspot-number extrema tabulated in ``ssn_extrema.csv``.

    The table ships with the package, so no download is needed. It takes
    no arguments.

    Examples
    --------
    >>> extrema = SSNExtrema()
    >>> extrema.data.loc[24].dt.strftime("%Y-%m-%d").to_dict()
    {'Min': '2008-12-01', 'Max': '2014-04-01'}

    Cycle 24 rises from its minimum to its maximum and falls until the
    minimum of cycle 25:

    >>> extrema.cycle_intervals.loc[24, "Fall"]
    Interval(2014-04-01 00:00:00, 2019-12-01 00:00:00, closed='right')
    """

    def load_or_set_data(self, *args, **kwargs):
        r"""Read the ``Min`` and ``Max`` dates of each cycle from ``ssn_extrema.csv``.

        Parameters
        ----------
        *args, **kwargs
            Must be empty; accepted for the signature of
            :meth:`~solarwindpy.solar_activity.base.IndicatorExtrema.load_or_set_data`.

        Raises
        ------
        ValueError
            If any argument is passed.
        """
        if len(args) or len(kwargs):
            raise ValueError(
                f"""{self.__class__.__name__} expects empty args and kwargs."""
            )

        path = Path(__file__).parent / "ssn_extrema.csv"
        data = pd.read_csv(path, header=0, skiprows=48, index_col=0)
        data = pd.to_datetime(data.stack(), format="%Y-%m-%d").unstack(level=1)
        data.columns.names = ["kind"]
        self._data = data
