# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""How a Plasma species quantity combines over a "+" total.

The author's ruling (2026-11-10): "+" means "combine in physically viable
way". Number density, mass density, thermal pressure and temperature add over
species; a total thermal speed is refused. ``RULING`` restates that ruling
here so the expected values come from outside the code.

The behaviour tests run on the example plasma with species masked as in
``tests/core/test_missing_data.py``: p1 is missing at row 0, a at row 1 and
both at row 2; p2 is complete.
"""

import inspect
import re

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from solarwindpy.core.plasma import Plasma
from tests.core.test_missing_data import _species_masked_plasma

# The author's ruling, 2026-11-10. "strict_sum": a sum over the species present
# that the caller can make strict with skipna=False.
RULING = {
    "n": "strict_sum",
    "rho": "sum",
    "w": "refuse",
    "pth": "sum",
    "T": "sum",
}
SUMMED = sorted(k for k, rule in RULING.items() if rule != "refuse")
REFUSED = sorted(k for k, rule in RULING.items() if rule == "refuse")

_NO_HELPER = (
    "Plasma has no _gather helper or _SPECIES_COMBINE mapping yet; "
    "remove this marker when the species gather refactor lands"
)


@pytest.fixture(scope="module")
def masked():
    r"""Example plasma with p1 masked at row 0, a at row 1, both at row 2."""
    return _species_masked_plasma()


def _per_species(result, s):
    r"""The species-``s`` part of a several-species result."""
    if result.columns.nlevels == 1:
        return result.loc[:, s]
    return result.xs(s, axis=1, level="S")


def _assert_same(got, expected):
    if isinstance(expected, pd.Series):
        pdt.assert_series_equal(got, expected, check_names=False)
    else:
        pdt.assert_frame_equal(got, expected, check_like=True, check_names=False)


# Architecture: one home for the combining rule.


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=_NO_HELPER)
def test_the_combine_mapping_is_the_authors_ruling():
    r"""``Plasma._SPECIES_COMBINE`` holds exactly the author's ruling.

    This inspects private structure at the author's request: the mapping is the
    one home for the "+" rule.

    ON FAILURE: the code is wrong, unless the author revised the ruling; then
    update ``RULING``.
    """
    assert Plasma._SPECIES_COMBINE == RULING


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=_NO_HELPER)
@pytest.mark.parametrize("key", sorted(RULING))
def test_each_ruled_quantity_delegates_to_the_one_gather(key):
    r"""Plasma method ``key`` calls ``_gather(key, ...)`` and gathers nothing itself.

    This inspects source at the author's request: no ruled method re-implements
    the select, concatenate and combine form.

    ON FAILURE: the code is wrong; a ruled method has its own copy of the form.
    """
    assert callable(Plasma._gather)
    src = inspect.getsource(getattr(Plasma, key))
    assert f'self._gather("{key}"' in src
    for copied in ("self.ions.loc", "pd.concat", "_species_total", "reorder_levels"):
        assert copied not in src


@pytest.mark.xfail(strict=True, raises=AttributeError, reason=_NO_HELPER)
def test_every_gathered_quantity_has_a_combine_rule():
    r"""Every ``_gather("<key>"`` call in Plasma names a key of the mapping.

    ON FAILURE: the code is wrong; a quantity was routed through ``_gather``
    without a rule for "+".
    """
    rules = Plasma._SPECIES_COMBINE
    called = set(re.findall(r'self\._gather\("(\w+)"', inspect.getsource(Plasma)))
    assert called
    assert called <= set(rules)


# Behaviour: the ruling as the user sees it.


@pytest.mark.parametrize("key", REFUSED)
@pytest.mark.parametrize("species", [("a+p1",), ("p1+a",), ("a", "p1+a")])
def test_a_refused_quantity_raises_for_any_plus_species(masked, key, species):
    r"""A refused total raises NotImplementedError whenever any argument has "+".

    ON FAILURE: the code is wrong, unless the author revises the ruling that a
    total thermal speed is not physically viable.
    """
    with pytest.raises(NotImplementedError, match="physically ambiguous"):
        getattr(masked, key)(*species)


@pytest.mark.parametrize("key", SUMMED)
def test_a_species_total_adds_the_species_present(masked, key):
    r"""``key("a+p1")`` is the per-species values added where present, NaN where none.

    Identity: the across-species rule of docs page ``missing_data``. Adding with
    ``fill_value=0`` keeps a lone species and leaves NaN where both are missing.
    So row 0 is the alpha value, row 1 the proton value and row 2 NaN.

    ON FAILURE: the code is wrong, unless the author revises the across-species
    missing-data rule.
    """
    method = getattr(masked, key)
    a, p1 = method("a"), method("p1")
    expected = a.add(p1, fill_value=0)
    total = method("a+p1")

    _assert_same(total, expected)
    _assert_same(total.iloc[[0]], a.iloc[[0]])
    _assert_same(total.iloc[[1]], p1.iloc[[1]])
    assert np.isnan(total.iloc[2]).all()


@pytest.mark.parametrize("key", SUMMED)
def test_the_order_of_species_in_a_total_does_not_change_it(masked, key):
    r"""``key("a+p1")`` equals ``key("p1+a")`` (identity: addition commutes).

    ON FAILURE: the code is wrong.
    """
    method = getattr(masked, key)
    _assert_same(method("p1+a"), method("a+p1"))


def test_the_strict_density_total_is_nan_where_any_species_is_missing(masked):
    r"""``n("p1+p2", skipna=False)`` is NaN where p1 is missing, the sum elsewhere.

    p2 is complete and p1 is missing at rows 0 and 2, so the strict total is NaN
    there and p1 + p2 at row 1, while the default total is p2 alone at rows 0
    and 2. With no species present (``"a+p1"`` at row 2) both are NaN.

    ON FAILURE: the code is wrong, unless the author revises the strict total of
    docs page ``missing_data``.
    """
    p1, p2 = masked.n("p1"), masked.n("p2")
    strict = masked.n("p1+p2", skipna=False)
    assert strict.isna().tolist() == [True, False, True]
    _assert_same(strict.iloc[[1]], (p1 + p2).iloc[[1]])
    _assert_same(masked.n("p1+p2").iloc[[0, 2]], p2.iloc[[0, 2]])
    assert np.isnan(masked.n("a+p1").iloc[2])
    assert np.isnan(masked.n("a+p1", skipna=False).iloc[2])


@pytest.mark.parametrize("key", sorted(RULING))
def test_several_species_give_one_column_set_per_species_on_level_S(masked, key):
    r"""``key("a", "p1")`` has an "S" level whose parts equal ``key("a")``, ``key("p1")``.

    ON FAILURE: the code is wrong; callers select species with
    ``xs(..., level="S")``.
    """
    method = getattr(masked, key)
    several = method("a", "p1")
    assert "S" in several.columns.names
    assert set(several.columns.get_level_values("S")) == {"a", "p1"}
    for s in ("a", "p1"):
        _assert_same(_per_species(several, s), method(s))


@pytest.mark.parametrize("key", sorted(RULING))
def test_the_order_of_several_species_does_not_change_the_result(masked, key):
    r"""``key("a", "p1")`` equals ``key("p1", "a")``, columns included.

    ON FAILURE: the code is wrong.
    """
    method = getattr(masked, key)
    pdt.assert_frame_equal(method("p1", "a"), method("a", "p1"))


@pytest.mark.parametrize("key", ["n", "rho"])
@pytest.mark.parametrize("species", ["a", "p1+a", "a+p1"])
def test_a_scalar_total_is_named_by_the_species_as_written(masked, key, species):
    r"""``n`` and ``rho`` of one species string are Series named by that string.

    The name is the argument as written, so ``"p1+a"`` is not reordered.

    ON FAILURE: the code is wrong.
    """
    assert getattr(masked, key)(species).name == species
