#!/usr/bin/env python
"""Tests for :mod:`solarwindpy.core.base`: time-index checks and equality."""

import re

import pandas as pd
import pytest
from unittest import TestCase

import solarwindpy as swp
from solarwindpy.core import ions, plasma, spacecraft, tensor, vector

from . import _fixtures as fixtures


# Time-index checks shared by every data-backed object (``Core._time_disorder``).


def _warning_records(caplog):
    return [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]


def _example_rows(rows):
    """The example plasma, spacecraft and field frames, taking ``rows`` in order."""
    p = swp.examples.load_plasma()
    b = p.data.xs("b", axis=1, level="M").xs("", axis=1, level="S")
    return p, p.data.iloc[rows], p.sc.data.iloc[rows], b.iloc[rows]


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
    v = _with_missing_time(p.p1.v.data)
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


class _SortFailsVector(vector.Vector):
    """A Vector whose sort step fails with a TypeError unrelated to comparison.

    Stands in for a defect inside the sort itself (not an index whose values
    cannot be compared), which no public input can provoke.
    """

    def _put_in_time_order(self, data, what, refusal=None):
        raise TypeError("unrelated failure inside the sort")


def test_an_unrelated_type_error_while_sorting_is_not_swallowed():
    r"""Only an index that cannot be compared is kept as given; other TypeErrors raise.

    The fallback for unorderable indexes must not hide a real failure in the
    sort: with comparable, in-order times, a TypeError raised while sorting
    reaches the caller.

    ON FAILURE: the code is wrong; the unorderable-index fallback swallows unrelated errors.
    """
    _, _, _, b = _example_rows([0, 1, 2])
    with pytest.raises(TypeError, match="unrelated failure inside the sort"):
        _SortFailsVector(b)


class TestQuantitySubclassEquality(TestCase):
    @classmethod
    def setUpClass(cls):
        r"""Override `setUpClass` so that it doesn't call `set_object_testing`."""
        fixture = fixtures.SyntheticData()
        data = fixture.plasma_data
        cls.gse = fixture.spacecraft_data.gse
        coeff = pd.Series({"par": 1.0, "per": 2.0}) / 3.0
        scalar = data.w.pow(2).multiply(coeff, axis=1, level="C")

        scalar = scalar.T.groupby(level="S").sum().T.pow(0.5)

        cols = pd.MultiIndex.from_tuples(
            scalar.columns.to_series().apply(lambda x: ("w", "scalar", x)),
            names=data.columns.names,
        )
        scalar.columns = cols
        scalar.name = "scalar"
        data = pd.concat([data, scalar], axis=1).sort_index(axis=1)
        cls.data = data

    def test_v(self):
        """Two Vectors built from the same alpha velocity are equal.

        ON FAILURE: the code is wrong.
        """
        data = self.data.v.xs("a", axis=1, level="S")
        va0 = vector.Vector(data)
        va1 = vector.Vector(data)
        self.assertEqual(va0, va0)
        self.assertEqual(va0, va1)

    def test_b(self):
        """Two BFields built from the same field are equal.

        ON FAILURE: the code is wrong.
        """
        data = self.data.b.xs("", axis=1, level="S")
        b0 = vector.BField(data)
        b1 = vector.BField(data)
        self.assertEqual(b0, b0)
        self.assertEqual(b0, b1)

    def test_b_v(self):
        """A BField never equals a Vector holding a velocity.

        ON FAILURE: the code is wrong.
        """
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        v = vector.Vector(self.data.v.xs("p2", axis=1, level="S"))
        self.assertNotEqual(b, v)

    def test_b_w(self):
        """A BField never equals a Tensor.

        ON FAILURE: the code is wrong.
        """
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        w = tensor.Tensor(self.data.w.xs("a", axis=1, level="S"))
        self.assertNotEqual(b, w)

    def test_gse(self):
        """Vectors from one GSE position are equal; a shifted one is not.

        The shifted position is displaced by 1.0 along GSE x.

        ON FAILURE: the code is wrong.
        """
        gse0 = vector.Vector(self.gse)
        gse1 = vector.Vector(self.gse)
        shifted = self.gse.copy()
        shifted["x"] = shifted["x"] + 1.0
        gse2 = vector.Vector(shifted)
        self.assertEqual(gse0, gse0)
        self.assertEqual(gse0, gse1)
        self.assertNotEqual(gse0, gse2)

    def test_b_gse(self):
        """A BField never equals a Vector, here the GSE position.

        ON FAILURE: the code is wrong.
        """
        b = vector.BField(self.data.b.xs("", axis=1, level="S"))
        gse = vector.Vector(self.gse)
        self.assertNotEqual(b, gse)

    def test_gse_v(self):
        """Vectors holding different data (GSE position, p2 velocity) differ.

        ON FAILURE: the code is wrong.
        """
        gse = vector.Vector(self.gse)
        v = vector.Vector(self.data.v.xs("p2", axis=1, level="S"))
        self.assertNotEqual(gse, v)

    def test_gse_w(self):
        """A Vector (GSE position) never equals a Tensor (alpha thermal speed).

        ON FAILURE: the code is wrong.
        """
        gse = vector.Vector(self.gse)
        w = tensor.Tensor(self.data.w.xs("a", axis=1, level="S"))
        self.assertNotEqual(gse, w)

    def test_va_vp1(self):
        """Alpha and p1 velocity Vectors differ.

        ON FAILURE: the code is wrong.
        """
        va = vector.Vector(self.data.v.xs("a", axis=1, level="S"))
        vp1 = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        self.assertNotEqual(va, vp1)

    def test_v_w(self):
        """A Vector never equals a Tensor of the same species.

        ON FAILURE: the code is wrong.
        """
        v = vector.Vector(self.data.v.xs("p1", axis=1, level="S"))
        w = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        self.assertNotEqual(v, w)

    def test_wp1_wp2(self):
        """p1 and p2 thermal-speed Tensors differ.

        ON FAILURE: the code is wrong.
        """
        wp1 = tensor.Tensor(self.data.w.xs("p1", axis=1, level="S"))
        wp2 = tensor.Tensor(self.data.w.xs("p2", axis=1, level="S"))
        self.assertNotEqual(wp1, wp2)
