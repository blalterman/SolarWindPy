#!/usr/bin/env python
"""Test SIDC_ID: which SILSO series a key selects, and how its URL is built.

``SIDC_ID`` maps a short series key to a SILSO endpoint. The tests below
assert each URL against the class's own documentation -- the Key/URL table in
``SIDC_ID.__init__`` and the base it names -- and the class's error
behaviour. The documentation is what users read, so a URL that disagrees with
it is wrong either way.

The endpoint names are documented in the class's own docstring table and on
SILSO's data page, <https://www.sidc.be/SILSO/datafiles>.

KNOWN GAP -- the endpoints are not reached
------------------------------------------
Whether ``http://www.sidc.be/silso/INFO/snmtotcsv.php`` still serves the
monthly series is a question about SILSO, not about this code, and answering
it needs the network. Nothing here contacts it.
"""

import re

import pytest

from solarwindpy.solar_activity.base import ID
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID

VALID_KEYS = ("d", "m", "m13", "y", "hd", "hm", "hm13")


def _documented_urls():
    """``{key: url}`` from the ``SIDC_ID.__init__`` docstring.

    The Key/URL table supplies each key's file name; the sentence "URLs
    replace the wild card in ``<base>*``" supplies the base. The table is
    parsed structurally: the rows between the second and third ``======``
    rules, one key per line at the Key column's indent (the second line of
    "Hemispheric" is indented past it and contributes no key).
    """
    doc = SIDC_ID.__init__.__doc__
    lines = doc.splitlines()
    rules = [i for i, line in enumerate(lines) if line.strip().startswith("======")]
    assert len(rules) == 3, "the docstring table's rules moved; this parse is stale"
    key_column = len(lines[rules[1]]) - len(lines[rules[1]].lstrip())

    (base,) = re.findall(r"``(http\S+)\*``", doc)
    urls = {}
    first_row, last_row = rules[1] + 1, rules[2]
    for line in lines[first_row:last_row]:
        if line.strip() and len(line) - len(line.lstrip()) == key_column:
            fields = line.split()
            urls[fields[0]] = base + fields[-1]
    return base, urls


DOCUMENTED_BASE, DOCUMENTED_URLS = _documented_urls()


@pytest.mark.parametrize("key", VALID_KEYS)
def test_valid_key_is_retained(key):
    """A supported key is stored as given.

    ON FAILURE: the identifier reports a different series than was requested,
    and the loader would cache the download under the wrong name. The code is
    wrong.
    """
    assert SIDC_ID(key).key == key


@pytest.mark.parametrize("key", VALID_KEYS)
def test_url_is_the_base_joined_to_the_keys_fragment(key):
    """URL = documented base + the file the docstring table lists for the key.

    ON FAILURE: URL construction is dropping or mangling a component -- for
    instance urljoin discarding a path because the base lost its trailing
    slash -- or the docstring table no longer matches the code. The code is
    wrong, unless the author changed an endpoint and the docstring lags.
    """
    assert SIDC_ID(key).url == DOCUMENTED_URLS[key]


def test_every_key_maps_to_a_distinct_endpoint():
    """No two series share a URL.

    A collision would silently serve one series' data under another's key,
    which no caller could detect.

    ON FAILURE: two keys point at the same endpoint. The code is wrong.
    """
    urls = [SIDC_ID(key).url for key in VALID_KEYS]
    assert len(set(urls)) == len(urls)


def test_the_documented_keys_are_the_supported_keys():
    """The keys the class documents are exactly the keys it accepts.

    The docstring table on ``SIDC_ID.__init__`` is the user-facing list of
    series. Every documented key must construct, and ``VALID_KEYS`` (the keys
    ``test_valid_key_is_retained`` shows are accepted) must be the documented
    set; a key present in one and not the other is a documentation bug that
    presents as a runtime error.

    ON FAILURE: the docstring table and the accepted keys disagree. One of
    them is wrong.
    """
    assert set(DOCUMENTED_URLS) == set(VALID_KEYS)
    for key in DOCUMENTED_URLS:
        assert SIDC_ID(key).key == key


def test_urls_are_absolute_http_urls():
    """Every constructed URL is an absolute URL under the documented SILSO base.

    ON FAILURE: a relative or malformed URL would be handed to read_csv, which
    would try to open it as a local path. The code is wrong.
    """
    assert DOCUMENTED_BASE.startswith("http://")
    for key in VALID_KEYS:
        url = SIDC_ID(key).url
        assert url.startswith(DOCUMENTED_BASE)
        assert len(url) > len(DOCUMENTED_BASE)


@pytest.mark.parametrize(
    "key",
    [
        "M",  # right series, wrong case
        " m ",  # right series, surrounding whitespace
        "",
        None,
        13,
        "13",
        "abc",
        "toolong",
        "m13-special!@#$%",
    ],
)
def test_unsupported_key_is_refused_at_construction(key):
    """An unknown key fails immediately rather than at download time.

    Includes the near misses -- wrong case, stray whitespace, the integer 13
    for the string "m13" -- because those are the mistakes a caller actually
    makes, and a silent fallback would download the wrong series.

    ON FAILURE: a mistyped key is accepted and the error surfaces much later,
    or not at all. The code is wrong.
    """
    with pytest.raises(NotImplementedError, match="key unavailable"):
        SIDC_ID(key)


def test_is_an_id():
    """SIDC_ID is an ID, which is what ActivityIndicator.set_id requires.

    ON FAILURE: ``SIDC.set_id`` would reject the identifier its own
    constructor builds. The code is wrong.
    """
    assert isinstance(SIDC_ID("m"), ID)


def test_construction_is_deterministic():
    """Two identifiers for the same key agree on key and URL.

    ON FAILURE: identifier construction depends on hidden state. The code is
    wrong.
    """
    first = SIDC_ID("hm13")
    second = SIDC_ID("hm13")

    assert first.key == second.key
    assert first.url == second.url
