#!/usr/bin/env python
"""Access sunspot-number data from the SIDC."""

import pdb  # noqa: F401
import numpy as np
import pandas as pd
import matplotlib as mpl

from pathlib import Path
from collections import namedtuple

from .. import base

Base = base.Base
ID = base.ID
DataLoader = base.DataLoader
IndicatorExtrema = base.IndicatorExtrema
_Loader_Dtypes_Columns = base._Loader_Dtypes_Columns
ActivityIndicator = base.ActivityIndicator

# import Base, ID, DataLoader, _Loader_Dtypes_Columns, ActivityIndicator

pd.set_option("mode.chained_assignment", "raise")


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
        return r"http://www.sidc.be/silso/INFO/"

    @property
    def _trans_url(self):
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
    @property
    def data_path(self):
        return super().data_path / "sidc" / self.key

    def convert_nans(self, data):
        data.replace(-1, np.nan, inplace=True)

    def download_data(self, new_data_path, old_data_path):
        r"""Download and save the data to `new_data_path`.

        If `old_data_path` exists,
        remove it.
        """
        url = self.url  # self._trans_url.get(key)
        self.logger.info("Downloading from SIDC sunspot number\nurl: %s", url)

        key = self.key
        dtypes_columns = _Dtypes_Columns._asdict().get(key)
        if dtypes_columns is None:
            raise NotImplementedError(
                f"""You have not yet used the SSN specified by your key ({key}). Please verify the column labels before continuing."""
            )

        csv = pd.read_csv(self.url, sep=";", header=None, dtype=dtypes_columns.dtypes)
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

            std_error.columns = (std_error.columns.to_series() + "std_error").values

            csv = pd.concat([csv, std_error], axis=1, sort=True)

        else:
            std_error = csv.loc[:, "std"].divide(
                csv.loc[:, "n_obs"].apply(np.sqrt), axis=0
            )
            csv.loc[:, "std_error"] = std_error
            csv.sort_index(axis=1, inplace=True)

        csv.set_index(ts, inplace=True)
        self.convert_nans(csv)

        new_data_path = new_data_path.with_suffix(".csv")
        csv.to_csv(new_data_path, sep=",", na_rep="NaN")
        old_data_path = old_data_path.with_suffix(".csv")
        try:
            old_data_path.unlink()
        except FileNotFoundError:
            pass

    def load_data(self):
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
        self._init_logger()
        self.set_id(SIDC_ID(key))
        self.load_data()
        self.set_extrema()
        self.calculate_extrema_kind()
        self.calculate_edge()

    #     @property
    #     def extrema(self):
    #         return self._extrema

    @property
    def spec_by_ssn_band(self):
        return self._spec_by_ssn_band

    @property
    def ssn_band_intervals(self):
        return self._ssn_band_intervals

    def load_data(self):
        loader = SIDCLoader(self.id.key, self.id.url)
        loader.load_data()
        self._loader = loader

    def set_extrema(self):
        self._extrema = SSNExtrema()

    def interpolate_data(self, target_index, key="ssn"):
        interpolated = super(SIDC, self).interpolate_data(
            self.data.loc[:, key].dropna(how="any", axis=0), target_index
        )
        self._interpolated = interpolated
        return interpolated

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
        try:
            #             return self._normalized_ssn
            return self.data.loc[:, "nssn"]
        except KeyError:  # AttributeError:
            return self.run_normalization()

    def _run_normalization(self, indicator, norm_fcn):
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
        self.data.sort_index(axis=1, inplace=True)

        try:
            interpolated = self.interpolated.loc[:, "ssn"]
            normed_interpolated = self._run_normalization(interpolated, norm_fcn)
            self.interpolated.loc[:, "nssn"] = normed_interpolated

        except AttributeError:
            pass

        return normed

    run_normalization.__doc__ = ActivityIndicator.run_normalization

    def cut_spec_by_ssn_band(self, key="ssn", dssn=2.0):
        r"""Cut the sunspot number at each spectrum in intervals of width +/- dssn."""

        dssn = float(dssn)
        if (key == "nssn") and (dssn >= 1):
            raise ValueError("Normalized SSN requires that dssn < 1")

        data = self.data.loc[:, key]
        mids = np.arange(0, data.max(), 2.0 * dssn)

        left = mids - dssn
        right = mids + dssn
        intervals = [pd.Interval(ll, rr) for ll, rr in zip(left, right)]
        intervals = pd.IntervalIndex(intervals, name="ssn_intervals")
        try:
            cut = pd.cut(
                self.interpolated.loc[:, key],  # TODO: Fix this generalized hack
                intervals,
            )
        except KeyError as e:
            if np.isnan(e.args[0]):
                # Check that intervals don't overlap.
                for ll, rr in zip(intervals[:-1], intervals[1:]):
                    l_upper = ll.right
                    r_lower = rr.left
                    if l_upper > r_lower:
                        msg = f"""Your intervals can't overlap.
Interval 0: {ll}
Interval 1: {rr}
It causes a KeyError in `pd.cut`."""
                        raise ValueError(msg)
            else:
                raise

        cut.name = f"{key}_band"
        self._spec_by_ssn_band = cut
        self._ssn_band_intervals = intervals
        return cut

    def plot_on_colorbar(self, cax, t0, t1, vertical_cbar=True):
        r"""Plot SSN on the color bar."""
        # TODO: Refactor and abstract to :pyclass:`ActivityIndicator`.
        ssn = self.data.loc[t0:t1, "ssn"]

        x = mpl.dates.date2num(ssn.index)
        y = ssn  # .values
        #         print("SSN values", y.min(), y.max())

        if vertical_cbar:
            y0, y1 = cax.get_xlim()
        else:
            y0, y1 = cax.get_ylim()

        dy = y1 - y0
        #         s0, s1 = 0, 200
        s0, s1 = np.array([0, np.round(ssn.max(), -2)], dtype=int)
        y = ((y / s1) * dy) + y0
        #       print("Map Range", y0, y1)
        #       print("Scaled SSN", y.min(), y.max())

        if vertical_cbar:
            cax.plot(y, x, ls="-", color="w", lw=1)
            cax.plot(y, x, ls=(0, (7, 3, 2, 3, 2, 3, 2, 3)), color="k", lw=1)
            cax.set_xlabel(r"$\mathrm{SSN} \; [\#]$")
            x0, x1 = cax.get_xlim()

            # We force the maximum value to be even and minimum value to be
            # odd, so the mid-point must be an even integer.
            cax.xaxis.set_ticks([x0, 0.5 * (x0 + x1), x1])
            cax.xaxis.set_ticklabels((s0, int(0.5 * (s0 + s1)), s1))
            cax.xaxis.set_tick_params(rotation=25)
            cax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(25))
            cax.yaxis.set_tick_params(left=True)

        else:
            cax.plot(x, y, ls="-", color="w", lw=1)
            cax.plot(x, y, ls=(0, (7, 3, 2, 3, 2, 3, 2, 3)), color="k", lw=1)
            cax.set_ylabel(r"$\mathrm{SSN} \; [\#]$")
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


class SSNExtrema(IndicatorExtrema):
    def load_or_set_data(self, *args, **kwargs):
        if len(args) or len(kwargs):
            raise ValueError(
                f"""{self.__class__.__name__} expects empty args and kwargs."""
            )

        path = Path(__file__).parent / "ssn_extrema.csv"
        data = pd.read_csv(path, header=0, skiprows=45, index_col=0)
        data = pd.to_datetime(data.stack(), format="%Y-%m-%d").unstack(level=1)
        data.columns.names = ["kind"]
        self._data = data
