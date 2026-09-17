#!/usr/bin/env python
"""Test SIDC_ID: which SILSO series a key selects, and how its URL is built.

``SIDC_ID`` maps a short series key to a SILSO endpoint. The tests below
assert the composition -- URL = base + fragment -- and the class's error
behaviour, rather than restating the lookup table, which would only assert
that the module equals itself.

The endpoint names are documented in the class's own docstring table and on
SILSO's data page, <https://www.sidc.be/SILSO/datafiles>.

KNOWN GAP -- the endpoints are not reached
------------------------------------------
Whether ``http://www.sidc.be/silso/INFO/snmtotcsv.php`` still serves the
monthly series is a question about SILSO, not about this code, and answering
it needs the network. Nothing here contacts it.
"""

import pytest

from solarwindpy.solar_activity.base import ID
from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID

VALID_KEYS = ("d", "m", "m13", "y", "hd", "hm", "hm13")


@pytest.fixture
def identifier():
    """An arbitrary valid identifier, used to reach the class's lookup table."""
    return SIDC_ID("m")


@pytest.mark.parametrize("key", VALID_KEYS)
def test_valid_key_is_retained(key):
    """A supported key is stored as given.

    ON FAILURE: the identifier reports a different series than was requested,
    and the loader would cache the download under the wrong name. The code is
    wrong.
    """
    assert SIDC_ID(key).key == key


@pytest.mark.parametrize("key", VALID_KEYS)
def test_url_is_the_base_joined_to_the_keys_fragment(key, identifier):
    """URL = base + the fragment the key maps to.

    Identity, composed from the parts the class exposes, so it holds whatever
    the table contains and survives SILSO changing an endpoint name.

    ON FAILURE: URL construction is dropping or mangling a component -- for
    instance urljoin discarding a path because the base lost its trailing
    slash. The code is wrong.
    """
    sidc_id = SIDC_ID(key)
    assert sidc_id.url == identifier._url_base + identifier._trans_url[key]


def test_every_key_maps_to_a_distinct_endpoint(identifier):
    """No two series share a URL.

    A collision would silently serve one series' data under another's key,
    which no caller could detect.

    ON FAILURE: two keys point at the same endpoint. The code is wrong.
    """
    urls = [SIDC_ID(key).url for key in identifier._trans_url]
    assert len(set(urls)) == len(urls)


def test_the_documented_keys_are_the_supported_keys(identifier):
    """The keys the class documents are exactly the keys it accepts.

    The docstring table on ``SIDC_ID.__init__`` is the user-facing list of
    series. A key present in one and not the other is a documentation bug that
    presents as a runtime error.

    The table is parsed structurally -- the rows between the second and third
    ``======`` rules -- rather than by filtering against the answer. Filtering
    candidate keys through VALID_KEYS would make the documented set a subset
    by construction, so the test could only ever catch a key that is
    implemented but undocumented, never one that is documented but missing.

    ON FAILURE: the docstring table and the URL table disagree. One of them is
    wrong.
    """
    lines = SIDC_ID.__init__.__doc__.splitlines()
    rules = [i for i, line in enumerate(lines) if line.strip().startswith("======")]
    assert len(rules) == 3, "the docstring table's rules moved; this parse is stale"

    rule = lines[rules[1]]
    key_column = len(rule) - len(rule.lstrip())

    first_row, last_row = rules[1] + 1, rules[2]

    documented = set()
    for line in lines[first_row:last_row]:
        if not line.strip():
            continue
        # A continuation line (the second line of "Hemispheric") is indented
        # past the Key column and contributes no key.
        if len(line) - len(line.lstrip()) == key_column:
            documented.add(line.split()[0])

    assert documented == set(identifier._trans_url) == set(VALID_KEYS)


def test_urls_are_absolute_http_urls(identifier):
    """Every constructed URL is an absolute URL under the SILSO base.

    ON FAILURE: a relative or malformed URL would be handed to read_csv, which
    would try to open it as a local path. The code is wrong.
    """
    for key in identifier._trans_url:
        url = SIDC_ID(key).url
        assert url.startswith(identifier._url_base)
        assert len(url) > len(identifier._url_base)


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


def test_is_an_id(identifier):
    """SIDC_ID is an ID, which is what ActivityIndicator.set_id requires.

    ON FAILURE: ``SIDC.set_id`` would reject the identifier its own
    constructor builds. The code is wrong.
    """
    assert isinstance(identifier, ID)


def test_construction_is_deterministic():
    """Two identifiers for the same key agree on key and URL.

    ON FAILURE: identifier construction depends on hidden state. The code is
    wrong.
    """
    first = SIDC_ID("hm13")
    second = SIDC_ID("hm13")

    assert first.key == second.key
    assert first.url == second.url
