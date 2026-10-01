#!/usr/bin/env python
"""Interfaces for the LASP Interactive Solar Irradiance Data Center (LISIRD).

The submodule provides classes for downloading and working with data hosted at
`LASP <http://lasp.colorado.edu/lisird/>`_.
"""

__all__ = [
    "LISIRD_ID",
    "LISIRDLoader",
    "LISIRD",
    "LISIRDExtrema",
]

import urllib.request
import json
import numpy as np
import pandas as pd

from pathlib import Path

from ..base import (
    ID,
    DataLoader,
    ActivityIndicator,
    IndicatorExtrema,
)
from .extrema_calculator import ExtremaCalculator

pd.set_option("mode.chained_assignment", "raise")


class LISIRD_ID(ID):
    r"""Identifier mapping a LISIRD data set name to its download URL."""

    def __init__(self, key):
        r"""Identifier for LISIRD data products.

        Parameters
        ----------
        key : str
            Short name of the data set. Examples include ``"Lalpha"`` or
            ``"f107-noaa"``.

            ================ ======================== ===========================
             Key              Description              URL
            ================ ======================== ===========================
             Lalpha           Lyman-alpha              composite_lyman_alpha.jsond
             CaK              Calcium K line           cak.jsond
             f107-noaa        NOAA F10.7 flux          noaa_radio_flux.jsond
             f107-penticton   Penticton F10.7 flux     penticton_radio_flux.jsond
             MgII             Composite Magnesium II   composite_mg_index.jsond
            ================ ======================== ===========================

        URLs replace the wild card in
        ``http://lasp.colorado.edu/lisird/latis/dap/*``.

        Note that the CaK line should probably be served directly from
        ``https://www.nso.edu/uncategorized/ca-ii-k-line-monitoring-program/``.
        The quantities in CaK data are

            ======== ====================================================
             k3       Core Intensity
             k2vk3    Relative blue K2 peak w/rt K3 instensity
             delk1    Separation of the blue and red K1 minima (K1V-K1R)
             delk2    Separation of the two emission maxima (K2V-K2R)
             delwb    Wilson-Bappu parameter, width between the outer
                      edges of the K2 emission peaks
             emdx     Emission index equivalent width in 1 angstrom
                      band centered on K3
             viored   ???
            ======== ====================================================

        (<https://www.nso.edu/wp-content/uploads/2018/09/cak_paper.pdf>).
        """
        super(LISIRD_ID, self).__init__(key)

    @property
    def _url_base(self):
        r"""Base URL of the LISIRD LaTiS data service."""
        return r"http://lasp.colorado.edu/lisird/latis/dap/"

    @property
    def _trans_url(self):
        r"""Map from data set key to file name under :attr:`_url_base`."""
        trans_url = (
            ("Lalpha", "composite_lyman_alpha.jsond"),
            ("CaK", "cak.jsond"),
            ("f107-penticton", "penticton_radio_flux.jsond"),
            ("f107-noaa", "noaa_radio_flux.jsond"),
            (
                "MgII",
                "composite_mg_index.jsond",
            ),  # CHECK: Change to "bremen_composite_mgii.jsond" ?
        )

        return dict(trans_url)


class LISIRDLoader(DataLoader):
    r"""Download, cache, and load one LISIRD data set."""

    @property
    def data_path(self):
        r"""Cache directory for this data set, ``<DataLoader.data_path>/lisird/<key>``."""
        return super(LISIRDLoader, self).data_path / "lisird" / self.key

    @property
    def meta(self):
        r"""Metadata that LISIRD serves with the data set, as a dict."""
        return self._meta

    def convert_nans(self, data, meta):
        r"""Replace the data set's missing-value sentinel with NaN, in place.

        Parameters
        ----------
        data : pandas.DataFrame
            Downloaded data.
        meta : dict
            LISIRD metadata holding each parameter's ``missing_value``.

        Raises
        ------
        NotImplementedError
            For a key whose missing values have not been inspected, or for
            ``"Lalpha"`` when irradiance and uncertainty use different
            sentinels.
        """
        key = self.key
        if key in ("CaK", "MgII", "f107-noaa", "f107-penticton"):
            self.logger.info("Prior inspection shows no missing data in `%s`.", key)
            return

        elif key == "Lalpha":
            mv0 = np.float64(meta["irradiance"]["missing_value"])
            mv1 = np.float64(meta["uncertainty"]["missing_value"])
            if not mv0 == mv1:
                raise NotImplementedError(
                    f"Unsure how to handle mv0 ({mv0:.0f}) != mv1 ({mv1:.0f})"
                )
            mv = mv0
        else:
            raise NotImplementedError("Haven't inspected other data to convert.")

        data.replace(to_replace=mv, value=np.nan, inplace=True)

    def verify_monotonic_epoch(self, df):
        r"""Drop rows with a duplicated timestamp.

        For ``"f107-penticton"``, three timestamps identified by inspection as
        bad are dropped too.

        Parameters
        ----------
        df : pandas.DataFrame
            Data with a :class:`pandas.DatetimeIndex` and a ``milliseconds``
            column.

        Returns
        -------
        pandas.DataFrame
        """
        epoch = df.index
        assert isinstance(epoch, pd.DatetimeIndex)
        epoch = epoch.to_series()

        ms = df.loc[:, "milliseconds"]
        drop = ms.duplicated()

        if self.key == "f107-penticton":
            manually_identified_bad_timestamps = [
                1_061_657_971_200,
                1_277_073_820_800,
                1_568_685_597_120,
            ]
            manual_bad = ms.isin(manually_identified_bad_timestamps)
            drop = drop | manual_bad

        df = df.loc[~drop]
        return df

    def download_data(self, new_data_path, old_data_path):
        r"""Download the data set and write it to ``new_data_path``.

        The data are written as ``.csv`` and the metadata as ``.json``. Files
        at ``old_data_path`` with those suffixes are removed.

        Parameters
        ----------
        new_data_path, old_data_path : pathlib.Path
            Paths without suffix.
        """
        key = self.key
        url = self.url
        self.logger.info("Downloading solar activity data: %s\nurl: %s" % (key, url))

        with urllib.request.urlopen(url) as url_:
            data = json.loads(url_.read().decode())[Path(self.url).stem]

        meta = data["metadata"]
        df = pd.DataFrame(data["data"], columns=data["parameters"])

        t0 = pd.to_datetime("1970-01-01 00:00:00")
        ms = df.pop("time")  # Time in milliseconds since 1970-01-01.
        dt = pd.to_timedelta(ms, unit="ms")
        t = dt.add(t0)
        df.loc[:, "milliseconds"] = ms
        df.index = t
        df = df.sort_index(axis=1)

        self.convert_nans(df, meta)
        df = self.verify_monotonic_epoch(df)

        d = new_data_path.with_suffix(".csv")
        m = new_data_path.with_suffix(".json")

        df.to_csv(d, sep=",", na_rep="NaN")
        with open(m, "w") as f:
            json.dump(meta, f, indent=4)

        d_old = old_data_path.with_suffix(".csv")
        m_old = old_data_path.with_suffix(".json")
        try:
            d_old.unlink()
        except FileNotFoundError:
            pass
        try:
            m_old.unlink()
        except FileNotFoundError:
            pass

    def load_data(self):
        r"""Load today's cached data and metadata, downloading if stale."""
        super(LISIRDLoader, self).load_data()
        today = pd.to_datetime("today").strftime("%Y%m%d")
        data_path = self.data_path / today

        with open(data_path.with_suffix(".json")) as f:
            meta = json.load(f)

        self._meta = meta
        self.logger.info("Load complete")


class LISIRD(ActivityIndicator):
    r"""Wrapper around LISIRD data sets."""

    def __init__(self, key):
        r"""Instantiate a LISIRD data object.

        Parameters
        ----------
        key : str
            Identifier passed to :class:`LISIRD_ID`.
        """
        self._init_logger()
        self.set_id(LISIRD_ID(key))
        self.load_data()
        self.set_extrema()

    def set_extrema(self):
        r"""Do nothing: extrema are not set for LISIRD data sets.

        Use :class:`LISIRDExtrema` to calculate them.
        """
        pass

    @property
    def meta(self):
        r"""Metadata that LISIRD serves with the data set, as a dict."""
        return self.loader.meta

    @property
    def normalized(self):
        r"""``None``: normalization is not implemented for LISIRD data sets."""
        pass

    def run_normalization(self, norm_by="feature-scale"):
        r"""Not implemented for LISIRD data sets.

        Raises
        ------
        NotImplementedError
            Always.
        """
        raise NotImplementedError(r"""Need to fix normalization handling for each LISIRD
quantity""")

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

        normalized = {
            k: self._run_normalization(v, norm_fcn) for k, v in self.data.items()
        }
        normalized = pd.concat(normalized, axis=1)

        normed_interpolated = None
        try:
            interpolated = self.interpolated
            normed_interpolated = {
                k: self._run_normalization(v, norm_fcn) for k, v in interpolated.items()
            }
            normed_interpolated = pd.concat(normed_interpolated, axis=1)
        except AttributeError:
            pass

        return normalized, normed_interpolated

    def load_data(self):
        r"""Load the data set through a :class:`LISIRDLoader`."""
        loader = LISIRDLoader(self.id.key, self.id.url)
        loader.load_data()
        self._loader = loader

    def interpolate_data(self, target_index):
        r"""Interpolate the data set's primary quantity onto ``target_index``.

        The quantity is ``irradiance`` for ``"Lalpha"``, ``mg_index`` for
        ``"MgII"``, ``emdx`` for ``"CaK"``, and ``adjusted_flux`` for both F10.7
        data sets.

        Parameters
        ----------
        target_index : pandas.DatetimeIndex
            Times to interpolate onto.

        Returns
        -------
        pandas.DataFrame
            Interpolated values; NaN outside the data's time range.
        """
        trans = {
            "Lalpha": "irradiance",
            "MgII": "mg_index",
            "CaK": "emdx",  # Other CaK data is available, but unsure how to use.
            # Per <https://www.spaceweather.gc.ca/solarflux/sx-3-en.php>, adjusted value is scaled for variation in Earth-Sun distance
            "f107-noaa": "adjusted_flux",
            "f107-penticton": "adjusted_flux",
        }

        source = self.data.loc[:, trans[self.id.key]].dropna(how="any", axis=0)
        interpolated = super(LISIRD, self).interpolate_data(source, target_index)
        self._interpolated = interpolated
        return interpolated


class LISIRDExtrema(IndicatorExtrema):
    r"""Solar-cycle extrema of a LISIRD index, found by :class:`.ExtremaCalculator`.

    Arguments are passed to :class:`.ExtremaCalculator`.
    """

    @property
    def extrema_calculator(self):
        r""":py:class:`.ExtremaCalculator` used to calculate the extrema."""
        return self._extrema_calculator

    def load_or_set_data(self, *args, **kwargs):
        r"""Get extrema from :py:class:`.ExtremaCalculator`."""
        ec = ExtremaCalculator(*args, **kwargs)
        extrema = ec.formatted_extrema
        self._data = extrema
        self._extrema_calculator = ec
