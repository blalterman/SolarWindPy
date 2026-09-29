"""The ``solarwindpy.solar_activity`` package entry point.

``get_all_indices`` builds real ``LISIRD`` and ``SIDC`` indicators, which
download from LASP and SILSO. The network is the only thing faked: each
identifier's URL base is pointed at a local directory of small payloads
written in the upstream formats (LISIRD ``.jsond`` JSON, SILSO ``;``-separated
CSV), and the home directory that holds the cache is moved under
``tmp_path``. Download, parsing, caching and assembly all run for real, and
every expected value is read off the payloads below.
"""

import importlib
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest

import solarwindpy.solar_activity as sa
from solarwindpy.solar_activity.lisird.lisird import LISIRD_ID
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID

DAY_MS = 86_400_000
T0_MS = int(pd.Timestamp("2020-01-01").timestamp() * 1000)
LALPHA_MISSING = -99.0

# Upstream payloads. Each LISIRD file is {<file stem>: {metadata, parameters,
# data}} with time in ms since 1970; SILSO m13 columns are year; month;
# decimal year; ssn; std; n_obs; definitive, with -1 for missing.
LISIRD_PAYLOADS = {
    "composite_lyman_alpha.jsond": {
        "metadata": {
            "irradiance": {"missing_value": str(LALPHA_MISSING)},
            "uncertainty": {"missing_value": str(LALPHA_MISSING)},
        },
        "parameters": ["time", "irradiance", "uncertainty"],
        "data": [
            [T0_MS, 6.0e-3, 1.0e-4],
            [T0_MS + DAY_MS, LALPHA_MISSING, LALPHA_MISSING],
            [T0_MS + 2 * DAY_MS, 6.2e-3, 1.0e-4],
        ],
    },
    "cak.jsond": {
        "metadata": {},
        "parameters": ["time", "emdx", "k3"],
        "data": [
            [T0_MS, 0.08, 0.050],
            [T0_MS + DAY_MS, 0.09, 0.051],
            [T0_MS + 2 * DAY_MS, 0.10, 0.052],
        ],
    },
    # Sampled at noon: the package moves MgII onto the date alone.
    "composite_mg_index.jsond": {
        "metadata": {},
        "parameters": ["time", "mg_index"],
        "data": [
            [T0_MS + DAY_MS // 2, 0.15],
            [T0_MS + 3 * DAY_MS // 2, 0.16],
            [T0_MS + 5 * DAY_MS // 2, 0.17],
        ],
    },
}
SILSO_M13 = (
    "2019;12;2019.958;   1.5;   0.2;  700;1\n"
    "2020;01;2020.042;   1.8;   0.3;  800;1\n"
    "2020;02;2020.124;  -1.0;  -1.0;   -1;0\n"
)


def write_remote(remote):
    """Write every upstream payload ``get_all_indices`` fetches into ``remote``."""
    for name, body in LISIRD_PAYLOADS.items():
        stem = name.split(".")[0]
        (remote / name).write_text(json.dumps({stem: body}))
    (remote / "snmstotcsv.php").write_text(SILSO_M13)


@pytest.fixture
def urllib_request_loaded():
    """Load ``urllib.request`` for one test, then restore ``sys.modules``.

    LISIRD downloads need ``urllib.request`` but ``lisird.py`` never imports
    it (recorded by ``test_lisird_download_works_in_a_fresh_interpreter``).
    Loading it here, and unloading it afterwards if it was not loaded
    before, confines that workaround to the tests that request it.
    """
    was_loaded = "urllib.request" in sys.modules
    importlib.import_module("urllib.request")
    yield
    if not was_loaded:
        sys.modules.pop("urllib.request", None)
        if hasattr(urllib, "request"):
            delattr(urllib, "request")


@pytest.fixture
def local_upstream(tmp_path, monkeypatch, urllib_request_loaded):
    """Move the cache home under ``tmp_path`` and serve the payloads locally.

    ``DataLoader`` reads the cache date from an 8-digit run anywhere in the
    cache's absolute path, so a ``tmp_path`` that holds one would be misread.
    """
    if re.search(r"\d{8}", str(tmp_path)):
        pytest.skip(f"tmp_path contains an 8-digit run: {tmp_path}")
    home = tmp_path / "home"
    home.mkdir()
    remote = tmp_path / "remote"
    remote.mkdir()
    write_remote(remote)

    base = remote.as_uri() + "/"
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(LISIRD_ID, "_url_base", property(lambda self: base))
    monkeypatch.setattr(SIDC_ID, "_url_base", property(lambda self: base))
    return tmp_path


@pytest.fixture
def indices(local_upstream):
    return sa.get_all_indices()


def test_each_indicator_lands_on_its_own_dates(indices):
    """Each indicator's values sit at the times its source reported them.

    Read off the payloads: on 2020-01-01 Lyman-alpha is 6.0e-3, CaK emdx is
    0.08, MgII is 0.15 and the smoothed SSN is 1.8; SSN is monthly, so
    2019-12-01 carries SSN 1.5 and nothing else.

    ON FAILURE: the code is wrong.
    """
    day = indices.loc[pd.Timestamp("2020-01-01")]
    # rel=1e-12: values pass through a CSV round trip unchanged.
    assert day[("Lalpha", "irradiance")] == pytest.approx(6.0e-3, rel=1e-12, abs=0)
    assert day[("CaK", "emdx")] == pytest.approx(0.08, rel=1e-12, abs=0)
    assert day[("MgII", "mg_index")] == pytest.approx(0.15, rel=1e-12, abs=0)
    assert day[("ssn", "ssn")] == pytest.approx(1.8, rel=1e-12, abs=0)

    december = indices.loc[pd.Timestamp("2019-12-01")]
    assert december[("ssn", "ssn")] == pytest.approx(1.5, rel=1e-12, abs=0)
    assert december.drop(("ssn", "ssn")).isna().all()


def test_indicators_share_one_index_and_keep_their_gaps(indices):
    """The table is the union of every source's dates, with gaps kept as NaN.

    The union of the payload dates is 2019-12-01, 2020-01-01..03 and
    2020-02-01.

    ON FAILURE: the code is wrong.
    """
    expected = pd.DatetimeIndex(
        ["2019-12-01", "2020-01-01", "2020-01-02", "2020-01-03", "2020-02-01"]
    )
    assert indices.index.equals(expected.as_unit(indices.index.unit))
    assert np.isnan(indices.loc[pd.Timestamp("2020-01-02"), ("ssn", "ssn")])


def test_mgii_sampled_at_noon_is_placed_on_its_date(indices):
    """MgII reported at 12:00 is aligned with the other indices' midnights.

    ON FAILURE: the code is wrong.
    """
    assert (indices.index == indices.index.normalize()).all()
    mgii = indices[("MgII", "mg_index")].dropna()
    # rel=1e-12: values pass through a CSV round trip unchanged.
    assert mgii.to_numpy() == pytest.approx([0.15, 0.16, 0.17], rel=1e-12, abs=0)


def test_missing_value_sentinels_become_nan(indices):
    """Upstream missing-value sentinels are NaN, not numbers.

    From the payloads: Lyman-alpha is -99 on 2020-01-02 (its declared
    missing value) and SILSO reports -1 for February 2020.

    ON FAILURE: the code is wrong.
    """
    assert np.isnan(indices.loc[pd.Timestamp("2020-01-02"), ("Lalpha", "irradiance")])
    assert np.isnan(indices.loc[pd.Timestamp("2020-02-01"), ("ssn", "ssn")])


def test_every_cak_quantity_except_the_raw_timestamp_is_kept(indices):
    """All CaK quantities are reported, but the raw millisecond clock is not.

    ON FAILURE: the code is wrong.
    """
    cak = set(indices["CaK"].columns)
    assert cak == {"emdx", "k3"}


def test_a_failed_download_raises_instead_of_returning_a_partial_table(
    local_upstream,
):
    """If one upstream product cannot be fetched, the call raises.

    Chosen input: the CaK payload is removed. ``OSError`` covers the
    ``URLError`` a missing URL raises.

    ON FAILURE: the code is wrong.
    """
    (local_upstream / "remote" / "cak.jsond").unlink()
    with pytest.raises(OSError):
        sa.get_all_indices()


@pytest.mark.parametrize("name", sa.__all__)
def test_every_exported_name_resolves(name):
    """Every name in ``__all__`` is an attribute of the package.

    ON FAILURE: the code is wrong.
    """
    assert getattr(sa, name) is not None


def test_ssn_is_the_sunspot_number_module():
    """``ssn`` is an alias for ``sunspot_number``, not a copy.

    ON FAILURE: the code is wrong.
    """
    assert sa.ssn is sa.sunspot_number


class UrllibRequestNotImported(AssertionError):
    """Raised only for the missing ``urllib.request`` import below.

    ``pytest.mark.xfail`` narrows by exception type alone, so a dedicated
    subclass keeps the marker from absorbing any other failure.
    """


# Runs in a fresh interpreter: in-process, whether ``urllib.request`` is
# already imported depends on which tests ran first (this module imports it
# at the top so the other tests exercise the download path at all).
FRESH_DOWNLOAD = textwrap.dedent("""
    import sys
    from solarwindpy.solar_activity.lisird.lisird import LISIRD, LISIRD_ID
    LISIRD_ID._url_base = property(lambda self: sys.argv[1])
    print(LISIRD("CaK").data["emdx"].tolist())
    """)


@pytest.mark.xfail(
    strict=True,
    raises=UrllibRequestNotImported,
    reason=(
        "solar_activity/lisird/lisird.py does `import urllib` and then calls "
        "urllib.request.urlopen in LISIRDLoader.download_data; `import "
        "urllib` does not import the `request` submodule, so in a fresh "
        "interpreter every LISIRD download (and so get_all_indices) raises "
        "AttributeError \"module 'urllib' has no attribute 'request'\". "
        "Remove this marker when lisird.py imports urllib.request."
    ),
)
def test_lisird_download_works_in_a_fresh_interpreter(local_upstream):
    """A LISIRD download succeeds in a new Python process.

    Read off the CaK payload: emdx is 0.08, 0.09, 0.10.

    ON FAILURE: (unexpected pass) lisird.py now imports urllib.request; drop
    the xfail marker.
    """
    # Import the same solarwindpy this suite is testing, not whichever copy
    # the environment has installed.
    package_root = Path(sa.__file__).resolve().parents[2]
    home = local_upstream / "home"
    base = (local_upstream / "remote").as_uri() + "/"
    # Inherit the environment (conda activation, library paths), but move the
    # home directory and keep matplotlib's existing config and font cache.
    child_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    child_env.update(
        HOME=str(home), MPLBACKEND="Agg", MPLCONFIGDIR=matplotlib.get_configdir()
    )
    result = subprocess.run(
        [sys.executable, "-c", FRESH_DOWNLOAD, base],
        cwd=package_root,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if "module 'urllib' has no attribute 'request'" in result.stderr:
        raise UrllibRequestNotImported(result.stderr.strip().splitlines()[-1])
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[0.08, 0.09, 0.1]"
