# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Supported spacecraft and frames live in one table that every check reads."""

import dataclasses

import numpy as np
import pandas.testing as pdt
import pytest
from scipy import constants

import solarwindpy as swp
from solarwindpy.core import quantities, spacecraft


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


@pytest.mark.parametrize("frame", spacecraft._SUPPORTED["frame"])
def test_every_supported_frame_has_a_registry_unit(frame):
    r"""Each supported frame has a registry entry with an SI factor and a TeX unit.

    The table and the registry are two lists, so a frame added to one and not
    the other would be accepted but neither convertible nor labelled.

    ON FAILURE: the code is wrong.
    """
    entry = quantities.QUANTITIES[frame.lower()]
    assert entry.si is not None
    assert entry.units is not None


@pytest.mark.parametrize("frame", spacecraft._SUPPORTED["frame"])
def test_distance_reads_the_frame_radius_from_the_registry(monkeypatch, frame):
    r"""``distance2sun`` scales position by the registry's radius for its frame.

    With the radius replaced by 2 m, HCI distance is twice ``pos.mag`` and GSE
    distance is from (1 AU - 2 x, 2 y, 2 z) m.

    ON FAILURE: the code is wrong.
    """
    registry = dict(quantities.QUANTITIES)
    key = frame.lower()
    registry[key] = dataclasses.replace(registry[key], si=2.0)
    monkeypatch.setattr(quantities, "QUANTITIES", registry)
    sc = spacecraft.Spacecraft(_position_data(), "PSP", frame)
    pos = sc.pos.data * 2.0
    if frame == "GSE":
        pos = pos.assign(x=constants.au - pos.loc[:, "x"])
    expected = np.sqrt(pos.pow(2).sum(axis=1)).rename("distance2sun")
    pdt.assert_series_equal(sc.distance2sun, expected)


@pytest.mark.parametrize("frame", spacecraft._SUPPORTED["frame"])
def test_position_units_are_the_frame_entry_units(frame):
    r"""``pos_units`` is the TeX unit of the spacecraft's frame entry.

    The ``pos`` entry states no unit, because the unit depends on the frame.

    ON FAILURE: the code is wrong.
    """
    sc = spacecraft.Spacecraft(_position_data(), "PSP", frame)
    assert sc.pos_units == quantities.QUANTITIES[frame.lower()].units
    assert quantities.QUANTITIES["pos"].units is None
