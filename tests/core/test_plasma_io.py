"""`Plasma.save` and `Plasma.load_from_file`: the HDF5 round trip."""

import functools
import re

import pandas as pd
import pandas.testing as pdt
import pytest

import solarwindpy as swp
from solarwindpy.core import plasma
from tests.tolerances import exact
from . import test_base

# The example plasma's spacecraft is Parker Solar Probe in the HCI frame.
SC_NAME = "PSP"
SC_FRAME = "HCI"


def _example_plasma():
    """Example plasma with its spacecraft and two auxiliary columns."""
    p = swp.examples.load_plasma()
    # What the tests below assume of the example data.
    assert p.species == ("a", "e", "p1", "p2"), "example plasma species changed"
    # test_save_applies_each_modifier_function_before_writing drops "carr".
    assert "carr" in p.sc.data.columns.get_level_values("M"), (
        "example spacecraft no longer has Carrington coordinates"
    )
    aux = pd.DataFrame(
        {("quality", "", ""): [0, 1, 0], ("chisq", "", "p1"): [1.5, 2.5, 3.5]},
        index=p.epoch,
    )
    aux.columns.names = ["M", "C", "S"]
    p.set_auxiliary_data(aux)
    return p


def _assert_same_frame(actual, expected):
    """Labels equal and values equal to float rounding, NaN matching NaN."""
    assert actual.index.equals(expected.index)
    assert actual.columns.equals(expected.columns)
    assert actual.to_numpy(dtype=float) == exact(
        expected.to_numpy(dtype=float), nan_ok=True
    )


def _identity(frame):
    return frame


def test_save_and_load(tmp_path):
    """A plasma without spacecraft or auxiliary data loads back equal to itself.

    ON FAILURE: the code is wrong.
    """
    data = test_base.SyntheticData().plasma_data
    plas = plasma.Plasma(data, "a", "p1")
    fname = tmp_path / "plasma.h5"
    plas.save(fname)
    loaded = plasma.Plasma.load_from_file(fname, "a", "p1", sckey=None, akey=None)
    assert loaded == plas
    assert loaded.species == plas.species


def test_save_then_load_round_trips_data_spacecraft_and_auxiliary_data(tmp_path):
    """Saving and loading with the default keys returns the same plasma.

    The data (including the recomputed scalar thermal speed), species,
    spacecraft data, name and frame, and auxiliary data all come back. No
    species are passed to `load_from_file`, so it reads them from the data.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    loaded = plasma.Plasma.load_from_file(fname, sc_name=SC_NAME, sc_frame=SC_FRAME)

    assert loaded.species == p.species
    _assert_same_frame(loaded.data, p.data)
    assert loaded.sc.name == SC_NAME
    assert loaded.sc.frame == SC_FRAME
    _assert_same_frame(loaded.sc.data, p.sc.data)
    _assert_same_frame(loaded.aux, p.aux)


def test_save_writes_data_spacecraft_and_aux_at_the_default_keys(tmp_path):
    """`save` stores data at "FC", spacecraft at "SC" and aux at "FC_AUX".

    These are the documented defaults that `load_from_file` reads back. "FC"
    holds the plasma's measured columns; the scalar thermal speed is derived
    from them and recomputed on load, so it is not written.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    with pd.HDFStore(fname, mode="r") as store:
        assert sorted(store.keys()) == ["/FC", "/FC_AUX", "/SC"]
    measured = p.data.drop("scalar", axis=1, level="C")
    assert "scalar" in p.data.columns.get_level_values("C"), "nothing was dropped"
    _assert_same_frame(pd.read_hdf(fname, key="FC"), measured)
    _assert_same_frame(pd.read_hdf(fname, key="SC"), p.sc.data)
    _assert_same_frame(pd.read_hdf(fname, key="FC_AUX"), p.aux)


@pytest.mark.parametrize(
    "start, stop",
    [
        ("2022-01-01", None),
        (None, "2022-06-01"),
        ("2000-01-01", "2022-06-01"),
    ],
    ids=["start-only", "stop-only", "start-and-stop"],
)
def test_load_from_file_keeps_only_rows_between_start_and_stop(tmp_path, start, stop):
    """`start` and `stop` each bound the loaded rows, alone or together.

    The spacecraft and auxiliary data are cut to the same rows as the data.

    ON FAILURE: the code is wrong, unless the sanity assertion on the example
    epochs fails; then the example data changed and the bounds need new dates.
    """
    p = _example_plasma()
    # Rows of the plasma's epochs inside the closed interval [start, stop].
    rows = pd.Series(True, index=p.epoch)
    if start is not None:
        rows &= p.epoch >= pd.Timestamp(start)
    if stop is not None:
        rows &= p.epoch <= pd.Timestamp(stop)
    rows = rows.to_numpy()
    assert 0 < rows.sum() < len(rows), "bounds must keep some, not all, example rows"

    fname = tmp_path / "plasma.h5"
    p.save(fname)
    loaded = plasma.Plasma.load_from_file(
        fname, sc_name=SC_NAME, sc_frame=SC_FRAME, start=start, stop=stop
    )
    _assert_same_frame(loaded.data, p.data.iloc[rows])
    _assert_same_frame(loaded.sc.data, p.sc.data.iloc[rows])
    _assert_same_frame(loaded.aux, p.aux.iloc[rows])


def test_save_applies_each_modifier_function_before_writing(tmp_path):
    """Each modifier function changes what is saved for its own frame only.

    The data modifier drops the alphas, the spacecraft modifier drops the
    Carrington coordinates, and the aux modifier drops the chi-squared column.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(
        fname,
        data_modifier_fcn=lambda d: d.drop(columns="a", level="S"),
        sc_modifier_fcn=lambda sc: sc.drop(columns="carr", level="M"),
        aux_modifier_fcn=lambda aux: aux.drop(columns="chisq", level="M"),
    )
    loaded = plasma.Plasma.load_from_file(fname, sc_name=SC_NAME, sc_frame=SC_FRAME)

    assert loaded.species == ("e", "p1", "p2")
    _assert_same_frame(loaded.data, p.data.drop(columns="a", level="S"))
    _assert_same_frame(loaded.sc.data, p.sc.data.drop(columns="carr", level="M"))
    _assert_same_frame(loaded.aux, p.aux.drop(columns="chisq", level="M"))


@pytest.mark.parametrize(
    "kwarg", ["data_modifier_fcn", "sc_modifier_fcn", "aux_modifier_fcn"]
)
def test_save_rejects_a_modifier_that_is_not_a_function(tmp_path, kwarg):
    """A modifier must be a plain function; another callable raises TypeError.

    `functools.partial` is callable and would work if called, so the error
    comes from the type check alone. The other two modifiers are valid
    functions, so a check that inspects the wrong parameter does not raise.
    The message names the rejected type, not the parameter.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    modifiers = {
        "data_modifier_fcn": _identity,
        "sc_modifier_fcn": _identity,
        "aux_modifier_fcn": _identity,
    }
    modifiers[kwarg] = functools.partial(_identity)
    with pytest.raises(TypeError, match="partial"):
        p.save(tmp_path / "plasma.h5", **modifiers)


@pytest.mark.parametrize(
    "sc_name, sc_frame, missing",
    [
        (None, SC_FRAME, rf"name : None\nframe: {re.escape(SC_FRAME)}"),
        (SC_NAME, None, rf"name : {re.escape(SC_NAME)}\nframe: None"),
        (None, None, r"name : None\nframe: None"),
    ],
    ids=["no-name", "no-frame", "neither"],
)
def test_load_from_file_needs_spacecraft_name_and_frame(
    tmp_path, sc_name, sc_frame, missing
):
    """Loading spacecraft data without both its name and frame raises ValueError.

    The message reports each parameter's value, so the missing one reads None.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    with pytest.raises(ValueError, match=missing):
        plasma.Plasma.load_from_file(fname, sc_name=sc_name, sc_frame=sc_frame)


def test_load_from_file_loads_only_the_species_passed(tmp_path):
    """Species passed to `load_from_file` select the species of the plasma.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    loaded = plasma.Plasma.load_from_file(fname, "p1", sckey=None, akey=None)
    assert loaded.species == ("p1",)
    assert loaded.ions.index.tolist() == ["p1"]


def test_load_from_file_passes_extra_keywords_to_plasma(tmp_path):
    """Keywords `load_from_file` does not name go to `Plasma.__init__`.

    With ``akey=None`` nothing is read from the file's aux key, so the
    auxiliary data can only come from the ``auxiliary_data`` keyword.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    aux = p.aux.drop(columns="chisq", level="M")
    loaded = plasma.Plasma.load_from_file(
        fname, sckey=None, akey=None, auxiliary_data=aux
    )
    pdt.assert_frame_equal(loaded.aux, aux)


_O9C = (
    "author's ruling o9c: sc and aux are written under the names they are read "
    "by (set_sc, set_aux, sc=, aux=, auxkey=); remove this marker when it lands"
)


@pytest.mark.xfail(strict=True, reason=_O9C)
def test_sc_and_aux_are_written_under_the_names_they_are_read_by():
    """``plasma.sc`` and ``plasma.aux`` are set by ``set_sc`` and ``set_aux``.

    The constructor takes ``sc=`` and ``aux=``, and ``save`` and
    ``load_from_file`` take ``auxkey=`` beside ``sckey=``. The long names are
    gone.

    ON FAILURE: the code is wrong.
    """
    import inspect

    cls = plasma.Plasma
    assert hasattr(cls, "set_sc") and hasattr(cls, "set_aux")
    assert not hasattr(cls, "set_spacecraft")
    assert not hasattr(cls, "set_auxiliary_data")
    init = inspect.signature(cls.__init__).parameters
    assert {"sc", "aux"} <= set(init)
    assert not {"spacecraft", "auxiliary_data"} & set(init)
    for method in (cls.save, cls.load_from_file):
        params = inspect.signature(method).parameters
        assert {"sckey", "auxkey"} <= set(params)
        assert "akey" not in params


@pytest.mark.xfail(strict=True, reason=_O9C)
def test_sc_and_aux_keywords_round_trip_at_a_chosen_aux_key(tmp_path):
    """A plasma built with ``sc=`` and ``aux=`` saves and loads at ``auxkey``.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    built = plasma.Plasma(p.data, *p.species, sc=p.sc, aux=p.aux)
    fname = tmp_path / "plasma.h5"
    built.save(fname, auxkey="AUX")
    with pd.HDFStore(fname, mode="r") as store:
        assert sorted(store.keys()) == ["/AUX", "/FC", "/SC"]
    loaded = plasma.Plasma.load_from_file(
        fname, auxkey="AUX", sc_name=SC_NAME, sc_frame=SC_FRAME
    )
    _assert_same_frame(loaded.sc.data, p.sc.data)
    _assert_same_frame(loaded.aux, p.aux)
