# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Supported spacecraft and frames live in one table that every check reads."""

import numpy as np
import pytest

import solarwindpy as swp
from solarwindpy.core import spacecraft


def _position_data():
    return swp.examples.load_plasma().sc.data


def test_every_supported_frame_is_accepted_and_gives_a_finite_distance():
    r"""Each frame in the table constructs and converts to a distance to the Sun.

    The relation keeps ``set_frame_name`` and ``distance2sun`` from drifting
    apart: a frame one accepts the other must convert.

    ON FAILURE: the code is wrong.
    """
    data = _position_data()
    frames = spacecraft._SUPPORTED["frame"]
    assert frames
    for frame in frames:
        sc = spacecraft.Spacecraft(data, "PSP", frame)
        assert sc.frame == frame
        assert np.isfinite(sc.distance2sun.to_numpy()).all()


def test_every_supported_name_constructs():
    r"""Each spacecraft name in the table constructs and is stored upper-cased.

    ON FAILURE: the code is wrong.
    """
    data = _position_data()
    names = spacecraft._SUPPORTED["name"]
    assert names
    for name in names:
        assert spacecraft.Spacecraft(data, name.lower(), "HCI").name == name


def test_the_name_check_reads_the_table(monkeypatch):
    r"""A name added to the table is accepted, so the check has no second list.

    ON FAILURE: the code is wrong.
    """
    supported = dict(spacecraft._SUPPORTED)
    supported["name"] = (*supported["name"], "ACE")
    monkeypatch.setattr(spacecraft, "_SUPPORTED", supported)
    assert spacecraft.Spacecraft(_position_data(), "ace", "GSE").name == "ACE"


@pytest.mark.parametrize(
    "name, frame, supported",
    [("PSP", "rtn", ("GSE", "HCI")), ("ace", "GSE", ("PSP", "WIND"))],
    ids=["frame", "name"],
)
def test_a_refusal_names_the_supported_values(name, frame, supported):
    r"""An unsupported frame or name is refused with the values that are supported.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(NotImplementedError) as excinfo:
        spacecraft.Spacecraft(_position_data(), name, frame)
    for value in supported:
        assert value in str(excinfo.value)
