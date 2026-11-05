# Spent-When: PERMANENT(Plasma stops offering info)
# Supersedes: none
"""Tests for :meth:`solarwindpy.core.plasma.Plasma.info`.

``info()`` is a one-column table, one row per field: the spacecraft and its
frame ("none" without one), the first and last observation time, the number
of observations, the species, and whether auxiliary data are attached. The
expected values are those the example's docstring documents
(``solarwindpy.examples.load_plasma``): PSP in HCI, three rows, species a, e,
p1 and p2, no auxiliary data.
"""

import pandas as pd

import solarwindpy as swp
from solarwindpy.core.plasma import Plasma

FIELDS = [
    "spacecraft",
    "frame",
    "start",
    "end",
    "observations",
    "species",
    "auxiliary data",
]


def test_info_of_the_example_names_its_spacecraft_times_and_species():
    """The example plasma: PSP in HCI, three rows, four species, no aux.

    ON FAILURE: the code is wrong.
    """
    plasma = swp.examples.load_plasma()
    info = plasma.info()
    assert isinstance(info, pd.DataFrame)
    assert info.index.tolist() == FIELDS
    assert info.columns.tolist() == ["value"]
    value = info.loc[:, "value"]
    assert value["spacecraft"] == "PSP"
    assert value["frame"] == "HCI"
    assert value["start"] == pd.Timestamp("1995-01-01 12:35:00")
    assert value["end"] == pd.Timestamp("2022-10-09 01:47:01.234560")
    assert value["observations"] == 3
    assert value["species"] == "a, e, p1, p2"
    assert value["auxiliary data"] == "no"


def test_info_without_a_spacecraft_says_none():
    """A plasma built without ``sc`` reports "none" for spacecraft and frame.

    ON FAILURE: the code is wrong.
    """
    example = swp.examples.load_plasma()
    plasma = Plasma(example.data, *example.species)
    value = plasma.info().loc[:, "value"]
    assert value["spacecraft"] == "none"
    assert value["frame"] == "none"
    assert value["observations"] == 3


def test_info_reports_attached_auxiliary_data():
    """After ``set_aux``, auxiliary data reads "yes".

    ON FAILURE: the code is wrong.
    """
    plasma = swp.examples.load_plasma()
    flags = pd.DataFrame({("quality", "", ""): [0, 1, 0]}, index=plasma.epoch)
    flags.columns.names = ["M", "C", "S"]
    plasma.set_aux(flags)
    assert plasma.info().loc["auxiliary data", "value"] == "yes"
