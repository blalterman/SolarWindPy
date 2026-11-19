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
import matplotlib as mpl

from pathlib import Path
from collections import namedtuple

from ...plotting.base import Guides
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

_m_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
    ["year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"],
)

_m13_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
    ("year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"),
)

_y_dtypes_columns = _Loader_Dtypes_Columns(
    {0: float, 1: float, 2: float, 3: int, 4: bool},
    ["year", "ssn", "std", "n_obs", "definitive"],
)

# Column 3: Date in fraction of year for the middle of the corresponding month (~ day 15)

_hm13_dtypes_columns = _Loader_Dtypes_Columns(
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


_Dtypes_Columns = namedtuple("Dtypes_Columns", "d,m,m13,y,hd,hm,hm13", defaults=(None,))

_Dtypes_Columns = _Dtypes_Columns(
    _d_dtypes_columns,
    _m_dtypes_columns,
    _m13_dtypes_columns,
    _y_dtypes_columns,
    _hd_dtypes_columns,
    _hm_dtypes_columns,
    _hm13_dtypes_columns,
)


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
        trans_url = (
            ("d", r"sndtotcsv.php"),
            ("m", r"snmtotcsv.php"),
            ("m13", r"snmstotcsv.php"),
            ("y", r"snytotcsv.php"),
            ("hd", r"sndhemcsv.php"),
            ("hm", r"snmhemcsv.php"),
            ("hm13", r"snmshemcsv.php"),
        )
        return dict(trans_url)


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
        dtypes_columns = _Dtypes_Columns._asdict().get(key)
        if dtypes_columns is None:
            raise NotImplementedError(
                f"""You have not yet used the SSN specified by your key ({key}). Please verify the column labels before continuing."""
            )

        csv = pd.read_csv(path, sep=";", header=None, dtype=dtypes_columns.dtypes)
        csv.columns = dtypes_columns.columns

        if key in ("m13", "m", "hm", "hm13"):
            dt = csv.loc[:, ["year", "month"]]
            dt.loc[:, "day"] = 1
            ts = pd.to_datetime(dt)

        elif key in ("d", "hd"):
            dt = csv.loc[:, ["year", "month", "day"]]
            ts = pd.to_datetime(dt)

        elif key in ("y",):
            import astropy.time

            dt = astropy.time.Time(csv.loc[:, "year"], format="decimalyear")
            ts = pd.DatetimeIndex(dt.datetime)

        else:
            raise NotImplementedError(
                f"Please specify how to build {key} datetime column"
            )

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
        :class:`SSNExtrema`, that contains each time.
        """
        super().load_data()

        extrema = SSNExtrema()
        # Calculate Cycle to which each mesurement belongs
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
        r"""Set :attr:`extrema` to the tabulated :class:`SSNExtrema`."""
        self._extrema = SSNExtrema()

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

    def calculate_extrema_kind(self):
        r"""Determine whether an SSN observation belongs to a cycle Minimum or Maximum.

            Min: ssn < cycle mean
            Max: ssn >= cycle mean

        Labels for the extremum kind include indicators for which cycle the extremum
        belongs to. These can be easily stripped with string manipulations, but are
        difficult to calculate after the fact.
        """
        extrema = self.extrema.data
        kind = pd.Series(np.nan, index=self.data.index, dtype=str)
        for k, g in self.data.loc[:, ["cycle", "ssn"]].groupby("cycle"):
            g = g.loc[:, "ssn"]
            mid = 0.5 * g.max()
            max_date = extrema.loc[k, "Max"]
            before_max = g.index <= max_date
            after_max = g.index > max_date

            case = pd.Series(index=g.index, dtype=str)
            case.loc[g >= mid] = f"{k}-Max"
            case.loc[(g < mid) & before_max] = f"{k}-Min"
            case.loc[(g < mid) & after_max] = f"{k + 1}-Min"

            kind.update(case)

        self.data.loc[:, "extremum"] = kind

    def calculate_edge(self):
        r"""Determine whether an SSN observation belongs to a rising or falling edge."""
        extrema = self.extrema.data
        kind = pd.Series(np.nan, index=self.data.index, dtype=str)

        for k, g in self.data.loc[:, ["cycle", "ssn"]].groupby("cycle"):
            g = g.loc[:, "ssn"]
            max_date = extrema.loc[k, "Max"]
            before_max = g.index <= max_date
            after_max = g.index > max_date

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

    def plot_on_colorbar(self, cax, t0, t1, vertical_cbar=True):
        r"""Plot SSN on the color bar.

        The sunspot numbers are scaled onto the colour bar's value axis over
        ``[0, top]``, where ``top`` is :meth:`ssn_scale_top` of the window, so
        the line always stays inside the scale. Major ticks are labelled 0, ``top / 2`` and ``top``;
        minor ticks fall every 25.

        Parameters
        ----------
        cax : matplotlib.axes.Axes
            The colour bar's axes.
        t0, t1 : datetime-like
            Start and end of the window plotted.
        vertical_cbar : bool
            If True, the colour bar is vertical: time runs along its y-axis
            and the SSN scale along its x-axis.

        Returns
        -------
        cax : matplotlib.axes.Axes
        underlay : matplotlib.lines.Line2D
            The solid white line drawn under the overlay.
        overlay : matplotlib.lines.Line2D
            The dash-dotted black sunspot-number line.
        guides : Guides
            Every field None: the method receives only the colour bar's
            axes, not the :class:`matplotlib.colorbar.Colorbar`, and draws no
            guide of its own. The slot keeps the return order
            ``(ax, artists..., guides)`` shared by every plot.
        """
        # TODO: Refactor and abstract to :pyclass:`ActivityIndicator`.
        ssn = self.data.loc[t0:t1, "ssn"]

        x = mpl.dates.date2num(ssn.index)
        y = ssn

        if vertical_cbar:
            y0, y1 = cax.get_xlim()
        else:
            y0, y1 = cax.get_ylim()

        dy = y1 - y0
        s0, s1 = 0, self.ssn_scale_top(ssn)
        y = ((y / s1) * dy) + y0

        if vertical_cbar:
            (underlay,) = cax.plot(y, x, ls="-", color="w", lw=1)
            (overlay,) = cax.plot(
                y, x, ls=(0, (7, 3, 2, 3, 2, 3, 2, 3)), color="k", lw=1
            )
            cax.set_xlabel(r"$\mathrm{SSN} \; \left[\#\right]$")
            x0, x1 = cax.get_xlim()

            # We force the maximum value to be even and minimum value to be
            # odd, so the mid-point must be an even integer.
            cax.xaxis.set_ticks([x0, 0.5 * (x0 + x1), x1])
            cax.xaxis.set_ticklabels((s0, int(0.5 * (s0 + s1)), s1))
            cax.xaxis.set_tick_params(rotation=25)
            cax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(25))
            cax.yaxis.set_tick_params(left=True)

        else:
            (underlay,) = cax.plot(x, y, ls="-", color="w", lw=1)
            (overlay,) = cax.plot(
                x, y, ls=(0, (7, 3, 2, 3, 2, 3, 2, 3)), color="k", lw=1
            )
            cax.set_ylabel(r"$\mathrm{SSN} \; \left[\#\right]$")
            x0, x1 = cax.get_ylim()

            # We force the maximum value to be even and minimum value to be
            # odd, so the mid-point must be an even integer.
            cax.yaxis.set_ticks([x0, 0.5 * (x0 + x1), x1])
            cax.yaxis.set_ticklabels((s0, int(0.5 * (s0 + s1)), s1))
            cax.yaxis.set_tick_params(rotation=25)
            cax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(25))
            cax.xaxis.set_tick_params(top=True)
            cax.xaxis.set_ticks_position("top")
            cax.xaxis.set_label_position("top")

        return cax, underlay, overlay, Guides()


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
