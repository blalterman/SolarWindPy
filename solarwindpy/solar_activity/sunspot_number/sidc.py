#!/usr/bin/env python
r"""Sunspot number from the solar information data center (SIDC).

Data taken from <http://www.sidc.be/silso/datafiles#total>.

Available SSN listed in :py:class:`SIDC_ID`. Descriptions are available at the SIDC
website. Per the website, standard error is std/sqrt(n_obs) for each SSN value.
"""

import pdb  # noqa: F401
import numpy as np
import pandas as pd

from pathlib import Path

from .. import base

Base = base.Base
ID = base.ID
DataLoader = base.DataLoader
IndicatorExtrema = base.IndicatorExtrema
_Loader_Dtypes_Columns = base._Loader_Dtypes_Columns
ActivityIndicator = base.ActivityIndicator

# import Base, ID, DataLoader, _Loader_Dtypes_Columns, ActivityIndicator

pd.set_option("mode.chained_assignment", "raise")

_m13_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
    ("year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"),
)

_m_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
    ["year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"],
)

_d_dtypes_columns = _Loader_Dtypes_Columns(
    {0: int, 1: int, 2: int, 3: float, 4: float, 5: float, 6: int, 7: bool},
    ["year", "month", "day", "year_fraction", "ssn", "std", "n_obs", "definitive"],
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
        ====== =================== ================

        URLs replace the wild card in <http://www.sidc.be/silso/INFO/*>.
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
        )
        return dict(trans_url)


class SIDCLoader(DataLoader):
    @property
    def data_path(self):
        return super(SIDCLoader, self).data_path / "sidc" / self.key

    def convert_nans(self, data):
        data.replace(-1, np.nan, inplace=True)

    def download_data(self, new_data_path, old_data_path):
        r"""Download and save the data to `new_data_path`. If `old_data_path` exists,
        remove it.
        """
        url = self.url  # self._trans_url.get(key)
        self.logger.info("Downloading from SIDC sunspot number\nurl: %s", url)

        key = self.key
        if key == "m13":
            dtypes_columns = _m13_dtypes_columns
            csv = pd.read_csv(
                self.url, sep=";", header=None, dtype=dtypes_columns.dtypes
            )
            csv.columns = dtypes_columns.columns
            dt = csv.loc[:, ["year", "month"]]
            dt.loc[:, "day"] = 1

        elif key == "m":
            dtypes_columns = _m_dtypes_columns
            csv = pd.read_csv(
                self.url, sep=";", header=None, dtype=dtypes_columns.dtypes
            )
            csv.columns = dtypes_columns.columns
            dt = csv.loc[:, ["year", "month"]]
            dt.loc[:, "day"] = 1

        elif key == "d":
            dtypes_columns = _d_dtypes_columns
            csv = pd.read_csv(
                self.url, sep=";", header=None, dtype=dtypes_columns.dtypes
            )
            csv.columns = dtypes_columns.columns

            dt = csv.loc[:, ["year", "month", "day"]]

        else:
            msg = (
                "You have not yet used the SSN specified by your key (%s). "
                "Please verify the column labels before continuing."
            )
            raise NotImplementedError(msg % key)

        std_error = csv.loc[:, "std"].divide(csv.loc[:, "n_obs"].apply(np.sqrt), axis=0)
        csv.loc[:, "std_error"] = std_error
        csv.sort_index(axis=1, inplace=True)

        ts = pd.to_datetime(dt)
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
        super(SIDCLoader, self).load_data()

        #        today = pd.to_datetime("today").strftime("%Y%m%d")
        #        fpath = (self.data_path / today).with_suffix(".csv")
        #        data = pd.read_csv(fpath, index_col=0, header=0)
        #
        #        self._data = data
        self.logger.info("Load complete")


class SIDC(ActivityIndicator):
    def __init__(self, key):
        r"""
        Parameters
        ----------
        key: str
            See `SIDC_ID`.
        convert_nan: bool
            See `SIDC.convert_nan`.
        """

        self._init_logger()
        self.set_id(SIDC_ID(key))
        self.load_data()
        self._extrema = SSNExtrema()

    @property
    def extrema(self):
        return self._extrema

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

    def interpolate_data(self, target_index):
        interpolated = super(SIDC, self).interpolate_data(
            self.data.loc[:, "ssn"].dropna(how="any", axis=0), target_index
        )
        self._interpolated = interpolated
        return interpolated

    #################
    # Normalize SSN #
    #################
    @property
    def normalized_ssn(self):
        try:
            #             return self._normalized_ssn
            return self.data.loc[:, "nssn"]
        except KeyError:  # AttributeError:
            return self.normalize_ssn()

    #     @property
    #     def interpolated_normalized_ssn(self):
    #         try:
    #             return self._

    @property
    def norm_by(self):
        try:
            return self._norm_by
        except AttributeError:
            raise AttributeError("Please calculate `normalize_ssn`")

    def _run_normalization(self, ssn, norm_fcn):
        cut = self.extrema.cut_spec_by_interval(ssn.index, kind="All")
        joint = pd.concat([ssn, cut], axis=1, keys=["ssn", "cycle"]).sort_index(axis=1)
        grouped = joint.groupby("cycle")

        normed = {}
        for k, g in grouped:
            g = g.loc[:, "ssn"]
            normed[k] = norm_fcn(g)
        normed = pd.concat(normed.values(), axis=0).sort_index()
        return normed

    def normalize_ssn(self, norm_by="max"):
        r"""
        Normalize SSN within each solar cycle.

        If data has been interpolated, interpolate NSSN to interpolated datetime.

        Parameters
        ----------
        norm_by: str
            max, zscore, feature-scale
        """
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

    def cut_spec_by_ssn_band(self, dssn=2.0):
        r"""Cut the sunspot number at each spectrum in intervals of 10 with a width +/- dssn.
        """

        #         raise NotImplementedError(
        #             r"""Do you want this to apply to `SIDC` data or something
        #         you've interpolated?"""
        #         )

        # TODO: need to update this for a normalized SSN option.
        dssn = float(dssn)
        #         mids = np.linspace(30, 180, 16)
        mids = np.arange(
            0,
            self.data.ssn.max(),  # TODO: change to account for normalized ssn
            2.0 * dssn,
        )

        #         mids = np.linspace(0, 180, 37)
        left = mids - dssn
        right = mids + dssn
        intervals = [pd.Interval(l, r) for l, r in zip(left, right)]
        intervals = pd.IntervalIndex(intervals, name="ssn_intervals")
        try:
            cut = pd.cut(
                self.interpolated.loc[:, "ssn"],  # TODO: Fix this generalized hack
                intervals,
            )
        except KeyError as e:
            if np.isnan(e.args[0]):
                # Check that intervals don't overlap.
                for l, r in zip(intervals[:-1], intervals[1:]):
                    l_upper = l.right
                    r_lower = r.left
                    if l_upper > r_lower:
                        msg = "Your intervals can't overlap.\nInterval 0: %s\nInterval 1: %s\nIt causes a KeyError in `pd.cut`."
                        raise ValueError(msg % (l, r))
            else:
                raise

        cut.name = "ssn_band"
        self._spec_by_ssn_band = cut
        self._ssn_band_intervals = intervals
        return cut


#     ####################################################
#     # Calculate dt bands about ssn defined by ssn_band #
#     ####################################################
#     @property
#     def ssn_dt_bands(self):
#         r"""
#         The (left, right) values for each dt about a given ssn.
#         """
#         try:
#             return self._ssn_dt_bands
#         except AttributeError:
#             self.logger.debug("Calculating `cut_jd_by_ssn_dt_band` with defaults")
#             self.cut_jd_by_ssn_dt_band()
#             return self._ssn_dt_bands

#     @property
#     def ssn_dt_band_intervals(self):
#         r"""
#         The intervals corresponding to `ssn_dt_bands`.

#         These are primarily useful for finding mappers between `ssn_dt_bands`
#         and the corresponding `cycle_edge`.
#         """
#         try:
#             return self._ssn_dt_band_intervals
#         except AttributeError:
#             self.logger.debug("Calculating `cut_jd_by_ssn_dt_band` with defaults")
#             self.cut_jd_by_ssn_dt_band()
#             return self._ssn_dt_band_intervals

#     @property
#     def spec_by_ssn_dt_band(self):
#         r"""
#         For each (ssn_band, cycle_edge) pair, find the timestamp closest to
#         the middle of the band and report the timestamp +/- dt for that value.

#         Note
#         ----
#         In contrast to other `spec_by_<X>` properties, this returns categoricals
#         identified by a (cycle_edge, ssn_band) point. Care must be taken to ensure
#         gropby operations are properly performed with them.
#         """
#         try:
#             return self._spec_by_ssn_dt_band
#         except AttributeError:
#             self.logger.info("Calculating `cut_jd_by_ssn_dt_band` with defaults")
#             return self.cut_jd_by_ssn_dt_band()


# class SSNExtrema(Base):
#     def __init__(self):
#         self._init_logger()
#         self.load_data()
#         self.calculate_intervals()

#     @property
#     def data(self):
#         return self._data

#     @property
#     def cycle_intervals(self):
#         r"""`pd.Interval`s corresponding to each Rising and Fall edge along with each
#         full SSN cycle.
#         """
#         return self._cycle_intervals

#     @property
#     def extrema_bands(self):
#         r"""Bands of time ($\Delta t$) about SSN extrema, where dt is specified when
#         calling :py:meth:`calculate_intervals`.
#         """
#         return self._extrema_bands

#     def load_data(self):
#         path = Path(__file__).parent / "ssn_extrema.csv"
#         data = pd.read_csv(path, header=0, skiprows=15, index_col=0)
#         data = pd.to_datetime(data.stack(), format="%Y-%m-%d").unstack(level=1)
#         data.columns.names = ["kind"]
#         self._data = data

#     #######################################################################
#     # Tools for grouping data by Cycle and Cycle Edge (Rising or Falling) #
#     #######################################################################
#     def calculate_intervals(self):
#         r"""The rising edge comes before the falling edge in time, i.e. it's Max N, Min N.
#         Also calculate intervals for a full SSN cycle.
#         """
#         extrema = self.data
#         intervals = pd.DataFrame(
#             index=extrema.index, columns=pd.Index(["Rise", "Fall", "All"], name="kind")
#         )

#         # Make `today` only keep the date.
#         today = pd.to_datetime(pd.to_datetime("today").date())
#         for c, r in extrema.iterrows():
#             t0 = r.loc["Min"]
#             t1 = r.loc["Max"]
#             try:
#                 t2 = extrema.loc[c + 1, "Min"]
#             except KeyError:
#                 t2 = today

#             rise_ = pd.Interval(t0, t1)
#             fall_ = pd.Interval(t1, t2)
#             all_ = pd.Interval(t0, t2)

#             intervals.loc[c] = pd.Series({"Rise": rise_, "Fall": fall_, "All": all_})

#         self._cycle_intervals = intervals.sort_index(axis=1)

#     def cut_spec_by_interval(self, epoch, kind=None):
#         r"""`pd.cut` the Datetime variable `epoch` into rising and falling edges and
#         cycle numbers.

#         If `kind` is not None, it should be some subset of "All", "Rise", or "Fall". If
#         `kind` is "Edges", use ["Rise", "Fall"].
#         """
#         if isinstance(epoch, pd.DatetimeIndex):
#             epoch = epoch.to_series()

#         intervals = self.cycle_intervals

#         available_kind = intervals.columns.get_level_values("kind")
#         if kind is None:
#             kind = available_kind
#         elif isinstance(kind, str):
#             if kind == "Edges":
#                 intervals = intervals.loc[:, ["Fall", "Rise"]]
#             #                 kind = ["Rise", "Fall"]
#             else:
#                 intervals = intervals.loc[:, [kind]]
#         #                 kind = [kind]
#         elif hasattr(kind, "__iter__"):
#             if not np.all([k in available_kind for k in kind]):
#                 raise ValueError(f"""Interval `{kind!s}` is unavailable""")
#             intervals = intervals.loc[:, kind]
#         else:
#             raise ValueError(f"""Interval `{kind!s}` is unavailable""")

#         #         kind = np.unique(kind)

#         ii = pd.IntervalIndex(intervals.stack().sort_values())
#         if not (ii.is_unique and ii.is_monotonic_increasing):
#             raise ValueError

#         cut = pd.cut(epoch, ii)
#         cut.name = "Cycle_Interval"

#         return cut

#     ############################################################
#     # Tools for selecting data within some dt of cycle extrema #
#     ############################################################
#     def calculate_extrema_bands(self, dt="365d"):
#         r"""Calculate `pd.IntervalIndex` that is at extrema +/- dt.
#         """
#         dt = pd.to_timedelta(dt)
#         extrema = self.data.stack()

#         left = extrema.subtract(dt)
#         right = extrema.add(dt)
#         lr = pd.DataFrame({"left": left, "right": right})

#         def make_interval(x):
#             return pd.Interval(x.loc["left"], x.loc["right"])

#         bands = lr.apply(make_interval, axis=1).unstack(level="kind")
#         self._extrema_bands = bands

#     def cut_about_extrema_bands(self, epoch):
#         r"""Assign each `epoch` measurement within $\Delta t$ to a SSN extrema, where
#         $\Delta t$ is assigned by :py:meth:`calc_extrema_bands`.
#         """
#         bands = self.extrema_bands

#         # TODO: verify bands shape
#         intervals = pd.IntervalIndex(bands.stack().values).sort_values()
#         cut = pd.cut(epoch, intervals)
#         cut.name = "spec_by_extrema_band"

#         return cut


class SSNExtrema(IndicatorExtrema):
    def load_or_set_data(self, *args, **kwargs):
        if len(args) or len(kwargs):
            raise ValueError(
                f"""{self.__class__.__name__} expects empty args and kwargs."""
            )

        path = Path(__file__).parent / "ssn_extrema.csv"
        data = pd.read_csv(path, header=0, skiprows=15, index_col=0)
        data = pd.to_datetime(data.stack(), format="%Y-%m-%d").unstack(level=1)
        data.columns.names = ["kind"]
        self._data = data
