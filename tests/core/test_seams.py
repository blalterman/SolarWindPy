# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Every column operation in core/ names the level it acts on.

Columns form a MultiIndex with levels ``M`` (measurement), ``C`` (component)
and ``S`` (species). These tests pin the seam that later lets the data model
change behind one accessor: selection and reduction by level *name*, never by
level position, and Vector and Tensor holding a single species.

The accessor and reduction helpers are private to ``core``. They are tested
directly because they are the seam itself: every public quantity routes
through them, so their contract is the contract each public quantity relies
on. The missing-data rule they carry is docs page ``missing_data``.
"""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

import solarwindpy as swp
from solarwindpy.core import base, tensor, vector


@pytest.fixture(scope="module")
def plasma_data():
    return swp.examples.load_plasma().data


def _times(n):
    return pd.date_range("2000-01-01", periods=n, freq="min")


def _components(rows, labels=("x", "y", "z"), name="C"):
    """A frame of hand-chosen component rows on a flat index named ``name``."""
    columns = pd.Index(list(labels), name=name)
    return pd.DataFrame(rows, index=_times(len(rows)), columns=columns, dtype=float)


def _two_species(rows_by_species, labels=("x", "y", "z")):
    """A frame with column levels ``("C", "S")`` from per-species component rows."""
    frames = {s: _components(rows, labels) for s, rows in rows_by_species.items()}
    out = pd.concat(frames, axis=1, names=["S"], sort=True)
    return out.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)


# --- The accessor -----------------------------------------------------------


def test_species_selection_names_the_level_not_its_position(plasma_data):
    r"""Selecting species p1 by level name ignores where the ``S`` level sits.

    With the levels reordered to ``("S", "M", "C")``, the accessor still returns
    the columns that ``.xs("p1", level="S")`` returns from the stored order.

    ON FAILURE: the code is wrong.
    """
    expected = plasma_data.xs("p1", axis=1, level="S")
    moved = plasma_data.reorder_levels(["S", "M", "C"], axis=1)
    got = base.Core._select(moved, "p1", "S")
    got = got.reorder_levels(["M", "C"], axis=1).sort_index(axis=1)
    pdt.assert_frame_equal(got, expected.sort_index(axis=1))


def test_component_selection_shares_the_parent_data():
    r"""A component selected from a flat frame shares the frame's memory.

    The package relies on ``.xs`` views to keep memory down (CLAUDE.md, Data
    model), so the accessor must not copy.

    ON FAILURE: the code is wrong; the accessor copied instead of selecting a view.
    """
    frame = _components([[1, 2, 3], [4, 5, 6]])
    got = base.Core._select(frame, "y", "C")
    pdt.assert_series_equal(got, frame["y"])
    assert np.shares_memory(got.to_numpy(), frame["y"].to_numpy())


def test_a_list_of_components_keeps_the_order_asked_for():
    r"""Selecting ``["z", "x"]`` returns exactly those columns in that order.

    ON FAILURE: the code is wrong.
    """
    frame = _components([[1, 2, 3], [4, 5, 6]])
    got = base.Core._select(frame, ["z", "x"], "C")
    assert got.columns.tolist() == ["z", "x"]
    pdt.assert_frame_equal(got, frame.loc[:, ["z", "x"]])


def test_a_list_of_components_on_two_levels_keeps_every_species():
    r"""Selecting ``["y", "x"]`` on ``("C", "S")`` columns keeps both species.

    ON FAILURE: the code is wrong.
    """
    frame = _two_species({"a": [[1, 2, 3]], "p1": [[4, 5, 6]]})
    got = base.Core._select(frame, ["y", "x"], "C")
    expected = [("y", "a"), ("y", "p1"), ("x", "a"), ("x", "p1")]
    assert got.columns.tolist() == expected
    assert got.loc[:, ("x", "p1")].tolist() == [4.0]


def test_an_unknown_label_raises_naming_the_level_and_its_labels():
    r"""Selecting a component that is absent raises KeyError listing x, y and z.

    ON FAILURE: the code is wrong.
    """
    frame = _components([[1, 2, 3]])
    with pytest.raises(KeyError, match=r"component 'par'.*x.*y.*z"):
        base.Core._select(frame, "par", "C")


def test_a_flat_index_named_for_another_level_is_refused():
    r"""Selecting a component from flat columns named ``S`` raises ValueError.

    A flat index carries one level; its name, when set, says which.

    ON FAILURE: the code is wrong.
    """
    frame = _components([[1, 2]], labels=("a", "p1"), name="S")
    with pytest.raises(ValueError, match=r"level 'C'.*'S'"):
        base.Core._select(frame, "a", "C")


def test_vector_and_tensor_share_one_component_call():
    r"""Vector and Tensor resolve ``__call__`` to the same function.

    CLAUDE.md: extract shared logic at the second copy.

    ON FAILURE: the code is wrong; the component call was copied again.
    """
    assert vector.Vector.__call__ is tensor.Tensor.__call__


# --- Reductions name their level -----------------------------------------


def test_a_component_sum_is_nan_where_any_component_is_missing():
    r"""Summing over ``C`` is strict: one missing component makes the row NaN.

    Rows (1, 2, 3) and (4, NaN, 6): the first sums to 6, the second is NaN
    (docs page ``missing_data``, Within a species).

    ON FAILURE: the code is wrong.
    """
    frame = _components([[1, 2, 3], [4, np.nan, 6]])
    got = base.Core._component_reduce(frame)
    assert got.iloc[0] == 6.0
    assert np.isnan(got.iloc[1])


def test_a_component_product_is_nan_where_any_component_is_missing():
    r"""A product over ``C`` is strict: (2, 3) gives 6, (2, NaN) gives NaN.

    ON FAILURE: the code is wrong.
    """
    frame = _components([[2, 3], [2, np.nan]], labels=("par", "per"))
    got = base.Core._component_reduce(frame, "prod")
    assert got.iloc[0] == 6.0
    assert np.isnan(got.iloc[1])


def test_a_component_sum_keeps_each_species_whatever_the_level_order():
    r"""Summing over ``C`` keeps one column per species, for either level order.

    Species a has rows (1, 2, 3) and (NaN, 1, 1); p1 has (4, 5, 6) twice. The
    sums are a: 6 then NaN, p1: 15 twice, with columns ``("C", "S")`` or
    ``("S", "C")``.

    ON FAILURE: the code is wrong; the sum reduced a level by position.
    """
    frame = _two_species({"a": [[1, 2, 3], [np.nan, 1, 1]], "p1": [[4, 5, 6]] * 2})
    expected = pd.DataFrame(
        {"a": [6.0, np.nan], "p1": [15.0, 15.0]},
        index=frame.index,
        columns=pd.Index(["a", "p1"], name="S"),
    )
    for order in (["C", "S"], ["S", "C"]):
        moved = frame.reorder_levels(order, axis=1).sort_index(axis=1)
        pdt.assert_frame_equal(base.Core._component_reduce(moved), expected)


def test_a_species_total_uses_the_species_present():
    r"""Summing over ``S`` is partial: NaN only where no species is present.

    Densities a = (1, NaN, NaN) and p1 = (10, 20, NaN) total 11, 20, NaN
    (docs page ``missing_data``, Across species).

    ON FAILURE: the code is wrong.
    """
    frame = _components([[1, 10], [np.nan, 20], [np.nan, np.nan]], ("a", "p1"), "S")
    got = base.Core._species_total(frame)
    assert got.iloc[:2].tolist() == [11.0, 20.0]
    assert np.isnan(got.iloc[2])


def test_a_species_total_keeps_each_component():
    r"""Summing over ``S`` on ``("C", "S")`` columns keeps one column per component.

    a = (1, 2, NaN) at row 0 and absent at row 1; p1 = (4, 5, 6) both rows. The
    totals are (5, 7, 6) then (4, 5, 6).

    ON FAILURE: the code is wrong.
    """
    frame = _two_species(
        {"a": [[1, 2, np.nan], [np.nan] * 3], "p1": [[4, 5, 6], [4, 5, 6]]}
    )
    expected = _components([[5, 7, 6], [4, 5, 6]])
    pdt.assert_frame_equal(base.Core._species_total(frame), expected)


def test_a_reduction_refuses_columns_without_its_level():
    r"""A component sum of flat columns named ``S`` raises ValueError.

    ON FAILURE: the code is wrong; a reduction summed over the wrong level.
    """
    frame = _components([[1, 10]], labels=("a", "p1"), name="S")
    with pytest.raises(ValueError, match=r"level 'C'.*'S'"):
        base.Core._component_reduce(frame)


# --- Vector and Tensor hold one species ----------------------------------

_BUILDERS = {
    "vector": (vector.Vector, ("x", "y", "z")),
    "bfield": (vector.BField, ("x", "y", "z")),
    "tensor": (tensor.Tensor, ("par", "per", "scalar")),
}


@pytest.mark.parametrize("cls, labels", list(_BUILDERS.values()), ids=list(_BUILDERS))
def test_several_species_are_refused_naming_them(cls, labels):
    r"""Building from columns whose ``S`` level holds a and p1 raises ValueError.

    Vector and Tensor are single-species by the author's design.

    ON FAILURE: the code is wrong; a multi-species frame was accepted.
    """
    frame = _two_species({"a": [[1, 2, 3]], "p1": [[4, 5, 6]]}, labels)
    with pytest.raises(ValueError, match=r"'a', 'p1'"):
        cls(frame)


@pytest.mark.parametrize(
    "cls", [vector.Vector, vector.BField], ids=["vector", "bfield"]
)
def test_one_species_on_a_species_level_is_accepted(cls):
    r"""Building a Vector from ``("C", "S")`` columns holding only p1 succeeds unchanged.

    Tensor is left out: it requires flat ``par``, ``per`` and ``scalar`` columns.

    ON FAILURE: the code is wrong; the single-species guard refuses one species.
    """
    frame = _two_species({"p1": [[4, 5, 6]]})
    pdt.assert_frame_equal(cls(frame).data, frame)
