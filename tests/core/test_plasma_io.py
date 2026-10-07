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
    """Example plasma with its spacecraft and two auxiliary columns.

    The example epochs are 1995-01-01, 2022-03-23 and 2022-10-09, so a start or
    stop date in 2022 keeps a known subset of rows.
    """
    p = swp.examples.load_plasma()
    # What the tests below assume of the example data.
    assert p.species == ("a", "e", "p1", "p2"), "example plasma species changed"
    # test_save_applies_each_modifier_function_before_writing drops "carr".
    assert "carr" in p.spacecraft.data.columns.get_level_values(
        "M"
    ), "example spacecraft no longer has Carrington coordinates"
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
    assert loaded.spacecraft.name == SC_NAME
    assert loaded.spacecraft.frame == SC_FRAME
    _assert_same_frame(loaded.spacecraft.data, p.spacecraft.data)
    _assert_same_frame(loaded.auxiliary_data, p.auxiliary_data)


def test_save_writes_data_spacecraft_and_aux_at_the_default_keys(tmp_path):
    """`save` stores data at "FC", spacecraft at "SC" and aux at "FC_AUX".

    These are the documented defaults that `load_from_file` reads back.

    ON FAILURE: the code is wrong.
    """
    p = _example_plasma()
    fname = tmp_path / "plasma.h5"
    p.save(fname)
    with pd.HDFStore(fname, mode="r") as store:
        assert sorted(store.keys()) == ["/FC", "/FC_AUX", "/SC"]
    _assert_same_frame(pd.read_hdf(fname, key="SC"), p.spacecraft.data)
    _assert_same_frame(pd.read_hdf(fname, key="FC_AUX"), p.auxiliary_data)


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
    _assert_same_frame(loaded.spacecraft.data, p.spacecraft.data.iloc[rows])
    _assert_same_frame(loaded.auxiliary_data, p.auxiliary_data.iloc[rows])


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
    _assert_same_frame(
        loaded.spacecraft.data, p.spacecraft.data.drop(columns="carr", level="M")
    )
    _assert_same_frame(
        loaded.auxiliary_data, p.auxiliary_data.drop(columns="chisq", level="M")
    )


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
    aux = p.auxiliary_data.drop(columns="chisq", level="M")
    loaded = plasma.Plasma.load_from_file(
        fname, sckey=None, akey=None, auxiliary_data=aux
    )
    pdt.assert_frame_equal(loaded.auxiliary_data, aux)
