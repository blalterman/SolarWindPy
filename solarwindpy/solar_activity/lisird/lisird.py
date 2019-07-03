#!/usr/bin/env python
"""-Tools for interfacing with the LASP Interactive Solar Irradiance Data Center (LISIRD).
<http://lasp.colorado.edu/lisird/>
"""

import pdb  # noqa: F401
import urllib
import json
import numpy as np
import pandas as pd

from pathlib import Path

# from scipy.interpolate import InterpolatedUnivariateSpline

from ..base import (
    ID,
    DataLoader,
    ActivityIndicator,
    IndicatorExtrema,
)  # , _Loader_Dtypes_Columns
from .extrema_calculator import ExtremaCalculator

pd.set_option("mode.chained_assignment", "raise")

# _m13_dtypes_columns = _Loader_Dtypes_Columns(
# {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
# ("year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive")
# )
#
# _m_dtypes_columns = _Loader_Dtypes_Columns(
# {0: int, 1: int, 2: float, 3: float, 4: float, 5: int, 6: bool},
# ["year", "month", "year_fraction", "ssn", "std", "n_obs", "definitive"]
# )
#
# _d_dtypes_columns = _Loader_Dtypes_Columns(
# {0: int, 1: int, 2: int, 3: float, 4: float, 5: float, 6: int, 7: bool},
# ["year", "month", "day", "year_fraction", "ssn", "std", "n_obs", "definitive"
# )


class LISIRD_ID(ID):
    def __init__(self, key):
        r"""
        ======== ======================== =======================
          Key          Description                  URL
        ======== ======================== =======================
         Lalpha   Lyman-alpha              composite_lyman_alpha.jsond
         CaK      Calcium K line           cak.jsond
         f107     F10.7 flux               noaa_radio_flux.jsond
         MgII     Composite Magnesium II   composite_mg_index.jsond
        ======== ======================== =======================

        URLs replace the wild card in <http://lasp.colorado.edu/lisird/latis/*>.

        Note that the CaK line should probably be served directly from
        <https://www.nso.edu/uncategorized/ca-ii-k-line-monitoring-program/>.
        The quantities in CaK data are

            ======== ====================================================
             k3       Core Intensity
             k2vk3    Relative blue K2 peak w/rt K3 instensity
             delk1    Separation of the blue and red K1 minima (K1V-K1R)
             delk2    Separation of the two emission maxima (K2V-K2R)
             delwb    Wilson-Bappu parameter, width between the outer
                      edges of the K2 emission peaks
             emdx     Emission index equivalent width in 1 angstrom
                      band centered on K3
             viored   ???
            ======== ====================================================

        (<https://www.nso.edu/wp-content/uploads/2018/09/cak_paper.pdf>).
        """
        super(LISIRD_ID, self).__init__(key)

    @property
    def _url_base(self):
        return r"http://lasp.colorado.edu/lisird/latis/"

    @property
    def _trans_url(self):
        trans_url = (
            ("Lalpha", "composite_lyman_alpha.jsond"),
            ("CaK", "cak.jsond"),
            ("f107", "noaa_radio_flux.jsond"),
            ("MgII", "composite_mg_index.jsond"),
        )

        return dict(trans_url)


class LISIRDLoader(DataLoader):
    @property
    def data_path(self):
        return super(LISIRDLoader, self).data_path / "lisird" / self.key

    @property
    def meta(self):
        return self._meta

    def convert_nans(self, data, meta):
        key = self.key
        if key in ("CaK", "MgII"):
            self.logger.info("Prior inspection shows no missing data in `%s`.", key)
            return

        elif key == "Lalpha":
            mv = np.float64(meta["type"]["missing_value"])
        elif key == "f107":
            mv = np.float64(meta["f107"]["missing_value"])
        else:
            raise NotImplementedError("Haven't inspected other data to convert.")

        data.replace(to_replace=mv, value=np.nan, inplace=True)

    def download_data(self, new_data_path, old_data_path):
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
        super(LISIRDLoader, self).load_data()
        #        self.logger.info("Loading %s LISIRD data", self.key)
        #
        #        self.maybe_update_stale_data()
        #
        today = pd.to_datetime("today").strftime("%Y%m%d")
        data_path = self.data_path / today

        #        data = pd.read_csv(data_path.with_suffix(".csv"))
        #        self._data = data
        with open(data_path.with_suffix(".json")) as f:
            meta = json.load(f)

        self._meta = meta
        self.logger.info("Load complete")


class LISIRD(ActivityIndicator):
    r"""
    Solar activity data from the LASP Interactive Solar IRadiance Datacenter
    (LISIRD), accessed with LaTiS tools.

    Data taken from <http://lasp.colorado.edu/lisird/about/latis>.

    Descriptions are available at by following links at the LaTiS website
    described in :py:class:`LISIRDID`.
    """

    def __init__(self, key):
        r"""
        Parameters
        ----------
        key: str
            See :py:property:`LISIRD.key`.
        """
        self._init_logger()
        self.set_id(LISIRD_ID(key))
        self.load_data()

    @property
    def meta(self):
        return self.loader.meta

    def load_data(self):
        loader = LISIRDLoader(self.id.key, self.id.url)
        loader.load_data()
        self._loader = loader

    def interpolate_data(self, target_index):
        trans = {
            "Lalpha": "LymanAlpha",
            "MgII": "mg_index",
            "CaK": "emdx",  # Other CaK data is available, but unsure how to use.
            "f107": "f107",
        }

        source = self.data.loc[:, trans[self.id.key]].dropna(how="any", axis=0)
        interpolated = super(LISIRD, self).interpolate_data(source, target_index)
        self._interpolated = interpolated
        return interpolated


class LISIRDExtrema(IndicatorExtrema):
    @property
    def extrema_calculator(self):
        r""":py:class:`ExtremaCalculator` used to calculate the extrema.
        """
        return self._extrema_calculator

    def load_or_set_data(self, *args, **kwargs):
        r"""Get extrema from :py:class:`ExtremaCalculator`.
        """
        ec = ExtremaCalculator(*args, **kwargs)
        extrema = ec.formatted_extrema
        self._data = extrema
        self._extrema_calculator = ec
