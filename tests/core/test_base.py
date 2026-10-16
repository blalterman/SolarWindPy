#!/usr/bin/env python
"""Tests for basic synthetic data setup."""

import re

import pandas as pd
import pytest
from unittest import TestCase

import solarwindpy as swp
from solarwindpy.core import ions, plasma, spacecraft, tensor, vector
from solarwindpy.examples import _read_example

pd.set_option("mode.chained_assignment", "raise")


class SyntheticData(object):
    """The example data behind ``solarwindpy.examples.load_plasma``, as frames.

    ``plasma_data`` keeps every column of the example CSV, including those
    ``Plasma`` drops; ``spacecraft_data`` holds both the HCI trajectory and
    the GSE position as ``(M, C)`` columns.
    """

    def __init__(self):
        self._plasma_data = _read_example("plasma")
        self._spacecraft_data = _read_example("spacecraft").xs("", axis=1, level="S")

    @property
    def spacecraft_data(self):
        return self._spacecraft_data

    @property
    def plasma_data(self):
        return self._plasma_data

    @property
    def combined_data(self):
        sc = pd.concat(
            {"sc": self.spacecraft_data}, axis=1, names=["S"], sort=True
        ).reorder_levels(["M", "C", "S"], axis=1)
        out = pd.concat([self.plasma_data, sc], axis=1, sort=True)
        return out


class SWEData(TestCase):
    @classmethod
    def setUpClass(cls):
        data = SyntheticData()
        cls.data = data.plasma_data.sort_index(axis=1)
        cls.set_object_testing()


class AlphaTest(object):
    @property
    def species(self):
        return "a"


class P1Test(object):
    @property
    def species(self):
        return "p1"


class P2Test(object):
    @property
    def species(self):
        return "p2"


class AlphaP1Test(object):
    @property
    def species(self):
        return "a+p1"


class AlphaP2Test(object):
    @property
    def species(self):
        return "a+p2"


class P1P2Test(object):
    @property
    def species(self):
        return "p1+p2"


class AlphaP1P2Test(object):
    @property
    def species(self):
        return "a+p1+p2"


# Time-index checks shared by every data-backed object (``Core._time_disorder``).


def _warning_records(caplog):
    return [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]


def _example_rows(rows):
    """The example plasma, spacecraft and field frames, taking ``rows`` in order."""
    p = swp.examples.load_plasma()
    b = p.data.xs("b", axis=1, level="M").xs("", axis=1, level="S")
    return p, p.data.iloc[rows], p.spacecraft.data.iloc[rows], b.iloc[rows]


def _build_plasma(p, data):
    """Build a Plasma and every child object it serves, as a user would."""
    built = plasma.Plasma(data, *p.species)
    for s in built.species:
        ion = built.ions.loc[s]
        ion.v, ion.w, ion.n
    built.b
    return built


_BUILDS = {
    "plasma": lambda p, data, sc, b: _build_plasma(p, data),
    "spacecraft": lambda p, data, sc, b: spacecraft.Spacecraft(sc, "PSP", "HCI"),
    "vector": lambda p, data, sc, b: vector.BField(b),
}


@pytest.mark.parametrize("build", list(_BUILDS.values()), ids=list(_BUILDS))
def test_one_out_of_order_problem_logs_exactly_one_warning(caplog, build):
    r"""Rows out of time order log one warning for the whole build, never two.

    The example rows are taken in order 2, 0, 1: one problem. Building a
    Plasma and every Ion, Vector and Tensor it serves, a standalone
    Spacecraft, or a standalone BField each logs exactly one warning. Each
    sorts before the shared order check looks, so it does not repeat the
    warning.

    ON FAILURE: the code is wrong; an object or its children report one problem twice.
    """
    p, data, sc, b = _example_rows([2, 0, 1])
    with caplog.at_level("WARNING", logger="solarwindpy"):
        build(p, data, sc, b)
    assert len(_warning_records(caplog)) == 1


NOT_DATETIME = "non-DatetimeIndex"
NOT_INCREASING = "not monotonically increasing"


_ORDERED = {
    "vector": lambda data: vector.Vector(
        data.xs("v", axis=1, level="M").xs("p1", axis=1, level="S")
    ),
    "bfield": lambda data: vector.BField(
        data.xs("b", axis=1, level="M").xs("", axis=1, level="S")
    ),
    "tensor": lambda data: tensor.Tensor(
        data.xs("w", axis=1, level="M").xs("p1", axis=1, level="S")
    ),
}


@pytest.mark.parametrize("build", list(_ORDERED.values()), ids=list(_ORDERED))
def test_a_standalone_vector_or_tensor_out_of_order_warns_then_sorts(caplog, build):
    r"""A Vector, BField or Tensor built on rows out of order warns once, then sorts.

    Per the author, a Vector or Tensor built directly follows Plasma's time
    rule. The example rows taken in order 2, 0, 1 hold one problem: one
    warning naming the rows earlier than the row before them, and the data
    stored in time order, each row with its own values.

    ON FAILURE: the code is wrong; a Vector or Tensor built directly kept rows out of order.
    """
    data = swp.examples.load_plasma().data
    expected = build(data).data
    with caplog.at_level("WARNING", logger="solarwindpy"):
        obj = build(data.iloc[[2, 0, 1]])
    (message,) = _warning_records(caplog)
    assert "earlier than the row before them" in message
    pd.testing.assert_frame_equal(obj.data, expected)


def _with_missing_time(frame):
    """``frame``'s first three rows with the middle time replaced by NaT."""
    frame = frame.iloc[[0, 1, 2]]
    times = pd.DatetimeIndex([frame.index[0], pd.NaT, frame.index[2]])
    return frame.set_axis(times, axis=0)


_STANDALONE = {
    "ion": lambda p: ions.Ion(
        _with_missing_time(p.data.xs("p1", axis=1, level="S")), "p1"
    ),
    "vector": lambda p: vector.Vector(
        _with_missing_time(
            p.data.xs("v", axis=1, level="M").xs("p1", axis=1, level="S")
        )
    ),
    "tensor": lambda p: tensor.Tensor(
        _with_missing_time(
            p.data.xs("w", axis=1, level="M").xs("p1", axis=1, level="S")
        )
    ),
    "bfield": lambda p: vector.BField(
        _with_missing_time(p.data.xs("b", axis=1, level="M").xs("", axis=1, level="S"))
    ),
}


_CLASS_NAMES = {
    "ion": "Ion",
    "vector": "Vector",
    "tensor": "Tensor",
    "bfield": "BField",
}


@pytest.mark.parametrize(
    "build, name",
    [(_STANDALONE[k], _CLASS_NAMES[k]) for k in _STANDALONE],
    ids=list(_STANDALONE),
)
def test_a_standalone_object_refuses_missing_times(build, name):
    r"""An Ion, Vector, Tensor or BField built directly with a NaT time raises.

    Per the author, every time-indexed object refuses missing timestamps, as
    Plasma and Spacecraft do: three rows with the middle time NaT raise a
    ValueError naming the object's data and 1 missing of 3.

    ON FAILURE: the code is wrong; a directly built object accepted a NaT time.
    """
    p = swp.examples.load_plasma()
    with pytest.raises(
        ValueError,
        match=rf"{name} data time index has 1 of 3 timestamps missing \(NaT\); "
        "drop those rows first",
    ):
        build(p)


def test_a_spacecraft_refuses_missing_times_naming_its_data():
    r"""A Spacecraft built with a NaT time raises ValueError naming its data.

    ON FAILURE: the code is wrong.
    """
    p = swp.examples.load_plasma()
    with pytest.raises(
        ValueError, match=r"Spacecraft data time index has 1 of 3 timestamps missing"
    ):
        spacecraft.Spacecraft(_with_missing_time(p.spacecraft.data), "PSP", "HCI")


def test_one_non_datetime_index_logs_one_warning_across_a_plasma_build(caplog):
    r"""A Plasma on a non-DatetimeIndex logs that problem once, not once per child.

    The example data on a RangeIndex hold one problem. Building the Plasma and
    every Ion, Vector and Tensor it serves logs one non-DatetimeIndex warning:
    the children are built from data the Plasma already checked.

    ON FAILURE: the code is wrong; a child built from checked data repeated the index check.
    """
    p = swp.examples.load_plasma()
    data = p.data.set_axis(pd.RangeIndex(len(p.data)), axis=0)
    with caplog.at_level("WARNING", logger="solarwindpy"):
        _build_plasma(p, data)
    (message,) = _warning_records(caplog)
    assert NOT_DATETIME in message


def test_a_vector_built_directly_on_a_non_datetime_index_warns(caplog):
    r"""A Vector built directly, with the default, runs the full index check.

    The example field on a RangeIndex logs one non-DatetimeIndex warning; only
    objects a Plasma builds from its own checked data skip the check.

    ON FAILURE: the code is wrong; an object built directly skipped its index check.
    """
    _, _, _, b = _example_rows([0, 1, 2])
    with caplog.at_level("WARNING", logger="solarwindpy"):
        vector.Vector(b.set_axis(pd.RangeIndex(3), axis=0))
    (message,) = _warning_records(caplog)
    assert NOT_DATETIME in message


def test_a_child_whose_times_differ_from_its_parents_is_checked():
    r"""A child handed its parent's time index skips the checks only on that index.

    A builder passes the parent's checked time index as ``_time_checked``,
    the private switch documented on ``Base``. Data whose index is not that
    one, here the plasma's proton velocity with the middle time replaced by
    NaT, are checked like any directly built object and raise.

    ON FAILURE: the code is wrong; a child trusted a time index it was not built on.
    """
    p = swp.examples.load_plasma()
    v = _with_missing_time(p.p1.velocity.data)
    with pytest.raises(ValueError, match=r"1 of 3 timestamps missing \(NaT\)"):
        vector.Vector(v, _time_checked=p.data.index)


def test_an_ion_a_plasma_built_still_checks_new_data():
    r"""An Ion built by a Plasma refuses a NaT time passed to its ``set_data``.

    The Plasma's children skip the time checks only for the data the Plasma
    handed them; data set on them later are checked like any other.

    ON FAILURE: the code is wrong; skipping the time checks outlived construction.
    """
    p = swp.examples.load_plasma()
    with pytest.raises(ValueError, match=r"1 of 3 timestamps missing \(NaT\)"):
        p.p1.set_data(_with_missing_time(p.data.xs("p1", axis=1, level="S")))


def test_a_vector_on_an_index_that_cannot_be_ordered_warns_and_is_kept(caplog):
    r"""A Vector on an index of mixed types warns twice and keeps its rows.

    The index ``[1, "a", 2.0]`` is not a DatetimeIndex and its values cannot be
    compared, so it has no order: the Vector logs the non-DatetimeIndex and
    the order warnings, does not sort, and does not raise.

    ON FAILURE: the code is wrong; an index that cannot be ordered crashed or was sorted.
    """
    _, _, _, b = _example_rows([0, 1, 2])
    index = pd.Index([1, "a", 2.0])
    with caplog.at_level("WARNING", logger="solarwindpy"):
        v = vector.Vector(b.set_axis(index, axis=0))
    first, second = _warning_records(caplog)
    assert NOT_DATETIME in first
    assert NOT_INCREASING in second
    assert v.data.index.equals(index)


@pytest.mark.parametrize("species", [("a+p1",), ("p1", "a+p2")])
def test_a_plasma_species_joined_by_plus_raises_value_error_naming_it(species):
    r"""A Plasma species containing ``+`` raises ValueError naming that species.

    Combined species are formed in method calls, never stored; the error
    names the offending entry so the caller can split it.

    ON FAILURE: the code is wrong.
    """
    data = swp.examples.load_plasma().data
    combined = [s for s in species if "+" in s][0]
    expected = re.escape(f"Plasma.species can't contain '+': {combined}")
    with pytest.raises(ValueError, match=expected):
        plasma.Plasma(data, *species)


def test_objects_with_differently_labelled_data_are_unequal():
    r"""Two Vectors whose data have different times or columns compare unequal.

    Chosen input: the same field one day later, and the same field with an
    extra column ``w``. Neither comparison raises.

    ON FAILURE: the code is wrong.
    """
    p = swp.examples.load_plasma()
    b = p.data.xs("b", axis=1, level="M").xs("", axis=1, level="S")
    later = b.set_axis(b.index + pd.Timedelta("1D"), axis=0)
    extra = b.assign(w=1.0)
    assert vector.Vector(b) != vector.Vector(later)
    assert vector.Vector(b) != vector.Vector(extra)
    assert vector.Vector(b) == vector.Vector(b.copy())
