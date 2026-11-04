# Spent-When: PERMANENT(ICMECAT stops probing for catalog versions after the pinned one)
# Supersedes: none
"""ICMECAT's bounded probe for catalog versions after the pinned v23.

HELIO4CAST hosts one ICMECAT version at a time. When the pinned v23 answers
HTTP 404, ICMECAT tries v24 through v28 and loads the first that exists,
warning that the package expects v23; a network failure, or any status other
than 404, never starts or continues that climb.

The network is the boundary. ``cache._download_file``, the single point where
SolarWindPy downloads, is replaced by ``FakeHost``: a map from URL to what the
host serves, either catalog text, an HTTP status, or a timeout. A served file
enters astropy's real cache through ``import_file_to_cache``, exactly as a
download would leave it, and every URL the fake is asked for is recorded, so a
test can assert which versions were probed.
"""

import email.message
import io
import os
import time
import urllib.error
import warnings

from pathlib import Path

import pandas as pd
import pytest

from astropy.utils.data import import_file_to_cache

from solarwindpy.solar_activity import cache
from solarwindpy.solar_activity.icme import icmecat
from solarwindpy.solar_activity.icme.icmecat import ICMECAT, ICMECATDownloadError

from .conftest import CATALOG

BASE = "https://helioforecast.space/static/sync/icmecat/HELIO4CAST_ICMECAT_v{}.csv"
V23 = BASE.format(23)

TIMEOUT = "timeout"

PROBE_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="ICMECAT has no version probe, version attribute or ICMECAT "
    "warning classes; remove this marker when the probe lands",
)


def catalog_text(frame=CATALOG):
    """``frame`` as the CSV text the host serves."""
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue()


class UnexpectedURL(AssertionError):
    """Raised when ICMECAT asks the fake host for a URL the test did not plan."""


class FakeHost:
    """Stand-in for HELIO4CAST: ``served`` maps each URL to text, a status or TIMEOUT."""

    def __init__(self, tmp_path, served):
        self.served = served
        self.requested = []
        self.sources = tmp_path / "host"
        self.sources.mkdir()

    def __call__(self, url, cache):
        self.requested.append(url)
        if url not in self.served:
            raise UnexpectedURL(f"ICMECAT requested {url}")
        outcome = self.served[url]
        if outcome == TIMEOUT:
            raise TimeoutError(f"timed out reaching {url}")
        if isinstance(outcome, int):
            raise urllib.error.HTTPError(
                url, outcome, "status", email.message.Message(), None
            )
        source = self.sources / f"{len(self.requested)}.csv"
        source.write_text(outcome)
        return import_file_to_cache(url, str(source), pkgname="solarwindpy")


@pytest.fixture
def host(tmp_path, monkeypatch):
    """Return ``serve(served)``: point ICMECAT at v23 on a ``FakeHost`` serving ``served``."""

    def _serve(served):
        fake = FakeHost(tmp_path, served)
        monkeypatch.setattr(icmecat, "ICMECAT_URL", V23)
        monkeypatch.setattr(cache, "_download_file", fake)
        return fake

    return _serve


def seed_v23(tmp_path, frame=CATALOG, age_days=40):
    """Cache ``frame`` as v23's download, ``age_days`` old (stale against 30 days)."""
    source = tmp_path / "seed.csv"
    source.write_text(catalog_text(frame))
    path = Path(import_file_to_cache(V23, str(source), pkgname="solarwindpy"))
    then = time.time() - age_days * 86400
    os.utime(path, (then, then))


def all_404(*versions):
    return {BASE.format(v): 404 for v in versions}


@PROBE_XFAIL
def test_the_pinned_version_is_loaded_and_recorded(host):
    """With v23 hosted, it is loaded without probing and ``version`` is "v23".

    ON FAILURE: the code is wrong.
    """
    fake = host({V23: catalog_text()})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        cat = ICMECAT()
    assert cat.version == "v23"
    assert fake.requested == [V23]
    assert len(cat) == len(CATALOG)


@PROBE_XFAIL
def test_a_404_climbs_to_the_first_hosted_version_and_warns(host):
    """v23 404s, v24 404s, v25 is hosted: v25 is loaded, with a warning naming both.

    Chosen input: v25 serves only the last catalog row, so the loaded data
    show which version was read.

    ON FAILURE: the code is wrong.
    """
    fake = host({**all_404(23, 24), BASE.format(25): catalog_text(CATALOG.iloc[[5]])})
    with pytest.warns(icmecat.ICMECATVersionWarning, match=r"v25.*v23") as record:
        cat = ICMECAT()
    assert "update" in str(record[0].message)
    assert cat.version == "v25"
    assert cat.data["icmecat_id"].tolist() == ["S1"]
    assert fake.requested == [V23, BASE.format(24), BASE.format(25)]


@PROBE_XFAIL
def test_no_hosted_version_warns_and_raises_without_a_cache(host):
    """v23 through v28 all 404 and nothing is cached: warn, then raise.

    The probe stops at v28, five versions past the pin.

    ON FAILURE: the code is wrong.
    """
    fake = host(all_404(23, 24, 25, 26, 27, 28))
    with pytest.warns(
        icmecat.ICMECATNotHostedWarning,
        match=r"v23 to v28.*helioforecast\.space/icmecat",
    ):
        with pytest.raises(ICMECATDownloadError):
            ICMECAT()
    assert fake.requested == [BASE.format(v) for v in range(23, 29)]


@PROBE_XFAIL
def test_no_hosted_version_falls_back_to_the_cached_pin(host, tmp_path):
    """v23 through v28 all 404 with v23 cached: warn twice and load the cache.

    ON FAILURE: the code is wrong.
    """
    seed_v23(tmp_path)
    host(all_404(23, 24, 25, 26, 27, 28))
    with pytest.warns(icmecat.ICMECATNotHostedWarning):
        with pytest.warns(cache.StaleCacheWarning, match="40.0 days old"):
            cat = ICMECAT()
    assert cat.version == "v23"
    assert len(cat) == len(CATALOG)


@PROBE_XFAIL
@pytest.mark.parametrize("failure", [TIMEOUT, 500, 503], ids=str)
def test_a_failure_that_is_not_a_404_never_climbs(host, tmp_path, failure):
    """A timeout or 5xx on v23 uses the cached v23 and probes nothing else.

    ON FAILURE: the code is wrong.
    """
    seed_v23(tmp_path)
    fake = host({V23: failure})
    with pytest.warns(cache.StaleCacheWarning, match="40.0 days old"):
        cat = ICMECAT()
    assert fake.requested == [V23]
    assert cat.version == "v23"


def test_a_failure_that_is_not_a_404_raises_without_a_cache(host):
    """A timeout on v23 with nothing cached raises, without probing.

    ON FAILURE: the code is wrong.
    """
    fake = host({V23: TIMEOUT})
    with pytest.raises(ICMECATDownloadError):
        ICMECAT()
    assert fake.requested == [V23]


@PROBE_XFAIL
def test_a_failure_during_the_climb_stops_it(host, tmp_path):
    """v23 404s and v24 times out: the climb stops and the cached v23 is used.

    v25 is hosted, so skipping past the inconclusive v24 would load it.

    ON FAILURE: the code is wrong.
    """
    seed_v23(tmp_path)
    fake = host({V23: 404, BASE.format(24): TIMEOUT, BASE.format(25): catalog_text()})
    with pytest.warns(cache.StaleCacheWarning):
        cat = ICMECAT()
    assert fake.requested == [V23, BASE.format(24)]
    assert cat.version == "v23"


@PROBE_XFAIL
def test_an_unknown_spacecraft_warns_instead_of_failing(host):
    """A catalog naming a spacecraft outside SPACECRAFT_NAMES loads, with a warning.

    Chosen input: a newer catalog adds one row from "NewProbe".

    ON FAILURE: the code is wrong.
    """
    extra = pd.concat(
        [CATALOG, CATALOG.iloc[[0]].assign(icmecat_id="N1", sc_insitu="NewProbe")],
        ignore_index=True,
    )
    host({V23: catalog_text(extra)})
    with pytest.warns(icmecat.ICMECATSpacecraftWarning, match="NewProbe"):
        cat = ICMECAT()
    assert cat.data["icmecat_id"].tolist()[-1] == "N1"
    assert len(cat.filter("NewProbe")) == 1


@PROBE_XFAIL
def test_filter_keeps_the_loaded_version(host):
    """A filtered catalog reports the version its parent loaded.

    ON FAILURE: the code is wrong.
    """
    host({**all_404(23), BASE.format(24): catalog_text()})
    with pytest.warns(icmecat.ICMECATVersionWarning):
        cat = ICMECAT()
    assert cat.filter("Wind").version == "v24"


def test_a_missing_local_catalog_still_raises_without_probing(tmp_path, monkeypatch):
    """A local path names no version, so a missing one raises as before.

    ON FAILURE: the code is wrong.
    """
    fake = FakeHost(tmp_path, {})
    monkeypatch.setattr(cache, "_download_file", fake)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ICMECATDownloadError):
            ICMECAT()
    assert fake.requested == []
