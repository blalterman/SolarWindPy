# Spent-When: PERMANENT(SolarWindPy stops issuing warnings)
# Supersedes: none
"""Every warning SolarWindPy issues names the caller's code, not the package's.

A warning's ``filename`` and ``lineno`` tell the user which of their lines
triggered it, and ``-W error::<category>:<module>`` filters match on that
module. A warning attributed to a frame inside ``solarwindpy`` names a file the
user never wrote. The rule is one shared helper, ``solarwindpy.tools._warn``,
that skips every frame under the package directory; the cases below trigger
warnings from different subpackages at different call depths and check each
lands on this file, and the guard checks no ``warnings.warn`` call bypasses the
helper.

The network and the download cache are the boundary: the cache is pointed at
``tmp_path`` through ``XDG_CACHE_HOME``, and ``cache._download_file``, the one
place SolarWindPy downloads, is replaced where a test needs a host.
"""

import ast
import email.message
import os
import time
import urllib.error
import warnings

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from astropy.utils.data import import_file_to_cache
from scipy.optimize import OptimizeWarning

import solarwindpy
from solarwindpy.fitfunctions.lines import Line
from solarwindpy.solar_activity import cache
from solarwindpy.solar_activity.base import DataLoader
from solarwindpy.solar_activity.icme import icmecat

PACKAGE_DIR = Path(solarwindpy.__file__).resolve().parent
# The helper's module and name; only the call inside its body may be direct.
HELPER = (PACKAGE_DIR / "tools" / "__init__.py", "_warn")

BASE = "https://helioforecast.space/static/sync/icmecat/HELIO4CAST_ICMECAT_v{}.csv"
V23 = BASE.format(23)

# One event per spacecraft, in the columns ICMECAT reads.
CATALOG_CSV = (
    "icmecat_id,sc_insitu,icme_start_time,mo_start_time,mo_end_time\n"
    "W1,Wind,2000-04-01,2000-04-01 12:00,2000-04-02\n"
)


class WarnedFromInsidePackage(AssertionError):
    """The warning names a file other than the code that triggered it."""


class WarnBypassesHelper(AssertionError):
    """A package module calls ``warnings.warn`` instead of the shared helper."""


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the download cache at an empty directory under ``tmp_path``.

    astropy honours ``XDG_CACHE_HOME`` only when it exists, and releases
    before 8 only when ``<XDG_CACHE_HOME>/solarwindpy`` exists too.
    """
    root = tmp_path / "xdg-cache"
    (root / "solarwindpy").mkdir(parents=True)
    monkeypatch.setenv("XDG_CACHE_HOME", str(root))
    return root


def seed(url, text, tmp_path, age_days):
    """Cache ``text`` as ``url``'s download, ``age_days`` old."""
    source = tmp_path / f"seed-{abs(hash(url))}.csv"
    source.write_text(text)
    path = Path(import_file_to_cache(url, str(source), pkgname="solarwindpy"))
    then = time.time() - age_days * 86400.0
    os.utime(path, (then, then))


def host(monkeypatch, tmp_path, served):
    """Replace the download with a host serving ``served``: URL to text, status or OSError."""

    def download(url, cache):
        outcome = served[url]
        if isinstance(outcome, int):
            raise urllib.error.HTTPError(
                url, outcome, "status", email.message.Message(), None
            )
        if isinstance(outcome, BaseException):
            raise outcome
        source = tmp_path / f"served-{abs(hash(url))}.csv"
        source.write_text(outcome)
        return import_file_to_cache(url, str(source), pkgname="solarwindpy")

    monkeypatch.setattr(cache, "_download_file", download)


class DailyLoader(DataLoader):
    """A loader of the CSV its URL serves, fresh for one day."""

    @property
    def max_age(self):
        return pd.Timedelta(days=1)

    @staticmethod
    def convert_nans(data):
        return data

    def read_data(self, path):
        return pd.read_csv(path, index_col=0)

    def load_data(self):
        super().load_data()


def stale_cache_from_the_base_loader(tmp_path, monkeypatch):
    """A loader whose refresh fails loads its 3-day-old copy: StaleCacheWarning."""
    url = "https://example.invalid/daily.csv"
    seed(url, "t,value\n2021-03-01,7.0\n", tmp_path, age_days=3)
    host(monkeypatch, tmp_path, {url: TimeoutError("unreachable")})
    DailyLoader("daily", url).load_data()
    return cache.StaleCacheWarning


def stale_cache_from_icmecat(tmp_path, monkeypatch):
    """ICMECAT whose refresh times out loads its 40-day-old v23: StaleCacheWarning."""
    seed(V23, CATALOG_CSV, tmp_path, age_days=40)
    monkeypatch.setattr(icmecat, "ICMECAT_URL", V23)
    host(monkeypatch, tmp_path, {V23: TimeoutError("unreachable")})
    icmecat.ICMECAT()
    return cache.StaleCacheWarning


def icmecat_version_from_a_404(tmp_path, monkeypatch):
    """v23 answers 404 and v24 is hosted: ICMECATVersionWarning."""
    monkeypatch.setattr(icmecat, "ICMECAT_URL", V23)
    host(monkeypatch, tmp_path, {V23: 404, BASE.format(24): CATALOG_CSV})
    icmecat.ICMECAT()
    return icmecat.ICMECATVersionWarning


def icmecat_unknown_spacecraft(tmp_path, monkeypatch):
    """A local catalog naming a spacecraft outside SPACECRAFT_NAMES: ICMECATSpacecraftWarning."""
    path = tmp_path / "icmecat.csv"
    path.write_text(CATALOG_CSV.replace("Wind", "Voyager"))
    monkeypatch.setattr(icmecat, "ICMECAT_URL", str(path))
    icmecat.ICMECAT()
    return icmecat.ICMECATSpacecraftWarning


def covariance_from_a_fit_with_no_degree_of_freedom(tmp_path, monkeypatch):
    """Two samples for a two-parameter line: OptimizeWarning from make_fit."""
    x = np.array([0.0, 1.0])
    Line(x, 2.0 * x + 1.0).make_fit()
    return OptimizeWarning


def plain_string_label_on_a_plot(tmp_path, monkeypatch):
    """A Hist2D labelled with a plain str: PlainStringLabelWarning, one call deep."""
    from solarwindpy.plotting.hist2d import Hist2D
    from solarwindpy.plotting.labels import base as labels_base

    x = pd.Series([0.5, 1.5, 1.5], name="x")
    Hist2D(x, x.rename("y"), nbins=[[0.0, 1.0, 2.0]] * 2).set_labels(x="Speed")
    return labels_base.PlainStringLabelWarning


def plain_string_label_through_a_trend_fit(tmp_path, monkeypatch):
    """Plain str labels shared through a TrendFit, two calls deep."""
    from solarwindpy.fitfunctions.gaussians import Gaussian
    from solarwindpy.fitfunctions.trend_fits import TrendFit
    from solarwindpy.plotting.labels import base as labels_base

    xbins = pd.interval_range(0, 10, periods=10)
    x = xbins.mid.values
    columns = pd.interval_range(0, 3, periods=3)
    agged = pd.DataFrame(
        {
            c: 10.0 * np.exp(-0.5 * ((x - mu) / 1.2) ** 2)
            for c, mu in zip(columns, [4.0, 5.0, 6.5])
        },
        index=xbins,
    )
    tf = TrendFit(agged, Gaussian, Line, y=("mu", "value"), yerr=("sigma", "value"))
    tf.make_fit()
    tf.set_shared_labels(x="time", y="density", z="counts")
    return labels_base.PlainStringLabelWarning


@pytest.mark.parametrize(
    "trigger",
    [
        pytest.param(stale_cache_from_the_base_loader, id="base-loader-stale-cache"),
        pytest.param(stale_cache_from_icmecat, id="icmecat-stale-cache"),
        pytest.param(icmecat_version_from_a_404, id="icmecat-version"),
        pytest.param(icmecat_unknown_spacecraft, id="icmecat-spacecraft"),
        pytest.param(
            covariance_from_a_fit_with_no_degree_of_freedom,
            id="fitfunction-covariance",
        ),
        pytest.param(
            plain_string_label_on_a_plot,
            id="plot-plain-string-label",
        ),
        pytest.param(
            plain_string_label_through_a_trend_fit,
            id="trend-fit-plain-string-label",
        ),
    ],
)
def test_a_warning_names_the_code_that_triggered_it(trigger, tmp_path, monkeypatch):
    """The warning's ``filename`` is this test file, the first frame outside the package.

    Chosen input: one warning per subpackage and call depth, from a direct
    call (the fit), through an abstract base class (the loader), and from
    ICMECAT's constructor one and two calls above the warning.

    ON FAILURE: the code is wrong.
    """
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        category = trigger(tmp_path, monkeypatch)
    issued = [w for w in record if issubclass(w.category, category)]
    assert issued, f"no {category.__name__} was issued"
    misattributed = [
        w.filename
        for w in issued
        if Path(w.filename).resolve() != Path(__file__).resolve()
    ]
    if misattributed:
        raise WarnedFromInsidePackage(misattributed)


def _calls_to_warnings_warn(tree):
    """Line numbers of ``warnings.warn(...)`` and of a ``warn`` imported from warnings."""
    imported = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "warnings"
        for alias in node.names
        if alias.name == "warn"
    }
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "warn"
            and isinstance(func.value, ast.Name)
            and func.value.id == "warnings"
        ) or (isinstance(func, ast.Name) and func.id in imported):
            lines.append(node.lineno)
    return lines


def test_the_guard_finds_a_direct_call():
    """The scan finds both spellings of a direct call.

    ON FAILURE: fix the guard's scan.
    """
    source = (
        "import warnings\n"
        "from warnings import warn as w\n"
        "warnings.warn('a')\n"
        "w('b')\n"
        "warn('c')\n"
    )
    assert _calls_to_warnings_warn(ast.parse(source)) == [3, 4]


def _helper_lines(tree):
    """The line range of the helper's own body in its module's ``tree``."""
    (helper,) = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == HELPER[1]
    ]
    return range(helper.lineno, helper.end_lineno + 1)


def test_every_package_warning_goes_through_the_shared_helper():
    """No package code but the helper's own body calls ``warnings.warn``.

    ON FAILURE: the code is wrong; issue the warning with
    ``solarwindpy.tools._warn``.
    """
    bypasses = []
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        allowed = _helper_lines(tree) if path == HELPER[0] else range(0)
        bypasses += [
            f"{path.relative_to(PACKAGE_DIR)}, line {line}"
            for line in _calls_to_warnings_warn(tree)
            if line not in allowed
        ]
    if bypasses:
        raise WarnBypassesHelper(bypasses)


def test_the_helper_itself_calls_warnings_warn_once():
    """The helper's body holds the package's one direct call.

    ON FAILURE: the guard's exemption no longer names the helper; fix
    ``HELPER``.
    """
    tree = ast.parse(HELPER[0].read_text(encoding="utf-8"))
    calls = _calls_to_warnings_warn(tree)
    assert len(calls) == 1
    assert calls[0] in _helper_lines(tree)
